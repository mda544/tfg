from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.clients.weather_client import OpenMeteoClient, NasaPowerClient
from app.infrastructure.cache.climate_processor import ClimateProcessor
from app.infrastructure.repositories.climate_repository import climate_repo
from app.api.schemas.models import SeasonalPercentilesDTO, ClimatePercentilesResponseDTO, GeoPointDTO

def _to_dto(p) -> SeasonalPercentilesDTO:
    return SeasonalPercentilesDTO(
        temp_p10_c=p.temp_p10_c, temp_p50_c=p.temp_p50_c, temp_p90_c=p.temp_p90_c,
        wind_p10_ms=p.wind_p10_ms, wind_p50_ms=p.wind_p50_ms, wind_p90_ms=p.wind_p90_ms,
        radiation_p50_wm2=p.radiation_p50_wm2, radiation_p90_wm2=p.radiation_p90_wm2,
        n_hours=p.n_hours, source=p.source, years_covered=p.years_covered
    )

SOURCE_NAMES = {
    "openmeteo": "Open-Meteo Historical (ERA5)",
    "nasa":      "NASA POWER (MERRA-2)",
}

async def get_climate_percentiles(
    db: AsyncSession, lat: float, lon: float, source: str = "openmeteo",
    year_start: int = 1990, year_end: int = 2023,
) -> ClimatePercentilesResponseDTO:

    # Redondear a 1 decimal para la caché
    lat_r = round(lat, 1)
    lon_r = round(lon, 1)
    source_db  = SOURCE_NAMES.get(source, source)

    # Caché en BD — buscar con coordenadas redondeadas
    cached = await climate_repo.get_climate(db, lat_r, lon_r, source_db)
    if cached:
        print(f"[Climate] CACHE HIT — llama a bd {source} lat={lat_r} lon={lon_r}"),
        return ClimatePercentilesResponseDTO(
            source=source, point=GeoPointDTO(lat=lat, lon=lon),  # se devolvuelven las originales
            percentiles={s: _to_dto(p) for s, p in cached.items()}
        )
    
    print(f"[Climate] CACHE MISS — no llama bd {source} lat={lat_r} lon={lon_r}")

    # Llamar API con coordenadas redondeadas
    years_str = f"{year_start}-{year_end}"
    if source == "nasa":
        raw = await NasaPowerClient().fetch_daily_data(lat_r, lon_r, f"{year_start}-01-01", f"{year_end}-12-31")
        percentiles = ClimateProcessor.process_nasa_data(lat_r, lon_r, years_str, raw)
    else:
        raw = await OpenMeteoClient().fetch_hourly_data(lat_r, lon_r, f"{year_start}-01-01", f"{year_end}-12-31")
        percentiles = ClimateProcessor.process_openmeteo_data(lat_r, lon_r, years_str, raw)

    # Guardar y devolver
    await climate_repo.save_climate(db, percentiles)

    return ClimatePercentilesResponseDTO(
        source=source, point=GeoPointDTO(lat=lat, lon=lon),
        percentiles={s: _to_dto(p) for s, p in percentiles.items()}
    )