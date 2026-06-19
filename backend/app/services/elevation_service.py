import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.repository_interfaces import IElevationRepository
from app.infrastructure.clients.elevation_client import (
    fetch_openmeteo_elevation,
    fetch_opentopodata_elevation,
)
from app.infrastructure.repositories.elevation_repository import (
    elevation_repo as _elevation_repo,
)
from app.infrastructure.mappers.elevation_mapper import build_elevation_dto
from app.api.schemas.models import ElevationResponseDTO


async def add_elevation(
    db: AsyncSession,
    coordinates: list[dict],
    repo: IElevationRepository = _elevation_repo,
) -> list[dict]:

    n = len(coordinates)
    elevations = [0.0] * n
    pending_idx: list[int] = []
    pending_pts: list[tuple[float, float]] = []

    for i, c in enumerate(coordinates):
        existing = c.get("elevation_m")
        if existing is not None and float(existing) > 0:
            elevations[i] = float(existing)
            continue

        lat, lon = c["lat"], c["lon"]
        cached = await repo.get_elevation(db, lat, lon)
        if cached is not None:
            elevations[i] = cached
            continue

        pending_idx.append(i)
        pending_pts.append((lat, lon))

    if not pending_pts:
        return [{**c, "elevation_m": e} for c, e in zip(coordinates, elevations)]

    batch = await fetch_openmeteo_elevation(pending_pts)

    if len(batch) != len(pending_pts):
        print(
            f"[DEM] Warning: expected {len(pending_pts)} results, got {len(batch)} — padding with None"
        )
        batch = batch + [None] * (len(pending_pts) - len(batch))

    still_pending: list[tuple[int, tuple[float, float]]] = []

    for j, (idx, elev) in enumerate(zip(pending_idx, batch)):
        if elev is not None:
            elevations[idx] = elev
            await repo.create_elevation(db, pending_pts[j][0], pending_pts[j][1], elev)
        else:
            still_pending.append((idx, pending_pts[j]))

    if still_pending:
        tasks = [
            fetch_opentopodata_elevation(lat, lon) for _, (lat, lon) in still_pending
        ]
        fallbacks = await asyncio.gather(*tasks)
        for (idx, (lat, lon)), elev in zip(still_pending, fallbacks):
            elevations[idx] = elev or 0.0
            if elev:
                await repo.create_elevation(db, lat, lon, elev)

    return [{**c, "elevation_m": e} for c, e in zip(coordinates, elevations)]


async def get_elevation(
    db: AsyncSession,
    lat: float,
    lon: float,
    repo: IElevationRepository = _elevation_repo,
) -> ElevationResponseDTO:
    result = await add_elevation(db, [{"lat": lat, "lon": lon}], repo)
    return build_elevation_dto(lat, lon, result[0].get("elevation_m", 0.0))
