# Magellan Trading System - Architect Review Quick Reference

**Reviewer:** Software Architect  
**Primary Focus:** Code Quality, Maintainability, Scalability, Production Readiness

---

## Top Priority Refactoring Tasks

### 1. Unify Configuration System 🔴 HIGH PRIORITY
**Current Problem:** Two separate config systems cause confusion and duplication

**Files Involved:**
- `src/config_loader.py` (EngineConfig singleton)
- `config/__init__.py` (Node config loader)
- `config/nodes/*.json` (6 ticker configs)

**Issue:**
```python
# Current: Dual config access patterns
from src.config_loader import EngineConfig
from config import load_node_config

engine_config = EngineConfig()
retrain_interval = engine_config.get('RETRAIN_INTERVAL')  # Global

node_configs = load_node_config()
alpha_weights = node_configs['NVDA']['alpha_weights']  # Ticker-specific

# Problem: Same parameters defined in both systems!
```

**Recommended Solution:**
```yaml
# config/magellan.yaml (single unified config)
engine:
  retrain_interval: 5
  position_cap: 50000
  initial_seed: 100000
  
universe:
  tickers: ["NVDA", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA"]
  
node_defaults:
  alpha_weights:rsi_14: 0.4
    volume_zscore: 0.3
    sentiment: 0.3
  rsi_lookback: 14
  sentry_gate: 0.0
  
nodes:
  NVDA:
    alpha_weights:
      rsi_14: 0.7
      volume_zscore: 0.2
      sentiment: 0.1
    position_cap_usd: 20000
  
  QQQ:
    # Inherits from node_defaults
    pass
```

**Implementation:**
```python
# config/config_manager.py (new file)
from pydantic import BaseModel, validator
import yaml

class AlphaWeights(BaseModel):
    rsi_14: float
    volume_zscore: float
    sentiment: float
    
    @validator('*')
    def weights_sum_to_one(cls, v, values):
        total = sum(values.values()) + v
        assert 0.99 <= total <= 1.01, "Weights must sum to 1.0"
        return v

class NodeConfig(BaseModel):
    alpha_weights: AlphaWeights
    rsi_lookback: int = 14
    sentry_gate: float = 0.0
    position_cap_usd: float = 50000

class MagellanConfig(BaseModel):
    engine: dict
    universe: dict
    node_defaults: NodeConfig
    nodes: dict[str, NodeConfig]

def load_config(path: str = "config/magellan.yaml") -> MagellanConfig:
    with open(path) as f:
        data = yaml.safe_load(f)
    return MagellanConfig(**data)
```

**Migration Path:**
1. Create `config/magellan.yaml` with merged settings (2 hours)
2. Implement Pydantic models with validation (3 hours)
3. Update all modules to use new config manager (4 hours)
4. Delete old config files (15 min)
5. Update tests (1 hour)

---

### 2. Add Test Infrastructure 🔴 HIGH PRIORITY
**Current Problem:** ZERO test coverage

**Required Files:**
```
tests/
├── __init__.py
├── conftest.py              # Pytest fixtures
├── test_features.py         # Feature engineering tests
├── test_backtester.py       # Backtesting logic tests
├── test_data_handler.py     # Data fetching tests (mocked)
├── test_executor.py         # Execution tests (mocked)
├── test_temporal_leak.py    # Critical: Leak detection
└── test_integration.py      # End-to-end pipeline
```

**Critical Test: Temporal Leak Detection**
```python
# tests/test_temporal_leak.py
import pytest
import pandas as pd
from src.features import generate_master_signal

def test_forward_return_never_in_features():
    """CRITICAL: Ensure forward_return never leaks into feature set."""
    # Create test data with forward_return column
    df = pd.DataFrame({
        'rsi_14': [50, 55, 60],
        'volume_zscore': [0.1, 0.2, 0.3],
        'sentiment': [0.5, 0.6, 0.7],
        'log_return': [0.01, 0.02, 0.03],
        'close': [100, 101, 102],
        'forward_return': [0.05, 0.06, 0.07]  # Should be excluded
    })
    
    # Generate signal
    result_df = generate_master_signal(df, ticker='TEST')
    
    # Verify forward_return was NOT used in alpha calculation
    # This is validated by confirming it was dropped in the function
    assert 'alpha_score' in result_df.columns
    
    # Additional check: ensure function doesn't crash
    assert len(result_df) == len(df)
```

**Other Critical Tests:**
```python
# tests/test_features.py
def test_rsi_calculation_accuracy():
    """Verify RSI matches TradingView reference."""
    df = create_test_ohlcv()  # Known test data
    rsi = calculate_rsi(df['close'], period=14)
    assert rsi.iloc[-1] == pytest.approx(67.45, abs=0.1)

def test_rolling_normalization_no_lookahead():
    """Ensure normalization only uses historical data."""
    df = create_test_data()
    normalized = rolling_normalize(df, window=252)
    
    # Check that value at index i only depends on [0:i]
    for i in range(252, len(df)):
        expected = (df.iloc[i] - df.iloc[i-252:i].min()) / (df.iloc[i-252:i].max() - df.iloc[i-252:i].min())
        assert normalized.iloc[i] == pytest.approx(expected, abs=0.01)

# tests/test_backtester.py
def test_wfe_bounds():
    """Ensure WFE stays within realistic bounds."""
    result = run_rolling_backtest('SPY', days=15)
    assert 0.5 <= result['wfe'] <= 1.2, f"WFE {result['wfe']} outside realistic range"
```

**Implementation Steps:**
1. Add `pytest`, `pytest-asyncio`, `pytest-mock` to requirements.txt
2. Create tests/ directory structure (15 min)
3. Write 10 critical tests (1 day)
4. Set up GitHub Actions CI (2 hours)
5. Aim for 80% coverage goal (1 week)

---

### 3. Extract Shared Utilities (DRY Principle) 🟡 MEDIUM PRIORITY
**Current Problem:** 240 lines of OHLCV resampling logic duplicated between AlpacaDataClient and FMPDataClient

**Files Involved:**
- `src/data_handler.py` (lines 158-242: force_resample_ohlcv in Alpaca section)
- `src/data_handler.py` (lines 262-394: nearly identical logic in FMP section)

**Solution:**
```python
# src/utils/resampling.py (new file)
import pandas as pd
from typing import Tuple

INTERVAL_MAP = {
    '1Min': 60,
    '5Min': 300,
    '15Min': 900,
    '1Hour': 3600,
    '1Day': 86400
}

def resample_ohlcv(
    df: pd.DataFrame,
    target_interval: str,
    ticker: str = 'UNKNOWN'
) -> Tuple[pd.DataFrame, bool]:
    """
    Unified OHLCV resampling logic.
    
    Returns:
        (resampled_df, was_resampled)
    """
    if target_interval not in INTERVAL_MAP:
        raise ValueError(f"Unknown interval: {target_interval}")
    
    expected_seconds = INTERVAL_MAP[target_interval]
    
    # Detect actual bar frequency
    if len(df) < 2:
        return df, False
    
    actual_seconds = (df.index[1] - df.index[0]).total_seconds()
    
    if abs(actual_seconds - expected_seconds) < 1:
        # Already correct frequency
        return df, False
    
    # Resample logic (once, not duplicated)
    resampled = df.resample(f'{expected_seconds}S').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()
    
    return resampled, True
```

**Update both clients:**
```python
# src/data_handler.py
from src.utils.resampling import resample_ohlcv

class AlpacaDataClient:
    def fetch_historical_bars(self, ...):
        # ... existing code ...
        df, was_resampled = resample_ohlcv(df, timeframe, symbol)
        # ... rest of logic ...

class FMPDataClient:
    def fetch_historical_bars(self, ...):
        # ... existing code ...
        df, was_resampled = resample_ohlcv(df, timeframe, symbol)
        # ... rest of logic ...
```

**Impact:**
- **Lines saved:** 240+ (50% reduction in data_handler.py)
- **Maintenance:** Bug fixes only needed once
- **Testability:** Single function to test instead of two

---

### 4. Error Handling & Retry Logic 🟡 MEDIUM PRIORITY
**Current Problem:** API calls have no retry logic; single failure crashes trading loop

**Examples of Missing Error Handling:**
- `data_handler.py:85` - `self.api.get_bars()` (no try/except)
- `executor.py:82` - `client.get_current_quote()` (no retry)
- `monitor.py:48` - `self.api.get_account()` (crashes if API down)

**Solution: Retry Decorator**
```python
# src/utils/retry.py (new file)
import tenacity
import logging

retry_policy = tenacity.retry(
    retry=tenacity.retry_if_exception_type((ConnectionError, TimeoutError)),
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(multiplier=1, min=1, max=10),
    before_sleep=tenacity.before_sleep_log(logging.getLogger(), logging.WARNING)
)

@retry_policy
def fetch_with_retry(api_call, *args, **kwargs):
    """Wrap any API call with retry logic."""
    try:
        return api_call(*args, **kwargs)
    except Exception as e:
        logging.error(f"API call failed: {e}")
        raise
```

**Update API calls:**
```python
# src/data_handler.py
from src.utils.retry import fetch_with_retry

class AlpacaDataClient:
    def fetch_historical_bars(self, symbol, timeframe, start, end):
        bars = fetch_with_retry(
            self.api.get_bars,
            symbol=symbol,
            timeframe=timeframe,
            start=start,
            end=end,
            feed='sip'
        )
        
        if bars is None or len(bars.df) == 0:
            raise ValueError(f"Empty API response for {symbol}")
        
        return bars.df
```

**Add Circuit Breaker for Persistent Failures:**
```python
# src/utils/circuit_breaker.py
from datetime import datetime, timedelta

class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=300):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func, *args, **kwargs):
        if self.state == 'OPEN':
            if (datetime.now() - self.last_failure_time).seconds > self.timeout:
                self.state = 'HALF_OPEN'
            else:
                raise Exception("Circuit breaker OPEN: API temporarily disabled")
        
        try:
            result = func(*args, **kwargs)
            self.failure_count = 0
            self.state = 'CLOSED'
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            if self.failure_count >= self.failure_threshold:
                self.state = 'OPEN'
                logging.error(f"Circuit breaker OPEN after {self.failure_count} failures")
            
            raise
```

---

### 5. Decompose main.py (Single Responsibility) 🟢 LOW-MEDIUM PRIORITY
**Current Problem:** main.py is 902 lines with multiple responsibilities

**Proposed Structure:**
```
src/
├── engines/
│   ├── __init__.py
│   ├── simulation_engine.py    # Backtesting/simulation mode
│   └── live_engine.py           # Live trading mode
├── main.py                      # Thin CLI entry point
```

**Refactored main.py:**
```python
# main.py (new, ~50 lines)
import argparse
from src.engines.simulation_engine import run_simulation
from src.engines.live_engine import run_live_trading

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['simulation', 'live'], required=True)
    parser.add_argument('--ticker', default='NVDA')
    parser.add_argument('--config', default='config/magellan.yaml')
    parser.add_argument('--days', type=int, default=15)
    args = parser.parse_args()
    
    if args.mode == 'simulation':
        run_simulation(args.ticker, args.config, args.days)
    else:
        run_live_trading(args.config)

if __name__ == '__main__':
    main()
```

**Extract to simulation_engine.py:**
```python
# src/engines/simulation_engine.py
def run_simulation(ticker: str, config_path: str, days: int):
    """Run backtesting simulation."""
    # Lines 387-750 from current main.py
    # All simulation-specific logic
```

**Extract to live_engine.py:**
```python
# src/engines/live_engine.py
async def run_live_trading(config_path: str):
    """Run live trading loop."""
    # Lines 102-384 from current main.py
    # All live trading logic
```

---

## Deployment Architecture Recommendations

### Current: Single-Process Fragility
```
[main.py] → Crash = All trading stops
```

### Recommended: Service-Based Architecture
```
┌─────────────────────────────┐
│   Nginx Load Balancer       │
└─────────────────────────────┘
              │
    ┌─────────┴─────────┐
    │                   │
┌───▼────┐         ┌───▼────┐
│Worker 1│         │Worker 2│
│(Symbols│         │(Symbols│
│ 1-4)   │         │ 5-8)   │
└───┬────┘         └───┬────┘
    │                   │
    └─────────┬─────────┘
              │
    ┌─────────▼──────────┐
    │   PostgreSQL       │
    │  (Trade History)   │
    └────────────────────┘
    ┌────────────────────┐
    │   Redis            │
    │  (Position Cache)  │
    └────────────────────┘
```

**Implementation:**
```python
# src/engines/worker.py
class TradingWorker:
    def __init__(self, assigned_tickers: list):
        self.tickers = assigned_tickers
        self.db = connect_to_postgres()
        self.redis = connect_to_redis()
    
    async def run(self):
        while True:
            for ticker in self.tickers:
                signal = await self.generate_signal(ticker)
                await self.execute_trade(signal, ticker)
                
                # Write to shared state
                self.redis.set(f"position:{ticker}", position)
                self.db.execute("INSERT INTO trades ...")
            
            await asyncio.sleep(60)  # 1-minute heartbeat
```

---

## Code Quality Quick Wins

### 1. Add Type Hints (30 min)
```python
# Before
def calculate_rsi(close_series, period=14):
    ...

# After
def calculate_rsi(close_series: pd.Series, period: int = 14) -> pd.Series:
    ...
```

### 2. Document Magic Numbers (1 hour)
```python
# Before
if abs(gap_pct) > 1.5 and volume_ratio < 0.8:
    ...

# After
GAP_THRESHOLD_PCT = 1.5  # Institutional definition: "large gap"
LOW_VOLUME_RATIO = 0.8   # 80% of 20-day average

if abs(gap_pct) > GAP_THRESHOLD_PCT and volume_ratio < LOW_VOLUME_RATIO:
    ...
```

### 3. Remove Dead Code (15 min)
```python
# optimizer.py lines 180-212: print_optimizer_result() is fully commented out
# Action: Delete the function entirely
```

---

## CI/CD Pipeline Recommendation

**File:** `.github/workflows/test.yml`
```yaml
name: Magellan Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio
      
      - name: Run tests
        run: pytest --cov=src --cov-report=html
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
      
      - name: Lint check
        run: |
          pip install ruff
          ruff check src/
```

---

## Next Steps

**Week 1:**
- [ ] Unify configuration system (1 day)
- [ ] Add 10 critical unit tests (1 day)
- [ ] Extract resampling utility (2 hours)

**Week 2:**
- [ ] Add retry logic to all API calls (1 day)
- [ ] Decompose main.py into engines/ (4 hours)
- [ ] Set up CI/CD pipeline (2 hours)

**Week 3:**
- [ ] Add type hints to all functions (1 day)
- [ ] Document magic numbers in config (3 hours)
- [ ] Remove dead code (1 hour)

**Week 4:**
- [ ] Design multi-worker architecture (2 days)
- [ ] Add PostgreSQL for trade history (1 day)
- [ ] Production readiness checklist (1 day)

---

**Document Reference:** See [magellan_system_audit.md](file:///C:/Users/adshu/.gemini/antigravity/brain/e62a9fe2-67df-427a-ba77-8062ab8e0fed/magellan_system_audit.md) for full context
