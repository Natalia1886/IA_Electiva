"""Skill: repositorio y operaciones de base de datos para la tienda religiosa.
Garantiza transaccionalidad atómica (RNF05) y auditabilidad (RNF08).
"""

from datetime import datetime, date
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from core.skill_base.base_skill import BaseSkill
from core.skill_base.skill_registry import register_skill
from core.database.connection import SessionLocal
from core.database.models import User, Product, Sale, SaleItem, InventoryMovement, Festivity
from core.security.guardrails import validate_product_data, validate_sale_items, BusinessValidationError


@register_skill
class DbRepositorySkill(BaseSkill):
    name = "db_repository"

    def run(self, params: dict) -> dict:
        action = params.get("action")
        db = SessionLocal()
        try:
            if action == "get_products":
                return {"products": self._get_products(db, params.get("filters", {}))}
            elif action == "get_product_by_id":
                prod = db.query(Product).filter_by(id=params.get("product_id")).first()
                return {"product": self._serialize_product(prod) if prod else None}
            elif action == "create_product":
                return {"product": self._create_product(db, params.get("data", {}), params.get("user_id"))}
            elif action == "update_product":
                return {"product": self._update_product(db, params.get("product_id"), params.get("data", {}))}
            elif action == "deactivate_product":
                return {"success": self._deactivate_product(db, params.get("product_id"))}
            elif action == "register_sale":
                return self._register_sale(db, params.get("sale_data", {}), params.get("user_id"))
            elif action == "get_inventory_status":
                return self._get_inventory_status(db)
            elif action == "get_daily_summary":
                return self._get_daily_summary(db, params.get("target_date"))
            elif action == "get_festivities":
                return {"festivities": self._get_festivities(db)}
            elif action == "create_festivity":
                return {"festivity": self._create_festivity(db, params.get("data", {}))}
            elif action == "get_sales_history":
                return {"history": self._get_sales_history(db, params.get("days", 30))}
            else:
                return {"error": f"Acción desconocida: {action}"}
        finally:
            db.close()

    def _serialize_product(self, p: Optional[Product]) -> Optional[Dict[str, Any]]:
        if not p:
            return None
        return {
            "id": p.id,
            "code": p.code,
            "name": p.name,
            "category": p.category,
            "description": p.description,
            "price": p.price,
            "stock_actual": p.stock_actual,
            "stock_minimo": p.stock_minimo,
            "is_active": p.is_active,
            "created_at": p.created_at.isoformat() if p.created_at else None
        }

    def _get_products(self, db: Session, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        query = db.query(Product)
        if filters.get("active_only", True):
            query = query.filter(Product.is_active.is_(True))
        if filters.get("category"):
            query = query.filter(Product.category.ilike(f"%{filters['category']}%"))
        if filters.get("search"):
            term = f"%{filters['search']}%"
            query = query.filter((Product.name.ilike(term)) | (Product.code.ilike(term)))
        
        products = query.order_by(Product.name).all()
        return [self._serialize_product(p) for p in products]

    def _create_product(self, db: Session, data: Dict[str, Any], user_id: Optional[int]) -> Dict[str, Any]:
        validate_product_data(data)
        
        code = data.get("code")
        if not code:
            # Generar código automático si no viene dado
            count = db.query(Product).count() + 1
            code = f"PROD-{count:03d}"

        product = Product(
            code=code,
            name=data["name"],
            category=data["category"],
            description=data.get("description", ""),
            price=float(data["price"]),
            stock_actual=int(data.get("stock_actual", 0)),
            stock_minimo=int(data.get("stock_minimo", 5)),
            is_active=True
        )
        db.add(product)
        db.flush()

        # Registro auditable del stock inicial (RNF08)
        if product.stock_actual > 0:
            mov = InventoryMovement(
                product_id=product.id,
                movement_type="ENTRADA",
                quantity=product.stock_actual,
                previous_stock=0,
                new_stock=product.stock_actual,
                reason="Stock inicial al crear producto",
                user_id=user_id
            )
            db.add(mov)

        db.commit()
        db.refresh(product)
        return self._serialize_product(product)

    def _update_product(self, db: Session, product_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        product = db.query(Product).filter_by(id=product_id).first()
        if not product:
            return None

        if "price" in data:
            if float(data["price"]) < 0:
                raise BusinessValidationError("El precio no puede ser negativo.")
            product.price = float(data["price"])

        if "name" in data and data["name"].strip():
            product.name = data["name"].strip()

        if "category" in data and data["category"].strip():
            product.category = data["category"].strip()

        if "stock_minimo" in data:
            product.stock_minimo = int(data["stock_minimo"])

        if "description" in data:
            product.description = data["description"]

        db.commit()
        db.refresh(product)
        return self._serialize_product(product)

    def _deactivate_product(self, db: Session, product_id: int) -> bool:
        product = db.query(Product).filter_by(id=product_id).first()
        if not product:
            return False
        product.is_active = False
        db.commit()
        return True

    def _register_sale(self, db: Session, sale_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """Registro transaccional atómico de venta con descuento de stock (RF06, RF07, RNF05, HU03)."""
        raw_items = sale_data.get("items", [])
        if not raw_items:
            raise BusinessValidationError("La venta debe contener al menos un producto.")

        # Iniciar transacción atómica
        try:
            # 1. Bloquear y validar stock de productos
            product_ids = [item["product_id"] for item in raw_items]
            products = db.query(Product).filter(Product.id.in_(product_ids)).all()
            prod_map = {p.id: p for p in products}

            if len(prod_map) != len(product_ids):
                raise BusinessValidationError("Uno o más productos solicitados no existen.")

            stock_lookup = {p.id: p.stock_actual for p in products}
            validate_sale_items(raw_items, stock_lookup)

            # 2. Generar número consecutivo de venta
            sale_count = db.query(Sale).count() + 1
            sale_num = f"VTA-{sale_count:05d}"

            total_amount = 0.0
            sale = Sale(
                sale_number=sale_num,
                user_id=user_id,
                payment_method=sale_data.get("payment_method", "EFECTIVO"),
                notes=sale_data.get("notes", ""),
                created_at=datetime.utcnow()
            )
            db.add(sale)
            db.flush()

            # 3. Procesar detalle, descontar stock y generar movimientos de inventario (RNF05, RNF08)
            processed_items = []
            for item in raw_items:
                pid = item["product_id"]
                qty = int(item["quantity"])
                prod = prod_map[pid]

                subtotal = prod.price * qty
                total_amount += subtotal

                sale_item = SaleItem(
                    sale_id=sale.id,
                    product_id=pid,
                    quantity=qty,
                    unit_price=prod.price,
                    subtotal=subtotal
                )
                db.add(sale_item)

                # Descuento atómico de stock (RF07)
                prev_stock = prod.stock_actual
                prod.stock_actual = prev_stock - qty

                # Movimiento de inventario auditable (RNF08, HU03)
                mov = InventoryMovement(
                    product_id=pid,
                    movement_type="SALIDA",
                    quantity=qty,
                    previous_stock=prev_stock,
                    new_stock=prod.stock_actual,
                    reason=f"Venta realizada #{sale.sale_number}",
                    user_id=user_id
                )
                db.add(mov)

                processed_items.append({
                    "product_id": pid,
                    "product_name": prod.name,
                    "quantity": qty,
                    "unit_price": prod.price,
                    "subtotal": subtotal,
                    "remaining_stock": prod.stock_actual
                })

            sale.total_amount = total_amount
            db.commit()
            db.refresh(sale)

            return {
                "status": "success",
                "sale_id": sale.id,
                "sale_number": sale.sale_number,
                "total_amount": total_amount,
                "items": processed_items,
                "created_at": sale.created_at.isoformat()
            }

        except Exception as e:
            db.rollback()
            raise e

    def _get_inventory_status(self, db: Session) -> Dict[str, Any]:
        """Consulta el estado del inventario e historial auditable (RF09)."""
        products = db.query(Product).filter_by(is_active=True).all()
        result_products = []
        for p in products:
            status = "NORMAL"
            if p.stock_actual == 0:
                status = "AGOTADO"
            elif p.stock_actual <= p.stock_minimo:
                status = "STOCK_BAJO"

            result_products.append({
                "id": p.id,
                "code": p.code,
                "name": p.name,
                "category": p.category,
                "stock_actual": p.stock_actual,
                "stock_minimo": p.stock_minimo,
                "price": p.price,
                "status": status
            })

        recent_movements = db.query(InventoryMovement).order_by(InventoryMovement.created_at.desc()).limit(30).all()
        serialized_movs = [
            {
                "id": m.id,
                "product_name": m.product.name if m.product else "N/A",
                "movement_type": m.movement_type,
                "quantity": m.quantity,
                "previous_stock": m.previous_stock,
                "new_stock": m.new_stock,
                "reason": m.reason,
                "created_at": m.created_at.strftime("%Y-%m-%d %H:%M") if m.created_at else ""
            }
            for m in recent_movements
        ]

        return {
            "products": result_products,
            "recent_movements": serialized_movs
        }

    def _get_daily_summary(self, db: Session, target_date_str: Optional[str] = None) -> Dict[str, Any]:
        """Genera el resumen diario con ventas, total, transacciones y más vendidos (RF08)."""
        if target_date_str:
            target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
        else:
            target_date = datetime.utcnow().date()

        start_dt = datetime.combine(target_date, datetime.min.time())
        end_dt = datetime.combine(target_date, datetime.max.time())

        sales = db.query(Sale).filter(Sale.created_at >= start_dt, Sale.created_at <= end_dt).all()
        total_amount = sum(s.total_amount for s in sales)
        total_transactions = len(sales)

        product_counts: Dict[str, Dict[str, Any]] = {}
        for s in sales:
            for item in s.items:
                pname = item.product.name if item.product else f"ID {item.product_id}"
                if pname not in product_counts:
                    product_counts[pname] = {"quantity": 0, "total_subtotal": 0.0}
                product_counts[pname]["quantity"] += item.quantity
                product_counts[pname]["total_subtotal"] += item.subtotal

        top_products = sorted(
            [{"name": k, "units_sold": v["quantity"], "revenue": v["total_subtotal"]} for k, v in product_counts.items()],
            key=lambda x: x["units_sold"],
            reverse=True
        )

        return {
            "date": target_date.strftime("%Y-%m-%d"),
            "total_sales_amount": total_amount,
            "transaction_count": total_transactions,
            "top_products": top_products[:5]
        }

    def _get_festivities(self, db: Session) -> List[Dict[str, Any]]:
        festivities = db.query(Festivity).filter_by(is_active=True).all()
        return [
            {
                "id": f.id,
                "name": f.name,
                "start_date": f.start_date,
                "end_date": f.end_date,
                "demand_factor": f.demand_factor,
                "affected_categories": f.affected_categories.split(",") if f.affected_categories else [],
                "affected_products": f.affected_products.split(",") if f.affected_products else [],
                "description": f.description
            }
            for f in festivities
        ]

    def _create_festivity(self, db: Session, data: Dict[str, Any]) -> Dict[str, Any]:
        fest = Festivity(
            name=data["name"],
            start_date=data["start_date"],
            end_date=data["end_date"],
            demand_factor=float(data.get("demand_factor", 1.5)),
            affected_categories=",".join(data.get("affected_categories", [])) if isinstance(data.get("affected_categories"), list) else data.get("affected_categories", ""),
            affected_products=",".join(data.get("affected_products", [])) if isinstance(data.get("affected_products"), list) else data.get("affected_products", ""),
            description=data.get("description", "")
        )
        db.add(fest)
        db.commit()
        db.refresh(fest)
        return {
            "id": fest.id,
            "name": fest.name,
            "start_date": fest.start_date,
            "end_date": fest.end_date,
            "demand_factor": fest.demand_factor
        }

    def _get_sales_history(self, db: Session, days: int = 30) -> List[Dict[str, Any]]:
        cutoff = datetime.utcnow() - datetime.timedelta(days=days) if hasattr(datetime, 'timedelta') else datetime.now()
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)
        items = db.query(SaleItem).join(Sale).filter(Sale.created_at >= cutoff).all()

        history = []
        for it in items:
            history.append({
                "sale_id": it.sale_id,
                "product_id": it.product_id,
                "product_name": it.product.name if it.product else "",
                "category": it.product.category if it.product else "",
                "quantity": it.quantity,
                "subtotal": it.subtotal,
                "date": it.sale.created_at.strftime("%Y-%m-%d")
            })
        return history
