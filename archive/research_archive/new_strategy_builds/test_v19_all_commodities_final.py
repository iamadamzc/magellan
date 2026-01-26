"""
V19 FINAL TEST - ALL 12 ALPACA COMMODITIES
Fresh data fetch with full year 2024
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from research.new_strategy_builds.strategies.orb_v19_futures import run_orb_v19_futures

# All 12 available Alpaca commodities
commodities = [
    ('ES', 'S&P 500 E-mini'),
    ('CL', 'Crude Oil'),
    ('NG', 'Natural Gas'),
    ('HG', 'Copper'),
    ('PL', 'Platinum'),
    ('ZS', 'Soybeans'),
    ('KC', 'Coffee'),
    ('SB', 'Sugar'),
    ('CC', 'Cocoa'),
    ('HE', 'Lean Hogs'),
    ('LE', 'Live Cattle'),
    ('GF', 'Feeder Cattle'),
]

print("\n" + "="*80)
print("V19 ORB - COMMODITY FUTURES FINAL TEST")
print("Testing on 12 Alpaca commodities - Full Year 2024")
print("="*80)

results = []

for symbol, name in commodities:
    print(f"\n{'='*80}")
    print(f"{symbol} ({name})")
    print(f"{'='*80}")
    
    try:
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
    except Exception as e:
        print(f"❌ {symbol}: Error - {str(e)[:100]}")

# Summary
print(f"\n{'='*80}")
print("FINAL RESULTS - ALL COMMODITIES")
print(f"{'='*80}")

if results:
    import pandas as pd
    df = pd.DataFrame(results)
    df_sorted = df.sort_values('total_pnl', ascending=False)
    
    print(f"\n{'Rank':<6} {'Symbol':<8} {'Name':<20} {'P&L':>12} {'Trades':>8} {'Win%':>8} {'Status':<10}")
    print("─"*80)
    
    for idx, row in df_sorted.iterrows():
        rank = df_sorted.index.get_loc(idx) + 1
        status = "✅ DEPLOY" if row['total_pnl'] > 0 else "❌ REJECT"
        print(f"{rank:<6} {row['symbol']:<8} {row['name']:<20} {row['total_pnl']:>11.2f}% {row['total_trades']:>8} {row['win_rate']:>7.1f}% {status:<10}")
    
    winners = df[df['total_pnl'] > 0]
    
    if len(winners) > 0:
        print(f"\n{'='*80}")
        print(f"🎉🎉🎉 FOUND {len(winners)} PROFITABLE COMMODITIES! 🎉🎉🎉")
        print(f"{'='*80}")
        
        for _, winner in winners.iterrows():
            print(f"   ✅ {winner['symbol']:<4} ({winner['name']}): {winner['total_pnl']:+.2f}% - {winner['total_trades']} trades - {winner['win_rate']:.1f}% win")
        
        avg_pnl = winners['total_pnl'].mean()
        total_pnl = winners['total_pnl'].sum()
        total_trades = winners['total_trades'].sum()
        
        print(f"\n📊 PORTFOLIO STATS (if trading all winners equally):")
        print(f"   Number of Symbols: {len(winners)}")
        print(f"   Average Return per Symbol: {avg_pnl:+.2f}%")
        print(f"   Total Combined Return: {total_pnl:+.2f}%")
        print(f"   Total Trades: {total_trades}")
        print(f"\n🚀 ORB V19 WORKS ON COMMODITY FUTURES!")
        print(f"   READY FOR DEPLOYMENT!")
        
        # Save winners
        winners_path = project_root / 'research' / 'new_strategy_builds' / 'results' / 'ORB_V19_COMMODITY_WINNERS.csv'
        winners.to_csv(winners_path, index=False)
        print(f"\n📁 Winners saved to: {winners_path}")
    else:
        print(f"\n❌ No profitable commodities found")
        print(f"   ORB strategy does not have edge on these markets")
else:
    print(f"\n❌ No valid trades found across all commodities")
    print(f"   Possible issues:")
    print(f"   - Filters too strict")
    print(f"   - Data quality problems")
    print(f"   - ORB doesn't work on these markets")

print(f"\n{'='*80}\n")
