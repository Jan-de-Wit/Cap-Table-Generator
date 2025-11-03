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

    def _get_sheet_name(self) -> str:
        """Returns 'Rounds'."""
        return "Rounds"

    def generate(self) -> xlsxwriter.worksheet.Worksheet:
        """Generate the Rounds sheet."""
        sheet = self.workbook.add_worksheet('Rounds')
        self.sheet = sheet

        rounds = self.data.get('rounds', [])
        if not rounds:
            sheet.write(0, 0, 'No rounds found', self.formats.get('text'))
            return sheet

        # Track current row as we build vertically
        current_row = 0

        # Write rounds vertically
        for round_idx, round_data in enumerate(rounds):
            current_row = self._write_round(
                sheet, round_idx, round_data, rounds, current_row
            )
            # Add spacing between rounds (3 rows)
            current_row += 3

        # Set column widths
        self.set_column_widths([
            (0, 0, 25),  # Holder name
            (1, 1, 20),  # Class name
            (2, 15, 15),  # Other columns
        ])

        return sheet

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

        # Write round heading
        sheet.write(current_row, 0, round_name, self.formats.get('round_header_plain'))
        current_row += 1

        # Write constants section
        constants_row = current_row
        current_row = self._write_round_constants(
            sheet, round_idx, round_data, all_rounds, current_row
        )

        # Add dropdown validation for valuation basis fields
        if calc_type == 'valuation_based':
            valuation_basis_row = self._find_constant_row(round_idx, 'Valuation Basis:')
            if valuation_basis_row is not None:
                sheet.data_validation(
                    valuation_basis_row, 1,  # Column B
                    valuation_basis_row, 1,
                    {
                        'validate': 'list',
                        'source': ['pre_money', 'post_money'],
                        'error_type': 'stop',
                        'error_title': 'Invalid Valuation Basis',
                        'error_message': 'Please select either "pre_money" or "post_money" from the dropdown.'
                    }
                )
        elif calc_type == 'convertible':
            valuation_cap_basis_row = self._find_constant_row(round_idx, 'Valuation Cap Basis:')
            if valuation_cap_basis_row is not None:
                sheet.data_validation(
                    valuation_cap_basis_row, 1,  # Column B
                    valuation_cap_basis_row, 1,
                    {
                        'validate': 'list',
                        'source': ['pre_money', 'post_money', 'fixed'],
                        'error_type': 'stop',
                        'error_title': 'Invalid Valuation Cap Basis',
                        'error_message': 'Please select "pre_money", "post_money", or "fixed" from the dropdown.'
                    }
                )

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
            # No instruments - just write placeholder
            sheet.write(current_row, 0, 'No instruments',
                        self.formats.get('text'))
            current_row += 1

        # Register round section with DLM
        self.dlm.register_round_section(
            round_name, 'Rounds', constants_row, instruments_start_row
        )

        # Store round range info for progression sheet
        instruments_end_row = current_row - 1 if regular_instruments else instruments_start_row
        # Include table metadata if a table was created
        table_name = self._get_round_table_name(round_idx, round_data)
        self.round_ranges[round_idx] = {
            'start_row': instruments_start_row + 2,  # +1 for header
            'end_row': instruments_end_row + 1,
            'holder_col': 'A',  # Column letters retained for fallback
            'shares_col': self._get_shares_column_letter(calc_type),
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
        allowed_fields = {"holder_name", "class_name", "pro_rata_type", "pro_rata_percentage"}
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
        start_row: int
    ) -> int:
        """Write round constants and return next row."""
        current_row = start_row
        calc_type = round_data.get('calculation_type', 'fixed_shares')

        # Initialize constants tracking for this round
        self.round_constants_rows[round_idx] = {}

        # Constants labels in column A, values in column B
        col_label = 0
        col_value = 1

        # Round Date
        sheet.write(current_row, col_label, 'Round Date:',
                    self.formats.get('label'))
        round_date = round_data.get('round_date', '')
        sheet.write(current_row, col_value, round_date,
                    self.formats.get('date'))
        current_row += 1

        # Calculation Type
        sheet.write(current_row, col_label, 'Calculation Type:',
                    self.formats.get('label'))
        sheet.write(current_row, col_value, calc_type,
                    self.formats.get('text'))
        current_row += 1

        # Pre-Round Shares
        sheet.write(current_row, col_label, 'Pre-Round Shares:',
                    self.formats.get('label'))
        self.round_constants_rows[round_idx]['Pre-Round Shares:'] = current_row
        
        # Calculate cell reference with absolute addressing for named range
        pre_round_shares_cell = f"$B${current_row + 1}"
        
        if round_idx == 0:
            # First round: sum all initial shares from previous rounds (none for first)
            sheet.write(current_row, col_value, 0, self.formats.get('number'))
        else:
            # Previous round's pre_round_shares + base shares issued + prior round pro rata shares
            prev_round = all_rounds[round_idx - 1]
            prev_pre_round_ref = self._get_pre_round_shares_ref(
                round_idx - 1, prev_round, all_rounds)
            prev_shares_issued_ref = self._get_shares_issued_ref(
                round_idx - 1, prev_round, all_rounds)
            prev_prorata_total_ref = self._get_pro_rata_total_ref(round_idx - 1, prev_round, all_rounds)
            formula = f"=IFERROR({prev_pre_round_ref} + {prev_shares_issued_ref} + {prev_prorata_total_ref}, 0)"
            sheet.write_formula(current_row, col_value,
                                formula, self.formats.get('number'))

        # Register named range for pre_round_shares
        # Use absolute cell reference format that xlsxwriter expects
        round_name_key = round_data.get('name', '').replace(' ', '_')
        named_range_name = f"{round_name_key}_PreRoundShares"
        self.dlm.register_named_range(
            named_range_name, 'Rounds', current_row, col_value)
        # Define with absolute reference: 'SheetName'!$B$5
        self.workbook.define_name(
            named_range_name, f"'Rounds'!{pre_round_shares_cell}")
        current_row += 1

        # Valuation fields (for valuation_based and convertible)
        if calc_type in ['valuation_based', 'convertible']:
            if calc_type == 'valuation_based':
                valuation_basis = round_data.get(
                    'valuation_basis', 'pre_money')
                sheet.write(current_row, col_label,
                            'Valuation Basis:', self.formats.get('label'))
                sheet.write(current_row, col_value,
                            valuation_basis, self.formats.get('text'))
                self.round_constants_rows[round_idx]['Valuation Basis:'] = current_row
                current_row += 1

            if calc_type == 'convertible':
                valuation_cap_basis = round_data.get(
                    'valuation_cap_basis', 'pre_money')
                sheet.write(current_row, col_label,
                            'Valuation Cap Basis:', self.formats.get('label'))
                sheet.write(current_row, col_value,
                            valuation_cap_basis, self.formats.get('text'))
                self.round_constants_rows[round_idx]['Valuation Cap Basis:'] = current_row
                current_row += 1

            # Pre-Money Valuation
            if 'pre_money_valuation' in round_data:
                sheet.write(current_row, col_label,
                            'Pre-Money Valuation:', self.formats.get('label'))
                self.round_constants_rows[round_idx]['Pre-Money Valuation:'] = current_row
                pre_money_val = round_data.get('pre_money_valuation')
                if isinstance(pre_money_val, dict) and pre_money_val.get('is_calculated'):
                    formula = self.formula_resolver.resolve_feo(pre_money_val)
                    sheet.write_formula(
                        current_row, col_value, formula, self.formats.get('currency'))
                else:
                    sheet.write(current_row, col_value,
                                pre_money_val or 0, self.formats.get('currency'))
                current_row += 1

            # Post-Money Valuation
            if 'post_money_valuation' in round_data:
                sheet.write(current_row, col_label,
                            'Post-Money Valuation:', self.formats.get('label'))
                self.round_constants_rows[round_idx]['Post-Money Valuation:'] = current_row
                post_money_val = round_data.get('post_money_valuation')
                if isinstance(post_money_val, dict) and post_money_val.get('is_calculated'):
                    formula = self.formula_resolver.resolve_feo(post_money_val)
                    sheet.write_formula(
                        current_row, col_value, formula, self.formats.get('currency'))
                else:
                    sheet.write(current_row, col_value,
                                post_money_val or 0, self.formats.get('currency'))
                current_row += 1

            # Price Per Share
            if 'price_per_share' in round_data or calc_type == 'convertible':
                sheet.write(current_row, col_label,
                            'Price Per Share:', self.formats.get('label'))
                self.round_constants_rows[round_idx]['Price Per Share:'] = current_row
                pps = round_data.get('price_per_share')
                
                # For convertible rounds, calculate price_per_share based on valuation_cap_basis
                if calc_type == 'convertible':
                    valuation_cap_basis = round_data.get('valuation_cap_basis', 'pre_money')
                    pre_round_shares_ref = self._get_pre_round_shares_ref(round_idx, round_data, all_rounds)
                    
                    # Get the valuation reference based on basis
                    valuation_cap_basis_row = self._find_constant_row(round_idx, 'Valuation Cap Basis:')
                    valuation_cap_basis_ref = f"B{valuation_cap_basis_row + 1}" if valuation_cap_basis_row is not None else None
                    
                    pre_money_ref = f"B{self._find_constant_row(round_idx, 'Pre-Money Valuation:') + 1}"
                    post_money_ref = f"B{self._find_constant_row(round_idx, 'Post-Money Valuation:') + 1}"
                    
                    if valuation_cap_basis_ref:
                        # Dynamic formula that checks valuation_cap_basis dropdown
                        # For pre_money and post_money, calculate from valuation
                        pre_money_pps_formula = valuation.create_price_per_share_from_valuation_formula(
                            pre_money_ref, pre_round_shares_ref
                        )
                        post_money_pps_formula = valuation.create_price_per_share_from_valuation_formula(
                            post_money_ref, pre_round_shares_ref
                        )
                        # Remove leading = from formulas for IF statement
                        pre_money_pps_formula_no_eq = pre_money_pps_formula.lstrip('=')
                        post_money_pps_formula_no_eq = post_money_pps_formula.lstrip('=')
                        # When dropdown is "fixed", keep current value; otherwise calculate from valuation
                        # Note: When user changes dropdown to "fixed", they'll need to enter the value manually
                        # We can't make it truly dynamic for fixed because it would require circular reference
                        fixed_initial_value = pps if pps else 0
                        pps_formula = f"=IF({valuation_cap_basis_ref}=\"fixed\", {fixed_initial_value}, IF({valuation_cap_basis_ref}=\"pre_money\", {pre_money_pps_formula_no_eq}, {post_money_pps_formula_no_eq}))"
                        sheet.write_formula(
                            current_row, col_value, pps_formula, self.formats.get('currency'))
                    else:
                        # Fallback to static calculation
                        if valuation_cap_basis == 'pre_money':
                            pps_formula = valuation.create_price_per_share_from_valuation_formula(
                                pre_money_ref, pre_round_shares_ref
                            )
                        else:
                            pps_formula = valuation.create_price_per_share_from_valuation_formula(
                                post_money_ref, pre_round_shares_ref
                            )
                        sheet.write_formula(
                            current_row, col_value, pps_formula, self.formats.get('currency'))
                else:
                    # For non-convertible rounds, use existing logic
                    if isinstance(pps, dict) and pps.get('is_calculated'):
                        formula = self.formula_resolver.resolve_feo(pps)
                        sheet.write_formula(
                            current_row, col_value, formula, self.formats.get('currency'))
                    else:
                        sheet.write(current_row, col_value, pps or 0,
                                    self.formats.get('currency'))
                
                # Register named range for price_per_share
                round_name_key = round_data.get('name', '').replace(' ', '_')
                price_per_share_cell = f"$B${current_row + 1}"
                named_range_name = f"{round_name_key}_PricePerShare"
                self.dlm.register_named_range(
                    named_range_name, 'Rounds', current_row, col_value)
                # Define with absolute reference: 'SheetName'!$B$5
                self.workbook.define_name(
                    named_range_name, f"'Rounds'!{price_per_share_cell}")
                
                current_row += 1

        # Shares Issued (calculated from instruments)
        sheet.write(current_row, col_label, 'Shares Issued:',
                    self.formats.get('label'))
        self.round_constants_rows[round_idx]['Shares Issued:'] = current_row
        shares_issued_cell = f"B{current_row + 1}"
        # Formula will sum all instrument shares from this round
        # We'll update this after writing instruments
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

        # Define column headers based on calculation type
        if calc_type == 'fixed_shares':
            headers = ['Holder Name', 'Class Name',
                       'Acquisition Date', 'Shares']
            col_map = {'holder_name': 0, 'class_name': 1,
                       'acquisition_date': 2, 'shares': 3}
        elif calc_type == 'target_percentage':
            headers = ['Holder Name', 'Class Name', 'Target %', 'Calculated Shares']
            col_map = {'holder_name': 0, 'class_name': 1, 'target_percentage': 2, 'shares': 3}
        elif calc_type == 'valuation_based':
            headers = ['Holder Name', 'Class Name', 'Investment Amount', 'Accrued Interest', 'Calculated Shares']
            col_map = {'holder_name': 0, 'class_name': 1, 'investment_amount': 2,
                       'accrued_interest': 3, 'shares': 4}
        elif calc_type == 'convertible':
            headers = ['Holder Name', 'Class Name', 'Investment Amount', 'Interest Start',
                       'Interest End', 'Days Passed', 'Interest Rate', 'Interest Type',
                       'Accrued Interest', 'Discount Rate', 'Calculated Shares']
            col_map = {'holder_name': 0, 'class_name': 1, 'investment_amount': 2,
                       'interest_start_date': 3, 'interest_end_date': 4, 'days_passed': 5,
                       'interest_rate': 6, 'interest_type': 7, 'accrued_interest': 8,
                       'discount_rate': 9, 'shares': 10}
        else:
            headers = ['Holder Name', 'Class Name', 'Shares']
            col_map = {'holder_name': 0, 'class_name': 1, 'shares': 2}

        # Write headers
        for col_idx, header in enumerate(headers):
            sheet.write(current_row, col_idx, header,
                        self.formats.get('header'))
        current_row += 1

        # Write instruments
        first_instrument_row = current_row  # Track for shares_issued calculation
        interest_type_rows = []  # Track rows with interest_type for dropdown validation
        for inst_idx, instrument in enumerate(instruments):
            row = current_row

            # Write basic fields
            sheet.write(row, col_map['holder_name'], instrument.get(
                'holder_name', ''), self.formats.get('text'))
            sheet.write(row, col_map['class_name'], instrument.get(
                'class_name', ''), self.formats.get('text'))

            # Write fields based on calculation type
            if calc_type == 'fixed_shares':
                acquisition_date = instrument.get('acquisition_date', '')
                sheet.write(row, col_map['acquisition_date'],
                            acquisition_date, self.formats.get('date'))

                initial_qty = instrument.get('initial_quantity', 0)
                if isinstance(initial_qty, dict) and initial_qty.get('is_calculated'):
                    formula = self.formula_resolver.resolve_feo(initial_qty)
                    sheet.write_formula(
                        row, col_map['shares'], formula, self.formats.get('number'))
                else:
                    sheet.write(
                        row, col_map['shares'], initial_qty or 0, self.formats.get('number'))

            elif calc_type == 'target_percentage':
                target_pct = instrument.get('target_percentage', 0)
                sheet.write(row, col_map['target_percentage'],
                            target_pct, self.formats.get('percent'))

                # Calculated shares (base shares only - pro rata handled separately)
                pre_round_shares_ref = self._get_pre_round_shares_ref(
                    round_idx, round_data, all_rounds)
                # Target percentage is in column C (index 2)
                target_pct_col = self._col_letter(col_map['target_percentage'])
                shares_formula = valuation.create_shares_from_percentage_formula(
                    f"{target_pct_col}{row + 1}", pre_round_shares_ref
                )
                sheet.write_formula(
                    row, col_map['shares'], shares_formula, self.formats.get('number'))

            elif calc_type == 'valuation_based':
                investment = instrument.get('investment_amount', 0)
                sheet.write(row, col_map['investment_amount'],
                            investment, self.formats.get('currency'))

                accrued_interest = instrument.get('accrued_interest', 0)
                if isinstance(accrued_interest, dict) and accrued_interest.get('is_calculated'):
                    formula = self.formula_resolver.resolve_feo(
                        accrued_interest)
                    sheet.write_formula(
                        row, col_map['accrued_interest'], formula, self.formats.get('currency'))
                else:
                    sheet.write(
                        row, col_map['accrued_interest'], accrued_interest or 0, self.formats.get('currency'))

                # Calculated shares (base shares only - pro rata handled separately)
                pre_round_shares_ref = self._get_pre_round_shares_ref(
                    round_idx, round_data, all_rounds)

                # Investment Amount is in column C (index 2), Accrued Interest is in column D (index 3)
                investment_col = self._col_letter(col_map['investment_amount'])
                interest_col = self._col_letter(col_map['accrued_interest'])
                
                # Get references to valuation fields
                valuation_basis_row = self._find_constant_row(round_idx, 'Valuation Basis:')
                valuation_basis_ref = f"B{valuation_basis_row + 1}" if valuation_basis_row is not None else None
                pre_money_ref = f"B{self._find_constant_row(round_idx, 'Pre-Money Valuation:') + 1}"
                post_money_ref = f"B{self._find_constant_row(round_idx, 'Post-Money Valuation:') + 1}"
                
                # Create dynamic formula that checks valuation_basis cell value
                if valuation_basis_ref:
                    # Dynamic formula using IF to check valuation_basis cell
                    pre_money_formula = valuation.create_shares_from_investment_premoney_formula(
                        f"{investment_col}{row + 1}", f"{interest_col}{row + 1}", pre_money_ref, pre_round_shares_ref
                    )
                    post_money_formula = valuation.create_shares_from_investment_postmoney_formula(
                        f"{investment_col}{row + 1}", f"{interest_col}{row + 1}", post_money_ref, pre_round_shares_ref
                    )
                    # Remove leading = from formulas for IF statement
                    pre_money_formula_no_eq = pre_money_formula.lstrip('=')
                    post_money_formula_no_eq = post_money_formula.lstrip('=')
                    shares_formula = f"=IF({valuation_basis_ref}=\"pre_money\", {pre_money_formula_no_eq}, {post_money_formula_no_eq})"
                else:
                    # Fallback to static value
                    valuation_basis = round_data.get('valuation_basis', 'pre_money')
                    if valuation_basis == 'pre_money':
                        shares_formula = valuation.create_shares_from_investment_premoney_formula(
                            f"{investment_col}{row + 1}", f"{interest_col}{row + 1}", pre_money_ref, pre_round_shares_ref
                        )
                    else:
                        shares_formula = valuation.create_shares_from_investment_postmoney_formula(
                            f"{investment_col}{row + 1}", f"{interest_col}{row + 1}", post_money_ref, pre_round_shares_ref
                        )

                # Write base shares (pro rata handled separately in Pro Rata Allocations sheet)
                sheet.write_formula(
                    row, col_map['shares'], shares_formula, self.formats.get('number'))

            elif calc_type == 'convertible':
                investment = instrument.get('investment_amount', 0)
                sheet.write(row, col_map['investment_amount'],
                            investment, self.formats.get('currency'))

                interest_start = instrument.get('interest_start_date', '')
                sheet.write(row, col_map['interest_start_date'],
                            interest_start, self.formats.get('date'))

                interest_end = instrument.get('interest_end_date', '')
                sheet.write(row, col_map['interest_end_date'],
                            interest_end, self.formats.get('date'))

                # Days passed
                days_passed = instrument.get('days_passed')
                if isinstance(days_passed, dict) and days_passed.get('is_calculated'):
                    formula = self.formula_resolver.resolve_feo(days_passed)
                    sheet.write_formula(
                        row, col_map['days_passed'], formula, self.formats.get('number'))
                else:
                    start_col = self._col_letter(col_map['interest_start_date'])
                    end_col = self._col_letter(col_map['interest_end_date'])
                    days_formula = interest.create_days_passed_formula(
                        f"{start_col}{row + 1}", f"{end_col}{row + 1}"
                    )
                    sheet.write_formula(
                        row, col_map['days_passed'], days_formula, self.formats.get('number'))

                interest_rate = instrument.get('interest_rate', 0)
                sheet.write(row, col_map['interest_rate'],
                            interest_rate, self.formats.get('percent'))

                interest_type = instrument.get('interest_type', 'simple')
                sheet.write(row, col_map['interest_type'],
                            interest_type, self.formats.get('text'))
                # Track this row for dropdown validation
                interest_type_rows.append(row)

                # Accrued interest
                accrued_interest = instrument.get('accrued_interest')
                if isinstance(accrued_interest, dict) and accrued_interest.get('is_calculated'):
                    formula = self.formula_resolver.resolve_feo(
                        accrued_interest)
                    sheet.write_formula(
                        row, col_map['accrued_interest'], formula, self.formats.get('currency'))
                else:
                    # Use dynamic column references based on col_map
                    principal_col = self._col_letter(col_map['investment_amount'])
                    rate_col = self._col_letter(col_map['interest_rate'])
                    start_col = self._col_letter(col_map['interest_start_date'])
                    end_col = self._col_letter(col_map['interest_end_date'])
                    interest_type_col = self._col_letter(col_map['interest_type'])
                    # Pass the cell reference for interest_type so formula updates dynamically
                    interest_formula = interest.create_accrued_interest_formula(
                        f"{principal_col}{row + 1}", f"{rate_col}{row + 1}",
                        f"{start_col}{row + 1}", f"{end_col}{row + 1}",
                        interest_type=interest_type,  # Keep for initial value
                        interest_type_ref=f"{interest_type_col}{row + 1}"  # Reference for dynamic formula
                    )
                    sheet.write_formula(
                        row, col_map['accrued_interest'], interest_formula, self.formats.get('currency'))

                discount_rate = instrument.get('discount_rate', 0)
                sheet.write(row, col_map['discount_rate'],
                            discount_rate, self.formats.get('percent'))

                # Calculated shares (base shares only - pro rata handled separately)
                # Price per share is already calculated based on valuation_cap_basis (pre_money/post_money/fixed)
                round_pps_ref = f"B{self._find_constant_row(round_idx, 'Price Per Share:') + 1}"

                # Get dynamic column references for convertible formula
                investment_col = self._col_letter(col_map['investment_amount'])
                interest_col = self._col_letter(col_map['accrued_interest'])
                discount_col = self._col_letter(col_map['discount_rate'])
                
                # Use price_per_share directly (it's already calculated based on valuation_cap_basis)
                # The shares formula just uses price_per_share with discount, without recalculating cap price
                shares_formula = valuation.create_convertible_shares_formula(
                    f"{investment_col}{row + 1}", f"{interest_col}{row + 1}", f"{discount_col}{row + 1}",
                    round_pps_ref
                )

                # Write base shares (pro rata handled separately in Pro Rata Allocations sheet)
                sheet.write_formula(
                    row, col_map['shares'], shares_formula, self.formats.get('number'))

            # Register instrument with DLM
            self.dlm.register_round_instrument(
                round_idx, inst_idx, round_data.get(
                    'name', ''), 'Rounds', row, col_map
            )

            current_row += 1

        # Add dropdown validation to interest_type column for convertible instruments
        if calc_type == 'convertible' and interest_type_rows:
            interest_type_col = col_map['interest_type']
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

        # Update shares_issued formula in constants section
        last_instrument_row = current_row - 1
        shares_col_letter = self._col_letter(col_map['shares'])
        shares_issued_row = self._find_constant_row(
            round_idx, 'Shares Issued:')
        if shares_issued_row is not None:
            shares_issued_formula = f"=SUM({shares_col_letter}{first_instrument_row + 1}:{shares_col_letter}{last_instrument_row + 1})"
            sheet.write_formula(
                shares_issued_row, 1, shares_issued_formula, self.formats.get('number'))

        # Create Excel Table for this round's instruments to enable structured references
        # Table range includes header row and all instrument rows
        if last_instrument_row >= first_instrument_row:
            header_row = first_instrument_row - 1
            end_col = len(headers) - 1
            columns_def = [{'header': h} for h in headers]
            table_name = self._get_round_table_name(round_idx, round_data)
            sheet.add_table(
                header_row,
                0,
                last_instrument_row,
                end_col,
                {
                    'name': table_name,
                    'columns': columns_def,
                    'style': 'Table Style Medium 2'
                }
            )
            # Update Shares Issued to sum the table's shares column using structured references
            if shares_issued_row is not None:
                shares_header = 'Shares' if calc_type == 'fixed_shares' else 'Calculated Shares'
                structured_sum = f"=SUM({table_name}[[#All],[{shares_header}]])"
                sheet.write_formula(
                    shares_issued_row, 1, structured_sum, self.formats.get('number'))

        return current_row


    def _get_pre_round_shares_ref(self, round_idx: int, round_data: Dict[str, Any],
                                  all_rounds: List[Dict[str, Any]]) -> str:
        """Get Excel reference for pre_round_shares."""
        round_name_key = round_data.get('name', '').replace(' ', '_')
        named_range = f"{round_name_key}_PreRoundShares"

        # Try to resolve from DLM, otherwise construct cell reference
        ref = self.dlm.resolve_reference(named_range)
        if ref:
            return ref

        # Fallback: construct cell reference (would need to track row)
        # For now, use named range directly
        return named_range

    def _get_shares_issued_ref(self, round_idx: int, round_data: Dict[str, Any],
                               all_rounds: List[Dict[str, Any]]) -> str:
        """Get Excel reference for shares_issued."""
        # Find the row where shares_issued constant is written
        row = self._find_constant_row(round_idx, 'Shares Issued:')
        if row is not None:
            return f"B{row + 1}"
        return "0"

    def _get_pro_rata_total_ref(self, round_idx: int, round_data: Dict[str, Any],
                                 all_rounds: List[Dict[str, Any]]) -> str:
        """Get Named Range for total pro rata shares for a given round."""
        round_name_key = round_data.get('name', '').replace(' ', '_')
        named_range = f"{round_name_key}_ProRataShares"
        # Prefer DLM resolve if available, otherwise return named range directly
        ref = self.dlm.resolve_reference(named_range)
        return ref or named_range

    def _find_constant_row(self, round_idx: int, constant_label: str) -> Optional[int]:
        """Find the row where a constant label appears."""
        if round_idx in self.round_constants_rows:
            return self.round_constants_rows[round_idx].get(constant_label)
        return None

    def _get_shares_column_letter(self, calc_type: str) -> str:
        """Get the column letter for shares based on calculation type."""
        if calc_type == 'fixed_shares':
            return 'D'  # 4th column (0-indexed: 3)
        elif calc_type == 'target_percentage':
            return 'D'  # 4th column (0-indexed: 3)
        elif calc_type == 'valuation_based':
            return 'E'  # 5th column (0-indexed: 4)
        elif calc_type == 'convertible':
            return 'K'  # 11th column (0-indexed: 10)
        return 'D'  # Default

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
    
    def get_shares_issued_ref(self, round_idx: int) -> Optional[str]:
        """Get Excel reference for shares_issued for a round."""
        row = self._find_constant_row(round_idx, 'Shares Issued:')
        if row is not None:
            return f"Rounds!B{row + 1}"
        return None
