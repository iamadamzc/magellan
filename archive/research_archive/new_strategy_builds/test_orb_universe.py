"""Test V7 on Full Universe - Speedboats vs Mid-Cap vs Tankers"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from research.new_strategy_builds.strategies.orb_v7 import run_orb_v7
import pandas as pd

# Define universe by category
universe = {
    'SPEEDBOATS (Float < 20M)': [
        ('SAVA', '2024-11-01', '2025-01-17'),
        ('MULN', '2024-11-01', '2025-01-17'),
        ('GREE', '2024-11-01', '2025-01-17'),
        ('SPRC', '2024-11-01', '2025-01-17'),
    ],
    'MID-CAP (50M-100M Float)': [
        ('HOOD', '2024-11-01', '2025-01-17'),
        ('SOFI', '2024-11-01', '2025-01-17'),
        ('DKNG', '2024-11-01', '2025-01-17'),
    ],
    'TANKERS (Float > 100M)': [
        ('RIOT', '2024-11-01', '2025-01-17'),
        ('MARA', '2024-11-01', '2025-01-17'),
        ('AMC', '2024-11-01', '2025-01-17'),
    ],
}

all_results = []

for category, symbols in universe.items():
    print("\n" + "="*80)
    print(f"TESTING: {category}")
    print("="*80)
    
    for symbol, start, end in symbols:
        try:
            result = run_orb_v7(symbol, start, end)
            result['category'] = category
            all_results.append(result)
        except Exception as e:
            print(f"✗ {symbol}: {e}")

# Analysis
if all_results:
    df = pd.DataFrame(all_results)
    
    print("\n" + "="*80)
    print("UNIVERSE ANALYSIS - V7 BARBELL STRATEGY")
    print("="*80)
    
    # By category
    for category in ['SPEEDBOATS (Float < 20M)', 'MID-CAP (50M-100M Float)', 'TANKERS (Float > 100M)']:
        cat_data = df[df['category'] == category]
        
        if len(cat_data) == 0:
            continue
        
        print(f"\n{category}:")
        print(f"  Symbols tested: {len(cat_data)}")
        print(f"  Total trades: {cat_data['total_trades'].sum()}")
        print(f"  Avg win rate: {cat_data['win_rate'].mean():.1f}%")
        print(f"  Avg P&L/trade: {cat_data['avg_pnl'].mean():+.3f}%")
        print(f"  Total P&L: {cat_data['total_pnl'].sum():+.2f}%")
        print(f"  Profitable symbols: {(cat_data['avg_pnl'] > 0).sum()}/{len(cat_data)}")
        
        # Individual symbols
        for _, row in cat_data.iterrows():
            status = "✅" if row['avg_pnl'] > 0 else "❌"
            print(f"    {status} {row['symbol']:6} | {row['total_trades']:3} trades | {row['win_rate']:5.1f}% win | {row['avg_pnl']:+.3f}% avg | {row['total_pnl']:+7.2f}% total")
    
    # Overall summary
    print("\n" + "="*80)
    print("OVERALL SUMMARY")
    print("="*80)
    print(f"Total symbols tested: {len(df)}")
    print(f"Profitable symbols: {(df['avg_pnl'] > 0).sum()}")
    print(f"Total trades: {df['total_trades'].sum()}")
    print(f"Overall avg P&L: {df['avg_pnl'].mean():+.3f}%")
    print(f"Overall total P&L: {df['total_pnl'].sum():+.2f}%")
    
    # Save results
    output_path = Path('research/new_strategy_builds/results/orb_full_universe_test.csv')
    df.to_csv(output_path, index=False)
    print(f"\n✅ Results saved to: {output_path}")
    
    # Gem's verdict
    print("\n" + "="*80)
    print("GEM'S VERDICT - WHICH UNIVERSE WINS?")
    print("="*80)
    
    for category in ['SPEEDBOATS (Float < 20M)', 'MID-CAP (50M-100M Float)', 'TANKERS (Float > 100M)']:
        cat_data = df[df['category'] == category]
        if len(cat_data) > 0:
            avg_pnl = cat_data['avg_pnl'].mean()
            profitable_pct = (cat_data['avg_pnl'] > 0).sum() / len(cat_data) * 100
            
            verdict = ""
            if avg_pnl > 0:
                verdict = "✅ PROFITABLE"
            elif avg_pnl > -0.05:
                verdict = "⚡ NEAR BREAKEVEN"
            else:
                verdict = "❌ LOSING"
            
            print(f"{category:30} | {avg_pnl:+.3f}% avg | {profitable_pct:.0f}% profitable | {verdict}")
    
    # Winner
    best_category = df.groupby('category')['avg_pnl'].mean().idxmax()
    best_avg = df.groupby('category')['avg_pnl'].mean().max()
    
    print(f"\n🏆 WINNER: {best_category}")
    print(f"   Average P&L: {best_avg:+.3f}% per trade")
    
    if best_avg > 0:
        print("\n🎉 WE FOUND A PROFITABLE UNIVERSE!")
    else:
        print("\n⚠️ No universe is profitable yet. Need further optimization.")
