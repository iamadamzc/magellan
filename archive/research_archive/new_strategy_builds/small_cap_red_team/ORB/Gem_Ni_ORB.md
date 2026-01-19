Based on the ORB_PARAMETER_TUNING_SUMMARY.md provided, I have conducted a deep review of your current strategy state (V4).Here is the hard truth: You do not have a trading strategy; you have a time-based exit algorithm.When 96.7% of your trades exit via Time Stop, you are not testing the validity of the breakout; you are simply measuring the drift of the asset over 30 minutes. The market is not being given enough room to breathe, nor enough time to reach your profit targets (only 0.3% reach 1R).Here are my specific recommendations to tune this strategy from a losing state to a potential winner, prioritized by impact.1. Critical Fix: The "Time Stop" FallacyProblem: The 30-minute hard stop is the primary cause of failure. It artificially caps your upside (Positive Drift) while ensuring you pay the spread/friction on every attempt.The Fix: Replace the Hard Time Stop with a Technical Invalidator.Logic Change: Volatility in Small Caps (RIOT, MARA) is bursty. If the price is above the breakout level and above VWAP, there is no reason to exit simply because 30 minutes have passed.Recommendation:Remove MAX_HOLD_MINUTES entirely or set it to "End of Day" (e.g., 3:55 PM).Implement an "Inactivity Stop" instead: If price fails to make a new high within 15 minutes after entry, then exit. This filters out "zombie" trades without killing active trends.2. Entry Filter: Respect the VWAPProblem: The current logic enters on a price break of the OR High. In Mean Reverting regimes (choppy markets), price often breaks the High, grabs liquidity, and slams back down.The Fix: Add a Regime Filter.Logic Change: Never go long if the price is below the Volume Weighted Average Price (VWAP), even if it breaks the OR High.Formula:$$Condition = (Price > OR_{High}) \land (Price > VWAP_{Current})$$Why: VWAP acts as the "institutional line in the sand." Longs above VWAP have a higher probability of sustaining momentum.3. Tightening the "R" (Risk Unit)Problem: Your stop loss is OR Low - 0.6 ATR. For a 10-minute candle on RIOT, the range between High and Low can be massive. This makes your "1R" target extremely far away, explaining why only 0.3% of trades hit it.The Fix: Decouple the Stop from the OR Low.Logic Change: Use the Midpoint or VWAP as the stop, or a tighter ATR trail from the Entry Price rather than the OR Low.Recommendation:Stop Loss: max(OR_Low, VWAP_at_Entry - 0.2 ATR)Effect: This shrinks the distance of "1R." If your risk is smaller, your 1R profit target is closer, increasing the hit rate of your profit taking.4. Optimize Exit: The "3-Bar Reversal"Problem: The trailing stop of 0.8 ATR is decent, but ATR lags.The Fix: Use Price Action trailing.Logic Change: Once the trade is > 0.5R, trail the stop at the Low of the previous 3 candles.Why: This allows the stock to trend but exits immediately when momentum breaks structure.Proposed "V5" Configuration (Winning Candidate)Here is the specific parameter set I recommend for your next grid search:ParameterOld Value (V4)New Value (V5)RationaleOR_MINUTES101510m is noisy; 15m aligns with significant market algo timestamps.STOP_LOGICOR Low - 0.6 ATRVWAP - 0.2 ATRTightens risk; increases R-Multiple velocity.MAX_HOLD30 minOFF (End of Day)Let winners run. 96% exit rate on time stops is unacceptable.ENTRY_FILTERNonePrice > VWAPEnsures we aren't buying a "trap" breakout in a downtrend.PROFIT_TAKE1R (0.4 scale)None (Full Trail)If you catch a trend, don't cap it. Scale out only if momentum stalls.TRAIL_STOP0.8 ATRLow of Last 5 MinsTighter trail once in profit to lock in gains faster.Mathematical Expectancy AdjustmentYou noted a friction of 12.5 bps.$$Friction = 0.125\%$$$$Avg PnL (Current) = -0.121\%$$You are essentially paying the broker to churn capital. By removing the time stop, you reduce the number of churned trades and increase the magnitude of the winners (the "Fat Tail").The Goal for V5:Reduce trade frequency from ~900 to ~300 (higher quality).Increase Average Winner size from <1R to >2R by removing the 30-minute cap.Suggested Code Modification (Python/Pandas Logic)Python# V5 Proposed Logic Snippet

# 1. Regime Filter
is_above_vwap = df['close'] > df['vwap']

# 2. Breakout Condition
breakout = (df['close'] > df['or_high']) & (df['volume'] > df['avg_vol'] * VOL_MULT)

# 3. Entry Signal (Must satisfy both)
df['entry_signal'] = breakout & is_above_vwap

# 4. Stop Loss Calculation (Tighter)
# Instead of OR Low, use the average of OR Open and Close, or VWAP
df['stop_loss'] = df['vwap'] - (df['atr'] * 0.3) 

# 5. Inactivity Exit (Replacing Max Hold)
# If price hasn't made a new high in 15 mins, exit
bars_since_high = df.groupby('trade_id')['high'].apply(lambda x: x.expanding().max())
# (Implementation logic would go here)  
  
  Here is the drafted V5 Strategy Class (orb_v5_vwap_trend.py).I have structured this to be compatible with standard event-driven or vectorized backtesting frameworks (like the one implied by your file structure). I have incorporated the VWAP Regime Filter, Inactivity Stop, and Dynamic Trailing to address the critical flaws identified in the V4 review.Strategy Logic: V5 - "VWAP Trend & Trail"Entry: Breakout of 15m OR High + Price > VWAP.Stop Loss: Initial risk anchored to VWAP, not the arbitrary OR Low.Exit:Inactivity Stop: Exits if price stagnates for 15 mins (replaces the 30m hard time stop).3-Bar Low Trail: Locks in profit aggressively once the trade works.Pythonimport pandas as pd
import numpy as np
from dataclasses import dataclass

@dataclass
class ORBParameters:
    # --- Tuned V5 Parameters ---
    OR_MINUTES: int = 15          # Wider range to filter noise
    VOL_MULT: float = 1.5         # Keep volume confirmation
    STOP_ATR_DIST: float = 0.2    # Tighter initial risk (from VWAP)
    
    # --- Management ---
    INACTIVITY_PERIOD: int = 15   # Exit if no new high in 15 mins
    TRAIL_TRIGGER_R: float = 0.5  # Start trailing after 0.5R profit
    TRAIL_LOOKBACK: int = 3       # Trail stop at lowest low of last 3 bars
    
    # --- Position Sizing ---
    RISK_PCT: float = 0.01        # Risk 1% account equity per trade

class ORBStrategyV5:
    """
    V5: VWAP Regime Filter + Inactivity Stop + 3-Bar Trailing
    Designed to fix the '96.7% Time Stop' issue identified in V4.
    """
    
    def __init__(self, data, params=ORBParameters()):
        self.data = data
        self.params = params
        self.orders = []
        
    def calculate_indicators(self):
        """Pre-calculate technicals needed for decision logic."""
        df = self.data.copy()
        
        # 1. Opening Range (First N minutes of session)
        session_start = df.index.time[0] # Assuming intraday data chunks
        or_slice = df.between_time(session_start, 
                                   (pd.Timestamp(str(session_start)) + pd.Timedelta(minutes=self.params.OR_MINUTES)).time())
        
        df['or_high'] = or_slice['high'].max()
        df['or_low'] = or_slice['low'].min()
        
        # 2. VWAP Calculation (Session based)
        df['cum_vol'] = df['volume'].cumsum()
        df['cum_pv'] = (df['close'] * df['volume']).cumsum()
        df['vwap'] = df['cum_pv'] / df['cum_vol']
        
        # 3. ATR for Stops
        df['tr'] = np.maximum(df['high'] - df['low'], 
                              np.abs(df['high'] - df['close'].shift(1)))
        df['atr'] = df['tr'].rolling(14).mean()
        
        # 4. Volume SMA
        df['vol_sma'] = df['volume'].rolling(20).mean()
        
        return df

    def generate_signal(self, bar, context):
        """
        Determines entry validation.
        REPLACES V4 Logic: Adds VWAP Regime Filter.
        """
        # Condition A: Price breaks OR High
        breakout = bar['close'] > context['or_high']
        
        # Condition B: Volume Spike
        vol_check = bar['volume'] > (context['vol_sma'] * self.params.VOL_MULT)
        
        # Condition C: VWAP Regime (NEW)
        # Prevents buying 'traps' where price pops but remains below institutional average
        vwap_check = bar['close'] > context['vwap']
        
        if breakout and vol_check and vwap_check:
            return True
        return False

    def manage_trade(self, position, bar, context):
        """
        Manages active position exits.
        REPLACES V4 Logic: Removes Hard Time Stop, adds Inactivity & Technical Trail.
        """
        
        # 1. Update Inactivity Counter
        # If current price > highest price seen in trade, reset counter
        if bar['high'] > position.highest_high:
            position.highest_high = bar['high']
            position.bars_since_high = 0
        else:
            position.bars_since_high += 1
            
        # 2. Check Inactivity Stop (The "Zombie" Killer)
        # Instead of killing ALL trades at 30 mins, only kill STALLED trades
        if position.bars_since_high >= self.params.INACTIVITY_PERIOD:
            return "EXIT_INACTIVITY"

        # 3. Dynamic Stop Loss Management
        # Initial Stop: VWAP - 0.2 ATR (Tighter than V4's OR Low)
        initial_stop = context['vwap'] - (context['atr'] * self.params.STOP_ATR_DIST)
        
        # Trailing Logic: 3-Bar Low
        # Once we are in profit (0.5R), move stop to low of last 3 bars
        current_r = (bar['close'] - position.entry_price) / (position.entry_price - initial_stop)
        
        if current_r > self.params.TRAIL_TRIGGER_R:
            three_bar_low = context['history'][-self.params.TRAIL_LOOKBACK:]['low'].min()
            new_stop = max(position.stop_loss, three_bar_low)
            position.stop_loss = new_stop
            
        # Check if stopped out
        if bar['low'] < position.stop_loss:
            return "EXIT_STOP_LOSS"
            
        return "HOLD"
Summary of ChangesFeatureOld Logic (V4)New Logic (V5)ImpactStop LossOR Low - 0.6 ATRVWAP - 0.2 ATRTightens Risk: Reduces R-distance, making 1R targets easier to hit.Exit30-min Hard StopInactivity StopFixes Cut Winners: Only exits if the stock stops trending (15m of no new highs).FilterNonePrice > VWAPQuality Control: Prevents long entries in bearish intraday trends.TrailingFixed ATR Trail3-Bar LowReacts Faster: Price action trailing captures rapid reversals better than ATR.Next StepI recommend running a Backtest Comparison between V4 and this V5 code specifically on RIOT.Metric to watch: Look at the "Avg Winning Trade Duration." In V4 it was likely capped at 20-30m. In V5, you want to see this expand to 45m+ for winners, indicating you are capturing the full trend.