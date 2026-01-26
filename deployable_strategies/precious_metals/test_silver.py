"""Test silver with optimized RSI 55/30 bands"""

import sys

sys.path.insert(0, ".")
from gold_silver_trend import run_trend_backtest

print("SILVER with RSI 55/30 (Very Wide) bands:")
print("-" * 50)
for lev in [5, 6, 7, 8, 9, 10]:
    r = run_trend_backtest(
        "SIUSD",
        "2024-01-01",
        "2025-01-24",
        20000,
        leverage=lev,
        rsi_period=28,
        entry_band=55,
        exit_band=30,
        verbose=False,
    )
    mark = " <<< TARGET" if r["avg_daily_pnl"] >= 200 else ""
    print(
        f"{lev}x: ${r['avg_daily_pnl']:.0f}/day | DD: {r['max_drawdown_pct']:.0f}% | Trades: {r['total_trades']}{mark}"
    )
