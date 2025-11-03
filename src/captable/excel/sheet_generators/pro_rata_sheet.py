"""
Pro Rata Allocations Sheet Generator

Creates the Pro Rata Allocations sheet showing pro rata share allocations for each stakeholder per round.
Pro rata calculations happen AFTER regular round shares are calculated.
"""

from typing import Dict, List, Any, Set, Optional
import xlsxwriter
from ..base import BaseSheetGenerator
from ...formulas import ownership


class ProRataSheetGenerator(BaseSheetGenerator):
    """
    Generates the Pro Rata Allocations sheet.
    
    This sheet lists all stakeholders per round and calculates their pro rata share allocations.
    Pro rata calculations are based on:
    - Standard pro rata: Maintain current ownership percentage
    - Super pro rata: Achieve target ownership percentage
    
    Pro rata shares are calculated AFTER regular round shares.
    """
    
    def __init__(self, workbook, data, formats, dlm, formula_resolver):
        """Initialize pro rata sheet generator."""
        super().__init__(workbook, data, formats, dlm, formula_resolver)
        self.round_ranges = {}  # Round ranges from rounds sheet
        self.shares_issued_refs = {}  # Shares issued cell references per round
        self.holder_data_range = {}  # Row range for holder data (for summing pro rata %)
    
    def _get_sheet_name(self) -> str:
        """Returns 'Pro Rata Allocations'."""
        return "Pro Rata Allocations"
    
    def generate(self) -> xlsxwriter.worksheet.Worksheet:
        """Generate the Pro Rata Allocations sheet."""
        sheet = self.workbook.add_worksheet('Pro Rata Allocations')
        self.sheet = sheet
        
        rounds = self.data.get('rounds', [])
        if not rounds:
            sheet.write(0, 0, 'No rounds found', self.formats.get('text'))
            return sheet
        
        # Extract unique holders from all rounds
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
        
        self._write_holder_data(
            sheet, rounds, all_holders, data_start_row, first_holder_row, last_holder_row
        )
        
        # Write total row
        self._write_total_row(sheet, rounds, all_holders, first_holder_row, last_holder_row)
        
        # Set column widths
        self.set_column_widths([
            (0, 0, 25),  # Holder name
            (1, len(rounds) * 3 + 1, 15),  # Round columns
        ])
        
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
        col = 1  # Start after "Shareholders"
        
        for round_data in rounds:
            round_name = round_data.get('name', 'Round')
            # Merge 3 cells for each round (Pro Rata Type, Pro Rata %, Pro Rata Shares)
            sheet.merge_range(row, col, row, col + 2, round_name, self.formats.get('header'))
            col += 4  # 3 data columns + 1 separator
        
        # Row 1: Column subheaders
        row = 1
        col = 0
        
        sheet.write(row, col, 'Shareholders', self.formats.get('header'))
        col += 1
        
        for _ in rounds:
            sheet.write(row, col, 'Pro Rata Type', self.formats.get('header'))
            col += 1
            sheet.write(row, col, 'Pro Rata %', self.formats.get('header'))
            col += 1
            sheet.write(row, col, 'Pro Rata Shares', self.formats.get('header'))
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
    ):
        """Write holder data with pro rata calculations."""
        row = data_start_row
        pro_rata_type_rows_by_round = {}  # Track rows for dropdown validation per round
        
        for holder_name in holders:
            # Write holder name
            sheet.write(row, 0, holder_name, self.formats.get('text'))
            col = 1
            
            # For each round, write pro rata data
            for round_idx, round_data in enumerate(rounds):
                type_col = col  # Pro Rata Type column for this round
                col = self._write_round_pro_rata_data(
                    sheet, row, col, round_idx, holder_name, rounds,
                    first_holder_row, last_holder_row
                )
                
                # Track rows that have pro rata type cells for dropdown validation
                if round_idx not in pro_rata_type_rows_by_round:
                    pro_rata_type_rows_by_round[round_idx] = []
                pro_rata_type_rows_by_round[round_idx].append(row)
            
            row += 1
        
        # Store row ranges for calculating sum of pro rata percentages
        self.holder_data_range = {
            'first_row': first_holder_row,
            'last_row': row - 1  # Last holder row
        }
        
        # Add dropdown validation for pro rata type columns
        self._add_pro_rata_dropdowns(sheet, rounds, pro_rata_type_rows_by_round)
    
    def _write_round_pro_rata_data(
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
        """Write pro rata data for one round and return updated column position."""
        type_col = col
        pct_col = col + 1
        shares_col = col + 2
        separator_col = col + 3
        
        round_data = rounds[round_idx]
        instruments = round_data.get('instruments', [])
        
        # Find instrument for this holder in this round
        holder_instrument = None
        for instrument in instruments:
            if instrument.get('holder_name') == holder_name:
                holder_instrument = instrument
                break
        
        # Get pro rata data from instrument if it exists
        pro_rata_type = 'none'
        pro_rata_pct = None
        if holder_instrument:
            pro_rata_type = holder_instrument.get('pro_rata_type', 'none')
            pro_rata_pct = holder_instrument.get('pro_rata_percentage')
        
        # Write pro rata type (will have dropdown validation added later)
        sheet.write(row, type_col, pro_rata_type, self.formats.get('text'))
        
        # Pro Rata % column: dynamic formula based on pro_rata_type
        # For "standard": calculate ownership % = holder_shares_start / pre_round_shares
        # For "super": use the value from data (allow manual entry)
        # For "none": empty
        type_col_letter = self._col_letter(type_col)
        type_cell_ref = f"{type_col_letter}{row + 1}"
        
        # Get references needed for ownership % calculation
        round_data = rounds[round_idx]
        round_name_key = round_data.get('name', '').replace(' ', '_')
        pre_round_shares_ref = f"{round_name_key}_PreRoundShares"
        
        # Get holder's shares at start of round (for standard pro rata ownership % calculation)
        if round_idx == 0:
            holder_shares_start_ref = "0"
        else:
            prev_round_total_col = self._get_progression_total_col(round_idx - 1, rounds)
            holder_row = row + 1
            holder_shares_start_ref = f"'Cap Table Progression'!{prev_round_total_col}{holder_row}"
        
        # Dynamic formula for Pro Rata % column
        # If "standard": calculate ownership % = holder_shares_start / pre_round_shares
        # If "super": use initial value from data (stored in formula, but can be manually edited)
        # Otherwise: empty
        ownership_pct_formula = f"IFERROR({holder_shares_start_ref} / {pre_round_shares_ref}, 0)"
        
        # Always use a formula that checks the type dropdown
        # For "standard": automatically calculates ownership %
        # For "super": uses the initial value from data (can be manually edited by user)
        # For "none" or empty: shows empty
        initial_super_value = pro_rata_pct if (pro_rata_type == 'super' and pro_rata_pct is not None) else 0
        pct_formula = (
            f"=IF({type_cell_ref}=\"standard\", {ownership_pct_formula}, "
            f"IF({type_cell_ref}=\"super\", {initial_super_value}, \"\"))"
        )
        sheet.write_formula(row, pct_col, pct_formula, self.formats.get('percent'))
        
        # Get cell references for formulas
        pct_col_letter = self._col_letter(pct_col)
        pct_cell_ref = f"{pct_col_letter}{row + 1}"
        
        # Create formulas for each pro rata type
        none_formula = "0"
        standard_formula = self._create_standard_pro_rata_formula(
            round_idx, holder_name, rounds, row, pct_col, first_holder_row, last_holder_row
        )
        super_formula = self._create_super_pro_rata_formula(
            round_idx, holder_name, rounds, row, pct_col, first_holder_row, last_holder_row
        )
        
        # Remove leading = from formulas for IF statement
        standard_formula_no_eq = standard_formula.lstrip('=')
        super_formula_no_eq = super_formula.lstrip('=')
        
        # Dynamic formula using nested IF to check pro_rata_type cell
        # Handles: "none", "standard", "super", or empty/invalid (defaults to 0)
        shares_formula = (
            f"=IFERROR(IF(OR({type_cell_ref}=\"\", {type_cell_ref}=\"none\"), {none_formula}, "
            f"IF({type_cell_ref}=\"standard\", {standard_formula_no_eq}, "
            f"IF({type_cell_ref}=\"super\", {super_formula_no_eq}, "
            f"{none_formula}))), 0)"
        )
        sheet.write_formula(row, shares_col, shares_formula, self.formats.get('number'))
        
        # Separator
        sheet.write(row, separator_col, '', self.formats.get('text'))
        
        return separator_col + 1
    
    def _create_standard_pro_rata_formula(
        self,
        round_idx: int,
        holder_name: str,
        rounds: List[Dict[str, Any]],
        row: int,
        pct_col: int,
        first_holder_row: int,
        last_holder_row: int
    ) -> str:
        """Create formula for pro rata shares (standard uses Pro Rata % cell as target)."""
        round_data = rounds[round_idx]
        round_name_key = round_data.get('name', '').replace(' ', '_')
        pre_round_shares_ref = f"{round_name_key}_PreRoundShares"

        # Base round shares (before pro rata)
        if round_idx in self.shares_issued_refs:
            shares_issued_ref = self.shares_issued_refs[round_idx]
        elif round_idx in self.round_ranges:
            range_info = self.round_ranges[round_idx]
            shares_col = range_info.get('shares_col', 'D')
            shares_range = f"Rounds!{shares_col}{range_info['start_row']}:{shares_col}{range_info['end_row']}"
            shares_issued_ref = f"SUM({shares_range})"
        else:
            shares_issued_ref = "0"

        # Holder's current shares before pro rata = prev round total + base shares issued this round
        prev_round_total_col = self._get_progression_total_col(round_idx - 1, rounds) if round_idx > 0 else None
        holder_row = row + 1
        prev_total_ref = f"'Cap Table Progression'!{prev_round_total_col}{holder_row}" if prev_round_total_col else "0"
        holder_base_shares_ref = self._get_holder_base_shares_ref(round_idx, holder_row)
        holder_shares_start_ref = f"({prev_total_ref} + {holder_base_shares_ref})"

        # Target percentage is the Pro Rata % cell for this row
        target_pct_col_letter = self._col_letter(pct_col)
        holder_target_pct_ref = f"{target_pct_col_letter}{row + 1}"

        # Aggregates across participants
        sum_standard_target_pct_ref = self._get_sum_standard_pro_rata_pct_ref(round_idx, rounds, first_holder_row, last_holder_row)
        sum_super_target_pct_ref = self._get_sum_super_target_pct_ref(round_idx, rounds, first_holder_row, last_holder_row)
        sum_standard_current_shares_ref = self._get_sum_standard_current_shares_ref(round_idx, rounds, first_holder_row, last_holder_row)
        sum_super_current_shares_ref = self._get_sum_super_current_shares_ref(round_idx, rounds, first_holder_row, last_holder_row)

        # Unified formula
        formula = ownership.create_unified_pro_rata_shares_formula(
            holder_target_pct_ref,
            pre_round_shares_ref,
            shares_issued_ref,
            holder_shares_start_ref,
            sum_standard_target_pct_ref,
            sum_super_target_pct_ref,
            sum_standard_current_shares_ref,
            sum_super_current_shares_ref
        )
        return formula
    
    def _create_super_pro_rata_formula(
        self,
        round_idx: int,
        holder_name: str,
        rounds: List[Dict[str, Any]],
        row: int,
        pct_col: int,
        first_holder_row: int,
        last_holder_row: int
    ) -> str:
        """Create formula for super pro rata shares (unified simultaneous solution)."""
        round_data = rounds[round_idx]
        round_name_key = round_data.get('name', '').replace(' ', '_')
        pre_round_shares_ref = f"{round_name_key}_PreRoundShares"

        # Base round shares (before pro rata)
        if round_idx in self.shares_issued_refs:
            shares_issued_ref = self.shares_issued_refs[round_idx]
        elif round_idx in self.round_ranges:
            range_info = self.round_ranges[round_idx]
            shares_range = f"Rounds!{range_info['shares_col']}{range_info['start_row']}:{range_info['shares_col']}{range_info['end_row']}"
            shares_issued_ref = f"SUM({shares_range})"
        else:
            shares_issued_ref = "0"

        # Target ownership % is in the pct_col column of this row
        target_pct_col_letter = self._col_letter(pct_col)
        target_pct_ref = f"{target_pct_col_letter}{row + 1}"

        # Holder's current shares before pro rata = prev round total + base shares issued this round
        prev_round_total_col = self._get_progression_total_col(round_idx - 1, rounds) if round_idx > 0 else None
        holder_row = row + 1
        prev_total_ref = f"'Cap Table Progression'!{prev_round_total_col}{holder_row}" if prev_round_total_col else "0"
        holder_base_shares_ref = self._get_holder_base_shares_ref(round_idx, holder_row)
        holder_shares_start_ref = f"({prev_total_ref} + {holder_base_shares_ref})"

        # Aggregates across participants
        sum_standard_target_pct_ref = self._get_sum_standard_pro_rata_pct_ref(round_idx, rounds, first_holder_row, last_holder_row)
        sum_super_target_pct_ref = self._get_sum_super_target_pct_ref(round_idx, rounds, first_holder_row, last_holder_row)
        sum_standard_current_shares_ref = self._get_sum_standard_current_shares_ref(round_idx, rounds, first_holder_row, last_holder_row)
        sum_super_current_shares_ref = self._get_sum_super_current_shares_ref(round_idx, rounds, first_holder_row, last_holder_row)

        # Unified formula
        formula = ownership.create_unified_pro_rata_shares_formula(
            target_pct_ref,
            pre_round_shares_ref,
            shares_issued_ref,
            holder_shares_start_ref,
            sum_standard_target_pct_ref,
            sum_super_target_pct_ref,
            sum_standard_current_shares_ref,
            sum_super_current_shares_ref
        )
        return formula
    
    def _get_sum_pro_rata_pct_ref(
        self,
        round_idx: int,
        rounds: List[Dict[str, Any]],
        first_holder_row: int,
        last_holder_row: int
    ) -> str:
        """
        Get reference to Excel formula that sums all pro rata percentages in this round.
        
        The Pro Rata % column contains:
        - For "standard": automatically calculated ownership % = holder_shares_start / pre_round_shares
        - For "super": target ownership % (manual entry)
        - For "none": empty or 0
        
        Returns an Excel SUM formula that sums all Pro Rata % values in this round's column.
        This will be embedded in the pro rata shares calculation formulas.
        """
        # Build SUM over holder data rows directly so formulas are valid during row creation
        first_row = first_holder_row
        last_row = last_holder_row
        
        # Pro Rata % column for this round
        # Column position: 1 (type) + 1 (pct) + round_idx * 4
        pct_col = 2 + (round_idx * 4)
        pct_col_letter = self._col_letter(pct_col)
        
        # Create Excel SUM formula for the Pro Rata % column in this round
        sheet_name = self._get_sheet_name()
        pct_range = f"'{sheet_name}'!{pct_col_letter}{first_row + 1}:{pct_col_letter}{last_row + 1}"
        sum_pro_rata_pct_formula = f"SUM({pct_range})"
        return sum_pro_rata_pct_formula

    def _get_sum_standard_pro_rata_pct_ref(
        self,
        round_idx: int,
        rounds: List[Dict[str, Any]],
        first_holder_row: int,
        last_holder_row: int
    ) -> str:
        """
        Get reference to Excel formula that sums only STANDARD pro rata percentages in this round.
        Uses SUMIF over the Pro Rata Type column == "standard".
        """
        # Determine the type and pct column letters for this round
        type_col = 1 + (round_idx * 4)
        pct_col = type_col + 1
        type_col_letter = self._col_letter(type_col)
        pct_col_letter = self._col_letter(pct_col)

        first_row = first_holder_row
        last_row = last_holder_row

        sheet_name = self._get_sheet_name()
        type_range = f"'{sheet_name}'!{type_col_letter}{first_row + 1}:{type_col_letter}{last_row + 1}"
        pct_range = f"'{sheet_name}'!{pct_col_letter}{first_row + 1}:{pct_col_letter}{last_row + 1}"
        return f"SUMIF({type_range}, \"standard\", {pct_range})"

    def _get_sum_super_target_pct_ref(
        self,
        round_idx: int,
        rounds: List[Dict[str, Any]],
        first_holder_row: int,
        last_holder_row: int
    ) -> str:
        """
        Sum of target percentages for rows with Pro Rata Type == "super" in this round.
        """
        type_col = 1 + (round_idx * 4)
        pct_col = type_col + 1
        type_col_letter = self._col_letter(type_col)
        pct_col_letter = self._col_letter(pct_col)
        sheet_name = self._get_sheet_name()
        type_range = f"'{sheet_name}'!{type_col_letter}{first_holder_row + 1}:{type_col_letter}{last_holder_row + 1}"
        pct_range = f"'{sheet_name}'!{pct_col_letter}{first_holder_row + 1}:{pct_col_letter}{last_holder_row + 1}"
        return f"SUMIF({type_range}, \"super\", {pct_range})"

    def _get_sum_super_current_shares_ref(
        self,
        round_idx: int,
        rounds: List[Dict[str, Any]],
        first_holder_row: int,
        last_holder_row: int
    ) -> str:
        """
        Sum of current shares (pre-round) for all holders who selected SUPER in this round.
        """
        # When round_idx == 0 there is no previous total; treat as 0
        if round_idx == 0:
            return "0"

        prev_round_total_col = self._get_progression_total_col(round_idx - 1, rounds)
        progression_range = f"'Cap Table Progression'!{prev_round_total_col}{first_holder_row + 1}:{prev_round_total_col}{last_holder_row + 1}"

        type_col = 1 + (round_idx * 4)
        type_col_letter = self._col_letter(type_col)
        sheet_name = self._get_sheet_name()
        type_range = f"'{sheet_name}'!{type_col_letter}{first_holder_row + 1}:{type_col_letter}{last_holder_row + 1}"

        # Add base shares issued this round per holder via SUMIF over Rounds range
        rounds_holder_range, rounds_shares_range = self._get_rounds_holder_and_shares_ranges(round_idx)
        holder_name_range = f"'{sheet_name}'!A{first_holder_row + 1}:A{last_holder_row + 1}"
        base_sum_array = f"SUMIF({rounds_holder_range}, {holder_name_range}, {rounds_shares_range})"

        return f"SUMPRODUCT(--({type_range}=\"super\"), {progression_range} + {base_sum_array})"

    def _get_sum_standard_current_shares_ref(
        self,
        round_idx: int,
        rounds: List[Dict[str, Any]],
        first_holder_row: int,
        last_holder_row: int
    ) -> str:
        """
        Sum of current shares (pre-pro-rata) for all holders who selected STANDARD in this round.
        Includes prev round totals plus base shares issued this round.
        """
        if round_idx == 0:
            # Only base shares apply in first round
            rounds_holder_range, rounds_shares_range = self._get_rounds_holder_and_shares_ranges(round_idx)
            sheet_name = self._get_sheet_name()
            type_col = 1 + (round_idx * 4)
            type_col_letter = self._col_letter(type_col)
            type_range = f"'{sheet_name}'!{type_col_letter}{first_holder_row + 1}:{type_col_letter}{last_holder_row + 1}"
            holder_name_range = f"'{sheet_name}'!A{first_holder_row + 1}:A{last_holder_row + 1}"
            base_sum_array = f"SUMIF({rounds_holder_range}, {holder_name_range}, {rounds_shares_range})"
            return f"SUMPRODUCT(--({type_range}=\"standard\"), {base_sum_array})"

        prev_round_total_col = self._get_progression_total_col(round_idx - 1, rounds)
        progression_range = f"'Cap Table Progression'!{prev_round_total_col}{first_holder_row + 1}:{prev_round_total_col}{last_holder_row + 1}"

        type_col = 1 + (round_idx * 4)
        type_col_letter = self._col_letter(type_col)
        sheet_name = self._get_sheet_name()
        type_range = f"'{sheet_name}'!{type_col_letter}{first_holder_row + 1}:{type_col_letter}{last_holder_row + 1}"

        rounds_holder_range, rounds_shares_range = self._get_rounds_holder_and_shares_ranges(round_idx)
        holder_name_range = f"'{sheet_name}'!A{first_holder_row + 1}:A{last_holder_row + 1}"
        base_sum_array = f"SUMIF({rounds_holder_range}, {holder_name_range}, {rounds_shares_range})"

        return f"SUMPRODUCT(--({type_range}=\"standard\"), {progression_range} + {base_sum_array})"

    def _get_holder_base_shares_ref(self, round_idx: int, holder_row_1_based: int) -> str:
        """SUMIF over Rounds for base shares issued to the holder in this round."""
        rounds_holder_range, rounds_shares_range = self._get_rounds_holder_and_shares_ranges(round_idx)
        sheet_name = self._get_sheet_name()
        holder_name_cell = f"'{sheet_name}'!A{holder_row_1_based}"
        return f"IFERROR(SUMIF({rounds_holder_range}, {holder_name_cell}, {rounds_shares_range}), 0)"

    def _get_rounds_holder_and_shares_ranges(self, round_idx: int) -> tuple:
        """Return tuple of (holder_range, shares_range) for the given round on Rounds sheet."""
        if round_idx in self.round_ranges:
            range_info = self.round_ranges[round_idx]
            holder_col = range_info.get('holder_col', 'A')
            shares_col = range_info.get('shares_col', 'D')
            holder_range = f"Rounds!{holder_col}{range_info['start_row']}:{holder_col}{range_info['end_row']}"
            shares_range = f"Rounds!{shares_col}{range_info['start_row']}:{shares_col}{range_info['end_row']}"
            return holder_range, shares_range
        # Fallback to empty ranges that sum to 0
        return "Rounds!A1:A1", "Rounds!A1:A1"

    def _get_sum_standard_current_shares_ref(
        self,
        round_idx: int,
        rounds: List[Dict[str, Any]],
        first_holder_row: int,
        last_holder_row: int
    ) -> str:
        """
        Sum of current shares (pre-round) for all holders who selected STANDARD in this round.
        """
        if round_idx == 0:
            return "0"

        prev_round_total_col = self._get_progression_total_col(round_idx - 1, rounds)
        progression_range = f"'Cap Table Progression'!{prev_round_total_col}{first_holder_row + 1}:{prev_round_total_col}{last_holder_row + 1}"

        type_col = 1 + (round_idx * 4)
        type_col_letter = self._col_letter(type_col)
        sheet_name = self._get_sheet_name()
        type_range = f"'{sheet_name}'!{type_col_letter}{first_holder_row + 1}:{type_col_letter}{last_holder_row + 1}"

        return f"SUMPRODUCT(--({type_range}=\"standard\"), {progression_range})"
    
    def _get_progression_start_col(self, round_idx: int, rounds: List[Dict[str, Any]]) -> str:
        """Get the column letter for the Start column of a round in progression sheet."""
        # Each round has 4 columns: Start, New, Total, %
        # Plus 2 initial columns: Shareholders, empty
        # Formula: col = 2 + (round_idx * 5) + 0 (for Start column)
        col_idx = 2 + (round_idx * 5)
        return self._col_letter(col_idx)
    
    def _get_progression_total_col(self, round_idx: int, rounds: List[Dict[str, Any]]) -> str:
        """Get the column letter for the Total column of a round in progression sheet."""
        # Each round has 4 columns: Start, New, Total, %
        # Total is 2 columns after Start
        # Formula: col = 2 + (round_idx * 5) + 2 (for Total column)
        col_idx = 2 + (round_idx * 5) + 2
        return self._col_letter(col_idx)
    
    
    def _write_total_row(
        self,
        sheet: xlsxwriter.worksheet.Worksheet,
        rounds: List[Dict[str, Any]],
        holders: List[str],
        first_holder_row: int,
        last_holder_row: int
    ):
        """Write the total row at the bottom."""
        if not holders:
            return
        
        row = last_holder_row + 1
        sheet.write(row, 0, 'TOTAL', self.formats.get('label'))
        col = 1
        
        for round_idx, round_data in enumerate(rounds):
            type_col = col
            pct_col = col + 1
            shares_col = col + 2
            separator_col = col + 3
            
            sheet.write(row, type_col, '', self.formats.get('text'))
            # Sum all pro rata percentages for this round
            pct_col_letter = self._col_letter(pct_col)
            sheet.write_formula(
                row, pct_col,
                f"=SUM({pct_col_letter}{first_holder_row + 1}:{pct_col_letter}{last_holder_row + 1})",
                self.formats.get('percent')
            )
            # Highlight when total pro rata % exceeds 100%
            sheet.conditional_format(
                row, pct_col, row, pct_col,
                {
                    'type': 'cell',
                    'criteria': 'greater than',
                    'value': 1,
                    'format': self.formats.get('error') if 'error' in self.formats else self.formats.get('percent')
                }
            )
            
            # Sum all pro rata shares for this round
            shares_col_letter = self._col_letter(shares_col)
            sheet.write_formula(
                row, shares_col,
                f"=SUM({shares_col_letter}{first_holder_row + 1}:{shares_col_letter}{last_holder_row + 1})",
                self.formats.get('number')
            )

            # Define a Named Range for this round's total pro rata shares so other sheets can reference it
            round_name_key = round_data.get('name', '').replace(' ', '_')
            pr_total_named = f"{round_name_key}_ProRataShares"
            cell_ref_abs = f"'Pro Rata Allocations'!${shares_col_letter}${row + 1}"
            self.workbook.define_name(pr_total_named, cell_ref_abs)
            
            sheet.write(row, separator_col, '', self.formats.get('text'))
            col = separator_col + 1
    
    def set_round_ranges(self, round_ranges: Dict[int, Dict[str, Any]]):
        """Set round ranges from rounds sheet generator."""
        self.round_ranges = round_ranges
    
    def set_shares_issued_refs(self, shares_issued_refs: Dict[int, str]):
        """Set shares_issued cell references from rounds sheet generator."""
        self.shares_issued_refs = shares_issued_refs
    
    def _add_pro_rata_dropdowns(
        self,
        sheet: xlsxwriter.worksheet.Worksheet,
        rounds: List[Dict[str, Any]],
        pro_rata_type_rows_by_round: Dict[int, List[int]]
    ):
        """Add dropdown validation to Pro Rata Type columns."""
        for round_idx, rows in pro_rata_type_rows_by_round.items():
            if not rows:
                continue
            
            # Pro Rata Type column is the first column of each round section
            # Column position: 1 + (round_idx * 4)
            type_col = 1 + (round_idx * 4)
            
            first_row = min(rows)
            last_row = max(rows)
            
            # Add dropdown with valid pro rata type options
            sheet.data_validation(
                first_row, type_col,
                last_row, type_col,
                {
                    'validate': 'list',
                    'source': ['none', 'standard', 'super'],
                    'error_type': 'stop',
                    'error_title': 'Invalid Pro Rata Type',
                    'error_message': 'Please select "none", "standard", or "super" from the dropdown.'
                }
            )

