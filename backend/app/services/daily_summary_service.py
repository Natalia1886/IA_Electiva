from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.core.stock_status import compute_stock_status
from app.database import async_session_factory
from app.models.product import Product
from app.models.sale import Sale, SaleItem
from app.models.user import User


async def daily_summary(db, target: date) -> dict:
    stmt = (
        select(SaleItem, Sale.total, Product)
        .join(Sale, Sale.id == SaleItem.sale_id)
        .join(Product, Product.id == SaleItem.product_id)
        .where(Sale.sale_date == target, Sale.status == "completed")
    )
    rows = (await db.execute(stmt)).all()

    total_value = sum(float(sale_total) for _, sale_total, _ in rows)
    transactions = {item.sale_id for item, _, _ in rows}
    per_product: dict[int, dict] = {}

    for item, _, product in rows:
        units = item.quantity
        value = float(item.subtotal)
        entry = per_product.setdefault(
            product.id,
            {"product_id": product.id, "code": product.code, "name": product.name, "units_sold": 0, "total_value": 0.0},
        )
        entry["units_sold"] += units
        entry["total_value"] += value

    items = sorted(per_product.values(), key=lambda p: (-p["units_sold"], -p["total_value"]))
    return {
        "date": target,
        "total_value": round(total_value, 2),
        "transaction_count": len(transactions),
        "units_sold": sum(i["units_sold"] for i in items),
        "products_count": len(items),
        "items": items,
        "top_products": items[:5],
    }


async def sales_trend(db, days: int = 7) -> list[dict]:
    start = date.today() - timedelta(days=days - 1)
    rows = await db.execute(
        select(Sale.sale_date, func.coalesce(func.sum(Sale.total), 0).label("total"), func.count(Sale.id).label("n"))
        .where(Sale.sale_date >= start, Sale.status == "completed")
        .group_by(Sale.sale_date)
        .order_by(Sale.sale_date)
    )
    lookup = {d: (float(t), n) for d, t, n in rows.all()}
    trend = []
    for offset in range(days):
        d = start + timedelta(days=offset)
        total, n = lookup.get(d, (0.0, 0))
        trend.append({"date": d.isoformat(), "total": round(total, 2), "transactions": n})
    return trend


async def top_products(db, days: int = 30, limit: int = 5) -> list[dict]:
    start = date.today() - timedelta(days=days)
    rows = await db.execute(
        select(
            Product.id,
            Product.code,
            Product.name,
            func.sum(SaleItem.quantity).label("units"),
            func.sum(SaleItem.subtotal).label("value"),
        )
        .select_from(Sale)
        .join(SaleItem, SaleItem.sale_id == Sale.id)
        .join(Product, Product.id == SaleItem.product_id)
        .where(Sale.sale_date >= start, Sale.status == "completed")
        .group_by(Product.id, Product.code, Product.name)
        .order_by(func.sum(SaleItem.quantity).desc())
        .limit(limit)
    )
    return [
        {"product_id": pid, "code": code, "name": name, "units_sold": int(units), "total_value": round(float(value), 2)}
        for pid, code, name, units, value in rows.all()
    ]


async def inventory_stock_position(db) -> dict:
    products = (
        (await db.execute(
            select(Product).options(selectinload(Product.category)).where(Product.is_active.is_(True))
        ))
        .scalars()
        .all()
    )
    total_units = sum(p.stock for p in products)
    stock_value = round(sum(p.stock * (float(p.cost) if p.cost is not None else float(p.price)) for p in products), 2)
    low = [
        {
            "product_id": p.id,
            "code": p.code,
            "name": p.name,
            "category_name": p.category.name if p.category else None,
            "stock": p.stock,
            "min_stock": p.min_stock,
            "stock_status": compute_stock_status(p.stock, p.min_stock),
            "low_stock": compute_stock_status(p.stock, p.min_stock) == "low",
            "out_of_stock": p.stock == 0,
            "missing_units": max(0, p.min_stock - p.stock),
        }
        for p in products
        if p.stock <= p.min_stock
    ]
    return {
        "total_units": total_units,
        "total_products": len(products),
        "products_low": len(low),
        "stock_value": stock_value,
        "low_stock": low,
    }


async def get_dashboard(db) -> dict:
    today = date.today()
    position = await inventory_stock_position(db)
    return {
        "today": today,
        "today_sales_value": (await daily_summary(db, today))["total_value"],
        "today_transactions": (await daily_summary(db, today))["transaction_count"],
        "today_units": (await daily_summary(db, today))["units_sold"],
        "week_trend": await sales_trend(db, 7),
        "top_products_30d": await top_products(db, 30, 5),
        "low_stock_products": position["low_stock"],
        "total_products": position["total_products"],
        "total_stock_value": position["stock_value"],
    }