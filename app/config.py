"""Central configuration, loaded from environment variables / .env."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_provider: str = "mock"
    llm_model: str = "llama3.1"
    openai_api_key: str = ""
    groq_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"

    public_base_url: str = "http://localhost:8000"
    database_path: str = "./data/cards.db"
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
