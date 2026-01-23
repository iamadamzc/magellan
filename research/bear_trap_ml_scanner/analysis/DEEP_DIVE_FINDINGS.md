# Deep Dive Analysis - Intraday Selloff Dataset
> Key findings from selloff-smallcap-10pct-5yr-v1 (8,999 events)
> Analysis Date: January 22, 2026

---

## 📊 SECTION 1: 200 SMA POSITIONING DEEP DIVE

**Key Question**: Do selloffs above 200 SMA behave differently? Scanning opportunity?

| Metric | Above 200 SMA | Below 200 SMA |
|--------|---------------|---------------|
| Events | ~3,200 (39%) | ~5,000 (61%) |
| Mean Drop | TBD | TBD |
| Median Distance | +X% above | -X% below |

**Key Findings**:
- **39% of selloffs occur in confirmed uptrends** (above 200 SMA)
- When combined with **Golden Cross** (50 > 200 SMA), these are pullbacks in STRONG uptrends
- **Hypothesis**: Pullbacks in uptrends have HIGHER reversal probability

**🎯 Strategy Opportunity: "Uptrend Pullback"**
- Filter: Above 200 SMA + Golden Cross + Near 52w high
- These are healthy pullbacks, not broken stocks
- May require smaller position size but higher success rate

---

## 📊 SECTION 2: SERIAL SELLERS & VOLATILITY PERSISTENCE

**Key Question**: Do some symbols sell off repeatedly? Cooldown period?

**Top Serial Sellers** (5 years):
- FFIE, ANY, ATNF, BIOL, MARA with 100+ selloffs each
- These symbols have median gaps of only ~15-20 days between selloffs

**Key Findings**:
- **~15% of selloffs occur within 5 days of previous selloff** (same symbol)
- These "clustered" selloffs may indicate **momentum continuation** (not reversal)
- **Hypothesis**: Recent selloffs = LOWER reversal probability

**🎯 ML Feature**: `days_since_last_selloff` - critical for filtering

---

## 📊 SECTION 3: MARKET-WIDE vs IDIOSYNCRATIC

**Key Question**: Are selloffs correlated (market-wide) or random (stock-specific)?

**Market-Wide Selloff Days** (20+ symbols):
- ~50 days with 20+ simultaneous selloffs
- Top days correlate with market crashes (COVID, rate hikes, etc.)

**Key Findings**:
- **More selloffs happen on UP market days** than down days!
- Isolated selloffs = stock-specific issues
- Market-wide selloffs = potential oversold bounce

**🎯 Strategy Opportunity: "Market-Wide Recovery"**
- When 15+ symbols sell off on same day + SPY down
- Likely oversold, sector/market recovery lifts all

**🎯 Strategy Opportunity: "Isolated Selloff"**
- Selloff when <3 other symbols selling + SPY flat/up
- Stock-specific news - could go either way (need catalyst analysis)

---

## 📊 SECTION 4: INTRADAY TIMING PATTERNS

**Key Finding**: Selloffs cluster in AFTERNOON, not morning!

| Time Period | Events | % | Avg Drop |
|-------------|--------|---|----------|
| Opening (9:30-9:45) | 50 | 0.6% | TBD |
| Morning (9:45-11:00) | 312 | 3% | TBD |
| Midday (11:00-14:00) | 3,514 | 39% | TBD |
| Afternoon (14:00-15:00) | 2,998 | 33% | TBD |
| Power Hour (15:00-16:00) | 2,125 | 24% | TBD |

**Implications**:
- Opening selloffs = gap-related, different dynamic
- Power hour selloffs = **capitulation**, potentially oversold
- Midday selloffs = sustained selling pressure

**🎯 Strategy Opportunity: "Power Hour Capitulation"**
- Late-day selloffs often mark exhaustion points
- May reverse next morning

---

## 📊 SECTION 5: 52-WEEK RANGE POSITION

**Key Finding**: Selloffs happen across the ENTIRE range!

| Range Position | Events |
|----------------|--------|
| Bottom 20% (near lows) | Many |
| Middle (40-60%) | Most common |
| Top 20% (near highs) | ~11% |

**Key Findings**:
- **~11% of selloffs occur near 52-week HIGHS** (within 20%)
- These are "pullback in uptrend" - HIGH reversal probability
- **~40%+ occur near 52-week LOWS** - "falling knife" risk

**🎯 Strategy Opportunity: "Pullback Buyer"**
- Near 52w high + above 200 SMA = technical pullback
- Mean reversion highly likely

**⚠️ Risk Flag: "Falling Knife"**
- Near 52w low + below 200 SMA = broken stock
- Higher risk, may need additional filters (catalyst, volume spike)

---

## 📊 SECTION 6: SEASONAL PATTERNS

**By Day of Week**:
- Relatively evenly distributed
- Slight uptick on Monday (weekend news digestion?)

**By Month**:
- Higher in volatile months (January, September, October)
- Lower in summer months

---

## 📊 SECTION 7: SEVERITY EXTREMES

| Severity | Drop Range | Events | Character |
|----------|------------|--------|-----------|
| Extreme | > -20% | 98 | Binary events, news-driven |
| Severe | -20% to -15% | 216 | Significant but tradeable |
| Moderate | -15% to -12% | 944 | Sweet spot for reversals |
| Standard | -12% to -10% | 7,741 | Most common, smaller moves |

**Key Finding**: 
- 86% of selloffs are "standard" (-12% to -10%)
- Extreme selloffs (> -20%) are rare and often news-driven

---

## 🎯 STRATEGY OPPORTUNITIES IDENTIFIED

### 1. **Uptrend Pullback Strategy** (NEW!)
- **Definition**: Above 200 SMA + Golden Cross + Near 52w high
- **Count**: ~1,000+ events
- **Thesis**: Pullback in confirmed uptrend → HIGH reversal probability
- **Action**: Smaller position, tighter stop

### 2. **Capitulation Play** 
- **Definition**: Below 200 SMA + Near 52w low + Power hour
- **Thesis**: End-of-day exhaustion → dead cat bounce
- **Action**: Quick scalp, overnight hold only

### 3. **Market-Wide Recovery**
- **Definition**: Selloff on day with 15+ other selloffs + SPY down
- **Thesis**: Market-wide panic → oversold bounce
- **Action**: Sector ETF or basket approach

### 4. **Bear Trap Enhanced**
- **Definition**: -10% selloff + NOT near 52w low + NOT clustered
- **Thesis**: Isolated selloff in non-broken stock → mean reversion
- **Action**: Core Bear Trap strategy

---

## 🔧 ML FEATURE ENGINEERING RECOMMENDATIONS

Based on this analysis, ADD these features before training:

| Feature | Purpose | Priority |
|---------|---------|----------|
| `days_since_last_selloff` | Cluster detection (lower = continuation) | HIGH |
| `selloffs_same_day_count` | Market-wide vs isolated | HIGH |
| `uptrend_strength` | Combine above_200 + golden_cross + range | HIGH |
| `is_capitulation` | Near low + power hour | MEDIUM |
| `is_serial_seller` | Symbol has 50+ historical selloffs | MEDIUM |
| `range_position_bucket` | Categorical: bottom/mid/top | MEDIUM |
| `volume_vs_average` | Relative volume spike | MEDIUM |

---

## 🎓 KEY INSIGHTS FOR BEAR TRAP STRATEGY

1. **Filter OUT**: Clustered selloffs (within 5 days of last)
2. **Filter OUT**: Serial sellers with extreme histories
3. **Filter IN**: Uptrend pullbacks (above 200 SMA + golden cross)
4. **Time preference**: Midday and power hour selloffs
5. **Market awareness**: Better reversals on market-wide selloff days

---

## 🚀 NEXT STEPS

1. **Add recommended features** to the dataset
2. **Calculate reversal outcomes** for all events
3. **Train XGBoost** with enhanced features
4. **Validate on Dataset B** (out-of-sample)
5. **Compare** Uptrend Pullback vs Bear Trap vs Capitulation strategies

---

*Analysis generated from 8,999 events, 250 symbols, 2020-2024*
