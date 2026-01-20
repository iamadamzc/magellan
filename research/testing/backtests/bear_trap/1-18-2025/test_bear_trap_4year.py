"""
Bear Trap - 4-Year Validation (2022-2025)
Test the 31 profitable symbols from 2024 on extended period
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from research.new_strategy_builds.strategies.bear_trap import run_bear_trap

# Top 31 profitable symbols from 2024 test
winners = [
    'MULN', 'CLSK', 'WKHS', 'AMC', 'GOEV', 'GME', 'ONDS', 'OCGN', 'FCEL', 'SPCE',
    'ACB', 'BTBT', 'SENS', 'BTCS', 'BNGO', 'HOOD', 'NKLA', 'CAN', 'SNDL', 'MARA',
    'ZIM', 'ARVL', 'GEVO', 'OGI', 'TLRY', 'RIOT', 'SOFI', 'CGC', 'PLUG', 'EBON', 'MOGO'
]

print("\n" + "="*80)
print("BEAR TRAP - 4-YEAR VALIDATION (2022-2025)")
print(f"Testing {len(winners)} profitable symbols from 2024")
print("="*80)

results = []

for symbol in winners:
    print(f"\n{symbol}:")
    print("-"*40)
    
    try:
        result = run_bear_trap(symbol, '2022-01-01', '2025-12-31')
        
        if result['total_trades'] > 0:
            results.append(result)
            status = "✅" if result['total_pnl_pct'] > 0 else "❌"
            print(f"{status} {result['total_pnl_pct']:+.2f}% (${result['total_pnl_dollars']:+,.0f}) - {result['total_trades']} trades")
        else:
            print("⚠️  No trades")
    
    except Exception as e:
        print(f"❌ Error: {str(e)[:60]}")

# Summary
if results:
    import pandas as pd
    df = pd.DataFrame(results)
    df_sorted = df.sort_values('total_pnl_pct', ascending=False)
    
    print(f"\n{'='*80}")
    print("4-YEAR VALIDATION RESULTS")
    print(f"{'='*80}")
    print(f"\n{'Rank':<6} {'Symbol':<8} {'4Y P&L %':>12} {'4Y P&L $':>14} {'Trades':>8} {'Win%':>8}")
    print("─"*80)
    
    for idx, row in df_sorted.head(20).iterrows():
        rank = df_sorted.index.get_loc(idx) + 1
        status = "✅" if row['total_pnl_pct'] > 0 else "❌"
        print(f"{rank:<6} {row['symbol']:<8} {row['total_pnl_pct']:>11.2f}% ${row['total_pnl_dollars']:>12,.0f} {row['total_trades']:>8} {row['win_rate']:>7.1f}%")
    
    winners_4y = df[df['total_pnl_pct'] > 0]
    
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Symbols Tested: {len(df)}")
    print(f"Profitable (4Y): {len(winners_4y)} ({len(winners_4y)/len(df)*100:.1f}%)")
    print(f"Total Trades: {df['total_trades'].sum():,}")
    print(f"Avg Win Rate: {df['win_rate'].mean():.1f}%")
    
    if len(winners_4y) > 0:
        print(f"\n✅ VALIDATED WINNERS:")
        print(f"   Total 4Y P&L: ${winners_4y['total_pnl_dollars'].sum():,.0f}")
        print(f"   Avg 4Y P&L: ${winners_4y['total_pnl_dollars'].mean():,.0f}")
        print(f"   Best: {winners_4y.iloc[0]['symbol']} ({winners_4y.iloc[0]['total_pnl_pct']:+.2f}%)")
        
        # Save
        winners_4y.to_csv('research/new_strategy_builds/results/BEAR_TRAP_VALIDATED_4YEAR.csv', index=False)
        print(f"\n📁 Saved to: BEAR_TRAP_VALIDATED_4YEAR.csv")
        
        # Deployment recommendation
        top_10 = winners_4y.head(10)
        print(f"\n🚀 TOP 10 FOR DEPLOYMENT:")
        for idx, row in top_10.iterrows():
            rank = winners_4y.index.get_loc(idx) + 1
            print(f"   {rank}. {row['symbol']}: {row['total_pnl_pct']:+.2f}% (${row['total_pnl_dollars']:+,.0f})")
    else:
        print(f"\n❌ No symbols profitable over 4 years")

print(f"\n{'='*80}\n")
