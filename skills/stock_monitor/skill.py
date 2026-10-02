"""Skill: monitoreo continuo de inventario y generación de alertas tempranas (RF09, HU05)."""

from typing import Dict, Any, List
from core.skill_base.base_skill import BaseSkill
from core.skill_base.skill_registry import register_skill


@register_skill
class StockMonitorSkill(BaseSkill):
    name = "stock_monitor"

    def run(self, params: dict) -> dict:
        products: List[Dict[str, Any]] = params.get("products", [])
        alerts = []
        out_of_stock_count = 0
        low_stock_count = 0

        for p in products:
            stock = p.get("stock_actual", 0)
            stock_min = p.get("stock_minimo", 5)
            pid = p.get("id")
            pname = p.get("name")
            pcode = p.get("code")

            if stock == 0:
                out_of_stock_count += 1
                alerts.append({
                    "product_id": pid,
                    "product_code": pcode,
                    "product_name": pname,
                    "stock_actual": stock,
                    "stock_minimo": stock_min,
                    "alert_type": "AGOTADO",
                    "severity": "CRITICA",
                    "message": f"El producto '{pname}' está completamente agotado (0 unidades)."
                })
            elif stock <= stock_min:
                low_stock_count += 1
                alerts.append({
                    "product_id": pid,
                    "product_code": pcode,
                    "product_name": pname,
                    "stock_actual": stock,
                    "stock_minimo": stock_min,
                    "alert_type": "STOCK_BAJO",
                    "severity": "ALTA",
                    "message": f"Stock bajo en '{pname}': quedan {stock} unidades (mínimo sugerido: {stock_min})."
                })

        return {
            "status": "success",
            "total_products_monitored": len(products),
            "out_of_stock_count": out_of_stock_count,
            "low_stock_count": low_stock_count,
            "total_alerts": len(alerts),
            "alerts": alerts
        }
