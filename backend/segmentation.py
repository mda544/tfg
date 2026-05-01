from dataclasses import dataclass
from shapely.geometry import LineString, Point
from shapely.ops import transform
from pyproj import Transformer
from typing import List
import math

@dataclass
class Tramo:
    id: str
    indice: int
    punto_inicio: dict
    punto_medio: dict
    punto_fin: dict
    longitud_km: float
    altitud_m: float = 0.0

def proyectar_linea(coordenadas: list[dict]) -> LineString:
    puntos = [(pt["lng"], pt["lat"]) for pt in coordenadas]
    linea_geo = LineString(puntos)
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    return transform(transformer.transform, linea_geo)

def _punto_a_wgs84(p: Point, transformer_inv: Transformer) -> dict:
    lon, lat = transformer_inv.transform(p.x, p.y)
    return {"lat": round(lat, 6), "lon": round(lon, 6)}

def _haversine_m(a: dict, b: dict) -> float:
    """Distancia en metros entre dos puntos {lat, lng/lon}."""
    R = 6_371_000.0
    lat1 = math.radians(a["lat"])
    lat2 = math.radians(b["lat"])
    lon1 = math.radians(a.get("lon") or a.get("lng", 0))
    lon2 = math.radians(b.get("lon") or b.get("lng", 0))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    x = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 2 * R * math.asin(math.sqrt(x))

def segmentar_trazado(
    coordenadas: list[dict],
    paso_m: float = 500.0,
) -> List[Tramo]:
    linea_proj = proyectar_linea(coordenadas)
    longitud_total = linea_proj.length
    n_tramos = max(1, int(longitud_total / paso_m))
    paso_real = longitud_total / n_tramos

    transformer_inv = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
    tramos = []

    for i in range(n_tramos):
        d_inicio = i * paso_real
        d_medio  = d_inicio + paso_real / 2.0
        d_fin    = d_inicio + paso_real

        p_ini  = linea_proj.interpolate(d_inicio)
        p_mid  = linea_proj.interpolate(d_medio)
        p_fin  = linea_proj.interpolate(min(d_fin, longitud_total))

        tramos.append(Tramo(
            id=f"T{i+1:03d}",
            indice=i,
            punto_inicio=_punto_a_wgs84(p_ini, transformer_inv),
            punto_medio=_punto_a_wgs84(p_mid, transformer_inv),
            punto_fin=_punto_a_wgs84(p_fin, transformer_inv),
            longitud_km=round(paso_real / 1000.0, 3),
        ))

    return tramos

def segmentar_por_apoyos(coordenadas: list[dict]) -> list[Tramo]:
    """
    Crea un tramo por vano real entre apoyos consecutivos.
    Usa las coordenadas del Excel directamente, incluyendo altitud Z si existe.
    Ideal cuando el trazado viene de un fichero con apoyos reales.
    """
    tramos = []
    for i in range(len(coordenadas) - 1):
        p_ini = coordenadas[i]
        p_fin = coordenadas[i + 1]
        
        # Normalizar clave lon/lng
        lon_ini = p_ini.get("lon") or p_ini.get("lng", 0)
        lon_fin = p_fin.get("lon") or p_fin.get("lng", 0)
        
        # Altitud media del vano — usa Z del Excel si existe, 0 si no
        alt_ini = p_ini.get("altitud", 0) or 0
        alt_fin = p_fin.get("altitud", 0) or 0
        altitud_media = (alt_ini + alt_fin) / 2.0
        
        longitud_m = _haversine_m(
            {"lat": p_ini["lat"], "lng": lon_ini},
            {"lat": p_fin["lat"],  "lng": lon_fin},
        )
        
        tramos.append(Tramo(
            id=f"V{i+1:03d}",
            indice=i,
            punto_inicio={"lat": p_ini["lat"], "lon": lon_ini},
            punto_medio={
                "lat": (p_ini["lat"] + p_fin["lat"]) / 2,
                "lon": (lon_ini + lon_fin) / 2,
            },
            punto_fin={"lat": p_fin["lat"], "lon": lon_fin},
            longitud_km=round(longitud_m / 1000.0, 3),
            altitud_m=round(altitud_media, 1),
        ))
    return tramos