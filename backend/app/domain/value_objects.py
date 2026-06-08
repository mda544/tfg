from dataclasses import dataclass, field
from typing import Literal
from app.domain.types import Season, ConvMode


@dataclass(frozen=True)
class GeoPoint:
    """Punto geográfico WGS84."""

    lat: float
    lon: float


@dataclass(frozen=True)
class WeatherInput:
    """Condiciones meteorológicas para un escenario estacional.
    Son la entrada del cálculo IEEE 738 — persisten en rate_weather_inputs."""

    season: Season
    temp_amb_c: float
    wind_speed_ms: float
    wind_angle_deg: float
    solar_radiation_wm2: float


@dataclass(frozen=True)
class PointMeteoConditions:
    """WeatherInput + elevation_m del segmento.
    Se crea justo antes de llamar a IEEE738Calculator."""

    temp_amb_c: float
    wind_speed_ms: float
    wind_angle_deg: float
    solar_radiation_wm2: float
    elevation_m: float = 0.0


@dataclass(frozen=True)
class SegmentRating:
    """Resultado IEEE 738 para un segmento y escenario concreto.
    Inmutable — producido por IEEE738Calculator."""

    ampacity: float
    temp_conductor_c: float
    qc_wm: float
    qr_wm: float
    qs_wm: float
    r_tc_ohm_m: float
    conv_mode: ConvMode


@dataclass(frozen=True)
class ValidationResult:
    """Resultado de validar la geometría de un trazado."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info: dict = field(default_factory=dict)
