"""
Conversation Router

Handles conversation management endpoints for message history.
"""

from fastapi import APIRouter
from webapp.backend.services.conversation_store import conversation_store
from typing import Dict, Any

router = APIRouter(prefix="/api", tags=["conversation"])


@router.post("/conversation")
async def create_conversation():
    """Create a new conversation and return its ID."""
    conversation_id = conversation_store.create_conversation()
    return {"conversation_id": conversation_id}


@router.get("/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation details and message history."""
    try:
        messages = conversation_store.get_messages(conversation_id)
        return {
            "conversation_id": conversation_id,
            "message_count": len(messages),
            "messages": messages
        }
    except KeyError:
        return {"error": "Conversation not found", "conversation_id": conversation_id}


@router.delete("/conversation/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation."""
    conversation_store.delete_conversation(conversation_id)
    return {"status": "deleted", "conversation_id": conversation_id}


@router.post("/conversation/cleanup")
async def cleanup_conversations():
    """Remove expired conversations."""
    removed = conversation_store.cleanup_expired()
    return {"removed_count": removed}


@router.get("/conversation/stats")
async def conversation_stats():
    """Get conversation store statistics."""
    stats = conversation_store.get_stats()
    return stats

