from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import AdminUser, AnyUser, CurrentUser, DbDep
from app.models.product import Product, ProductCategory
from app.schemas.product import CategoryCreate, CategoryOut, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
async def list_categories(db: DbDep, user: CurrentUser, include_inactive: bool = False):
    stmt = select(ProductCategory).order_by(ProductCategory.name)
    if not include_inactive:
        stmt = stmt.where(ProductCategory.is_active.is_(True))
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(payload: CategoryCreate, db: DbDep, user: AdminUser):
    exists = await db.execute(select(ProductCategory).where(ProductCategory.name == payload.name))
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="La categoría ya existe")
    category = ProductCategory(name=payload.name, description=payload.description)
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


@router.patch("/{category_id}", response_model=CategoryOut)
async def update_category(category_id: int, payload: CategoryUpdate, db: DbDep, user: AdminUser):
    category = await db.get(ProductCategory, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(category, key, value)
    await db.commit()
    await db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(category_id: int, db: DbDep, user: AdminUser):
    category = await db.get(ProductCategory, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    products = await db.execute(
        select(Product).options(selectinload(Product.category)).where(Product.category_id == category_id)
    )
    if products.scalars().first() is not None:
        raise HTTPException(status_code=400, detail="No se puede eliminar una categoría con productos")
    category.is_active = False
    await db.commit()