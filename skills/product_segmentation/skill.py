"""Skill: ejecución y reentrenamiento del modelo de segmentación de productos (RF11, RNF06)."""

from typing import Dict, Any, List
from core.skill_base.base_skill import BaseSkill
from core.skill_base.skill_registry import register_skill
from skills.product_segmentation.model import ProductSegmentationModel

_model_instance = ProductSegmentationModel(n_clusters=3)


@register_skill
class ProductSegmentationSkill(BaseSkill):
    name = "product_segmentation"

    def run(self, params: dict) -> dict:
        action = params.get("action", "segment")
        products: List[Dict[str, Any]] = params.get("products", [])
        sales_history: List[Dict[str, Any]] = params.get("sales_history", [])
        festivities: List[Dict[str, Any]] = params.get("festivities", [])
        window_days = params.get("window_days", 30)

        df = _model_instance.extract_features(products, sales_history, festivities, window_days)
        segmented_products = _model_instance.train_and_segment(df)

        return {
            "status": "success",
            "action_executed": action,
            "is_trained": _model_instance.is_fitted,
            "segmented_products": segmented_products
        }
