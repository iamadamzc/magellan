"""
QUANTITATIVE ANALYSIS: Why Tuning Test Results Differ from Actual Trading

This analysis identifies the methodological flaw in the 15-hour tuning test.
"""

import pandas as pd
import numpy as np

print("=" * 80)
print("QUANTITATIVE ANALYSIS: METHODOLOGY COMPARISON")
print("=" * 80)

#------------------------------------------------------------------------------
# FINDING 1: THE BUG IN THE TUNING TEST
#------------------------------------------------------------------------------

print("""
================================================================================
FINDING #1: CRITICAL BUG IN TUNING TEST METHODOLOGY
================================================================================

The 15-hour tuning test (tune_strategy.py) has a fundamental flaw:

TUNING TEST CODE (lines 110-125):
```python
# Forward returns - THIS IS WRONG
oos_data['forward_return'] = oos_data['log_return'].shift(-forward_horizon)

# This compounds ALL bars' returns in a single day
position_returns = valid['signal'] * valid['forward_return']
period_return = (1 + position_returns).prod() - 1
```

WHAT THIS ACTUALLY CALCULATES:
- forward_return = log_return at bar T+20 (a single 1-minute return)
- NOT the cumulative return from T to T+20

EXAMPLE:
- Bar at 10:00: signal = LONG
- forward_return = log_return at 10:20 = log(close[10:20] / close[10:19])
- This is the 1-minute return from 10:19 to 10:20
- NOT the 20-minute return from 10:00 to 10:20

CORRECT CALCULATION SHOULD BE:
- forward_return = log(close[T+20] / close[T])
- OR sum of log returns from T to T+20

This bug causes MASSIVE overestimation of returns because:
1. It applies signal to ~350 bars per day
2. Each bar's "forward return" is just a random 1-min return in the future
3. The product of many small returns compounds exponentially
""")

#------------------------------------------------------------------------------
# FINDING 2: OVERLAPPING POSITIONS
#------------------------------------------------------------------------------

print("""
================================================================================
FINDING #2: OVERLAPPING POSITIONS IN TUNING TEST
================================================================================

The tuning test evaluates a signal at EVERY bar, creating overlapping "positions":

Time    Signal    "Forward Return" Being Used
10:00   LONG      Return at 10:20
10:01   SHORT     Return at 10:21
10:02   LONG      Return at 10:22
...     ...       ...
10:20   LONG      Return at 10:40

This means:
- 350+ "positions" per day, all compounding together
- Many signals for the same future time window
- Massive return amplification

CORRECT APPROACH (optimal_backtest.py):
- Enter at 10:00, hold until 10:20, exit = 1 trade
- Next trade starts at 10:20 = 1 trade
- ~20 non-overlapping trades per day
""")

#------------------------------------------------------------------------------
# FINDING 3: NUMERICAL VERIFICATION
#------------------------------------------------------------------------------

print("""
================================================================================
FINDING #3: NUMERICAL VERIFICATION
================================================================================
""")

# Load trade data
trades_df = pd.read_csv('optimal_trades.csv')

# Summary by symbol
for symbol in ['SPY', 'QQQ', 'IWM']:
    sym_df = trades_df[trades_df['symbol'] == symbol]
    
    # Calculate trades per day
    sym_df['date'] = pd.to_datetime(sym_df['entry_time']).dt.date
    trades_per_day = sym_df.groupby('date').size()
    
    print(f"\n{symbol}:")
    print(f"  Total trades: {len(sym_df):,}")
    print(f"  Trading days: {sym_df['date'].nunique()}")
    print(f"  Avg trades/day: {trades_per_day.mean():.1f}")
    print(f"  Hit rate: {sym_df['correct'].mean()*100:.1f}%")
    print(f"  Total P&L: ${sym_df['pnl_dollars'].sum():,.2f}")
    print(f"  Avg P&L/trade: ${sym_df['pnl_dollars'].mean():.4f}")

#------------------------------------------------------------------------------
# FINDING 4: WHY RESULTS DIFFER
#------------------------------------------------------------------------------

print("""
================================================================================
FINDING #4: ROOT CAUSE OF DISCREPANCY
================================================================================

TUNING TEST REPORTED:
- SPY: +78.58% return
- QQQ: +119.14% return
- IWM: +40.16% return

ACTUAL TRADING SIMULATION:
- SPY: -11.49% return
- QQQ: +30.28% return  
- IWM: -67.54% return

ROOT CAUSES:
1. Wrong forward return calculation (1-min return instead of N-min cumulative)
2. Overlapping positions (350/day vs 20/day)
3. Compounding artifact (many small returns multiplied together)

THE TUNING TEST WAS FUNDAMENTALLY FLAWED AND GAVE MISLEADING RESULTS.
The "optimal" parameters were selected based on broken methodology.
""")

#------------------------------------------------------------------------------
# FINDING 5: ACTUAL STRATEGY PERFORMANCE
#------------------------------------------------------------------------------

print("""
================================================================================
FINDING #5: ACTUAL STRATEGY PERFORMANCE (CORRECT METHODOLOGY)
================================================================================
""")

# Analyze by trade outcome
for symbol in ['SPY', 'QQQ', 'IWM']:
    sym_df = trades_df[trades_df['symbol'] == symbol].copy()
    
    winning_trades = sym_df[sym_df['pnl_dollars'] > 0]
    losing_trades = sym_df[sym_df['pnl_dollars'] <= 0]
    
    avg_win = winning_trades['pnl_dollars'].mean() if len(winning_trades) > 0 else 0
    avg_loss = losing_trades['pnl_dollars'].mean() if len(losing_trades) > 0 else 0
    
    print(f"\n{symbol}:")
    print(f"  Winning trades: {len(winning_trades):,} ({100*len(winning_trades)/len(sym_df):.1f}%)")
    print(f"  Losing trades: {len(losing_trades):,} ({100*len(losing_trades)/len(sym_df):.1f}%)")
    print(f"  Avg win: ${avg_win:.2f}")
    print(f"  Avg loss: ${avg_loss:.2f}")
    
    if avg_loss != 0:
        profit_factor = abs(winning_trades['pnl_dollars'].sum() / losing_trades['pnl_dollars'].sum())
        print(f"  Profit factor: {profit_factor:.3f}")

#------------------------------------------------------------------------------
# FINDING 6: SIGNAL ANALYSIS
#------------------------------------------------------------------------------

print("""
================================================================================
FINDING #6: SIGNAL DIRECTION ANALYSIS
================================================================================
""")

for symbol in ['SPY', 'QQQ', 'IWM']:
    sym_df = trades_df[trades_df['symbol'] == symbol]
    
    long_trades = sym_df[sym_df['signal'] == 'LONG']
    short_trades = sym_df[sym_df['signal'] == 'SHORT']
    
    long_hr = long_trades['correct'].mean() * 100 if len(long_trades) > 0 else 0
    short_hr = short_trades['correct'].mean() * 100 if len(short_trades) > 0 else 0
    
    long_pnl = long_trades['pnl_dollars'].sum()
    short_pnl = short_trades['pnl_dollars'].sum()
    
    print(f"\n{symbol}:")
    print(f"  LONG trades: {len(long_trades):,} | Hit rate: {long_hr:.1f}% | P&L: ${long_pnl:,.2f}")
    print(f"  SHORT trades: {len(short_trades):,} | Hit rate: {short_hr:.1f}% | P&L: ${short_pnl:,.2f}")

print("\n" + "=" * 80)
print("CONCLUSION")  
print("=" * 80)
print("""
The 15-hour tuning test was fundamentally flawed due to:
1. Incorrect forward return calculation
2. Overlapping position evaluation
3. Compounding artifacts

The "optimal" parameters selected by this test are NOT optimal.
They were selected based on broken methodology.

RECOMMENDATION:
1. Discard the tuning test results
2. Use the actual trading simulation results
3. Investigate why hit rates are consistently below 50%
4. Consider if this strategy has any edge at all
""")
print("=" * 80)
