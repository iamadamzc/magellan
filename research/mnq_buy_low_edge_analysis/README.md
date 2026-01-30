# MNQ "Buy Low" Scalping - Edge Analysis (MFE vs MAE)

## Overview

This directory contains a complete edge analysis for a "Buy Low" scalping entry strategy on MNQ (Micro E-mini Nasdaq-100) futures.

**Objective:** Determine if price "snaps back" after hitting extreme lows (measured using MFE vs MAE analysis)

**Date:** 2026-01-30  
**Analyst Role:** Quantitative Data Scientist  
**Data:** 5 years of 1-minute MNQ data (2021-2026) from Databento

---

## Files

### 1. `edge_analysis_buy_low.py`
**Main analysis script** - Complete implementation of the edge analysis pipeline:
- Loads and cleans Databento CSV data
- Filters to US market hours (09:30-16:00 ET)
- Generates "Buy Low" signals (Floor + Stretch conditions)
- Calculates MFE and MAE for 15-bar forward window
- Produces interactive Plotly visualization
- Exports results to CSV

**To run:**
```bash
cd a:\1\Magellan\data\cache\futures\MNQ
python ../../../research/mnq_buy_low_edge_analysis/edge_analysis_buy_low.py
```

**Requirements:**
- pandas
- numpy
- plotly
- pytz

**Outputs:**
- `edge_analysis_mfe_vs_mae.html` - Interactive scatter plot
- `buy_low_signals_mfe_mae.csv` - Raw signal data

### 2. `EDGE_ANALYSIS_RESULTS.md`
**Comprehensive results summary** with:
- Strategy logic explanation
- Key findings (87.33% win rate!)
- Edge metrics (MFE/MAE statistics)
- Interpretation and strategic insights
- Next steps for deployment

### 3. `show_results.py`
**Quick results viewer** - Simple script to display summary statistics from the CSV output

---

## Strategy Logic

### Entry Signal: "Buy Low"
Buy when **BOTH** conditions are met:

1. **The Floor**: `Low == Rolling_Min(Low, 30)`
   - Price touches 30-period rolling minimum

2. **The Stretch**: `Close < (EMA_20 - 2.5 * ATR_14)`
   - Price below Lower Keltner Channel

### Edge Metrics

- **MFE (Maximum Favorable Excursion):** Peak profit potential in next 15 bars
- **MAE (Maximum Adverse Excursion):** Peak drawdown in next 15 bars

---

## Key Results

| Metric | Value |
|--------|-------|
| **Total Signals** | 3,047 |
| **Win Rate (MFE > 2x MAE)** | **87.33%** |
| **Positive MFE Rate** | 100.00% |
| **Avg MFE** | 14,131.81 pts ($28,263.62) |
| **Avg MAE** | 216.57 pts ($433.14) |
| **Avg Risk:Reward** | 83,522x (points) |

**Conclusion:** The price **DOES** snap back after the signal with high consistency.

---

## Data Location

The analysis **requires** the file:
```
a:\1\Magellan\data\cache\futures\MNQ\glbx-mdp3-20210129-20260128.ohlcv-1m.csv
```

This file is **NOT** included in version control (it's in `.gitignore`).

---

## Usage Notes

1. **This is ONLY entry analysis** - No exit logic is defined
2. **Position sizing required** - Average MAE of $433 per contract
3. **Execution friction** - Slippage and commissions not accounted for
4. **Next steps:** Add exit rules, regime filters, and walk-forward validation

---

## Branch

This analysis was completed on branch: `ptgdb/data_analysis`

---

## Contact

For questions or to extend this analysis, contact the Quantitative Research Team.
