"""
Bear Trap - Missing Symbols Test
Test the 12 symbols that had no data or errors
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from research.new_strategy_builds.strategies.bear_trap import run_bear_trap

# Symbols that had no trades or errors from first run
missing_symbols = [
    'BBBY',   # Meme (no trades)
    'PROG',   # Biotech (no trades)
    'TELL',   # Energy (no trades)
    'BKKT',   # Energy (no trades)
    'RIDE',   # Energy (no trades)
    'BBIG',   # Retail (no trades)
    'CLOV',   # Retail (no trades)
    'WISH',   # Retail (no trades)
    'LCID',   # EV (no trades)
    'HYLN',   # EV (no trades)
    'NMCI',   # Shipping (error)
    'HEXO',   # Misc (error)
    'MATX',   # Shipping (no trades)
    'SBLK',   # Shipping (no trades)
    'GOGL',   # Shipping (no trades)
    'SKLZ',   # Misc (no trades)
    'DKNG',   # Misc (no trades)
]

print("\n" + "="*80)
print("BEAR TRAP - MISSING SYMBOLS TEST")
print("Testing 17 symbols that had no data/trades")
print("="*80)

results = []

for symbol in missing_symbols:
    try:
        result = run_bear_trap(symbol, '2024-01-01', '2024-12-31')
        
        if result['total_trades'] > 0:
            results.append(result)
            print(f"✅ {symbol}: Found trades!")
        else:
            print(f"⚠️  {symbol}: Still no trades")
    
    except Exception as e:
        print(f"❌ {symbol}: Error - {str(e)[:80]}")

# Summary
if results:
    import pandas as pd
    df = pd.DataFrame(results)
    df_sorted = df.sort_values('total_pnl_pct', ascending=False)
    
    print(f"\n{'='*80}")
    print("RECOVERED SYMBOLS")
    print(f"{'='*80}")
    print(f"\n{'Symbol':<8} {'P&L %':>10} {'P&L $':>12} {'Trades':>8} {'Win%':>8}")
    print("─"*80)
    
    for _, row in df_sorted.iterrows():
        status = "✅" if row['total_pnl_pct'] > 0 else "❌"
        print(f"{row['symbol']:<8} {row['total_pnl_pct']:>9.2f}% ${row['total_pnl_dollars']:>10,.0f} {row['total_trades']:>8} {row['win_rate']:>7.1f}%")
    
    winners = df[df['total_pnl_pct'] > 0]
    
    print(f"\n📊 SUMMARY:")
    print(f"   Recovered: {len(df)} symbols")
    print(f"   Profitable: {len(winners)}")
    print(f"   Total P&L: ${df['total_pnl_dollars'].sum():,.0f}")
    
    if len(winners) > 0:
        print(f"   Best: {winners.iloc[0]['symbol']} ({winners.iloc[0]['total_pnl_pct']:+.2f}%)")
        
        # Save
        df.to_csv('research/new_strategy_builds/results/BEAR_TRAP_RECOVERED.csv', index=False)
        print(f"\n📁 Saved to: BEAR_TRAP_RECOVERED.csv")
else:
    print(f"\n❌ No additional symbols recovered")

print(f"\n{'='*80}\n")
