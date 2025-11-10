"""
Valuation Formula Generator

Formulas for calculating shares, valuations, and conversion prices.
"""


def create_safe_conversion_price_formula(round_pps_ref: str, discount_rate_ref: str,
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


def create_safe_conversion_shares_formula(investment_ref: str, conversion_price_ref: str) -> str:
    """Create SAFE conversion shares formula."""
    return f"=IFERROR({investment_ref} / {conversion_price_ref}, 0)"


def create_shares_from_investment_premoney_formula(investment_ref: str,
                                                   pre_money_val_ref: str,
                                                   pre_round_shares_ref: str) -> str:
    """
    Calculate shares issued from investment using PRE-MONEY valuation.

    PRE-MONEY VALUATION APPROACH:
    - Investment is added ON TOP of pre-money valuation
    - Post-money = Pre-money + Investment + Interest

    Mathematical Formula:
        Shares = (Investment + Interest) * Pre-Round-Shares / PreMoney

    Excel Formula:
        =IFERROR((Investment + Interest) * PreRoundShares / PreMoney, 0)

    Example:
        Pre-round shares: 10M
        Investment: $10M
        Pre-money: $40M
        Post-money: $50M
        Shares: $10M * 10M / $50M = 2M shares (20% ownership)

    Args:
        investment_ref: Reference to investment amount
        pre_money_val_ref: Reference to pre-money valuation (from Rounds sheet column E)
        pre_round_shares_ref: Reference to shares outstanding before round

    Returns:
        Excel formula string
    """
    # Shares = Investment * PreRoundShares / PreMoney
    return f"=IFERROR({investment_ref} * {pre_round_shares_ref} / {pre_money_val_ref}, 0)"


def create_shares_from_investment_postmoney_formula(investment_ref: str,
                                                    post_money_val_ref: str,
                                                    pre_round_shares_ref: str) -> str:
    """
    Calculate shares issued from investment using POST-MONEY valuation.

    POST-MONEY VALUATION APPROACH:
    - Investment is INCLUDED in the post-money valuation
    - Pre-money = Post-money - Investment - Interest
    - Ownership percentage is FIXED: (Investment + Interest) / Post-Money

    Mathematical Formula:
        ownership% = (Investment + Interest) / Post-Money
        Shares = PreRoundShares * ownership% / (1 - ownership%)

    Excel Formula:
        =IFERROR(PreRoundShares * ((Investment + Interest) / PostMoney), 0)

    Example:
        Pre-round shares: 10M
        Investment: $10M
        Post-money: $50M
        Ownership%: $10M / $50M = 20%
        Shares: 10M * 0.20 / (1 - 0.20) = 10M * 0.20 / 0.80 = 2.5M shares (20% ownership, FIXED)

    Args:
        investment_ref: Reference to investment amount
        post_money_val_ref: Reference to post-money valuation (from Rounds sheet column E)
        pre_round_shares_ref: Reference to shares outstanding before round

    Returns:
        Excel formula string
    """
    ownership_pct = f"({investment_ref} / {post_money_val_ref})"
    # Shares = PreRoundShares * ownership% / (1 - ownership%)
    numerator = f"{pre_round_shares_ref} * {ownership_pct}"
    return f"=IFERROR({numerator}, 0)"


def create_price_per_share_from_valuation_formula(valuation_ref: str,
                                                  shares_outstanding_ref: str) -> str:
    """
    Calculate price per share from valuation.

    Args:
        valuation_ref: Reference to valuation (pre or post money)
        shares_outstanding_ref: Reference to shares outstanding

    Returns:
        Excel formula string
    """
    return f"=IFERROR({valuation_ref} / {shares_outstanding_ref}, 0)"


def create_post_money_from_pre_money_formula(pre_money_ref: str,
                                             investment_ref: str,
                                             ) -> str:
    """
    Calculate post-money valuation from pre-money valuation and investment.

    Args:
        pre_money_ref: Reference to pre-money valuation
        investment_ref: Reference to investment amount

    Returns:
        Excel formula string
    """
    return f"={pre_money_ref} + {investment_ref}"


def create_pre_money_from_post_money_formula(post_money_ref: str,
                                             investment_ref: str) -> str:
    """
    Calculate pre-money valuation from post-money valuation and investment.

    Args:
        post_money_ref: Reference to post-money valuation
        investment_ref: Reference to investment amount

    Returns:
        Excel formula string
    """
    return f"={post_money_ref} - {investment_ref}"


def create_shares_from_percentage_formula(percentage_ownership_ref: str,
                                          pre_round_shares_ref: str,
                                          holder_current_shares_ref: str = "0") -> str:
    """
    Calculate shares issued from ownership percentage, subtracting existing shares.

    PERCENTAGE-BASED CALCULATION:
    - Investor gets a fixed percentage of the company after the round
    - Formula: New Shares = (p × PreRoundShares - CurrentShares) / (1 - p)
    - Where: (CurrentShares + NewShares) / (PreRoundShares + NewShares) = p

    Mathematical derivation:
        (C + N) / (P + N) = p
        C + N = p × (P + N)
        C + N = p×P + p×N
        C = p×P + p×N - N
        C = p×P + N×(p - 1)
        C - p×P = N×(p - 1)
        N = (C - p×P) / (p - 1)
        N = (p×P - C) / (1 - p)

    Excel Formula:
        =IFERROR(MAX(0, (Ownership% × PreRoundShares - HolderCurrentShares) / (1 - Ownership%)), 0)

    Example:
        Pre-round shares: 10M
        Holder current shares: 0.5M
        Ownership target: 20%
        New shares: (0.20 × 10M - 0.5M) / (1 - 0.20) = (2M - 0.5M) / 0.80 = 1.875M
        After round: (0.5M + 1.875M) / (10M + 1.875M) = 2.375M / 11.875M = 20% ✓

    Args:
        percentage_ownership_ref: Reference to ownership percentage (as decimal, e.g., 0.20 for 20%)
        pre_round_shares_ref: Reference to shares outstanding before round
        holder_current_shares_ref: Reference to holder's current shares before this round (default: "0")

    Returns:
        Excel formula string
    """
    # Formula: N = (p × P - C) / (1 - p)
    numerator = f"({percentage_ownership_ref} * {pre_round_shares_ref} - {holder_current_shares_ref})"
    denominator = f"(1 - {percentage_ownership_ref})"
    new_shares = f"({numerator} / {denominator})"
    return f"=IFERROR(MAX(0, {new_shares}), 0)"


def create_convertible_shares_formula(investment_ref: str, interest_ref: str,
                                      discount_rate_ref: str, round_pps_ref: str) -> str:
    """
    Calculate shares from convertible instrument (SAFE or convertible note).

    CONVERTIBLE CALCULATION:
    - Uses the lower of: discounted price or full price per share
    - Conversion price = MIN(round_pps * (1 - discount), round_pps)
    - Shares = (investment + interest) / conversion_price

    Note: When valuation_cap_basis is used, price_per_share is calculated separately
    based on the basis (pre_money, post_money, or fixed). This formula uses that
    price_per_share directly.

    Args:
        investment_ref: Reference to investment amount
        interest_ref: Reference to accrued interest
        discount_rate_ref: Reference to discount rate (as decimal)
        round_pps_ref: Reference to round price per share (already calculated based on basis)

    Returns:
        Excel formula string
    """
    discounted_price = f"({round_pps_ref} * (1 - {discount_rate_ref}))"
    # Conversion price is the lower of discounted price or full price
    # Since discount is typically positive, this is usually just the discounted price
    conversion_price = f"MIN({discounted_price}, {round_pps_ref})"

    return f"=IFERROR(({investment_ref} + {interest_ref}) / {conversion_price}, 0)"
