from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound
from fastapi import HTTPException

from app.infrastructure.repositories.lines_repository import lines_repo, geometry_to_geojson
from app.infrastructure.orm_models import LineORM, UserORM
from app.api.schemas.models import LineCreateDTO, LineResponseDTO


def _to_dto(obj: LineORM) -> LineResponseDTO:
    return LineResponseDTO(
        id               = obj.id,
        name             = obj.name,
        description      = obj.description,
        length_km        = obj.length_km,
        geometry_geojson = geometry_to_geojson(obj),
        created_at       = obj.created_at.isoformat(),
        updated_at       = obj.updated_at.isoformat(),
    )


async def get_all(db: AsyncSession, user: UserORM) -> list[LineResponseDTO]:
    return [_to_dto(o) for o in await lines_repo.get_all(db, user.id)]


async def get_by_id(db: AsyncSession, line_id: str, user: UserORM) -> LineResponseDTO:
    try:
        return _to_dto(await lines_repo.get_by_id(db, line_id, user.id))
    except NoResultFound:
        raise HTTPException(404, detail=f"Line {line_id} not found.")


async def create(db: AsyncSession, data: LineCreateDTO, user: UserORM) -> LineResponseDTO:
    return _to_dto(await lines_repo.create(db, user.id, data))


async def update(
    db: AsyncSession, line_id: str, data: LineCreateDTO, user: UserORM
) -> LineResponseDTO:
    try:
        return _to_dto(await lines_repo.update(db, line_id, user.id, data))
    except NoResultFound:
        raise HTTPException(404, detail=f"Line {line_id} not found.")


async def delete(db: AsyncSession, line_id: str, user: UserORM) -> None:
    deleted = await lines_repo.delete(db, line_id, user.id)
    if not deleted:
        raise HTTPException(404, detail=f"Line {line_id} not found.")