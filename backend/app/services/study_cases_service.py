from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound

from app.domain.exceptions import EntityNotFoundError
from app.domain.repository_interfaces import (
    IStudyCasesRepository,
    ILinesRepository,
    IConductorsRepository,
    ICalculationsRepository,
)
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


async def _validate_line(
    db, line_id: str, user_id: str, lines_repo: ILinesRepository
) -> None:
    if not await lines_repo.exists(db, line_id, user_id):
        raise EntityNotFoundError(f"Line {line_id} not found.")


async def _validate_conductor(
    db, conductor_id: str, user_id: str, conductors_repo: IConductorsRepository
) -> None:
    try:
        await conductors_repo.get_by_id(db, conductor_id, user_id)
    except NoResultFound:
        raise EntityNotFoundError(f"Conductor {conductor_id} not found.")


async def get_all(
    db: AsyncSession, user_id: str, repo: IStudyCasesRepository
) -> list[StudyCaseResponseDTO]:
    return [entity_to_dto(e) for e in await repo.get_all(db, user_id)]


async def get_by_id(
    db: AsyncSession, case_id: str, user_id: str, repo: IStudyCasesRepository
) -> StudyCaseResponseDTO:
    try:
        return entity_to_dto(await repo.get_by_id(db, case_id, user_id))
    except NoResultFound:
        raise EntityNotFoundError(f"Study case {case_id} not found.")


async def list_calculations(
    db: AsyncSession,
    case_id: str,
    user_id: str,
    study_cases_repo: IStudyCasesRepository,
    calculations_repo: ICalculationsRepository,
) -> list[CalculationResponseDTO]:
    if not await study_cases_repo.exists(db, case_id, user_id):
        raise EntityNotFoundError(f"Study case {case_id} not found.")
    return [
        calculation_entity_to_dto(c)
        for c in await calculations_repo.get_by_study_case(db, case_id, user_id)
    ]


async def get_calculation(
    db: AsyncSession,
    case_id: str,
    calc_id: str,
    user_id: str,
    calculations_repo: ICalculationsRepository,
) -> CalculationResponseDTO:
    try:
        entity = await calculations_repo.get_by_id(db, calc_id, user_id)
    except NoResultFound:
        raise EntityNotFoundError(f"Calculation {calc_id} not found.")
    if entity.study_case_id != case_id:
        raise EntityNotFoundError(f"Calculation {calc_id} not found.")
    return calculation_entity_to_dto(entity)


async def create(
    db: AsyncSession,
    data: StudyCaseCreateDTO,
    user_id: str,
    study_cases_repo: IStudyCasesRepository,
    lines_repo: ILinesRepository,
    conductors_repo: IConductorsRepository,
) -> StudyCaseResponseDTO:
    await _validate_line(db, data.line_id, user_id, lines_repo)
    await _validate_conductor(db, data.conductor_id, user_id, conductors_repo)
    return entity_to_dto(
        await study_cases_repo.create(db, user_id, create_dto_to_entity(data))
    )


async def update(
    db: AsyncSession,
    case_id: str,
    data: StudyCaseCreateDTO,
    user_id: str,
    study_cases_repo: IStudyCasesRepository,
    lines_repo: ILinesRepository,
    conductors_repo: IConductorsRepository,
) -> StudyCaseResponseDTO:
    if not await study_cases_repo.exists(db, case_id, user_id):
        raise EntityNotFoundError(f"Study case {case_id} not found.")
    await _validate_line(db, data.line_id, user_id, lines_repo)
    await _validate_conductor(db, data.conductor_id, user_id, conductors_repo)
    return entity_to_dto(
        await study_cases_repo.update(db, case_id, user_id, create_dto_to_entity(data))
    )


async def delete(
    db: AsyncSession, case_id: str, user_id: str, repo: IStudyCasesRepository
) -> None:
    if not await repo.delete(db, case_id, user_id):
        raise EntityNotFoundError(f"Study case {case_id} not found.")
