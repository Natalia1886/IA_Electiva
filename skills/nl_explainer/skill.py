"""Skill: generación de explicaciones en lenguaje natural para el tendero/administrador (RF13, HU07, RNF01).
Transforma métricas y números en motivos claros, empáticos y libres de tecnicismos.
"""

from typing import Dict, Any, List
from core.skill_base.base_skill import BaseSkill
from core.skill_base.skill_registry import register_skill


@register_skill
class NLExplainerSkill(BaseSkill):
    name = "nl_explainer"

    def run(self, params: dict) -> dict:
        recommendations: List[Dict[str, Any]] = params.get("recommendations", [])
        festivities: List[Dict[str, Any]] = params.get("festivities", [])

        # Buscar festividad principal más próxima
        upcoming_fest_name = festivities[0]["name"] if festivities else "las próximas celebraciones religiosas"

        explained_items = []
        for rec in recommendations:
            pname = rec["product_name"]
            stock = rec["stock_actual"]
            min_stock = rec["stock_minimo"]
            qty = rec["suggested_quantity"]
            priority = rec["priority"]
            fest_factor = rec.get("festivity_factor", 1.0)
            action = rec.get("action", "COMPRAR")

            if action == "NO_COMPRAR":
                reason = (
                    f"Atención: Este producto tiene suficiente mercancía en bodega ({stock} unidades) "
                    f"y ha tenido muy pocas salidas recientemente. Le sugerimos NO comprar más por ahora "
                    f"para evitar acumular dinero y productos sin rotar."
                )
            elif priority == "URGENTE":
                if fest_factor > 1.2:
                    reason = (
                        f"¡Producto agotado! Quedan 0 unidades en la tienda y se aproxima {upcoming_fest_name}. "
                        f"Como los feligreses lo pedirán con mayor frecuencia, le recomendamos pedir "
                        f"{qty} unidades de inmediato para no perder ventas."
                    )
                else:
                    reason = (
                        f"¡Producto agotado! Actualmente no tiene existencias (0 unidades). "
                        f"Le recomendamos encargar {qty} unidades a su proveedor para reponer el inventario habitual."
                    )
            elif fest_factor > 1.2:
                reason = (
                    f"Se aproxima {upcoming_fest_name} (demanda estimada al {int(fest_factor * 100)}%). "
                    f"Actualmente solo le quedan {stock} unidades (el mínimo seguro es {min_stock}). "
                    f"Se recomienda comprar {qty} unidades para abastecer la tienda antes de que comiencen las ventas fuertes."
                )
            elif stock <= min_stock:
                reason = (
                    f"El stock actual ({stock} unidades) está por debajo de su nivel de seguridad ({min_stock} unidades). "
                    f"Se aconseja encargar {qty} unidades para mantener un surtido seguro y no quedarse sin mercancía."
                )
            else:
                reason = (
                    f"Producto con ventas regulares. Con {stock} unidades actuales, se sugiere comprar {qty} "
                    f"unidades adicionales para cubrir la demanda estimada de los próximos 15 días."
                )

            item = rec.copy()
            item["natural_language_reason"] = reason
            explained_items.append(item)

        return {
            "status": "success",
            "explained_recommendations": explained_items
        }
