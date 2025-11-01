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
    holder_ownership_pct_ref: str,
    new_round_shares_ref: str
) -> str:
    """
    Create pro rata shares calculation formula.
    
    PRO RATA RIGHTS:
    - Right to maintain ownership percentage in future rounds
    - Formula: Shares = Holder Ownership % × New Round Shares / (1 - Holder Ownership %)
    
    Mathematical Formula:
        Shares = holder% × new_round_shares / (1 - holder%)
    
    Excel Formula:
        =IFERROR(holder_ownership% × new_round_shares / (1 - holder_ownership%), 0)
    
    Example:
        Holder owns 20% (0.20) of company pre-round
        New round issues 2M shares
        Pro rata shares: 0.20 × 2M / (1 - 0.20) = 0.20 × 2M / 0.80 = 500,000 shares
        This maintains their 20% ownership post-round
    
    Args:
        holder_ownership_pct_ref: Reference to holder's ownership percentage (as decimal, e.g., 0.20 for 20%)
        new_round_shares_ref: Reference to total new shares issued in the round
        
    Returns:
        Excel formula string
    """
    numerator = f"{holder_ownership_pct_ref} * {new_round_shares_ref}"
    denominator = f"(1 - {holder_ownership_pct_ref})"
    return f"=IFERROR({numerator} / {denominator}, 0)"


def create_super_pro_rata_shares_formula(
    target_ownership_pct_ref: str,
    pre_round_shares_ref: str,
    holder_current_shares_ref: str
) -> str:
    """
    Create super pro rata shares calculation formula.
    
    SUPER PRO RATA RIGHTS:
    - Right to purchase shares to achieve a target ownership percentage (higher than current pro rata)
    - Formula: Shares needed = (Target % × PreRoundShares) / (1 - Target %) - Holder Current Shares
    
    Mathematical Formula:
        target_shares_post_round = target_ownership% × pre_round_shares / (1 - target_ownership%)
        shares_to_purchase = target_shares_post_round - holder_current_shares
    
    Excel Formula:
        =IFERROR((target_ownership% × pre_round_shares / (1 - target_ownership%)) - holder_current_shares, 0)
    
    Example:
        Holder owns 15% (0.15) of company pre-round (1.5M shares out of 10M)
        Target ownership: 25% (0.25)
        Pre-round shares: 10M
        Target shares post-round: 0.25 × 10M / (1 - 0.25) = 2.5M / 0.75 = 3.33M shares
        Shares to purchase: 3.33M - 1.5M = 1.83M shares
    
    Args:
        target_ownership_pct_ref: Reference to target ownership percentage (as decimal, e.g., 0.25 for 25%)
        pre_round_shares_ref: Reference to total shares outstanding before round
        holder_current_shares_ref: Reference to holder's current shares before the round
        
    Returns:
        Excel formula string (returns max of 0 or calculated shares)
    """
    target_shares = f"({target_ownership_pct_ref} * {pre_round_shares_ref} / (1 - {target_ownership_pct_ref}))"
    shares_to_purchase = f"({target_shares} - {holder_current_shares_ref})"
    return f"=IFERROR(MAX(0, {shares_to_purchase}), 0)"

