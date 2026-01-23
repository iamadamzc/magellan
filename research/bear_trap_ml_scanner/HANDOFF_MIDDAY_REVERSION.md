# Midday Reversion Strategy - Full Quant Testing Handoff

> **For**: Next Agent / Quant Analyst
> **Project**: Bear Trap ML Scanner Research
> **Created**: January 22, 2026
> **Priority**: HIGH - Ready for full quantitative validation

---

## 🎯 Executive Summary

We have identified a **high-probability mean reversion opportunity** in small-cap intraday selloffs. The "Midday Reversion" strategy shows a **59.8% win rate** on 60-minute reversals, with 3,514 historical opportunities over 5 years.

**Your task**: Conduct full quantitative validation and prepare for production deployment.

---

## 📊 Strategy Overview

### Core Concept
When a small-cap stock drops ≥10% from session open during **midday hours (11:30 AM - 2:00 PM)**, there is a statistically significant probability (~60%) of a reversal within 60 minutes.

### Key Statistics (from 8,999 events analysis)
| Metric | Value | vs Baseline |
|--------|-------|-------------|
| Events Analyzed | 3,514 | Largest segment |
| 60-min Reversal Rate | **59.8%** | +17.4% above baseline |
| EOD Reversal Rate | 63.1% | -2.9% below baseline |
| Average 60-min Recovery | ~6% | Above baseline |
| Baseline (all selloffs) | 42.4% | Reference |

### Why It Works
1. **Midday = digest period**: Morning momentum exhausted
2. **Not gap-related**: Unlike opening selloffs
3. **Time for recovery**: Full afternoon ahead
4. **Institutional rebalancing**: Midday liquidity

---

## 📁 Data Assets Available

### Primary Dataset Location
```
a:\1\Magellan\data\market_events\intraday_selloffs\v1_smallcap_10pct_5yr\
├── combined_with_outcomes.csv    # FULL DATASET - 8,999 events with outcomes
├── combined_with_features.csv    # Features only (no outcomes)
├── MANIFEST.json                 # Dataset metadata
└── dataset_a_validated.csv       # A/B split
```

### Dataset Schema
```python
# Load the data
import pandas as pd
df = pd.read_csv('data/market_events/intraday_selloffs/v1_smallcap_10pct_5yr/combined_with_outcomes.csv')

# Key columns for Midday Reversion:
FEATURES = [
    'symbol',                   # Stock ticker
    'date',                     # YYYY-MM-DD
    'timestamp',                # Selloff timestamp
    'drop_pct',                 # Drop from session open (-10% to -86%)
    'session_open',             # Session open price
    'low',                      # Selloff low price
    'time_bucket',              # 'opening', 'morning', 'midday', 'afternoon', 'power_hour'
    'minutes_since_open',       # Minutes from 9:30 AM
    'above_200sma',             # 1 = above, 0 = below
    'golden_cross',             # 1 = 50 SMA > 200 SMA
    'pct_from_52w_high',        # Distance from 52-week high
    'spy_change_day',           # SPY daily change %
    'dataset',                  # 'dataset_a' or 'dataset_b'
]

OUTCOMES = [
    'reversed_30min',           # Binary: recovered >50% of drop in 30 min
    'reversed_60min',           # Binary: recovered >50% of drop in 60 min
    'reversed_eod',             # Binary: closed above selloff low
    'recovery_pct_30min',       # % recovery at 30 min
    'recovery_pct_60min',       # % recovery at 60 min
    'recovery_pct_eod',         # % recovery at EOD
    'max_additional_drop',      # Max further drop after selloff
    'time_to_recovery',         # Minutes to first recovery
    'eod_close',                # End of day close price
    'selloff_was_day_low',      # Binary: selloff = day's low
]
```

### Filtering for Midday Reversion
```python
# Filter to Midday bucket only
midday = df[df['time_bucket'] == 'midday'].copy()
print(f"Midday events: {len(midday):,}")  # ~3,514

# Optional: Add SPY up-day filter
midday_tailwind = midday[midday['spy_change_day'] > 0]
```

---

## ✅ Validation Tasks Required

### 1. Walk-Forward Analysis (WFA)
**Objective**: Validate edge is not curve-fitted

```python
# Suggested approach:
# Train: 2020-2022
# Validate: 2023
# Test: 2024

# Split by year
train = df[df['date'] < '2023-01-01']
validate = df[(df['date'] >= '2023-01-01') & (df['date'] < '2024-01-01')]
test = df[df['date'] >= '2024-01-01']

# Compare reversal rates across periods
for name, subset in [('Train', train), ('Validate', validate), ('Test', test)]:
    midday_subset = subset[subset['time_bucket'] == 'midday']
    rate = midday_subset['reversed_60min'].mean() * 100
    print(f"{name}: {rate:.1f}% reversal rate")
```

**Pass Criteria**: Reversal rate > 50% in ALL periods

### 2. A/B Symbol Validation
**Objective**: Confirm edge generalizes to unseen symbols

```python
# Dataset A = validated symbols (trained on)
# Dataset B = random symbols (unseen)
midday_a = midday[midday['dataset'] == 'dataset_a']
midday_b = midday[midday['dataset'] == 'dataset_b']

print(f"Dataset A: {midday_a['reversed_60min'].mean()*100:.1f}%")
print(f"Dataset B: {midday_b['reversed_60min'].mean()*100:.1f}%")
```

**Pass Criteria**: Dataset B rate within 10% of Dataset A

### 3. Entry/Exit Mechanics Backtest
**Objective**: Define tradeable rules and measure realistic P&L

Required parameters to test:
- **Entry**: At selloff detection vs. wait for confirmation
- **Stop Loss**: -X% from entry (test -5%, -10%)
- **Profit Target**: +X% (test +3%, +5%, +7%)
- **Time Stop**: Exit after X minutes if neither hit
- **Position Size**: Fixed or confidence-based

### 4. Risk Metrics
Calculate for final strategy:
- Win rate
- Average win / Average loss
- Profit factor
- Max drawdown
- Sharpe ratio (if possible)
- Sortino ratio

### 5. Stress Testing
- Performance during market crashes (2020, 2022)
- Performance by market regime (bull/bear/sideways)
- Tail risk analysis (worst 5% of trades)

---

## 🔧 Enhancement Opportunities

Based on our analysis, consider adding these filters:

### High-Probability Filters
| Filter | Expected Impact |
|--------|-----------------|
| SPY > 0% (up day) | +5% win rate |
| Above 200 SMA | +3% win rate |
| Not near 52w low | Reduce max loss |
| Exclude clustered (recent selloff) | TBD |

### ML Integration (Optional)
Train XGBoost to predict reversal probability:
```python
# Training code exists at:
# research/bear_trap_ml_scanner/models/  (to be created)

# Features with predictive value:
# - drop_pct
# - minutes_since_open
# - spy_change_day
# - above_200sma
```

---

## 📊 Expected Outcomes

### Conservative Estimate (simple time filter only)
- Win Rate: 55-60%
- Avg Win: +4-5%
- Avg Loss: -5-6%
- Profit Factor: 1.3-1.5

### With Filters (SPY up + trend filters)
- Win Rate: 60-65%
- Avg Win: +5-7%
- Avg Loss: -5-6%
- Profit Factor: 1.5-1.8

---

## 🚀 Deliverables Expected

1. **Walk-Forward Analysis Report**
   - Reversal rates by year
   - Edge stability assessment

2. **Backtest Results**
   - Entry/exit rules tested
   - Risk metrics calculated
   - Parameter sensitivity

3. **Production Recommendation**
   - Final rule set
   - Position sizing recommendation
   - Risk limits

4. **Comparison to Current Bear Trap**
   - Which performs better?
   - Should we replace or run both?

---

## 📎 Related Documentation

- **Strategy Catalog**: `research/bear_trap_ml_scanner/STRATEGY_CATALOG.md`
- **Deep Dive Analysis**: `research/bear_trap_ml_scanner/analysis/DEEP_DIVE_FINDINGS.md`
- **Data Catalog**: `data/catalog/DATA_CATALOG.md`
- **Segment Analysis**: `research/bear_trap_ml_scanner/analysis/SEGMENT_RESULTS.txt`

---

## ⚠️ Known Issues / Considerations

1. **Outcome labeling limitation**: Recovery % calculated from same-day intraday data only
2. **Symbol universe**: Small/mid-cap focus - may not apply to large caps
3. **Execution assumption**: Assumes can enter at selloff detection price
4. **Slippage**: Not modeled - small-caps may have wide spreads

---

## 💬 Questions for Quant Review

1. Is 60% win rate sufficient given expected R:R?
2. Should we split into separate EOD vs. intraday strategies?
3. What's the minimum sample size per year for statistical significance?
4. How should we handle clustered selloffs (same symbol multiple days)?

---

*Handoff created: January 22, 2026*
*Data collection: 10 hours*
*Analysis: 2 hours*
*Ready for Phase 2: Full Quantitative Validation*
