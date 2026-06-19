from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_climate_repo
from app.api.schemas.models import ClimatePercentilesResponseDTO
from app.domain.repository_interfaces import IClimateRepository
from app.domain.client_interfaces import IWeatherClient
from app.infrastructure.clients.weather_client import OpenMeteoClient, NasaPowerClient
from app.services import climate_service

router = APIRouter()


def _get_weather_client(source: str) -> IWeatherClient:
    return NasaPowerClient() if source == "nasa" else OpenMeteoClient()


@router.get("/percentiles", response_model=ClimatePercentilesResponseDTO)
async def get_climate_percentiles(
    lat: float,
    lon: float,
    source: str = "openmeteo",
    year_start: int = 1990,
    year_end: int = 2023,
    db: AsyncSession = Depends(get_db),
    repo: IClimateRepository = Depends(get_climate_repo),
):
    client = _get_weather_client(source)
    return await climate_service.get_climate_percentiles(
        db, lat, lon, repo, client, source, year_start, year_end
    )
