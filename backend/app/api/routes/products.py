from fastapi import APIRouter, status

from app.api.deps import AdminUser, AnyUser, DbDep
from app.schemas.product import ProductCreate, ProductOut, ProductUpdate
from app.services import products_service

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductOut])
async def list_products(
    db: DbDep,
    user: AnyUser,
    category_id: int | None = None,
    search: str | None = None,
    low_stock: bool = False,
    include_inactive: bool = False,
    holiday_id: int | None = None,
):
    return await products_service.list_products(
        db,
        category_id=category_id,
        search=search,
        low_stock=low_stock,
        include_inactive=include_inactive,
        holiday_id=holiday_id,
    )


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(product_id: int, db: DbDep, user: AnyUser):
    return await products_service.get_product(db, product_id)


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def create_product(payload: ProductCreate, db: DbDep, user: AdminUser):
    return await products_service.create_product(db, payload)


@router.patch("/{product_id}", response_model=ProductOut)
async def update_product(product_id: int, payload: ProductUpdate, db: DbDep, user: AdminUser):
    return await products_service.update_product(db, product_id, payload)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_product(product_id: int, db: DbDep, user: AdminUser):
    await products_service.deactivate_product(db, product_id)


@router.post("/{product_id}/reactivate", response_model=ProductOut)
async def reactivate_product(product_id: int, db: DbDep, user: AdminUser):
    return await products_service.reactivate_product(db, product_id)