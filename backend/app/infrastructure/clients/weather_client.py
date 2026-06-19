from app.infrastructure.clients.base_client import _request_with_retry
from app.core.config import settings


class OpenMeteoClient:
    """Implementa IWeatherClient con datos horarios ERA5 (Open-Meteo Archive)."""

    async def fetch_period(
        self,
        lat: float,
        lon: float,
        start_date: str,
        end_date: str,
    ) -> dict:
        # Fechas formato: "YYYY-MM-DD"
        return await _request_with_retry(
            service="Open-Meteo Archive",
            url=settings.openmeteo_url,
            params={
                "latitude": lat,
                "longitude": lon,
                "start_date": start_date,
                "end_date": end_date,
                "hourly": "temperature_2m,wind_speed_10m,"
                "wind_direction_10m,shortwave_radiation",
                "wind_speed_unit": "ms",
                "timezone": "UTC",
            },
        )


class NasaPowerClient:
    """Implementa IWeatherClient con datos diarios MERRA-2 (NASA POWER).
    wind_dir_predominant_deg quedará a None, esta fuente no la proporciona."""

    async def fetch_period(
        self,
        lat: float,
        lon: float,
        start_date: str,
        end_date: str,
    ) -> dict:
        # Fechas formato: "YYYY-MM-DD" (se convierte a "YYYYMMDD" internamente)
        return await _request_with_retry(
            service="NASA POWER",
            url=settings.nasa_power_url,
            params={
                "parameters": "T2M,WS10M,ALLSKY_SFC_SW_DWN",
                "community": "RE",
                "longitude": lon,
                "latitude": lat,
                "start": start_date.replace("-", ""),
                "end": end_date.replace("-", ""),
                "format": "JSON",
            },
        )
