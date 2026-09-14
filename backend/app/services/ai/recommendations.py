"""Purchase recommendation service — ML decision + NL phrasing.

Pipeline (Prompt 17):

1. The team-trained **segmentation model** (see ``scripts/train_segmenter.py``
   and :mod:`app.services.ai.segmentation`) classifies each active product by
   demand behaviour using the digitized sales history.
2. This service cross-references the model output with current inventory,
   minimum-stock levels, sales history and the next religious holiday to
   compute an **estimated demand** and a **recommended quantity** per product.
3. A language model (or a deterministic template when no API key is set)
   phrases that numeric result into a readable recommendation.

The recommendation is fully explainable: every item carries a ``reason`` built
from the actual feature values that drove the decision (segment, rate, uplift
around the feast, stock vs minimum), never generic disconnected text.
"""
from __future__ import annotations

import math
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.holiday import ReligiousHoliday
from app.models.product import Product
from app.services.ai import holiday_engine, natural_language, segmentation

COVERAGE_DAYS = 15   # days of forecast demand to purchase for
ROUND_TO = 5         # quantities are bought in multiples of 5 (retail reality)
HOLIDAY_TRIGGER = 1.15  # minimum uplift to treat a feast as a buy trigger


def _round_up(value: float, step: int = ROUND_TO) -> int:
    return int(math.ceil(value / step) * step)


def _build_reason(product, f: dict, label: str | None, rate: float, est: float,
                  holiday: dict | None, uplift: float, factor: float) -> str:
    parts = []
    if label and rate > 0:
        parts.append(f"producto del segmento de demanda {label} ({rate:.2f} uds/día en los últimos {segmentation.LOOKBACK_DAYS} días)")
    elif rate > 0:
        parts.append(f"velocidad de venta de {rate:.2f} uds/día")
    else:
        parts.append("sin ventas en los últimos 30 días")

    if holiday and factor > HOLIDAY_TRIGGER and factor >= uplift:
        parts.append(
            f"factor de demanda esperada x{factor:.1f} registrado por el administrador para "
            f"{holiday['name']} (próxima fecha en {holiday['days_until']} días)"
        )
    elif holiday and uplift > HOLIDAY_TRIGGER:
        parts.append(
            f"alza de {round((uplift - 1) * 100)}% en sus ventas en torno a {holiday['name']} "
            f"(próxima fecha en {holiday['days_until']} días)"
        )
    elif holiday:
        parts.append(f"se acerca {holiday['name']} (en {holiday['days_until']} días)")

    if product.stock < product.min_stock:
        parts.append(f"stock actual ({product.stock}) por debajo del mínimo ({product.min_stock})")

    if f["days_since_last"] >= 10:
        parts.append(f"última venta hace {f['days_since_last']} días")

    if not parts:
        parts.append("proyección de demanda")

    parts.append(f"demanda estimada de {est:.0f} uds en los próximos {COVERAGE_DAYS} días")
    return "; ".join(parts)


def _summary(items: list[dict], ml: bool) -> str:
    if ml:
        return (
            "El modelo de segmentación recomienda reponer {} productos. "
            "Las cantidades cruzan inventario, stock mínimo y demanda histórica "
            "incluyendo la correlación con festividades religiosas próximas."
        ).format(len(items))
    return (
        "Modelo de segmentación no entrenado: se usa una heurística de reglas. "
        "Recomendaciones para {} productos según velocidad de venta y stock mínimo."
    ).format(len(items))


async def generate_recommendations(db) -> dict:
    products = (
        (await db.execute(
            select(Product)
            .options(selectinload(Product.category), selectinload(Product.holidays))
            .where(Product.is_active.is_(True))
        ))
        .scalars()
        .all()
    )
    holidays = (
        (await db.execute(select(ReligiousHoliday).options(selectinload(ReligiousHoliday.products))))
        .scalars()
        .all()
    )

    today = date.today()
    features = await segmentation.feature_rows(db, products, holidays, today)
    by_id = {f["product_id"]: f for f in features}

    artifact = segmentation.load_segmenter()
    ml = artifact is not None
    segments = segmentation.predict_segments(artifact, features) if ml else {}
    source = (
        f"segmentación ML (k={artifact['metrics']['k']}, silueta={artifact['metrics']['silhouette']})"
        if ml
        else "reglas (modelo no entrenado)"
    )

    # Empirical mean demand rate per segment -> explainable "segment baseline".
    seg_values: dict[str, list[float]] = {}
    for f in features:
        seg = segments.get(f["product_id"])
        if seg:
            seg_values.setdefault(seg, []).append(f["freq_rate"])
    seg_rate = {seg: sum(v) / len(v) for seg, v in seg_values.items()}

    upcoming_map: dict[int, dict] = {}
    for h in holiday_engine.upcoming_holidays(
        holidays, today, window_days=segmentation.HOLIDAY_LOOKAHEAD_DAYS
    ):
        for p in h["products"]:
            upcoming_map.setdefault(p["id"], h)

    items = []
    for product in products:
        f = by_id.get(product.id)
        if f is None:
            continue

        label = segments.get(product.id) if ml else None
        rate = seg_rate.get(label, f["freq_rate"]) if label else f["freq_rate"]

        holiday = upcoming_map.get(product.id)
        holiday_factor = float(holiday.get("factor", 1.0)) if holiday else 1.0
        # Cross-reference with the administrator-registered demand factor (Prompt 18):
        # the configured multiplier wins when it exceeds the empirical holiday uplift.
        uplift = max(f["holiday_uplift"], holiday_factor)
        est = rate * COVERAGE_DAYS
        if uplift > HOLIDAY_TRIGGER:
            est *= uplift

        suggested = _round_up(max(est - product.stock, 0.0))
        if product.stock < product.min_stock:
            suggested = max(suggested, _round_up(product.min_stock - product.stock))

        triggered = (
            suggested >= ROUND_TO
            or product.stock < product.min_stock
            or (holiday is not None and uplift > HOLIDAY_TRIGGER)
        )
        if not triggered:
            continue

        reason = _build_reason(product, f, label, rate, est, holiday, f["holiday_uplift"], holiday_factor)
        items.append(
            {
                "product_id": product.id,
                "code": product.code,
                "name": product.name,
                "current_stock": product.stock,
                "min_stock": product.min_stock,
                "sold_last_30_days": int(f["units_30"]),
                "upcoming_holiday": holiday["name"] if holiday else None,
                "segment": label,
                "estimated_demand": round(est, 1),
                "suggested_quantity": suggested,
                "reason": reason,
                "rationale": "",
            }
        )

    texts = await natural_language.phrase_recommendations(items)
    for item in items:
        item["rationale"] = texts.get(item["code"], "")

    items.sort(key=lambda i: i["suggested_quantity"], reverse=True)
    return {
        "generated_for": today,
        "source": source,
        "items": items,
        "summary": _summary(items, ml),
    }