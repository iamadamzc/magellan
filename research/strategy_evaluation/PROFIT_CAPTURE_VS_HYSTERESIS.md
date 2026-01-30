# Strategy Evaluation: Profit Capture vs. Hysteresis Signal

**Date:** Jan 27, 2026
**Topic:** Evaluating Exit Logic for Daily Trend (Track 1) and Hourly Swing (Track 3)
**Current Logic:** Pure Trend Following (RSI Hysteresis)
**Proposed Logic:** Profit Capture Benchmark (Fixed Targets / Trailing Stops)

## 1. Current State: The "Infinite" Hold
Currently, both strategies use a "Hysteresis Loop":
- **Entry:** Strong Momentum (RSI > Upper)
- **Exit:** Trend Collapse (RSI < Lower)

**Pros:**
- Captures the "Meat of the Move" (e.g., a 20-30% run in NVDA).
- Ignores minor pullbacks and noise.
- Mathematically aligns with "Let Winners Run."

**Cons:**
- **"Round-Tripping" Profits:** You might be up +10%, but the trend reverses slowly, and you exit at +2% (or -1%) because the signal lagged.
- **Opportunity Cost:** Capital is tied up in "dead money" periods (choppy sideways movement where RSI stays between bands).
- **Psychological Drift:** Holding for weeks without realizing gains can be stressful.

## 2. Proposed Improvement: Profit Capture Benchmark
The proposal is to introduce a **Price-Based Exit** alongside or instead of the Signal-Based Exit.

### Option A: Fixed Take Profit (The "Sniper")
*Example: Sell 100% of position at +10% gain.*
- **Verdict:** **Risk of Upside Capping.**
- **Why:** If NVDA runs +40% in a month (common), you sold at +10%. You miss 75% of the trend. This is detrimental to trend-following systems which rely on a few massive winners to pay for small losers.

### Option B: The Hybrid Scaling (The "Banker")
*Example: Sell 50% at +5% gain, hold 50% until Signal Exit.*
- **Verdict:** **Strongly Recommended Alternative.**
- **Why:**
    1.  **Locks in Profit:** financing the risk of the remaining position.
    2.  **Reduces Variance:** Smooths out the equity curve.
    3.  **Retains Upside:** You still catch the "runner" with half size.

### Option C: ATR Trailing Stop (The "Protector")
*Example: Trail a stop 3x ATR below the highest price.*
- **Verdict:** **Best for Volatility Management.**
- **Why:** It respects the volatility of the asset. If the price crashes *before* the RSI signal reacts, the Trailing Stop gets you out. It prevents giving back open profits during a sharp crash.

## 3. Implementation Plan for Evaluation

To validate this hypothesis, we should run a **Comparative Backtest** (using the `backtrader` engine already in the repo):

**Scenario 1 (Baseline):** Current RSI Hysteresis (Benchmark).
**Scenario 2 (Fixed):** RSI Entry + Sell at +8% Profit.
**Scenario 3 (Trailing):** RSI Entry + 3x ATR Trailing Stop.

### Recommendation
I agree that **pure signal exits** can be inefficient in choppy markets (giving back gains). However, replacing it *entirely* with a fixed target usually hurts long-term P&L in trending assets like TSLA/NVDA.

**My suggestion:** Implement **Option C (ATR Trailing Stop)** or **Option B (Scaling)**. This adds a "profit floor" without putting a "profit ceiling" on your winners.

## 4. Decision Log (Jan 27, 2026)
**User Decision:** Defer execution.
**Status:** **Backlog / Future Consideration**.
**Notes:** The concept of adding profit capture benchmarks (scaling or trailing stops) is valid but lowers priority vs. current stability tasks. We will revisit this when optimizing the Daily Trend/Hourly Swing performance in Q2.
