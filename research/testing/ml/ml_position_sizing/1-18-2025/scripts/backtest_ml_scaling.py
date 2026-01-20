"""
ML Position Sizing Backtest - Proof of Concept

Compares baseline (no ML) vs ML-enhanced position sizing using risk posture labels.

Focus on Chad's metrics:
- Worst trades (tail risk)
- Variance reduction
- Sharpe improvement
"""
import pandas as pd
import numpy as np
from pathlib import Path

# Load labeled trades
df = pd.read_csv('research/ml_position_sizing/data/labeled_regimes_v2.csv')
print(f"Loaded {len(df)} trades with ML labels\n")

# Position sizing parameters
INITIAL_CAPITAL = 100000
BASE_RISK_PER_TRADE = 0.02  # 2% risk per trade

# Scaling templates - CORRECTED
# NO_ADD gets LESS capital (low R expected)
# ADD_ALLOWED gets MORE capital (high R expected)
TEMPLATES = {
    'CONSERVATIVE': {
        'initial': 0.5,    # HALF position (low confidence)
        'adds': [],        # No adds
        'description': 'NO_ADD regime - low R expected, reduce exposure'
    },
    
    'NORMAL': {
        'initial': 0.8,    # 80% at entry
        'adds': [
            {'trigger': 0.5, 'size': 0.2},  # Add 20% at +0.5R
        ],
        'description': 'ADD_NEUTRAL regime - normal confidence'
    },
    
    'AGGRESSIVE': {
        'initial': 1.0,    # FULL position (high confidence)
        'adds': [
            {'trigger': 0.5, 'size': 0.3},  # Add 30% at +0.5R
            {'trigger': 1.0, 'size': 0.3},  # Add 30% at +1.0R
        ],
        'description': 'ADD_ALLOWED regime - high R expected, scale aggressively'
    }
}

def simulate_baseline(trades_df):
    """Baseline: No ML, same position size for all trades"""
    results = []
    equity = INITIAL_CAPITAL
    
    for idx, trade in trades_df.iterrows():
        # Fixed position size
        risk_amount = equity * BASE_RISK_PER_TRADE
        position_size = risk_amount  # Simplified (assume $1 risk per share)
        
        # Trade outcome
        pnl = position_size * trade['r_multiple']
        equity += pnl
        
        results.append({
            'trade_id': idx,
            'symbol': trade['symbol'],
            'r_multiple': trade['r_multiple'],
            'position_size': position_size,
            'pnl': pnl,
            'equity': equity,
            'template': 'baseline',
        })
    
    return pd.DataFrame(results)

def simulate_ml_enhanced(trades_df):
    """ML-Enhanced: Different templates based on risk posture"""
    results = []
    equity = INITIAL_CAPITAL
    
    for idx, trade in trades_df.iterrows():
        # Select template based on ML label
        regime = trade['regime_label_v2']
        
        if regime == 'NO_ADD':
            template = TEMPLATES['CONSERVATIVE']
        elif regime == 'ADD_NEUTRAL':
            template = TEMPLATES['NORMAL']
        else:  # ADD_ALLOWED
            template = TEMPLATES['AGGRESSIVE']
        
        # Calculate base risk
        risk_amount = equity * BASE_RISK_PER_TRADE
        
        # Simulate scaling
        # For simplicity, calculate expected R based on template and actual outcome
        r = trade['r_multiple']
        
        # Initial position
        initial_r = r * template['initial']
        
        # Add positions (only if R reached those levels)
        total_r = initial_r
        for add in template.get('adds', []):
            if r >= add['trigger']:  # Trade reached the add level
                # Add gets the remaining R from trigger point
                add_r = (r - add['trigger']) * add['size']
                total_r += add_r
        
        # Calculate P&L
        pnl = risk_amount * total_r
        equity += pnl
        
        results.append({
            'trade_id': idx,
            'symbol': trade['symbol'],
            'regime': regime,
            'template': template['description'],
            'r_multiple_actual': r,
            'r_multiple_realized': total_r,
            'position_size': risk_amount,
            'pnl': pnl,
            'equity': equity,
        })
    
    return pd.DataFrame(results)

# Run simulations
print("="*80)
print("RUNNING SIMULATIONS")
print("="*80)

baseline_results = simulate_baseline(df)
ml_results = simulate_ml_enhanced(df)

# Calculate performance metrics
def calculate_metrics(results_df, label):
    """Calculate performance and risk metrics"""
    
    total_pnl = results_df['pnl'].sum()
    total_return = (results_df['equity'].iloc[-1] - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100
    
    trade_returns = results_df['pnl'] / INITIAL_CAPITAL
    sharpe = (trade_returns.mean() / trade_returns.std()) * np.sqrt(252) if trade_returns.std() > 0 else 0
    
    # Risk metrics (Chad's focus)
    worst_10 = results_df.nsmallest(10, 'pnl')['pnl'].sum()
    worst_trade = results_df['pnl'].min()
    variance = results_df['pnl'].std()
    
    # Drawdown
    equity_curve = results_df['equity']
    running_max = equity_curve.expanding().max()
    drawdown = (equity_curve - running_max) / running_max * 100
    max_dd = drawdown.min()
    
    print(f"\n{label}:")
    print(f"  Total Return: {total_return:+.2f}%")
    print(f"  Total P&L: ${total_pnl:,.0f}")
    print(f"  Final Equity: ${results_df['equity'].iloc[-1]:,.0f}")
    print(f"  Sharpe Ratio: {sharpe:.2f}")
    print(f"  Max Drawdown: {max_dd:.2f}%")
    print(f"\n  Risk Metrics (Chad's Focus):")
    print(f"    Worst 10 trades: ${worst_10:,.0f}")
    print(f"    Worst single trade: ${worst_trade:,.0f}")
    print(f"    P&L Variance (std): ${variance:,.0f}")
    
    return {
        'label': label,
        'total_return': total_return,
        'sharpe': sharpe,
        'max_dd': max_dd,
        'worst_10': worst_10,
        'worst_trade': worst_trade,
        'variance': variance,
    }

print("\n" + "="*80)
print("PERFORMANCE COMPARISON")
print("="*80)

baseline_metrics = calculate_metrics(baseline_results, "BASELINE (No ML)")
ml_metrics = calculate_metrics(ml_results, "ML-ENHANCED (Risk Posture)")

# Direct comparison
print("\n" + "="*80)
print("IMPROVEMENT ANALYSIS")
print("="*80)

return_improvement = ml_metrics['total_return'] - baseline_metrics['total_return']
sharpe_improvement = ml_metrics['sharpe'] - baseline_metrics['sharpe']
sharpe_improvement_pct = (sharpe_improvement / baseline_metrics['sharpe'] * 100) if baseline_metrics['sharpe'] != 0 else 0

variance_reduction = baseline_metrics['variance'] - ml_metrics['variance']
variance_reduction_pct = (variance_reduction / baseline_metrics['variance'] * 100)

worst10_improvement = ml_metrics['worst_10'] - baseline_metrics['worst_10']

print(f"\nReturns:")
print(f"  Baseline: {baseline_metrics['total_return']:+.2f}%")
print(f"  ML-Enhanced: {ml_metrics['total_return']:+.2f}%")
print(f"  Improvement: {return_improvement:+.2f}% {'✅' if return_improvement > 0 else '❌'}")

print(f"\nSharpe Ratio:")
print(f"  Baseline: {baseline_metrics['sharpe']:.2f}")
print(f"  ML-Enhanced: {ml_metrics['sharpe']:.2f}")
print(f"  Improvement: {sharpe_improvement:+.2f} ({sharpe_improvement_pct:+.1f}%) {'✅' if sharpe_improvement > 0 else '❌'}")

print(f"\nRisk Metrics (Lower is better):")
print(f"  Variance:")
print(f"    Baseline: ${baseline_metrics['variance']:,.0f}")
print(f"    ML-Enhanced: ${ml_metrics['variance']:,.0f}")
print(f"    Reduction: ${variance_reduction:,.0f} ({variance_reduction_pct:+.1f}%) {'✅' if variance_reduction > 0 else '❌'}")

print(f"\n  Worst 10 Trades:")
print(f"    Baseline: ${baseline_metrics['worst_10']:,.0f}")
print(f"    ML-Enhanced: ${ml_metrics['worst_10']:,.0f}")
print(f"    Improvement: ${worst10_improvement:,.0f} {'✅' if worst10_improvement > 0 else '❌'}")

print(f"\n  Worst Single Trade:")
print(f"    Baseline: ${baseline_metrics['worst_trade']:,.0f}")
print(f"    ML-Enhanced: ${ml_metrics['worst_trade']:,.0f}")
print(f"    Improvement: ${ml_metrics['worst_trade'] - baseline_metrics['worst_trade']:,.0f} {'✅' if ml_metrics['worst_trade'] > baseline_metrics['worst_trade'] else '❌'}")

# Success criteria
print("\n" + "="*80)
print("SUCCESS CRITERIA (Chad's Framework)")
print("="*80)

success_count = 0
total_criteria = 4

print("\n1. Does ML improve Sharpe ratio?")
if sharpe_improvement > 0:
    print(f"   ✅ YES: +{sharpe_improvement:.2f} ({sharpe_improvement_pct:+.1f}%)")
    success_count += 1
else:
    print(f"   ❌ NO: {sharpe_improvement:.2f}")

print("\n2. Does ML reduce variance (tail risk)?")
if variance_reduction > 0:
    print(f"   ✅ YES: -{variance_reduction_pct:.1f}%")
    success_count += 1
else:
    print(f"   ❌ NO: +{-variance_reduction_pct:.1f}%")

print("\n3. Does ML improve worst 10 trades?")
if worst10_improvement > 0:
    print(f"   ✅ YES: ${worst10_improvement:,.0f} better")
    success_count += 1
else:
    print(f"   ❌ NO: ${worst10_improvement:,.0f}")

print("\n4. Does ML improve overall returns?")
if return_improvement > 0:
    print(f"   ✅ YES: +{return_improvement:.2f}%")
    success_count += 1
else:
    print(f"   ❌ NO: {return_improvement:.2f}%")

print(f"\n{'='*80}")
print(f"OVERALL SCORE: {success_count}/{total_criteria} criteria met")
print(f"{'='*80}")

if success_count >= 3:
    print("\n🎉 SUCCESS! ML position sizing adds value")
    print("   → Proceed to deployment")
elif success_count >= 2:
    print("\n⚠️  MIXED RESULTS: ML shows promise but needs refinement")
    print("   → Add Tier 2 features and retest")
else:
    print("\n❌ INSUFFICIENT: ML does not add value yet")
    print("   → Revisit feature engineering")

# Save results
baseline_results.to_csv('research/ml_position_sizing/results/baseline_backtest.csv', index=False)
ml_results.to_csv('research/ml_position_sizing/results/ml_enhanced_backtest.csv', index=False)

print(f"\n✓ Results saved to research/ml_position_sizing/results/")
print(f"  - baseline_backtest.csv")
print(f"  - ml_enhanced_backtest.csv")
