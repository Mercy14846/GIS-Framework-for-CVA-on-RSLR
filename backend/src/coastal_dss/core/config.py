from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_DATA = Path(__file__).resolve().parents[4] / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DSS_", env_file=".env", extra="ignore")

    # "demo" serves synthetic placeholder data; "raster" reads layers from data/processed,
    # built from USGS M2M downloads by `python -m coastal_dss.ingestion all`.
    data_mode: str = "demo"
    data_dir: Path = REPO_DATA
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    database_url: str = "postgresql+psycopg://dss:dss@localhost:5432/dss"
    redis_url: str = "redis://localhost:6379/0"

    # USGS EROS M2M credentials: ERS username and an M2M application token (not the password).
    usgs_username: str = ""
    usgs_token: SecretStr = SecretStr("")

    # Analysis grid for real data (cells over the study area). 110 x 60 is ~550 m.
    grid_nx: int = 110
    grid_ny: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
