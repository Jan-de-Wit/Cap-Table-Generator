"""
Application Settings

Main application configuration using Pydantic Settings.
"""

from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    app_name: str = Field(default="Cap Table Generator", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    
    # API
    api_title: str = Field(default="Cap Table Generator API", description="API title")
    api_version: str = Field(default="1.0.0", description="API version")
    api_prefix: str = Field(default="/api/v1", description="API prefix")
    
    # CORS
    cors_origins: list[str] = Field(default=["*"], description="CORS allowed origins")
    cors_credentials: bool = Field(default=True, description="CORS allow credentials")
    
    # Performance
    max_workers: Optional[int] = Field(default=None, description="Max worker threads")
    cache_enabled: bool = Field(default=True, description="Enable caching")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings (singleton)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings




