"""
Base Formula Resolver

Core functionality for resolving Formula Encoding Objects (FEO) into Excel formulas.
Handles placeholder replacement, reference resolution, and formula validation.
"""

import re
from typing import Dict, List, Any, Optional
from ..dlm import DeterministicLayoutMap


class FormulaResolver:
    """
    Resolves Formula Encoding Objects into Excel formula strings.
    Translates symbolic placeholders into actual Excel references.
    """
    
    def __init__(self, dlm: DeterministicLayoutMap):
        """Initialize formula resolver with a DLM instance."""
        self.dlm = dlm
        
    def resolve_feo(self, feo: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
        """
        Resolve a Formula Encoding Object to an Excel formula string.
        
        Args:
            feo: Formula Encoding Object with formula_string and dependency_refs
            context: Optional context (e.g., current entity UUID, row info)
            
        Returns:
            Excel formula string ready for injection
        """
        if not isinstance(feo, dict) or not feo.get('is_calculated'):
            raise ValueError("Not a valid Formula Encoding Object")
        
        formula_string = feo.get('formula_string', '')
        dependency_refs = feo.get('dependency_refs', [])
        
        # Build replacement map: placeholder -> Excel reference
        replacements = {}
        for dep in dependency_refs:
            placeholder = dep.get('placeholder')
            path = dep.get('path')
            reference_type = dep.get('reference_type', 'uuid_lookup')
            
            if not placeholder or not path:
                continue
            
            # Resolve the path to an Excel reference
            excel_ref = self._resolve_path(path, reference_type, context)
            if excel_ref:
                replacements[placeholder] = excel_ref
        
        # Replace placeholders in formula string
        resolved_formula = self._replace_placeholders(formula_string, replacements)
        
        # Ensure formula starts with '='
        if not resolved_formula.startswith('='):
            resolved_formula = '=' + resolved_formula
        
        # Wrap division operations in IFERROR for safety
        resolved_formula = self._wrap_divisions_in_iferror(resolved_formula)
        
        return resolved_formula
    
    def _resolve_path(self, path: str, reference_type: str, 
                     context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Resolve a JSON pointer or identifier to an Excel reference.
        
        Args:
            path: JSON pointer, UUID, or symbolic name
            reference_type: Type of reference (named_range, structured_reference, etc.)
            context: Optional context information
            
        Returns:
            Excel reference string or None
        """
        # Handle named ranges (e.g., "Total_FDS", "Current_PPS")
        if reference_type == 'named_range':
            return self.dlm.resolve_reference(path, context)
        
        # Handle structured references (table columns)
        if reference_type == 'structured_reference':
            # Path might be like "Ledger.shares" or "[@[shares]]"
            if '.' in path:
                table_name, column_name = path.split('.', 1)
                return self.dlm.get_structured_reference(table_name, column_name, current_row=True)
            return path  # Already formatted
        
        # Handle UUID lookups
        if reference_type == 'uuid_lookup':
            return self.dlm.resolve_reference(path, context)
        
        # Handle cell references
        if reference_type == 'cell_reference':
            return self.dlm.resolve_reference(path, context)
        
        # Fallback: try direct resolution
        return self.dlm.resolve_reference(path, context)
    
    def _replace_placeholders(self, formula: str, replacements: Dict[str, str]) -> str:
        """
        Replace symbolic placeholders in formula with Excel references.
        
        Args:
            formula: Formula string with placeholders
            replacements: Dict mapping placeholder -> Excel reference
            
        Returns:
            Formula with replaced placeholders
        """
        result = formula
        
        # Sort by length (descending) to avoid partial replacements
        sorted_placeholders = sorted(replacements.keys(), key=len, reverse=True)
        
        for placeholder in sorted_placeholders:
            excel_ref = replacements[placeholder]
            # Use word boundary matching to avoid partial replacements
            # Match placeholder as whole word (not part of another identifier)
            pattern = r'\b' + re.escape(placeholder) + r'\b'
            result = re.sub(pattern, excel_ref, result)
        
        return result
    
    def _wrap_divisions_in_iferror(self, formula: str) -> str:
        """
        Wrap division operations in IFERROR to handle divide-by-zero gracefully.
        
        Args:
            formula: Excel formula string
            
        Returns:
            Formula with divisions wrapped in IFERROR
        """
        # Simple pattern: look for division not already in IFERROR
        # This is a basic implementation; a full parser would be more robust
        
        # Check if formula already contains IFERROR at the start
        if formula.strip().startswith('=IFERROR('):
            return formula
        
        # If formula contains division, wrap the whole thing
        if '/' in formula:
            # Remove leading = if present
            f = formula.lstrip('=')
            # Wrap in IFERROR, return 0 on error
            return f"=IFERROR({f}, 0)"
        
        return formula

