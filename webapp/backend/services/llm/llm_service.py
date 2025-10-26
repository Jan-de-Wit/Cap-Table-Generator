"""
Main LLM Service Orchestrator

Coordinates LLM interactions with tool calling, streaming, and multi-step execution.
Delegates to specialized modules for client, tools, prompts, and streaming.
"""

import json
import logging
import sys
import os
from typing import AsyncGenerator, Dict, Any, List, Optional, Tuple

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from webapp.backend.services.tool_orchestrator import tool_orchestrator
from webapp.backend.services.captable_service import cap_table_service
from webapp.backend.models import ExecutionMode
from webapp.backend.utils.color_logger import (
    setup_tool_logging,
    log_llm_tool_request,
    log_llm_tool_response,
)
from webapp.backend.config import settings

# Import specialized modules
from .client import LLMClient
from .tool_definitions import get_all_tools
from .prompt_manager import build_system_prompt_with_context

# Set up logger
logger = setup_tool_logging(__name__)


class LLMService:
    """
    Unified LLM service with streaming support.
    
    Coordinates OpenAI interactions with tool calling, multi-step execution,
    and streaming responses back to the frontend.
    """
    
    def __init__(self):
        """Initialize LLM service with client."""
        self.client = LLMClient()
        self.provider = self.client.provider
        self.model = self.client.model
        
        if self.provider == "openai":
            self.openai_client = self.client.get_client()
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _analyze_tool_dependencies(self, tool_calls: List[Dict[str, Any]]) -> List[List[int]]:
        """
        Analyze dependencies between tool calls and group them into batches.
        
        Args:
            tool_calls: List of tool call dictionaries
            
        Returns:
            List of batches, where each batch is a list of tool call indices
        """
        # Parse all tool calls to understand what they're doing
        parsed_calls = []
        for idx, tc in enumerate(tool_calls):
            try:
                args = json.loads(tc.get("arguments", "{}"))
                operation = args.get("operation")
                path = args.get("path", "")
                value = args.get("value", {})
                
                parsed_calls.append({
                    "index": idx,
                    "operation": operation,
                    "path": path,
                    "value": value,
                    "name": tc.get("name")
                })
            except:
                # If we can't parse, treat as independent
                parsed_calls.append({
                    "index": idx,
                    "operation": None,
                    "path": None,
                    "value": {},
                    "name": tc.get("name")
                })
        
        # Build dependency graph
        # dependencies[i] = list of indices that call i depends on
        dependencies = {i: [] for i in range(len(parsed_calls))}
        
        for i, call_i in enumerate(parsed_calls):
            # Check if call_i depends on any previous call
            for j, call_j in enumerate(parsed_calls):
                if i == j:
                    continue
                if _depends_on(call_i, call_j):
                    dependencies[i].append(j)
        
        # Topological sort to create batches
        batches = []
        remaining = set(range(len(parsed_calls)))
        visited = set()
        
        while remaining:
            # Find all calls with no unvisited dependencies
            batch_indices = []
            for idx in remaining:
                if all(dep in visited for dep in dependencies[idx]):
                    batch_indices.append(idx)
            
            if not batch_indices:
                # Circular dependency or all remaining depend on each other
                # Put all remaining in one batch
                batch_indices = list(remaining)
            
            batches.append(batch_indices)
            for idx in batch_indices:
                visited.add(idx)
                remaining.remove(idx)
        
        return batches
    
    async def chat_stream(
        self, 
        messages: List[Dict[str, str]],
        execution_mode: ExecutionMode = ExecutionMode.AUTO,
        approved_tool_call_ids: Optional[List[str]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat responses from OpenAI.
        Handles tool calls through orchestrator.
        
        Args:
            messages: Conversation history
            execution_mode: Tool execution mode
            approved_tool_call_ids: Tool call IDs to execute
            
        Yields:
            Event chunks from the LLM response
        """
        if self.provider == "openai":
            async for chunk in self._chat_stream_openai(messages, execution_mode, approved_tool_call_ids):
                yield chunk
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    async def _chat_stream_openai(
        self, 
        messages: List[Dict[str, str]],
        execution_mode: ExecutionMode,
        approved_tool_call_ids: Optional[List[str]]
    ) -> AsyncGenerator[str, None]:
        """Stream from OpenAI with tool orchestration - supports unlimited multi-step execution."""
        # Get current cap table state for context
        current_cap_table = cap_table_service.get_cap_table()
        
        # Create system prompt with context
        system_content = build_system_prompt_with_context(current_cap_table)
        base_messages = [{"role": "system", "content": system_content}]
        base_messages.extend(messages)
        
        # Clear previous execution results for this request
        tool_orchestrator._execution_results.clear()
        if hasattr(tool_orchestrator, '_execution_results_by_call'):
            tool_orchestrator._execution_results_by_call.clear()
        
        # Get all available tools
        tools = get_all_tools()
        
        # Multi-step loop: continue until LLM stops making tool calls
        max_iterations = 25
        iteration = 0
        conversation_messages = base_messages.copy()
        
        # Emit thinking start event
        import time
        thinking_start = time.time()
        yield json.dumps({"event": "thinking_start", "data": {}})
        
        while iteration < max_iterations:
            iteration += 1
            logger.info(f"[LLM_ITERATION] Starting iteration {iteration}/{max_iterations}")
            
            # Make LLM call with current conversation
            stream = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=conversation_messages,
                tools=tools,
                stream=True,
                temperature=0.7
            )
            
            tool_calls = []
            current_tool_call = None
            content_chunks = []
            has_started_content = False
            
            # Stream response and collect tool calls and content
            async for chunk in stream:
                delta = chunk.choices[0].delta
                
                # Handle content
                if delta.content:
                    # Track that we've started content
                    if not has_started_content:
                        has_started_content = True
                        if iteration == 1:
                            thinking_duration = time.time() - thinking_start
                            yield json.dumps({"event": "thinking_end", "data": {"duration_seconds": thinking_duration}})
                    
                    # Yield content as JSON event
                    content_chunks.append(delta.content)
                    yield json.dumps({"event": "content", "data": delta.content})
                
                # Handle tool calls
                if delta.tool_calls:
                    for tool_call_delta in delta.tool_calls:
                        if tool_call_delta.index is not None:
                            # New or existing tool call
                            while len(tool_calls) <= tool_call_delta.index:
                                tool_calls.append({"id": "", "name": "", "arguments": ""})
                            
                            current_tool_call = tool_calls[tool_call_delta.index]
                            
                            if tool_call_delta.id:
                                current_tool_call["id"] = tool_call_delta.id
                            if tool_call_delta.function.name:
                                current_tool_call["name"] = tool_call_delta.function.name
                            if tool_call_delta.function.arguments:
                                current_tool_call["arguments"] += tool_call_delta.function.arguments
            
            # Add content to conversation if present
            if content_chunks:
                assistant_content = "".join(content_chunks)
                conversation_messages.append({
                    "role": "assistant",
                    "content": assistant_content
                })
            
            # If no tool calls, LLM is done
            if not tool_calls:
                logger.info(f"[LLM_ITERATION] No tool calls in iteration {iteration} - completing task")
                break
            
            # Execute tool calls with batching
            logger.info(f"[LLM_ITERATION] Executing {len(tool_calls)} tool call(s) in iteration {iteration}")
            
            # Analyze dependencies and create batches
            batches = self._analyze_tool_dependencies(tool_calls)
            logger.info(f"[LLM_BATCHING] Grouped {len(tool_calls)} calls into {len(batches)} batch(es)")
            
            yield json.dumps({
                "event": "tool_calls_start", 
                "data": {
                    "count": len(tool_calls), 
                    "iteration": iteration,
                    "batches": len(batches)
                }
            })
            
            tool_results_messages = []
            
            # Execute each batch
            for batch_idx, batch_indices in enumerate(batches):
                batch_size = len(batch_indices)
                logger.info(f"[LLM_BATCHING] Executing batch {batch_idx + 1}/{len(batches)} with {batch_size} call(s)")
                
                yield json.dumps({
                    "event": "batch_start",
                    "data": {
                        "batch_index": batch_idx,
                        "batch_size": batch_size,
                        "total_batches": len(batches)
                    }
                })
                
                # Execute all calls in this batch
                for idx in batch_indices:
                    tool_call = tool_calls[idx]
                    tool_name = tool_call.get('name')
                    logger.info(f"[LLM_TOOL_REQUEST] Processing: {tool_name} (batch {batch_idx + 1}, call {idx})")
                    
                    # Emit tool execution start event
                    yield json.dumps({
                        "event": "tool_execution_start", 
                        "data": {
                            "tool_name": tool_name,
                            "operation": tool_call.get('arguments', '{}'),
                            "iteration": iteration,
                            "batch_index": batch_idx
                        }
                    })
                    
                    # Execute tool call and get result
                    result_content, events = await self._execute_tool_call(tool_call, execution_mode)
                    
                    # Yield all events from tool execution
                    for event in events:
                        yield event
                    
                    tool_results_messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.get("id"),
                        "name": tool_name,
                        "content": result_content
                    })
                
                yield json.dumps({
                    "event": "batch_complete",
                    "data": {
                        "batch_index": batch_idx,
                        "batch_size": batch_size
                    }
                })
            
            # Add assistant message with tool calls to conversation
            conversation_messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": tc.get("id"),
                    "type": "function",
                    "function": {
                        "name": tc.get("name"),
                        "arguments": tc.get("arguments", "{}")
                    }
                } for tc in tool_calls if tc.get("id")]
            })
            
            # Add tool results to conversation
            conversation_messages.extend(tool_results_messages)
            
            yield json.dumps({"event": "tools_complete", "data": {"count": len(tool_calls), "iteration": iteration}})
            
            logger.info(f"[LLM_ITERATION] Completed iteration {iteration}")
        
        if iteration >= max_iterations:
            logger.warning(f"[LLM_ITERATION] Reached max iterations ({max_iterations})")
    
    async def _execute_tool_call(self, tool_call: Dict[str, Any], execution_mode: ExecutionMode) -> Tuple[str, List[str]]:
        """Execute a single tool call and return (result_content, events_list)."""
        tool_name = tool_call.get('name')
        call_id = tool_call.get("id", "")
        events = []
        
        try:
            if tool_name == "get_schema_data":
                from src.captable.schema import CAP_TABLE_SCHEMA
                result = {"schema": CAP_TABLE_SCHEMA}
                
                events.append(json.dumps({
                    "event": "tool_result",
                    "data": {
                        "tool_call_id": call_id,
                        "result": result,
                        "status": "success"
                    }
                }))
                
                events.append(json.dumps({
                    "event": "tool_execution_complete",
                    "data": {
                        "tool_call_id": call_id,
                        "status": "success"
                    }
                }))
                
                return json.dumps(result), events
            
            elif tool_name == "get_cap_table_json":
                current_cap_table = cap_table_service.get_cap_table()
                result = {"capTable": current_cap_table}
                
                logger.info(f"[LLM_TOOL_RESPONSE] Returning current cap table JSON")
                
                events.append(json.dumps({
                    "event": "tool_result",
                    "data": {
                        "tool_call_id": call_id,
                        "result": result,
                        "status": "success"
                    }
                }))
                
                events.append(json.dumps({
                    "event": "tool_execution_complete",
                    "data": {
                        "tool_call_id": call_id,
                        "status": "success"
                    }
                }))
                
                return json.dumps(result), events
                
            elif tool_name == "cap_table_editor":
                args = json.loads(tool_call["arguments"])
                log_llm_tool_request(logger, tool_name, args)
                
                # Create proposal via orchestrator
                proposal = tool_orchestrator.propose_tool_call(
                    name=tool_name,
                    arguments=args,
                    execution_mode=execution_mode
                )
                
                call_id = proposal.tool_call.id
                
                if execution_mode == ExecutionMode.APPROVAL:
                    logger.info(f"[LLM_TOOL_RESPONSE] Approval mode - requesting approval for {call_id}")
                    # Emit proposal event for approval
                    events.append(json.dumps({
                        "event": "tool_proposal",
                        "data": {
                            "tool_call_id": call_id,
                            "name": proposal.tool_call.name,
                            "arguments": proposal.tool_call.arguments,
                            "preview": proposal.preview,
                            "validation_errors": proposal.validation_errors
                        }
                    }))
                    return "Awaiting approval", events
                else:
                    # Auto mode - check for validation errors first
                    if proposal.validation_errors:
                        logger.warning(f"[LLM_TOOL_RESPONSE] Auto mode - validation errors detected")
                        error_summary = "; ".join(proposal.validation_errors)
                        
                        log_llm_tool_response(logger, call_id, "failed (validation errors)", f"Errors: {error_summary}")
                        
                        # Send error back to LLM as tool result so it can rework
                        error_result = {
                            "ok": False,
                            "status": "failed",
                            "errors": [
                                {"path": "/", "message": err, "rule": "validation"} 
                                for err in proposal.validation_errors
                            ]
                        }
                        
                        events.append(json.dumps({
                            "event": "tool_execution_complete",
                            "data": {
                                "tool_call_id": call_id,
                                "status": "failed"
                            }
                        }))
                        
                        events.append(json.dumps({
                            "event": "tool_result",
                            "data": {
                                "tool_call_id": call_id,
                                "result": error_result,
                                "status": "failed"
                            }
                        }))
                        return json.dumps(error_result), events
                    else:
                        # No validation errors - execute immediately
                        logger.info(f"[LLM_TOOL_RESPONSE] Auto mode - executing immediately")
                        try:
                            result = tool_orchestrator.execute_tool_call(call_id)
                            
                            # Store result for tool results messages
                            if not hasattr(tool_orchestrator, '_execution_results_by_call'):
                                tool_orchestrator._execution_results_by_call = {}
                            tool_orchestrator._execution_results_by_call[call_id] = result
                            
                            # Determine status based on result
                            result_status = "success"
                            if result and "ok" in result and result.get("ok") is False:
                                result_status = "failed"
                                
                                error_summary = "Validation failed"
                                if "errors" in result:
                                    errors = result.get("errors", [])
                                    error_msgs = [e.get("message", str(e)) if isinstance(e, dict) else str(e) for e in errors]
                                    error_summary = "; ".join(error_msgs)
                                
                                log_llm_tool_response(logger, call_id, result_status, error_summary)
                            
                            else:
                                log_llm_tool_response(logger, call_id, result_status, f"Diff items: {len(result.get('diff', []))}")
                            
                            # Format result for LLM consumption
                            result_content = {
                                "ok": result_status == "success",
                                "status": result_status
                            }
                            
                            # Add detailed information if available
                            if result and isinstance(result, dict):
                                diff_items = result.get("diff", [])
                                metrics = result.get("metrics", {})
                                
                                if diff_items:
                                    result_content["changes_applied"] = [
                                        diff_item.get("description", "") 
                                        for diff_item in diff_items[:5]
                                    ]
                                
                                # Include metrics summary if available
                                if metrics:
                                    totals = metrics.get("totals", {})
                                    if totals:
                                        result_content["current_totals"] = {
                                            "issued": totals.get("issued", 0),
                                            "fully_diluted": totals.get("fullyDiluted", 0)
                                        }
                                
                                # Include any errors if present
                                if "errors" in result:
                                    result_content["errors"] = result.get("errors", [])
                            
                            # Emit tool execution complete event
                            events.append(json.dumps({
                                "event": "tool_execution_complete",
                                "data": {
                                    "tool_call_id": call_id,
                                    "status": result_status
                                }
                            }))
                            
                            events.append(json.dumps({
                                "event": "tool_result",
                                "data": {
                                    "tool_call_id": call_id,
                                    "result": result,
                                    "status": result_status
                                }
                            }))
                            
                            # Return JSON so LLM can parse both successes and failures consistently
                            return json.dumps(result_content), events
                            
                        except Exception as e:
                            error_msg = str(e)
                            log_llm_tool_response(logger, call_id, "failed", f"Exception: {error_msg}")
                            logger.exception(e)
                            
                            error_result = {
                                "ok": False,
                                "status": "failed",
                                "errors": [
                                    {"path": "/", "message": error_msg, "rule": "execution_error"}
                                ]
                            }
                            
                            # Send structured error result to LLM so it can rework
                            events.append(json.dumps({
                                "event": "tool_execution_complete",
                                "data": {
                                    "tool_call_id": call_id,
                                    "status": "failed"
                                }
                            }))
                            
                            events.append(json.dumps({
                                "event": "tool_result",
                                "data": {
                                    "tool_call_id": call_id,
                                    "result": error_result,
                                    "status": "failed"
                                }
                            }))
                            
                            return json.dumps(error_result), events
                
            else:
                logger.warning(f"[LLM_TOOL_REQUEST] Received unknown tool call: {tool_name}")
                return "Unknown tool", []
                
        except Exception as e:
            logger.error(f"[LLM_TOOL_RESPONSE] Error processing tool call: {str(e)}")
            logger.exception(e)
            events.append(json.dumps({
                "event": "content",
                "data": f"✗ Tool error: {str(e)}\n"
            }))
            return f"Error: {str(e)}", events


def _depends_on(call_a: Dict[str, Any], call_b: Dict[str, Any]) -> bool:
    """
    Check if call_a depends on call_b.
    
    Args:
        call_a: First tool call
        call_b: Second tool call
        
    Returns:
        True if call_a depends on call_b
    """
    # A depends on B if A reads something that B might write
    # or if A needs something that B creates
    
    # Append operations depend on the array existing
    # (but we create arrays on demand, so no dependency)
    
    # Delete operations should run before other operations on same path
    # to avoid references to deleted items
    if call_a.get("operation") == "delete" and call_b.get("operation") in ["replace", "upsert"]:
        if call_a.get("path") == call_b.get("path"):
            return True
    
    # Operations on different paths are independent
    return False


# Global service instance
llm_service = LLMService()

