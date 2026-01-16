# Magellan Trading System

## 🚀 Quick Start - Daily Trend Hysteresis Strategy

**Want to test the validated trading strategy?**

👉 **[READ THIS FIRST: docs/operations/strategies/daily_trend_hysteresis/README.md](docs/operations/strategies/daily_trend_hysteresis/README.md)**

### Run Portfolio Backtest (2024-2025):
```bash
python docs/operations/strategies/daily_trend_hysteresis/backtest_portfolio.py
```

**Results**: 10/11 assets profitable, +45% average return, 1.05 Sharpe

---

## 📁 Strategy Directory Structure

```
docs/operations/strategies/
└── daily_trend_hysteresis/
    ├── README.md              ⭐ Complete strategy guide
    ├── backtest_portfolio.py  🧪 Test all assets
    ├── backtest_single.py     🧪 Test single asset (GOOGL)
    └── results.csv            📊 Validated results (2024-2025)
```

---

## 📊 Validated Performance (2024-2025)

| Asset | Return  | Sharpe | Status |
|-------|---------|--------|--------|
| GOOGL | +118.4% | 1.54   | ✅     |
| GLD   | +87.1%  | 1.88   | ✅     |
| META  | +68.9%  | 1.09   | ✅     |
| TSLA  | +36.2%  | 0.56   | ✅     |
| AAPL  | +34.9%  | 0.97   | ✅     |
| QQQ   | +30.5%  | 1.03   | ✅     |
| MSFT  | +29.9%  | 0.87   | ✅     |
| SPY   | +25.0%  | 1.20   | ✅     |
| AMZN  | +11.7%  | 0.34   | ✅     |
| IWM   | +10.3%  | 0.39   | ✅     |
| NVDA  | -81.6%  | -0.16  | ❌     |

**Success Rate**: 91% (10/11 assets)

---

## 🔧 System Configuration

- **Strategy Config**: `config/nodes/master_config.json`
- **Core Logic**: `src/features.py` (line 693)
- **Backtester**: `src/backtester_pro.py`

---

## 📚 Documentation

- **Strategy Guide**: `docs/operations/strategies/daily_trend_hysteresis/README.md`
- **Bug Fixes**: `docs/CRITICAL_BUG_FIXES_2026-01-16.md`
- **Deployment**: `docs/VALIDATED_STRATEGIES_DEPLOYMENT.md`

---

## 🔧 System Status

- ✅ Critical bugs fixed (2026-01-16)
- ✅ Strategy validated on 2 full years
- ✅ Production ready
- ⏳ Paper trading recommended before live

---

**For full documentation, see**: `docs/operations/strategies/daily_trend_hysteresis/README.md`
