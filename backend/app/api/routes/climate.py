from fastapi import APIRouter, HTTPException
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
):
    try:
        return await climate_service.get_climate_percentiles(
            lat, lon, source, year_start, year_end
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))