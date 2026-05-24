import math
from typing import Union


def _get_lat_lon(c) -> tuple[float, float]:
    if hasattr(c, "lat") and hasattr(c, "lon"):
        return c.lat, c.lon
    return c["lat"], c.get("lon") or c.get("lng", 0)


def haversine_m(a, b) -> float:

    R = 6_371_000.0
    lat1, lon1 = map(math.radians, _get_lat_lon(a))
    lat2, lon2 = map(math.radians, _get_lat_lon(b))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    x = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    return 2 * R * math.asin(math.sqrt(x))


def calcular_azimut(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula el azimut (orientación respecto al Norte) entre dos puntos GPS."""
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(
        dlon
    )
    return (math.degrees(math.atan2(x, y)) + 360) % 360
