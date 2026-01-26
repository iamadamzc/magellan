"""Test ORB Final"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from research.new_strategy_builds.strategies.orb_final import run_orb_final

tests = [
    ('RIOT', '2024-11-01', '2025-01-17'),
    ('MARA', '2024-11-01', '2025-01-17'),
    ('AMC', '2024-11-01', '2025-01-17'),
]

results = []
for symbol, start, end in tests:
    try:
        r = run_orb_final(symbol, start, end)
        results.append(r)
        print(f"  → {r['total_trades']} trades | {r['win_rate']:.1f}% win | {r['avg_pnl']:+.3f}% avg | {r['total_pnl']:+.2f}% total")
    except Exception as e:
        print(f"✗ {symbol}: {e}")

if results:
    import pandas as pd
    df = pd.DataFrame(results)
    
    print("\n" + "="*80)
    print("ORB FINAL - RESULTS")
    print("="*80)
    total_trades = df['total_trades'].sum()
    total_pnl = df['total_pnl'].sum()
    avg_win_rate = df['win_rate'].mean()
    avg_pnl = df['avg_pnl'].mean()
    
    print(f"Total trades: {total_trades}")
    print(f"Avg win rate: {avg_win_rate:.1f}%")
    print(f"Avg P&L/trade: {avg_pnl:+.3f}%")
    print(f"Total P&L: {total_pnl:+.2f}%")
    
    if total_pnl > 0:
        print("\n🎉 PROFITABLE STRATEGY!")
    else:
        print(f"\n⚠️ Still losing {total_pnl:.2f}%")
