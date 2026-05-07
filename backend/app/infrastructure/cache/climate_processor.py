import numpy as np
from dataclasses import dataclass

from app.domain.types import Season


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


class ClimateProcessor:
    @staticmethod
    def process_openmeteo_data(
        lat: float, lon: float, anios: str, raw_data: dict
    ) -> dict[Season, PercentilesEstacionales]:
        hourly      = raw_data["hourly"]
        times       = hourly["time"]
        temps       = np.array(hourly["temperature_2m"],    dtype=float)
        vientos     = np.array(hourly["wind_speed_10m"],    dtype=float)
        radiaciones = np.array(hourly["shortwave_radiation"], dtype=float)
        meses       = np.array([int(t[5:7]) for t in times], dtype=int)

        return ClimateProcessor._calcular_percentiles_array(
            lat, lon, meses, temps, vientos, radiaciones,
            fuente="Open-Meteo Historical (ERA5)",
            anios=anios,
        )

    @staticmethod
    def process_nasa_data(
        lat: float, lon: float, anios: str, raw_data: dict
    ) -> dict[Season, PercentilesEstacionales]:
        props = raw_data["properties"]["parameter"]
        t2m   = props["T2M"]
        ws10  = props["WS10M"]
        rad   = props["ALLSKY_SFC_SW_DWN"]

        fechas    = sorted(set(t2m) & set(ws10) & set(rad))
        fechas    = [f for f in fechas if t2m[f] != -999 and ws10[f] != -999]
        meses     = np.array([int(f[4:6]) for f in fechas], dtype=int)
        temps     = np.array([t2m[f]  for f in fechas], dtype=float)
        vientos   = np.array([ws10[f] for f in fechas], dtype=float)
        radiaciones = np.array([(rad[f] * 1000.0) / 12.0 for f in fechas], dtype=float)

        return ClimateProcessor._calcular_percentiles_array(
            lat, lon, meses, temps, vientos, radiaciones,
            fuente="NASA POWER (MERRA-2)",
            anios=anios,
        )

    @staticmethod
    def _calcular_percentiles_array(
        lat: float, lon: float,
        meses: np.ndarray, temps: np.ndarray,
        vientos: np.ndarray, radiaciones: np.ndarray,
        fuente: str, anios: str,
    ) -> dict[Season, PercentilesEstacionales]:
        resultados: dict[Season, PercentilesEstacionales] = {}

        for estacion, lista_meses in MESES_ESTACION.items():
            mask    = np.isin(meses, lista_meses)
            t_est   = temps[mask][~np.isnan(temps[mask])]
            v_est   = vientos[mask][~np.isnan(vientos[mask])]
            r_est   = radiaciones[mask]
            r_diurna = r_est[r_est > 5]

            resultados[estacion] = PercentilesEstacionales(
                estacion=estacion,
                lat=lat,
                lon=lon,
                temp_p90_c         = round(float(np.percentile(t_est, 90)), 1),
                temp_p50_c         = round(float(np.percentile(t_est, 50)), 1),
                temp_p10_c         = round(float(np.percentile(t_est, 10)), 1),
                viento_p10_ms      = round(float(np.percentile(v_est, 10)), 2),
                viento_p50_ms      = round(float(np.percentile(v_est, 50)), 2),
                viento_p90_ms      = round(float(np.percentile(v_est, 90)), 2),
                radiacion_p50_wm2  = round(float(np.percentile(r_diurna, 50)) if len(r_diurna) > 0 else 0.0, 1),
                radiacion_p90_wm2  = round(float(np.percentile(r_diurna, 90)) if len(r_diurna) > 0 else 0.0, 1),
                n_horas            = int(len(t_est)),
                fuente             = fuente,
                anios_cubiertos    = anios,
            )
        return resultados