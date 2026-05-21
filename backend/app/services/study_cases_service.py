from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound
from fastapi import HTTPException

from app.infrastructure.repositories.study_cases_repository import study_cases_repo
from app.infrastructure.repositories.lines_repository import lines_repo
from app.infrastructure.repositories.conductors_repository import conductors_repo
from app.infrastructure.orm_models import StudyCaseORM
from app.api.schemas.models import (
    StudyCaseCreateDTO,
    StudyCaseResponseDTO,
    MeteoScenarioResponseDTO,
)


def _to_dto(obj: StudyCaseORM) -> StudyCaseResponseDTO:
    return StudyCaseResponseDTO(
        id=obj.id,
        name=obj.name,
        description=obj.description,
        line_id=obj.line_id,
        conductor_id=obj.conductor_id,
        segment_step_m=obj.segment_step_m,
        use_real_spans=obj.use_real_spans,
        use_dem=obj.use_dem,
        scenarios=[
            MeteoScenarioResponseDTO(
                id=s.id,
                season=s.season,
                temp_amb_c=s.temp_amb_c,
                wind_speed_ms=s.wind_speed_ms,
                wind_angle_deg=s.wind_angle_deg,
                solar_radiation_wm2=s.solar_radiation_wm2,
            )
            for s in (obj.scenarios or [])
        ],
        created_at=obj.created_at.isoformat(),
        updated_at=obj.updated_at.isoformat(),
    )


async def _validate_references(
    db: AsyncSession, line_id: str, conductor_id: str
) -> None:
    """Verifica que la línea y el conductor referenciados existan.
    Usa exists() en lugar de get_by_id() — un solo campo, sin traer el objeto completo.
    """
    if not await lines_repo.exists(db, line_id):
        raise HTTPException(404, detail=f"Line {line_id} not found.")
    if not await conductors_repo.exists(db, conductor_id):
        raise HTTPException(404, detail=f"Conductor {conductor_id} not found.")


async def get_all(db: AsyncSession) -> list[StudyCaseResponseDTO]:
    return [_to_dto(o) for o in await study_cases_repo.get_all(db)]


async def get_by_id(db: AsyncSession, case_id: str) -> StudyCaseResponseDTO:
    try:
        return _to_dto(await study_cases_repo.get_by_id(db, case_id))
    except NoResultFound:
        raise HTTPException(404, detail=f"Study case {case_id} not found.")


async def create(db: AsyncSession, data: StudyCaseCreateDTO) -> StudyCaseResponseDTO:
    await _validate_references(db, data.line_id, data.conductor_id)
    return _to_dto(await study_cases_repo.create(db, data))


async def update(
    db: AsyncSession, case_id: str, data: StudyCaseCreateDTO
) -> StudyCaseResponseDTO:
    if not await study_cases_repo.exists(db, case_id):
        raise HTTPException(404, detail=f"Study case {case_id} not found.")
    await _validate_references(db, data.line_id, data.conductor_id)
    return _to_dto(await study_cases_repo.update(db, case_id, data))


async def delete(db: AsyncSession, case_id: str) -> None:
    deleted = await study_cases_repo.delete(db, case_id)
    if not deleted:
        raise HTTPException(404, detail=f"Study case {case_id} not found.")
