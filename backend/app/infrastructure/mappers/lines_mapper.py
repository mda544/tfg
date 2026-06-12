from geoalchemy2.shape import to_shape, from_shape
from shapely.geometry import LineString as ShapelyLineString

from app.api.schemas.models import LineCreateDTO, LineResponseDTO
from app.domain.entities import Line
from app.domain.value_objects import GeoPoint
from app.infrastructure.orm_models import LineORM


def create_dto_to_entity(dto: LineCreateDTO) -> Line:
    return Line(
        name=dto.name,
        description=dto.description or "",
        coordinates=[
            GeoPoint(lat=c.lat, lon=c.lon, elevation_m=c.elevation_m)
            for c in dto.coordinates
        ],
    )


def entity_to_geometry(entity: Line):
    """Convierte las coordenadas a WKBElement de GeoAlchemy2 usando Shapely.
    Siempre genera LINESTRING Z — usa 0.0 cuando no hay elevación del archivo.
    Esto garantiza compatibilidad con la columna GeometryZ(4326) de PostGIS."""
    coords = [(c.lon, c.lat, c.elevation_m or 0.0) for c in entity.coordinates]
    return from_shape(ShapelyLineString(coords), srid=4326)


def entity_to_orm(entity: Line, owner_id: str) -> LineORM:
    """El servicio calcula length_km, n_points y bbox antes de llamar aquí."""
    elev_stats = _elevation_stats(entity.coordinates)
    return LineORM(
        owner_id=owner_id,
        name=entity.name,
        description=entity.description,
        geometry=entity_to_geometry(entity),
        length_km=entity.length_km,
        n_points=entity.n_points,
        bbox_lat_min=entity.bbox_lat_min,
        bbox_lat_max=entity.bbox_lat_max,
        bbox_lon_min=entity.bbox_lon_min,
        bbox_lon_max=entity.bbox_lon_max,
        min_elevation_m=elev_stats["min"] if elev_stats else None,
        max_elevation_m=elev_stats["max"] if elev_stats else None,
        avg_elevation_m=elev_stats["avg"] if elev_stats else None,
        elevation_source=entity.elevation_source,
    )


def orm_to_entity(obj: LineORM) -> Line:
    shape = to_shape(obj.geometry)
    raw_coords = list(shape.coords)
    has_z = len(raw_coords[0]) == 3 if raw_coords else False

    coordinates = [
        GeoPoint(
            lat=lat,
            lon=lon,
            elevation_m=round(z, 1) if (has_z and z != 0.0) else None,
        )
        for coord in raw_coords
        for lon, lat, *zval in [coord]
        for z in (zval if zval else [None])
    ]

    return Line(
        id=obj.id,
        name=obj.name,
        description=obj.description or "",
        coordinates=coordinates,
        length_km=obj.length_km,
        n_points=obj.n_points,
        bbox_lat_min=obj.bbox_lat_min,
        bbox_lat_max=obj.bbox_lat_max,
        bbox_lon_min=obj.bbox_lon_min,
        bbox_lon_max=obj.bbox_lon_max,
        min_elevation_m=obj.min_elevation_m,
        max_elevation_m=obj.max_elevation_m,
        avg_elevation_m=obj.avg_elevation_m,
        elevation_source=obj.elevation_source,
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
        elevation_source=entity.elevation_source,
        geometry_geojson={"type": "LineString", "coordinates": coords},
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def _elevation_stats(coordinates) -> dict | None:
    elevations = [c.elevation_m for c in coordinates if c.elevation_m is not None]
    if not elevations:
        return None
    return {
        "min": round(min(elevations), 1),
        "max": round(max(elevations), 1),
        "avg": round(sum(elevations) / len(elevations), 1),
    }
