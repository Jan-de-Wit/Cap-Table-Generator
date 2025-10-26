"""
Delete Operation

Implements the delete operation for removing values from the cap table.
Supports matching deletion for arrays based on partial value matching.
"""

import jsonpointer
from typing import Dict, Any, Optional, List
from .utils import normalize_path


def apply_delete(cap_table: Dict[str, Any], path: str, value: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Delete value at path or match in array.
    
    Args:
        cap_table: Cap table data structure
        path: JSON Pointer path
        value: Optional match criteria for array deletion
        
    Returns:
        Updated cap table
        
    Raises:
        ValueError: If path does not exist or match not found
    """
    path = normalize_path(path)
    pointer = jsonpointer.JsonPointer(path)
    
    try:
        target = pointer.resolve(cap_table)
    except jsonpointer.JsonPointerException:
        raise ValueError(f"Path does not exist: {path}")
    
    # If value is provided, treat as array deletion with matching
    if value is not None and isinstance(target, list):
        # Find matching element
        matching_indices = _find_matching_indices(target, value)
        
        if not matching_indices:
            # No match found
            value_str = ", ".join(f"{k}={v}" for k, v in value.items())
            raise ValueError(f"No matching element found in {path} with {value_str}")
        
        if len(matching_indices) > 1:
            # Multiple matches - delete all
            for idx in reversed(matching_indices):
                del target[idx]
        else:
            # Single match - delete it
            del target[matching_indices[0]]
    else:
        # Simple path deletion
        parent_path = "/" + "/".join(path.split("/")[:-1])
        field_name = path.split("/")[-1]
        
        if not field_name:
            # Deleting entire array/object
            parent = jsonpointer.JsonPointer(parent_path).resolve(cap_table)
            pointer.set(cap_table, None)
        else:
            # Deleting a field
            parent = jsonpointer.JsonPointer(parent_path).resolve(cap_table)
            if isinstance(parent, dict):
                del parent[field_name]
            elif isinstance(parent, list):
                del parent[int(field_name)]
    
    return cap_table


def _find_matching_indices(array: List[Dict[str, Any]], match: Dict[str, Any]) -> List[int]:
    """
    Find indices in array where object matches all criteria in match dict.
    
    Args:
        array: List of objects to search
        match: Dict of key-value pairs to match
        
    Returns:
        List of indices matching the criteria
    """
    matching = []
    
    for idx, item in enumerate(array):
        if not isinstance(item, dict):
            continue
        
        # Check if all match criteria are satisfied
        matches = all(
            item.get(key) == value 
            for key, value in match.items()
        )
        
        if matches:
            matching.append(idx)
    
    return matching

