"""
Number Utilities

Number formatting and validation functions.
"""

from typing import Optional


def format_currency(value: Optional[float], decimals: int = 2) -> str:
    """
    Format number as currency.
    
    Args:
        value: Number to format
        decimals: Number of decimal places
        
    Returns:
        Formatted currency string
    """
    if value is None:
        return "-"
    
    return f"${value:,.{decimals}f}"


def format_percentage(value: Optional[float], decimals: int = 2) -> str:
    """
    Format number as percentage.
    
    Args:
        value: Number to format (0-1 range)
        decimals: Number of decimal places
        
    Returns:
        Formatted percentage string
    """
    if value is None:
        return "-"
    
    return f"{value * 100:.{decimals}f}%"


def format_number(value: Optional[float], decimals: int = 0) -> str:
    """
    Format number with thousands separator.
    
    Args:
        value: Number to format
        decimals: Number of decimal places
        
    Returns:
        Formatted number string
    """
    if value is None:
        return "-"
    
    if decimals == 0:
        return f"{int(value):,}"
    else:
        return f"{value:,.{decimals}f}"


def validate_percentage(value: Optional[float], min_val: float = 0.0, max_val: float = 1.0) -> bool:
    """
    Validate percentage value.
    
    Args:
        value: Percentage value (0-1 range)
        min_val: Minimum value
        max_val: Maximum value
        
    Returns:
        True if valid, False otherwise
    """
    if value is None:
        return True
    
    return min_val <= value <= max_val


def validate_positive(value: Optional[float]) -> bool:
    """
    Validate that value is positive.
    
    Args:
        value: Value to validate
        
    Returns:
        True if positive or None, False otherwise
    """
    if value is None:
        return True
    
    return value > 0

