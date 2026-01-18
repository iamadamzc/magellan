"""Batch Test ORB V10C - Aggressive Breakout"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
from research.new_strategy_builds.strategies.orb_v10c import run_orb_v10c

symbols = ['RIOT', 'MARA', 'AMC', 'JCSE', 'LCFY', 'CTMX', 'BIYA', 'IBRX', 'RIOX', 'CGTL', 'TNMG', 'VERO', 'NEOV', 'TYGO']

print("="*80)
print("ORB V10C - AGGRESSIVE BREAKOUT (VOLUME 1.2x, NO VWAP, NO FTA)")
print("="*80)

all_trades = []
for symbol in symbols:
    try:
        print(f"{symbol}...", end=' ')
        trades = run_orb_v10c(symbol, '2024-11-01', '2024-11-30')
        all_trades.extend(trades)
        print(f"✓ {len(trades)}")
    except Exception as e:
        print(f"✗ {e}")

print(f"\n{'='*80}")
print(f"TOTAL: {len(all_trades)} trades")

if len(all_trades) > 0:
    df = pd.DataFrame(all_trades)
    df['pnl_net'] = df['pnl_pct'] - 0.125
    
    print(f"Win Rate: {(df['pnl_net'] > 0).sum() / len(df) * 100:.1f}%")
    print(f"Avg P&L:  {df['pnl_net'].mean():+.3f}%")
    print(f"Total P&L: {df['pnl_net'].sum():+.2f}%")
    print(f"Sharpe:   {df['pnl_net'].mean() / df['pnl_net'].std():.2f}" if df['pnl_net'].std() > 0 else "Sharpe:   N/A")
    
    print(f"\nExit Breakdown:")
    for exit_type, count in df['type'].value_counts().items():
        avg_pnl = df[df['type'] == exit_type]['pnl_net'].mean()
        print(f"  {exit_type:<15}: {count:>3} ({count/len(df)*100:>5.1f}%)  Avg: {avg_pnl:+.3f}%")
    
    df.to_csv('research/new_strategy_builds/results/orb_v10c_trades.csv', index=False)
    print(f"\n✓ Saved to orb_v10c_trades.csv")
