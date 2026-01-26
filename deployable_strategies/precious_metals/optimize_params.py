"""
Parameter Grid Search for Precious Metals Strategy
Goal: Find parameters that achieve $200/day at LOWEST leverage
"""
import sys
sys.path.insert(0, '.')
from gold_silver_trend import run_trend_backtest
import pandas as pd

TARGET_DAILY_PNL = 200
CAPITAL = 20000

print("=" * 70)
print("PARAMETER OPTIMIZATION: Finding lowest leverage for $200/day target")
print("=" * 70)

results = []

# Test different RSI band combinations
rsi_configs = [
    (52, 35, "Wide (52/35) - baseline"),
    (50, 40, "Narrow (50/40) - more trades"),
    (55, 30, "Very Wide (55/30) - longer holds"),
    (48, 42, "Tight (48/42) - frequent trading"),
    (52, 38, "Medium (52/38)"),
]

print("\nTesting RSI band configurations on GOLD...")
print("-" * 70)

for entry, exit_band, desc in rsi_configs:
    for lev in [5, 6, 7, 8, 9, 10]:
        r = run_trend_backtest(
            'GCUSD', '2024-01-01', '2025-01-24', CAPITAL,
            leverage=lev, rsi_period=28, entry_band=entry, exit_band=exit_band,
            verbose=False
        )
        results.append({
            'entry': entry,
            'exit': exit_band,
            'desc': desc,
            'leverage': lev,
            'daily_pnl': r['avg_daily_pnl'],
            'total_return': r['total_return_pct'],
            'max_dd': r['max_drawdown_pct'],
            'trades': r['total_trades'],
            'win_rate': r['win_rate']
        })

df = pd.DataFrame(results)

# Find configurations that hit $200/day
winners = df[df['daily_pnl'] >= TARGET_DAILY_PNL].copy()
if len(winners) > 0:
    # Sort by lowest leverage first
    winners = winners.sort_values('leverage')
    print("\n✅ CONFIGURATIONS THAT HIT $200/day (sorted by lowest leverage):")
    print("-" * 70)
    for _, row in winners.head(10).iterrows():
        print(f"{row['leverage']}x | RSI {row['entry']}/{row['exit']} | ${row['daily_pnl']:.0f}/day | DD: {row['max_dd']:.0f}% | Trades: {row['trades']}")
else:
    print("\n❌ No configuration hit $200/day target")

# Show best for each leverage level
print("\n📊 BEST CONFIG PER LEVERAGE LEVEL:")
print("-" * 70)
for lev in [5, 6, 7, 8]:
    lev_df = df[df['leverage'] == lev]
    best = lev_df.loc[lev_df['daily_pnl'].idxmax()]
    print(f"{lev}x: RSI {best['entry']:.0f}/{best['exit']:.0f} -> ${best['daily_pnl']:.0f}/day | DD: {best['max_dd']:.0f}%")
