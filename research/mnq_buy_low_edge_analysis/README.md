# MNQ Edge Analysis Research

**Location:** `a:\1\Magellan\research\mnq_buy_low_edge_analysis`  
**Asset:** MNQ (Micro E-mini Nasdaq-100 Futures)  
**Date:** 2026-01-30  
**Branch:** `ptgdb/midas_backtest`

---

## Project Overview

This research project discovers and validates high-probability entry setups for MNQ futures using a systematic quantitative approach:

1. **Discovery** - Identify "Golden Trades" (high reward, low risk) via inverse analysis
2. **Rule Extraction** - Use Decision Tree ML to find precise entry conditions
3. **Backtest** - Validate with full equity curve simulation

---

## Key Results: MIDAS Protocol

| Metric | Value |
|--------|-------|
| **Starting Capital** | $5,000 |
| **Final Equity** | **$1,679,065** |
| **Total P&L** | **$1,674,065** |
| **Total Return** | **33,481%** |
| **Win Rate** | **90.2%** |
| **Sharpe Ratio** | **19.98** |
| **Max Drawdown** | -$4,133 (-0.2%) |
| **Total Trades** | 24,436 (over 5 years) |

---

## Folder Structure

```
mnq_buy_low_edge_analysis/
├── 01_discovery/               # Initial edge discovery
│   ├── edge_analysis_buy_low.py
│   ├── inverse_analysis_golden_trades.py
│   ├── INVERSE_ANALYSIS_GOLDEN_TRADES.md
│   ├── EDGE_ANALYSIS_RESULTS.md
│   └── CORRECTED_RESULTS.md
│
├── 02_rule_extraction/         # ML rule extraction (Decision Tree)
│   ├── midas_protocol.py
│   ├── MIDAS_PROTOCOL_RESULTS.md
│   └── 2hr_windows.txt
│
├── 03_backtest/                # Final backtest simulation
│   ├── midas_backtest.py
│   ├── MIDAS_BACKTEST_RESULTS.md
│   ├── midas_equity_curve.png
│   └── midas_trades.csv
│
├── data/                       # Generated data files
│   ├── golden_trades_analysis.csv
│   ├── buy_low_signals_mfe_mae.csv
│   └── edge_analysis_mfe_vs_mae.html
│
└── README.md                   # This file
```

---

## Strategy: MIDAS Protocol

### Trading Window
02:00 - 06:00 UTC (9pm - 1am US Eastern)

### Entry Setups

**Setup #1: Crash Reversal (60.4% win rate)**
```python
Velocity_5m <= -67 AND
Dist_EMA200 <= 220 AND
ATR_Ratio > 0.50
```

**Setup #2: Quiet Mean Reversion (57.7% win rate)**
```python
Velocity_5m <= 10 AND
Dist_EMA200 <= 220 AND
0.06 < ATR_Ratio <= 0.50
```

### Execution Rules
- Take Profit: +40 points ($80 per contract)
- Stop Loss: -12 points ($24 per contract)
- Position Size: 1 contract

---

## Data Source

All analyses use the full MNQ dataset:
```
a:\1\Magellan\data\cache\futures\MNQ\glbx-mdp3-20210129-20260128.ohlcv-1m.csv
```

| Metric | Value |
|--------|-------|
| **Total Rows** | 2,813,783 |
| **Date Range** | 2021-01-29 to 2026-01-28 |
| **Resolution** | 1-minute |
| **Source** | Databento (glbx-mdp3) |

---

## Usage

### Run Discovery Analysis
```bash
cd a:\1\Magellan\data\cache\futures
python a:\1\Magellan\research\mnq_buy_low_edge_analysis\01_discovery\inverse_analysis_golden_trades.py
```

### Run Rule Extraction
```bash
python a:\1\Magellan\research\mnq_buy_low_edge_analysis\02_rule_extraction\midas_protocol.py
```

### Run Backtest
```bash
python a:\1\Magellan\research\mnq_buy_low_edge_analysis\03_backtest\midas_backtest.py
```

---

## Requirements

- pandas
- numpy
- scikit-learn
- matplotlib
- plotly

---

*Magellan Quantitative Research*
