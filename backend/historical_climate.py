from clients.weather_clients import OpenMeteoClient, NasaPowerClient
from services.climate_processor import ClimateProcessor, Season, PercentilesEstacionales

async def obtener_historico_openmeteo(
    lat: float, lon: float, anio_inicio: int = 1990, anio_fin: int = 2023
) -> dict[Season, PercentilesEstacionales]:
    """Obtiene datos crudos de Open-Meteo y los procesa estadísticamente."""
    client = OpenMeteoClient()
    raw_data = await client.fetch_hourly_data(
        lat, lon, f"{anio_inicio}-01-01", f"{anio_fin}-12-31"
    )
    
    return ClimateProcessor.process_openmeteo_data(
        lat, lon, f"{anio_inicio}-{anio_fin}", raw_data
    )

async def obtener_historico_nasa_power(
    lat: float, lon: float, anio_inicio: int = 1990, anio_fin: int = 2023
) -> dict[Season, PercentilesEstacionales]:
    """Obtiene datos crudos de la NASA y los procesa estadísticamente."""
    client = NasaPowerClient()
    raw_data = await client.fetch_daily_data(
        lat, lon, f"{anio_inicio}-01-01", f"{anio_fin}-12-31"
    )
    
    return ClimateProcessor.process_nasa_data(
        lat, lon, f"{anio_inicio}-{anio_fin}", raw_data
    )