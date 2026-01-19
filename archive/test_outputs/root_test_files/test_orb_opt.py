"""Test ORB Optimized"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from research.new_strategy_builds.strategies.orb_optimized import run_orb_optimized

test_cases = [
    ('RIOT', '2024-11-01', '2025-01-17'),
    ('RIOT', '2025-04-01', '2025-06-30'),
    ('MARA', '2024-11-01', '2025-01-17'),
    ('AMC', '2024-11-01', '2025-01-17'),
]

results = []
for symbol, start, end in test_cases:
    try:
        result = run_orb_optimized(symbol, start, end)
        results.append(result)
    except Exception as e:
        print(f"✗ {symbol}: {e}")

if results:
    import pandas as pd
    df = pd.DataFrame(results)
    
    print("\n" + "="*80)
    print("ORB OPTIMIZED - RESULTS")
    print("="*80)
    print(df.to_string(index=False))
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total trades: {df['total_trades'].sum()}")
    print(f"Avg trades/test: {df['total_trades'].mean():.1f}")
    print(f"Avg win rate: {df['win_rate'].mean():.1f}%")
    print(f"Avg P&L/trade: {df['avg_pnl'].mean():+.3f}%")
    print(f"Total P&L: {df['total_pnl'].sum():+.2f}%")
    print(f"Avg Sharpe: {df['sharpe'].mean():.2f}")
    
    # Check if profitable
    if df['total_pnl'].sum() > 0:
        print("\n✅ STRATEGY IS PROFITABLE!")
    else:
        print("\n⚠️ Still losing, need more optimization")
