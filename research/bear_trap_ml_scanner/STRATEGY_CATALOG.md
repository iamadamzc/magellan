# Intraday Selloff Strategy Catalog
> Derived from 8,999 selloff events (2020-2024)
> Analysis Date: January 22, 2026

---

## 📊 Baseline Statistics

| Metric | Value |
|--------|-------|
| Total Events Analyzed | 8,999 |
| Overall 60-min Reversal Rate | 42.4% |
| Overall EOD Reversal Rate | 66.0% |
| Average 60-min Recovery | 5.8% |

---

## 🎯 STRATEGY 1: Morning Bear Trap

### Concept
Exploit the 60%+ reversal rate of morning/early selloffs on non-down market days.

### Entry Criteria
- Selloff crosses -10% from session open
- Time: **9:30 AM - 11:30 AM (Morning bucket)**
- SPY: Flat or positive (> -0.3%)
- Optional: Above 200 SMA

### Statistics
| Metric | Value | vs Baseline |
|--------|-------|-------------|
| Events | ~300-400 | - |
| 60-min Reversal | **65.9%** | +23.5% |
| EOD Reversal | 60.9% | -5.1% |
| Expected R:R | 2:1 minimum | |

### Pros
- ✅ Highest 60-min reversal rate
- ✅ Full trading day ahead for management
- ✅ Clear time-based filter

### Cons
- ⚠️ Lower EOD reversal (may reverse then continue down)
- ⚠️ Smaller sample size
- ⚠️ Requires fast execution

### Status: 🟢 **HIGH PRIORITY**

---

## 🎯 STRATEGY 2: Midday Mean Reversion

### Concept
Capture consistent midday selloff reversals with moderate edge.

### Entry Criteria
- Selloff crosses -10% from session open
- Time: **11:30 AM - 2:00 PM (Midday bucket)**
- Any market condition

### Statistics
| Metric | Value | vs Baseline |
|--------|-------|-------------|
| Events | 3,514 | Largest sample |
| 60-min Reversal | **59.8%** | +17.4% |
| EOD Reversal | 63.1% | -2.9% |
| Expected R:R | 1.5:1 | |

### Pros
- ✅ Large sample size (statistically robust)
- ✅ Good 60-min reversal rate
- ✅ Time to manage position

### Cons
- ⚠️ EOD slightly below baseline
- ⚠️ Less dramatic than morning edge

### Status: 🟢 **HIGH PRIORITY - Best Volume**

---

## 🎯 STRATEGY 3: Opening Scalp

### Concept
Ultra-fast reversal play on opening selloffs. **71% 60-min reversal!**

### Entry Criteria
- Selloff crosses -10% from session open
- Time: **9:30 AM - 9:45 AM (Opening bucket)**
- Quick entry/exit (15-30 min hold max)

### Statistics
| Metric | Value | vs Baseline |
|--------|-------|-------------|
| Events | 50 | Very small |
| 60-min Reversal | **71.4%** 🔥 | +29.0% |
| EOD Reversal | 34.0% | -32.0% |
| Expected R:R | 3:1 scalp | |

### Pros
- ✅ HIGHEST 60-min reversal rate
- ✅ Fast in-and-out
- ✅ Clear exit before reversal fails

### Cons
- ⚠️ Very small sample (50 events)
- ⚠️ Must exit quickly (EOD rate is terrible)
- ⚠️ Needs fast execution
- ⚠️ May be gap-related (different dynamics)

### Status: 🟡 **INTERESTING - Needs More Study**

---

## 🎯 STRATEGY 4: Power Hour Overnight Hold

### Concept
Enter on power hour selloffs, hold overnight for EOD recovery.

### Entry Criteria
- Selloff crosses -10% from session open
- Time: **3:00 PM - 4:00 PM (Power Hour)**
- Entry near close

### Statistics
| Metric | Value | vs Baseline |
|--------|-------|-------------|
| Events | 2,125 | Good sample |
| 60-min Reversal | 15.4% ❌ | -27.0% |
| EOD Reversal | **70.7%** 🔥 | +4.7% |
| Expected R:R | 1:1 with overnight gap | |

### Pros
- ✅ Highest EOD reversal rate
- ✅ Capitulation signal (likely exhaustion)
- ✅ Overnight gap potential

### Cons
- ⚠️ No intraday edge (15% 60-min)
- ⚠️ Overnight risk (news, gaps)
- ⚠️ Ties up capital

### Status: 🟡 **SECONDARY - Different Risk Profile**

---

## 🎯 STRATEGY 5: Uptrend Pullback

### Concept
Focus only on selloffs in confirmed uptrends (above 200 SMA + golden cross).

### Entry Criteria
- Selloff crosses -10% from session open
- Above 200 SMA + 50 SMA > 200 SMA (Golden Cross)
- Preferably near 52-week high (within -30%)
- Time: Morning or Midday preferred

### Statistics
| Metric | Value | vs Baseline |
|--------|-------|-------------|
| Events | 2,462 (full), 980 (near highs) | Good sample |
| 60-min Reversal | 44.1% / 46.4% | +2-4% |
| EOD Reversal | 67.8% | +1.8% |
| Avg Recovery | **6.45%** | +11% |

### Pros
- ✅ Trading WITH the trend
- ✅ Higher expected recovery %
- ✅ Lower risk (healthy pullback, not broken stock)

### Cons
- ⚠️ Smaller edge on reversal rate alone
- ⚠️ Requires SMA calculation before entry

### Status: 🟢 **CORE FILTER - Use with other strategies**

---

## 🎯 STRATEGY 6: Market Tailwind

### Concept
Only trade selloffs on UP market days where broad support helps recovery.

### Entry Criteria
- Selloff crosses -10% from session open
- **SPY change > +0.5%** for the day
- Any time bucket

### Statistics
| Metric | Value | vs Baseline |
|--------|-------|-------------|
| Events | 3,041 | Large sample |
| 60-min Reversal | **46.6%** | +4.2% |
| EOD Reversal | ~68% | +2% |

### Pros
- ✅ Market provides tailwind
- ✅ Simple real-time filter (just check SPY)
- ✅ Good sample size

### Cons
- ⚠️ Edge is smaller (+4%)
- ⚠️ Filters out 2/3 of opportunities

### Status: 🟢 **CORE FILTER - Combine with time**

---

## 🎯 STRATEGY 7: "Golden" Combo Filter

### Concept
Combine best conditions: Uptrend + Good Timing + Not Near Lows

### Entry Criteria
- Selloff crosses -10% from session open
- Above 200 SMA
- Not near 52-week low (range position > 30%)
- Time: Midday or Afternoon

### Statistics
| Metric | Value | vs Baseline |
|--------|-------|-------------|
| Events | 1,975 | Moderate sample |
| 60-min Reversal | **52.8%** 🔥 | +10.4% |
| EOD Reversal | 65.3% | -0.7% |
| Avg Recovery | **7.43%** | +28% |

### Pros
- ✅ HIGHEST combined 60-min edge (+10%)
- ✅ Significantly higher recovery magnitude
- ✅ Good sample size for validation

### Cons
- ⚠️ Multiple conditions to check
- ⚠️ May miss some opportunities

### Status: 🟢 **TOP PRIORITY - Best Edge**

---

## 🎯 STRATEGY 8: Anti-Falling Knife Filter

### Concept
AVOID the worst setups: Below 200 SMA + Near 52-week lows

### Filter Criteria (AVOID these)
- Below 200 SMA
- Price range position < 20% (near 52w low)
- Additional avg drop: **-3.48%** (painful!)

### Statistics
| Metric | Value | Note |
|--------|-------|------|
| Events to AVOID | 4,276 | 47.5% of all selloffs |
| 60-min Reversal | 40.7% | Below baseline |
| Max Additional Drop | **-3.48%** avg | RISK! |

### Use Case
- NOT a strategy - a **risk filter**
- Apply to ALL strategies above
- Protects capital from broken stocks

### Status: 🔴 **RISK FILTER - Always Apply**

---

## 📊 Strategy Comparison Matrix

| Strategy | Events | 60-min % | EOD % | Recovery | Priority |
|----------|--------|----------|-------|----------|----------|
| Baseline | 8,999 | 42.4% | 66.0% | 5.8% | - |
| 1. Morning Bear Trap | ~350 | **65.9%** | 60.9% | 6% | 🟢 HIGH |
| 2. Midday Reversion | 3,514 | **59.8%** | 63.1% | 6% | 🟢 HIGH |
| 3. Opening Scalp | 50 | **71.4%** | 34.0% | 4% | 🟡 STUDY |
| 4. Power Hour O/N | 2,125 | 15.4% | **70.7%** | - | 🟡 SECONDARY |
| 5. Uptrend Pullback | 980 | 46.4% | 66.9% | **6.45%** | 🟢 FILTER |
| 6. Market Tailwind | 3,041 | 46.6% | 68% | 6% | 🟢 FILTER |
| 7. Golden Combo | 1,975 | **52.8%** | 65.3% | **7.43%** | 🟢 TOP |
| 8. Anti-Knife | 4,276 | 40.7% | 65.4% | RISK | 🔴 AVOID |

---

## 🎯 Recommended Prioritization

### Phase 1: Core Strategy
**Strategy 7: Golden Combo** OR **Strategy 2: Midday Reversion**
- Both have 50%+ 60-min reversal
- Good sample sizes
- Clear, implementable filters

### Phase 2: Enhancement
**Strategy 1: Morning Bear Trap** as time-based overlay
- Apply to core strategy during morning hours
- Expect even higher win rate

### Phase 3: Exploration
**Strategy 3: Opening Scalp** - Needs further validation
- Small sample but huge edge
- Could be separate "quick scalp" strategy

### Always Apply
**Strategy 8: Anti-Falling Knife Filter**
- Never trade below 200 SMA + near 52w lows
- Protects from worst setups

---

## 🚀 Next Steps

1. **Pick one strategy** to implement first
2. **Backtest with full Bear Trap mechanics** (stops, targets)
3. **Validate on Dataset B** (out-of-sample)
4. **Deploy to paper trading**
5. **Return to implement other strategies**

---

*Catalog generated from selloff-smallcap-10pct-5yr-v1 dataset*
*Last Updated: January 22, 2026*
