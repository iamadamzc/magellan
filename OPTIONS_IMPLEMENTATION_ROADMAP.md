# OPTIONS STRATEGY - TECHNICAL IMPLEMENTATION ROADMAP

**Date**: 2026-01-15  
**Branch**: `feature/options-trend-following`  
**Status**: 📋 PLANNING PHASE

---

## 🏗️ SYSTEM ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────┐
│                    MAGELLAN OPTIONS ENGINE                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │ EQUITY DATA  │    │OPTIONS CHAIN │    │   GREEKS     │ │
│  │  (Alpaca)    │────│   (Alpaca)   │────│ (Calculated) │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│         │                     │                    │        │
│         └─────────────────────┴────────────────────┘        │
│                              │                               │
│                    ┌─────────▼────────┐                     │
│                    │ OPTIONS FEATURES │                     │
│                    │ • IV Rank        │                     │
│                    │ • Delta Select   │                     │
│                    │ • DTE Logic      │                     │
│                    │ • Earnings Filter│                     │
│                    └──────────────────┘                     │
│                              │                               │
│                    ┌─────────▼────────┐                     │
│                    │  SIGNAL ENGINE   │                     │
│                    │ (EXISTING RSI    │                     │
│                    │  HYSTERESIS)     │                     │
│                    └──────────────────┘                     │
│                              │                               │
│              ┌───────────────┼───────────────┐             │
│              │               │               │             │
│     ┌────────▼────────┐ ┌───▼────┐ ┌───────▼────────┐    │
│     │  BUY CALL       │ │  HOLD  │ │   BUY PUT      │    │
│     │ (RSI > 55)      │ │ (CASH) │ │  (RSI < 45)    │    │
│     └─────────────────┘ └────────┘ └────────────────┘    │
│              │                              │              │
│     ┌────────▼──────────────────────────────▼────────┐   │
│     │      OPTIONS EXECUTOR                          │   │
│     │  • Strike Selection (delta 0.50-0.70)          │   │
│     │  • Expiration Selection (30-60 DTE)            │   │
│     │  • Auto-Roll Logic (DTE < 7)                   │   │
│     │  • Position Sizing (delta-adjusted notional)   │   │
│     └────────────────────────────────────────────────┘   │
│              │                                             │
│     ┌────────▼──────────────────────────────────────┐    │
│     │      ALPACA OPTIONS API                       │    │
│     │  • Place options orders                       │    │
│     │  • Track positions                            │    │
│     │  • Monitor P&L                                │    │
│     └───────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 FILE STRUCTURE (New Components)

```
Magellan/
├── src/
│   ├── options/                        # NEW: Options-specific modules
│   │   ├── __init__.py
│   │   ├── data_handler.py            # Alpaca options API client
│   │   ├── features.py                # IV, Greeks, DTE calculations
│   │   ├── executor.py                # Options order execution
│   │   ├── pnl_tracker.py             # Options P&L accounting
│   │   ├── backtester.py              # Options-specific backtest
│   │   └── utils.py                   # Symbol formatting, helpers
│   │
│   ├── data_handler.py                # MODIFY: Add options data methods
│   ├── features.py                    # KEEP: Reuse RSI hysteresis
│   ├── config_loader.py               # MODIFY: Add options config params
│   └── ...
│
├── config/
│   └── options/                       # NEW: Options configurations
│       ├── SPY.json                   # SPY options config
│       ├── QQQ.json
│       ├── NVDA.json
│       └── master_options_config.json
│
├── research/                          # NEW: Development scripts
│   ├── options_api_test.py            # Phase 1: API connection test
│   ├── test_options_chain.py          # Check chain data quality
│   ├── test_greeks_calculation.py     # Validate Greek formulas
│   ├── test_strike_selection.py       # Delta-based strike logic
│   ├── test_options_system1.py        # Full backtest (Phase 2)
│   └── options_paper_trade.py         # Manual paper trading
│
├── OPTIONS_TREND_FOLLOWING_ASSESSMENT.md  # Strategy assessment (this doc's companion)
├── OPTIONS_IMPLEMENTATION_ROADMAP.md      # This document
└── OPTIONS_VALIDATION_REPORT.md           # Created after Phase 3
```

---

## 🔧 PHASE 1: PROOF OF CONCEPT (WEEKS 1-3)

### **Objective**: Connect to Alpaca Options API and fetch basic data

### **Task 1.1: API Connection Test**

**File**: `research/options_api_test.py`

```python
"""
Test connection to Alpaca Options API and fetch options chain.
"""

import os
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOptionContractsRequest
from alpaca.data.historical import OptionHistoricalDataClient
from datetime import datetime, timedelta

def test_alpaca_options_connection():
    """
    Verify Alpaca Options API credentials and basic connectivity.
    """
    print("🔌 Testing Alpaca Options API Connection...")
    
    # Initialize clients
    api_key = os.getenv("APCA_API_KEY_ID")
    secret_key = os.getenv("APCA_API_SECRET_KEY")
    paper = True  # Always use paper for testing
    
    trading_client = TradingClient(api_key, secret_key, paper=paper)
    
    # Test 1: Check if options trading is enabled
    account = trading_client.get_account()
    print(f"✅ Account Status: {account.status}")
    print(f"✅ Options Trading Approved: {account.options_approved_level}")
    
    if account.options_approved_level == 0:
        print("❌ ERROR: Options trading not enabled on this account!")
        print("   → Visit Alpaca dashboard to enable options")
        return False
    
    # Test 2: Fetch options chain for SPY
    print("\n📊 Fetching SPY options chain...")
    
    # Get contracts expiring in next 30-60 days
    expiry_start = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    expiry_end = (datetime.now() + timedelta(days=60)).strftime('%Y-%m-%d')
    
    request = GetOptionContractsRequest(
        underlying_symbols=['SPY'],
        expiration_date_gte=expiry_start,
        expiration_date_lte=expiry_end,
        type='call'  # Start with calls
    )
    
    contracts = trading_client.get_option_contracts(request)
    
    if len(contracts) == 0:
        print("❌ ERROR: No options contracts found!")
        return False
    
    print(f"✅ Found {len(contracts)} SPY call contracts")
    
    # Display sample contracts
    print("\n📋 Sample Contracts:")
    for contract in contracts[:5]:
        print(f"  • {contract.symbol}")
        print(f"    Strike: ${contract.strike_price}")
        print(f"    Expiry: {contract.expiration_date}")
        print(f"    Type: {contract.type}")
        print()
    
    # Test 3: Fetch quote for a specific contract
    print("💰 Fetching quote for first contract...")
    sample_symbol = contracts[0].symbol
    
    # Note: Use the options data client for quotes
    data_client = OptionHistoricalDataClient(api_key, secret_key)
    
    # Get latest snapshot (quote)
    from alpaca.data.requests import OptionLatestQuoteRequest
    quote_request = OptionLatestQuoteRequest(symbol_or_symbols=sample_symbol)
    
    try:
        quote = data_client.get_option_latest_quote(quote_request)
        print(f"✅ Quote Retrieved:")
        print(f"  Bid: ${quote[sample_symbol].bid_price}")
        print(f"  Ask: ${quote[sample_symbol].ask_price}")
        print(f"  Spread: ${quote[sample_symbol].ask_price - quote[sample_symbol].bid_price:.2f}")
    except Exception as e:
        print(f"⚠️  Could not fetch quote: {e}")
    
    print("\n✅ ALL TESTS PASSED! Alpaca Options API is ready.")
    return True


if __name__ == "__main__":
    success = test_alpaca_options_connection()
    exit(0 if success else 1)
```

**Expected Output**:
```
🔌 Testing Alpaca Options API Connection...
✅ Account Status: ACTIVE
✅ Options Trading Approved: 2

📊 Fetching SPY options chain...
✅ Found 127 SPY call contracts

📋 Sample Contracts:
  • SPY260221C00590000
    Strike: $590.0
    Expiry: 2026-02-21
    Type: call

💰 Fetching quote for first contract...
✅ Quote Retrieved:
  Bid: $1.45
  Ask: $1.48
  Spread: $0.03

✅ ALL TESTS PASSED! Alpaca Options API is ready.
```

**Success Criteria**:
- [ ] Script runs without errors
- [ ] Options contracts are retrieved
- [ ] Bid/ask quotes are available
- [ ] Spread is reasonable (<$0.10 for ATM options)

---

### **Task 1.2: Create Options Data Handler**

**File**: `src/options/data_handler.py`

```python
"""
Alpaca Options Data Client
Handles fetching options chains, quotes, and Greeks.
"""

import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import pandas as pd
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOptionContractsRequest
from alpaca.data.historical import OptionHistoricalDataClient
from alpaca.data.requests import OptionLatestQuoteRequest
from src.logger import LOG


class AlpacaOptionsClient:
    """Client for fetching and processing options data from Alpaca."""
    
    def __init__(self):
        """
        Initialize the Alpaca Options Client.
        
        Credentials are loaded from environment variables:
        - APCA_API_KEY_ID: Alpaca API key
        - APCA_API_SECRET_KEY: Alpaca secret key
        - APCA_API_BASE_URL: Alpaca API base URL (paper vs live)
        """
        self.api_key = os.getenv("APCA_API_KEY_ID")
        self.secret_key = os.getenv("APCA_API_SECRET_KEY")
        self.base_url = os.getenv("APCA_API_BASE_URL", "https://paper-api.alpaca.markets")
        
        self.paper = "paper" in self.base_url.lower()
        
        # Initialize clients
        self.trading_client = TradingClient(
            self.api_key, 
            self.secret_key, 
            paper=self.paper
        )
        
        self.data_client = OptionHistoricalDataClient(
            self.api_key,
            self.secret_key
        )
        
        LOG.info(f"[OPTIONS CLIENT] Initialized ({'PAPER' if self.paper else 'LIVE'} mode)")
    
    def get_options_chain(
        self, 
        symbol: str,
        option_type: str = 'call',
        min_dte: int = 30,
        max_dte: int = 60
    ) -> List[Dict]:
        """
        Fetch options chain for a given underlying symbol.
        
        Args:
            symbol: Underlying stock symbol (e.g., 'SPY')
            option_type: 'call' or 'put'
            min_dte: Minimum days to expiration
            max_dte: Maximum days to expiration
        
        Returns:
            List of contract dictionaries with keys:
            - symbol: Options symbol (e.g., 'SPY260221C00590000')
            - strike: Strike price
            - expiration: Expiration date
            - type: 'call' or 'put'
        """
        LOG.flow(f"[{symbol}] Fetching {option_type} options chain (DTE {min_dte}-{max_dte})...")
        
        expiry_start = (datetime.now() + timedelta(days=min_dte)).strftime('%Y-%m-%d')
        expiry_end = (datetime.now() + timedelta(days=max_dte)).strftime('%Y-%m-%d')
        
        request = GetOptionContractsRequest(
            underlying_symbols=[symbol],
            expiration_date_gte=expiry_start,
            expiration_date_lte=expiry_end,
            type=option_type
        )
        
        contracts = self.trading_client.get_option_contracts(request)
        
        # Convert to dictionaries for easier handling
        chain = []
        for contract in contracts:
            chain.append({
                'symbol': contract.symbol,
                'strike': float(contract.strike_price),
                'expiration': contract.expiration_date,
                'type': contract.type,
                'underlying': symbol
            })
        
        LOG.success(f"[{symbol}] Found {len(chain)} {option_type} contracts")
        return chain
    
    def get_option_quote(self, option_symbol: str) -> Dict:
        """
        Fetch current bid/ask quote for an option contract.
        
        Args:
            option_symbol: Options symbol (e.g., 'SPY260221C00590000')
        
        Returns:
            Dictionary with keys:
            - bid: Bid price
            - ask: Ask price
            - mid: Mid price (average of bid/ask)
            - spread: Bid-ask spread
            - spread_pct: Spread as % of mid price
        """
        request = OptionLatestQuoteRequest(symbol_or_symbols=option_symbol)
        
        try:
            quote_data = self.data_client.get_option_latest_quote(request)
            quote = quote_data[option_symbol]
            
            bid = float(quote.bid_price)
            ask = float(quote.ask_price)
            mid = (bid + ask) / 2.0
            spread = ask - bid
            spread_pct = (spread / mid * 100) if mid > 0 else 0
            
            return {
                'bid': bid,
                'ask': ask,
                'mid': mid,
                'spread': spread,
                'spread_pct': spread_pct
            }
        
        except Exception as e:
            LOG.warning(f"[{option_symbol}] Failed to fetch quote: {e}")
            return None
    
    def get_atm_strike(self, symbol: str, current_price: float) -> float:
        """
        Find the at-the-money (ATM) strike price.
        
        Args:
            symbol: Underlying symbol
            current_price: Current stock price
        
        Returns:
            Nearest strike price to current stock price
        """
        # Get a sample chain to see available strikes
        chain = self.get_options_chain(symbol, min_dte=30, max_dte=60)
        
        if not chain:
            LOG.warning(f"[{symbol}] No options chain found, using current price as ATM")
            return round(current_price)
        
        # Extract unique strikes
        strikes = sorted(set([c['strike'] for c in chain]))
        
        # Find closest strike
        atm_strike = min(strikes, key=lambda x: abs(x - current_price))
        
        LOG.flow(f"[{symbol}] Current: ${current_price:.2f}, ATM Strike: ${atm_strike:.2f}")
        return atm_strike
```

**Usage Example**:
```python
from src.options.data_handler import AlpacaOptionsClient

client = AlpacaOptionsClient()

# Get SPY call options chain (30-60 DTE)
chain = client.get_options_chain('SPY', option_type='call', min_dte=30, max_dte=60)

# Get quote for a specific contract
quote = client.get_option_quote('SPY260221C00590000')
print(f"Mid Price: ${quote['mid']:.2f}, Spread: {quote['spread_pct']:.1f}%")
```

---

## 🧪 PHASE 2: STRATEGY TRANSLATION (WEEKS 4-7)

### **Task 2.1: Options Feature Engineering**

**File**: `src/options/features.py`

```python
"""
Options Feature Engineering
Calculates Greeks, IV metrics, and filters for options selection.
"""

import numpy as np
import pandas as pd
from scipy.stats import norm
from typing import Dict
from src.logger import LOG


class OptionsFeatureEngineer:
    """
    Calculates options-specific features for strategy logic.
    """
    
    @staticmethod
    def calculate_black_scholes_greeks(
        S: float,  # Spot price
        K: float,  # Strike price
        T: float,  # Time to expiration (years)
        r: float,  # Risk-free rate
        sigma: float,  # Implied volatility
        option_type: str = 'call'
    ) -> Dict[str, float]:
        """
        Calculate Black-Scholes Greeks for an option.
        
        Returns:
            Dictionary with keys: delta, gamma, theta, vega
        """
        # Prevent division by zero
        if T <= 0:
            LOG.warning("Time to expiration <= 0, returning zero Greeks")
            return {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0}
        
        # Black-Scholes intermediate calculations
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        # Delta
        if option_type == 'call':
            delta = norm.cdf(d1)
        else:  # put
            delta = norm.cdf(d1) - 1
        
        # Gamma (same for calls and puts)
        gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
        
        # Vega (same for calls and puts, convert to $ per 1% IV change)
        vega = S * norm.pdf(d1) * np.sqrt(T) * 0.01
        
        # Theta (daily decay)
        if option_type == 'call':
            theta = (
                -(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
                - r * K * np.exp(-r * T) * norm.cdf(d2)
            ) / 365
        else:  # put
            theta = (
                -(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
                + r * K * np.exp(-r * T) * norm.cdf(-d2)
            ) / 365
        
        return {
            'delta': delta,
            'gamma': gamma,
            'theta': theta,
            'vega': vega
        }
    
    @staticmethod
    def calculate_iv_rank(
        current_iv: float,
        iv_history: pd.Series,
        lookback_days: int = 252
    ) -> float:
        """
        Calculate IV Rank (percentile of current IV vs historical range).
        
        IV Rank = (Current IV - Min IV) / (Max IV - Min IV) * 100
        
        Args:
            current_iv: Current implied volatility (e.g., 0.35 = 35%)
            iv_history: Series of historical IV values
            lookback_days: Number of days for historical range
        
        Returns:
            IV Rank (0-100)
        """
        recent_iv = iv_history.tail(lookback_days)
        
        if len(recent_iv) < 30:
            LOG.warning(f"Insufficient IV history ({len(recent_iv)} days), using 50 as default")
            return 50.0
        
        min_iv = recent_iv.min()
        max_iv = recent_iv.max()
        
        if max_iv == min_iv:
            return 50.0
        
        iv_rank = ((current_iv - min_iv) / (max_iv - min_iv)) * 100
        return iv_rank
    
    @staticmethod
    def select_strike_by_delta(
        chain: list,
        target_delta: float,
        current_price: float,
        option_type: str = 'call'
    ) -> Dict:
        """
        Select the strike closest to a target delta.
        
        Args:
            chain: List of option contracts (from AlpacaOptionsClient)
            target_delta: Target delta (e.g., 0.50 for ATM, 0.30 for OTM)
            current_price: Current stock price
            option_type: 'call' or 'put'
        
        Returns:
            Contract dictionary with closest delta to target
        """
        # Filter by option type
        filtered_chain = [c for c in chain if c['type'] == option_type]
        
        if not filtered_chain:
            LOG.warning(f"No {option_type} options found in chain!")
            return None
        
        # Calculate approximate delta for each strike
        # (Simplified: delta ≈ 0.50 for ATM, increases OTM for calls, decreases for puts)
        r = 0.04  # Risk-free rate assumption
        sigma = 0.30  # IV assumption (could fetch from market)
        
        best_contract = None
        min_delta_diff = float('inf')
        
        for contract in filtered_chain:
            K = contract['strike']
            
            # Days to expiration
            expiry = pd.to_datetime(contract['expiration'])
            T = (expiry - pd.Timestamp.now()).days / 365.0
            
            if T <= 0:
                continue
            
            # Calculate delta
            greeks = OptionsFeatureEngineer.calculate_black_scholes_greeks(
                S=current_price,
                K=K,
                T=T,
                r=r,
                sigma=sigma,
                option_type=option_type
            )
            
            delta = abs(greeks['delta'])  # Use absolute value for puts
            
            # Find closest to target
            delta_diff = abs(delta - target_delta)
            if delta_diff < min_delta_diff:
                min_delta_diff = delta_diff
                best_contract = contract
                best_contract['estimated_delta'] = greeks['delta']
                best_contract['estimated_theta'] = greeks['theta']
        
        if best_contract:
            LOG.flow(
                f"Selected {option_type} strike ${best_contract['strike']:.2f} "
                f"(delta: {best_contract['estimated_delta']:.2f}, "
                f"target: {target_delta:.2f})"
            )
        
        return best_contract
```

---

### **Task 2.2: Options Signal Translator**

**File**: `src/options/executor.py`

```python
"""
Options Executor
Translates equity signals into options positions.
"""

from typing import Dict, Optional
from datetime import datetime
from src.logger import LOG
from src.options.data_handler import AlpacaOptionsClient
from src.options.features import OptionsFeatureEngineer


class OptionsExecutor:
    """
    Executes options trades based on equity signals.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize options executor.
        
        Args:
            config: Options strategy configuration with keys:
                - target_delta: Target delta for strike selection (0.50-0.70)
                - min_dte: Minimum days to expiration
                - max_dte: Maximum days to expiration
                - roll_threshold_dte: Roll when DTE < this value
                - max_iv_rank: Maximum IV rank to enter new positions
        """
        self.config = config
        self.client = AlpacaOptionsClient()
        self.feature_eng = OptionsFeatureEngineer()
        
        # Extract config params
        self.target_delta = config.get('target_delta', 0.60)
        self.min_dte = config.get('min_dte', 30)
        self.max_dte = config.get('max_dte', 60)
        self.roll_threshold_dte = config.get('roll_threshold_dte', 7)
        self.max_iv_rank = config.get('max_iv_rank', 70)
        
        LOG.info(f"[OPTIONS EXECUTOR] Initialized (Delta: {self.target_delta}, DTE: {self.min_dte}-{self.max_dte})")
    
    def translate_signal_to_position(
        self,
        signal: str,  # 'BUY', 'SELL', 'HOLD'
        symbol: str,
        current_price: float,
        current_position: Optional[Dict] = None
    ) -> Dict:
        """
        Translate equity signal to options position.
        
        Args:
            signal: Equity signal ('BUY', 'SELL', 'HOLD')
            symbol: Underlying symbol (e.g., 'SPY')
            current_price: Current stock price
            current_position: Current options position (if any)
        
        Returns:
            Dictionary with keys:
            - action: 'OPEN_CALL', 'OPEN_PUT', 'CLOSE', 'ROLL', 'HOLD'
            - contract: Options contract to trade
            - qty: Number of contracts
        """
        LOG.flow(f"[{symbol}] Translating signal: {signal}, Price: ${current_price:.2f}")
        
        # HOLD signal → Close all options, go to cash
        if signal == 'HOLD':
            if current_position:
                return {
                    'action': 'CLOSE',
                    'contract': current_position['contract'],
                    'qty': current_position['qty'],
                    'reason': 'Signal = HOLD (Hysteresis quiet zone)'
                }
            else:
                return {'action': 'HOLD', 'reason': 'No position, signal = HOLD'}
        
        # Check if we need to roll existing position
        if current_position:
            dte = self._get_dte(current_position['contract']['expiration'])
            if dte < self.roll_threshold_dte:
                LOG.warning(f"[{symbol}] DTE = {dte}, rolling position...")
                return self._roll_position(symbol, current_price, current_position, signal)
        
        # BUY signal → Open CALL or roll to CALL
        if signal == 'BUY':
            # If already holding CALL, keep it
            if current_position and current_position.get('type') == 'call':
                return {'action': 'HOLD', 'reason': 'Already holding CALL'}
            
            # If holding PUT, close it and open CALL
            if current_position and current_position.get('type') == 'put':
                return {
                    'action': 'SWITCH_TO_CALL',
                    'close_contract': current_position['contract'],
                    'open_contract': self._select_call(symbol, current_price),
                    'qty': current_position['qty']
                }
            
            # No position, open CALL
            call_contract = self._select_call(symbol, current_price)
            return {
                'action': 'OPEN_CALL',
                'contract': call_contract,
                'qty': self._calculate_position_size(call_contract, current_price),
                'reason': 'Signal = BUY (RSI > 55)'
            }
        
        # SELL signal → Open PUT or roll to PUT
        if signal == 'SELL':
            # If already holding PUT, keep it
            if current_position and current_position.get('type') == 'put':
                return {'action': 'HOLD', 'reason': 'Already holding PUT'}
            
            # If holding CALL, close it and open PUT
            if current_position and current_position.get('type') == 'call':
                return {
                    'action': 'SWITCH_TO_PUT',
                    'close_contract': current_position['contract'],
                    'open_contract': self._select_put(symbol, current_price),
                    'qty': current_position['qty']
                }
            
            # No position, open PUT
            put_contract = self._select_put(symbol, current_price)
            return {
                'action': 'OPEN_PUT',
                'contract': put_contract,
                'qty': self._calculate_position_size(put_contract, current_price),
                'reason': 'Signal = SELL (RSI < 45)'
            }
    
    def _select_call(self, symbol: str, current_price: float) -> Dict:
        """Select optimal CALL contract based on target delta."""
        chain = self.client.get_options_chain(
            symbol, 
            option_type='call', 
            min_dte=self.min_dte, 
            max_dte=self.max_dte
        )
        
        contract = self.feature_eng.select_strike_by_delta(
            chain, 
            target_delta=self.target_delta, 
            current_price=current_price,
            option_type='call'
        )
        
        return contract
    
    def _select_put(self, symbol: str, current_price: float) -> Dict:
        """Select optimal PUT contract based on target delta."""
        chain = self.client.get_options_chain(
            symbol, 
            option_type='put', 
            min_dte=self.min_dte, 
            max_dte=self.max_dte
        )
        
        contract = self.feature_eng.select_strike_by_delta(
            chain, 
            target_delta=self.target_delta, 
            current_price=current_price,
            option_type='put'
        )
        
        return contract
    
    def _calculate_position_size(self, contract: Dict, current_price: float) -> int:
        """
        Calculate number of contracts based on target notional exposure.
        
        For now, use simple delta-adjusted sizing:
        Target Notional = $10,000
        Delta-Adjusted Shares = Target Notional / Current Price
        Contracts = Delta-Adjusted Shares / 100 / Delta
        """
        target_notional = self.config.get('target_notional', 10000)
        delta = abs(contract.get('estimated_delta', 0.60))
        
        shares_needed = target_notional / current_price
        contracts_needed = shares_needed / (100 * delta)
        
        # Round to nearest integer, min 1 contract
        qty = max(1, round(contracts_needed))
        
        LOG.flow(
            f"Position size: {qty} contracts "
            f"(Target: ${target_notional}, Delta: {delta:.2f})"
        )
        
        return qty
    
    def _get_dte(self, expiration_date: str) -> int:
        """Calculate days to expiration."""
        expiry = pd.to_datetime(expiration_date)
        return (expiry - pd.Timestamp.now()).days
    
    def _roll_position(self, symbol: str, current_price: float, current_position: Dict, signal: str) -> Dict:
        """
        Roll existing position to new expiration.
        """
        option_type = current_position['type']
        
        # Select new contract with freshDTE
        if option_type == 'call':
            new_contract = self._select_call(symbol, current_price)
        else:
            new_contract = self._select_put(symbol, current_price)
        
        return {
            'action': 'ROLL',
            'close_contract': current_position['contract'],
            'open_contract': new_contract,
            'qty': current_position['qty'],
            'reason': f'DTE < {self.roll_threshold_dte}, rolling to new expiration'
        }
```

---

## 📊 PHASE 3: BACKTESTING (WEEKS 8-10)

### **Task 3.1: Options Backtester**

**File**: `src/options/backtester.py`

```python
"""
Options Backtesting Engine
Simulates historical options trading with friction costs.
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from src.logger import LOG
from src.options.features import OptionsFeatureEngineer


class OptionsBacktester:
    """
    Backtest options strategies with realistic friction modeling.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize backtester.
        
        Args:
            config: Backtest configuration with keys:
                - initial_capital: Starting cash
                - slippage_pct: Bid-ask slippage as % of mid price
                - contract_fee: Per-contract regulatory fees ($0.097)
        """
        self.config = config
        self.initial_capital = config.get('initial_capital', 100000)
        self.slippage_pct = config.get('slippage_pct', 1.0)  # 1% slippage
        self.contract_fee = config.get('contract_fee', 0.097)  # Alpaca fees
        
        LOG.info(f"[OPTIONS BACKTESTER] Initialized (Capital: ${self.initial_capital}, Slippage: {self.slippage_pct}%)")
    
    def simulate(
        self,
        price_df: pd.DataFrame,  # Daily OHLCV
        signals_df: pd.DataFrame,  # Signals (BUY/SELL/HOLD)
        iv_df: pd.DataFrame  # Historical IV data
    ) -> Dict:
        """
        Run backtest simulation.
        
        Returns:
            Dictionary with backtest results:
            - equity_curve: Daily equity values
            - trades: List of all trades
            - metrics: Performance metrics
        """
        LOG.event("[BACKTEST] Starting options simulation...")
        
        # Initialize tracking
        cash = self.initial_capital
        positions = []
        equity_curve = []
        trades = []
        
        for date, row in price_df.iterrows():
            current_price = row['close']
            signal = signals_df.loc[date, 'signal'] if date in signals_df.index else 'HOLD'
            
            # Mark-to-market existing positions
            position_value = self._mark_to_market(positions, current_price, date, iv_df)
            
            # Total equity = cash + position value
            total_equity = cash + position_value
            equity_curve.append({
                'date': date,
                'equity': total_equity,
                'cash': cash,
                'position_value': position_value
            })
            
            # Execute signal logic
            if signal == 'BUY':
                # Open CALL or switch from PUT
                pass  # Implementation similar to OptionsExecutor
            elif signal == 'SELL':
                # Open PUT or switch from CALL
                pass
            elif signal == 'HOLD':
                # Close all positions
                if positions:
                    cash += self._close_all_positions(positions, current_price, date)
                    positions = []
        
        # Calculate metrics
        equity_df = pd.DataFrame(equity_curve).set_index('date')
        metrics = self._calculate_metrics(equity_df)
        
        return {
            'equity_curve': equity_df,
            'trades': trades,
            'metrics': metrics
        }
    
    def _mark_to_market(self, positions: List, current_price: float, date, iv_df: pd.DataFrame) -> float:
        """
        Calculate current value of all open positions.
        """
        total_value = 0
        
        for pos in positions:
            # Calculate theoretical option value using Black-Scholes
            # (In reality, use mid price from market data if available)
            total_value += self._calculate_option_value(pos, current_price, date, iv_df)
        
        return total_value
    
    def _calculate_option_value(self, position: Dict, S: float, date, iv_df: pd.DataFrame) -> float:
        """
        Estimate option value using Black-Scholes.
        """
        K = position['strike']
        expiry = pd.to_datetime(position['expiration'])
        T = (expiry - date).days / 365.0
        
        if T <= 0:
            # Expired, intrinsic value only
            if position['type'] == 'call':
                intrinsic = max(0, S - K)
            else:
                intrinsic = max(0, K - S)
            return intrinsic * position['qty'] * 100
        
        # Get IV for this date
        iv = iv_df.loc[date, 'iv'] if date in iv_df.index else 0.30
        
        # Black-Scholes
        greeks = OptionsFeatureEngineer.calculate_black_scholes_greeks(
            S=S, K=K, T=T, r=0.04, sigma=iv, option_type=position['type']
        )
        
        # Simplified: Option value ≈ intrinsic + extrinsic (theta decay)
        # For full implementation, use BS formula to get price
        
        # PLACEHOLDER: Return simplified estimate
        if position['type'] == 'call':
            value = max(0, S - K) * position['qty'] * 100
        else:
            value = max(0, K - S) * position['qty'] * 100
        
        return value
    
    def _calculate_metrics(self, equity_df: pd.DataFrame) -> Dict:
        """
        Calculate performance metrics.
        """
        returns = equity_df['equity'].pct_change().dropna()
        
        total_return = (equity_df['equity'].iloc[-1] / self.initial_capital - 1) * 100
        sharpe = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
        max_dd = ((equity_df['equity'] / equity_df['equity'].cummax()) - 1).min() * 100
        
        return {
            'total_return_pct': total_return,
            'sharpe_ratio': sharpe,
            'max_drawdown_pct': max_dd,
            'final_equity': equity_df['equity'].iloc[-1]
        }
```

---

## 🎯 NEXT STEPS

### **Immediate Actions (This Week)**

1. **Review Assessment** ✅ (You're reading it!)
2. **Decide on Commitment**:
   - **Option A**: Full build-out (12-week timeline)
   - **Option B**: POC only (3 weeks), then reassess
   - **Option C**: Defer until System 1/2 are live

3. **If proceeding**:
   - Run `research/options_api_test.py` to verify Alpaca access
   - Create feature branch: ✅ DONE (`feature/options-trend-following`)
   - Begin Phase 1 implementation

### **Development Milestones**

| Week | Milestone | Deliverable |
|------|-----------|-------------|
| 1-3 | Phase 1 POC | API connection, basic data fetch |
| 4-7 | Phase 2 Translation | Options feature eng, executor logic |
| 8-10 | Phase 3 Backtest | SPY backtest results |
| 11-12 | Multi-asset validation | 3-4 asset configs |
| 13-16 | Paper trading | Live monitoring |

---

**END OF ROADMAP**

**Status**: Ready to begin Phase 1 when approved 🚀
