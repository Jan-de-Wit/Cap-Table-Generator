"""
LLM Service - OpenAI client with streaming.
Handles tool calling for cap_table_editor.
"""

import json
import logging
import os
import sys
from typing import AsyncGenerator, Dict, Any, List, Optional, Tuple
from openai import AsyncOpenAI
from webapp.backend.services.tool_orchestrator import tool_orchestrator
from webapp.backend.services.captable_service import cap_table_service
from webapp.backend.models import ExecutionMode

from webapp.backend.utils.color_logger import (
    setup_tool_logging,
    log_llm_tool_request,
    log_llm_tool_response,
)

# Set up logger with color coding
logger = setup_tool_logging(__name__)

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from webapp.backend.config import settings
from webapp.backend.services.tool_executor import tool_executor
from webapp.backend.models import CapTableEditorRequest

# System prompt for LLM
SYSTEM_PROMPT = """You are Cappy, an assistant for managing capitalization tables through a chat interface.

AVAILABLE TOOLS:
1. get_schema_data - Retrieve the schema to understand available fields and structure
2. cap_table_editor - Apply changes to the cap table data (requires schema knowledge)

CORE WORKFLOW:
1. Use get_schema_data when you need to understand field requirements
2. Use cap_table_editor to modify data - never output raw JSON
3. Ask clarifying questions when details are missing
4. Explain your actions before executing them

CRITICAL RULE - PREVENT DUPLICATES:
Before creating any entity (holder, class, terms, round), ALWAYS check if it already exists in the current cap table.
- If a holder/class/round with the same name already exists, DO NOT create it again
- Simply reference the existing entity in your response
- Only use append operation when creating a genuinely NEW entity
- The tool will reject attempts to create duplicate names

KEY RULES:
- All names must be unique within their entity type
- References must exist (e.g., holder_name must match existing holder)
- For preferred shares: Create terms package FIRST, then the class
- Dates: YYYY-MM-DD format
- Never output negative numbers

WORKFLOW FOR CREATING ENTITIES:
1. When user asks to add a holder/class/round, think: "Does this already exist?"
2. If creating NEW entity → use append
3. If entity already exists → do not create it, just acknowledge it exists
4. When creating instruments, the holder and class must already exist

ENTITY FIELD REQUIREMENTS:

Holders: REQUIRED (name, type), OPTIONAL (email)
  Types: founder, employee, investor, advisor, option_pool
  
Security Classes: REQUIRED (name, type), CONDITIONAL (terms_name for preferred)
  Types: common, preferred, option, warrant, safe, convertible_note
  OPTIONAL: conversion_ratio (default 1.0)
  
Instruments: REQUIRED (holder_name, class_name, initial_quantity)
  OPTIONAL: round_name, current_quantity, strike_price, acquisition_price, acquisition_date, vesting_terms, convertible_terms
  
  VestingTerms structure (for vesting_terms):
  - grant_date: date (YYYY-MM-DD) - REQUIRED
  - cliff_days: integer - REQUIRED (e.g., 365 for 1 year cliff)
  - vesting_period_days: integer - REQUIRED (e.g., 1460 for 4 years)
  - vested_quantity: calculated field (auto-generated, don't set)
  
  ConvertibleTerms structure (for convertible_terms):
  - investment_amount: number - OPTIONAL
  - discount_rate: number (0-1) - OPTIONAL (e.g., 0.20 for 20%)
  - price_cap: number - OPTIONAL
  - conversion_shares: calculated field (auto-generated, don't set)
  
Terms Packages: REQUIRED (name)
  OPTIONAL: liquidation_multiple (default 1.0), participation_type (default non_participating), participation_cap, seniority_rank, dividend_rate, anti_dilution
  
Rounds: REQUIRED (name, round_date)
  OPTIONAL: investment_amount, pre_money_valuation, post_money_valuation, price_per_share, shares_issued, option_pool_increase

EXAMPLE TOOL CALLS:

Add holder:
{
  "operation": "append",
  "path": "/holders",
  "value": {"name": "John Smith", "type": "founder", "email": "john@example.com"}
}

Add common stock class:
{
  "operation": "append",
  "path": "/classes",
  "value": {"name": "Common Stock", "type": "common"}
}

Add preferred with terms (2 steps):
Step 1 - Terms: {"operation": "append", "path": "/terms", "value": {"name": "Series A Terms", "liquidation_multiple": 1.0, "participation_type": "participating", "seniority_rank": 1}}
Step 2 - Class: {"operation": "append", "path": "/classes", "value": {"name": "Series A Preferred", "type": "preferred", "terms_name": "Series A Terms"}}

Add instrument:
{
  "operation": "append",
  "path": "/instruments",
  "value": {
    "holder_name": "John Smith",
    "class_name": "Common Stock",
    "initial_quantity": 100000,
    "acquisition_price": 1.0,
    "acquisition_date": "2024-01-15"
  }
}

Add instrument with vesting (options):
{
  "operation": "append",
  "path": "/instruments",
  "value": {
    "holder_name": "John Smith",
    "class_name": "Employee Options",
    "initial_quantity": 50000,
    "strike_price": 0.5,
    "acquisition_date": "2024-01-15",
    "vesting_terms": {
      "grant_date": "2024-01-15",
      "cliff_days": 365,
      "vesting_period_days": 1460
    }
  }
}

Add round:
{
  "operation": "append",
  "path": "/rounds",
  "value": {
    "name": "Series A",
    "round_date": "2024-06-01",
    "investment_amount": 5000000,
    "pre_money_valuation": 20000000,
    "post_money_valuation": 25000000
  }
}

TONE: Be concise, conversational, and explain before acting."""

# Tool definition for cap_table_editor
CAP_TABLE_EDITOR_TOOL = {
    "type": "function",
    "function": {
        "name": "cap_table_editor",
        "description": "Apply structured changes to the current cap table JSON and return updated document, diff, and recomputed metrics.",
        "parameters": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["replace", "append", "upsert", "delete", "bulkPatch"],
                    "description": "Type of operation to perform"
                },
                "path": {
                    "type": "string",
                    "description": "JSON Pointer path (e.g., '/holders', '/company/name')"
                },
                "value": {
                    "description": "Value to set (for replace, append, upsert)"
                },
                "patch": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "op": {"type": "string", "enum": ["add", "replace", "remove"]},
                            "path": {"type": "string"},
                            "value": {}
                        }
                    },
                    "description": "Array of JSON Patch operations (for bulkPatch)"
                },
                "explain": {
                    "type": "boolean",
                    "description": "Whether to include detailed explanation",
                    "default": True
                }
            },
            "required": ["operation"]
        }
    }
}

# Tool definition for get_schema_data
GET_SCHEMA_DATA_TOOL = {
    "type": "function",
    "function": {
        "name": "get_schema_data",
        "description": "Retrieve the current schema and field definitions for the cap table structure. Use this to understand what fields are required and available for different entities.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}


class LLMService:
    """Unified LLM service with streaming support."""
    
    def __init__(self):
        """Initialize LLM client."""
        self.provider = settings.active_provider
        self.model = settings.active_model
        
        if self.provider == "openai":
            self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _create_entity_summary(self, cap_table: Dict[str, Any]) -> str:
        """
        Create a structured summary of existing entities to help LLM avoid creating duplicates.
        
        Args:
            cap_table: Current cap table data
            
        Returns:
            Structured summary string of existing entities
        """
        sections = []
        
        # Company
        company = cap_table.get("company", {})
        if company.get("name"):
            sections.append(f"COMPANY: {company.get('name')}")
        
        # Holders
        holders = cap_table.get("holders", [])
        if holders:
            holder_names = ", ".join([f"{h.get('name')} ({h.get('type')})" for h in holders])
            sections.append(f"HOLDERS: {holder_names}")
        
        # Classes
        classes = cap_table.get("classes", [])
        if classes:
            class_names = ", ".join([f"{c.get('name')} ({c.get('type')})" for c in classes])
            sections.append(f"CLASSES: {class_names}")
        
        # Terms
        terms = cap_table.get("terms", [])
        if terms:
            term_names = ", ".join([t.get('name') for t in terms])
            sections.append(f"TERMS: {term_names}")
        
        # Rounds
        rounds = cap_table.get("rounds", [])
        if rounds:
            round_names = ", ".join([f"{r.get('name')} ({r.get('round_date')})" for r in rounds])
            sections.append(f"ROUNDS: {round_names}")
        
        # Instruments summary (more compact)
        instruments = cap_table.get("instruments", [])
        if instruments:
            sections.append(f"INSTRUMENTS: {len(instruments)} total holdings")
        
        if not sections:
            return "No entities exist yet - all will be new."
        
        return " | ".join(sections)
    
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
        
        # Create a summary of existing entities to help LLM avoid duplicates
        existing_context = self._create_entity_summary(current_cap_table)
        
        # Prepare messages with system prompt and current state context
        system_content = SYSTEM_PROMPT + "\n\nCURRENT CAP TABLE STATE (format: KEY: value1, value2 | KEY: value...):\n" + existing_context
        base_messages = [{"role": "system", "content": system_content}]
        base_messages.extend(messages)
        
        # Clear previous execution results for this request
        tool_orchestrator._execution_results.clear()
        if hasattr(tool_orchestrator, '_execution_results_by_call'):
            tool_orchestrator._execution_results_by_call.clear()
        
        # Multi-step loop: continue until LLM stops making tool calls
        max_iterations = 10
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
                tools=[CAP_TABLE_EDITOR_TOOL, GET_SCHEMA_DATA_TOOL],
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
            
            # Execute tool calls
            logger.info(f"[LLM_ITERATION] Executing {len(tool_calls)} tool call(s) in iteration {iteration}")
            yield json.dumps({"event": "tool_calls_start", "data": {"count": len(tool_calls), "iteration": iteration}})
            
            tool_results_messages = []
            
            for tool_call in tool_calls:
                tool_name = tool_call.get('name')
                logger.info(f"[LLM_TOOL_REQUEST] Processing: {tool_name}")
                
                # Emit tool execution start event
                yield json.dumps({
                    "event": "tool_execution_start", 
                    "data": {
                        "tool_name": tool_name,
                        "operation": tool_call.get('arguments', '{}'),
                        "iteration": iteration
                    }
                })
                
                # Execute tool call and get result (events yielded inline)
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
                            
                            # Format result for LLM consumption (always JSON for consistency)
                            # Build a structured message for the LLM
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


# Global service instance
llm_service = LLMService()

