from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    DATABASE_URL: str = f"sqlite:///{(Path(__file__).resolve().parents[1] / 'pos.db')}"
    APP_NAME: str = "POS App (PyQt)"
    LOCALE: str = "en_US"
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
