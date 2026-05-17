from dataclasses import dataclass, field
from typing import Literal
from app.domain.types import Season


# Conductor y cálculo térmico

@dataclass
class Conductor:
    # Parámetros eléctricos y térmicos del conductor.
    diameter_mm:      float
    r_ac_75_ohm_km:   float
    r_ac_25_ohm_km:   float
    emissivity:       float
    absorptivity:     float
    max_temp_c:       float


@dataclass
class MeteoConditions:
    # Condiciones meteorológicas de un punto y momento concreto.
    temp_amb_c:          float
    wind_speed_ms:       float
    wind_angle_deg:      float
    solar_radiation_wm2: float
    elevation_m:         float = 0.0


@dataclass
class SegmentRating:
    # Resultado del cálculo IEEE 738 para un segmento y escenario.
    ampacity_a:       float
    temp_conductor_c: float
    qc_wm:            float
    qr_wm:            float
    qs_wm:            float
    r_tc_ohm_m:       float
    conv_mode:        Literal["forced_low", "forced_high", "natural"]


# Segmentación

@dataclass
class Segment:
    # Segmento de la linea con geometría y altitud media.
    id:           str
    index:        int
    start_point:  dict
    mid_point:    dict
    end_point:    dict
    length_km:    float
    elevation_m:  float = 0.0
    azimuth_deg:  float = 90.0


# Validación 

@dataclass
class ValidationResult:
    # Resultado de validate_route.
    valid:    bool
    errors:   list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info:     dict      = field(default_factory=dict)


# Escenarios estacionales

@dataclass
class MeteoScenario:
    # Condiciones meteorológicas conservadoras de un escenario estacional.
    name:                str
    season:              Season
    temp_amb_c:          float
    wind_speed_ms:       float
    wind_angle_deg:      float
    solar_radiation_wm2: float
    description:         str = ""


@dataclass
class SegmentAccumulator:
    # Acumulador de resultados para un segmento durante el cálculo.
    segment_id:      str
    length_km:       float
    avg_elevation_m: float
    rates:           dict[Season, float] = field(default_factory=dict)
    details:         dict                = field(default_factory=dict)


# Climatología

@dataclass
class SeasonalPercentiles:
    # Percentiles estadísticos históricos para una estación concreta.
    season:            Season
    lat:               float
    lon:               float
    temp_p90_c:        float
    temp_p50_c:        float
    temp_p10_c:        float
    wind_p10_ms:       float
    wind_p50_ms:       float
    wind_p90_ms:       float
    radiation_p50_wm2: float
    radiation_p90_wm2: float
    n_hours:           int
    source:            str
    years_covered:     str