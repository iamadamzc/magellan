"""
V17 MULTI-ASSET HUNT - Find the Winners
Testing V17 regime filter on top candidates across asset classes
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from research.new_strategy_builds.strategies.orb_v17_simple_regime import run_orb_v17_simple_regime

# Top candidates across asset classes
candidates = [
    # Crypto Proxies
    ('MARA', 'Crypto Proxy'),
    ('MSTR', 'Crypto Proxy'),
    ('COIN', 'Crypto Proxy'),
    
    # Leveraged ETFs
    ('TQQQ', '3x Tech ETF'),
    ('SQQQ', '3x Inverse Tech'),
    
    # High Vol Stocks
    ('SMCI', 'AI/Tech'),
    ('TSLA', 'EV/Tech'),
    
    # Small Caps (already tested, for comparison)
    ('TNMG', 'Small Cap'),
    ('CGTL', 'Small Cap'),
]

# Futures will need different handling, test these separately
futures_candidates = [
    ('NG', 'Natural Gas'),
    ('GC', 'Gold'),
    ('CL', 'Crude Oil'),
    ('KC', 'Coffee'),
]

print("\n" + "="*80)
print("V17 MULTI-ASSET PROFITABILITY HUNT")
print("Testing V17 regime filter on top candidates - Full 2024")
print("="*80)

results = []

# Test equities/ETFs
for symbol, asset_class in candidates:
    print(f"\n{'='*80}")
    print(f"Testing: {symbol} ({asset_class})")
    print(f"{'='*80}")
    
    try:
        result = run_orb_v17_simple_regime(symbol, '2024-01-01', '2024-12-31')
        
        if result:
            results.append({
                'symbol': symbol,
                'asset_class': asset_class,
                'total_pnl': result['total_pnl'],
                'total_trades': result['total_trades'],
                'win_rate': result['win_rate'],
                'days_traded': result.get('days_traded', 0),
                'days_skipped': result.get('days_skipped', 0)
            })
            
            status = "🎉 WINNER" if result['total_pnl'] > 0 else "❌ LOSER"
            print(f"\n{status}: {symbol} = {result['total_pnl']:+.2f}% ({result['total_trades']} trades)")
    
    except Exception as e:
        print(f"❌ Error testing {symbol}: {e}")
        results.append({
            'symbol': symbol,
            'asset_class': asset_class,
            'total_pnl': 0,
            'total_trades': 0,
            'win_rate': 0,
            'days_traded': 0,
            'days_skipped': 0,
            'error': str(e)
        })

# Summary
print("\n" + "="*80)
print("FINAL RESULTS - WINNER BOARD")
print("="*80)

import pandas as pd
df = pd.DataFrame(results)

# Sort by P&L
df_sorted = df.sort_values('total_pnl', ascending=False)

print(f"\n{'Rank':<6} {'Symbol':<8} {'Asset Class':<18} {'P&L':>12} {'Trades':>8} {'Win%':>8} {'Status':<10}")
print("─"*80)

for idx, row in df_sorted.iterrows():
    rank = df_sorted.index.get_loc(idx) + 1
    status = "✅ DEPLOY" if row['total_pnl'] > 0 else "❌ REJECT"
    print(f"{rank:<6} {row['symbol']:<8} {row['asset_class']:<18} {row['total_pnl']:>11.2f}% {row['total_trades']:>8} {row['win_rate']:>7.1f}% {status:<10}")

# Winners
winners = df[df['total_pnl'] > 0]
print(f"\n{'='*80}")
print(f"🏆 WINNERS FOUND: {len(winners)}/{len(df)}")
print(f"{'='*80}")

if len(winners) > 0:
    print(f"\n✅ DEPLOYABLE STRATEGIES:")
    for _, winner in winners.iterrows():
        print(f"   • {winner['symbol']:<8} {winner['total_pnl']:+.2f}% ({winner['total_trades']} trades, {winner['win_rate']:.1f}% win rate)")
    
    avg_winner_pnl = winners['total_pnl'].mean()
    total_winner_pnl = winners['total_pnl'].sum()
    
    print(f"\n📊 Portfolio Stats (if deploying all winners equally):")
    print(f"   Average Return per Symbol: {avg_winner_pnl:+.2f}%")
    print(f"   Combined Return: {total_winner_pnl:+.2f}%")
    print(f"\n🚀 READY FOR DEPLOYMENT!")
    
else:
    print(f"\n⚠️  No profitable symbols found")
    print(f"   Consider:")
    print(f"   1. Test futures (NG, GC, CL, KC)")
    print(f"   2. Try different timeframes (5-min bars)")
    print(f"   3. Test in bull market periods only")

# Best overall
if len(df) > 0:
    best = df_sorted.iloc[0]
    worst = df_sorted.iloc[-1]
    
    print(f"\n🥇 Best Performer: {best['symbol']} ({best['total_pnl']:+.2f}%)")
    print(f"🥉 Worst Performer: {worst['symbol']} ({worst['total_pnl']:+.2f}%)")

print(f"\n{'='*80}\n")

# Save results
output_path = project_root / 'research' / 'new_strategy_builds' / 'results' / 'V17_MULTI_ASSET_HUNT.csv'
df.to_csv(output_path, index=False)
print(f"📁 Results saved to: {output_path}")
