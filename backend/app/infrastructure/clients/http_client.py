"""
Cliente HTTP compartido para todas las llamadas a APIs externas.
Se inicializa en el lifespan de FastAPI y se cierra al apagar.
Reutiliza conexiones (connection pooling) en lugar de crear
un AsyncClient nuevo en cada petición.
"""

import httpx
from app.core.config import settings

_client: httpx.AsyncClient | None = None


async def startup() -> None:
    """Inicializar el cliente HTTP compartido al arrancar la aplicación."""
    global _client
    _client = httpx.AsyncClient(
        timeout=httpx.Timeout(
            connect = 10.0,
            read    = float(settings.openmeteo_timeout),
            write   = 10.0,
            pool    = 5.0,
        ),
        limits=httpx.Limits(
            max_connections          = 20,
            max_keepalive_connections = 10,
        ),
    )


async def shutdown() -> None:
    """Cerrar el cliente HTTP al apagar la aplicación."""
    global _client
    if _client:
        await _client.aclose()
        _client = None


def get_client() -> httpx.AsyncClient:
    if _client is None:
        raise RuntimeError("HTTP client not initialized. Call startup() first.")
    return _client