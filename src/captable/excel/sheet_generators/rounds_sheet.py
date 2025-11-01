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
        sheet.write(current_row, 0, round_name, self.formats.get('label'))
        current_row += 1

        # Write constants section
        constants_row = current_row
        current_row = self._write_round_constants(
            sheet, round_idx, round_data, all_rounds, current_row
        )

        # Write instruments table
        instruments_start_row = current_row
        instruments = round_data.get('instruments', [])

        if instruments:
            current_row = self._write_instruments_table(
                sheet, round_idx, round_data, instruments, all_rounds, current_row
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
        instruments_end_row = current_row - 1 if instruments else instruments_start_row
        self.round_ranges[round_idx] = {
            'start_row': instruments_start_row + 1,  # +1 for header
            'end_row': instruments_end_row,
            'holder_col': 'A',  # Assuming holder_name is column A
            'shares_col': self._get_shares_column_letter(calc_type)
        }

        return current_row

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
            # Previous round's pre_round_shares + shares_issued
            prev_round = all_rounds[round_idx - 1]
            prev_pre_round_ref = self._get_pre_round_shares_ref(
                round_idx - 1, prev_round, all_rounds)
            prev_shares_issued_ref = self._get_shares_issued_ref(
                round_idx - 1, prev_round, all_rounds)
            formula = f"=IFERROR({prev_pre_round_ref} + {prev_shares_issued_ref}, 0)"
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
                current_row += 1

            if calc_type == 'convertible':
                valuation_cap_basis = round_data.get(
                    'valuation_cap_basis', 'pre_money')
                sheet.write(current_row, col_label,
                            'Valuation Cap Basis:', self.formats.get('label'))
                sheet.write(current_row, col_value,
                            valuation_cap_basis, self.formats.get('text'))
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
            if 'price_per_share' in round_data:
                sheet.write(current_row, col_label,
                            'Price Per Share:', self.formats.get('label'))
                self.round_constants_rows[round_idx]['Price Per Share:'] = current_row
                pps = round_data.get('price_per_share')
                if isinstance(pps, dict) and pps.get('is_calculated'):
                    formula = self.formula_resolver.resolve_feo(pps)
                    sheet.write_formula(
                        current_row, col_value, formula, self.formats.get('currency'))
                else:
                    sheet.write(current_row, col_value, pps or 0,
                                self.formats.get('currency'))
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
            headers = ['Holder Name', 'Class Name', 'Target %',
                       'Pro Rata Type', 'Pro Rata %', 'Calculated Shares']
            col_map = {'holder_name': 0, 'class_name': 1, 'target_percentage': 2,
                       'pro_rata_type': 3, 'pro_rata_percentage': 4, 'shares': 5}
        elif calc_type == 'valuation_based':
            headers = ['Holder Name', 'Class Name', 'Investment Amount', 'Accrued Interest',
                       'Pro Rata Type', 'Pro Rata %', 'Calculated Shares']
            col_map = {'holder_name': 0, 'class_name': 1, 'investment_amount': 2,
                       'accrued_interest': 3, 'pro_rata_type': 4, 'pro_rata_percentage': 5, 'shares': 6}
        elif calc_type == 'convertible':
            headers = ['Holder Name', 'Class Name', 'Investment Amount', 'Interest Start',
                       'Interest End', 'Days Passed', 'Interest Rate', 'Interest Type',
                       'Accrued Interest', 'Discount Rate', 'Pro Rata Type', 'Pro Rata %', 'Calculated Shares']
            col_map = {'holder_name': 0, 'class_name': 1, 'investment_amount': 2,
                       'interest_start_date': 3, 'interest_end_date': 4, 'days_passed': 5,
                       'interest_rate': 6, 'interest_type': 7, 'accrued_interest': 8,
                       'discount_rate': 9, 'pro_rata_type': 10, 'pro_rata_percentage': 11, 'shares': 12}
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

                # Pro rata fields
                pro_rata_type = instrument.get('pro_rata_type', 'none')
                sheet.write(row, col_map['pro_rata_type'],
                            pro_rata_type, self.formats.get('text'))

                pro_rata_pct = instrument.get('pro_rata_percentage')
                if pro_rata_pct is not None:
                    sheet.write(
                        row, col_map['pro_rata_percentage'], pro_rata_pct, self.formats.get('percent'))

                # Calculated shares
                pre_round_shares_ref = self._get_pre_round_shares_ref(
                    round_idx, round_data, all_rounds)
                # Target percentage is in column C (index 2)
                target_pct_col = self._col_letter(col_map['target_percentage'])
                base_shares_formula = valuation.create_shares_from_percentage_formula(
                    f"{target_pct_col}{row + 1}", pre_round_shares_ref
                )

                # Apply pro rata if needed
                shares_formula = self._apply_pro_rata_to_shares(
                    sheet, row, col_map, instrument, base_shares_formula,
                    round_idx, round_data, all_rounds, calc_type
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

                # Pro rata fields
                pro_rata_type = instrument.get('pro_rata_type', 'none')
                sheet.write(row, col_map['pro_rata_type'],
                            pro_rata_type, self.formats.get('text'))

                pro_rata_pct = instrument.get('pro_rata_percentage')
                if pro_rata_pct is not None:
                    sheet.write(
                        row, col_map['pro_rata_percentage'], pro_rata_pct, self.formats.get('percent'))

                # Calculated shares
                valuation_basis = round_data.get(
                    'valuation_basis', 'pre_money')
                pre_round_shares_ref = self._get_pre_round_shares_ref(
                    round_idx, round_data, all_rounds)

                # Investment Amount is in column C (index 2), Accrued Interest is in column D (index 3)
                investment_col = self._col_letter(col_map['investment_amount'])
                interest_col = self._col_letter(col_map['accrued_interest'])
                
                if valuation_basis == 'pre_money':
                    pre_money_ref = f"B{self._find_constant_row(round_idx, 'Pre-Money Valuation:') + 1}"
                    base_shares_formula = valuation.create_shares_from_investment_premoney_formula(
                        f"{investment_col}{row + 1}", f"{interest_col}{row + 1}", pre_money_ref, pre_round_shares_ref
                    )
                else:
                    post_money_ref = f"B{self._find_constant_row(round_idx, 'Post-Money Valuation:') + 1}"
                    base_shares_formula = valuation.create_shares_from_investment_postmoney_formula(
                        f"{investment_col}{row + 1}", f"{interest_col}{row + 1}", post_money_ref, pre_round_shares_ref
                    )

                # Apply pro rata if needed
                shares_formula = self._apply_pro_rata_to_shares(
                    sheet, row, col_map, instrument, base_shares_formula,
                    round_idx, round_data, all_rounds, calc_type
                )
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
                    days_formula = interest.create_days_passed_formula(
                        f"D{row + 1}", f"E{row + 1}"
                    )
                    sheet.write_formula(
                        row, col_map['days_passed'], days_formula, self.formats.get('number'))

                interest_rate = instrument.get('interest_rate', 0)
                sheet.write(row, col_map['interest_rate'],
                            interest_rate, self.formats.get('percent'))

                interest_type = instrument.get('interest_type', 'simple')
                sheet.write(row, col_map['interest_type'],
                            interest_type, self.formats.get('text'))

                # Accrued interest
                accrued_interest = instrument.get('accrued_interest')
                if isinstance(accrued_interest, dict) and accrued_interest.get('is_calculated'):
                    formula = self.formula_resolver.resolve_feo(
                        accrued_interest)
                    sheet.write_formula(
                        row, col_map['accrued_interest'], formula, self.formats.get('currency'))
                else:
                    interest_formula = interest.create_accrued_interest_formula(
                        f"C{row + 1}", f"G{row + 1}", f"D{row + 1}", f"E{row + 1}", interest_type
                    )
                    sheet.write_formula(
                        row, col_map['accrued_interest'], interest_formula, self.formats.get('currency'))

                discount_rate = instrument.get('discount_rate', 0)
                sheet.write(row, col_map['discount_rate'],
                            discount_rate, self.formats.get('percent'))

                # Pro rata fields
                pro_rata_type = instrument.get('pro_rata_type', 'none')
                sheet.write(row, col_map['pro_rata_type'],
                            pro_rata_type, self.formats.get('text'))

                pro_rata_pct = instrument.get('pro_rata_percentage')
                if pro_rata_pct is not None:
                    sheet.write(
                        row, col_map['pro_rata_percentage'], pro_rata_pct, self.formats.get('percent'))

                # Calculated shares
                valuation_cap_basis = round_data.get(
                    'valuation_cap_basis', 'pre_money')
                pre_round_shares_ref = self._get_pre_round_shares_ref(
                    round_idx, round_data, all_rounds)

                if valuation_cap_basis == 'pre_money':
                    valuation_cap_ref = f"B{self._find_constant_row(round_idx, 'Pre-Money Valuation:') + 1}"
                else:
                    valuation_cap_ref = f"B{self._find_constant_row(round_idx, 'Post-Money Valuation:') + 1}"

                round_pps_ref = f"B{self._find_constant_row(round_idx, 'Price Per Share:') + 1}"

                base_shares_formula = valuation.create_convertible_shares_formula(
                    f"C{row + 1}", f"I{row + 1}", f"J{row + 1}",
                    round_pps_ref, valuation_cap_ref, pre_round_shares_ref
                )

                # Apply pro rata if needed
                shares_formula = self._apply_pro_rata_to_shares(
                    sheet, row, col_map, instrument, base_shares_formula,
                    round_idx, round_data, all_rounds, calc_type
                )
                sheet.write_formula(
                    row, col_map['shares'], shares_formula, self.formats.get('number'))

            # Register instrument with DLM
            self.dlm.register_round_instrument(
                round_idx, inst_idx, round_data.get(
                    'name', ''), 'Rounds', row, col_map
            )

            current_row += 1

        # Update shares_issued formula in constants section
        last_instrument_row = current_row - 1
        shares_col_letter = self._col_letter(col_map['shares'])
        shares_issued_row = self._find_constant_row(
            round_idx, 'Shares Issued:')
        if shares_issued_row is not None:
            shares_issued_formula = f"=SUM({shares_col_letter}{first_instrument_row + 1}:{shares_col_letter}{last_instrument_row + 1})"
            sheet.write_formula(
                shares_issued_row, 1, shares_issued_formula, self.formats.get('number'))

        return current_row

    def _apply_pro_rata_to_shares(
        self,
        sheet: xlsxwriter.worksheet.Worksheet,
        row: int,
        col_map: Dict[str, int],
        instrument: Dict[str, Any],
        base_shares_formula: str,
        round_idx: int,
        round_data: Dict[str, Any],
        all_rounds: List[Dict[str, Any]],
        calc_type: str
    ) -> str:
        """
        Apply pro rata or super pro rata calculations to base shares formula.

        Returns updated formula string.
        """
        pro_rata_type = instrument.get('pro_rata_type', 'none')

        if pro_rata_type == 'none':
            # No pro rata - use base formula as-is
            return base_shares_formula

        # Remove leading '=' from base formula for manipulation
        base_formula = base_shares_formula.lstrip('=')

        # Calculate round shares issued (sum of base shares without pro rata)
        pre_round_shares_ref = self._get_pre_round_shares_ref(
            round_idx, round_data, all_rounds)
        shares_col_letter = self._col_letter(col_map['shares'])
        first_inst_row = row  # Approximate - would need to track better
        last_inst_row = row  # Approximate
        new_round_shares_ref = f"SUM({shares_col_letter}{first_inst_row + 1}:{shares_col_letter}{last_inst_row + 1})"

        if pro_rata_type == 'standard':
            # Pro rata: maintain ownership percentage
            # Need holder's current ownership percentage
            # For now, calculate from holder's current shares / pre_round_shares
            # This is simplified - ideally we'd reference progression sheet
            # Would need progression sheet reference
            holder_current_shares_ref = f"'Cap Table Progression'!TODO"
            holder_ownership_pct = f"({holder_current_shares_ref} / {pre_round_shares_ref})"

            pro_rata_shares_formula = ownership.create_pro_rata_shares_formula(
                holder_ownership_pct, new_round_shares_ref
            )

            # Use MAX of base shares or pro rata shares
            return f"=MAX({base_formula}, {pro_rata_shares_formula.lstrip('=')})"

        elif pro_rata_type == 'super':
            # Super pro rata: achieve target ownership percentage
            pro_rata_pct = instrument.get('pro_rata_percentage', 0)
            pro_rata_pct_ref = self._col_letter(
                col_map['pro_rata_percentage']) + str(row + 1)

            # Need holder's current shares
            # Would need progression sheet reference
            holder_current_shares_ref = f"'Cap Table Progression'!TODO"

            super_pro_rata_formula = ownership.create_super_pro_rata_shares_formula(
                pro_rata_pct_ref, pre_round_shares_ref, holder_current_shares_ref
            )

            # Use MAX of base shares or super pro rata shares
            return f"=MAX({base_formula}, {super_pro_rata_formula.lstrip('=')})"

        return base_shares_formula

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
            return 'F'  # 6th column (0-indexed: 5)
        elif calc_type == 'valuation_based':
            return 'G'  # 7th column (0-indexed: 6)
        elif calc_type == 'convertible':
            return 'M'  # 13th column (0-indexed: 12)
        return 'D'  # Default

    def get_round_ranges(self) -> Dict[int, Dict[str, Any]]:
        """Get round ranges for progression sheet reference."""
        return self.round_ranges
