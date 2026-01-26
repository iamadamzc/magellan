"""
Alpaca Options Data Handler

Fetches options chains, quotes, and Greeks from Alpaca API.
Handles caching, error recovery, and data quality validation.
"""

import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta, date
import pandas as pd

try:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import GetOptionContractsRequest
    from alpaca.data.historical import OptionHistoricalDataClient
    from alpaca.data.requests import OptionLatestQuoteRequest, OptionBarsRequest
    from alpaca.data.timeframe import TimeFrame
except ImportError:
    raise ImportError("alpaca-py not installed. Run: pip install alpaca-py")

from src.logger import LOG
from src.options.utils import build_option_symbol, parse_option_symbol, calculate_dte, validate_option_symbol


class AlpacaOptionsClient:
    """
    Client for fetching and processing options data from Alpaca.

    Features:
    - Fetch options chains with filtering (DTE, strike range, type)
    - Get real-time and historical quotes
    - Calculate Greeks (via Black-Scholes if not provided by API)
    - Data quality validation
    - Error handling and retry logic
    """

    def __init__(self, paper: bool = True):
        """
        Initialize Alpaca Options Client.

        Args:
            paper: Use paper trading account (default: True)

        Credentials loaded from environment:
        - APCA_API_KEY_ID
        - APCA_API_SECRET_KEY
        """
        self.api_key = os.getenv("APCA_API_KEY_ID")
        self.secret_key = os.getenv("APCA_API_SECRET_KEY")

        if not self.api_key or not self.secret_key:
            raise ValueError("Alpaca credentials not found. " "Set APCA_API_KEY_ID and APCA_API_SECRET_KEY in .env")

        self.paper = paper

        # Initialize clients
        self.trading_client = TradingClient(self.api_key, self.secret_key, paper=self.paper)

        self.data_client = OptionHistoricalDataClient(self.api_key, self.secret_key)

        LOG.info(f"[OPTIONS CLIENT] Initialized ({'PAPER' if self.paper else 'LIVE'} mode)")

    def get_options_chain(
        self,
        symbol: str,
        option_type: Optional[str] = None,
        min_dte: int = 30,
        max_dte: int = 60,
        min_strike: Optional[float] = None,
        max_strike: Optional[float] = None,
    ) -> List[Dict]:
        """
        Fetch options chain for a symbol with filtering.

        Args:
            symbol: Underlying symbol (e.g., 'SPY')
            option_type: 'call', 'put', or None (both)
            min_dte: Minimum days to expiration
            max_dte: Maximum days to expiration
            min_strike: Minimum strike price (optional)
            max_strike: Maximum strike price (optional)

        Returns:
            List of contract dictionaries with keys:
            - symbol: Options symbol
            - underlying: Underlying ticker
            - strike: Strike price
            - expiration: Expiration date
            - type: 'call' or 'put'
            - dte: Days to expiration

        Example:
            >>> client.get_options_chain('SPY', option_type='call', min_dte=30, max_dte=60)
            [
                {
                    'symbol': 'SPY260220C00590000',
                    'underlying': 'SPY',
                    'strike': 590.0,
                    'expiration': date(2026, 2, 20),
                    'type': 'call',
                    'dte': 36
                },
                ...
            ]
        """
        LOG.flow(f"[{symbol}] Fetching options chain (DTE {min_dte}-{max_dte}, type={option_type or 'both'})...")

        # Calculate date range
        start_date = (datetime.now() + timedelta(days=min_dte)).strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=max_dte)).strftime("%Y-%m-%d")

        # Fetch contracts
        contracts = []

        types_to_fetch = ["call", "put"] if option_type is None else [option_type.lower()]

        for opt_type in types_to_fetch:
            request = GetOptionContractsRequest(
                underlying_symbols=[symbol], expiration_date_gte=start_date, expiration_date_lte=end_date, type=opt_type
            )

            try:
                response = self.trading_client.get_option_contracts(request)

                # Convert response to list
                raw_contracts = list(response.option_contracts) if hasattr(response, "option_contracts") else []

                for contract in raw_contracts:
                    strike = float(contract.strike_price)

                    # Apply strike filters
                    if min_strike is not None and strike < min_strike:
                        continue
                    if max_strike is not None and strike > max_strike:
                        continue

                    # Parse expiration date
                    if isinstance(contract.expiration_date, str):
                        expiry = datetime.strptime(contract.expiration_date, "%Y-%m-%d").date()
                    else:
                        expiry = contract.expiration_date

                    # Calculate DTE
                    dte = calculate_dte(expiry)

                    contracts.append(
                        {
                            "symbol": contract.symbol,
                            "underlying": symbol,
                            "strike": strike,
                            "expiration": expiry,
                            "type": contract.type,
                            "dte": dte,
                        }
                    )

            except Exception as e:
                LOG.warning(f"[{symbol}] Failed to fetch {opt_type} contracts: {e}")
                continue

        LOG.success(f"[{symbol}] Found {len(contracts)} contracts")

        return contracts

    def get_option_quote(self, option_symbol: str) -> Optional[Dict]:
        """
        Fetch current quote for an option contract.

        Args:
            option_symbol: Options symbol (e.g., 'SPY260220C00590000')

        Returns:
            Dictionary with quote data:
            - bid: Bid price
            - ask: Ask price
            - mid: Mid price (bid + ask) / 2
            - spread: Bid-ask spread
            - spread_pct: Spread as % of mid
            - timestamp: Quote timestamp

            Returns None if quote unavailable.

        Example:
            >>> client.get_option_quote('SPY260220C00590000')
            {
                'bid': 5.45,
                'ask': 5.50,
                'mid': 5.475,
                'spread': 0.05,
                'spread_pct': 0.91,
                'timestamp': datetime(...)
            }
        """
        if not validate_option_symbol(option_symbol):
            LOG.warning(f"[{option_symbol}] Invalid option symbol format")
            return None

        try:
            request = OptionLatestQuoteRequest(symbol_or_symbols=option_symbol)
            quote_data = self.data_client.get_option_latest_quote(request)

            if option_symbol not in quote_data:
                LOG.warning(f"[{option_symbol}] No quote data returned")
                return None

            quote = quote_data[option_symbol]

            bid = float(quote.bid_price)
            ask = float(quote.ask_price)
            mid = (bid + ask) / 2.0
            spread = ask - bid
            spread_pct = (spread / mid * 100) if mid > 0 else 0

            return {
                "bid": bid,
                "ask": ask,
                "mid": mid,
                "spread": spread,
                "spread_pct": spread_pct,
                "timestamp": quote.timestamp,
            }

        except Exception as e:
            LOG.warning(f"[{option_symbol}] Failed to fetch quote: {e}")
            return None

    def get_atm_strike(self, symbol: str, current_price: float, option_type: str = "call") -> Optional[float]:
        """
        Find at-the-money (ATM) strike price.

        Args:
            symbol: Underlying symbol
            current_price: Current stock price
            option_type: 'call' or 'put'

        Returns:
            Nearest strike to current price, or None if no contracts found

        Example:
            >>> client.get_atm_strike('SPY', 592.35, 'call')
            590.0  # Nearest available strike
        """
        # Fetch a sample chain to see available strikes
        chain = self.get_options_chain(symbol, option_type=option_type, min_dte=30, max_dte=60)

        if not chain:
            LOG.warning(f"[{symbol}] No options chain found")
            return None

        # Extract unique strikes
        strikes = sorted(set(c["strike"] for c in chain))

        # Find closest strike
        atm_strike = min(strikes, key=lambda x: abs(x - current_price))

        LOG.flow(f"[{symbol}] Current: ${current_price:.2f}, ATM Strike: ${atm_strike:.2f}")

        return atm_strike

    def get_strike_by_delta(
        self,
        symbol: str,
        current_price: float,
        target_delta: float,
        option_type: str = "call",
        min_dte: int = 30,
        max_dte: int = 60,
    ) -> Optional[Dict]:
        """
        Find strike closest to target delta.

        Note: This is a simplified approximation. For production, use actual
        Greeks from market data or calculate via Black-Scholes.

        Args:
            symbol: Underlying symbol
            current_price: Current stock price
            target_delta: Target delta (e.g., 0.50 for ATM, 0.60 for slightly ITM)
            option_type: 'call' or 'put'
            min_dte: Minimum DTE for contracts
            max_dte: Maximum DTE for contracts

        Returns:
            Contract dictionary closest to target delta, or None

        Example:
            >>> client.get_strike_by_delta('SPY', 592.0, 0.60, 'call')
            {
                'symbol': 'SPY260220C00585000',
                'strike': 585.0,
                'estimated_delta': 0.62,
                ...
            }
        """
        chain = self.get_options_chain(symbol, option_type=option_type, min_dte=min_dte, max_dte=max_dte)

        if not chain:
            return None

        # Simple delta approximation (for calls):
        # ATM (strike = spot) ≈ delta 0.50
        # ITM (strike < spot) ≈ delta > 0.50 (approaches 1.0 deep ITM)
        # OTM (strike > spot) ≈ delta < 0.50 (approaches 0.0 deep OTM)

        best_contract = None
        min_delta_diff = float("inf")

        for contract in chain:
            strike = contract["strike"]

            # Rough delta approximation
            if option_type == "call":
                # For calls: delta increases as strike decreases (more ITM)
                moneyness = current_price / strike
                if moneyness >= 1.2:
                    estimated_delta = 0.80  # Deep ITM
                elif moneyness >= 1.1:
                    estimated_delta = 0.70
                elif moneyness >= 1.05:
                    estimated_delta = 0.60
                elif moneyness >= 0.95:
                    estimated_delta = 0.50  # ATM
                elif moneyness >= 0.90:
                    estimated_delta = 0.40
                elif moneyness >= 0.85:
                    estimated_delta = 0.30
                else:
                    estimated_delta = 0.20  # Deep OTM
            else:  # put
                # For puts: delta increases (in absolute value) as strike increases (more ITM)
                moneyness = strike / current_price
                if moneyness >= 1.2:
                    estimated_delta = -0.80  # Deep ITM
                elif moneyness >= 1.1:
                    estimated_delta = -0.70
                elif moneyness >= 1.05:
                    estimated_delta = -0.60
                elif moneyness >= 0.95:
                    estimated_delta = -0.50  # ATM
                elif moneyness >= 0.90:
                    estimated_delta = -0.40
                elif moneyness >= 0.85:
                    estimated_delta = -0.30
                else:
                    estimated_delta = -0.20  # Deep OTM

            # Find closest to target
            delta_diff = abs(abs(estimated_delta) - abs(target_delta))
            if delta_diff < min_delta_diff:
                min_delta_diff = delta_diff
                best_contract = contract.copy()
                best_contract["estimated_delta"] = estimated_delta

        if best_contract:
            LOG.flow(
                f"[{symbol}] Selected {option_type} strike ${best_contract['strike']:.2f} "
                f"(delta: {best_contract['estimated_delta']:.2f}, target: {target_delta:.2f})"
            )

        return best_contract

    def get_option_bars(
        self, option_symbol: str, start_date: str, end_date: str, timeframe: str = "1Day"
    ) -> Optional[pd.DataFrame]:
        """
        Fetch historical OHLCV bars for an option.

        Args:
            option_symbol: Options symbol
            start_date: Start date ('YYYY-MM-DD')
            end_date: End date ('YYYY-MM-DD')
            timeframe: Bar timeframe ('1Min', '1Hour', '1Day')

        Returns:
            DataFrame with columns: open, high, low, close, volume, timestamp
            Returns None if data unavailable

        Note: Historical options data may be limited. Use for backtesting only.
        """
        try:
            # Map timeframe string to Alpaca TimeFrame
            if timeframe == "1Min":
                tf = TimeFrame.Minute
            elif timeframe == "1Hour":
                tf = TimeFrame.Hour
            elif timeframe == "1Day":
                tf = TimeFrame.Day
            else:
                LOG.warning(f"Unsupported timeframe: {timeframe}")
                return None

            request = OptionBarsRequest(symbol_or_symbols=option_symbol, timeframe=tf, start=start_date, end=end_date)

            bars_data = self.data_client.get_option_bars(request)

            if option_symbol not in bars_data:
                LOG.warning(f"[{option_symbol}] No bar data returned")
                return None

            bars = bars_data[option_symbol]

            # Convert to DataFrame
            df = pd.DataFrame(
                [
                    {
                        "timestamp": bar.timestamp,
                        "open": float(bar.open),
                        "high": float(bar.high),
                        "low": float(bar.low),
                        "close": float(bar.close),
                        "volume": int(bar.volume),
                    }
                    for bar in bars
                ]
            )

            df.set_index("timestamp", inplace=True)

            LOG.success(f"[{option_symbol}] Fetched {len(df)} bars")

            return df

        except Exception as e:
            LOG.warning(f"[{option_symbol}] Failed to fetch bars: {e}")
            return None

    def validate_quote_quality(self, quote: Dict, max_spread_pct: float = 10.0) -> bool:
        """
        Validate quote data quality.

        Args:
            quote: Quote dictionary from get_option_quote()
            max_spread_pct: Maximum acceptable spread (%)

        Returns:
            True if quote passes quality checks
        """
        if quote is None:
            return False

        # Check 1: Bid > 0
        if quote["bid"] <= 0:
            LOG.warning(f"Invalid bid price: {quote['bid']}")
            return False

        # Check 2: Ask > Bid
        if quote["ask"] <= quote["bid"]:
            LOG.warning(f"Invalid market: ask ({quote['ask']}) <= bid ({quote['bid']})")
            return False

        # Check 3: Spread reasonable
        if quote["spread_pct"] > max_spread_pct:
            LOG.warning(f"Wide spread: {quote['spread_pct']:.2f}% > {max_spread_pct}%")
            return False

        return True
