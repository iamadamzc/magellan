"""Test V8 on Paradox Symbols + RIOT"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
from research.new_strategy_builds.strategies.orb_v8_rescue import run_orb_v8

# Load V7 results for comparison
v7_df = pd.read_csv('research/new_strategy_builds/results/paradox_symbols.csv')

# Add RIOT as control
paradox_symbols = v7_df['symbol'].tolist() + ['RIOT']

print("="*80)
print("V8 TEST - PARADOX RESCUE + RIOT CONTROL")
print("="*80)
print(f"Testing {len(paradox_symbols)} symbols")
print("Changes: 0.7R target (was 1.3R) + No pullback entry (was pullback)")
print("="*80)

# Run V8
v8_results = []
for symbol in paradox_symbols:
    try:
        result = run_orb_v8(symbol, '2024-11-01', '2025-01-17')
        v8_results.append(result)
    except Exception as e:
        print(f"✗ {symbol}: {e}")

# Compare to V7
v8_df = pd.DataFrame(v8_results)

# Merge with V7 data
comparison = v8_df.merge(
    v7_df[['symbol', 'total_pnl']].rename(columns={'total_pnl': 'v7_pnl'}),
    on='symbol',
    how='left'
)

# RIOT's V7 performance
comparison.loc[comparison['symbol'] == 'RIOT', 'v7_pnl'] = 4.18

# Calculate improvement
comparison['improvement'] = comparison['total_pnl'] - comparison['v7_pnl']
comparison['flipped'] = (comparison['v7_pnl'] < 0) & (comparison['total_pnl'] > 0)

print("\n" + "="*80)
print("V7 vs V8 COMPARISON")
print("="*80)
print(comparison[['symbol', 'total_trades', 'win_rate', 'v7_pnl', 'total_pnl', 'improvement', 'flipped']].to_string(index=False))

# Summary stats
print("\n" + "="*80)
print("SUMMARY")
print("="*80)

flipped = comparison[comparison['flipped'] == True]
improved = comparison[comparison['improvement'] > 0]
hurt = comparison[comparison['improvement'] < 0]

print(f"Symbols tested: {len(comparison)}")
print(f"Flipped to profitable: {len(flipped)} ({len(flipped)/len(comparison)*100:.1f}%)")
print(f"Improved: {len(improved)} ({len(improved)/len(comparison)*100:.1f}%)")
print(f"Hurt: {len(hurt)} ({len(hurt)/len(comparison)*100:.1f}%)")
print(f"\nAvg improvement: {comparison['improvement'].mean():+.2f}%")
print(f"Total V7 P&L: {comparison['v7_pnl'].sum():+.2f}%")
print(f"Total V8 P&L: {comparison['total_pnl'].sum():+.2f}%")
print(f"Net gain: {(comparison['total_pnl'].sum() - comparison['v7_pnl'].sum()):+.2f}%")

# RIOT check
riot = comparison[comparison['symbol'] == 'RIOT'].iloc[0]
print(f"\n{'='*80}")
print("RIOT CHECK (Don't hurt the winner!)")
print("="*80)
print(f"V7: {riot['v7_pnl']:+.2f}%")
print(f"V8: {riot['total_pnl']:+.2f}%")
print(f"Change: {riot['improvement']:+.2f}% {'✅ IMPROVED' if riot['improvement'] > 0 else '❌ WORSE' if riot['improvement'] < -1 else '⚠️ SIMILAR'}")

# Top improvers
print(f"\n{'='*80}")
print("TOP 5 IMPROVEMENTS")
print("="*80)
top = comparison.nlargest(5, 'improvement')
print(top[['symbol', 'v7_pnl', 'total_pnl', 'improvement']].to_string(index=False))

# Save
comparison.to_csv('research/new_strategy_builds/results/v8_paradox_test.csv', index=False)
print(f"\n✅ Saved to: v8_paradox_test.csv")

# Verdict
print(f"\n{'='*80}")
print("VERDICT")
print("="*80)

if len(flipped) >= 5 and riot['improvement'] >= 0:
    print("✅ SUCCESS! V8 rescued the paradox AND didn't hurt RIOT")
    print("   Deploy V8 or continue tuning from here")
elif len(flipped) >= 3:
    print("⚠️ PARTIAL SUCCESS - Some symbols flipped, needs more work")
elif improvement.mean() > 0:
    print("⚠️ MARGINAL - Improved on average but didn't flip many")
else:
    print("❌ FAILED - Changes didn't help")
