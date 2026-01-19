"""Quick test of ORB strategy"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from research.new_strategy_builds.strategies.orb_strategy import run_orb_backtest

# Test on 3 symbols × 2 periods
test_cases = [
    ('RIOT', '2024-11-01', '2025-01-17'),
    ('RIOT', '2025-04-01', '2025-06-30'),
    ('MARA', '2024-11-01', '2025-01-17'),
    ('AMC', '2024-11-01', '2025-01-17'),
]

results = []
for symbol, start, end in test_cases:
    try:
        result = run_orb_backtest(symbol, start, end)
        results.append(result)
    except Exception as e:
        print(f"✗ {symbol} {start}: {e}")

print("\n" + "="*80)
print("ORB STRATEGY - BATCH TEST RESULTS")
print("="*80)

if results:
    import pandas as pd
    df = pd.DataFrame(results)
    print(df[['symbol', 'total_trades', 'win_rate', 'avg_pnl', 'sharpe']].to_string(index=False))
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total tests: {len(df)}")
    print(f"Total trades: {df['total_trades'].sum()}")
    print(f"Avg trades per test: {df['total_trades'].mean():.1f}")
    print(f"Avg win rate: {df['win_rate'].mean():.1f}%")
    print(f"Avg P&L per trade: {df['avg_pnl'].mean():+.2f}%")
    print(f"Avg Sharpe: {df['sharpe'].mean():.2f}")
