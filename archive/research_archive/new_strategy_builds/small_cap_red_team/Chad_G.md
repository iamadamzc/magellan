Small-cap momentum scalping strategies with ideal starter parameters designed for algorithmic execution, including stop loss, trailing, pyramiding, and scale-out rules for each.

Agent: Chad G

### Strategy 1: Opening Range Breakout (ORB) Continuation

Type: Momentum Breakout
Market: Small-cap equities ($1–$20)

Core Logic:

Define Opening Range (OR) over OR_MINUTES

Trigger LONG when price breaks ORH with:

Volume expansion vs OR volume

Trend confirmation (VWAP + MAs aligned)

Spread + liquidity gates

Entry Rules:

LONG on break above ORH + ENTRY_BUFFER

Require:

VOL_MULT_OR vs OR avg

Price > VWAP + VWAP_BUFFER

SPREAD_BPS <= MAX_SPREAD_BPS

REL_VOL >= MIN_REL_VOL

Exit Rules:

Stop Loss: ORH - STOP_CUSHION_ATR * ATR

Take Profit: Partial at R1_MULT, final at R2_MULT or trailing

Time Stop: exit if no progress by STALL_MINUTES

Trailing Stop:

Activate after TRAIL_ACTIVATE_R

Trail = MAX(HIGHEST - TRAIL_ATR * ATR, VWAP - VWAP_TRAIL_ATR * ATR)

Pyramiding:

Add on high-tight flag or micro pullback after breakout:

Add only if position is at least ADD_MIN_R in profit

Max adds = MAX_ADDS

Scaling Out:

SCALE1_PCT at R1_MULT

SCALE2_PCT at R2_MULT

Runner on trailing stop

Configurable Parameters:

OR_MINUTES (default: 5)

ENTRY_BUFFER (default: 0.02)

VOL_MULT_OR (default: 1.8)

MIN_REL_VOL (default: 2.0)

VWAP_BUFFER (default: 0.00–0.02)

STOP_CUSHION_ATR (default: 0.35)

R1_MULT (default: 1.0R)

R2_MULT (default: 2.0R)

TRAIL_ACTIVATE_R (default: 1.2R)

TRAIL_ATR (default: 1.1)

MAX_ADDS (default: 2)

STALL_MINUTES (default: 8)

MAX_SPREAD_BPS (default: 35)

### Strategy 2: VWAP Reclaim (Red-to-Green / VWAP Flip)

Type: Mean Reversion → Momentum Shift
Market: Small-cap equities ($1–$20)

Core Logic:

Detect strong morning flush/weakness

Trigger LONG when price reclaims VWAP with demand confirmation

Entry Rules:

LONG when:

Cross above VWAP and holds HOLD_BARS

Volume on reclaim >= RECLAIM_VOL_MULT * recent avg

Pullback does not lose VWAP by more than VWAP_FAIL_BPS

Exit Rules:

Stop Loss: VWAP - STOP_ATR * ATR (or last swing low)

Take Profit: previous HOD / ORH / key resistance level

Time Stop: MAX_HOLD_MINUTES

Trailing Stop:

After TRAIL_AFTER_HOD_TOUCH = true, trail under:

last 1-min higher low, or

HIGHEST - TRAIL_ATR * ATR

Pyramiding:

Add on:

First successful VWAP retest bounce

Break of reclaim pivot (PIVOT + ADD_BUFFER)

Only add if UNREALIZED_R >= ADD_MIN_R

Scaling Out:

First scale at reclaim → first resistance

Second scale at HOD test

Runner trails

Configurable Parameters:

HOLD_BARS (default: 2 on 1-min)

RECLAIM_VOL_MULT (default: 1.5)

VWAP_FAIL_BPS (default: 15)

STOP_ATR (default: 0.45)

MAX_HOLD_MINUTES (default: 35)

TRAIL_ATR (default: 1.0)

ADD_MIN_R (default: 0.8R)

ADD_BUFFER (default: 0.01)

SCALE1_PCT (default: 40%)

SCALE2_PCT (default: 30%)

### Strategy 3: High-Tight Flag (HTF) Breakout

Type: Momentum Continuation / Volatility Contraction
Market: Small-cap equities ($1–$20)

Core Logic:

Identify impulsive leg up (the “pole”)

Detect consolidation with tight range + declining volatility

Breakout triggers LONG with range expansion + volume

Entry Rules:

LONG on break above flag high with:

FLAG_RANGE_PCT <= MAX_FLAG_RANGE_PCT

ATR_CONTRACTION >= MIN_ATR_DROP_PCT

Breakout volume >= BREAK_VOL_MULT

Exit Rules:

Stop Loss: below flag low or ENTRY - STOP_ATR * ATR

Take Profit: measured move (pole height * MM_MULT) or resistance

Trailing Stop:

Trail under last flag higher low

Switch to ATR trail after TRAIL_SWITCH_R

Pyramiding:

Add on:

First breakout retest (flag high reclaim)

Micro-flag inside the breakout

Cap adds tightly (this trade is already “late” by nature)

Scaling Out:

Scale at 1R, 2R, runner

Configurable Parameters:

POLE_MIN_PCT (default: +12%)

FLAG_MIN_BARS (default: 6 on 1-min)

MAX_FLAG_RANGE_PCT (default: 2.0%)

MIN_ATR_DROP_PCT (default: 20%)

BREAK_VOL_MULT (default: 1.6)

STOP_ATR (default: 0.5)

MM_MULT (default: 0.7–1.0)

TRAIL_SWITCH_R (default: 1.5R)

MAX_ADDS (default: 1)

### Strategy 4: HOD Break (High of Day Breakout)

Type: Momentum Breakout / Squeeze Release
Market: Small-cap equities ($1–$20)

Core Logic:

Identify HOD level with repeated tests (liquidity builds there)

LONG on break when supply is absorbed

Entry Rules:

LONG when:

TOUCHES_HOD >= MIN_TOUCHES

Break above HOD + ENTRY_BUFFER

Volume spike >= HOD_BREAK_VOL_MULT

TIME_SINCE_LAST_HALT >= HALT_COOLDOWN_MIN (if halted)

Exit Rules:

Stop Loss: HOD - STOP_CUSHION_ATR * ATR or last pivot

Take Profit: quick 1R–2R scalp, runner only if trend persists

Time Stop: if break fails within FAIL_WINDOW_BARS

Trailing Stop:

Fast trail (scalp-style):

After 0.8R, trail by TRAIL_TICKS or 0.6 * ATR

Pyramiding:

Add only on clean retest reclaim of HOD (avoid chasing)

Requires spread improvement + tape strength (if available)

Scaling Out:

Heavy early scale (because small caps love rug pulls)

Runner small

Configurable Parameters:

MIN_TOUCHES (default: 2)

ENTRY_BUFFER (default: 0.02)

HOD_BREAK_VOL_MULT (default: 2.0)

STOP_CUSHION_ATR (default: 0.35)

FAIL_WINDOW_BARS (default: 3)

TRAIL_TICKS (default: 6–12)

HALT_COOLDOWN_MIN (default: 5)

SCALE1_PCT (default: 50% at 1R)

SCALE2_PCT (default: 30% at 1.7R)

### Strategy 5: Micro Pullback Continuation (1-min / 2-min)

Type: Trend Continuation / Momentum Scalping
Market: Small-cap equities ($1–$20)

Core Logic:

In a strong uptrend, enter on shallow pullbacks to a fast MA/VWAP band

Works best in sustained momentum names

Entry Rules:

LONG when:

Trend filter: EMA_FAST > EMA_SLOW and price above VWAP

Pullback depth <= MAX_PULLBACK_ATR

Reversal candle prints with volume >= PB_REV_VOL_MULT

Entry on break of reversal candle high

Exit Rules:

Stop Loss: below pullback low or ENTRY - STOP_ATR * ATR

Take Profit: 1R and 2R targets, runner trails

Time Stop: MAX_HOLD_MINUTES (scalp = short)

Trailing Stop:

Trail under EMA_FAST - EMA_TRAIL_ATR * ATR or last higher low

Pyramiding:

Add on subsequent micro pullbacks if:

overall position risk stays capped

UNREALIZED_R >= ADD_MIN_R

no blow-off extension detected

Scaling Out:

Standard 40/30/30 or 50/25/25 depending on volatility regime

Configurable Parameters:

EMA_FAST (default: 9)

EMA_SLOW (default: 20)

MAX_PULLBACK_ATR (default: 0.8)

PB_REV_VOL_MULT (default: 1.3)

STOP_ATR (default: 0.45)

MAX_HOLD_MINUTES (default: 20)

EMA_TRAIL_ATR (default: 0.7)

ADD_MIN_R (default: 0.7R)

MAX_ADDS (default: 2)

### Strategy 6: First Pullback After Breakout (FPB)

Type: Breakout → Structured Pullback Entry
Market: Small-cap equities ($1–$20)

Core Logic:

Avoid chasing the initial breakout

Enter on the first orderly pullback that holds the breakout level

Entry Rules:

Identify breakout above key level (ORH/HOD/resistance)

Wait for pullback with:

PULLBACK_DEPTH <= MAX_PB_DEPTH_ATR

Holds level within LEVEL_HOLD_BPS

Entry on reclaim of pullback micro pivot

Exit Rules:

Stop Loss: below pullback low or below level - cushion

Take Profit: previous impulse measured move or 2R

Trailing Stop:

Start trail after 1.2R using swing-low trail

Convert to ATR trail after 2R

Pyramiding:

Add on:

successful retest of breakout level

second higher low (if volume supports)

Scaling Out:

Less aggressive than HOD break; this is higher quality entry

Keep a meaningful runner

Configurable Parameters:

MAX_PB_DEPTH_ATR (default: 1.0)

LEVEL_HOLD_BPS (default: 20)

STOP_CUSHION_ATR (default: 0.35)

TRAIL_START_R (default: 1.2R)

TRAIL_ATR (default: 1.1)

MAX_ADDS (default: 1)

SCALE1_PCT (default: 35% at 1R)

SCALE2_PCT (default: 25% at 2R)

### Strategy 7: Gap-and-Go (Premarket High Break)

Type: Momentum Open / Catalyst Continuation
Market: Small-cap equities ($1–$20)

Core Logic:

Strong premarket trend + catalyst

Enter on break of premarket high with open liquidity/volume confirmation

Entry Rules:

LONG when:

Break above PMH + ENTRY_BUFFER

REL_VOL >= MIN_REL_VOL

PM_RANGE_PCT >= MIN_PM_RANGE_PCT

Price holds above VWAP within VWAP_GRACE_BPS

Exit Rules:

Stop Loss: below PMH reclaim level or STOP_ATR * ATR

Take Profit: quick to 1R–2R; watch for halt risk

Trailing Stop:

Tight trail to protect against open volatility:

HIGHEST - OPEN_TRAIL_ATR * ATR

Pyramiding:

Add only after the open stabilizes (post NO_ADD_MINUTES)

Add on VWAP hold + higher low

Scaling Out:

Heavier early scale due to halt/spike risk

Configurable Parameters:

ENTRY_BUFFER (default: 0.03)

MIN_REL_VOL (default: 3.0)

MIN_PM_RANGE_PCT (default: 8%)

VWAP_GRACE_BPS (default: 20)

STOP_ATR (default: 0.6)

OPEN_TRAIL_ATR (default: 1.0)

NO_ADD_MINUTES (default: 10)

MAX_ADDS (default: 1)

SCALE1_PCT (default: 50% at 1R)

### Strategy 8: Parabolic Exhaustion Fade (Blow-Off Top Short)

Type: Mean Reversion / Momentum Exhaustion
Market: Small-cap equities ($1–$20)

Core Logic:

Detect vertical extension + climax volume

Enter SHORT on failure/rejection and first lower high

Entry Rules:

SHORT when:

Extension: DIST_FROM_VWAP_ATR >= EXT_ATR_MIN

Climax: volume >= CLIMAX_VOL_MULT * recent avg

Rejection candle wick ratio >= WICK_RATIO_MIN

Break of rejection candle low or lower-high confirmation

Exit Rules:

Stop Loss: above blow-off high + STOP_CUSHION_ATR * ATR

Take Profit: VWAP, then prior support levels

Time Stop: exit if VWAP doesn’t approach within MAX_HOLD_MINUTES

Trailing Stop:

Trail above lower highs or LOWEST + TRAIL_ATR * ATR (for shorts)

Pyramiding:

Add on:

first lower-high retest

VWAP underside rejection (best add)

Only if borrow/locate constraints allow and spread is sane

Scaling Out:

Scale at first flush (fast 1R)

Next at VWAP

Small runner for overshoot

Configurable Parameters:

EXT_ATR_MIN (default: 3.0)

CLIMAX_VOL_MULT (default: 2.5)

WICK_RATIO_MIN (default: 0.35)

STOP_CUSHION_ATR (default: 0.4)

TRAIL_ATR (default: 1.2)

MAX_HOLD_MINUTES (default: 25)

MAX_ADDS (default: 2)

### Strategy 9: Failed Breakout (HOD Fail / Bull Trap Short)

Type: Structural Breakdown / Trap Reversal
Market: Small-cap equities ($1–$20)

Core Logic:

Price breaks HOD, fails to hold, re-enters range

Short the reclaim failure (classic trap)

Entry Rules:

SHORT when:

Break above HOD occurred

Price falls back below HOD - FAIL_BUFFER

Confirm with volume + loss of VWAP (optional)

Exit Rules:

Stop Loss: above trap high + STOP_CUSHION_ATR * ATR

Take Profit: VWAP then LOD/range low

Time Stop: exit if no follow-through in FAIL_FOLLOWTHRU_BARS

Trailing Stop:

Trail above lower highs or above VWAP after VWAP break

Pyramiding:

Add on:

underside HOD retest rejection

VWAP underside rejection

Scaling Out:

Partial quickly at 1R (these can snap back violently)

More at VWAP

Configurable Parameters:

FAIL_BUFFER (default: 0.02)

STOP_CUSHION_ATR (default: 0.35)

FAIL_FOLLOWTHRU_BARS (default: 3)

TRAIL_ATR (default: 1.0)

MAX_HOLD_MINUTES (default: 30)

MAX_ADDS (default: 2)

### Strategy 10: Support Sweep + Reclaim (LOD Sweep Long)

Type: Liquidity Sweep / Mean Reversion / Trap
Market: Small-cap equities ($1–$20)

Core Logic:

Price sweeps a known support (LOD / key level), then reclaims it

Enter LONG on reclaim with confirmation

Entry Rules:

Identify sweep:

New low by at least SWEEP_BPS

Wick ratio >= WICK_RATIO_MIN

LONG on reclaim of sweep pivot with:

RECLAIM_VOL_MULT

Close back above key level within RECLAIM_WINDOW_BARS

Exit Rules:

Stop Loss: below sweep low - STOP_CUSHION_ATR * ATR

Take Profit: VWAP, then mid-range resistance

Time Stop: MAX_HOLD_MINUTES

Trailing Stop:

Trail under higher lows; switch to ATR trail after VWAP touch

Pyramiding:

Add on:

first higher low after reclaim

VWAP reclaim (if entry was below VWAP)

Scaling Out:

Scale into VWAP (common magnet)

Keep runner only if trend flips

Configurable Parameters:

SWEEP_BPS (default: 25)

WICK_RATIO_MIN (default: 0.25)

RECLAIM_VOL_MULT (default: 1.4)

RECLAIM_WINDOW_BARS (default: 3)

STOP_CUSHION_ATR (default: 0.45)

TRAIL_ATR (default: 1.1)

MAX_HOLD_MINUTES (default: 40)

MAX_ADDS (default: 1)

Global Risk & Execution Modules (apply to all strategies)

Because the market doesn’t care about your “setup,” only whether your risk is controlled.

Position Sizing

Risk per trade: RISK_PCT_EQUITY (default: 0.10%–0.30%)

Shares = FLOOR((EQUITY * RISK_PCT_EQUITY) / STOP_DISTANCE_$)

Hard cap: MAX_POSITION_PCT_ADV (default: 0.5% of 1-min ADV) to avoid being the liquidity

Trade Validity Gates

MIN_PRICE (default: 1.00), MAX_PRICE (default: 20.00)

MIN_1M_DOLLAR_VOL (default: $250k)

MAX_SPREAD_BPS (default: 35–60 depending on volatility)

MIN_REL_VOL (default: 2.0)

HALT_FILTER_ENABLED (default: true)

Kill Switches

Daily max loss: DAILY_MAX_LOSS_R (default: -3R)

Consecutive losses: MAX_CONSEC_LOSSES (default: 3)

Slippage spike: disable if AVG_SLIPPAGE_BPS > SLIPPAGE_LIMIT_BPS (default: 15–25bps)

Stop Handling

Hard stop always placed immediately (or simulated with server-side protection if broker constraints)

Stop refresh cooldown: STOP_UPDATE_COOLDOWN_MS (default: 500–1500ms) to avoid thrashing

Pyramiding Controls

Total risk cap across adds: MAX_TOTAL_RISK_R (default: 1.2R per idea)

Only add when the stop for prior size can be moved to reduce net risk (netting logic)

Scaling Out Template

Conservative: 50% @ 1R, 30% @ 1.7R, 20% runner

Balanced: 40% @ 1R, 30% @ 2R, 30% runner

Trend-heavy: 30% @ 1R, 30% @ 2R, 40% runner (only for strongest trend filter)

If you build these with clean modules (signal, gates, sizing, stop engine, trail engine, pyramid engine, scale engine), you can mix-and-match without turning your codebase into a haunted house.