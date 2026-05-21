from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound
from fastapi import HTTPException

from app.infrastructure.repositories.conductors_repository import conductors_repo
from app.infrastructure.orm_models import ConductorORM, UserORM
from app.api.schemas.models import ConductorCreateDTO, ConductorResponseDTO


def _to_dto(obj: ConductorORM) -> ConductorResponseDTO:
    return ConductorResponseDTO(
        id=obj.id,
        name=obj.name,
        description=obj.description,
        diameter_mm=obj.diameter_mm,
        r_ac_75_ohm_km=obj.r_ac_75_ohm_km,
        r_ac_25_ohm_km=obj.r_ac_25_ohm_km,
        emissivity=obj.emissivity,
        absorptivity=obj.absorptivity,
        max_temp_c=obj.max_temp_c,
        created_at=obj.created_at.isoformat(),
        updated_at=obj.updated_at.isoformat(),
    )


async def get_all(db: AsyncSession, user: UserORM) -> list[ConductorResponseDTO]:
    return [_to_dto(o) for o in await conductors_repo.get_all(db, user.id)]


async def get_by_id(
    db: AsyncSession, conductor_id: str, user: UserORM
) -> ConductorResponseDTO:
    try:
        return _to_dto(await conductors_repo.get_by_id(db, conductor_id, user.id))
    except NoResultFound:
        raise HTTPException(404, detail=f"Conductor {conductor_id} not found.")


async def create(
    db: AsyncSession, data: ConductorCreateDTO, user: UserORM
) -> ConductorResponseDTO:
    return _to_dto(await conductors_repo.create(db, user.id, data))


async def update(
    db: AsyncSession, conductor_id: str, data: ConductorCreateDTO, user: UserORM
) -> ConductorResponseDTO:
    try:
        return _to_dto(await conductors_repo.update(db, conductor_id, user.id, data))
    except NoResultFound:
        raise HTTPException(404, detail=f"Conductor {conductor_id} not found.")


async def delete(db: AsyncSession, conductor_id: str, user: UserORM) -> None:
    deleted = await conductors_repo.delete(db, conductor_id, user.id)
    if not deleted:
        raise HTTPException(404, detail=f"Conductor {conductor_id} not found.")
