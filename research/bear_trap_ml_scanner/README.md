# Bear Trap ML Scanner Research Project

> **Status**: Phase 1 Complete - Data Collection & Analysis ✅
> **Next**: Phase 2 - Strategy Validation & Scanner Build
> **Created**: January 21-22, 2026

---

## 🎯 Project Summary

This research project collected and analyzed **8,999 intraday selloff events** across 250 symbols over 5 years (2020-2024) to optimize the Bear Trap trading strategy. We discovered significant statistical edges based on **time of day**, **market context**, and **trend positioning**.

### Key Finding
> **Midday selloffs (11:30 AM - 2:00 PM) have a 60% reversal rate within 60 minutes, compared to 42% baseline.**

---

## 📊 Project Outcomes

### Data Assets Created
| Asset | Size | Location |
|-------|------|----------|
| Full Dataset | 8,999 events | `data/market_events/intraday_selloffs/v1_smallcap_10pct_5yr/` |
| With Outcomes | 30+ columns | `combined_with_outcomes.csv` |
| Manifest | Metadata | `MANIFEST.json` |

### Strategies Identified
| Strategy | Win Rate | Events | Priority |
|----------|----------|--------|----------|
| Morning Bear Trap | 65.9% | 350 | 🟢 High |
| **Midday Reversion** | 59.8% | 3,514 | 🟢 **Top** |
| Opening Scalp | 71.4% | 50 | 🟡 Study |
| Power Hour Overnight | 70.7% EOD | 2,125 | 🟡 Secondary |
| Golden Combo | 52.8% | 1,975 | 🟢 Best Filters |

### Current Bear Trap Issue
- Problem: -15% threshold too restrictive (no trades)
- Solution: Lower to -10% + add time filters
- See: `BEAR_TRAP_ASSESSMENT.md`

---

## 📁 Documentation Index

### Handoff Documents
| Document | Purpose |
|----------|---------|
| `HANDOFF_MIDDAY_REVERSION.md` | Full quant testing handoff |
| `HANDOFF_SCANNER_BUILD.md` | Scanner development guide |
| `DATA_USAGE_GUIDE.md` | How to use the dataset |
| `BEAR_TRAP_ASSESSMENT.md` | Current strategy issues |

### Analysis Results
| Document | Purpose |
|----------|---------|
| `STRATEGY_CATALOG.md` | All 8 strategies documented |
| `analysis/DEEP_DIVE_FINDINGS.md` | Statistical insights |
| `analysis/SEGMENT_RESULTS.txt` | Raw segment numbers |

### Data Catalog
| Document | Purpose |
|----------|---------|
| `data/catalog/DATA_CATALOG.md` | Central data registry |
| `data/catalog.json` | Machine-readable catalog |

---

## 🚀 Next Steps

### Priority 1: Validate Midday Reversion
- Walk-forward analysis (2020-22 train, 2023-24 test)
- Define entry/exit mechanics
- Calculate risk metrics
- See: `HANDOFF_MIDDAY_REVERSION.md`

### Priority 2: Fix Current Bear Trap
- Review current configuration
- Lower threshold to -10%
- Add time filter
- See: `BEAR_TRAP_ASSESSMENT.md`

### Priority 3: Build Scanner
- Real-time selloff detection
- Priority scoring
- Integration with strategy
- See: `HANDOFF_SCANNER_BUILD.md`

---

## 📊 Data Collection Summary

### What We Collected
- **8,999 selloff events** (≥10% drop from open)
- **250 volatile small/mid-cap symbols**
- **5 years** (2020-2024)
- **20+ features** per event
- **13 outcome columns** (reversal rates, recovery %)

### Data Quality
- ✅ 99.7% feature completeness
- ✅ 0 duplicate events
- ✅ Proper deduplication (first-cross only)
- ✅ A/B split for validation

---

## 🔧 Technical Resources

### API Keys Required
- `APCA_API_KEY_ID` - Alpaca API
- `APCA_API_SECRET_KEY` - Alpaca Secret
- `FMP_API_KEY` - Financial Modeling Prep (limited use)

### Key Scripts
```
data_collection/
├── collect_resumable.py       # Main data collector
├── extract_outcomes.py        # Add reversal outcomes
├── extract_ultimate_features.py

analysis/
├── comprehensive_eda.py       # Full EDA
├── segment_analysis.py        # Key segment stats
├── deep_dive_analysis.py      # Pattern discovery
```

---

## 📈 Key Statistics Reference

### Reversal Rates by Time
| Time | 60-min | EOD |
|------|--------|-----|
| Opening | 71% | 34% |
| Morning | 66% | 61% |
| **Midday** | **60%** | 63% |
| Afternoon | 38% | 67% |
| Power Hour | 15% | 71% |

### Reversal Rates by Context
| Context | 60-min |
|---------|--------|
| SPY Up Day | 47% |
| SPY Down Day | 39% |
| Above 200 SMA | 44% |
| Golden Cross | 44% |

---

## 💡 Key Insights

1. **Time is the strongest predictor** - Morning/Midday beats baseline by 17-24%
2. **SPY context matters** - Up days = +5% edge
3. **Trend helps but less than timing** - Above 200 SMA = +2-4%
4. **66% of all selloffs reverse by EOD** - Mean reversion is real
5. **Falling knife filter critical** - Below 200 + near lows = highest risk

---

*Project Created: January 21-22, 2026*
*Duration: ~12 hours*
*Status: Ready for Phase 2*
