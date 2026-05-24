from app.domain.types import Season
from app.domain.value_objects import WeatherInput

DEFAULT_SCENARIOS: dict[Season, WeatherInput] = {
    "verano": WeatherInput(
        season="verano",
        temp_amb_c=38.0,
        wind_speed_ms=0.6,
        wind_angle_deg=90.0,
        solar_radiation_wm2=900.0,
    ),
    "otono": WeatherInput(
        season="otono",
        temp_amb_c=20.0,
        wind_speed_ms=2.0,
        wind_angle_deg=90.0,
        solar_radiation_wm2=500.0,
    ),
    "invierno": WeatherInput(
        season="invierno",
        temp_amb_c=5.0,
        wind_speed_ms=3.0,
        wind_angle_deg=90.0,
        solar_radiation_wm2=200.0,
    ),
    "primavera": WeatherInput(
        season="primavera",
        temp_amb_c=18.0,
        wind_speed_ms=2.5,
        wind_angle_deg=90.0,
        solar_radiation_wm2=650.0,
    ),
}
