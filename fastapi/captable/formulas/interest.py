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
                                    interest_type: str = "simple", interest_type_ref: str = None) -> str:
    """
    Create interest accrual formula based on interest type.

    Args:
        principal_ref: Reference to principal/investment amount
        interest_rate_ref: Reference to annual interest rate (as decimal)
        start_date_ref: Reference to start date
        end_date_ref: Reference to end date (default: Current_Date)
        interest_type: One of "simple", "compound_yearly", "compound_monthly", 
                      "compound_daily", or "no_interest" (default: simple)
                      Used only when interest_type_ref is not provided
        interest_type_ref: Reference to cell containing interest type (optional).
                          If provided, formula will dynamically check this cell value.

    Returns:
        Excel formula string for accrued interest
    """
    # Calculate days elapsed
    days_elapsed = f"IFERROR({end_date_ref} - {start_date_ref}, 0)"

    # If interest_type_ref is provided, create dynamic formula with IF statements
    if interest_type_ref:
        # Create formulas for each interest type
        years_elapsed = f"({days_elapsed} / 365)"

        # Simple interest formula
        simple_formula = f"{principal_ref} * {interest_rate_ref} * {years_elapsed}"

        # Compound yearly formula
        compound_yearly_formula = f"{principal_ref} * (POWER((1 + {interest_rate_ref}), {years_elapsed}) - 1)"

        # Compound monthly formula
        months_elapsed = f"({days_elapsed} / 365 * 12)"
        monthly_rate = f"({interest_rate_ref} / 12)"
        compound_monthly_formula = f"{principal_ref} * (POWER((1 + {monthly_rate}), {months_elapsed}) - 1)"

        # Compound daily formula
        daily_rate = f"({interest_rate_ref} / 365)"
        compound_daily_formula = f"{principal_ref} * (POWER((1 + {daily_rate}), {days_elapsed}) - 1)"

        # Use IFS function to check interest_type_ref cell value
        # IFS checks conditions in order and returns the first matching result
        # Format: IFS(condition1, value1, condition2, value2, ..., default)
        # Use IF for compatibility (IFS is not available in older Excel)
        # Check for both original format and human-friendly format (with spaces and title case)
        formula = (
            f"=IFERROR("
            f"IF(OR({interest_type_ref}=\"no_interest\", {interest_type_ref}=\"No interest\"), 0, "
            f"IF(OR({interest_type_ref}=\"simple\", {interest_type_ref}=\"Simple interest\"), {simple_formula}, "
            f"IF(OR({interest_type_ref}=\"compound_yearly\", {interest_type_ref}=\"Compounded yearly\"), {compound_yearly_formula}, "
            f"IF(OR({interest_type_ref}=\"compound_monthly\", {interest_type_ref}=\"Compounded monthly\"), {compound_monthly_formula}, "
            f"IF(OR({interest_type_ref}=\"compound_daily\", {interest_type_ref}=\"Compounded daily\"), {compound_daily_formula}, "
            f"{simple_formula}))))), 0)"
        )
        return formula

    # Static formula based on interest_type parameter (legacy behavior)
    if interest_type == "no_interest":
        # No interest: return 0
        return f"=0"

    elif interest_type == "simple":
        # Simple interest: Principal * Rate * (Days / 365)
        years_elapsed = f"({days_elapsed} / 365)"
        return f"=IFERROR({principal_ref} * {interest_rate_ref} * {years_elapsed}, 0)"

    elif interest_type == "compound_yearly":
        # Compound yearly: Principal * ((1 + Rate)^(Days/365) - 1)
        years_elapsed = f"({days_elapsed} / 365)"
        return f"=IFERROR({principal_ref} * (POWER((1 + {interest_rate_ref}), {years_elapsed}) - 1), 0)"

    elif interest_type == "compound_monthly":
        # Compound monthly: Principal * ((1 + Rate/12)^(Days/365*12) - 1)
        months_elapsed = f"({days_elapsed} / 365 * 12)"
        monthly_rate = f"({interest_rate_ref} / 12)"
        return f"=IFERROR({principal_ref} * (POWER((1 + {monthly_rate}), {months_elapsed}) - 1), 0)"

    elif interest_type == "compound_daily":
        # Compound daily: Principal * ((1 + Rate/365)^Days - 1)
        daily_rate = f"({interest_rate_ref} / 365)"
        return f"=IFERROR({principal_ref} * (POWER((1 + {daily_rate}), {days_elapsed}) - 1), 0)"

    else:
        # Default to simple interest for unknown types
        years_elapsed = f"({days_elapsed} / 365)"
        return f"=IFERROR({principal_ref} * {interest_rate_ref} * {years_elapsed}, 0)"
