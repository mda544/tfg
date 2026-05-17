from typing import List
from shapely.geometry import LineString, Point
from shapely.ops import transform
from pyproj import Transformer

from app.domain.entities import Segment
from app.core.utils.geo import haversine_m, calcular_azimut


def _project_line(coordinates: list[dict]) -> LineString:
    points      = [(pt["lon"], pt["lat"]) for pt in coordinates]
    line_geo    = LineString(points)
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    return transform(transformer.transform, line_geo)


def _to_wgs84(p: Point, transformer_inv: Transformer) -> dict:
    lon, lat = transformer_inv.transform(p.x, p.y)
    return {"lat": round(lat, 6), "lon": round(lon, 6)}


# Segmenta el trazado en tramos de longitud fija.
def segment_route(
    coordinates: list[dict],
    step_m:      float = 500.0,
) -> List[Segment]:
    line_proj   = _project_line(coordinates)
    total_len   = line_proj.length
    n_segments  = max(1, int(total_len / step_m))
    step_real   = total_len / n_segments

    transformer_inv = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
    segments = []

    for i in range(n_segments):
        d_start = i * step_real
        d_mid   = d_start + step_real / 2.0
        d_end   = d_start + step_real

        p_start = line_proj.interpolate(d_start)
        p_mid   = line_proj.interpolate(d_mid)
        p_end   = line_proj.interpolate(min(d_end, total_len))

        pt_start = _to_wgs84(p_start, transformer_inv)
        pt_end   = _to_wgs84(p_end,   transformer_inv)
        azimuth  = calcular_azimut(
            pt_start["lat"], pt_start["lon"],
            pt_end["lat"],   pt_end["lon"],
        )

        segments.append(Segment(
            id          = f"T{i + 1:03d}",
            index       = i,
            start_point = pt_start,
            mid_point   = _to_wgs84(p_mid, transformer_inv),
            end_point   = pt_end,
            length_km   = round(step_real / 1000.0, 3),
            azimuth_deg = round(azimuth, 1),
        ))

    return segments

# Crea un segmento por vano real entre apoyos consecutivos.
def segment_by_spans(coordinates: list[dict]) -> List[Segment]:
    segments = []
    for i in range(len(coordinates) - 1):
        p_start    = coordinates[i]
        p_end      = coordinates[i + 1]
        elev_start = p_start.get("elevation", 0) or 0
        elev_end   = p_end.get("elevation", 0) or 0
        length_m   = haversine_m(p_start, p_end)
        azimuth    = calcular_azimut(
            p_start["lat"], p_start["lon"],
            p_end["lat"],   p_end["lon"],
        )

        segments.append(Segment(
            id          = f"V{i + 1:03d}",
            index       = i,
            start_point = {"lat": p_start["lat"], "lon": p_start["lon"]},
            mid_point   = {
                "lat": (p_start["lat"] + p_end["lat"]) / 2,
                "lon": (p_start["lon"] + p_end["lon"]) / 2,
            },
            end_point   = {"lat": p_end["lat"], "lon": p_end["lon"]},
            length_km   = round(length_m / 1000.0, 3),
            elevation_m = round((elev_start + elev_end) / 2.0, 1),
            azimuth_deg = round(azimuth, 1),
        ))

    return segments