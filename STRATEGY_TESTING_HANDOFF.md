# STRATEGY TESTING HANDOFF - PHASE 2

**Date**: 2026-01-16  
**From**: Phase 1 POC (Infrastructure Validation)  
**To**: Phase 2 (Strategy Discovery & Testing)  
**Branch**: `main` (all changes merged & pushed)

---

## 🔴 HFT RESEARCH UPDATE (2026-01-16)

**STATUS**: ✅ **COMPLETED - ALL HFT STRATEGIES REJECTED**

**What was tested**:
- 6 HFT strategies (Liquidity Grab, Range Scalping, Opening Range, Mean Reversion, VWAP, Momentum)
- 7 asset classes (SPY, QQQ, IWM, NVDA, TSLA, ES, NQ)
- Full-year validation on 4 best strategies (2024 + 2025 = 504 days)

**Result**: **ALL STRATEGIES FAILED** after full-year validation
- Q1 samples showed false positives (Sharpe 0.84 to 2.04)
- Full-year testing revealed losses (Sharpe -0.21 to -1.91)
- **Sample bias is severe**: Average Sharpe collapse of -2.29 points

**Verdict**: **HFT NOT VIABLE** with residential latency + realistic friction

**See**: `research/high_frequency/HFT_FINAL_RESEARCH_SUMMARY.md`

**Recommendation**: Focus on **FOMC Event Straddles** (Sharpe 1.17, validated)

---


## YOUR ROLE

**You are a quantitative trading strategist with extensive experience in:**
- High-frequency and algorithmic trading strategy development
- Walk-forward analysis and rigorous backtesting methodologies
- Options strategies (volatility trading, event-driven, income generation)
- Market microstructure and latency-sensitive execution
- Statistical validation and risk management

**Your mission**: Discover and validate NEW profitable trading strategies using the upgraded infrastructure capabilities revealed in Phase 1.

---

## CRITICAL CONTEXT: WHAT CHANGED

### Infrastructure Breakthrough
**Phase 1 POC discovered our system is 7.5x faster than assumed:**
- **Actual latency**: 67ms median (South Texas → Virginia)
- **Previous assumption**: 500ms
- **Implication**: High-frequency strategies are NOW VIABLE

### New Capabilities Unlocked
1. **FMP Ultimate** (`/stable` endpoints working):
   - Economic calendar (946 events)
   - 1-minute bars (full coverage)
   - News WebSocket (untested)
   - Insider trades, 13F, Congressional trades (untested)

2. **Alpaca Premium**:
   - WebSocket streaming (code ready, needs market hours)
   - <100ms execution possible

3. **Existing WFA Validated** (NO retesting needed):
   - Premium Selling: NO-GO (Sharpe 0.36)
   - Earnings Straddles: GO (Sharpe 2.91)
   - Daily Hysteresis: NO-GO (Sharpe 0.22)

---

## YOUR PRIORITIES (IN ORDER)

### TIER 1: IMMEDIATE TESTING (Week 1-2)

#### 1. Event Straddles (FOMC/CPI/NFP) ⭐ TOP PRIORITY
**Status**: Partially validated (Sharpe 1.19 on 3 FOMC events)  
**What to do**:
- [ ] Backtest full 2024 calendar (8 FOMC + 12 CPI + 12 NFP = 32 events)
- [ ] Get pre-market data for 8:30 AM events (CPI/NFP)
- [ ] Paper trade Jan 27 FOMC (upcoming!)
- [ ] Build auto-execution system (T-5min entry)

**Files**:
- POC code: `research/websocket_poc/event_straddle_backtest.py`
- Calendar: `research/websocket_poc/economic_calendar.json`

**Expected Sharpe**: 1.0-1.5  
**Capital**: $5k-20k per trade  
**Trades/year**: 20-30

---

#### 2. News-Driven Momentum 🆕 HIGH-FREQUENCY
**Status**: Not tested (but 67ms enables it)  
**What to do**:
- [ ] Test FMP news WebSocket during market hours
- [ ] Build sentiment filter (positive >80 OR negative <20)
- [ ] Backtest on 2024 news events
- [ ] Measure latency: news→parse→execute

**Strategy**:
```
Entry: <500ms after breaking news
Hold: 30-60 seconds
Target: 0.5-1% move
Exit: Profit target OR 30-sec timeout
```

**Expected Sharpe**: 1.5-2.0  
**Trades/day**: 5-20  
**Latency requirement**: <100ms (we have 67ms ✅)

**GitHub Reference**: ChatGPTTradingBot achieves 5-70ms execution using same tools

---

#### 3. Intraday Scalping (1-5 min holds) ✅ COMPLETED - NO-GO
**Status**: ❌ **EXHAUSTIVELY TESTED - ALL STRATEGIES FAILED**  
**Research completed**: 2026-01-16  

**What was tested** (6 strategies, 7 asset classes, full-year validation):
- ✅ Liquidity Grab (QQQ): Q1 Sharpe 0.84 → Full year -1.91 ❌
- ✅ Range Scalping (ES): Q1 Sharpe 1.29 → Full year -0.21 ❌
- ✅ Opening Range Breakout (QQQ): Q1 Sharpe 0.99 → Full year -1.64 ❌
- ✅ Mean Reversion (NVDA): Q1 Sharpe 2.04 → Full year -0.23 ❌
- ✅ VWAP Scalping (SPY): Sharpe -4.32 ❌
- ✅ Momentum Scalping (SPY): Sharpe -3.64 ❌

**Critical finding**: **SEVERE SAMPLE BIAS**
- 30-day samples showed false positives (Sharpe 0.84 to 2.04)
- Full-year testing revealed true performance (all negative)
- Average Sharpe collapse: -2.29 points

**Why ALL strategies failed**:
- Win rates 25-60% insufficient to overcome friction
- 1.0 bps friction × 5-7 trades/day = 12-17% annual friction
- Avg losses often exceed avg wins
- Market regimes change - Q1 not representative

**See**: `research/high_frequency/HFT_FINAL_RESEARCH_SUMMARY.md`

**Verdict**: HFT NOT VIABLE with residential latency + realistic friction

**Strategy**:
```
Timeframe: 1-minute bars (SPY/QQQ)
Signals: RSI(5) extremes OR VWAP reversals
Entry: Fast breakouts/reversals
Target: 0.10-0.25%
Stop: 0.10%
Max hold: 5 minutes
```

**Expected Sharpe**: 0.8-1.2 (if latency advantage holds)  
**Trades/day**: 10-30  
**Risk**: HIGH - needs extensive validation

---

### TIER 2: ENHANCEMENTS (Week 3-4)

#### 4. Enhanced Earnings Straddles
**Current**: Sharpe 2.91 (1-day hold)  
**Enhancement**: Add FMP earnings transcript sentiment for early exits

**What to do**:
- [ ] Access FMP earnings transcript API
- [ ] Build sentiment parser (keywords or LLM)
- [ ] Backtest on 2024 earnings with sentiment exits

**Expected improvement**: +20-30% Sharpe (2.91 → 3.5-3.8)

---

#### 5. Alternative Data Strategies
**Status**: Proven externally, untested by us

**A) Insider Trade Clustering**:
- Signal: 3+ insiders buy within 7 days
- Expected Sharpe: 0.8-1.2

**B) 13F Following**:
- Signal: New positions by top hedge funds
- Expected Sharpe: 0.5-0.8

**C) Congressional Trade Following** ("Pelosi Tracker"):
- Signal: Senator/Representative buys
- Expected Sharpe: 0.8-1.5

**What to do**:
- [ ] Access FMP insider/13F/Congress APIs
- [ ] Backtest on 2024 data
- [ ] Build monitoring dashboard

---

## MANDATORY PROTOCOLS

### Git Workflow (STRICT)
```bash
# For EVERY new strategy test:
1. Create feature branch: git checkout -b feature/strategy-name
2. Work in research/ directory (NOT src/)
3. Commit frequently: git commit -m "test: description"
4. Merge to main when validated
5. Push regularly
```

**Branch naming**:
- `feature/event-straddles-full` (strategy testing)
- `feature/news-momentum-poc` (new POC)
- `research/scalping-viability` (research only)

### Model Selection (CRITICAL)
Use the RIGHT model for each task:

| Task Type | Model | Why |
|-----------|-------|-----|
| Complex async code (WebSocket) | Claude Sonnet 4.5 Thinking | Handles event loops |
| Backtesting (WFA, validation) | Claude Opus 4.5 | Statistical rigor |
| Simple edits, documentation | Gemini Flash 2.0 | Fast, cheap |
| Strategy design, planning | Claude Sonnet 4.5 Thinking | Creative problem-solving |

### Testing Standards
**Every strategy MUST have**:
1. ✅ Backtest on ≥50 trades (or ≥1 year data)
2. ✅ Walk-forward analysis (if multi-parameter)
3. ✅ Sharpe ratio ≥1.0 for GO decision
4. ✅ Realistic slippage/commissions
5. ✅ Paper trading (≥2 trades before live)

### Documentation Requirements
**For each strategy tested, create**:
- `research/[strategy-name]/README.md` (overview)
- `research/[strategy-name]/backtest_results.json` (metrics)
- `research/[strategy-name]/[strategy-name]_backtest.py` (code)

**Update these artifacts**:
- `task.md` (track progress)
- `PHASE2_RESULTS.md` (findings summary)

---

## KEY DOCUMENTATION TO READ FIRST

### Phase 1 Findings (READ THESE)
1. **`PHASE1_FINAL_REPORT.md`** (brain/) - Full POC results ⭐ START HERE
2. **`POC_RESULTS.md`** (brain/) - Detailed latency findings
3. **`research/capabilities_research/fmp_ultimate_audit.md`** - FMP features
4. **`research/capabilities_research/alpaca_premium_audit.md`** - Alpaca features

### WFA Validation (Reference)
1. **`WFA_RESULTS_COMPREHENSIVE.md`** (brain/) - All 3 strategies tested
2. **`GO_NO_GO_DECISIONS.md`** (brain/) - Final decisions
3. **`research/backtests/phase4_audit/wfa_core.py`** - Reusable WFA functions

### POC Code (Working Examples)
1. **`research/websocket_poc/event_straddle_backtest.py`** - Event straddles
2. **`research/websocket_poc/rest_latency_test.py`** - Latency benchmark
3. **`research/websocket_poc/economic_calendar.py`** - FMP calendar
4. **`research/websocket_poc/alpaca_ws_poc.py`** - WebSocket (needs market hours)

---

## DECISION FRAMEWORK

### GO Criteria (Deploy to Paper Trading)
- Sharpe ≥1.5 (strong edge)
- Win rate ≥50%
- ≥50 trades OR ≥1 year data
- Passes WFA (if multi-parameter)
- Realistic execution assumptions

### CONDITIONAL (More Testing)
- Sharpe 1.0-1.5 (moderate edge)
- Needs parameter tuning
- Limited sample size
- Execution risk unclear

### NO-GO (Archive)
- Sharpe <1.0
- Overfit (WFA degradation >30%)
- Unrealistic assumptions
- Too capital intensive

---

## EXPECTED DELIVERABLES

### Week 1-2
- [ ] Event straddles: Full 2024 backtest
- [ ] WebSocket: Tested during market hours
- [ ] News momentum: POC tested
- [ ] Jan 27 FOMC: Paper traded

### Week 3-4
- [ ] Scalping: Viability assessment
- [ ] Enhanced earnings: Sentiment integration
- [ ] Alternative data: API access + initial backtest

### End of Phase 2
- [ ] `PHASE2_RESULTS.md` - All findings
- [ ] ≥2 new strategies validated (Sharpe >1.0)
- [ ] Production deployment plan
- [ ] Updated `task.md`

---

## RISK WARNINGS

### High-Risk Areas
1. **Intraday scalping**: Tight margins, high slippage sensitivity
2. **News momentum**: Execution speed critical (<100ms)
3. **AWS costs**: $200-500/mo if deployed

### Common Pitfalls
1. ❌ Testing on in-sample data (use WFA!)
2. ❌ Ignoring slippage/commissions
3. ❌ Overfitting parameters
4. ❌ Not testing during market hours
5. ❌ Assuming fills at mid-price

---

## QUICK START CHECKLIST

**Before you start coding**:
- [ ] Read `PHASE1_FINAL_REPORT.md` (brain/)
- [ ] Review `WFA_RESULTS_COMPREHENSIVE.md` (brain/)
- [ ] Check `research/websocket_poc/` POC code
- [ ] Verify git on `main` branch, clean working tree

**First task**:
- [ ] Create branch: `git checkout -b feature/event-straddles-full`
- [ ] Run: `python research/websocket_poc/event_straddle_backtest.py`
- [ ] Extend to full 2024 calendar (20 events)
- [ ] Document results

**Model to use**: Claude Opus 4.5 (backtesting rigor)

---

## COMMUNICATION PROTOCOL

### When to ask user
- Strategy shows Sharpe >1.5 (GO decision)
- Strategy shows Sharpe <0.5 (NO-GO decision)
- Need to deploy AWS ($200+/mo cost)
- Found critical bug in existing code
- Uncertain about parameter choices

### When to proceed autonomously
- Backtesting (standard WFA)
- Code refactoring
- Documentation updates
- Branch management
- POC testing

---

## SUCCESS METRICS

**Phase 2 is successful if**:
1. ✅ ≥2 new strategies validated (Sharpe >1.0)
2. ✅ Event straddles fully tested (20+ events)
3. ✅ WebSocket working during market hours
4. ✅ Clear GO/NO-GO on news momentum
5. ✅ Scalping viability determined

**Stretch goals**:
- 3+ strategies validated
- Alternative data integrated
- AWS deployment plan ready

---

## FINAL NOTES

**You have a Ferrari** (67ms latency) - don't drive it like a Prius (500ms strategies).

**The infrastructure is ready** - focus on finding alpha, not fixing plumbing.

**Be rigorous** - WFA everything, assume realistic execution, validate on paper trades.

**Git hygiene matters** - new branch per strategy, commit often, merge when validated.

**Good luck!** 🚀

---

**Questions? Check**:
- `PHASE1_FINAL_REPORT.md` (comprehensive)
- `research/websocket_poc/HANDOFF_CONTEXT.md` (POC details)
- `WFA_RESULTS_COMPREHENSIVE.md` (validation methodology)
