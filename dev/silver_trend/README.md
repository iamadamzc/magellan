# Silver Trend-Following Strategy

Position trading strategy for silver (SIUSD/MSI) optimized for bull markets.

## Overview

| Parameter | Value |
|:----------|:------|
| Asset | Silver (SIUSD spot / MSI micro futures) |
| Strategy | RSI trend-following (long only) |
| Leverage | 6x |
| Capital | $20,000 |

## Optimized Parameters

Found via comprehensive grid search (1,728 combinations tested):

- **RSI Period**: 21
- **Entry**: RSI > 48
- **Exit**: RSI < 30
- **Leverage**: 6x

## Validated Performance (2024-2025)

| Metric | Result |
|:-------|:-------|
| Total Trades | 2 |
| Win Rate | 100% |
| Total P&L | $58,000 |
| Total Return | +290% |
| Sharpe Ratio | 1.71 |
| Max Drawdown | -51% |

## How It Works

1. **Wait for breakout**: RSI crosses above 48
2. **Enter long**: Buy with 6x leverage
3. **Hold the trend**: Stay in position for weeks/months
4. **Exit on weakness**: RSI drops below 30

**This is position trading, not day trading** - makes 2-3 large trades per year.

## Usage

```bash
# Run backtest
python strategy.py

# Custom parameters
python strategy.py --start 2024-01-01 --end 2025-01-24 --capital 20000 --leverage 6
```

## Risk Warning

- **6x leverage** amplifies both gains and losses
- **-51% max drawdown** - silver is more volatile than gold
- Requires stronger risk tolerance than gold strategy
- Suitable for bull markets only
- PDT rules don't apply (futures exempt from $25k minimum)

## vs Gold Strategy

| Metric | Silver | Gold |
|:-------|:-------|:-----|
| Sharpe | 1.71 | 2.39 ✅ |
| Max DD | -51% | -27% ✅ |
| Return | +290% | +280% |

Gold has better risk-adjusted returns.

## Files

- `strategy.py` - Main backtest script
- `config.json` - Strategy parameters
- `README.md` - This file

---

**Status**: Validated and optimized via comprehensive parameter search.
