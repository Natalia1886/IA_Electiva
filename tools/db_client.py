"""Cliente directo para operaciones y consultas de infraestructura de base de datos."""

from core.database.connection import SessionLocal
from core.database.models import Product, Sale, InventoryMovement, Festivity


class DatabaseClient:
    """Cliente utilitario de bajo nivel para mantenimiento y consultas directas."""

    @staticmethod
    def get_database_statistics():
        db = SessionLocal()
        try:
            return {
                "total_products": db.query(Product).count(),
                "active_products": db.query(Product).filter_by(is_active=True).count(),
                "total_sales": db.query(Sale).count(),
                "total_movements": db.query(InventoryMovement).count(),
                "total_festivities": db.query(Festivity).count(),
            }
        finally:
            db.close()
