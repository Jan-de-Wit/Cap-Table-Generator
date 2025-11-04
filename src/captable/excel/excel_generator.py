"""
Excel Generator

Creates Excel workbooks from cap table JSON data using xlsxwriter.
Implements standardized sheet structure with Named Ranges, Excel Tables, and formulas.

This module has been refactored to use modular sheet generators for maintainability.
The main ExcelGenerator class orchestrates generation by calling specialized generators.

ARCHITECTURE - ROUND-BASED DESIGN:

The Excel workbook centers around the ROUNDS sheet as the source of truth, with each
round containing nested instruments. The Cap Table Progression provides a summary view.

Data Flow:
1. Rounds Sheet (Source of Truth)
   - Each round displayed vertically with constants and nested instruments
   - Formulas calculate share quantities based on round's calculation_type
   - Different column sets for: fixed_shares, target_percentage, valuation_based, convertible

2. Cap Table Progression (Summary View)
   - Shows ownership evolution across rounds
   - References instrument shares from Rounds sheet
   - Chains rounds: Round 1 Total → Round 2 Start → Round 2 Total, etc.

All calculations are transparent and fully traceable through Excel formulas.
No hardcoded share amounts - everything derives from source data.
"""

import xlsxwriter
from typing import Dict, List, Any, Optional
from datetime import datetime
from ..dlm import DeterministicLayoutMap
from ..formulas import FormulaResolver
from .formatters import ExcelFormatters
from .sheet_generators import (
    RoundsSheetGenerator,
    ProgressionSheetGenerator,
    ProRataSheetGenerator
)


class ExcelGenerator:
    """
    Generates Excel workbooks with dynamic formulas from cap table data.

    This class orchestrates the creation of Excel workbooks by coordinating
    specialized sheet generators that handle individual sheet types.
    """

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
        Generate the complete Excel workbook with round-based architecture.

        Sheet creation order:
        1. Rounds (SOURCE OF TRUTH - contains all instruments nested within rounds)
        2. Cap Table Progression (SUMMARY VIEW - references Rounds sheet)

        Returns:
            Path to generated Excel file
        """
        # Create workbook
        self.workbook = xlsxwriter.Workbook(self.output_path)
        self.workbook.set_calc_mode('auto')  # Force recalculation on open

        # Set default format for all cells: font size 10 and background color #869A78
        self.workbook.formats[0].set_font_size(10)
        self.workbook.formats[0].set_bg_color('#869A78')

        # Create formats
        self.formats = ExcelFormatters.create_formats(self.workbook)

        # STEP 1: Create Rounds sheet (SOURCE OF TRUTH)
        # Each round contains constants and nested instruments
        # Instruments displayed with columns based on round's calculation_type
        # Contains base shares only (no pro rata)
        rounds_gen = RoundsSheetGenerator(
            self.workbook, self.data, self.formats, self.dlm, self.formula_resolver
        )
        self.sheets['Rounds'] = rounds_gen.generate()

        # STEP 2: Create Pro Rata Allocations sheet
        # Lists all stakeholders per round and calculates pro rata share allocations
        # Pro rata calculations happen AFTER regular round shares are calculated
        pro_rata_gen = ProRataSheetGenerator(
            self.workbook, self.data, self.formats, self.dlm, self.formula_resolver
        )
        pro_rata_gen.set_round_ranges(rounds_gen.get_round_ranges())
        # Pass shares_issued references for each round
        self.sheets['Pro Rata Allocations'] = pro_rata_gen.generate()

        # STEP 3: Create Cap Table Progression sheet (SUMMARY VIEW)
        # References instrument shares from Rounds sheet + Pro Rata Allocations sheet
        # Shows ownership evolution across rounds
        progression_gen = ProgressionSheetGenerator(
            self.workbook, self.data, self.formats, self.dlm, self.formula_resolver
        )
        # Pass round ranges from rounds sheet
        progression_gen.round_ranges = rounds_gen.get_round_ranges()
        self.sheets['Cap Table Progression'] = progression_gen.generate()

        # Close and save
        self.workbook.close()

        return self.output_path
