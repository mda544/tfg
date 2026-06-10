from app.domain.entities import Conductor, RateResult
from app.domain.value_objects import WeatherInput
from app.domain.types import Season, SEASONS
from app.infrastructure.orm_models import RateResultORM, RateWeatherInputORM
from app.infrastructure.mappers.conductors_mapper import (
    orm_to_entity as conductor_orm_to_entity,
    entity_to_dto as conductor_entity_to_dto,
)
from app.infrastructure.mappers.segments_mapper import (
    orm_to_entity as segment_orm_to_entity,
    entity_to_dto as segment_entity_to_dto,
)
from app.api.schemas.models import WeatherInputDTO, RateResultResponseDTO

# WeatherInput


def weather_input_dto_to_vo(dto: WeatherInputDTO) -> WeatherInput:
    return WeatherInput(
        season=dto.season,
        temp_amb_c=dto.temp_amb_c,
        wind_speed_ms=dto.wind_speed_ms,
        wind_angle_deg=dto.wind_angle_deg,
        solar_radiation_wm2=dto.solar_radiation_wm2,
        wind_dir_predominant_deg=dto.wind_dir_predominant_deg,
    )


def weather_input_vo_to_dto(wi: WeatherInput) -> WeatherInputDTO:
    return WeatherInputDTO(
        season=wi.season,
        temp_amb_c=wi.temp_amb_c,
        wind_speed_ms=wi.wind_speed_ms,
        wind_angle_deg=wi.wind_angle_deg,
        solar_radiation_wm2=wi.solar_radiation_wm2,
        wind_dir_predominant_deg=wi.wind_dir_predominant_deg,
    )


def weather_input_vo_to_orm(
    wi: WeatherInput, rate_result_id: str
) -> RateWeatherInputORM:
    return RateWeatherInputORM(
        rate_result_id=rate_result_id,
        season=wi.season,
        temp_amb_c=wi.temp_amb_c,
        wind_speed_ms=wi.wind_speed_ms,
        wind_angle_deg=wi.wind_angle_deg,
        wind_dir_predominant_deg=wi.wind_dir_predominant_deg,
        solar_radiation_wm2=wi.solar_radiation_wm2,
    )


# ORM -> Entidad


def orm_to_entity(obj: RateResultORM) -> RateResult:
    conductor = conductor_orm_to_entity(obj.conductor)

    weather_inputs = [
        WeatherInput(
            season=wi.season,
            temp_amb_c=wi.temp_amb_c,
            wind_speed_ms=wi.wind_speed_ms,
            wind_angle_deg=wi.wind_angle_deg,
            solar_radiation_wm2=wi.solar_radiation_wm2,
            wind_dir_predominant_deg=wi.wind_dir_predominant_deg,
        )
        for wi in sorted(obj.weather_inputs, key=lambda w: SEASONS.index(w.season))
    ]

    segments = [
        segment_orm_to_entity(s, conductor.max_temp_c)
        for s in sorted(obj.segments, key=lambda x: x.index)
    ]

    return RateResult(
        id=obj.id,
        study_case_id=obj.study_case_id,
        conductor_id=obj.conductor_id,
        conductor=conductor,
        weather_inputs=weather_inputs,
        segments=segments,
        climate_source=obj.climate_source,
        elevation_source=obj.elevation_source,
        warnings=list(obj.warnings or []),
        created_at=obj.created_at.isoformat(),
    )


# Entidad -> DTO


def entity_to_dto(entity: RateResult) -> RateResultResponseDTO:
    return RateResultResponseDTO(
        id=entity.id,
        study_case_id=entity.study_case_id,
        conductor=conductor_entity_to_dto(entity.conductor),
        weather_inputs=[weather_input_vo_to_dto(w) for w in entity.weather_inputs],
        climate_source=entity.climate_source,
        elevation_source=entity.elevation_source,
        n_segments=entity.n_segments,
        rate_summer=entity.rates_by_season.get("verano", 0.0),
        rate_autumn=entity.rates_by_season.get("otono", 0.0),
        rate_winter=entity.rates_by_season.get("invierno", 0.0),
        rate_spring=entity.rates_by_season.get("primavera", 0.0),
        design_rate=entity.design_rate,
        segments=[segment_entity_to_dto(s) for s in entity.segments],
        warnings=entity.warnings,
        created_at=entity.created_at,
    )


# Builder desde cálculo


def build_rate_entity(
    rate_id: str,
    study_case_id: str,
    conductor: Conductor,
    weather_inputs: list[WeatherInput],
    segments: list,
    climate_source: str,
    elevation_source: str,
    warnings: list[str],
) -> RateResult:
    return RateResult(
        id=rate_id,
        study_case_id=study_case_id,
        conductor_id=conductor.id,
        conductor=conductor,
        weather_inputs=weather_inputs,
        segments=segments,
        climate_source=climate_source,
        elevation_source=elevation_source,
        warnings=warnings,
    )
