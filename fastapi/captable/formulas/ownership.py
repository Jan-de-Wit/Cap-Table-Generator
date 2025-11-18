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


def create_pro_rata_shares_formula(
    participant_target_pct_ref: str,
    pre_round_shares_ref: str,
    shares_issued_ref: str,
    holder_current_shares_ref: str,
    sum_pro_rata_pct_ref: str = "0",
    sum_current_shares_ref: str = "0",
) -> str:
    """
    Create a Pro-rata Shares calculation formula without LET for simplicity.

    This solves for final total shares T such that:
      - For each participant i: final_i / T = p_i (their target percentage)

    Variables:
      P = pre_round_shares
      B = shares_issued (base round shares before pro rata)
      R = sum of pro rata percentages
      C = sum of current shares (pre-round)

    Then the final total shares are:
      T = (P + B - C) / (1 - R)

    And the additional shares for a participant k with target p_k are:
      x_k = max(0, p_k * T - current_k)

    Args:
        participant_target_pct_ref: Cell ref of participant's target percentage (standard: pre-round ownership, super: target)
        pre_round_shares_ref: Named/cell ref to pre-round shares P
        shares_issued_ref: Cell ref to base new shares B
        holder_current_shares_ref: Cell ref to participant's current shares before this round
        sum_pro_rata_pct_ref: Ref to sum of pro rata percentages R
        sum_current_shares_ref: Ref to sum of current shares C

    Returns:
        Excel formula string computing shares to purchase for the participant
    """
    # Calculate numerator: (pre_round_shares + shares_issued - sum_current_shares)
    numerator = f"({pre_round_shares_ref} + {shares_issued_ref} - {sum_current_shares_ref})"
    
    # Calculate denominator: (1 - sum_pro_rata_pct)
    denominator = f"(1 - {sum_pro_rata_pct_ref})"
    
    # Calculate total shares after pro rata: numerator / denominator
    # Formula: T = (P + B - C) / (1 - R)
    total_shares = f"IFERROR({numerator} / {denominator}, 0)"
    
    # Calculate target shares for this participant: target_pct * total_shares
    # Formula: targetShares = p_k * T
    target_shares = f"({participant_target_pct_ref} * {total_shares})"
    
    # Calculate shares to purchase: target_shares - current_shares
    # Formula: sharesToPurchase = targetShares - current_k
    shares_to_purchase = f"({target_shares} - {holder_current_shares_ref})"
    
    # Final result: max(0, shares_to_purchase) to ensure non-negative
    # Formula: MAX(0, sharesToPurchase) with error handling
    result = f"IFERROR(MAX(0, {shares_to_purchase}), 0)"
    
    # Format formula with line breaks and indentation for readability
    # Excel will accept formulas with whitespace/newlines
    formula = (
        f"={result}"
    )
    
    return formula
