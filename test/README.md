# 🧪 TEST - `/test/` - Stage 2: Validation & Tuning

**This directory represents Stage 2 of the Magellan Strategy Pipeline.**

1.  **Dev** (`/dev/`) -> Experimental
2.  **Test** (`/test/`) -> Validation (YOU ARE HERE)
3.  **Deployable** (`/deployable_strategies/`) -> Production Code (Verified)
4.  **Deployed** (`/deployed/`) -> Live Configurations

Strategies in this folder are undergoing:
-   Rigorous backtesting
-   Walk-Forward Analysis (WFA)
-   Paper trading calibration

Once validated, strategies move to `/deployable_strategies/`. **Do not edit strategies in `/deployable_strategies/` directly.** Perform changes here, validate, then promote.

## Rules

- ✅ **Use cached data** - Set `USE_ARCHIVED_DATA=true` for local testing
- ✅ **Work here** - This is where you edit and improve strategies
- ✅ **Keep all strategies** - Strategies stay here even after promoted to prod
- ✅ **Test before promoting** - Validate changes before copying to prod/

## Workflow

### **For Existing Strategies** (tune/enhance):
```bash
# Work in test/
cd test/bear_trap
vim strategy.py  # Make improvements

# Test locally with cache
export USE_ARCHIVED_DATA=true
python runner.py

# Run tests
pytest tests/ -v

# When validated, copy to prod/
Copy-Item test/bear_trap prod/bear_trap -Recurse -Force

# Push to deploy
git add prod/bear_trap
git commit -m "Update Bear Trap with improvements"
git push
```

### **For New Strategies**:
```bash
# Create in dev/ first
mkdir dev/new_strategy

# When ready for testing, move to test/
mv dev/new_strategy test/new_strategy

# Develop and test in test/
# ... tune, validate ...

# When production-ready, copy to prod/
Copy-Item test/new_strategy prod/new_strategy -Recurse -Force

# Push to deploy
git add prod/new_strategy
git push
```

## Structure

```
test/
├── bear_trap/           # Working copy (tune here)
│   ├── strategy.py
│   ├── runner.py        # Uses cache when USE_ARCHIVED_DATA=true
│   ├── config.json
│   ├── tests/
│   ├── deployment/
│   └── docs/
│
├── daily_trend/         # Working copy
└── hourly_swing/        # Working copy
```

## Key Points

1. **ALL strategies live here** - Even after deployed to prod
2. **Use local cache** - Test safely without live API
3. **Work here first** - Never edit prod/ directly
4. **Copy when ready** - Promote to prod/ when validated

## Environment

**Local Testing** (Always use cache):
```bash
export USE_ARCHIVED_DATA=true
cd test/bear_trap
python runner.py  # Safe - uses cached data
```

**CI/CD Testing** (Automatic):
```yaml
# Tests run on test/ automatically with cache
env:
  USE_ARCHIVED_DATA: 'true'
```

---

**Current Strategies**: 3 (Bear Trap, Daily Trend, Hourly Swing)  
**All validated and deployed to AWS**
