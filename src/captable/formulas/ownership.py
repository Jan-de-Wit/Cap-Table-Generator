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
    new_round_shares_ref: str,
    sum_pro_rata_pct_ref: str = "0"
) -> str:
    """
    Create pro rata shares calculation formula.
    
    PRO RATA RIGHTS:
    - Right to maintain ownership percentage in future rounds
    - Formula: Shares = Holder Ownership % × New Round Shares × (1 + Sum(Pro Rata %)) / (1 - Holder Ownership %)
    
    Mathematical Formula:
        Shares = holder% × new_round_shares × (1 + sum_pro_rata_pct) / (1 - holder%)
    
    Excel Formula:
        =IFERROR(holder_ownership% × new_round_shares × (1 + sum_pro_rata_pct) / (1 - holder_ownership%), 0)
    
    Example:
        Holder owns 20% (0.20) of company pre-round
        New round issues 2M shares
        Sum of pro rata % in round: 0.15 (15% from other holders exercising pro rata)
        Pro rata shares: 0.20 × 2M × (1 + 0.15) / (1 - 0.20) = 0.20 × 2.3M / 0.80 = 575,000 shares
        This accounts for dilution from other pro rata allocations
    
    Args:
        holder_ownership_pct_ref: Reference to holder's ownership percentage (as decimal, e.g., 0.20 for 20%)
        new_round_shares_ref: Reference to total new shares issued in the round
        sum_pro_rata_pct_ref: Reference to sum of all pro rata percentages in this round (default: "0")
        
    Returns:
        Excel formula string
    """
    # Correct simultaneous allocation solution:
    # For participants with pro rata percentages p_i, base new shares B, total additional shares X satisfy:
    #   X = (sum p_i) * (B + X)  =>  X = (sum p_i * B) / (1 - sum p_i)
    # Individual allocation for holder i: x_i = p_i * B / (1 - sum p_i)
    numerator = f"{holder_ownership_pct_ref} * {new_round_shares_ref}"
    inv_denominator = f"IFERROR(1 / (1 - {sum_pro_rata_pct_ref}), 0)"
    return f"=IFERROR({numerator} * {inv_denominator}, 0)"


def create_super_pro_rata_shares_formula(
    target_ownership_pct_ref: str,
    pre_round_shares_ref: str,
    shares_issued_ref: str,
    holder_current_shares_ref: str,
    sum_standard_pro_rata_pct_ref: str = "0",
    sum_super_target_pct_ref: str = "0",
    sum_super_current_shares_ref: str = "0"
) -> str:
    """
    Create super pro rata shares calculation formula.
    
    SUPER PRO RATA RIGHTS:
    - Right to purchase shares to achieve a target ownership percentage (higher than current pro rata)
    - Formula: Shares needed = (Target % × (PreRoundShares + SharesIssued) × (1 + Sum(Pro Rata %))) / (1 - Target %) - Holder Current Shares
    
    Mathematical Formula:
        base_post_round_shares = pre_round_shares + shares_issued
        post_round_shares = base_post_round_shares × (1 + sum_pro_rata_pct)
        target_shares_post_round = target_ownership% × post_round_shares / (1 - target_ownership%)
        shares_to_purchase = target_shares_post_round - holder_current_shares
    
    Excel Formula:
        =IFERROR((target_ownership% × (pre_round_shares + shares_issued) × (1 + sum_pro_rata_pct) / (1 - target_ownership%)) - holder_current_shares, 0)
    
    Example:
        Holder owns 15% (0.15) of company pre-round (1.5M shares out of 10M)
        Target ownership: 25% (0.25)
        Pre-round shares: 10M
        Shares issued in round: 2M
        Sum of pro rata % in round: 0.30 (30% from other holders exercising pro rata)
        Base post-round shares: 12M
        Adjusted post-round shares: 12M × (1 + 0.30) = 15.6M
        Target shares post-round: 0.25 × 15.6M / (1 - 0.25) = 3.9M / 0.75 = 5.2M shares
        Shares to purchase: 5.2M - 1.5M = 3.7M shares
    
    Args:
        target_ownership_pct_ref: Reference to target ownership percentage (as decimal, e.g., 0.25 for 25%)
        pre_round_shares_ref: Reference to total shares outstanding before round
        shares_issued_ref: Reference to total shares issued in this round (base shares only)
        holder_current_shares_ref: Reference to holder's current shares before the round
        sum_pro_rata_pct_ref: Reference to sum of all pro rata percentages in this round (default: "0")
        
    Returns:
        Excel formula string (returns max of 0 or calculated shares)
    """
    # Super pro rata (multiple supers) simultaneous solution:
    # B = pre_round_shares + shares_issued
    # X_std = (sum_standard * B) / (1 - sum_standard)
    # T_after_standard = B + X_std
    # Let S = sum targets of supers; C = sum current shares of supers (pre-round)
    # Final total T = (T_after_standard - C) / (1 - S)
    # For investor i: x_i = max(0, t_i * T - current_i)
    base_post_round_shares = f"({pre_round_shares_ref} + {shares_issued_ref})"
    standard_extra_shares = f"(({sum_standard_pro_rata_pct_ref} * {base_post_round_shares}) * IFERROR(1 / (1 - {sum_standard_pro_rata_pct_ref}), 0))"
    post_after_standard_shares = f"({base_post_round_shares} + {standard_extra_shares})"
    final_total_shares = f"(({post_after_standard_shares} - {sum_super_current_shares_ref}) * IFERROR(1 / (1 - {sum_super_target_pct_ref}), 0))"
    target_shares = f"({target_ownership_pct_ref} * {final_total_shares})"
    shares_to_purchase = f"({target_shares} - {holder_current_shares_ref})"
    return f"=IFERROR(MAX(0, {shares_to_purchase}), 0)"


def create_unified_pro_rata_shares_formula(
    participant_target_pct_ref: str,
    pre_round_shares_ref: str,
    shares_issued_ref: str,
    holder_current_shares_ref: str,
    sum_standard_target_pct_ref: str = "0",
    sum_super_target_pct_ref: str = "0",
    sum_standard_current_shares_ref: str = "0",
    sum_super_current_shares_ref: str = "0"
) -> str:
    """
    Create a unified pro rata shares calculation formula (standard and super simultaneous solution).

    This solves for final total shares T such that:
      - For each standard participant i: final_i / T = r_i (their pre-round ownership)
      - For each super participant j: final_j / T = t_j (their specified target)

    Let:
      P = pre_round_shares
      B = shares_issued (base round shares before pro rata)
      R = sum of standard target percentages (equals sum of pre-round ownerships of standards)
      S = sum of super target percentages
      C_R = sum of current shares (pre-round) of standards
      C_S = sum of current shares (pre-round) of supers

    Then the final total shares are:
      T = (P + B - C_R - C_S) / (1 - R - S)

    And the additional shares for a participant k with target p_k (either r_i or t_j) are:
      x_k = max(0, p_k * T - current_k)

    Args:
        participant_target_pct_ref: Cell ref of participant's target percentage (standard: pre-round ownership, super: target)
        pre_round_shares_ref: Named/cell ref to pre-round shares P
        shares_issued_ref: Cell ref to base new shares B
        holder_current_shares_ref: Cell ref to participant's current shares before this round
        sum_standard_target_pct_ref: Ref to sum of standard targets R
        sum_super_target_pct_ref: Ref to sum of super targets S
        sum_standard_current_shares_ref: Ref to sum of current shares of standards C_R
        sum_super_current_shares_ref: Ref to sum of current shares of supers C_S

    Returns:
        Excel formula string computing shares to purchase for the participant
    """
    # Cap total target sum at just under 1 and scale individual targets proportionally when needed
    total_target_sum = f"({sum_standard_target_pct_ref} + {sum_super_target_pct_ref})"
    safe_total_sum = f"MIN({total_target_sum}, 0.999999)"
    scale_factor = f"IF({total_target_sum}>1, {safe_total_sum} / {total_target_sum}, 1)"

    # Effective sums and participant target after scaling
    eff_sum_targets = f"(({sum_standard_target_pct_ref} + {sum_super_target_pct_ref}) * {scale_factor})"
    eff_participant_target = f"({participant_target_pct_ref} * {scale_factor})"

    numerator_T = f"({pre_round_shares_ref} + {shares_issued_ref} - {sum_standard_current_shares_ref} - {sum_super_current_shares_ref})"
    denom_T = f"(1 - {eff_sum_targets})"
    total_T = f"({numerator_T} * IFERROR(1 / {denom_T}, 0))"
    target_shares = f"({eff_participant_target} * {total_T})"
    shares_to_purchase = f"({target_shares} - {holder_current_shares_ref})"
    return f"=IFERROR(MAX(0, {shares_to_purchase}), 0)"

