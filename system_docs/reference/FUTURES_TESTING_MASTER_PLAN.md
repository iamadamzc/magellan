# FUTURES TESTING MASTER PLAN

**Date**: 2026-01-16  
**Author**: Quantitative Strategy Team  
**Scope**: Comprehensive futures validation for all Magellan strategies

---

## EXECUTIVE SUMMARY

This document outlines the complete testing protocol for adapting the three validated Magellan trading strategies to the **futures asset class**, specifically targeting **CME Micro Futures** contracts for capital efficiency.

### Strategies Under Test

| Strategy | Equity Performance | Futures Adaptation | Expected Outcome |
|----------|-------------------|-------------------|------------------|
| **Daily Trend Hysteresis** | Sharpe 0.8-1.5 on MAG7/Indices | Direct translation | 4-6 contracts ✅ |
| **Hourly Swing** | Sharpe 1.0+ on NVDA/TSLA/PLTR | Enhanced by 24hr trading | 3-5 contracts ✅ |
| **FOMC Event Straddles** | Sharpe 1.17 on SPY options | Directional breakout version | 2-4 contracts ⚠️ |
| **Earnings Straddles** | — | N/A (futures have no earnings) | ❌ Not applicable |

---

## FUTURES UNIVERSE

### All 13 Micro Futures Contracts (CME)

#### Equity Indices (4)
- **MES** - Micro E-mini S&P 500 ($1.25/tick)
- **MNQ** - Micro E-mini Nasdaq 100 ($0.50/tick)
- **MYM** - Micro E-mini Dow ($0.50/tick)
- **M2K** - Micro E-mini Russell 2000 ($0.50/tick)

#### Commodities (5)
- **MCL** - Micro Crude Oil ($1.00/tick)
- **MGC** - Micro Gold ($1.00/tick)
- **MSI** - Micro Silver ($1.25/tick)
- **MNG** - Micro Natural Gas ($0.125/tick)
- **MCP** - Micro Copper ($1.25/tick)

#### Currencies (3)
- **M6E** - Micro EUR/USD ($1.25/tick)
- **M6B** - Micro GBP/USD ($1.25/tick)
- **M6A** - Micro AUD/USD ($1.00/tick)

####Crypto (1)
- **MBT** - Micro Bitcoin ($0.25/tick, 0.10 BTC multiplier)

---

## DIRECTORY STRUCTURE

```
docs/operations/strategies/
│
├── daily_trend_hysteresis/
│   ├── ...existing files...
│   ├── tests/
│   │   ├── ...existing tests...
│   │   └── futures/                       ⭐ NEW
│   │       ├── README.md                  # Testing guide
│   │       ├── run_futures_baseline.py    # Main backtest
│   │       ├── futures_baseline_results.csv
│   │       ├── FUTURES_VALIDATION_REPORT.md
│   │       └── tuning/
│   │           ├── run_futures_tuning.py
│   │           └── tuning_results.csv
│   └── assets/
│       ├── ...existing equity assets...
│       └── MES/                           ⭐ NEW (example)
│           └── config.json
│
├── hourly_swing/
│   ├── ...existing files...
│   ├── tests/
│   │   └── futures/                       ⭐ NEW
│   │       ├── README.md
│   │       ├── run_futures_hourly.py
│   │       ├── futures_hourly_results.csv
│   │       ├── FUTURES_HOURLY_VALIDATION.md
│   │       └── tuning/
│   │           ├── run_volatility_tuning.py
│   │           └── volatility_tuning_results.csv
│   └── assets/
│       ├── ...existing equity assets...
│       └── MBT/                           ⭐ NEW (example)
│           └── config.json
│
├── fomc_event_straddles/
│   ├── ...existing files...
│   ├── tests/
│   │   └── futures/                       ⭐ NEW
│   │       ├── README.md
│   │       ├── run_fomc_futures_backtest.py
│   │       ├── fomc_futures_results.csv
│   │       ├── FOMC_FUTURES_VALIDATION.md
│   │       └── method_comparison.csv
│   └── assets/
│       └── (TBD based on results)
│
├── earnings_straddles/
│   └── (No futures adaptation - N/A)
│
└── FUTURES_TESTING_MASTER_PLAN.md        ⭐ THIS FILE
```

---

## TESTING PROTOCOL

### Phase 1: Data Infrastructure (Week 1)

**Objective**: Establish futures data pipeline

**Tasks**:
1. ✅ Sign up for **Polygon.io** Starter plan ($99/month)
2. ✅ Implement `PolygonFuturesClient` in `src/data_handler.py`
3. ✅ Test data fetching for all 13 contracts (daily + hourly)
4. ✅ Validate data quality (no gaps, correct timezone handling)

**Deliverables**:
- `src/data_handler.py` updated with futures support
- `tests/data_validation/test_futures_data.py`
- Sample CSV output for MES (proof of concept)

---

### Phase 2: Daily Trend Hysteresis on Futures (Week 2)

**Objective**: Validate RSI hysteresis on daily futures bars

**Tasks**:
1. ✅ Run `daily_trend_hysteresis/tests/futures/run_futures_baseline.py`
2. ✅ Analyze `futures_baseline_results.csv`
3. ✅ Tune parameters for low-Sharpe assets (if 0.3 < Sharpe < 0.7)
4. ✅ Create asset configs for Sharpe > 0.7 contracts
5. ✅ Write `FUTURES_VALIDATION_REPORT.md`

**Success Criteria**:
- At least 4 contracts with Sharpe > 0.7
- At least 2 contracts with Sharpe > 1.0
- No catastrophic failures (Sharpe < -0.5)

**Expected Pass**: MES, MNQ, MGC, MYM

---

### Phase 3: Hourly Swing on Futures (Week 3)

**Objective**: Validate hourly hysteresis on high-volatility futures

**Tasks**:
1. ✅ Run `hourly_swing/tests/futures/run_futures_hourly.py`
2. ✅ Identify high-volatility winners (MBT, MNG, MCL expected)
3. ✅ Test wider bands (65/35, 70/30) for extreme volatility
4. ✅ Create asset configs for Sharpe > 1.0 contracts
5. ✅ Write `FUTURES_HOURLY_VALIDATION.md`

**Success Criteria**:
- At least 3 contracts with Sharpe > 1.0
- MBT (Bitcoin) shows Sharpe > 1.2 (high-volatility flagship)
- Trade frequency: 15-40 trades/year per contract

**Expected Pass**: MBT, MCL, MNG

---

### Phase 4: FOMC Event Straddles on Futures (Week 4)

**Objective**: Test event-driven futures strategies on FOMC announcements

**Tasks**:
1. ✅ Run `fomc_event_straddles/tests/futures/run_fomc_futures_backtest.py`
2. ✅ Compare "Volatility Breakout" vs "Mean Reversion" methods
3. ✅ Test on Tier 1 assets (MES, M6E) first
4. ✅ Create asset configs for Win Rate > 70% contracts
5. ✅ Write `FOMC_FUTURES_VALIDATION.md`

**Success Criteria**:
- At least 2 contracts with Win Rate ≥ 70% (≥6/8 FOMC events)
- Average return ≥ 8% per event
- Sharpe ≥ 1.0

**Expected Pass**: MES, M6E (best FOMC sensitivity)

---

### Phase 5: Portfolio Construction (Week 5)

**Objective**: Build diversified futures portfolio

**Tasks**:
1. ✅ Compile all approved contracts across strategies
2. ✅ Calculate correlation matrix (avoid over-concentration)
3. ✅ Set position sizing rules (max 10% per contract)
4. ✅ Update `config/nodes/master_config.json`
5. ✅ Run `scripts/update_master_config.py` to sync

**Deliverables**:
- `FUTURES_PORTFOLIO_ALLOCATION.md`
- Updated `master_config.json` with futures entries
- Deployment checklist

---

## EXPECTED OUTCOMES

### Conservative Estimate (Minimum Viable Portfolio)

| Strategy | Contracts | Avg Sharpe | Expected Annual Return |
|----------|-----------|------------|------------------------|
| Daily Trend (Futures) | 4-6 | 0.8-1.2 | +30-50% |
| Hourly Swing (Futures) | 3-5 | 1.0-1.5 | +40-70% |
| FOMC Events (Futures) | 2-4 | 1.0-1.3 | +60-100% (8 events) |
| **TOTAL** | **9-15** | **1.0-1.3** | **+50-90%** |

### Optimistic Estimate (Full Pass)

| Strategy | Contracts | Avg Sharpe | Expected Annual Return |
|----------|-----------|------------|------------------------|
| Daily Trend (Futures) | 8-10 | 1.2-1.8 | +50-80% |
| Hourly Swing (Futures) | 6-8 | 1.5-2.0 | +80-120% |
| FOMC Events (Futures) | 4-6 | 1.3-1.7 | +100-150% (8 events) |
| **TOTAL** | **18-24** | **1.3-1.8** | **+90-150%** |

---

## KEY ADVANTAGES OF FUTURES

1. **24-Hour Trading**: Capture overnight moves (especially Asia/Europe sessions)
2. **Lower Capital Requirements**: Micro contracts require $1000-$2000 margin vs $10k+ for equity positions
3. **No PDT Rule**: Unlimited day trades (no pattern day trader restrictions)
4. **Tax Benefits**: 60/40 tax treatment (60% long-term, 40% short-term regardless of hold time)
5. **Leverage Built-In**: 10-20x leverage vs 2x for equities (manage risk carefully)
6. **Deep Liquidity**: Micro futures have tight spreads and high volume

---

## RISK MANAGEMENT

### Position Sizing Rules
- **Max 1-2 contracts** per futures symbol (micro contracts are small, but leverage is high)
- **Max 10% allocation** per contract in portfolio
- **Max 50% total futures exposure** (rest in equities to diversify)

### Overnight Risk
- **22-hour exposure**: Futures trade nearly 24 hours, increasing event risk
- **Mitigation**: 
  - Close positions before scheduled major events (FOMC, CPI if not FOMC strategy)
  - Use wider stops (1.5x equity stops) to account for overnight gaps
  - Monitor margin calls aggressively

### Rollover Management
- **Contract expiry**: Quarterly (Mar, Jun, Sep, Dec)
- **Rollover timing**: 5-10 days before first notice day
- **Cost**: ~2-5 bps per roll

---

## DATA REQUIREMENTS

### Primary Data Source: Polygon.io

**Plan**: Starter ($99/month)
- ✅ Futures historical data (all CME contracts)
- ✅ 1-minute, hourly, daily bars
- ✅ API rate limits: 5 requests/second

**Alternative**: Interactive Brokers
- ✅ Free historical data via API
- ✅ Requires IB account ($0 minimum for paper trading)
- ❌ More complex API (use `ib_insync` wrapper)

### Data Validation Checklist
- [ ] All 13 contracts fetchable (daily + hourly)
- [ ] No missing bars (handle holidays correctly)
- [ ] Timezone: All data in America/New_York (ET)
- [ ] Continuous contracts available (or rollover logic implemented)

---

## TIMELINE

| Week | Focus | Deliverables |
|------|-------|--------------|
| 1 | Data Infrastructure | Polygon client, data validation |
| 2 | Daily Trend Futures | Baseline results, configs |
| 3 | Hourly Swing Futures | Volatility tuning, configs |
| 4 | FOMC Event Futures | Method comparison, configs |
| 5 | Portfolio Construction | Master config, deployment plan |

**Total**: 5 weeks to full futures portfolio validation

---

## SUCCESS METRICS

### After Week 5:
- [ ] ≥10 futures contracts approved across strategies
- [ ] Portfolio Sharpe ≥ 1.0 (combined futures + equities)
- [ ] All asset configs created and synced to `master_config.json`
- [ ] Paper trading deployment checklist complete

### After 3 Months Paper Trading:
- [ ] Live Sharpe within 20% of backtest Sharpe
- [ ] No execution failures (missed entries/exits)
- [ ] Margin management process validated
- [ ] Rollover process validated

---

## NEXT IMMEDIATE STEPS

1. **[USER ACTION REQUIRED]** Sign up for Polygon.io Starter plan
2. **[DEV]** Implement `PolygonFuturesClient` in `src/data_handler.py`
3. **[TEST]** Run `run_futures_baseline.py` (expect data errors initially)
4. **[ITERATE]** Debug data fetching and retry
5. **[ANALYZE]** Review first results and proceed to tuning

---

**Status**: Ready for Phase 1 (Data Infrastructure)  
**Blocker**: Futures data source (Polygon.io sign-up required)  
**Estimated Completion**: 5 weeks from Phase 1 start
