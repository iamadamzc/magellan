"""
Options Utilities Module

Helper functions for options symbol formatting, date calculations, and common operations.
"""

from datetime import datetime, date
from typing import Tuple, Optional
import pandas as pd


def build_option_symbol(ticker: str, expiry_date: datetime | date | str, option_type: str, strike: float) -> str:
    """
    Build Alpaca options symbol from components.

    Format: TICKER + YYMMDD + C/P + STRIKE (8 digits, padded)
    Example: SPY260117C00590000 = SPY Jan 17, 2026 $590 Call

    Args:
        ticker: Underlying symbol (e.g., 'SPY')
        expiry_date: Expiration date (datetime, date, or 'YYYY-MM-DD' string)
        option_type: 'call' or 'put' (or 'C'/'P')
        strike: Strike price (e.g., 590.0)

    Returns:
        Alpaca options symbol string

    Example:
        >>> build_option_symbol('SPY', '2026-01-17', 'call', 590.0)
        'SPY260117C00590000'
    """
    # Parse expiry date
    if isinstance(expiry_date, str):
        expiry_date = datetime.strptime(expiry_date, "%Y-%m-%d").date()
    elif isinstance(expiry_date, datetime):
        expiry_date = expiry_date.date()

    # Format date as YYMMDD
    yy = expiry_date.strftime("%y")
    mm = expiry_date.strftime("%m")
    dd = expiry_date.strftime("%d")

    # Normalize option type
    option_type = option_type.upper()
    if option_type in ["CALL", "C"]:
        opt_char = "C"
    elif option_type in ["PUT", "P"]:
        opt_char = "P"
    else:
        raise ValueError(f"Invalid option_type: {option_type}. Must be 'call', 'put', 'C', or 'P'")

    # Format strike price (multiply by 1000, pad to 8 digits)
    strike_int = int(strike * 1000)
    strike_padded = f"{strike_int:08d}"

    # Build symbol
    symbol = f"{ticker}{yy}{mm}{dd}{opt_char}{strike_padded}"

    return symbol


def parse_option_symbol(option_symbol: str) -> dict:
    """
    Parse Alpaca options symbol into components.

    Args:
        option_symbol: Alpaca options symbol (e.g., 'SPY260117C00590000')

    Returns:
        Dictionary with keys:
        - ticker: Underlying symbol
        - expiry_date: Expiration date (datetime.date)
        - option_type: 'call' or 'put'
        - strike: Strike price (float)

    Example:
        >>> parse_option_symbol('SPY260117C00590000')
        {
            'ticker': 'SPY',
            'expiry_date': date(2026, 1, 17),
            'option_type': 'call',
            'strike': 590.0
        }
    """
    # Options symbols have format: TICKER + YYMMDD + C/P + STRIKE (8 digits)
    # Minimum length: 3 (ticker) + 6 (date) + 1 (type) + 8 (strike) = 18
    if len(option_symbol) < 18:
        raise ValueError(f"Invalid option symbol (too short): {option_symbol}")

    # Extract strike (last 8 characters)
    strike_str = option_symbol[-8:]
    strike = int(strike_str) / 1000.0

    # Extract option type (9th character from end)
    opt_char = option_symbol[-9]
    if opt_char == "C":
        option_type = "call"
    elif opt_char == "P":
        option_type = "put"
    else:
        raise ValueError(f"Invalid option type character: {opt_char}")

    # Extract date (6 characters before option type)
    date_str = option_symbol[-15:-9]
    yy = date_str[0:2]
    mm = date_str[2:4]
    dd = date_str[4:6]

    # Parse date (assume 20xx for year)
    expiry_date = datetime.strptime(f"20{yy}-{mm}-{dd}", "%Y-%m-%d").date()

    # Extract ticker (everything before date)
    ticker = option_symbol[:-15]

    return {"ticker": ticker, "expiry_date": expiry_date, "option_type": option_type, "strike": strike}


def calculate_dte(expiry_date: datetime | date | str, reference_date: Optional[datetime | date] = None) -> int:
    """
    Calculate days to expiration (DTE).

    Args:
        expiry_date: Option expiration date
        reference_date: Reference date (default: today)

    Returns:
        Days to expiration (integer)

    Example:
        >>> calculate_dte('2026-02-20')  # Assuming today is 2026-01-15
        36
    """
    # Parse expiry date
    if isinstance(expiry_date, str):
        expiry_date = datetime.strptime(expiry_date, "%Y-%m-%d").date()
    elif isinstance(expiry_date, datetime):
        expiry_date = expiry_date.date()

    # Parse reference date (default to today)
    if reference_date is None:
        reference_date = datetime.now().date()
    elif isinstance(reference_date, str):
        reference_date = datetime.strptime(reference_date, "%Y-%m-%d").date()
    elif isinstance(reference_date, datetime):
        reference_date = reference_date.date()

    # Calculate difference
    dte = (expiry_date - reference_date).days

    return dte


def get_next_expiration(
    current_date: Optional[datetime | date] = None,
    min_dte: int = 30,
    max_dte: int = 60,
    day_of_week: int = 4,  # Friday = 4 (0=Monday, 6=Sunday)
) -> date:
    """
    Get next options expiration date within DTE range.

    Standard options expire on Fridays (day_of_week=4).

    Args:
        current_date: Reference date (default: today)
        min_dte: Minimum days to expiration
        max_dte: Maximum days to expiration
        day_of_week: Day of week for expiration (0=Mon, 4=Fri, 6=Sun)

    Returns:
        Next expiration date (datetime.date)

    Example:
        >>> get_next_expiration(min_dte=30, max_dte=60)
        date(2026, 2, 20)  # Next Friday 30-60 days out
    """
    if current_date is None:
        current_date = datetime.now().date()
    elif isinstance(current_date, datetime):
        current_date = current_date.date()

    # Start from min_dte days out
    candidate_date = current_date + pd.Timedelta(days=min_dte)

    # Find next occurrence of target day_of_week
    days_ahead = (day_of_week - candidate_date.weekday()) % 7
    if days_ahead == 0 and candidate_date == current_date:
        days_ahead = 7  # If today is the target day, get next week

    next_expiry = candidate_date + pd.Timedelta(days=days_ahead)

    # Check if within max_dte
    dte = calculate_dte(next_expiry, current_date)
    if dte > max_dte:
        # Too far out, go back one week
        next_expiry = next_expiry - pd.Timedelta(days=7)

    return next_expiry


def format_option_display(option_symbol: str) -> str:
    """
    Format option symbol for human-readable display.

    Args:
        option_symbol: Alpaca options symbol

    Returns:
        Human-readable string

    Example:
        >>> format_option_display('SPY260117C00590000')
        'SPY Jan 17, 2026 $590 Call'
    """
    parsed = parse_option_symbol(option_symbol)

    ticker = parsed["ticker"]
    expiry = parsed["expiry_date"].strftime("%b %d, %Y")
    strike = parsed["strike"]
    opt_type = parsed["option_type"].capitalize()

    return f"{ticker} {expiry} ${strike:.0f} {opt_type}"


def calculate_breakeven(strike: float, premium: float, option_type: str) -> float:
    """
    Calculate breakeven price for an option.

    Args:
        strike: Strike price
        premium: Premium paid per share
        option_type: 'call' or 'put'

    Returns:
        Breakeven stock price

    Example:
        >>> calculate_breakeven(590.0, 5.50, 'call')
        595.50  # Stock must reach $595.50 to break even
    """
    if option_type.lower() in ["call", "c"]:
        return strike + premium
    elif option_type.lower() in ["put", "p"]:
        return strike - premium
    else:
        raise ValueError(f"Invalid option_type: {option_type}")


def calculate_intrinsic_value(stock_price: float, strike: float, option_type: str) -> float:
    """
    Calculate intrinsic value of an option.

    Args:
        stock_price: Current stock price
        strike: Strike price
        option_type: 'call' or 'put'

    Returns:
        Intrinsic value (always >= 0)

    Example:
        >>> calculate_intrinsic_value(595.0, 590.0, 'call')
        5.0  # $5 in-the-money

        >>> calculate_intrinsic_value(585.0, 590.0, 'call')
        0.0  # Out-of-the-money
    """
    if option_type.lower() in ["call", "c"]:
        return max(0, stock_price - strike)
    elif option_type.lower() in ["put", "p"]:
        return max(0, strike - stock_price)
    else:
        raise ValueError(f"Invalid option_type: {option_type}")


def is_itm(stock_price: float, strike: float, option_type: str) -> bool:
    """
    Check if option is in-the-money (ITM).

    Args:
        stock_price: Current stock price
        strike: Strike price
        option_type: 'call' or 'put'

    Returns:
        True if ITM, False otherwise
    """
    return calculate_intrinsic_value(stock_price, strike, option_type) > 0


def calculate_moneyness(stock_price: float, strike: float) -> float:
    """
    Calculate moneyness (stock price / strike price).

    Moneyness interpretation:
    - > 1.0: Call is ITM, Put is OTM
    - = 1.0: ATM
    - < 1.0: Call is OTM, Put is ITM

    Args:
        stock_price: Current stock price
        strike: Strike price

    Returns:
        Moneyness ratio

    Example:
        >>> calculate_moneyness(595.0, 590.0)
        1.0085  # Slightly ITM for calls
    """
    return stock_price / strike


# Validation functions


def validate_option_symbol(option_symbol: str) -> bool:
    """
    Validate if string is a valid Alpaca options symbol.

    Args:
        option_symbol: Symbol to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        parse_option_symbol(option_symbol)
        return True
    except (ValueError, IndexError):
        return False


def validate_strike_price(strike: float) -> bool:
    """
    Validate strike price is reasonable.

    Args:
        strike: Strike price to validate

    Returns:
        True if valid, False otherwise
    """
    # Strike must be positive and reasonable (< $10,000)
    return 0 < strike < 10000.0


def validate_dte(dte: int, min_dte: int = 0, max_dte: int = 365) -> bool:
    """
    Validate DTE is within acceptable range.

    Args:
        dte: Days to expiration
        min_dte: Minimum acceptable DTE
        max_dte: Maximum acceptable DTE

    Returns:
        True if valid, False otherwise
    """
    return min_dte <= dte <= max_dte
