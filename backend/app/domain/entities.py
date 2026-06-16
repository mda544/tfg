from dataclasses import dataclass, field
from app.domain.types import Season
from app.domain.value_objects import GeoPoint, SegmentRating


@dataclass
class Conductor:
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
    elevation_source: str | None = None
    support_metadata: list | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class StudyCase:
    """Configuración del sistema eléctrico a analizar: trazado, conductor y
    parámetros de segmentación. Permanece estable entre ejecuciones del modelo.
    Cada Calculation sobre este caso puede usar distintas condiciones climáticas."""

    name: str
    line_id: str
    conductor_id: str
    id: str | None = None
    description: str = ""
    segment_step_m: float | None = None
    use_real_spans: bool = False
    use_dem: bool = True
    conductor: "Conductor | None" = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class WeatherInput:
    """Condiciones meteorológicas representativas de una estación del año.
    Define las variables de entrada del modelo térmico estacionario IEEE 738:
    temperatura ambiente, velocidad y dirección del viento, radiación solar."""

    season: Season
    temp_amb_c: float
    wind_speed_ms: float
    wind_angle_deg: float
    solar_radiation_wm2: float
    wind_dir_predominant_deg: float | None = None


@dataclass
class Segment:
    """Tramo del trazado con geometría y resultado del modelo térmico IEEE 738
    para unas condiciones atmosféricas concretas. Cada segmento tiene una única
    ampacidad calculada — no es compartida entre estaciones."""

    id: str
    index: int
    start_point: GeoPoint
    mid_point: GeoPoint
    end_point: GeoPoint
    length_km: float
    elevation_m: float = 0.0
    azimuth_deg: float = 90.0
    ampacity: float = 0.0
    rating: SegmentRating | None = None

    @property
    def design_rate(self) -> float:
        return self.ampacity


@dataclass
class SeasonResult:
    """Resultado del modelo térmico estacionario IEEE 738 para una estación
    meteorológica concreta. Contiene las condiciones atmosféricas representativas
    de la estación y la ampacidad calculada por tramo."""

    id: str
    calculation_id: str
    season: Season
    weather_input: WeatherInput
    segments: list[Segment] = field(default_factory=list)
    elevation_source: str = "none"
    created_at: str | None = None

    @property
    def design_rate(self) -> float:
        return min((s.ampacity for s in self.segments), default=0.0)

    @property
    def n_segments(self) -> int:
        return len(self.segments)


@dataclass
class Calculation:
    """Ejecución del modelo térmico sobre un StudyCase con una fuente climática concreta.
    Agrupa los cuatro SeasonResult estacionales y el design_rate global,
    definido como el mínimo de todos los tramos y estaciones."""

    id: str
    study_case_id: str
    climate_source: str
    season_results: list[SeasonResult] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    created_at: str | None = None

    @property
    def design_rate(self) -> float:
        return min((sr.design_rate for sr in self.season_results), default=0.0)

    @property
    def n_segments(self) -> int:
        return max((sr.n_segments for sr in self.season_results), default=0)

    @property
    def elevation_source(self) -> str:
        if self.season_results:
            return self.season_results[0].elevation_source
        return "none"

    def get_season(self, season: Season) -> SeasonResult | None:
        return next((sr for sr in self.season_results if sr.season == season), None)


@dataclass
class SeasonalPercentiles:
    season: str
    lat: float
    lon: float
    temp_p90_c: float
    temp_p50_c: float
    temp_p10_c: float
    wind_p10_ms: float
    wind_p50_ms: float
    wind_p90_ms: float
    wind_dir_predominant_deg: float | None
    radiation_p50_wm2: float
    radiation_p90_wm2: float
    n_hours: int
    source: str
    years_covered: str
