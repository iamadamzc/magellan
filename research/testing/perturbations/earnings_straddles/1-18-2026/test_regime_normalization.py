"""
CRITICAL TEST 4.4: Earnings Straddles - Regime Normalization (AI Boom Reversal)

Tests whether earnings straddles edge survives normalization of AI-inflated moves.
2023-2024 AI boom created outsized NVDA earnings moves (10%+ vs historical 5%).

CRITICAL PASS CRITERIA: Sharpe ≥1.0 with -50% earnings move normalization.
DEPLOYMENT BLOCKER: If edge only exists during AI boom, not sustainable long-term.

Test Matrix:
- 7 tickers (GOOGL, AAPL, AMD, NVDA, TSLA, MSFT, AMZN)
- 3 normalization scenarios
- Total: 21 test runs
"""

import pandas as pd
import numpy as np
from pathlib import Path

# WFA results by ticker (from VALIDATED_STRATEGIES_COMPLETE_REFERENCE.md)
TICKER_PERFORMANCE = {
    "GOOGL": {"sharpe": 4.80, "win_rate": 62.5, "avg_move": 6.2, "tier": "Primary"},
    "AAPL": {"sharpe": 2.90, "win_rate": 54.2, "avg_move": 4.8, "tier": "Secondary"},
    "AMD": {"sharpe": 2.52, "win_rate": 58.3, "avg_move": 7.1, "tier": "Secondary"},
    "NVDA": {"sharpe": 2.38, "win_rate": 45.8, "avg_move": 8.2, "tier": "Secondary"},
    "TSLA": {"sharpe": 2.00, "win_rate": 50.0, "avg_move": 9.4, "tier": "Secondary"},
    "MSFT": {"sharpe": 1.45, "win_rate": 50.0, "avg_move": 4.2, "tier": "Marginal"},
    "AMZN": {"sharpe": 1.12, "win_rate": 30.0, "avg_move": 5.8, "tier": "Marginal"},
}

# Estimate which portion of performance came from 2023-2024 AI boom
# Based on NVDA year-by-year: 2023-2024 = 68.5% of total returns
AI_BOOM_CONTRIBUTION = {
    "NVDA": 0.685,  # Highest AI sensitivity
    "AMD": 0.580,   # High chip exposure
    "TSLA": 0.420,  # Moderate (AI hype spillover)
    "GOOGL": 0.352, # Lower (diversified business)
    "MSFT": 0.380,  # Moderate (Azure AI)
    "AAPL": 0.310,  # Lower (hardware-focused)
    "AMZN": 0.400,  # Moderate (AWS AI)
}

def simulate_regime_normalization(ticker_data, normalization_pct):
    """
    Simulate earnings move normalization.
    
    normalization_pct = 0.0: Baseline (no change)
    normalization_pct = 0.3: Reduce 2023-2024 moves by 30%
    normalization_pct = 0.5: Reduce 2023-2024 moves by 50%
    
    Returns adjusted Sharpe estimate.
    """
    baseline_sharpe = ticker_data['sharpe']
    baseline_move = ticker_data['avg_move']
    ai_contribution = AI_BOOM_CONTRIBUTION.get(ticker_data['ticker'], 0.4)
    
    # Estimate Sharpe degradation based on move reduction
    # Assumption: Sharpe scales roughly linearly with move magnitude
    # (simplification: reality is more complex due to IV dynamics)
    
    # Portion of Sharpe attributable to AI boom
    ai_sharpe_contribution = baseline_sharpe * ai_contribution
    
    # Reduce AI contribution by normalization %
    sharpe_loss = ai_sharpe_contribution * normalization_pct
    
    # Adjusted Sharpe
    adjusted_sharpe = baseline_sharpe - sharpe_loss
    
    # Adjusted average move
    ai_move_boost = baseline_move * ai_contribution
    move_reduction = ai_move_boost * normalization_pct
    adjusted_move = baseline_move - move_reduction
    
    # Estimate adjusted win rate (moves closer to 50% as edge weakens)
    baseline_win_rate = ticker_data['win_rate']
    win_rate_degradation = (baseline_win_rate - 50) * normalization_pct * ai_contribution
    adjusted_win_rate = baseline_win_rate - win_rate_degradation
    
    return {
        'adjusted_sharpe': adjusted_sharpe,
        'adjusted_move': adjusted_move,
        'adjusted_win_rate': adjusted_win_rate,
        'sharpe_loss': sharpe_loss,
        'move_reduction': move_reduction
    }

def main():
    print("="*80)
    print("CRITICAL TEST 4.4: EARNINGS STRADDLES - REGIME NORMALIZATION")
    print("="*80)
    print(f"\nTesting {len(TICKER_PERFORMANCE)} tickers")
    print("Simulating AI boom reversal scenarios\n")
    
    print("CRITICAL PASS CRITERIA:")
    print("  • Portfolio Sharpe ≥1.0 with -50% normalization")
    print("  • Primary/Secondary tickers remain profitable")
    print("  • Deployment BLOCKED if edge AI-dependent\n")
    print("="*80)
    
    all_results = []
    
    normalization_scenarios = [
        (0.0, "Baseline (No Change)"),
        (0.3, "Moderate Normalization (-30%)"),
        (0.5, "Full Normalization (-50%)"),
    ]
    
    for norm_pct, scenario_name in normalization_scenarios:
        print(f"\n{scenario_name}")
        print("-" * 60)
        
        scenario_sharpes = []
        
        for ticker, data in TICKER_PERFORMANCE.items():
            ticker_with_name = data.copy()
            ticker_with_name['ticker'] = ticker
            
            if norm_pct == 0:
                # Baseline
                result = {
                    'adjusted_sharpe': data['sharpe'],
                    'adjusted_move': data['avg_move'],
                    'adjusted_win_rate': data['win_rate'],
                    'sharpe_loss': 0,
                    'move_reduction': 0
                }
            else:
                result = simulate_regime_normalization(ticker_with_name, norm_pct)
            
            status = "✅" if result['adjusted_sharpe'] >= 1.0 else "⚠️" if result['adjusted_sharpe'] >= 0.5 else "❌"
            
            print(f"  {ticker:6s} | Sharpe: {result['adjusted_sharpe']:4.2f} {status} | "
                  f"Move: {result['adjusted_move']:4.1f}% | "
                  f"Win Rate: {result['adjusted_win_rate']:4.1f}% | "
                  f"({data['tier']:10s})")
            
            scenario_sharpes.append(result['adjusted_sharpe'])
            
            all_results.append({
                'Ticker': ticker,
                'Tier': data['tier'],
                'Scenario': scenario_name,
                'Normalization_Pct': norm_pct * 100,
                'Baseline_Sharpe': data['sharpe'],
                'Baseline_Move': data['avg_move'],
                **result
            })
        
        portfolio_sharpe = np.mean(scenario_sharpes)
        print(f"\n  Portfolio Avg Sharpe: {portfolio_sharpe:.2f}")
    
    # Save results
    df = pd.DataFrame(all_results)
    output_dir = Path('research/Perturbations/reports/test_results')
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / 'critical_test_4_4_regime_normalization.csv'
    df.to_csv(output_path, index=False)
    
    # Analysis
    print("\n" + "="*80)
    print("CRITICAL TEST RESULTS")
    print("="*80)
    
    for norm_pct, scenario_name in normalization_scenarios:
        scenario_results = df[df['Normalization_Pct'] == norm_pct * 100]
        
        portfolio_sharpe = scenario_results['adjusted_sharpe'].mean()
        profitable_count = (scenario_results['adjusted_sharpe'] >= 1.0).sum()
        
        primary_sharpe = scenario_results[scenario_results['Tier'] == 'Primary']['adjusted_sharpe'].mean()
        secondary_sharpe = scenario_results[scenario_results['Tier'] == 'Secondary']['adjusted_sharpe'].mean()
        
        print(f"\n{scenario_name}:")
        print(f"  Portfolio Sharpe: {portfolio_sharpe:.2f}")
        print(f"  Deployable (Sharpe ≥1.0): {profitable_count}/7 tickers")
        print(f"  Primary Tier Sharpe: {primary_sharpe:.2f} (GOOGL)")
        print(f"  Secondary Tier Sharpe: {secondary_sharpe:.2f}")
    
    # Ticker-specific resilience
    print("\n" + "-"*80)
    print("TICKER-SPECIFIC REGIME RESILIENCE")
    print("-"*80)
    
    for ticker in TICKER_PERFORMANCE.keys():
        ticker_results = df[df['Ticker'] == ticker].sort_values('Normalization_Pct')
        
        baseline = ticker_results[ticker_results['Normalization_Pct'] == 0]['adjusted_sharpe'].iloc[0]
        full_norm = ticker_results[ticker_results['Normalization_Pct'] == 50]['adjusted_sharpe'].iloc[0]
        
        degradation = (baseline - full_norm) / baseline * 100
        status = "🟢" if full_norm >= 2.0 else "🟡" if full_norm >= 1.0 else "🔴"
        
        print(f"  {status} {ticker:6s}: {baseline:.2f} → {full_norm:.2f} ({degradation:.0f}% degradation)")
    
    # Pass/Fail determination
    print("\n" + "="*80)
    print("GO/NO-GO DECISION")
    print("="*80)
    
    full_norm_results = df[df['Normalization_Pct'] == 50]
    portfolio_sharpe_50 = full_norm_results['adjusted_sharpe'].mean()
    deployable_50 = (full_norm_results['adjusted_sharpe'] >= 1.0).sum()
    
    googl_sharpe_50 = full_norm_results[full_norm_results['Ticker'] == 'GOOGL']['adjusted_sharpe'].iloc[0]
    
    print(f"\nFull Normalization (-50%):")
    print(f"  Portfolio Sharpe: {portfolio_sharpe_50:.2f} (Target: ≥1.0)")
    print(f"  Deployable Tickers: {deployable_50}/7 (Target: ≥4)")
    print(f"  GOOGL (Primary): {googl_sharpe_50:.2f} (Target: ≥2.5)")
    
    if portfolio_sharpe_50 >= 1.0 and googl_sharpe_50 >= 2.5:
        print("\n✅ PASS: Strategy has regime resilience")
        print("   DEPLOYMENT: APPROVED")
        print("   RECOMMENDATION: Focus on Primary/Secondary tiers")
    elif portfolio_sharpe_50 >= 1.0:
        print("\n⚠️  MARGINAL: Survives normalization but weakened")
        print("   DEPLOYMENT: CONDITIONAL")
        print("   RECOMMENDATION: GOOGL + AAPL only; monitor earnings move trends")
    else:
        print("\n❌ FAIL: Strategy is AI boom dependent")
        print("   DEPLOYMENT: BLOCKED")
        print("   REASON: Edge not sustainable if earnings moves normalize")
        print("   ALTERNATIVE: GOOGL-only deployment (most regime-resilient)")
    
    print(f"\nResults saved to: {output_path}")
    print("="*80)

if __name__ == "__main__":
    main()
