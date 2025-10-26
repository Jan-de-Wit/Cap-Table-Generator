# Multi-Step Task Execution Audit

## Summary

**Issue Found: Limited to 2 Rounds Only**

The repository currently supports **exactly 2 rounds** of LLM tool calling, not unlimited multi-step execution. The cycle cannot continue beyond the second batch of tool calls.

---

## Current Implementation Flow

### Round 1: Initial Tool Calls
```python:364:559:webapp/backend/services/llm_service.py
# Lines 364-559: First batch executes
if tool_calls:
    # Execute first batch
    for tool_call in tool_calls:
        # Process and execute tools
        ...
```

**Location:** `webapp/backend/services/llm_service.py` lines 364-559

### Round 2: Continuation (One-Time Only)
```python:617:646:webapp/backend/services/llm_service.py
# Lines 617-646: Make continuation LLM call
continuation_messages = formatted_messages + [...] + tool_results_messages

summary_stream = await self.openai_client.chat.completions.create(
    model=self.model,
    messages=continuation_messages,
    tools=[...],
    stream=True
)
```

**Location:** `webapp/backend/services/llm_service.py` lines 617-646

### Round 2 Execution
```python:682:732:webapp/backend/services/llm_service.py
# Lines 682-732: Process additional tool calls from continuation
if more_tool_calls:
    for tool_call in more_tool_calls:
        # Execute additional tools
        ...
    
    yield json.dumps({"event": "tools_complete", ...})  # STOPS HERE
```

**Location:** `webapp/backend/services/llm_service.py` lines 682-732

**Problem:** After line 732, the function returns without checking for further tool calls.

---

## What Should Happen

For true multi-step execution, the flow should be:

```python
# Pseudocode of what SHOULD happen
while True:
    # Get LLM response with possible tool calls
    llm_response = await llm_client.chat(...)
    tool_calls = extract_tool_calls(llm_response)
    
    if not tool_calls:
        # LLM is done - no more tool calls
        break
    
    # Execute all tool calls
    results = []
    for tool_call in tool_calls:
        result = execute_tool(tool_call)
        results.append(result)
    
    # Add tool results to conversation
    conversation.append({
        "role": "assistant",
        "tool_calls": tool_calls
    })
    conversation.append({
        "role": "tool",
        "content": results
    })
    
    # Loop back to get LLM's next response
    # (LLM may make more tool calls or provide final answer)
```

---

## Current Limitation

1. ✅ Initial LLM makes tool calls
2. ✅ First batch executes
3. ✅ LLM reviews results via continuation call
4. ✅ LLM makes additional tool calls if needed (ROUND 2 ONLY)
5. ❌ **MISSING:** Loop back to step 3 for ROUND 3, ROUND 4, etc.

### Example Multi-Step Scenario

User asks: "Add a Series A preferred stock class with special terms"

**Ideal Execution (Infinite Loop):**
1. ROUND 1: LLM calls `get_schema_data` to understand structure
2. ROUND 2: LLM calls `cap_table_editor` to create terms package
3. ROUND 3: LLM calls `cap_table_editor` to create preferred class
4. ROUND 4: LLM provides summary response

**Current Execution (Fixed 2 Rounds):**
1. ROUND 1: Execute tool calls ✓
2. ROUND 2: Execute tool calls ✓
3. ROUND 3: **NO OPTION TO CONTINUE** ❌
4. ROUND 4: **NO OPTION TO CONTINUE** ❌

---

## Files Involved

- **`webapp/backend/services/llm_service.py`** (738 lines)
  - Lines 292-732: Main streaming logic
  - Lines 617-732: Continuation logic (non-looping)
  - **Problem:** No while loop to continue beyond 2 rounds

- **`webapp/backend/services/tool_orchestrator.py`** (343 lines)
  - Handles execution mode and approvals
  - Works correctly for each batch, but not called in a loop

- **`webapp/backend/services/tool_executor.py`** (446 lines)
  - Executes individual tool operations
  - Works correctly per execution

---

## Impact Assessment

### Low Impact Scenarios
- Simple single-step requests ("Add one holder")
- Requests with clear dependency chains that fit in 2 rounds
- Cases where LLM can batch operations in first round

### High Impact Scenarios
- Complex entity creation requiring multiple sequential steps
- Error recovery requiring additional tool calls after failed attempts
- Tasks requiring 3+ logical steps:
  - Creating preferred stock with terms
  - Multi-step data migrations
  - Complex validations requiring schema checks first

---

## Recommended Fix

Refactor the continuation logic in `llm_service.py`:

1. **Create a while loop** around the tool execution logic
2. **Continue until no more tool calls** are requested by the LLM
3. **Prevent infinite loops** by limiting max iterations (e.g., 10)
4. **Track iteration count** and emit events to frontend

### Example Fix Structure

```python
async def _chat_stream_openai(...):
    max_iterations = 10
    iteration = 0
    
    messages_with_context = create_base_messages()
    
    while iteration < max_iterations:
        iteration += 1
        
        # Get LLM response
        stream = await self.openai_client.chat.completions.create(
            model=self.model,
            messages=messages_with_context,
            tools=[...],
            stream=True
        )
        
        tool_calls = []
        content = ""
        
        # Stream and collect tool calls
        async for chunk in stream:
            # ... extract tool_calls and content ...
        
        yield content
        
        if not tool_calls:
            # LLM is done - no more tool calls
            break
        
        # Execute all tool calls
        results = []
        for tool_call in tool_calls:
            result = execute_tool(tool_call)
            results.append(result)
        
        # Update conversation for next iteration
        messages_with_context.append({
            "role": "assistant",
            "tool_calls": tool_calls
        })
        messages_with_context.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result
        } for tool_call, result in zip(tool_calls, results))
```

---

## Testing Recommendations

After implementing the fix, test these scenarios:

1. **3+ Step Task:** "Create a Series A preferred class with participation rights"
   - Should require: schema check → create terms → create class → summary

2. **Error Recovery:** Intentionally cause validation error, verify LLM can fix

3. **Max Iterations:** Ensure loop terminates after reasonable number

4. **Mixed Responses:** LLM makes tool calls in some rounds, text-only in others

---

## Conclusion

**Status:** ✅ **FIXED**

The system has been updated to support unlimited multi-step execution through a while loop with max_iterations=10. The LLM can now make tool calls in unlimited rounds until the task is complete.

**Implementation:** Refactored `llm_service.py` to use a while loop that continues until LLM makes no more tool calls or reaches max iterations (10).

**Changes Made:**
- Wrapped tool execution in `while iteration < max_iterations` loop
- LLM response → Execute tools → Update conversation → Loop back
- Added iteration tracking and logging
- Fixed tool execution to return (result, events) tuple instead of yielding
- Conversation messages accumulate through iterations
- Loop terminates when LLM makes no tool calls (task complete)

**Priority:** ~~Medium-High~~ **COMPLETED** ✅

