"""
Clientes para APIs meteorológicas externas.

Open-Meteo Archive: datos horarios ERA5 (temperatura, viento, radiación)
NASA POWER:         datos diarios MERRA-2 (mismas variables)

Ambos usan el cliente HTTP compartido con connection pooling,
reintentos automáticos con backoff exponencial y excepciones tipadas.
"""

import asyncio
import httpx

from app.infrastructure.clients.http_client import get_client
from app.core.config import settings


class ExternalAPIError(Exception):
    """Error al llamar a una API externa."""
    def __init__(self, service: str, status_code: int | None, message: str):
        self.service     = service
        self.status_code = status_code
        super().__init__(f"[{service}] {message} (HTTP {status_code})")


class ExternalAPIUnavailableError(ExternalAPIError):
    """La API está caída o rate-limited — reintentable."""
    pass


class ExternalAPIClientError(ExternalAPIError):
    """Error en los parámetros enviados — no reintentable."""
    pass


async def _request_with_retry(
    service:     str,
    url:         str,
    params:      dict,
    max_retries: int   = 3,
    retry_delay: float = 2.0,
) -> dict:
    """
    Petición GET con reintentos en errores transitorios.
    Reintenta en: timeout, 429 (rate limit), 503 (servicio caído).
    No reintenta en: 400, 401, 403, 404 (error del cliente).
    Backoff exponencial: 2s → 4s → 8s entre intentos.
    """
    client     = get_client()
    last_error: Exception | None = None

    for attempt in range(max_retries):
        try:
            resp = await client.get(url, params=params)

            if resp.status_code == 200:
                return resp.json()

            if 400 <= resp.status_code < 500 and resp.status_code != 429:
                raise ExternalAPIClientError(
                    service     = service,
                    status_code = resp.status_code,
                    message     = f"Bad request: {resp.text[:200]}",
                )

            last_error = ExternalAPIUnavailableError(
                service     = service,
                status_code = resp.status_code,
                message     = f"Service unavailable: {resp.text[:200]}",
            )

        except httpx.TimeoutException:
            last_error = ExternalAPIUnavailableError(
                service     = service,
                status_code = None,
                message     = f"Timeout after {settings.openmeteo_timeout}s",
            )
        except httpx.NetworkError as e:
            last_error = ExternalAPIUnavailableError(
                service     = service,
                status_code = None,
                message     = f"Network error: {e}",
            )

        if attempt < max_retries - 1:
            wait = retry_delay * (2 ** attempt)  # 2s, 4s, 8s
            print(f"[{service}] Attempt {attempt + 1} failed, retrying in {wait}s...")
            await asyncio.sleep(wait)

    raise last_error


class OpenMeteoClient:
    """
    Cliente para Open-Meteo Archive API (ERA5 reanalysis).
    Cobertura: global, 1940-presente, resolución 0.25°
    Límites: gratuito sin API key, ~10k req/día
    """

    BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

    async def fetch_hourly_data(
        self,
        lat:        float,
        lon:        float,
        start_date: str,
        end_date:   str,
    ) -> dict:
        """
        Datos horarios de temperatura, viento y radiación.
        Fechas formato: "YYYY-MM-DD"
        """
        return await _request_with_retry(
            service = "Open-Meteo Archive",
            url     = self.BASE_URL,
            params  = {
                "latitude":        lat,
                "longitude":       lon,
                "start_date":      start_date,
                "end_date":        end_date,
                "hourly":          "temperature_2m,wind_speed_10m,shortwave_radiation",
                "wind_speed_unit": "ms",
                "timezone":        "UTC",
            },
        )


class NasaPowerClient:
    """
    Cliente para NASA POWER API (MERRA-2 reanalysis).
    Cobertura: global, 1981-presente, resolución 0.5°
    Nota: devuelve datos diarios en MJ/m²/día para radiación
    """

    BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

    async def fetch_daily_data(
        self,
        lat:        float,
        lon:        float,
        start_date: str,
        end_date:   str,
    ) -> dict:
        """
        Datos diarios de temperatura, viento y radiación.
        Fechas formato: "YYYY-MM-DD" (se convierte a "YYYYMMDD" internamente)
        """
        return await _request_with_retry(
            service = "NASA POWER",
            url     = self.BASE_URL,
            params  = {
                "parameters": "T2M,WS10M,ALLSKY_SFC_SW_DWN",
                "community":  "RE",
                "longitude":  lon,
                "latitude":   lat,
                "start":      start_date.replace("-", ""),
                "end":        end_date.replace("-", ""),
                "format":     "JSON",
            },
        )