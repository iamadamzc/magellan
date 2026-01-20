"""
Bear Trap Strategy - 50 Symbol Test
Test on small-cap universe (2024 data)
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from research.new_strategy_builds.strategies.bear_trap import run_bear_trap

# 50 Small-Cap Universe
symbols = {
    'Meme/Volatile': ['AMC', 'GME', 'BBBY', 'MULN', 'ONDS'],
    'Small-Cap Tech': ['SNDL', 'PLUG', 'RIOT', 'MARA', 'CLSK'],
    'Small-Cap Biotech': ['OCGN', 'GEVO', 'BNGO', 'SENS', 'PROG'],
    'Small-Cap Energy': ['TELL', 'FCEL', 'BKKT', 'WKHS', 'RIDE'],
    'Small-Cap Retail/Consumer': ['BBIG', 'CLOV', 'WISH', 'SOFI', 'HOOD'],
    'Small-Cap EV/Battery': ['NKLA', 'LCID', 'GOEV', 'ARVL', 'HYLN'],
    'Small-Cap Crypto-Related': ['BTBT', 'EBON', 'CAN', 'MOGO', 'BTCS'],
    'Small-Cap Shipping': ['ZIM', 'MATX', 'SBLK', 'GOGL', 'NMCI'],
    'Small-Cap Misc': ['SPCE', 'OPEN', 'SKLZ', 'DKNG', 'PENN', 'TLRY', 'CGC', 'ACB', 'HEXO', 'OGI'],
}

print("\n" + "="*80)
print("BEAR TRAP STRATEGY - 50 SYMBOL TEST")
print("Small-Cap Reversal Hunter (2024)")
print("="*80)

all_results = []
category_results = {}

for category, symbol_list in symbols.items():
    print(f"\n{'='*80}")
    print(f"{category}")
    print(f"{'='*80}")
    
    category_results[category] = []
    
    for symbol in symbol_list:
        try:
            result = run_bear_trap(symbol, '2024-01-01', '2024-12-31')
            
            if result['total_trades'] > 0:
                all_results.append(result)
                category_results[category].append(result)
        
        except Exception as e:
            print(f"❌ {symbol}: Error - {str(e)[:50]}")

# Overall Summary
if all_results:
    import pandas as pd
    df = pd.DataFrame(all_results)
    df_sorted = df.sort_values('total_pnl_pct', ascending=False)
    
    print(f"\n{'='*80}")
    print("TOP 20 PERFORMERS")
    print(f"{'='*80}")
    print(f"\n{'Rank':<6} {'Symbol':<8} {'P&L %':>10} {'P&L $':>12} {'Trades':>8} {'Win%':>8}")
    print("─"*80)
    
    for idx, row in df_sorted.head(20).iterrows():
        rank = df_sorted.index.get_loc(idx) + 1
        status = "✅" if row['total_pnl_pct'] > 0 else "❌"
        print(f"{rank:<6} {row['symbol']:<8} {row['total_pnl_pct']:>9.2f}% ${row['total_pnl_dollars']:>10,.0f} {row['total_trades']:>8} {row['win_rate']:>7.1f}%")
    
    # Winners
    winners = df[df['total_pnl_pct'] > 0]
    
    print(f"\n{'='*80}")
    print("SUMMARY STATISTICS")
    print(f"{'='*80}")
    print(f"Total Symbols Tested: {len(df)}")
    print(f"Profitable Symbols: {len(winners)} ({len(winners)/len(df)*100:.1f}%)")
    print(f"Total Trades: {df['total_trades'].sum()}")
    print(f"Avg Trades per Symbol: {df['total_trades'].mean():.1f}")
    print(f"Avg Win Rate: {df['win_rate'].mean():.1f}%")
    
    if len(winners) > 0:
        print(f"\nWINNERS:")
        print(f"  Total P&L: ${winners['total_pnl_dollars'].sum():,.0f}")
        print(f"  Avg P&L per Winner: ${winners['total_pnl_dollars'].mean():,.0f}")
        print(f"  Best Performer: {winners.iloc[0]['symbol']} ({winners.iloc[0]['total_pnl_pct']:+.2f}%)")
        
        # Save winners
        winners.to_csv('research/new_strategy_builds/results/BEAR_TRAP_WINNERS.csv', index=False)
        print(f"\n📁 Winners saved to: BEAR_TRAP_WINNERS.csv")
    
    # Category breakdown
    print(f"\n{'='*80}")
    print("CATEGORY PERFORMANCE")
    print(f"{'='*80}")
    
    for category, results in category_results.items():
        if results:
            cat_df = pd.DataFrame(results)
            cat_winners = cat_df[cat_df['total_pnl_pct'] > 0]
            total_pnl = cat_df['total_pnl_dollars'].sum()
            
            print(f"\n{category}:")
            print(f"  Tested: {len(cat_df)} | Profitable: {len(cat_winners)}")
            print(f"  Total P&L: ${total_pnl:,.0f}")
            if len(cat_winners) > 0:
                best = cat_df.loc[cat_df['total_pnl_pct'].idxmax()]
                print(f"  Best: {best['symbol']} ({best['total_pnl_pct']:+.2f}%)")

else:
    print(f"\n❌ No trades generated across all symbols")

print(f"\n{'='*80}\n")
