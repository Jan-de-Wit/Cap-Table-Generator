"""
Tools Router

Handles tool execution, approval, and pending tool call management.
"""

from typing import List
from fastapi import APIRouter
from webapp.backend.services.tool_executor import tool_executor
from webapp.backend.services.tool_orchestrator import tool_orchestrator
from webapp.backend.models import CapTableEditorRequest

router = APIRouter(prefix="/api", tags=["tools"])


@router.post("/tool/cap_table_editor")
async def execute_tool(request: CapTableEditorRequest):
    """
    Execute a tool operation on the cap table.
    For manual tool execution with validation.
    """
    result = await tool_executor.execute_operation(request)
    return result


@router.post("/tool/approve")
async def approve_tools(tool_call_ids: List[str]):
    """
    Approve pending tool calls for execution.
    Used in approval mode to queue tool calls.
    """
    for tool_call_id in tool_call_ids:
        tool_orchestrator.approve_tool_call(tool_call_id)
    
    return {
        "status": "approved",
        "approved_count": len(tool_call_ids)
    }


@router.get("/tool/pending")
async def get_pending_tools():
    """Get all pending tool calls awaiting approval."""
    pending = tool_orchestrator.get_pending_calls()
    return {
        "pending_count": len(pending),
        "pending": pending
    }

