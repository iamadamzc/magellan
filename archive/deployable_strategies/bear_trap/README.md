# Bear Trap Strategy - Deployment Package

**Status:** ✅ APPROVED FOR DEPLOYMENT  
**Version:** 1.0 (Baseline)  
**Last Updated:** 2026-01-20

---

## Quick Start

### **Deployment Status**
- **Strategy:** Bear Trap (Baseline, No ML)
- **Symbols:** MULN, ONDS, AMC, NKLA, WKHS (Tier 1)
- **Capital:** $100k (phased deployment)
- **Next Step:** Begin paper trading

### **Performance Summary**
- **4-Year Return:** +135.6% (2022-2025)
- **Profitable Symbols:** 8/9 (89%)
- **Cross-Validation:** Perfect (9/9 folds)
- **Sharpe Ratios:** 1.74 - 4.35 (Tier 1)

---

## Files in This Directory

### **Core Strategy Files**
1. **`bear_trap_strategy.py`** - Production strategy code
   - Entry: Stock down ≥15%, reclaim candle at session low
   - Exit: Multi-stage (40% mid, 30% HOD, 30% trail)
   - Position sizing: 2% risk per trade, $50k max
   - Risk gates: 10% daily loss limit, 10 trades/day max

2. **`parameters_bear_trap.md`** - Complete parameter specification
   - All strategy parameters documented
   - Entry/exit logic detailed
   - Risk management rules
   - Performance metrics from 4-year validation

### **Deployment Documentation**
3. **`VALIDATION_SUMMARY.md`** - Complete validation results
   - Test suite results
   - Tier 1 symbol performance
   - ML enhancement analysis
   - Risk assessment

4. **`DEPLOYMENT_DECISION.md`** - Deployment rationale
   - Why baseline (no ML)
   - Phased rollout plan
   - Risk management strategy

5. **`DEPLOYMENT_CHECKLIST.md`** - Step-by-step deployment guide
   - Pre-deployment checklist
   - Phase 1: Paper trading (2 weeks)
   - Phase 2: Live pilot (4 weeks)
   - Phase 3: Full deployment

6. **`BEAR_TRAP_DEPLOYMENT_GUIDE.md`** - Original deployment guide
   - Historical validation results
   - Symbol categorization
   - Troubleshooting guide

---

## Strategy Parameters (Quick Reference)

### **Entry Criteria**
```python
{
    'MIN_DAY_CHANGE_PCT': 15.0,        # Stock down ≥15%
    'RECLAIM_WICK_RATIO_MIN': 0.15,    # Quality reclaim candle
    'RECLAIM_VOL_MULT': 0.2,           # Volume confirmation
    'RECLAIM_BODY_RATIO_MIN': 0.2,     # Conviction filter
}
```

### **Exit Rules**
```python
{
    'STOP_ATR_MULTIPLIER': 0.45,       # Tight stop (0.45x ATR)
    'SCALE_TP1_PCT': 40,               # 40% at mid-range
    'SCALE_TP2_PCT': 30,               # 30% at HOD
    'RUNNER_PCT': 30,                  # 30% trail
    'MAX_HOLD_MINUTES': 30,            # 30-min max hold
}
```

### **Risk Management**
```python
{
    'PER_TRADE_RISK_PCT': 0.02,        # 2% risk per trade
    'MAX_POSITION_DOLLARS': 50000,     # $50k max position
    'MAX_DAILY_LOSS_PCT': 0.10,        # 10% daily loss limit
    'MAX_TRADES_PER_DAY': 10,          # 10 trades/day max
}
```

---

## Tier 1 Deployment Symbols

| Symbol | 4-Year PnL | Trades | Win Rate | Sharpe | Status |
|--------|-----------|--------|----------|--------|--------|
| MULN | +30.0% | 588 | 43.4% | 1.74 | ✅ Deploy |
| ONDS | +25.9% | 61 | 52.5% | 4.35 | ✅ Deploy |
| AMC | +18.1% | 153 | 47.7% | 2.89 | ✅ Deploy |
| NKLA | +19.4% | 140 | 42.9% | 1.75 | ✅ Deploy |
| WKHS | +20.1% | 73 | 45.2% | 2.05 | ✅ Deploy |

---

## Deployment Phases

### **Phase 1: Paper Trading (2 Weeks)**
- **Goal:** Validate execution and confirm backtest alignment
- **Symbols:** All Tier 1 (MULN, ONDS, AMC, NKLA, WKHS)
- **Capital:** Virtual $100k
- **Checklist:** See `DEPLOYMENT_CHECKLIST.md`

### **Phase 2: Live Pilot (4 Weeks)**
- **Goal:** Prove profitability with real money
- **Symbols:** Top 3 (MULN, ONDS, AMC)
- **Capital:** $25k (25% allocation)
- **Success Criteria:** Positive P&L, drawdown <15%, win rate >40%

### **Phase 3: Full Deployment**
- **Goal:** Scale to full allocation
- **Symbols:** All Tier 1
- **Capital:** $100k
- **Monitoring:** Daily P&L, weekly reviews, monthly evaluation

---

## Risk Management

### **Hard Stops**
- Daily loss limit: -$10,000 (10%)
- Max trades per day: 10
- Max position size: $50,000
- Max spread: 2%
- Min liquidity: 50 shares bid/ask

### **Emergency Procedures**
**Stop trading if:**
- Daily loss exceeds $10,000
- 3 consecutive losing days
- Win rate drops below 30% for 2 weeks
- Max drawdown exceeds 20%
- Execution issues or system failures

---

## Usage

### **Running a Backtest**
```python
from deployable_strategies.bear_trap.bear_trap_strategy import run_bear_trap

result = run_bear_trap(
    symbol='MULN',
    start='2024-01-01',
    end='2024-12-31',
    initial_capital=100000
)

print(f"Total PnL: {result['total_pnl_pct']:.2f}%")
print(f"Total Trades: {result['total_trades']}")
print(f"Win Rate: {result['win_rate']:.1f}%")
```

### **Validation Reports Location**
- Cross-Validation: `research/testing/wfa/bear_trap/01-19-2026/CROSS_VALIDATION_REPORT.md`
- Baseline vs ML: `research/testing/backtests/bear_trap/01-19-2026/BASELINE_ML_COMPARISON_REPORT.md`
- Monte Carlo: `research/testing/backtests/bear_trap/01-19-2026/MONTE_CARLO_REPORT.md`

---

## ML Enhancement (Not Deployed)

**Decision:** ML enhancement NOT included in initial deployment

**Reasons:**
- Not integrated into production code
- Only +12% improvement vs +166% expected
- Baseline already strong (+135.6%)
- Reduced complexity

**Can revisit:** In 6 months if baseline underperforms

---

## Support & Troubleshooting

### **Common Issues**
1. **No trades generated:** Check if symbols meet -15% day change criteria
2. **Execution errors:** Verify data cache is populated
3. **Unexpected losses:** Review risk limits and position sizing

### **Documentation**
- Full parameters: `parameters_bear_trap.md`
- Deployment guide: `BEAR_TRAP_DEPLOYMENT_GUIDE.md`
- Validation summary: `VALIDATION_SUMMARY.md`

---

## Version History

### **v1.0 (2026-01-20)** - Initial Deployment
- Baseline strategy validated over 4 years
- Tier 1 symbols: MULN, ONDS, AMC, NKLA, WKHS
- Status: APPROVED for paper trading
- ML enhancement deferred

---

## Contact & Approval

**Validated:** 2026-01-20  
**Branch:** `feature/bear-trap-validation-suite`  
**Status:** ✅ Ready for Paper Trading

**Next Step:** Begin Phase 1 (Paper Trading) - See `DEPLOYMENT_CHECKLIST.md`
