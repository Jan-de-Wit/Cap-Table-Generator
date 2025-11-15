"""
Valuation Formula Generator

Formulas for calculating shares, valuations, and conversion prices.
"""


def create_safe_conversion_price_formula(round_pps_ref: str, discount_rate_ref: str,
                                         price_cap_ref: str, shares_preround_ref: str) -> str:
    """
    Create SAFE/convertible note conversion price formula.

    Uses the best (maximum) of two conversion prices:
    1. Discounted price: Price per Share * (1 - discount%)
    2. Cap price: Valuation Cap / Total # shares

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
    return f"=MAX({discounted_price}, {cap_price})"


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


def create_convertible_shares_formula(conversion_amount_ref: str,
                                      discount_rate_ref: str, round_pps_ref: str = None,
                                      valuation_cap_ref: str = None, total_shares_ref: str = None,
                                      valuation_basis: str = None, post_money_ref: str = None,
                                      is_safe: bool = False,
                                      future_round_pps_ref: str = None,
                                      future_round_pre_investment_cap_ref: str = None,
                                      total_conversion_amount_ref: str = None,
                                      per_instrument_cap_ref: str = None,
                                      per_instrument_cap_type_ref: str = None) -> str:
    """
    Calculate shares from convertible instrument (SAFE or convertible note).

    CONVERTIBLE CALCULATION:
    Uses the best (maximum shares = minimum price) of two methods:

    Method 1 (when future_round_pps_ref is provided):
        Price per share = (Pre-investment Valuation Cap - Total Conversion Amount) / Total Shares Pre-conversion
        Conversion price = Price per share * (1 - discount%)
        Shares = Conversion amount / Conversion price

    Method 2 (valuation cap method):
        Price per share = Pre-investment Valuation Cap / Total Shares Pre-conversion
        Shares = Conversion amount / Price per share

        Where Pre-investment Valuation Cap:
        - If per_instrument_cap_ref is provided and not empty:
          - If cap_type is 'pre_conversion': use cap directly
          - If cap_type is 'post_conversion_own': subtract only own conversion amount
          - If cap_type is 'post_conversion_total': subtract round's total conversion amount
        - Otherwise, use round-level cap:
          - If post_money basis: Post-investment Valuation - Conversion Amount
          - If pre_money basis: Pre-investment Valuation (directly from valuation_cap_ref)

    Args:
        conversion_amount_ref: Reference to conversion amount (Principal + Interest, or just Principal for SAFE)
        discount_rate_ref: Reference to discount rate (as decimal)
        round_pps_ref: Reference to current round price per share (used for Method 2 fallback)
        valuation_cap_ref: Reference to round-level pre-investment valuation cap (fallback)
        total_shares_ref: Reference to total shares (pre-round shares)
        valuation_basis: Basis for valuation ('pre_money' or 'post_money')
        post_money_ref: Reference to post-investment valuation (used when valuation_basis is 'post_money')
        is_safe: If True, this is a SAFE (no interest). If False, this is a convertible note.
        future_round_pps_ref: Optional reference to future valuation-based round's price per share
        future_round_pre_investment_cap_ref: Optional reference to future round's pre-investment valuation cap
        total_conversion_amount_ref: Optional reference to total conversion amount (for Method 1 calculation)
        per_instrument_cap_ref: Optional reference to per-instrument valuation cap cell
        per_instrument_cap_type_ref: Optional reference to per-instrument valuation cap type cell

    Returns:
        Excel formula string
    """
    # Validate required parameters
    if valuation_cap_ref is None:
        raise ValueError(
            "valuation_cap_ref is required for convertible shares calculation")
    if total_shares_ref is None:
        raise ValueError(
            "total_shares_ref is required for convertible shares calculation")
    if valuation_basis is None:
        raise ValueError(
            "valuation_basis is required for convertible shares calculation")

    # Method 1: Using future round's price per share with discount
    # This method requires a future valuation-based round reference
    # We need the pre-investment cap and total conversion amount to calculate the adjusted price per share
    if future_round_pre_investment_cap_ref and total_conversion_amount_ref:
        # The price per share is calculated from the pre-investment valuation cap minus total conversion amount
        # Price per share = (Pre-investment Valuation Cap - Total Conversion Amount) / Total Shares Pre-conversion
        # Note: We use the future round's pre-investment cap, but adjust it by subtracting total conversion
        adjusted_price_per_share = f"(({future_round_pre_investment_cap_ref} - {total_conversion_amount_ref}) / {total_shares_ref})"
        # Apply discount to get conversion price
        method1_conversion_price = f"({adjusted_price_per_share} * (1 - {discount_rate_ref}))"
        # Calculate shares: Conversion amount / Conversion price
        method1_shares = f"({conversion_amount_ref} / {method1_conversion_price})"
    else:
        method1_shares = None

    # Method 2: Using valuation cap from current round
    # Calculate pre-investment valuation cap
    # First, determine if we should use per-instrument cap or round-level cap
    if per_instrument_cap_ref and per_instrument_cap_type_ref:
        # Use per-instrument cap if provided (not empty)
        # Check if per_instrument_cap_ref is not empty using IF and ISBLANK
        # Build the effective cap based on cap type
        # For pre_conversion: use cap directly
        # For post_conversion_own: subtract own conversion amount
        # For post_conversion_total: subtract total conversion amount (need to get this reference)
        # We'll need to pass total_conversion_amount_ref for post_conversion_total case

        # Build effective cap formula based on type
        # IF(ISBLANK(per_instrument_cap_ref), use round-level, use per-instrument logic)
        # For per-instrument:
        #   IF(cap_type = "pre_conversion", cap,
        #      IF(cap_type = "post_conversion_own", cap - own_conversion,
        #         IF(cap_type = "post_conversion_total", cap - total_conversion, round-level)))

        # Get total conversion amount reference for post_conversion_total case
        # We need to pass this from rounds_sheet, but for now we'll construct it
        # Actually, we can use the round-level calculation as fallback

        # Build the effective cap calculation
        # First check if per-instrument cap is provided (not blank and not zero)
        # Calculate round-level cap for fallback/default
        if valuation_basis == 'post_money' and post_money_ref:
            round_level_cap = f"({post_money_ref} - {conversion_amount_ref})"
        else:
            round_level_cap = valuation_cap_ref

        # Build per-instrument cap calculations
        pre_conversion_cap = per_instrument_cap_ref
        post_conversion_own_cap = f"({per_instrument_cap_ref} - {conversion_amount_ref})"
        # For post_conversion_total, we need total_conversion_amount_ref
        # If not provided, fall back to using own conversion amount (same as post_conversion_own)
        if total_conversion_amount_ref:
            post_conversion_total_cap = f"({per_instrument_cap_ref} - {total_conversion_amount_ref})"
        else:
            # Fallback: use own conversion amount (same as post_conversion_own)
            post_conversion_total_cap = post_conversion_own_cap

        # Build the effective cap formula
        # Check if per-instrument cap is provided (not blank and not zero) AND cap type is not "default"
        # Check for both original format and human-friendly format
        # IF(OR(ISBLANK(per_instrument_cap_ref), per_instrument_cap_ref=0, OR(per_instrument_cap_type_ref="default", per_instrument_cap_type_ref="Default")), round-level,
        #    IF(OR(per_instrument_cap_type_ref = "pre_conversion", per_instrument_cap_type_ref = "Pre-conversion"), pre_conversion_cap,
        #       IF(OR(per_instrument_cap_type_ref = "post_conversion_own", per_instrument_cap_type_ref = "Post-conversion (own investment)"), post_conversion_own_cap,
        #          IF(per_instrument_cap_type_ref = "post_conversion_total", per_instrument_cap_type_ref = "Post-conversion (total investment)", post_conversion_total_cap))))
        effective_cap = f"IF(OR(ISBLANK({per_instrument_cap_ref}), {per_instrument_cap_ref}=0, OR({per_instrument_cap_type_ref}=\"default\", {per_instrument_cap_type_ref}=\"Default\")), {round_level_cap}, IF(OR({per_instrument_cap_type_ref}=\"pre_conversion\", {per_instrument_cap_type_ref}=\"Pre-conversion\"), {pre_conversion_cap}, IF(OR({per_instrument_cap_type_ref}=\"post_conversion_own\", {per_instrument_cap_type_ref}=\"Post-conversion (own investment)\"), {post_conversion_own_cap}, IF(OR({per_instrument_cap_type_ref}=\"post_conversion_total\", {per_instrument_cap_type_ref}=\"Post-conversion (total investment)\"), {post_conversion_total_cap}, {round_level_cap}))))"
    else:
        # Use round-level cap (existing logic)
        if valuation_basis == 'post_money' and post_money_ref:
            # For post_money: calculate pre-investment by subtracting conversion amount
            # Pre-investment = Post-investment - Conversion Amount
            effective_cap = f"({post_money_ref} - {conversion_amount_ref})"
        else:
            # For pre_money: use valuation cap directly (it's already pre-investment)
            effective_cap = valuation_cap_ref

    # Price per share from valuation cap
    method2_price_per_share = f"({effective_cap} / {total_shares_ref})"
    method2_shares = f"({conversion_amount_ref} / {method2_price_per_share})"

    # Return the maximum (best for investor) of the two methods
    if method1_shares:
        return f"=IFERROR(MAX({method1_shares}, {method2_shares}), 0)"
    else:
        return f"=IFERROR({method2_shares}, 0)"
