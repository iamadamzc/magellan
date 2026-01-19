"""
Fix Data Errors and Retest Missing Symbols
============================================
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
from research.new_strategy_builds.strategies.orb_v7 import run_orb_v7
from research.new_strategy_builds.strategies.orb_v7_futures import run_orb_v7_futures

# Symbols that had data errors
EQUITIES_MISSING = ['BITF', 'JCSE', 'LCFY', 'CTMX', 'BIYA', 'TYGO', 'VERO']

FUTURES_MISSING = [
    # Indices
    'NQ', 'RTY', 'YM',
    # Metals
    'GC', 'SI',
    # Energy
    'RB', 'HO',
    # Ags
    'ZC', 'ZW', 'ZL',
    # Softs
    'CT',
    # Rates
    'ZN', 'ZB', 'ZF', 'ZT', 'ZQ',
    # FX
    '6E', '6J', '6B', '6C', '6A', '6S'
]

print("="*80)
print("RETESTING SYMBOLS WITH DATA ERRORS")
print("="*80)

# Try equities first
print(f"\nTesting {len(EQUITIES_MISSING)} missing equities...")
equity_results = []
for symbol in EQUITIES_MISSING:
    try:
        result = run_orb_v7(symbol, '2024-11-01', '2025-01-17')
        if result['total_trades'] > 0:
            result['asset_class'] = 'MISSING EQUITIES'
            equity_results.append(result)
    except Exception as e:
        print(f"✗ {symbol}: {str(e)[:100]}")

# Try futures
print(f"\nTesting {len(FUTURES_MISSING)} missing futures...")
futures_results = []
for symbol in FUTURES_MISSING:
    try:
        result = run_orb_v7_futures(symbol, '2024-11-01', '2025-01-17', '1hour')
        if result['total_trades'] > 0:
            result['asset_class'] = 'MISSING FUTURES'
            futures_results.append(result)
    except Exception as e:
        print(f"✗ {symbol}: {str(e)[:100]}")

# Combine results
all_results = equity_results + futures_results

if all_results:
    df = pd.DataFrame(all_results)
    
    print("\n" + "="*80)
    print("RECOVERED RESULTS")  
    print("="*80)
    print(df[['symbol', 'asset_class', 'total_trades', 'win_rate', 'avg_pnl', 'total_pnl']].to_string(index=False))
    
    # Find winners
    winners = df[df['total_pnl'] > 0].sort_values('total_pnl', ascending=False)
    if len(winners) > 0:
        print("\n" + "="*80)
        print("🏆 NEW WINNERS FROM RECOVERED DATA")
        print("="*80)
        print(winners[['symbol', 'asset_class', 'total_trades', 'win_rate', 'total_pnl']].to_string(index=False))
    
    # Save
    df.to_csv('research/new_strategy_builds/results/ORB_V7_RECOVERED.csv', index=False)
    print(f"\n✅ Saved to: ORB_V7_RECOVERED.csv")
else:
    print("\n⚠️ No symbols recovered successfully")

print("\n" + "="*80)
print("COMPLETE")
print("="*80)
