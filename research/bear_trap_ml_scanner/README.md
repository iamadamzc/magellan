# Bear Trap ML Scanner - Research Project

**Objective**: Build a data-driven ML-enhanced scanner for dynamic Bear Trap opportunity discovery

## Project Overview

This research project aims to enhance the Bear Trap strategy by:
1. **Dynamic Symbol Discovery**: Replace static 21-symbol watchlist with real-time market scanning
2. **ML-Enhanced Classification**: Predict reversal probability to filter death spirals
3. **Confidence-Based Risk**: Dynamic position sizing and hold times based on ML confidence
4. **Hold Time Optimization**: Validate and optimize the 30-minute rule

## Project Structure

```
research/bear_trap_ml_scanner/
├── data_collection/     # Historical data fetching & feature extraction
├── analysis/            # EDA, feature analysis, validation studies
├── models/              # ML model training & evaluation
├── scanner/             # Real-time scanner implementation
├── backtesting/         # Performance validation
└── data/                # Raw & processed datasets
```

## Data Sources

- **Alpaca Market Data Plus**: Intraday bars, fundamentals, streaming
- **FMP Ultimate**: News, fundamentals, short interest, sector data
- **Historical Scope**: 2021-2025 (4-5 years)

## Feature Set (35 features)

Categories: Price Context, Volume Analysis, Selloff Characteristics, Market Context, News & Catalysts, Fundamental Health, Historical Behavior

## ML Architecture

- **Tier 2**: Reversal Classifier (XGBoost)
- **Tier 4**: Risk Allocator (confidence-based position sizing)

## Timeline

- Weeks 1-2: Data collection & EDA
- Weeks 3-4: ML model development  
- Week 5: Scanner integration
- Week 6: Backtesting & validation

---

**Branch**: `research/bear-trap-ml-scanner`  
**Created**: January 21, 2026  
**Status**: Initial setup
