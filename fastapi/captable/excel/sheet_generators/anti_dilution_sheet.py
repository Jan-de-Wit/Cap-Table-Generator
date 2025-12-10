"""
Anti-Dilution Allocations Sheet Generator

Creates the Anti-Dilution Allocations sheet showing anti-dilution share adjustments for each stakeholder per round.
Anti-dilution calculations happen AFTER pro rata allocations are calculated.
"""

from typing import Dict, List, Any, Set, Optional
import xlsxwriter
from ..base import BaseSheetGenerator


class AntiDilutionSheetGenerator(BaseSheetGenerator):
    """
    Generates the Anti-Dilution Allocations sheet.

    This sheet lists all stakeholders per round who have instruments with anti-dilution protection
    and calculates their additional share allocations due to price adjustments.

    Anti-dilution methods:
    - full_ratchet: Adjusts conversion price to the lowest price in the new round
    - narrow_based_weighted_average: Weighted average using only outstanding preferred shares
    - broad_based_weighted_average: Weighted average using all outstanding shares
    - percentage_based: Maintains ownership percentage rather than adjusting price

    Anti-dilution Shares are calculated AFTER pro rata allocations.

    Note: Price-based anti-dilution methods (full_ratchet, weighted_average) only apply to
    rounds that support price-based calculations (valuation_based, convertible, safe).
    They are skipped for fixed_shares and target_percentage rounds.
    Percentage-based anti-dilution applies to all round types.
    """

    def __init__(self, workbook, data, formats, dlm, formula_resolver):
        """Initialize anti-dilution sheet generator."""
        super().__init__(workbook, data, formats, dlm, formula_resolver)
        self.round_ranges = {}  # Round ranges from rounds sheet
        self.pro_rata_ranges = {}  # Pro rata ranges from pro rata sheet
        # Padding offset for table positioning
        self.padding_offset = 1

    def _get_sheet_name(self) -> str:
        """Returns 'Anti-Dilution Allocations'."""
        return "Anti-Dilution Allocations"

    def generate(self) -> xlsxwriter.worksheet.Worksheet:
        """Generate the Anti-Dilution Allocations sheet."""
        sheet = self.workbook.add_worksheet('Anti-Dilution Allocations')
        self.sheet = sheet

        rounds = self.data.get('rounds', [])
        if not rounds:
            sheet.write(self.padding_offset, self.padding_offset,
                        'No rounds found', self.formats.get('text'))
            return sheet

        # Title row inside border (top-left of table, respecting padding)
        title_row = self.padding_offset + 1
        sheet.write(title_row, self.padding_offset + 1,
                    'Anti-Dilution Allocation', self.formats.get('round_header_plain'))

        # Extract all holders with grouping (same as cap table sheet)
        holders_by_group, all_holders = self._get_holders_with_groups(rounds)

        if not all_holders:
            sheet.write(self.padding_offset + 1, self.padding_offset + 1,
                        'No holders found', self.formats.get('text'))
            return sheet

        # Calculate table bounds for border (border includes 1 cell padding on all sides)
        border_start_row = self.padding_offset
        border_start_col = self.padding_offset
        # Each round has 7 columns (6 data + 1 separator)
        num_rounds = len(rounds)
        border_end_col = self.padding_offset + 1 + 2 + (num_rounds * 7) - 1
        # Last row includes padding, so we need to calculate after writing data

        # Write headers aligned with title row for round names
        self._write_headers(sheet, rounds)

        # Write holder data with grouping
        data_start_row = self.padding_offset + 1 + 2
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
            (self.padding_offset + 1, 25),  # Title row (also round names row)
            (self.padding_offset + 2, 25),  # Column headers row
        ]

        column_widths = [
            (0, 0, 4.0),  # Outer padding column
            (border_start_col, border_start_col, 4.0),  # Inner padding column
            # Shareholders column
            (self.padding_offset + 1, self.padding_offset + 1, 35),
            # Description column
            (self.padding_offset + 2, self.padding_offset + 2, 35),
        ]

        # For each round, set widths for columns
        for round_idx in range(num_rounds):
            start_col = self.padding_offset + 1 + 2 + (round_idx * 7)
            # Set data columns to width 20
            column_widths.append((start_col, start_col + 5, 20))
            # Set separator column to width 5
            separator_col = start_col + 6
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

    def _get_holders_with_groups(self, rounds: List[Dict[str, Any]]) -> tuple:
        """
        Get all holders list with grouping information (same as cap table sheet).

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

    def _sort_groups(self, groups: List[str]) -> List[str]:
        """
        Sort groups according to the default order.
        """
        default_order = ['Founders', 'ESOP', 'Noteholders', 'Investors']

        ordered_groups = []
        unordered_groups = []

        for group in groups:
            if group in default_order:
                ordered_groups.append(group)
            else:
                unordered_groups.append(group)

        ordered_groups.sort(key=lambda g: default_order.index(g))
        unordered_groups.sort()

        return ordered_groups + unordered_groups

    def _write_headers(self, sheet: xlsxwriter.worksheet.Worksheet, rounds: List[Dict[str, Any]]):
        """Write the header rows."""
        header_row = self.padding_offset + 1
        subheader_row = self.padding_offset + 2
        start_col = self.padding_offset + 1 + 2

        # Write Shareholders and Description headers first
        sheet.write(subheader_row, self.padding_offset + 1,
                    'Shareholders', self.formats.get('header'))
        sheet.write(subheader_row, self.padding_offset +
                    2, '', self.formats.get('header'))

        # Use utility function to write round headers
        subheaders = ['Anti-Dilution Method', 'Original Price', 'Current Price',
                      'Original Shares', 'Adjusted Shares', 'Additional Shares']
        self.write_round_headers(
            sheet,
            rounds,
            header_row,
            start_col,
            columns_per_round=6,
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
        holder_row_map = {}
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
                    row += 1
                row += 1
                current_group = group
            elif not group and current_group is not None:
                row += 1
                current_group = None

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

        # Second pass: write data
        data_rows = []
        row = data_start_row
        current_group = None

        for holder_name in all_holders:
            group = holder_to_group.get(holder_name, '')

            # Add group header and spacing row before new group
            if group and group != current_group:
                if current_group is not None:
                    row += 1
                sheet.write(row, self.padding_offset + 1,
                            group, self.formats.get('label'))
                row += 1
                current_group = group
            elif not group and current_group is not None:
                row += 1
                current_group = None

            # Write holder name
            sheet.write(row, self.padding_offset + 1,
                        holder_name, self.formats.get('text'))
            sheet.write(row, self.padding_offset + 2, holder_to_description.get(
                holder_name, ''), self.formats.get('italic_text'))
            col = self.padding_offset + 1 + 2

            # For each round, write anti-dilution data
            for round_idx, round_data in enumerate(rounds):
                is_last_round = (round_idx == len(rounds) - 1)
                col = self._write_round_anti_dilution_data(
                    sheet, row, col, round_idx, holder_name, rounds, is_last_round
                )

            data_rows.append(row)
            row += 1

        return data_rows, first_holder_row, last_holder_row

    def _write_round_anti_dilution_data(
        self,
        sheet: xlsxwriter.worksheet.Worksheet,
        row: int,
        col: int,
        round_idx: int,
        holder_name: str,
        rounds: List[Dict[str, Any]],
        is_last_round: bool = False
    ) -> int:
        """Write anti-dilution data for one round and return updated column position."""
        method_col = col
        original_price_col = col + 1
        adjusted_price_col = col + 2
        original_shares_col = col + 3
        adjusted_shares_col = col + 4
        additional_shares_col = col + 5
        separator_col = col + 6

        round_data = rounds[round_idx]
        instruments = round_data.get('instruments', [])
        round_calculation_type = round_data.get('calculation_type', '')

        # Helper function to check if a round type supports price-based anti-dilution
        def supports_price_based_anti_dilution(calc_type: str) -> bool:
            """Check if round type supports price-based anti-dilution methods."""
            return calc_type not in ['fixed_shares', 'target_percentage']

        # Find all anti-dilution allocation instruments for this holder in this round
        # There can be multiple if the holder has anti-dilution from different original rounds
        holder_anti_dilution_instruments = []
        for instrument in instruments:
            if instrument.get('holder_name') == holder_name:
                dilution_method = instrument.get('dilution_method')
                if dilution_method:
                    # For price-based methods (full_ratchet, weighted_average), only apply to rounds
                    # that support price-based anti-dilution (not fixed_shares or target_percentage)
                    if dilution_method != 'percentage_based':
                        if not supports_price_based_anti_dilution(round_calculation_type):
                            # Skip price-based anti-dilution for rounds that don't support it
                            continue
                    # For percentage-based, apply to all round types
                    holder_anti_dilution_instruments.append(instrument)

        if not holder_anti_dilution_instruments:
            # No anti-dilution protection for this holder in this round
            sheet.write(row, method_col, '-', self.formats.get('text'))
            sheet.write(row, original_price_col, '', self.formats.get('text'))
            sheet.write(row, adjusted_price_col, '', self.formats.get('text'))
            sheet.write(row, original_shares_col, '', self.formats.get('text'))
            sheet.write(row, adjusted_shares_col, '', self.formats.get('text'))
            sheet.write(row, additional_shares_col,
                        '', self.formats.get('text'))
            if not is_last_round:
                sheet.write(row, separator_col, '', self.formats.get('text'))
                return separator_col + 1
            else:
                return additional_shares_col + 1

        # Get anti-dilution method(s) - if multiple, show combined or first
        # For multiple allocations, we'll aggregate the additional shares
        primary_instrument = holder_anti_dilution_instruments[0]
        dilution_method = primary_instrument.get('dilution_method', '')

        # If multiple methods, show combined display
        if len(holder_anti_dilution_instruments) > 1:
            methods = [inst.get('dilution_method', '')
                       for inst in holder_anti_dilution_instruments]
            unique_methods = list(set(methods))
            if len(unique_methods) == 1:
                method_display = unique_methods[0].replace('_', ' ').title()
            else:
                method_display = f"Multiple ({len(holder_anti_dilution_instruments)})"
        else:
            method_display = dilution_method.replace(
                '_', ' ').title() if dilution_method else '-'

        sheet.write(row, method_col, method_display, self.formats.get('text'))

        # Get original round where anti-dilution rights were received
        # Use the original_investment_round field from the instrument
        original_investment_round_name = primary_instrument.get(
            'original_investment_round')

        if original_investment_round_name:
            # Find the round by name
            anti_dilution_rights_round_idx = None
            for idx, rnd in enumerate(rounds):
                if rnd.get('name') == original_investment_round_name:
                    anti_dilution_rights_round_idx = idx
                    break

            if anti_dilution_rights_round_idx is not None:
                # Get the actual price per share from the round where anti-dilution rights were received
                # Use the named range for PricePerShare from the Rounds sheet
                anti_dilution_round_name_key = self._sanitize_excel_name(
                    original_investment_round_name)
                original_price_formula = f"=IFERROR({anti_dilution_round_name_key}_PricePerShare, 0)"
            else:
                # Round name not found, fallback to previous round
                if round_idx > 0:
                    prev_round = rounds[round_idx - 1]
                    prev_round_name_key = self._sanitize_excel_name(
                        prev_round.get('name', ''))
                    original_price_formula = f"=IFERROR({prev_round_name_key}_PricePerShare, 0)"
                else:
                    round_name_key = self._sanitize_excel_name(
                        round_data.get('name', ''))
                    original_price_formula = f"=IFERROR({round_name_key}_PricePerShare, 0)"
        else:
            # Fallback: try to find using old method if original_investment_round not provided
            anti_dilution_rights_round_idx = self._find_anti_dilution_rights_round(
                holder_name, primary_instrument, rounds, round_idx
            )
            if anti_dilution_rights_round_idx is not None:
                anti_dilution_round = rounds[anti_dilution_rights_round_idx]
                anti_dilution_round_name_key = self._sanitize_excel_name(
                    anti_dilution_round.get('name', ''))
                original_price_formula = f"=IFERROR({anti_dilution_round_name_key}_PricePerShare, 0)"
            elif round_idx > 0:
                prev_round = rounds[round_idx - 1]
                prev_round_name_key = self._sanitize_excel_name(
                    prev_round.get('name', ''))
                original_price_formula = f"=IFERROR({prev_round_name_key}_PricePerShare, 0)"
            else:
                round_name_key = self._sanitize_excel_name(
                    round_data.get('name', ''))
                original_price_formula = f"=IFERROR({round_name_key}_PricePerShare, 0)"

        sheet.write_formula(row, original_price_col, original_price_formula,
                            self.formats.get('table_currency'))

        # Current price = current round's price per share
        round_name_key = self._sanitize_excel_name(round_data.get('name', ''))
        pre_money_valuation_ref = f"{round_name_key}_PreMoneyValuation"
        pre_round_shares_ref = f"{round_name_key}_PreRoundShares"
        current_price_formula = f"=IFERROR({pre_money_valuation_ref} / {pre_round_shares_ref}, 0)"
        sheet.write_formula(row, adjusted_price_col, current_price_formula,
                            self.formats.get('table_currency'))

        # Original shares = holder's total shares at the end of the round where anti-dilution rights were received
        # Link back to Cap Table sheet for that round
        # Use the original_investment_round field from the instrument
        if not original_investment_round_name:
            # Fallback: try to find using old method if original_investment_round not provided
            anti_dilution_rights_round_idx = self._find_anti_dilution_rights_round(
                holder_name, primary_instrument, rounds, round_idx
            )
        else:
            # Find the round by name
            anti_dilution_rights_round_idx = None
            for idx, rnd in enumerate(rounds):
                if rnd.get('name') == original_investment_round_name:
                    anti_dilution_rights_round_idx = idx
                    break

        # If anti-dilution rights were granted in the current round or we can't find them, use previous round's total
        if anti_dilution_rights_round_idx is not None and anti_dilution_rights_round_idx < round_idx:
            # Get holder's total shares at end of anti-dilution rights round (from Cap Table sheet)
            # Cap Table structure: each round has Total column
            # Total column is 4 columns after Start column
            # Start column for round N is at: 2 + (N * 5)
            # So Total column for round N is at: 2 + (N * 5) + 4
            anti_dilution_round_total_col_idx = 2 + \
                (anti_dilution_rights_round_idx * 5) + 4
            anti_dilution_round_total_col = self._col_letter(
                anti_dilution_round_total_col_idx)
            holder_name_col = self._col_letter(self.padding_offset + 1)
            holder_name_escaped = f'"{holder_name}"'
            original_shares_formula = f"=IFERROR(SUMIF('Cap Table'!{holder_name_col}:{holder_name_col}, {holder_name_escaped}, 'Cap Table'!{anti_dilution_round_total_col}:{anti_dilution_round_total_col}), 0)"
        elif round_idx > 0:
            # Fallback: use previous round's total shares (for first time anti-dilution can be exercised)
            prev_round_total_col_idx = 2 + ((round_idx - 1) * 5) + 4
            prev_round_total_col = self._col_letter(prev_round_total_col_idx)
            holder_name_col = self._col_letter(self.padding_offset + 1)
            holder_name_escaped = f'"{holder_name}"'
            original_shares_formula = f"=IFERROR(SUMIF('Cap Table'!{holder_name_col}:{holder_name_col}, {holder_name_escaped}, 'Cap Table'!{prev_round_total_col}:{prev_round_total_col}), 0)"
        else:
            # First round: use current round's shares (no previous round to reference)
            if round_idx in self.round_ranges:
                range_info = self.round_ranges[round_idx]
                table_name = range_info.get('table_name')
                if table_name:
                    holder_col_ref = f"{table_name}[[#All],[Holder Name]]"
                    shares_col_ref = f"{table_name}[[#All],[Shares]]"
                    holder_col_letter = self._col_letter(
                        self.padding_offset + 1)
                    rounds_shares = f"SUMIF({holder_col_ref}, {holder_col_letter}{row + 1}, {shares_col_ref})"
                else:
                    holder_range = f"Rounds!{range_info['holder_col']}{range_info['start_row']}:{range_info['holder_col']}{range_info['end_row']}"
                    shares_range = f"Rounds!{range_info['shares_col']}{range_info['start_row']}:{range_info['shares_col']}{range_info['end_row']}"
                    holder_col_letter = self._col_letter(
                        self.padding_offset + 1)
                    rounds_shares = f'SUMIF({holder_range}, {holder_col_letter}{row + 1}, {shares_range})'
            else:
                rounds_shares = "0"
            pro_rata_shares_col = self._get_pro_rata_shares_col(
                round_idx, rounds)
            pro_rata_shares = f"'Pro Rata Allocations'!{pro_rata_shares_col}{row + 1}"
            original_shares_formula = f"=ROUND({rounds_shares} + {pro_rata_shares}, 0)"

        sheet.write_formula(row, original_shares_col, original_shares_formula,
                            self.formats.get('table_number'))

        # Adjusted shares calculation depends on dilution method
        # Initial shares = original shares from the anti-dilution rights round
        original_shares_cell = f"{self._col_letter(original_shares_col)}{row + 1}"
        original_price_cell = f"{self._col_letter(original_price_col)}{row + 1}"
        current_price_cell = f"{self._col_letter(adjusted_price_col)}{row + 1}"

        # For broad-based weighted average: use average of original and current price
        # For other methods: use original price / current price
        if dilution_method == 'broad_based_weighted_average':
            # Calculate average price: (original_price + current_price) / 2
            average_price = f"IFERROR(({original_price_cell} + {current_price_cell}) / 2, {current_price_cell})"
            # Calculate multiplier: original price / average price
            price_multiplier = f"IFERROR({original_price_cell} / {average_price}, 1)"
        else:
            # Standard calculation: original price / current price
            price_multiplier = f"IFERROR({original_price_cell} / {current_price_cell}, 1)"

        # Calculate shares with multiplier: initial shares * price_multiplier
        multiplied_shares = f"({original_shares_cell} * {price_multiplier})"

        # Sum additional shares from earlier anti-dilution rounds (Additional Shares column)
        # Each round has 6 columns + 1 separator = 7 columns total
        # Start column for round N: padding_offset + 1 + 2 + (N * 7)
        # Additional Shares is at col + 5 from the start of each round
        earlier_anti_dilution_shares = []
        for prev_round_idx in range(round_idx):
            # Additional Shares column for round N: start_col + 5
            # Start col = padding_offset + 1 + 2 + (N * 7)
            prev_round_start_col_idx = self.padding_offset + \
                1 + 2 + (prev_round_idx * 7)
            prev_additional_shares_col_idx = prev_round_start_col_idx + 5
            prev_additional_shares_col = self._col_letter(
                prev_additional_shares_col_idx)
            earlier_anti_dilution_shares.append(
                f"'Anti-Dilution Allocations'!{prev_additional_shares_col}{row + 1}")

        if earlier_anti_dilution_shares:
            # Sum all earlier anti-dilution shares
            earlier_shares_sum = " + ".join(earlier_anti_dilution_shares)
            earlier_shares_ref = f"IFERROR({earlier_shares_sum}, 0)"
        else:
            earlier_shares_ref = "0"

        # Adjusted shares = multiplied shares (without subtracting earlier anti-dilution shares)
        adjusted_shares_formula = f"=MAX(0, ROUND({multiplied_shares}, 0))"

        sheet.write_formula(row, adjusted_shares_col, adjusted_shares_formula,
                            self.formats.get('table_number'))

        # Additional shares = adjusted shares - original shares - earlier anti-dilution shares
        adjusted_shares_cell = f"{self._col_letter(adjusted_shares_col)}{row + 1}"
        original_shares_cell = f"{self._col_letter(original_shares_col)}{row + 1}"
        additional_shares_formula = f"=MAX(0, ROUND({adjusted_shares_cell} - {original_shares_cell} - {earlier_shares_ref}, 0))"
        sheet.write_formula(row, additional_shares_col, additional_shares_formula,
                            self.formats.get('table_number'))

        # Separator (skip for last round)
        if not is_last_round:
            sheet.write(row, separator_col, '', self.formats.get('text'))
            return separator_col + 1
        else:
            return additional_shares_col + 1

    def _get_pro_rata_shares_col(self, round_idx: int, rounds: List[Dict[str, Any]]) -> str:
        """Get the column letter for Pro-rata Shares in Pro Rata Allocations sheet."""
        padding_offset = 1
        col_idx = padding_offset + 1 + 2 + (round_idx * 10) + 6
        return self._col_letter(col_idx)

    def _find_original_instrument_round(
        self,
        holder_name: str,
        holder_instrument: Dict[str, Any],
        rounds: List[Dict[str, Any]],
        current_round_idx: int
    ) -> Optional[int]:
        """
        Find the original round where the instrument was issued.

        Returns the round index of the earliest round (before current_round_idx) where
        this holder has an instrument with the same class_name, or None if not found.
        """
        class_name = holder_instrument.get('class_name')
        if not class_name:
            return None

        # Search backwards from current round to find the original issuance
        for prev_round_idx in range(current_round_idx - 1, -1, -1):
            prev_round = rounds[prev_round_idx]
            instruments = prev_round.get('instruments', [])
            for instrument in instruments:
                if (instrument.get('holder_name') == holder_name and
                        instrument.get('class_name') == class_name):
                    return prev_round_idx

        return None

    def _is_anti_dilution_allocation(self, instrument: Dict[str, Any]) -> bool:
        """
        Check if an instrument is a standalone anti-dilution allocation (not an investment instrument).

        Anti-dilution allocations only have holder_name, class_name, and dilution_method.
        Investment instruments have additional fields like investment_amount, principal, etc.
        """
        # If it has dilution_method but no investment-related fields, it's an anti-dilution allocation
        has_dilution = 'dilution_method' in instrument
        has_investment = 'investment_amount' in instrument or 'principal' in instrument or 'initial_quantity' in instrument or 'target_percentage' in instrument
        return has_dilution and not has_investment

    def _find_anti_dilution_rights_round(
        self,
        holder_name: str,
        holder_instrument: Dict[str, Any],
        rounds: List[Dict[str, Any]],
        current_round_idx: int
    ) -> Optional[int]:
        """
        Find the round where anti-dilution rights were received (the original investment round).

        Returns the round index of the earliest round (before current_round_idx) where
        this holder has an INVESTMENT instrument (not just an anti-dilution allocation) with 
        the same dilution_method. This is the round where the investment was made and 
        anti-dilution rights were granted.
        """
        class_name = holder_instrument.get('class_name')
        dilution_method = holder_instrument.get('dilution_method')
        if not dilution_method:
            return None

        # Search backwards from current round to find the EARLIEST investment instrument
        # with anti-dilution rights (not just an anti-dilution allocation)
        earliest_round_idx = None

        for prev_round_idx in range(current_round_idx - 1, -1, -1):
            prev_round = rounds[prev_round_idx]
            instruments = prev_round.get('instruments', [])
            for instrument in instruments:
                # Skip anti-dilution allocations - we want the original investment instrument
                if self._is_anti_dilution_allocation(instrument):
                    continue

                # Check if this is an investment instrument with anti-dilution rights
                if (instrument.get('holder_name') == holder_name and
                        instrument.get('dilution_method') == dilution_method):
                    # First try to match by class_name for more precise matching
                    if class_name and instrument.get('class_name') == class_name:
                        # Found matching investment instrument - this is the earliest we'll find
                        return prev_round_idx
                    # Track the earliest round with matching dilution_method (even if class doesn't match)
                    if earliest_round_idx is None:
                        earliest_round_idx = prev_round_idx

        # Return the earliest round found (if any)
        return earliest_round_idx

    def _calculate_adjusted_price_formula(
        self,
        dilution_method: str,
        round_idx: int,
        holder_name: str,
        holder_instrument: Dict[str, Any],
        rounds: List[Dict[str, Any]],
        original_price_col: int,
        row: int
    ) -> str:
        """
        Calculate the adjusted price formula based on the anti-dilution method.

        Methods:
        - full_ratchet: Adjusted price = new round's price per share (lowest price)
        - narrow_based_weighted_average: Weighted average using only preferred shares
        - broad_based_weighted_average: Weighted average using all outstanding shares

        Formula for weighted average (standard formula):
        CP₂ = CP₁ × (A + B) / (A + C)
        Where:
        - CP₁ = Original conversion price (from original_investment_round)
        - A = Outstanding shares before new issuance (preferred only for narrow, all for broad)
        - B = Total consideration from new issuance / CP₁ = (PP × NS) / CP₁
        - C = New shares issued in current round (NS)
        - PP = Price per share of new issuance (current round)

        This is mathematically equivalent to: (CP₁ × A + PP × NS) / (A + NS)
        """
        round_data = rounds[round_idx]
        round_name_key = self._sanitize_excel_name(round_data.get('name', ''))
        current_round_pre_money_ref = f"{round_name_key}_PreMoneyValuation"
        current_round_pre_shares_ref = f"{round_name_key}_PreRoundShares"
        current_round_price_ref = f"{current_round_pre_money_ref} / {current_round_pre_shares_ref}"

        if dilution_method == 'full_ratchet':
            # Full ratchet: adjusted price = new round's price per share (lowest price)
            # Only applies when new price is lower than original price

            # Find original round where instrument was issued
            original_round_idx = self._find_original_instrument_round(
                holder_name, holder_instrument, rounds, round_idx
            )

            if original_round_idx is None:
                # If we can't find the original round, use current price
                return f"=IFERROR({current_round_price_ref}, 0)"

            # Get original round's price per share
            original_round = rounds[original_round_idx]
            original_round_name_key = self._sanitize_excel_name(
                original_round.get('name', ''))
            original_round_pre_money_ref = f"{original_round_name_key}_PreMoneyValuation"
            original_round_pre_shares_ref = f"{original_round_name_key}_PreRoundShares"
            original_price_ref = f"{original_round_pre_money_ref} / {original_round_pre_shares_ref}"

            # Full ratchet: use new price if it's lower, otherwise keep original price
            return f"=IF({current_round_price_ref} < {original_price_ref}, IFERROR({current_round_price_ref}, {original_price_ref}), {original_price_ref})"

        elif dilution_method in ['narrow_based_weighted_average', 'broad_based_weighted_average']:
            # Weighted average anti-dilution formula: CP₂ = CP₁ × (A + B) / (A + C)
            # Where:
            #   CP₁ = Original conversion price (from original_investment_round)
            #   A = Outstanding shares before new issuance
            #   B = Total consideration from new issuance / CP₁
            #   C = New shares issued in current round
            # Only applies when new price is lower than original price (down round)

            # Use original_investment_round field from the instrument
            original_investment_round_name = holder_instrument.get(
                'original_investment_round')

            if original_investment_round_name:
                # Find the round by name
                original_round_idx = None
                for idx, rnd in enumerate(rounds):
                    if rnd.get('name') == original_investment_round_name:
                        original_round_idx = idx
                        break
            else:
                # Fallback: try to find using old method
                original_round_idx = self._find_original_instrument_round(
                    holder_name, holder_instrument, rounds, round_idx
                )

            if original_round_idx is None:
                # If we can't find the original round, fall back to current price
                return f"=IFERROR({current_round_price_ref}, 0)"

            # Get original round's price per share (CP₁)
            original_round = rounds[original_round_idx]
            original_round_name_key = self._sanitize_excel_name(
                original_round.get('name', ''))
            original_round_price_ref = f"{original_round_name_key}_PricePerShare"
            original_price_ref = f"IFERROR({original_round_price_ref}, 0)"

            # Get outstanding shares before current round (A)
            # For narrow-based: only preferred shares (use PreRoundShares as approximation)
            # For broad-based: all outstanding shares (PreRoundShares)
            # Note: In practice, narrow-based should only count preferred, but we use PreRoundShares
            # as a reasonable approximation since we don't track share classes separately
            outstanding_shares_ref = current_round_pre_shares_ref

            # Get new shares issued in current round (C)
            new_shares_ref = self._get_new_shares_issued_ref(round_idx, rounds)

            # Current round price per share (PP)
            new_price_ref = current_round_price_ref

            # Calculate B = Total consideration from new issuance / CP₁
            # Total consideration = PP × NS
            total_consideration = f"({new_price_ref} * {new_shares_ref})"
            b_value = f"IFERROR({total_consideration} / {original_price_ref}, 0)"

            # Calculate weighted average: CP₁ × (A + B) / (A + C)
            # Only apply if new price < original price (anti-dilution only triggers on down rounds)
            numerator = f"({outstanding_shares_ref} + {b_value})"
            denominator = f"({outstanding_shares_ref} + {new_shares_ref})"
            weighted_avg_price = f"IFERROR({original_price_ref} * {numerator} / {denominator}, {original_price_ref})"

            # Use conditional to ensure we don't adjust upward (only downward adjustments)
            # If new price >= original price, use original price (no adjustment)
            # If new price < original price, use the weighted average
            return f"=IF({new_price_ref} < {original_price_ref}, IFERROR({weighted_avg_price}, {original_price_ref}), {original_price_ref})"

        elif dilution_method == 'percentage_based':
            # Percentage-based: Maintains ownership percentage rather than adjusting price
            # For percentage-based, we calculate additional shares to maintain the original ownership %
            # This doesn't adjust price, but adjusts shares directly

            # Find original round where instrument was issued
            original_round_idx = self._find_original_instrument_round(
                holder_name, holder_instrument, rounds, round_idx
            )

            if original_round_idx is None:
                # If we can't find the original round, use current price (no adjustment)
                return f"=IFERROR({current_round_price_ref}, 0)"

            # Get original round's pre-round shares to calculate original ownership %
            original_round = rounds[original_round_idx]
            original_round_name_key = self._sanitize_excel_name(
                original_round.get('name', ''))
            original_round_pre_shares_ref = f"{original_round_name_key}_PreRoundShares"

            # Get holder's original shares (from rounds sheet + pro rata in original round)
            # We'll use the original shares calculation from the original round
            # For percentage-based, adjusted price = original price (no price adjustment)
            # The share adjustment happens in the adjusted shares calculation
            original_price_ref = f"{current_round_pre_money_ref} / {current_round_pre_shares_ref}"

            # Percentage-based doesn't adjust price, it maintains ownership percentage
            # So adjusted price = original price (no change)
            return f"=IFERROR({original_price_ref}, 0)"

        else:
            # Unknown method, fall back to original price
            original_price_cell = f"{self._col_letter(original_price_col)}{row + 1}"
            return f"={original_price_cell}"

    def _get_new_shares_issued_ref(self, round_idx: int, rounds: List[Dict[str, Any]]) -> str:
        """
        Get a reference to the total new shares issued in this round.
        This is the sum of shares from the rounds sheet for this round.
        """
        round_data = rounds[round_idx]

        if round_idx in self.round_ranges:
            range_info = self.round_ranges[round_idx]
            table_name = range_info.get('table_name')
            if table_name:
                # Use structured reference to sum all shares in the table
                return f"SUM({table_name}[[#All],[Shares]])"
            else:
                # Fallback to column range
                shares_col = range_info.get('shares_col', 'D')
                shares_range = f"Rounds!{shares_col}{range_info['start_row']}:{shares_col}{range_info['end_row']}"
                return f"SUM({shares_range})"
        else:
            # Fallback: return 0 if we can't find the range
            return "0"

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

        row = last_holder_row + 2
        sheet.write(row, self.padding_offset + 1, 'TOTAL',
                    self.formats.get('total_label'))
        sheet.write(row, self.padding_offset + 2, '',
                    self.formats.get('total_text'))
        col = self.padding_offset + 1 + 2

        for round_idx, round_data in enumerate(rounds):
            is_last_round = (round_idx == len(rounds) - 1)
            method_col = col
            original_price_col = col + 1
            adjusted_price_col = col + 2
            original_shares_col = col + 3
            adjusted_shares_col = col + 4
            additional_shares_col = col + 5
            separator_col = col + 6

            sheet.write(row, method_col, '', self.formats.get('total_text'))
            sheet.write(row, original_price_col, '',
                        self.formats.get('total_text'))
            sheet.write(row, adjusted_price_col, '',
                        self.formats.get('total_text'))

            # Sum original shares
            original_shares_col_letter = self._col_letter(original_shares_col)
            sheet.write_formula(
                row, original_shares_col,
                f"=SUM({original_shares_col_letter}{first_holder_row + 1}:{original_shares_col_letter}{last_holder_row + 1})",
                self.formats.get('total_number')
            )

            # Sum adjusted shares
            adjusted_shares_col_letter = self._col_letter(adjusted_shares_col)
            sheet.write_formula(
                row, adjusted_shares_col,
                f"=SUM({adjusted_shares_col_letter}{first_holder_row + 1}:{adjusted_shares_col_letter}{last_holder_row + 1})",
                self.formats.get('total_number')
            )

            # Sum additional shares
            additional_shares_col_letter = self._col_letter(
                additional_shares_col)
            sheet.write_formula(
                row, additional_shares_col,
                f"=SUM({additional_shares_col_letter}{first_holder_row + 1}:{additional_shares_col_letter}{last_holder_row + 1})",
                self.formats.get('total_number')
            )

            # Define named range for anti-dilution shares total
            round_name_key = self._sanitize_excel_name(
                round_data.get('name', ''))
            ad_total_named = f"{round_name_key}_AntiDilutionShares"
            cell_ref_abs = f"'Anti-Dilution Allocations'!${additional_shares_col_letter}${row + 1}"
            self.workbook.define_name(ad_total_named, cell_ref_abs)

            if not is_last_round:
                sheet.write(row, separator_col, '',
                            self.formats.get('total_text'))
                col = separator_col + 1
            else:
                col = additional_shares_col + 1

    def set_round_ranges(self, round_ranges: Dict[int, Dict[str, Any]]):
        """Set round ranges from rounds sheet generator."""
        self.round_ranges = round_ranges

    def set_pro_rata_ranges(self, pro_rata_ranges: Dict[int, Dict[str, Any]]):
        """Set pro rata ranges from pro rata sheet generator."""
        self.pro_rata_ranges = pro_rata_ranges
