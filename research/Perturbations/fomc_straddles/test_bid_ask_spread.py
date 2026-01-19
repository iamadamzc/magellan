"""
CRITICAL TEST 3.2: FOMC Event Straddles - Bid-Ask Spread Stress

Tests whether FOMC straddle edge survives realistic options execution costs.
FOMC volatility causes spreads to widen 2-5x normal levels.

CRITICAL PASS CRITERIA: ≥75% win rate (6/8 events) at 1.0% round-trip slippage.
DEPLOYMENT BLOCKER: If <75% win rate at 0.6% slippage, strategy is NOT deployable.

Test Matrix:
- 8 FOMC events (2024)
- 5 slippage levels (0%, 0.2%, 0.6%, 1.0%, 2.0%)
- Total: 40 test runs
"""

import pandas as pd
import numpy as np
from pathlib import Path

# 2024 FOMC events with SPY 10-minute moves (from validation)
FOMC_2024_EVENTS = [
    {"date": "2024-01-31", "spy_move_pct": 0.16, "baseline_pnl_pct": 7.94},
    {"date": "2024-03-20", "spy_move_pct": 0.62, "baseline_pnl_pct": 31.24},
    {"date": "2024-05-01", "spy_move_pct": 0.13, "baseline_pnl_pct": 6.33},
    {"date": "2024-06-12", "spy_move_pct": 0.15, "baseline_pnl_pct": 7.40},
    {"date": "2024-07-31", "spy_move_pct": 0.05, "baseline_pnl_pct": 2.48},
    {"date": "2024-09-18", "spy_move_pct": 0.57, "baseline_pnl_pct": 28.54},  # Fed pivot
    {"date": "2024-11-07", "spy_move_pct": 0.05, "baseline_pnl_pct": 2.46},
    {"date": "2024-12-18", "spy_move_pct": 0.48, "baseline_pnl_pct": 23.80},
]

SLIPPAGE_LEVELS = [0.0, 0.2, 0.6, 1.0, 2.0]  # % round-trip cost

def calculate_slippage_adjusted_pnl(baseline_pnl_pct, slippage_pct):
    """
    Calculate P&L after slippage.
    
    Baseline P&L is profit from straddle assuming perfect mid-price fills.
    Slippage reduces profit by the round-trip cost.
    """
    adjusted_pnl = baseline_pnl_pct - slippage_pct
    return adjusted_pnl

def main():
    print("="*80)
    print("CRITICAL TEST 3.2: FOMC STRADDLES - BID-ASK SPREAD STRESS")
    print("="*80)
    print(f"\nTesting {len(FOMC_2024_EVENTS)} FOMC events (2024)")
    print(f"Slippage levels: {SLIPPAGE_LEVELS}\n")
    
    print("CRITICAL PASS CRITERIA:")
    print("  • ≥75% win rate (6/8 events) at 1.0% slippage")
    print("  • ≥87.5% win rate (7/8 events) at 0.6% slippage")
    print("  • Deployment BLOCKED if fail\n")
    print("="*80)
    
    all_results = []
    
    for slippage_pct in SLIPPAGE_LEVELS:
        print(f"\n{slippage_pct:.1f}% Slippage Scenario")
        print("-" * 60)
        
        wins = 0
        total_pnl = 0
        
        for event in FOMC_2024_EVENTS:
            adjusted_pnl = calculate_slippage_adjusted_pnl(event['baseline_pnl_pct'], slippage_pct)
            is_win = adjusted_pnl > 0
            
            if is_win:
                wins += 1
            
            total_pnl += adjusted_pnl
            
            status = "✅" if is_win else "❌"
            slippage_impact = event['baseline_pnl_pct'] - adjusted_pnl
            
            print(f"  {event['date']} | SPY: {event['spy_move_pct']:+.2f}% | "
                  f"P&L: {adjusted_pnl:+6.2f}% {status} "
                  f"(slippage: -{slippage_impact:.2f}%)")
            
            all_results.append({
                'Event_Date': event['date'],
                'SPY_Move_Pct': event['spy_move_pct'],
                'Slippage_Pct': slippage_pct,
                'Baseline_PnL': event['baseline_pnl_pct'],
                'Adjusted_PnL': adjusted_pnl,
                'Slippage_Impact': slippage_impact,
                'Win': is_win
            })
        
        win_rate = wins / len(FOMC_2024_EVENTS) * 100
        avg_pnl = total_pnl / len(FOMC_2024_EVENTS)
        
        print(f"\n  Win Rate: {wins}/{len(FOMC_2024_EVENTS)} ({win_rate:.1f}%)")
        print(f"  Avg P&L: {avg_pnl:+.2f}%")
    
    # Save results
    df = pd.DataFrame(all_results)
    output_dir = Path('research/Perturbations/reports/test_results')
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / 'critical_test_3_2_bid_ask_spread.csv'
    df.to_csv(output_path, index=False)
    
    # Analysis
    print("\n" + "="*80)
    print("CRITICAL TEST RESULTS")
    print("="*80)
    
    for slippage_pct in SLIPPAGE_LEVELS:
        slippage_results = df[df['Slippage_Pct'] == slippage_pct]
        wins = slippage_results['Win'].sum()
        win_rate = wins / len(slippage_results) * 100
        avg_pnl = slippage_results['Adjusted_PnL'].mean()
        
        print(f"\n{slippage_pct:.1f}% Slippage:")
        print(f"  Win Rate: {wins}/{len(slippage_results)} ({win_rate:.1f}%)")
        print(f"  Avg P&L: {avg_pnl:+.2f}%")
        print(f"  Worst Event: {slippage_results['Adjusted_PnL'].min():+.2f}%")
        print(f"  Best Event: {slippage_results['Adjusted_PnL'].max():+.2f}%")
    
    # Slippage breakeven analysis
    print("\n" + "-"*80)
    print("SLIPPAGE BREAKEVEN ANALYSIS")
    print("-"*80)
    
    for event in FOMC_2024_EVENTS:
        breakeven_slippage = event['baseline_pnl_pct']
        print(f"  {event['date']}: Breakeven at {breakeven_slippage:.2f}% slippage")
    
    # Pass/Fail determination
    print("\n" + "="*80)
    print("GO/NO-GO DECISION")
    print("="*80)
    
    results_06 = df[df['Slippage_Pct'] == 0.6]
    win_rate_06 = results_06['Win'].sum() / len(results_06) * 100
    
    results_10 = df[df['Slippage_Pct'] == 1.0]
    win_rate_10 = results_10['Win'].sum() / len(results_10) * 100
    avg_pnl_10 = results_10['Adjusted_PnL'].mean()
    
    print(f"\n0.6% Slippage: {results_06['Win'].sum()}/8 events profitable ({win_rate_06:.1f}%)")
    print(f"1.0% Slippage: {results_10['Win'].sum()}/8 events profitable ({win_rate_10:.1f}%)")
    print(f"1.0% Avg P&L: {avg_pnl_10:+.2f}%")
    
    if win_rate_10 >= 75 and win_rate_06 >= 87.5:
        print("\n✅ PASS: Strategy has strong slippage tolerance")
        print("   DEPLOYMENT: APPROVED")
        print(f"   Expected real-world return: ~{avg_pnl_10:.1f}% per event")
    elif win_rate_10 >= 75:
        print("\n⚠️  MARGINAL: 1.0% tolerance OK, but 0.6% marginal")
        print("   DEPLOYMENT: CONDITIONAL (excellent execution required)")
    else:
        print("\n❌ FAIL: Insufficient slippage tolerance")
        print("   DEPLOYMENT: BLOCKED")
        print("   REASON: Realistic spreads destroy edge")
        print("   ALTERNATIVE: Only trade 'big FOMC' events (SPY move >0.5%)")
    
    print(f"\nResults saved to: {output_path}")
    print("="*80)

if __name__ == "__main__":
    main()
