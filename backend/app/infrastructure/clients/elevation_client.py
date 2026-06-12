import asyncio
from typing import Optional

from app.infrastructure.clients.weather_client import (
    _request_with_retry,
    ExternalAPIUnavailableError,
)
from app.core.config import settings

# Valor 1 = solo una petición simultánea + 1.1s de espera entre llamadas.
_OPENTOPODATA_SEMAPHORE = asyncio.Semaphore(1)


# Obtiene elevaciones en batch desde Open-Meteo Elevation API. None para puntos fallidos
async def fetch_openmeteo_elevation(
    points: list[tuple[float, float]],
) -> list[Optional[float]]:
    if not points:
        return []

    results: list[Optional[float]] = []
    for i in range(0, len(points), 100):
        chunk = points[i : i + 100]
        try:
            data = await _request_with_retry(
                service="Open-Meteo Elevation",
                url=settings.openmeteo_elevation_url,
                params={
                    "latitude": ",".join(f"{p[0]:.6f}" for p in chunk),
                    "longitude": ",".join(f"{p[1]:.6f}" for p in chunk),
                },
            )
            elevations = data.get("elevation", [])
            results.extend(float(e) if e is not None else None for e in elevations)
        except ExternalAPIUnavailableError as e:
            print(f"[DEM] Batch {i} failed: {e}")
            results.extend([None] * len(chunk))

    return results


# Fallback usando Open-Topo-Data SRTM30m.
async def fetch_opentopodata_elevation(lat: float, lon: float) -> Optional[float]:
    async with _OPENTOPODATA_SEMAPHORE:
        try:
            data = await _request_with_retry(
                service="Open-Topo-Data",
                url=settings.opentopodata_url,
                params={"locations": f"{lat:.6f},{lon:.6f}"},
                max_retries=2,
            )
            res = data.get("results", [])
            return float(res[0].get("elevation") or 0) if res else None
        except Exception as e:
            print(f"[DEM] Fallback failed for ({lat:.4f}, {lon:.4f}): {e}")
            return None
        finally:
            await asyncio.sleep(1.1)
