# FMP ULTIMATE - COMPLETE CAPABILITIES AUDIT

**Subscription**: Ultimate Plan  
**Cost**: Premium tier  
**API Limits**: 3,000 calls/minute, 150GB/month bandwidth

---

## TIER INHERITANCE

Ultimate includes **EVERYTHING** from lower tiers:
- ✅ Basic (250 calls/day)
- ✅ Starter (300 calls/min, 5 years history)
- ✅ Premium (750 calls/min, 30 years history, intraday charts, technical indicators)
- ✅ **PLUS Ultimate exclusive features**

---

## ULTIMATE-EXCLUSIVE FEATURES

### 1. Global Coverage
- All US stocks ✅ (using)
- Canada ✅
- UK ✅
- Europe ✅
- Asia-Pacific ✅
- **Status**: NOT using international data

### 2. 1-Minute Intraday Charting
**Endpoints**:
- `/historical-chart/1min/{symbol}`
- Date range: Full historical access
- **Status**: ❌ NOT USING - we calculate from daily

**Impact**: Could enable:
- Intraday momentum strategies
- Opening range breakouts
- News momentum (1-min reaction time)

### 3. Earnings Call Transcripts
**Endpoint**: `/earning_call_transcript/{symbol}`
- Full text of earnings calls
- Same-day availability
- Sentiment analysis possible
- **Status**: ❌ NOT USING

**Impact**: Could enhance earnings straddles with:
- Transcript sentiment → early exit signals
- CEO tone analysis

### 4. ETF & Mutual Fund Holdings
**Endpoints**:
- `/etf-holder/{symbol}` - who holds what
- `/etf-stock-exposure/{symbol}` - portfolio breakdown
- **Status**: ❌ NOT USING

**Impact**: Could enable:
- ETF arbitrage (holdings vs price)
- Flow-through analysis (when ETFs rebalance)

### 5. 13F Institutional Holdings
**Endpoints**:
- `/form-thirteen/{cik}` - hedge fund positions
- `/institutional-ownership/symbol-ownership` - specific stock holders
- `/institutional-holder/portfolio-position-summary` - full portfolio
- **Status**: ❌ NOT USING

**Impact**: Could enable:
- Hedge fund following strategy
- Smart money tracking
- Position clustering signals

### 6. Bulk & Batch Delivery
**Endpoints**: All major endpoints support bulk export
- Download all data at once
- Reduced API call count
- **Status**: ❌ NOT USING

**Impact**: Could enable:
- Faster backtests
- Universe screening (scan 1000s of stocks)

---

## ALL AVAILABLE ENDPOINTS (BY CATEGORY)

### Company Data
| Endpoint | Tier | Using? |
|----------|------|--------|
| Company Profile | Basic | ✅ |
| Market Cap | Premium | ❌ |
| Employee Count | Premium | ❌ |
| Share Float | Premium | ❌ |
| Executives | Premium | ❌ |

### Financial Statements
| Endpoint | Tier | Using? |
|----------|------|--------|
| Income Statement | Starter | ❌ |
| Balance Sheet | Starter | ❌ |
| Cash Flow | Starter | ❌ |
| Financial Ratios | Starter | ❌ |
| Key Metrics TTM | Premium | ❌ |

### Market Data
| Endpoint | Tier | Using? |
|----------|------|--------|
| Real-time Quote | Starter | ⚠️ Via Alpaca |
| 1-Min Chart | **Ultimate** | ❌ |
| 5-Min Chart | Premium | ❌ |
| 1-Hour Chart | Premium | ⚠️ Calculating manually |
| Historical Daily | Basic | ✅ |

### News & Sentiment
| Endpoint | Tier | Using? |
|----------|------|--------|
| Stock News | Premium | ✅ |
| Press Releases | Premium | ❌ |
| General News | Premium | ❌ |
| News Sentiment | Premium | ⚠️ Batch only |

### Economic Data
| Endpoint | Tier | Using? |
|----------|------|--------|
| Treasury Rates | Premium | ❌ |
| Economic Indicators | Premium | ❌ |
| **Economic Calendar** | Premium | ❌ **HIGH VALUE** |
| Market Risk Premium | Premium | ❌ |

### Earnings & Events
| Endpoint | Tier | Using? |
|----------|------|--------|
| Earnings Calendar | Premium | ⚠️ Manual list |
| Dividends Calendar | Premium | ❌ |
| **Earnings Transcripts** | **Ultimate** | ❌ **HIGH VALUE** |
| IPO Calendar | Premium | ❌ |
| Stock Splits Calendar | Premium | ❌ |

### Insider & Institutional
| Endpoint | Tier | Using? |
|----------|------|--------|
| **Insider Trades** | Premium | ❌ **HIGH VALUE** |
| **Senate Trading** | Premium | ❌ **HIGH VALUE** |
| **House Trading** | Premium | ❌ **HIGH VALUE** |
| **13F Holdings** | **Ultimate** | ❌ **HIGH VALUE** |

### Technical Indicators
| Endpoint | Tier | Using? |
|----------|------|--------|
| RSI | Premium | ❌ Calculating manually |
| SMA | Premium | ❌ Calculating manually |
| EMA | Premium | ❌ Calculating manually |
| MACD | Premium | ❌ Calculating manually |
| Bollinger Bands | Premium | ❌ Calculating manually |
| ADX | Premium | ❌ |
| Williams %R | Premium | ❌ |

### Analyst & Ratings
| Endpoint | Tier | Using? |
|----------|------|--------|
| Analyst Estimates | Premium | ❌ |
| Price Targets | Premium | ❌ |
| Stock Grades | Premium | ❌ |
| Upgrades/Downgrades | Premium | ❌ |

### ETF & Funds
| Endpoint | Tier | Using? |
|----------|------|--------|
| **ETF Holdings** | **Ultimate** | ❌ |
| Fund Information | Premium | ❌ |
| Sector Weighting | Premium | ❌ |

### Commodities, Crypto, Forex
| Endpoint | Tier | Using? |
|----------|------|--------|
| Crypto Quotes | Starter | ❌ |
| Forex Pairs | Starter | ❌ |
| Commodities | Premium | ❌ |
| All with 1-min charts | Premium | ❌ |

---

## WEBSOCKET API (AVAILABLE)

**Confirmed**: FMP Ultimate has WebSocket streaming for:
1. Real-time stock quotes
2. News releases with timestamps
3. Economic data releases

**Latency**: <1 second from event to delivery

**Status**: ❌ **NOT USING WEBSOCKETS AT ALL**

---

## HIGH-VALUE UNUSED ENDPOINTS

### Immediate Opportunities

1. **Economic Calendar** (`/economic_calendar`)
   - Exact release times for CPI, NFP, FOMC
   - Use for: Event straddles with precise entry

2. **Insider Trades** (`/insider-trading`)
   - Same-day reporting of all insider buys/sells
   - Use for: Cluster detection, smart money following

3. **Earnings Transcripts** (`/earning_call_transcript`)
   - Full text, same-day availability
   - Use for: Enhanced earnings straddle exit signals

4. **13F Holdings** (`/form-thirteen`)
   - Hedge fund positions, quarterly updates
   - Use for: Copy-trading top investors

5. **Senate/House Trades** (`/senate-trading`, `/house-disclosure`)
   - Congressional trades in real-time
   - Use for: Political alpha ("Pelosi tracker")

6. **Pre-calculated Technical Indicators**
   - Stop calculating RSI, MA, etc. manually
   - Use FMP API for instant access

---

## RECOMMENDED USAGE PRIORITIES

### Priority 1 (This Week)
1. ✅ Enable WebSocket streaming
2. ✅ Economic Calendar integration
3. ✅ Switch to pre-calculated technical indicators

### Priority 2 (Next 2 Weeks)
1. ✅ 1-minute intraday charting
2. ✅ Insider trades monitoring
3. ✅ News sentiment WebSocket

### Priority 3 (Month 2)
1. ✅ Earnings transcripts for sentiment
2. ✅ 13F hedge fund following
3. ✅ Senate/House trade tracking

---

## BANDWIDTH OPTIMIZATION

**Current usage**: <1GB/month (only using daily bars + news)  
**Limit**: 150GB/month  
**Headroom**: 149GB unused!

We can:
- Pull 1-min data for 100s of stocks
- Stream real-time quotes
- Download bulk historical data
- **Without worry about limits**

---

## API RATE LIMITS

**Current usage**: ~100 calls/minute (backtesting)  
**Limit**: 3,000 calls/minute  
**Headroom**: 30x unused capacity

We can:
- Scan entire S&P 500 in seconds
- Real-time monitoring of 100s of stocks
- Backtests across huge universes

---

## PYTHON SDK

**Available**: Official FMP Python SDK  
**Features**:
- Optimized API calls
- Built-in caching
- Rate limit handling
- WebSocket support
- **Status**: ❌ NOT USING

**Benefit**: 2-3x faster than raw `requests` library

---

## CONCLUSION

**We're using <5% of FMP Ultimate capabilities.**

**Highest ROI opportunities**:
1. WebSocket streaming (instant news/quotes)
2. Economic calendar (precise event timing)
3. Insider trades (smart money signals)
4. Pre-calculated indicators (stop reinventing wheel)

**Next step**: Implement Phase 1 remediations from main doc.
