"""
Pydantic models for request/response validation.
"""

from pydantic import BaseModel, Field, model_validator
from typing import Optional, Literal, Any, List, Dict, Union
from enum import Enum


# ============================================================================
# Request Models
# ============================================================================

class ExecutionMode(str, Enum):
    """Tool execution mode."""
    AUTO = "auto"
    APPROVAL = "approval"


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: Optional[str] = Field(None, min_length=1)
    conversation_id: Optional[str] = None
    messages: Optional[List[Dict[str, str]]] = None
    execution_mode: ExecutionMode = Field(ExecutionMode.AUTO, description="Tool execution mode")
    approved_tool_call_ids: Optional[List[str]] = Field(None, description="Tool call IDs to approve")
    
    @model_validator(mode='after')
    def validate_message_or_messages(self):
        """Ensure either message or messages is provided."""
        if not self.message and not self.messages:
            raise ValueError("Either 'message' or 'messages' must be provided")
        return self


class CapTableEditorRequest(BaseModel):
    """Request model for cap_table_editor tool."""
    operation: Literal["replace", "append", "upsert", "delete", "bulkPatch"]
    path: Optional[str] = None
    value: Optional[Any] = None
    patch: Optional[List[Dict[str, Any]]] = None
    explain: bool = False


# ============================================================================
# Response Models
# ============================================================================

class ConfigResponse(BaseModel):
    """Response model for config endpoint."""
    provider: str
    model: str


class ErrorDetail(BaseModel):
    """Validation error detail."""
    path: str
    message: str
    rule: Optional[str] = None


class CapTableEditorErrorResponse(BaseModel):
    """Error response from cap_table_editor."""
    ok: Literal[False] = False
    errors: List[ErrorDetail]


class DiffItem(BaseModel):
    """Single diff item."""
    op: str
    path: str
    from_value: Optional[Any] = Field(None, alias="from")
    to: Optional[Any] = None
    description: Optional[str] = None


class OwnershipItem(BaseModel):
    """Ownership information for a holder."""
    holder_name: str
    shares_issued: float
    percent_issued: float
    shares_fd: float
    percent_fd: float


class Metrics(BaseModel):
    """Computed cap table metrics."""
    totals: Dict[str, float]
    ownership: List[OwnershipItem]
    pool: Dict[str, float]


class CapTableEditorSuccessResponse(BaseModel):
    """Success response from cap_table_editor."""
    ok: Literal[True] = True
    cap_table: Dict[str, Any] = Field(..., alias="capTable")
    diff: List[DiffItem]
    metrics: Metrics


class CapTableResponse(BaseModel):
    """Response model for cap table endpoint."""
    cap_table: Dict[str, Any] = Field(..., alias="capTable")
    metrics: Metrics


class ChatMessage(BaseModel):
    """Chat message in conversation."""
    role: Literal["user", "assistant", "system"]
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    messages: List[ChatMessage]
    preview: Optional[CapTableResponse] = None
    proposed_diff: Optional[List[DiffItem]] = Field(None, alias="proposedDiff")


# ============================================================================
# Tool Orchestration Models
# ============================================================================

class ToolCall(BaseModel):
    """Represents a single tool invocation."""
    id: str
    name: str
    arguments: Dict[str, Any]
    status: str  # pending, approved, executing, success, rejected, failed


class ToolCallProposal(BaseModel):
    """Tool call with preview of changes."""
    tool_call: ToolCall
    preview: Optional[Dict[str, Any]] = None  # Preview data from simulation
    validation_errors: List[str] = Field(default_factory=list)

