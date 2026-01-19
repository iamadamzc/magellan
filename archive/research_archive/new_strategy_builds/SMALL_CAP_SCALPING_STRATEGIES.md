# Small-Cap Momentum Scalping Strategies - Final Specification

**Integration into Daily Strategy Testing Suite**

Based on expert synthesis (Chad_G, Dee_S, Gem_Ni) + independent machine analysis

---

## Strategy E: VWAP Reclaim /Washout Reversal
**Type**: Mean Reversion → Momentum Shift  
**Tier**: Core / Highest Consensus  
**Market**: Small-cap ($1-$20), high RVOL, intraday movers

### Core Thesis
VWAP acts as liquidity magnet. Flushes below VWAP in strong names represent forced selling, not trend failure. Reclaim = smart money accumulation.

### Entry Logic
```python
# Prerequisites
stock_day_change >= 15%  # Up on day (momentum context)
price < VWAP  # Below VWAP
flush_deviation >= 0.8 * ATR  # Meaningful flush

# Flush candle characteristics
wick_ratio = lower_wick / candle_range
volume_spike = candle_volume / avg_volume_20

if wick_ratio >= 0.40:  # Absorption wick (Gem_Ni insight)
    if volume_spike >= 1.6:  # Volume confirmation
        # Wait for reclaim
        if price_close > VWAP:
            if hold_above_vwap_for >= 2:  # bars
                ENTER_LONG
```

### Exit Rules
- **Stop Loss**: Flush low - (0.45 × ATR)  
- **TP1** (40%): VWAP → Mid-range  
- **TP2** (30%): High of Day (HOD)  
- **Runner** (30%): Trail at VWAP  
- **Time Stop**: 30 minutes  

### Parameter Ranges (Optimized)
| Parameter | Range | Default | Source |
|-----------|-------|---------|--------|
| `MIN_DAY_CHANGE_PCT` | 10-20% | 15% | Chad_G |
| `FLUSH_DEV_ATR` | 0.7-1.2 | 0.8 | Consensus |
| `WICK_RATIO_MIN` | 0.35-0.45 | 0.40 | Gem_Ni key insight |
| `FLUSH_VOL_MULT` | 1.4-2.0 | 1.6 | Consensus |
| `STOP_LOSS_ATR` | 0.35-0.6 | 0.45 | Chad_G |
| `HOLD_BARS` | 1-3 | 2 | Chad_G |
| `MAX_HOLD_MINUTES` | 20-40 | 30 | Consensus |
| `SCALE_TP1_PCT` | 30-50% | 40% | Dee_S |
| `SCALE_TP2_PCT` | 25-35% | 30% | Consensus |

### Regime Filters (MANDATORY)
```python
# Liquidity gate (All experts)
dollar_volume_1min > 250_000

# Spread gate (Gem_Ni)
spread_bps = ((ask - bid) / bid) * 10000
if spread_bps > 35:
    REJECT

# Time of day
if time < "09:35" or time > "15:45":
    REJECT  # Avoid open/close volatility

# Halt cooldown (Chad_G)
if resumed_from_halt_within_minutes < 5:
    REJECT
```

---

## Strategy F: Opening Range / Pre-Market High Breakout
**Type**: Momentum Breakout  
**Tier**: Core / Best Clean Entry  
**Market**: Small-cap ($1-$20), gappers with catalyst

### Core Thesis
Valid breakouts above ORH/PMH with volume = continuation. First pullback after breakout = optimal R:R.

### Entry Logic
```python
# Gap requirement (Gem_Ni: needs massive catalyst)
if gap_pct < 15%:
    REJECT

# Opening Range established
OR_high = max(price_09_30_to_09_35)  # 5-minute OR
PMH = premarket_high

# Higher timeframe filter (Dee_S insight)
if ADX_5min < 25:  # Not trending
    REJECT
if price_5min < EMA_9_5min:
    REJECT  # Against 5min trend

# Breakout
breakout_level = max(OR_high, PMH)
if price > breakout_level:
    if volume >= 2.5 * avg_volume:  # Gem_Ni: 3.0x for small caps
        if price > VWAP:  # Above value
            ENTER_LONG at breakout_level + $0.02  # Buffer
```

### Exit Rules  
- **Stop Loss**: Breakout level - (0.40 × ATR)  
- **TP1** (45%): 1.0R  
- **TP2** (30%): 2.0R  
- **Runner** (25%): Trail at higher lows  
- **Time Stop**: 20 minutes  

### Parameter Ranges (Optimized)
| Parameter | Range | Default | Source |
|-----------|-------|---------|--------|
| `MIN_GAP_PCT` | 10-20% | 15% | Gem_Ni emphasis |
| `OR_MINUTES` | 3-10 | 5 | Dee_S |
| `BREAKOUT_VOL_MULT` | 1.8-3.0 | 2.5 | Gem_Ni: 3.0 for small caps |
| `HTF_ADX_MIN` | 20-30 | 25 | Dee_S multi-timeframe |
| `STOP_LOSS_ATR` | 0.35-0.5 | 0.40 | Consensus |
| `TRAIL_ACTIVATE_R` | 1.0-1.8 | 1.5 | Dee_S |
| `MAX_HOLD_MINUTES` | 15-25 | 20 | Consensus |
| `RVOL_MIN` | 2.0-3.0 | 2.5 | Dee_S |
| `MAX_SPREAD_BPS` | 25-50 | 35 | Chad_G/Gem_Ni |

### Regime Filters
```python
# Same liquidity/spread gates as Strategy E

# VIX adjustment (Dee_S missing component)
if VIX > 35:
    position_size *= 0.5  # High vol reduces size

# Halt cooldown
if halt_occurred_last_10min:
    REJECT

# Relative strength (Dee_S enhancement)
sector_etf = get_sector_etf(ticker)
if stock_return_5min < sector_return_5min:
    position_size *= 0.7  # Weak relative strength penalty
```

---

## Strategy G: Micro Pullback Continuation (High Frequency)
**Type**: Trend Continuation / Scalp  
**Tier**: Core / Highest Trade Frequency  
**Market**: Small-cap ($1-$20), sustained intraday trends

### Core Thesis
Strong trends reward repeated shallow pullbacks. Enter on momentum re-engagement after brief pauses.

### Entry Logic
```python
# Trend qualification
if price < VWAP:
    REJECT  # Not in uptrend

if EMA_8 < EMA_20:
    REJECT  # EMAs not aligned

# Pullback characteristics
pullback_depth = (recent_high - price) / ATR
pullback_volume_avg = last_3_bars_volume / avg_volume_20

if pullback_depth <= 0.75:  # Shallow (< 0.75 ATR)
    if pullback_volume_avg < 1.0:  # Volume contraction
        # Reversal signal
        if price > reversal_candle_high:
            if volume >= 1.3 * avg_volume:
                ENTER_LONG
```

### Exit Rules
- **Stop Loss**: Pullback low or 0.45 × ATR  
- **TP1** (45%): 1.0R  
- **TP2** (30%): 2.0R  
- **Runner** (25%): Trail at EMA_8 - (0.7 × ATR)  
- **Time Stop**: 15 minutes (tight for scalp)  

### Parameter Ranges (Optimized)
| Parameter | Range | Default | Source |
|-----------|-------|---------|--------|
| `EMA_FAST` | 8-9 | 8 | Chad_G |
| `EMA_SLOW` | 20-21 | 20 | Chad_G |
| `MAX_PULLBACK_ATR` | 0.6-0.9 | 0.75 | Consensus |
| `PB_VOL_CONTRACT` | <1.0 | <0.8 | Gem_Ni: decay check |
| `REV_VOL_MULT` | 1.2-1.5 | 1.3 | Chad_G |
| `STOP_LOSS_ATR` | 0.4-0.5 | 0.45 | Consensus |
| `EMA_TRAIL_ATR` | 0.6-0.8 | 0.7 | Chad_G |
| `MAX_HOLD_MINUTES` | 10-20 | 15 | Consensus |
| `MAX_ADDS` | 1-2 | 2 | Chad_G (only in strong trends) |

### Regime Filters
```python
# Same base gates (liquidity, spread, halt)

# Trend strength requirement
if ATR_change_pct > -20%:  # ATR NOT contracting
    REJECT  # Chad_G: only add when vol contracting

# Time of day (Dee_S enhancement)
if time > "14:30":
    MAX_HOLD_MINUTES *= 0.5  # Reduce late day

# Float consideration (Dee_S missing component)
if float_shares > 50_000_000:
    MAX_PULLBACK_ATR *= 1.2  # Higher float needs bigger moves
```

---

## Global Implementation Notes

### ATR-Normalization (Critical)
ALL parameters must use ATR-based stops/targets, not fixed percentages:
```python
ATR_14 = calculate_ATR(bars, period=14)
stop_distance = STOP_LOSS_ATR * ATR_14  # e.g., 0.45 × $0.50 = $0.225
```

### Pyramiding Rules (Chad_G emphasis)
```python
# Only add when NET RISK decreases
if first_position_profit_R >= 0.8:  # In profit
    move_stop_to_breakeven()  # Risk-free
    if add_signal_valid:
        add_position(size=0.5 * original)  # Half size add
```

### Time Stops (Non-Negotiable)
```python
if time_in_position_minutes > MAX_HOLD_MINUTES:
    CLOSE_POSITION  # Thesis expired
```

### Critical Missing Components (Dee_S Synthesis)

#### 1. Adaptive Position Sizing
```python
base_size = 100_shares

# Volatility adjustment
if ATR_current > ATR_avg_20:
    size_mult = ATR_avg_20 / ATR_current
else:
    size_mult = 1.0

# Time of day adjustment
if time > "14:30":
    size_mult *= 0.7  # Reduce late day

# VIX adjustment
if VIX > 35:
    size_mult *= 0.5

final_size = base_size * size_mult
```

#### 2. Execution Intelligence (Gem_Ni L2 Insight)
```python
# Before entry, check Level 2
ask_liquidity_depth = sum_ask_size_5_levels()

# If ask wall is thin, breakout more likely
if ask_liquidity_depth < avg_ask_depth * 0.6:
    confidence_boost = True

# Monitor print rate
if trades_per_second > 10:  # Rapid tape
    momentum_confirmed = True
```

---

## Testing Integration with Daily Strategies

### Unified Test Matrix
**Daily Strategies** (A-D): MAG7 + ETFs, daily timeframe  
**Scalping Strategies** (E-G): Small-cap universe, 1-minute timeframe

### Scalping Test Universe
```python
SMALL_CAP_UNIVERSE = [
    # High volume small caps for testing
    'RIOT', 'MARA', 'PLUG', 'LCID', 'NIO', 'SOFI',
    'AMC', 'GME', 'BBBY', 'SNDL', 'NAKD'  # Meme stocks (high RVOL)
]
```

### Test Periods
- **Primary**: Nov 2024 - Jan 2025 (3 months recent)  
- **Secondary**: Apr - Jun 2024 (3 months older)  

**Why 1-minute?** Small-cap scalping requires intraday precision. Daily data won't work.

### Expected Results (Conservative)
- **Win Rate**: 45-55% (not high, but R:R > 2:1)  
- **Profit Factor**: >1.3  
- **Max Hold**: <30 minutes  
- **Sharpe**: >0.8 (on winning strategies)  

### Key Differences from Daily Strategies
| Aspect | Daily (A-D) | Scalping (E-G) |
|--------|------------|----------------|
| Timeframe | 1-day bars | 1-minute bars |
| Hold Time | Days-weeks | Minutes |
| Friction | 1.5 bps | 10-15 bps |
| Stop | %-based or ATR | Tight ATR (0.4-0.5×) |
| Universe | MAG7, ETFs | Small-cap movers |
| Data Need | Daily cached | 1-min (cache or live) |

---

## Next Steps

1. **Add 1-min data to cache** for small-cap universe (if testing historical)
2. **Build Strategy E first** (VWAP Reclaim - highest consensus)
3. **Test on RIOT/MARA** (high vol, good test assets)
4. **Validate parameters** with walk-forward
5. **Build F and G** once E proves viable

**Critical**: These strategies REQUIRE 1-minute data and tight execution. Cannot backtest properly with daily bars.
