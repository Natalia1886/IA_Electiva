"""Pruebas unitarias para la skill de segmentación de productos (RF11, RNF06)."""

from skills.product_segmentation.skill import ProductSegmentationSkill


def test_segmentation_with_festivity_factor():
    skill = ProductSegmentationSkill()
    products = [
        {"id": 1, "name": "Vela Religiosa Blanca", "category": "Velas", "stock_actual": 5, "stock_minimo": 10},
        {"id": 2, "name": "Pesebre Tradicional", "category": "Pesebres", "stock_actual": 20, "stock_minimo": 5}
    ]
    sales_history = [
        {"sale_id": 1, "product_id": 1, "quantity": 4, "date": "2026-09-20"},
        {"sale_id": 2, "product_id": 1, "quantity": 3, "date": "2026-09-25"},
        {"sale_id": 3, "product_id": 1, "quantity": 5, "date": "2026-09-29"},
    ]
    festivities = [
        {"name": "Semana Santa", "demand_factor": 2.5, "affected_categories": ["Velas"], "affected_products": []}
    ]

    res = skill.run({
        "products": products,
        "sales_history": sales_history,
        "festivities": festivities,
        "window_days": 30
    })

    assert res["status"] == "success"
    segmented = res["segmented_products"]
    assert len(segmented) == 2

    # El producto 1 (Velas) debe verse impactado por Semana Santa
    prod1 = next(p for p in segmented if p["product_id"] == 1)
    assert prod1["festivity_factor"] == 2.5
    assert prod1["total_units_sold"] == 12

    # El producto 2 (Pesebre sin ventas recientes) debe ser identificado como Lenta Rotación
    prod2 = next(p for p in segmented if p["product_id"] == 2)
    assert prod2["segment"] == "LENTA_ROTACION"
