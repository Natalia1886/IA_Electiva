"""Script de siembra inicial de datos para la tienda de artículos religiosos.
Incluye usuarios por rol, productos religiosos, festividades locales (Ibagué/Semana Santa)
y ventas históricas para alimentar el modelo de IA.
"""

from datetime import datetime, timedelta
import random
from core.database.connection import SessionLocal, init_db
from core.database.models import User, Product, Sale, SaleItem, InventoryMovement, Festivity
from core.security.auth import hash_password


def seed_database():
    """Siembra datos iniciales completos en la base de datos."""
    init_db()
    db = SessionLocal()

    try:
        # 1. Usuarios (HU01)
        if db.query(User).count() == 0:
            admin_user = User(
                username="admin",
                password_hash=hash_password("admin123"),
                full_name="Administrador Tienda",
                role="ADMIN"
            )
            seller_user = User(
                username="vendedor1",
                password_hash=hash_password("vendedor123"),
                full_name="Natalia Vendedora",
                role="VENDEDOR"
            )
            db.add_all([admin_user, seller_user])
            db.commit()
            print("[OK] Usuarios sembrados (admin, vendedor1)")

        admin = db.query(User).filter_by(username="admin").first()
        vendedor = db.query(User).filter_by(username="vendedor1").first()

        # 2. Festividades religiosas (RF10, HU06)
        if db.query(Festivity).count() == 0:
            today = datetime.now()
            # Semana Santa configurada como próxima para probar recomendaciones inmediatas
            semana_santa_start = (today + timedelta(days=15)).strftime("%Y-%m-%d")
            semana_santa_end = (today + timedelta(days=22)).strftime("%Y-%m-%d")

            festivities_data = [
                Festivity(
                    name="Semana Santa",
                    start_date=semana_santa_start,
                    end_date=semana_santa_end,
                    demand_factor=2.5,
                    affected_categories="Velas,Crucifijos,Imágenes Religiosas",
                    affected_products="Vela Religiosa Blanca,Vela Cirio Pascual Grande,Crucifijo de Pared Madera y Metal",
                    description="Celebración litúrgica mayor: incremento masivo en velas blancas, cirios y crucifijos."
                ),
                Festivity(
                    name="Fiestas de Ibagué (San Juan y San Pedro)",
                    start_date=f"{today.year}-06-20",
                    end_date=f"{today.year}-07-02",
                    demand_factor=1.8,
                    affected_categories="Velas,Santos,Accesorios",
                    affected_products="Vela Religiosa Blanca,Figura San Cayetano 25cm",
                    description="Festividades folclóricas de Ibagué con gran afluencia de feligreses y turistas."
                ),
                Festivity(
                    name="Día de la Virgen del Carmen",
                    start_date=f"{today.year}-07-10",
                    end_date=f"{today.year}-07-17",
                    demand_factor=2.2,
                    affected_categories="Vírgenes,Velas",
                    affected_products="Velón Virgen del Carmen,Estatua Virgen de Guadalupe 30cm",
                    description="Patrona de los conductores y celebración muy concurrida en el Tolima."
                ),
                Festivity(
                    name="Fiesta Patronal San Cayetano",
                    start_date=f"{today.year}-08-01",
                    end_date=f"{today.year}-08-08",
                    demand_factor=2.0,
                    affected_categories="Santos,Velas",
                    affected_products="Figura San Cayetano 25cm,Vela Religiosa Blanca",
                    description="Patrono del pan y del trabajo, alta devoción popular."
                ),
                Festivity(
                    name="Navidad y Temporada de Pesebres",
                    start_date=f"{today.year}-12-01",
                    end_date=f"{today.year}-12-25",
                    demand_factor=3.0,
                    affected_categories="Pesebres,Velas",
                    affected_products="Pesebre Tradicional 11 Piezas,Vela Religiosa Blanca",
                    description="Novena de aguinaldos y armado de pesebres familiares."
                ),
            ]
            db.add_all(festivities_data)
            db.commit()
            print("[OK] Festividades religiosas sembradas")

        # 3. Productos religiosos (RF03, RF04, HU02, HU05)
        if db.query(Product).count() == 0:
            products_data = [
                Product(
                    code="VEL-001",
                    name="Vela Religiosa Blanca",
                    category="Velas",
                    description="Vela blanca parafina pura de 15cm para oración y peticiones",
                    price=3500.0,
                    stock_actual=8,      # Menor a stock_minimo (10) -> Stock Bajo (HU05)
                    stock_minimo=10
                ),
                Product(
                    code="VEL-002",
                    name="Velón Virgen del Carmen",
                    category="Velas",
                    description="Velón en vaso de vidrio con estampa bendecida",
                    price=12000.0,
                    stock_actual=0,      # Agotado (HU05)
                    stock_minimo=5
                ),
                Product(
                    code="VEL-003",
                    name="Vela Cirio Pascual Grande",
                    category="Velas",
                    description="Cirio con cruz y símbolos litúrgicos del año",
                    price=25000.0,
                    stock_actual=3,      # Menor a stock_minimo (10) -> Stock Bajo para Semana Santa
                    stock_minimo=10
                ),
                Product(
                    code="IMG-001",
                    name="Estatua Virgen de Guadalupe 30cm",
                    category="Imágenes Religiosas",
                    description="Imagen en resina pintada a mano con detalles dorados",
                    price=45000.0,
                    stock_actual=14,
                    stock_minimo=5
                ),
                Product(
                    code="IMG-002",
                    name="Figura San Cayetano 25cm",
                    category="Santos",
                    description="Patrono de la providencia, imagen con espigas y el Niño Jesús",
                    price=38000.0,
                    stock_actual=4,      # Menor a stock_minimo (6) -> Stock Bajo
                    stock_minimo=6
                ),
                Product(
                    code="IMG-003",
                    name="Divino Niño Jesús Resina 20cm",
                    category="Imágenes Religiosas",
                    description="Imagen tradicional con brazos abiertos",
                    price=32000.0,
                    stock_actual=15,
                    stock_minimo=4
                ),
                Product(
                    code="PES-001",
                    name="Pesebre Tradicional 11 Piezas",
                    category="Pesebres",
                    description="Misterio completo con Reyes Magos, animales y pastor",
                    price=85000.0,
                    stock_actual=18,     # Producto con acumulación fuera de temporada (Hallazgo 2)
                    stock_minimo=4
                ),
                Product(
                    code="CRU-001",
                    name="Crucifijo de Pared Madera y Metal",
                    category="Crucifijos",
                    description="Cruz en cedro con cuerpo de Cristo en aleación zamak",
                    price=28000.0,
                    stock_actual=7,      # Próximo a agotarse en festividad
                    stock_minimo=6
                ),
                Product(
                    code="ACC-001",
                    name="Rosario Madera de Olivo",
                    category="Accesorios",
                    description="Rosario engarzado a mano con aroma natural",
                    price=15000.0,
                    stock_actual=25,
                    stock_minimo=8
                ),
                Product(
                    code="ACC-002",
                    name="Medalla Milagrosa Plata Italiana",
                    category="Accesorios",
                    description="Medalla devocional con cordón",
                    price=9000.0,
                    stock_actual=20,
                    stock_minimo=5
                ),
            ]
            db.add_all(products_data)
            db.commit()

            # Registrar movimientos iniciales de inventario (RF09, RNF08)
            for prod in products_data:
                mov = InventoryMovement(
                    product_id=prod.id,
                    movement_type="ENTRADA",
                    quantity=prod.stock_actual,
                    previous_stock=0,
                    new_stock=prod.stock_actual,
                    reason="Inventario inicial de apertura",
                    user_id=admin.id
                )
                db.add(mov)
            db.commit()
            print("[OK] Productos religiosos e inventario inicial sembrados")

        # 4. Historial de ventas para que el modelo ML de segmentación y recomendación funcione (RF06, RF11)
        if db.query(Sale).count() == 0:
            products = db.query(Product).all()
            prod_dict = {p.code: p for p in products}

            sales_to_create = []
            now = datetime.now()

            # Simulamos 30 días de ventas históricas
            # Las velas se venden casi a diario (alta frecuencia)
            # Pesebres pocas ventas en últimos días (baja rotación)
            for day_offset in range(30, 0, -1):
                sale_time = now - timedelta(days=day_offset, hours=random.randint(1, 8))
                seller = random.choice([admin, vendedor])

                items_in_sale = []
                total = 0.0

                # Vela Blanca vendida frecuentemente
                if "VEL-001" in prod_dict and random.random() > 0.2:
                    p = prod_dict["VEL-001"]
                    q = random.randint(2, 6)
                    sub = p.price * q
                    items_in_sale.append((p, q, sub))
                    total += sub

                # Velón Virgen del Carmen vendida recurrentemente hasta agotarse
                if "VEL-002" in prod_dict and day_offset > 5 and random.random() > 0.4:
                    p = prod_dict["VEL-002"]
                    q = random.randint(1, 3)
                    sub = p.price * q
                    items_in_sale.append((p, q, sub))
                    total += sub

                # Santos vendidos con frecuencia media
                if "IMG-002" in prod_dict and random.random() > 0.5:
                    p = prod_dict["IMG-002"]
                    q = 1
                    sub = p.price * q
                    items_in_sale.append((p, q, sub))
                    total += sub

                # Crucifijos
                if "CRU-001" in prod_dict and random.random() > 0.6:
                    p = prod_dict["CRU-001"]
                    q = random.randint(1, 2)
                    sub = p.price * q
                    items_in_sale.append((p, q, sub))
                    total += sub

                # Rosarios
                if "ACC-001" in prod_dict and random.random() > 0.5:
                    p = prod_dict["ACC-001"]
                    q = random.randint(1, 2)
                    sub = p.price * q
                    items_in_sale.append((p, q, sub))
                    total += sub

                if items_in_sale:
                    sale = Sale(
                        sale_number=f"VTA-HIST-{day_offset:03d}",
                        user_id=seller.id,
                        total_amount=total,
                        payment_method=random.choice(["EFECTIVO", "NEQUI", "DAVIPLATA"]),
                        notes="Venta histórica registrada",
                        created_at=sale_time
                    )
                    db.add(sale)
                    db.flush()

                    for p, q, sub in items_in_sale:
                        s_item = SaleItem(
                            sale_id=sale.id,
                            product_id=p.id,
                            quantity=q,
                            unit_price=p.price,
                            subtotal=sub
                        )
                        db.add(s_item)

            db.commit()
            print("[OK] Historial de ventas simulado sembrado exitosamente")

    except Exception as e:
        db.rollback()
        print(f"Error sembrando datos: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
