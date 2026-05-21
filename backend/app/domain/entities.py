from dataclasses import dataclass
from app.domain.types import Season
from app.domain.value_objects import GeoPoint


@dataclass
class Conductor:
    """Entidad que representa el conductor eléctrico de la línea.
    Tiene identidad propia — puede persistirse y reutilizarse en
    múltiples casos de estudio."""

    diameter_mm: float
    r_ac_75_ohm_km: float
    r_ac_25_ohm_km: float
    emissivity: float
    absorptivity: float
    max_temp_c: float


@dataclass
class MeteoScenario:
    """Entidad que representa las condiciones meteorológicas de referencia
    para una estación del año. Puede persistirse asociada a un caso de estudio."""

    name: str
    season: Season
    temp_amb_c: float
    wind_speed_ms: float
    wind_angle_deg: float
    solar_radiation_wm2: float
    description: str = ""


@dataclass
class Segment:
    """Entidad que representa un tramo del trazado con su geometría y altitud.
    Producida por segmentation.py y persistida en la tabla segments."""

    id: str
    index: int
    start_point: GeoPoint
    mid_point: GeoPoint
    end_point: GeoPoint
    length_km: float
    elevation_m: float = 0.0
    azimuth_deg: float = 90.0


@dataclass
class SeasonalPercentiles:
    """Entidad que representa los percentiles históricos de un punto geográfico
    para una estación. Se persiste en climate_cache para evitar peticiones
    repetidas a las APIs externas."""

    season: Season
    lat: float
    lon: float
    temp_p90_c: float
    temp_p50_c: float
    temp_p10_c: float
    wind_p10_ms: float
    wind_p50_ms: float
    wind_p90_ms: float
    radiation_p50_wm2: float
    radiation_p90_wm2: float
    n_hours: int
    source: str
    years_covered: str
