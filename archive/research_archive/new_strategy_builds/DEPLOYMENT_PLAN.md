# REGIME SENTIMENT FILTER - DEPLOYMENT PLAN

**Date**: 2026-01-17  
**Status**: Ready for Paper Trading  
**Branch**: `research/new-daily-strategies`

---

## DEPLOYMENT ASSETS

### Tier 1: High Confidence (Deploy First)

**Equities** (Sharpe > 0.8 in bear markets):
- **META** - +147.63% bear (Sharpe 1.67) 🏆
- **NVDA** - +99.30% bear (Sharpe 1.19)
- **QQQ** - +22.19% bear (Sharpe 0.97) ✅ ETF
- **AMZN** - +38.35% bear (Sharpe 0.95)
- **COIN** - +87.47% bear (Sharpe 0.84)

### Tier 2: Solid Performers (Deploy Second)

**Equities**:
- PLTR - +62.35% bear (Sharpe 0.80)
- AAPL - +32.55% bear (Sharpe 1.26)
- MSFT - +22.02% bear (Sharpe 0.72)
- SPY - +9.60% bear (Sharpe 0.66) ✅ ETF
- AMD - +32.17% bear (Sharpe 0.64)
- NFLX - +25.89% bear (Sharpe 0.65)

**Futures**:
- NQUSD - +24.88% bear (Sharpe 1.11)
- ESUSD - +10.64% bear (Sharpe 0.74)

---

## STRATEGY PARAMETERS

### Entry Conditions

**Path 1: Bull Regime**
```python
entry = (RSI_28 > 55) & (SPY > SPY_MA_200) & (news_sentiment > -0.2)
```

**Path 2: Strong Breakout**
```python
entry = (RSI_28 > 65) & (news_sentiment > 0)
```

### Exit Conditions

```python
exit = (RSI_28 < 45) | (news_sentiment < -0.3)
```

### Risk Management

- **Position Size**: 10% of portfolio per asset (max 5 positions = 50% deployed)
- **Stop Loss**: None (strategy-based exits only)
- **Max Drawdown**: Expect 15-30% per asset
- **Rebalance**: Daily (check signals at close)

---

## PAPER TRADING PLAN

### Phase 1: Initial Validation (Week 1-2)

**Deploy on**:
- META, NVDA, QQQ (Tier 1 top 3)

**Monitor**:
- Entry/exit signals vs backtest
- Actual fills vs theoretical
- Slippage and friction
- News sentiment accuracy

**Success Criteria**:
- Signals match backtest expectations
- No major execution issues
- Sharpe > 0.5 (live)

### Phase 2: Expansion (Week 3-4)

**Add**:
- AMZN, COIN, PLTR, AAPL (complete Tier 1)

**Monitor**:
- Portfolio correlation
- Drawdown management
- Trade frequency

**Success Criteria**:
- Portfolio Sharpe > 0.6
- Max portfolio DD < 20%
- Win rate > 50%

### Phase 3: Full Deployment (Week 5+)

**Add**:
- Tier 2 assets (SPY, MSFT, AMD, NFLX)
- Futures (NQUSD, ESUSD) if approved

**Monitor**:
- Long-term performance
- Regime changes
- News sentiment drift

---

## DEPLOYMENT CHECKLIST

### Pre-Deployment

- [ ] Merge `research/new-daily-strategies` to `main`
- [ ] Create asset config files (JSON)
- [ ] Set up news sentiment feed (FMP API)
- [ ] Configure SPY 200 MA calculation
- [ ] Test signal generation on live data
- [ ] Set up monitoring dashboard

### Week 1

- [ ] Deploy META, NVDA, QQQ (paper)
- [ ] Monitor daily signals
- [ ] Log all entries/exits
- [ ] Compare to backtest expectations

### Week 2

- [ ] Review Week 1 performance
- [ ] Adjust if needed (friction, timing)
- [ ] Continue META, NVDA, QQQ

### Week 3-4

- [ ] Add AMZN, COIN, PLTR, AAPL
- [ ] Monitor portfolio metrics
- [ ] Validate correlation assumptions

### Week 5+

- [ ] Full Tier 1 + Tier 2 deployment
- [ ] Consider live trading if paper validates
- [ ] Document any deviations from backtest

---

## MONITORING METRICS

### Daily

- Entry/exit signals generated
- Positions opened/closed
- News sentiment values
- SPY regime status (above/below 200 MA)

### Weekly

- Portfolio return vs buy-hold
- Sharpe ratio (rolling 4-week)
- Max drawdown
- Win rate
- Trade count

### Monthly

- Compare to backtest expectations
- Analyze any underperformance
- Review news sentiment accuracy
- Assess regime filter effectiveness

---

## RISK CONTROLS

### Position Limits

- Max 10% per asset
- Max 50% total deployed
- Max 3 correlated positions (e.g., tech stocks)

### Drawdown Controls

- If portfolio DD > 25%: Reduce position sizes by 50%
- If portfolio DD > 35%: Halt new entries
- If individual asset DD > 40%: Force exit

### News Sentiment Validation

- Manually review news for top 3 positions weekly
- Validate FMP sentiment accuracy
- Flag any sentiment anomalies

---

## EXPECTED PERFORMANCE

### Conservative Estimates (50% of backtest)

**Bear Market**:
- Return: +19% (vs backtest +38%)
- Sharpe: 0.36 (vs backtest 0.72)

**Bull Market**:
- Return: +15% (vs backtest +30%)
- Sharpe: 0.26 (vs backtest 0.52)

### Success Thresholds

**Minimum Acceptable**:
- Sharpe > 0.3 (any market)
- Positive returns in bear markets
- Max DD < 30%

**Target**:
- Sharpe > 0.5
- Beat buy-hold in bear markets
- Match buy-hold in bull markets

---

## NEXT STEPS

1. **Immediate**: Merge branch to main
2. **Today**: Create config files for Tier 1 assets
3. **This Week**: Set up paper trading infrastructure
4. **Next Week**: Deploy META, NVDA, QQQ
5. **Week 3-4**: Expand to full Tier 1
6. **Month 2**: Consider live trading

---

**Status**: ✅ Ready to deploy  
**Confidence**: High (validated across 32 tests)  
**Risk**: Low (paper trading first)
