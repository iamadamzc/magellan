"""Show actual trade details"""

import sys

sys.path.insert(0, ".")
from gold_silver_trend import run_trend_backtest

print("=" * 60)
print("ACTUAL TRADE BREAKDOWN - GOLD")
print("=" * 60)

result = run_trend_backtest(
    "GCUSD",
    "2024-01-01",
    "2025-01-24",
    20000,
    leverage=6,
    rsi_period=35,
    entry_band=48,
    exit_band=40,
    verbose=True,
)

print()
print("Trade Details:")
for i, row in result["trades_df"].iterrows():
    entry = row["entry_price"]
    exit_p = row["exit_price"]
    pnl = row["pnl"]
    print(f"  Trade {i+1}: Entry ${entry:.0f} -> Exit ${exit_p:.0f} = ${pnl:,.0f} P&L")

print()
print(f"TOTAL P&L: ${result['total_pnl']:,.0f}")
print(f"Trading days: {result['trading_days']}")
print(f"Avg per trade: ${result['total_pnl']/result['total_trades']:,.0f}")
print()
print("NOTE: 'Daily P&L' is just total/days - NOT actual daily income!")
print(f"Real situation: {result['total_trades']} big trades over the year")
