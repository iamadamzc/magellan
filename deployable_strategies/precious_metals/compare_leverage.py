"""
Compare conservative leverage levels for precious metals
"""
import sys
sys.path.insert(0, '.')
from gold_silver_trend import run_trend_backtest

print("=" * 60)
print("CONSERVATIVE LEVERAGE COMPARISON")
print("Strategy: RSI Trend-Following (52/35 bands)")
print("Capital: $20,000")
print("=" * 60)

print("\n=== GOLD (GCUSD) ===")
for lev in [3, 4, 5, 6, 8]:
    r = run_trend_backtest(
        'GCUSD', '2024-01-01', '2025-01-24', 20000, 
        leverage=lev, rsi_period=28, entry_band=52, exit_band=35, 
        verbose=False
    )
    mark = " ✅ TARGET" if r['avg_daily_pnl'] >= 200 else ""
    print(f"  {lev}x: ${r['avg_daily_pnl']:.0f}/day | DD: {r['max_drawdown_pct']:.0f}%{mark}")

print("\n=== SILVER (SIUSD) ===")
for lev in [3, 4, 5, 6, 8]:
    r = run_trend_backtest(
        'SIUSD', '2024-01-01', '2025-01-24', 20000,
        leverage=lev, rsi_period=28, entry_band=52, exit_band=35,
        verbose=False
    )
    mark = " ✅ TARGET" if r['avg_daily_pnl'] >= 200 else ""
    print(f"  {lev}x: ${r['avg_daily_pnl']:.0f}/day | DD: {r['max_drawdown_pct']:.0f}%{mark}")

print("\n" + "=" * 60)
print("Note: PDT $25k rule applies to EQUITIES only.")
print("      Futures (MGC/MSI) are EXEMPT from PDT.")
print("=" * 60)
