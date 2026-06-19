import uuid

from app.domain.entities import Calculation, SeasonResult
from app.domain.types import SEASONS
from app.infrastructure.orm_models import CalculationORM
from app.infrastructure.mappers.season_results_mapper import (
    orm_to_entity as season_result_orm_to_entity,
    entity_to_dto as season_result_entity_to_dto,
)
from app.api.schemas.models import CalculationResponseDTO


def orm_to_entity(obj: CalculationORM) -> Calculation:
    season_results = [
        season_result_orm_to_entity(sr)
        for sr in sorted(obj.season_results, key=lambda x: SEASONS.index(x.season))
    ]
    return Calculation(
        id=obj.id,
        study_case_id=obj.study_case_id,
        climate_source=obj.climate_source,
        season_results=season_results,
        warnings=list(obj.warnings or []),
        created_at=obj.created_at.isoformat(),
    )


def entity_to_dto(entity: Calculation) -> CalculationResponseDTO:
    return CalculationResponseDTO(
        id=entity.id,
        study_case_id=entity.study_case_id,
        climate_source=entity.climate_source,
        design_rate=entity.design_rate,
        n_segments=entity.n_segments,
        warnings=entity.warnings,
        season_results=[
            season_result_entity_to_dto(sr) for sr in entity.season_results
        ],
        created_at=entity.created_at,
    )


def build_calculation_entity(
    study_case_id: str,
    climate_source: str,
    season_results: list[SeasonResult],
    warnings: list[str],
) -> Calculation:
    return Calculation(
        id=str(uuid.uuid4()),
        study_case_id=study_case_id,
        climate_source=climate_source,
        season_results=season_results,
        warnings=warnings,
    )
