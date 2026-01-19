# Logging System Analysis & Optimization Plan

## Current Issues

### **Problem 1: Too Many Log Levels**
Current system has **13 different log methods**:
- `info()`, `system()`, `metric()`, `ic_matrix()`
- `phase_lock()`, `cryogen()`, `symmetry()`, `stats()`
- `warning()`, `error()`, `ensemble()`
- `debug()`, `success()`, `config()`

**Issue**: Confusing, inconsistent usage, no clear hierarchy

---

### **Problem 2: Redundant Messages**
Examples from your recent output:
```
[INFO] ENGINE: Loading config from A:\1\Magellan\src\configs\mag7_default.json
[INFO] ENGINE: Loading default config (mag7_default.json)
```
→ **Duplicate information**

```
[HOT START] Fetching 252 warmup bars before 2022-01-01
[HOT START] Adjusted start: 2021-12-31
```
→ **Could be single line**

---

### **Problem 3: Backend Noise in Normal Mode**
Messages that users don't need to see:
- `[DEBUG] Fetching NVDA via SIP feed...` ← Backend detail
- `[DATA] Force-Resampled NVDA from 60s to 300s` ← Implementation detail
- `[VALIDATION] [OK] Frequency verified` ← Internal check
- `[FMP] Attempting Stable Quote endpoint` ← API internals

---

### **Problem 4: No Standard Log Levels**
Industry standard is:
1. **DEBUG**: Developer-only details
2. **INFO**: General informational messages
3. **WARNING**: Something unusual but not critical
4. **ERROR**: Something failed
5. **CRITICAL**: System-level failure

Your system doesn't follow this.

---

## Proposed Solution

### **New Clean Hierarchy**

```python
class SystemLogger:
    """
    Optimized logging with clear signal-to-noise ratio.
    
    Modes:
    - Normal: Shows only actionable events (trades, errors, major milestones)
    - Verbose: Shows process flow (what's happening step-by-step)
    - Debug: Everything (file-redirected, not shown in terminal)
    """
    
    # LEVELS (what user sees in terminal)
    # Level 0: CRITICAL - Always shown (errors, warnings, trades)
    # Level 1: EVENT - Normal mode (major milestones only)
    # Level 2: FLOW - Verbose mode (step-by-step process)
    # Level 3: DEBUG - Hidden (file only)
```

---

### **User-Facing Output** (Optimized)

**BEFORE** (Current):
```
[INFO] ENGINE: Loading config from A:\1\Magellan\src\configs\mag7_default.json
[INFO] ENGINE: Loading default config (mag7_default.json)
[SYSTEM] Digital Squelch Active: Event-Only Logging Enabled.
[HOT START] Fetching 252 warmup bars before 2022-01-01
[HOT START] Adjusted start: 2021-12-31
[DEBUG] Fetching NVDA via SIP feed...
[DATA] Force-Resampled NVDA from 60s to 300s
[FMP] Attempting Stable Quote endpoint for NVDA
[FMP] Using cached news for NVDA (2021-12-29 to 2025-12-31)
[SIGNAL] Fermi Gate: 0.0200 (Mean=0.0013 + 0.75*StdDev=0.0250)
[SIGNAL] Hysteresis Deadband: 0.05 (Anti-Chatter Active)
[SIGNAL] Fermi Results: 382 BUY, 0 SELL, 123696 FILTER
...
```

**AFTER** (Optimized):
```
[MAGELLAN] Initialized | Tickers: NVDA, AAPL, MSFT | Mode: Simulation
[NVDA] Processing 2022-01-01 to 2026-01-14 (3 days, cached news)
[NVDA] Signal: BUY (382/124K bars) | Validation: FAILED (hit rate <51%)
[NVDA] Complete | Equity curve: equity_curve_NVDA.csv

[AAPL] Processing...
```

**Key improvements**:
- ✅ One-line-per-major-event
- ✅ No backend details (SIP feed, resampling, API endpoints)
- ✅ Clear progress indicators
- ✅ Only errors and trades get full attention

---

### **Verbose Mode** (`--verbose` flag)

For when you want to see what's happening:
```
[MAGELLAN] Initialized | Config: mag7_default.json
  ├─ Alpaca: Connected (SIP feed)
  ├─ FMP: Connected (Ultimate plan)
  └─ Tickers: NVDA, AAPL, MSFT

[NVDA] Loading data...
  ├─ Bars: 124,078 (5Min, 2022-01-01 to 2026-01-14)
  ├─ News: 100 articles (cached)
  └─ Fundamentals: Market cap $2.8T, P/E 45.2

[NVDA] Feature engineering...
  ├─ Technical indicators: RSI, ATR, Bollinger
  ├─ Sentiment alignment: 4-hour lookback
  └─ Signal generation: Fermi gate (382 BUY signals)

[NVDA] Validation: FAILED
  └─ Reason: Out-of-sample hit rate 48% (<51% threshold)

[NVDA] Complete
```

**Benefits**:
- Tree structure shows hierarchy
- Still concise (not overwhelming)
- Shows what's happening without low-level details

---

### **Debug Mode** (file only)

All the backend details go to `debug_vault.log`:
```
[2026-01-14 16:01:04] [DEBUG] Fetching NVDA via SIP feed
[2026-01-14 16:01:05] [DEBUG] API Response: 200 OK, 124078 bars
[2026-01-14 16:01:05] [DEBUG] force-resampling from 60s to 300s
[2026-01-14 16:01:06] [DEBUG] FMP attempting stable quote endpoint
[2026-01-14 16:01:06] [DEBUG] Cache hit: NVDA news (2021-12-29 to 2025-12-31)
...
```

**Never shown in terminal** - only for debugging failures.

---

## Implementation Plan

### **Phase 1: Simplify Logger** (30 min)
```python
class SystemLogger:
    def __init__(self):
        self.verbosity = 1  # 0=quiet, 1=normal, 2=verbose
        self.debug_file = "debug_vault.log"
    
    # TERMINAL OUTPUT
    def critical(self, msg):  # Always shown (errors, warnings)
        print(msg)
    
    def event(self, msg):  # Normal+ (major milestones)
        if self.verbosity >= 1:
            print(msg)
    
    def flow(self, msg):  # Verbose only (step-by-step)
        if self.verbosity >= 2:
            print(msg)
    
    # FILE ONLY
    def debug(self, msg):  # Never shown, file only
        with open(self.debug_file, 'a') as f:
            f.write(f"{timestamp()} {msg}\n")
```

### **Phase 2: Refactor Calls** (60 min)
Replace:
- `LOG.info()` → `LOG.debug()` or `LOG.flow()` depending on importance
- `LOG.system()` → `LOG.event()` for milestones
- `LOG.error()` → `LOG.critical()`
- `LOG.success()` → `LOG.debug()` or `LOG.event()`

### **Phase 3: Add --verbose Flag** (15 min)
```python
parser.add_argument('--verbose', action='store_true',
                    help='Show detailed process flow')
if args.verbose:
    LOG.set_verbosity(2)
```

---

## Example Transformation

### **Current Code**:
```python
LOG.info(f"[STEP 1] Fetching {ticker} {interval_str} bars from Alpaca (SIP feed)...")
LOG.info(f"[HOT START] Fetching {WARMUP_BUFFER}-bar trailing history for normalization warmup")
LOG.debug(f"Fetching {ticker} via SIP feed...")
LOG.info(f"[{ticker}] Fetched {len(bars)} bars (includes {WARMUP_BUFFER} warmup)")
```

### **Optimized Code**:
```python
LOG.flow(f"[{ticker}] Loading {len(bars)} bars ({interval_str})...")
LOG.debug(f"SIP feed request: {ticker}, {start_date} to {end_date}")
```

**Terminal output** (normal mode): *(nothing - only shows when complete)*
**Terminal output** (verbose mode): `[NVDA] Loading 124,078 bars (5Min)...`
**Debug file**: Full details

---

## Migration Strategy

1. ✅ **Don't break existing code** - keep old methods as aliases initially
2. ✅ **Gradual transition** - refactor one file at a time
3. ✅ **Test at each step** - ensure output is cleaner, not broken

---

## Expected Results

**Backtest output** (Normal mode):
```
[MAGELLAN] Simulation | NVDA, AAPL, MSFT | 2022-01-01 to 2026-01-14
[NVDA] ✓ Complete | Validation: FAILED (hit rate 48%)
[AAPL] ✓ Complete | Validation: OK
[MSFT] ✓ Complete | Validation: OK
[REPORT] Equity curves saved to stress_test_*.csv
```

**Live trading output** (Normal mode):
```
[MAGELLAN] Live Trading | NVDA | 09:30 ET
[09:31] NVDA BUY 10 @ $850.50 (Order #ABC123)
[09:45] NVDA Position: +10 @ $850.50 | P&L: +$125.00
[10:00] No action (signal: FILTER)
[10:15] No action (signal: FILTER)
...
```

**Only shows trades and errors** - terminal stays quiet otherwise.

---

## Your Call

**Option A**: Implement full refactor (cleaner but takes 2 hours)
**Option B**: Quick fix (just hide noisy logs, 30 min)
**Option C**: Review and provide feedback first

Which approach do you prefer?
