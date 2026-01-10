# CLI OVERRIDE REFACTOR - USAGE GUIDE

## Overview
The stress test can now be force-executed with custom parameters, bypassing validation checks.

## Command Syntax

### Standard Simulation (Default: 15 days, validation required)
```powershell
python main.py --mode simulation
```
- Runs validation first
- Only executes stress test if validation passes
- Uses 15 days by default

### Force Stress Test (Bypass Validation)
```powershell
python main.py --mode simulation --stress-test-days 30
```
- **Bypasses validation check**
- Forces stress test for ALL tickers
- Uses specified number of days (e.g., 30)

### Quick Stress Test (7 days)
```powershell
python main.py --stress-test-days 7
```
- Fast execution for quick checks
- Bypasses validation
- Useful for rapid iteration

### Extended Stress Test (60 days)
```powershell
python main.py --stress-test-days 60
```
- Comprehensive multi-regime testing
- Bypasses validation
- Takes longer but more thorough

## Implementation Details

### CLI Arguments
- `--mode`: Execution mode (simulation | live)
- `--stress-test-days`: Force stress test with N days (0=disabled)

### Logic Flow
1. If `--stress-test-days > 0`:
   - Print: `[SYSTEM] Force-Starting Stress Test for {ticker} ({N} days)...`
   - Print: `[OVERRIDE] Bypassing validation check (--stress-test-days specified)`
   - Execute stress test with custom days
   - Skip validation requirement

2. If `--stress-test-days == 0` (default):
   - Run validation first
   - Only execute stress test if validation passes
   - Use default 15 days

### Telemetry
- Force mode: `[SYSTEM] Force-Starting Stress Test for SPY (30 days)...`
- Normal mode: `[SYSTEM] SPY VALIDATION PASSED - Trading signals are ACTIVE.`
- All logging remains ASCII-only (no charmap errors)

## Examples

### Example 1: Force 30-day stress test on all tickers
```powershell
python main.py --stress-test-days 30
```

### Example 2: Standard 15-day with validation
```powershell
python main.py
```

### Example 3: Quick 5-day test
```powershell
python main.py --stress-test-days 5
```

## Safety Features
- ASCII-only logging maintained
- Validation logic preserved when not forcing
- Clear telemetry for override mode
- All existing functionality intact
