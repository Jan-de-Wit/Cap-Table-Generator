"""
FastAPI Main Application
Serves the Cap Table Web App backend with LLM chat, tool execution, and exports.
"""

import sys
import os
from pathlib import Path
import tempfile
import json

# Add parent directory to import cap table modules
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../..')))

from webapp.backend.services.captable_service import cap_table_service
from webapp.backend.services.tool_executor import tool_executor
from webapp.backend.services.tool_orchestrator import tool_orchestrator
from webapp.backend.services.llm_service import llm_service
from webapp.backend.services.conversation_store import conversation_store
from webapp.backend.models import (
    ChatRequest,
    CapTableEditorRequest,
    ConfigResponse,
    CapTableResponse
)
from typing import List
from webapp.backend.config import settings
from src.captable.generator import generate_from_data
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from sse_starlette.sse import EventSourceResponse


# Initialize FastAPI app
app = FastAPI(
    title="Cap Table Generator API",
    description="LLM-driven cap table generation with real-time collaboration",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Cap Table Generator API",
        "version": "1.0.0",
        "provider": settings.active_provider,
        "model": settings.active_model
    }


@app.get("/api/config", response_model=ConfigResponse)
async def get_config():
    """
    Get current LLM configuration (read-only).
    Users cannot change this - it's server-configured only.
    """
    return ConfigResponse(
        provider=settings.active_provider,
        model=settings.active_model
    )


@app.post("/api/chat")
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

            # Send final cap table state
            cap_table = cap_table_service.get_cap_table()
            metrics = cap_table_service.calculate_metrics()

            yield {
                "data": json.dumps({
                    "event": "cap_table_update",
                    "data": {
                        "capTable": cap_table,
                        "metrics": metrics
                    }
                })
            }
        except Exception as e:
            yield {
                "data": json.dumps({"event": "error", "data": {"error": str(e)}})
            }

    return EventSourceResponse(event_generator())


@app.post("/api/tool/cap_table_editor")
async def execute_tool(request: CapTableEditorRequest):
    """
    Execute cap_table_editor tool directly.
    Returns success with updated cap table, diff, and metrics
    OR error with validation messages.
    """
    result = tool_executor.execute_cap_table_editor(request)
    return JSONResponse(content=result)


@app.post("/api/tool/approve")
async def approve_tools(tool_call_ids: List[str]):
    """
    Approve and execute pending tool calls.
    
    Args:
        tool_call_ids: List of tool call IDs to approve and execute
        
    Returns:
        List of execution results
    """
    results = []
    
    for call_id in tool_call_ids:
        try:
            result = tool_orchestrator.execute_tool_call(call_id)
            results.append({
                "tool_call_id": call_id,
                "status": "success",
                "result": result
            })
        except Exception as e:
            results.append({
                "tool_call_id": call_id,
                "status": "error",
                "error": str(e)
            })
    
    return JSONResponse(content={"results": results})


@app.get("/api/tool/pending")
async def get_pending_tools():
    """Get all pending tool calls awaiting approval."""
    pending = tool_orchestrator.get_pending_calls()
    return JSONResponse(content=[call.model_dump() for call in pending])


@app.get("/api/cap-table")
async def get_cap_table():
    """Get current cap table state with computed metrics."""
    cap_table = cap_table_service.get_cap_table()
    metrics = cap_table_service.calculate_metrics()

    return {
        "capTable": cap_table,
        "metrics": metrics
    }


@app.get("/api/cap-table/download")
async def download_cap_table(format: str = "json"):
    """
    Download cap table as JSON file.
    """
    if format != "json":
        raise HTTPException(
            status_code=400, detail="Only JSON format supported")

    cap_table = cap_table_service.get_cap_table()
    company_name = cap_table.get("company", {}).get("name", "captable")

    # Create safe filename
    safe_name = "".join(c for c in company_name if c.isalnum()
                        or c in (' ', '-', '_')).strip()
    filename = f"{safe_name}_captable.json"

    return JSONResponse(
        content=cap_table,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@app.get("/api/cap-table/excel")
async def export_excel():
    """
    Generate and download Excel file from current cap table.
    Calls the existing generate_from_data() function.
    """
    cap_table = cap_table_service.get_cap_table()
    company_name = cap_table.get("company", {}).get("name", "captable")

    # Create safe filename
    safe_name = "".join(c for c in company_name if c.isalnum()
                        or c in (' ', '-', '_')).strip()
    filename = f"{safe_name}_captable.xlsx"

    # Generate Excel in temp file
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.xlsx', delete=False) as tmp:
        temp_path = tmp.name

    try:
        # Generate Excel
        generate_from_data(cap_table, temp_path)

        # Return file
        return FileResponse(
            path=temp_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=filename,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except Exception as e:
        # Clean up temp file on error
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise HTTPException(
            status_code=500, detail=f"Excel generation failed: {str(e)}")


@app.delete("/api/cap-table/reset")
async def reset_cap_table():
    """Reset cap table to initial empty state."""
    cap_table_service.reset()
    return {"message": "Cap table reset successfully"}


# ============================================================================
# Conversation Management Endpoints
# ============================================================================

@app.post("/api/conversation")
async def create_conversation():
    """Create a new conversation and return its ID."""
    conversation_id = conversation_store.create_conversation()
    return {"conversation_id": conversation_id}


@app.get("/api/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation details and message history."""
    conversation = conversation_store.get_conversation(conversation_id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {
        "conversation_id": conversation_id,
        "messages": conversation.get("messages", []),
        "created_at": conversation.get("created_at").isoformat(),
        "last_accessed": conversation.get("last_accessed").isoformat(),
    }


@app.delete("/api/conversation/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation."""
    deleted = conversation_store.delete_conversation(conversation_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {"message": f"Conversation {conversation_id} deleted"}


@app.post("/api/conversation/cleanup")
async def cleanup_conversations():
    """Remove expired conversations."""
    count = conversation_store.cleanup_expired()
    return {"removed_count": count}


@app.get("/api/conversation/stats")
async def conversation_stats():
    """Get conversation store statistics."""
    return conversation_store.get_stats()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=True
    )
