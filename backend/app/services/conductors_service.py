from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound

from app.domain.exceptions import EntityNotFoundError
from app.domain.repository_interfaces import IConductorsRepository
from app.infrastructure.mappers.conductors_mapper import (
    create_dto_to_entity,
    entity_to_dto,
)
from app.api.schemas.models import ConductorCreateDTO, ConductorResponseDTO


async def get_all(
    db: AsyncSession, user_id: str, repo: IConductorsRepository
) -> list[ConductorResponseDTO]:
    return [entity_to_dto(e) for e in await repo.get_all(db, user_id)]


async def get_by_id(
    db: AsyncSession, conductor_id: str, user_id: str, repo: IConductorsRepository
) -> ConductorResponseDTO:
    try:
        return entity_to_dto(await repo.get_by_id(db, conductor_id, user_id))
    except NoResultFound:
        raise EntityNotFoundError(f"Conductor {conductor_id} not found.")


async def create(
    db: AsyncSession,
    data: ConductorCreateDTO,
    user_id: str,
    repo: IConductorsRepository,
) -> ConductorResponseDTO:
    return entity_to_dto(await repo.create(db, user_id, create_dto_to_entity(data)))


async def update(
    db: AsyncSession,
    conductor_id: str,
    data: ConductorCreateDTO,
    user_id: str,
    repo: IConductorsRepository,
) -> ConductorResponseDTO:
    try:
        return entity_to_dto(
            await repo.update(db, conductor_id, user_id, create_dto_to_entity(data))
        )
    except NoResultFound:
        raise EntityNotFoundError(f"Conductor {conductor_id} not found.")


async def delete(
    db: AsyncSession, conductor_id: str, user_id: str, repo: IConductorsRepository
) -> None:
    if not await repo.delete(db, conductor_id, user_id):
        raise EntityNotFoundError(f"Conductor {conductor_id} not found.")
