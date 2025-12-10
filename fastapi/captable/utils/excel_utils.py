"""
Excel Utilities

Excel-specific utility functions.
"""

from typing import Optional


def col_index_to_letter(col_idx: int) -> str:
    """
    Convert 0-based column index to Excel column letter(s).
    
    Args:
        col_idx: Zero-based column index
        
    Returns:
        Excel column letter (e.g., 'A', 'B', 'AA')
    
    Example:
        >>> col_index_to_letter(0)
        'A'
        >>> col_index_to_letter(25)
        'Z'
        >>> col_index_to_letter(26)
        'AA'
    """
    result = []
    col_idx += 1  # Convert to 1-based
    while col_idx > 0:
        col_idx -= 1
        result.append(chr(col_idx % 26 + ord('A')))
        col_idx //= 26
    return ''.join(reversed(result))


def letter_to_col_index(col_letter: str) -> int:
    """
    Convert Excel column letter(s) to 0-based column index.
    
    Args:
        col_letter: Excel column letter (e.g., 'A', 'B', 'AA')
        
    Returns:
        Zero-based column index
    
    Example:
        >>> letter_to_col_index('A')
        0
        >>> letter_to_col_index('Z')
        25
        >>> letter_to_col_index('AA')
        26
    """
    result = 0
    for char in col_letter:
        result = result * 26 + (ord(char) - ord('A') + 1)
    return result - 1  # Convert to 0-based


def get_cell_reference(
    row: int,
    col: int,
    sheet_name: Optional[str] = None,
    absolute: bool = True
) -> str:
    """
    Generate Excel cell reference.
    
    Args:
        row: Zero-based row index
        col: Zero-based column index
        sheet_name: Optional sheet name
        absolute: Use absolute reference ($A$1)
        
    Returns:
        Excel cell reference string
    """
    col_letter = col_index_to_letter(col)
    if absolute:
        address = f"${col_letter}${row + 1}"
    else:
        address = f"{col_letter}{row + 1}"
    
    if sheet_name:
        return f"{sheet_name}!{address}"
    return address




