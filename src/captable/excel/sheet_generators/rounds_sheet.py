"""
Rounds Sheet Generator - Round-Based Architecture

Creates the Rounds sheet showing financing rounds vertically, each with:
- Round heading
- Round constants (date, calculation_type, valuations, price_per_share)
- Instruments table with columns based on calculation_type
- Spacing between rounds

This is the SOURCE OF TRUTH for all instruments in the round-based architecture.
"""

from typing import Dict, Any, List, Tuple
import xlsxwriter

from ..base import BaseSheetGenerator
from ..table_builder import TableBuilder


class RoundsSheetGenerator(BaseSheetGenerator):
    """
    Generates the Rounds sheet with vertical round layout.
    
    Each round is displayed as:
    1. Round heading (name)
    2. Constants section (date, calculation_type, valuations)
    3. Instruments table (columns vary by calculation_type)
    4. Spacing before next round
    """
    
    def _get_sheet_name(self) -> str:
        """Returns 'Rounds'."""
        return "Rounds"
    
    def generate(self) -> xlsxwriter.worksheet.Worksheet:
        """
        Generate the Rounds sheet with vertical round layout.
        
        Returns:
            Worksheet instance
        """
        sheet = self.workbook.add_worksheet('Rounds')
        self.sheet = sheet
        
        rounds = self.data.get('rounds', [])
        current_row = 0
        
        # Track calculated_shares cells and constants rows for each round
        self.round_shares_info = {}
        self.round_constants_rows = {}
        # Track round ranges for lookup table
        self.round_ranges = {}  # {round_idx: {'start_row': X, 'end_row': Y, 'holder_col': 'A', 'shares_col': 'D'}}
        # Track row positions for key round constants
        self.round_constant_positions = {}  # {round_idx: {'pre_money_row': X, 'post_money_row': Y, 'pre_round_shares_row': Z, 'pps_row': W}}
        
        for round_idx, round_data in enumerate(rounds):
            # Generate this round's section
            end_row, shares_info, constants_row = self._generate_round_section(
                sheet, round_data, round_idx, current_row
            )
            
            # Store info for this round
            self.round_shares_info[round_idx] = shares_info
            self.round_constants_rows[round_idx] = constants_row
            
            # Track range for this round
            instruments_start_row = self.round_constants_rows[round_idx] + 4  # After constants
            instruments_end_row = end_row - 1  # Before spacing
            calc_type = round_data.get('calculation_type', 'fixed_shares')
            shares_col = self._get_shares_column_letter(calc_type)
            
            self.round_ranges[round_idx] = {
                'start_row': instruments_start_row + 1,  # +1 for header row, Excel is 1-based
                'end_row': instruments_end_row + 1,
                'holder_col': 'A',
                'shares_col': shares_col
            }
            
            # Add spacing before next round
            current_row = end_row + 3
        
        # Set column widths
        sheet.set_column(0, 0, 25)  # Column A (labels/holder names)
        sheet.set_column(1, 10, 18)  # Other columns
        
        return sheet
    
    def _generate_round_section(
        self,
        sheet: xlsxwriter.worksheet.Worksheet,
        round_data: Dict[str, Any],
        round_idx: int,
        start_row: int
    ) -> Tuple[int, Dict[str, Any], int]:
        """
        Generate a complete round section.
        
        Args:
            sheet: Worksheet to write to
            round_data: Round data dictionary
            round_idx: Index of the round
            start_row: Starting row for this round section
            
        Returns:
            Tuple of (ending row, shares info dict, constants_start_row)
        """
        current_row = start_row
        round_name = round_data.get('name', f'Round {round_idx + 1}')
        calc_type = round_data.get('calculation_type', 'fixed_shares')
        
        # 1. Round heading
        sheet.write(current_row, 0, f"Round: {round_name}", self.formats.get('header'))
        current_row += 1
        
        # 2. Constants section
        constants_start_row = current_row
        current_row = self._write_round_constants(
            sheet, round_data, round_idx, current_row
        )
        current_row += 1  # Spacing after constants
        
        # 3. Instruments table
        instruments = round_data.get('instruments', [])
        instruments_start_row = current_row
        
        shares_info = {}
        if instruments:
            current_row, shares_info = self._write_instruments_table(
                sheet, round_data, round_idx, instruments, current_row
            )
        else:
            sheet.write(current_row, 0, "No instruments in this round", self.formats.get('text'))
            current_row += 1
        
        # Register round section in DLM
        self.dlm.register_round_section(
            round_name, 'Rounds', constants_start_row, instruments_start_row
        )
        
        # Register named range for pre_round_shares
        self._register_pre_round_shares_named_range(round_data, round_idx, constants_start_row)
        
        return current_row, shares_info, constants_start_row
    
    def _write_round_constants(
        self,
        sheet: xlsxwriter.worksheet.Worksheet,
        round_data: Dict[str, Any],
        round_idx: int,
        start_row: int
    ) -> int:
        """
        Write round constants (date, calculation_type, valuations, etc.).
        
        Args:
            sheet: Worksheet
            round_data: Round data
            round_idx: Round index
            start_row: Starting row
            
        Returns:
            Ending row
        """
        current_row = start_row
        calc_type = round_data.get('calculation_type', '')
        
        # Initialize position tracking for this round
        self.round_constant_positions[round_idx] = {}
        
        # Date
        round_date = round_data.get('round_date', '')
        sheet.write(current_row, 0, "Date:", self.formats.get('label'))
        sheet.write(current_row, 1, round_date, self.formats.get('date'))
        current_row += 1
        
        # Calculation Type
        sheet.write(current_row, 0, "Calculation Type:", self.formats.get('label'))
        sheet.write(current_row, 1, calc_type, self.formats.get('text'))
        # Add dropdown for calculation_type
        sheet.data_validation(current_row, 1, current_row, 1, {
            'validate': 'list',
            'source': ['fixed_shares', 'target_percentage', 'convertible', 'valuation_based']
        })
        current_row += 1
        
        # Pre-Round Shares (calculated)
        sheet.write(current_row, 0, "Pre-Round Shares:", self.formats.get('label'))
        pre_round_formula = self._get_pre_round_shares_formula(round_idx, round_data)
        sheet.write_formula(current_row, 1, pre_round_formula, self.formats.get('number'))
        pre_round_shares_row = current_row
        self.round_constant_positions[round_idx]['pre_round_shares_row'] = current_row
        current_row += 1
        
        # Valuation fields (if applicable)
        if calc_type in ['valuation_based', 'convertible']:
            # Pre-Money Valuation
            pre_money = round_data.get('pre_money_valuation')
            if pre_money is not None:
                sheet.write(current_row, 0, "Pre-Money Valuation:", self.formats.get('label'))
                sheet.write(current_row, 1, pre_money, self.formats.get('currency'))
                self.round_constant_positions[round_idx]['pre_money_row'] = current_row
                current_row += 1
            
            # Post-Money Valuation
            post_money = round_data.get('post_money_valuation')
            if post_money is not None:
                sheet.write(current_row, 0, "Post-Money Valuation:", self.formats.get('label'))
                sheet.write(current_row, 1, post_money, self.formats.get('currency'))
                self.round_constant_positions[round_idx]['post_money_row'] = current_row
                current_row += 1
            
            # Price Per Share (calculated if both pre_money and pre_round_shares exist)
            pps = round_data.get('price_per_share')
            sheet.write(current_row, 0, "Price Per Share:", self.formats.get('label'))
            
            # Calculate from pre-money valuation and pre-round shares if available
            if (pre_money is not None and 
                'pre_round_shares_row' in self.round_constant_positions[round_idx] and
                pps is None):  # Only calculate if not explicitly provided
                pre_money_ref = f"Rounds!$B${self.round_constant_positions[round_idx].get('pre_money_row', current_row) + 1}"
                pre_round_ref = f"Rounds!$B${pre_round_shares_row + 1}"
                pps_formula = f"=IFERROR({pre_money_ref} / {pre_round_ref}, 0)"
                sheet.write_formula(current_row, 1, pps_formula, self.formats.get('currency'))
            elif pps is not None:
                sheet.write(current_row, 1, pps, self.formats.get('currency'))
            else:
                sheet.write(current_row, 1, 0, self.formats.get('currency'))
            
            self.round_constant_positions[round_idx]['pps_row'] = current_row
            current_row += 1
        
        # Valuation Basis (for valuation_based)
        if calc_type == 'valuation_based':
            valuation_basis = round_data.get('valuation_basis', 'post_money')
            sheet.write(current_row, 0, "Valuation Basis:", self.formats.get('label'))
            sheet.write(current_row, 1, valuation_basis, self.formats.get('text'))
            # Add dropdown for valuation_basis
            sheet.data_validation(current_row, 1, current_row, 1, {
                'validate': 'list',
                'source': ['pre_money', 'post_money']
            })
            current_row += 1
        
        # Valuation Cap Basis (for convertible)
        if calc_type == 'convertible':
            valuation_cap_basis = round_data.get('valuation_cap_basis')
            if valuation_cap_basis:
                sheet.write(current_row, 0, "Valuation Cap Basis:", self.formats.get('label'))
                sheet.write(current_row, 1, valuation_cap_basis, self.formats.get('text'))
                # Add dropdown for valuation_cap_basis
                sheet.data_validation(current_row, 1, current_row, 1, {
                    'validate': 'list',
                    'source': ['pre_money', 'post_money']
                })
                current_row += 1
        
        return current_row
    
    def _write_instruments_table(
        self,
        sheet: xlsxwriter.worksheet.Worksheet,
        round_data: Dict[str, Any],
        round_idx: int,
        instruments: List[Dict[str, Any]],
        start_row: int
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Write instruments table with columns based on calculation_type.
        
        Args:
            sheet: Worksheet
            round_data: Round data
            round_idx: Round index
            instruments: List of instruments
            start_row: Starting row
            
        Returns:
            Tuple of (ending row, shares_info dict with calculated_shares cell refs)
        """
        calc_type = round_data.get('calculation_type', 'fixed_shares')
        round_name = round_data.get('name', f'Round {round_idx + 1}')
        
        # Get columns based on calculation type
        columns = self._get_columns_for_calc_type(calc_type)
        
        # Find which column has calculated_shares
        shares_col_name = None
        if 'calculated_shares' in columns:
            shares_col_name = 'calculated_shares'
        elif 'shares' in columns:
            shares_col_name = 'shares'
        elif 'initial_quantity' in columns:
            shares_col_name = 'initial_quantity'
        
        # Write table header
        for col_idx, col_name in enumerate(columns):
            sheet.write(start_row, col_idx, col_name.replace('_', ' ').title(), 
                       self.formats.get('header'))
        
        # Find shares column index
        shares_col_idx = columns.index(shares_col_name) if shares_col_name else -1
        
        # Write instrument rows
        current_row = start_row + 1
        shares_info = {'rows': []}
        
        for inst_idx, instrument in enumerate(instruments):
            row_data = self._prepare_instrument_row_data(
                instrument, calc_type, round_data, round_idx, inst_idx
            )
            
            for col_idx, col_name in enumerate(columns):
                value = row_data.get(col_name)
                
                # Determine format and write value
                if value == 'FORMULA':
                    # Will write formula later
                    sheet.write(current_row, col_idx, 0, self.formats.get('number'))
                elif col_name in ['investment_amount', 'accrued_interest']:
                    sheet.write(current_row, col_idx, value or 0, self.formats.get('currency'))
                elif col_name in ['shares', 'initial_quantity', 'calculated_shares']:
                    sheet.write(current_row, col_idx, value or 0, self.formats.get('number'))
                elif col_name in ['target_percentage', 'discount_rate', 'interest_rate']:
                    sheet.write(current_row, col_idx, value or 0, self.formats.get('percent'))
                elif col_name in ['interest_start_date', 'interest_end_date', 'acquisition_date']:
                    sheet.write(current_row, col_idx, value or '', self.formats.get('date'))
                elif col_name == 'interest_type':
                    sheet.write(current_row, col_idx, value or '', self.formats.get('text'))
                    # Add dropdown for interest_type
                    sheet.data_validation(current_row, col_idx, current_row, col_idx, {
                        'validate': 'list',
                        'source': ['simple', 'compound_yearly', 'compound_monthly', 'compound_daily', 'no_interest']
                    })
                elif col_name == 'days_passed':
                    # This will be a formula, so don't write anything here
                    pass
                else:
                    sheet.write(current_row, col_idx, value or '', self.formats.get('text'))
            
            # Store shares cell reference
            if shares_col_idx >= 0:
                col_letter = self._col_letter(shares_col_idx)
                shares_cell = f"Rounds!${col_letter}${current_row + 1}"
                shares_info['rows'].append(shares_cell)
            
            # Register instrument in DLM
            col_indices = {col: idx for idx, col in enumerate(columns)}
            self.dlm.register_round_instrument(
                round_idx, inst_idx, round_name, 'Rounds', current_row, col_indices
            )
            
            current_row += 1
        
        # Write formulas for calculated fields
        self._write_instrument_formulas(
            sheet, round_data, round_idx, instruments, start_row + 1, columns
        )
        
        return current_row, shares_info
    
    def _get_columns_for_calc_type(self, calc_type: str) -> List[str]:
        """
        Get column names based on calculation type.
        
        Args:
            calc_type: Calculation type
            
        Returns:
            List of column names
        """
        if calc_type == 'fixed_shares':
            return ['holder_name', 'class_name', 'acquisition_date', 'shares']
        
        elif calc_type == 'target_percentage':
            return ['holder_name', 'class_name', 'target_percentage', 'calculated_shares']
        
        elif calc_type == 'valuation_based':
            return ['holder_name', 'class_name', 'investment_amount', 
                   'accrued_interest', 'calculated_shares']
        
        elif calc_type == 'convertible':
            return ['holder_name', 'class_name', 'investment_amount', 
                   'interest_start_date', 'interest_end_date', 'days_passed',
                   'interest_rate', 'interest_type', 'accrued_interest', 
                   'discount_rate', 'calculated_shares']
        
        else:
            return ['holder_name', 'class_name', 'shares']
    
    def _prepare_instrument_row_data(
        self,
        instrument: Dict[str, Any],
        calc_type: str,
        round_data: Dict[str, Any],
        round_idx: int,
        inst_idx: int
    ) -> Dict[str, Any]:
        """
        Prepare row data for an instrument based on calculation type.
        
        Args:
            instrument: Instrument data
            calc_type: Calculation type
            round_data: Round data
            round_idx: Round index
            inst_idx: Instrument index
            
        Returns:
            Dictionary of row data
        """
        row_data = {
            'holder_name': instrument.get('holder_name', ''),
            'class_name': instrument.get('class_name', ''),
        }
        
        if calc_type == 'fixed_shares':
            row_data['acquisition_date'] = instrument.get('acquisition_date', '')
            row_data['shares'] = instrument.get('initial_quantity', 0)
        
        elif calc_type == 'target_percentage':
            row_data['target_percentage'] = instrument.get('target_percentage', 0)
            row_data['calculated_shares'] = 'FORMULA'  # Will be calculated
        
        elif calc_type == 'valuation_based':
            row_data['investment_amount'] = instrument.get('investment_amount', 0)
            row_data['accrued_interest'] = instrument.get('accrued_interest', 0)
            row_data['calculated_shares'] = 'FORMULA'  # Will be calculated
        
        elif calc_type == 'convertible':
            row_data['investment_amount'] = instrument.get('investment_amount', 0)
            row_data['interest_start_date'] = instrument.get('interest_start_date', '')
            row_data['interest_end_date'] = instrument.get('interest_end_date', '')
            row_data['days_passed'] = 'FORMULA'  # Will be calculated
            row_data['interest_rate'] = instrument.get('interest_rate', 0)
            row_data['interest_type'] = instrument.get('interest_type', 'simple')
            row_data['accrued_interest'] = 'FORMULA'  # Will be calculated
            row_data['discount_rate'] = instrument.get('discount_rate', 0)
            row_data['calculated_shares'] = 'FORMULA'  # Will be calculated
        
        return row_data
    
    def _write_instrument_formulas(
        self,
        sheet: xlsxwriter.worksheet.Worksheet,
        round_data: Dict[str, Any],
        round_idx: int,
        instruments: List[Dict[str, Any]],
        start_row: int,
        columns: List[str]
    ) -> None:
        """
        Write formulas for calculated instrument fields.
        
        Args:
            sheet: Worksheet
            round_data: Round data
            round_idx: Round index
            instruments: List of instruments
            start_row: Starting row of instrument data
            columns: List of column names
        """
        calc_type = round_data.get('calculation_type')
        round_name = round_data.get('name', f'Round {round_idx + 1}')
        
        for inst_idx, instrument in enumerate(instruments):
            row = start_row + inst_idx
            
            if calc_type == 'target_percentage':
                self._write_target_percentage_formula(
                    sheet, round_data, round_idx, row, columns
                )
            
            elif calc_type == 'valuation_based':
                self._write_valuation_based_formula(
                    sheet, round_data, round_idx, inst_idx, row, columns, instrument
                )
            
            elif calc_type == 'convertible':
                self._write_convertible_formulas(
                    sheet, round_data, round_idx, inst_idx, row, columns, instrument
                )
    
    def _write_target_percentage_formula(
        self,
        sheet: xlsxwriter.worksheet.Worksheet,
        round_data: Dict[str, Any],
        round_idx: int,
        row: int,
        columns: List[str]
    ) -> None:
        """Write formula for target_percentage calculation."""
        target_pct_col = columns.index('target_percentage')
        shares_col = columns.index('calculated_shares')
        
        target_pct_ref = self._col_letter(target_pct_col) + str(row + 1)
        
        # Get pre_round_shares reference
        round_name = round_data.get('name', '').replace(' ', '_')
        pre_round_ref = f"{round_name}_PreRoundShares"
        
        # Formula: target_percentage * pre_round_shares / (1 - target_percentage)
        # Wrap with ROUND to ensure integer shares
        formula = f"=ROUND({target_pct_ref} * {pre_round_ref} / (1 - {target_pct_ref}), 0)"
        sheet.write_formula(row, shares_col, formula, self.formats.get('number'))
    
    def _write_valuation_based_formula(
        self,
        sheet: xlsxwriter.worksheet.Worksheet,
        round_data: Dict[str, Any],
        round_idx: int,
        inst_idx: int,
        row: int,
        columns: List[str],
        instrument: Dict[str, Any]
    ) -> None:
        """Write formula for valuation_based calculation."""
        investment_col = columns.index('investment_amount')
        interest_col = columns.index('accrued_interest')
        shares_col = columns.index('calculated_shares')
        
        investment_ref = self._col_letter(investment_col) + str(row + 1)
        interest_ref = self._col_letter(interest_col) + str(row + 1)
        
        # Get valuation_basis (default to post_money if not specified)
        valuation_basis = round_data.get('valuation_basis', 'post_money')
        
        # Get references to round constants
        positions = self.round_constant_positions.get(round_idx, {})
        pre_round_ref = f"Rounds!$B${positions.get('pre_round_shares_row', 0) + 1}"
        pps_ref = f"Rounds!$B${positions.get('pps_row', 0) + 1}"
        pre_money_ref = f"Rounds!$B${positions.get('pre_money_row', 0) + 1}"
        
        if valuation_basis == 'pre_money':
            # Pre-money calculation: shares = (investment + interest) * pre_round_shares / (pre_money + investment + interest)
            formula = f"=ROUND(({investment_ref} + {interest_ref}) * {pre_round_ref} / ({pre_money_ref} + {investment_ref} + {interest_ref}), 0)"
        else:
            # Post-money calculation: shares = (investment + interest) / price_per_share
            # Note: price_per_share should be calculated as pre_money / pre_round_shares for this to work correctly
            formula = f"=ROUND(({investment_ref} + {interest_ref}) / {pps_ref}, 0)"
        
        sheet.write_formula(row, shares_col, formula, self.formats.get('number'))
    
    def _write_convertible_formulas(
        self,
        sheet: xlsxwriter.worksheet.Worksheet,
        round_data: Dict[str, Any],
        round_idx: int,
        inst_idx: int,
        row: int,
        columns: List[str],
        instrument: Dict[str, Any]
    ) -> None:
        """Write formulas for convertible calculation."""
        # Days passed formula
        if 'days_passed' in columns:
            start_col = columns.index('interest_start_date')
            end_col = columns.index('interest_end_date')
            days_col = columns.index('days_passed')
            
            start_ref = self._col_letter(start_col) + str(row + 1)
            end_ref = self._col_letter(end_col) + str(row + 1)
            
            formula = f"={end_ref} - {start_ref}"
            sheet.write_formula(row, days_col, formula, self.formats.get('number'))
        
        # Accrued interest formula (depends on interest_type)
        if 'accrued_interest' in columns:
            investment_col = columns.index('investment_amount')
            rate_col = columns.index('interest_rate')
            days_col = columns.index('days_passed')
            interest_col = columns.index('accrued_interest')
            interest_type_col = columns.index('interest_type')
            
            investment_ref = self._col_letter(investment_col) + str(row + 1)
            rate_ref = self._col_letter(rate_col) + str(row + 1)
            days_ref = self._col_letter(days_col) + str(row + 1)
            interest_type_ref = self._col_letter(interest_type_col) + str(row + 1)
            
            # Create nested IF formula based on interest_type
            # IF(interest_type="no_interest", 0, IF(interest_type="simple", A*R*D/365, compound formula))
            # For compound: A * ((1 + R/n)^(n*t) - 1) where n is compounding frequency
            
            # Simple interest: investment * rate * (days / 365)
            simple_formula = f"{investment_ref} * {rate_ref} * ({days_ref} / 365)"
            
            # Compound yearly: investment * ((1 + rate)^(days/365) - 1)
            compound_yearly_formula = f"{investment_ref} * ((1 + {rate_ref})^({days_ref}/365) - 1)"
            
            # Compound monthly: investment * ((1 + rate/12)^(12*days/365) - 1)
            compound_monthly_formula = f"{investment_ref} * ((1 + {rate_ref}/12)^(12*{days_ref}/365) - 1)"
            
            # Compound daily: investment * ((1 + rate/365)^(days) - 1)
            compound_daily_formula = f"{investment_ref} * ((1 + {rate_ref}/365)^({days_ref}) - 1)"
            
            # Build nested IF formula
            formula = f'''=IF({interest_type_ref}="no_interest", 0, IF({interest_type_ref}="simple", {simple_formula}, IF({interest_type_ref}="compound_yearly", {compound_yearly_formula}, IF({interest_type_ref}="compound_monthly", {compound_monthly_formula}, {compound_daily_formula}))))'''
            
            sheet.write_formula(row, interest_col, formula, self.formats.get('currency'))
        
        # Calculated shares formula
        if 'calculated_shares' in columns:
            investment_col = columns.index('investment_amount')
            interest_col = columns.index('accrued_interest')
            discount_col = columns.index('discount_rate')
            shares_col = columns.index('calculated_shares')
            
            investment_ref = self._col_letter(investment_col) + str(row + 1)
            interest_ref = self._col_letter(interest_col) + str(row + 1)
            discount_ref = self._col_letter(discount_col) + str(row + 1)
            
            # Get references to round constants
            positions = self.round_constant_positions.get(round_idx, {})
            pps_ref = f"Rounds!$B${positions.get('pps_row', 0) + 1}"
            pre_money_ref = f"Rounds!$B${positions.get('pre_money_row', 0) + 1}"
            post_money_ref = f"Rounds!$B${positions.get('post_money_row', 0) + 1}"
            pre_round_ref = f"Rounds!$B${positions.get('pre_round_shares_row', 0) + 1}"
            
            # Determine valuation cap (based on valuation_cap_basis)
            valuation_cap_basis = round_data.get('valuation_cap_basis', 'pre_money')
            if valuation_cap_basis == 'pre_money' and pre_money_ref != f"Rounds!$B$0":
                valuation_cap_ref = pre_money_ref
            elif valuation_cap_basis == 'post_money' and post_money_ref != f"Rounds!$B$0":
                valuation_cap_ref = post_money_ref
            else:
                valuation_cap_ref = pre_money_ref if pre_money_ref != f"Rounds!$B$0" else post_money_ref
            
            # Conversion price = MIN(round_pps * (1 - discount), valuation_cap / pre_round_shares)
            # If pps is not available, fall back to just the cap-based price
            if pps_ref != f"Rounds!$B$0":
                discounted_price = f"({pps_ref} * (1 - {discount_ref}))"
                cap_price = f"({valuation_cap_ref} / {pre_round_ref})"
                conversion_price = f"MIN({discounted_price}, {cap_price})"
            else:
                conversion_price = f"({valuation_cap_ref} / {pre_round_ref})"
            
            # Shares = (investment + interest) / conversion_price
            # Wrap with ROUND to ensure integer shares
            formula = f"=ROUND(({investment_ref} + {interest_ref}) / {conversion_price}, 0)"
            sheet.write_formula(row, shares_col, formula, self.formats.get('number'))
    
    def _get_pre_round_shares_formula(self, round_idx: int, round_data: Dict[str, Any]) -> str:
        """
        Get pre_round_shares formula.
        
        Pre-round shares = Pre-round shares of previous round + Shares issued in previous round
        
        Args:
            round_idx: Round index
            round_data: Round data
            
        Returns:
            Excel formula string
        """
        if round_idx == 0:
            # First round: no previous shares
            return "=0"
        else:
            # For round_idx > 0: previous pre_round_shares + previous round's issued shares
            prev_round_idx = round_idx - 1
            
            # Get the cell reference for previous round's pre_round_shares
            # Pre-round shares is in column B, at row = constants_start_row + 2 (Date, Calc Type, then Pre-Round Shares)
            if prev_round_idx in self.round_constants_rows:
                prev_constants_row = self.round_constants_rows[prev_round_idx]
                prev_pre_round_row = prev_constants_row + 2  # Date, Calc Type, Pre-Round Shares
                prev_pre_round_cell = f"Rounds!$B${prev_pre_round_row + 1}"  # +1 for 0-based to 1-based
            else:
                # Fallback - calculate dynamically
                prev_constants_row = self._get_constants_row_for_round(prev_round_idx)
                prev_pre_round_cell = f"Rounds!$B${prev_constants_row + 2 + 1}"
            
            # Get previous round's issued shares
            if prev_round_idx in self.round_shares_info:
                prev_shares_info = self.round_shares_info[prev_round_idx]
                prev_shares_cells = prev_shares_info.get('rows', [])
                
                if not prev_shares_cells:
                    # No instruments in previous round
                    return f"={prev_pre_round_cell}"
                elif len(prev_shares_cells) == 1:
                    return f"={prev_pre_round_cell}+{prev_shares_cells[0]}"
                else:
                    # Sum all previous round's shares
                    return f"={prev_pre_round_cell}+SUM({','.join(prev_shares_cells)})"
            else:
                # Fallback
                return f"={prev_pre_round_cell}"
    
    def _register_pre_round_shares_named_range(
        self,
        round_data: Dict[str, Any],
        round_idx: int,
        constants_row: int
    ) -> None:
        """
        Register named range for pre_round_shares.
        
        Args:
            round_data: Round data
            round_idx: Round index
            constants_row: Row where constants start
        """
        round_name = round_data.get('name', f'Round {round_idx + 1}')
        round_name_clean = round_name.replace(' ', '_')
        
        # Pre_round_shares is at constants_row + 2 (Date, Calc Type, then Pre-Round Shares)
        pre_round_row = constants_row + 2
        
        self.workbook.define_name(
            f"{round_name_clean}_PreRoundShares",
            f"=Rounds!$B${pre_round_row + 1}"
        )
    
    def _col_letter(self, col_idx: int) -> str:
        """Convert 0-based column index to Excel column letter(s)."""
        result = []
        col_idx += 1
        while col_idx > 0:
            col_idx -= 1
            result.append(chr(col_idx % 26 + ord('A')))
            col_idx //= 26
        return ''.join(reversed(result))
    
    def _get_shares_column_letter(self, calc_type: str) -> str:
        """Get the column letter for shares based on calculation type."""
        if calc_type == 'fixed_shares':
            return 'D'  # holder_name, class_name, acquisition_date, shares
        elif calc_type == 'target_percentage':
            return 'D'  # holder_name, class_name, target_percentage, calculated_shares
        elif calc_type == 'valuation_based':
            return 'E'  # holder_name, class_name, investment, interest, calculated_shares
        elif calc_type == 'convertible':
            return 'K'  # calculated_shares is last column in convertible
        else:
            return 'D'
    
    def get_round_ranges(self) -> Dict[int, Dict[str, Any]]:
        """Get the round ranges dictionary."""
        return self.round_ranges
