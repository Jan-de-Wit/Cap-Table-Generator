"""
Excel Generator
Creates Excel workbooks from cap table JSON data using xlsxwriter.
Implements standardized sheet structure with Named Ranges, Excel Tables, and formulas.
"""

import xlsxwriter
from typing import Dict, List, Any, Optional
from datetime import datetime
from .dlm import DeterministicLayoutMap
from .formulas import FormulaResolver


class ExcelGenerator:
    """Generates Excel workbooks with dynamic formulas from cap table data."""
    
    def __init__(self, data: Dict[str, Any], output_path: str):
        """
        Initialize Excel generator.
        
        Args:
            data: Validated cap table JSON data
            output_path: Path for output Excel file
        """
        self.data = data
        self.output_path = output_path
        self.workbook = None
        self.sheets = {}
        self.formats = {}
        self.dlm = DeterministicLayoutMap()
        self.formula_resolver = FormulaResolver(self.dlm)
        
    def generate(self) -> str:
        """
        Generate the complete Excel workbook.
        
        Returns:
            Path to generated Excel file
        """
        # Create workbook
        self.workbook = xlsxwriter.Workbook(self.output_path)
        self.workbook.set_calc_mode('auto')  # Force recalculation on open
        
        # Create formats
        self._create_formats()
        
        # Create sheets in order
        self._create_summary_sheet()
        self._create_ledger_sheet()
        self._create_rounds_sheet()
        self._create_cap_table_progression_sheet()
        self._create_vesting_sheet()
        self._create_waterfall_sheet()
        
        # Close and save
        self.workbook.close()
        
        return self.output_path
    
    def _create_formats(self):
        """Create reusable cell formats."""
        self.formats['header'] = self.workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1
        })
        
        self.formats['currency'] = self.workbook.add_format({
            'num_format': '$#,##0.00'
        })
        
        self.formats['percent'] = self.workbook.add_format({
            'num_format': '0.00%'
        })
        
        self.formats['number'] = self.workbook.add_format({
            'num_format': '#,##0'
        })
        
        self.formats['decimal'] = self.workbook.add_format({
            'num_format': '#,##0.00'
        })
        
        self.formats['date'] = self.workbook.add_format({
            'num_format': 'yyyy-mm-dd'
        })
        
        self.formats['label'] = self.workbook.add_format({
            'bold': True
        })
    
    def _create_summary_sheet(self):
        """Create Summary sheet with global constants and Named Ranges."""
        sheet = self.workbook.add_worksheet('Summary')
        self.sheets['Summary'] = sheet
        
        company = self.data.get('company', {})
        company_name = company.get('name', 'Untitled Company')
        current_pps = company.get('current_pps', 1.0)
        current_date = company.get('current_date', datetime.now().strftime('%Y-%m-%d'))
        
        # Write company info
        row = 0
        sheet.write(row, 0, 'Company Name:', self.formats['label'])
        sheet.write(row, 1, company_name)
        row += 1
        
        sheet.write(row, 0, 'Current Date:', self.formats['label'])
        sheet.write(row, 1, current_date, self.formats['date'])
        row += 2
        
        # Global constants section
        sheet.write(row, 0, 'Global Constants', self.formats['header'])
        row += 1
        
        # Current PPS (for TSM calculations)
        sheet.write(row, 0, 'Current Price Per Share:', self.formats['label'])
        sheet.write(row, 1, current_pps, self.formats['currency'])
        self.dlm.register_named_range('Current_PPS', 'Summary', row, 1)
        self.workbook.define_name('Current_PPS', f"=Summary!${self._col_letter(1)}${row + 1}")
        row += 1
        
        # Current Date (for vesting calculations)
        sheet.write(row, 0, 'Evaluation Date:', self.formats['label'])
        sheet.write(row, 1, current_date, self.formats['date'])
        self.dlm.register_named_range('Current_Date', 'Summary', row, 1)
        self.workbook.define_name('Current_Date', f"=Summary!${self._col_letter(1)}${row + 1}")
        row += 1
        
        # Exit Value (for waterfall scenarios)
        exit_val = 10000000  # Default $10M exit
        if self.data.get('waterfall_scenarios'):
            exit_val = self.data['waterfall_scenarios'][0].get('exit_value', exit_val)
        sheet.write(row, 0, 'Exit Value (Scenario):', self.formats['label'])
        sheet.write(row, 1, exit_val, self.formats['currency'])
        self.dlm.register_named_range('Exit_Val', 'Summary', row, 1)
        self.workbook.define_name('Exit_Val', f"=Summary!${self._col_letter(1)}${row + 1}")
        row += 2
        
        # Calculated totals section
        sheet.write(row, 0, 'Calculated Totals', self.formats['header'])
        row += 1
        
        # Total FDS (will be calculated from Ledger)
        sheet.write(row, 0, 'Total Fully Diluted Shares:', self.formats['label'])
        # Formula: sum of all current_quantity from Ledger + net_dilution
        fds_formula = "=SUM(Ledger[current_quantity]) + SUM(Ledger[net_dilution])"
        sheet.write_formula(row, 1, fds_formula, self.formats['number'])
        self.dlm.register_named_range('Total_FDS', 'Summary', row, 1)
        self.workbook.define_name('Total_FDS', f"=Summary!${self._col_letter(1)}${row + 1}")
        row += 1
        
        # Total Common Shares
        sheet.write(row, 0, 'Total Common Shares:', self.formats['label'])
        common_formula = '=SUMIF(Ledger[class_type], "common", Ledger[current_quantity])'
        sheet.write_formula(row, 1, common_formula, self.formats['number'])
        row += 1
        
        # Total Preferred Shares
        sheet.write(row, 0, 'Total Preferred Shares:', self.formats['label'])
        preferred_formula = '=SUMIF(Ledger[class_type], "preferred", Ledger[current_quantity])'
        sheet.write_formula(row, 1, preferred_formula, self.formats['number'])
        row += 1
        
        # Total Options
        sheet.write(row, 0, 'Total Options:', self.formats['label'])
        options_formula = '=SUMIF(Ledger[class_type], "option", Ledger[initial_quantity])'
        sheet.write_formula(row, 1, options_formula, self.formats['number'])
        row += 1
        
        # Set column widths
        sheet.set_column(0, 0, 25)
        sheet.set_column(1, 1, 15)
    
    def _create_ledger_sheet(self):
        """Create Ledger sheet as an Excel Table with instruments."""
        sheet = self.workbook.add_worksheet('Ledger')
        self.sheets['Ledger'] = sheet
        
        # Define columns
        columns = [
            'holder_id', 'holder_name', 'holder_type',
            'class_id', 'class_name', 'class_type',
            'instrument_id', 'round_id',
            'initial_quantity', 'current_quantity',
            'strike_price', 'acquisition_price', 'acquisition_date',
            'ownership_percent_fds',
            'gross_itm', 'proceeds', 'shares_repurchased', 'net_dilution'
        ]
        
        # Register table
        start_row = 0
        start_col = 0
        self.dlm.register_table('Ledger', 'Ledger', start_row, start_col, columns)
        
        # Build data rows
        instruments = self.data.get('instruments', [])
        holders_map = {h['holder_id']: h for h in self.data.get('holders', [])}
        classes_map = {c['class_id']: c for c in self.data.get('classes', [])}
        
        table_data = []
        for idx, instrument in enumerate(instruments):
            holder = holders_map.get(instrument.get('holder_id'), {})
            sec_class = classes_map.get(instrument.get('class_id'), {})
            
            row_data = {
                'holder_id': instrument.get('holder_id', ''),
                'holder_name': holder.get('name', ''),
                'holder_type': holder.get('type', ''),
                'class_id': instrument.get('class_id', ''),
                'class_name': sec_class.get('name', ''),
                'class_type': sec_class.get('type', ''),
                'instrument_id': instrument.get('instrument_id', ''),
                'round_id': instrument.get('round_id', ''),
                'initial_quantity': instrument.get('initial_quantity', 0),
                'current_quantity': instrument.get('current_quantity', instrument.get('initial_quantity', 0)),
                'strike_price': instrument.get('strike_price', 0),
                'acquisition_price': instrument.get('acquisition_price', 0),
                'acquisition_date': instrument.get('acquisition_date', ''),
            }
            table_data.append(row_data)
            
            # Register this row in DLM
            self.dlm.register_table_row('Ledger', idx, uuid=instrument.get('instrument_id'))
        
        # Write table
        if table_data:
            self._write_table(sheet, 'Ledger', start_row, start_col, columns, table_data,
                            self._get_ledger_formulas())
        else:
            # Empty table - just write headers
            for col_idx, col_name in enumerate(columns):
                sheet.write(start_row, start_col + col_idx, col_name, self.formats['header'])
        
        # Set column widths
        sheet.set_column(0, 2, 12)  # IDs
        sheet.set_column(1, 1, 20)  # Names
        sheet.set_column(8, 17, 12)  # Numbers
    
    def _get_ledger_formulas(self) -> Dict[str, str]:
        """Get formula templates for Ledger calculated columns."""
        formulas = {}
        
        # Ownership percentage
        formulas['ownership_percent_fds'] = self.formula_resolver.create_ownership_formula(
            'Ledger[@[current_quantity]]', 'Total_FDS'
        )
        
        # TSM calculations for options
        formulas['gross_itm'] = self.formula_resolver.create_tsm_gross_itm_formula(
            'Ledger[@[initial_quantity]]', 'Ledger[@[strike_price]]', 'Current_PPS'
        )
        
        formulas['proceeds'] = self.formula_resolver.create_tsm_proceeds_formula(
            'Ledger[@[gross_itm]]', 'Ledger[@[strike_price]]'
        )
        
        formulas['shares_repurchased'] = self.formula_resolver.create_tsm_repurchase_formula(
            'Ledger[@[proceeds]]', 'Current_PPS'
        )
        
        formulas['net_dilution'] = self.formula_resolver.create_tsm_net_dilution_formula(
            'Ledger[@[gross_itm]]', 'Ledger[@[shares_repurchased]]'
        )
        
        return formulas
    
    def _create_rounds_sheet(self):
        """Create Rounds sheet with financing round data."""
        sheet = self.workbook.add_worksheet('Rounds')
        self.sheets['Rounds'] = sheet
        
        columns = [
            'round_id', 'round_name', 'round_date',
            'investment_amount', 'pre_money_valuation', 'post_money_valuation',
            'price_per_share', 'shares_issued'
        ]
        
        # Write headers
        for col_idx, col_name in enumerate(columns):
            sheet.write(0, col_idx, col_name, self.formats['header'])
        
        # Write round data
        rounds = self.data.get('rounds', [])
        for row_idx, round_data in enumerate(rounds, start=1):
            sheet.write(row_idx, 0, round_data.get('round_id', ''))
            sheet.write(row_idx, 1, round_data.get('name', ''))
            sheet.write(row_idx, 2, round_data.get('round_date', ''), self.formats['date'])
            sheet.write(row_idx, 3, round_data.get('investment_amount', 0), self.formats['currency'])
            
            # Handle calculated fields
            pre_money = round_data.get('pre_money_valuation')
            if isinstance(pre_money, dict) and pre_money.get('is_calculated'):
                formula = self.formula_resolver.resolve_feo(pre_money)
                sheet.write_formula(row_idx, 4, formula, self.formats['currency'])
            else:
                sheet.write(row_idx, 4, pre_money or 0, self.formats['currency'])
            
            post_money = round_data.get('post_money_valuation')
            if isinstance(post_money, dict) and post_money.get('is_calculated'):
                formula = self.formula_resolver.resolve_feo(post_money)
                sheet.write_formula(row_idx, 5, formula, self.formats['currency'])
            else:
                sheet.write(row_idx, 5, post_money or 0, self.formats['currency'])
            
            pps = round_data.get('price_per_share')
            if isinstance(pps, dict) and pps.get('is_calculated'):
                formula = self.formula_resolver.resolve_feo(pps)
                sheet.write_formula(row_idx, 6, formula, self.formats['currency'])
            else:
                sheet.write(row_idx, 6, pps or 0, self.formats['currency'])
            
            shares = round_data.get('shares_issued')
            if isinstance(shares, dict) and shares.get('is_calculated'):
                formula = self.formula_resolver.resolve_feo(shares)
                sheet.write_formula(row_idx, 7, formula, self.formats['number'])
            else:
                sheet.write(row_idx, 7, shares or 0, self.formats['number'])
        
        sheet.set_column(0, 0, 12)
        sheet.set_column(1, 1, 20)
        sheet.set_column(2, 7, 15)
    
    def _create_cap_table_progression_sheet(self):
        """Create Cap Table Progression sheet showing ownership evolution across rounds."""
        sheet = self.workbook.add_worksheet('Cap Table Progression')
        self.sheets['Cap Table Progression'] = sheet
        
        # Get rounds and sort by date
        rounds = sorted(self.data.get('rounds', []), key=lambda r: r.get('round_date', ''))
        
        if not rounds:
            # No rounds, just show current state
            sheet.write(0, 0, 'No financing rounds to display', self.formats['label'])
            return
        
        # Build holder categories
        holders_map = {h['holder_id']: h for h in self.data.get('holders', [])}
        instruments = self.data.get('instruments', [])
        
        # Group holders by type
        categories = {}
        for holder in self.data.get('holders', []):
            holder_type = holder.get('type', 'other')
            if holder_type not in categories:
                categories[holder_type] = []
            categories[holder_type].append(holder)
        
        # Category display names
        category_names = {
            'founder': 'Founders',
            'employee': 'Employees',
            'investor': 'Investors',
            'advisor': 'Advisors',
            'option_pool': 'Option Pool',
            'other': 'Other'
        }
        
        # Build header
        row = 0
        col = 0
        
        # Empty cell
        sheet.write(row, col, '', self.formats['header'])
        col += 1
        sheet.write(row, col, '', self.formats['header'])
        col += 1
        
        # For each round, create 4 columns: Start, New, Total, %
        round_start_cols = {}
        for round_data in rounds:
            round_name = round_data.get('name', 'Round')
            round_start_cols[round_data['round_id']] = col
            
            # Merge cells for round name
            sheet.merge_range(row, col, row, col + 3, round_name, self.formats['header'])
            col += 4
            
            # Empty separator
            sheet.write(row, col, '', self.formats['header'])
            col += 1
        
        # Subheader row
        row += 1
        col = 0
        sheet.write(row, col, 'Shareholders', self.formats['header'])
        col += 1
        sheet.write(row, col, '', self.formats['header'])
        col += 1
        
        for _ in rounds:
            sheet.write(row, col, 'Start (#)', self.formats['header'])
            col += 1
            sheet.write(row, col, 'New (#)', self.formats['header'])
            col += 1
            sheet.write(row, col, 'Total (#)', self.formats['header'])
            col += 1
            sheet.write(row, col, '(%)', self.formats['header'])
            col += 1
            sheet.write(row, col, '', self.formats['header'])
            col += 1
        
        # Data starts here
        data_start_row = row + 1
        
        # Track data row positions for each holder
        holder_row_positions = {}  # holder_id -> data row index
        
        # Write data by category and track positions
        row = data_start_row
        data_rows_per_holder = []  # Track which rows contain holder data (not category headers or totals)
        
        for category_key in ['founder', 'investor', 'employee', 'advisor', 'option_pool', 'other']:
            if category_key not in categories:
                continue
            
            category_holders = categories[category_key]
            if not category_holders:
                continue
            
            # Category header
            col = 0
            sheet.write(row, col, category_names.get(category_key, category_key.title()), self.formats['label'])
            row += 1
            
            # Each holder in category
            for holder in category_holders:
                holder_id = holder['holder_id']
                holder_name = holder['name']
                holder_row_positions[holder_id] = row
                
                col = 0
                sheet.write(row, col, holder_name)
                col += 1
                sheet.write(row, col, '')  # Empty column
                col += 1
                
                # Get new shares per round for this holder
                new_shares_per_round = {}
                for instrument in instruments:
                    if instrument.get('holder_id') == holder_id:
                        round_id = instrument.get('round_id')
                        shares = instrument.get('initial_quantity', 0)
                        if round_id:
                            if round_id not in new_shares_per_round:
                                new_shares_per_round[round_id] = 0
                            new_shares_per_round[round_id] += shares
                
                # Track start shares (non-round-specific)
                start_shares_value = 0
                for instrument in instruments:
                    if instrument.get('holder_id') == holder_id and not instrument.get('round_id'):
                        start_shares_value += instrument.get('initial_quantity', 0)
                
                # Write data for each round with formulas
                for round_idx, round_data in enumerate(rounds):
                    round_id = round_data['round_id']
                    
                    new_shares = new_shares_per_round.get(round_id, 0)
                    
                    # Define column positions for this round
                    start_col_idx = col
                    new_col_idx = col + 1
                    total_col_idx = col + 2
                    percent_col_idx = col + 3
                    
                    # Calculate Start shares cell reference
                    if round_idx == 0:
                        # First round: Start = static value (founder shares)
                        if start_shares_value > 0:
                            sheet.write(row, start_col_idx, start_shares_value, self.formats['number'])
                        else:
                            sheet.write(row, start_col_idx, 0, self.formats['number'])
                    else:
                        # Subsequent rounds: Start = previous round's Total
                        prev_total_col_idx = total_col_idx - 5  # 5 columns back (Start, New, Total, %, separator)
                        prev_total_col_letter = self._col_letter(prev_total_col_idx)
                        prev_total_cell_ref = f"{prev_total_col_letter}{row + 1}"
                        sheet.write_formula(row, start_col_idx, f"={prev_total_cell_ref}", self.formats['number'])
                    
                    # New shares: SUMIFS from Ledger table
                    # Formula: =SUMIFS(Ledger[initial_quantity], Ledger[holder_id], holder_id, Ledger[round_id], round_id)
                    new_formula = f'=SUMIFS(Ledger[initial_quantity], Ledger[holder_id], "{holder_id}", Ledger[round_id], "{round_id}")'
                    sheet.write_formula(row, new_col_idx, new_formula, self.formats['number'])
                    
                    # Total = Start + New (formula)
                    start_cell_ref = self._col_letter(start_col_idx) + str(row + 1)
                    new_cell_ref = self._col_letter(new_col_idx) + str(row + 1)
                    total_formula = f"={start_cell_ref} + {new_cell_ref}"
                    sheet.write_formula(row, total_col_idx, total_formula, self.formats['number'])
                    
                    # Percentage: Total / sum of all totals for this round
                    # We'll calculate this after we know all the holder rows
                    # Temporarily write a placeholder
                    sheet.write(row, percent_col_idx, 0, self.formats['percent'])
                    
                    # Separator
                    col += 5
                
                row += 1
                data_rows_per_holder.append(row - 1)
            
            # Blank row after category
            sheet.write(row, 0, '')
            row += 1
        
        # Now update percentage formulas for all rounds
        sheet_name = "'Cap Table Progression'"
        for round_idx, round_data in enumerate(rounds):
            # Round columns: Shareholder (col 0), Sep (col 1), Start (col 2), New (col 3), Total (col 4), % (col 5), Sep (col 6), ...
            # For each subsequent round, add 5 columns: Start (col 2+5N), New (col 3+5N), Total (col 4+5N), % (col 5+5N)
            total_col_base = 4 + (round_idx * 5)  # Total (#) is at column 4 for round 0, 9 for round 1, etc.
            percent_col_base = 5 + (round_idx * 5)  # % is one column after Total
            
            if data_rows_per_holder:
                total_col_letter = self._col_letter(total_col_base)
                
                # Build sum range: all holder rows for this round's Total column
                range_start = f"{total_col_letter}{data_rows_per_holder[0] + 1}"
                range_end = f"{total_col_letter}{data_rows_per_holder[-1] + 1}"
                sum_range = f"{sheet_name}!{range_start}:{range_end}"
                
                for holder_row in data_rows_per_holder:
                    # Individual total cell
                    total_cell_ref = f"{total_col_letter}{holder_row + 1}"
                    
                    # Percentage formula: Total / Sum of all totals
                    percent_formula = f"=IFERROR({total_cell_ref} / SUM({sum_range}), 0)"
                    sheet.write_formula(holder_row, percent_col_base, percent_formula, self.formats['percent'])
        
        # TOTAL row
        sheet.write(row, 0, 'TOTAL', self.formats['label'])
        sheet.write(row, 1, '')
        col = 2
        
        total_row = row
        
        # Calculate totals for each round with formulas
        for round_idx in range(len(rounds)):
            # Column indices for this round
            start_col_pos = col
            new_col_pos = col + 1
            total_col_pos = col + 2
            percent_col_pos = col + 3
            sep_col_pos = col + 4
            
            if data_rows_per_holder:
                # Start: sum of all Start values from holders above
                start_col_letter = self._col_letter(start_col_pos)
                start_range_start = f"{start_col_letter}{data_rows_per_holder[0] + 1}"
                start_range_end = f"{start_col_letter}{data_rows_per_holder[-1] + 1}"
                start_formula = f"=SUM({sheet_name}!{start_range_start}:{start_range_end})"
                sheet.write_formula(row, start_col_pos, start_formula, self.formats['number'])
                
                # New: sum of all shares issued in this round from Ledger table
                round_id = rounds[round_idx]['round_id']
                new_formula = f'=SUMIF(Ledger[round_id], "{round_id}", Ledger[initial_quantity])'
                sheet.write_formula(row, new_col_pos, new_formula, self.formats['number'])
                
                # Total: sum of all Total values from holders above
                total_col_letter = self._col_letter(total_col_pos)
                total_range_start = f"{total_col_letter}{data_rows_per_holder[0] + 1}"
                total_range_end = f"{total_col_letter}{data_rows_per_holder[-1] + 1}"
                total_formula = f"=SUM({sheet_name}!{total_range_start}:{total_range_end})"
                sheet.write_formula(row, total_col_pos, total_formula, self.formats['number'])
                
                # Percentage: sum of all percentages from holders above
                percent_col_letter = self._col_letter(percent_col_pos)
                percent_range_start = f"{percent_col_letter}{data_rows_per_holder[0] + 1}"
                percent_range_end = f"{percent_col_letter}{data_rows_per_holder[-1] + 1}"
                percent_formula = f"=SUM({sheet_name}!{percent_range_start}:{percent_range_end})"
                sheet.write_formula(row, percent_col_pos, percent_formula, self.formats['percent'])
            else:
                # No holders, write zeros
                sheet.write(row, start_col_pos, 0, self.formats['number'])
                sheet.write(row, new_col_pos, 0, self.formats['number'])
                sheet.write(row, total_col_pos, 0, self.formats['number'])
                sheet.write(row, percent_col_pos, 0, self.formats['percent'])
            
            # Write separator
            sheet.write(row, sep_col_pos, '')
            
            # Move to next round (5 columns ahead: Start, New, Total, %, Sep)
            col = sep_col_pos + 1
        
        # Set column widths
        sheet.set_column(0, 0, 20)  # Shareholder names
        sheet.set_column(1, 1, 2)   # Separator
        
        # Round columns
        for i in range(len(rounds)):
            base_col = 2 + (i * 5)
            sheet.set_column(base_col, base_col, 12)      # Start
            sheet.set_column(base_col + 1, base_col + 1, 12)  # New
            sheet.set_column(base_col + 2, base_col + 2, 12)  # Total
            sheet.set_column(base_col + 3, base_col + 3, 10)  # %
            sheet.set_column(base_col + 4, base_col + 4, 2)   # Separator
    
    def _create_vesting_sheet(self):
        """Create Vesting sheet for option grants with vesting schedules."""
        sheet = self.workbook.add_worksheet('Vesting')
        self.sheets['Vesting'] = sheet
        
        columns = [
            'instrument_id', 'holder_name', 'class_name',
            'total_granted', 'grant_date', 'cliff_days', 'vesting_period_days',
            'days_elapsed', 'vested_shares', 'unvested_shares', 'percent_vested'
        ]
        
        # Write headers
        for col_idx, col_name in enumerate(columns):
            sheet.write(0, col_idx, col_name, self.formats['header'])
        
        # Find instruments with vesting terms
        instruments = self.data.get('instruments', [])
        holders_map = {h['holder_id']: h for h in self.data.get('holders', [])}
        classes_map = {c['class_id']: c for c in self.data.get('classes', [])}
        
        row_idx = 1
        for instrument in instruments:
            vesting_terms = instrument.get('vesting_terms')
            if not vesting_terms:
                continue
            
            holder = holders_map.get(instrument.get('holder_id'), {})
            sec_class = classes_map.get(instrument.get('class_id'), {})
            
            sheet.write(row_idx, 0, instrument.get('instrument_id', ''))
            sheet.write(row_idx, 1, holder.get('name', ''))
            sheet.write(row_idx, 2, sec_class.get('name', ''))
            sheet.write(row_idx, 3, instrument.get('initial_quantity', 0), self.formats['number'])
            sheet.write(row_idx, 4, vesting_terms.get('grant_date', ''), self.formats['date'])
            sheet.write(row_idx, 5, vesting_terms.get('cliff_days', 0))
            sheet.write(row_idx, 6, vesting_terms.get('vesting_period_days', 0))
            
            # Days elapsed formula
            grant_cell = self._col_letter(4) + str(row_idx + 1)
            days_formula = f"=DAYS(Current_Date, {grant_cell})"
            sheet.write_formula(row_idx, 7, days_formula, self.formats['number'])
            
            # Vested shares formula
            total_cell = self._col_letter(3) + str(row_idx + 1)
            cliff_cell = self._col_letter(5) + str(row_idx + 1)
            period_cell = self._col_letter(6) + str(row_idx + 1)
            days_cell = self._col_letter(7) + str(row_idx + 1)
            
            vested_formula = f"={total_cell} * MIN(1, MAX(0, ({days_cell} - {cliff_cell}) / {period_cell}))"
            sheet.write_formula(row_idx, 8, vested_formula, self.formats['number'])
            
            # Unvested shares
            vested_cell = self._col_letter(8) + str(row_idx + 1)
            unvested_formula = f"={total_cell} - {vested_cell}"
            sheet.write_formula(row_idx, 9, unvested_formula, self.formats['number'])
            
            # Percent vested
            percent_formula = f"=IFERROR({vested_cell} / {total_cell}, 0)"
            sheet.write_formula(row_idx, 10, percent_formula, self.formats['percent'])
            
            row_idx += 1
        
        sheet.set_column(0, 0, 12)
        sheet.set_column(1, 2, 20)
        sheet.set_column(3, 10, 15)
    
    def _create_waterfall_sheet(self):
        """Create Waterfall sheet for liquidation scenarios."""
        sheet = self.workbook.add_worksheet('Waterfall')
        self.sheets['Waterfall'] = sheet
        
        columns = [
            'class_name', 'class_type', 'shares', 'ownership_fds',
            'lp_multiple', 'participation_type', 'seniority_rank',
            'lp_amount', 'exit_payout', 'payout_per_share'
        ]
        
        # Write headers
        for col_idx, col_name in enumerate(columns):
            sheet.write(0, col_idx, col_name, self.formats['header'])
        
        # Get classes with terms
        classes = self.data.get('classes', [])
        terms_map = {t['terms_id']: t for t in self.data.get('terms', [])}
        
        # Sort by seniority (lower rank = more senior, paid first)
        classes_with_terms = []
        for sec_class in classes:
            terms_id = sec_class.get('terms_id')
            if terms_id and terms_id in terms_map:
                classes_with_terms.append((sec_class, terms_map[terms_id]))
        
        classes_with_terms.sort(key=lambda x: x[1].get('seniority_rank', 999))
        
        row_idx = 1
        prior_payments_sum = ""
        
        for sec_class, terms in classes_with_terms:
            class_name = sec_class.get('name', '')
            class_type = sec_class.get('type', '')
            
            sheet.write(row_idx, 0, class_name)
            sheet.write(row_idx, 1, class_type)
            
            # Shares: sum from Ledger where class_name matches
            shares_formula = f'=SUMIF(Ledger[class_name], "{class_name}", Ledger[current_quantity])'
            sheet.write_formula(row_idx, 2, shares_formula, self.formats['number'])
            
            # Ownership FDS
            shares_cell = self._col_letter(2) + str(row_idx + 1)
            ownership_formula = f"=IFERROR({shares_cell} / Total_FDS, 0)"
            sheet.write_formula(row_idx, 3, ownership_formula, self.formats['percent'])
            
            # LP Multiple
            lp_multiple = terms.get('liquidation_multiple', 1.0)
            sheet.write(row_idx, 4, lp_multiple, self.formats['decimal'])
            
            # Participation type
            participation = terms.get('participation_type', 'non_participating')
            sheet.write(row_idx, 5, participation)
            
            # Seniority rank
            seniority = terms.get('seniority_rank', 0)
            sheet.write(row_idx, 6, seniority)
            
            # LP Amount: shares * acquisition_price * lp_multiple
            # Simplified: use SUMIF to get investment amount for this class
            lp_formula = f'=SUMIF(Ledger[class_name], "{class_name}", Ledger[initial_quantity]) * ' \
                        f'AVERAGEIF(Ledger[class_name], "{class_name}", Ledger[acquisition_price]) * ' \
                        f'{self._col_letter(4)}{row_idx + 1}'
            sheet.write_formula(row_idx, 7, lp_formula, self.formats['currency'])
            
            # Exit Payout (depends on participation type)
            lp_cell = self._col_letter(7) + str(row_idx + 1)
            ownership_cell = self._col_letter(3) + str(row_idx + 1)
            
            if participation == 'non_participating':
                # Greater of LP or pro-rata
                payout_formula = f"=MAX({lp_cell}, Exit_Val * {ownership_cell})"
            elif participation in ['participating', 'capped_participating']:
                # LP + participation in remaining
                if prior_payments_sum:
                    remaining = f"(Exit_Val - {prior_payments_sum})"
                else:
                    remaining = "Exit_Val"
                payout_formula = f"={lp_cell} + ({remaining} * {ownership_cell})"
            else:
                # Common stock: pro-rata of remaining after all LP
                if prior_payments_sum:
                    payout_formula = f"=(Exit_Val - {prior_payments_sum}) * {ownership_cell}"
                else:
                    payout_formula = f"=Exit_Val * {ownership_cell}"
            
            sheet.write_formula(row_idx, 8, payout_formula, self.formats['currency'])
            
            # Payout per share
            payout_cell = self._col_letter(8) + str(row_idx + 1)
            per_share_formula = f"=IFERROR({payout_cell} / {shares_cell}, 0)"
            sheet.write_formula(row_idx, 9, per_share_formula, self.formats['currency'])
            
            # Update prior payments sum for next iteration
            if not prior_payments_sum:
                prior_payments_sum = payout_cell
            else:
                prior_payments_sum = f"{prior_payments_sum} + {payout_cell}"
            
            row_idx += 1
        
        # Add common stock at the end
        sheet.write(row_idx, 0, 'Common Stock')
        sheet.write(row_idx, 1, 'common')
        
        shares_formula = '=SUMIF(Ledger[class_type], "common", Ledger[current_quantity])'
        sheet.write_formula(row_idx, 2, shares_formula, self.formats['number'])
        
        shares_cell = self._col_letter(2) + str(row_idx + 1)
        ownership_formula = f"=IFERROR({shares_cell} / Total_FDS, 0)"
        sheet.write_formula(row_idx, 3, ownership_formula, self.formats['percent'])
        
        sheet.write(row_idx, 4, '-')
        sheet.write(row_idx, 5, '-')
        sheet.write(row_idx, 6, 999)  # Lowest priority
        sheet.write(row_idx, 7, 0)
        
        # Common gets remaining after all preferred
        ownership_cell = self._col_letter(3) + str(row_idx + 1)
        if prior_payments_sum:
            common_payout = f"=(Exit_Val - {prior_payments_sum}) * {ownership_cell}"
        else:
            common_payout = f"=Exit_Val * {ownership_cell}"
        sheet.write_formula(row_idx, 8, common_payout, self.formats['currency'])
        
        payout_cell = self._col_letter(8) + str(row_idx + 1)
        per_share_formula = f"=IFERROR({payout_cell} / {shares_cell}, 0)"
        sheet.write_formula(row_idx, 9, per_share_formula, self.formats['currency'])
        
        sheet.set_column(0, 1, 20)
        sheet.set_column(2, 9, 15)
    
    def _write_table(self, sheet, table_name: str, start_row: int, start_col: int,
                    columns: List[str], data: List[Dict[str, Any]], 
                    formulas: Dict[str, str]):
        """
        Write an Excel Table with data and formulas.
        
        Args:
            sheet: Worksheet object
            table_name: Name for the Excel Table
            start_row: Starting row (0-based)
            start_col: Starting column (0-based)
            columns: List of column names
            data: List of row data dictionaries
            formulas: Dict of column_name -> formula template
        """
        if not data:
            return
        
        # Prepare table data for xlsxwriter
        table_rows = []
        for row_data in data:
            table_row = []
            for col_name in columns:
                value = row_data.get(col_name, '')
                table_row.append(value)
            table_rows.append(table_row)
        
        # Define table range
        end_row = start_row + len(data)  # +1 for header is implicit
        end_col = start_col + len(columns) - 1
        
        # Create column definitions with formulas
        col_defs = []
        for col_name in columns:
            col_def = {'header': col_name}
            if col_name in formulas:
                col_def['formula'] = formulas[col_name]
            col_defs.append(col_def)
        
        # Write table
        sheet.add_table(start_row, start_col, end_row, end_col, {
            'name': table_name,
            'data': table_rows,
            'columns': col_defs,
            'style': 'Table Style Medium 2'
        })
    
    def _col_letter(self, col_idx: int) -> str:
        """Convert 0-based column index to Excel letter."""
        result = []
        col_idx += 1
        while col_idx > 0:
            col_idx -= 1
            result.append(chr(col_idx % 26 + ord('A')))
            col_idx //= 26
        return ''.join(reversed(result))

