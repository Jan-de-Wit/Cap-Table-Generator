# Phase 2: Web Application Refactoring - Outline

## Summary

Phase 1 (Core Library Refactoring) is COMPLETE ✅. Phase 2 focuses on the web application architecture and will follow a similar modular decomposition approach.

## Completed in Phase 1

- ✅ Excel module decomposed into specialized sheet generators
- ✅ Formula module split into domain-specific modules  
- ✅ Validation module organized into specialized validators
- ✅ All 20 tests passing
- ✅ Improved maintainability and code organization

## Phase 2 Tasks Remaining

### 2.1 LLM Service Decomposition (1002 lines → modular package)
**Status**: Not Started

**Plan**:
- `llm/client.py` - OpenAI client wrapper with streaming
- `llm/tool_definitions.py` - Tool schemas (CAP_TABLE_EDITOR_TOOL, etc.)
- `llm/prompt_manager.py` - System prompts (SYSTEM_PROMPT)
- `llm/message_formatter.py` - Message formatting utilities
- `llm/stream_handler.py` - SSE streaming logic  
- `llm/llm_service.py` - Main orchestrator

**Key Functions to Extract**:
- `_analyze_tool_dependencies()` - Batch analysis
- `_create_entity_summary()` - Context generation
- `_execute_tool_call()` - Tool execution routing
- `_chat_stream_openai()` - Streaming orchestration

### 2.2 Tool Execution System
**Status**: Not Started

**Plan**:
Reorganize `services/tools/`:
- `executor.py` - Core execution logic
- `orchestrator.py` - Tool call management
- `operations/` - Individual operations:
  - `replace.py`
  - `append.py`  
  - `upsert.py`
  - `delete.py`
  - `bulk_patch.py`
- `validator.py` - Tool parameter validation

### 2.3 API Layer Organization  
**Status**: Not Started

**Plan**:
Create `routers/` package:
- `chat.py` - Chat endpoints
- `captable.py` - Cap table CRUD
- `tools.py` - Tool execution endpoints
- `conversation.py` - Conversation management
- `export.py` - Download endpoints

### 2.4 Frontend Refactoring
**Status**: Not Started

**Plan**:
- Reorganize components into logical folders
- Split `appStore.ts` into domain slices
- Create organized API service modules

## Next Session Plan

Given the scope and complexity of Phase 2, the next session should:

1. **Start with LLM Service** - Break down the 1002-line file into:
   - Client wrapper (~100 lines)
   - Tool definitions (~200 lines)
   - Prompt manager (~150 lines)
   - Stream handler (~250 lines)
   - Main service (~300 lines)

2. **Test Thoroughly** - Ensure web app still works after refactoring

3. **Continue Systematically** - Move to tool execution, then API layer

## Success Metrics for Phase 2

- Each LLM module under 300 lines
- Test coverage maintained for web app
- No breaking changes to API surface
- Clear separation of concerns
- Improved maintainability

