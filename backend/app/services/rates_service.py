import uuid
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound

from app.domain.geometry_validation import validate_route
from app.domain.thermal_model import IEEE738Calculator
from app.domain.segmentation import segment_route, segment_by_spans
from app.domain.value_objects import PointMeteoConditions, WeatherInput
from app.domain.types import Season
from app.infrastructure.repositories.rates_repository import rates_repo
from app.infrastructure.repositories.study_cases_repository import study_cases_repo
from app.infrastructure.repositories.lines_repository import lines_repo
from app.infrastructure.repositories.conductors_repository import conductors_repo
from app.infrastructure.mappers.rates_mapper import (
    build_rate_entity,
    entity_to_dto,
    weather_input_dto_to_vo,
)
from app.api.schemas.models import RateCreateDTO, RateResultResponseDTO

_calculator = IEEE738Calculator()


async def get_by_id(db: AsyncSession, rate_id: str) -> RateResultResponseDTO:
    try:
        return entity_to_dto(await rates_repo.get_by_id(db, rate_id))
    except NoResultFound:
        raise HTTPException(404, detail=f"Rate result {rate_id} not found.")


async def get_by_study_case(
    db: AsyncSession, case_id: str
) -> list[RateResultResponseDTO]:
    return [entity_to_dto(e) for e in await rates_repo.get_by_study_case(db, case_id)]


async def delete(db: AsyncSession, rate_id: str) -> None:
    if not await rates_repo.delete(db, rate_id):
        raise HTTPException(404, detail=f"Rate result {rate_id} not found.")


async def create(
    db: AsyncSession,
    req: RateCreateDTO,
    user_id: str,
) -> RateResultResponseDTO:

    # Obtener y validar StudyCase
    try:
        study_case = await study_cases_repo.get_by_id(db, req.study_case_id, user_id)
    except NoResultFound:
        raise HTTPException(404, detail=f"Study case {req.study_case_id} not found.")

    # Obtener y validar Conductor
    try:
        conductor = await conductors_repo.get_by_id(db, req.conductor_id, user_id)
    except NoResultFound:
        raise HTTPException(404, detail=f"Conductor {req.conductor_id} not found.")

    # Obtener la línea del caso de estudio
    try:
        line = await lines_repo.get_by_id(db, study_case.line_id, user_id)
    except NoResultFound:
        raise HTTPException(404, detail=f"Line {study_case.line_id} not found.")

    # WeatherInputs del request
    weather_inputs: list[WeatherInput] = [
        weather_input_dto_to_vo(w) for w in req.weather_inputs
    ]
    scenarios: dict[Season, WeatherInput] = {w.season: w for w in weather_inputs}

    # Coordenadas desde la línea persistida
    coordinates = [{"lat": c.lat, "lon": c.lon} for c in line.coordinates]

    # Si la línea tiene elevaciones guardadas las usamos directamente
    elevation_source = "none"
    if line.min_elevation_m is not None:
        for i, coord in enumerate(coordinates):
            coord["elevation"] = 0.0  # se rellenará segmento a segmento desde DEM
        elevation_source = "line_dem"

    # Validación geométrica
    validation = validate_route(coordinates)
    if not validation.valid:
        raise HTTPException(
            status_code=422,
            detail={
                "errors": list(validation.errors),
                "warnings": list(validation.warnings),
                "info": validation.info,
            },
        )

    # Segmentación
    if study_case.use_real_spans and len(coordinates) >= 2:
        segments = segment_by_spans(coordinates)
    elif study_case.segment_step_m > 0:
        segments = segment_route(coordinates, study_case.segment_step_m)
    else:
        raise HTTPException(400, detail="Invalid segmentation.")

    if not segments:
        raise HTTPException(400, detail="No segments could be generated.")

    # Cálculo IEEE 738 — rellena rates y ratings de cada Segment
    for segment in segments:
        for season, weather in scenarios.items():
            meteo = PointMeteoConditions(
                temp_amb_c=weather.temp_amb_c,
                wind_speed_ms=weather.wind_speed_ms,
                wind_angle_deg=weather.wind_angle_deg,
                solar_radiation_wm2=weather.solar_radiation_wm2,
                elevation_m=segment.elevation_m,
            )
            rating = _calculator.calcular(
                conductor=conductor,
                meteo=meteo,
                latitud_deg=segment.mid_point.lat,
                azimut_linea_deg=segment.azimuth_deg,
            )
            segment.rates[season] = rating.ampacity
            segment.ratings[season] = rating

    # 1. Entidad RateResult
    rate_entity = build_rate_entity(
        rate_id=str(uuid.uuid4()),
        study_case_id=req.study_case_id,
        conductor=conductor,
        weather_inputs=weather_inputs,
        segments=segments,
        climate_source=req.climate_source,
        elevation_source=elevation_source,
        warnings=list(validation.warnings),
    )

    # 2. Repositorio recibe entidad
    saved = await rates_repo.create(db, rate_entity)

    # 3. DTO para FastAPI
    return entity_to_dto(saved)
