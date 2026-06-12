from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.api.schemas.models import ElevationResponseDTO
from app.services import elevation_service

router = APIRouter()


@router.get("/", response_model=ElevationResponseDTO)
async def get_elevation(
    lat: float,
    lon: float,
    db: AsyncSession = Depends(get_db),
):
    return await elevation_service.get_elevation(db, lat, lon)
