from app.api.schemas.models import StudyCaseCreateDTO, StudyCaseResponseDTO
from app.domain.entities import StudyCase
from app.infrastructure.orm_models import StudyCaseORM


def create_dto_to_entity(dto: StudyCaseCreateDTO) -> StudyCase:
    return StudyCase(
        name=dto.name,
        description=dto.description or "",
        line_id=dto.line_id,
        segment_step_m=dto.segment_step_m,
        use_real_spans=dto.use_real_spans,
        use_dem=dto.use_dem,
    )


def orm_to_entity(obj: StudyCaseORM) -> StudyCase:
    return StudyCase(
        id=obj.id,
        name=obj.name,
        description=obj.description or "",
        line_id=obj.line_id,
        segment_step_m=obj.segment_step_m,
        use_real_spans=obj.use_real_spans,
        use_dem=obj.use_dem,
        created_at=obj.created_at.isoformat(),
        updated_at=obj.updated_at.isoformat(),
    )


def entity_to_dto(entity: StudyCase) -> StudyCaseResponseDTO:
    return StudyCaseResponseDTO(
        id=entity.id,
        name=entity.name,
        description=entity.description,
        line_id=entity.line_id,
        segment_step_m=entity.segment_step_m,
        use_real_spans=entity.use_real_spans,
        use_dem=entity.use_dem,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )
