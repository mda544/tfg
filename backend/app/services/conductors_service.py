from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound
from fastapi import HTTPException

from app.infrastructure.repositories.conductors_repository import conductors_repo
from app.infrastructure.mappers.conductors_mapper import (
    create_dto_to_entity,
    entity_to_dto,
)
from app.api.schemas.models import ConductorCreateDTO, ConductorResponseDTO


async def get_all(db: AsyncSession, user_id: str) -> list[ConductorResponseDTO]:
    return [entity_to_dto(e) for e in await conductors_repo.get_all(db, user_id)]


async def get_by_id(
    db: AsyncSession, conductor_id: str, user_id: str
) -> ConductorResponseDTO:
    try:
        return entity_to_dto(await conductors_repo.get_by_id(db, conductor_id, user_id))
    except NoResultFound:
        raise HTTPException(404, detail=f"Conductor {conductor_id} not found.")


async def create(
    db: AsyncSession, data: ConductorCreateDTO, user_id: str
) -> ConductorResponseDTO:
    return entity_to_dto(
        await conductors_repo.create(db, user_id, create_dto_to_entity(data))
    )


async def update(
    db: AsyncSession, conductor_id: str, data: ConductorCreateDTO, user_id: str
) -> ConductorResponseDTO:
    try:
        return entity_to_dto(
            await conductors_repo.update(
                db, conductor_id, user_id, create_dto_to_entity(data)
            )
        )
    except NoResultFound:
        raise HTTPException(404, detail=f"Conductor {conductor_id} not found.")


async def delete(db: AsyncSession, conductor_id: str, user_id: str) -> None:
    if not await conductors_repo.delete(db, conductor_id, user_id):
        raise HTTPException(404, detail=f"Conductor {conductor_id} not found.")
