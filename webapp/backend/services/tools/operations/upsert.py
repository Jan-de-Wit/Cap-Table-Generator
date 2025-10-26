"""
Upsert Operation

Implements the upsert (update or insert) operation for modifying or creating values.
"""

import jsonpointer
from typing import Dict, Any
from .utils import normalize_path


def apply_upsert(cap_table: Dict[str, Any], path: str, value: Any) -> Dict[str, Any]:
    """
    Update or insert value at path.
    
    Args:
        cap_table: Cap table data structure
        path: JSON Pointer path
        value: Value to set
        
    Returns:
        Updated cap table
    """
    path = normalize_path(path)
    pointer = jsonpointer.JsonPointer(path)
    
    # Just set the value, creating path if needed
    pointer.set(cap_table, value)
    return cap_table

