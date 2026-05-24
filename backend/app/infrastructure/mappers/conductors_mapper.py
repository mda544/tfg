from app.api.schemas.models import ConductorCreateDTO, ConductorResponseDTO
from app.domain.entities import Conductor
from app.infrastructure.orm_models import ConductorORM


def create_dto_to_entity(dto: ConductorCreateDTO) -> Conductor:
    return Conductor(
        name=dto.name,
        description=dto.description or "",
        diameter_mm=dto.diameter_mm,
        r_ac_75_ohm_km=dto.r_ac_75_ohm_km,
        r_ac_25_ohm_km=dto.r_ac_25_ohm_km,
        emissivity=dto.emissivity,
        absorptivity=dto.absorptivity,
        max_temp_c=dto.max_temp_c,
    )


def entity_to_orm(entity: Conductor, owner_id: str) -> ConductorORM:
    return ConductorORM(
        owner_id=owner_id,
        name=entity.name,
        description=entity.description,
        diameter_mm=entity.diameter_mm,
        r_ac_75_ohm_km=entity.r_ac_75_ohm_km,
        r_ac_25_ohm_km=entity.r_ac_25_ohm_km,
        emissivity=entity.emissivity,
        absorptivity=entity.absorptivity,
        max_temp_c=entity.max_temp_c,
    )


def orm_to_entity(obj: ConductorORM) -> Conductor:
    return Conductor(
        id=obj.id,
        name=obj.name,
        description=obj.description or "",
        diameter_mm=obj.diameter_mm,
        r_ac_75_ohm_km=obj.r_ac_75_ohm_km,
        r_ac_25_ohm_km=obj.r_ac_25_ohm_km,
        emissivity=obj.emissivity,
        absorptivity=obj.absorptivity,
        max_temp_c=obj.max_temp_c,
        created_at=obj.created_at.isoformat(),
        updated_at=obj.updated_at.isoformat(),
    )


def entity_to_dto(entity: Conductor) -> ConductorResponseDTO:
    return ConductorResponseDTO(
        id=entity.id,
        name=entity.name,
        description=entity.description,
        diameter_mm=entity.diameter_mm,
        r_ac_75_ohm_km=entity.r_ac_75_ohm_km,
        r_ac_25_ohm_km=entity.r_ac_25_ohm_km,
        emissivity=entity.emissivity,
        absorptivity=entity.absorptivity,
        max_temp_c=entity.max_temp_c,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )
