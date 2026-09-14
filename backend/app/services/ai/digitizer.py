"""Digitized-sale provenance helpers.

The photo/AI extractor was removed: sales created with ``digitization_id``
are still supported (historical sales that never touch current stock), and
these helpers keep the provenance and accuracy snapshot used when a digitized
batch is confirmed.
"""
from __future__ import annotations

from datetime import datetime

from app.models.product import Product


def compute_correction_stats(raw_entries: list[dict], validated_entries: list[dict]) -> dict:
    """Compare extracted rows against what the operator actually confirmed.

    Measures how much the digitizer had to be corrected, product- and field-wise,
    so the accuracy of future extractions can be tracked over time.
    """
    FIELDS = ("date", "product_code", "quantity", "unit_price")

    def normalized(value):
        return None if value in (None, "") else value

    total = 0
    corrected = 0
    field_breakdown: dict[str, dict[str, int]] = {
        f: {"corrected": 0, "correct": 0} for f in FIELDS
    }

    for i, raw in enumerate(raw_entries):
        validated = validated_entries[i] if i < len(validated_entries) else {}
        for field in FIELDS:
            total += 1
            r, v = normalized(raw.get(field)), normalized(validated.get(field))
            if r != v:
                corrected += 1
                field_breakdown[field]["corrected"] += 1
            else:
                field_breakdown[field]["correct"] += 1

    missed = sum(
        ("no_en_catalogo" in flag or flag.startswith("quantity:ilegible") or flag.startswith("price:ilegible"))
        for row in raw_entries
        for flag in (row.get("flags") or [])
    )
    accuracy = round((total - corrected) / total, 4) if total else None

    return {
        "rows_extracted": len(raw_entries),
        "rows_confirmed": len(validated_entries),
        "total_fields": total,
        "corrected_fields": corrected,
        "accuracy": accuracy,
        "flagged_fields": missed,
        "by_field": field_breakdown,
        "computed_at": datetime.now().isoformat(timespec="seconds"),
    }


def validated_entries_from_items(
    sale_date, products: dict[int, Product], items, unit_prices: dict[int, float]
) -> list[dict]:
    """Snapshot of what the operator confirmed, for provenance and stats."""
    return [
        {
            "date": sale_date.isoformat(),
            "product_code": products[item.product_id].code,
            "product_name": products[item.product_id].name,
            "quantity": item.quantity,
            "unit_price": unit_prices[item.product_id],
        }
        for item in items
    ]