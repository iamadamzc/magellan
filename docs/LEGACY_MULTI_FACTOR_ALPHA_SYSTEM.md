# Legacy Multi-Factor Alpha System (Archived)

**Date Archived**: 2026-01-16  
**Reason**: Replaced with validated Daily Trend Hysteresis strategy  
**Git Commit**: See commit history before feature/validated-strategies-deployment branch

---

## Overview

This document archives the original multi-factor alpha system that was used in `main.py` before transitioning to the validated strategies.

## System Architecture

### Signal Generation Approach
- **Multi-factor weighted alpha**: Combined RSI, volume z-score, and sentiment
- **FERMI Gate**: Dynamic threshold filtering based on sigma multipliers
- **Carrier Wave**: 60-minute vs 5-minute polarity alignment
- **Timeframe**: 5-minute bars (intraday)

### Configuration (Pre-Validation)

**Original `master_config.json`**:
```json
{
    "tickers": ["NVDA", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA"],
    "NVDA": {
        "interval": "5Min",
        "rsi_lookback": 14,
        "sentry_gate": 0.0,
        "rsi_wt": 0.7,
        "vol_wt": 0.2,
        "sent_wt": 0.1,
        "position_cap_usd": 20000,
        "high_pass_sigma": 0.75
    },
    "SPY": {
        "interval": "5Min",
        "rsi_lookback": 14,
        "sentry_gate": 0.0
    }
}
```

### Key Components

1. **Alpha Weights**:
   - `rsi_wt`: RSI component weight (typically 0.4-0.7)
   - `vol_wt`: Volume z-score weight (typically 0.2-0.3)
   - `sent_wt`: Sentiment weight (typically 0.1-0.3)

2. **FERMI Gate Logic** (`src/features.py` lines 792-864):
   - Dynamic threshold: `fermi_gate = alpha_mean + (sigma_multiplier * alpha_std)`
   - Ticker-specific sigma multipliers:
     - SPY: 2.25 (low conductivity)
     - QQQ: 1.25 (moderate)
     - IWM: 0.75 (high conductivity)
     - Default: 0.5

3. **Carrier Wave Filter** (`src/features.py` lines 756-778):
   - Compares 5-minute and 60-minute RSI polarities
   - Silences conflicting signals (destructive interference)

4. **Hysteresis Deadband** (`src/features.py` line 870):
   - Anti-chatter logic: 0.05 threshold
   - Prevents rapid state oscillations

## Why It Was Replaced

### Validation Results
- **Complex multi-factor system** proved difficult to validate
- **5-minute intraday trading** suffered from friction costs
- **Walk-forward analysis** showed inconsistent performance
- **Sample bias** in initial testing periods

### Validated Alternative
The **Daily Trend Hysteresis (Schmidt Trigger)** strategy proved superior:
- **Simpler**: Pure RSI-based with hysteresis bands
- **Lower friction**: Daily bars vs 5-minute
- **Robust**: Passed full WFA across 2020-2025
- **Consistent**: 11 assets validated with positive returns

## Code References

### Files Using This System
- `main.py`: Lines 1-926 (original implementation)
- `src/features.py`: `generate_master_signal()` function
- `src/optimizer.py`: `calculate_alpha_with_weights()`
- `src/validation.py`: `run_optimized_walk_forward_check()`

### To Restore This System
If you need to restore the old system:

```bash
# View the last commit before validated strategies
git log --oneline feature/validated-strategies-deployment

# Checkout specific files from before the change
git checkout <commit-hash> -- config/nodes/master_config.json
git checkout <commit-hash> -- main.py
```

## Migration Notes

### What Changed
1. **Config**: `master_config.json` updated with hysteresis parameters
2. **Timeframe**: Changed from `5Min` to `1Day`
3. **Signal Logic**: Switched from multi-factor to pure RSI hysteresis
4. **CLI**: All CLI flags preserved (backward compatible)

### What Stayed the Same
- All CLI arguments (`--symbols`, `--start-date`, `--max-position-size`, etc.)
- Data fetching infrastructure (Alpaca + FMP)
- Backtesting framework (`run_rolling_backtest`)
- Live trading loop structure

---

## References

- **Original Research**: See `research/high_frequency/` for HFT experiments
- **Validation Journey**: See `VALIDATED_STRATEGIES_FINAL.md`
- **WFA Results**: See `research/backtests/phase4_audit/`

**Status**: ⚠️ **ARCHIVED** - Do not use for production trading
