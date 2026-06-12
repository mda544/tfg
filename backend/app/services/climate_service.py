from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.climate_processor import ClimateProcessor
from app.domain.exceptions import ExternalServiceError
from app.infrastructure.clients.weather_client import OpenMeteoClient, NasaPowerClient
from app.infrastructure.repositories.climate_repository import climate_repo
from app.infrastructure.mappers.climate_mapper import build_climate_dto
from app.core.config import settings
from app.api.schemas.models import ClimatePercentilesResponseDTO


async def get_climate_percentiles(
    db: AsyncSession,
    lat: float,
    lon: float,
    source: str = "openmeteo",
    year_start: int = settings.year_start_default,
    year_end: int = settings.year_end_default,
) -> ClimatePercentilesResponseDTO:

    cached = await climate_repo.get_climate(db, lat, lon, source)
    if cached:
        return build_climate_dto(lat, lon, source, cached)

    years_str = f"{year_start}-{year_end}"
    date_start = f"{year_start}-01-01"
    date_end = f"{year_end}-12-31"

    try:
        if source == "nasa":
            raw = await NasaPowerClient().fetch_daily_data(
                lat, lon, date_start, date_end
            )
            percentiles = ClimateProcessor.process_nasa_data(lat, lon, years_str, raw)
        else:
            raw = await OpenMeteoClient().fetch_hourly_data(
                lat, lon, date_start, date_end
            )
            percentiles = ClimateProcessor.process_openmeteo_data(
                lat, lon, years_str, raw
            )
    except ExternalServiceError:
        raise
    except Exception as e:
        source_name = "NASA POWER" if source == "nasa" else "ERA5 (Open-Meteo)"
        raise ExternalServiceError(f"Error consultando {source_name}: {e}")

    await climate_repo.create_climate(db, percentiles)
    return build_climate_dto(lat, lon, source, percentiles)
