from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database import get_db
from app.api.schemas.models import ClimatePercentilesResponseDTO
from app.services import climate_service

router = APIRouter()


@router.get("/percentiles", response_model=ClimatePercentilesResponseDTO)
async def get_climate_percentiles(
    lat: float,
    lon: float,
    source: str = "openmeteo",
    year_start: int = 1990,
    year_end: int = 2023,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await climate_service.get_climate_percentiles(
            db, lat, lon, source, year_start, year_end
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
