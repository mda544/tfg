from typing import List
from shapely.geometry import LineString, Point
from shapely.ops import transform
from pyproj import Transformer

from app.domain.entities import Segment
from app.domain.value_objects import GeoPoint
from app.domain.geo import haversine_m, calcular_azimut


def _project_line(coordinates: list[dict]) -> LineString:
    points = [(pt["lon"], pt["lat"]) for pt in coordinates]
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    return transform(transformer.transform, LineString(points))


def _to_geopoint(p: Point, transformer_inv: Transformer) -> GeoPoint:
    lon, lat = transformer_inv.transform(p.x, p.y)
    return GeoPoint(lat=round(lat, 6), lon=round(lon, 6))


def _geodesic_length_m(coordinates: list[dict]) -> float:
    """Longitud total del trazado en metros usando Haversine (geodésica real).
    No usar EPSG:3857 para esto — la proyección Mercator distorsiona las
    distancias hasta un 24% a 43°N."""
    return sum(
        haversine_m(coordinates[i], coordinates[i + 1])
        for i in range(len(coordinates) - 1)
    )


def _interpolate_elevation_linear(
    coordinates: list[dict], mid_point: GeoPoint
) -> float:
    """Interpola la elevación del punto medio de un segmento entre los apoyos
    que tienen elevation_m definida. Si ninguno tiene elevación devuelve 0.0."""
    pts_with_elev = [
        c for c in coordinates
        if c.get("elevation_m") is not None and c["elevation_m"] > 0
    ]
    if not pts_with_elev:
        return 0.0
    if len(pts_with_elev) == 1:
        return float(pts_with_elev[0]["elevation_m"])

    def dist(c):
        return haversine_m(
            {"lat": c["lat"], "lon": c["lon"]},
            {"lat": mid_point.lat, "lon": mid_point.lon},
        )

    sorted_pts = sorted(pts_with_elev, key=dist)
    p1, p2 = sorted_pts[0], sorted_pts[1]
    d1, d2 = dist(p1), dist(p2)
    total = d1 + d2
    if total == 0:
        return float(p1["elevation_m"])
    elev = (p1["elevation_m"] * d2 + p2["elevation_m"] * d1) / total
    return round(elev, 1)


def segment_route(coordinates: list[dict], step_m: float = 500.0) -> List[Segment]:
    """Segmenta el trazado en tramos de longitud aproximadamente fija."""
    # Longitud real en metros — sin distorsión de proyección
    total_geodesic_m = _geodesic_length_m(coordinates)
    n_segments = max(1, int(total_geodesic_m / step_m))

    # Proyectar solo para interpolar posiciones a lo largo de la línea
    line_proj       = _project_line(coordinates)
    total_proj_m    = line_proj.length
    step_proj       = total_proj_m / n_segments   # paso en metros proyectados
    step_geodesic   = total_geodesic_m / n_segments

    transformer_inv = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
    segments = []

    for i in range(n_segments):
        d_start = i * step_proj
        p_start = _to_geopoint(line_proj.interpolate(d_start), transformer_inv)
        p_mid   = _to_geopoint(
            line_proj.interpolate(d_start + step_proj / 2), transformer_inv
        )
        p_end   = _to_geopoint(
            line_proj.interpolate(min(d_start + step_proj, total_proj_m)), transformer_inv
        )
        azimuth   = calcular_azimut(p_start.lat, p_start.lon, p_end.lat, p_end.lon)
        elevation = _interpolate_elevation_linear(coordinates, p_mid)

        segments.append(
            Segment(
                id          = f"T{i + 1:03d}",
                index       = i,
                start_point = p_start,
                mid_point   = p_mid,
                end_point   = p_end,
                length_km   = round(step_geodesic / 1000.0, 3),
                azimuth_deg = round(azimuth, 1),
                elevation_m = elevation,
            )
        )
    return segments


def segment_by_spans(coordinates: list[dict]) -> List[Segment]:
    """Crea un segmento por vano real entre apoyos consecutivos."""
    segments = []
    for i in range(len(coordinates) - 1):
        p_start = coordinates[i]
        p_end   = coordinates[i + 1]
        elev    = ((p_start.get("elevation_m") or 0) + (p_end.get("elevation_m") or 0)) / 2
        azimuth = calcular_azimut(
            p_start["lat"], p_start["lon"],
            p_end["lat"],   p_end["lon"],
        )
        segments.append(
            Segment(
                id          = f"V{i + 1:03d}",
                index       = i,
                start_point = GeoPoint(lat=p_start["lat"], lon=p_start["lon"]),
                mid_point   = GeoPoint(
                    lat=(p_start["lat"] + p_end["lat"]) / 2,
                    lon=(p_start["lon"] + p_end["lon"]) / 2,
                ),
                end_point   = GeoPoint(lat=p_end["lat"], lon=p_end["lon"]),
                length_km   = round(haversine_m(p_start, p_end) / 1000.0, 3),
                elevation_m = round(elev, 1),
                azimuth_deg = round(azimuth, 1),
            )
        )
    return segments