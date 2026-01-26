# Volatility Expansion Entry Strategy

**Version**: 2.0 (Sanitized)  
**Type**: Intraday Momentum  
**Symbols**: SPY, QQQ, IWM  
**Resolution**: 1-minute bars

---

## Strategy Overview

Statistically-derived strategy discovered through blind backwards analysis on 2.46M 1-minute bars (2022-2026). Uses unsupervised clustering to identify "volatility expansion" hidden states with positive expectancy across all VIX regimes.

### Performance (Research Backtest)

| Symbol | Hit Rate | Expectancy | Edge Ratio | Lift vs Baseline |
|--------|----------|------------|------------|------------------|
| **SPY** | 57.9% | 0.368R | 2.00 | 1.37x |
| **QQQ** | 57.0% | 0.355R | 2.00 | 1.32x |
| **IWM** | 55.0% | 0.326R | 2.00 | 1.22x |

### VIX Regime Performance (SPY)

| Regime | VIX Range | Hit Rate | Expectancy | Max Drawdown |
|--------|-----------|----------|------------|--------------|
| COMPLACENCY | < 15 | **60.9%** | **0.413R** | 11.5R |
| NORMAL | 15-25 | **56.9%** | **0.353R** | 29.5R |
| PANIC | > 25 | **46.0%** | **0.190R** | 22.5R |

**Key Finding**: Strategy performs best in low-volatility environments (opposite of typical momentum strategies).

---

## Entry Conditions (v2.0 Sanitized)

All conditions must be TRUE:

1. **effort_result_zscore < -0.5**  
   - Low volume absorption (efficient price movement)
   - z-score normalized over 50-bar window

2. **range_ratio_mean > 1.4**  
   - Wide bars relative to body (momentum building)
   - Safe calculation with min_tick floor (no divide-by-zero)

3. **volatility_ratio_mean > 1.0**  
   - ATR(5) / ATR(20) > 1.0 (volatility expanding)

4. **trade_intensity_mean > 0.9**  
   - Normal trade activity (not illiquid)

5. **body_position_mean > 0.25**  
   - Close in upper portion of bar (bullish bias)

---

## Exit Rules

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| **Target** | 2.5 ATR | Statistical edge threshold |
| **Stop Loss** | 1.25 ATR | 2:1 Risk-Reward ratio |
| **Time Exit** | 30 minutes | Event window constraint |
| **EOD Exit** | 3:55 PM ET | Close all before market close |

---

## Risk Management

- **Per-trade risk**: 2% of equity
- **Max position size**: $50,000
- **Max daily loss**: $10,000 (10% of capital)
- **Max trades/day**: 10
- **Max open positions**: 3

---

## Files

```
test/vol_expansion/
├── config.json           # Strategy configuration
├── strategy.py           # Main strategy implementation
├── runner.py             # Execution runner
├── README.md             # This file
└── docs/                 # Documentation
    ├── RESEARCH.md       # Research summary
    └── VALIDATION.md     # Testing checklist
```

---

## Testing Workflow

### 1. **Local Testing** (with cached data)

```bash
# Set environment
export USE_ARCHIVED_DATA=true
cd test/vol_expansion

# Run strategy
python runner.py
```

### 2. **Backtest Validation**

```python
# Compare to research results
python validate_backtest.py

# Expected outputs:
# - Hit rate: ~55-58% (within 5% of research)
# - Expectancy: ~0.3-0.4R
# - Signal frequency: 20-25% of bars
```

### 3. **Walk-Forward Test** (2025-2026 OOS data)

```bash
python walk_forward_test.py --start 2025-01-01 --end 2026-01-24
```

### 4. **Paper Trading** (30 days)

Track real execution vs backtest:
- Slippage impact
- Fill quality
- Signal frequency alignment

---

## Implementation Notes

### Features Calculated

**Core Features** (5):
- `effort_result_zscore`: Volume absorption metric
- `range_ratio`: Bar topology (with safe calculation)
- `volatility_ratio`: ATR expansion/compression
- `trade_intensity`: Trade activity metric
- `body_position`: Close location in bar

**Aggregated Features** (15):
- `_mean`: 50-bar rolling average
- `_std`: 50-bar rolling standard deviation
- `_trend`: 50-bar change

### v2.0 Improvements over v1.0

1. **Fixed "Hard Number" Issue**:  
   - v1.0: `effort_result_mean < 45` (absolute threshold, will drift)
   - v2.0: `effort_result_zscore < -0.5` (dynamic z-score)

2. **Fixed "Singularity" Issue**:  
   - v1.0: `range_ratio = (H-L) / |O-C|` (div-by-zero on Doji bars)
   - v2.0: `range_ratio = (H-L) / max(|O-C|, 0.01)` (floor protection)

---

## Next Steps

1. ✅ **Implemented**: Strategy code following Magellan patterns
2. ⏳ **TODO**: Walk-forward validation on 2025-2026 data
3. ⏳ **TODO**: Paper trading deployment (30 days)
4. ⏳ **TODO**: Performance monitoring dashboard
5. ⏳ **TODO**: Regime-aware position sizing

---

## References

- Research: `/test/blind_backwards/strategy_docs/FINAL_REPORT.md`
- Cluster Analysis: `research/blind_backwards_analysis/`
- Feature Engineering: `src/vol_expansion_features.py`

---

**Account**: PA3DDLQCBJSE (magellan-vol-expansion)  
**Created**: January 25, 2026  
**Status**: Ready for testing
