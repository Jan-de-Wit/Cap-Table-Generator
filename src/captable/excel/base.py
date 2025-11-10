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

    def _sanitize_excel_name(self, name: str) -> str:
        """
        Sanitize a string for use as an Excel named range.
        
        Excel named range rules:
        - Can contain letters, numbers, underscores, and periods
        - Cannot contain spaces, hyphens, or other special characters
        - Cannot start with a number
        - Cannot be a cell reference (like A1, B2, etc.)
        
        Args:
            name: String to sanitize (e.g., round name)
            
        Returns:
            Sanitized string safe for Excel named ranges
        """
        import re
        # Replace spaces, hyphens, and other invalid characters with underscores
        sanitized = re.sub(r'[^a-zA-Z0-9_.]', '_', name)
        # Remove leading numbers (prepend underscore if starts with digit)
        if sanitized and sanitized[0].isdigit():
            sanitized = '_' + sanitized
        # Remove consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        # Ensure it's not empty
        if not sanitized:
            sanitized = 'Name'
        return sanitized

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

    def set_row_heights(
        self,
        heights: List[tuple]
    ):
        """
        Set row heights for this sheet.

        Args:
            heights: List of tuples (row, height)
                   Example: [(0, 20), (1, 15)]
        """
        if not self.sheet:
            return

        for row, height in heights:
            self.sheet.set_row(row, height)

    def setup_table_formatting(
        self,
        sheet: xlsxwriter.worksheet.Worksheet,
        border_start_row: int,
        border_start_col: int,
        border_end_row: int,
        border_end_col: int,
        padding_offset: int = 1,
        row_heights: Optional[List[tuple]] = None,
        column_widths: Optional[List[tuple]] = None
    ):
        """
        Set up complete table formatting with padding, borders, and styling.
        
        This utility function handles all the common table formatting steps:
        - Adds padding cells with white background
        - Applies white background to entire table range
        - Applies borders to table edges
        - Sets row heights (if provided)
        - Sets column widths (if provided)
        
        Args:
            sheet: Worksheet to format
            border_start_row: Starting row for border (0-based)
            border_start_col: Starting column for border (0-based)
            border_end_row: Ending row for border (0-based)
            border_end_col: Ending column for border (0-based)
            padding_offset: Padding offset value (default: 1)
            row_heights: Optional list of tuples (row, height) for row heights
            column_widths: Optional list of tuples (start_col, end_col, width) for column widths
        """
        # Add padding cells with white background inside the border
        self._add_padding_cells(sheet, border_start_row, border_start_col, border_end_row, border_end_col)
        
        # Apply white background to all cells in the table
        self._apply_white_background(sheet, border_start_row, border_start_col, border_end_row, border_end_col)
        
        # Apply borders to entire table (including padding area)
        self._apply_table_borders(sheet, border_start_row, border_start_col, border_end_row, border_end_col)
        
        # Set row heights if provided
        if row_heights:
            for row, height in row_heights:
                sheet.set_row(row, height)
        
        # Set column widths if provided
        if column_widths:
            for start_col, end_col, width in column_widths:
                sheet.set_column(start_col, end_col, width)

    def _add_padding_cells(
        self,
        sheet: xlsxwriter.worksheet.Worksheet,
        border_start_row: int,
        border_start_col: int,
        border_end_row: int,
        border_end_col: int
    ):
        """Add padding cells with white background inside the border."""
        white_bg_format = self.formats.get('white_bg')
        
        # Fill top padding row (inside border, below top border)
        for col in range(border_start_col, border_end_col + 1):
            sheet.write(border_start_row, col, '', white_bg_format)
        
        # Fill bottom padding row (inside border, above bottom border)
        for col in range(border_start_col, border_end_col + 1):
            sheet.write(border_end_row, col, '', white_bg_format)
        
        # Fill left padding column (inside border, to the right of left border)
        for row in range(border_start_row + 1, border_end_row):
            sheet.write(row, border_start_col, '', white_bg_format)
        
        # Fill right padding column (inside border, to the left of right border)
        for row in range(border_start_row + 1, border_end_row):
            sheet.write(row, border_end_col, '', white_bg_format)

    def _apply_white_background(
        self,
        sheet: xlsxwriter.worksheet.Worksheet,
        start_row: int,
        start_col: int,
        end_row: int,
        end_col: int
    ):
        """Apply white background to all cells in the table range."""
        white_bg_format = self.formats.get('white_bg')
        # Apply white background to entire table range using conditional formatting
        sheet.conditional_format(
            start_row, start_col, end_row, end_col,
            {'type': 'formula', 'criteria': 'TRUE', 'format': white_bg_format}
        )

    def _apply_table_borders(
        self,
        sheet: xlsxwriter.worksheet.Worksheet,
        start_row: int,
        start_col: int,
        end_row: int,
        end_col: int
    ):
        """Apply borders to the entire table range using conditional formatting."""
        # Apply borders to all edge cells, ensuring corners get both borders
        
        # Top row: all cells get top border, corners also get left/right
        for col in range(start_col, end_col + 1):
            border_props = {'top': 1}
            if col == start_col:
                border_props['left'] = 1
            if col == end_col:
                border_props['right'] = 1
            top_border_format = self.workbook.add_format(border_props)
            sheet.conditional_format(
                start_row, col, start_row, col,
                {'type': 'formula', 'criteria': 'TRUE', 'format': top_border_format}
            )
        
        # Bottom row: all cells get bottom border, corners also get left/right
        for col in range(start_col, end_col + 1):
            border_props = {'bottom': 1}
            if col == start_col:
                border_props['left'] = 1
            if col == end_col:
                border_props['right'] = 1
            bottom_border_format = self.workbook.add_format(border_props)
            sheet.conditional_format(
                end_row, col, end_row, col,
                {'type': 'formula', 'criteria': 'TRUE', 'format': bottom_border_format}
            )
        
        # Left column: all cells get left border (corners already handled above)
        for row in range(start_row + 1, end_row):
            left_border_format = self.workbook.add_format({'left': 1})
            sheet.conditional_format(
                row, start_col, row, start_col,
                {'type': 'formula', 'criteria': 'TRUE', 'format': left_border_format}
            )
        
        # Right column: all cells get right border (corners already handled above)
        for row in range(start_row + 1, end_row):
            right_border_format = self.workbook.add_format({'right': 1})
            sheet.conditional_format(
                row, end_col, row, end_col,
                {'type': 'formula', 'criteria': 'TRUE', 'format': right_border_format}
            )

    def write_round_headers(
        self,
        sheet: xlsxwriter.worksheet.Worksheet,
        rounds: List[Dict[str, Any]],
        header_row: int,
        start_col: int,
        columns_per_round: int,
        separator_width: int = 1,
        round_name_format: Optional[xlsxwriter.worksheet.Format] = None,
        subheader_row: Optional[int] = None,
        subheaders: Optional[List[str]] = None
    ) -> int:
        """
        Write round headers across multiple columns.
        
        This utility function helps write round headers in a consistent way:
        - Writes merged round name headers (one per round)
        - Optionally writes subheaders for each round's columns
        - Handles separators between rounds
        
        Args:
            sheet: Worksheet to write to
            rounds: List of round dictionaries
            header_row: Row to write round names (0-based)
            start_col: Starting column for first round (0-based)
            columns_per_round: Number of data columns per round (excluding separator)
            separator_width: Width of separator column between rounds (default: 1)
            round_name_format: Format for round name headers (defaults to round_header)
            subheader_row: Optional row to write subheaders (0-based)
            subheaders: Optional list of subheader names (one per column_per_round)
            
        Returns:
            Column index after the last round's data (before final separator, if any)
        """
        if round_name_format is None:
            round_name_format = self.formats.get('round_header')
        
        col = start_col
        
        for round_idx, round_data in enumerate(rounds):
            round_name = round_data.get('name', f'Round {round_idx + 1}')
            is_last_round = (round_idx == len(rounds) - 1)
            
            # Write merged round name header
            if is_last_round:
                # Last round: no separator after, so merge all columns
                end_col = col + columns_per_round - 1
            else:
                # Not last round: merge up to but not including separator
                end_col = col + columns_per_round - 1
            
            sheet.merge_range(
                header_row, col,
                header_row, end_col,
                round_name,
                round_name_format
            )
            
            # Write subheaders if provided
            if subheader_row is not None and subheaders:
                subheader_format = self.formats.get('header')
                for subheader_idx, subheader in enumerate(subheaders):
                    if subheader_idx < columns_per_round:
                        sheet.write(
                            subheader_row,
                            col + subheader_idx,
                            subheader,
                            subheader_format
                        )
            
            # Move to next round's start column
            col += columns_per_round
            if not is_last_round:
                col += separator_width
        
        return col

    def calculate_round_column_position(
        self,
        round_idx: int,
        start_col: int,
        columns_per_round: int,
        separator_width: int = 1
    ) -> int:
        """
        Calculate the starting column position for a specific round.
        
        Args:
            round_idx: Zero-based index of the round
            start_col: Starting column for the first round
            columns_per_round: Number of data columns per round
            separator_width: Width of separator column between rounds (default: 1)
            
        Returns:
            Starting column index for the specified round
        """
        # Each round takes up columns_per_round columns
        # Each separator (except after last round) takes separator_width columns
        return start_col + (round_idx * (columns_per_round + separator_width))

    def get_round_section_range(
        self,
        round_idx: int,
        start_row: int,
        end_row: int,
        start_col: int,
        columns_per_round: int,
        separator_width: int = 1
    ) -> tuple:
        """
        Get the Excel range for a round's data section.
        
        Args:
            round_idx: Zero-based index of the round
            start_row: Starting row (0-based)
            end_row: Ending row (0-based, inclusive)
            start_col: Starting column for the first round
            columns_per_round: Number of data columns per round
            separator_width: Width of separator column between rounds (default: 1)
            
        Returns:
            Tuple of (start_col_letter, end_col_letter, start_row_1based, end_row_1based)
            for constructing Excel range references
        """
        round_start_col = self.calculate_round_column_position(
            round_idx, start_col, columns_per_round, separator_width
        )
        round_end_col = round_start_col + columns_per_round - 1
        
        start_col_letter = self._col_letter(round_start_col)
        end_col_letter = self._col_letter(round_end_col)
        
        return (start_col_letter, end_col_letter, start_row + 1, end_row + 1)
