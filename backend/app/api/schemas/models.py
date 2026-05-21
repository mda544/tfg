from typing import List, Optional, Dict
from pydantic import BaseModel
from app.domain.types import Season

# Tipos compartidos


class GeoPointDTO(BaseModel):
    """Punto geográfico WGS84. Clave canónica 'lon' — el frontend puede enviar
    'lng' pero se normaliza en rates_service antes de llegar aquí."""

    lat: float
    lon: float


# DTOs de entrada: POST /api/v1/rates


class ConductorDTO(BaseModel):
    """Parámetros del conductor. Convertido a Entidad Conductor (domain/entities.py)
    en rates_service. Usado dentro de RateCalculationRequestDTO."""

    diameter_mm: float
    r_ac_75_ohm_km: float
    r_ac_25_ohm_km: float
    emissivity: float = 0.5
    absorptivity: float = 0.5
    max_temp_c: float = 90.0


class MeteoScenarioDTO(BaseModel):
    """Escenario meteorológico personalizado para una estación.
    Lista opcional dentro de RateCalculationRequestDTO.
    Si se omite, rates_service usa DEFAULT_SCENARIOS (Península Ibérica)."""

    season: Season
    temp_amb_c: float
    wind_speed_ms: float
    wind_angle_deg: float = 90.0
    solar_radiation_wm2: float


class RateCalculationRequestDTO(BaseModel):
    """Cuerpo completo para POST /api/v1/rates.
    Punto de entrada único para el cálculo IEEE 738."""

    coordinates: List[dict]
    conductor: ConductorDTO
    scenarios: Optional[List[MeteoScenarioDTO]] = None
    segment_step_m: float = 500.0
    use_real_spans: bool = False
    use_dem: bool = True


# DTOs de respuesta: POST /api/v1/rates


class AppliedScenarioDTO(BaseModel):
    """Condiciones meteorológicas del escenario aplicadas a un segmento.
    Anidado dentro de SegmentDetailDTO para la trazabilidad del cálculo."""

    temp_amb_c: float
    wind_speed_ms: float
    solar_radiation_wm2: float


class SegmentDetailDTO(BaseModel):
    """Resultado completo IEEE 738 para un segmento y un escenario estacional.
    Incluye flujos de calor (qc, qr, qs), resistencia interpolada,
    y modo de convección. Anidado en SegmentResultDTO.details, indexado por Season."""

    ampacity_a: float
    qc_wm: float
    qr_wm: float
    qs_wm: float
    r_tc_ohm_m: float
    conv_mode: str
    elevation_m: float
    scenario: AppliedScenarioDTO


class SegmentResultDTO(BaseModel):
    """Resultado completo para un segmento individual del trazado.
    design_rate_a es el mínimo de los cuatro escenarios — el valor limitante."""

    segment_id: str
    length_km: float
    elevation_m: float
    mid_point: GeoPointDTO
    start_point: GeoPointDTO
    end_point: GeoPointDTO
    rates: Dict[Season, float]
    details: Dict[Season, SegmentDetailDTO]
    design_rate_a: float


class RouteInfoDTO(BaseModel):
    """Metadatos del trazado: longitud, fuente de elevación, modo de segmentación, rangos de elevación."""

    length_km: float
    n_points: int
    elevation_source: str
    segment_mode: str
    min_elevation_m: float
    max_elevation_m: float
    avg_elevation_m: float
    bbox: Optional[dict] = None
    long_spans: Optional[List[dict]] = None
    self_intersects: Optional[List[dict]] = None


class RateCalculationResponseDTO(BaseModel):
    """Respuesta completa para POST /api/v1/rates.
    id: UUID que identifica este resultado — usado por GET /api/v1/rates/{id}.
    design_rate_a: mínimo global — el peor segmento en el peor escenario."""

    id: str
    n_segments: int
    conductor: ConductorDTO
    segments: List[SegmentResultDTO]
    design_rate_a: float
    rates_by_season: Dict[Season, float]
    route_info: RouteInfoDTO
    warnings: List[str]


# DTOs de respuesta: GET /api/v1/climate/percentiles


class SeasonalPercentilesDTO(BaseModel):
    """Percentiles de una estación dentro de ClimatePercentilesResponseDTO.
    Sub-objeto anidado — no es un recurso independiente."""

    temp_p10_c: float
    temp_p50_c: float
    temp_p90_c: float
    wind_p10_ms: float
    wind_p50_ms: float
    wind_p90_ms: float
    radiation_p50_wm2: float
    radiation_p90_wm2: float
    n_hours: int
    source: str
    years_covered: str


class ClimatePercentilesResponseDTO(BaseModel):
    """Respuesta para GET /api/v1/climate/percentiles.
    Agrupa los percentiles de las cuatro estaciones en un punto geográfico."""

    source: str
    point: GeoPointDTO
    percentiles: Dict[Season, SeasonalPercentilesDTO]


# DTOs de respuesta: GET /api/v1/elevation


class ElevationResponseDTO(BaseModel):
    """Respuesta para GET /api/v1/elevation.
    Uso principal: previsualización desde el frontend mientras se dibuja el trazado."""

    lat: float
    lon: float
    elevation_m: float


# DTOs de Conductores


class ConductorCreateDTO(BaseModel):
    """Cuerpo de la petición para POST /api/v1/conductors y PUT /api/v1/conductors/{id}."""

    name: str
    description: Optional[str] = None
    diameter_mm: float
    r_ac_75_ohm_km: float
    r_ac_25_ohm_km: float
    emissivity: float = 0.5
    absorptivity: float = 0.5
    max_temp_c: float = 90.0


class ConductorResponseDTO(BaseModel):
    """Respuesta de conductor. Incluye id y marcas de tiempo generadas por el servidor."""

    id: str
    name: str
    description: Optional[str]
    diameter_mm: float
    r_ac_75_ohm_km: float
    r_ac_25_ohm_km: float
    emissivity: float
    absorptivity: float
    max_temp_c: float
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# DTOs de Líneas


class LineCreateDTO(BaseModel):
    """Cuerpo de la petición para POST /api/v1/lines y PUT /api/v1/lines/{id}.
    coordinates: lista de {lat, lon} — también acepta {lat, lng}."""

    name: str
    description: Optional[str] = None
    coordinates: List[dict]


class LineResponseDTO(BaseModel):
    """Respuesta de línea. geometry_geojson es el trazado listo para Leaflet."""

    id: str
    name: str
    description: Optional[str]
    length_km: Optional[float]
    geometry_geojson: dict
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# DTOs de Casos de Estudio


class MeteoScenarioCreateDTO(BaseModel):
    """Escenario meteorológico anidado dentro de StudyCaseCreateDTO."""

    season: Season
    temp_amb_c: float
    wind_speed_ms: float
    wind_angle_deg: float = 90.0
    solar_radiation_wm2: float


class StudyCaseCreateDTO(BaseModel):
    """Cuerpo de la petición para POST /api/v1/study-cases y PUT /api/v1/study-cases/{id}.
    scenarios es opcional — si se omite, el cálculo usa DEFAULT_SCENARIOS."""

    name: str
    description: Optional[str] = None
    line_id: str
    conductor_id: str
    segment_step_m: float = 500.0
    use_real_spans: bool = False
    use_dem: bool = True
    scenarios: Optional[List[MeteoScenarioCreateDTO]] = None


class MeteoScenarioResponseDTO(BaseModel):
    """Escenario meteorológico dentro de StudyCaseResponseDTO."""

    id: str
    season: Season
    temp_amb_c: float
    wind_speed_ms: float
    wind_angle_deg: float
    solar_radiation_wm2: float

    class Config:
        from_attributes = True


class StudyCaseResponseDTO(BaseModel):
    """Respuesta de caso de estudio con escenarios anidados."""

    id: str
    name: str
    description: Optional[str]
    line_id: str
    conductor_id: str
    segment_step_m: float
    use_real_spans: bool
    use_dem: bool
    scenarios: List[MeteoScenarioResponseDTO]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# DTOs de Autenticación


class RegisterRequestDTO(BaseModel):
    """Cuerpo de la petición para POST /api/v1/auth/register."""

    username: str
    password: str


class LoginRequestDTO(BaseModel):
    """Cuerpo de la petición para POST /api/v1/auth/login."""

    username: str
    password: str


class TokenResponseDTO(BaseModel):
    """Respuesta de inicio de sesión. El frontend guarda access_token en localStorage
    y lo envía como: Authorization: Bearer <token>"""

    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str
