import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound

from app.domain.exceptions import EntityNotFoundError, ValidationError, CalculationError
from app.domain.geometry_validation import validate_route
from app.domain.thermal_model import IEEE738Calculator
from app.domain.segmentation import segment_route, segment_by_spans
from app.domain.value_objects import PointMeteoConditions
from app.domain.entities import WeatherInput, SeasonResult, Segment
from app.domain.types import ElevationSource
from app.domain.geo import wind_angle_for_segment
from app.infrastructure.repositories.calculations_repository import calculations_repo
from app.infrastructure.repositories.study_cases_repository import study_cases_repo
from app.infrastructure.repositories.lines_repository import lines_repo
from app.infrastructure.mappers.calculations_mapper import (
    build_calculation_entity,
    entity_to_dto,
)
from app.infrastructure.mappers.season_results_mapper import weather_input_dto_to_entity
from app.services.elevation_service import add_elevation
from app.api.schemas.models import CalculationCreateDTO, CalculationResponseDTO

_calculator = IEEE738Calculator()


def _perform_thermal_calculations(
    seg_templates: list,
    weather_inputs: list[WeatherInput],
    conductor,
    calculation_id: str,
    elevation_source: ElevationSource,
) -> list[SeasonResult]:
    season_results = []
    for wi in weather_inputs:
        season_segments = []
        for tmpl in seg_templates:
            phi = wind_angle_for_segment(
                wind_dir_predominant_deg=wi.wind_dir_predominant_deg,
                segment_azimuth_deg=tmpl.azimuth_deg,
                user_wind_angle_deg=wi.wind_angle_deg,
            )
            meteo = PointMeteoConditions(
                temp_amb_c=wi.temp_amb_c,
                wind_speed_ms=wi.wind_speed_ms,
                wind_angle_deg=phi,
                solar_radiation_wm2=wi.solar_radiation_wm2,
                elevation_m=tmpl.elevation_m,
            )
            rating = _calculator.calcular(
                conductor=conductor,
                meteo=meteo,
                season=wi.season,
                latitud_deg=tmpl.mid_point.lat,
                azimut_linea_deg=tmpl.azimuth_deg,
            )
            season_segments.append(
                Segment(
                    id=tmpl.id,
                    index=tmpl.index,
                    start_point=tmpl.start_point,
                    mid_point=tmpl.mid_point,
                    end_point=tmpl.end_point,
                    length_km=tmpl.length_km,
                    elevation_m=tmpl.elevation_m,
                    azimuth_deg=tmpl.azimuth_deg,
                    ampacity=rating.ampacity,
                    rating=rating,
                )
            )
        season_results.append(
            SeasonResult(
                id=str(uuid.uuid4()),
                calculation_id=calculation_id,
                season=wi.season,
                weather_input=wi,
                segments=season_segments,
                elevation_source=elevation_source,
            )
        )
    return season_results


async def get_by_id(
    db: AsyncSession, calc_id: str, case_id: str, user_id: str
) -> CalculationResponseDTO:
    try:
        entity = await calculations_repo.get_by_id(db, calc_id, user_id)
    except NoResultFound:
        raise EntityNotFoundError(f"Calculation {calc_id} not found.")
    if entity.study_case_id != case_id:
        raise EntityNotFoundError(f"Calculation {calc_id} not found.")
    return entity_to_dto(entity)


async def get_by_study_case(
    db: AsyncSession, case_id: str, user_id: str
) -> list[CalculationResponseDTO]:
    return [
        entity_to_dto(e)
        for e in await calculations_repo.get_by_study_case(db, case_id, user_id)
    ]


async def delete(db: AsyncSession, calc_id: str, case_id: str, user_id: str) -> None:
    try:
        entity = await calculations_repo.get_by_id(db, calc_id, user_id)
    except NoResultFound:
        raise EntityNotFoundError(f"Calculation {calc_id} not found.")
    if entity.study_case_id != case_id:
        raise EntityNotFoundError(f"Calculation {calc_id} not found.")
    await calculations_repo.delete(db, calc_id, user_id)


async def create(
    db: AsyncSession,
    req: CalculationCreateDTO,
    user_id: str,
) -> CalculationResponseDTO:

    # 1. Resolver dependencias
    try:
        study_case = await study_cases_repo.get_by_id(db, req.study_case_id, user_id)
    except NoResultFound:
        raise EntityNotFoundError(f"Study case {req.study_case_id} not found.")

    # El conductor viene embebido en el StudyCase
    conductor = study_case.conductor
    if conductor is None:
        raise EntityNotFoundError(f"Conductor {study_case.conductor_id} not found.")

    try:
        line = await lines_repo.get_by_id(db, study_case.line_id, user_id)
    except NoResultFound:
        raise EntityNotFoundError(f"Line {study_case.line_id} not found.")

    # 2. Convertir DTOs a entidades
    weather_inputs: list[WeatherInput] = [
        weather_input_dto_to_entity(w) for w in req.weather_inputs
    ]

    # 3. Enriquecer con elevación
    coordinates = [
        {
            "lat": c.lat,
            "lon": c.lon,
            **({"elevation_m": c.elevation_m} if c.elevation_m is not None else {}),
        }
        for c in line.coordinates
    ]
    elevation_source: ElevationSource = "none"

    if study_case.use_dem:
        if line.min_elevation_m is not None:
            elevation_source = "file"
        else:
            try:
                coordinates = await add_elevation(db, coordinates)
                elevation_source = "dem"
            except Exception as e:
                print(f"[DEM] Elevation enrichment failed: {e}")

    # 4. Validar topología
    validation = validate_route(coordinates)
    if not validation.valid:
        raise ValidationError(
            "El trazado contiene errores geométricos.",
            errors=list(validation.errors),
            warnings=list(validation.warnings),
        )

    # 5. Segmentar
    if study_case.use_real_spans and len(coordinates) >= 2:
        seg_templates = segment_by_spans(coordinates)
    elif study_case.segment_step_m > 0:
        seg_templates = segment_route(coordinates, study_case.segment_step_m)
    else:
        raise CalculationError("Parámetros de segmentación no válidos.")

    if not seg_templates:
        raise CalculationError("No se pudieron generar segmentos.")

    # 6. Calcular
    calculation_id = str(uuid.uuid4())
    season_results = _perform_thermal_calculations(
        seg_templates=seg_templates,
        weather_inputs=weather_inputs,
        conductor=conductor,
        calculation_id=calculation_id,
        elevation_source=elevation_source,
    )

    # 7. Persistir
    calculation = build_calculation_entity(
        study_case_id=req.study_case_id,
        climate_source=req.climate_source,
        season_results=season_results,
        warnings=list(validation.warnings),
    )
    calculation.id = calculation_id

    saved = await calculations_repo.create(db, calculation)
    return entity_to_dto(saved)
