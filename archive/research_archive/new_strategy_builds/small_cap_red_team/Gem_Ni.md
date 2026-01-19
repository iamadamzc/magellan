Small Cap Momentum Scalping Strategies designed for a high-frequency algorithmic trading environment.
Agent: Gem Ni

These strategies cover the primary phases of the "Small Cap Cycle": The Open (Breakout), The Trend (Continuation), The Washout (Mean Reversion), The Event (Halts), and The Backside (Shorting).Strategy 1: PMH Ignition (Pre-Market High Breakout)
Type: Volatility Impulse / Structural Breakout Market: Small-cap Gappers ($1-$10), Gap > 15%, Relative Volume (RVOL) > 3.0

Core Logic:

Context: The algorithm caches the High of the Pre-Market session (4:00 AM - 9:30 AM EST).

Trigger: Price breaks above the Pre-Market High (PMH) after the market opens (9:30 AM).

Volume Filter: The 1-minute candle creating the breakout must have volume > BREAKOUT_VOL_MULT * (Average Volume of last 10 minutes).

L2 Validation: Logic checks for "Ask Kicking" (rapid depletion of Ask liquidity) to ensure the breakout isn't a fake-out into a hidden wall.

Exit Rules:

Stop Loss: Low of the Breakout Candle minus cushion (0.05 * ATR).

Take Profit: Open-ended (relies on trailing).

Time Stop: MOMENTUM_TIMEOUT (default 5 min). If price fails to expand away from entry, close.

Trailing Stop: 9-EMA Trail. If 1-min Close < 9-EMA, Exit Market.

Pyramiding:

Trigger: If price forms a "Bull Flag" above the breakout level and breaks that flag high.

Action: Add 50% of initial position.

Adjustment: Move Hard Stop to Break-Even immediately.

Scaling Out:

Scale 1: Sell 50% at +5% gain (Lock bank roll).

Scale 2: Sell 25% at +10% gain.

Runner: Hold 25% for Trailing Stop.

Configurable Parameters:

PMH_BUFFER_CENTS (default: 0.02)

BREAKOUT_VOL_MULT (default: 2.0)

MIN_GAP_PCT (default: 15.0)

MOMENTUM_TIMEOUT (default: 5)

MAX_SPREAD_ALLOWED (default: 0.05)

Strategy 2: The "Micro-Flag" (ABCD Pattern)
Type: Trend Continuation / Pattern Recognition Market: Trending Stocks, Price > VWAP, RSI > 50

Core Logic:

Context: Stock makes a sharp impulse move up (The Pole) > 4%.

Setup: Price enters a consolidation period (The Flag) for 2 to 8 candles on the 1-minute chart.

Constraint: Retracement of the flag must not exceed 50% of the Pole height (MAX_RETRACE_RATIO).

Trigger: Price breaks the High of the Flag consolidation range.

Volume Decay: Volume during the flag needs to be lower than the Pole volume (selling absorption).

Exit Rules:

Stop Loss: Lowest Low of the Flag consolidation.

Take Profit: Measured Move (Length of Pole projected from Breakout).

Trailing Stop: Low of the Previous 1-Minute Candle (Aggressive Tight Trail).

Pyramiding:

Trigger: DISABLED. High-frequency scalp; speed is prioritized over size accumulation.

Scaling Out:

Scale 1: Sell 75% at 1:1 Risk/Reward Ratio.

Scale 2: Sell 25% on Trailing Stop.

Configurable Parameters:

MIN_POLE_PCT (default: 4.0)

MAX_FLAG_CANDLES (default: 8)

MAX_RETRACE_RATIO (default: 0.5)

FLAG_VOL_DECAY_RATIO (default: 0.8)

FORCE_ENTRY_ON_WICK (default: True)

Strategy 3: VWAP Washout (The "Dip Buy")
Type: Mean Reversion / Support Logic Market: Strong Trenders (Up > 20% on Day) that experience panic selling

Core Logic:

Context: Stock is trending above VWAP but flushes down aggressively due to profit-taking.

Setup: Price pierces below the VWAP band.

Trigger: Price reclaims (closes back above) the VWAP.

Wick Validation: The candle that pierced VWAP must have a bottom wick that is at least 40% of the total candle size (WICK_RATIO), indicating limit orders absorbed the dump.

Exit Rules:

Stop Loss: Low of the flush/washout candle.

Take Profit: Re-test of High of Day (HOD).

Time Stop: STAGNATION_EXIT (default 20 min).

Trailing Stop: VWAP Line. If price closes below VWAP again, the thesis is invalid -> Exit.

Pyramiding:

Trigger: If price reclaims the 20-SMA after the VWAP bounce.

Action: Add 25% size.

Scaling Out:

Scale 1: Sell 33% at 50% retracement of the drop.

Scale 2: Sell 33% at HOD.

Scale 3: Trail the rest.

Configurable Parameters:

VWAP_ANCHOR (default: "SESSION")

WICK_RATIO_MIN (default: 0.4)

FLUSH_MIN_PCT (default: 3.0)

STAGNATION_EXIT (default: 20)

MAX_Attempts (default: 2)

Strategy 4: LULD Halt Arbitrage
Type: Event-Driven / Latency Arbitrage Market: Stocks halted on Circuit Breaker (Code M / LULD)

Core Logic:

Context: Stock enters a volatility halt. System subscribes to L1/L2 data during halt.

Data Ingestion: Monitor the "Indicative Match Price" (IMP) published by the exchange during the halt.

Trigger:

Scenario A (Gap Up): If IMP > Last Halt Price by GAP_THRESH_PCT, enter Market Buy on the exact second of resumption.

Scenario B (Gap Down): If IMP < Last Halt Price, wait for "Green over Red" candle pattern.

Safety: Do not enter if the spread is > $0.10 at resumption.

Exit Rules:

Stop Loss:

Hard Stop: Resumption Price - 5% (Volatility guard).

Technical Stop: Low of the resumption candle.

Take Profit: Next Halt Up Level (approx 10% higher).

Time Stop: 2 Minutes. (Momentum must be instant).

Trailing Stop: 10-period SMA on 10-second chart (requires high-res data).

Pyramiding: DISABLED (Too much gap risk).

Scaling Out:

Scale 1: Sell 100% into the flash spike (typically 10-30 seconds post-resumption).

Configurable Parameters:

GAP_THRESH_PCT (default: 2.0)

RESUMPTION_BUFFER_MS (default: 50)

MAX_SPREAD_AT_OPEN (default: 0.10)

FLASH_SCALP_SECONDS (default: 15)

Strategy 5: Parabolic Exhaustion (Short)
Type: Counter-Trend / Reversal Market: Over-extended Runners (Up > 50% on day), Late Day (after 11:00 AM)

Core Logic:

Context: Price is extended > EXT_MA_DIST % from the 9-EMA on the 5-minute chart.

Setup: A "Climax Candle" appears (Volume 3x average) with a long upper wick.

Trigger: Short Entry when price breaks the Low of the Climax Candle.

Constraint: Must confirm "Short Locate" availability via broker API before triggering.

Exit Rules:

Stop Loss: High of the Climax Candle + $0.05.

Take Profit: Touch of the 9-EMA or VWAP.

Time Stop: 15 Minutes.

Trailing Stop: VWAP. Cover if price reclaims VWAP from below.

Pyramiding:

Trigger: If price breaks VWAP to the downside and retests it as resistance.

Action: Add 25% to Short position.

Scaling Out:

Scale 1: Cover 50% at 9-EMA test.

Scale 2: Cover 25% at VWAP test.

Scale 3: Cover remainder at Session Low.

Configurable Parameters:

EXT_MA_DIST (default: 15.0)

CLIMAX_VOL_MULT (default: 3.0)

LOCATE_REQUIRED (default: True)

MAX_SHORT_RISK_PCT (default: 2.0)

RSI_OVERBOUGHT (default: 80)