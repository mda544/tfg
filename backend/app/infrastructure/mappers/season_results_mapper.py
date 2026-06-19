from app.domain.entities import SeasonResult, WeatherInput
from app.infrastructure.orm_models import SeasonResultORM
from app.infrastructure.mappers.segments_mapper import (
    orm_to_entity as segment_orm_to_entity,
    entity_to_orm as segment_entity_to_orm,
    entity_to_dto as segment_entity_to_dto,
)
from app.api.schemas.models import WeatherInputDTO, SeasonResultDTO



def weather_input_dto_to_entity(dto: WeatherInputDTO) -> WeatherInput:
    return WeatherInput(
        season=dto.season,
        temp_amb_c=dto.temp_amb_c,
        wind_speed_ms=dto.wind_speed_ms,
        wind_angle_deg=dto.wind_angle_deg,
        solar_radiation_wm2=dto.solar_radiation_wm2,
        wind_dir_predominant_deg=dto.wind_dir_predominant_deg,
    )


def weather_input_entity_to_dto(wi: WeatherInput) -> WeatherInputDTO:
    return WeatherInputDTO(
        season=wi.season,
        temp_amb_c=wi.temp_amb_c,
        wind_speed_ms=wi.wind_speed_ms,
        wind_angle_deg=wi.wind_angle_deg,
        solar_radiation_wm2=wi.solar_radiation_wm2,
        wind_dir_predominant_deg=wi.wind_dir_predominant_deg,
    )




def orm_to_entity(obj: SeasonResultORM) -> SeasonResult:
    segments = [
        segment_orm_to_entity(s) for s in sorted(obj.segments, key=lambda x: x.index)
    ]
    return SeasonResult(
        id=obj.id,
        calculation_id=obj.calculation_id,
        season=obj.season,
        weather_input=WeatherInput(
            season=obj.season,
            temp_amb_c=obj.temp_amb_c,
            wind_speed_ms=obj.wind_speed_ms,
            wind_angle_deg=obj.wind_angle_deg,
            solar_radiation_wm2=obj.solar_radiation_wm2,
            wind_dir_predominant_deg=obj.wind_dir_predominant_deg,
        ),
        segments=segments,
        elevation_source=obj.elevation_source,
    )




def entity_to_orm(entity: SeasonResult, calculation_id: str) -> SeasonResultORM:
    wi = entity.weather_input
    return SeasonResultORM(
        calculation_id=calculation_id,
        season=entity.season,
        temp_amb_c=wi.temp_amb_c,
        wind_speed_ms=wi.wind_speed_ms,
        wind_angle_deg=wi.wind_angle_deg,
        wind_dir_predominant_deg=wi.wind_dir_predominant_deg,
        solar_radiation_wm2=wi.solar_radiation_wm2,
        design_rate=entity.design_rate,
        elevation_source=entity.elevation_source,
    )




def entity_to_dto(entity: SeasonResult) -> SeasonResultDTO:
    return SeasonResultDTO(
        id=entity.id,
        season=entity.season,
        weather_input=weather_input_entity_to_dto(entity.weather_input),
        design_rate=entity.design_rate,
        elevation_source=entity.elevation_source,
        n_segments=entity.n_segments,
        segments=[segment_entity_to_dto(s) for s in entity.segments],
    )
