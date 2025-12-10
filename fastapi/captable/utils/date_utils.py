"""
Date Utilities

Date formatting, parsing, and validation functions.
"""

from datetime import datetime, date
from typing import Optional


def format_date(d: Optional[date | datetime | str], format_str: str = "%Y-%m-%d") -> str:
    """
    Format date to string.
    
    Args:
        d: Date, datetime, or date string
        format_str: Format string
        
    Returns:
        Formatted date string
    """
    if d is None:
        return ""
    
    if isinstance(d, str):
        return d
    
    if isinstance(d, (date, datetime)):
        return d.strftime(format_str)
    
    return str(d)


def parse_date(date_str: Optional[str], format_str: str = "%Y-%m-%d") -> Optional[date]:
    """
    Parse date string to date object.
    
    Args:
        date_str: Date string
        format_str: Format string
        
    Returns:
        Date object or None if parsing fails
    """
    if not date_str:
        return None
    
    try:
        return datetime.strptime(date_str, format_str).date()
    except (ValueError, TypeError):
        return None


def validate_date_range(start_date: Optional[date | str], end_date: Optional[date | str]) -> bool:
    """
    Validate that start_date <= end_date.
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        True if valid, False otherwise
    """
    if not start_date or not end_date:
        return True
    
    start = parse_date(start_date) if isinstance(start_date, str) else start_date
    end = parse_date(end_date) if isinstance(end_date, str) else end_date
    
    if not start or not end:
        return True
    
    return start <= end




