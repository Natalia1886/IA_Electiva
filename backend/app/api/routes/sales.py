from datetime import date

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy.orm import selectinload

from app.api.deps import AnyUser, DbDep
from app.models.sale import Sale, SaleItem
from app.models.user import User
from app.schemas.sale import DailySummary, SaleCreate, SaleItemOut, SaleOut
from app.services import daily_summary_service, sales_service

router = APIRouter(prefix="/sales", tags=["sales"])


@router.post("", response_model=SaleOut, status_code=status.HTTP_201_CREATED)
async def register_sale(payload: SaleCreate, db: DbDep, user: AnyUser):
    """Create a sale and return its full representation.

    The sale header, detail lines, stock deduction, inventory movement log and
    sale number are committed as a single atomic transaction.  Insufficient
    stock for any line item rejects the entire sale and nothing is persisted.
    """
    sale = await sales_service.create_sale(db, payload, user)
    return _serialize_sale(await sales_service.fetch_sale(db, sale.id))


@router.get("", response_model=list[SaleOut])
async def list_sales(
    db: DbDep,
    user: AnyUser,
    date_from: date | None = None,
    date_to: date | None = None,
    salesperson_id: int | None = None,
    source: str | None = None,
    limit: int = Query(default=200, le=500),
):
    # Salespeople can only see their OWN sales; the filter is pinned to themselves
    # regardless of the value sent, so they cannot enumerate other users' sales.
    if user.role == "salesperson":
        salesperson_id = user.id
    sales = await sales_service.list_sales(db, date_from, date_to, salesperson_id, source, limit)
    return [_serialize_sale(s) for s in sales]


@router.get("/daily/{target_date}", response_model=DailySummary)
async def daily_summary(target_date: date, db: DbDep, user: AnyUser):
    return await daily_summary_service.daily_summary(db, target_date)


@router.get("/{sale_id}", response_model=SaleOut)
async def get_sale(sale_id: int, db: DbDep, user: AnyUser):
    sale = await sales_service.fetch_sale(db, sale_id)
    if sale is None:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    return _serialize_sale(sale)


def _serialize_sale(sale: Sale) -> SaleOut:
    out = SaleOut.model_validate(sale)
    out.item_count = len(sale.items)
    out.salesperson_name = None
    out.items = [
        SaleItemOut(
            id=item.id,
            product_id=item.product_id,
            product_name=item.product.name if item.product else None,
            product_code=item.product.code if item.product else None,
            quantity=item.quantity,
            unit_price=float(item.unit_price),
            subtotal=float(item.subtotal),
        )
        for item in sale.items
    ]
    return out