# ✅ Intraday Alpha Strategy - Setup Complete

**Date**: January 22, 2026  
**Location**: `test/intraday_alpha/`

---

## Summary

Successfully extracted and archived the **Magellan V1.0 "Laminar DNA"** intraday alpha strategy that traded SPY, QQQ, and IWM on Alpaca Paper Trading (deployed January 10, 2026).

---

## Directory Structure

```
test/intraday_alpha/
├── strategy.py              # Core strategy logic (multi-factor alpha)
├── runner.py                # Simple test runner
├── config.json              # V1.0 configuration (SPY/QQQ/IWM)
├── README.md                # Strategy overview and documentation
└── docs/
    ├── V1_DEPLOYMENT.md     # Original deployment summary
    └── V1_LAUNCH.md         # Original launch checklist
```

---

## Strategy Details

**Original Deployment**: January 10, 2026  
**Platform**: Alpaca Paper Trading  
**Universe**: SPY, QQQ, IWM (index ETFs)  
**Timeframes**: 3-5 minute bars  
**Strategy Type**: Multi-factor intraday alpha (NOT HFT)

### Configuration

**SPY**:
- 5-minute bars
- 90% RSI / 0% Volume / 10% Sentiment
- Sentry gate: 0.0
- Position cap: $50,000

**QQQ**:
- 5-minute bars
- 80% RSI / 10% Volume / 10% Sentiment
- Sentry gate: 0.0
- Position cap: $50,000

**IWM**:
- 3-minute bars
- 100% RSI / 0% Volume / 0% Sentiment
- Sentry gate: -0.2
- Position cap: $50,000

---

## Git Reference

**Original Commit**: `2efcc54`  
**Tag**: `v1.1-MAG7-READY` (misleading name)  
**Branches**: `deployment/aws-paper-trading-setup`, `stable/mag7-2025-success`

**Note**: The tag name "MAG7-READY" is confusing because this version actually traded index ETFs (SPY/QQQ/IWM), not MAG7 stocks. The actual MAG7 deployment happened the next day (Jan 11, 2026) in commit `8c98818`.

---

## Testing

The strategy can be tested using archived data:

```bash
# Set environment variables
export ALPACA_API_KEY=your_key
export ALPACA_API_SECRET=your_secret
export USE_ARCHIVED_DATA=true

# Run test
cd test/intraday_alpha
python runner.py
```

---

## Key Features

1. **Multi-Factor Alpha**: Combines RSI, Volume, and Sentiment signals
2. **Sentry Gate**: Sentiment threshold that kills alpha in bearish conditions
3. **Position Caps**: $50k hard limit per ticker
4. **Intraday Timeframes**: 3-5 minute bars for tactical trading
5. **Risk Controls**: PDT protection, buying power checks, position-aware logic

---

## Historical Context

This strategy represents the **first production deployment** of Magellan to Alpaca Paper Trading. It was replaced the next day by the MAG7 deployment, which switched to trading tech stocks (AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA) instead of index ETFs.

The strategy is preserved here for:
- Historical reference
- Potential future adaptation
- Intraday ETF trading research
- Multi-factor alpha experimentation

---

## Related Documentation

- `../../V1_SPY_QQQ_IWM_DEPLOYMENT_FOUND.md` - Full git location guide
- `../../research/archived_research/DEPLOYMENT_V1.0.md` - Original deployment docs
- `../../research/archived_research/LAUNCH_V1.0.md` - Launch procedures
- `../../research/archived_research/SYNC_V1.0.md` - Synchronization details
- `../../research/archived_research/MAG7_LOCKDOWN_REPORT.md` - MAG7 transition

---

**Status**: ✅ Complete  
**Files Created**: 5  
**Structure**: Matches `test/hourly_swing/` pattern
