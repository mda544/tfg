import math
from typing import Union

import numpy as np


def _get_lat_lon(c) -> tuple[float, float]:
    if hasattr(c, "lat") and hasattr(c, "lon"):
        return c.lat, c.lon
    return c["lat"], c.get("lon") or c.get("lng", 0)


def haversine_m(a, b) -> float:
    """Distancia en metros entre dos puntos geográficos usando la fórmula Haversine."""
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


def circular_mean(angles_deg: np.ndarray) -> float:
    """Media circular para ángulos en grados (0-360).
    Se usa para calcular la dirección predominante del viento histórico."""
    if len(angles_deg) == 0:
        return 0.0
    rad = np.deg2rad(angles_deg)
    sin_m = np.mean(np.sin(rad))
    cos_m = np.mean(np.cos(rad))
    return round(float(np.rad2deg(np.arctan2(sin_m, cos_m)) % 360), 1)


def wind_angle_for_segment(
    wind_dir_predominant_deg: float | None,
    segment_azimuth_deg: float,
    user_wind_angle_deg: float,
) -> float:
    """Calcula el ángulo efectivo viento-conductor (φ) para un segmento.
    Si no hay dirección (NASA POWER o escenario manual) 
    usa el ángulo introducido por el usuario (90° por defecto)
    """
    if wind_dir_predominant_deg is None:
        return user_wind_angle_deg

    phi = abs(wind_dir_predominant_deg - segment_azimuth_deg) % 180.0
    if phi > 90.0:
        phi = 180.0 - phi
    return round(phi, 1)
