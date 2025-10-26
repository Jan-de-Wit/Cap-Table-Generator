"""
Base Sheet Generator

Provides common utilities and base class for all sheet generators.
Contains shared functionality used across different sheet types.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import xlsxwriter


class ExcelFormatDict(Dict[str, xlsxwriter.worksheet.Format]):
    """Type alias for Excel format dictionaries."""
    pass


class BaseSheetGenerator(ABC):
    """
    Abstract base class for Excel sheet generators.
    
    Provides common functionality for creating Excel sheets with formatting,
    tables, and formulas. Each sheet type should subclass this and implement
    the generate() method.
    
    Attributes:
        workbook: xlsxwriter Workbook instance
        data: Cap table JSON data
        formats: Dictionary of cell formats
        dlm: Deterministic layout map for reference management
        formula_resolver: Formula resolver for creating Excel formulas
    """
    
    def __init__(
        self,
        workbook: xlsxwriter.Workbook,
        data: Dict[str, Any],
        formats: ExcelFormatDict,
        dlm: Any,
        formula_resolver: Any
    ):
        """
        Initialize base sheet generator.
        
        Args:
            workbook: Excel workbook instance
            data: Cap table JSON data
            formats: Dictionary of cell format objects
            dlm: Deterministic layout map instance
            formula_resolver: Formula resolver instance
        """
        self.workbook = workbook
        self.data = data
        self.formats = formats
        self.dlm = dlm
        self.formula_resolver = formula_resolver
        self.sheet = None
        self.sheet_name = self._get_sheet_name()
    
    @abstractmethod
    def _get_sheet_name(self) -> str:
        """
        Get the name of this sheet.
        
        Returns:
            Sheet name string
        """
        pass
    
    @abstractmethod
    def generate(self) -> xlsxwriter.worksheet.Worksheet:
        """
        Generate this sheet.
        
        Returns:
            Created worksheet instance
        """
        pass
    
    def _col_letter(self, col_idx: int) -> str:
        """
        Convert 0-based column index to Excel column letter(s).
        
        Args:
            col_idx: Zero-based column index
            
        Returns:
            Excel column letter (e.g., 'A', 'B', 'AA')
            
        Example:
            >>> self._col_letter(0)
            'A'
            >>> self._col_letter(25)
            'Z'
            >>> self._col_letter(26)
            'AA'
        """
        result = []
        col_idx += 1  # Convert to 1-based
        while col_idx > 0:
            col_idx -= 1
            result.append(chr(col_idx % 26 + ord('A')))
            col_idx //= 26
        return ''.join(reversed(result))
    
    def _get_cell_reference(
        self,
        row: int,
        col: int,
        sheet_name: Optional[str] = None,
        absolute: bool = True
    ) -> str:
        """
        Generate a cell reference string.
        
        Args:
            row: Zero-based row index
            col: Zero-based column index
            sheet_name: Optional sheet name for cross-sheet references
            absolute: Use absolute reference ($A$1) vs relative (A1)
            
        Returns:
            Excel cell reference string (e.g., 'Sheet1!$A$1' or 'A1')
        """
        col_letter = self._col_letter(col)
        if absolute:
            address = f"${col_letter}${row + 1}"
        else:
            address = f"{col_letter}{row + 1}"
        
        if sheet_name:
            return f"{sheet_name}!{address}"
        return address
    
    def set_column_widths(
        self,
        widths: List[tuple]
    ):
        """
        Set column widths for this sheet.
        
        Args:
            widths: List of tuples (start_col, end_col, width)
                   Example: [(0, 0, 20), (1, 1, 15)]
        """
        if not self.sheet:
            return
        
        for start_col, end_col, width in widths:
            self.sheet.set_column(start_col, end_col, width)

