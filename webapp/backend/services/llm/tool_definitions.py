"""
Tool Definitions for LLM

Defines the schemas for OpenAI function calling used by the cap table editor.
These tools allow the LLM to interact with the cap table data.
"""

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

# Tool definition for get_cap_table_json
GET_CAP_TABLE_JSON_TOOL = {
    "type": "function",
    "function": {
        "name": "get_cap_table_json",
        "description": "Retrieve the current cap table JSON data to see what entities exist. CRITICAL: Always use this before attempting to delete items so you know exactly what to match.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}


def get_all_tools() -> list[dict]:
    """
    Get all available tools for the LLM.
    
    Returns:
        List of tool definition dictionaries
    """
    return [
        CAP_TABLE_EDITOR_TOOL,
        GET_SCHEMA_DATA_TOOL,
        GET_CAP_TABLE_JSON_TOOL
    ]

