"""
Excel Table Builder

Utilities for creating Excel Tables with data, formulas, and validation.
"""

from typing import Dict, List, Any
import xlsxwriter


class TableBuilder:
    """
    Helper class for building Excel Tables.
    
    Provides utilities for creating structured Excel tables with
    consistent formatting, formulas, and validation rules.
    """
    
    @staticmethod
    def create_table(
        sheet: xlsxwriter.worksheet.Worksheet,
        table_name: str,
        start_row: int,
        start_col: int,
        columns: List[str],
        data: List[Dict[str, Any]],
        formulas: Dict[str, str],
        formats: Dict[str, xlsxwriter.worksheet.Format]
    ):
        """
        Create an Excel Table with data and formulas.
        
        Args:
            sheet: Worksheet to add table to
            table_name: Name for the Excel Table
            start_row: Starting row (0-based)
            start_col: Starting column (0-based)
            columns: List of column header names
            data: List of row data dictionaries
            formulas: Dict of column_name -> formula template
            formats: Dictionary of cell formats
            
        Raises:
            ValueError: If data is empty or invalid
        """
        if not data:
            # Create an empty table structure (with just headers) so it can be referenced
            # Create a table with one empty row so the structure exists
            empty_row = [[''] * len(columns)]
            end_row = start_row + 1  # Header row + 1 empty data row
            end_col = start_col + len(columns) - 1
            
            # Create column definitions
            col_defs = [{'header': col_name} for col_name in columns]
            
            # Write table
            sheet.add_table(
                start_row, 
                start_col, 
                end_row, 
                end_col,
                {
                    'name': table_name,
                    'data': empty_row,
                    'columns': col_defs,
                    'style': 'Table Style Medium 2'
                }
            )
            return
        
        # Prepare table data for xlsxwriter
        table_rows = []
        for row_data in data:
            table_row = []
            for col_name in columns:
                value = row_data.get(col_name, '')
                table_row.append(value)
            table_rows.append(table_row)
        
        # Define table range
        end_row = start_row + len(data)  # +1 for header is implicit
        end_col = start_col + len(columns) - 1
        
        # Create column definitions with formulas
        col_defs = []
        for col_name in columns:
            col_def = {'header': col_name}
            if col_name in formulas:
                col_def['formula'] = formulas[col_name]
            col_defs.append(col_def)
        
        # Write table
        sheet.add_table(
            start_row, 
            start_col, 
            end_row, 
            end_col,
            {
                'name': table_name,
                'data': table_rows,
                'columns': col_defs,
                'style': 'Table Style Medium 2'
            }
        )
    
    @staticmethod
    def add_data_validation(
        sheet: xlsxwriter.worksheet.Worksheet,
        first_row: int,
        last_row: int,
        col: int,
        validation_config: Dict[str, Any]
    ):
        """
        Add data validation to a column range.
        
        Args:
            sheet: Worksheet to add validation to
            first_row: First data row (0-based)
            last_row: Last data row (0-based)
            col: Column index (0-based)
            validation_config: xlsxwriter data validation configuration
        
        Example:
            >>> builder.add_data_validation(
            ...     sheet, 1, 10, 0, {
            ...         'validate': 'list',
            ...         'source': '=MasterTable[column_name]'
            ...     }
            ... )
        """
        sheet.data_validation(
            first_row,
            col,
            last_row,
            col,
            validation_config
        )

