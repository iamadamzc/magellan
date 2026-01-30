# Strategy Holding Analysis: Hourly Swing

**Date:** Jan 27, 2026
**Strategy:** Hourly Swing (RSI Hysteresis)
**Symbols:** TSLA, NVDA

## Why Trails Are Held > 1 Week

Just like the Daily Trend strategy, the Hourly Swing strategy uses **Hysteresis Logic** to capture sustained momentum. It is **NOT** a day trading strategy; it is designed to hold through minor pullbacks.

### Logic Mechanism
1.  **Entry:** Momentum confirms (RSI > Upper Band).
2.  **Hold:** Trend is active (RSI between Bands).
3.  **Exit:** Trend breaks (RSI < Lower Band).

### Specific Symbol Thresholds

| Symbol | RSI Period | Upper Band (Buy) | Lower Band (Sell) | Implication |
| :--- | :--- | :--- | :--- | :--- |
| **TSLA** | **14** (Standard) | **> 60** | **< 40** | TSLA is highly volatile. An RSI(14) can stay above 40 for weeks during a bull run. It only exits on a sharp correction. |
| **NVDA** | **28** (Smooth) | **> 55** | **< 45** | Using RSI(28) creates a very smooth signal. It ignores almost all intraday noise. NVDA must basically crash or enter a deep bear trend to trigger the `< 45` exit. |

## Code Verification

File: `deployable_strategies/hourly_swing/strategy.py`

```python
# Lines 163-172
if (current_position == "flat" and current_rsi > symbol_params["hysteresis_upper"]):
    self._enter_long(symbol)

# Lines 173-181
elif (current_position == "long" and current_rsi < symbol_params["hysteresis_lower"]):
    self._exit_position(symbol)

else:
    # Lines 184-186
    self.logger.debug(f"{symbol}: RSI={current_rsi:.2f} → HOLD")
```

## Conclusion

The "stuck" trades are actually **Winning Trades** being managed correctly.
- If you were to manually close them, you would be cutting your winners short (violating the core "Let Winners Run" maxim).
- The strategy is waiting for a confirmed trend reversal (RSI breakdown) before exiting.

**Verdict:** System is functioning 100% as designed.
