"""Pruebas unitarias para el calculador de pronóstico y compras (RF12)."""

from skills.demand_forecaster.skill import DemandForecasterSkill


def test_forecaster_calculates_purchase_needed():
    skill = DemandForecasterSkill()
    segmented = [
        {
            "product_id": 1,
            "name": "Vela Religiosa Blanca",
            "category": "Velas",
            "stock_actual": 8,
            "stock_minimo": 10,
            "total_units_sold": 45,
            "festivity_factor": 2.5,
            "frequency_sales": 15,
            "segment": "ESTACIONAL_FESTIVO"
        },
        {
            "product_id": 2,
            "name": "Pesebre Tradicional",
            "category": "Pesebres",
            "stock_actual": 18,
            "stock_minimo": 4,
            "total_units_sold": 0,
            "festivity_factor": 1.0,
            "frequency_sales": 0,
            "segment": "LENTA_ROTACION"
        }
    ]

    res = skill.run({
        "segmented_products": segmented,
        "window_days": 30,
        "horizon_days": 15
    })

    assert res["status"] == "success"
    recs = res["recommendations"]

    # Vela debe tener acción COMPRAR y prioridad ALTA o URGENTE
    vela_rec = next(r for r in recs if r["product_id"] == 1)
    assert vela_rec["action"] == "COMPRAR"
    assert vela_rec["suggested_quantity"] > 0
    assert vela_rec["priority"] in ["ALTA", "URGENTE"]

    # Pesebre debe tener acción NO_COMPRAR (alerta de sobre-stock)
    pesebre_rec = next(r for r in recs if r["product_id"] == 2)
    assert pesebre_rec["action"] == "NO_COMPRAR"
    assert pesebre_rec["suggested_quantity"] == 0
