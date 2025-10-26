"""
Append Operation

Implements the append operation for adding new items to arrays in the cap table.
Includes duplicate name checking for entities.
"""

import jsonpointer
import logging
from typing import Dict, Any
from .utils import normalize_path

logger = logging.getLogger(__name__)


def apply_append(cap_table: Dict[str, Any], path: str, value: Any) -> Dict[str, Any]:
    """
    Append value to array at path.
    
    Args:
        cap_table: Cap table data structure
        path: JSON Pointer path to array
        value: Value to append
        
    Returns:
        Updated cap table
        
    Raises:
        ValueError: If path is not an array or duplicate name found
    """
    path = normalize_path(path)
    pointer = jsonpointer.JsonPointer(path)
    
    # Check for duplicate names in entity lists
    if path in ["/holders", "/classes", "/terms", "/rounds"] and isinstance(value, dict):
        name = value.get("name")
        if name:
            _check_duplicate_name(cap_table, path, name)
    
    try:
        target = pointer.resolve(cap_table)
    except jsonpointer.JsonPointerException:
        # Path doesn't exist, create it as array
        pointer.set(cap_table, [])
        target = pointer.resolve(cap_table)
    
    if not isinstance(target, list):
        raise ValueError(f"Path is not an array: {path}")
    
    target.append(value)
    return cap_table


def _check_duplicate_name(cap_table: Dict[str, Any], path: str, name: str) -> None:
    """
    Check if an entity with the given name already exists.
    
    Args:
        cap_table: Current cap table
        path: Path being appended to
        name: Name to check
        
    Raises:
        ValueError: If duplicate found
    """
    entity_type = path.replace("/", "")
    if entity_type not in ["holders", "classes", "terms", "rounds"]:
        return
    
    entities = cap_table.get(entity_type, [])
    
    for idx, entity in enumerate(entities):
        if isinstance(entity, dict) and entity.get("name") == name:
            # Duplicate found
            raise ValueError(f"{entity_type}[{idx}]: Duplicate name '{name}'. Entity already exists at index {idx}. To modify existing entity, use the 'replace' or 'upsert' operation instead of 'append'.")

