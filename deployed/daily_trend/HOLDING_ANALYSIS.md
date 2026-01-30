# Strategy Holding Analysis: Daily Trend & Hourly Swing

**Date:** Jan 27, 2026
**Issue:** User reported trades for IWM, GOOGL, GLD held for >1 week.
**Finding:** **Correct Strategy Behavior (Hysteresis Loop)**

## Analysis of "Stuck" Trades

The **Daily Trend Hysteresis** and **Hourly Swing** strategies are **Trend Following** momentum systems, not Mean Reversion scalpers. They use a "Hysteresis" logic to capture long moves:

1.  **ENTER LONG** when RSI breaks **ABOVE** Upper Band (Strong Momentum).
2.  **EXIT LONG** *only* when RSI drops **BELOW** Lower Band (Trend Reversal).
3.  **HOLD** when RSI is in the "Hysteresis Zone" (Middle).

### Specific Symbol Analysis

| Symbol | Entry Date | Logic | Upper Band (Buy) | Lower Band (Sell) | Status | Analysis |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **GLD** | Jan 21 | Daily Trend | **65** | **35** | **HOLD** | The band is extremely wide (30 points). GLD likely spiked >65 to trigger entry. It will NOT sell until RSI drops below 35. It can stay in the 36-64 zone for weeks. |
| **IWM** | Jan 22 | Daily Trend | **58** | **42** | **HOLD** | Entered on strength (>58). Holding while RSI > 42. |
| **GOOGL**| Jan 22 | Daily Trend | **55** | **45** | **HOLD** | Tighter bands, but if Google is chopping or drifting, RSI often stays ~50, triggering a hold. |

## Verification of Code Logic

`deployable_strategies/daily_trend/strategy.py`:
```python
if current_rsi > upper_band:
    self.signals[symbol] = "BUY"
elif current_rsi < lower_band:  # <--- Crucial: Only sells on cross BELOW
    self.signals[symbol] = "SELL"
else:
    self.signals[symbol] = "HOLD"  # <--- Hysteresis Zone
```

## Conclusion

The strategies are **working as designed**. They are "letting winners run" (or holding through noise) because the trend reversal signal (RSI < Lower Band) has not yet triggered.

- **Bear Trap** (your other strategy) is a quick scalper (30 mins).
- **Daily Trend** is a medium-term swing strategy (Days/Weeks).
- **Hourly Swing** is a short swing strategy (Hours/Days).

**Recommendation:** Do not manually interfere unless you want to change the strategy's risk profile. The long hold times are a feature, not a bug.
