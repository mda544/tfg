from typing import List
from shapely.geometry import LineString, Point
from shapely.ops import transform
from pyproj import Transformer

from app.domain.entities import Segment
from app.domain.value_objects import GeoPoint
from app.core.utils.geo import haversine_m, calcular_azimut


def _project_line(coordinates: list[dict]) -> LineString:
    points = [(pt["lon"], pt["lat"]) for pt in coordinates]
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    return transform(transformer.transform, LineString(points))


def _to_geopoint(p: Point, transformer_inv: Transformer) -> GeoPoint:
    lon, lat = transformer_inv.transform(p.x, p.y)
    return GeoPoint(lat=round(lat, 6), lon=round(lon, 6))


def segment_route(coordinates: list[dict], step_m: float = 500.0) -> List[Segment]:
    """Segmenta el trazado en tramos de longitud fija."""
    line_proj = _project_line(coordinates)
    total_len = line_proj.length
    n_segments = max(1, int(total_len / step_m))
    step_real = total_len / n_segments
    transformer_inv = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
    segments = []

    for i in range(n_segments):
        d_start = i * step_real
        p_start = _to_geopoint(line_proj.interpolate(d_start), transformer_inv)
        p_mid = _to_geopoint(
            line_proj.interpolate(d_start + step_real / 2), transformer_inv
        )
        p_end = _to_geopoint(
            line_proj.interpolate(min(d_start + step_real, total_len)), transformer_inv
        )
        azimuth = calcular_azimut(p_start.lat, p_start.lon, p_end.lat, p_end.lon)

        segments.append(
            Segment(
                id=f"T{i + 1:03d}",
                index=i,
                start_point=p_start,
                mid_point=p_mid,
                end_point=p_end,
                length_km=round(step_real / 1000.0, 3),
                azimuth_deg=round(azimuth, 1),
            )
        )
    return segments


def segment_by_spans(coordinates: list[dict]) -> List[Segment]:
    """Crea un segmento por vano real entre apoyos consecutivos."""
    segments = []
    for i in range(len(coordinates) - 1):
        p_start = coordinates[i]
        p_end = coordinates[i + 1]
        elev = ((p_start.get("elevation") or 0) + (p_end.get("elevation") or 0)) / 2
        azimuth = calcular_azimut(
            p_start["lat"], p_start["lon"], p_end["lat"], p_end["lon"]
        )

        segments.append(
            Segment(
                id=f"V{i + 1:03d}",
                index=i,
                start_point=GeoPoint(lat=p_start["lat"], lon=p_start["lon"]),
                mid_point=GeoPoint(
                    lat=(p_start["lat"] + p_end["lat"]) / 2,
                    lon=(p_start["lon"] + p_end["lon"]) / 2,
                ),
                end_point=GeoPoint(lat=p_end["lat"], lon=p_end["lon"]),
                length_km=round(haversine_m(p_start, p_end) / 1000.0, 3),
                elevation_m=round(elev, 1),
                azimuth_deg=round(azimuth, 1),
            )
        )
    return segments
