from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound
from fastapi import HTTPException

from app.infrastructure.repositories.lines_repository import lines_repo
from app.infrastructure.mappers.lines_mapper import create_dto_to_entity, entity_to_dto
from app.services.elevation_service import add_elevation
from app.api.schemas.models import LineCreateDTO, LineResponseDTO


async def get_all(db: AsyncSession, user_id: str) -> list[LineResponseDTO]:
    return [entity_to_dto(e) for e in await lines_repo.get_all(db, user_id)]


async def get_by_id(db: AsyncSession, line_id: str, user_id: str) -> LineResponseDTO:
    try:
        return entity_to_dto(await lines_repo.get_by_id(db, line_id, user_id))
    except NoResultFound:
        raise HTTPException(404, detail=f"Line {line_id} not found.")


async def create(
    db: AsyncSession, data: LineCreateDTO, user_id: str
) -> LineResponseDTO:
    entity = create_dto_to_entity(data)
    line = await lines_repo.create(db, user_id, entity)

    try:
        coordinates = [{"lat": c.lat, "lon": c.lon} for c in line.coordinates]
        enriched = await add_elevation(db, coordinates)
        elevations = [c.get("elevation", 0.0) or 0.0 for c in enriched]
        line = await lines_repo.enrich_with_elevation(
            db,
            line.id,
            user_id,
            min_elev=round(min(elevations), 1),
            max_elev=round(max(elevations), 1),
            avg_elev=round(sum(elevations) / len(elevations), 1),
        )
    except Exception as e:
        print(f"[DEM] Line enrichment failed: {e}")

    return entity_to_dto(line)


async def update(
    db: AsyncSession, line_id: str, data: LineCreateDTO, user_id: str
) -> LineResponseDTO:
    try:
        entity = create_dto_to_entity(data)
        return entity_to_dto(await lines_repo.update(db, line_id, user_id, entity))
    except NoResultFound:
        raise HTTPException(404, detail=f"Line {line_id} not found.")


async def delete(db: AsyncSession, line_id: str, user_id: str) -> None:
    if not await lines_repo.delete(db, line_id, user_id):
        raise HTTPException(404, detail=f"Line {line_id} not found.")
