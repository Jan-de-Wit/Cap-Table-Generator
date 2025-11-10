"""
Rounds Sheet Generator

Creates the Rounds sheet which is the SOURCE OF TRUTH in round-based architecture.
Each round is displayed vertically with its constants and nested instruments.
All calculations are formula-driven and fully traceable.
"""

from typing import Dict, List, Any, Optional
import xlsxwriter
from ..base import BaseSheetGenerator
from ...formulas import valuation, ownership, interest
from datetime import datetime


class RoundsSheetGenerator(BaseSheetGenerator):
    """
    Generates the Rounds sheet showing all rounds with nested instruments.

    Structure:
    - Each round displayed vertically
    - Round heading + constants section
    - Instruments table (columns vary by calculation_type)
    - Pro rata calculations when specified
    """

    def __init__(self, workbook, data, formats, dlm, formula_resolver):
        """Initialize rounds sheet generator."""
        super().__init__(workbook, data, formats, dlm, formula_resolver)
        self.round_ranges = {}  # For progression sheet reference
        # Track rows where constants are written: {round_idx: {constant_name: row}}
        self.round_constants_rows = {}
        # Padding offset for table positioning
        self.padding_offset = 1

    def _get_sheet_name(self) -> str:
        """Returns 'Rounds'."""
        return "Rounds"

    def generate(self) -> xlsxwriter.worksheet.Worksheet:
        """Generate the Rounds sheet."""
        sheet = self.workbook.add_worksheet('Rounds')
        self.sheet = sheet

        rounds = self.data.get('rounds', [])
        if not rounds:
            sheet.write(self.padding_offset + 1, self.padding_offset +
                        1, 'No rounds found', self.formats.get('text'))
            return sheet

        # Calculate border bounds
        border_start_row = self.padding_offset  # Row 1 (0-indexed)
        border_start_col = self.padding_offset  # Column 1 (0-indexed)

        # Content starts after padding + title + 2 spacing rows
        # Row 0: outer padding
        # Row 1: inner padding (border start)
        # Row 2: title
        # Row 3-4: spacing (2 rows)
        # Row 5+: content
        content_start_row = self.padding_offset + \
            1 + 3  # After padding + title + 2 spacing rows

        # Write title "Input for Cap-Table" at row after padding (row 2)
        title_row = self.padding_offset + 1
        sheet.write(title_row, self.padding_offset + 1,
                    'Input for Cap-Table', self.formats.get('round_header_plain'))

        # Add 2 spacing rows after title (rows 3 and 4)
        # No need to explicitly write empty rows - they'll be empty by default

        # Track current row as we build vertically (start after title + 2 spacing rows)
        current_row = content_start_row

        # Write rounds vertically
        for round_idx, round_data in enumerate(rounds):
            current_row = self._write_round(
                sheet, round_idx, round_data, rounds, current_row
            )
            # Add 2 spacing rows between rounds - but not after last round
            if round_idx < len(rounds) - 1:
                current_row += 2

        # Calculate border end row and column
        # Need to determine max column used across all rounds
        max_col = self._calculate_max_column(rounds)
        # Tables start at parameters column (padding_offset + 2), max content column is (padding_offset + 2) + max_col
        # Border end column includes padding after content: (padding_offset + 2) + max_col + padding_offset
        border_end_col = (self.padding_offset + 2) + \
            max_col + self.padding_offset
        border_end_row = current_row + self.padding_offset  # Add padding space

        # Set up table formatting using utility function
        row_heights = [
            (0, 16.0),  # Outer padding row
            (border_start_row, 16.0),  # Inner padding row (top border row)
            (title_row, 25),  # Title row
        ]

        column_widths = [
            (0, 0, 4.0),  # Outer padding column
            # Inner padding column (left border column)
            (border_start_col, border_start_col, 4.0),
            # Label column
            (self.padding_offset + 1, self.padding_offset + 1, 45),
            # Parameters column (same width as label column)
            (self.padding_offset + 2, self.padding_offset + 2, 45),
            # Table columns (tables start at padding_offset + 2, column 3)
            # Value column is padding_offset + 3 (column 4), but table starts at column 3
            (self.padding_offset + 3, max_col + self.padding_offset + 3, 25),
        ]

        self.setup_table_formatting(
            sheet,
            border_start_row,
            border_start_col,
            border_end_row,
            border_end_col,
            padding_offset=self.padding_offset,
            row_heights=row_heights,
            column_widths=column_widths
        )

        return sheet

    def _calculate_max_column(self, rounds: List[Dict[str, Any]]) -> int:
        """Calculate the maximum column index used across all rounds."""
        max_col = 0
        for round_data in rounds:
            calc_type = round_data.get('calculation_type', 'fixed_shares')
            if calc_type == 'fixed_shares':
                # Holder Name, Class Name, Acquisition Date, Shares = 4 columns
                max_col = max(max_col, 3)
            elif calc_type == 'target_percentage':
                # Holder Name, Class Name, Target %, Calculated Shares = 4 columns
                max_col = max(max_col, 3)
            elif calc_type == 'valuation_based':
                # Holder Name, Class Name, Investment Amount, Calculated Shares = 4 columns
                max_col = max(max_col, 3)
            elif calc_type == 'convertible':
                # 11 columns total
                max_col = max(max_col, 10)
            else:
                # Holder Name, Class Name, Shares = 3 columns
                max_col = max(max_col, 2)
        return max_col

    def _write_round(
        self,
        sheet: xlsxwriter.worksheet.Worksheet,
        round_idx: int,
        round_data: Dict[str, Any],
        all_rounds: List[Dict[str, Any]],
        start_row: int
    ) -> int:
        """Write a single round and return next row."""
        current_row = start_row
        round_name = round_data.get('name', f'Round {round_idx + 1}')
        calc_type = round_data.get('calculation_type', 'fixed_shares')

        # Write round heading (shifted by padding offset + 1)
        # First parameter will be written on the same row to the right
        round_name_row = current_row
        sheet.write(current_row, self.padding_offset + 1,
                    round_name, self.formats.get('round_name'))

        # Write constants section (first parameter on same row as round name, rest below)
        constants_row = current_row
        current_row = self._write_round_constants(
            sheet, round_idx, round_data, all_rounds, current_row, round_name_row
        )

        # Add dropdown validation for valuation basis fields
        if calc_type == 'valuation_based':
            valuation_basis_row = self._find_constant_row(
                round_idx, 'Valuation Basis:')
            if valuation_basis_row is not None:
                col_value = self.padding_offset + 3  # Values column (column 4)
                sheet.data_validation(
                    valuation_basis_row, col_value,
                    valuation_basis_row, col_value,
                    {
                        'validate': 'list',
                        'source': ['pre_money', 'post_money'],
                        'error_type': 'stop',
                        'error_title': 'Invalid Valuation Basis',
                        'error_message': 'Please select either "pre_money" or "post_money" from the dropdown.'
                    }
                )
        elif calc_type == 'convertible':
            valuation_cap_basis_row = self._find_constant_row(
                round_idx, 'Valuation Cap Basis:')
            if valuation_cap_basis_row is not None:
                col_value = self.padding_offset + 3  # Values column (column 4)
                sheet.data_validation(
                    valuation_cap_basis_row, col_value,
                    valuation_cap_basis_row, col_value,
                    {
                        'validate': 'list',
                        'source': ['pre_money', 'post_money', 'fixed'],
                        'error_type': 'stop',
                        'error_title': 'Invalid Valuation Cap Basis',
                        'error_message': 'Please select "pre_money", "post_money", or "fixed" from the dropdown.'
                    }
                )

        # Add spacing row before instruments table
        current_row += 1

        # Write instruments table
        instruments_start_row = current_row
        instruments = round_data.get('instruments', [])

        # Filter out pro rata allocations (they go in Pro Rata Allocations sheet, not Rounds sheet)
        regular_instruments = [
            inst for inst in instruments
            if not self._is_pro_rata_allocation(inst)
        ]

        if regular_instruments:
            current_row = self._write_instruments_table(
                sheet, round_idx, round_data, regular_instruments, all_rounds, current_row
            )
        else:
            # No instruments - just write placeholder (shifted by padding offset + 1)
            sheet.write(current_row, self.padding_offset + 1, 'No instruments',
                        self.formats.get('text'))
            current_row += 1

        # Register round section with DLM
        self.dlm.register_round_section(
            round_name, 'Rounds', constants_row, instruments_start_row
        )

        # Store round range info for progression sheet
        instruments_end_row = current_row - \
            1 if regular_instruments else instruments_start_row
        # Include table metadata if a table was created
        table_name = self._get_round_table_name(round_idx, round_data)
        # Start at parameters column (column 3)
        table_start_col = self.padding_offset + 2
        # Calculate holder column (first column of table) and shares column (accounting for table_start_col)
        # Holder name is first column of instruments table
        holder_col_idx = table_start_col
        shares_col_idx = table_start_col + \
            self._get_shares_column_index(calc_type)
        self.round_ranges[round_idx] = {
            # +1 for header, +1 for Breakdown label
            'start_row': instruments_start_row + 2,
            'end_row': instruments_end_row + 1,
            # Column letter for holder name
            'holder_col': self._col_letter(holder_col_idx),
            # Column letter for shares
            'shares_col': self._col_letter(shares_col_idx),
            'table_name': table_name,
            'calc_type': calc_type
        }

        return current_row

    def _is_pro_rata_allocation(self, instrument: Dict[str, Any]) -> bool:
        """
        Check if an instrument is a pro rata allocation.

        A pro rata allocation has only holder_name, class_name, and pro_rata_type.
        It may optionally have pro_rata_percentage.

        Args:
            instrument: Instrument dictionary

        Returns:
            True if this is a pro rata allocation, False otherwise
        """
        # Pro rata allocations have pro_rata_type and only basic fields
        if "pro_rata_type" not in instrument:
            return False

        # Check that it only has the allowed fields for pro rata allocations
        allowed_fields = {"holder_name", "class_name",
                          "pro_rata_type", "pro_rata_percentage"}
        instrument_fields = set(instrument.keys())

        # If the instrument has any fields beyond the allowed ones, it's not just a pro rata allocation
        if instrument_fields - allowed_fields:
            return False

        return True

    def _write_round_constants(
        self,
        sheet: xlsxwriter.worksheet.Worksheet,
        round_idx: int,
        round_data: Dict[str, Any],
        all_rounds: List[Dict[str, Any]],
        start_row: int,
        round_name_row: int
    ) -> int:
        """Write round constants and return next row.

        First parameter is written on the same row as round name (to the right).
        Subsequent parameters are written below, each on their own row.
        """
        calc_type = round_data.get('calculation_type', 'fixed_shares')

        # Initialize constants tracking for this round
        self.round_constants_rows[round_idx] = {}

        # Round name in column 2 (padding_offset + 1)
        # Parameters: labels and values in column 3 (padding_offset + 2)
        col_label = self.padding_offset + 1  # For round name
        col_param = self.padding_offset + 2  # For parameter labels and values

        # Collect all constants to write
        constants_to_write = []

        # Round Date
        round_date = round_data.get('round_date', '')
        constants_to_write.append(('Round Date:', round_date, 'date', None))

        # Pre-Round Shares (removed from visible parameters; sourced from Progression sheet)

        # Valuation fields (for valuation_based and convertible)
        if calc_type in ['valuation_based', 'convertible']:
            if calc_type == 'valuation_based':
                valuation_basis = round_data.get(
                    'valuation_basis', 'pre_money')
                constants_to_write.append(
                    ('Valuation Basis:', valuation_basis, 'param_text', 'Valuation Basis:'))

            if calc_type == 'convertible':
                valuation_cap_basis = round_data.get(
                    'valuation_cap_basis', 'pre_money')
                constants_to_write.append(
                    ('Valuation Cap Basis:', valuation_cap_basis, 'param_text', 'Valuation Cap Basis:'))

            # Pre/Post-Money Valuation (always include, infer if missing)
            pre_money_val = round_data.get('pre_money_valuation')
            post_money_val = round_data.get('post_money_valuation')
            constants_to_write.append(
                ('Pre-Money Valuation:', pre_money_val, 'currency', 'Pre-Money Valuation:'))
            constants_to_write.append(
                ('Post-Money Valuation:', post_money_val, 'currency', 'Post-Money Valuation:'))

            # Price Per Share
            if 'price_per_share' in round_data or calc_type == 'convertible':
                pps = round_data.get('price_per_share')
                constants_to_write.append(
                    ('Price Per Share:', pps, 'currency', 'Price Per Share:'))

        # Write first constant on the same row as round name (to the right)
        if constants_to_write:
            first_label, first_value, first_format_type, first_track_key = constants_to_write[
                0]

            # Write first parameter label and value on round name row (to the right in column 3)
            sheet.write(round_name_row, col_param, first_label,
                        self.formats.get('text'))

            if first_track_key:
                self.round_constants_rows[round_idx][first_track_key] = round_name_row

            # Write the value (next to label in column 3, but we'll use column 4 for values)
            # Actually, let's put label and value both in column 3, or label in 3 and value in 4?
            # Based on user request, parameters column should be same width as label column
            # So I think: label in column 3, value also in column 3 (or we merge?)
            # Let me put value in column 4 for now, but we can adjust
            col_value = self.padding_offset + 3  # Values in column 4

            # Regular value (no formula objects supported)
            sheet.write(round_name_row, col_value, first_value or '',
                        self.formats.get(first_format_type))

            current_row = round_name_row + 1
        else:
            current_row = round_name_row + 1

        # Write remaining constants below, each on their own row
        # Labels in column 3 (col_param), values in column 4 (col_value)
        for label, value, format_type, track_key in constants_to_write[1:]:
            sheet.write(current_row, col_param, label,
                        self.formats.get('text'))

            if track_key:
                self.round_constants_rows[round_idx][track_key] = current_row

            # Write the value
            if label == 'Price Per Share:':
                # Special handling for Price Per Share
                pps = round_data.get('price_per_share')

                if calc_type == 'convertible':
                    valuation_cap_basis = round_data.get(
                        'valuation_cap_basis', 'pre_money')
                    pre_round_shares_ref = self._get_pre_round_shares_ref(
                        round_idx, round_data, all_rounds)

                    valuation_cap_basis_row = self._find_constant_row(
                        round_idx, 'Valuation Cap Basis:')
                    col_value_ref = self.padding_offset + \
                        3  # Values column (column 4)
                    col_letter = self._col_letter(col_value_ref)
                    valuation_cap_basis_ref = f"{col_letter}{valuation_cap_basis_row + 1}" if valuation_cap_basis_row is not None else None

                    pre_row = self._find_constant_row(round_idx, 'Pre-Money Valuation:')
                    post_row = self._find_constant_row(round_idx, 'Post-Money Valuation:')
                    pre_money_ref = f"{col_letter}{pre_row + 1}" if pre_row is not None else None
                    post_money_ref = f"{col_letter}{post_row + 1}" if post_row is not None else None

                    if valuation_cap_basis_ref:
                        inv_total = self._get_round_investment_total_ref(round_idx, round_data)
                        if pre_money_ref is None and post_money_ref is not None:
                            pre_ref_safe = f"({post_money_ref} - {inv_total})"
                        else:
                            pre_ref_safe = pre_money_ref or "0"
                        if post_money_ref is None and pre_money_ref is not None:
                            post_ref_safe = f"({pre_money_ref} + {inv_total})"
                        else:
                            post_ref_safe = post_money_ref or "0"
                        pre_money_pps_formula = valuation.create_price_per_share_from_valuation_formula(
                            pre_ref_safe, pre_round_shares_ref
                        )
                        post_money_pps_formula = valuation.create_price_per_share_from_valuation_formula(
                            post_ref_safe, pre_round_shares_ref
                        )
                        pre_money_pps_formula_no_eq = pre_money_pps_formula.lstrip(
                            '=')
                        post_money_pps_formula_no_eq = post_money_pps_formula.lstrip(
                            '=')
                        fixed_initial_value = pps if pps else 0
                        pps_formula = f"=IF({valuation_cap_basis_ref}=\"fixed\", {fixed_initial_value}, IF({valuation_cap_basis_ref}=\"pre_money\", {pre_money_pps_formula_no_eq}, {post_money_pps_formula_no_eq}))"
                        sheet.write_formula(
                            current_row, col_value, pps_formula, self.formats.get('currency'))
                    else:
                        inv_total = self._get_round_investment_total_ref(round_idx, round_data)
                        if valuation_cap_basis == 'pre_money':
                            ref = pre_money_ref or (f"({post_money_ref} - {inv_total})" if post_money_ref else "0")
                            pps_formula = valuation.create_price_per_share_from_valuation_formula(
                                ref, pre_round_shares_ref
                            )
                        else:
                            ref = post_money_ref or (f"({pre_money_ref} + {inv_total})" if pre_money_ref else "0")
                            pps_formula = valuation.create_price_per_share_from_valuation_formula(
                                ref, pre_round_shares_ref
                            )
                        sheet.write_formula(
                            current_row, col_value, pps_formula, self.formats.get('currency'))
                else:
                    sheet.write(current_row, col_value, pps or 0,
                                self.formats.get('currency'))

                # Register named range
                round_name_key = self._sanitize_excel_name(round_data.get('name', ''))
                col_letter = self._col_letter(col_value)
                price_per_share_cell = f"${col_letter}${current_row + 1}"
                named_range_name = f"{round_name_key}_PricePerShare"
                self.dlm.register_named_range(
                    named_range_name, 'Rounds', current_row, col_value)
                self.workbook.define_name(
                    named_range_name, f"'Rounds'!{price_per_share_cell}")
            else:
                # Regular value or inferred valuation
                if label in ('Pre-Money Valuation:', 'Post-Money Valuation:') and (value is None or value == ''):
                    # Build inference formula using investment total and the counterpart constant
                    inv_total = self._get_round_investment_total_ref(round_idx, round_data)
                    col_letter = self._col_letter(col_value)
                    if label == 'Pre-Money Valuation:':
                        # Find the row of Post-Money (may be upcoming); prefer tracked, else assume next occurrence
                        post_row = self._find_constant_row(round_idx, 'Post-Money Valuation:')
                        if post_row is None:
                            # Assume Post is the next constant in sequence
                            post_row = current_row + 1
                        post_ref = f"{col_letter}{post_row + 1}"
                        formula = f"={post_ref} - {inv_total}"
                    else:
                        pre_row = self._find_constant_row(round_idx, 'Pre-Money Valuation:')
                        if pre_row is None:
                            # Assume Pre appeared just before
                            pre_row = current_row - 1
                        pre_ref = f"{col_letter}{pre_row + 1}"
                        formula = f"={pre_ref} + {inv_total}"
                    sheet.write_formula(current_row, col_value, formula, self.formats.get('currency'))
                else:
                    sheet.write(current_row, col_value, value or '',
                                self.formats.get(format_type))

            current_row += 1

        return current_row

    def _write_instruments_table(
        self,
        sheet: xlsxwriter.worksheet.Worksheet,
        round_idx: int,
        round_data: Dict[str, Any],
        instruments: List[Dict[str, Any]],
        all_rounds: List[Dict[str, Any]],
        start_row: int
    ) -> int:
        """Write instruments table and return next row."""
        calc_type = round_data.get('calculation_type', 'fixed_shares')
        current_row = start_row

        # Table starts at parameters column (padding_offset + 2, column 3)
        table_start_col = self.padding_offset + 2

        # Define column headers based on calculation type
        if calc_type == 'fixed_shares':
            headers = ['Holder Name', 'Class Name',
                       'Shares']
            col_map = {'holder_name': 0, 'class_name': 1,
                       'shares': 2}
        elif calc_type == 'target_percentage':
            headers = ['Holder Name', 'Class Name',
                       'Target %', 'Shares']
            col_map = {'holder_name': 0, 'class_name': 1,
                       'target_percentage': 2, 'shares': 3}
        elif calc_type == 'valuation_based':
            headers = ['Holder Name', 'Class Name', 'Investment Amount',
                       'Shares']
            col_map = {'holder_name': 0, 'class_name': 1, 'investment_amount': 2,
                       'shares': 3}
        elif calc_type == 'convertible':
            headers = ['Holder Name', 'Class Name', 'Investment Amount', 'Interest Start',
                       'Interest End', 'Days Passed', 'Interest (%)', 'Interest Type',
                       'Accrued Interest', 'Discount (%)', 'Shares']
            col_map = {'holder_name': 0, 'class_name': 1, 'investment_amount': 2,
                       'interest_start_date': 3, 'interest_end_date': 4, 'days_passed': 5,
                       'interest_rate': 6, 'interest_type': 7, 'accrued_interest': 8,
                       'discount_rate': 9, 'shares': 10}
        else:
            headers = ['Holder Name', 'Class Name', 'Shares']
            col_map = {'holder_name': 0, 'class_name': 1, 'shares': 2}

        # Write headers (shifted by table_start_col)
        for col_idx, header in enumerate(headers):
            sheet.write(current_row, table_start_col + col_idx, header,
                        self.formats.get('header'))
        current_row += 1

        # Write instruments
        first_instrument_row = current_row  # Track for shares_issued calculation
        interest_type_rows = []  # Track rows with interest_type for dropdown validation
        for inst_idx, instrument in enumerate(instruments):
            row = current_row

            # Write basic fields (shifted by table_start_col)
            sheet.write(row, table_start_col + col_map['holder_name'], instrument.get(
                'holder_name', ''), self.formats.get('text'))
            sheet.write(row, table_start_col + col_map['class_name'], instrument.get(
                'class_name', ''), self.formats.get('text'))

            # Write fields based on calculation type
            if calc_type == 'fixed_shares':
                initial_qty = instrument.get('initial_quantity', 0)
                sheet.write(
                    row, table_start_col + col_map['shares'], initial_qty or 0, self.formats.get('table_number'))

            elif calc_type == 'target_percentage':
                target_pct = instrument.get('target_percentage', 0)
                sheet.write(row, table_start_col + col_map['target_percentage'],
                            target_pct, self.formats.get('table_percent'))

                # Calculated shares (base shares only - pro rata handled separately)
                # Subtract existing shares from calculated shares, similar to pro rata calculation
                pre_round_shares_ref = self._get_pre_round_shares_ref(
                    round_idx, round_data, all_rounds)
                # Target percentage column (shifted by table_start_col)
                target_pct_col = self._col_letter(
                    table_start_col + col_map['target_percentage'])
                # Get holder's current shares before this round
                holder_name = instrument.get('holder_name', '')
                holder_current_shares_ref = self._get_holder_current_shares_ref(
                    round_idx, holder_name, all_rounds)
                shares_formula = valuation.create_shares_from_percentage_formula(
                    f"{target_pct_col}{row + 1}", pre_round_shares_ref, holder_current_shares_ref
                )
                sheet.write_formula(
                    row, table_start_col + col_map['shares'], shares_formula, self.formats.get('table_number'))

            elif calc_type == 'valuation_based':
                investment = instrument.get('investment_amount', 0)
                sheet.write(row, table_start_col + col_map['investment_amount'],
                            investment, self.formats.get('table_currency'))

                # Calculated shares (base shares only - pro rata handled separately)
                pre_round_shares_ref = self._get_pre_round_shares_ref(
                    round_idx, round_data, all_rounds)

                # Investment Amount and Accrued Interest columns (shifted by table_start_col)
                investment_col = self._col_letter(
                    table_start_col + col_map['investment_amount'])

                # Get references to valuation fields (values column is padding_offset + 3, column 4)
                valuation_basis_row = self._find_constant_row(
                    round_idx, 'Valuation Basis:')
                col_value_ref = self.padding_offset + \
                    3  # Values column (column 4)
                col_letter = self._col_letter(col_value_ref)
                valuation_basis_ref = f"{col_letter}{valuation_basis_row + 1}" if valuation_basis_row is not None else None
                pre_row = self._find_constant_row(round_idx, 'Pre-Money Valuation:')
                post_row = self._find_constant_row(round_idx, 'Post-Money Valuation:')
                pre_money_ref = f"{col_letter}{pre_row + 1}" if pre_row is not None else None
                post_money_ref = f"{col_letter}{post_row + 1}" if post_row is not None else None

                # Create dynamic formula that checks valuation_basis cell value
                if valuation_basis_ref:
                    # Dynamic formula using IF to check valuation_basis cell; infer missing using round investment total
                    inv_total = self._get_round_investment_total_ref(round_idx, round_data)
                    if pre_money_ref is None and post_money_ref is not None:
                        pre_ref_safe = f"({post_money_ref} - {inv_total})"
                    else:
                        pre_ref_safe = pre_money_ref or "0"
                    if post_money_ref is None and pre_money_ref is not None:
                        post_ref_safe = f"({pre_money_ref} + {inv_total})"
                    else:
                        post_ref_safe = post_money_ref or "0"
                    pre_money_formula = valuation.create_shares_from_investment_premoney_formula(
                        f"{investment_col}{row + 1}", pre_ref_safe, pre_round_shares_ref
                    )
                    post_money_formula = valuation.create_shares_from_investment_postmoney_formula(
                        f"{investment_col}{row + 1}", post_ref_safe, pre_round_shares_ref
                    )
                    # Remove leading = from formulas for IF statement
                    pre_money_formula_no_eq = pre_money_formula.lstrip('=')
                    post_money_formula_no_eq = post_money_formula.lstrip('=')
                    shares_formula = f"=IF({valuation_basis_ref}=\"pre_money\", {pre_money_formula_no_eq}, {post_money_formula_no_eq})"
                else:
                    # Fallback to static value with inference from investment total
                    inv_total = self._get_round_investment_total_ref(round_idx, round_data)
                    valuation_basis = round_data.get(
                        'valuation_basis', 'pre_money')
                    if valuation_basis == 'pre_money':
                        ref = pre_money_ref or (f"({post_money_ref} - {inv_total})" if post_money_ref else "0")
                        shares_formula = valuation.create_shares_from_investment_premoney_formula(
                            f"{investment_col}{row + 1}", ref, pre_round_shares_ref
                        )
                    else:
                        ref = post_money_ref or (f"({pre_money_ref} + {inv_total})" if pre_money_ref else "0")
                        shares_formula = valuation.create_shares_from_investment_postmoney_formula(
                            f"{investment_col}{row + 1}", ref, pre_round_shares_ref
                        )

                # Write base shares (pro rata handled separately in Pro Rata Allocations sheet)
                sheet.write_formula(
                    row, table_start_col + col_map['shares'], shares_formula, self.formats.get('table_number'))

            elif calc_type == 'convertible':
                investment = instrument.get('investment_amount', 0)
                sheet.write(row, table_start_col + col_map['investment_amount'],
                            investment, self.formats.get('table_currency'))

                interest_start = instrument.get('interest_start_date', '')
                sheet.write(row, table_start_col + col_map['interest_start_date'],
                            interest_start, self.formats.get('table_date'))

                interest_end = instrument.get('interest_end_date', '')
                sheet.write(row, table_start_col + col_map['interest_end_date'],
                            interest_end, self.formats.get('table_date'))

                # Days passed
                start_col = self._col_letter(
                    table_start_col + col_map['interest_start_date'])
                end_col = self._col_letter(
                    table_start_col + col_map['interest_end_date'])
                days_formula = interest.create_days_passed_formula(
                    f"{start_col}{row + 1}", f"{end_col}{row + 1}"
                )
                sheet.write_formula(
                    row, table_start_col + col_map['days_passed'], days_formula, self.formats.get('table_number'))

                interest_rate = instrument.get('interest_rate', 0)
                sheet.write(row, table_start_col + col_map['interest_rate'],
                            interest_rate, self.formats.get('table_percent'))

                interest_type = instrument.get('interest_type', 'simple')
                sheet.write(row, table_start_col + col_map['interest_type'],
                            interest_type, self.formats.get('text'))
                # Track this row for dropdown validation
                interest_type_rows.append(row)

                # Accrued interest
                # Use dynamic column references based on col_map (shifted by table_start_col)
                principal_col = self._col_letter(
                    table_start_col + col_map['investment_amount'])
                rate_col = self._col_letter(
                    table_start_col + col_map['interest_rate'])
                start_col = self._col_letter(
                    table_start_col + col_map['interest_start_date'])
                end_col = self._col_letter(
                    table_start_col + col_map['interest_end_date'])
                interest_type_col = self._col_letter(
                    table_start_col + col_map['interest_type'])
                # Pass the cell reference for interest_type so formula updates dynamically
                interest_formula = interest.create_accrued_interest_formula(
                    f"{principal_col}{row + 1}", f"{rate_col}{row + 1}",
                    f"{start_col}{row + 1}", f"{end_col}{row + 1}",
                    interest_type=interest_type,
                    interest_type_ref=f"{interest_type_col}{row + 1}"
                )
                sheet.write_formula(
                    row, table_start_col + col_map['accrued_interest'], interest_formula, self.formats.get('table_currency'))

                discount_rate = instrument.get('discount_rate', 0)
                sheet.write(row, table_start_col + col_map['discount_rate'],
                            discount_rate, self.formats.get('table_percent'))

                # Calculated shares (base shares only - pro rata handled separately)
                # Price per share is already calculated based on valuation_cap_basis (pre_money/post_money/fixed)
                # Need to get col_value from constants section (column 4)
                col_value_ref = self.padding_offset + \
                    3  # Values column (column 4)
                col_letter = self._col_letter(col_value_ref)
                round_pps_ref = f"{col_letter}{self._find_constant_row(round_idx, 'Price Per Share:') + 1}"

                # Get dynamic column references for convertible formula (shifted by table_start_col)
                investment_col = self._col_letter(
                    table_start_col + col_map['investment_amount'])
                interest_col = self._col_letter(
                    table_start_col + col_map['accrued_interest'])
                discount_col = self._col_letter(
                    table_start_col + col_map['discount_rate'])

                # Use price_per_share directly (it's already calculated based on valuation_cap_basis)
                # The shares formula just uses price_per_share with discount, without recalculating cap price
                shares_formula = valuation.create_convertible_shares_formula(
                    f"{investment_col}{row + 1}", f"{interest_col}{row + 1}", f"{discount_col}{row + 1}",
                    round_pps_ref
                )

                # Write base shares (pro rata handled separately in Pro Rata Allocations sheet)
                sheet.write_formula(
                    row, table_start_col + col_map['shares'], shares_formula, self.formats.get('table_number'))

            # Register instrument with DLM (col_map needs to be shifted by table_start_col)
            shifted_col_map = {k: table_start_col +
                               v for k, v in col_map.items()}
            self.dlm.register_round_instrument(
                round_idx, inst_idx, round_data.get(
                    'name', ''), 'Rounds', row, shifted_col_map
            )

            current_row += 1

        # Add dropdown validation to interest_type column for convertible instruments
        if calc_type == 'convertible' and interest_type_rows:
            interest_type_col = table_start_col + col_map['interest_type']
            first_row = min(interest_type_rows)
            last_row = max(interest_type_rows)
            # Create dropdown with valid interest type options
            sheet.data_validation(
                first_row, interest_type_col,
                last_row, interest_type_col,
                {
                    'validate': 'list',
                    'source': ['simple', 'compound_yearly', 'compound_monthly', 'compound_daily', 'no_interest'],
                    'error_type': 'stop',
                    'error_title': 'Invalid Interest Type',
                    'error_message': 'Please select a valid interest type from the dropdown.'
                }
            )

        # Write total row
        last_instrument_row = current_row - 1
        total_row = current_row

        # Write "TOTAL" label in first column
        sheet.write(total_row, table_start_col, 'TOTAL',
                    self.formats.get('total_label'))

        # Fill total row for all columns based on calculation type
        for col_idx in range(len(headers)):
            col_pos = table_start_col + col_idx
            header_name = headers[col_idx]

            # Determine format and value based on column type
            if col_idx == 0:  # Holder Name column - already written TOTAL
                continue
            elif col_idx == 1:  # Class Name column - empty
                sheet.write(total_row, col_pos, '',
                            self.formats.get('total_text'))
            elif header_name in ['Investment Amount', 'Accrued Interest']:
                # Sum currency columns
                col_letter = self._col_letter(col_pos)
                sum_formula = f"=SUM({col_letter}{first_instrument_row + 1}:{col_letter}{last_instrument_row + 1})"
                sheet.write_formula(
                    total_row, col_pos, sum_formula, self.formats.get('total_currency'))
            elif header_name in ['Shares']:
                # Sum shares column
                col_letter = self._col_letter(col_pos)
                sum_formula = f"=SUM({col_letter}{first_instrument_row + 1}:{col_letter}{last_instrument_row + 1})"
                sheet.write_formula(
                    total_row, col_pos, sum_formula, self.formats.get('total_number'))
            elif header_name in ['Target %']:
                # Sum percentage column
                col_letter = self._col_letter(col_pos)
                sum_formula = f"=SUM({col_letter}{first_instrument_row + 1}:{col_letter}{last_instrument_row + 1})"
                sheet.write_formula(
                    total_row, col_pos, sum_formula, self.formats.get('total_percent'))
            elif header_name in ['Days Passed']:
                # Sum days passed column
                col_letter = self._col_letter(col_pos)
                sum_formula = f"=SUM({col_letter}{first_instrument_row + 1}:{col_letter}{last_instrument_row + 1})"
                sheet.write_formula(
                    total_row, col_pos, sum_formula, self.formats.get('total_number'))
            elif header_name in ['Discount (%)', 'Interest (%)']:
                # Average percentage columns (or empty - depends on requirement)
                sheet.write(total_row, col_pos, '',
                            self.formats.get('total_text'))
            else:
                # Other columns (dates, text) - empty
                sheet.write(total_row, col_pos, '',
                            self.formats.get('total_text'))

        current_row = total_row + 1

        # Create Excel Table for this round's instruments to enable structured references
        # Table range includes header row and all instrument rows (shifted by table_start_col)
        if last_instrument_row >= first_instrument_row:
            header_row = first_instrument_row - 1
            end_col = table_start_col + len(headers) - 1
            columns_def = [{'header': h} for h in headers]
            table_name = self._get_round_table_name(round_idx, round_data)
            # Omit style to avoid default table styling (blue borders, white text)
            sheet.add_table(
                header_row,
                table_start_col,
                last_instrument_row,
                end_col,
                {
                    'name': table_name,
                    'columns': columns_def
                }
            )
            # Override header row formatting to ensure black text, white background, bottom border only
            header_format = self.formats.get('header')
            for col_idx in range(len(headers)):
                col_pos = table_start_col + col_idx
                # Re-write header cell with our custom format to override table default styling
                sheet.write(header_row, col_pos,
                            headers[col_idx], header_format)

        return current_row

    def _get_pre_round_shares_ref(self, round_idx: int, round_data: Dict[str, Any],
                                  all_rounds: List[Dict[str, Any]]) -> str:
        """Get Excel reference for pre_round_shares."""
        round_name_key = self._sanitize_excel_name(round_data.get('name', ''))
        named_range = f"{round_name_key}_PreRoundShares"

        # Try to resolve from DLM, otherwise construct cell reference
        ref = self.dlm.resolve_reference(named_range)
        if ref:
            return ref

        # Fallback: construct cell reference (would need to track row)
        # For now, use named range directly
        return named_range

    def _get_holder_current_shares_ref(self, round_idx: int, holder_name: str,
                                       all_rounds: List[Dict[str, Any]]) -> str:
        """
        Get Excel reference for holder's current shares before this round.
        Uses SUMIF to get the holder's total shares from the previous round in Cap Table Progression.
        
        Args:
            round_idx: Current round index
            holder_name: Name of the holder
            all_rounds: List of all rounds data
            
        Returns:
            Excel formula string that references holder's current shares
        """
        if round_idx == 0:
            # First round - no previous shares
            return "0"
        
        # Get the previous round's total column in progression sheet
        # Each round has 4 columns: Start, New, Total, %
        # Total is 2 columns after Start
        # Formula: col = 2 + ((round_idx - 1) * 5) + 4 (for Total column)
        prev_round_idx = round_idx - 1
        prev_round_total_col_idx = 2 + (prev_round_idx * 5) + 4
        prev_round_total_col = self._col_letter(prev_round_total_col_idx)
        
        # Holder names are in column B (padding_offset + 1 = column 2, which is B)
        holder_name_col = self._col_letter(self.padding_offset + 1)
        
        # Use SUMIF to match holder name and get their total from previous round
        # Format: SUMIF('Cap Table Progression'!B:B, holder_name, 'Cap Table Progression'!<col>:<col>)
        holder_name_escaped = f'"{holder_name}"'
        progression_sheet = "'Cap Table Progression'"
        holder_range = f"{progression_sheet}!{holder_name_col}:{holder_name_col}"
        total_range = f"{progression_sheet}!{prev_round_total_col}:{prev_round_total_col}"
        
        return f"IFERROR(SUMIF({holder_range}, {holder_name_escaped}, {total_range}), 0)"

    def _get_pro_rata_total_ref(self, round_idx: int, round_data: Dict[str, Any],
                                all_rounds: List[Dict[str, Any]]) -> str:
        """Get Named Range for total pro rata shares for a given round."""
        round_name_key = self._sanitize_excel_name(round_data.get('name', ''))
        named_range = f"{round_name_key}_ProRataShares"
        # Prefer DLM resolve if available, otherwise return named range directly
        ref = self.dlm.resolve_reference(named_range)
        return ref or named_range

    def _get_round_investment_total_ref(self, round_idx: int, round_data: Dict[str, Any]) -> str:
        """Return an Excel SUM over this round's Investment Amount column using table structured refs."""
        table_name = self._get_round_table_name(round_idx, round_data)
        return f"SUM({table_name}[[#All],[Investment Amount]])"

    def _find_constant_row(self, round_idx: int, constant_label: str) -> Optional[int]:
        """Find the row where a constant label appears."""
        if round_idx in self.round_constants_rows:
            return self.round_constants_rows[round_idx].get(constant_label)
        return None

    def _get_shares_column_index(self, calc_type: str) -> int:
        """Get the column index (within table) for shares based on calculation type."""
        if calc_type == 'fixed_shares':
            return 3  # 4th column (0-indexed: 3)
        elif calc_type == 'target_percentage':
            return 3  # 4th column (0-indexed: 3)
        elif calc_type == 'valuation_based':
            return 4  # 5th column (0-indexed: 4)
        elif calc_type == 'convertible':
            return 10  # 11th column (0-indexed: 10)
        return 3  # Default

    def _get_shares_column_letter(self, calc_type: str) -> str:
        """Get the column letter for shares based on calculation type (legacy method)."""
        table_start_col = self.padding_offset + \
            2  # Start at parameters column (column 3)
        shares_col_idx = table_start_col + \
            self._get_shares_column_index(calc_type)
        return self._col_letter(shares_col_idx)

    def _get_round_table_name(self, round_idx: int, round_data: Dict[str, Any]) -> str:
        """Generate a stable Excel table name for a round's instruments table."""
        round_name = round_data.get('name', f'Round {round_idx + 1}')
        calc_type = round_data.get('calculation_type', 'fixed_shares')
        # Excel table name rules: letters, numbers, underscores, cannot look like a cell reference
        safe_round = ''.join(ch if ch.isalnum() else '_' for ch in round_name)
        safe_calc = ''.join(ch if ch.isalnum() else '_' for ch in calc_type)
        return f"{safe_round}_{safe_calc}_Instruments"

    def get_round_ranges(self) -> Dict[int, Dict[str, Any]]:
        """Get round ranges for progression sheet reference."""
        return self.round_ranges
