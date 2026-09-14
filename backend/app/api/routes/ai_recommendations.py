from fastapi import APIRouter

from app.api.deps import AdminUser, DbDep
from app.schemas.reports import RecommendationOut
from app.services.ai import recommendations as rec_service

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/recommendations", response_model=RecommendationOut)
@router.get("/recomendaciones", response_model=RecommendationOut)
async def recommendations(db: DbDep, user: AdminUser):
    data = await rec_service.generate_recommendations(db)
    return data