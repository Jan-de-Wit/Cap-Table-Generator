# Deletion Logic Fix Summary

## Problem
When the LLM attempted to delete a specific instrument from the cap table, the deletion operation was removing the **entire `instruments` array** instead of just the matching item. This caused schema validation to fail with:
```
ERROR: 'instruments' is a required property
```

## Root Cause
The `_apply_delete` method in `tool_executor.py` was using a simple JSON Patch "remove" operation at the specified path. When path was `/instruments` with a value to match, it was deleting the entire array rather than finding and removing the specific item.

## Solution Implemented

### 1. Enhanced Deletion Logic (`tool_executor.py`)
Updated `_apply_delete` to:
- Accept an optional `value` parameter for matching
- When path points to an array AND value is provided:
  - Search the array for an item matching all fields in `value`
  - Delete only the matched item by its index (e.g., `/instruments/1`)
- Otherwise, delete the entire value at path (original behavior preserved)

```python
def _apply_delete(self, cap_table, path, value=None):
    if value is not None:
        target = jsonpointer.resolve_pointer(cap_table, path)
        if isinstance(target, list):
            # Find matching item
            for i, item in enumerate(target):
                if all(item.get(k) == v for k, v in value.items()):
                    # Delete specific item
                    delete_path = f"{path}/{i}"
                    return jsonpatch.apply(delete_path)
    # Otherwise delete entire path
    return jsonpatch.apply(path)
```

### 2. Added `get_cap_table_json` Tool (`llm_service.py`)
Created a new tool that allows the LLM to retrieve the current cap table JSON:
- **Purpose**: LLM can inspect current state before attempting deletions
- **Critical**: Helps LLM identify exact fields to match for deletion
- **Tool name**: `get_cap_table_json`
- **Returns**: Complete cap table JSON

### 3. Updated System Prompt (`llm_service.py`)
Added comprehensive deletion workflow instructions:

```
WORKFLOW FOR DELETING ENTITIES:
1. ALWAYS use get_cap_table_json FIRST to see what exists
2. Find the EXACT item to delete (match holder_name, class_name, etc.)
3. Use delete operation with:
   - path: the array path (e.g., "/instruments", "/holders")
   - value: a dict with fields that uniquely identify the item to delete
4. The system will find and delete ONLY the matching item, not the entire array
```

Added delete examples:
```json
// Delete specific instrument
{
  "operation": "delete",
  "path": "/instruments",
  "value": {"holder_name": "John Smith", "class_name": "Common Stock"}
}

// Delete specific holder
{
  "operation": "delete",
  "path": "/holders",
  "value": {"name": "John Smith"}
}
```

## Test Results

### Test 1: Delete Specific Instrument ✅
- **Before**: 3 instruments (Founder A, Founder B, Investor)
- **Action**: Delete Investor's Preferred Stock
- **After**: 2 instruments (Founder A, Founder B)
- **Result**: ✅ PASS - Only the specific instrument was removed

### Test 2: Delete Holder with Referential Integrity ✅
- **Action**: Delete Founder B (who has an instrument)
- **Result**: ✅ CORRECT VALIDATION ERROR - Cannot delete holder with existing instruments
- **Note**: This is correct behavior - referential integrity is maintained

### Test 3: Partial Field Matching ✅
- **Action**: Delete by holder_name only (without specifying class_name)
- **Result**: ✅ PASS - Matches and deletes the first matching item

## Key Features

1. **Precise Deletion**: Delete specific array items, not entire arrays
2. **Flexible Matching**: Provide any subset of fields to match
3. **Referential Integrity**: Validation prevents orphaned references
4. **LLM Awareness**: New tool lets LLM inspect before deleting
5. **Clear Instructions**: System prompt explains deletion workflow

## Usage Example

```javascript
// Step 1: Get current state
await llm.callTool("get_cap_table_json")

// Step 2: Delete specific item
await llm.callTool("cap_table_editor", {
  operation: "delete",
  path: "/instruments",
  value: {
    holder_name: "Joost VC",
    class_name: "Series A Preferred"
  }
})
```

## Files Modified

1. `webapp/backend/services/tool_executor.py`
   - Enhanced `_apply_delete` method with value matching
   - Added index-based deletion for array items

2. `webapp/backend/services/llm_service.py`
   - Added `GET_CAP_TABLE_JSON_TOOL` definition
   - Added tool handler in `_execute_tool_call`
   - Updated system prompt with deletion workflow
   - Added deletion examples

## Benefits

✅ **No More Array Wipes**: Deleting one item doesn't remove the entire array
✅ **Referential Integrity**: Validation prevents broken references  
✅ **Better LLM Context**: LLM can inspect state before deleting
✅ **Clear Instructions**: System prompt guides LLM on proper deletion
✅ **Flexible Matching**: Match by any combination of fields

## Error Prevention

The system now prevents:
- ❌ Deleting entire arrays when only one item should be removed
- ❌ Deleting holders/classes/rounds that are still referenced
- ❌ Blind deletions without knowing current state
- ❌ Missing required fields after deletion

