# IT'S NOT THE SYSTEM - REMEDIATIONS

**Date**: 2026-01-16  
**Purpose**: Identify and remediate actual bottlenecks preventing higher-frequency profitable trading

---

## Executive Summary

**The Magellan system architecture is SOLID.** The limitation is NOT the codebase - it's:
1. **Speed** (execution latency ~500ms, competitors at <10ms)
2. **Data** (using REST polling, not WebSocket streaming)
3. **Costs** (2-3 bps, need sub-1 bps or rebates)
4. **Strategy Alpha** (untested opportunities in our data feeds)

**The Good News**: We have premium subscriptions (FMP Ultimate, Alpaca) that we're DRAMATICALLY underutilizing.

---

## 1. SPEED REMEDIATION

### Current State
- **Execution**: Python + Alpaca REST API = ~500ms round-trip
- **Location**: Running on home laptop with consumer ISP
- **Latency breakdown**:
  - Network: 50-100ms (home → Alpaca)
  - API overhead: 200-300ms (REST synchronous)
  - Python processing: 100-200ms

### What We're Paying For (Not Using)

#### Alpaca WebSocket Streaming
**Current**: Polling REST API every second/minute  
**Available**: Real-time WebSocket streaming

```python
# We have access to:
wss://api.alpaca.markets/stream  # Trade/account updates
wss://data.alpaca.markets/v2/sip # Market data (Stock & Options)
```

**Benefits**:
- **Sub-100ms latency** for market data
- **Instant** trade confirmations
- **Zero polling overhead**

**Alpaca's Infrastructure**:
- Co-located in Secaucus, NJ data center
- Direct fiber to exchanges
- ~20ms internal SIP latency
- **We can access this from AWS us-east-1**

#### FMP WebSocket Streaming (AVAILABLE!)
**Documentation confirms**: FMP Ultimate has WebSocket API for:
- Real-time stock quotes
- News sentiment feeds
- Economic releases

**We're not using this at all.**

### Speed Remediation Strategy

#### Phase 1: WebSocket Migration (Weeks: 1-2)
```
Current: REST polling (500ms)
↓
Target: WebSocket streaming (100ms)
Improvement: 5x faster
```

**Implementation**:
1. Alpaca WebSocket for trades/positions
2. FMP WebSocket for price/news
3. Async Python (`asyncio`) for concurrent processing

**Expected Latency**: 100-150ms

#### Phase 2: AWS Deployment (Weeks: 2-3)
```
Current: Home laptop (random latency)
↓
Target: AWS us-east-1 (near Alpaca servers)
Improvement: Consistent <50ms network latency
```

**Options**:
- **AWS EC2 c6i.2xlarge** (8 vCPU, optimized for compute)
- **AWS Local Zone NYC** (1-2ms to NYSE/NASDAQ)
- **Cluster Placement Group** (minimize inter-instance latency)

**Cost**: ~$200/month EC2 + bandwidth

#### Phase 3: AWS Outposts (Future - If Needed)
```
Current: AWS us-east-1 (50ms)
↓
Target: AWS Outposts co-located with exchange
Improvement: <5ms latency
```

**Cost**: $Hundreds of thousands (only if we scale to $10M+)

### Realistic Speed Target
**Near-term achievable**: 50-100ms execution (10x improvement)  
**Cost**: ~$200/month  
**Effort**: 2-3 weeks

---

## 2. DATA REMEDIATION

### Current State
We're using <10% of FMP Ultimate capabilities.

### FMP Ultimate - What We're NOT Using

#### Available Real-Time Data (PAID FOR)
| Data Type | Current Usage | Available | Latency |
|-----------|---------------|-----------|---------|
| **1-Min Intraday Charts** | ❌ Not used | ✅ All stocks | Real-time |
| **Economic Calendar** | ❌ Not used | ✅ FOMC, CPI, NFP | Pre-scheduled |
| **News Sentiment** | ⚠️ Batch only | ✅ WebSocket stream | <1s from release |
| **Insider Trades** | ❌ Not used | ✅ All filings | Same-day |
| **13F Institutional** | ❌ Not used | ✅ All holders | Quarterly |
| **Earnings Transcripts** | ❌ Not used | ✅ Full text | Same day |
| **Technical Indicators** | ❌ Calculating manually | ✅ Pre-calculated | Real-time |
| **Senate/House Trades** | ❌ Not used | ✅ All disclosures | Real-time |
| **Options Flow** | ❌ Not used | ✅ Unusual activity | Real-time |

#### Data We Can Access RIGHT NOW

**Economic Data**:
- Treasury rates (real-time)
- Economic indicators (CPI, GDP, NFP)
- **Economic calendar with exact release times**

**Alternative Data**:
- Reddit sentiment (via external APIs)
- Twitter/X mentions
- Google Trends correlation

### Data Remediation Strategy

#### Quick Wins (Week 1)
1. **Enable FMP WebSocket** for news
2. **Economic calendar integration** for event straddles
3. **Technical indicators API** (stop calculating RSI manually)

#### Medium-term (Weeks 2-4)
1. **News-driven momentum** (trade within 1s of news)
2. **Insider trade signals** (cluster detection)
3. **13F flow-following** (institutional positioning)

#### Advanced (Months 2-3)
1. **Options flow tracking** (unusual activity)
2. **Earnings transcript sentiment** (ML on text)
3. **Congressional trade following** (Pelosi tracker)

---

## 3. COST REMEDIATION

### Current State
- **Alpaca commission**: $0 per trade ✅
- **Slippage**: 1-3 bps (market orders)
- **Effective cost**: 2-3 bps per round-trip

### Breakdown
**For a $10,000 trade**:
- Entry: $10,000 * 0.0003 = $3
- Exit: $10,000 * 0.0003 = $3
- **Total friction**: $6 = 6 bps on $10k

**Impact**: Any alpha <6 bps is wiped out.

### Cost Remediation Strategy

#### Immediate (Free)
1. **Limit orders instead of market** (earn spread, don't pay)
2. **Larger positions** (fixed costs spread over more $)
3. **Longer holds** (amortize costs over bigger moves)

#### Medium-term
1. **Alpaca Algo Trader Plus** subscription
   - NBBO access (best execution)
   - Smart order routing
   - **Potentially negative costs** via rebates

2. **Options instead of equity**
   - More leverage = lower friction as % of notional
   - Earnings straddles already do this

#### Advanced (If Scaling Past $1M)
1. **Market making** instead of taking
2. **Direct market access** (DMA)
3. **Multiple brokers** for routing optimization

### Realistic Cost Target
**Current**: 3-6 bps  
**Near-term**: 1-2 bps (better execution)  
**Long-term**: <1 bps or net rebates

---

## 4. STRATEGY ALPHA OPPORTUNITIES

### Untested Strategies Using Available Data

#### 4A: News-Driven Momentum (<100ms trades)
**Example from GitHub**: ChatGPTTradingBot achieves 5-70ms news→trade

**Our advantages**:
- FMP Ultimate news WebSocket
- Alpaca WebSocket execution
- AWS us-east-1 deployment

**Strategy**:
```python
1. FMP news arrives with sentiment score
2. If sentiment > 0.7 → BUY within 100ms
3. Hold for 30-60 seconds
4. Exit with 0.5-1% profit target
```

**Expected Sharpe**: 1.5-2.0 (if fast enough)  
**Trades/day**: 5-20  
**Capital**: $10k-50k per trade

#### 4B: Economic Release Straddles
**Data available**: FMP Economic Calendar with exact release times

**Strategy**:
```python
Events: CPI, NFP, GDP, FOMC
Entry: 5 minutes before release
Exit: 5 minutes after release
Asset: SPY/QQQ ATM straddles
```

**Why it failed before**: We tested DAILY straddles (hold overnight)  
**Why it works now**: Enter 5min before, exit 5min after (capture instant move)

**Expected Sharpe**: 1.0-1.5  
**Trades/year**: 50-60 events

#### 4C: Insider Trade Clustering
**Data available**: FMP Insider Trades (same-day)

**Strategy**:
```python
1. Track all insider buys for MAG7
2. When 3+ insiders buy within 7 days → Signal
3. Buy stock, hold 20 days
4. Exit or trail stop
```

**Expected Sharpe**: 0.8-1.2  
**Trades/year**: 10-20

#### 4D: 13F Hedge Fund Following
**Data available**: FMP 13F filings with analytics

**Strategy**:
```python
1. Track top 10 hedge funds (Buffett, Ackman, etc.)
2. When new 13F shows NEW position → copy within 5 days
3. Hold for 90 days (one quarter)
4. Rebalance on next 13F
```

**Expected Sharpe**: 0.5-0.8 (lower but reliable)  
**Trades/quarter**: 5-10

#### 4E: Options Flow Following
**Data available**: FMP unusual options activity

**Strategy**:
```python
1. Detect unusual call volume (10x average)
2. If smart-money indicators present → copy trade
3. Buy same-strike calls within 1 hour
4. Hold until earnings or 30 days
```

**Expected Sharpe**: 1.0-1.5  
**Trades/month**: 2-5

#### 4F: Enhanced Earnings Straddles
**Current**: 2 days before, 1 day after  
**Enhancement using FMP data**:

```python
1. Use earnings transcript sentiment (FMP API)
2. If transcript sentiment > 0.5 → early exit (same day)
3. If sentiment < 0 → hold longer (3 days)
```

**Expected improvement**: +20-30% Sharpe

---

## 5. INFRASTRUCTURE RECOMMENDATIONS

### Tier 1: Low-Hanging Fruit (Weeks 1-2, ~$0 cost)
1. ✅ Migrate to WebSocket (Alpaca + FMP)
2. ✅ Switch to limit orders
3. ✅ Enable FMP economic calendar
4. ✅ Test news-driven momentum backtest

**Expected Impact**: 5-10x latency improvement, new strategy opportunities

### Tier 2: AWS Deployment (Weeks 2-4, ~$200/mo)
1. ✅ EC2 c6i.2xlarge in us-east-1
2. ✅ Cluster Placement Group
3. ✅ Direct Connect (if scaling past $1M)
4. ✅ WebSocket-optimized Python code

**Expected Impact**: Consistent <100ms execution, 24/7 uptime

### Tier 3: Advanced (Months 2-3, ~$500/mo)
1. ✅ AWS Local Zone NYC (1-2ms to exchanges)
2. ✅ Multiple broker failover
3. ✅ Redis for state management
4. ✅ Prometheus/Grafana monitoring

**Expected Impact**: Production-grade reliability

---

## 6. PRIORITY ACTION PLAN

### Week 1: Proof of Concept
```
Day 1-2: FMP WebSocket news + Alpaca WebSocket trades
Day 3-4: Backtest news-driven momentum
Day 5: Economic calendar integration
Day 6-7: Deploy simple version locally
```

**Deliverable**: Working news-momentum strategy with <200ms latency

### Week 2: AWS Migration
```
Day 1-2: Set up EC2 + deploy code
Day 3-4: Test latency improvements
Day 5-7: Paper trade for 3 days
```

**Deliverable**: Production deployment with <100ms latency

### Week 3-4: Strategy Expansion
```
Week 3: Economic release straddles
Week 4: Insider trade clustering
```

**Deliverable**: 2-3 new strategies tested

### Month 2-3: Scale
```
Deploy AWS Local Zone if needed
Add 13F following
Add options flow
```

**Deliverable**: Full multi-strategy system

---

## 7. TECHNOLOGY STACK UPGRADES

### Current Stack
```
Python 3.x
Alpaca REST API
FMP REST API
Home laptop
Manual indicator calculation
```

### Upgraded Stack
```
Python 3.11+ with asyncio
Alpaca WebSocket (real-time trades)
FMP WebSocket (real-time news/data)
FMP SDK (optimized)
AWS EC2 us-east-1
Pre-calculated technical indicators (FMP API)
Redis for caching
```

### Code Architecture Changes

#### Current: Synchronous/Polling
```python
# Bad: REST polling every 1 second
while True:
    data = alpaca.get_bars(...)
    process(data)
    time.sleep(1)  # Waste 1 second
```

#### Target: Asynchronous/Event-Driven
```python
# Good: WebSocket streaming
async def on_trade(trade):
    # Process instantly, no sleep
    await process(trade)

await alpaca_ws.subscribe_trades(on_trade)
```

---

## 8. COST-BENEFIT ANALYSIS

### Remediation Investments

| Remediation | Time | Cost/Month | Latency Improvement | Expected Sharpe Gain |
|-------------|------|------------|---------------------|----------------------|
| WebSocket migration | 1 week | $0 | 500ms → 100ms (5x) | +0.5-1.0 |
| AWS us-east-1 | 1 week | $200 | 100ms → 50ms (2x) | +0.2-0.5 |
| News momentum strategy | 2 weeks | $0 | N/A | +1.0-1.5 Sharpe |
| Economic straddles | 1 week | $0 | N/A | +0.5-1.0 Sharpe |
| AWS Local Zone | Future | $500 | 50ms → 2ms (25x) | +0.3-0.5 |

**Total near-term**: 4 weeks, $200/month, expected +2.0-3.0 Sharpe

---

## 9. EXTERNAL LIBRARIES & TOOLS

### Available Tools We Should Use

#### FMP Python SDK
**Repository**: Official FMP SDK  
**Benefit**: Optimized API calls, built-in caching, faster than raw requests

#### Alpaca-py
**Repository**: Official Alpaca Python SDK  
**Benefit**: WebSocket handling, async support, production-tested

#### Finance Toolkit
**Repository**: GitHub - Powered by FMP  
**Benefit**: 200+ indicators pre-calculated, no manual engineering

#### TA-Lib (Technical Analysis)
**Repository**: mrjbq7/ta-lib  
**Benefit**: Fast C-based indicator calculation (backup to FMP API)

---

## 10. BENCHMARKING TARGETS

### Latency Benchmarks

| Metric | Current | Target (Phase 1) | Target (Phase 2) | Elite HFT |
|--------|---------|------------------|------------------|-----------|
| Data latency | 1000ms | 100ms | 20ms | <1ms |
| Order execution | 500ms | 100ms | 50ms | <10ms |
| News→Trade | N/A | 500ms | 100ms | 20ms |
| Total round-trip | 2000ms | 300ms | 100ms | <50ms |

### Strategy Performance Targets

| Strategy | Est. Sharpe | Trades/Year | Capital Required |
|----------|-------------|-------------|------------------|
| News momentum | 1.5-2.0 | 500-1000 | $10k-50k |
| Economic straddles | 1.0-1.5 | 50-60 | $5k-20k |
| Insider following | 0.8-1.2 | 10-20 | $20k-50k |
| Enhanced earnings | 3.0-3.5 | 28 | $5k-15k |

---

## CONCLUSION

**The system is NOT the problem. We are underutilizing paid capabilities.**

### Immediate Actions (This Week)
1. ✅ Enable Alpaca WebSocket
2. ✅ Enable FMP WebSocket
3. ✅ Test news-driven momentum
4. ✅ Integrate economic calendar

### Expected Outcomes
- **10x faster execution** (500ms → 50ms)
- **2-3 new Sharpe 1.0+ strategies**
- **~$200/month infrastructure cost**
- **Production-ready in 4 weeks**

**We have everything we need. Let's use it.**
