from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, loaded from environment variables / .env.

    Credentials and connection strings are never hardcoded here: missing
    required values fail fast at import time with a clear message.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Milan — Sistema de Inventario y Ventas"
    database_url: str = ""
    secret_key: str = ""
    access_token_expire_minutes: int = 480
    openai_api_key: str | None = None
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    upload_dir: str = "app/uploads"
    ai_model_dir: str = "app/ai_models"

    @model_validator(mode="after")
    def _require_core_config(self) -> "Settings":
        if not self.database_url.startswith("postgresql"):
            raise ValueError(
                "DATABASE_URL no está configurada o es inválida. "
                "Copie `.env.example` a `.env` y defina la conexión a PostgreSQL."
            )
        if not self.secret_key:
            raise ValueError(
                "SECRET_KEY no está configurada. "
                "Copie `.env.example` a `.env` y defina una clave secreta."
            )
        return self


settings = Settings()