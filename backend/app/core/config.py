from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API — raramente cambian, pueden tener default
    api_title:       str = "Pypacity API"
    api_version:     str = "1.0.0"
    api_description: str = "Seasonal static ampacity rating of overhead lines (IEEE 738)."

    # Base de datos
    database_url: str

    # JWT
    jwt_secret:      str
    jwt_algorithm:   str = "HS256"
    jwt_expires_min: int = 1440

    # CORS 
    cors_origins: List[str]

    # Rango histórico — parámetros de dominio
    anio_inicio_default: int = 1990
    anio_fin_default:    int = 2023

    # Timeouts para APIs externas
    openmeteo_timeout:    int = 120
    nasa_timeout:         int = 120
    dem_timeout:          int = 15
    dem_fallback_timeout: int = 10


settings = Settings()