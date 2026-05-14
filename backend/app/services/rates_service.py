import uuid
from typing import Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound

from app.domain.geometry_validation import validate_route
from app.domain.thermal_model import IEEE738Calculator
from app.domain.segmentation import segment_route, segment_by_spans
from app.domain.seasonal_scenarios import DEFAULT_SCENARIOS
from app.domain.entities import Conductor, MeteoConditions, MeteoScenario, SegmentAccumulator
from app.domain.types import Season
from app.services.elevation_service import enrich_with_elevation
from app.infrastructure.repositories.rates_repository import rates_repo
from app.infrastructure.orm_models import RateResultORM
from app.api.schemas.models import RateCalculationRequestDTO, RateCalculationResponseDTO

_calculator = IEEE738Calculator()


# ORM → DTO

def _to_dto(obj: RateResultORM) -> RateCalculationResponseDTO:
    return RateCalculationResponseDTO(
        id              = obj.id,
        n_segments      = obj.n_segments,
        conductor       = obj.conductor_snapshot,
        segments        = obj.segments_data or [],  
        design_rate_a   = obj.design_rate_a,
        rates_by_season = obj.rates_by_season,
        route_info      = obj.route_info,
        warnings        = obj.warnings or [],
    )


# Consultas y borrado

async def get_by_id(db: AsyncSession, rate_id: str) -> RateCalculationResponseDTO:
    try:
        return _to_dto(await rates_repo.get_by_id(db, rate_id))
    except NoResultFound:
        raise HTTPException(404, detail=f"Rate result {rate_id} not found.")


async def get_by_study_case(
    db: AsyncSession, case_id: str
) -> list[RateCalculationResponseDTO]:
    return [_to_dto(o) for o in await rates_repo.get_by_study_case(db, case_id)]


async def delete(db: AsyncSession, rate_id: str) -> None:
    deleted = await rates_repo.delete(db, rate_id)
    if not deleted:
        raise HTTPException(404, detail=f"Rate result {rate_id} not found.")


# Normalización

def _normalize_coordinates(coordinates: list[dict]) -> list[dict]:
    """
    Normaliza a clave canónica 'lon' y 'elevation'.
    Acepta 'lng' (Leaflet) o 'lon' (GeoJSON).
    Acepta 'altitud' o 'elevation' para la altitud.
    """
    normalized = []
    for c in coordinates:
        point = {
            "lat": c["lat"],
            "lon": c.get("lon") or c.get("lng", 0),
        }
        elevation = c.get("elevation") or c.get("altitud")
        if elevation is not None:
            point["elevation"] = elevation
        normalized.append(point)
    return normalized


# Cálculo principal

async def calculate_seasonal_rates(
    req:           RateCalculationRequestDTO,
    db:            AsyncSession,
    study_case_id: Optional[str] = None,
) -> dict:

    # 1. Normalización
    coordinates = _normalize_coordinates(req.coordinates)

    # 2. Validación geométrica
    validation = validate_route(coordinates)
    if not validation.valid:
        raise HTTPException(status_code=422, detail={
            "errors":   validation.errors,
            "warnings": validation.warnings,
            "info":     validation.info,
        })

    # 3. Enriquecimiento DEM
    elevation_source = "none"
    has_excel_z      = any((c.get("elevation") or 0) > 0 for c in coordinates)

    if has_excel_z:
        elevation_source = "excel_z"
    elif req.use_dem:
        try:
            coordinates      = await enrich_with_elevation(db, coordinates)
            elevation_source = "open_meteo_dem"
        except Exception as e:
            print(f"[DEM] Enrichment failed: {e}")
            elevation_source = "dem_error"

    # 4. Conductor — DTO → entidad de dominio
    conductor = Conductor(**req.conductor.model_dump())

    # 5. Escenarios meteorológicos
    scenarios: dict[Season, MeteoScenario] = (
        {
            s.season: MeteoScenario(
                name                = s.season,
                season              = s.season,
                temp_amb_c          = s.temp_amb_c,
                wind_speed_ms       = s.wind_speed_ms,
                wind_angle_deg      = s.wind_angle_deg,
                solar_radiation_wm2 = s.solar_radiation_wm2,
            )
            for s in req.scenarios
        }
        if req.scenarios
        else DEFAULT_SCENARIOS
    )

    # 6. Segmentación
    if req.use_real_spans and len(coordinates) >= 2:
        segments     = segment_by_spans(coordinates)
        segment_mode = f"real_spans ({len(segments)} spans)"
    elif req.segment_step_m > 0:
        segments     = segment_route(coordinates, req.segment_step_m)
        segment_mode = f"every_{req.segment_step_m:.0f}m"
    else:
        raise HTTPException(status_code=400, detail="Invalid segmentation.")

    if not segments:
        raise HTTPException(status_code=400, detail="No segments could be generated.")

    # 7. Cálculo IEEE 738 por segmento
    results = []
    for i, segment in enumerate(segments):
        elevation = float(segment.elevation_m or 0.0)
        acc       = SegmentAccumulator(
            segment_id      = segment.id,
            length_km       = segment.length_km,
            avg_elevation_m = elevation,
        )

        for season, scenario in scenarios.items():
            meteo = MeteoConditions(
                temp_amb_c          = scenario.temp_amb_c,
                wind_speed_ms       = scenario.wind_speed_ms,
                wind_angle_deg      = scenario.wind_angle_deg,
                solar_radiation_wm2 = scenario.solar_radiation_wm2,
                elevation_m         = elevation,
            )
            rating = _calculator.calcular(
                conductor        = conductor,
                meteo            = meteo,
                latitud_deg      = segment.mid_point["lat"],
                azimut_linea_deg = segment.azimuth_deg,
            )

            acc.rates[season]   = rating.ampacity_a   
            acc.details[season] = {
                "ampacity_a":  rating.ampacity_a,      
                "qc_wm":       rating.qc_wm,
                "qr_wm":       rating.qr_wm,
                "qs_wm":       rating.qs_wm,
                "r_tc_ohm_m":  rating.r_tc_ohm_m,
                "conv_mode":   rating.conv_mode,
                "elevation_m": elevation,
                "scenario": {
                    "temp_amb_c":          scenario.temp_amb_c,
                    "wind_speed_ms":       scenario.wind_speed_ms,
                    "solar_radiation_wm2": scenario.solar_radiation_wm2,
                },
            }

        results.append({
            "segment_id":    acc.segment_id,
            "index":         i,
            "length_km":     acc.length_km,
            "elevation_m":   elevation,
            "azimuth_deg":   segment.azimuth_deg,
            "mid_point":     segment.mid_point,
            "start_point":   segment.start_point,
            "end_point":     segment.end_point,
            "rates":         acc.rates,
            "details":       acc.details,
            "design_rate_a": min(acc.rates.values()),
        })

    # 8. Construir respuesta
    response = {
        "id":             str(uuid.uuid4()),
        "study_case_id":  study_case_id,
        "n_segments":     len(results),
        "conductor":      req.conductor.model_dump(),
        "segments":       results,
        "design_rate_a":  min(r["design_rate_a"] for r in results),
        "rates_by_season": {
            season: min(r["rates"].get(season, 9999) for r in results)
            for season in scenarios
        },
        "route_info": {
            **validation.info,
            "elevation_source": elevation_source,
            "segment_mode":     segment_mode,
            "min_elevation_m":  min(r["elevation_m"] for r in results),
            "max_elevation_m":  max(r["elevation_m"] for r in results),
            "avg_elevation_m":  round(
                sum(r["elevation_m"] for r in results) / len(results), 1
            ),
        },
        "warnings": validation.warnings,
    }

    # 9. Persistir en BD
    saved            = await rates_repo.save(db, response)
    response["created_at"] = saved.created_at.isoformat()

    return response