from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound
from fastapi import HTTPException

from app.infrastructure.repositories.study_cases_repository import study_cases_repo
from app.infrastructure.repositories.lines_repository import lines_repo
from app.infrastructure.repositories.rates_repository import rates_repo
from app.infrastructure.mappers.study_cases_mapper import (
    create_dto_to_entity,
    entity_to_dto,
)
from app.infrastructure.mappers.rates_mapper import entity_to_dto as rate_entity_to_dto
from app.api.schemas.models import (
    StudyCaseCreateDTO,
    StudyCaseResponseDTO,
    RateResultResponseDTO,
)


async def _validate_line(db: AsyncSession, line_id: str, user_id: str) -> None:
    if not await lines_repo.exists(db, line_id, user_id):
        raise HTTPException(404, detail=f"Line {line_id} not found.")


async def get_all(db: AsyncSession, user_id: str) -> list[StudyCaseResponseDTO]:
    return [entity_to_dto(e) for e in await study_cases_repo.get_all(db, user_id)]


async def get_by_id(
    db: AsyncSession, case_id: str, user_id: str
) -> StudyCaseResponseDTO:
    try:
        return entity_to_dto(await study_cases_repo.get_by_id(db, case_id, user_id))
    except NoResultFound:
        raise HTTPException(404, detail=f"Study case {case_id} not found.")


async def list_rates(
    db: AsyncSession, case_id: str, user_id: str
) -> list[RateResultResponseDTO]:
    return [
        rate_entity_to_dto(r)
        for r in await rates_repo.get_by_study_case(db, case_id, user_id)
    ]


async def get_rate(
    db: AsyncSession, case_id: str, rate_id: str, user_id: str
) -> RateResultResponseDTO:
    try:
        entity = await rates_repo.get_by_id(db, rate_id, user_id)
    except NoResultFound:
        raise HTTPException(404, detail=f"Rate {rate_id} not found.")
    if entity.study_case_id != case_id:
        raise HTTPException(404, detail=f"Rate {rate_id} not found.")
    return rate_entity_to_dto(entity)


async def create(
    db: AsyncSession, data: StudyCaseCreateDTO, user_id: str
) -> StudyCaseResponseDTO:
    await _validate_line(db, data.line_id, user_id)
    return entity_to_dto(
        await study_cases_repo.create(db, user_id, create_dto_to_entity(data))
    )


async def update(
    db: AsyncSession, case_id: str, data: StudyCaseCreateDTO, user_id: str
) -> StudyCaseResponseDTO:
    if not await study_cases_repo.exists(db, case_id, user_id):
        raise HTTPException(404, detail=f"Study case {case_id} not found.")
    await _validate_line(db, data.line_id, user_id)
    return entity_to_dto(
        await study_cases_repo.update(db, case_id, user_id, create_dto_to_entity(data))
    )


async def delete(db: AsyncSession, case_id: str, user_id: str) -> None:
    if not await study_cases_repo.delete(db, case_id, user_id):
        raise HTTPException(404, detail=f"Study case {case_id} not found.")
