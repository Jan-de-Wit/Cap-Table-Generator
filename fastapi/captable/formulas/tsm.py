"""
Treasury Stock Method (TSM) Formula Generator

Formulas for calculating TSM dilution from in-the-money options.
"""


def create_tsm_gross_itm_formula(quantity_ref: str, strike_ref: str,
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


def create_tsm_proceeds_formula(gross_itm_ref: str, strike_ref: str) -> str:
    """Create TSM proceeds from exercise formula."""
    return f"={gross_itm_ref} * {strike_ref}"


def create_tsm_repurchase_formula(proceeds_ref: str, current_pps_ref: str = "Current_PPS") -> str:
    """Create TSM shares repurchased formula."""
    return f"=IFERROR({proceeds_ref} / {current_pps_ref}, 0)"


def create_tsm_net_dilution_formula(gross_itm_ref: str, repurchase_ref: str) -> str:
    """Create TSM net dilution formula."""
    return f"={gross_itm_ref} - {repurchase_ref}"

