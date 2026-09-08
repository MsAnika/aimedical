from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AI Medical Diagnostic System"
    secret_key: str = "dev-secret-change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    database_url: str = "sqlite:///./meddiag.db"

    model_dir: str = "./backend/app/services/ml/models"
    media_dir: str = "./media"

    force_demo: bool = False
    allow_demo_predictions: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
