"""Test V19 on futures with correct RTH handling"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from research.new_strategy_builds.strategies.orb_v19_futures import run_orb_v19_futures

futures = ['NG', 'CL', 'KC', 'HG']

print("\n" + "="*80)
print("V19 FUTURES - FIXED RTH SESSION TIMES")
print("="*80)

results = []

for symbol in futures:
    print(f"\n{'='*80}")
    print(f"{symbol}")
    print(f"{'='*80}")
    
    result = run_orb_v19_futures(symbol, '2024-01-01', '2024-12-31', rth_open_hour=9, rth_open_min=0)
    
    if result and result['total_trades'] > 0:
        results.append(result)
        status = "🎉" if result['total_pnl'] > 0 else "❌"
        print(f"{status} {symbol}: {result['total_pnl']:+.2f}%")

if results:
    import pandas as pd
    df = pd.DataFrame(results)
    df_sorted = df.sort_values('total_pnl', ascending=False)
    
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    for _, row in df_sorted.iterrows():
        status = "✅" if row['total_pnl'] > 0 else "❌"
        print(f"{status} {row['symbol']}: {row['total_pnl']:+.2f}% ({row['total_trades']} trades, {row['win_rate']:.1f}%)")
    
    winners = df[df['total_pnl'] > 0]
    if len(winners) > 0:
        print(f"\n🎉 FOUND {len(winners)} PROFITABLE FUTURES!")
    else:
        print(f"\n❌ No winners")
