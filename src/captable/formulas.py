"""
Formula Resolver
Processes Formula Encoding Objects (FEO) and translates symbolic formulas
into actual Excel formulas with proper references.
"""

import re
from typing import Dict, List, Any, Optional
from .dlm import DeterministicLayoutMap


class FormulaResolver:
    """
    Resolves Formula Encoding Objects into Excel formula strings.
    Translates symbolic placeholders into actual Excel references.
    """
    
    def __init__(self, dlm: DeterministicLayoutMap):
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
        
        # Pattern to match division operations: (something) / (something)
        # This is simplified and may not catch all cases perfectly
        
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
    
    def create_ownership_formula(self, shares_ref: str, total_fds_ref: str = "Total_FDS") -> str:
        """
        Create a standard ownership percentage formula.
        
        Args:
            shares_ref: Reference to shares held
            total_fds_ref: Reference to total FDS (default: Named Range)
            
        Returns:
            Excel formula string
        """
        return f"=IFERROR({shares_ref} / {total_fds_ref}, 0)"
    
    def create_tsm_gross_itm_formula(self, quantity_ref: str, strike_ref: str,
                                     current_pps_ref: str = "Current_PPS") -> str:
        """
        Create Treasury Stock Method gross in-the-money shares formula.
        
        Args:
            quantity_ref: Reference to option quantity
            strike_ref: Reference to strike price
            current_pps_ref: Reference to current PPS
            
        Returns:
            Excel formula string
        """
        return f"=IF({current_pps_ref} > {strike_ref}, {quantity_ref}, 0)"
    
    def create_tsm_proceeds_formula(self, gross_itm_ref: str, strike_ref: str) -> str:
        """Create TSM proceeds from exercise formula."""
        return f"={gross_itm_ref} * {strike_ref}"
    
    def create_tsm_repurchase_formula(self, proceeds_ref: str,
                                      current_pps_ref: str = "Current_PPS") -> str:
        """Create TSM shares repurchased formula."""
        return f"=IFERROR({proceeds_ref} / {current_pps_ref}, 0)"
    
    def create_tsm_net_dilution_formula(self, gross_itm_ref: str, repurchase_ref: str) -> str:
        """Create TSM net dilution formula."""
        return f"={gross_itm_ref} - {repurchase_ref}"
    
    def create_vesting_formula(self, total_granted_ref: str, grant_date_ref: str,
                              cliff_days_ref: str, vesting_period_ref: str,
                              current_date_ref: str = "Current_Date") -> str:
        """
        Create vesting schedule formula.
        
        Args:
            total_granted_ref: Reference to total shares granted
            grant_date_ref: Reference to grant date
            cliff_days_ref: Reference to cliff period (days)
            vesting_period_ref: Reference to total vesting period (days)
            current_date_ref: Reference to current/evaluation date
            
        Returns:
            Excel formula string
        """
        days_elapsed = f"DAYS({current_date_ref}, {grant_date_ref})"
        cliff_check = f"MAX(0, ({days_elapsed} - {cliff_days_ref}))"
        vesting_fraction = f"{cliff_check} / {vesting_period_ref}"
        return f"={total_granted_ref} * MIN(1, MAX(0, {vesting_fraction}))"
    
    def create_safe_conversion_price_formula(self, round_pps_ref: str, discount_rate_ref: str,
                                            price_cap_ref: str, shares_preround_ref: str) -> str:
        """
        Create SAFE/convertible note conversion price formula.
        
        Args:
            round_pps_ref: Reference to round price per share
            discount_rate_ref: Reference to discount rate
            price_cap_ref: Reference to valuation cap
            shares_preround_ref: Reference to pre-round shares
            
        Returns:
            Excel formula string
        """
        discounted_price = f"{round_pps_ref} * (1 - {discount_rate_ref})"
        cap_price = f"{price_cap_ref} / {shares_preround_ref}"
        return f"=MIN({discounted_price}, {cap_price})"
    
    def create_safe_conversion_shares_formula(self, investment_ref: str,
                                             conversion_price_ref: str) -> str:
        """Create SAFE conversion shares formula."""
        return f"=IFERROR({investment_ref} / {conversion_price_ref}, 0)"
    
    def create_waterfall_nonparticipating_formula(self, lp_amount_ref: str,
                                                  exit_val_ref: str,
                                                  ownership_ref: str) -> str:
        """
        Create non-participating preferred liquidation payout formula.
        
        Args:
            lp_amount_ref: Reference to liquidation preference amount
            exit_val_ref: Reference to exit value
            ownership_ref: Reference to ownership percentage (FDS)
            
        Returns:
            Excel formula string
        """
        prorata_payout = f"{exit_val_ref} * {ownership_ref}"
        return f"=MAX({lp_amount_ref}, {prorata_payout})"
    
    def create_waterfall_participating_formula(self, lp_amount_ref: str,
                                              exit_val_ref: str,
                                              prior_payments_ref: str,
                                              ownership_ref: str) -> str:
        """
        Create participating preferred liquidation payout formula.
        
        Args:
            lp_amount_ref: Reference to liquidation preference amount
            exit_val_ref: Reference to total exit value
            prior_payments_ref: Reference to sum of prior (senior) payments
            ownership_ref: Reference to ownership percentage (FDS)
            
        Returns:
            Excel formula string
        """
        remaining = f"({exit_val_ref} - {prior_payments_ref})"
        participation = f"{remaining} * {ownership_ref}"
        return f"={lp_amount_ref} + {participation}"
    
    def create_option_pool_topup_formula(self, fds_preround_ref: str,
                                        target_percent_ref: str) -> str:
        """
        Create option pool top-up calculation formula.
        
        Args:
            fds_preround_ref: Reference to pre-round FDS
            target_percent_ref: Reference to target pool percentage
            
        Returns:
            Excel formula string
        """
        numerator = f"{fds_preround_ref} * {target_percent_ref}"
        denominator = f"(1 - {target_percent_ref})"
        return f"=IFERROR({numerator} / {denominator}, 0)"

