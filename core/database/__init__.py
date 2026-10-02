"""Módulo de base de datos relacional y persistencia."""
from core.database.connection import get_db, init_db, SessionLocal
from core.database.models import User, Product, Sale, SaleItem, InventoryMovement, Festivity

__all__ = [
    "get_db",
    "init_db",
    "SessionLocal",
    "User",
    "Product",
    "Sale",
    "SaleItem",
    "InventoryMovement",
    "Festivity",
]
