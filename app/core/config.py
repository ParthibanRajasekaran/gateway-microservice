from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_env: str = "local"
    log_level: str = "INFO"
    vat_rate_default: float = 0.2

    class Config:
        env_prefix = ""
        case_sensitive = False

settings = Settings()
