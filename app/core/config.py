from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    database_url: str

    # OpenAI
    openai_api_key: str

    # Twitter/X API
    twitter_api_key: str
    twitter_api_secret: str
    twitter_access_token: str
    twitter_access_token_secret: str
    twitter_bearer_token: str
    twitter_bot_id: str

    # Application
    embedding_model: str = "text-embedding-3-small"
    similarity_threshold: float = 0.8


settings = Settings()
