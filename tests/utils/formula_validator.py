"""
Formula Validator

Validate Excel formulas in generated files.
"""

from typing import List, Dict, Any
from .excel_reader import ExcelReader


class FormulaValidator:
    """Validate Excel formulas."""
    
    def __init__(self, excel_reader: ExcelReader):
        """
        Initialize formula validator.
        
        Args:
            excel_reader: ExcelReader instance
        """
        self.excel_reader = excel_reader
    
    def validate_formulas(self, sheet_name: str) -> List[Dict[str, Any]]:
        """
        Validate formulas in a sheet.
        
        Args:
            sheet_name: Name of sheet to validate
            
        Returns:
            List of validation results
        """
        sheet = self.excel_reader.get_sheet(sheet_name)
        if not sheet:
            return []
        
        results = []
        
        # Iterate through all cells with formulas
        for row in sheet.iter_rows():
            for cell in row:
                if cell.data_type == 'f':  # Formula
                    formula = cell.value
                    result = {
                        "cell": cell.coordinate,
                        "formula": formula,
                        "value": cell.value,
                        "is_valid": True,
                        "error": None
                    }
                    
                    # Basic validation - check for common errors
                    if formula and isinstance(formula, str):
                        if formula.startswith("=#REF!"):
                            result["is_valid"] = False
                            result["error"] = "Reference error"
                        elif formula.startswith("=#VALUE!"):
                            result["is_valid"] = False
                            result["error"] = "Value error"
                        elif formula.startswith("=#DIV/0!"):
                            result["is_valid"] = False
                            result["error"] = "Division by zero"
                    
                    results.append(result)
        
        return results
    
    def find_formula_errors(self, sheet_name: str) -> List[Dict[str, Any]]:
        """
        Find formula errors in a sheet.
        
        Args:
            sheet_name: Name of sheet to check
            
        Returns:
            List of formula errors
        """
        results = self.validate_formulas(sheet_name)
        return [r for r in results if not r["is_valid"]]

