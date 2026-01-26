
Small Cap Momentum Scalping Strategies for Algorithmic Trading
Overview

Agent: Dee S.

The following strategies are designed for small-cap equities ($1B - $2B market cap) with high relative volume and volatility. Each strategy incorporates full risk management protocols including stop-loss, trailing stops, pyramiding, and scaling-out mechanics.

Strategy 1: Momentum Squeeze Breakout
Type: Momentum / Volatility Contraction Expansion
Core Concept: Identifies periods of low volatility (Bollinger Band squeeze) followed by a high-momentum breakout on elevated volume, signaling the start of a directional move.

Entry Logic (LONG):

Volatility Condition: (Upper_BB(20,2) - Lower_BB(20,2)) / SMA(20) < VOL_SQZ_THRESH (e.g., 0.1) for SQZ_BARS (e.g., 5) consecutive bars.

Volume Spike: Current volume > VOL_SPIKE_MULT (e.g., 1.5) * VWAP(20) volume.

Breakout Bar: Price closes above Upper_BB(20,2) with a strong body ((close - open) / (high - low) > MIN_BODY_STRENGTH, e.g., 0.6).

Momentum Confirmation: RSI(2) > RSI_ENTRY (e.g., 60) and Keltner_Channel(20, 1.5) is expanding.

Exit & Risk Management:

Initial Stop Loss: Lower_BB(20,2) or entry_price - (ATR(14) * STOP_ATR_MULT).

Trailing Stop: Activates after price moves TRAIL_TRIGGER (e.g., 0.03) above entry. Trail using a parabolic SAR with an aggressive factor (PSAR_AF_START = 0.02, PSAR_AF_MAX = 0.2).

Take Profit Targets (Scaling Out):

TP1 (33% of position): entry_price + (ATR(14) * TP1_ATR_MULT).

TP2 (33% of position): entry_price + (ATR(14) * TP2_ATR_MULT). Trail remainder with SAR.

TP3 (34% of position): Held for a potential runner, exited via trailing SAR.

Pyramiding Rules: A second unit may be added if the price pulls back to the Upper_BB(20,2) (now acting as support) and rebounds with volume, provided the initial position is in profit > PYRAMID_MIN_PROFIT.

Configurable Parameters:

VOL_SQZ_THRESH: 0.08 - 0.12

SQZ_BARS: 3 - 7

VOL_SPIKE_MULT: 1.3 - 2.0

MIN_BODY_STRENGTH: 0.55

STOP_ATR_MULT: 1.0 - 1.5

TP1_ATR_MULT: 1.0 - 1.3

TP2_ATR_MULT: 2.0 - 2.5

TRAIL_TRIGGER: 0.02 - 0.04

PYRAMID_MIN_PROFIT: 0.01 (1%)

Strategy 2: Gap & Go (Pre-Market Momentum)
Type: Gap / Opening Range Breakout
Core Concept: Exploits momentum from significant pre-market gaps. Takes a directional bet on the gap holding and accelerating as the regular session begins.

Entry Logic (LONG):

Gap Filter: Pre-market price > previous close * MIN_GAP_PERCENT (e.g., 1.02 for a 2% gap up).

Pre-Market Trend: Pre-market high > pre-market VWAP, indicating sustained buying interest.

Opening Range Break (ORB): In the first ORB_MINUTES (e.g., 5) of RTH, price breaks above the high of the 1-minute opening range.

Volume Confirmation: Volume on the breakout bar > ORB_VOL_MULT (e.g., 3.0) * average 1-minute volume for the same period in prior days.

Exit & Risk Management:

Initial Stop Loss: The low of the opening range (for LONG) OR pre_market_VWAP (whichever is higher).

Trailing Stop: Activates at TRAIL_ACTIVATION_R (e.g., R_multiple of 2). Uses a dynamic, volume-adjusted stop: highest_close_since_entry - (ATR(5) * VOL_ADJ_TRAIL_MULT), where the multiplier increases as volume declines.

Scaling Out:

TP1 (50%): entry_price + (Gap_Size * TP1_GAP_MULT) (e.g., 0.5). Tighten stop to breakeven on TP1 fill.

TP2 (50%): Target VWAP of the session, or exit via trailing stop.

Pyramiding: Not typically used due to the compressed time frame. Overridden if a clear secondary base forms near VWAP with low volatility.

Configurable Parameters:

MIN_GAP_PERCENT: 1.015 - 1.04 (1.5% - 4%)

ORB_MINUTES: 3 - 10

ORB_VOL_MULT: 2.0 - 5.0

TP1_GAP_MULT: 0.5 - 1.0

TRAIL_ACTIVATION_R: 1.5 - 2.5 (Risk Multiple)

VOL_ADJ_TRAIL_MULT: 1.0 - 2.5

Strategy 3: VWAP Reversion Scalp
Type: Mean Reversion / Statistical Edge
Core Concept: Capitalizes on the magnetic pull of VWAP in small caps. Fades extreme moves away from VWAP, expecting a reversion, with a momentum filter to avoid catching falling knives.

Entry Logic (SHORT - for moves above VWAP):

Deviation: Price > VWAP + DEV_THRESHOLD * ATR(14) (e.g., 0.8).

Momentum Exhaustion: RSI(5) > RSI_OVERBOUGHT (e.g., 75). MACD(12,26,9) histogram shows deceleration.

Rejection Signal: A 1- or 2-minute candle shows a strong upper wick ((high - max(open, close)) / (high - low) > WICK_RATIO, e.g., 0.4) or closes near its low.

Volume Confirmation: Volume on the rejection candle is elevated relative to recent average.

Exit & Risk Management:

Initial Stop Loss: Above the recent swing high or entry_price + (ATR(14) * REV_STOP_MULT).

Profit Target: Primary target is VWAP. Secondary target is VWAP - SECONDARY_TARGET_ATR * ATR.

Trailing Stop: Not typically used for a pure reversion play; system exits fully at target.

Scaling Out: 70% at VWAP, 30% runner to secondary target.

Pyramiding: A second, smaller unit can be added if price bounces off VWAP and shows rejection again at the DEV_THRESHOLD level, forming a "double top" pattern relative to VWAP.

Configurable Parameters:

DEV_THRESHOLD: 0.7 - 1.2 (ATR multiples from VWAP)

RSI_OVERBOUGHT/OVERSOLD: 75 / 25

WICK_RATIO: 0.35 - 0.5

REV_STOP_MULT: 0.5 - 0.8

SECONDARY_TARGET_ATR: 0.3 - 0.6

Strategy 4: Micro-Pump Fade (Illiquidity Exploit)
Type: Counter-Trend / Micro-Structure
Core Concept: Targets low-float, low-dollar small caps prone to artificial "pumps." Fades parabolic, high-speed moves on unsustained volume.

Entry Logic (SHORT):

Velocity Filter: Price increase > PUMP_VELOCITY% (e.g., 8%) within VELOCITY_WINDOW minutes (e.g., 3).

Volume Divergence: Price makes a new high for the move, but volume is lower than the previous high (VOL_DIV_BARS lookback).

Exhaustion Candle: A "shooting star" or "gravestone doji" forms on the 1-minute chart at the peak.

Order Book Confirmation (if available): Large sell walls appear at round-number price levels just above the high.

Exit & Risk Management:

Initial Stop Loss: Extremely tight, placed just above the exhaustion candle's high.

Trailing Stop: Activates immediately after entry due to extreme volatility. Uses a tick-based trailing stop (e.g., trail by $0.05 or $0.10 depending on price).

Profit Target: Based on measured move or key micro-support (e.g., prior 1-minute low, VWAP).

Scaling Out: 50% at ATR(5) profit, 50% at 2 * ATR(5) profit.

Pyramiding: FORBIDDEN for this strategy due to extreme risk.

Configurable Parameters:

PUMP_VELOCITY: 5% - 15%

VELOCITY_WINDOW: 2 - 5 minutes

VOL_DIV_BARS: 3 - 5

TICK_TRAIL_DISTANCE: $0.03 - $0.15 (price-dependent)

MAX_POSITION_SIZE_CAP: Strict cap as % of portfolio (e.g., 0.5%).

Strategy 5: Fractal Momentum (Multi-Timeframe Confirmation)
Type: Trend / Multi-Timeframe Momentum
Core Concept: Uses a faster timeframe (e.g., 1-min) for entry timing within the context of a momentum move identified on a higher timeframe (e.g., 5-min).

Entry Logic (LONG):

HTF Bias: 5-minute chart shows ADX(14) > MIN_ADX (e.g., 25) and EMA(8) > EMA(21). Price is above the 5-min VWAP.

LTF Trigger: On the 1-minute chart, a pullback to the EMA(8) or Keltner_Channel midline occurs.

Momentum Re-engagement: 1-minute candle breaks above the pullback's high with a close above its open.

Confirmation: 1-minute RSI(3) crosses back above 50.

Exit & Risk Management:

Initial Stop Loss: Below the low of the 1-minute pullback structure or the Lower_KC(1min, 20, 1.0).

Trailing Stop: Switches between two modes:

Aggressive: 1-minute Parabolic SAR.

Moderate: Trail below the 5-minute EMA(8).

Scaling Out:

TP1 (40%): ATR(14)[5min] target from entry.

TP2 (40%): 2 * ATR(14)[5min] target. Trail remainder.

Pyramiding: Allowed on subsequent 1-minute pullbacks to dynamic support (e.g., EMA) as long as the 5-minute trend remains intact and the position is in profit. Maximum 3 units.

Configurable Parameters:

MIN_ADX: 20 - 30

HTF_EMA_FAST/SLOW: 8 / 21

LTF_PULLBACK_TO: EMA(8) or KC_MID

TRAIL_MODE: SAR or HTF_EMA

PYRAMID_MAX_UNITS: 2 - 3

General Risk Management Overlay (Applies to All Strategies):

Daily Loss Limit: System halts if daily portfolio drawdown exceeds MAX_DAILY_LOSS (e.g., 2%).

Position Sizing: Based on ATR(14) and account risk per trade (e.g., 0.25% - 0.5%). Position Size = (Account Risk %) / ((Entry - Stop Loss) / Entry).

Correlation Check: Limits total exposure to highly correlated sectors.

Market Regime Filter: Reduces position size or skips trades if VIX > VIX_CAP (e.g., 35) or if the broader market (SPY) is below its 200-day SMA.