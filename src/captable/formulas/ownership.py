"""
Ownership Formula Generator

Formulas for calculating ownership percentages and dilution.
"""


def create_ownership_formula(shares_ref: str, total_fds_ref: str = "Total_FDS") -> str:
    """
    Create a standard ownership percentage formula.
    
    Args:
        shares_ref: Reference to shares held
        total_fds_ref: Reference to total FDS (default: Named Range)
        
    Returns:
        Excel formula string
    """
    return f"=IFERROR({shares_ref} / {total_fds_ref}, 0)"


def create_option_pool_topup_formula(fds_preround_ref: str, target_percent_ref: str) -> str:
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

