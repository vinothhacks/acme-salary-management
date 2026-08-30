from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "ACME Salary Management"
    environment: str = "development"
    database_url: str = "sqlite+pysqlite:///:memory:"
    secret_key: str = "dev-only-change-me"
    session_cookie_name: str = "acme_session"
    cors_origins: str = "http://localhost:5173"
    hr_email: str = "hr@acme.example"
    hr_password: str = "acme-hr-change-me"
    session_https_only: bool = False
    openrouter_api_key: str = ""
    mistral_api_key: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
