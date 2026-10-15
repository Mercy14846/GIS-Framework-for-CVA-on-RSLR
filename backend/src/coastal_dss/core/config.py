from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DSS_", env_file=".env", extra="ignore")

    # "demo" serves synthetic placeholder data; "raster" will read real GeoTIFF/PostGIS layers.
    data_mode: str = "demo"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    database_url: str = "postgresql+psycopg://dss:dss@localhost:5432/dss"
    redis_url: str = "redis://localhost:6379/0"


@lru_cache
def get_settings() -> Settings:
    return Settings()
