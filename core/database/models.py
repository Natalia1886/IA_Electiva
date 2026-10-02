"""Modelos de datos relacionales para la tienda de artículos religiosos.
Cumple con requerimientos de transaccionalidad (RNF05) y auditabilidad (RNF08).
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    """Usuario del sistema con roles definidos (RF01, RF02, HU01)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)  # RNF03: Passwords cifradas
    full_name = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False, default="VENDEDOR")  # 'ADMIN' o 'VENDEDOR'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    sales = relationship("Sale", back_populates="seller")
    movements = relationship("InventoryMovement", back_populates="user")


class Product(Base):
    """Producto de la tienda religiosa (RF03, RF04, RF05, HU02)."""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(30), unique=True, nullable=False, index=True)  # Código formal
    name = Column(String(150), nullable=False, index=True)
    category = Column(String(60), nullable=False, index=True)  # Velas, Vírgenes, Santos, Pesebres, etc.
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)  # Validar >= 0
    stock_actual = Column(Integer, nullable=False, default=0)
    stock_minimo = Column(Integer, nullable=False, default=5)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    sale_items = relationship("SaleItem", back_populates="product")
    movements = relationship("InventoryMovement", back_populates="product")


class Sale(Base):
    """Venta registrada en la tienda (RF06, RF07, RF08, HU03)."""
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    sale_number = Column(String(30), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_amount = Column(Float, nullable=False, default=0.0)
    payment_method = Column(String(30), default="EFECTIVO")  # Efectivo, Nequi, Tarjeta
    notes = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    seller = relationship("User", back_populates="sales")
    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")


class SaleItem(Base):
    """Detalle de productos en una venta (RF06)."""
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)

    sale = relationship("Sale", back_populates="items")
    product = relationship("Product", back_populates="sale_items")


class InventoryMovement(Base):
    """Histórico auditable de entradas y salidas de stock (RF09, RNF08)."""
    __tablename__ = "inventory_movements"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    movement_type = Column(String(20), nullable=False)  # 'ENTRADA', 'SALIDA', 'AJUSTE'
    quantity = Column(Integer, nullable=False)
    previous_stock = Column(Integer, nullable=False)
    new_stock = Column(Integer, nullable=False)
    reason = Column(String(255), nullable=False)  # 'Venta #VTA-001', 'Compra a proveedor', 'Ajuste inicial'
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    product = relationship("Product", back_populates="movements")
    user = relationship("User", back_populates="movements")


class Festivity(Base):
    """Festividades religiosas que impactan la demanda (RF10, HU06)."""
    __tablename__ = "festivities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)  # Ej. "Semana Santa", "Fiestas de Ibagué"
    start_date = Column(String(10), nullable=False)  # YYYY-MM-DD
    end_date = Column(String(10), nullable=False)    # YYYY-MM-DD
    demand_factor = Column(Float, nullable=False, default=1.5)  # Multiplicador de demanda (ej. 1.8x)
    affected_categories = Column(Text, nullable=True)  # JSON o lista separada por comas
    affected_products = Column(Text, nullable=True)    # JSON o lista separada por comas
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
