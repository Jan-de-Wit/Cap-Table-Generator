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
        # Padding offset for table positioning
        self.padding_offset = 1
    
    def _get_sheet_name(self) -> str:
        """Returns 'Cap Table Progression'."""
        return "Cap Table Progression"
    
    def generate(self) -> xlsxwriter.worksheet.Worksheet:
        """Generate the Cap Table Progression sheet."""
        sheet = self.workbook.add_worksheet('Cap Table Progression')
        self.sheet = sheet
        
        rounds = self.data.get('rounds', [])
        if not rounds:
            sheet.write(self.padding_offset, self.padding_offset, 'No rounds found', self.formats.get('text'))
            return sheet
        
        # Extract holders with grouping
        holders_by_group, all_holders = self._get_holders_with_groups(rounds)
        
        if not all_holders:
            sheet.write(self.padding_offset + 1, self.padding_offset + 1, 'No instruments found', self.formats.get('text'))
            return sheet
        
        # Calculate table bounds for border (border includes 1 cell padding on all sides)
        # Border starts at padding_offset (1), content starts at padding_offset + 1 (2)
        border_start_row = self.padding_offset
        border_start_col = self.padding_offset
        # Calculate last column: padding + 1 (padding) + 2 (Shareholders + Description) + (rounds * 5) - 1
        # Each round has 5 columns (4 data + 1 separator), last round's separator is the last column
        num_rounds = len(rounds)
        border_end_col = self.padding_offset + 1 + 2 + (num_rounds * 5) - 1
        # Last row includes padding, so we need to calculate after writing data
        
        # Write headers (shifted by padding offset + 1 for content within border)
        self._write_headers(sheet, rounds)
        
        # Write holder data with grouping (shifted by padding offset + 1 for content within border)
        data_start_row = self.padding_offset + 1 + 2  # After padding + headers
        data_rows_per_holder, first_holder_row, last_holder_row = self._write_holder_data_with_groups(
            sheet, rounds, all_holders, holders_by_group, data_start_row
        )
        
        # Write total row
        self._write_total_row(sheet, rounds, data_rows_per_holder)
        
        # Calculate border end row (includes padding)
        border_end_row = data_rows_per_holder[-1] + 2 + 1  # Total row + spacing + padding
        
        # Set up table formatting using utility function
        row_heights = [
            (0, 16.0),  # Outer padding row
            (border_start_row, 16.0),  # Inner padding row (top border row)
            (self.padding_offset + 1, 25),  # Round names row
            (self.padding_offset + 2, 25),  # Column headers row
        ]
        
        column_widths = [
            (0, 0, 4.0),  # Outer padding column
            (border_start_col, border_start_col, 4.0),  # Inner padding column (left border column)
            (self.padding_offset + 1, self.padding_offset + 1, 35),  # Shareholders column
            (self.padding_offset + 2, self.padding_offset + 2, 35),  # Description column
        ]
        
        # For each round, set widths for Start, New, Total, % (15) and separator (5)
        for round_idx in range(num_rounds):
            # Start column: padding + 1 (inner padding) + 2 (Shareholders + Description) + (round_idx * 5)
            start_col = self.padding_offset + 1 + 2 + (round_idx * 5)
            # Set Start, New, Total, % columns to width 15
            column_widths.append((start_col, start_col + 3, 15))
            # Set separator column to width 5
            separator_col = start_col + 4
            column_widths.append((separator_col, separator_col, 5))
        
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
        
        freeze_row = self.padding_offset + 2 + 1
        freeze_col = self.padding_offset + 2
        sheet.freeze_panes(freeze_row, freeze_col)
        
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
    
    def _get_holders_with_groups(self, rounds: List[Dict[str, Any]]) -> tuple:
        """
        Get holders list with grouping information.
        
        Returns:
            Tuple of (holders_by_group: Dict[str, List[str]], all_holders: List[str])
            where holders_by_group maps group name to list of holder names,
            and all_holders is a flat list of all holders in group order.
        """
        # First, get all unique holders from instruments
        holders_set = set()
        for round_data in rounds:
            instruments = round_data.get('instruments', [])
            for instrument in instruments:
                holder_name = instrument.get('holder_name')
                if holder_name:
                    holders_set.add(holder_name)
        
        # Build holder-to-group mapping from holders array
        holder_to_group = {}
        if 'holders' in self.data:
            for holder_data in self.data['holders']:
                holder_name = holder_data.get('name')
                group = holder_data.get('group', '')
                if holder_name and holder_name in holders_set:
                    holder_to_group[holder_name] = group
        
        # Group holders by their group
        holders_by_group: Dict[str, List[str]] = {}
        ungrouped = []
        
        for holder_name in sorted(holders_set):
            group = holder_to_group.get(holder_name, '')
            if group:
                if group not in holders_by_group:
                    holders_by_group[group] = []
                holders_by_group[group].append(holder_name)
            else:
                ungrouped.append(holder_name)
        
        # Build flat list: groups first (sorted by group name), then ungrouped
        all_holders = []
        for group in sorted(holders_by_group.keys()):
            all_holders.extend(holders_by_group[group])
        all_holders.extend(ungrouped)
        
        return holders_by_group, all_holders
    
    
    def _write_headers(self, sheet: xlsxwriter.worksheet.Worksheet, rounds: List[Dict[str, Any]]):
        """Write the header rows (shifted by padding offset + 1 for content within border)."""
        # Row (shifted by padding + 1): Round names (merged headers)
        header_row = self.padding_offset + 1
        subheader_row = self.padding_offset + 2
        start_col = self.padding_offset + 1 + 2  # Start after padding + "Shareholders" and empty column
        
        # Write Shareholders and Description headers first
        sheet.write(subheader_row, self.padding_offset + 1, 'Shareholders', self.formats.get('header'))
        sheet.write(subheader_row, self.padding_offset + 2, '', self.formats.get('header'))
        
        # Use utility function to write round headers
        subheaders = ['Start (#)', 'New (#)', 'Total (#)', '(%)']
        self.write_round_headers(
            sheet,
            rounds,
            header_row,
            start_col,
            columns_per_round=4,
            separator_width=1,
            subheader_row=subheader_row,
            subheaders=subheaders
        )
    
    def _write_holder_data_with_groups(
        self,
        sheet: xlsxwriter.worksheet.Worksheet,
        rounds: List[Dict[str, Any]],
        all_holders: List[str],
        holders_by_group: Dict[str, List[str]],
        data_start_row: int
    ) -> tuple:
        """
        Write holder data with grouping and spacing rows.
        
        Returns:
            Tuple of (data_rows: List[int], first_holder_row: int, last_holder_row: int)
        """
        # First pass: calculate row positions
        holder_row_map = {}  # holder_name -> row
        row = data_start_row
        first_holder_row = None
        
        # Build reverse mapping: holder -> group
        holder_to_group = {}
        for group, holders in holders_by_group.items():
            for holder in holders:
                holder_to_group[holder] = group
        
        # Calculate which row each holder will be on
        current_group = None
        for holder_name in all_holders:
            group = holder_to_group.get(holder_name, '')
            
            # Add group header and spacing row before new group
            if group and group != current_group:
                if current_group is not None:
                    # Add spacing row after previous group
                    row += 1
                # Add group header row
                row += 1
                current_group = group
            elif not group and current_group is not None:
                # Add spacing row before ungrouped holders
                row += 1
                current_group = None
            
            # Track first and last holder rows (excluding spacing rows and group headers)
            if first_holder_row is None:
                first_holder_row = row
            
            holder_row_map[holder_name] = row
            row += 1
        
        last_holder_row = row - 1
        
        # Build holder -> description mapping
        holder_to_description: Dict[str, str] = {}
        for holder in self.data.get('holders', []) or []:
            name = holder.get('name')
            desc = holder.get('description', '')
            if name:
                holder_to_description[name] = desc

        # Second pass: write data with correct row references
        data_rows = []
        row = data_start_row
        current_group = None
        
        for holder_name in all_holders:
            group = holder_to_group.get(holder_name, '')
            
            # Add group header and spacing row before new group
            if group and group != current_group:
                if current_group is not None:
                    # Add spacing row after previous group
                    row += 1
                # Write group header row (bold) - shifted by padding offset + 1 for content within border
                sheet.write(row, self.padding_offset + 1, group, self.formats.get('label'))
                # Leave other columns empty for group header
                row += 1
                current_group = group
            elif not group and current_group is not None:
                # Add spacing row before ungrouped holders
                row += 1
                current_group = None
            
            # Write holder name - shifted by padding offset + 1 for content within border
            sheet.write(row, self.padding_offset + 1, holder_name, self.formats.get('text'))
            # Description column (optional) - shifted by padding offset + 1 for content within border
            sheet.write(row, self.padding_offset + 2, holder_to_description.get(holder_name, ''), self.formats.get('italic_text'))
            col = self.padding_offset + 1 + 2
            
            # For each round, write Start, New, Total, %
            for round_idx, round_data in enumerate(rounds):
                is_last_round = (round_idx == len(rounds) - 1)
                col = self._write_round_data(
                    sheet, row, col, round_idx, holder_name, rounds, first_holder_row, last_holder_row, is_last_round
                )
            
            data_rows.append(row)
            row += 1
        
        return data_rows, first_holder_row, last_holder_row
    
    def _write_holder_data(
        self,
        sheet: xlsxwriter.worksheet.Worksheet,
        rounds: List[Dict[str, Any]],
        holders: List[str],
        data_start_row: int,
        first_holder_row: int,
        last_holder_row: int
    ) -> List[int]:
        """Write holder data (legacy method, kept for compatibility)."""
        row = data_start_row
        data_rows = []
        
        for holder_idx, holder_name in enumerate(holders):
            # Write holder name using INDEX to get from holders list
            # Since we have the list, just write it directly - shifted by padding offset + 1 for content within border
            sheet.write(row, self.padding_offset + 1, holder_name, self.formats.get('text'))
            sheet.write(row, self.padding_offset + 2, '', self.formats.get('text'))  # Empty column
            col = self.padding_offset + 1 + 2
            
            # For each round, write Start, New, Total, %
            for round_idx, round_data in enumerate(rounds):
                is_last_round = (round_idx == len(rounds) - 1)
                col = self._write_round_data(
                    sheet, row, col, round_idx, holder_name, rounds, first_holder_row, last_holder_row, is_last_round
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
        last_holder_row: int,
        is_last_round: bool = False
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
            sheet.write_formula(row, start_col, "=0", self.formats.get('table_number'))
        else:
            # Reference previous round's Total
            # Previous total is 3 columns back (from the start column)
            # Format: =Cap Table Progression!E4 (for example)
            prev_total_col = start_col - 3
            prev_col_letter = self._col_letter(prev_total_col)
            prev_cell = f"'{self._get_sheet_name()}'!{prev_col_letter}{row + 1}"
            sheet.write_formula(row, start_col, f"={prev_cell}", self.formats.get('table_number'))
        
        # NEW: Sum shares for this holder in this round
        # Includes base shares from Rounds sheet + pro rata shares from Pro Rata Allocations sheet
        if round_idx in self.round_ranges:
            range_info = self.round_ranges[round_idx]
            table_name = range_info.get('table_name')
            if table_name:
                # Use structured references over the round's instruments table
                shares_header = self._get_shares_header(range_info.get('calc_type'))
                holder_col_ref = f"{table_name}[[#All],[Holder Name]]"
                shares_col_ref = f"{table_name}[[#All],[{shares_header}]]"
                # Shareholders column is at padding_offset + 1 (within border)
                holder_col_letter = self._col_letter(self.padding_offset + 1)
                rounds_shares = f"SUMIF({holder_col_ref}, {holder_col_letter}{row + 1}, {shares_col_ref})"
            else:
                holder_range = f"Rounds!{range_info['holder_col']}{range_info['start_row']}:{range_info['holder_col']}{range_info['end_row']}"
                shares_range = f"Rounds!{range_info['shares_col']}{range_info['start_row']}:{range_info['shares_col']}{range_info['end_row']}"
                # Shareholders column is at padding_offset + 1 (within border)
                holder_col_letter = self._col_letter(self.padding_offset + 1)
                rounds_shares = f'SUMIF({holder_range}, {holder_col_letter}{row + 1}, {shares_range})'
        else:
            # Fallback to old method with direct string matching
            calc_type = rounds[round_idx].get('calculation_type', 'fixed_shares')
            shares_col_letter = self._get_shares_column_letter(calc_type)
            # Use actual holder name directly instead of cell reference
            holder_name_escaped = f'"{holder_name}"'
            rounds_shares = f'SUMIF(Rounds!A:A, {holder_name_escaped}, Rounds!{shares_col_letter}:{shares_col_letter})'
        
        # Get pro rata shares from Pro Rata Allocations sheet
        # Pro rata sheet has same row structure (holders in same order)
        # Each round has columns: Pro Rata Type, Pro Rata %, Pro Rata Shares, Price Per Share, Investment Amount, Separator
        # Pro Rata Shares is 2 columns after the start of each round section
        pro_rata_start_col = self._get_pro_rata_shares_col(round_idx, rounds)
        pro_rata_shares = f"'Pro Rata Allocations'!{pro_rata_start_col}{row + 1}"
        
        # Total new shares = rounds sheet shares + pro rata shares
        new_formula = f'=ROUND({rounds_shares} + {pro_rata_shares}, 0)'
        sheet.write_formula(row, new_col, new_formula, self.formats.get('table_number'))
        
        # TOTAL: Start + New (rounded to integer)
        start_cell = self._col_letter(start_col) + str(row + 1)
        new_cell = self._col_letter(new_col) + str(row + 1)
        total_formula = f"=ROUND(SUM({start_cell},{new_cell}), 0)"
        sheet.write_formula(row, total_col, total_formula, self.formats.get('table_number'))
        
        # PERCENTAGE: Total / Sum of all Totals for this round
        # Formula: =Total / SUM(All Totals in this round across all holders)
        total_cell = self._col_letter(total_col) + str(row + 1)
        total_col_letter = self._col_letter(total_col)
        # Sum range is from first holder to last holder in the same total column
        sum_range = f"{total_col_letter}{first_holder_row + 1}:{total_col_letter}{last_holder_row + 1}"
        percent_formula = f"=IFERROR({total_cell} / SUM({sum_range}), 0)"
        sheet.write_formula(row, percent_col, percent_formula, self.formats.get('table_percent'))
        
        # Separator (skip for last round)
        if is_last_round:
            col = col + 4
        else:
            col = col + 5
        return col
    
    def _get_shares_column_letter(self, calc_type: str) -> str:
        """Get the column letter for shares based on calculation type."""
        # Determine which column has shares based on calc_type
        if calc_type == 'fixed_shares':
            # Columns: holder_name, class_name, shares
            return 'C'  # shares is column C (3rd column)
        elif calc_type == 'target_percentage':
            # Columns: holder_name, class_name, target_percentage, calculated_shares
            return 'D'  # calculated_shares is column D
        elif calc_type == 'valuation_based':
            # Columns: holder_name, class_name, investment_amount, calculated_shares
            return 'D'  # calculated_shares is column D (4th column)
        elif calc_type == 'convertible':
            # Columns: holder_name, class_name, investment_amount, ..., calculated_shares
            return 'K'  # calculated_shares is column K (11th column)
        else:
            return 'D'  # Default to column D
    
    def _get_pro_rata_shares_col(self, round_idx: int, rounds: List[Dict[str, Any]]) -> str:
        """Get the column letter for pro rata shares in Pro Rata Allocations sheet."""
        # Pro Rata Allocations sheet structure (with padding):
        # Column 0: Outer padding
        # Column 1: Inner padding (border_start_col)
        # Column 2: Shareholders (padding_offset + 1)
        # Column 3: Description (padding_offset + 2)
        # Each round: Pro Rata Type, Pro Rata %, Pro Rata Shares, Price Per Share, Investment Amount, Separator
        # Pro Rata Shares is 2 columns after the start of each round
        # Start of round: padding_offset + 1 + 2 + (round_idx * 6)
        # Pro Rata Shares: padding_offset + 1 + 2 + (round_idx * 6) + 2
        padding_offset = 1  # Pro Rata sheet has padding_offset = 1
        col_idx = padding_offset + 1 + 2 + (round_idx * 6) + 2
        return self._col_letter(col_idx)
    
    def _get_shares_header(self, calc_type: str) -> str:
        """Return the header text for the shares column for a given calc_type."""
        if calc_type == 'fixed_shares':
            return 'Shares'
        # For target_percentage, valuation_based, and convertible the header used is 'Calculated Shares'
        return 'Calculated Shares'
    
    def _write_total_row(
        self,
        sheet: xlsxwriter.worksheet.Worksheet,
        rounds: List[Dict[str, Any]],
        data_rows_per_holder: List[int]
    ):
        """Write the total row at the bottom with spacing row before it."""
        if not data_rows_per_holder:
            return
        
        # Add spacing row before total
        row = data_rows_per_holder[-1] + 2
        sheet.write(row, self.padding_offset + 1, 'TOTAL', self.formats.get('total_label'))
        sheet.write(row, self.padding_offset + 2, '', self.formats.get('total_text'))
        col = self.padding_offset + 1 + 2
        
        for round_idx, round_data in enumerate(rounds):
            is_last_round = (round_idx == len(rounds) - 1)
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
                self.formats.get('total_number')
            )
            # Define named range for Pre-Round Shares for this round
            round_name_key = rounds[round_idx].get('name', '').replace(' ', '_')
            named_range_name = f"{round_name_key}_PreRoundShares"
            # Register with DLM and workbook (absolute reference)
            try:
                self.dlm.register_named_range(
                    named_range_name, self._get_sheet_name(), row, start_col
                )
            except Exception:
                # DLM may not require registration; continue with workbook name definition
                pass
            abs_cell_ref = f"'{self._get_sheet_name()}'!${start_col_letter}${row + 1}"
            self.workbook.define_name(named_range_name, abs_cell_ref)
            
            # NEW
            new_col_letter = self._col_letter(new_col)
            sheet.write_formula(
                row, new_col,
                f"=SUM({sheet_name}!{new_col_letter}{first_row}:{new_col_letter}{last_row})",
                self.formats.get('total_number')
            )
            
            # TOTAL
            total_col_letter = self._col_letter(total_col)
            sheet.write_formula(
                row, total_col,
                f"=SUM({sheet_name}!{total_col_letter}{first_row}:{total_col_letter}{last_row})",
                self.formats.get('total_number')
            )
            
            # PERCENTAGE - Sum of all percentages (should be 100%)
            percent_col_letter = self._col_letter(percent_col)
            sheet.write_formula(
                row, percent_col,
                f"=SUM({sheet_name}!{percent_col_letter}{first_row}:{percent_col_letter}{last_row})",
                self.formats.get('total_percent')
            )
            
            # Separator (skip for last round)
            if not is_last_round:
                sheet.write(row, col + 4, '', self.formats.get('total_text'))  # Separator
                col += 5
            else:
                col += 4
    
    def _col_letter(self, col_idx: int) -> str:
        """Convert 0-based column index to Excel column letter(s)."""
        result = []
        col_idx += 1  # Excel columns are 1-based
        while col_idx > 0:
            col_idx -= 1
            result.append(chr(col_idx % 26 + ord('A')))
            col_idx //= 26
        return ''.join(reversed(result))
