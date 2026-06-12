from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound

from app.domain.exceptions import EntityNotFoundError
from app.infrastructure.repositories.study_cases_repository import study_cases_repo
from app.infrastructure.repositories.lines_repository import lines_repo
from app.infrastructure.repositories.conductors_repository import conductors_repo
from app.infrastructure.repositories.calculations_repository import calculations_repo
from app.infrastructure.mappers.study_cases_mapper import (
    create_dto_to_entity,
    entity_to_dto,
)
from app.infrastructure.mappers.calculations_mapper import (
    entity_to_dto as calculation_entity_to_dto,
)
from app.api.schemas.models import (
    StudyCaseCreateDTO,
    StudyCaseResponseDTO,
    CalculationResponseDTO,
)


async def _validate_line(db, line_id: str, user_id: str) -> None:
    if not await lines_repo.exists(db, line_id, user_id):
        raise EntityNotFoundError(f"Line {line_id} not found.")


async def _validate_conductor(db, conductor_id: str, user_id: str) -> None:
    try:
        await conductors_repo.get_by_id(db, conductor_id, user_id)
    except NoResultFound:
        raise EntityNotFoundError(f"Conductor {conductor_id} not found.")


async def get_all(db: AsyncSession, user_id: str) -> list[StudyCaseResponseDTO]:
    return [entity_to_dto(e) for e in await study_cases_repo.get_all(db, user_id)]


async def get_by_id(
    db: AsyncSession, case_id: str, user_id: str
) -> StudyCaseResponseDTO:
    try:
        return entity_to_dto(await study_cases_repo.get_by_id(db, case_id, user_id))
    except NoResultFound:
        raise EntityNotFoundError(f"Study case {case_id} not found.")


async def list_calculations(
    db: AsyncSession, case_id: str, user_id: str
) -> list[CalculationResponseDTO]:
    if not await study_cases_repo.exists(db, case_id, user_id):
        raise EntityNotFoundError(f"Study case {case_id} not found.")
    return [
        calculation_entity_to_dto(c)
        for c in await calculations_repo.get_by_study_case(db, case_id, user_id)
    ]


async def get_calculation(
    db: AsyncSession, case_id: str, calc_id: str, user_id: str
) -> CalculationResponseDTO:
    try:
        entity = await calculations_repo.get_by_id(db, calc_id, user_id)
    except NoResultFound:
        raise EntityNotFoundError(f"Calculation {calc_id} not found.")
    if entity.study_case_id != case_id:
        raise EntityNotFoundError(f"Calculation {calc_id} not found.")
    return calculation_entity_to_dto(entity)


async def create(
    db: AsyncSession, data: StudyCaseCreateDTO, user_id: str
) -> StudyCaseResponseDTO:
    await _validate_line(db, data.line_id, user_id)
    await _validate_conductor(db, data.conductor_id, user_id)
    return entity_to_dto(
        await study_cases_repo.create(db, user_id, create_dto_to_entity(data))
    )


async def update(
    db: AsyncSession, case_id: str, data: StudyCaseCreateDTO, user_id: str
) -> StudyCaseResponseDTO:
    if not await study_cases_repo.exists(db, case_id, user_id):
        raise EntityNotFoundError(f"Study case {case_id} not found.")
    await _validate_line(db, data.line_id, user_id)
    await _validate_conductor(db, data.conductor_id, user_id)
    return entity_to_dto(
        await study_cases_repo.update(db, case_id, user_id, create_dto_to_entity(data))
    )


async def delete(db: AsyncSession, case_id: str, user_id: str) -> None:
    if not await study_cases_repo.delete(db, case_id, user_id):
        raise EntityNotFoundError(f"Study case {case_id} not found.")
