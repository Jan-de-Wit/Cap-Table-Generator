"""
Excel Cell Formatting

Provides reusable cell formats for Excel workbooks.
All format definitions are centralized here for consistency.
"""

from typing import Dict
import xlsxwriter


class ExcelFormatters:
    """
    Factory for creating Excel cell formats.
    
    Provides a centralized location for all format definitions used
    throughout Excel generation, ensuring consistency across sheets.
    """
    
    @staticmethod
    def create_formats(workbook: xlsxwriter.Workbook) -> Dict[str, xlsxwriter.worksheet.Format]:
        """
        Create all standard cell formats for the workbook.
        
        Args:
            workbook: xlsxwriter Workbook instance
            
        Returns:
            Dictionary mapping format names to Format objects
            
        Available formats:
            - header: Bold white text on blue background with border
            - currency: Currency format with $ and commas, shows "-" when empty
            - percent: Percentage format, shows "-" when empty
            - number: Integer with thousands separator, shows "-" when empty
            - decimal: Decimal number with commas
            - date: Date format (YYYY-MM-DD)
            - label: Bold text for labels
            - empty: Shows "-" for empty cells
        """
        return {
            'header': workbook.add_format({
                'bold': True,
                'bg_color': '#4472C4',
                'font_color': 'white',
                'border': 1
            }),
            'currency': workbook.add_format({
                'num_format': '$#,##0.00;[Red]-$#,##0.00;"-"'
            }),
            'percent': workbook.add_format({
                'num_format': '0.00%;-0.00%;"-"'
            }),
            'number': workbook.add_format({
                'num_format': '#,##0;-###,##0;"-"'
            }),
            'decimal': workbook.add_format({
                'num_format': '#,##0.00'
            }),
            'date': workbook.add_format({
                'num_format': 'yyyy-mm-dd'
            }),
            'label': workbook.add_format({
                'bold': True
            }),
            'empty': workbook.add_format({
                'num_format': '"-"'
            })
        }

