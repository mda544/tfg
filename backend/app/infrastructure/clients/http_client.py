import httpx
from app.core.config import settings

_client: httpx.AsyncClient | None = None


async def startup() -> None:
    global _client
    _client = httpx.AsyncClient(
        timeout=httpx.Timeout(
            connect=10.0,
            read=float(settings.openmeteo_timeout),
            write=10.0,
            pool=5.0,
        ),
        limits=httpx.Limits(
            max_connections=20,
            max_keepalive_connections=10,
        ),
    )


async def shutdown() -> None:
    global _client
    if _client:
        await _client.aclose()
        _client = None


def get_client() -> httpx.AsyncClient:
    if _client is None:
        raise RuntimeError("HTTP client not initialized. Call startup() first.")
    return _client
