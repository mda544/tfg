from dataclasses import dataclass, field

from app.domain.types import Season


@dataclass
class ScenarioMeteo:
    """
    Parámetros meteorológicos representativos de un escenario estacional.
    Los valores deben reflejar condiciones conservadoras (percentil alto de temperatura,
    percentil bajo de viento) para que el rate resultante sea seguro.
    """
    nombre: str
    estacion: Season
    temp_amb_c: float
    vel_viento_ms: float
    angulo_viento_deg: float  # 90° = perpendicular al conductor (caso más desfavorable)
    radiacion_solar_wm2: float
    descripcion: str = ""


# Escenarios por defecto para la Península Ibérica
# Fuente de referencia para calibrar: ERA5 percentil 90 Ta / percentil 10 viento
ESCENARIOS_DEFAULT: dict[Season, ScenarioMeteo] = {
    "verano": ScenarioMeteo(
        nombre="Verano peninsular",
        estacion="verano",
        temp_amb_c=38.0,       # P90 temperatura en julio/agosto
        vel_viento_ms=0.6,     # P10 velocidad: condición más restrictiva
        angulo_viento_deg=90.0,
        radiacion_solar_wm2=900.0,
        descripcion="Condición más restrictiva del año. Verano con calma de vientos.",
    ),
    "otono": ScenarioMeteo(
        nombre="Otoño peninsular",
        estacion="otono",
        temp_amb_c=20.0,
        vel_viento_ms=2.0,
        angulo_viento_deg=90.0,
        radiacion_solar_wm2=500.0,
        descripcion="Condición intermedia.",
    ),
    "invierno": ScenarioMeteo(
        nombre="Invierno peninsular",
        estacion="invierno",
        temp_amb_c=5.0,        # P90 frío: condición más favorable para la línea
        vel_viento_ms=3.0,
        angulo_viento_deg=90.0,
        radiacion_solar_wm2=200.0,
        descripcion="Mayor capacidad de transporte. Viento y temperatura bajos.",
    ),
    "primavera": ScenarioMeteo(
        nombre="Primavera peninsular",
        estacion="primavera",
        temp_amb_c=18.0,
        vel_viento_ms=2.5,
        angulo_viento_deg=90.0,
        radiacion_solar_wm2=650.0,
        descripcion="Condición intermedia.",
    ),
}


@dataclass
class SeasonalRates:
    """Resultado completo de rates estacionales para una línea o tramo."""
    id_tramo: str
    longitud_km: float
    altitud_media_m: float
    rates: dict[Season, float] = field(default_factory=dict)    # A por estación
    detalles: dict = field(default_factory=dict)                 # RateResult completo por estación