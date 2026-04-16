from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Loads from backend/.env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    env: str = "local"
    app_name: str = "AI Verification Copilot"
    api_v1_prefix: str = "/api/v1"

    # Database
    database_url: str

    # AI provider (for later)
    model_provider: str = "openai"  # "openai" or "ollama"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"


settings = Settings()