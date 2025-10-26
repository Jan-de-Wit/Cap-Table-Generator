"""
Operation Utilities

Shared utility functions for all operation modules.
"""

def normalize_path(path: str) -> str:
    """
    Normalize path to JSON Pointer format.
    
    Args:
        path: Input path (supports both JSON Pointer and dot notation)
        
    Returns:
        Normalized JSON Pointer path
    """
    if not path:
        return ""
    if not path.startswith("/"):
        # Convert dot notation to JSON Pointer
        path = "/" + path.replace(".", "/")
    return path

