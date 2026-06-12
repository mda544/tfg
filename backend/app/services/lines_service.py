from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound

from app.domain.exceptions import EntityNotFoundError, ValidationError
from app.domain.geo import haversine_m
from app.domain.value_objects import GeoPoint
from app.infrastructure.repositories.lines_repository import lines_repo
from app.infrastructure.mappers.lines_mapper import create_dto_to_entity, entity_to_dto
from app.services.elevation_service import add_elevation
from app.api.schemas.models import LineCreateDTO, LineResponseDTO

_MAX_POINTS = 10_000
_MIN_POINTS = 2


def _calc_length_km(coordinates) -> float:
    total_m = sum(
        haversine_m(
            {"lat": coordinates[i].lat, "lon": coordinates[i].lon},
            {"lat": coordinates[i + 1].lat, "lon": coordinates[i + 1].lon},
        )
        for i in range(len(coordinates) - 1)
    )
    return round(total_m / 1000.0, 3)


def _set_bbox(entity, coordinates):
    entity.bbox_lat_min = min(c.lat for c in coordinates)
    entity.bbox_lat_max = max(c.lat for c in coordinates)
    entity.bbox_lon_min = min(c.lon for c in coordinates)
    entity.bbox_lon_max = max(c.lon for c in coordinates)


async def get_all(db: AsyncSession, user_id: str) -> list[LineResponseDTO]:
    return [entity_to_dto(e) for e in await lines_repo.get_all(db, user_id)]


async def get_by_id(db: AsyncSession, line_id: str, user_id: str) -> LineResponseDTO:
    try:
        return entity_to_dto(await lines_repo.get_by_id(db, line_id, user_id))
    except NoResultFound:
        raise EntityNotFoundError(f"Line {line_id} not found.")


async def create(
    db: AsyncSession, data: LineCreateDTO, user_id: str
) -> LineResponseDTO:
    if len(data.coordinates) < _MIN_POINTS:
        raise ValidationError("El trazado necesita al menos 2 puntos.")
    if len(data.coordinates) > _MAX_POINTS:
        raise ValidationError(
            f"El trazado no puede superar los {_MAX_POINTS:,} puntos."
            f" Recibidos: {len(data.coordinates)}."
        )

    entity = create_dto_to_entity(data)

    # Enriquecer con DEM si no hay elevación del archivo
    has_file_elevation = any(c.elevation_m is not None for c in entity.coordinates)
    if has_file_elevation:
        entity.elevation_source = "file"
    else:
        try:
            raw = [{"lat": c.lat, "lon": c.lon} for c in entity.coordinates]
            enriched = await add_elevation(db, raw)
            entity.coordinates = [
                GeoPoint(
                    lat=c.lat,
                    lon=c.lon,
                    elevation_m=enriched[i].get("elevation_m") or None,
                )
                for i, c in enumerate(entity.coordinates)
            ]
            entity.elevation_source = "dem"
        except Exception as e:
            print(f"[DEM] Line enrichment failed: {e}")

    # Calcular métricas sobre las coordenadas definitivas
    entity.length_km = _calc_length_km(entity.coordinates)
    entity.n_points = len(entity.coordinates)
    _set_bbox(entity, entity.coordinates)

    # Calcular stats de elevación para los campos min/max/avg
    elevations = [c.elevation_m for c in entity.coordinates if c.elevation_m]
    if elevations:
        entity.min_elevation_m = round(min(elevations), 1)
        entity.max_elevation_m = round(max(elevations), 1)
        entity.avg_elevation_m = round(sum(elevations) / len(elevations), 1)

    return entity_to_dto(await lines_repo.create(db, user_id, entity))


async def update(
    db: AsyncSession, line_id: str, data: LineCreateDTO, user_id: str
) -> LineResponseDTO:
    try:
        entity = create_dto_to_entity(data)
        entity.length_km = _calc_length_km(entity.coordinates)
        entity.n_points = len(entity.coordinates)
        _set_bbox(entity, entity.coordinates)
        return entity_to_dto(await lines_repo.update(db, line_id, user_id, entity))
    except NoResultFound:
        raise EntityNotFoundError(f"Line {line_id} not found.")


async def delete(db: AsyncSession, line_id: str, user_id: str) -> None:
    if not await lines_repo.delete(db, line_id, user_id):
        raise EntityNotFoundError(f"Line {line_id} not found.")
