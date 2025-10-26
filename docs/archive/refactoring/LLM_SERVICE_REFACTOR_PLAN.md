# LLM Service Refactoring Plan

## Current Structure
- `llm_service.py` - 1002 lines mixing all concerns

## Target Structure
```
webapp/backend/services/llm/
├── __init__.py              # Exports main service
├── llm_service.py           # Main orchestrator (~150 lines)
├── client.py                # OpenAI client wrapper (~100 lines)
├── tool_definitions.py      # Tool schemas (~250 lines)
├── prompt_manager.py        # System prompts (~200 lines)
├── stream_handler.py        # SSE streaming logic (~300 lines)
└── message_formatter.py     # Message formatting utilities (~100 lines)
```

## Key Components to Extract

### 1. Tool Definitions (`tool_definitions.py`)
- `CAP_TABLE_EDITOR_TOOL`
- `GET_SCHEMA_DATA_TOOL`
- `GET_CAP_TABLE_JSON_TOOL`
- Tool schema helpers

### 2. System Prompts (`prompt_manager.py`)
- `SYSTEM_PROMPT` constant
- Prompt building utilities
- Context management functions

### 3. OpenAI Client (`client.py`)
- `AsyncOpenAI` wrapper
- Provider abstraction
- Configuration management

### 4. Stream Handler (`stream_handler.py`)
- `_chat_stream_openai()` - Multi-step streaming
- Tool call batching
- Event emission
- Tool execution routing

### 5. Message Formatter (`message_formatter.py`)
- `_create_entity_summary()` - Context generation
- Message building utilities
- Format helpers

### 6. Main Service (`llm_service.py`)
- `LLMService` class orchestrator
- Public API
- Delegates to specialized modules

## Benefits
- Each module < 300 lines
- Clear separation of concerns
- Easy to test components
- Maintainable structure

