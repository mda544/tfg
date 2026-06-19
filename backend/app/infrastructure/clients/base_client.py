"""
Lógica HTTP compartida entre todos los clientes a servicios externos
(clima, elevación)."""

import asyncio
import httpx

from app.infrastructure.clients.http_client import get_client
from app.core.config import settings


class ExternalAPIError(Exception):
    """Error al llamar a una API externa."""

    def __init__(self, service: str, status_code: int | None, message: str):
        self.service = service
        self.status_code = status_code
        super().__init__(f"[{service}] {message} (HTTP {status_code})")


class ExternalAPIUnavailableError(ExternalAPIError):
    """La API está caída o rate-limited (reintentable)."""

    pass


class ExternalAPIClientError(ExternalAPIError):
    """Error en los parámetros enviados (no reintentable)."""

    pass


async def _request_with_retry(
    service: str,
    url: str,
    params: dict,
    max_retries: int = 3,
    retry_delay: float = 2.0,
) -> dict:
    """Reintenta con backoff exponencial (2s, 4s, 8s) ante fallos
    recuperables (timeout, error de red, 5xx, 429). No reintenta errores
    4xx distintos de 429 — esos son errores del cliente, no del servicio."""

    client = get_client()
    last_error: Exception | None = None

    for attempt in range(max_retries):
        try:
            resp = await client.get(url, params=params)

            if resp.status_code == 200:
                return resp.json()

            if 400 <= resp.status_code < 500 and resp.status_code != 429:
                raise ExternalAPIClientError(
                    service=service,
                    status_code=resp.status_code,
                    message=f"Bad request: {resp.text[:200]}",
                )

            last_error = ExternalAPIUnavailableError(
                service=service,
                status_code=resp.status_code,
                message=f"Service unavailable: {resp.text[:200]}",
            )

        except httpx.TimeoutException:
            last_error = ExternalAPIUnavailableError(
                service=service,
                status_code=None,
                message=f"Timeout after {settings.openmeteo_timeout}s",
            )
        except httpx.NetworkError as e:
            last_error = ExternalAPIUnavailableError(
                service=service,
                status_code=None,
                message=f"Network error: {e}",
            )

        if attempt < max_retries - 1:
            wait = retry_delay * (2**attempt)  # 2s, 4s, 8s
            print(f"[{service}] Attempt {attempt + 1} failed, retrying in {wait}s...")
            await asyncio.sleep(wait)

    raise last_error
