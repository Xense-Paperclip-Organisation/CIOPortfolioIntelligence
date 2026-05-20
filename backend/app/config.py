from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    anthropic_api_key: str = ""
    claude_advisory_model: str = "claude-opus-4-6"
    claude_personalization_model: str = "claude-sonnet-4-6"
    claude_chat_model: str = "claude-opus-4-6"

    alpha_vantage_api_key: str = ""
    fred_api_key: str = ""

    redis_url: str = "redis://redis:6379/0"
    price_cache_ttl_seconds: int = 300
    news_cache_ttl_seconds: int = 900
    macro_cache_ttl_seconds: int = 3600
    personalization_cache_ttl_seconds: int = 86400

    request_timeout_seconds: float = 12.0


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
