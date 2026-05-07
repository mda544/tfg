"""
Caché en disco y orquestación de datos climáticos históricos.
Fusiona historical_cache.py + historical_climate.py originales.
"""

import json
import hashlib
from dataclasses import asdict
from pathlib import Path

from app.infrastructure.clients.weather_client import OpenMeteoClient, NasaPowerClient
from app.infrastructure.cache.climate_processor import ClimateProcessor, PercentilesEstacionales
from app.domain.types import Season

BASE_DIR  = Path(__file__).resolve().parents[3]   # /backend
CACHE_DIR = BASE_DIR / "climate_cache"
CACHE_DIR.mkdir(exist_ok=True)


def _ruta_cache(lat: float, lon: float, fuente: str) -> Path:
    # Redondear a 0.25° — resolución de ERA5/Open-Meteo
    lat_r = round(round(lat * 4) / 4, 2)
    lon_r = round(round(lon * 4) / 4, 2)
    clave = hashlib.md5(f"{lat_r}_{lon_r}_{fuente}".encode()).hexdigest()[:12]
    return CACHE_DIR / f"{clave}.json"


async def obtener_percentiles(
    lat: float,
    lon: float,
    fuente: str = "openmeteo",
    anio_inicio: int = 1990,
    anio_fin: int = 2023,
) -> dict[Season, PercentilesEstacionales]:
    ruta = _ruta_cache(lat, lon, fuente)

    if ruta.exists():
        datos = json.loads(ruta.read_text())
        return {est: PercentilesEstacionales(**v) for est, v in datos.items()}

    if fuente == "nasa":
        percentiles = await _obtener_nasa(lat, lon, anio_inicio, anio_fin)
    else:
        percentiles = await _obtener_openmeteo(lat, lon, anio_inicio, anio_fin)

    ruta.write_text(json.dumps(
        {est: asdict(p) for est, p in percentiles.items()},
        indent=2,
    ))
    return percentiles


async def _obtener_openmeteo(
    lat: float, lon: float, anio_inicio: int, anio_fin: int
) -> dict[Season, PercentilesEstacionales]:
    client   = OpenMeteoClient()
    raw_data = await client.fetch_hourly_data(lat, lon, f"{anio_inicio}-01-01", f"{anio_fin}-12-31")
    return ClimateProcessor.process_openmeteo_data(lat, lon, f"{anio_inicio}-{anio_fin}", raw_data)


async def _obtener_nasa(
    lat: float, lon: float, anio_inicio: int, anio_fin: int
) -> dict[Season, PercentilesEstacionales]:
    client   = NasaPowerClient()
    raw_data = await client.fetch_daily_data(lat, lon, f"{anio_inicio}-01-01", f"{anio_fin}-12-31")
    return ClimateProcessor.process_nasa_data(lat, lon, f"{anio_inicio}-{anio_fin}", raw_data)