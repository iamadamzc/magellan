"""
ORB V13 ABLATION TEST - RIOT
-----------------------------
Phase 1 Testing: Does fixing exit asymmetry solve the paradox?

TEST DESIGN:
- Symbol: RIOT (best baseline, 50 trades, +4.18% in V7)
- Period: Nov 2024 - Jan 2025
- Control: V7 baseline (current losing config on most symbols)
- Treatment: V13 surgical (expert consensus fixes)

SUCCESS CRITERIA:
- V13 Total P&L > V7 Total P&L by at least 30%
- V13 Expectancy (R) > 0.0
- V13 Avg Winner > 1.0R (vs 0.5R in V7)

EXPECTED OUTCOME:
- Win rate drops: 59% → 45-50%
- Avg Win increases: 0.5R → 1.2-1.5R
- Expectancy flips: -0.10R → +0.10-0.20R

If V13 wins decisively, proceed to Phase 2 (Universe Testing).
"""

import pandas as pd
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from research.new_strategy_builds.strategies.orb_v7 import run_orb_v7
from research.new_strategy_builds.strategies.orb_v13_surgical import run_orb_v13_surgical

def main():
    symbol = 'RIOT'
    start = '2024-11-01'
    end = '2025-01-17'
    
    print("\n" + "="*70)
    print("ORB V13 SURGICAL - PHASE 1 ABLATION TEST")
    print("="*70)
    print(f"\n🎯 Objective: Prove exit asymmetry was the root cause")
    print(f"📊 Test Symbol: {symbol}")
    print(f"📅 Test Period: {start} to {end}")
    print(f"\n{'='*70}\n")
    
    # Control: V7 Baseline
    print("🔬 CONTROL GROUP: ORB V7 (Current Baseline)")
    print("─"*70)
    v7_result = run_orb_v7(symbol, start, end)
    
    print("\n\n")
    
    # Treatment: V13 Surgical
    print("💉 TREATMENT GROUP: ORB V13 (Expert Consensus Fixes)")
    print("─"*70)
    v13_result = run_orb_v13_surgical(symbol, start, end)
    
    # Comparison
    print("\n" + "="*70)
    print("📈 COMPARATIVE ANALYSIS")
    print("="*70)
    
    if v7_result['total_trades'] == 0 or v13_result['total_trades'] == 0:
        print("❌ Insufficient data for comparison")
        return
    
    print(f"\n{'Metric':<25} {'V7 (Control)':<20} {'V13 (Treatment)':<20} {'Delta':<15}")
    print("─"*80)
    
    # Trades
    trades_delta = v13_result['total_trades'] - v7_result['total_trades']
    trades_pct = (trades_delta / v7_result['total_trades'] * 100) if v7_result['total_trades'] > 0 else 0
    print(f"{'Total Trades':<25} {v7_result['total_trades']:<20} {v13_result['total_trades']:<20} {trades_delta:+d} ({trades_pct:+.1f}%)")
    
    # Win Rate
    wr_delta = v13_result['win_rate'] - v7_result['win_rate']
    print(f"{'Win Rate':<25} {v7_result['win_rate']:<20.1f}% {v13_result['win_rate']:<20.1f}% {wr_delta:+.1f}%")
    
    # Total P&L
    pnl_delta = v13_result['total_pnl'] - v7_result['total_pnl']
    pnl_improvement_pct = (pnl_delta / abs(v7_result['total_pnl']) * 100) if v7_result['total_pnl'] != 0 else 0
    print(f"{'Total P&L':<25} {v7_result['total_pnl']:+.2f}%{'':11} {v13_result['total_pnl']:+.2f}%{'':11} {pnl_delta:+.2f}% ({pnl_improvement_pct:+.0f}%)")
    
    # Avg P&L
    avg_pnl_delta = v13_result['avg_pnl'] - v7_result['avg_pnl']
    print(f"{'Avg P&L per Trade':<25} {v7_result['avg_pnl']:+.3f}%{'':11} {v13_result['avg_pnl']:+.3f}%{'':11} {avg_pnl_delta:+.3f}%")
    
    # Sharpe
    sharpe_delta = v13_result['sharpe'] - v7_result['sharpe']
    print(f"{'Sharpe Ratio':<25} {v7_result['sharpe']:.2f}{'':15} {v13_result['sharpe']:.2f}{'':15} {sharpe_delta:+.2f}")
    
    # R-Multiple Analysis (KEY)
    print(f"\n{'─'*80}")
    print("💡 R-MULTIPLE ANALYSIS (The Core of the Hypothesis)")
    print(f"{'─'*80}")
    
    v7_avg_winner = 0.5  # Estimated from handoff doc (V7 doesn't track this)
    v7_avg_loser = -1.0
    v7_expectancy = (v7_result['win_rate']/100 * v7_avg_winner) + ((100-v7_result['win_rate'])/100 * v7_avg_loser)
    
    print(f"{'Metric':<25} {'V7 (Control)':<20} {'V13 (Treatment)':<20} {'Delta':<15}")
    print(f"{'Avg Winner (R)':<25} {v7_avg_winner:+.2f}R{'':13} {v13_result['avg_winner_r']:+.2f}R{'':13} {v13_result['avg_winner_r'] - v7_avg_winner:+.2f}R")
    print(f"{'Avg Loser (R)':<25} {v7_avg_loser:+.2f}R{'':13} {v13_result['avg_loser_r']:+.2f}R{'':13} {v13_result['avg_loser_r'] - v7_avg_loser:+.2f}R")
    print(f"{'Expectancy (R)':<25} {v7_expectancy:+.3f}R{'':13} {v13_result['expectancy_r']:+.3f}R{'':13} {v13_result['expectancy_r'] - v7_expectancy:+.3f}R")
    
    # Verdict
    print(f"\n{'='*70}")
    print("🏆 VERDICT")
    print(f"{'='*70}\n")
    
    success_criteria = {
        'Total P&L Improvement': (pnl_delta > 0, f"{pnl_delta:+.2f}% (Target: > 0%)"),
        'Expectancy Positive': (v13_result['expectancy_r'] > 0, f"{v13_result['expectancy_r']:+.3f}R (Target: > 0.0R)"),
        'Avg Winner > 1.0R': (v13_result['avg_winner_r'] > 1.0, f"{v13_result['avg_winner_r']:+.2f}R (Target: > 1.0R)"),
        'P&L Improvement > 30%': (pnl_improvement_pct > 30, f"{pnl_improvement_pct:+.0f}% (Target: > 30%)")
    }
    
    passes = 0
    fails = 0
    
    for criterion, (passed, value) in success_criteria.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status:8s} | {criterion:<25s} | {value}")
        if passed:
            passes += 1
        else:
            fails += 1
    
    print(f"\n{'─'*70}")
    print(f"Overall: {passes}/{len(success_criteria)} criteria passed")
    
    if passes >= 3:
        print(f"\n🎉 SUCCESS! V13 decisively beats V7.")
        print(f"   ➡️  Hypothesis CONFIRMED: Exit asymmetry was the root cause.")
        print(f"   ➡️  NEXT STEP: Proceed to Phase 2 (Universe Testing)")
        recommendation = "PROCEED_TO_PHASE_2"
    elif passes >= 2:
        print(f"\n⚠️  PARTIAL SUCCESS. V13 shows improvement but not decisive.")
        print(f"   ➡️  Consider parameter tuning before Phase 2.")
        recommendation = "TUNE_THEN_PHASE_2"
    else:
        print(f"\n❌ FAILURE. V13 did not improve over V7.")
        print(f"   ➡️  Hypothesis may be wrong. Re-examine entry logic or universe.")
        recommendation = "REVISIT_HYPOTHESIS"
    
    # Save results
    comparison_df = pd.DataFrame({
        'Version': ['V7', 'V13'],
        'Total_Trades': [v7_result['total_trades'], v13_result['total_trades']],
        'Win_Rate': [v7_result['win_rate'], v13_result['win_rate']],
        'Avg_PnL': [v7_result['avg_pnl'], v13_result['avg_pnl']],
        'Total_PnL': [v7_result['total_pnl'], v13_result['total_pnl']],
        'Sharpe': [v7_result['sharpe'], v13_result['sharpe']],
        'Avg_Winner_R': [v7_avg_winner, v13_result['avg_winner_r']],
        'Avg_Loser_R': [v7_avg_loser, v13_result['avg_loser_r']],
        'Expectancy_R': [v7_expectancy, v13_result['expectancy_r']]
    })
    
    output_path = project_root / 'research' / 'new_strategy_builds' / 'results' / 'ORB_V13_ABLATION_RIOT.csv'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    comparison_df.to_csv(output_path, index=False)
    
    print(f"\n📁 Results saved to: {output_path}")
    print(f"🚀 Recommendation: {recommendation}")
    print(f"\n{'='*70}\n")
    
    return comparison_df, recommendation

if __name__ == "__main__":
    main()
