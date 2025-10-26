"""
LLM Service - OpenAI client with streaming.
Handles tool calling for cap_table_editor.

This module now acts as a compatibility layer that imports from the refactored llm package.
The new modular structure is in webapp/backend/services/llm/
"""

# Import from the refactored llm package
from webapp.backend.services.llm.llm_service import llm_service

# Re-export for backward compatibility
from webapp.backend.services.llm.llm_service import LLMService
