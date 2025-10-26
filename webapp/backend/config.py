"""
Configuration management for Cap Table Web App.
Uses environment variables with validation.
"""

from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # LLM Configuration (server-side only, users cannot change)
    active_provider: Literal["openai"] = "openai"
    active_model: str = "gpt-4"

    # API Keys
    openai_api_key: str = ""

    # Server Configuration
    cors_origins: str = "http://localhost:5173"
    port: int = 8173

    class Config:
        env_file = ".env"
        case_sensitive = False

    def get_cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    def get_api_key(self) -> str:
        """Get API key for the active provider."""
        if self.active_provider == "openai":
            return self.openai_api_key
        else:
            raise ValueError(f"Unknown provider: {self.active_provider}")


# Global settings instance
settings = Settings()
