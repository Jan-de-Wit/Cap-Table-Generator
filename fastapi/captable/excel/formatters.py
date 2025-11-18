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
            - text: 11pt PT Sans for body text
            - italic_text: 11pt PT Sans Italic for italic text (e.g., descriptions)
            - header: 11pt PT Sans Bold, white text on blue background with border (table headers)
            - label: 11pt PT Sans Bold for labels (group names)
            - round_name: 11pt PT Sans Bold for round names
            - round_header: Century Gothic 14pt Bold with blue background for merged round headers
            - round_header_plain: Century Gothic 14pt Bold for plain round names (no background)
            - currency: Currency format with $ and commas, shows "-" when empty
            - percent: Percentage format, shows "-" when empty
            - number: Integer with thousands separator, shows "-" when empty
            - decimal: Decimal number with commas
            - date: Date format (YYYY-MM-DD)
            - empty: Shows "-" for empty cells
            - total_label: Bold text with top and bottom borders for total row label
            - total_number: Number format with top and bottom borders for total row
            - total_percent: Percent format with top and bottom borders for total row
            - total_currency: Currency format with top and bottom borders for total row
            - total_text: Text format with top and bottom borders for total row
            - param_text: Right-aligned text format for parameter values
            - table_currency: Left-aligned currency format for table cells
            - table_number: Left-aligned number format for table cells
            - table_date: Left-aligned date format for table cells
            - table_percent: Left-aligned percent format for table cells
        """
        return {
            'text': workbook.add_format({
                'font_name': 'PT Sans',
                'font_size': 11,
                'font_color': '#000000',
                'bg_color': '#FFFFFF'
            }),
            'italic_text': workbook.add_format({
                'font_name': 'PT Sans',
                'font_size': 11,
                'italic': True
            }),
            'header': workbook.add_format({
                'font_name': 'PT Sans',
                'font_size': 11,
                'bold': True,
                'font_color': '#000000',
                'bottom': 1,
                'bg_color': '#FFFFFF'
            }),
            'label': workbook.add_format({
                'font_name': 'PT Sans',
                'font_size': 11,
                'bold': True
            }),
            'round_name': workbook.add_format({
                'font_name': 'PT Sans',
                'font_size': 11,
                'bold': True
            }),
            'round_header': workbook.add_format({
                'font_name': 'Century Gothic',
                'font_size': 14,
                'bold': True,
            }),
            'round_header_plain': workbook.add_format({
                'font_name': 'Century Gothic',
                'font_size': 14,
                'bold': True
            }),
            'currency': workbook.add_format({
                'font_name': 'PT Sans',
                'font_size': 11,
                'font_color': '#000000',
                'num_format': '_($* #,##0.00_);_($* (#,##0.00);_($* "-"??_);_(@_)',
                'bg_color': '#FFFFFF',
                'align': 'right'
            }),
            'percent': workbook.add_format({
                'font_name': 'PT Sans',
                'font_size': 11,
                'font_color': '#000000',
                'num_format': '0.00%;-0.00%;"-"',
                'bg_color': '#FFFFFF',
                'align': 'right'
            }),
            'number': workbook.add_format({
                'font_name': 'PT Sans',
                'font_size': 11,
                'font_color': '#000000',
                'num_format': '#,##0;-###,##0;"-"',
                'bg_color': '#FFFFFF',
                'align': 'right'
            }),
            'decimal': workbook.add_format({
                'font_name': 'PT Sans',
                'font_size': 11,
                'font_color': '#000000',
                'num_format': '#,##0.00',
                'bg_color': '#FFFFFF',
                'align': 'right'
            }),
            'date': workbook.add_format({
                'font_name': 'PT Sans',
                'font_size': 11,
                'font_color': '#000000',
                'num_format': 'yyyy-mm-dd',
                'bg_color': '#FFFFFF',
                'align': 'right'
            }),
            'empty': workbook.add_format({
                'font_name': 'PT Sans',
                'font_size': 11,
                'font_color': '#000000',
                'num_format': '"-"'
            }),
            'total_label': workbook.add_format({
                'font_name': 'PT Sans',
                'font_size': 11,
                'bold': True,
                'font_color': '#000000',
                'top': 1,
                'bottom': 1,
                'bg_color': '#FFFFFF',
                'align': 'left'
            }),
            'total_number': workbook.add_format({
                'font_name': 'PT Sans',
                'font_size': 11,
                'font_color': '#000000',
                'num_format': '#,##0;-###,##0;"-"',
                'top': 1,
                'bottom': 1,
                'bg_color': '#FFFFFF',
                'align': 'left'
            }),
            'total_percent': workbook.add_format({
                'font_name': 'PT Sans',
                'font_size': 11,
                'font_color': '#000000',
                'num_format': '0.00%;-0.00%;"-"',
                'top': 1,
                'bottom': 1,
                'bg_color': '#FFFFFF',
                'align': 'left'
            }),
            'total_percent_small_italic': workbook.add_format({
                'font_name': 'PT Sans',
                'font_size': 9,
                'italic': True,
                'font_color': '#000000',
                'num_format': '0.00%;-0.00%;"-"',
                'top': 1,
                'bottom': 1,
                'bg_color': '#FFFFFF',
                'align': 'left'
            }),
            'total_currency': workbook.add_format({
                'font_name': 'PT Sans',
                'font_size': 11,
                'font_color': '#000000',
                'num_format': '_($* #,##0.00_);_($* (#,##0.00);_($* "-"??_);_(@_)',
                'top': 1,
                'bottom': 1,
                'bg_color': '#FFFFFF',
                'align': 'left'
            }),
            'total_text': workbook.add_format({
                'font_name': 'PT Sans',
                'font_size': 11,
                'font_color': '#000000',
                'top': 1,
                'bottom': 1,
                'bg_color': '#FFFFFF',
                'align': 'left'
            }),
            'param_text': workbook.add_format({
                'font_name': 'PT Sans',
                'font_size': 11,
                'font_color': '#000000',
                'bg_color': '#FFFFFF',
                'align': 'right'
            }),
            'table_currency': workbook.add_format({
                'font_name': 'PT Sans',
                'font_size': 11,
                'font_color': '#000000',
                'num_format': '_($* #,##0.00_);_($* (#,##0.00);_($* "-"??_);_(@_)',
                'bg_color': '#FFFFFF',
                'align': 'left'
            }),
            'table_number': workbook.add_format({
                'font_name': 'PT Sans',
                'font_size': 11,
                'font_color': '#000000',
                'num_format': '#,##0;-###,##0;"-"',
                'bg_color': '#FFFFFF',
                'align': 'left'
            }),
            'table_date': workbook.add_format({
                'font_name': 'PT Sans',
                'font_size': 11,
                'font_color': '#000000',
                'num_format': 'yyyy-mm-dd',
                'bg_color': '#FFFFFF',
                'align': 'left'
            }),
            'table_percent': workbook.add_format({
                'font_name': 'PT Sans',
                'font_size': 11,
                'font_color': '#000000',
                'num_format': '0.00%;-0.00%;"-"',
                'bg_color': '#FFFFFF',
                'align': 'left'
            }),
            'table_percent_small_italic': workbook.add_format({
                'font_name': 'PT Sans',
                'font_size': 9,
                'italic': True,
                'font_color': '#000000',
                'num_format': '0.00%;-0.00%;"-"',
                'bg_color': '#FFFFFF',
                'align': 'left'
            }),
            'white_bg': workbook.add_format({
                'bg_color': '#FFFFFF'
            }),
            'table_border': workbook.add_format({
                'top': 1,
                'bottom': 1,
                'left': 1,
                'right': 1
            }),
            'error': workbook.add_format({
                'font_name': 'PT Sans',
                'font_size': 11,
                'font_color': '#000000',
                'bg_color': '#FF0000',  # Red background
                'num_format': '0.00%;-0.00%;"-"',  # Percent format for pro rata %
                'align': 'left'
            }),
            'error_text': workbook.add_format({
                'font_name': 'PT Sans',
                'font_size': 11,
                'font_color': '#000000',
                'bg_color': '#FF0000',  # Red background
                'align': 'left'
            })
        }
