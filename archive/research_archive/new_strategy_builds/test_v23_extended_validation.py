"""
V23 EXTENDED VALIDATION - 4 Years (2022-2025)
Test the 3 winners on extended period to validate robustness
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from research.new_strategy_builds.strategies.orb_v23_all_day import run_orb_v23_all_day

winners = [
    ('NG', 'Natural Gas'),
    ('KC', 'Coffee'),
    ('SB', 'Sugar'),
]

print("\n" + "="*80)
print("V23 EXTENDED VALIDATION - 4 Years (Jan 2022 - Dec 2025)")
print("Testing on NG, KC, SB to validate robustness")
print("="*80)

results = []

for symbol, name in winners:
    print(f"\n{'='*80}")
    print(f"{symbol} ({name})")
    print(f"{'='*80}")
    
    # Test each year separately for analysis
    yearly_results = []
    
    for year in [2022, 2023, 2024, 2025]:
        start = f"{year}-01-01"
        end = f"{year}-12-31"
        
        print(f"\n{year}:")
        result = run_orb_v23_all_day(symbol, start, end)
        
        if result['total_trades'] > 0:
            yearly_results.append({
                'year': year,
                'pnl': result['total_pnl'],
                'trades': result['total_trades'],
                'win_rate': result['win_rate']
            })
    
    # Full period
    print(f"\nFULL PERIOD (2022-2025):")
    full_result = run_orb_v23_all_day(symbol, '2022-01-01', '2025-12-31')
    
    if len(yearly_results) > 0:
        import pandas as pd
        df_yearly = pd.DataFrame(yearly_results)
        
        profitable_years = (df_yearly['pnl'] > 0).sum()
        avg_annual = df_yearly['pnl'].mean()
        
        results.append({
            'symbol': symbol,
            'name': name,
            'total_pnl': full_result['total_pnl'],
            'total_trades': full_result['total_trades'],
            'win_rate': full_result['win_rate'],
            'profitable_years': profitable_years,
            'total_years': len(yearly_results),
            'avg_annual': avg_annual,
            'yearly_data': yearly_results
        })
        
        print(f"\n📊 YEARLY BREAKDOWN:")
        for yr in yearly_results:
            status = "✅" if yr['pnl'] > 0 else "❌"
            print(f"   {yr['year']}: {status} {yr['pnl']:+.2f}% ({yr['trades']} trades, {yr['win_rate']:.1f}% win)")
        
        print(f"\n📈 SUMMARY:")
        print(f"   Profitable Years: {profitable_years}/{len(yearly_results)}")
        print(f"   Avg Annual Return: {avg_annual:+.2f}%")
        print(f"   Total 4-Year Return: {full_result['total_pnl']:+.2f}%")

# Final Summary
if results:
    import pandas as pd
    df = pd.DataFrame(results)
    
    print(f"\n{'='*80}")
    print("FINAL 4-YEAR VALIDATION RESULTS")
    print(f"{'='*80}")
    print(f"\n{'Symbol':<8} {'Name':<15} {'Total P&L':>12} {'Trades':>8} {'Win%':>8} {'Prof Years':>12}")
    print("─"*80)
    
    for _, row in df.iterrows():
        status = "✅ DEPLOY" if row['total_pnl'] > 0 and row['profitable_years'] >= 3 else "⚠️  REVIEW"
        print(f"{row['symbol']:<8} {row['name']:<15} {row['total_pnl']:>11.2f}% {row['total_trades']:>8} {row['win_rate']:>7.1f}% {row['profitable_years']}/{row['total_years']:>10}")
    
    # Deployment criteria
    print(f"\n{'='*80}")
    print("DEPLOYMENT DECISION")
    print(f"{'='*80}")
    
    deployable = df[(df['total_pnl'] > 0) & (df['profitable_years'] >= 3)]
    
    if len(deployable) > 0:
        print(f"\n✅ APPROVED FOR DEPLOYMENT ({len(deployable)} symbols):")
        for _, sym in deployable.iterrows():
            print(f"\n   🚀 {sym['symbol']} ({sym['name']})")
            print(f"      Total 4-Year Return: {sym['total_pnl']:+.2f}%")
            print(f"      Avg Annual Return: {sym['avg_annual']:+.2f}%")
            print(f"      Profitable Years: {sym['profitable_years']}/4")
            print(f"      Total Trades: {sym['total_trades']}")
            print(f"      Win Rate: {sym['win_rate']:.1f}%")
        
        # Save
        deployable.to_csv('research/new_strategy_builds/results/ORB_V23_VALIDATED_4YEAR.csv', index=False)
        print(f"\n📁 Saved to: ORB_V23_VALIDATED_4YEAR.csv")
    else:
        print(f"\n❌ NO SYMBOLS MEET DEPLOYMENT CRITERIA")
        print(f"   (Need: Total P&L > 0 AND Profitable in 3+ years)")
    
    # Warning for marginal performers
    marginal = df[(df['total_pnl'] > 0) & (df['profitable_years'] < 3)]
    if len(marginal) > 0:
        print(f"\n⚠️  MARGINAL PERFORMERS ({len(marginal)} symbols):")
        for _, sym in marginal.iterrows():
            print(f"   {sym['symbol']}: Profitable overall but only {sym['profitable_years']}/4 years")

print(f"\n{'='*80}\n")
