"""
Replace Operation

Implements the replace operation for updating existing values in the cap table.
"""

import jsonpointer
from typing import Dict, Any
from .utils import normalize_path


def apply_replace(cap_table: Dict[str, Any], path: str, value: Any) -> Dict[str, Any]:
    """
    Replace value at path.
    
    Args:
        cap_table: Cap table data structure
        path: JSON Pointer path to replace
        value: New value to set
        
    Returns:
        Updated cap table
        
    Raises:
        ValueError: If path does not exist
    """
    path = normalize_path(path)
    
    # Use jsonpointer for safe access
    pointer = jsonpointer.JsonPointer(path)
    
    # Check if path exists
    try:
        pointer.resolve(cap_table)
    except jsonpointer.JsonPointerException:
        raise ValueError(f"Path does not exist: {path}")
    
    # Set new value
    pointer.set(cap_table, value)
    return cap_table

