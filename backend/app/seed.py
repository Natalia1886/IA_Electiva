"""Database seeder — creates the schema and demo data for the Milan MVP.

Run from backend/ with:  python -m app.seed
"""
import asyncio
import random
from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy import select

from app.core.security import hash_password
from app.database import Base, async_session_factory, engine
from app.models.holiday import ReligiousHoliday
from app.models.product import Product, ProductCategory
from app.models.user import User, UserRole
from app.services import sales_service
from app.services.ai import holiday_engine

random.seed(42)


class _Item:
    def __init__(self, product_id, quantity):
        self.product_id = product_id
        self.quantity = quantity
        self.unit_price = None


class SalePayload:
    def __init__(self, sale_date, items, payment_method="cash"):
        self.sale_date = sale_date
        self.items = items
        self.payment_method = payment_method
        self.digitization_id = None  # seeded sales are always manual
        self.note = None


async def seed() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as db:
        if (await db.execute(select(User))).scalars().first():
            print("→ La base ya tiene datos; no se vuelve a sembrar.")
            return

        admin = User(
            username="admin",
            email="admin@example.com",
            full_name="Administrador Milan",
            hashed_password=hash_password("admin123"),
            role=UserRole.admin.value,
        )
        seller = User(
            username="vendedor",
            email="vendedor@example.com",
            full_name="Vendedor Milan",
            hashed_password=hash_password("vendedor123"),
            role=UserRole.salesperson.value,
        )
        db.add_all([admin, seller])

        cats = {
            "img": ProductCategory(name="Imágenes religiosas", description="Vírgenes, santos y cuadros"),
            "velas": ProductCategory(name="Velas", description="Velas, cirios y veladoras"),
            "naci": ProductCategory(name="Nacimientos", description="Nacimientos y figuras"),
            "rosa": ProductCategory(name="Rosarios", description="Rosarios y accesorios"),
            "gral": ProductCategory(name="Artículos varios", description="Otros artículos religiosos"),
        }
        db.add_all(cats.values())
        await db.flush()

        holidays = {
            "guadalupe": ReligiousHoliday(name="Día de la Virgen de Guadalupe", day=12, month=12,
                                          expected_demand_factor=2.5,
                                          description="11-12 de diciembre. Alta demanda de veladoras e imágenes."),
            "navidad": ReligiousHoliday(name="Navidad", day=25, month=12,
                                        expected_demand_factor=1.8,
                                        description="Temporada de nacimientos y velas decorativas."),
            "candelaria": ReligiousHoliday(name="Candelaria", day=2, month=2,
                                           expected_demand_factor=1.5,
                                           description="Presentación del Niño Dios, 2 de febrero."),
            "semanasanta": ReligiousHoliday(name="Semana Santa", day=1, month=4, variable_date_code="easter",
                                            expected_demand_factor=2.0,
                                            description="Fecha variable (cálculo de Pascua). Alta demanda de velas."),
            "corpus": ReligiousHoliday(name="Corpus Christi", day=1, month=6, variable_date_code="corpus_christi",
                                       expected_demand_factor=1.5,
                                       description="Variable. Procesiones y velas."),
            "dmuertos": ReligiousHoliday(name="Día de los Muertos", day=2, month=11,
                                         expected_demand_factor=2.0,
                                         description="Veladoras y recuerdos."),
            "sjudas": ReligiousHoliday(name="San Judas Tadeo", day=28, month=10,
                                       expected_demand_factor=2.0,
                                       description="Devoción popular; veladoras e imágenes."),
        }
        db.add_all(holidays.values())
        await db.flush()

        products_data = [
            ("VIR-001", "Virgen de Guadalupe 20 cm", 350000.0, 160000.0, 18, 6, "img", ["guadalupe"]),
            ("VIR-002", "Virgen de Guadalupe 40 cm", 650000.0, 300000.0, 9, 4, "img", ["guadalupe"]),
            ("VIR-003", "Nuestra Señora del Rosario 25 cm", 420000.0, 195000.0, 12, 4, "img", []),
            ("SAN-001", "San Judas Tadeo 20 cm", 380000.0, 175000.0, 14, 5, "img", ["sjudas"]),
            ("SAN-002", "San Martín de Porres 15 cm", 300000.0, 140000.0, 8, 3, "img", []),
            ("VEL-001", "Veladora Virgen de Guadalupe", 45000.0, 18000.0, 60, 30, "velas", ["guadalupe", "dmuertos"]),
            ("VEL-002", "Cirio pascual 30 cm", 85000.0, 38000.0, 40, 20, "velas", ["semanasanta", "corpus"]),
            ("VEL-003", "Vela votiva blanca", 25000.0, 9000.0, 120, 60, "velas", []),
            ("VEL-004", "Veladora San Judas Tadeo", 50000.0, 20000.0, 22, 15, "velas", ["sjudas"]),
            ("NAC-001", "Nacimiento 10 piezas 30 cm", 1450000.0, 700000.0, 5, 3, "naci", ["navidad"]),
            ("NAC-002", "Figura Niño Dios bendición", 220000.0, 90000.0, 18, 6, "naci", ["candelaria", "navidad"]),
            ("ROS-001", "Rosario de madera", 95000.0, 40000.0, 50, 25, "rosa", []),
            ("ROS-002", "Rosario de plata", 380000.0, 180000.0, 15, 8, "rosa", []),
            ("GRA-001", "Estampa San Judas", 8000.0, 2000.0, 200, 100, "gral", ["sjudas"]),
        ]
        products = {}
        for code, name, price, cost, stock, min_stock, cat_key, hkeys in products_data:
            p = Product(
                code=code, name=name, price=price, cost=cost, stock=1000, min_stock=min_stock,
                category_id=cats[cat_key].id,
            )
            p.holidays = [holidays[h] for h in hkeys]
            db.add(p)
            products[code] = p
        await db.flush()

        sold_volume = {
            "VIR-001": 3, "VIR-002": 1, "VIR-003": 2, "SAN-001": 2, "SAN-002": 1,
            "VEL-001": 6, "VEL-002": 5, "VEL-003": 8, "VEL-004": 3,
            "NAC-001": 1, "NAC-002": 2, "ROS-001": 4, "ROS-002": 1, "GRA-001": 5,
        }
        weights = [code for code, w in sold_volume.items() for _ in range(w)]

        today = date.today()

        # Demand bursts around the previous occurrence of each upcoming feast,
        # so the historical data really shows religious-date correlation
        # (the segmentation model feeds on that feature).
        holiday_codes: dict[str, list[str]] = defaultdict(list)
        for code, *_names, hkeys in [list(p) for p in products_data]:
            for h in hkeys:
                holiday_codes[h].append(code)

        boost: dict[date, dict[str, float]] = defaultdict(dict)
        history_start = today - timedelta(days=430)
        for hkey, codes in holiday_codes.items():
            prev = holiday_engine.next_occurrence(holidays[hkey], history_start)
            if history_start <= prev < today:
                for offset in range(1, 13):  # 12 days before the feast
                    burst_day = prev - timedelta(days=offset)
                    for code in codes:
                        boost[burst_day][code] = max(boost[burst_day].get(code, 0.0), 8.0)

        for day_offset in range(400, 0, -1):
            sale_date = today - timedelta(days=day_offset)
            day_weights = list(weights)
            for code, mult in boost.get(sale_date, {}).items():
                day_weights.extend([code] * int(mult * 10))
            for _ in range(random.randint(0, 5)):
                num_items = random.randint(1, 3)
                chosen: dict[str, int] = {}
                for _ in range(num_items):
                    code = random.choice(day_weights)
                    chosen[code] = chosen.get(code, 0) + random.randint(1, 3)
                payload = SalePayload(
                    sale_date,
                    [_Item(products[code].id, qty) for code, qty in chosen.items()],
                    payment_method=random.choice(["cash", "cash", "cash", "card", "transfer"]),
                )
                await sales_service.create_sale(db, payload, seller if random.random() < 0.8 else admin)

        final_stock = {code: stock for code, name, price, cost, stock, min_stock, cat_key, hkeys in products_data}
        for code, stock in final_stock.items():
            products[code].stock = stock
        for code in ["VEL-004", "SAN-001"]:
            products[code].stock = 3
        await db.commit()

        print("✓ Base sembrada correctamente.")
        print("  Usuarios:")
        print("   · admin / admin123  (Administrador)")
        print("   · vendedor / vendedor123  (Vendedor)")


if __name__ == "__main__":
    asyncio.run(seed())