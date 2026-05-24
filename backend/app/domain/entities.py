from dataclasses import dataclass, field
from app.domain.types import Season
from app.domain.value_objects import GeoPoint, WeatherInput, SegmentRating


@dataclass
class Conductor:
    """Entidad — conductor eléctrico del usuario. UUID de BD."""

    name: str
    diameter_mm: float
    r_ac_75_ohm_km: float
    r_ac_25_ohm_km: float
    emissivity: float
    absorptivity: float
    max_temp_c: float
    id: str | None = None
    description: str = ""
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class Line:
    """Entidad — trazado geográfico de la línea. UUID de BD."""

    name: str
    coordinates: list[GeoPoint]
    id: str | None = None
    description: str = ""
    length_km: float | None = None
    n_points: int | None = None
    bbox_lat_min: float | None = None
    bbox_lat_max: float | None = None
    bbox_lon_min: float | None = None
    bbox_lon_max: float | None = None
    min_elevation_m: float | None = None
    max_elevation_m: float | None = None
    avg_elevation_m: float | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class StudyCase:
    """Entidad — agrupa una línea con su historial de cálculos."""

    name: str
    line_id: str
    id: str | None = None
    description: str = ""
    segment_step_m: float = 500.0
    use_real_spans: bool = False
    use_dem: bool = True
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class Segment:
    """Entidad — tramo del trazado con geometría y resultados IEEE 738.
    Tiene id propio (T001/V002) y se persiste en BD con FK a RateResult.
    Su ciclo de vida está ligado al RateResult — no tiene endpoint REST propio.

    Se construye en dos pasos en rates_service:
      1. segmentation.py rellena la geometría
      2. El bucle IEEE 738 rellena rates y ratings por estación

    design_rate = min(rates.values()) — el tramo más restrictivo."""

    id: str
    index: int
    start_point: GeoPoint
    mid_point: GeoPoint
    end_point: GeoPoint
    length_km: float
    elevation_m: float = 0.0
    azimuth_deg: float = 90.0
    rates: dict[Season, float] = field(default_factory=dict)
    ratings: dict[Season, SegmentRating] = field(default_factory=dict)

    @property
    def design_rate(self) -> float:
        return min(self.rates.values()) if self.rates else 0.0


@dataclass
class RateResult:
    """Entidad — resultado de un cálculo de rates. UUID de BD.
    design_rate = min de los design_rate de todos los segmentos."""

    id: str
    study_case_id: str
    conductor_id: str
    conductor: Conductor
    weather_inputs: list[WeatherInput]
    segments: list[Segment]
    climate_source: str
    elevation_source: str
    warnings: list[str]
    created_at: str | None = None

    @property
    def design_rate(self) -> float:
        return min(s.design_rate for s in self.segments) if self.segments else 0.0

    @property
    def rates_by_season(self) -> dict[Season, float]:
        if not self.segments:
            return {}
        return {
            season: min(s.rates.get(season, 9999) for s in self.segments)
            for season in self.segments[0].rates
        }

    @property
    def n_segments(self) -> int:
        return len(self.segments)


@dataclass
class SeasonalPercentiles:
    """Entidad — caché de percentiles históricos. No es del dominio central."""

    season: str
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
