# 📊 Intraday Alpha Strategy (V1.0 Archive)

**Status**: 🗄️ Archived  
**Original Deployment**: January 10, 2026  
**Platform**: Alpaca Paper Trading  
**Version**: V1.0 "Laminar DNA"

---

## Overview

This is an **archived version** of the original Magellan V1.0 deployment that traded SPY, QQQ, and IWM on intraday timeframes using a multi-factor alpha strategy.

**Important**: This strategy was replaced by the MAG7 deployment on January 11, 2026. It is preserved here for historical reference and potential future adaptation.

---

## Strategy Logic

### Multi-Factor Alpha Calculation

The strategy combines three signals with custom weights per symbol:

```
Alpha = (RSI_weight × RSI_signal) + (Volume_weight × Vol_signal) + (Sentiment_weight × Sent_signal)
```

**Signal Generation**:
- Alpha > 0.5 → **BUY**
- Alpha < -0.5 → **SELL**
- Otherwise → **FILTER** (no action)

### Sentry Gate

A sentiment threshold that "kills" the alpha score if market sentiment falls below a configured level:
- **SPY/QQQ**: Gate at 0.0 (neutral/bullish only)
- **IWM**: Gate at -0.2 (allows slight bearish sentiment)

### Position Sizing

- Base allocation: 25% of equity per position
- Hard cap: $50,000 per ticker
- Cap enforced at execution layer before order submission

---

## Symbol Configuration

### SPY (S&P 500 ETF)
- **Timeframe**: 5-minute bars
- **Weights**: 90% RSI / 0% Volume / 10% Sentiment
- **Sentry Gate**: 0.0 (neutral/bullish only)
- **Position Cap**: $50,000

### QQQ (Nasdaq 100 ETF)
- **Timeframe**: 5-minute bars
- **Weights**: 80% RSI / 10% Volume / 10% Sentiment
- **Sentry Gate**: 0.0 (neutral/bullish only)
- **Position Cap**: $50,000

### IWM (Russell 2000 ETF)
- **Timeframe**: 3-minute bars
- **Weights**: 100% RSI / 0% Volume / 0% Sentiment
- **Sentry Gate**: -0.2 (allows slight bearish)
- **Position Cap**: $50,000

---

## Risk Controls

1. **Position Cap**: $50,000 maximum per ticker
2. **PDT Protection**: Requires $25k+ equity to trade
3. **Buying Power Check**: Rejects orders exceeding available funds
4. **Sentry Gate**: Kills alpha on bearish sentiment
5. **Position-Aware Logic**: Prevents duplicate long entries

---

## Original Deployment Details

**Git Information**:
- Commit: `2efcc54`
- Tag: `v1.1-MAG7-READY` (misleading - actually traded indices)
- Branch: `deployment/aws-paper-trading-setup`, `stable/mag7-2025-success`

**Deployment Environment**:
- Platform: Alpaca Paper Trading
- API Endpoint: `https://paper-api.alpaca.markets`
- Mode: Paper (no real money)

**Key Features**:
- Standard RSI calculation (no VWAP weighting)
- Multi-factor alpha with custom weights
- Marketable limit order execution
- 10-second fill polling with timeout

---

## Why This Version Was Replaced

**Timeline**:
1. **Jan 10, 2026**: V1.0 deployed with SPY/QQQ/IWM
2. **Jan 11, 2026**: Switched to MAG7 stocks (AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA)

**Reasons for Change**:
- Index ETFs showed mean-reverting behavior at daily timeframes
- MAG7 tech stocks offered better momentum characteristics
- Position sizing reduced from $50k to $20k per ticker
- Added hysteresis (0.02 deadband) to prevent signal chatter
- Implemented edge-triggered logging for cleaner output

---

## Files

```
test/intraday_alpha/
├── strategy.py          # Core strategy logic
├── config.json          # V1.0 configuration
├── README.md            # This file
└── docs/
    └── V1_DEPLOYMENT.md # Original deployment documentation
```

---

## Testing

This strategy can be tested using archived data:

```bash
# Set environment to use cached data
export USE_ARCHIVED_DATA=true

# Run strategy test
cd test/intraday_alpha
python strategy.py
```

---

## Historical Context

This strategy represents:
- **First Production Deployment**: The initial live deployment to Alpaca
- **Index ETF Focus**: Tested on liquid, stable instruments
- **Intraday Trading**: Used 3-5 minute bars for higher frequency signals
- **Multi-Factor Alpha**: Combined RSI, Volume, and Sentiment
- **Risk-Controlled**: Implemented position caps and sentiment gates

**Not an HFT System**: This was a tactical intraday strategy, not high-frequency trading.

---

## Documentation

For complete deployment documentation, see:
- `docs/V1_DEPLOYMENT.md` - Full deployment summary
- `../../V1_SPY_QQQ_IWM_DEPLOYMENT_FOUND.md` - Git location and access guide
- `../../research/archived_research/DEPLOYMENT_V1.0.md` - Original deployment docs
- `../../research/archived_research/LAUNCH_V1.0.md` - Launch checklist
- `../../research/archived_research/SYNC_V1.0.md` - Synchronization details

---

## Potential Future Use

This strategy could be adapted for:
1. **Intraday ETF Trading**: Reactivate for SPY/QQQ/IWM on intraday timeframes
2. **Multi-Factor Research**: Test different weight combinations
3. **Sentiment Integration**: Enhance with real-time sentiment data
4. **Volatility Regimes**: Apply to high-volatility market conditions
5. **Alternative Timeframes**: Test on 1-minute or 15-minute bars

---

**Last Updated**: January 22, 2026  
**Status**: Archived for historical reference
