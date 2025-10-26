# Backend Fix - Chat Endpoint 422 Error

## Problem
The chat endpoint was returning 422 Unprocessable Content error because:
1. The `ChatRequest` model required the `message` field
2. When sending conversation history with `messages`, the frontend didn't provide `message`
3. Pydantic validation failed because `message` was marked as required

## Solution
Updated the `ChatRequest` model to accept either `message` OR `messages`:
- Made `message` optional
- Added a model validator to ensure at least one is provided
- Backend logic handles both cases

## Changes Made

### 1. webapp/backend/models.py
- Changed `message: str` to `message: Optional[str]`
- Added `@model_validator` to ensure either `message` or `messages` is provided
- Imported `model_validator` from pydantic

### 2. webapp/backend/main.py  
- Simplified logic since validator handles the requirement check
- Added fallback to single message for backwards compatibility

## Testing
The chat endpoint should now accept:
1. Single message: `{ "message": "Create a cap table" }`
2. Conversation history: `{ "messages": [{"role": "user", "content": "..."}] }`

This fix ensures the frontend can send full conversation history for context-aware LLM interactions.

