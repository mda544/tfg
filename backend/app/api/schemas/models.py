from typing import List, Optional, Dict
from pydantic import BaseModel, field_validator
from app.domain.types import Season, ClimateSource, ElevationSource


class GeoPointDTO(BaseModel):
    lat: float
    lon: float
    elevation_m: Optional[float] = None


class UserCreateDTO(BaseModel):
    username: str
    password: str


class LoginDTO(BaseModel):
    username: str
    password: str


class TokenDTO(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str


class ConductorCreateDTO(BaseModel):
    name: str
    description: Optional[str] = None
    diameter_mm: float
    r_ac_75_ohm_km: float
    r_ac_25_ohm_km: float
    emissivity: float = 0.5
    absorptivity: float = 0.5
    max_temp_c: float = 90.0


class ConductorResponseDTO(BaseModel):
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


class PuntoSingularDTO(BaseModel):

    lat: float
    lon: float
    station: Optional[str] = None
    comment: Optional[str] = None
    altitud: Optional[float] = None
    number: Optional[str] = None
    lineAngle: Optional[float] = None
    z: Optional[float] = None
    elevation_m: Optional[float] = None 

    @field_validator("station", "number", mode="before")
    @classmethod
    def coerce_to_str(cls, v):
        if v is None:
            return None
        return str(v)

    model_config = {"extra": "ignore"}


class LineCreateDTO(BaseModel):
    name: str
    description: Optional[str] = None
    coordinates: List[GeoPointDTO]
    support_metadata: Optional[List[PuntoSingularDTO]] = None


class LineResponseDTO(BaseModel):
    id: str
    name: str
    description: Optional[str]
    length_km: Optional[float]
    n_points: Optional[int]
    bbox_lat_min: Optional[float]
    bbox_lat_max: Optional[float]
    bbox_lon_min: Optional[float]
    bbox_lon_max: Optional[float]
    min_elevation_m: Optional[float]
    max_elevation_m: Optional[float]
    avg_elevation_m: Optional[float]
    support_metadata: Optional[List[PuntoSingularDTO]] = None
    geometry_geojson: dict
    created_at: str
    updated_at: str


class StudyCaseCreateDTO(BaseModel):
    name: str
    description: Optional[str] = None
    line_id: str
    conductor_id: str
    segment_step_m: Optional[float]
    use_real_spans: bool = False
    use_dem: bool = True


class StudyCaseResponseDTO(BaseModel):
    id: str
    name: str
    description: Optional[str]
    line_id: str
    conductor_id: str
    conductor: ConductorResponseDTO
    segment_step_m: Optional[float]
    use_real_spans: bool
    use_dem: bool
    created_at: str
    updated_at: str


class WeatherInputDTO(BaseModel):
    season: Season
    temp_amb_c: float
    wind_speed_ms: float
    wind_angle_deg: float = 90.0
    solar_radiation_wm2: float
    wind_dir_predominant_deg: Optional[float] = None


class CalculationCreateDTO(BaseModel):
    study_case_id: str
    weather_inputs: List[WeatherInputDTO]  
    climate_source: ClimateSource = "manual"


class SegmentResultDTO(BaseModel):
    segment_id: str
    index: int
    length_km: float
    elevation_m: float
    azimuth_deg: float
    mid_point: GeoPointDTO
    start_point: GeoPointDTO
    end_point: GeoPointDTO
    ampacity: float
    design_rate: float
    qc_wm: float
    qr_wm: float
    qs_wm: float
    r_tc_ohm_m: float
    conv_mode: str


class SeasonResultDTO(BaseModel):
    id: str
    season: Season
    weather_input: WeatherInputDTO
    design_rate: float
    elevation_source: ElevationSource
    n_segments: int
    segments: List[SegmentResultDTO]


class CalculationResponseDTO(BaseModel):
    id: str
    study_case_id: str
    climate_source: str
    design_rate: float
    n_segments: int
    warnings: List[str]
    season_results: List[SeasonResultDTO]
    created_at: Optional[str] = None


class SeasonalPercentilesDTO(BaseModel):
    temp_p10_c: float
    temp_p50_c: float
    temp_p90_c: float
    wind_p10_ms: float
    wind_p50_ms: float
    wind_p90_ms: float
    wind_dir_predominant_deg: Optional[float] = None
    radiation_p50_wm2: float
    radiation_p90_wm2: float
    n_hours: int
    source: str
    years_covered: str


class ClimatePercentilesResponseDTO(BaseModel):
    source: str
    point: GeoPointDTO
    percentiles: Dict[Season, SeasonalPercentilesDTO]


class ElevationResponseDTO(BaseModel):
    lat: float
    lon: float
    elevation_m: float
