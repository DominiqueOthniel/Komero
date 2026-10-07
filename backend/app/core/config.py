from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Komero"
    app_env: str = "development"
    api_prefix: str = "/api/v1"
    secret_key: str = "dev-secret-change-me"
    access_token_expire_minutes: int = 60
    database_url: str = "postgresql+psycopg://komero:komero@localhost:5432/komero"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    frontend_url: str = "http://localhost:3000"
    currency_default: str = "XAF"
    token_encryption_key: str = "dev-token-encryption-key-change-me"

    whatsapp_verify_token: str = "komero-verify-token"
    whatsapp_app_secret: str = ""
    whatsapp_access_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_business_account_id: str = ""
    whatsapp_adapter: str = "mock"

    ai_provider: str = "mock"
    ai_api_key: str = ""

    storage_provider: str = "local"

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
