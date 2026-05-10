from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.clients.weather_client import OpenMeteoClient, NasaPowerClient
from app.infrastructure.cache.climate_processor import ClimateProcessor
from app.infrastructure.repositories.cache_repository import cache_repo
from app.api.schemas.models import SeasonalPercentilesDTO, ClimatePercentilesResponseDTO, GeoPointDTO

def _to_dto(p) -> SeasonalPercentilesDTO:
    # Copia aquí la misma función _to_dto que tenías en tu propuesta
    return SeasonalPercentilesDTO(
        temp_p10_c=p.temp_p10_c, temp_p50_c=p.temp_p50_c, temp_p90_c=p.temp_p90_c,
        wind_p10_ms=p.wind_p10_ms, wind_p50_ms=p.wind_p50_ms, wind_p90_ms=p.wind_p90_ms,
        radiation_p50_wm2=p.radiation_p50_wm2, radiation_p90_wm2=p.radiation_p90_wm2,
        n_hours=p.n_hours, source=p.source, years_covered=p.years_covered
    )

async def get_climate_percentiles(
    db: AsyncSession, lat: float, lon: float, source: str = "openmeteo",
    year_start: int = 1990, year_end: int = 2023,
) -> ClimatePercentilesResponseDTO:

    # 1. Caché en BD
    cached = await cache_repo.get_climate(db, lat, lon, source)
    if cached:
        return ClimatePercentilesResponseDTO(
            source=source, point=GeoPointDTO(lat=lat, lon=lon),
            percentiles={s: _to_dto(p) for s, p in cached.items()}
        )

    # 2. Si no hay caché, llamar API externa y procesar
    years_str = f"{year_start}-{year_end}"
    if source == "nasa":
        raw = await NasaPowerClient().fetch_daily_data(lat, lon, f"{year_start}-01-01", f"{year_end}-12-31")
        percentiles = ClimateProcessor.process_nasa_data(lat, lon, years_str, raw)
    else:
        raw = await OpenMeteoClient().fetch_hourly_data(lat, lon, f"{year_start}-01-01", f"{year_end}-12-31")
        percentiles = ClimateProcessor.process_openmeteo_data(lat, lon, years_str, raw)

    # 3. Guardar en BD a través del repo y devolver
    await cache_repo.save_climate(db, percentiles)
    
    return ClimatePercentilesResponseDTO(
        source=source, point=GeoPointDTO(lat=lat, lon=lon),
        percentiles={s: _to_dto(p) for s, p in percentiles.items()}
    )