Here are some Small Cap Momentum Scalping Strategies suitable for algorithmic trading system  

Agent: Marina G

Strategy 1: Micro Pullback Bull Flag
Type: Momentum Continuation / Mean Reversion Market: Small-cap equities ($1-$20), low float, high relative volume Core Logic:
Identify stocks with strong upward momentum (e.g., up >20% on the day, high relative volume, clear news catalyst, priced $3-$8, float < 20 million).
Look for a sharp upward move (the "flagpole") followed by a shallow pullback on lighter volume (the "flag" or "pennant") that does not exceed ~30% retracement of the flagpole and stays above key short-term moving averages (e.g., 9 EMA) and VWAP.
Entry is triggered when a new 1-minute or 5-minute candle makes a new high, engulfing the high of the previous pullback candle, ideally on increasing volume.
Entry Rules:
Enter LONG when the price breaks the high of the last candle of the pullback/consolidation.
Volume on entry should ideally be higher than pullback volume.
Exit Rules:
Stop Loss: Below the low of the pullback/flag formation, or a fixed amount (e.g., $0.20-$0.30 per share) below entry.
Trailing Stop Loss: Can be set to trail below the low of the previous 1-min or 5-min candle, or trail by a fixed amount/percentage, or trail below a fast-moving average (e.g., 9 EMA).
Take Profit: Initial target could be $0.20-$0.50 per share, or the projected flagpole height added to the breakout, or at the next key resistance level.
Time Stop: If the trade isn't working or consolidating for too long (e.g., 10-15 minutes) without moving towards the target, exit.
Pyramiding & Scaling Out:
Pyramiding: Consider adding to the position if the price breaks subsequent small consolidation/flag patterns on the way up, with a tight stop on the add-on portion. Only pyramid from a position of profit.
Scaling Out: Take partial profits at predefined targets (e.g., scale out 1/3 at $0.20, 1/3 at $0.40, let the rest run with a trailing stop at breakeven or better).
Configurable Parameters:
MAX_PULLBACK_PERCENT (default: 30%)
MIN_REL_VOLUME (default: 3.0)
PRICE_MIN, PRICE_MAX (default: 3, 8)
MAX_FLOAT (default: 20,000,000)
STOP_LOSS_CENTS (default: 20)
TARGET_CENTS_1, TARGET_CENTS_2 (default: 20, 40)
TRAILING_STOP_TYPE (e.g., 'CANDLE_LOW', 'FIXED', 'EMA')
TRAILING_STOP_VALUE (e.g., 1 for candle, 15 cents, 9 for EMA period)
MAX_HOLD_MINUTES (default: 15)
PYRAMID_ENABLED (default: False)
SCALE_OUT_ENABLED (default: True)
Strategy 2: High of Day (HOD) Breakout/Retest
Type: Breakout / Support & Resistance Market: Small-cap equities ($1-$20), gappers, strong momentum Core Logic:
Identify stocks approaching or having recently set the high of the day (HOD).
Breakout: For a HOD breakout, look for consolidation near the HOD, then enter when the price breaks above HOD with significant volume increase.
Retest: After a breakout, if the price pulls back to retest the previous HOD (which now acts as support), look for a bounce/confirmation to enter long.
Entry Rules:
Breakout: Enter LONG when price breaks HOD with volume confirmation.
Retest: Enter LONG when price retests former HOD, holds, and starts to move up, ideally with a bullish candle pattern and volume.
Exit Rules:
Stop Loss:
Breakout: Below the HOD level or the low of the breakout candle.
Retest: Below the retest low.
Trailing Stop Loss: Trail below key moving averages, previous candle lows, or a fixed percentage/amount.
Take Profit: Fixed target, next resistance level, or when momentum wanes.
Time Stop: Exit if momentum doesn't continue shortly after entry.
Pyramiding & Scaling Out:
Pyramiding: Less common on initial breakout due to chase risk, but possible on subsequent consolidations after a successful breakout.
Scaling Out: Scale out at predefined profit targets or resistance levels.
Configurable Parameters:
HOD_BREAK_VOL_MULT (default: 1.5)
RETEST_CONFIRMATION_TIME (e.g., how long it holds HOD as support)
STOP_LOSS_OFFSET (cents below HOD/retest low)
TRAILING_STOP_TYPE
TRAILING_STOP_VALUE
INITIAL_TARGET_CENTS
MAX_HOLD_BREAKOUT (default: 10 min)
Strategy 3: Flat Top Breakout
Type: Breakout Market: Small-cap equities ($1-$20) Core Logic:
Identify a clear horizontal resistance level (flat top) where the price has been rejected multiple times.
Observe price action consolidating near this resistance level.
Entry is triggered when the price breaks through the flat top resistance with a surge in volume.
Entry Rules:
Enter LONG on the break of the flat top resistance level, ideally with volume significantly above average.
Exit Rules:
Stop Loss: Below the breakout level (former resistance) or low of the breakout candle.
Trailing Stop Loss: As per other strategies (candle lows, MA, fixed).
Take Profit: Measure the height of the consolidation below the flat top and project it upwards from the breakout point, or next resistance.
Time Stop: If breakout fails and price falls back below resistance quickly.
Pyramiding & Scaling Out:
Pyramiding: Possible if the price forms further consolidations above the initial breakout level.
Scaling Out: At projected targets or subsequent resistance.
Configurable Parameters:
FLATTOP_HITS_MIN (default: 2-3)
BREAKOUT_VOL_MULT (default: 2.0)
STOP_LOSS_CENTS_BELOW_BREAK
PROJECTION_TARGET_ENABLED (default: True)
TRAILING_STOP_TYPE
TRAILING_STOP_VALUE