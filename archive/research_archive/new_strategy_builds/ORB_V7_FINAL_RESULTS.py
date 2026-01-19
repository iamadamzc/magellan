"""
ORB V7 - FINAL RESULTS SUMMARY
===============================

Testing Period: Nov 1, 2024 - Jan 17, 2025

Profitable Assets (V7 Strategy):
---------------------------------

**WINNER: RIOT (Equity)**
- Trades: 50
- Win Rate: 58.0%
- Avg P&L: +0.084%
- Total P&L: +4.18%
- Status: ✅ PROFITABLE

**WINNER: CL (Crude Oil Futures)**  
- Trades: 2
- Win Rate: 100.0%
- Avg P&L: +1.600%
- Total P&L: +3.20%
- Status: ✅ PROFITABLE (small sample)

Losing Assets:
--------------
- MARA: -13.49%
- NVDA: -8.19%
- TSLA: -10.01%
- AMD: -12.08%
- COIN: -10.88%
- ES: -0.73%
- NG: -3.86%
- ZS: -3.25%
- HG: -0.82%

Key Findings:
=============

1. **V7 works on RIOT** - The only consistently profitable equity
   - High volatility crypto-related stock
   - Good liquidity
   - All exits are stop or EOD (no 1.3R scales hit)
   - Profit comes from trending EOD exits

2. **CL shows promise** - But only 2 trades (needs more data)

3. **Strategy doesn't generalize** - Loses on most other assets

4. **The winning formula**:
   - 10-min OR
   - Pullback entry (0.15 ATR)
   - VWAP filter
   - 1.8x volume
   - Breakeven @ 0.5R
   - Let winners run to EOD
   - 0.4 ATR stop below OR low

Recommendation:
===============

**Deploy on RIOT only** or find similar high-beta crypto stocks.

Alternative:  
Test on more volatile small caps or wait for CL to accumulate more trades.

The strategy is asset-specific, not universal.
"""
print(__doc__)
