"""
Batch Test ORB V10B Across Momentum Universe
---------------------------------------------
Test on: RIOT, MARA, AMC + momentum universe symbols
Period: Nov 2024
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
from research.new_strategy_builds.strategies.orb_v10b import run_orb_v10b

# Expanded universe: crypto + meme + momentum
symbols = [
    'RIOT', 'MARA', 'AMC',  # Known volatile symbols
    'JCSE', 'LCFY', 'CTMX', 'BIYA', 'IBRX', 'RIOX', 
    'CGTL', 'TNMG', 'VERO', 'NEOV', 'TYGO'  # Momentum universe
]

print("="*80)
print("ORB V10B - BATCH TEST (VOLUME 1.3x)")
print("="*80)
print(f"Testing {len(symbols)} symbols on Nov 2024")
print("="*80)

all_trades = []
results = []

for symbol in symbols:
    try:
        print(f"\nTesting {symbol}...", end=' ')
        trades = run_orb_v10b(symbol, '2024-11-01', '2024-11-30')
        all_trades.extend(trades)
        print(f"✓ {len(trades)} trades")
        
        if len(trades) > 0:
            trades_df = pd.DataFrame(trades)
            trades_df['pnl_net'] = trades_df['pnl_pct'] - 0.125
            
            results.append({
                'symbol': symbol,
                'trades': len(trades_df),
                'win_rate': (trades_df['pnl_net'] > 0).sum() / len(trades_df) * 100,
                'avg_pnl': trades_df['pnl_net'].mean(),
                'total_pnl': trades_df['pnl_net'].sum(),
                'avg_mae': trades_df['mae'].mean(),
                'avg_mfe': trades_df['mfe'].mean(),
            })
        else:
            results.append({
                'symbol': symbol,
                'trades': 0,
                'win_rate': 0,
                'avg_pnl': 0,
                'total_pnl': 0,
                'avg_mae': 0,
                'avg_mfe': 0,
            })
    except Exception as e:
        print(f"✗ Error: {e}")
        results.append({
            'symbol': symbol,
            'trades': 0,
            'win_rate': 0,
            'avg_pnl': 0,
            'total_pnl': 0,
            'avg_mae': 0,
            'avg_mfe': 0,
        })

print("\n" + "="*80)
print("RESULTS BY SYMBOL")
print("="*80)

results_df = pd.DataFrame(results)
print(results_df.to_string(index=False))

print("\n" + "="*80)
print("PORTFOLIO SUMMARY")
print("="*80)

if len(all_trades) > 0:
    all_trades_df = pd.DataFrame(all_trades)
    all_trades_df['pnl_net'] = all_trades_df['pnl_pct'] - 0.125
    
    winners = all_trades_df[all_trades_df['pnl_net'] > 0]
    losers = all_trades_df[all_trades_df['pnl_net'] <= 0]
    
    print(f"Total Trades:     {len(all_trades_df)}")
    print(f"Win Rate:         {(all_trades_df['pnl_net'] > 0).sum() / len(all_trades_df) * 100:.1f}%")
    print(f"Avg P&L:          {all_trades_df['pnl_net'].mean():+.3f}%")
    print(f"Total P&L:        {all_trades_df['pnl_net'].sum():+.2f}%")
    print(f"Avg Win:          {winners['pnl_net'].mean():+.3f}%" if len(winners) > 0 else "Avg Win:          N/A")
    print(f"Avg Loss:         {losers['pnl_net'].mean():+.3f}%" if len(losers) > 0 else "Avg Loss:         N/A")
    print(f"Avg MAE:          {all_trades_df['mae'].mean():.2f}R")
    print(f"Avg MFE:          {all_trades_df['mfe'].mean():.2f}R")
    print(f"Sharpe:           {all_trades_df['pnl_net'].mean() / all_trades_df['pnl_net'].std():.2f}" if all_trades_df['pnl_net'].std() > 0 else "Sharpe:           N/A")
    
    print("\n" + "="*80)
    print("EXIT TYPE BREAKDOWN")
    print("="*80)
    exit_breakdown = all_trades_df['type'].value_counts()
    for exit_type, count in exit_breakdown.items():
        pct = count / len(all_trades_df) * 100
        avg_pnl = all_trades_df[all_trades_df['type'] == exit_type]['pnl_net'].mean()
        print(f"{exit_type:<15}: {count:>4} ({pct:>5.1f}%)  Avg P&L: {avg_pnl:+.3f}%")
    
    print("\n" + "="*80)
    print("VERDICT")
    print("="*80)
    
    if len(all_trades_df) < 50:
        print("⚠️ WARNING: Too few trades (<50). Need more setups.")
        print("   Recommendation: Relax volume further (1.3x → 1.2x) or remove VWAP filter")
    elif all_trades_df['pnl_net'].mean() < 0:
        print("❌ FAILED: Negative expectancy")
        print(f"   Avg P&L: {all_trades_df['pnl_net'].mean():+.3f}%")
        print("   Recommendation: Review exit logic, especially FTA threshold")
    elif all_trades_df['pnl_net'].mean() > 0 and all_trades_df['pnl_net'].mean() < 0.05:
        print("⚠️ MARGINAL: Positive but weak expectancy")
        print(f"   Avg P&L: {all_trades_df['pnl_net'].mean():+.3f}%")
        print("   Recommendation: Tune exit parameters or test on different period")
    else:
        sharpe = all_trades_df['pnl_net'].mean() / all_trades_df['pnl_net'].std() if all_trades_df['pnl_net'].std() > 0 else 0
        print("✅ SUCCESS: Positive expectancy achieved!")
        print(f"   Total Trades: {len(all_trades_df)}")
        print(f"   Win Rate: {(all_trades_df['pnl_net'] > 0).sum() / len(all_trades_df) * 100:.1f}%")
        print(f"   Avg P&L: {all_trades_df['pnl_net'].mean():+.3f}%")
        print(f"   Sharpe: {sharpe:.2f}")
        print("\n   Next steps:")
        print("   1. Run walk-forward analysis (Dec 2024)")
        print("   2. Test on Jan 2025 for validation")
        print("   3. Generate deployment configs")
    
    # Save results
    results_df.to_csv('research/new_strategy_builds/results/orb_v10b_results.csv', index=False)
    all_trades_df.to_csv('research/new_strategy_builds/results/orb_v10b_trades.csv', index=False)
    print("\n✓ Results saved to research/new_strategy_builds/results/")
else:
    print("❌ FAILED: 0 trades across all symbols")
    print("   Filters are still too restrictive")
