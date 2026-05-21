from app.domain.types import Season
from app.domain.entities import MeteoScenario, SegmentResults

DEFAULT_SCENARIOS: dict[Season, MeteoScenario] = {
    "verano": MeteoScenario(
        name="Iberian summer",
        season="verano",
        temp_amb_c=38.0,
        wind_speed_ms=0.6,
        wind_angle_deg=90.0,
        solar_radiation_wm2=900.0,
        description="Most restrictive condition of the year.",
    ),
    "otono": MeteoScenario(
        name="Iberian autumn",
        season="otono",
        temp_amb_c=20.0,
        wind_speed_ms=2.0,
        wind_angle_deg=90.0,
        solar_radiation_wm2=500.0,
        description="Intermediate condition.",
    ),
    "invierno": MeteoScenario(
        name="Iberian winter",
        season="invierno",
        temp_amb_c=5.0,
        wind_speed_ms=3.0,
        wind_angle_deg=90.0,
        solar_radiation_wm2=200.0,
        description="Highest transport capacity.",
    ),
    "primavera": MeteoScenario(
        name="Iberian spring",
        season="primavera",
        temp_amb_c=18.0,
        wind_speed_ms=2.5,
        wind_angle_deg=90.0,
        solar_radiation_wm2=650.0,
        description="Intermediate condition.",
    ),
}
