# Quick Reference: Validated Strategies Deployment

## ✅ What's Done

1. **Created new branch**: `feature/validated-strategies-deployment`
2. **Archived old system**: `docs/LEGACY_MULTI_FACTOR_ALPHA_SYSTEM.md`
3. **Updated config**: `config/nodes/master_config.json` with validated parameters
4. **Committed changes**: Full git history preserved
5. **Started test**: GOOGL backtest running

## 📋 Current Status

- **Branch**: `feature/validated-strategies-deployment` (NOT on main yet)
- **Test Running**: GOOGL 2024 backtest
- **Config**: Daily bars, RSI-28, hysteresis 55/45

## 🎯 Next Steps

1. **Wait for GOOGL test** to complete
2. **Verify results** match expectations:
   - Daily bars (not 5-minute)
   - Hysteresis signal (not FERMI)
   - ~4-8 trades for 2024
   - Positive return
3. **Test more assets** if GOOGL looks good
4. **Merge to main** when validated

## 🔧 CLI Commands Still Work

All your existing CLI commands are preserved:

```bash
# Single ticker backtest
python main.py --symbols GOOGL --start-date 2024-01-01 --end-date 2024-12-31

# Multiple tickers
python main.py --symbols GOOGL,TSLA,GLD --start-date 2024-01-01 --end-date 2025-12-31

# With position cap
python main.py --symbols SPY --max-position-size 10000 --stress-test-days 30

# Quiet mode
python main.py --symbols NVDA --start-date 2025-07-01 --end-date 2025-12-31 --quiet
```

## 📊 Expected Performance (2024-2025)

| Asset | Return | Sharpe | Trades/Yr |
|-------|--------|--------|-----------|
| GOOGL | +108% | 2.05 | 8 |
| TSLA | +167% | 1.45 | 6 |
| GLD | +96% | 2.41 | 2 |
| SPY | +25% | 1.37 | 6 |

## ⚠️ Important Notes

- **NVDA**: Only trade from July 2025 onwards (stock split issue)
- **All assets**: Long-only (no shorts)
- **Position size**: $10k per asset default
- **Strategy**: Daily Trend Hysteresis (Schmidt Trigger)

## 🔄 To Switch Back to Old System

```bash
git checkout main
```

## 📁 Key Files

- **Config**: `config/nodes/master_config.json`
- **Archive**: `docs/LEGACY_MULTI_FACTOR_ALPHA_SYSTEM.md`
- **Migration**: `docs/VALIDATED_STRATEGIES_DEPLOYMENT.md`
- **Strategies**: `VALIDATED_STRATEGIES_FINAL.md`
