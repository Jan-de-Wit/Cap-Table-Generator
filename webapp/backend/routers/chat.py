"""
Chat Router

Handles chat endpoints including LLM streaming and configuration.
"""

import json
from fastapi import APIRouter
from webapp.backend.services.llm_service import llm_service
from webapp.backend.services.conversation_store import conversation_store
from webapp.backend.models import ChatRequest, ConfigResponse
from webapp.backend.config import settings
from sse_starlette.sse import EventSourceResponse

router = APIRouter(prefix="/api", tags=["chat"])


@router.get("/config", response_model=ConfigResponse)
async def get_config():
    """
    Get current LLM configuration (read-only).
    Users cannot change this - it's server-configured only.
    """
    return ConfigResponse(
        provider=settings.active_provider,
        model=settings.active_model
    )


@router.post("/chat")
async def chat(request: ChatRequest):
    """
    Chat endpoint with streaming LLM responses.
    Handles tool calls through orchestrator with execution mode support.
    Uses conversation store for message history management.
    """
    # Handle conversation memory
    conversation_id = request.conversation_id
    
    # Get or create conversation
    if conversation_id:
        # Retrieve existing conversation
        messages = conversation_store.get_messages(conversation_id)
        if not messages:
            # Conversation doesn't exist, create new one
            conversation_id = conversation_store.create_conversation()
            messages = []
    else:
        # Create new conversation
        conversation_id = conversation_store.create_conversation()
        messages = []
    
    # Add new message(s) to conversation
    if request.messages and len(request.messages) > 0:
        # Use provided messages (frontend manages history)
        new_messages = request.messages
    else:
        # Single message (backwards compatibility)
        new_messages = [{"role": "user", "content": request.message}]
    
    # Update conversation with new messages
    conversation_store.add_messages(conversation_id, new_messages)
    messages = conversation_store.get_messages(conversation_id)

    async def event_generator():
        """Generate SSE events for streaming response."""
        try:
            # Send conversation_id first so frontend knows where to continue
            yield {
                "data": json.dumps({
                    "event": "conversation_id",
                    "data": {"conversation_id": conversation_id}
                })
            }
            
            # Track assistant response to add to conversation
            assistant_response = ""
            
            async for chunk in llm_service.chat_stream(
                messages, 
                execution_mode=request.execution_mode,
                approved_tool_call_ids=request.approved_tool_call_ids
            ):
                # chunk is already a JSON string - just forward it
                yield {"data": chunk}
                
                # Collect assistant response for conversation history
                # (Parse the chunk to extract content)
                try:
                    import json as json_lib
                    data = json_lib.loads(chunk)
                    if data.get("event") == "content":
                        assistant_response += data.get("data", "")
                except:
                    pass

            # Add assistant response to conversation history
            if assistant_response:
                assistant_message = {"role": "assistant", "content": assistant_response}
                conversation_store.add_messages(conversation_id, [assistant_message])

        except Exception as e:
            yield {
                "data": json.dumps({
                    "event": "error",
                    "data": {"message": str(e)}
                })
            }

    return EventSourceResponse(event_generator())

