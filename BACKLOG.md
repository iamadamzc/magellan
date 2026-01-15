# Project Magellan - Technical Backlog

## High Priority: Strategy Refinement

### 1. Adaptive Hysteresis Thresholds
**Context**: The 55/45 RSD thresholds effectively stopped whipsaw but were too conservative for the SPY 2024-2025 bull run, causing the strategy to sit in cash during uptrends.
**Action**: Implement adaptive thresholds based on market volatility (ATR or Rolling StdDev).
- High Volatility (ATR > 2x Avg): Widen bands (e.g., 60/40)
- Low Volatility (ATR < 1x Avg): Tighten bands (e.g., 52/48)
- **Goal**: improve participation in low-volatility drifts while maintaining protection.

### 2. Asymmetric Bands Testing
**Context**: Bull markets drift up slowly but correct sharply. Symmetric bands (55/45) might not capture this behavior efficiently.
**Action**: Test asymmetric configurations.
- Entry: 55 RSI (Conservative entry)
- Exit: 48 RSI (Faster exit)
- **Goal**: Balance capital protection with "time in the market".

### 3. Baseline Comparison Test
**Context**: To scientifically validate "Variant F", we need to quantify the exact "Cost of Whipsaw" saved.
**Action**: Run a backtest with simple RSI=50 threshold (No Hysteresis) on the exact same SPY dataset.
- Compare Trade Frequency (Expected: 2-3x higher)
- Compare Transaction Costs (Expected: Significantly higher)
- Compare Net P&L
- **Goal**: Prove that simpler strategies burn alpha through friction.

## Medium Priority: Infrastructure & Data

### 4. Split-Adjusted Price Handling (NVDA Fix)
**Context**: The NVDA backtest failed because the P&L calculation didn't account for the 10-for-1 stock split on June 10, 2024. Alpaca SIP data should be adjusted, or we need to handle it manually.
**Action**: Update `AlpacaDataClient` or the P&L logic to handle splits.
- Option A: Ensure `adjustment='all'` parameter works correctly in Alpaca SDK.
- Option B: Implement share-based tracking in the backtester instead of simple `% return` compounding.

### 5. Configurable Backtester (Timeframe Support)
**Context**: `backtester_pro.py` currently has `timeframe='1Min'` hardcoded on line 169.
**Action**: Update `run_rolling_backtest` to accept a `timeframe` argument (default to '1Min') so it can natively run Daily strategies without a separate test script.

### 6. Share-Based P&L Tracking
**Context**: Current backtesters often use `(1 + ret).cumprod()` which breaks on large price discontinuities like splits.
**Action**: Refactor `backtester_pro.py` and test scripts to track `shares_held` and `cash_balance` explicitly. This is more robust for splits and dividends.

## Low Priority: Future Expansions

### 7. Multi-Timeframe Confirmation
**Context**: Daily signals can be noisy.
**Action**: Add logic to confirm Daily Hysteresis signals with Weekly trend checks.
- Only exit Long if Daily RSI < 45 AND Weekly RSI < 50.

### 8. Position Sizing Scaling
**Context**: Binary On/Off (100% / 0%) is harsh.
**Action**: Implement stepwise scaling.
- RSI > 55: 100% Long
- RSI 50-55: 50% Long
- RSI < 50: 0% Long
