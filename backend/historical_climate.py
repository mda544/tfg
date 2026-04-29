import httpx
import numpy as np
import asyncio
from dataclasses import dataclass
from typing import Literal

Season = Literal["verano", "otono", "invierno", "primavera"]

MESES_ESTACION: dict[Season, list[int]] = {
    "verano":    [6, 7, 8],
    "otono":     [9, 10, 11],
    "invierno":  [12, 1, 2],
    "primavera": [3, 4, 5],
}

@dataclass
class PercentilesEstacionales:
    estacion: Season
    lat: float
    lon: float
    temp_p90_c: float
    temp_p50_c: float
    temp_p10_c: float
    viento_p10_ms: float
    viento_p50_ms: float
    viento_p90_ms: float
    radiacion_p50_wm2: float
    radiacion_p90_wm2: float
    n_horas: int
    fuente: str
    anios_cubiertos: str


# ── Open-Meteo Historical ────────────────────────────────────────────────────

async def obtener_historico_openmeteo(
    lat: float,
    lon: float,
    anio_inicio: int = 1990,
    anio_fin: int = 2023,
) -> dict[Season, PercentilesEstacionales]:
    """
    Descarga datos horarios históricos desde Open-Meteo (basado en ERA5).
    Variables: temperatura 2m, viento 10m, radiación solar descendente.
    Sin registro. Sin límite de peticiones para uso no comercial.
    """
    url = "https://archive.open-meteo.com/v1/archive"
    params = {
        "latitude":            lat,
        "longitude":           lon,
        "start_date":          f"{anio_inicio}-01-01",
        "end_date":            f"{anio_fin}-12-31",
        "hourly":              "temperature_2m,wind_speed_10m,shortwave_radiation",
        "wind_speed_unit":     "ms",
        "timezone":            "UTC",
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        datos = resp.json()

    hourly = datos["hourly"]
    times        = hourly["time"]                  # "YYYY-MM-DDTHH:00"
    temps        = np.array(hourly["temperature_2m"],    dtype=float)
    vientos      = np.array(hourly["wind_speed_10m"],    dtype=float)
    radiaciones  = np.array(hourly["shortwave_radiation"], dtype=float)

    # Extraer mes de cada timestamp
    meses = np.array([int(t[5:7]) for t in times], dtype=int)

    return _calcular_percentiles_array(
        lat, lon, meses, temps, vientos, radiaciones,
        fuente="Open-Meteo Historical (ERA5)",
        anios=f"{anio_inicio}-{anio_fin}",
    )


# ── NASA POWER ───────────────────────────────────────────────────────────────

async def obtener_historico_nasa_power(
    lat: float,
    lon: float,
    anio_inicio: int = 1990,
    anio_fin: int = 2023,
) -> dict[Season, PercentilesEstacionales]:
    """
    Descarga datos diarios desde NASA POWER.
    Parámetros útiles para ampacidad:
      T2M      → temperatura a 2m (°C)
      WS10M    → viento a 10m (m/s)
      ALLSKY_SFC_SW_DWN → irradiancia horizontal global (Wh/m²/día → W/m²)
    Sin registro. Resolución ~0.5°.
    """
    url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    params = {
        "parameters":  "T2M,WS10M,ALLSKY_SFC_SW_DWN",
        "community":   "RE",
        "longitude":   lon,
        "latitude":    lat,
        "start":       f"{anio_inicio}0101",
        "end":         f"{anio_fin}1231",
        "format":      "JSON",
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        datos = resp.json()

    props = datos["properties"]["parameter"]
    t2m   = props["T2M"]      # dict "YYYYMMDD": valor
    ws10  = props["WS10M"]
    rad   = props["ALLSKY_SFC_SW_DWN"]

    # Alinear por fechas comunes
    fechas = sorted(set(t2m) & set(ws10) & set(rad))
    fechas = [f for f in fechas if t2m[f] != -999 and ws10[f] != -999]

    meses       = np.array([int(f[4:6]) for f in fechas], dtype=int)
    temps       = np.array([t2m[f]  for f in fechas], dtype=float)
    vientos     = np.array([ws10[f] for f in fechas], dtype=float)
    # NASA POWER da Wh/m²/día → convertir a W/m² promedio diario
    radiaciones = np.array([rad[f] / 24.0 for f in fechas], dtype=float)

    return _calcular_percentiles_array(
        lat, lon, meses, temps, vientos, radiaciones,
        fuente="NASA POWER (MERRA-2)",
        anios=f"{anio_inicio}-{anio_fin}",
    )


# ── Núcleo estadístico compartido ────────────────────────────────────────────

def _calcular_percentiles_array(
    lat: float,
    lon: float,
    meses: np.ndarray,
    temps: np.ndarray,
    vientos: np.ndarray,
    radiaciones: np.ndarray,
    fuente: str,
    anios: str,
) -> dict[Season, PercentilesEstacionales]:

    resultados: dict[Season, PercentilesEstacionales] = {}

    for estacion, lista_meses in MESES_ESTACION.items():
        mask = np.isin(meses, lista_meses)

        t_est   = temps[mask]
        v_est   = vientos[mask]
        r_est   = radiaciones[mask]

        # Para radiación: solo valores diurnos (> 5 W/m²)
        r_diurna = r_est[r_est > 5]

        # Limpiar NaN
        t_est    = t_est[~np.isnan(t_est)]
        v_est    = v_est[~np.isnan(v_est)]

        resultados[estacion] = PercentilesEstacionales(
            estacion=estacion,
            lat=lat,
            lon=lon,
            # Temperatura
            temp_p90_c=round(float(np.percentile(t_est, 90)), 1),
            temp_p50_c=round(float(np.percentile(t_est, 50)), 1),
            temp_p10_c=round(float(np.percentile(t_est, 10)), 1),
            # Viento — P10 es el caso restrictivo (menos enfriamiento)
            viento_p10_ms=round(float(np.percentile(v_est, 10)), 2),
            viento_p50_ms=round(float(np.percentile(v_est, 50)), 2),
            viento_p90_ms=round(float(np.percentile(v_est, 90)), 2),
            # Radiación diurna
            radiacion_p50_wm2=round(
                float(np.percentile(r_diurna, 50)) if len(r_diurna) > 0 else 0.0, 1
            ),
            radiacion_p90_wm2=round(
                float(np.percentile(r_diurna, 90)) if len(r_diurna) > 0 else 0.0, 1
            ),
            n_horas=int(len(t_est)),
            fuente=fuente,
            anios_cubiertos=anios,
        )

    return resultados