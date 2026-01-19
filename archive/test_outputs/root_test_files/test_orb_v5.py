"""Test ORB V5 - Expert Consensus Implementation"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from research.new_strategy_builds.strategies.orb_v5 import run_orb_v5

tests = [
    ('RIOT', '2024-11-01', '2025-01-17'),
    ('MARA', '2024-11-01', '2025-01-17'),
    ('AMC', '2024-11-01', '2025-01-17'),
]

results = []
for symbol, start, end in tests:
    try:
        r = run_orb_v5(symbol, start, end)
        results.append(r)
    except Exception as e:
        print(f"✗ {symbol}: {e}")
        import traceback
        traceback.print_exc()

if results:
    import pandas as pd
    df = pd.DataFrame(results)
    
    print("\n" + "="*80)
    print("ORB V5 - EXPERT CONSENSUS RESULTS")
    print("="*80)
    total_trades = df['total_trades'].sum()
    total_pnl = df['total_pnl'].sum()
    avg_win_rate = df['win_rate'].mean()
    avg_pnl = df['avg_pnl'].mean()
    
    print(f"Total trades: {total_trades}")
    print(f"Avg win rate: {avg_win_rate:.1f}%")
    print(f"Avg P&L/trade: {avg_pnl:+.3f}%")
    print(f"Total P&L: {total_pnl:+.2f}%")
    
    print("\n" + "="*80)
    print("COMPARISON")
    print("="*80)
    print("V4: 920 trades, 40.8% win, -0.121% avg, -105.96% total")
    print(f"V5: {total_trades} trades, {avg_win_rate:.1f}% win, {avg_pnl:+.3f}% avg, {total_pnl:+.2f}% total")
    
    if total_pnl > -105.96:
        improvement = total_pnl - (-105.96)
        print(f"\n✅ IMPROVEMENT: {improvement:+.2f}% better!")
    
    if total_pnl > 0:
        print("\n🎉🎉🎉 PROFITABLE STRATEGY! 🎉🎉🎉")
        print(f"Achieved {avg_pnl:+.3f}% per trade (target was +0.015%)")
