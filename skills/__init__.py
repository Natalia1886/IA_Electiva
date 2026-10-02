"""Skills del sistema para la tienda religiosa."""
from skills.db_repository.skill import DbRepositorySkill
from skills.product_segmentation.skill import ProductSegmentationSkill
from skills.demand_forecaster.skill import DemandForecasterSkill
from skills.nl_explainer.skill import NLExplainerSkill
from skills.stock_monitor.skill import StockMonitorSkill

__all__ = [
    "DbRepositorySkill",
    "ProductSegmentationSkill",
    "DemandForecasterSkill",
    "NLExplainerSkill",
    "StockMonitorSkill",
]
