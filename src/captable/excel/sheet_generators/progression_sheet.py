"""
Cap Table Progression Sheet Generator

Creates the Cap Table Progression sheet showing ownership evolution across rounds.
This sheet is a SUMMARY VIEW that references the Rounds sheet for instrument data.

In round-based architecture v2.0, instruments are nested within rounds.
This progression sheet aggregates shares by holder and shows evolution across rounds.
"""

from typing import Dict, Any, List, Set
import xlsxwriter

from ..base import BaseSheetGenerator


class ProgressionSheetGenerator(BaseSheetGenerator):
    """
    Generates the Cap Table Progression sheet as a summary view.
    
    In v2.0 architecture:
    - Instruments are nested within rounds (data['rounds'][i]['instruments'])
    - Need to aggregate by holder_name across all rounds
    - Each round gets columns: Start (#), New (#), Total (#), (%)
    - Uses round ranges from Rounds sheet for lookup
    """
    
    def __init__(self, workbook, data, formats, dlm, formula_resolver):
        """Initialize with optional round_ranges."""
        super().__init__(workbook, data, formats, dlm, formula_resolver)
        self.round_ranges = {}  # Will be set from rounds_gen
    
    def _get_sheet_name(self) -> str:
        """Returns 'Cap Table Progression'."""
        return "Cap Table Progression"
    
    def generate(self) -> xlsxwriter.worksheet.Worksheet:
        """Generate the Cap Table Progression sheet."""
        sheet = self.workbook.add_worksheet('Cap Table Progression')
        self.sheet = sheet
        
        rounds = self.data.get('rounds', [])
        if not rounds:
            sheet.write(0, 0, 'No rounds found', self.formats.get('text'))
            return sheet
        
        # Extract unique holders from nested instruments
        all_holders = self._extract_unique_holders(rounds)
        
        if not all_holders:
            sheet.write(0, 0, 'No instruments found', self.formats.get('text'))
            return sheet
        
        # Write headers
        self._write_headers(sheet, rounds)
        
        # Write holder data
        data_start_row = 2  # After headers
        first_holder_row = data_start_row
        last_holder_row = data_start_row + len(all_holders) - 1
        
        data_rows_per_holder = self._write_holder_data(
            sheet, rounds, all_holders, data_start_row, first_holder_row, last_holder_row
        )
        
        # Write total row
        self._write_total_row(sheet, rounds, data_rows_per_holder)
        
        return sheet
    
    def _extract_unique_holders(self, rounds: List[Dict[str, Any]]) -> List[str]:
        """Extract unique holder names from nested instruments."""
        holders_set = set()
        for round_data in rounds:
            instruments = round_data.get('instruments', [])
            for instrument in instruments:
                holder_name = instrument.get('holder_name')
                if holder_name:
                    holders_set.add(holder_name)
        return sorted(list(holders_set))
    
    def _write_headers(self, sheet: xlsxwriter.worksheet.Worksheet, rounds: List[Dict[str, Any]]):
        """Write the header rows (row 0 and 1)."""
        # Row 0: Round names (merged headers)
        row = 0
        col = 2  # Start after "Shareholders" and empty column
        
        for round_data in rounds:
            round_name = round_data.get('name', 'Round')
            # Merge 4 cells for each round (Start, New, Total, %)
            sheet.merge_range(row, col, row, col + 3, round_name, self.formats.get('header'))
            col += 5  # 4 data columns + 1 separator
        
        # Row 1: Column subheaders
        row = 1
        col = 0
        
        sheet.write(row, col, 'Shareholders', self.formats.get('header'))
        col += 1
        sheet.write(row, col, '', self.formats.get('header'))  # Empty
        col += 1
        
        for _ in rounds:
            sheet.write(row, col, 'Start (#)', self.formats.get('header'))
            col += 1
            sheet.write(row, col, 'New (#)', self.formats.get('header'))
            col += 1
            sheet.write(row, col, 'Total (#)', self.formats.get('header'))
            col += 1
            sheet.write(row, col, '(%)', self.formats.get('header'))
            col += 1
            sheet.write(row, col, '', self.formats.get('header'))  # Separator
            col += 1
    
    def _write_holder_data(
        self,
        sheet: xlsxwriter.worksheet.Worksheet,
        rounds: List[Dict[str, Any]],
        holders: List[str],
        data_start_row: int,
        first_holder_row: int,
        last_holder_row: int
    ) -> List[int]:
        """Write holder data and return list of row indices."""
        row = data_start_row
        data_rows = []
        
        for holder_idx, holder_name in enumerate(holders):
            # Write holder name using INDEX to get from holders list
            # Since we have the list, just write it directly
            sheet.write(row, 0, holder_name, self.formats.get('text'))
            sheet.write(row, 1, '', self.formats.get('text'))  # Empty column
            col = 2
            
            # For each round, write Start, New, Total, %
            for round_idx, round_data in enumerate(rounds):
                col = self._write_round_data(
                    sheet, row, col, round_idx, holder_name, rounds, first_holder_row, last_holder_row
                )
            
            data_rows.append(row)
            row += 1
        
        return data_rows
    
    def _write_round_data(
        self,
        sheet: xlsxwriter.worksheet.Worksheet,
        row: int,
        col: int,
        round_idx: int,
        holder_name: str,
        rounds: List[Dict[str, Any]],
        first_holder_row: int,
        last_holder_row: int
    ) -> int:
        """Write data for one round and return updated column position."""
        start_col = col
        new_col = col + 1
        total_col = col + 2
        percent_col = col + 3
        
        # START: Shares at beginning of round
        if round_idx == 0:
            # First round: 0 or founders' shares
            # For now, write 0 (would need to handle founders separately)
            sheet.write_formula(row, start_col, "=0", self.formats.get('number'))
        else:
            # Reference previous round's Total
            # Previous total is 3 columns back (from the start column)
            # Format: =Cap Table Progression!E4 (for example)
            prev_total_col = start_col - 3
            prev_col_letter = self._col_letter(prev_total_col)
            prev_cell = f"'{self._get_sheet_name()}'!{prev_col_letter}{row + 1}"
            sheet.write_formula(row, start_col, f"={prev_cell}", self.formats.get('number'))
        
        # NEW: Sum shares for this holder in this round
        # Includes base shares from Rounds sheet + pro rata shares from Pro Rata Allocations sheet
        if round_idx in self.round_ranges:
            range_info = self.round_ranges[round_idx]
            holder_range = f"Rounds!{range_info['holder_col']}{range_info['start_row']}:{range_info['holder_col']}{range_info['end_row']}"
            shares_range = f"Rounds!{range_info['shares_col']}{range_info['start_row']}:{range_info['shares_col']}{range_info['end_row']}"
            
            # Get holder name from column A of this row (same sheet, use relative reference)
            rounds_shares = f'SUMIF({holder_range}, A{row + 1}, {shares_range})'
        else:
            # Fallback to old method with direct string matching
            calc_type = rounds[round_idx].get('calculation_type', 'fixed_shares')
            shares_col_letter = self._get_shares_column_letter(calc_type)
            # Use actual holder name directly instead of cell reference
            holder_name_escaped = f'"{holder_name}"'
            rounds_shares = f'SUMIF(Rounds!A:A, {holder_name_escaped}, Rounds!{shares_col_letter}:{shares_col_letter})'
        
        # Get pro rata shares from Pro Rata Allocations sheet
        # Pro rata sheet has same row structure (holders in same order)
        # Each round has columns: Pro Rata Type, Pro Rata %, Pro Rata Shares
        # Pro Rata Shares is 2 columns after the start of each round section
        pro_rata_start_col = self._get_pro_rata_shares_col(round_idx, rounds)
        pro_rata_shares = f"'Pro Rata Allocations'!{pro_rata_start_col}{row + 1}"
        
        # Total new shares = rounds sheet shares + pro rata shares
        new_formula = f'=ROUND({rounds_shares} + {pro_rata_shares}, 0)'
        sheet.write_formula(row, new_col, new_formula, self.formats.get('number'))
        
        # TOTAL: Start + New (rounded to integer)
        start_cell = self._col_letter(start_col) + str(row + 1)
        new_cell = self._col_letter(new_col) + str(row + 1)
        total_formula = f"=ROUND(SUM({start_cell},{new_cell}), 0)"
        sheet.write_formula(row, total_col, total_formula, self.formats.get('number'))
        
        # PERCENTAGE: Total / Sum of all Totals for this round
        # Formula: =Total / SUM(All Totals in this round across all holders)
        total_cell = self._col_letter(total_col) + str(row + 1)
        total_col_letter = self._col_letter(total_col)
        # Sum range is from first holder to last holder in the same total column
        sum_range = f"{total_col_letter}{first_holder_row + 1}:{total_col_letter}{last_holder_row + 1}"
        percent_formula = f"=IFERROR({total_cell} / SUM({sum_range}), 0)"
        sheet.write_formula(row, percent_col, percent_formula, self.formats.get('percent'))
        
        # Separator
        col = col + 5
        return col
    
    def _get_shares_column_letter(self, calc_type: str) -> str:
        """Get the column letter for shares based on calculation type."""
        # Determine which column has shares based on calc_type
        if calc_type == 'fixed_shares':
            # Columns: holder_name, class_name, acquisition_date, shares
            return 'D'  # shares is column D (4th column)
        elif calc_type == 'target_percentage':
            # Columns: holder_name, class_name, target_percentage, calculated_shares
            return 'D'  # calculated_shares is column D
        elif calc_type == 'valuation_based':
            # Columns: holder_name, class_name, investment_amount, accrued_interest, calculated_shares
            return 'E'  # calculated_shares is column E (5th column)
        elif calc_type == 'convertible':
            # Columns: holder_name, class_name, investment_amount, ..., calculated_shares
            return 'K'  # calculated_shares is column K (11th column)
        else:
            return 'D'  # Default to column D
    
    def _get_pro_rata_shares_col(self, round_idx: int, rounds: List[Dict[str, Any]]) -> str:
        """Get the column letter for pro rata shares in Pro Rata Allocations sheet."""
        # Pro Rata Allocations sheet structure:
        # Column 0: Shareholders
        # Each round: Pro Rata Type, Pro Rata %, Pro Rata Shares, Separator
        # Pro Rata Shares is 2 columns after the start of each round (col 1 + round_idx * 4 + 2)
        col_idx = 1 + (round_idx * 4) + 2
        return self._col_letter(col_idx)
    
    def _write_total_row(
        self,
        sheet: xlsxwriter.worksheet.Worksheet,
        rounds: List[Dict[str, Any]],
        data_rows_per_holder: List[int]
    ):
        """Write the total row at the bottom."""
        if not data_rows_per_holder:
            return
        
        row = data_rows_per_holder[-1] + 1
        sheet.write(row, 0, 'TOTAL', self.formats.get('label'))
        sheet.write(row, 1, '')
        col = 2
        
        for round_idx, round_data in enumerate(rounds):
            start_col = col
            new_col = col + 1
            total_col = col + 2
            percent_col = col + 3
            
            # Sum all holder rows for each column
            first_row = data_rows_per_holder[0] + 1
            last_row = data_rows_per_holder[-1] + 1
            sheet_name = f"'{self._get_sheet_name()}'"
            
            # START
            start_col_letter = self._col_letter(start_col)
            sheet.write_formula(
                row, start_col,
                f"=SUM({sheet_name}!{start_col_letter}{first_row}:{start_col_letter}{last_row})",
                self.formats.get('number')
            )
            
            # NEW
            new_col_letter = self._col_letter(new_col)
            sheet.write_formula(
                row, new_col,
                f"=SUM({sheet_name}!{new_col_letter}{first_row}:{new_col_letter}{last_row})",
                self.formats.get('number')
            )
            
            # TOTAL
            total_col_letter = self._col_letter(total_col)
            sheet.write_formula(
                row, total_col,
                f"=SUM({sheet_name}!{total_col_letter}{first_row}:{total_col_letter}{last_row})",
                self.formats.get('number')
            )
            
            # PERCENTAGE - Sum of all percentages (should be 100%)
            percent_col_letter = self._col_letter(percent_col)
            sheet.write_formula(
                row, percent_col,
                f"=SUM({sheet_name}!{percent_col_letter}{first_row}:{percent_col_letter}{last_row})",
                self.formats.get('percent')
            )
            
            sheet.write(row, col + 4, '')  # Separator
            col += 5
    
    def _col_letter(self, col_idx: int) -> str:
        """Convert 0-based column index to Excel column letter(s)."""
        result = []
        col_idx += 1  # Excel columns are 1-based
        while col_idx > 0:
            col_idx -= 1
            result.append(chr(col_idx % 26 + ord('A')))
            col_idx //= 26
        return ''.join(reversed(result))
