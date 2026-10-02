"""Skill: pronóstico de demanda y cálculo de cantidades de compra (RF12).
Cruza stock actual, ventas históricas y factor de festividades religiosas.
"""

import math
from typing import Dict, Any, List
from core.skill_base.base_skill import BaseSkill
from core.skill_base.skill_registry import register_skill


@register_skill
class DemandForecasterSkill(BaseSkill):
    name = "demand_forecaster"

    def run(self, params: dict) -> dict:
        segmented_products: List[Dict[str, Any]] = params.get("segmented_products", [])
        window_days = params.get("window_days", 30)
        horizon_days = params.get("horizon_days", 15)

        recommendations = []

        for p in segmented_products:
            stock_actual = p["stock_actual"]
            stock_minimo = p["stock_minimo"]
            total_sold = p.get("total_units_sold", 0)
            fest_factor = p.get("festivity_factor", 1.0)
            segment = p.get("segment", "ROTACION_MODERADA")

            # Tasa de venta diaria base
            daily_base_rate = (total_sold / max(window_days, 1))

            # Ajuste por festividad religiosa (RF10, RF12)
            adjusted_daily_rate = daily_base_rate * fest_factor

            # Demanda proyectada en el horizonte de compra
            projected_demand = adjusted_daily_rate * horizon_days

            # Stock de seguridad deseado
            safety_stock = max(stock_minimo, math.ceil(adjusted_daily_rate * 4))

            # Stock total necesario para el periodo
            total_needed = projected_demand + safety_stock
            net_deficit = total_needed - stock_actual

            if net_deficit > 0:
                suggested_units = max(1, math.ceil(net_deficit))
                
                # Asignación de prioridad
                if stock_actual == 0:
                    priority = "URGENTE"
                elif fest_factor > 1.2 or stock_actual <= stock_minimo:
                    priority = "ALTA"
                else:
                    priority = "MEDIA"

                recommendations.append({
                    "product_id": p["product_id"],
                    "product_name": p["name"],
                    "category": p["category"],
                    "stock_actual": stock_actual,
                    "stock_minimo": stock_minimo,
                    "suggested_quantity": suggested_units,
                    "priority": priority,
                    "festivity_factor": fest_factor,
                    "segment": segment,
                    "daily_rate": round(adjusted_daily_rate, 2),
                    "projected_demand": round(projected_demand, 1),
                    "action": "COMPRAR"
                })
            else:
                # Detección de mercancía estancada o sobre-stock (Hallazgo 2 y 3)
                if stock_actual > stock_minimo * 2 and p.get("frequency_sales", 0) <= 1:
                    recommendations.append({
                        "product_id": p["product_id"],
                        "product_name": p["name"],
                        "category": p["category"],
                        "stock_actual": stock_actual,
                        "stock_minimo": stock_minimo,
                        "suggested_quantity": 0,
                        "priority": "ALERTA_SOBRE_STOCK",
                        "festivity_factor": fest_factor,
                        "segment": segment,
                        "daily_rate": round(adjusted_daily_rate, 2),
                        "projected_demand": round(projected_demand, 1),
                        "action": "NO_COMPRAR"
                    })

        # Ordenar por prioridad (URGENTE primero, luego ALTA, luego MEDIA)
        prio_order = {"URGENTE": 0, "ALTA": 1, "MEDIA": 2, "ALERTA_SOBRE_STOCK": 3}
        recommendations.sort(key=lambda x: prio_order.get(x["priority"], 99))

        return {
            "status": "success",
            "horizon_days": horizon_days,
            "recommendations": recommendations
        }
