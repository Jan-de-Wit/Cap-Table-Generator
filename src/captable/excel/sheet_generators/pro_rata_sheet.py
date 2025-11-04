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
        # Row range for holder data (for summing pro rata %)
        self.holder_data_range = {}
        # Padding offset for table positioning
        self.padding_offset = 1

    def _get_sheet_name(self) -> str:
        """Returns 'Pro Rata Allocations'."""
        return "Pro Rata Allocations"

    def generate(self) -> xlsxwriter.worksheet.Worksheet:
        """Generate the Pro Rata Allocations sheet."""
        sheet = self.workbook.add_worksheet('Pro Rata Allocations')
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
        # Calculate last column: padding + 1 (padding) + 2 (Shareholders + Description) + (rounds * 6) - 1
        # Each round has 6 columns (5 data + 1 separator), last round's separator is the last column
        num_rounds = len(rounds)
        border_end_col = self.padding_offset + 1 + 2 + (num_rounds * 6) - 1
        # Last row includes padding, so we need to calculate after writing data
        
        # Write headers (shifted by padding offset + 1 for content within border)
        self._write_headers(sheet, rounds)

        # Write holder data with grouping (shifted by padding offset + 1 for content within border)
        data_start_row = self.padding_offset + 1 + 2  # After padding + headers
        data_rows_per_holder, first_holder_row, last_holder_row = self._write_holder_data_with_groups(
            sheet, rounds, all_holders, holders_by_group, data_start_row
        )

        # Write total row
        self._write_total_row(sheet, rounds, all_holders,
                              first_holder_row, last_holder_row)

        # Calculate border end row (includes padding)
        border_end_row = last_holder_row + 2 + 1  # Total row + spacing + padding

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

        # For each round, set widths for Pro Rata Type, Pro Rata %, Pro Rata Shares, Price Per Share, Investment Amount (15) and separator (5)
        for round_idx in range(num_rounds):
            # Start column: padding + 1 (inner padding) + 2 (Shareholders + Description) + (round_idx * 6)
            start_col = self.padding_offset + 1 + 2 + (round_idx * 6)
            # Set Pro Rata Type, Pro Rata %, Pro Rata Shares, Price Per Share, Investment Amount columns to width 15
            column_widths.append((start_col, start_col + 4, 15))
            # Set separator column to width 5
            separator_col = start_col + 5
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

        # Freeze columns and header rows
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
        header_row = self.padding_offset + 1
        subheader_row = self.padding_offset + 2
        start_col = self.padding_offset + 1 + 2  # Start after padding + "Shareholders" and "Description"

        # Write Shareholders and Description headers first
        sheet.write(subheader_row, self.padding_offset + 1, 'Shareholders', self.formats.get('header'))
        sheet.write(subheader_row, self.padding_offset + 2, '', self.formats.get('header'))

        # Use utility function to write round headers
        subheaders = ['Pro Rata Type', 'Pro Rata %', 'Pro Rata Shares', 'Price per Share', 'Investment']
        self.write_round_headers(
            sheet,
            rounds,
            header_row,
            start_col,
            columns_per_round=5,
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
            # Description column - shifted by padding offset + 1 for content within border
            sheet.write(row, self.padding_offset + 2, holder_to_description.get(
                holder_name, ''), self.formats.get('italic_text'))
            col = self.padding_offset + 1 + 2

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
        self._add_pro_rata_dropdowns(
            sheet, rounds, pro_rata_type_rows_by_round)

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
        shares_col = col + 2
        pps_col = col + 3
        investment_col = col + 4
        separator_col = col + 5

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
            prev_round_total_col = self._get_progression_total_col(
                round_idx - 1, rounds)
            holder_row = row + 1
            holder_shares_start_ref = f"'Cap Table Progression'!{prev_round_total_col}{holder_row}"

        # Dynamic formula for Pro Rata % column
        # If "standard": calculate ownership % = holder_shares_start / pre_round_shares
        # If "super": use initial value from data (stored in formula, but can be manually edited)
        # Otherwise: empty
        ownership_pct_formula = f"IFERROR({holder_shares_start_ref} / {pre_round_shares_ref}, 0)"

        # Always use ownership % for both standard and super; blank for none
        pct_formula = (
            f"=IF(OR({type_cell_ref}=\"standard\", {type_cell_ref}=\"super\"), {ownership_pct_formula}, \"\")"
        )
        sheet.write_formula(row, pct_col, pct_formula,
                            self.formats.get('table_percent'))

        # Create formulas for each pro rata type
        pro_rata_formula = self._create_pro_rata_formula(
            round_idx, holder_name, rounds, row, pct_col, first_holder_row, last_holder_row
        ).lstrip('=')

        # Dynamic formula using nested IF to check pro_rata_type cell
        # Handles: "none", "standard", "super", or empty/invalid (defaults to 0)
        # Use the standard formula for both standard and super
        shares_formula = (
            f"=IFERROR(IF(OR({type_cell_ref}=\"\", {type_cell_ref}=\"none\"), 0, {pro_rata_formula}), 0)"
        )
        sheet.write_formula(row, shares_col, shares_formula,
                            self.formats.get('table_number'))

        # Price Per Share column: reference from rounds sheet
        round_name_key = round_data.get('name', '').replace(' ', '_')
        price_per_share_ref = f"{round_name_key}_PricePerShare"
        pps_formula = f"=IFERROR({price_per_share_ref}, 0)"
        sheet.write_formula(row, pps_col, pps_formula,
                            self.formats.get('table_currency'))

        # Investment Amount column: Price Per Share * Pro Rata Shares
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

    def _create_pro_rata_formula(
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
        prev_round_total_col = self._get_progression_total_col(
            round_idx - 1, rounds) if round_idx > 0 else None
        holder_row = row + 1
        prev_total_ref = f"'Cap Table Progression'!{prev_round_total_col}{holder_row}" if prev_round_total_col else "0"
        holder_base_shares_ref = self._get_holder_base_shares_ref(
            round_idx, holder_row)
        holder_shares_start_ref = f"({prev_total_ref} + {holder_base_shares_ref})"

        # Target percentage is the Pro Rata % cell for this row
        target_pct_col_letter = self._col_letter(pct_col)
        holder_target_pct_ref = f"{target_pct_col_letter}{row + 1}"

        # Aggregates across participants
        sum_pro_rata_pct_ref = self._get_sum_pro_rata_pct_ref(
            round_idx, rounds, first_holder_row, last_holder_row)
        sum_current_shares_ref = self._get_sum_current_shares_ref(
            round_idx, rounds, first_holder_row, last_holder_row)

        # Standard pro rata formula using unified form
        formula = ownership.create_pro_rata_shares_formula(
            holder_target_pct_ref,
            pre_round_shares_ref,
            shares_issued_ref,
            holder_shares_start_ref,
            sum_pro_rata_pct_ref,
            sum_current_shares_ref
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
        # Column position: padding + 1 (inner padding) + 2 (Shareholders + Description) + round_idx * 6 (5 data columns + 1 separator)
        type_col = self.padding_offset + 1 + 2 + (round_idx * 6)
        pct_col = type_col + 1
        pct_col_letter = self._col_letter(pct_col)

        # Create Excel SUM formula for the Pro Rata % column in this round
        sheet_name = self._get_sheet_name()
        pct_range = f"'{sheet_name}'!{pct_col_letter}{first_row + 1}:{pct_col_letter}{last_row + 1}"
        sum_pro_rata_pct_formula = f"SUM({pct_range})"
        return sum_pro_rata_pct_formula

    def _get_sum_pro_rata_pct_ref(
        self,
        round_idx: int,
        rounds: List[Dict[str, Any]],
        first_holder_row: int,
        last_holder_row: int
    ) -> str:
        """
        Get reference to Excel formula that sums only STANDARD pro rata percentages in this round.
        Uses SUM over the Pro Rata Type column == "standard".
        """
        # Determine the type and pct column letters for this round
        # Column position: padding + 1 (inner padding) + 2 (Shareholders + Description) + round_idx * 6 (5 data columns + 1 separator)
        type_col = self.padding_offset + 1 + 2 + (round_idx * 6)
        pct_col = type_col + 1
        pct_col_letter = self._col_letter(pct_col)

        first_row = first_holder_row
        last_row = last_holder_row

        sheet_name = self._get_sheet_name()
        pct_range = f"'{sheet_name}'!{pct_col_letter}{first_row + 1}:{pct_col_letter}{last_row + 1}"
        return f"SUM({pct_range})"

    def _get_sum_current_shares_ref(
        self,
        round_idx: int,
        rounds: List[Dict[str, Any]],
        first_holder_row: int,
        last_holder_row: int
    ) -> str:
        """
        Sum of current shares (pre-pro-rata) for STANDARD and SUPER rows in this round.
        Concise single-formula form: SUMPRODUCT(--((type="standard")+(type="super")>0), progression + base_shares)
        """
        # Build ranges
        sheet_name = self._get_sheet_name()
        # Column position: padding + 1 (inner padding) + 2 (Shareholders + Description) + round_idx * 6 (5 data columns + 1 separator)
        type_col = self.padding_offset + 1 + 2 + (round_idx * 6)
        type_col_letter = self._col_letter(type_col)
        type_range = f"'{sheet_name}'!{type_col_letter}{first_holder_row + 1}:{type_col_letter}{last_holder_row + 1}"

        rounds_holder_range, rounds_shares_range = self._get_rounds_holder_and_shares_ranges(
            round_idx)
        # Shareholders column is at padding_offset + 1 (within border)
        holder_name_col_letter = self._col_letter(self.padding_offset + 1)
        holder_name_range = f"'{sheet_name}'!{holder_name_col_letter}{first_holder_row + 1}:{holder_name_col_letter}{last_holder_row + 1}"
        base_sum_array = f"SUMIF({rounds_holder_range}, {holder_name_range}, {rounds_shares_range})"

        # Progression range is 0 in the first round
        if round_idx == 0:
            progression_range = "0"
        else:
            prev_round_total_col = self._get_progression_total_col(
                round_idx - 1, rounds)
            progression_range = f"'Cap Table Progression'!{prev_round_total_col}{first_holder_row + 1}:{prev_round_total_col}{last_holder_row + 1}"

        type_filter = f"(({type_range}=\"standard\")+({type_range}=\"super\")>0)"
        return f"SUMPRODUCT(--({type_filter}), {progression_range} + {base_sum_array})"

    def _get_holder_base_shares_ref(self, round_idx: int, holder_row_1_based: int) -> str:
        """SUMIF over Rounds for base shares issued to the holder in this round."""
        rounds_holder_range, rounds_shares_range = self._get_rounds_holder_and_shares_ranges(
            round_idx)
        sheet_name = self._get_sheet_name()
        # Shareholders column is at padding_offset + 1 (within border)
        holder_name_col_letter = self._col_letter(self.padding_offset + 1)
        holder_name_cell = f"'{sheet_name}'!{holder_name_col_letter}{holder_row_1_based}"
        return f"IFERROR(SUMIF({rounds_holder_range}, {holder_name_cell}, {rounds_shares_range}), 0)"

    def _get_rounds_holder_and_shares_ranges(self, round_idx: int) -> tuple:
        """Return tuple of (holder_range, shares_range) for the given round on Rounds sheet."""
        if round_idx in self.round_ranges:
            range_info = self.round_ranges[round_idx]
            table_name = range_info.get('table_name')
            if table_name:
                # Prefer structured references when table exists
                calc_type = range_info.get('calc_type')
                shares_header = 'Shares' if calc_type == 'fixed_shares' else 'Calculated Shares'
                holder_range = f"{table_name}[[#All],[Holder Name]]"
                shares_range = f"{table_name}[[#All],[{shares_header}]]"
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
        sheet.write(row, self.padding_offset + 1, 'TOTAL', self.formats.get('total_label'))
        sheet.write(row, self.padding_offset + 2, '', self.formats.get(
            'total_text'))  # Description column
        col = self.padding_offset + 1 + 2

        for round_idx, round_data in enumerate(rounds):
            is_last_round = (round_idx == len(rounds) - 1)
            type_col = col
            pct_col = col + 1
            shares_col = col + 2
            pps_col = col + 3
            investment_col = col + 4
            separator_col = col + 5

            sheet.write(row, type_col, '', self.formats.get('total_text'))
            # Sum all pro rata percentages for this round
            pct_col_letter = self._col_letter(pct_col)
            sheet.write_formula(
                row, pct_col,
                f"=SUM({pct_col_letter}{first_holder_row + 1}:{pct_col_letter}{last_holder_row + 1})",
                self.formats.get('total_percent')
            )
            # Highlight when total pro rata % exceeds 100%
            sheet.conditional_format(
                row, pct_col, row, pct_col,
                {
                    'type': 'cell',
                    'criteria': 'greater than',
                    'value': 1,
                    'format': self.formats.get('error') if 'error' in self.formats else self.formats.get('total_percent')
                }
            )

            # Sum all pro rata shares for this round
            shares_col_letter = self._col_letter(shares_col)
            sheet.write_formula(
                row, shares_col,
                f"=SUM({shares_col_letter}{first_holder_row + 1}:{shares_col_letter}{last_holder_row + 1})",
                self.formats.get('total_number')
            )

            # Define a Named Range for this round's total pro rata shares so other sheets can reference it
            round_name_key = round_data.get('name', '').replace(' ', '_')
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
        """Add dropdown validation to Pro Rata Type columns."""
        for round_idx, rows in pro_rata_type_rows_by_round.items():
            if not rows:
                continue

            # Pro Rata Type column is the first column of each round section
            # Column position: padding + 1 (inner padding) + 2 (Shareholders + Description) + round_idx * 6 (5 data columns + 1 separator)
            type_col = self.padding_offset + 1 + 2 + (round_idx * 6)

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
