# 🎯 MAGELLAN V1.0 - SPY/QQQ/IWM DEPLOYMENT LOCATED

**Status:** ✅ FOUND  
**Date Created:** 2026-01-10  
**Date Located:** 2026-01-22  
**Version:** V1.0 (Laminar DNA)

---

## ⚠️ IMPORTANT CLARIFICATION: TAG NAME IS MISLEADING

**The tag `v1.1-MAG7-READY` is confusing because:**
- The tag name says "MAG7-READY" (suggesting it trades MAG7 stocks)
- But this version **actually traded SPY, QQQ, IWM** (index ETFs)
- The tag was **forward-looking** - it meant the system was "ready" to be configured for MAG7
- The **actual MAG7 deployment** happened the next day (Jan 11, 2026) in commit `8c98818`

**Timeline:**
- **Jan 10, 2026:** V1.0 deployed with SPY/QQQ/IWM (commit `2efcc54`, tagged `v1.1-MAG7-READY`)
- **Jan 11, 2026:** MAG7 lockdown - switched to AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA (commit `8c98818`)

So the tag name refers to the **infrastructure being ready** for MAG7, not the actual trading universe at that commit.

---

## 📍 LOCATION SUMMARY

The version of Magellan that traded **SPY, QQQ, and IWM** on Alpaca Paper Trading has been successfully located in the repository.

### Git Commit Information
- **Primary Commit:** `2efcc54` - "MAGELLAN-V1.1-STABLE: LAMINAR-DNA-LOCK"
- **Related Commit:** `22e17e6` - "MAGELLAN-V1.1-STABLE: LAMINAR-DNA-LOCK"
- **Date:** January 10, 2026
- **Tag:** `v1.1-MAG7-READY`

### Branches Containing This Version
All of the following branches contain this deployment:
- `codebase-cleanup-analysis`
- `debug/hysteresis-activation`
- `deployment/aws-paper-trading-setup`
- `deployment/aws-paper-trading-test-prod-structure`
- `research/small-cap-scalping`
- `stable/mag7-2025-success`

**Recommended Branch:** `deployment/aws-paper-trading-setup` or `stable/mag7-2025-success`

---

## 🎯 STRATEGY CONFIGURATION

### Trading Universe
The V1.0 deployment traded **3 index ETFs**:
1. **SPY** - S&P 500 ETF
2. **QQQ** - Nasdaq 100 ETF  
3. **IWM** - Russell 2000 Small Cap ETF

### Strategy Type
**NOT a High-Frequency Trading (HFT) system** - This was a **multi-factor alpha strategy** using:
- RSI (Relative Strength Index)
- Volume indicators
- Sentiment analysis
- Intraday timeframes (3-5 minute bars)

---

## 📋 CONFIGURATION DETAILS

### SPY Configuration
```json
{
    "interval": "5Min",
    "rsi_lookback": 14,
    "sentry_gate": 0.0,
    "rsi_wt": 0.9,
    "vol_wt": 0.0,
    "sent_wt": 0.1,
    "position_cap_usd": 50000
}
```
- **Weights:** 90% RSI / 0% Volume / 10% Sentiment
- **Timeframe:** 5-minute bars
- **Sentiment Gate:** 0.0 (Neutral/Bullish only)
- **Max Position:** $50,000

### QQQ Configuration
```json
{
    "interval": "5Min",
    "rsi_lookback": 14,
    "sentry_gate": 0.0,
    "rsi_wt": 0.8,
    "vol_wt": 0.1,
    "sent_wt": 0.1,
    "position_cap_usd": 50000
}
```
- **Weights:** 80% RSI / 10% Volume / 10% Sentiment
- **Timeframe:** 5-minute bars
- **Sentiment Gate:** 0.0 (Neutral/Bullish only)
- **Max Position:** $50,000

### IWM Configuration
```json
{
    "interval": "3Min",
    "rsi_lookback": 14,
    "sentry_gate": -0.2,
    "rsi_wt": 1.0,
    "vol_wt": 0.0,
    "sent_wt": 0.0,
    "position_cap_usd": 50000
}
```
- **Weights:** 100% RSI / 0% Volume / 0% Sentiment
- **Timeframe:** 3-minute bars
- **Sentiment Gate:** -0.2 (Allows slight bearish sentiment)
- **Max Position:** $50,000

---

## 🔧 KEY TECHNICAL DETAILS

### Core Features
1. **Standard RSI Calculation** - Uses 'close' price only (no VWAP weighting)
2. **Multi-Factor Alpha** - Combines RSI, Volume, and Sentiment with custom weights per ticker
3. **Sentry Gate** - Sentiment threshold that kills alpha when market sentiment is too bearish
4. **Position Cap** - Hard $50k limit per ticker enforced at execution layer
5. **Marketable Limit Orders** - Order execution strategy
6. **PDT Protection** - Requires $25k+ equity to trade

### Risk Controls
- **PDT Protection:** Halts trading if equity < $25,000
- **Buying Power Check:** Rejects orders exceeding available funds
- **Position Cap:** $50,000 per ticker maximum
- **Sentry Gate:** Kills alpha on bearish sentiment (SPY/QQQ: 0.0, IWM: -0.2)
- **Position-Aware Logic:** Prevents duplicate longs

### Deployment Environment
- **Platform:** Alpaca Paper Trading
- **API Endpoint:** `https://paper-api.alpaca.markets`
- **Mode:** Paper Trading (paper=True)
- **Safety:** NO REAL MONEY AT RISK

---

## 📁 KEY FILES IN THIS VERSION

### Configuration
- `config/nodes/master_config.json` - Production DNA configuration with SPY/QQQ/IWM settings

### Core Code
- `main.py` - Entry point and orchestration
- `src/features.py` - Alpha generation (standard RSI, no VWAP)
- `src/executor.py` - Order execution with position cap enforcement
- `src/monitor.py` - Account health dashboard

### Documentation
- `research/archived_research/DEPLOYMENT_V1.0.md` - Full deployment summary
- `research/archived_research/LAUNCH_V1.0.md` - Launch checklist and procedures
- `research/archived_research/SYNC_V1.0.md` - Synchronization and verification

---

## 🚀 HOW TO ACCESS THIS VERSION

### Option 1: Checkout Specific Commit
```bash
git checkout 2efcc54
```

### Option 2: Checkout Tagged Version
```bash
git checkout v1.1-MAG7-READY
```

### Option 3: Checkout Deployment Branch
```bash
git checkout deployment/aws-paper-trading-setup
git log --oneline --since="2026-01-08" --until="2026-01-12"
# Find the commit with "LAMINAR-DNA-LOCK" and checkout
```

### Option 4: View Files Without Checkout
```bash
# View the configuration
git show 2efcc54:config/nodes/master_config.json

# View main.py
git show 2efcc54:main.py

# View executor
git show 2efcc54:src/executor.py
```

---

## 📊 WHAT CHANGED AFTER V1.0

The current codebase has evolved significantly since V1.0:

### Current State (as of Jan 22, 2026)
- **Universe:** MAG7 stocks + ETFs (AAPL, MSFT, GOOGL, NVDA, META, AMZN, TSLA, SPY, QQQ, IWM, GLD, etc.)
- **Strategies:** Multiple validated strategies (Bear Trap, Daily Trend, Hourly Swing, GSB, Earnings Straddles, FOMC Straddles)
- **Timeframes:** Daily and Hourly (not intraday 3-5 minute bars)
- **Structure:** V3 production structure with DEV/TEST/PROD separation
- **Deployment:** Live on EC2 with CI/CD pipeline

### V1.0 State (Jan 10, 2026)
- **Universe:** Only SPY, QQQ, IWM
- **Strategy:** Single multi-factor alpha strategy
- **Timeframes:** Intraday 3-5 minute bars
- **Structure:** Simple main.py + src/ directory
- **Deployment:** Manual Alpaca Paper Trading

---

## 🎓 WHY THIS VERSION IS IMPORTANT

This V1.0 deployment represents:

1. **First Production Deployment** - The initial live deployment to Alpaca
2. **Index ETF Focus** - Tested the strategy on liquid, stable instruments
3. **Intraday Trading** - Used 3-5 minute bars for higher frequency signals
4. **Multi-Factor Alpha** - Combined RSI, Volume, and Sentiment
5. **Risk-Controlled** - Implemented position caps and sentiment gates

This was **NOT an HFT system** but rather a **tactical intraday strategy** using multi-factor signals on index ETFs.

---

## 🔄 THE ACTUAL MAG7 VERSION (Jan 11, 2026)

If you're looking for the version that **actually traded MAG7 stocks**, that's a different commit:

### MAG7 Deployment Details
- **Commit:** `8c98818` (also tagged `v1.1-MAG7-READY` but this is the actual MAG7 version)
- **Date:** January 11, 2026 (one day after SPY/QQQ/IWM)
- **Universe:** AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA
- **Timeframe:** 5-minute bars (all tickers)
- **Position Cap:** $20,000 per ticker (reduced from $50k)

### Key Differences from SPY/QQQ/IWM Version
1. **Ticker Universe:** Changed from 3 index ETFs to 7 tech stocks
2. **Position Sizing:** Reduced from $50k to $20k per ticker
3. **Weights:** Customized per stock (e.g., NVDA 70/20/10, TSLA 50/30/20)
4. **Hysteresis:** Added 0.02 deadband to prevent signal chatter
5. **Logging:** Edge-triggered logging (only prints on state changes)

### Access MAG7 Version
```bash
# The actual MAG7 deployment
git checkout 8c98818

# View MAG7 configuration
git show 8c98818:config/nodes/master_config.json
```

---

## 📞 NEXT STEPS

### To Restore This Version
1. Checkout the commit: `git checkout 2efcc54`
2. Review the configuration: `config/nodes/master_config.json`
3. Check the deployment docs: `research/archived_research/DEPLOYMENT_V1.0.md`
4. Verify the code: `main.py`, `src/features.py`, `src/executor.py`

### To Compare with Current Version
```bash
# Compare configuration
git diff 2efcc54:config/nodes/master_config.json main:config/nodes/master_config.json

# Compare main entry point
git diff 2efcc54:main.py main:prod/daily_trend/run_daily_trend.py
```

### To Extract Specific Features
If you want to extract specific logic from V1.0 (e.g., the multi-factor alpha calculation or sentiment gating), you can:
1. View the specific file: `git show 2efcc54:src/features.py`
2. Copy relevant functions
3. Adapt to current codebase structure

---

## ✅ VERIFICATION COMPLETE

**Confirmation:**
- ✅ Found the V1.0 deployment that traded SPY, QQQ, and IWM
- ✅ Located in commit `2efcc54` and tagged as `v1.1-MAG7-READY`
- ✅ Available on multiple branches including `deployment/aws-paper-trading-setup`
- ✅ Configuration confirmed: 5Min (SPY/QQQ) and 3Min (IWM) bars
- ✅ Strategy confirmed: Multi-factor alpha (RSI + Volume + Sentiment)
- ✅ Deployment confirmed: Alpaca Paper Trading
- ✅ NOT an HFT system - Tactical intraday strategy

---

**END OF LOCATION REPORT**

*Magellan V1.0 - SPY/QQQ/IWM Deployment - Successfully Located* 🎯
