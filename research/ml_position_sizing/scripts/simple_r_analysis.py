"""
ML Position Sizing - Simple R-Multiple Comparison

Focus on average R-multiples, not compounded dollars.
This shows the true impact without inflation from comp

ounding.
"""
import pandas as pd
import numpy as np

# Load labeled trades
df = pd.read_csv('research/ml_position_sizing/data/labeled_regimes_v2.csv')
print(f"==="*30)
print("ML POSITION SIZING - SIMPLE ANALYSIS")
print(f"==="*30)
print(f"\nTotal trades: {len(df)}")

# Calculate realized R for each regime with different templates
def calculate_realized_r(row, template):
    """Calculate realized R for a trade given a template"""
    r_actual = row['r_multiple']
    
    # Initial position
    r_realized = r_actual * template['initial']
    
    # Add positions
    for add in template.get('adds', []):
        if r_actual >= add['trigger']:
            # Remaining R from trigger point
            r_from_add = (r_actual - add['trigger']) * add['size']
            r_realized += r_from_add
    
    return r_realized

# Templates (corrected)
TEMPLATES = {
    'NO_ADD': {
        'initial': 0.5,
        'adds': [],
    },
    'ADD_NEUTRAL': {
        'initial': 0.8,
        'adds': [{'trigger': 0.5, 'size': 0.2}],
    },
    'ADD_ALLOWED': {
        'initial': 1.0,
        'adds': [
            {'trigger': 0.5, 'size': 0.3},
            {'trigger': 1.0, 'size': 0.3},
        ],
    }
}

# Calculate baseline (all trades same)
baseline_template = {'initial': 1.0, 'adds': []}
df['r_baseline'] = df.apply(lambda row: calculate_realized_r(row, baseline_template), axis=1)

# Calculate ML-enhanced (different templates per regime)
def get_ml_realized_r(row):
    regime = row['regime_label_v2']
    if regime == 'NO_ADD':
        template = TEMPLATES['NO_ADD']
    elif regime == 'ADD_NEUTRAL':
        template = TEMPLATES['ADD_NEUTRAL']
    else:  # ADD_ALLOWED
        template = TEMPLATES['ADD_ALLOWED']
    return calculate_realized_r(row, template)

df['r_ml_enhanced'] = df.apply(get_ml_realized_r, axis=1)

# Compare
print(f"\n{'='*80}")
print("OVERALL PERFORMANCE")
print(f"{'='*80}")

baseline_avg = df['r_baseline'].mean()
ml_avg = df['r_ml_enhanced'].mean()

baseline_sharpe = (df['r_baseline'].mean() / df['r_baseline'].std()) * np.sqrt(252/len(df)) if df['r_baseline'].std() > 0 else 0
ml_sharpe = (df['r_ml_enhanced'].mean() / df['r_ml_enhanced'].std()) * np.sqrt(252/len(df)) if df['r_ml_enhanced'].std() > 0 else 0

print(f"\nAverage R-Multiple:")
print(f"  Baseline:     {baseline_avg:+.3f}R")
print(f"  ML-Enhanced:  {ml_avg:+.3f}R")
print(f"  Improvement:  {ml_avg - baseline_avg:+.3f}R ({(ml_avg/baseline_avg-1)*100:+.1f}%)")

print(f"\nSharpe Ratio (annualized):")
print(f"  Baseline:     {baseline_sharpe:.2f}")
print(f"  ML-Enhanced:  {ml_sharpe:.2f}")
print(f"  Improvement:  {ml_sharpe - baseline_sharpe:+.2f}")

print(f"\nStandard Deviation:")
print(f"  Baseline:     {df['r_baseline'].std():.3f}R")
print(f"  ML-Enhanced:  {df['r_ml_enhanced'].std():.3f}R")
print(f"  Change:       {(df['r_ml_enhanced'].std() - df['r_baseline'].std()):.3f}R")

# Worst trades
print(f"\n{'='*80}")
print("TAIL RISK ANALYSIS")
print(f"{'='*80}")

baseline_worst_10 = df.nsmallest(10, 'r_baseline')['r_baseline'].mean()
ml_worst_10 = df.nsmallest(10, 'r_ml_enhanced')['r_ml_enhanced'].mean()

baseline_worst = df['r_baseline'].min()
ml_worst = df['r_ml_enhanced'].min()

print(f"\nWorst 10 trades average:")
print(f"  Baseline:     {baseline_worst_10:+.2f}R")
print(f"  ML-Enhanced:  {ml_worst_10:+.2f}R")
print(f"  Improvement:  {ml_worst_10 - baseline_worst_10:+.2f}R")

print(f"\nWorst single trade:")
print(f"  Baseline:     {baseline_worst:+.2f}R")
print(f"  ML-Enhanced:  {ml_worst:+.2f}R")
print(f"  Improvement:  {ml_worst - baseline_worst:+.2f}R")

# By regime
print(f"\n{'='*80}")
print("PERFORMANCE BY REGIME")
print(f"{'='*80}")

for regime in ['ADD_ALLOWED', 'ADD_NEUTRAL', 'NO_ADD']:
    subset = df[df['regime_label_v2'] == regime]
    if len(subset) > 0:
        baseline_avg_regime = subset['r_baseline'].mean()
        ml_avg_regime = subset['r_ml_enhanced'].mean()
        
        print(f"\n{regime} ({len(subset)} trades):")
        print(f"  Baseline avg R:     {baseline_avg_regime:+.3f}")
        print(f"  ML-Enhanced avg R:  {ml_avg_regime:+.3f}")
        print(f"  Template effect:    {ml_avg_regime - baseline_avg_regime:+.3f}R")

# Success criteria
print(f"\n{'='*80}")
print("SUCCESS CRITERIA")
print(f"{'='*80}")

success_count = 0

print(f"\n1. Does ML improve average R?")
if ml_avg > baseline_avg:
    print(f"   ✅ YES: +{(ml_avg - baseline_avg):.3f}R")
    success_count += 1
else:
    print(f"   ❌ NO: {(ml_avg - baseline_avg):.3f}R")

print(f"\n2. Does ML improve or maintain Sharpe?")
if ml_sharpe >= baseline_sharpe * 0.95:  # Within 5%
    print(f"   ✅ YES: {ml_sharpe:.2f} vs {baseline_sharpe:.2f}")
    success_count += 1
else:
    print(f"   ❌ NO: {ml_sharpe:.2f} vs {baseline_sharpe:.2f}")

print(f"\n3. Does ML improve worst 10 trades?")
if ml_worst_10 > baseline_worst_10:
    print(f"   ✅ YES: {ml_worst_10:+.2f}R vs {baseline_worst_10:+.2f}R")
    success_count += 1
else:
    print(f"   ❌ NO: {ml_worst_10:+.2f}R vs {baseline_worst_10:+.2f}R")

print(f"\n4. Does ML reduce variance?")
if df['r_ml_enhanced'].std() < df['r_baseline'].std():
    print(f"   ✅ YES: {df['r_ml_enhanced'].std():.3f}R vs {df['r_baseline'].std():.3f}R")
    success_count += 1
else:
    print(f"   ❌ NO: {df['r_ml_enhanced'].std():.3f}R vs {df['r_baseline'].std():.3f}R")

print(f"\n{'='*80}")
print(f"FINAL SCORE: {success_count}/4 criteria met")
print(f"{'='*80}")

if success_count >= 3:
    print("\n🎉 SUCCESS! ML position sizing adds clear value")
elif success_count >= 2:
    print("\n⚠️  PROMISING: ML shows benefit, minor refinement needed")
else:
    print("\n❌ NEEDS WORK: Revise approach")

# Save summary
summary = pd.DataFrame({
    'metric': ['Avg R', 'Sharpe', 'Std Dev', 'Worst 10', 'Worst Single'],
    'baseline': [baseline_avg, baseline_sharpe, df['r_baseline'].std(), baseline_worst_10, baseline_worst],
    'ml_enhanced': [ml_avg, ml_sharpe, df['r_ml_enhanced'].std(), ml_worst_10, ml_worst],
    'improvement': [
        ml_avg - baseline_avg,
        ml_sharpe - baseline_sharpe,
        df['r_ml_enhanced'].std() - df['r_baseline'].std(),
        ml_worst_10 - baseline_worst_10,
        ml_worst - baseline_worst
    ]
})

summary.to_csv('research/ml_position_sizing/results/summary_comparison.csv', index=False)
print(f"\n✓ Summary saved to research/ml_position_sizing/results/summary_comparison.csv")
