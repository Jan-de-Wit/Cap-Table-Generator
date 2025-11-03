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
        """
        return {
            'text': workbook.add_format({
                'font_name': 'PT Sans',
                'font_size': 11
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
                'bottom': 1
            }),
            'label': workbook.add_format({
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
                'num_format': '$#,##0.00;[Red]-$#,##0.00;"-"'
            }),
            'percent': workbook.add_format({
                'font_name': 'PT Sans',
                'font_size': 11,
                'num_format': '0.00%;-0.00%;"-"'
            }),
            'number': workbook.add_format({
                'font_name': 'PT Sans',
                'font_size': 11,
                'num_format': '#,##0;-###,##0;"-"'
            }),
            'decimal': workbook.add_format({
                'font_name': 'PT Sans',
                'font_size': 11,
                'num_format': '#,##0.00'
            }),
            'date': workbook.add_format({
                'font_name': 'PT Sans',
                'font_size': 11,
                'num_format': 'yyyy-mm-dd'
            }),
            'empty': workbook.add_format({
                'font_name': 'PT Sans',
                'font_size': 11,
                'num_format': '"-"'
            }),
            'total_label': workbook.add_format({
                'font_name': 'PT Sans',
                'font_size': 11,
                'bold': True,
                'top': 1,
                'bottom': 1
            }),
            'total_number': workbook.add_format({
                'font_name': 'PT Sans',
                'font_size': 11,
                'num_format': '#,##0;-###,##0;"-"',
                'top': 1,
                'bottom': 1
            }),
            'total_percent': workbook.add_format({
                'font_name': 'PT Sans',
                'font_size': 11,
                'num_format': '0.00%;-0.00%;"-"',
                'top': 1,
                'bottom': 1
            }),
            'total_currency': workbook.add_format({
                'font_name': 'PT Sans',
                'font_size': 11,
                'num_format': '$#,##0.00;[Red]-$#,##0.00;"-"',
                'top': 1,
                'bottom': 1
            }),
            'total_text': workbook.add_format({
                'font_name': 'PT Sans',
                'font_size': 11,
                'top': 1,
                'bottom': 1
            }),
            'white_bg': workbook.add_format({
                'bg_color': '#FFFFFF'
            }),
            'table_border': workbook.add_format({
                'top': 1,
                'bottom': 1,
                'left': 1,
                'right': 1
            })
        }
