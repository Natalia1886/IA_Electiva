"""Feature engineering + product-demand segmentation model.

Role in the pipeline
--------------------
This is the *decision* layer of the purchase recommender:

1. :func:`feature_rows` builds, for every product, features from the digitized
   sales history: sales frequency, days since the last sale, sales variance,
   category and correlation with religious holidays (uplift during the
   preparation window before each next religious feast).
2. The team trains a small, explainable **KMeans** segmentation on those
   features (see ``scripts/train_segmenter.py``) — each cluster is a demand
   segment whose *centroid is a readable profile* (e.g. "high frequency,
   strong holiday correlation").
3. At runtime the trained model assigns each product to a segment; the
   recommender turns the segment + the product's own features into a
   recommended quantity.

A large language model is only used to *phrase* the resulting number into a
readable recommendation — it never decides the quantity.
"""
from __future__ import annotations

import math
import os
from collections import Counter, defaultdict
from datetime import date, timedelta
from statistics import pstdev

import joblib
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import davies_bouldin_score, silhouette_score
from sklearn.preprocessing import StandardScaler
from sqlalchemy import func, select

from app.config import settings
from app.models.sale import Sale, SaleItem
from app.services.ai import holiday_engine

LOOKBACK_DAYS = 30      # window for frequency/velocity metrics
BASELINE_DAYS = 60      # window for daily-variance and baseline demand
HOLIDAY_LOOKAHEAD_DAYS = 60  # only feasts inside this window can trigger a buy
HOLIDAY_PREP_WINDOW = 14     # demand concentrates in the days BEFORE the feast
MAX_UPLIFT = 10.0           # cap on holiday-uplift ratio (protects outliers)
NO_SALE_AGE = 400           # "never sold" recency value (days ago)

FEATURE_COLUMNS = [
    "freq_rate",        # units/day over the last 30 days (sales frequency)
    "tx_count_30d",     # number of sale transactions in the last 30 days
    "days_since_last",  # recency in days
    "daily_var",        # std of daily units over the last 60 days
    "category_code",    # ordinal encoding of the product category
    "holiday_uplift",   # max demand ratio around upcoming religious feasts
]

MODEL_FILE = "segmenter.joblib"


def model_path() -> str:
    return os.path.join(settings.ai_model_dir, MODEL_FILE)


async def _load_sales_history(db, as_of: date, window_days: int = 400) -> dict[int, Counter]:
    """Daily units per product over the historical window."""
    start = as_of - timedelta(days=window_days)
    rows = (
        await db.execute(
            select(SaleItem.product_id, Sale.sale_date, func.sum(SaleItem.quantity))
            .join(Sale, Sale.id == SaleItem.sale_id)
            .where(Sale.status == "completed", Sale.sale_date >= start)
            .group_by(SaleItem.product_id, Sale.sale_date)
        )
    ).all()

    daily: dict[int, Counter] = defaultdict(Counter)
    for product_id, sale_date, quantity in rows:
        daily[product_id][sale_date] += int(quantity)
    return daily


async def _tx_count_30d(db, product_ids: list[int], as_of: date) -> dict[int, int]:
    """Number of sale transactions per product in the last 30 days."""
    thirty = as_of - timedelta(days=LOOKBACK_DAYS)
    rows = (
        await db.execute(
            select(SaleItem.product_id, func.count(func.distinct(SaleItem.sale_id)))
            .join(Sale, Sale.id == SaleItem.sale_id)
            .where(Sale.status == "completed", Sale.sale_date >= thirty,
                   SaleItem.product_id.in_(product_ids))
            .group_by(SaleItem.product_id)
        )
    ).all()
    return {pid: int(cnt) for pid, cnt in rows}


def _holiday_uplift_ratio(
    holidays,
    upcoming: list[dict],
    daily: dict[int, Counter],
    baseline_day: dict[int, float],
    as_of: date,
) -> dict[int, float]:
    """Max ratio of (holiday-window daily demand) / (baseline daily demand)."""
    ratio: dict[int, float] = defaultdict(float)
    for holiday in upcoming:
        if holiday["days_until"] > HOLIDAY_LOOKAHEAD_DAYS:
            continue
        occurrence = holiday["date"]
        if occurrence <= as_of:
            continue
        previous = _previous_occurrence(holiday["id"], occurrence, holidays, as_of)
        if previous is None:
            continue
        win_start = previous - timedelta(days=HOLIDAY_PREP_WINDOW)
        win_end = previous - timedelta(days=1)
        for product_id in baseline_day:
            units = sum(
                qty for d, qty in daily[product_id].items() if win_start <= d <= win_end
            )
            base = max(baseline_day[product_id], 1e-6)
            r = (units / HOLIDAY_PREP_WINDOW) / base
            if r > ratio[product_id]:
                ratio[product_id] = r
    return {pid: min(round(r, 3), MAX_UPLIFT) for pid, r in ratio.items()}


def _previous_occurrence(holiday_id: int, upcoming_date: date, holidays, as_of: date) -> date | None:
    holiday = next((h for h in holidays if h.id == holiday_id), None)
    if holiday is None:
        return None
    candidates = [
        holiday_engine.next_occurrence(holiday, date(year, 1, 1))
        for year in (upcoming_date.year - 1, upcoming_date.year - 2)
        if date(year, 1, 1) >= as_of - timedelta(days=730)
    ]
    valid = [c for c in candidates if c < upcoming_date]
    return max(valid) if valid else None


async def feature_rows(db, products, holidays, as_of: date | None = None) -> list[dict]:
    """Compute the feature vector for every product (used in training AND at runtime)."""
    as_of = as_of or date.today()
    rows: list[dict] = []
    if not products:
        return rows

    product_ids = [p.id for p in products]
    daily = await _load_sales_history(db, as_of)
    tx_30 = await _tx_count_30d(db, product_ids, as_of)
    thirty = as_of - timedelta(days=LOOKBACK_DAYS)
    sixty = as_of - timedelta(days=BASELINE_DAYS)

    category_names = {p.category.name if p.category else "SIN_CATEGORÍA" for p in products}
    cat_code = {name: i for i, name in enumerate(sorted(category_names))}

    upcoming = holiday_engine.upcoming_holidays(holidays, as_of, window_days=HOLIDAY_LOOKAHEAD_DAYS)

    raw: dict[int, dict] = {}
    baseline_day: dict[int, float] = {}
    for product in products:
        pid = product.id
        series = daily.get(pid, Counter())
        units_30 = sum(q for d, q in series.items() if d >= thirty)
        units_60 = sum(q for d, q in series.items() if d >= sixty)
        last = max(series) if series else None
        recent_60 = [series.get(d, 0) for d in _date_range(sixty, as_of)]
        raw[pid] = {
            "freq": units_30 / LOOKBACK_DAYS,
            "units_30": units_30,
            "days_since": (as_of - last).days if last else NO_SALE_AGE,
            "var60": pstdev(recent_60) if len(recent_60) > 1 else 0.0,
            "tx30": tx_30.get(pid, 0),
            "category": cat_code[product.category.name if product.category else "SIN_CATEGORÍA"],
        }
        baseline_day[pid] = units_60 / BASELINE_DAYS

    uplift = _holiday_uplift_ratio(holidays, upcoming, daily, baseline_day, as_of)

    for product in products:
        pid = product.id
        f = raw[pid]
        rows.append(
            {
                "product_id": pid,
                "code": product.code,
                "name": product.name,
                "freq_rate": round(f["freq"], 5),
                "tx_count_30d": f["tx30"],
                "days_since_last": f["days_since"],
                "daily_var": round(f["var60"], 4),
                "category_code": f["category"],
                "holiday_uplift": uplift.get(pid, 0.0),
                "units_30": f["units_30"],
            }
        )
    return rows


def _date_range(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def feature_matrix(rows: list[dict]) -> np.ndarray:
    return np.array([[row[c] for c in FEATURE_COLUMNS] for row in rows], dtype=float)


def train_segmenter(rows: list[dict], min_clusters=2, max_clusters=5) -> dict:
    """Fit KMeans on standardized features, pick k by silhouette score.

    Returns everything needed to evaluate AND to reproduce the decision at
    runtime: scaler, model, segment names and the fitted metrics.
    """
    X = feature_matrix(rows)
    if len(X) < 2:
        raise ValueError("Se necesitan al menos 2 productos con datos para entrenar")

    scaler = StandardScaler().fit(X)
    Xs = scaler.transform(X)

    best: dict = {"k": min_clusters, "score": -math.inf}
    for k in range(min_clusters, min(max_clusters, len(Xs)) + 1):
        model = KMeans(n_clusters=k, n_init=10, random_state=42).fit(Xs)
        score = silhouette_score(Xs, model.labels_)
        if score > best["score"]:
            best = {"k": k, "score": float(score), "model": model}

    model = best["model"]
    labels = model.labels_
    metrics = {
        "k": best["k"],
        "silhouette": round(best["score"], 4),
        "davies_bouldin": round(float(davies_bouldin_score(Xs, labels)), 4),
        "inertia": round(float(model.inertia_), 2),
        "cluster_sizes": {int(i): int((labels == i).sum()) for i in range(best["k"])},
        "trained_at": date.today().isoformat(),
    }

    # Name each cluster by its empirical velocity (real freq_rate average),
    # most-velocity first, so a segment is a readable profile: alta/media/baja.
    mean_freq = [float(np.mean([rows[j]["freq_rate"] for j in range(len(rows)) if labels[j] == i]))
                 for i in range(best["k"])]
    order = sorted(range(best["k"]), key=lambda i: mean_freq[i], reverse=True)
    names = ["alta", "media", "baja", "ocasional", "inactiva"]
    segment_labels = {int(i): names[pos] for pos, i in enumerate(order)}

    return {
        "scaler": scaler,
        "model": model,
        "feature_columns": FEATURE_COLUMNS,
        "category_codes": None,  # filled by caller if needed
        "segment_labels": segment_labels,
        "metrics": metrics,
    }


def save_segmenter(artifact: dict, path: str | None = None) -> str:
    target = path or model_path()
    os.makedirs(os.path.dirname(target), exist_ok=True)
    joblib.dump(artifact, target)
    return target


def load_segmenter(path: str | None = None) -> dict | None:
    target = path or model_path()
    if not os.path.exists(target):
        return None
    return joblib.load(target)


def predict_segments(artifact: dict, rows: list[dict]) -> dict[int, str]:
    """Assign each product row to its segment label using the trained model."""
    if artifact is None or not rows:
        return {}
    Xs = artifact["scaler"].transform(feature_matrix(rows))
    labels = artifact["model"].predict(Xs)
    labels_by_id = {row["product_id"]: int(lab) for row, lab in zip(rows, labels)}
    return {pid: artifact["segment_labels"][lab] for pid, lab in labels_by_id.items()}