"""
V22 vs V21 COMPARISON - Fix the Win Rate Paradox
Test on all commodities that had trades
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from research.new_strategy_builds.strategies.orb_v21_adaptive import run_orb_v21_adaptive
from research.new_strategy_builds.strategies.orb_v22_let_it_run import run_orb_v22_let_it_run

# Test on all that had trades in V21
commodities = [
    ('ES', 'S&P 500'),
    ('CL', 'Crude Oil'),
    ('NG', 'Natural Gas'),
    ('HG', 'Copper'),
    ('KC', 'Coffee'),
    ('SB', 'Sugar'),
    ('CC', 'Cocoa'),
]

print("\n" + "="*80)
print("V22 'LET IT RUN' vs V21 - Fixing the Win Rate Paradox")
print("="*80)

results = []

for symbol, name in commodities:
    print(f"\n{'='*80}")
    print(f"{symbol} ({name})")
    print(f"{'='*80}")
    
    print("\nV21 (Original):")
    v21 = run_orb_v21_adaptive(symbol, '2024-01-01', '2024-12-31')
    
    print("\nV22 (Let It Run):")
    v22 = run_orb_v22_let_it_run(symbol, '2024-01-01', '2024-12-31')
    
    if v21['total_trades'] > 0 or v22['total_trades'] > 0:
        improvement = v22['total_pnl'] - v21['total_pnl']
        
        results.append({
            'symbol': symbol,
            'name': name,
            'v21_pnl': v21['total_pnl'],
            'v21_trades': v21['total_trades'],
            'v21_win_rate': v21['win_rate'],
            'v22_pnl': v22['total_pnl'],
            'v22_trades': v22['total_trades'],
            'v22_win_rate': v22['win_rate'],
            'v22_avg_winner': v22.get('avg_winner', 0),
            'v22_avg_loser': v22.get('avg_loser', 0),
            'improvement': improvement
        })
        
        print(f"\n📊 COMPARISON:")
        print(f"V21: {v21['total_pnl']:+.2f}% ({v21['total_trades']} trades, {v21['win_rate']:.1f}% win)")
        print(f"V22: {v22['total_pnl']:+.2f}% ({v22['total_trades']} trades, {v22['win_rate']:.1f}% win)")
        print(f"Improvement: {improvement:+.2f}%")

# Summary
if results:
    import pandas as pd
    df = pd.DataFrame(results)
    df_sorted = df.sort_values('v22_pnl', ascending=False)
    
    print(f"\n{'='*80}")
    print("FINAL RESULTS - V22")
    print(f"{'='*80}")
    print(f"\n{'Symbol':<8} {'Name':<15} {'V21 P&L':>10} {'V22 P&L':>10} {'Δ':>8} {'V22 Wins':>10} {'V22 WR%':>8}")
    print("─"*80)
    
    for _, row in df_sorted.iterrows():
        delta_symbol = "📈" if row['improvement'] > 0 else "📉"
        status = "✅" if row['v22_pnl'] > 0 else "❌"
        print(f"{row['symbol']:<8} {row['name']:<15} {row['v21_pnl']:>9.2f}% {row['v22_pnl']:>9.2f}% {delta_symbol}{abs(row['improvement']):>6.2f}% {row['v22_trades']:>10} {row['v22_win_rate']:>7.1f}%")
    
    winners = df[df['v22_pnl'] > 0]
    
    if len(winners) > 0:
        print(f"\n🎉 V22 WINNERS: {len(winners)} commodities")
        for _, w in winners.iterrows():
            print(f"   ✅ {w['symbol']}: {w['v22_pnl']:+.2f}% (Avg Win: {w['v22_avg_winner']:+.2f}%, Avg Loss: {w['v22_avg_loser']:+.2f}%)")
        
        winners.to_csv('research/new_strategy_builds/results/ORB_V22_WINNERS.csv', index=False)
        print(f"\n📁 Saved to: ORB_V22_WINNERS.csv")
    else:
        print(f"\n❌ No profitable commodities with V22")
    
    # Check improvement
    improved = df[df['improvement'] > 0]
    print(f"\n📈 V22 improved {len(improved)}/{len(df)} commodities")

print(f"\n{'='*80}\n")
