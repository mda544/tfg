from dataclasses import dataclass, field
from typing import Literal
from app.domain.types import Season


@dataclass(frozen=True)
class GeoPoint:
    """Value Object que representa un punto geográfico en WGS84.
    Clave canónica: lat, lon."""

    lat: float
    lon: float


@dataclass(frozen=True)
class PointMeteoConditions:
    """Value Object que representa las condiciones meteorológicas concretas
    en un punto geográfico y altitud específicos durante el cálculo IEEE 738.
    Es inmutable — se crea para cada segmento y escenario y se descarta."""

    temp_amb_c: float
    wind_speed_ms: float
    wind_angle_deg: float
    solar_radiation_wm2: float
    elevation_m: float = 0.0


@dataclass(frozen=True)
class SegmentRating:
    """Value Object que representa el resultado del cálculo IEEE 738
    para un segmento y un escenario estacional concreto.
    Inmutable — producido por IEEE738Calculator."""

    ampacity_a: float
    temp_conductor_c: float
    qc_wm: float
    qr_wm: float
    qs_wm: float
    r_tc_ohm_m: float
    conv_mode: Literal["forced_low", "forced_high", "natural"]


@dataclass(frozen=True)
class ValidationResult:
    """Value Object que representa el resultado de validar la geometría
    de un trazado. Inmutable — producido por validate_route()."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info: dict = field(default_factory=dict)


@dataclass
class SegmentResults:
    """Value Object que acumula los SegmentRating de los cuatro escenarios
    estacionales para un mismo segmento durante el cálculo.
    No es inmutable porque se construye incrementalmente en rates_service."""

    segment_id: str
    length_km: float
    avg_elevation_m: float
    rates: dict[Season, float] = field(default_factory=dict)
    details: dict = field(default_factory=dict)
