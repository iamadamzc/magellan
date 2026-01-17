"""Test ORB V7 - Gem's Barbell Stack (No FTA)"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from research.new_strategy_builds.strategies.orb_v7 import run_orb_v7

tests = [
    ('RIOT', '2024-11-01', '2025-01-17'),
    ('MARA', '2024-11-01', '2025-01-17'),
    ('AMC', '2024-11-01', '2025-01-17'),
]

results = []
for symbol, start, end in tests:
    try:
        r = run_orb_v7(symbol, start, end)
        results.append(r)
    except Exception as e:
        print(f"✗ {symbol}: {e}")
        import traceback
        traceback.print_exc()

if results:
    import pandas as pd
    df = pd.DataFrame(results)
    
    print("\n" + "="*80)
    print("ORB V7 - GEM'S BARBELL STACK (NO FTA)")
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
    print("FULL PROGRESSION")
    print("="*80)
    print("V4: 920 trades, 40.8% win, -0.121% avg, -105.96% total")
    print("V5: 242 trades, 62.1% win, -0.221% avg, -55.88% total")
    print("V6: 356 trades, 39.2% win, -0.123% avg, -45.78% total (FTA killed it)")
    print(f"V7: {total_trades} trades, {avg_win_rate:.1f}% win, {avg_pnl:+.3f}% avg, {total_pnl:+.2f}% total")
    
    if total_pnl > 0:
        print("\n🎉🎉🎉 PROFITABLE STRATEGY! 🎉🎉🎉")
        print(f"✅ Achieved {avg_pnl:+.3f}% per trade (target was +0.015%)")
        print(f"✅ Total profit: {total_pnl:+.2f}%")
        print("\n🏆 ORB STRATEGY COMPLETE!")
    elif avg_pnl > -0.02:
        print("\n⚡ VERY CLOSE TO PROFITABLE!")
        print(f"Current: {avg_pnl:+.3f}% per trade")
        print(f"Target: +0.015% per trade")
        print(f"Gap: {0.015 - avg_pnl:.3f}% (minor tweaks needed)")
    else:
        improvement = total_pnl - (-45.78)
        print(f"\n✅ IMPROVEMENT: {improvement:+.2f}% better than V6")
