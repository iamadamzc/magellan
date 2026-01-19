# Magellan CLI Usage Guide

## Quick Reference

### 1. **Backtest (Simulation Mode)** - Default behavior
```bash
# Simplest: Run 15-day stress test on NVDA using defaults
python main.py --symbols NVDA --stress-test-days 15

# Full control: Specific date range, multiple tickers
python main.py --symbols NVDA,AAPL --start-date 2024-01-01 --end-date 2024-12-31

# Quiet mode (less verbose output)
python main.py --symbols NVDA --stress-test-days 30 --quiet
```

### 2. **Live Paper Trading**
```bash
# Run live with MAG7 default tickers
python main.py --mode live

# Run live with specific ticker and position cap
python main.py --mode live --symbols NVDA --max-position-size 10000
```

### 3. **Observation Mode** (Hangar/ORH Analysis)
```bash
python main.py --mode observe
```

---

## Understanding Defaults

### **What happens if you run `python main.py` with NO arguments?**

| Setting | Default Value | Source |
|---------|---------------|--------|
| `--mode` | `simulation` | Hardcoded in argparse |
| `--config` | `src/configs/mag7_default.json` | Fallback logic (line 478) |
| `--symbols` | `["NVDA", "AAPL", ...]` MAG7 | Loaded from `master_config.json` |
| `--stress-test-days` | `0` (disabled) | Hardcoded in argparse |
| `--data-source` | `FMP` | Hardcoded in argparse |
| `--max-position-size` | `None` (uses config value) | Hardcoded in argparse |

**Result**: Runs a simulation on all MAG7 tickers without stress testing.

---

## Command-Line Arguments Reference

### Core Execution Modes

#### `--mode` (Default: `simulation`)
**Choices**: `simulation`, `live`, `observe`

- **`simulation`**: Backtest mode - processes historical data, no real trades
- **`live`**: Paper trading mode - submits real orders to Alpaca Paper account
- **`observe`**: ORH (Opening Range High) analysis mode

**Example**:
```bash
python main.py --mode live
```

---

### Ticker Selection

#### `--symbols` (Default: MAG7 from config)
**Format**: Comma-separated list (no spaces around commas)

**Overrides** the default ticker list from `master_config.json`

**Examples**:
```bash
# Single ticker
python main.py --symbols NVDA

# Multiple tickers
python main.py --symbols NVDA,AAPL,MSFT

# Note: Tickers must be in MAG7_UNIVERSE or will be skipped (validation at line 578)
```

**What it does**:
1. Splits on `,` → `['NVDA', 'AAPL', 'MSFT']`
2. Adds to MAG7 allowlist (line 572)
3. Processes each ticker in loop (line 576)

---

### Backtest Time Range (3 ways to specify)

#### **Option 1: Stress Test (Recommended for quick backtests)**
```bash
--stress-test-days N
```
- Fetches last `N` trading days from yesterday
- Automatically calculates start/end dates
- Bypasses normal validation
- Default: `0` (disabled)

**Example**:
```bash
python main.py --symbols NVDA --stress-test-days 15  # Last 15 trading days
```

#### **Option 2: Explicit Date Range**
```bash
--start-date YYYY-MM-DD --end-date YYYY-MM-DD
```
- Full control over temporal range
- **Overrides** `--stress-test-days` if both are set
- Must be ISO-8601 format

**Example**:
```bash
python main.py --symbols NVDA --start-date 2024-01-01 --end-date 2024-12-31
```

#### **Option 3: Default (No time args)**
- Uses internal default logic (varies by mode)
- For simulation: typically recent data
- **Recommendation**: Always specify one of the above to avoid ambiguity

---

### Configuration Files

#### `--config` (Default: `src/configs/mag7_default.json`)
**Format**: Path to JSON config file

**What it controls**:
- `RETRAIN_INTERVAL`: How often to re-optimize weights
- `POSITION_CAP`: Default max position size
- `LOOKBACK_WINDOW`: Feature engineering window
- Other engine-level parameters

**Files loaded**:
1. **Engine config** (via `--config`): `mag7_default.json`
2. **Ticker configs** (always): `config/nodes/master_config.json`

**Example**:
```bash
# Use custom engine configuration
python main.py --config src/configs/custom_config.json --symbols NVDA
```

**Config hierarchy**:
```
master_config.json (ticker-specific: intervals, weights, caps)
    ↓ overrides
mag7_default.json (engine-level: retrain interval, lookback)
    ↓ overrides
--max-position-size (CLI flag, highest priority)
```

---

### Risk Management

#### `--max-position-size` (Default: `None`)
**Format**: Float (dollar amount)

**What it does**:
- Caps position size for **all tickers** to this dollar amount
- Overrides `position_cap_usd` in `master_config.json`
- Applied in `process_ticker()` → `node_config['position_cap_usd']`

**Example**:
```bash
# Cap all positions at $10,000
python main.py --mode live --symbols NVDA,AAPL --max-position-size 10000
```

---

### Output Control

#### `--quiet`
- Suppresses verbose logs
- Compresses output to essential info only
- Recommended for long backtests

#### `--report-only`
- Minimizes per-window logs
- Shows summary reports only

**Example**:
```bash
python main.py --symbols NVDA --stress-test-days 30 --quiet --report-only
```

---

### Data Source Override

#### `--data-source` (Default: `FMP`)
**Choices**: `FMP`, `Alpaca`

**Note**: Currently FMP is used for news/fundamentals, Alpaca for OHLCV bars. This flag allows forcing one provider.

**Example**:
```bash
python main.py --symbols NVDA --data-source Alpaca
```

---

## Common Use Cases

### **Use Case 1: Quick 3-day backtest on NVDA**
```bash
python main.py --symbols NVDA --stress-test-days 3 --quiet
```
**What happens**:
- Mode: `simulation` (default)
- Tickers: NVDA only
- Date range: Last 3 trading days
- Config: `mag7_default.json` + NVDA from `master_config.json`
- Output: Quiet mode (minimal logs)

---

### **Use Case 2: Full 2024 backtest on MAG7**
```bash
python main.py --start-date 2024-01-01 --end-date 2024-12-31
```
**What happens**:
- Mode: `simulation` (default)
- Tickers: All 7 MAG7 stocks (from `master_config.json`)
- Date range: Jan 1 - Dec 31, 2024
- Output: Full verbose logs

---

### **Use Case 3: Live paper trading with position cap**
```bash
python main.py --mode live --symbols NVDA --max-position-size 10000
```
**What happens**:
- Mode: `live` (paper trading)
- Tickers: NVDA only
- Position cap: $10,000 per ticker
- Runs continuously until Ctrl+C

---

### **Use Case 4: Testing custom config**
```bash
python main.py --config src/configs/my_custom.json --symbols TSLA --stress-test-days 15
```
**What happens**:
- Mode: `simulation`
- Tickers: TSLA
- Config: Custom engine config + TSLA from `master_config.json`
- Date range: Last 15 trading days

---

## File Locations

### **Configuration Files**
```
src/configs/
├── mag7_default.json          # Engine-level defaults (--config)
└── (custom configs here)

config/nodes/
└── master_config.json         # Ticker-specific configs (always loaded)
```

### **Output Files** (auto-generated, gitignored)
```
.cache/fmp_news/               # News cache (24-hour TTL)
equity_curve_*.csv             # P&L over time
stress_test_*.csv              # Backtest results
stress_test_*.txt              # Detailed reports
```

---

## Decision Tree: Which Command to Run?

```
┌─ What do you want to do?
│
├─ [BACKTEST] Test strategy on historical data
│  ├─ Quick test (last N days)
│  │  └─ python main.py --symbols NVDA --stress-test-days 15
│  │
│  └─ Specific date range
│     └─ python main.py --symbols NVDA --start-date 2024-01-01 --end-date 2024-12-31
│
├─ [LIVE TRADE] Run on paper account
│  ├─ Default MAG7 tickers
│  │  └─ python main.py --mode live
│  │
│  └─ Specific ticker with cap
│     └─ python main.py --mode live --symbols NVDA --max-position-size 10000
│
└─ [ANALYZE] Opening Range High study
   └─ python main.py --mode observe
```

---

## Priority Order (What Overrides What)

Highest to lowest priority:

1. **CLI Flags** (`--symbols`, `--max-position-size`, etc.)
2. **Custom Config** (via `--config`)
3. **Default Engine Config** (`mag7_default.json`)
4. **Ticker-Specific Config** (`master_config.json`)
5. **Hardcoded Defaults** (in argparse)

**Example**:
```bash
# If master_config.json says NVDA position_cap_usd = 20000
# And you run:
python main.py --symbols NVDA --max-position-size 10000

# Result: Position cap = $10,000 (CLI overrides config)
```

---

## Troubleshooting

### **"No tickers processed"**
→ Check `--symbols` matches MAG7 allowlist or is added dynamically

### **"Insufficient data for warmup"**
→ Increase `--stress-test-days` or adjust `--start-date` earlier

### **"Config file not found"**
→ Use absolute path or check relative path from project root

### **"API 402 Payment Required"**
→ Check FMP Ultimate plan status (should now fail loudly)

---

## Recommendations

### **For Development/Testing**:
```bash
python main.py --symbols NVDA --stress-test-days 3 --quiet
```
Fast feedback loop, minimal output.

### **For Production Backtests**:
```bash
python main.py --start-date 2024-01-01 --end-date 2024-12-31 --report-only
```
Full year, summary reports only.

### **For Live Trading**:
```bash
python main.py --mode live --max-position-size 10000
```
Clear risk limit, all MAG7 tickers.

---

## Summary

**Golden Rule**: Be explicit with CLI flags to avoid surprises.

**Minimum for backtest**: `--symbols TICKER --stress-test-days N`
**Minimum for live**: `--mode live`

When in doubt, add `--quiet` to reduce log noise and see what's actually happening.
