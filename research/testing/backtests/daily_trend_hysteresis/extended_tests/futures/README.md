# Daily Trend Hysteresis: Futures Validation Suite

**Date**: 2026-01-16  
**Version**: 1.0  
**Asset Class**: Micro Futures (CME)

---

## PURPOSE

Test the Daily Trend Hysteresis strategy across futures markets to determine if the RSI-based momentum logic translates profitably from equities to commodity, index, currency, and crypto futures.

---

## ASSET UNIVERSE

### Equity Indices (CME)
- **MES** - Micro E-mini S&P 500
- **MNQ** - Micro E-mini Nasdaq 100
- **MYM** - Micro E-mini Dow
- **M2K** - Micro E-mini Russell 2000

### Commodities (CME)
- **MCL** - Micro Crude Oil
- **MGC** - Micro Gold
- **MSI** - Micro Silver
- **MNG** - Micro Natural Gas
- **MCP** - Micro Copper

### Currencies (FX) (CME)
- **M6E** - Micro EUR/USD
- **M6B** - Micro GBP/USD
- **M6A** - Micro AUD/USD

### Crypto (CME)
- **MBT** - Micro Bitcoin

**Total**: 13 futures contracts

---

## STRATEGY LOGIC (DAILY TIMEFRAME)

**Core Mechanics**:
- **Entry**: RSI > 55 (momentum confirmed)
- **Exit**: RSI < 45 (trend broken)
- **Hysteresis "Dead Zone"**: 45-55 holds current position
- **Position**: Long-only
- **Timeframe**: Daily bars

**Baseline Parameters**:
- RSI Period: 28
- Upper Band: 55
- Lower Band: 45

---

## TESTING PROTOCOL

### Phase 1: Initial Validation (2024-2025)
1. Test all 13 futures on 2-year sample
2. Generate `futures_baseline_results.csv`
3. Identify which asset classes respond to momentum logic

**Success Criteria**:
- Sharpe > 0.5
- Max DD < 25%
- Win Rate > 45%

### Phase 2: Parameter Tuning
1. For assets with Sharpe 0.3-0.5, test wider bands (60/40)
2. For volatile assets (MNG, MBT), test longer RSI periods (35-42)
3. Save tuning experiments to `tuning_results.csv`

### Phase 3: Asset Selection
1. Accept assets with **Sharpe > 0.7** after tuning
2. Create individual `assets/<CONTRACT>/config.json` files
3. Reject assets with persistent Sharpe < 0.3

---

## EXPECTED OUTCOMES

**Likely Winners**:
- Equity Indices (MES, MNQ) - Established trends similar to SPY/QQQ
- Gold (MGC) - Strong trend follower historically

**Likely Strugglers**:
- Natural Gas (MNG) - Extreme volatility, mean-reverting
- Crypto (MBT) - Parabolic structure, may need different bands

**Unknown**:
- Currencies - Typically range-bound, may fail hysteresis logic

---

## FILE OUTPUTS

```
tests/futures/
├── README.md                          # This file
├── run_futures_baseline.py            # Main test script
├── futures_baseline_results.csv       # Raw results
├── FUTURES_VALIDATION_REPORT.md       # Summary findings
├── tuning/
│   ├── run_futures_tuning.py          # Parameter sweep
│   └── tuning_results.csv
└── (Optional) wfa/                    # Walk-forward if promising
```

---

## FRICTION ASSUMPTIONS

Futures have **lower friction** than equities but still material:

| Cost Type | Futures | Equities |
|-----------|---------|----------|
| Commission | $0.50/contract | $0.00 (most brokers) |
| Spread | 1-2 ticks | 0.01-0.05% |
| Slippage | 1-2 ticks | 2-5 bps |
| **Total** | ~3-5 bps | ~2-4 bps |

**Conservative Estimate**: 5 bps per round-turn trade.

---

## DEPLOYMENT CRITERIA

For a futures contract to be approved for deployment:

1. **Sharpe > 0.8** (Higher bar than equities due to leverage)
2. **Max DD < 20%** 
3. **Consistent** across 2024 and 2025 (no single-year fluke)
4. **Reasonable trade frequency** (6-20 trades/year ideal)

---

## NEXT STEPS

1. Run `run_futures_baseline.py`
2. Review `futures_baseline_results.csv`
3. Create `FUTURES_VALIDATION_REPORT.md` with findings
4. For approved contracts, create `assets/<CONTRACT>/config.json`
