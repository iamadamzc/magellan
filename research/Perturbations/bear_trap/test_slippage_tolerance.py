"""
CRITICAL TEST 5.1: Bear Trap - Slippage Tolerance

Tests whether Bear Trap edge survives realistic small-cap execution costs.
Small-cap stocks have wide spreads; assumed 0.125% may be too optimistic.

CRITICAL PASS CRITERIA:
- ≥7/9 symbols profitable at 0.5% slippage
- ≥5/9 symbols profitable at 1.0% slippage
- DEPLOYMENT BLOCKED if <5 symbols pass at 1.0%

Test Matrix: 9 symbols × 5 slippage levels = 45 runs
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

# Note: This is a SIMPLIFIED slippage overlay test
# Real implementation would require running full Bear Trap backtest with adjusted friction

# Validated symbols and their 4-year results (from deployment guide)
VALIDATED_SYMBOLS = {
    "MULN": {"4y_return": 54.24, "trades": 1172, "tier": "Tier 1"},
    "ONDS": {"4y_return": 40.31, "trades": 129, "tier": "Tier 1"},
    "NKLA": {"4y_return": 29.99, "trades": 188, "tier": "Tier 2"},
    "ACB": {"4y_return": 26.63, "trades": 83, "tier": "Tier 1"},
    "AMC": {"4y_return": 25.75, "trades": 136, "tier": "Tier 2"},
    "GOEV": {"4y_return": 24.99, "trades": 190, "tier": "Tier 1"},
    "SENS": {"4y_return": 23.66, "trades": 34, "tier": "Tier 2"},
    "BTCS": {"4y_return": 22.25, "trades": 70, "tier": "Tier 1"},
    "WKHS": {"4y_return": 18.55, "trades": 129, "tier": "Tier 2"},
}

SLIPPAGE_LEVELS = [0.125, 0.25, 0.50, 1.00, 2.00]  # % per round-trip
BASELINE_FRICTION = 0.125  # % per trade (assumed in validation)

def calculate_slippage_adjusted_return(baseline_return, baseline_friction, trades, new_friction):
    """
    Estimate return with adjusted friction.
    
    Simplified model:
    - Each trade costs friction
    - Total friction = trades × friction_pct
    - Adjusted return = baseline_return - (additional_friction × trades)
    """
    baseline_friction_cost = trades * (baseline_friction / 100)
    new_friction_cost = trades * (new_friction / 100)
    additional_friction = new_friction_cost - baseline_friction_cost
    
    adjusted_return = baseline_return - additional_friction
    
    return adjusted_return

def main():
    print("="*80)
    print("CRITICAL TEST 5.1: BEAR TRAP SLIPPAGE TOLERANCE")
    print("="*80)
    print(f"\nTesting {len(VALIDATED_SYMBOLS)} symbols at {len(SLIPPAGE_LEVELS)} slippage levels")
    print(f"Total test runs: {len(VALIDATED_SYMBOLS) * len(SLIPPAGE_LEVELS)}\n")
    
    print("CRITICAL PASS CRITERIA:")
    print("  • ≥7/9 symbols profitable at 0.5% slippage")
    print("  • ≥5/9 symbols profitable at 1.0% slippage")
    print("  • DEPLOYMENT BLOCKED if fail\n")
    print("="*80)
    
    all_results = []
    
    for symbol, data in VALIDATED_SYMBOLS.items():
        print(f"\n{symbol} ({data['tier']}) - Baseline: +{data['4y_return']:.2f}% over {data['trades']} trades")
        print("-" * 60)
        
        for slippage_pct in SLIPPAGE_LEVELS:
            adjusted_return = calculate_slippage_adjusted_return(
                baseline_return=data['4y_return'],
                baseline_friction=BASELINE_FRICTION,
                trades=data['trades'],
                new_friction=slippage_pct
            )
            
            profitable = adjusted_return > 0
            status_icon = "✅" if profitable else "❌"
            degradation_pct = ((data['4y_return'] - adjusted_return) / data['4y_return'] * 100) if data['4y_return'] > 0 else 0
            
            print(f"  {slippage_pct:5.3f}% slippage: {status_icon} Return: {adjusted_return:+7.2f}% "
                  f"(degradation: {degradation_pct:.1f}%)")
            
            all_results.append({
                'Symbol': symbol,
                'Tier': data['tier'],
                'Baseline_Return': data['4y_return'],
                'Trades': data['trades'],
                'Slippage_Pct': slippage_pct,
                'Adjusted_Return': adjusted_return,
                'Degradation_Pct': degradation_pct,
                'Profitable': profitable
            })
    
    # Save results
    df = pd.DataFrame(all_results)
    output_dir = Path('research/Perturbations/reports/test_results')
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / 'critical_test_5_1_bear_trap_slippage.csv'
    df.to_csv(output_path, index=False)
    
    # Analysis
    print("\n" + "="*80)
    print("CRITICAL TEST RESULTS")
    print("="*80)
    
    for slippage_pct in SLIPPAGE_LEVELS:
        slippage_results = df[df['Slippage_Pct'] == slippage_pct]
        profitable_count = slippage_results['Profitable'].sum()
        avg_return = slippage_results['Adjusted_Return'].mean()
        
        print(f"\n{slippage_pct:.3f}% Slippage:")
        print(f"  Profitable: {profitable_count}/9 symbols")
        print(f"  Avg Return: {avg_return:+.2f}%")
        print(f"  Tier 1: {slippage_results[slippage_results['Tier']=='Tier 1']['Profitable'].sum()}/5")
        print(f"  Tier 2: {slippage_results[slippage_results['Tier']=='Tier 2']['Profitable'].sum()}/4")
        
        # Show failures
        failures = slippage_results[~slippage_results['Profitable']]['Symbol'].tolist()
        if failures:
            print(f"  Failed: {', '.join(failures)}")
    
    # Pass/Fail determination
    print("\n" + "="*80)
    print("GO/NO-GO DECISION")
    print("="*80)
    
    results_05 = df[df['Slippage_Pct'] == 0.50]
    profitable_05 = results_05['Profitable'].sum()
    
    results_10 = df[df['Slippage_Pct'] == 1.00]
    profitable_10 = results_10['Profitable'].sum()
    avg_return_10 = results_10['Adjusted_Return'].mean()
    
    print(f"\n0.5% Slippage: {profitable_05}/9 profitable (Target: ≥7/9)")
    print(f"1.0% Slippage: {profitable_10}/9 profitable (Target: ≥5/9)")
    print(f"1.0% Avg Return: {avg_return_10:+.2f}%")
    
    if profitable_05 >= 7 and profitable_10 >= 5:
        print("\n✅ PASS: Strategy has acceptable slippage tolerance")
        print("   DEPLOYMENT: APPROVED")
        print(f"   Recommendation: Deploy all {profitable_10} symbols passing 1.0% test")
    elif profitable_10 >= 5:
        print("\n⚠️  MARGINAL: Acceptable at 1.0% but marginal at 0.5%")
        print("   DEPLOYMENT: CONDITIONAL")
        print(f"   Recommendation: Deploy {profitable_10} best symbols, monitor spreads")
    else:
        print("\n❌ FAIL: Insufficient slippage tolerance")
        print("   DEPLOYMENT: BLOCKED")
        print("   REASON: Realistic execution costs destroy edge")
        print(f"   Only {profitable_10}/9 symbols survive 1.0% slippage")
    
    # Symbol-specific recommendations
    print("\n" + "-"*80)
    print("SYMBOL-SPECIFIC RECOMMENDATIONS")
    print("-"*80)
    
    for symbol in VALIDATED_SYMBOLS.keys():
        symbol_results = df[df['Symbol'] == symbol].sort_values('Slippage_Pct')
        
        # Find breakeven slippage
        profitable_at = symbol_results[symbol_results['Profitable']]['Slippage_Pct'].max() if symbol_results['Profitable'].any() else 0
        
        if profitable_at >= 1.0:
            status = "🟢 DEPLOY"
        elif profitable_at >= 0.5:
            status = "🟡 MONITOR"  
        else:
            status = "🔴 EXCLUDE"
        
        print(f"  {status} {symbol:6s}: Profitable up to {profitable_at:.2f}% slippage")
    
    print(f"\nResults saved to: {output_path}")
    print("="*80)

if __name__ == "__main__":
    main()
