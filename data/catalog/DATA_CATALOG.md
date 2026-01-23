# Magellan Data Catalog
> Central repository for all market data, training datasets, and analytical assets

## 📁 Directory Structure

```
data/
├── catalog.json              # Master index of all datasets
├── catalog/
│   └── DATA_CATALOG.md       # This file - human-readable catalog
│
├── market_events/            # Labeled Market Event Datasets
│   ├── intraday_selloffs/
│   │   ├── v1_smallcap_10pct_5yr/
│   │   │   ├── MANIFEST.json
│   │   │   ├── dataset_a_validated_symbols.csv
│   │   │   ├── dataset_b_random_symbols.csv
│   │   │   └── combined_with_features.csv
│   │   └── v0_pilot_15pct_3yr/
│   │       └── ...
│   │
│   ├── gap_events/
│   ├── earnings_moves/
│   └── reversal_patterns/
│
├── market_data_cache/        # Raw Market Data (for reuse)
│   ├── daily_bars/
│   ├── minute_bars/
│   └── fundamentals/
│
├── strategy_outputs/         # Strategy Backtest Results
│   ├── bear_trap/
│   ├── daily_trend/
│   └── hourly_swing/
│
└── ml_artifacts/             # Trained Models & Validation
    ├── models/
    ├── predictions/
    └── validation_splits/
```

---

## 📊 Dataset Registry

### 📉 Intraday Selloff Events

| Dataset ID | Version | Events | Symbols | Date Range | Threshold | Features | Status |
|------------|---------|--------|---------|------------|-----------|----------|--------|
| `selloff-smallcap-10pct-5yr-v1` | 1.0 | 8,999 | 250 | 2020-2024 | -10% | 20+ | ✅ Active |
| `selloff-pilot-15pct-3yr-v0` | 0.1 | 495 | 57 | 2022-2024 | -15% | 20+ | 🔒 Archived |

#### selloff-smallcap-10pct-5yr-v1 (Active)

**Description**: Comprehensive dataset of intraday selloff events where small/mid-cap stocks dropped ≥10% from session open, deduplicated to first-cross only.

**Metadata**:
- **Created**: 2026-01-22
- **Source**: Alpaca Market Data Plus (SIP feed, 1-minute bars)
- **Event Definition**: First 1-minute bar where `low` crosses -10% from session open
- **Deduplication**: One event per symbol per trading day (first-cross only)
- **Symbol Universe**: 250 volatile small/mid-cap stocks across sectors
- **Location**: `market_events/intraday_selloffs/v1_smallcap_10pct_5yr/`

**Dataset Splits**:
- **Dataset A (Validated Symbols)**: 5,517 events from 125 historically volatile symbols
- **Dataset B (Random Sample)**: 3,482 events from 125 randomly selected symbols
- **Purpose**: A/B testing for model generalization

**Features** (20+):
- Price context: 52w high/low, distance from SMAs (20/50/200)
- Market regime: SPY daily change
- Time features: Hour, minute, time bucket (opening/morning/midday/afternoon/power_hour)
- Event metrics: Drop %, session open, low, close, volume

**Use Cases**:
- Reversal prediction (bounce vs continuation)
- Entry timing optimization
- Risk classification
- Volatility modeling
- Pattern recognition

---

### 📈 Gap Events
*Coming soon*

### 📊 Earnings Moves
*Coming soon*

### 🔄 Reversal Patterns
*Coming soon*

---

## 🏷️ Dataset Manifest Schema

Each dataset folder contains a `MANIFEST.json`:

```json
{
  "id": "selloff-smallcap-10pct-5yr-v1",
  "name": "Small-Cap Intraday Selloffs (-10%, 5-Year)",
  "version": "1.0",
  "created": "2026-01-22T16:00:00Z",
  "category": "intraday_selloffs",
  
  "description": "First-cross intraday selloff events (≥10% drop from open) across 250 small/mid-cap stocks, 2020-2024",
  
  "source": {
    "provider": "Alpaca Market Data Plus",
    "feed": "SIP",
    "timeframe": "1-minute bars",
    "api_version": "2.0"
  },
  
  "event_definition": {
    "trigger": "low crosses -10% from session open",
    "deduplication": "first_cross_per_symbol_per_day",
    "threshold_pct": -10.0
  },
  
  "scope": {
    "symbols": 250,
    "symbol_categories": ["meme_stocks", "ev_tech", "crypto_related", "biotech", "cannabis", "fintech", "gaming"],
    "date_range": ["2020-01-01", "2024-12-31"],
    "trading_days": 1260
  },
  
  "splits": {
    "dataset_a": {
      "events": 5517,
      "symbols": 125,
      "description": "Validated volatile symbols with known selloff history",
      "file": "dataset_a_validated_symbols.csv"
    },
    "dataset_b": {
      "events": 3482,
      "symbols": 125,
      "description": "Random sample for out-of-sample validation",
      "file": "dataset_b_random_symbols.csv"
    }
  },
  
  "features": {
    "count": 20,
    "categories": {
      "price_context": ["pct_from_52w_high", "pct_from_52w_low", "distance_from_20sma", "distance_from_50sma", "distance_from_200sma"],
      "market_regime": ["spy_change_day"],
      "time_features": ["hour", "minute", "minutes_since_open", "time_bucket"],
      "event_metrics": ["drop_pct", "session_open", "low", "close", "volume"]
    },
    "file": "combined_with_features.csv"
  },
  
  "quality": {
    "total_events": 8999,
    "feature_completeness": 0.95,
    "validated": true,
    "validation_date": "2026-01-22"
  },
  
  "lineage": {
    "raw_bars_scanned": 122000000,
    "symbols_scanned": 250,
    "days_scanned": 1260,
    "events_identified": 8999
  }
}
```

---

## 🔄 Data Lineage

```
Raw Alpaca 1-Min Bars
(122M bars across 250 symbols, 5 years)
         │
         ▼
Selloff Event Detection
(Low crosses -10% from session open)
         │
         ▼
First-Cross Deduplication
(One event per symbol per day)
         │
         ├─► Dataset A: Validated Symbols (125) ─► 5,517 events
         └─► Dataset B: Random Symbols (125) ────► 3,482 events
         │
         ▼
Feature Extraction
(Price context, market regime, time features)
         │
         ▼
ML-Ready Dataset
(8,999 events × 20+ features)
```

---

## 📋 Naming Convention

### Dataset IDs
Format: `{event_type}-{universe}-{threshold}-{timespan}-v{version}`

Examples:
- `selloff-smallcap-10pct-5yr-v1` ✅
- `gap-largecap-5pct-3yr-v1`
- `earnings-tech-1day-5yr-v2`
- `reversal-volatile-15pct-2yr-v1`

### File Names
- `dataset_a_{description}.csv` - Primary/validated split
- `dataset_b_{description}.csv` - Secondary/test split
- `combined_with_features.csv` - Full dataset with all features
- `MANIFEST.json` - Dataset metadata

---

## 🔐 Access Patterns

| Use Case | Dataset | Load Command |
|----------|---------|--------------|
| Train reversal classifier | `selloff-smallcap-10pct-5yr-v1` | `pd.read_csv('data/market_events/intraday_selloffs/v1_smallcap_10pct_5yr/combined_with_features.csv')` |
| Out-of-sample validation | Dataset B split | `df[df['dataset'] == 'dataset_b']` |
| Quick prototyping | `selloff-pilot-15pct-3yr-v0` | (archived) |

---

## 📈 Usage Log

| Dataset | Created | Last Accessed | Models Trained | Production Use |
|---------|---------|---------------|----------------|----------------|
| `selloff-smallcap-10pct-5yr-v1` | 2026-01-22 | 2026-01-22 | 0 | No |
| `selloff-pilot-15pct-3yr-v0` | 2026-01-21 | 2026-01-22 | 0 | No |

---

*Last Updated: 2026-01-22*
