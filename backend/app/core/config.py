from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # CORS
    cors_origins: List[str] = ["*"]

    # Caché en disco
    climate_cache_dir: str = "climate_cache"
    dem_cache_dir: str = "dem_cache"

    # Rango histórico por defecto para percentiles
    anio_inicio_default: int = 1990
    anio_fin_default: int = 2023


settings = Settings()