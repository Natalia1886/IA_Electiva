"""Pruebas unitarias para el monitor de niveles de stock (RF09, HU05)."""

from skills.stock_monitor.skill import StockMonitorSkill


def test_stock_monitor_alerts():
    skill = StockMonitorSkill()
    products = [
        {"id": 1, "code": "VEL-001", "name": "Vela Blanca", "stock_actual": 8, "stock_minimo": 10},
        {"id": 2, "code": "VEL-002", "name": "Velón Virgen", "stock_actual": 0, "stock_minimo": 5},
        {"id": 3, "code": "IMG-001", "name": "Virgen Guadalupe", "stock_actual": 15, "stock_minimo": 5},
    ]

    res = skill.run({"products": products})
    assert res["status"] == "success"
    assert res["out_of_stock_count"] == 1
    assert res["low_stock_count"] == 1

    alerts = res["alerts"]
    assert len(alerts) == 2

    agotado = next(a for a in alerts if a["alert_type"] == "AGOTADO")
    assert agotado["product_code"] == "VEL-002"

    stock_bajo = next(a for a in alerts if a["alert_type"] == "STOCK_BAJO")
    assert stock_bajo["product_code"] == "VEL-001"
