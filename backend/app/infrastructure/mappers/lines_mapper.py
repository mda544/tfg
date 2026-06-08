from geoalchemy2.shape import to_shape
from shapely.geometry import mapping

from app.api.schemas.models import LineCreateDTO, LineResponseDTO
from app.domain.entities import Line
from app.domain.value_objects import GeoPoint
from app.infrastructure.orm_models import LineORM


def create_dto_to_entity(dto: LineCreateDTO) -> Line:
    return Line(
        name=dto.name,
        description=dto.description or "",
        coordinates=[GeoPoint(lat=c.lat, lon=c.lon) for c in dto.coordinates],
    )


def entity_to_wkt(entity: Line) -> str:
    pts = ", ".join(f"{c.lon} {c.lat}" for c in entity.coordinates)
    return f"LINESTRING({pts})"


def orm_to_entity(obj: LineORM) -> Line:
    shape = to_shape(obj.geometry)
    return Line(
        id=obj.id,
        name=obj.name,
        description=obj.description or "",
        coordinates=[GeoPoint(lat=lat, lon=lon) for lon, lat in shape.coords],
        length_km=obj.length_km,
        n_points=obj.n_points,
        bbox_lat_min=obj.bbox_lat_min,
        bbox_lat_max=obj.bbox_lat_max,
        bbox_lon_min=obj.bbox_lon_min,
        bbox_lon_max=obj.bbox_lon_max,
        min_elevation_m=obj.min_elevation_m,
        max_elevation_m=obj.max_elevation_m,
        avg_elevation_m=obj.avg_elevation_m,
        created_at=obj.created_at.isoformat(),
        updated_at=obj.updated_at.isoformat(),
    )


def entity_to_dto(entity: Line) -> LineResponseDTO:
    coords = [(c.lon, c.lat) for c in entity.coordinates]
    return LineResponseDTO(
        id=entity.id,
        name=entity.name,
        description=entity.description,
        length_km=entity.length_km,
        n_points=entity.n_points,
        bbox_lat_min=entity.bbox_lat_min,
        bbox_lat_max=entity.bbox_lat_max,
        bbox_lon_min=entity.bbox_lon_min,
        bbox_lon_max=entity.bbox_lon_max,
        min_elevation_m=entity.min_elevation_m,
        max_elevation_m=entity.max_elevation_m,
        avg_elevation_m=entity.avg_elevation_m,
        geometry_geojson={"type": "LineString", "coordinates": coords},
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )
