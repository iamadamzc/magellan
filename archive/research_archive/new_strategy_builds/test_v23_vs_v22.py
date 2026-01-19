"""
V23 ALL DAY vs V22 FIRST HOUR - Does opening the window help?
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from research.new_strategy_builds.strategies.orb_v22_let_it_run import run_orb_v22_let_it_run
from research.new_strategy_builds.strategies.orb_v23_all_day import run_orb_v23_all_day

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
print("V23 ALL DAY vs V22 FIRST HOUR ONLY")
print("Testing if removing entry window increases profitability")
print("="*80)

results = []

for symbol, name in commodities:
    print(f"\n{'='*80}")
    print(f"{symbol} ({name})")
    print(f"{'='*80}")
    
    print("\nV22 (First Hour Only - 10-60 min):")
    v22 = run_orb_v22_let_it_run(symbol, '2024-01-01', '2024-12-31')
    
    print("\nV23 (All Day):")
    v23 = run_orb_v23_all_day(symbol, '2024-01-01', '2024-12-31')
    
    if v22['total_trades'] > 0 or v23['total_trades'] > 0:
        improvement = v23['total_pnl'] - v22['total_pnl']
        trade_increase = v23['total_trades'] - v22['total_trades']
        
        results.append({
            'symbol': symbol,
            'name': name,
            'v22_pnl': v22['total_pnl'],
            'v22_trades': v22['total_trades'],
            'v23_pnl': v23['total_pnl'],
            'v23_trades': v23['total_trades'],
            'v23_win_rate': v23['win_rate'],
            'v23_avg_winner': v23.get('avg_winner', 0),
            'v23_avg_loser': v23.get('avg_loser', 0),
            'improvement': improvement,
            'trade_increase': trade_increase
        })
        
        print(f"\n📊 COMPARISON:")
        print(f"V22: {v22['total_pnl']:+.2f}% ({v22['total_trades']} trades)")
        print(f"V23: {v23['total_pnl']:+.2f}% ({v23['total_trades']} trades)")
        print(f"Δ P&L: {improvement:+.2f}% | Δ Trades: {trade_increase:+d}")

# Summary
if results:
    import pandas as pd
    df = pd.DataFrame(results)
    df_sorted = df.sort_values('v23_pnl', ascending=False)
    
    print(f"\n{'='*80}")
    print("FINAL RESULTS - V23 ALL DAY")
    print(f"{'='*80}")
    print(f"\n{'Symbol':<8} {'Name':<15} {'V22':>10} {'V23':>10} {'Δ P&L':>8} {'Trades':>8} {'Status':<10}")
    print("─"*80)
    
    for _, row in df_sorted.iterrows():
        delta = "📈" if row['improvement'] > 0 else "📉" if row['improvement'] < 0 else "="
        status = "✅ PROFIT" if row['v23_pnl'] > 0 else "❌ LOSS"
        print(f"{row['symbol']:<8} {row['name']:<15} {row['v22_pnl']:>9.2f}% {row['v23_pnl']:>9.2f}% {delta}{abs(row['improvement']):>6.2f}% {row['v23_trades']:>8} {status:<10}")
    
    winners = df[df['v23_pnl'] > 0]
    improved = df[df['improvement'] > 0]
    
    if len(winners) > 0:
        print(f"\n🎉 V23 WINNERS: {len(winners)} commodities")
        for _, w in winners.iterrows():
            print(f"   ✅ {w['symbol']}: {w['v23_pnl']:+.2f}% ({w['v23_trades']} trades, {w['v23_win_rate']:.1f}% win)")
        
        winners.to_csv('research/new_strategy_builds/results/ORB_V23_WINNERS.csv', index=False)
        print(f"\n📁 Saved to: ORB_V23_WINNERS.csv")
    
    print(f"\n📊 ANALYSIS:")
    print(f"   V23 improved: {len(improved)}/{len(df)} commodities")
    print(f"   Avg trade increase: {df['trade_increase'].mean():.1f} trades per symbol")
    
    if len(winners) > len(df[df['v22_pnl'] > 0]):
        print(f"   ✅ Opening window HELPED - more profitable symbols!")
    elif len(winners) < len(df[df['v22_pnl'] > 0]):
        print(f"   ❌ Opening window HURT - fewer profitable symbols")
    else:
        print(f"   = No change in number of profitable symbols")

print(f"\n{'='*80}\n")
