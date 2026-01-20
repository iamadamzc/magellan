# FOMC EVENT STRADDLES: Futures Adaptation

**Date**: 2026-01-16  
**Version**: 1.0  
**Asset Class**: Micro Futures (CME) - FOMC Event-Driven

---

## PURPOSE

Adapt the validated FOMC Event Straddles strategy from SPY options to **futures contracts** that react strongly to Federal Reserve announcements. The core hypothesis is that FOMC-driven volatility creates tradeable opportunities in index futures, commodity futures, and currency futures.

---

## STRATEGY ADAPTATION FOR FUTURES

### Original Strategy (SPY Options)
- **Entry**: T-5 minutes (1:55 PM ET) before FOMC
- **Position**: Buy ATM straddle (Call + Put)
- **Exit**: T+5 minutes (2:05 PM ET) after announcement
- **Hold**: 10 minutes
- **Results**: 100% win rate, 12.84% avg return per event, Sharpe 1.17

### Futures Adaptation
Since futures don't have options straddles (or they're less liquid), we test **directional breakout** strategies on the FOMC event itself:

**Method 1: Volatility Breakout (Primary)**
- **Entry**: At 2:00 PM (FOMC announcement time), wait for initial move
- **Position**: Go long if futures spike >0.1% in first 2 minutes, short if drop >0.1%
- **Exit**: T+10 minutes (2:10 PM) - same 10-minute hold window
- **Target**: Capture the continuation of initial volatility spike

**Method 2: Mean Reversion (Alternative)**
- **Entry**: At T+3 minutes (2:03 PM), after initial spike
- **Position**: Fade the move (short if spiked up, long if dropped)
- **Exit**: T+10 minutes (2:10 PM)
- **Target**: Capture the post-announcement reversal

---

## ASSET UNIVERSE

### Tier 1: High-Probability Candidates (FOMC-Sensitive)

**Equity Indices** - Direct SPY correlation
- **MES** - Micro E-mini S&P 500 (Primary)
- **MNQ** - Micro E-mini Nasdaq 100
- **MYM** - Micro E-mini Dow
- **M2K** - Micro E-mini Russell 2000

**Currencies** - Fed policy directly affects USD strength
- **M6E** - Micro EUR/USD
- **M6B** - Micro GBP/USD
- **M6A** - Micro AUD/USD

### Tier 2: Moderate Probability (Interest Rate Sensitive)

**Commodities**
- **MGC** - Micro Gold (inverse USD correlation)
- **MSI** - Micro Silver (follows gold)

### Tier 3: Low Probability (Less FOMC-Sensitive)

**Commodities**
- **MCL** - Micro Crude Oil (OPEC-driven, not Fed-driven)
- **MNG** - Micro Natural Gas (supply/demand driven)
- **MCP** - Micro Copper (China-driven)

**Crypto**
- **MBT** - Micro Bitcoin (crypto, but risk-off/risk-on sensitive)

---

## TESTING PROTOCOL

### Phase 1: Historical Event Study (2024)
Test all 8 FOMC events from 2024 on each futures contract:

**FOMC Dates**:
- Jan 31, 2024
- Mar 20, 2024
- May 01, 2024
- Jun 12, 2024
- Jul 31, 2024
- Sep 18, 2024 (Fed Pivot)
- Nov 07, 2024
- Dec 18, 2024

**Data Requirements**:
- 1-minute bars for each contract
- Window: 1:50 PM - 2:15 PM ET (25-minute window around event)

**Metrics**:
- Win rate across 8 events
- Average return per event
- Sharpe ratio
- Best/worst event

### Phase 2: Method Comparison
Compare both methods (Volatility Breakout vs Mean Reversion) for each contract:

| Contract | Breakout Win% | Breakout Avg | Reversion Win% | Reversion Avg | Winner |
|----------|---------------|--------------|----------------|---------------|--------|
| MES      | ?             | ?            | ?              | ?             | ?      |
| MNQ      | ?             | ?            | ?              | ?             | ?      |
| ...      | ...           | ...          | ...            | ...           | ...    |

### Phase 3: Portfolio Construction
- Select top 3-5 contracts with Win Rate >70% and Avg Return >5% per event
- Create asset-specific configs for deployment
- Document optimal entry/exit timing for each

---

## SUCCESS CRITERIA

For a futures contract to be approved:

1. **Win Rate ≥ 70%** (at least 6/8 wins in 2024)
2. **Average Return ≥ 8%** per event
3. **Sharpe Ratio ≥ 1.0** 
4. **Consistent** across "boring" and "volatile" FOMC events
5. **No catastrophic losses** (max single-event loss <15%)

**Expected Pass Rate**: 3-5 contracts out of 13

---

## KEY INSIGHTS

### Why This Might Work
- FOMC creates **guaranteed volatility** across all financial markets
- Futures are **highly liquid** during market hours (tight spreads)
- Futures trade **24 hours**, so no pre-market data issues like CPI/NFP
- **Lower friction** than options (no theta decay, lower commissions)

### Why This Might Fail
- Futures are **directional** (no straddle hedge like options)
- **Whipsaw risk**: Initial spike may reverse immediately
- **Lower leverage** than options (can't get 30%+ returns from 0.5% SPY move)

### Mitigation
- Test **both** breakout and mean reversion to find best structural fit
- Use **Tier 1 assets first** (highest FOMC sensitivity)
- Require **70%+ win rate** vs 100% for options (acknowledge directional risk)

---

## FILE STRUCTURE

```
tests/futures/
├── README.md                          # This file
├── run_fomc_futures_backtest.py       # Main test script
├── fomc_futures_results.csv           # Raw event-by-event results
├── FOMC_FUTURES_VALIDATION.md         # Summary findings
├── method_comparison.csv              # Breakout vs Reversion
└── assets/                            # Configs for approved contracts
    ├── MES/
    │   └── config.json
    └── ...
```

---

## IMPLEMENTATION NOTES

### Data Sources
- **Alpaca**: May not have futures (check docs)
- **FMP**: No futures data
- **Alternative**: Use **Polygon.io** for futures (has CME data)
- **Fallback**: Use **/ES**, **/NQ** (full-size E-mini) as proxy and scale results

### Execution Considerations
- Futures hours: 6:00 PM ET (Sunday) - 5:00 PM ET (Friday with daily break)
- FOMC is at 2:00 PM ET (intraday, during RTH)
- **Commissions**: ~$0.50/contract (2× for round-turn = $1.00 total)
- **Spread**: 1-2 ticks on micro contracts

---

## NEXT STEPS

1. **Check data availability** for micro futures (Alpaca, Polygon)
2. Create `run_fomc_futures_backtest.py`
3. Run on **Tier 1 assets first** (MES, MNQ, M6E)
4. Generate `FOMC_FUTURES_VALIDATION.md` with findings
5. If promising (≥2 contracts pass), create asset configs and deploy

---

## EXPECTED TIMELINE

- **Data check**: 15 minutes
- **Script development**: 2 hours
- **Testing**: 1 hour
- **Analysis**: 1 hour
- **Documentation**: 30 minutes

**Total**: ~5 hours for complete validation

---

**Status**: Ready for implementation  
**Priority**: High (FOMC is proven edge on SPY, futures version is natural extension)  
**Risk**: Medium (directional vs straddle introduces new risk profile)
