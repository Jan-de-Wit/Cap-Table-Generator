"""
Bulk Patch Operation

Implements the bulk patch operation for applying multiple JSON Patch operations at once.
"""

import jsonpatch
from typing import Dict, Any, List


def apply_bulk_patch(cap_table: Dict[str, Any], patch: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Apply multiple patch operations to the cap table.
    
    Args:
        cap_table: Cap table data structure
        patch: List of patch operations
        
    Returns:
        Updated cap table
        
    Raises:
        ValueError: If patch operations are invalid
    """
    try:
        # Use jsonpatch library for multiple operations
        patch_obj = jsonpatch.JsonPatch(patch)
        patched_data = patch_obj.apply(cap_table)
        return patched_data
    except jsonpatch.JsonPatchException as e:
        raise ValueError(f"Invalid patch operations: {str(e)}")

