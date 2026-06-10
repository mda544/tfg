import numpy as np
from app.domain.types import Season
from app.domain.entities import SeasonalPercentiles
from app.domain.geo import circular_mean

SEASON_MONTHS: dict[Season, list[int]] = {
    "verano": [6, 7, 8],
    "otono": [9, 10, 11],
    "invierno": [12, 1, 2],
    "primavera": [3, 4, 5],
}


class ClimateProcessor:

    @staticmethod
    def process_openmeteo_data(
        lat: float, lon: float, years: str, raw_data: dict
    ) -> dict[Season, SeasonalPercentiles]:
        hourly = raw_data["hourly"]
        times = hourly["time"]
        temps = np.array(hourly["temperature_2m"], dtype=float)
        winds = np.array(hourly["wind_speed_10m"], dtype=float)
        radiation = np.array(hourly["shortwave_radiation"], dtype=float)
        months = np.array([int(t[5:7]) for t in times], dtype=int)

        wind_dirs = np.array(
            hourly.get("wind_direction_10m", []),
            dtype=float,
        )

        return ClimateProcessor._compute_percentiles(
            lat,
            lon,
            months,
            temps,
            winds,
            wind_dirs,
            radiation,
            source="Open-Meteo Historical (ERA5)",
            years=years,
        )

    @staticmethod
    def process_nasa_data(
        lat: float, lon: float, years: str, raw_data: dict
    ) -> dict[Season, SeasonalPercentiles]:
        props = raw_data["properties"]["parameter"]
        t2m = props["T2M"]
        ws10 = props["WS10M"]
        rad = props["ALLSKY_SFC_SW_DWN"]

        dates = sorted(set(t2m) & set(ws10) & set(rad))
        dates = [d for d in dates if t2m[d] != -999 and ws10[d] != -999]
        months = np.array([int(d[4:6]) for d in dates], dtype=int)
        temps = np.array([t2m[d] for d in dates], dtype=float)
        winds = np.array([ws10[d] for d in dates], dtype=float)
        radiation = np.array([(rad[d] * 1000.0) / 12.0 for d in dates], dtype=float)

        # NASA POWER diario no incluye dirección del viento — array vacío
        wind_dirs = np.array([], dtype=float)

        return ClimateProcessor._compute_percentiles(
            lat,
            lon,
            months,
            temps,
            winds,
            wind_dirs,
            radiation,
            source="NASA POWER (MERRA-2)",
            years=years,
        )

    @staticmethod
    def _compute_percentiles(
        lat: float,
        lon: float,
        months: np.ndarray,
        temps: np.ndarray,
        winds: np.ndarray,
        wind_dirs: np.ndarray,
        radiation: np.ndarray,
        source: str,
        years: str,
    ) -> dict[Season, SeasonalPercentiles]:
        results: dict[Season, SeasonalPercentiles] = {}
        has_wind_dirs = len(wind_dirs) == len(temps)

        for season, season_months in SEASON_MONTHS.items():
            mask = np.isin(months, season_months)
            t_season = temps[mask][~np.isnan(temps[mask])]
            w_season = winds[mask][~np.isnan(winds[mask])]
            r_season = radiation[mask]
            r_daytime = r_season[r_season > 5]

            if has_wind_dirs:
                wd_season = wind_dirs[mask]
                wd_season = wd_season[~np.isnan(wd_season)]
                wind_dir_predominant = circular_mean(wd_season)
            else:
                wind_dir_predominant = None

            results[season] = SeasonalPercentiles(
                season=season,
                lat=lat,
                lon=lon,
                temp_p90_c=round(float(np.percentile(t_season, 90)), 1),
                temp_p50_c=round(float(np.percentile(t_season, 50)), 1),
                temp_p10_c=round(float(np.percentile(t_season, 10)), 1),
                wind_p10_ms=round(float(np.percentile(w_season, 10)), 2),
                wind_p50_ms=round(float(np.percentile(w_season, 50)), 2),
                wind_p90_ms=round(float(np.percentile(w_season, 90)), 2),
                wind_dir_predominant_deg=wind_dir_predominant,
                radiation_p50_wm2=round(
                    float(np.percentile(r_daytime, 50)) if len(r_daytime) > 0 else 0.0,
                    1,
                ),
                radiation_p90_wm2=round(
                    float(np.percentile(r_daytime, 90)) if len(r_daytime) > 0 else 0.0,
                    1,
                ),
                n_hours=int(len(t_season)),
                source=source,
                years_covered=years,
            )

        return results
