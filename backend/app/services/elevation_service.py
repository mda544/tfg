import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.clients.elevation_client import fetch_openmeteo_elevation, fetch_opentopodata_elevation
from app.infrastructure.repositories.elevation_repository import elevation_repo
from app.api.schemas.models import ElevationResponseDTO


async def add_elevation(db: AsyncSession, coordinates: list[dict]) -> list[dict]:
    n          = len(coordinates)
    elevations = [0.0] * n
    pending_idx: list[int]               = []
    pending_pts: list[tuple[float, float]] = []

    # Revisar db y excel
    for i, c in enumerate(coordinates):
        existing = c.get("altitud") or c.get("elevation")
        if existing and float(existing) > 0:
            elevations[i] = float(existing)
            continue

        lat, lon = c["lat"], c["lon"]
        cached = await elevation_repo.get_elevation(db, lat, lon)
        if cached is not None:
            elevations[i] = cached
            continue

        pending_idx.append(i)
        pending_pts.append((lat, lon))

    if not pending_pts:
        return [{**c, "elevation": e} for c, e in zip(coordinates, elevations)]

    # Open-Meteo Elevation
    batch        = await fetch_openmeteo_elevation(pending_pts)
    still_pending: list[tuple[int, tuple[float, float]]] = []

    for j, (idx, elev) in enumerate(zip(pending_idx, batch)):
        if elev is not None:
            elevations[idx] = elev
            await elevation_repo.save_elevation(db, pending_pts[j][0], pending_pts[j][1], elev)
        else:
            still_pending.append((idx, pending_pts[j]))

    # En caso de error en alguna de las respuestas.
    if still_pending:
        tasks     = [fetch_opentopodata_elevation(lat, lon) for _, (lat, lon) in still_pending]
        fallbacks = await asyncio.gather(*tasks)
        for (idx, (lat, lon)), elev in zip(still_pending, fallbacks):
            elevations[idx] = elev or 0.0
            if elev:
                await elevation_repo.save_elevation(db, lat, lon, elev)

    return [{**c, "elevation": e} for c, e in zip(coordinates, elevations)]


async def get_elevation(db: AsyncSession, lat: float, lon: float) -> ElevationResponseDTO:
    result = await add_elevation(db, [{"lat": lat, "lon": lon}])
    return ElevationResponseDTO(lat=lat, lon=lon, elevation_m=result[0].get("elevation", 0))