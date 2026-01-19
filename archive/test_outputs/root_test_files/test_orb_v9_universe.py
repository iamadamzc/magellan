"""Test ORB V9 on Cached Universe"""
import sys
from pathlib import Path
import pandas as pd

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from research.new_strategy_builds.strategies.orb_v9 import run_orb_v9

# Load cached universe
cached_symbols = ['CGTL', 'CTMX', 'IBRX', 'JCSE', 'LCFY', 'NEOV', 'TNMG', 'TYGO', 'VERO']

print("="*80)
print("ORB V9 TEST - CACHED MOMENTUM UNIVERSE")
print("="*80)
print(f"Testing {len(cached_symbols)} symbols for November 2024\n")

results = []

for symbol in cached_symbols:
    print(f"Testing {symbol}...")
    try:
        result = run_orb_v9(symbol, '2024-11-01', '2024-11-30', or_minutes=10)
        result['symbol'] = symbol
        results.append(result)
        
        print(f"  ✓ {result['total_trades']} trades | {result['win_rate']:.1f}% win | {result['avg_pnl']:+.3f}% avg")
    except Exception as e:
        print(f"  ✗ Error: {e}")

# Summary
if results:
    df = pd.DataFrame(results)
    
    print("\n" + "="*80)
    print("RESULTS - ORB V9 ON MOMENTUM UNIVERSE")
    print("="*80)
    
    total_trades = df['total_trades'].sum()
    avg_win_rate = df['win_rate'].mean()
    avg_pnl = df['avg_pnl'].mean()
    # Calculate total P&L
    total_pnl = sum(df['avg_pnl'] * df['total_trades']) / total_trades if total_trades > 0 else 0
    profitable_symbols = (df['avg_pnl'] > 0).sum()
    
    print(f"\nTotal trades: {total_trades}")
    print(f"Avg win rate: {avg_win_rate:.1f}%")
    print(f"Avg P&L/trade: {avg_pnl:+.3f}%")
    print(f"Total P&L: {total_pnl:+.2f}%")
    print(f"Profitable symbols: {profitable_symbols}/{len(df)}")
    
    print("\nBy Symbol:")
    for _, row in df.iterrows():
        status = "✅" if row['avg_pnl'] > 0 else "❌"
        print(f"  {status} {row['symbol']:6} | {row['total_trades']:3} trades | {row['win_rate']:5.1f}% win | {row['avg_pnl']:+.3f}% avg")
    
    # Save
    output_path = Path('research/new_strategy_builds/results/orb_v9_momentum_universe.csv')
    df.to_csv(output_path, index=False)
    print(f"\n✅ Results saved to: {output_path}")
    
    # Verdict
    print("\n" + "="*80)
    print("VERDICT")
    print("="*80)
    
    if avg_pnl > 0:
        print(f"🎉 PROFITABLE! {avg_pnl:+.3f}% per trade")
        print("   ORB V9 works on momentum universe!")
    elif avg_pnl > -0.05:
        print(f"⚡ NEAR BREAKEVEN: {avg_pnl:+.3f}% per trade")
        print("   Close to profitability")
    else:
        print(f"❌ LOSING: {avg_pnl:+.3f}% per trade")
        print("   Strategy needs more work or different universe")
else:
    print("\n⚠️ No results")
