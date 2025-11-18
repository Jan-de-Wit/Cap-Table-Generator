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

    Pro-rata Shares are calculated AFTER regular round shares.
    """

    def __init__(self, workbook, data, formats, dlm, formula_resolver):
        """Initialize pro rata sheet generator."""
        super().__init__(workbook, data, formats, dlm, formula_resolver)
        self.round_ranges = {}  # Round ranges from rounds sheet
        self.shares_issued_refs = {}  # Shares issued cell references per round
        # Row range for holder data (for summing pro rata %)
        self.holder_data_range = {}
        # Padding offset for table positioning
        self.padding_offset = 1
        # Named ranges for SUMIF expressions per round (Option 7: Extract SUMIF to Named Range)
        self.sumif_named_ranges = {}  # round_idx -> named_range_name

    def _get_sheet_name(self) -> str:
        """Returns 'Pro Rata Allocations'."""
        return "Pro Rata Allocations"

    def generate(self) -> xlsxwriter.worksheet.Worksheet:
        """Generate the Pro Rata Allocations sheet."""
        sheet = self.workbook.add_worksheet('Pro Rata Allocations')
        self.sheet = sheet

        rounds = self.data.get('rounds', [])
        if not rounds:
            sheet.write(self.padding_offset, self.padding_offset,
                        'No rounds found', self.formats.get('text'))
            return sheet

        # Title row inside border (top-left of table, respecting padding)
        title_row = self.padding_offset + 1
        sheet.write(title_row, self.padding_offset + 1,
                    'Pro Rata Allocation', self.formats.get('round_header_plain'))

        # Extract holders with grouping
        holders_by_group, all_holders = self._get_holders_with_groups(rounds)

        if not all_holders:
            sheet.write(self.padding_offset + 1, self.padding_offset + 1,
                        'No instruments found', self.formats.get('text'))
            return sheet

        # Calculate table bounds for border (border includes 1 cell padding on all sides)
        # Border starts at padding_offset (1), content starts at padding_offset + 1 (2)
        border_start_row = self.padding_offset
        border_start_col = self.padding_offset
        # Calculate last column: padding + 1 (padding) + 2 (Shareholders + Description) + (rounds * 10) - 1
        # Each round has 10 columns (9 data + 1 separator), last round's separator is the last column
        num_rounds = len(rounds)
        border_end_col = self.padding_offset + 1 + 2 + (num_rounds * 10) - 1
        # Last row includes padding, so we need to calculate after writing data

        # Write headers aligned with title row for round names
        self._write_headers(sheet, rounds)

        # Write holder data with grouping (shifted by padding offset + 1 for content within border)
        # After padding + title/round names + column headers
        data_start_row = self.padding_offset + 1 + 2
        data_rows_per_holder, first_holder_row, last_holder_row = self._write_holder_data_with_groups(
            sheet, rounds, all_holders, holders_by_group, data_start_row
        )

        # Create named ranges for SUMIF expressions (Option 7: Extract SUMIF to Named Range)
        self._create_sumif_named_ranges(
            rounds, first_holder_row, last_holder_row)

        # Write total row
        self._write_total_row(sheet, rounds, all_holders,
                              first_holder_row, last_holder_row)

        # Calculate border end row (includes padding)
        border_end_row = last_holder_row + 2 + 1  # Total row + spacing + padding

        # Set up table formatting using utility function
        row_heights = [
            (0, 16.0),  # Outer padding row
            (border_start_row, 16.0),  # Inner padding row (top border row)
            (self.padding_offset + 1, 25),  # Title row (also round names row)
            (self.padding_offset + 2, 25),  # Column headers row
        ]

        column_widths = [
            (0, 0, 4.0),  # Outer padding column
            # Inner padding column (left border column)
            (border_start_col, border_start_col, 4.0),
            # Shareholders column
            (self.padding_offset + 1, self.padding_offset + 1, 35),
            # Description column
            (self.padding_offset + 2, self.padding_offset + 2, 35),
        ]

        # For each round, set widths for Pro-rata Rights, Super pro rata %, Exercise Type, Partial Amount, Partial %, Effective %, Pro-rata Shares, Price Per Share, Investment Amount (20) and separator (5)
        for round_idx in range(num_rounds):
            # Start column: padding + 1 (inner padding) + 2 (Shareholders + Description) + (round_idx * 10)
            start_col = self.padding_offset + 1 + 2 + (round_idx * 10)
            # Set Pro-rata Rights, Super pro rata %, Exercise Type, Partial Amount, Partial %, Effective %, Pro-rata Shares, Price Per Share, Investment Amount columns to width 20
            column_widths.append((start_col, start_col + 8, 20))
            # Set separator column to width 5
            separator_col = start_col + 9
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

        # Freeze columns and header rows (below column headers)
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

    def _sort_groups(self, groups: List[str]) -> List[str]:
        """
        Sort groups according to the default order:
        1. Founders
        2. ESOP
        3. Noteholders
        4. Investors
        5. Other groups (alphabetically)

        Args:
            groups: List of group names to sort

        Returns:
            Sorted list of group names
        """
        # Define the default order
        default_order = ['Founders', 'ESOP', 'Noteholders', 'Investors']

        # Separate groups into ordered and unordered
        ordered_groups = []
        unordered_groups = []

        for group in groups:
            if group in default_order:
                ordered_groups.append(group)
            else:
                unordered_groups.append(group)

        # Sort ordered groups by their position in default_order
        ordered_groups.sort(key=lambda g: default_order.index(g))

        # Sort unordered groups alphabetically
        unordered_groups.sort()

        # Combine: ordered groups first, then unordered groups
        return ordered_groups + unordered_groups

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

        # Build flat list: groups first (sorted by custom order), then ungrouped
        all_holders = []
        sorted_groups = self._sort_groups(list(holders_by_group.keys()))
        for group in sorted_groups:
            all_holders.extend(holders_by_group[group])
        all_holders.extend(ungrouped)

        return holders_by_group, all_holders

    def _write_headers(self, sheet: xlsxwriter.worksheet.Worksheet, rounds: List[Dict[str, Any]]):
        """Write the header rows (shifted by padding offset + 1 for content within border)."""
        # Place round names header on the same row as the title
        header_row = self.padding_offset + 1
        subheader_row = self.padding_offset + 2
        # Start after padding + "Shareholders" and "Description"
        start_col = self.padding_offset + 1 + 2

        # Write Shareholders and Description headers first
        sheet.write(subheader_row, self.padding_offset + 1,
                    'Shareholders', self.formats.get('header'))
        sheet.write(subheader_row, self.padding_offset +
                    2, '', self.formats.get('header'))

        # Use utility function to write round headers
        subheaders = ['Pro-rata Rights', 'Super pro rata %', 'Exercise Type',
                      'Partial Amount', 'Partial %', 'Effective %', 'Pro-rata Shares', 'Price per Share', 'Investment']
        self.write_round_headers(
            sheet,
            rounds,
            header_row,
            start_col,
            columns_per_round=9,
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
        pro_rata_type_rows_by_round = {}  # Track rows for dropdown validation per round

        for holder_name in all_holders:
            group = holder_to_group.get(holder_name, '')

            # Add group header and spacing row before new group
            if group and group != current_group:
                if current_group is not None:
                    # Add spacing row after previous group
                    row += 1
                # Write group header row (bold) - shifted by padding offset + 1 for content within border
                sheet.write(row, self.padding_offset + 1,
                            group, self.formats.get('label'))
                # Leave other columns empty for group header
                row += 1
                current_group = group
            elif not group and current_group is not None:
                # Add spacing row before ungrouped holders
                row += 1
                current_group = None

            # Write holder name - shifted by padding offset + 1 for content within border
            sheet.write(row, self.padding_offset + 1,
                        holder_name, self.formats.get('text'))
            # Description column - shifted by padding offset + 1 for content within border
            sheet.write(row, self.padding_offset + 2, holder_to_description.get(
                holder_name, ''), self.formats.get('italic_text'))
            col = self.padding_offset + 1 + 2

            # For each round, write pro rata data
            for round_idx, round_data in enumerate(rounds):
                type_col = col  # Pro-rata Rights column for this round
                col = self._write_round_pro_rata_data(
                    sheet, row, col, round_idx, holder_name, rounds,
                    first_holder_row, last_holder_row
                )

                # Track rows that have pro rata type cells for dropdown validation
                if round_idx not in pro_rata_type_rows_by_round:
                    pro_rata_type_rows_by_round[round_idx] = []
                pro_rata_type_rows_by_round[round_idx].append(row)

            data_rows.append(row)
            row += 1

        # Store row ranges for calculating sum of pro rata percentages
        self.holder_data_range = {
            'first_row': first_holder_row,
            'last_row': last_holder_row
        }

        # Add dropdown validation for pro rata type columns
        self._add_pro_rata_dropdowns(
            sheet, rounds, pro_rata_type_rows_by_round)

        return data_rows, first_holder_row, last_holder_row

    def _write_holder_data(
        self,
        sheet: xlsxwriter.worksheet.Worksheet,
        rounds: List[Dict[str, Any]],
        holders: List[str],
        data_start_row: int,
        first_holder_row: int,
        last_holder_row: int
    ):
        """Write holder data with pro rata calculations (legacy method, kept for compatibility)."""
        row = data_start_row
        pro_rata_type_rows_by_round = {}  # Track rows for dropdown validation per round

        for holder_name in holders:
            # Write holder name
            sheet.write(row, 0, holder_name, self.formats.get('text'))
            col = 1

            # For each round, write pro rata data
            for round_idx, round_data in enumerate(rounds):
                type_col = col  # Pro-rata Rights column for this round
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
        self._add_pro_rata_dropdowns(
            sheet, rounds, pro_rata_type_rows_by_round)

    def _has_shares_in_previous_rounds(
        self,
        holder_name: str,
        round_idx: int,
        rounds: List[Dict[str, Any]]
    ) -> bool:
        """
        Check if a shareholder has shares in previous rounds by examining JSON data.

        Args:
            holder_name: Name of the shareholder to check
            round_idx: Current round index (0-based)
            rounds: List of all rounds data

        Returns:
            True if holder has shares in any previous round, False otherwise
        """
        if round_idx == 0:
            # First round - no previous rounds
            return False

        # Check all previous rounds (0 to round_idx - 1)
        for prev_round_idx in range(round_idx):
            prev_round = rounds[prev_round_idx]
            prev_instruments = prev_round.get('instruments', [])

            # Check if holder has any instrument in this previous round
            for instrument in prev_instruments:
                if instrument.get('holder_name') == holder_name:
                    # Check if instrument has shares (initial_quantity, or calculated shares > 0)
                    # For fixed_shares, check initial_quantity
                    if 'initial_quantity' in instrument:
                        if instrument.get('initial_quantity', 0) > 0:
                            return True
                    # For other types, if the instrument exists, they likely have shares
                    # (valuation_based, target_percentage, convertible all result in shares)
                    # We can check if there's an investment_amount, target_percentage, principal, etc.
                    if any(key in instrument for key in ['investment_amount', 'target_percentage', 'principal', 'shares']):
                        # If any of these fields exist, the holder will have shares
                        return True

        return False

    def _write_round_pro_rata_data(
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
        """Write pro rata data for one round and return updated column position."""
        type_col = col
        pct_col = col + 1
        exercise_type_col = col + 2
        partial_amount_col = col + 3
        partial_pct_col = col + 4
        effective_pct_col = col + 5
        shares_col = col + 6
        pps_col = col + 7
        investment_col = col + 8
        separator_col = col + 9

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
        exercise_type = 'full'
        partial_exercise_amount = None
        partial_exercise_percentage = None
        if holder_instrument:
            pro_rata_type = holder_instrument.get('pro_rata_type', 'none')
            pro_rata_pct = holder_instrument.get('pro_rata_percentage')
            exercise_type = holder_instrument.get('exercise_type', 'full')
            partial_exercise_amount = holder_instrument.get(
                'partial_exercise_amount')
            partial_exercise_percentage = holder_instrument.get(
                'partial_exercise_percentage')

        # Check if holder has shares in previous rounds from JSON data
        has_previous_shares = self._has_shares_in_previous_rounds(
            holder_name, round_idx, rounds
        )

        if has_previous_shares:
            # Holder has shares in previous rounds - add dropdown with None, Standard, Super
            # Format pro rata type for display (capitalize first letter)
            pro_rata_type_display = pro_rata_type.capitalize() if pro_rata_type else 'None'
            sheet.write(row, type_col, pro_rata_type_display,
                        self.formats.get('text'))
            # Add dropdown validation
            sheet.data_validation(
                row, type_col, row, type_col,
                {
                    'validate': 'list',
                    'source': ['None', 'Standard', 'Super'],
                    'error_type': 'stop',
                    'error_title': 'Invalid Value',
                    'error_message': 'Please select one of: None, Standard, Super'
                }
            )
        else:
            # Holder has no shares in previous rounds - show "-"
            sheet.write(row, type_col, '-', self.formats.get('text'))

        # Get references needed for formulas (used regardless of has_previous_shares)
        type_col_letter = self._col_letter(type_col)
        type_cell_ref = f"{type_col_letter}{row + 1}"

        # Get holder's shares at start of round for formulas
        if round_idx == 0:
            holder_shares_start_ref = "0"
        else:
            prev_round_total_col = self._get_progression_total_col(
                round_idx - 1, rounds)
            holder_row = row + 1
            holder_shares_start_ref = f"'Cap Table'!{prev_round_total_col}{holder_row}"

        # Add conditional formatting as safety measure (in case someone manually edits the cell)
        # This will highlight if pro rata is enabled but holder has no shares
        if has_previous_shares:
            # Conditional formatting: highlight red if pro rata enabled (standard/super) but no prev round shares
            # This is a safety measure in case the Excel calculation shows 0 shares even though JSON had shares
            # Check for both lowercase and capitalized versions
            sheet.conditional_format(
                row, type_col, row, type_col,
                {
                    'type': 'formula',
                    'criteria': f'=AND(OR({type_cell_ref}="standard", {type_cell_ref}="super", {type_cell_ref}="Standard", {type_cell_ref}="Super"), {holder_shares_start_ref}<=0)',
                    'format': self.formats.get('error_text')
                }
            )

        # Pro Rata % column: dynamic formula based on pro_rata_type
        # For "standard": calculate ownership % = (holder_shares_start + shares issued to holder) / (pre_round_shares + total shares issued)
        # For "super": use the value from data (allow manual entry)
        # For "none": empty
        # Get references needed for ownership % calculation
        round_data = rounds[round_idx]
        round_name_key = self._sanitize_excel_name(round_data.get('name', ''))
        pre_round_shares_ref = f"{round_name_key}_PreRoundShares"

        # Get holder's shares issued in this round (from Rounds table)
        holder_row = row + 1
        holder_base_shares_ref = self._get_holder_base_shares_ref(
            round_idx, holder_row)

        # Get total shares issued in this round
        if round_idx in self.shares_issued_refs:
            shares_issued_total_ref = self.shares_issued_refs[round_idx]
        elif round_idx in self.round_ranges:
            range_info = self.round_ranges[round_idx]
            table_name = range_info.get('table_name')
            if table_name:
                shares_issued_total_ref = f"SUM({table_name}[[#All],[Shares]])"
            else:
                shares_col = range_info.get('shares_col', 'D')
                shares_range = f"Rounds!{shares_col}{range_info['start_row']}:{shares_col}{range_info['end_row']}"
                shares_issued_total_ref = f"SUM({shares_range})"
        else:
            shares_issued_total_ref = "0"

        # Get previous round ownership % from Cap Table sheet (at end of previous round, before current round shares)
        # This is needed for Effective % column (prev_round_ownership_pct_ref)
        if round_idx == 0:
            # First round: no previous round, so ownership % is 0
            prev_round_ownership_pct_ref = "0"
        else:
            prev_round_percent_col = self._get_progression_percent_col(
                round_idx - 1, rounds)
            holder_row = row + 1
            prev_round_ownership_pct_ref = f"'Cap Table'!{prev_round_percent_col}{holder_row}"

        # Super pro rata % column: only filled when super pro rata % was included in input
        # For "super": display the super pro rata % value (from data, editable) - only if provided in input
        # For "standard" or "none": empty
        # Calculate ownership % = (holder_shares_start + shares issued to holder) / (pre_round_shares + total shares issued)
        # This accounts for shares already issued in the round (kept for current_ownership_pct_ref used elsewhere)
        holder_total_shares_ref = f"({holder_shares_start_ref} + {holder_base_shares_ref})"
        total_shares_ref = f"({pre_round_shares_ref} + {shares_issued_total_ref})"
        ownership_pct_formula = f"IFERROR({holder_total_shares_ref} / {total_shares_ref}, 0)"

        # Only fill Super pro rata % when super type is selected AND pro_rata_pct was provided in input
        if pro_rata_type and pro_rata_type.lower() == 'super' and pro_rata_pct is not None:
            # For "super": write the value directly (editable, not a formula)
            sheet.write(row, pct_col, pro_rata_pct,
                        self.formats.get('table_percent'))
        else:
            # For "standard", "none", or super without pro_rata_pct: empty
            sheet.write(row, pct_col, '', self.formats.get('table_percent'))

        # Get cell references needed for Effective % formula (calculate before writing columns)
        pct_col_letter = self._col_letter(pct_col)
        pct_cell_ref = f"{pct_col_letter}{row + 1}"
        exercise_type_col_letter = self._col_letter(exercise_type_col)
        exercise_type_cell_ref = f"{exercise_type_col_letter}{row + 1}"
        partial_amount_col_letter = self._col_letter(partial_amount_col)
        partial_amount_cell_ref = f"{partial_amount_col_letter}{row + 1}"
        partial_pct_col_letter = self._col_letter(partial_pct_col)
        partial_pct_cell_ref = f"{partial_pct_col_letter}{row + 1}"

        # Get round valuation reference (post-money valuation)
        round_name_key = self._sanitize_excel_name(round_data.get('name', ''))
        post_money_valuation_ref = f"{round_name_key}_PostMoneyValuation"

        # Get current ownership % for budget-based calculations
        # Current ownership % = (holder_shares_start + shares issued to holder) / (pre_round_shares + total shares issued)
        # This is used for partial amount calculations in Effective % column
        current_ownership_pct_ref = ownership_pct_formula

        # Exercise Type column: write value from data
        exercise_type_display = exercise_type.capitalize() if exercise_type else 'Full'
        sheet.write(row, exercise_type_col, exercise_type_display,
                    self.formats.get('text'))
        # Add dropdown validation
        sheet.data_validation(
            row, exercise_type_col, row, exercise_type_col,
            {
                'validate': 'list',
                'source': ['Full', 'Partial'],
                'error_type': 'stop',
                'error_title': 'Invalid Value',
                'error_message': 'Please select one of: Full, Partial'
            }
        )

        # Partial Exercise Amount column: write value from data (if exists)
        if partial_exercise_amount is not None:
            sheet.write(row, partial_amount_col, partial_exercise_amount,
                        self.formats.get('table_currency'))
        else:
            sheet.write(row, partial_amount_col, '', self.formats.get('text'))

        # Partial Exercise Percentage column: write value from data (if exists)
        if partial_exercise_percentage is not None:
            sheet.write(row, partial_pct_col, partial_exercise_percentage,
                        self.formats.get('table_percent'))
        else:
            sheet.write(row, partial_pct_col, '', self.formats.get('text'))

        # Get price per share reference for converting partial amount to effective %
        pre_money_valuation_ref = f"{round_name_key}_PreMoneyValuation"
        price_per_share_ref = f"IFERROR({pre_money_valuation_ref} / {pre_round_shares_ref}, 0)"

        # Effective % column: calculate based on the new unified formula
        effective_pct_formula = self._create_effective_pct_formula(
            type_cell_ref, pct_cell_ref, exercise_type_cell_ref,
            partial_amount_cell_ref, partial_pct_cell_ref, post_money_valuation_ref,
            current_ownership_pct_ref, prev_round_ownership_pct_ref, price_per_share_ref, pre_round_shares_ref,
            round_idx, row, first_holder_row, last_holder_row
        )
        sheet.write_formula(row, effective_pct_col, effective_pct_formula,
                            self.formats.get('table_percent'))

        # Get effective % cell reference for shares calculation
        effective_pct_col_letter = self._col_letter(effective_pct_col)
        effective_pct_cell_ref = f"{effective_pct_col_letter}{row + 1}"

        # Create formulas for each pro rata type
        # Pass cell references instead of hardcoded values so formulas update when Excel cells change
        pro_rata_formula = self._create_pro_rata_formula(
            round_idx, holder_name, rounds, row, type_cell_ref, effective_pct_cell_ref,
            current_ownership_pct_ref, pre_round_shares_ref, first_holder_row, last_holder_row
        ).lstrip('=')

        # Shares calculation: use effective % approach
        # The effective % already incorporates partial amount constraints (capped to ensure investment doesn't exceed partial amount)
        # So we just use the effective % approach without any additional capping
        # Dynamic formula using nested IF to check pro_rata_type cell
        # Handles: "none", "None", "-", "standard", "super", "Standard", "Super", or empty/invalid (defaults to 0)
        # Check for both lowercase and capitalized versions
        # Format with line breaks and indentation for readability
        shares_formula = (
            f"=IFERROR("
            f"IF("
            f"OR({type_cell_ref}=\"\", {type_cell_ref}=\"none\", {type_cell_ref}=\"None\", {type_cell_ref}=\"-\"), "
            f"0, "
            f"{pro_rata_formula}"
            f"), "
            f"0"
            f")"
        )
        sheet.write_formula(row, shares_col, shares_formula,
                            self.formats.get('table_number'))

        # Price Per Share column: calculate from pre-round valuation cap divided by pre-round shares
        pps_formula = f"=IFERROR({pre_money_valuation_ref} / {pre_round_shares_ref}, 0)"
        sheet.write_formula(row, pps_col, pps_formula,
                            self.formats.get('table_currency'))

        # Investment Amount column: Price Per Share * Pro-rata Shares
        shares_col_letter = self._col_letter(shares_col)
        shares_cell_ref = f"{shares_col_letter}{row + 1}"
        pps_col_letter = self._col_letter(pps_col)
        pps_cell_ref = f"{pps_col_letter}{row + 1}"
        investment_formula = f"=IFERROR({pps_cell_ref} * {shares_cell_ref}, 0)"
        sheet.write_formula(row, investment_col,
                            investment_formula, self.formats.get('table_currency'))

        # Separator (skip for last round)
        if not is_last_round:
            sheet.write(row, separator_col, '', self.formats.get('text'))
            return separator_col + 1
        else:
            return investment_col + 1

    def _create_effective_pct_formula(
        self,
        type_cell_ref: str,
        pct_cell_ref: str,
        exercise_type_cell_ref: str,
        partial_amount_cell_ref: str,
        partial_pct_cell_ref: str,
        post_money_valuation_ref: str,
        current_ownership_pct_ref: str,
        prev_round_ownership_pct_ref: str,
        price_per_share_ref: str,
        pre_round_shares_ref: str,
        round_idx: int,
        row: int,
        first_holder_row: int,
        last_holder_row: int
    ) -> str:
        """
        Generate an easy-to-read Excel formula for the Effective % column.

        - If full pro rata rights exercised:
            - type == standard: prev round ownership %
            - type == super: super pro rata % (from Super pro rata % column, only if provided in input)
        - Else if partial rights exercised:
            - type == standard: partial ownership % (min(partial %, prev round ownership %) or capped by partial amount if specified)
            - type == super: (min(partial %, super pro rata %) or capped by partial amount if specified)
        - If type is 'none' or cell is empty, return ""

        Note: Uses previous round ownership % for standard type calculations.
        For super type, uses Super pro rata % column value (only filled when provided in input).
        For partial amount calculations, uses current ownership % (after current round shares).
        """

        # Logical conditions for Excel
        is_none = f"OR({type_cell_ref}=\"\", {type_cell_ref}=\"none\", {type_cell_ref}=\"-\", {type_cell_ref}=\"None\", UPPER(TRIM({type_cell_ref}))=\"NONE\")"
        is_standard = f"OR({type_cell_ref}=\"standard\", {type_cell_ref}=\"Standard\", UPPER(TRIM({type_cell_ref}))=\"STANDARD\")"
        is_super = f"OR({type_cell_ref}=\"super\", {type_cell_ref}=\"Super\", UPPER(TRIM({type_cell_ref}))=\"SUPER\")"

        # For full exercises: use previous round ownership % for standard, super pro rata % for super (if provided)
        # For super: only use pct_cell_ref if it's not blank, otherwise return empty
        pro_rata_pct_expr = (
            f"IF(\n"
            f"    {is_standard}, {prev_round_ownership_pct_ref},\n"
            f"    IF({is_super}, IF(NOT(ISBLANK({pct_cell_ref})), {pct_cell_ref}, \"\"), \"\")\n"
            f")"
        )

        # Check exercise type (case-insensitive)
        is_full = f"OR(UPPER(TRIM({exercise_type_cell_ref}))=\"FULL\", {exercise_type_cell_ref}=\"Full\")"
        is_partial = f"OR(UPPER(TRIM({exercise_type_cell_ref}))=\"PARTIAL\", {exercise_type_cell_ref}=\"Partial\")"

        # Whether a partial % is entered
        has_partial_pct = f"AND(NOT(ISBLANK({partial_pct_cell_ref})), {partial_pct_cell_ref}<>0)"

        # Whether a partial $ amount is entered
        has_partial_amount = f"AND(NOT(ISBLANK({partial_amount_cell_ref})), {partial_amount_cell_ref}<>0)"
        # For partial amount: add current ownership % (after current round shares) to the partial amount percentage
        partial_amount_pct_from_valuation = f"IFERROR({partial_amount_cell_ref}/{post_money_valuation_ref}, 0)"
        partial_amount_pct_expr = f"IF({has_partial_amount}, {current_ownership_pct_ref} + {partial_amount_pct_from_valuation}, 999999)"

        # For partial exercises:
        # - standard: MIN(partial_pct, prev_round_ownership_pct) then cap by (current_ownership_pct + partial_amount_pct) if partial_amount specified
        # - super: MIN(partial_pct, super_pro_rata_pct) then cap by (current_ownership_pct + partial_amount_pct) if partial_amount specified
        # If partial_pct is not specified, use a large number so MIN will use the pro_rata_pct
        # (or if partial_amount is specified, it will be capped by that)
        partial_pct_value = f"IF({has_partial_pct}, {partial_pct_cell_ref}, 999999)"

        # Calculate MIN(partial_pct, pro_rata_pct) for each type
        # Use previous round ownership % for standard (not current ownership %)
        # For super: use pct_cell_ref if not blank, otherwise use a large number (will be capped by partial_amount if specified)
        partial_standard_expr = f"MIN({partial_pct_value}, {prev_round_ownership_pct_ref})"
        partial_super_expr = f"MIN({partial_pct_value}, IF(NOT(ISBLANK({pct_cell_ref})), {pct_cell_ref}, 999999))"

        # Then cap by (current_ownership_pct + partial_amount_pct) if partial_amount is specified
        partial_standard_final = f"MIN({partial_standard_expr}, {partial_amount_pct_expr})"
        partial_super_final = f"MIN({partial_super_expr}, {partial_amount_pct_expr})"

        # Compose the human-readable formula, pretty formatted
        # First check exercise type: if Full, use full rights; if Partial, use partial calculations
        formula = (
            f"=IF(\n"
            f"    {is_none}, \"\",\n"
            f"    IF(\n"
            f"        {is_full},\n"
            f"        {pro_rata_pct_expr},\n"
            f"        IF(\n"
            f"            {is_partial},\n"
            f"            IF(\n"
            f"                {is_standard}, {partial_standard_final},\n"
            f"                IF({is_super}, {partial_super_final}, \"\")\n"
            f"            ),\n"
            f"            \"\"\n"
            f"        )\n"
            f"    )\n"
            f")"
        )

        return formula

    def _get_sum_numerator_ref(
        self,
        round_idx: int,
        first_holder_row: int,
        last_holder_row: int,
        V_ref: str,
        P_ref: str
    ) -> str:
        """
        Get reference to sum of numerator terms across all holders for the denominator calculation.

        For each holder j, calculates:
        min(S_a,j * partial_pct_j (if defined, else S_a,j), partial_amount_j / P (if defined, else S_a,j))

        Where S_a,j = (target_pct_j * V) / P

        Returns an Excel formula that sums this across all holders in the round.
        """
        sheet_name = self._get_sheet_name()

        # Get column references for this round
        type_col = self.padding_offset + 1 + 2 + (round_idx * 10)
        pct_col = type_col + 1
        partial_pct_col = type_col + 5
        partial_amount_col = type_col + 4

        type_col_letter = self._col_letter(type_col)
        pct_col_letter = self._col_letter(pct_col)
        partial_pct_col_letter = self._col_letter(partial_pct_col)
        partial_amount_col_letter = self._col_letter(partial_amount_col)

        # Get ownership % column reference (we'll need to calculate this per row)
        # Ownership % is calculated as: (holder_shares_start + shares issued) / (pre_round_shares + total shares issued)
        # For now, we'll reference the Super pro rata % column (though it's only filled for super type)
        # and calculate ownership % for all holders

        # Build ranges
        type_range = f"'{sheet_name}'!{type_col_letter}{first_holder_row + 1}:{type_col_letter}{last_holder_row + 1}"
        pct_range = f"'{sheet_name}'!{pct_col_letter}{first_holder_row + 1}:{pct_col_letter}{last_holder_row + 1}"
        partial_pct_range = f"'{sheet_name}'!{partial_pct_col_letter}{first_holder_row + 1}:{partial_pct_col_letter}{last_holder_row + 1}"
        partial_amount_range = f"'{sheet_name}'!{partial_amount_col_letter}{first_holder_row + 1}:{partial_amount_col_letter}{last_holder_row + 1}"

        # For each holder, we need to calculate:
        # 1. target_pct_j (based on type)
        # 2. S_a,j = (target_pct_j * V) / P
        # 3. min(S_a,j * partial_pct_j (if defined, else S_a,j), partial_amount_j / P (if defined, else S_a,j))

        # This is complex to do in a single SUM formula. We'll use SUMPRODUCT with array operations.
        # For standard: target_pct = ownership_pct (which is in pct_range)
        # For super: target_pct = pct_range (which contains the absolute target percentage)
        # For none: target_pct = 0

        # Check if type is standard or super
        is_standard_or_super = f"(UPPER({type_range})=\"STANDARD\") + (UPPER({type_range})=\"SUPER\")"

        # For standard: target_pct = pct_range (which contains ownership %)
        # For super: target_pct = pct_range (which contains the absolute target percentage)
        # So for both, target_pct = pct_range when type is standard or super, else 0
        target_pct_array = f"IF({is_standard_or_super}, {pct_range}, 0)"

        # S_a,j = (target_pct_j * V) / P
        S_a_array = f"IFERROR(({target_pct_array} * {V_ref}) / {P_ref}, 0)"

        # Check if partial_pct is defined (not blank and not 0)
        has_partial_pct_array = f"(NOT(ISBLANK({partial_pct_range})) * ({partial_pct_range}<>0))"
        # S_a,j * partial_pct_j (if defined, else S_a,j)
        S_a_with_partial_pct_array = f"IF({has_partial_pct_array}, {S_a_array} * {partial_pct_range}, {S_a_array})"

        # Check if partial_amount is defined
        has_partial_amount_array = f"(NOT(ISBLANK({partial_amount_range})) * ({partial_amount_range}<>0))"
        # partial_amount_j / P (if defined, else S_a,j)
        partial_amount_over_P_array = f"IFERROR({partial_amount_range} / {P_ref}, 0)"
        partial_amount_term_array = f"IF({has_partial_amount_array}, {partial_amount_over_P_array}, {S_a_array})"

        # min(S_a_with_partial_pct, partial_amount_term) for each holder
        # Use IF to implement element-wise MIN: if S_a_with_partial_pct <= partial_amount_term, use S_a_with_partial_pct, else use partial_amount_term
        min_array = f"IF({S_a_with_partial_pct_array} <= {partial_amount_term_array}, {S_a_with_partial_pct_array}, {partial_amount_term_array})"

        # Sum across all holders (only for standard/super types)
        # Multiply by is_standard_or_super to exclude "none" types
        sum_formula = f"SUMPRODUCT({is_standard_or_super}, {min_array})"

        return sum_formula

    def _create_pro_rata_formula(
        self,
        round_idx: int,
        holder_name: str,
        rounds: List[Dict[str, Any]],
        row: int,
        type_cell_ref: str,
        effective_pct_ref: str,
        current_ownership_pct_ref: str,
        pre_round_shares_ref: str,
        first_holder_row: int,
        last_holder_row: int
    ) -> str:
        """Create formula for Pro-rata Shares using target percentage.

        Formula: shares = (target % * (shares prevRound + shares issued this round) / (1 - sum of target % in round)) - current shares

        The target percentage is calculated the same way as in _create_effective_pct_formula:
        - For "none": target_pct_i = 0
        - For "standard": target_pct_i = ownership_pct_i
        - For "super": target_pct_i = pct_cell_ref (which contains ownership_pct_i + super_pro_rata_pct_i)

        Args:
            type_cell_ref: Cell reference for Pro-rata Rights column
            pct_cell_ref: Cell reference for Super pro rata % column
            current_ownership_pct_ref: Formula reference for current ownership percentage
            pre_round_shares_ref: Named range reference for pre-round shares
        """
        round_data = rounds[round_idx]
        round_name_key = self._sanitize_excel_name(round_data.get('name', ''))
        pre_round_shares_ref = f"{round_name_key}_PreRoundShares"

        # Base round shares (before pro rata)
        if round_idx in self.shares_issued_refs:
            shares_issued_ref = self.shares_issued_refs[round_idx]
        elif round_idx in self.round_ranges:
            range_info = self.round_ranges[round_idx]
            table_name = range_info.get('table_name')
            if table_name:
                # Prefer structured references to the table's unified shares column header
                shares_issued_ref = f"SUM({table_name}[[#All],[Shares]])"
            else:
                # Fallback to A1-style column range if table is unavailable
                shares_col = range_info.get('shares_col', 'D')
                shares_range = f"Rounds!{shares_col}{range_info['start_row']}:{shares_col}{range_info['end_row']}"
                shares_issued_ref = f"SUM({shares_range})"
        else:
            shares_issued_ref = "0"

        # Holder's current shares before pro rata = prev round total + base shares issued this round
        prev_round_total_col = self._get_progression_total_col(
            round_idx - 1, rounds) if round_idx > 0 else None
        holder_row = row + 1
        prev_total_ref = f"'Cap Table'!{prev_round_total_col}{holder_row}" if prev_round_total_col else "0"
        holder_base_shares_ref = self._get_holder_base_shares_ref(
            round_idx, holder_row)
        holder_shares_start_ref = f"({prev_total_ref} + {holder_base_shares_ref})"

        # Aggregates across participants - use target % instead of effective %
        sum_target_pct_ref = self._get_sum_effective_pct_ref(
            round_idx, rounds, first_holder_row, last_holder_row)
        sum_current_shares_ref = self._get_sum_current_shares_ref(
            round_idx, rounds, first_holder_row, last_holder_row)

        # Formula based on ownership.py reference:
        # T = (P + B - C) / (1 - R)
        # where P = pre_round_shares, B = shares_issued, C = sum_current_shares, R = sum_target_pct
        numerator = f"({pre_round_shares_ref} + {shares_issued_ref} - {sum_current_shares_ref})"
        denominator = f"(1 - {sum_target_pct_ref})"
        total_shares = f"IFERROR({numerator} / {denominator}, 0)"

        # Calculate target shares for this participant: target_pct * total_shares
        target_shares = f"({effective_pct_ref} * {total_shares})"

        # Calculate shares to purchase: target_shares - current_shares
        shares_to_purchase = f"({target_shares} - {holder_shares_start_ref})"

        # Final result: max(0, shares_to_purchase) to ensure non-negative
        formula = (
            f"=IFERROR(\n"
            f"    MAX(0, {shares_to_purchase}),\n"
            f"    0\n"
            f")"
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

        The Super pro rata % column contains:
        - For "super": fixed super pro rata % (only if provided in input)
        - For "standard" or "none": empty

        Returns an Excel SUM formula that sums all Super pro rata % values in this round's column.
        This will be embedded in the Pro-rata Shares calculation formulas.
        """
        # Build SUM over holder data rows directly so formulas are valid during row creation
        first_row = first_holder_row
        last_row = last_holder_row

        # Super pro rata % column for this round
        # Column structure: type, pct, exercise_type, partial_amount, partial_pct, effective_pct, shares, pps, investment, separator
        # Each round has 10 columns (9 data + 1 separator)
        # Column position: padding + 1 (inner padding) + 2 (Shareholders + Description) + round_idx * 10
        type_col = self.padding_offset + 1 + 2 + (round_idx * 10)
        pct_col = type_col + 1
        pct_col_letter = self._col_letter(pct_col)

        # Create Excel SUM formula for the Super pro rata % column in this round
        sheet_name = self._get_sheet_name()
        pct_range = f"'{sheet_name}'!{pct_col_letter}{first_row + 1}:{pct_col_letter}{last_row + 1}"
        sum_pro_rata_pct_formula = f"SUM({pct_range})"
        return sum_pro_rata_pct_formula

    def _get_sum_effective_pct_ref(
        self,
        round_idx: int,
        rounds: List[Dict[str, Any]],
        first_holder_row: int,
        last_holder_row: int
    ) -> str:
        """
        Get reference to the total row cell that contains the sum of effective percentages in this round.

        The total row is at last_holder_row + 2, and the Effective % column is at col + 5.

        Returns a cell reference to the total row's Effective % cell.
        This will be embedded in the Pro-rata Shares calculation formulas.
        """
        # Total row is at last_holder_row + 2 (spacing row before it)
        total_row = last_holder_row + 2

        # Effective % column for this round
        # Column structure: type, pct, exercise_type, partial_amount, partial_pct, effective_pct, shares, pps, investment, separator
        # Each round has 10 columns (9 data + 1 separator)
        # Column position: padding + 1 (inner padding) + 2 (Shareholders + Description) + round_idx * 10
        type_col = self.padding_offset + 1 + 2 + (round_idx * 10)
        effective_pct_col = type_col + 5
        effective_pct_col_letter = self._col_letter(effective_pct_col)

        # Reference the total row cell directly (Excel is 1-based, so add 1 to row)
        sheet_name = self._get_sheet_name()
        total_cell_ref = f"'{sheet_name}'!{effective_pct_col_letter}{total_row + 1}"
        return total_cell_ref

    def _get_sum_current_shares_ref(
        self,
        round_idx: int,
        rounds: List[Dict[str, Any]],
        first_holder_row: int,
        last_holder_row: int
    ) -> str:
        """
        Sum of current shares (pre-pro-rata) for STANDARD and SUPER rows in this round.
        Simplified to check if type is not "None" and not empty.
        Uses named range for holder names when available (Option 7).
        """
        # Build ranges
        sheet_name = self._get_sheet_name()
        # Column structure: type, pct, exercise_type, partial_amount, partial_pct, effective_pct, shares, pps, investment, separator
        # Each round has 10 columns (9 data + 1 separator)
        # Column position: padding + 1 (inner padding) + 2 (Shareholders + Description) + round_idx * 10
        type_col = self.padding_offset + 1 + 2 + (round_idx * 10)
        type_col_letter = self._col_letter(type_col)
        type_range = f"'{sheet_name}'!{type_col_letter}{first_holder_row + 1}:{type_col_letter}{last_holder_row + 1}"

        rounds_holder_range, rounds_shares_range = self._get_rounds_holder_and_shares_ranges(
            round_idx)
        # Use named range for holder names if available (Option 7)
        if round_idx in self.sumif_named_ranges:
            holder_name_range = "ProRata_HolderNames"
        else:
            holder_name_col_letter = self._col_letter(self.padding_offset + 1)
            holder_name_range = f"'{sheet_name}'!{holder_name_col_letter}{first_holder_row + 1}:{holder_name_col_letter}{last_holder_row + 1}"
        base_sum_array = f"SUMIF({rounds_holder_range}, {holder_name_range}, {rounds_shares_range})"

        # Progression range is 0 in the first round
        if round_idx == 0:
            progression_range = "0"
        else:
            prev_round_total_col = self._get_progression_total_col(
                round_idx - 1, rounds)
            progression_range = f"'Cap Table'!{prev_round_total_col}{first_holder_row + 1}:{prev_round_total_col}{last_holder_row + 1}"

        type_filter = f"((UPPER({type_range})=\"STANDARD\") + (UPPER({type_range})=\"SUPER\")>0)"
        return f"SUMPRODUCT(--({type_filter}), {progression_range} + {base_sum_array})"

    def _get_sum_current_ownership_pct_ref(
        self,
        round_idx: int,
        rounds: List[Dict[str, Any]],
        first_holder_row: int,
        last_holder_row: int,
        pre_round_shares_ref: str,
        shares_issued_ref: str
    ) -> str:
        """
        Get reference to Excel formula that calculates the sum of current ownership % for all holders in this round.

        Current ownership % for each holder = (holder_shares_start + shares issued to holder) / (pre_round_shares + total shares issued)

        Sum of current ownership % = sum(holder_shares_start + shares issued to holder) / (pre_round_shares + total shares issued)

        This sums across all holders who have pro rata rights (STANDARD or SUPER).

        Returns an Excel formula that calculates the sum of current ownership percentages.
        """
        # Get sum of (holder_shares_start + shares issued to holder) for all STANDARD and SUPER holders
        # This is the same as sum_current_shares_ref
        sum_current_shares_ref = self._get_sum_current_shares_ref(
            round_idx, rounds, first_holder_row, last_holder_row)

        # Sum of current ownership % = sum_current_shares / (pre_round_shares + total shares issued)
        numerator = sum_current_shares_ref
        denominator = f"({pre_round_shares_ref} + {shares_issued_ref})"

        sum_current_ownership_pct_formula = f"IFERROR({numerator} / {denominator}, 0)"
        return sum_current_ownership_pct_formula

    def _create_sumif_named_ranges(
        self,
        rounds: List[Dict[str, Any]],
        first_holder_row: int,
        last_holder_row: int
    ) -> None:
        """
        Create named ranges for SUMIF expressions per round (Option 7: Extract SUMIF to Named Range).

        This creates a named range for the holder name range that can be reused in SUMIF formulas,
        reducing formula complexity.
        """
        sheet_name = self._get_sheet_name()
        holder_name_col_letter = self._col_letter(self.padding_offset + 1)
        holder_name_range = f"'{sheet_name}'!{holder_name_col_letter}{first_holder_row + 1}:{holder_name_col_letter}{last_holder_row + 1}"

        # Create a named range for the holder names range (used in SUMIF)
        named_range_name = "ProRata_HolderNames"
        try:
            self.dlm.register_named_range(
                named_range_name, sheet_name, first_holder_row, self.padding_offset + 1
            )
        except Exception:
            pass
        self.workbook.define_name(named_range_name, holder_name_range)

        # Create named ranges for each round's SUMIF base formula
        for round_idx, round_data in enumerate(rounds):
            rounds_holder_range, rounds_shares_range = self._get_rounds_holder_and_shares_ranges(
                round_idx)
            round_name_key = self._sanitize_excel_name(
                round_data.get('name', ''))

            # Create named range for the SUMIF lookup ranges
            sumif_base_name = f"{round_name_key}_ProRata_BaseShares"
            # Store the ranges for use in formulas
            self.sumif_named_ranges[round_idx] = {
                'holder_range': rounds_holder_range,
                'shares_range': rounds_shares_range,
                'named_range_base': sumif_base_name
            }

    def _get_holder_base_shares_ref(self, round_idx: int, holder_row_1_based: int) -> str:
        """
        SUMIF over Rounds for base shares issued to the holder in this round.
        For single holder lookup, we use the individual cell reference.
        Named ranges are used in array operations (see _get_sum_current_shares_ref).
        """
        rounds_holder_range, rounds_shares_range = self._get_rounds_holder_and_shares_ranges(
            round_idx)
        sheet_name = self._get_sheet_name()
        # Shareholders column is at padding_offset + 1 (within border)
        holder_name_col_letter = self._col_letter(self.padding_offset + 1)
        holder_name_cell = f"'{sheet_name}'!{holder_name_col_letter}{holder_row_1_based}"

        # For single holder lookup, use the cell reference directly
        # Named range is used for array operations in _get_sum_current_shares_ref
        return f"IFERROR(SUMIF({rounds_holder_range}, {holder_name_cell}, {rounds_shares_range}), 0)"

    def _get_rounds_holder_and_shares_ranges(self, round_idx: int) -> tuple:
        """Return tuple of (holder_range, shares_range) for the given round on Rounds sheet."""
        if round_idx in self.round_ranges:
            range_info = self.round_ranges[round_idx]
            table_name = range_info.get('table_name')
            if table_name:
                # Prefer structured references when table exists. The shares column header is unified as 'Shares'.
                holder_range = f"{table_name}[[#All],[Holder Name]]"
                shares_range = f"{table_name}[[#All],[Shares]]"
                return holder_range, shares_range
            holder_col = range_info.get('holder_col', 'A')
            shares_col = range_info.get('shares_col', 'D')
            holder_range = f"Rounds!{holder_col}{range_info['start_row']}:{holder_col}{range_info['end_row']}"
            shares_range = f"Rounds!{shares_col}{range_info['start_row']}:{shares_col}{range_info['end_row']}"
            return holder_range, shares_range
        # Fallback to empty ranges that sum to 0
        return "Rounds!A1:A1", "Rounds!A1:A1"

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
        col_idx = 2 + (round_idx * 5) + 4
        return self._col_letter(col_idx)

    def _get_progression_percent_col(self, round_idx: int, rounds: List[Dict[str, Any]]) -> str:
        """Get the column letter for the Percentage column of a round in progression sheet."""
        # Each round has 4 columns: Start, New, Total, %
        # % is 3 columns after Start
        # Formula: col = 2 + (round_idx * 5) + 3 (for % column) + 2 (for Padding)
        col_idx = 2 + (round_idx * 5) + 3 + 2
        return self._col_letter(col_idx)

    def _write_total_row(
        self,
        sheet: xlsxwriter.worksheet.Worksheet,
        rounds: List[Dict[str, Any]],
        holders: List[str],
        first_holder_row: int,
        last_holder_row: int
    ):
        """Write the total row at the bottom with spacing row before it."""
        if not holders:
            return

        # Add spacing row before total
        row = last_holder_row + 2
        sheet.write(row, self.padding_offset + 1, 'TOTAL',
                    self.formats.get('total_label'))
        sheet.write(row, self.padding_offset + 2, '', self.formats.get(
            'total_text'))  # Description column
        col = self.padding_offset + 1 + 2

        for round_idx, round_data in enumerate(rounds):
            is_last_round = (round_idx == len(rounds) - 1)
            # Column structure: type, pct, exercise_type, partial_amount, partial_pct, effective_pct, shares, pps, investment, separator
            type_col = col
            pct_col = col + 1
            exercise_type_col = col + 2  # Skip in total row
            partial_amount_col = col + 3  # Skip in total row
            partial_pct_col = col + 4  # Skip in total row
            effective_pct_col = col + 5
            shares_col = col + 6
            pps_col = col + 7
            investment_col = col + 8
            separator_col = col + 9

            sheet.write(row, type_col, '', self.formats.get('total_text'))
            # Sum all Super pro rata percentages for this round
            pct_col_letter = self._col_letter(pct_col)
            sheet.write_formula(
                row, pct_col,
                f"=SUM({pct_col_letter}{first_holder_row + 1}:{pct_col_letter}{last_holder_row + 1})",
                self.formats.get('total_percent')
            )
            # Highlight when total pro rata % >= 100% (red background)
            sheet.conditional_format(
                row, pct_col, row, pct_col,
                {
                    'type': 'cell',
                    'criteria': '>=',
                    'value': 1,
                    'format': self.formats.get('error')
                }
            )

            # Add data validation with error message for sum >= 100%
            pct_cell_ref = f"{pct_col_letter}{row + 1}"
            sum_range = f"{pct_col_letter}{first_holder_row + 1}:{pct_col_letter}{last_holder_row + 1}"
            sheet.data_validation(
                row, pct_col, row, pct_col,
                {
                    'validate': 'custom',
                    'value': f'={sum_range}<1',
                    'error_type': 'stop',
                    'error_title': 'Invalid Pro Rata Percentage',
                    'error_message': 'The sum of pro rata percentages in this round cannot be 100% or greater. Please adjust the values.'
                }
            )

            # Sum all effective percentages for this round
            effective_pct_col_letter = self._col_letter(effective_pct_col)
            sheet.write_formula(
                row, effective_pct_col,
                f"=SUM({effective_pct_col_letter}{first_holder_row + 1}:{effective_pct_col_letter}{last_holder_row + 1})",
                self.formats.get('total_percent')
            )
            # Highlight when total effective % >= 100% (red background)
            sheet.conditional_format(
                row, effective_pct_col, row, effective_pct_col,
                {
                    'type': 'cell',
                    'criteria': '>=',
                    'value': 1,
                    'format': self.formats.get('error')
                }
            )

            # Add data validation with error message for sum >= 100%
            effective_pct_cell_ref = f"{effective_pct_col_letter}{row + 1}"
            effective_sum_range = f"{effective_pct_col_letter}{first_holder_row + 1}:{effective_pct_col_letter}{last_holder_row + 1}"
            sheet.data_validation(
                row, effective_pct_col, row, effective_pct_col,
                {
                    'validate': 'custom',
                    'value': f'={effective_sum_range}<1',
                    'error_type': 'stop',
                    'error_title': 'Invalid Effective Percentage',
                    'error_message': 'The sum of effective percentages in this round cannot be 100% or greater. Please adjust the values.'
                }
            )

            # Skip exercise_type, partial_amount, and partial_pct columns in total row
            sheet.write(row, exercise_type_col, '',
                        self.formats.get('total_text'))
            sheet.write(row, partial_amount_col, '',
                        self.formats.get('total_text'))
            sheet.write(row, partial_pct_col, '',
                        self.formats.get('total_text'))

            # Sum all Pro-rata Shares for this round
            shares_col_letter = self._col_letter(shares_col)
            sheet.write_formula(
                row, shares_col,
                f"=SUM({shares_col_letter}{first_holder_row + 1}:{shares_col_letter}{last_holder_row + 1})",
                self.formats.get('total_number')
            )

            # Define a Named Range for this round's total Pro-rata Shares so other sheets can reference it
            round_name_key = self._sanitize_excel_name(
                round_data.get('name', ''))
            pr_total_named = f"{round_name_key}_ProRataShares"
            cell_ref_abs = f"'Pro Rata Allocations'!${shares_col_letter}${row + 1}"
            self.workbook.define_name(pr_total_named, cell_ref_abs)

            # Price Per Share column: leave empty in total row
            sheet.write(row, pps_col, '', self.formats.get('total_text'))

            # Sum all investment amounts for this round
            investment_col_letter = self._col_letter(investment_col)
            sheet.write_formula(
                row, investment_col,
                f"=SUM({investment_col_letter}{first_holder_row + 1}:{investment_col_letter}{last_holder_row + 1})",
                self.formats.get('total_currency')
            )

            # Separator (skip for last round)
            if not is_last_round:
                sheet.write(row, separator_col, '',
                            self.formats.get('total_text'))
                col = separator_col + 1
            else:
                col = investment_col + 1

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
        """Add dropdown validation to Pro-rata Rights columns."""
        for round_idx, rows in pro_rata_type_rows_by_round.items():
            if not rows:
                continue

            # Pro-rata Rights column is the first column of each round section
            # Column structure: type, pct, exercise_type, partial_amount, partial_pct, effective_pct, shares, pps, investment, separator
            # Each round has 10 columns (9 data + 1 separator)
            # Column position: padding + 1 (inner padding) + 2 (Shareholders + Description) + round_idx * 10
            type_col = self.padding_offset + 1 + 2 + (round_idx * 10)

            first_row = min(rows)
            last_row = max(rows)

            # Add dropdown with valid pro rata type options (capitalized)
            sheet.data_validation(
                first_row, type_col,
                last_row, type_col,
                {
                    'validate': 'list',
                    'source': ['None', 'Standard', 'Super'],
                    'error_type': 'stop',
                    'error_title': 'Invalid Pro-rata Rights',
                    'error_message': 'Please select "None", "Standard", or "Super" from the dropdown.'
                }
            )
