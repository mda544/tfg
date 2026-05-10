import asyncio
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.clients.weather_client import _request_with_retry, ExternalAPIUnavailableError
from app.infrastructure.repositories.cache_repository import cache_repo
from app.api.schemas.models import ElevationResponseDTO

# 1. Semáforo con el nombre correcto
_OPENTOPODATA_SEMAPHORE = asyncio.Semaphore(1)

async def _fetch_openmeteo_elevation_batch(
    points: list[tuple[float, float]]
) -> list[Optional[float]]:
    if not points:
        return []

    results: list[Optional[float]] = []
    for i in range(0, len(points), 100):
        chunk = points[i:i + 100]
        try:
            data = await _request_with_retry(
                service = "Open-Meteo Elevation",
                url     = "https://api.open-meteo.com/v1/elevation",
                params  = {
                    "latitude":  ",".join(f"{p[0]:.6f}" for p in chunk),
                    "longitude": ",".join(f"{p[1]:.6f}" for p in chunk),
                },
            )
            elevations = data.get("elevation", [])
            results.extend(float(e) if e is not None else None for e in elevations)
        except ExternalAPIUnavailableError as e:
            print(f"[DEM] Batch {i} failed: {e}")
            results.extend([None] * len(chunk))

    return results

async def _fetch_opentopodata_fallback(
    lat: float, lon: float
) -> Optional[float]:
    # 2. Ahora sí encuentra el semáforo
    async with _OPENTOPODATA_SEMAPHORE:
        try:
            data = await _request_with_retry(
                service     = "Open-Topo-Data",
                url         = "https://api.opentopodata.org/v1/srtm30m",
                params      = {"locations": f"{lat:.6f},{lon:.6f}"},
                max_retries = 2,
            )
            res = data.get("results", [])
            return float(res[0].get("elevation") or 0) if res else None
        except Exception as e:
            print(f"[DEM] Fallback failed for ({lat:.4f}, {lon:.4f}): {e}")
            return None
        finally:
            await asyncio.sleep(1.1)

async def enrich_with_elevation(db: AsyncSession, coordinates: list[dict]) -> list[dict]:
    n = len(coordinates)
    elevations = [0.0] * n
    pending_idx = []
    pending_pts = []

    for i, c in enumerate(coordinates):
        existing = c.get("altitud") or c.get("elevation")
        if existing and float(existing) > 0:
            elevations[i] = float(existing)
            continue

        lat, lon = c["lat"], c["lon"]
        cached = await cache_repo.get_elevation(db, lat, lon)
        if cached is not None:
            elevations[i] = cached
            continue

        pending_idx.append(i)
        pending_pts.append((lat, lon))

    if not pending_pts:
        return [{**c, "elevation": e} for c, e in zip(coordinates, elevations)]

    # 3. Llamada con el nombre correcto de la función
    batch = await _fetch_openmeteo_elevation_batch(pending_pts)
    still_pending = []
    
    for j, (idx, elev) in enumerate(zip(pending_idx, batch)):
        if elev is not None:
            elevations[idx] = elev
            await cache_repo.save_elevation(db, pending_pts[j][0], pending_pts[j][1], elev)
        else:
            still_pending.append((idx, pending_pts[j]))

    if still_pending:
        # 4. Llamada con el nombre correcto de la función
        tasks = [_fetch_opentopodata_fallback(lat, lon) for _, (lat, lon) in still_pending]
        fallbacks = await asyncio.gather(*tasks)
        for (idx, (lat, lon)), elev in zip(still_pending, fallbacks):
            elevations[idx] = elev or 0.0
            if elev:
                await cache_repo.save_elevation(db, lat, lon, elev)

    return [{**c, "elevation": e} for c, e in zip(coordinates, elevations)]

async def get_elevation(db: AsyncSession, lat: float, lon: float) -> ElevationResponseDTO:
    result = await enrich_with_elevation(db, [{"lat": lat, "lon": lon}])
    return ElevationResponseDTO(lat=lat, lon=lon, elevation_m=result[0].get("elevation", 0))