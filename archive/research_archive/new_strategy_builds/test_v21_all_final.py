"""
V21 ADAPTIVE SESSION - FINAL TEST ON ALL COMMODITIES
Uses each symbol's actual session start time
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from research.new_strategy_builds.strategies.orb_v21_adaptive import run_orb_v21_adaptive

commodities = [
    ('ES', 'S&P 500'),
    ('CL', 'Crude Oil'),
    ('NG', 'Natural Gas'),
    ('HG', 'Copper'),
    ('PL', 'Platinum'),
    ('ZS', 'Soybeans'),
    ('KC', 'Coffee'),
    ('SB', 'Sugar'),
    ('CC', 'Cocoa'),
    ('HE', 'Lean Hogs'),
]

print("\n" + "="*80)
print("V21 ADAPTIVE SESSION - ALL COMMODITIES FINAL TEST")
print("="*80)

results = []

for symbol, name in commodities:
    print(f"\n{'='*80}")
    print(f"{symbol} ({name})")
    print(f"{'='*80}")
    
    try:
        result = run_orb_v21_adaptive(symbol, '2024-01-01', '2024-12-31')
        
        if result and result['total_trades'] > 0:
            results.append({
                'symbol': symbol,
                'name': name,
                'total_pnl': result['total_pnl'],
                'total_trades': result['total_trades'],
                'win_rate': result['win_rate']
            })
            
            status = "🎉" if result['total_pnl'] > 0 else "❌"
            print(f"{status} {result['total_pnl']:+.2f}%")
    except Exception as e:
        print(f"❌ Error: {str(e)[:100]}")

# Results
if results:
    import pandas as pd
    df = pd.DataFrame(results)
    df_sorted = df.sort_values('total_pnl', ascending=False)
    
    print(f"\n{'='*80}")
    print("FINAL RESULTS")
    print(f"{'='*80}")
    print(f"\n{'Rank':<6} {'Symbol':<8} {'Name':<20} {'P&L':>12} {'Trades':>8} {'Win%':>8}")
    print("─"*80)
    
    for idx, row in df_sorted.iterrows():
        rank = df_sorted.index.get_loc(idx) + 1
        status = "✅" if row['total_pnl'] > 0 else "❌"
        print(f"{rank:<6} {row['symbol']:<8} {row['name']:<20} {row['total_pnl']:>11.2f}% {row['total_trades']:>8} {row['win_rate']:>7.1f}%")
    
    winners = df[df['total_pnl'] > 0]
    
    if len(winners) > 0:
        print(f"\n🎉 {len(winners)} PROFITABLE!")
        for _, w in winners.iterrows():
            print(f"   ✅ {w['symbol']}: {w['total_pnl']:+.2f}%")
        
        # Save
        winners.to_csv('research/new_strategy_builds/results/ORB_V21_WINNERS.csv', index=False)
        print(f"\n📁 Saved to: ORB_V21_WINNERS.csv")
    else:
        print(f"\n❌ No profitable commodities")
else:
    print(f"\n❌ No trades")

print(f"\n{'='*80}\n")
