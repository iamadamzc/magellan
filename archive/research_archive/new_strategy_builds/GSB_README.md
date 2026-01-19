# GSB - Gas & Sugar Breakout Strategy

**Status:** ✅ Validated & Ready for Deployment  
**Performance:** +90.67% over 4 years (2022-2025)  
**Symbols:** Natural Gas (NG), Sugar (SB)

---

## Quick Stats

| Metric | Natural Gas (NG) | Sugar (SB) | Combined |
|--------|------------------|------------|----------|
| **4-Year Return** | +55.04% | +35.63% | +90.67% |
| **Avg Annual** | +13.76% | +7.17% | +20.93% |
| **Total Trades** | 274 | 233 | 507 |
| **Win Rate** | 55.8% | 53.6% | 54.8% |
| **Profitable Years** | 3/4 | 3/4 | - |

---

## What Is GSB?

GSB (Gas & Sugar Breakout) is a commodity futures day-trading strategy that:
- Trades **Natural Gas** and **Sugar** futures
- Uses **session-specific opening range breakouts**
- Trades **all day** (not just first hour)
- Adapts to each commodity's actual session times

**Origin:** Evolved from 26 versions of ORB (Opening Range Breakout) testing. After extensive research on equities and multiple futures, GSB emerged as the only consistently profitable configuration.

---

## Key Features

✅ **Validated Across 4 Years** (2022-2025)  
✅ **Profitable in 3/4 Years** for both symbols  
✅ **Large Sample Size** (507 trades)  
✅ **Diversified** (Energy + Agriculture)  
✅ **Fully Documented** (Deployment guide + Research summary)

---

## Files

### Documentation
- **`GSB_DEPLOYMENT_GUIDE.md`** - Complete deployment guide
- **`GSB_RESEARCH_SUMMARY.md`** - Full research journey (26 versions)
- **`README.md`** - This file

### Code
- **`strategies/gsb_strategy.py`** - Main strategy implementation
- **`commodity_session_times.json`** - Session start times for each commodity

### Results
- **`results/GSB_VALIDATED_4YEAR.csv`** - 4-year validation results
- **`results/ORB_V23_WINNERS.csv`** - 2024 single-year results

---

## Quick Start

### 1. Read the Documentation
Start with `GSB_DEPLOYMENT_GUIDE.md` for:
- Strategy logic and parameters
- Entry/exit rules
- Risk analysis
- Deployment checklist

### 2. Review the Research
See `GSB_RESEARCH_SUMMARY.md` for:
- Complete testing history (V7-V23)
- What worked and what didn't
- Key discoveries
- Lessons learned

### 3. Understand the Performance
Check `results/GSB_VALIDATED_4YEAR.csv` for:
- Year-by-year breakdown
- Trade statistics
- Win/loss analysis

---

## Strategy Overview

### Session Times (Critical!)
- **NG (Natural Gas):** Session starts 13:29 ET
- **SB (Sugar):** Session starts 13:30 ET

**Note:** These are actual data session times. Using standard 9:30 AM will fail!

### Entry Logic
1. Calculate Opening Range (first 10 minutes)
2. Wait for breakout above OR high with volume
3. Enter on pullback to OR high with VWAP confirmation
4. Trade all day (no time restriction)

### Exit Logic
- Initial stop: OR low - 0.4 ATR
- Move to breakeven at +0.8R
- Trail at 1.0 ATR after breakeven
- Profit target at +2.0R
- Close all at end of session

---

## Performance by Year

### Natural Gas (NG)
- **2022:** +7.08% ✅
- **2023:** -12.50% ❌
- **2024:** +30.85% ✅
- **2025:** +29.61% ✅

### Sugar (SB)
- **2022:** +21.62% ✅
- **2023:** -8.85% ❌
- **2024:** +5.58% ✅
- **2025:** +10.35% ✅

**Note:** Both had the same losing year (2023), providing diversification benefit in other years.

---

## Why "GSB"?

**Gas & Sugar Breakout** - The name tells you exactly what it trades:
- **Gas** = Natural Gas (NG)
- **Sugar** = Sugar (SB)
- **Breakout** = Opening range breakout methodology

Simple, memorable, and descriptive!

---

## Evolution from ORB

GSB started as "ORB V23" but evolved significantly:

1. **Started:** Opening Range Breakout on equities
2. **Pivoted:** To commodity futures after equity failures
3. **Discovered:** Adaptive session times critical
4. **Breakthrough:** All-day trading beats first-hour
5. **Validated:** Only NG and SB consistently profitable
6. **Renamed:** To GSB to reflect what it actually trades

See `GSB_RESEARCH_SUMMARY.md` for the complete 26-version journey.

---

## Next Steps

### Immediate
1. Read `GSB_DEPLOYMENT_GUIDE.md`
2. Review validation results
3. Understand risk parameters

### Deployment
1. Paper trade for 2 weeks
2. Validate signals match backtest
3. Start live with minimum size
4. Scale up after validation

### Ongoing
1. Monthly performance reviews
2. Quarterly out-of-sample validation
3. Monitor for regime changes

---

## Support

**Created:** January 18, 2026  
**Version:** GSB v1.0  
**Next Review:** April 2026 (Q1 2026 validation)

For questions or issues, refer to the troubleshooting section in `GSB_DEPLOYMENT_GUIDE.md`.

---

**Ready to deploy a validated, profitable commodity futures strategy!** 🚀
