# Final src/ File Analysis - All 21 Files Categorized

**Date**: 2026-01-18  
**Result**: ALL 21 src/ files are production code - **KEEP ALL**

---

## Complete Analysis

### ✅ KEEP ALL 21 src/ Files

**All 4 "uncertain" files are live trading infrastructure:**

| File | Purpose | Used For | Keep? |
|------|---------|----------|-------|
| **src/risk_manager.py** | Volatility targeting & position sizing | Live trading risk controls | ✅ KEEP |
| **src/monitor.py** | Real-time dashboard | Live trading monitoring | ✅ KEEP |
| **src/reconcile.py** | Position reconciliation | Account verification utility | ✅ KEEP |
| **src/monday_release.py** | Monday gap analysis | Special Monday trading logic | ✅ KEEP |

---

## Detailed Findings

### 1. risk_manager.py ✅ CRITICAL

**Purpose**: Portfolio-level volatility targeting and dynamic position sizing

**Key Components**:
- `VolatilityTargeter` class - Industry-standard risk management
- Scales positions inversely to realized volatility
- Implements Moreira & Muir (2017) academic approach
- Safety bounds: 0.25x to 2.0x leverage limits

**Used for**: Live trading position sizing to maintain constant portfolio risk

**Verdict**: ✅ **KEEP** - Core risk management infrastructure

---

### 2. monitor.py ✅ PRODUCTION TOOL

**Purpose**: Real-time live trading dashboard

**Key Components**:
- `MagellanMonitor` class with rich terminal UI
- Account health monitoring (equity, buying power, PDT status)
- Active positions display with P&L
- Trade history viewer
- System heartbeat indicator
- Emergency kill-switch instructions

**Used for**: Real-time monitoring during live trading sessions

**Verdict**: ✅ **KEEP** - Essential operational tool

---

### 3. reconcile.py ✅ OPERATIONAL UTILITY

**Purpose**: Position reconciliation and account verification

**Key Components**:
- Fetches and displays current account snapshot
- Lists all open positions with P&L
- Shows inventory status
- Simple standalone utility script

**Used for**: Daily reconciliation and position verification

**Verdict**: ✅ **KEEP** - Important operational utility

---

### 4. monday_release.py ✅ TRADING LOGIC

**Purpose**: Special Monday morning gap trading logic

**Key Components**:
- `monday_release_logic()` function
- Analyzes opening gap vs Friday close
- Calculates impulse volume z-score
- Decision matrix:
  - **FADING_GAP**: Large gap + low volume → Mean reversion
  - **MOMENTUM_FLOW**: Large gap + high volume → Follow gap
  - **LAMINAR_NORMAL**: Otherwise → Standard strategy

**Used for**: Enhanced Monday trading strategy based on weekend gap behavior

**Verdict**: ✅ **KEEP** - Active trading logic

---

## Final src/ Inventory

### All 21 Files - Complete List

**Core Infrastructure (13 files):**
1. `src/__init__.py` - Package marker
2. `src/backtester_pro.py` - Rolling backtest engine
3. `src/config_loader.py` - Configuration management
4. `src/data_cache.py` - Data caching (used by ALL 6 strategies)
5. `src/data_handler.py` - Alpaca/FMP data client
6. `src/discovery.py` - Feature correlation & IC
7. `src/executor.py` - Trade execution
8. `src/features.py` - Feature engineering
9. `src/hangar.py` - ORH observation mode
10. `src/logger.py` - Logging system
11. `src/optimizer.py` - Alpha weight optimization
12. `src/pnl_tracker.py` - P&L simulation
13. `src/validation.py` - Walk-forward validation

**Live Trading Infrastructure (4 files):**
14. `src/risk_manager.py` - Volatility targeting & position sizing
15. `src/monitor.py` - Real-time dashboard
16. `src/reconcile.py` - Position reconciliation
17. `src/monday_release.py` - Monday gap trading logic

**Options Support (4 files):**
18. `src/options/__init__.py` - Package marker
19. `src/options/data_handler.py` - Options data handling
20. `src/options/features.py` - OptionsFeatureEngineer
21. `src/options/utils.py` - Options utilities

---

## Why ALL 21 Files Are Needed

### Files Used by main.py (11 files)
Direct imports traced from main.py entry point

### Files Used by Strategies (1 file)
- `data_cache.py` - ALL 6 Perturbations strategies import this

### Files Used by Validation (4 files)
- `options/*` - FOMC & Earnings strategies use OptionsFeatureEngineer

### Files for Live Trading (4 files)
- `risk_manager.py` - Risk controls
- `monitor.py` - Live monitoring
- `reconcile.py` - Account verification
- `monday_release.py` - Special trading logic

### Package Markers (1 file)
- `src/__init__.py` - Required for Python imports

---

## Summary

**Total src/ files: 21**  
**Confirmed production code: 21 (100%)**  
**Safe to archive: 0 (0%)**

**Recommendation**: ✅ **KEEP ALL src/ FILES**

Every single file in `src/` serves a production purpose:
- Core backtesting and validation
- Data management
- Live trading execution
- Risk management
- Operational monitoring
- Options strategy support

---

**None of the src/ files should be archived.**
