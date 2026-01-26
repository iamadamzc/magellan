# Data Usage Guide - Intraday Selloff Dataset

> **For**: Any Agent / Analyst
> **Purpose**: Quick reference for using the selloff research data
> **Created**: January 22, 2026

---

## 🎯 Quick Start

### Load the Full Dataset
```python
import pandas as pd

# Primary dataset with all features and outcomes
df = pd.read_csv('data/market_events/intraday_selloffs/v1_smallcap_10pct_5yr/combined_with_outcomes.csv')

print(f"Total events: {len(df):,}")  # 8,999
print(f"Columns: {len(df.columns)}")  # 30+
```

---

## 📁 Data Location

### Primary Data Path
```
a:\1\Magellan\data\market_events\intraday_selloffs\v1_smallcap_10pct_5yr\
```

### Files Available
| File | Contents | Rows |
|------|----------|------|
| `combined_with_outcomes.csv` | **USE THIS** - Full dataset with features + outcomes | 8,999 |
| `combined_with_features.csv` | Features only (no outcomes) | 8,999 |
| `dataset_a_validated_symbols.csv` | Raw Dataset A | 5,517 |
| `dataset_b_random_symbols.csv` | Raw Dataset B | 3,482 |
| `combined_raw.csv` | Original raw collection | 8,999 |
| `MANIFEST.json` | Dataset metadata | - |

### Catalog Reference
- **Data Catalog**: `data/catalog/DATA_CATALOG.md`
- **Schema Details**: `data/catalog.json`

---

## 📊 Dataset Schema

### Identification Columns
| Column | Type | Description |
|--------|------|-------------|
| `symbol` | str | Stock ticker (e.g., 'RIOT', 'MULN') |
| `date` | str | Event date YYYY-MM-DD |
| `timestamp` | str | Exact selloff time |
| `dataset` | str | 'dataset_a' or 'dataset_b' |

### Event Metrics
| Column | Type | Description |
|--------|------|-------------|
| `drop_pct` | float | % drop from session open (always negative) |
| `session_open` | float | Opening price |
| `low` | float | Price at selloff detection |

### Feature Columns (Pre-Selloff Context)
| Column | Type | Description |
|--------|------|-------------|
| `pct_from_52w_high` | float | Distance from 52-week high (%) |
| `pct_from_52w_low` | float | Distance from 52-week low (%) |
| `price_range_position` | float | Position in 52w range (0-1) |
| `distance_from_20sma` | float | % above/below 20-day SMA |
| `distance_from_50sma` | float | % above/below 50-day SMA |
| `distance_from_200sma` | float | % above/below 200-day SMA |
| `above_200sma` | int | 1 = above 200 SMA, 0 = below |
| `golden_cross` | int | 1 = 50 SMA > 200 SMA |
| `spy_change_day` | float | SPY daily change % |
| `hour` | int | Hour of selloff (9-16) |
| `minute` | int | Minute of selloff |
| `minutes_since_open` | int | Minutes from 9:30 AM |
| `time_bucket` | str | 'opening', 'morning', 'midday', 'afternoon', 'power_hour' |

### Outcome Columns (Post-Selloff Recovery)
| Column | Type | Description |
|--------|------|-------------|
| `recovery_pct_30min` | float | % recovery 30 min after selloff |
| `recovery_pct_60min` | float | % recovery 60 min after selloff |
| `recovery_pct_120min` | float | % recovery 120 min after selloff |
| `recovery_pct_eod` | float | % recovery by end of day |
| `reversed_30min` | int | 1 = recovered >50% of drop in 30 min |
| `reversed_60min` | int | 1 = recovered >50% of drop in 60 min |
| `reversed_eod` | int | 1 = closed above selloff low |
| `eod_close` | float | End of day close price |
| `eod_high` | float | Session high |
| `eod_low` | float | Session low |
| `max_additional_drop` | float | Max further drop after selloff (always ≤0) |
| `time_to_recovery` | float | Minutes until first recovery above low |
| `selloff_was_day_low` | int | 1 = selloff was day's lowest point |

---

## 🔍 Common Analysis Patterns

### Filter by Time Bucket
```python
# Midday only (highest volume, good edge)
midday = df[df['time_bucket'] == 'midday']
print(f"Midday events: {len(midday):,}")
print(f"60-min reversal: {midday['reversed_60min'].mean()*100:.1f}%")
```

### Filter by Trend Context
```python
# Uptrend stocks only
uptrend = df[(df['above_200sma'] == 1) & (df['golden_cross'] == 1)]
print(f"Uptrend events: {len(uptrend):,}")
```

### Filter by Market Regime
```python
# Selloffs on up market days
spy_up = df[df['spy_change_day'] > 0.5]
print(f"SPY up day events: {len(spy_up):,}")
```

### Compare Segments
```python
# Easy comparison
for bucket in ['morning', 'midday', 'afternoon', 'power_hour']:
    subset = df[df['time_bucket'] == bucket]
    rate = subset['reversed_60min'].mean() * 100
    print(f"{bucket}: {rate:.1f}% reversal")
```

### Year-Over-Year Analysis
```python
df['year'] = pd.to_datetime(df['date']).dt.year
for year in [2020, 2021, 2022, 2023, 2024]:
    subset = df[df['year'] == year]
    rate = subset['reversed_60min'].mean() * 100
    print(f"{year}: {rate:.1f}% reversal")
```

### A/B Split Analysis
```python
# Validate generalization
for dataset in ['dataset_a', 'dataset_b']:
    subset = df[df['dataset'] == dataset]
    rate = subset['reversed_60min'].mean() * 100
    print(f"{dataset}: {rate:.1f}%")
```

---

## 📈 Key Statistics Reference

### Overall Baseline
| Metric | Value |
|--------|-------|
| Total Events | 8,999 |
| 60-min Reversal Rate | 42.4% |
| EOD Reversal Rate | 66.0% |
| Average 60-min Recovery | 5.8% |

### By Time Bucket
| Bucket | Events | 60-min % | EOD % |
|--------|--------|----------|-------|
| Opening | 50 | 71.4% | 34.0% |
| Morning | 312 | 65.9% | 60.9% |
| Midday | 3,514 | 59.8% | 63.1% |
| Afternoon | 2,998 | 38.0% | 67.3% |
| Power Hour | 2,125 | 15.4% | 70.7% |

---

## 📎 Related Analysis Scripts

```
research/bear_trap_ml_scanner/analysis/
├── comprehensive_eda.py          # Full EDA
├── deep_dive_analysis.py         # Deep patterns
├── segment_analysis.py           # Segment comparisons
├── quick_summary.py              # Quick stats
└── DEEP_DIVE_FINDINGS.md         # Written findings
```

---

## ⚠️ Important Notes

1. **Data is SMALL-CAPS** - MULN, RIOT, MARA, etc., NOT SPY/QQQ
2. **Threshold is -10%** - Selloff = low crosses -10% from open
3. **First-cross only** - One event per symbol per day
4. **Date range**: 2020-01-01 to 2024-12-31
5. **Missing values**: Some features ~90% complete (200 SMA requires history)

---

## 💡 Ideas for Further Analysis

1. **Sector breakdown** - Do crypto stocks behave differently?
2. **Volume analysis** - Is high volume predicitive?
3. **Earnings proximity** - Selloffs near earnings dates?
4. **Catalyst types** - News-driven vs technical breakdown?
5. **Multi-day patterns** - Do Day 2+ reversals differ?

---

*Data Usage Guide Created: January 22, 2026*
*Dataset: selloff-smallcap-10pct-5yr-v1*
