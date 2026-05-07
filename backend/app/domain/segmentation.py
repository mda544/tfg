from dataclasses import dataclass
from shapely.geometry import LineString, Point
from shapely.ops import transform
from pyproj import Transformer
from typing import List

from app.core.utils.geo import haversine_m, calcular_azimut


@dataclass
class Tramo:
    id: str
    indice: int
    punto_inicio: dict
    punto_medio: dict
    punto_fin: dict
    longitud_km: float
    altitud_m: float = 0.0
    azimut_deg: float = 90.0


def _proyectar_linea(coordenadas: list[dict]) -> LineString:
    puntos = [(pt["lon"], pt["lat"]) for pt in coordenadas]
    linea_geo = LineString(puntos)
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    return transform(transformer.transform, linea_geo)


def _punto_a_wgs84(p: Point, transformer_inv: Transformer) -> dict:
    lon, lat = transformer_inv.transform(p.x, p.y)
    return {"lat": round(lat, 6), "lon": round(lon, 6)}


def segmentar_trazado(
    coordenadas: list[dict],
    paso_m: float = 500.0,
) -> List[Tramo]:
    linea_proj = _proyectar_linea(coordenadas)
    longitud_total = linea_proj.length
    n_tramos = max(1, int(longitud_total / paso_m))
    paso_real = longitud_total / n_tramos

    transformer_inv = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
    tramos = []

    for i in range(n_tramos):
        d_inicio = i * paso_real
        d_medio  = d_inicio + paso_real / 2.0
        d_fin    = d_inicio + paso_real

        p_ini = linea_proj.interpolate(d_inicio)
        p_mid = linea_proj.interpolate(d_medio)
        p_fin = linea_proj.interpolate(min(d_fin, longitud_total))

        pt_inicio = _punto_a_wgs84(p_ini, transformer_inv)
        pt_fin    = _punto_a_wgs84(p_fin, transformer_inv)

        azimut = calcular_azimut(
            pt_inicio["lat"], pt_inicio["lon"],
            pt_fin["lat"],    pt_fin["lon"],
        )

        tramos.append(Tramo(
            id=f"T{i + 1:03d}",
            indice=i,
            punto_inicio=pt_inicio,
            punto_medio=_punto_a_wgs84(p_mid, transformer_inv),
            punto_fin=pt_fin,
            longitud_km=round(paso_real / 1000.0, 3),
            azimut_deg=round(azimut, 1),
        ))

    return tramos


def segmentar_por_apoyos(coordenadas: list[dict]) -> List[Tramo]:
    """
    Crea un tramo por vano real entre apoyos consecutivos.
    Usa las coordenadas del Excel directamente, incluyendo altitud Z si existe.
    Coordenadas ya normalizadas a clave canónica 'lon'.
    """
    tramos = []
    for i in range(len(coordenadas) - 1):
        p_ini = coordenadas[i]
        p_fin = coordenadas[i + 1]

        alt_ini = p_ini.get("altitud", 0) or 0
        alt_fin = p_fin.get("altitud", 0) or 0
        altitud_media = (alt_ini + alt_fin) / 2.0

        longitud_m = haversine_m(p_ini, p_fin)
        azimut     = calcular_azimut(
            p_ini["lat"], p_ini["lon"],
            p_fin["lat"], p_fin["lon"],
        )

        tramos.append(Tramo(
            id=f"V{i + 1:03d}",
            indice=i,
            punto_inicio={"lat": p_ini["lat"], "lon": p_ini["lon"]},
            punto_medio={
                "lat": (p_ini["lat"] + p_fin["lat"]) / 2,
                "lon": (p_ini["lon"] + p_fin["lon"]) / 2,
            },
            punto_fin={"lat": p_fin["lat"], "lon": p_fin["lon"]},
            longitud_km=round(longitud_m / 1000.0, 3),
            altitud_m=round(altitud_media, 1),
            azimut_deg=round(azimut, 1),
        ))

    return tramos
