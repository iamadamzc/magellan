"""Test V10E"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import pandas as pd
from research.new_strategy_builds.strategies.orb_v10e import run_orb_v10e

symbols = ['RIOT', 'MARA', 'AMC', 'JCSE', 'LCFY', 'CTMX', 'BIYA', 'IBRX']

print("V10E - WIDER TARGETS (0.5R/1.0R/2.0R)")
all_trades = []
for sym in symbols:
    try:
        trades = run_orb_v10e(sym, '2024-11-01', '2024-11-30')
        all_trades.extend(trades)
        print(f"{sym}: {len(trades)}")
    except: pass

if all_trades:
    df = pd.DataFrame(all_trades)
    df['pnl_net'] = df['pnl_pct'] - 0.125
    print(f"\nTOTAL: {len(df)} | Win: {(df['pnl_net']>0).sum()/len(df)*100:.1f}% | Avg: {df['pnl_net'].mean():+.3f}% | Total: {df['pnl_net'].sum():+.2f}% | Sharpe: {df['pnl_net'].mean()/df['pnl_net'].std():.2f}")
    for t, c in df['type'].value_counts().items():
        print(f"  {t}: {c} ({df[df['type']==t]['pnl_net'].mean():+.3f}%)")
