"""Test V10 on broad sample"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import pandas as pd
from research.new_strategy_builds.strategies.orb_v10_surgical import run_orb_v10

# Load V7 results
v7_df = pd.read_csv('research/new_strategy_builds/results/ORB_V7_FULL_UNIVERSE.csv')

# Test on:
# 1. RIOT (control - must stay positive)
# 2. All paradox symbols (should flip)
# 3. Top 10 losers (see if we rescue any)

paradox_symbols = ['PLTR', 'NVDA', 'XLE', 'COIN', 'SOFI', 'MARA', 'MSTR', 'IREN', 'HOOD', 'OXY']
big_losers = v7_df.nsmallest(10, 'total_pnl')['symbol'].tolist()
test_symbols = ['RIOT'] + paradox_symbols + [s for s in big_losers if s not in paradox_symbols][:5]

print("="*80)
print("V10 SURGICAL FIX TEST (V7 + 0.7R target)")
print("="*80)
print(f"Testing {len(test_symbols)} symbols")
print(f"Change: Only 0.7R scale target (was 1.3R)")
print("="*80)

v10_results = []
for symbol in test_symbols:
    try:
        result = run_orb_v10(symbol, '2024-11-01', '2025-01-17')
        v10_results.append(result)
    except Exception as e:
        print(f"✗ {symbol}: {str(e)[:50]}")

# Compare
v10_df = pd.DataFrame(v10_results)
comparison = v10_df.merge(
    v7_df[['symbol', 'total_trades', 'win_rate', 'total_pnl']].rename(columns={
        'total_trades': 'v7_trades',
        'win_rate': 'v7_win',
        'total_pnl': 'v7_pnl'
    }),
    on='symbol',
    how='left'
)

comparison['delta'] = comparison['total_pnl'] - comparison['v7_pnl']
comparison['flipped'] = (comparison['v7_pnl'] < 0) & (comparison['total_pnl'] > 0)

print("\n" + "="*80)
print("V7 vs V10 RESULTS")
print("="*80)
print(comparison[['symbol', 'v7_trades', 'total_trades', 'v7_win', 'win_rate', 'v7_pnl', 'total_pnl', 'delta', 'flipped']].to_string(index=False))

print("\n" + "="*80)
print("SUMMARY")
print("="*80)

flipped = comparison[comparison['flipped'] == True]
improved = comparison[comparison['delta'] > 0]
profitable = comparison[comparison['total_pnl'] > 0]

print(f"Symbols tested: {len(comparison)}")
print(f"Flipped to profitable: {len(flipped)} / {len(comparison[comparison['v7_pnl'] < 0])}")
print(f"Improved vs V7: {len(improved)} ({len(improved)/len(comparison)*100:.1f}%)")
print(f"Now profitable: {len(profitable)} ({len(profitable)/len(comparison)*100:.1f}%)")
print(f"\nV7 total P&L: {comparison['v7_pnl'].sum():+.2f}%")
print(f"V10 total P&L: {comparison['total_pnl'].sum():+.2f}%")
print(f"Net improvement: {comparison['delta'].sum():+.2f}%")

# RIOT check
riot = comparison[comparison['symbol'] == 'RIOT'].iloc[0]
print(f"\n{'='*80}")
print("RIOT CHECK (Must not break the winner!)")
print("="*80)
print(f"V7: {riot['v7_pnl']:+.2f}% ({riot['v7_trades']:.0f} trades)")
print(f"V10: {riot['total_pnl']:+.2f}% ({riot['total_trades']:.0f} trades)")
if riot['delta'] > 0:
    print(f"✅ IMPROVED by {riot['delta']:+.2f}%")
elif riot['delta'] > -1:
    print(f"⚠️ Similar ({riot['delta']:+.2f}%)")
else:
    print(f"❌ WORSE by {riot['delta']:+.2f}%")

# Save
comparison.to_csv('research/new_strategy_builds/results/v10_surgical_test.csv', index=False)
print(f"\n✅ Saved to: v10_surgical_test.csv")

print("\n" + "="*80)
print("VERDICT")
print("="*80)

if len(flipped) >= 3 and riot['delta'] >= -0.5 and len(profitable) > len(v7_df[v7_df['total_pnl'] > 0]):
    print("✅ SUCCESS! V10 rescued symbols without breaking RIOT")
    print("   0.7R target is THE fix. Deploy or test on full universe.")
elif len(improved) > len(comparison) * 0.6:
    print("⚠️ PROMISING - Majority improved, needs full universe test")
else:
    print("❌ DID NOT WORK - Need different approach")
