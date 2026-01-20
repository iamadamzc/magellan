# Hourly Swing: Futures Validation Suite

**Date**: 2026-01-16  
**Version**: 1.0  
**Asset Class**: Micro Futures (CME)

---

## PURPOSE

Test the Hourly Swing strategy (RSI hysteresis on 1-hour bars) across futures markets to capture intraday volatility swings in commodity, index, currency, and crypto futures.

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
- **MNG** - Micro Natural Gas ⭐ HIGH VOLATILITY
- **MCP** - Micro Copper

### Currencies (FX) (CME)
- **M6E** - Micro EUR/USD
- **M6B** - Micro GBP/USD
- **M6A** - Micro AUD/USD

### Crypto (CME)
- **MBT** - Micro Bitcoin ⭐ EXTREME VOLATILITY

**Total**: 13 futures contracts

---

## STRATEGY LOGIC (HOURLY TIMEFRAME)

**Core Mechanics**:
- **Entry**: Hourly RSI > 60 (breakout confirmed)
- **Exit**: Hourly RSI < 40 (breakdown)
- **Hysteresis "Dead Zone"**: 40-60 holds current position
- **Position**: Long-only
- **Timeframe**: 1-hour bars
- **Hold Time**: Typically 2-5 days (overnight holds)

**Baseline Parameters**:
- RSI Period: 28
- Upper Band: 60
- Lower Band: 40

---

## TESTING PROTOCOL

### Phase 1: Initial Validation (2024-2025)
1. Test all 13 futures on 2-year hourly sample
2. Generate `futures_hourly_results.csv`
3. Identify high-beta assets (likely MBT, MNG, MCL)

**Success Criteria**:
- Sharpe > 0.5
- Max DD < 30%
- Win Rate > 40%
- Trade frequency: 10-50/year (avoid over-trading)

### Phase 2: Volatility-Adjusted Tuning
For high-volatility assets (MBT, MNG), test wider bands:
- **Conservative**: 65/35 bands (reduce trade frequency)
- **Aggressive**: 70/30 bands (only extreme moves)

### Phase 3: Asset Selection
- Accept assets with **Sharpe > 0.8** after tuning
- Create individual `assets/<CONTRACT>/config.json` files
- Reject assets with persistent Sharpe < 0.3

---

## EXPECTED OUTCOMES

**Likely Winners**:
- **MBT (Bitcoin)**: Extreme volatility, clear trends
- **MNG (Natural Gas)**: High intraday volatility
- **MCL (Crude Oil)**: Strong intraday momentum

**Likely Moderate**:
- **MES, MNQ**: Lower volatility than equities (TSLA, NVDA)
- **MGC (Gold)**: Steady trends but slower

**Likely Strugglers**:
- **Currencies**: Typically range-bound on hourly timeframes
- **M2K, MYM**: Lower volatility indices

---

## KEY ADVANTAGES FOR FUTURES

1. **24-Hour Trading**: Captures overnight moves that equity strategies miss
2. **Lower Friction**: No pattern day trader rules, lower commissions
3. **Leverage**: Built-in leverage allows smaller capital deployment
4. **No Gaps**: Continuous trading reduces gap risk

---

## FILE OUTPUTS

```
tests/futures/
├── README.md                          # This file
├── run_futures_hourly.py              # Main test script
├── futures_hourly_results.csv         # Raw results
├── FUTURES_HOURLY_VALIDATION.md       # Summary findings
└── tuning/
    ├── run_volatility_tuning.py       # Band width optimization
    └── volatility_tuning_results.csv
```

---

## FRICTION ASSUMPTIONS

| Cost Type | Futures (Hourly) | Equities (Hourly) |
|-----------|------------------|-------------------|
| Commission | $0.50/contract | $0.00 |
| Spread | 1-2 ticks | 2-5 bps |
| Slippage | 1-2 ticks | 3-5 bps |
| **Total** | ~8-10 bps | ~5-8 bps |

**Conservative Estimate**: 10 bps per round-turn trade.

---

## DEPLOYMENT CRITERIA

For a futures contract to be approved:

1. **Sharpe > 1.0** (Higher bar due to leverage and 24-hour risk)
2. **Max DD < 25%**
3. **Trade frequency**: 15-40 trades/year (avoid under/over-trading)
4. **Consistent** across 2024 and 2025
5. **No single catastrophic loss** (>20%)

---

## SPECIAL CONSIDERATIONS

### 24-Hour Trading Risk
- Futures can gap on **news events** outside RTH (regular trading hours)
- **Mitigation**: Use wider stops for overnight holds
- **Alternative**: Close positions before major scheduled events (FOMC, CPI, etc.)

### Rollover Management
- Futures contracts expire quarterly
- **Solution**: Use continuous contracts or roll at 5-10 days before expiry
- **Cost**: ~2-5 bps per roll (minimal)

---

## NEXT STEPS

1. Implement futures data source (Polygon.io recommended)
2. Create `run_futures_hourly.py`
3. Test **Tier 1 high-volatility assets first** (MBT, MNG, MCL)
4. Generate `FUTURES_HOURLY_VALIDATION.md`
5. For approved contracts, create asset configs

---

**Expected Winners**: 3-5 contracts  
**Expected Sharpe Leaders**: MBT (Bitcoin), MCL (Crude Oil)  
**Expected Failures**: Currencies (range-bound), low-vol indices
