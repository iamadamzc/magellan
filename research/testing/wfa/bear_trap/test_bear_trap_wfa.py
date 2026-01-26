"""
Bear Trap - Walk-Forward Analysis (WFA)
Test on rolling 1-year periods to validate robustness
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from research.new_strategy_builds.strategies.bear_trap import run_bear_trap

# Top 10 symbols for WFA
top_symbols = ['MULN', 'ONDS', 'NKLA', 'ACB', 'AMC', 'GOEV', 'SENS', 'BTCS', 'CLSK', 'WKHS']

# Rolling 1-year periods
periods = [
    ('2022', '2022-01-01', '2022-12-31'),
    ('2023', '2023-01-01', '2023-12-31'),
    ('2024', '2024-01-01', '2024-12-31'),
    ('2025', '2025-01-01', '2025-12-31'),
]

print("\n" + "="*80)
print("BEAR TRAP - WALK-FORWARD ANALYSIS")
print("Testing Top 10 symbols on rolling 1-year periods")
print("="*80)

all_results = []

for symbol in top_symbols:
    print(f"\n{'='*80}")
    print(f"{symbol}")
    print(f"{'='*80}")
    
    yearly_results = []
    
    for year, start, end in periods:
        try:
            result = run_bear_trap(symbol, start, end)
            
            if result['total_trades'] > 0:
                yearly_results.append({
                    'symbol': symbol,
                    'year': year,
                    'pnl_pct': result['total_pnl_pct'],
                    'pnl_dollars': result['total_pnl_dollars'],
                    'trades': result['total_trades'],
                    'win_rate': result['win_rate']
                })
                
                status = "✅" if result['total_pnl_pct'] > 0 else "❌"
                print(f"{year}: {status} {result['total_pnl_pct']:+.2f}% ({result['total_trades']} trades, {result['win_rate']:.1f}% win)")
            else:
                print(f"{year}: ⚠️  No trades")
        
        except Exception as e:
            print(f"{year}: ❌ Error - {str(e)[:50]}")
    
    if yearly_results:
        import pandas as pd
        df_yearly = pd.DataFrame(yearly_results)
        
        profitable_years = (df_yearly['pnl_pct'] > 0).sum()
        total_years = len(df_yearly)
        avg_annual = df_yearly['pnl_pct'].mean()
        
        all_results.extend(yearly_results)
        
        print(f"\n📊 {symbol} SUMMARY:")
        print(f"   Profitable Years: {profitable_years}/{total_years}")
        print(f"   Avg Annual Return: {avg_annual:+.2f}%")

# Overall WFA Summary
if all_results:
    import pandas as pd
    df = pd.DataFrame(all_results)
    
    print(f"\n{'='*80}")
    print("WALK-FORWARD ANALYSIS RESULTS")
    print(f"{'='*80}")
    
    # By Symbol
    print(f"\n{'Symbol':<8} {'2022':>10} {'2023':>10} {'2024':>10} {'2025':>10} {'Avg':>10} {'Prof Yrs':>10}")
    print("─"*80)
    
    for symbol in top_symbols:
        symbol_data = df[df['symbol'] == symbol]
        
        if len(symbol_data) > 0:
            year_pnls = {}
            for year in ['2022', '2023', '2024', '2025']:
                year_data = symbol_data[symbol_data['year'] == year]
                year_pnls[year] = year_data['pnl_pct'].iloc[0] if len(year_data) > 0 else 0
            
            avg_pnl = symbol_data['pnl_pct'].mean()
            prof_years = (symbol_data['pnl_pct'] > 0).sum()
            total_years = len(symbol_data)
            
            print(f"{symbol:<8} {year_pnls['2022']:>9.2f}% {year_pnls['2023']:>9.2f}% {year_pnls['2024']:>9.2f}% {year_pnls['2025']:>9.2f}% {avg_pnl:>9.2f}% {prof_years}/{total_years:>8}")
    
    # By Year
    print(f"\n{'='*80}")
    print("PERFORMANCE BY YEAR")
    print(f"{'='*80}")
    
    for year in ['2022', '2023', '2024', '2025']:
        year_data = df[df['year'] == year]
        
        if len(year_data) > 0:
            profitable = (year_data['pnl_pct'] > 0).sum()
            total = len(year_data)
            avg_pnl = year_data['pnl_pct'].mean()
            total_pnl = year_data['pnl_dollars'].sum()
            total_trades = year_data['trades'].sum()
            
            print(f"\n{year}:")
            print(f"   Profitable Symbols: {profitable}/{total} ({profitable/total*100:.1f}%)")
            print(f"   Avg Return: {avg_pnl:+.2f}%")
            print(f"   Total P&L: ${total_pnl:,.0f}")
            print(f"   Total Trades: {total_trades}")
    
    # Consistency Analysis
    print(f"\n{'='*80}")
    print("CONSISTENCY ANALYSIS")
    print(f"{'='*80}")
    
    consistency = df.groupby('symbol').agg({
        'pnl_pct': ['count', lambda x: (x > 0).sum(), 'mean', 'std']
    }).round(2)
    
    print(f"\nSymbols with 4/4 profitable years:")
    for symbol in top_symbols:
        symbol_data = df[df['symbol'] == symbol]
        prof_years = (symbol_data['pnl_pct'] > 0).sum()
        if prof_years == 4:
            avg = symbol_data['pnl_pct'].mean()
            print(f"   ✅ {symbol}: {avg:+.2f}% avg")
    
    print(f"\nSymbols with 3/4 profitable years:")
    for symbol in top_symbols:
        symbol_data = df[df['symbol'] == symbol]
        prof_years = (symbol_data['pnl_pct'] > 0).sum()
        if prof_years == 3:
            avg = symbol_data['pnl_pct'].mean()
            print(f"   ⚠️  {symbol}: {avg:+.2f}% avg")
    
    # Save WFA results
    df.to_csv('research/new_strategy_builds/results/BEAR_TRAP_WFA.csv', index=False)
    print(f"\n📁 WFA results saved to: BEAR_TRAP_WFA.csv")
    
    # Deployment Recommendation
    print(f"\n{'='*80}")
    print("DEPLOYMENT RECOMMENDATION")
    print(f"{'='*80}")
    
    # Symbols profitable in 3+ years
    deploy_symbols = []
    for symbol in top_symbols:
        symbol_data = df[df['symbol'] == symbol]
        prof_years = (symbol_data['pnl_pct'] > 0).sum()
        if prof_years >= 3:
            deploy_symbols.append({
                'symbol': symbol,
                'prof_years': prof_years,
                'avg_annual': symbol_data['pnl_pct'].mean()
            })
    
    if deploy_symbols:
        deploy_df = pd.DataFrame(deploy_symbols).sort_values('avg_annual', ascending=False)
        
        print(f"\n✅ APPROVED FOR DEPLOYMENT ({len(deploy_df)} symbols):")
        print(f"   Criteria: Profitable in ≥3 out of 4 years\n")
        
        for idx, row in deploy_df.iterrows():
            print(f"   {row['symbol']}: {row['avg_annual']:+.2f}% avg ({row['prof_years']}/4 years)")
        
        deploy_df.to_csv('research/new_strategy_builds/results/BEAR_TRAP_DEPLOY.csv', index=False)
        print(f"\n📁 Deployment list saved to: BEAR_TRAP_DEPLOY.csv")

print(f"\n{'='*80}\n")
