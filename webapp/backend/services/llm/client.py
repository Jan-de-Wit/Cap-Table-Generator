"""
OpenAI Client Module

Provides abstraction over the OpenAI API client with streaming support.
Handles provider configuration and client initialization.
"""

import os
import sys
from openai import AsyncOpenAI
from typing import Optional

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from webapp.backend.config import settings


class LLMClient:
    """
    Wraps OpenAI client with configuration management.
    
    Provides a consistent interface for LLM interactions regardless of the
    underlying provider (currently OpenAI).
    """
    
    def __init__(self):
        """Initialize LLM client based on configured provider."""
        self.provider = settings.active_provider
        self.model = settings.active_model
        
        if self.provider == "openai":
            self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def is_openai(self) -> bool:
        """
        Check if using OpenAI provider.
        
        Returns:
            True if OpenAI, False otherwise
        """
        return self.provider == "openai"
    
    def get_client(self) -> AsyncOpenAI:
        """
        Get the underlying OpenAI client.
        
        Returns:
            AsyncOpenAI client instance
            
        Raises:
            ValueError: If provider is not OpenAI
        """
        if not self.is_openai():
            raise ValueError(f"Client not available for provider: {self.provider}")
        return self.openai_client
    
    def get_model(self) -> str:
        """
        Get the configured model name.
        
        Returns:
            Model identifier string
        """
        return self.model

