"""Rutas del módulo de Inteligencia Artificial y Recomendaciones de Compra (RF11, RF12, RF13, RF14, HU07, RNF06)."""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from core.orchestrator.executor import Executor
from core.database.models import User
from interfaces.api.dependencies import require_admin

router = APIRouter(prefix="/recommendations", tags=["Recomendaciones IA"])
executor = Executor()


@router.get("")
def get_purchase_recommendations(
    horizon_days: int = Query(15, ge=1, le=90, description="Días de proyección de demanda"),
    window_days: int = Query(30, ge=7, le=180, description="Días de historial de ventas a evaluar"),
    current_user: User = Depends(require_admin)  # Solo Administrador (RF14, HU07)
):
    """Genera recomendaciones inteligentes de compra en lenguaje natural cruzando inventario, historial y festividades (RF12, RF13, RF14, HU07)."""
    task = {
        "intent": "recommend_purchases",
        "horizon_days": horizon_days,
        "window_days": window_days
    }
    result = executor.execute(task)
    return result


@router.post("/retrain")
def retrain_segmentation_model(
    current_user: User = Depends(require_admin)  # Solo Administrador (RNF06)
):
    """Reentrena el modelo de segmentación de productos con los últimos datos de ventas y festividades (RF11, RNF06)."""
    task = {
        "intent": "recommend_purchases",
        "horizon_days": 15,
        "window_days": 30,
        "force_retrain": True
    }
    result = executor.execute(task)
    return {
        "status": "success",
        "message": "Modelo de segmentación de productos reentrenado satisfactoriamente.",
        "details": result
    }
