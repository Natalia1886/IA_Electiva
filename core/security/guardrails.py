"""Guardrails y validaciones de negocio para proteger la integridad de datos (HU02, HU03)."""

from typing import List, Dict, Any, Tuple


class BusinessValidationError(Exception):
    """Excepción de validación de reglas de negocio."""
    pass


def validate_product_data(data: Dict[str, Any]) -> None:
    """Valida reglas de negocio para creación y edición de productos (RF04, HU02)."""
    price = data.get("price")
    if price is None or price < 0:
        raise BusinessValidationError("El precio del producto no puede ser negativo.")

    stock = data.get("stock_actual", 0)
    if stock is not None and stock < 0:
        raise BusinessValidationError("El stock inicial no puede ser negativo.")

    name = data.get("name", "").strip()
    if not name:
        raise BusinessValidationError("El nombre del producto es obligatorio.")

    category = data.get("category", "").strip()
    if not category:
        raise BusinessValidationError("La categoría del producto es obligatoria.")


def validate_sale_items(items: List[Dict[str, Any]], stock_lookup: Dict[int, int]) -> None:
    """Valida que los productos a vender tengan stock suficiente (HU03)."""
    if not items:
        raise BusinessValidationError("La venta debe contener al menos un producto.")

    for item in items:
        pid = item.get("product_id")
        qty = item.get("quantity", 0)

        if qty <= 0:
            raise BusinessValidationError(f"La cantidad para el producto ID {pid} debe ser mayor a 0.")

        available_stock = stock_lookup.get(pid, 0)
        if qty > available_stock:
            raise BusinessValidationError(
                f"Stock insuficiente para el producto ID {pid}. Solicitado: {qty}, Disponible: {available_stock}."
            )
