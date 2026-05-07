from dataclasses import dataclass, field
from typing import Literal
from pydantic import BaseModel
from app.domain.types import Season


# ── Conductor y cálculo térmico ──────────────────────────────────────────────

@dataclass
class ConductorParams:
    """Parámetros eléctricos y térmicos del conductor.
    Entidad interna — se construye desde ConductorInput (DTO HTTP)
    en calculos_service y se pasa a IEEE738Calculator."""
    diametro_mm:      float
    r_ac_75_ohm_km:   float
    r_ac_25_ohm_km:   float
    emisividad:       float
    absortividad:     float
    temp_max_c:       float


@dataclass
class MeteoParams:
    """Condiciones meteorológicas de un punto y momento concreto.
    Se construye en calculos_service para cada tramo y escenario."""
    temp_amb_c:          float
    vel_viento_ms:       float
    angulo_viento_deg:   float
    radiacion_solar_wm2: float
    altitud_m:           float = 0.0


@dataclass
class RateResult:
    """Resultado del cálculo IEEE 738 para un tramo y escenario.
    Lo produce IEEE738Calculator y lo consume calculos_service
    para construir la respuesta final."""
    ampacidad_a:      float
    temp_conductor_c: float
    qc_wm:            float
    qr_wm:            float
    qs_wm:            float
    r_tc_ohm_m:       float
    modo_conveccion:  Literal["forzada_baja", "forzada_alta", "natural"]


# ── Segmentación ─────────────────────────────────────────────────────────────

@dataclass
class Tramo:
    """Segmento del trazado con su geometría y altitud media.
    Lo producen segmentar_trazado y segmentar_por_apoyos.
    Lo consume calculos_service para iterar el cálculo IEEE 738."""
    id:           str
    indice:       int
    punto_inicio: dict
    punto_medio:  dict
    punto_fin:    dict
    longitud_km:  float
    altitud_m:    float = 0.0
    azimut_deg:   float = 90.0


# ── Validación ───────────────────────────────────────────────────────────────

@dataclass
class ResultadoValidacion:
    """Resultado de validar_trazado.
    Si valido=False, calculos_service lanza 422 con errores e info."""
    valido:       bool
    errores:      list[str] = field(default_factory=list)
    advertencias: list[str] = field(default_factory=list)
    info:         dict      = field(default_factory=dict)


# ── Escenarios estacionales ──────────────────────────────────────────────────

@dataclass
class ScenarioMeteo:
    """Condiciones meteorológicas conservadoras de un escenario estacional.
    ESCENARIOS_DEFAULT contiene los valores por defecto para la Península.
    El usuario puede sobreescribirlos vía ScenarioInput (DTO HTTP)."""
    nombre:              str
    estacion:            Season
    temp_amb_c:          float
    vel_viento_ms:       float
    angulo_viento_deg:   float
    radiacion_solar_wm2: float
    descripcion:         str = ""


@dataclass
class SeasonalRates:
    """Acumulador de resultados para un tramo durante el cálculo.
    Solo vive dentro de calculos_service — no sale por la API directamente,
    su contenido se vuelca en el dict de respuesta."""
    id_tramo:        str
    longitud_km:     float
    altitud_media_m: float
    rates:           dict[Season, float] = field(default_factory=dict)
    detalles:        dict                = field(default_factory=dict)


# ── Climatología ─────────────────────────────────────────────────────────────

class PercentilesEstacionales(BaseModel):
    """Percentiles estadísticos históricos para una estación concreta.
    Hereda de BaseModel (no @dataclass) para poder usarse directamente
    como schema de respuesta en PercentilesResponse sin clase duplicada.
    La produce ClimateProcessor y la cachea historical_cache en disco."""
    estacion:          Season
    lat:               float
    lon:               float
    temp_p90_c:        float
    temp_p50_c:        float
    temp_p10_c:        float
    viento_p10_ms:     float
    viento_p50_ms:     float
    viento_p90_ms:     float
    radiacion_p50_wm2: float
    radiacion_p90_wm2: float
    n_horas:           int
    fuente:            str
    anios_cubiertos:   str