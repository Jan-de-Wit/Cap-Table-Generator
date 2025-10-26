"""
Interest Formula Generator

Formulas for calculating accrued interest and days passed on convertible instruments.
"""


def create_days_passed_formula(start_date_ref: str, end_date_ref: str) -> str:
    """
    Create formula to calculate days between two dates.
    
    Args:
        start_date_ref: Reference to start date cell
        end_date_ref: Reference to end date cell
        
    Returns:
        Excel formula string for days passed
    """
    return f"=IFERROR({end_date_ref} - {start_date_ref}, 0)"


def create_accrued_interest_formula(principal_ref: str, interest_rate_ref: str,
                                   start_date_ref: str, end_date_ref: str = "Current_Date",
                                   interest_type: str = "simple") -> str:
    """
    Create interest accrual formula (simple or compound).
    
    Args:
        principal_ref: Reference to principal/investment amount
        interest_rate_ref: Reference to annual interest rate (as decimal)
        start_date_ref: Reference to start date
        end_date_ref: Reference to end date (default: Current_Date)
        interest_type: "simple" or "compound" (default: simple)
        
    Returns:
        Excel formula string for accrued interest
    """
    # Calculate years elapsed (fractional)
    days_elapsed = f"DAYS({end_date_ref}, {start_date_ref})"
    years_elapsed = f"({days_elapsed} / 365)"
    
    if interest_type == "compound":
        # Compound interest: Principal * ((1 + Rate)^Years - 1)
        return f"=IFERROR({principal_ref} * (POWER((1 + {interest_rate_ref}), {years_elapsed}) - 1), 0)"
    else:
        # Simple interest: Principal * Rate * Years
        return f"=IFERROR({principal_ref} * {interest_rate_ref} * {years_elapsed}, 0)"

