# Magellan `/src` Directory - Complete Architecture Guide

**Created:** 2026-01-18  
**Purpose:** Explain every file in `/src` and which strategies use them  
**Status:** Production System Documentation

---

## 📋 **Directory Overview**

The `/src` directory contains **21 Python files** organized into:
- **17 core modules** (root level)
- **4 options-specific modules** (`/src/options/`)

---

## 🏗️ **Core Infrastructure Files**

### **1. `data_cache.py`** 
**Purpose:** Local caching system to avoid repeated API calls  
**Used By:** ✅ **ALL STRATEGIES**

**What it does:**
- Stores historical price data in `data/cache/` as Parquet files
- Automatically fetches missing data from APIs (Alpaca, FMP)
- Provides `cache.get_or_fetch_equity()` and `cache.get_or_fetch_futures()`
- Handles equities, futures, earnings calendars, and news data

**Key Functions:**
```python
cache.get_or_fetch_equity(symbol, timeframe, start, end)  # For stocks/ETFs
cache.get_or_fetch_futures(symbol, timeframe, start, end)   # For commodities
cache.get_or_fetch_earnings_calendar(symbol, start, end)    # For earnings
```

**Strategies Using It:**
- ✅ Daily Trend (SPY, QQQ, IWM, GLD data)
- ✅ Hourly Swing (TSLA, NVDA data)
- ✅ Bear Trap (9 small-cap symbols, 1-minute data)
- ✅ GSB (NG, SB futures data)
- ✅ FOMC/Earnings Straddles (SPY 1-minute data, earnings calendars)

---

### **2. `data_handler.py`**
**Purpose:** API wrapper for Alpaca and FMP data providers  
**Used By:** ✅ **ALL STRATEGIES** (via data_cache)

**What it does:**
- `AlpacaDataClient`: Fetches OHLCV data from Alpaca API
- `FMPDataClient`: Fetches fundamentals, news, earnings from FMP API
- Handles timeframe conversions (1min → 1hour resampling)
- Provides data quality checks and cleaning

**Key Classes:**
```python
AlpacaDataClient().fetch_historical_bars(symbol, timeframe, start, end)
FMPDataClient().fetch_news_sentiment(symbol)
FMPDataClient().fetch_historical_news(symbol, start, end)
FMPDataClient().fetch_fundamental_metrics(symbol)
```

**Strategies Using It:**
- ✅ All strategies (indirectly through `data_cache`)
- ⚠️ Options strategies use raw Alpaca data for minute-level precision

---

### **3. `features.py`**
**Purpose:** Technical indicator calculations and feature engineering  
**Used By:** ⚠️ **Advanced strategies only** (NOT simple RSI strategies)

**What it does:**
- Calculates RSI, RVOL, Parkinson volatility
- Generates alpha signals from multi-factor models
- Merges price data with FMP fundamentals and sentiment
- Advanced: Wavelet decomposition, carrier-wave filters
- Used for **multi-factor portfolio strategies** (not current 6 strategies)

**Key Functions:**
```python
calculate_rsi(close_series, period=14)
add_technical_indicators(df, node_config)
generate_master_signal(df, node_config)  # Advanced multi-factor
merge_news_pit(price_df, news_list)     # Point-in-time sentiment
```

**Strategies Using It:**
- ❌ Daily Trend: NO (calculates RSI inline)
- ❌ Hourly Swing: NO (calculates RSI inline)
- ❌ Bear Trap: NO (uses ATR, Volume inline)
- ❌ GSB: NO (uses ATR, VWAP inline)
- ❌ FOMC/Earnings: NO (options pricing only)
- ✅ **Future use:** For advanced multi-factor alpha models

---

### **4. `config_loader.py`**
**Purpose:** Centralized configuration management (Singleton)  
**Used By:** ⚠️ **Some strategies** (for parameter loading)

**What it does:**
- Loads JSON config files from `src/configs/`
- Provides `EngineConfig().get('PARAMETER_NAME')` access
- Singleton pattern ensures consistent config across modules
- Default config: `src/configs/mag7_default.json`

**Key Usage:**
```python
config = EngineConfig()
retrain_interval = config.get('RETRAIN_INTERVAL', strict=True)
position_cap = config.get('POSITION_CAP')
```

**Strategies Using It:**
- ⚠️ **Live trading infrastructure** (for system-level params)
- ❌ Current 6 strategies use strategy-local config files instead
- ✅ `backtester_pro.py` and `executor.py` use it

---

### **5. `logger.py`**
**Purpose:** Structured logging system with verbosity levels  
**Used By:** ✅ **ALL FILES** (system-wide logging)

**What it does:**
- Three verbosity levels: QUIET, NORMAL, VERBOSE
- `LOG.critical()`: Always shown (errors, trades)
- `LOG.event()`: Major milestones (NORMAL level)
- `LOG.flow()`: Step-by-step details (VERBOSE level)
- `LOG.debug()`: Backend details (file only, never terminal)
- Writes all logs to `debug_vault.log`

**Key Usage:**
```python
from src.logger import LOG

LOG.critical("❌ Error: trade failed")
LOG.event("✓ Strategy initialized")
LOG.debug("[CACHE] Fetching SPY data...")
```

**Strategies Using It:**
- ✅ ALL strategies use it for error handling and progress updates

---

### **6. `backtester_pro.py`**
**Purpose:** Walk-forward backtesting engine  
**Used By:** ⚠️ **Advanced validation workflows** (NOT basic strategy tests)

**What it does:**
- Runs rolling walk-forward analysis (WFA)
- In-Sample (3 days) → Out-of-Sample (1 day) testing
- Calculates Walk-Forward Efficiency (WFE)
- Generates equity curves and stress test reports
- **Advanced tool** for robustness validation

**Key Functions:**
```python
run_rolling_backtest(ticker, days=15, in_sample_days=3)
print_stress_test_summary(result)
export_stress_test_results(result, filepath)
```

**Strategies Using It:**
- ❌ Simple strategy tests (use inline simulations)
- ✅ **Validation phase** for final robustness checks
- ✅ Perturbation testing infrastructure

---

### **7. `executor.py`**
**Purpose:** Live trade execution via Alpaca API  
**Used By:** ✅ **Production deployment** (when going live)

**What it does:**
- `AlpacaTradingClient`: Executes orders via Alpaca Paper/Live API
- Uses "Marketable Limit" orders (ask+$0.01 for stealth)
- PDT (Pattern Day Trader) protection
- Buying power checks
- Logs all trades to `live_trades.log`
- Emergency liquidation function

**Key Functions:**
```python
client = AlpacaTradingClient()
execute_trade(client, signal, symbol, allocation_pct)
client.liquidate_all_positions()  # Emergency kill-switch
```

**Strategies Using It:**
- ✅ **Paper trading**: Test all strategies before real money
- ✅ **Live trading**: Execute Daily Trend, Hourly Swing signals
- ❌ NOT used for backtesting (simulate_* scripts do that)

---

### **8. `risk_manager.py`**
**Purpose:** Volatility targeting for dynamic position sizing  
**Used By:** ⚠️ **Portfolio-level risk management** (optional)

**What it does:**
- Implements industry-standard volatility targeting
- Scales positions inversely to realized volatility
- Target: 15% annualized portfolio volatility (default)
- Safety bounds: 0.25x to 2.0x leverage
- Based on Moreira & Muir (2017) "Volatility-Managed Portfolios"

**Key Functions:**
```python
targeter = VolatilityTargeter(target_vol=0.15, lookback_days=20)
result = targeter.calculate_scaling_factor()
position_size = base_size * result['scaling_factor']
```

**Strategies Using It:**
- ❌ Fixed-size strategies (Bear Trap, GSB)
- ✅ **Portfolio management** when deploying multiple strategies
- ✅ **Optional enhancement** for Daily Trend/Hourly Swing

---

### **9. `pnl_tracker.py`**
**Purpose:** Virtual P&L simulation and equity curve generation  
**Used By:** ⚠️ **Backtesting infrastructure** (not strategies directly)

**What it does:**
- Simulates portfolio performance from signals
- Applies transaction costs (friction)
- Calculates max drawdown, Sharpe ratio
- Generates ASCII equity curves for terminal display
- Handles position caps and realistic timing (T+1 execution)

**Key Functions:**
```python
metrics = simulate_portfolio(df, initial_capital=100000, friction_bps=1.5)
print_virtual_trading_statement(metrics)
generate_equity_curve_ascii(equity_curve)
```

**Strategies Using It:**
- ✅ Backtesting scripts call this for P&L calculation
- ✅ Walk-forward analysis uses it
- ❌ Simple simulations calculate returns inline

---

### **10. `monitor.py`**
**Purpose:** Real-time position monitoring and alerts  
**Used By:** ✅ **Live trading operations**

**What it does:**
- Monitors open positions
- Tracks P&L and portfolio health
- Sends alerts for unusual events
- Dashboard-style reporting

**Strategies Using It:**
- ✅ Live deployment monitoring
- ❌ NOT used during backtesting

---

### **11. `optimizer.py`**
**Purpose:** Parameter optimization and grid search  
**Used By:** ⚠️ **Research and development**

**What it does:**
- Grid search for optimal RSI periods, thresholds
- Walk-forward optimization
- Prevents over-fitting via robust validation

**Strategies Using It:**
- ✅ **Development phase**: Finding optimal parameters
- ❌ NOT used in production strategies (parameters are fixed)

---

### **12. `discovery.py`**
**Purpose:** Universe selection and symbol scanning  
**Used By:** ⚠️ **Dynamic universe strategies**

**What it does:**
- Scans for high-volatility symbols
- Filters by liquidity, spread, float
- Pre-market gappers detection

**Strategies Using It:**
- ❌ Fixed universe strategies (Daily Trend, Hourly Swing)
- ✅ Bear Trap (could use for real-time symbol discovery)
- ❌ Currently: Bear Trap uses fixed 9-symbol list

---

### **13. `hangar.py`**
**Purpose:** Historical trade and position management  
**Used By:** ⚠️ **Record keeping**

**What it does:**
- Stores trade history
- Position reconciliation
- Historical analytics

**Strategies Using It:**
- ✅ Live trading record-keeping
- ❌ Backtesting (uses in-memory only)

---

### **14. `reconcile.py`**
**Purpose:** Position reconciliation with broker  
**Used By:** ✅ **Live trading safety checks**

**What it does:**
- Compares internal positions vs Alpaca actual positions
- Detects discrepancies
- Prevents phantom positions

**Strategies Using It:**
- ✅ Live deployment safety
- ❌ NOT needed for backtesting

---

### **15. `validation.py`**
**Purpose:** Strategy validation framework  
**Used By:** ✅ **Perturbation testing**

**What it does:**
- Implements validation protocols
- Checks for statistical significance
- Prevents data leakage

**Strategies Using It:**
- ✅ Perturbation tests in `research/Perturbations/`
- ✅ Walk-forward analysis

---

### **16. `monday_release.py`**
**Purpose:** Weekly model retraining scheduler  
**Used By:** ⚠️ **Advanced adaptive strategies**

**What it does:**
- Schedules weekly parameter updates
- Prevents overfitting via limited retraining frequency

**Strategies Using It:**
- ❌ Fixed-parameter strategies (current 6)
- ✅ **Future use**: Adaptive ML-based strategies

---

## 📁 **Options-Specific Files** (`/src/options/`)

### **17. `options/data_handler.py`**
**Purpose:** Options pricing data fetching  
**Used By:** ✅ **FOMC Straddles, Earnings Straddles**

**What it does:**
- Fetches options chain data
- Calculates ATM (at-the-money) strikes
- Handles 0DTE (zero days to expiration) options

---

### **18. `options/features.py`**
**Purpose:** Options greeks calculation  
**Used By:** ✅ **Options strategies**

**What it does:**
- Calculates Delta, Gamma, Theta, Vega
- Implied volatility (IV) estimation
- Black-Scholes model implementation

**Functions:**
```python
calculate_option_greeks(underlying_price, strike, dte, implied_vol)
get_atm_strikes(underlying_price, options_chain)
```

---

### **19. `options/utils.py`**
**Purpose:** Options helper functions  
**Used By:** ✅ **Options strategies**

**What it does:**
- Strike selection logic
- Expiration date handling
- Position P&L calculation for straddles

---

### **20. `options/__init__.py`**
**Purpose:** Options module initialization  
**Used By:** ✅ **Options strategies** (import convenience)

---

## 📊 **Strategy Usage Matrix**

| File | Daily Trend | Hourly Swing | Bear Trap | GSB | FOMC | Earnings |
|------|-------------|--------------|-----------|-----|------|----------|
| `data_cache.py` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `data_handler.py` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `features.py` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `config_loader.py` | ⚠️ | ⚠️ | ❌ | ❌ | ❌ | ❌ |
| `logger.py` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `backtester_pro.py` | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
| `executor.py` | ✅* | ✅* | ✅* | ✅* | ✅* | ✅* |
| `risk_manager.py` | ⚠️ | ⚠️ | ❌ | ❌ | ❌ | ❌ |
| `pnl_tracker.py` | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
| `options/*` | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |

**Legend:**
- ✅ = Always used
- ✅* = Used in live trading
- ⚠️ = Optional/infrastructure
- ❌ = Not used

---

## 🎯 **Quick Reference: Which Files Matter Most?**

### **For Simple Backtesting:**
1. `data_cache.py` - Get historical data
2. `logger.py` - Print messages
3. Inline RSI/indicator calculations (no `features.py` needed)

### **For Live Trading:**
1. `data_cache.py` - Real-time data
2. `executor.py` - Place trades
3. `config_loader.py` - System parameters
4. `risk_manager.py` - Position sizing
5. `monitor.py` - Track positions

### **For Validation:**
1. `backtester_pro.py` - Walk-forward analysis
2. `validation.py` - Statistical checks
3. `pnl_tracker.py` - Performance metrics

---

## 💡 **Key Insight: Current 6 Strategies Are Simple**

Your **6 validated strategies** (Daily Trend, Hourly Swing, Bear Trap, GSB, FOMC, Earnings) are **intentionally simple**:

- ✅ They use **few dependencies** (mostly just `data_cache` and `logger`)
- ✅ They calculate indicators **inline** (RSI, ATR, VWAP)
- ✅ They use **strategy-local config files** (not `config_loader`)
- ❌ They **don't use** `features.py` (multi-factor alpha)
- ❌ They **don't use** complex infrastructure

**Why?** Simplicity = robustness. The complex infrastructure (`features.py`, `backtester_pro.py`, etc.) is for:
- **Advanced strategies** (multi-factor, ML-based)
- **Validation workflows** (perturbation testing, WFA)
- **Live deployment** (execution, monitoring)

---

## 📝 **Summary**

**Core Files Used by ALL Strategies:**
1. `data_cache.py` - Data fetching and caching
2. `logger.py` - Logging and error handling

**Live Trading Infrastructure:**
3. `executor.py` - Trade execution
4. `monitor.py` - Position monitoring
5. `risk_manager.py` - Vol targeting

**Validation Infrastructure:**
6. `backtester_pro.py` - Walk-forward testing
7. `validation.py` - Statistical checks
8. `pnl_tracker.py` - Performance simulation

**Optional/Advanced:**
9. `features.py` - Multi-factor alpha (NOT used by current strategies)
10. `config_loader.py` - System-wide config
11. `optimizer.py` - Parameter tuning
12. `discovery.py` - Symbol scanning

**Options-Specific:**
13-16. `options/*` - Only for FOMC and Earnings Straddles

---

**Last Updated:** 2026-01-18  
**Status:** Complete Architecture Documentation
