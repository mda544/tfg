from dataclasses import dataclass
from app.domain.types import Season


@dataclass(frozen=True)
class ScenarioDefaults:
    """Valores meteorológicos representativos de una estación del año
    para la Península Ibérica. Inmutable."""

    temp_amb_c: float
    wind_speed_ms: float
    wind_angle_deg: float
    solar_radiation_wm2: float


DEFAULT_SCENARIOS: dict[Season, ScenarioDefaults] = {
    "verano": ScenarioDefaults(
        temp_amb_c=38.0,
        wind_speed_ms=0.6,
        wind_angle_deg=90.0,
        solar_radiation_wm2=900.0,
    ),
    "otono": ScenarioDefaults(
        temp_amb_c=20.0,
        wind_speed_ms=2.0,
        wind_angle_deg=90.0,
        solar_radiation_wm2=500.0,
    ),
    "invierno": ScenarioDefaults(
        temp_amb_c=5.0,
        wind_speed_ms=3.0,
        wind_angle_deg=90.0,
        solar_radiation_wm2=200.0,
    ),
    "primavera": ScenarioDefaults(
        temp_amb_c=18.0,
        wind_speed_ms=2.5,
        wind_angle_deg=90.0,
        solar_radiation_wm2=650.0,
    ),
}
