"""
String Utilities

String manipulation and sanitization functions.
"""

import re
from typing import Optional


def sanitize_name(name: str, replacement: str = "_") -> str:
    """
    Sanitize string for use as Excel named range or identifier.
    
    Args:
        name: String to sanitize
        replacement: Replacement character for invalid characters
        
    Returns:
        Sanitized string
    """
    if not name:
        return "Name"
    
    # Replace spaces, hyphens, and other invalid characters
    sanitized = re.sub(r'[^a-zA-Z0-9_.]', replacement, name)
    
    # Remove leading numbers (prepend underscore if starts with digit)
    if sanitized and sanitized[0].isdigit():
        sanitized = replacement + sanitized
    
    # Remove consecutive underscores
    sanitized = re.sub(r'_+', replacement, sanitized)
    
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    
    # Ensure it's not empty
    if not sanitized:
        sanitized = "Name"
    
    return sanitized


def truncate_string(s: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate string to maximum length.
    
    Args:
        s: String to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated string
    """
    if len(s) <= max_length:
        return s
    
    return s[:max_length - len(suffix)] + suffix


def normalize_whitespace(s: str) -> str:
    """
    Normalize whitespace in string.
    
    Args:
        s: String to normalize
        
    Returns:
        Normalized string
    """
    return " ".join(s.split())





