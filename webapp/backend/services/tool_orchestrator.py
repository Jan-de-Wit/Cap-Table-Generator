"""
Tool Orchestrator - Manages tool call execution with approval workflow.
Handles both automatic and approval-required execution modes.
"""

import uuid
import logging
from typing import Dict, Any, List, Optional
from enum import Enum

from webapp.backend.services.tool_executor import tool_executor
from webapp.backend.services.captable_service import cap_table_service
from webapp.backend.models import (
    CapTableEditorRequest,
    ToolCall,
    ToolCallProposal,
    ExecutionMode
)
from webapp.backend.utils.color_logger import (
    setup_tool_logging,
    log_tool_call_start,
    log_tool_call_validated,
    log_tool_call_executing,
    log_tool_call_success,
    log_tool_call_failure,
    log_orchestration_event,
)

logger = setup_tool_logging(__name__)


class ToolCallStatus(Enum):
    """Status of a tool call."""
    PENDING = "pending"  # Awaiting approval
    APPROVED = "approved"  # Approved, ready to execute
    EXECUTING = "executing"  # Currently being executed
    SUCCESS = "success"  # Executed successfully
    REJECTED = "rejected"  # User rejected
    FAILED = "failed"  # Execution failed


class ToolOrchestrator:
    """
    Orchestrates tool call execution with mode support.
    Manages pending tool calls and approval workflows.
    """
    
    def __init__(self):
        """Initialize orchestrator."""
        self.pending_calls: Dict[str, ToolCall] = {}
        self.execution_history: List[ToolCall] = []
        self._execution_results: Dict[str, Any] = {}  # Store results by call_id
    
    def propose_tool_call(
        self,
        name: str,
        arguments: Dict[str, Any],
        execution_mode: ExecutionMode
    ) -> ToolCallProposal:
        """
        Create a tool call proposal with preview.
        
        Args:
            name: Tool name (currently only 'cap_table_editor')
            arguments: Tool arguments
            execution_mode: Execution mode
            
        Returns:
            Tool call proposal with preview data
        """
        # Generate unique ID for this tool call
        call_id = str(uuid.uuid4())
        
        # Log comprehensive tool call start
        log_tool_call_start(logger, call_id, name, arguments, execution_mode.value)
        
        # Create tool call object
        tool_call = ToolCall(
            id=call_id,
            name=name,
            arguments=arguments,
            status=ToolCallStatus.PENDING.value
        )
        
        # Try to get a preview of the changes
        # NOTE: In AUTO mode, skip preview to avoid double execution
        # Preview is only useful in APPROVAL mode to show the user before execution
        preview = None
        validation_errors = []
        
        # Only run preview in APPROVAL mode
        if execution_mode == ExecutionMode.APPROVAL:
            try:
                # Simulate the operation without mutating state
                preview = self._preview_changes(name, arguments)
                
                # Extract validation errors from preview result
                if preview:
                    # Check for explicit error response
                    if preview.get("ok") is False:
                        # Look for errors array (structured error response)
                        if "errors" in preview:
                            for error in preview.get("errors", []):
                                if isinstance(error, dict):
                                    error_msg = error.get("message", str(error))
                                else:
                                    error_msg = str(error)
                                validation_errors.append(error_msg)
                                
                        # Check for single error string
                        elif "error" in preview:
                            error_msg = preview.get("error")
                            if error_msg:
                                validation_errors.append(str(error_msg))
                                
                        logger.warning(
                            f"Preview returned error status - {len(validation_errors)} error(s) found"
                        )
                    else:
                        # Success case
                        logger.info("Preview completed successfully")
                    
            except Exception as e:
                error_msg = str(e)
                validation_errors.append(error_msg)
                logger.error(f"Preview failed with exception: {e}")
                logger.exception(e)
        else:
            # AUTO mode - no preview needed, will execute directly
            logger.debug("AUTO mode - skipping preview, will execute directly")
        
        # Store pending call
        self.pending_calls[call_id] = tool_call
        
        # Create proposal
        proposal = ToolCallProposal(
            tool_call=tool_call,
            preview=preview,
            validation_errors=validation_errors
        )
        
        # Log validation result
        log_tool_call_validated(logger, call_id, validation_errors)
        
        log_orchestration_event(
            logger,
            f"Tool call {call_id} proposed in {execution_mode.value} mode",
            call_id,
            f"Validation: {'PASSED' if not validation_errors else f'FAILED ({len(validation_errors)} errors)'}"
        )
        
        return proposal
    
    def _preview_changes(
        self,
        name: str,
        arguments: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Preview changes without mutating state.
        
        Executes the operation in preview mode, which validates the operation
        and generates a preview but does NOT persist changes to the cap table.
        
        Args:
            name: Tool name
            arguments: Tool arguments
            
        Returns:
            Preview data with diff and metrics, or error response
        """
        logger.debug(f"Previewing changes for tool: {name}")
        
        if name != "cap_table_editor":
            logger.warning(f"Unknown tool name for preview: {name}")
            return None
        
        # Create request from arguments
        try:
            request = CapTableEditorRequest(**arguments)
            logger.debug(f"Created request: operation={request.operation}, path={request.path}")
        except Exception as e:
            logger.error(f"Failed to create request from arguments: {e}")
            return {
                "ok": False,
                "errors": [
                    {
                        "path": arguments.get("path", "/"),
                        "message": f"Invalid request parameters: {str(e)}",
                        "rule": "request_validation"
                    }
                ]
            }
        
        # Execute the operation in preview mode (won't persist state)
        try:
            result = tool_executor.execute_cap_table_editor(request, preview_mode=True)
            
            # Log result
            if result and "ok" in result:
                if result.get("ok"):
                    logger.debug("Preview execution succeeded")
                else:
                    logger.warning(f"Preview execution failed: {result.get('errors', [])}")
            
            return result
            
        except Exception as e:
            logger.error(f"Preview execution raised exception: {e}")
            logger.exception(e)
            
            # Format as error response
            return {
                "ok": False,
                "errors": [
                    {
                        "path": arguments.get("path", "/"),
                        "message": str(e),
                        "rule": "execution_error"
                    }
                ]
            }
    
    def execute_tool_call(
        self,
        call_id: str
    ) -> Dict[str, Any]:
        """
        Execute an approved tool call.
        
        Args:
            call_id: Tool call ID to execute
            
        Returns:
            Execution result
        """
        if call_id not in self.pending_calls:
            log_tool_call_failure(logger, call_id, f"Tool call not found in pending calls")
            raise ValueError(f"Tool call {call_id} not found")
        
        tool_call = self.pending_calls[call_id]
        
        # Log execution start with parameters
        operation = tool_call.arguments.get('operation', 'unknown')
        log_tool_call_executing(logger, call_id, tool_call.name, operation)
        logger.info(f"Arguments preview: {tool_call.arguments}")
        
        # Update status
        tool_call.status = ToolCallStatus.EXECUTING.value
        
        try:
            # Execute based on tool name
            if tool_call.name == "cap_table_editor":
                result = self._execute_cap_table_editor(tool_call.arguments)
            else:
                raise ValueError(f"Unknown tool: {tool_call.name}")
            
            # Check if result contains errors
            if result and result.get("ok") is False:
                # Execution completed but returned validation errors
                tool_call.status = ToolCallStatus.FAILED.value
                
                # Store result for later retrieval
                self._execution_results[call_id] = result
                
                error_messages = []
                if "errors" in result:
                    for error in result.get("errors", []):
                        if isinstance(error, dict):
                            error_msg = error.get("message", str(error))
                        else:
                            error_msg = str(error)
                        error_messages.append(error_msg)
                
                error_summary = "; ".join(error_messages) if error_messages else "Unknown validation error"
                log_tool_call_failure(logger, call_id, f"Validation failed: {error_summary}")
                
                # Move to history
                self.execution_history.append(tool_call)
                del self.pending_calls[call_id]
                
                return result
            
            # Success path
            tool_call.status = ToolCallStatus.SUCCESS.value
            
            # Store result for later retrieval
            self._execution_results[call_id] = result
            
            # Move to history
            self.execution_history.append(tool_call)
            del self.pending_calls[call_id]
            
            # Log success with result details
            log_tool_call_success(logger, call_id, result)
            
            return result
            
        except Exception as e:
            tool_call.status = ToolCallStatus.FAILED.value
            log_tool_call_failure(logger, call_id, f"Exception: {str(e)}")
            logger.exception(e)
            raise
    
    def _execute_cap_table_editor(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute cap table editor tool."""
        logger.debug(f"Executing cap_table_editor with: operation={arguments.get('operation')}")
        request = CapTableEditorRequest(**arguments)
        return tool_executor.execute_cap_table_editor(request)
    
    def approve_tool_call(self, call_id: str):
        """Mark a tool call as approved."""
        if call_id not in self.pending_calls:
            raise ValueError(f"Tool call {call_id} not found")
        
        self.pending_calls[call_id].status = ToolCallStatus.APPROVED.value
        log_orchestration_event(logger, "Approved tool call", call_id)
    
    def reject_tool_call(self, call_id: str):
        """Mark a tool call as rejected."""
        if call_id not in self.pending_calls:
            raise ValueError(f"Tool call {call_id} not found")
        
        tool_call = self.pending_calls[call_id]
        tool_call.status = ToolCallStatus.REJECTED.value
        
        log_orchestration_event(logger, "Rejected tool call", call_id)
        
        # Move to history
        self.execution_history.append(tool_call)
        del self.pending_calls[call_id]
    
    def get_pending_calls(self) -> List[ToolCall]:
        """Get all pending tool calls."""
        return list(self.pending_calls.values())
    
    def clear_pending_calls(self):
        """Clear all pending tool calls."""
        self.pending_calls.clear()


# Global orchestrator instance
tool_orchestrator = ToolOrchestrator()

