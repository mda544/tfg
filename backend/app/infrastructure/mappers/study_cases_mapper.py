from app.api.schemas.models import StudyCaseCreateDTO, StudyCaseResponseDTO
from app.domain.entities import StudyCase
from app.infrastructure.orm_models import StudyCaseORM
from app.infrastructure.mappers.conductors_mapper import (
    orm_to_entity as conductor_orm_to_entity,
    entity_to_dto as conductor_entity_to_dto,
)


def create_dto_to_entity(dto: StudyCaseCreateDTO) -> StudyCase:
    return StudyCase(
        name=dto.name,
        description=dto.description or "",
        line_id=dto.line_id,
        conductor_id=dto.conductor_id,
        segment_step_m=dto.segment_step_m,
        use_real_spans=dto.use_real_spans,
        use_dem=dto.use_dem,
    )


def entity_to_orm(entity: StudyCase, owner_id: str) -> StudyCaseORM:
    return StudyCaseORM(
        owner_id=owner_id,
        name=entity.name,
        description=entity.description,
        line_id=entity.line_id,
        conductor_id=entity.conductor_id,
        segment_step_m=entity.segment_step_m,
        use_real_spans=entity.use_real_spans,
        use_dem=entity.use_dem,
    )


def orm_to_entity(obj: StudyCaseORM) -> StudyCase:
    conductor = conductor_orm_to_entity(obj.conductor) if obj.conductor else None
    return StudyCase(
        id=obj.id,
        name=obj.name,
        description=obj.description or "",
        line_id=obj.line_id,
        conductor_id=obj.conductor_id,
        conductor=conductor,
        segment_step_m=obj.segment_step_m,
        use_real_spans=obj.use_real_spans,
        use_dem=obj.use_dem,
        created_at=obj.created_at.isoformat(),
        updated_at=obj.updated_at.isoformat(),
    )


def entity_to_dto(entity: StudyCase) -> StudyCaseResponseDTO:
    conductor_dto = (
        conductor_entity_to_dto(entity.conductor) if entity.conductor else None
    )
    return StudyCaseResponseDTO(
        id=entity.id,
        name=entity.name,
        description=entity.description,
        line_id=entity.line_id,
        conductor_id=entity.conductor_id,
        conductor=conductor_dto,
        segment_step_m=entity.segment_step_m,
        use_real_spans=entity.use_real_spans,
        use_dem=entity.use_dem,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )
