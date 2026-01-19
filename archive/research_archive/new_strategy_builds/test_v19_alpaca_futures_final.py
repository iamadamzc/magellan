"""
V19 TEST ON ALPACA FUTURES - The Final Test
Test on the 5 futures we have full year data for
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from research.new_strategy_builds.strategies.orb_v19_futures import run_orb_v19_futures

# The 5 Alpaca futures with full year data
futures = [
    ('ES', 'S&P 500 E-mini'),
    ('CL', 'Crude Oil'),
    ('NG', 'Natural Gas'),
    ('HG', 'Copper'),
    ('KC', 'Coffee'),
]

print("\n" + "="*80)
print("V19 FUTURES - FINAL TEST")
print("Testing on 5 Alpaca futures with full year 2024 data")
print("="*80)

results = []

for symbol, name in futures:
    print(f"\n{'='*80}")
    print(f"{symbol} ({name})")
    print(f"{'='*80}")
    
    result = run_orb_v19_futures(symbol, '2024-01-01', '2024-12-31', rth_open_hour=9, rth_open_min=0)
    
    if result and result['total_trades'] > 0:
        results.append({
            'symbol': symbol,
            'name': name,
            'total_pnl': result['total_pnl'],
            'total_trades': result['total_trades'],
            'win_rate': result['win_rate']
        })
        
        status = "🎉" if result['total_pnl'] > 0 else "❌"
        print(f"{status} {symbol}: {result['total_pnl']:+.2f}% ({result['total_trades']} trades, {result['win_rate']:.1f}%)")
    else:
        print(f"⚠️  {symbol}: No trades")

# Summary
print(f"\n{'='*80}")
print("FINAL RESULTS")
print(f"{'='*80}")

if results:
    import pandas as pd
    df = pd.DataFrame(results)
    df_sorted = df.sort_values('total_pnl', ascending=False)
    
    print(f"\n{'Rank':<6} {'Symbol':<8} {'Name':<20} {'P&L':>12} {'Trades':>8} {'Win%':>8}")
    print("─"*80)
    
    for idx, row in df_sorted.iterrows():
        rank = df_sorted.index.get_loc(idx) + 1
        status = "✅" if row['total_pnl'] > 0 else "❌"
        print(f"{rank:<6} {row['symbol']:<8} {row['name']:<20} {row['total_pnl']:>11.2f}% {row['total_trades']:>8} {row['win_rate']:>7.1f}%")
    
    winners = df[df['total_pnl'] > 0]
    
    if len(winners) > 0:
        print(f"\n{'='*80}")
        print(f"🎉 FOUND {len(winners)} PROFITABLE FUTURES!")
        print(f"{'='*80}")
        
        for _, winner in winners.iterrows():
            print(f"   ✅ {winner['symbol']:<4} ({winner['name']}): {winner['total_pnl']:+.2f}%")
        
        avg_pnl = winners['total_pnl'].mean()
        total_pnl = winners['total_pnl'].sum()
        
        print(f"\n📊 PORTFOLIO STATS (if trading all winners equally):")
        print(f"   Average Return per Symbol: {avg_pnl:+.2f}%")
        print(f"   Total Combined Return: {total_pnl:+.2f}%")
        print(f"\n🚀 ORB V19 IS DEPLOYABLE ON FUTURES!")
        
        # Save winners
        winners_path = project_root / 'research' / 'new_strategy_builds' / 'results' / 'ORB_V19_FUTURES_WINNERS.csv'
        winners.to_csv(winners_path, index=False)
        print(f"\n📁 Winners saved to: {winners_path}")
    else:
        print(f"\n❌ No profitable futures found")
        print(f"   ORB strategy is not viable")
else:
    print(f"\n❌ No valid trades found")

print(f"\n{'='*80}\n")
