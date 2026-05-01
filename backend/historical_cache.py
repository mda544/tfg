import json
import hashlib
from pathlib import Path
from dataclasses import asdict
from historical_climate import (
    obtener_historico_openmeteo,
    obtener_historico_nasa_power,
)
from services.climate_processor import (
    PercentilesEstacionales, Season,
)

CACHE_DIR = Path("climate_cache")
CACHE_DIR.mkdir(exist_ok=True)

Fuente = "openmeteo"  # o "nasa"

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
        percentiles = await obtener_historico_nasa_power(lat, lon, anio_inicio, anio_fin)
    else:
        percentiles = await obtener_historico_openmeteo(lat, lon, anio_inicio, anio_fin)

    ruta.write_text(json.dumps(
        {est: asdict(p) for est, p in percentiles.items()},
        indent=2,
    ))

    return percentiles