from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import json


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    database_url: str

    # OpenAI
    openai_api_key: str

    # Twitter/X API (optional if only using other platforms)
    twitter_api_key: str = ""
    twitter_api_secret: str = ""
    twitter_access_token: str = ""
    twitter_access_token_secret: str = ""
    twitter_bearer_token: str = ""
    twitter_bot_id: str = ""

    # Bluesky API
    bluesky_handle: str = ""
    bluesky_app_password: str = ""
    bluesky_service_url: str = "https://bsky.social"

    # Platform Selection
    enabled_platforms: str = '["twitter"]'

    # Application
    embedding_model: str = "text-embedding-3-small"
    similarity_threshold: float = 0.8
    base_url: str = "http://localhost:8000"
    contribution_expiry_hours: int = 24

    # Stripe
    stripe_api_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_min_contribution_cents: int = 100  # $1.00

    # ChatGPT
    chatgpt_model: str = "gpt-3.5-turbo"

    @property
    def get_enabled_platforms(self) -> List[str]:
        """Parse enabled_platforms JSON string into a list."""
        try:
            platforms = json.loads(self.enabled_platforms)
            if not isinstance(platforms, list):
                return ["twitter"]
            return platforms
        except (json.JSONDecodeError, TypeError):
            return ["twitter"]


settings = Settings()
