"""
Master Orchestration Script - Blind Backwards Analysis

Runs all 4 phases sequentially:
1. Target Definition (Event Discovery)
2. Feature Engineering
3. Cluster Analysis
4. Strategy Synthesis

Output: Discovered trading strategies with Edge Ratio, Hit Rate, and confidence intervals
"""

import sys
from pathlib import Path
import time

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from discover_events import main as run_phase1
from feature_engine import main as run_phase2
from cluster_analysis import main as run_phase3
from strategy_synthesis import main as run_phase4


def run_full_pipeline():
    """Execute complete blind backwards analysis pipeline."""
    
    start_time = time.time()
    
    print("\n" + "=" * 70)
    print("   BLIND BACKWARDS ANALYSIS - INTRADAY ALPHA DISCOVERY")
    print("   " + "-" * 50)
    print("   NO classic patterns | NO standard indicators | DATA ONLY")
    print("=" * 70 + "\n")
    
    # Phase 1: Target Definition
    print("\n" + "▓" * 70)
    print("  PHASE 1: TARGET DEFINITION - IDENTIFYING WINNING EVENTS")
    print("▓" * 70)
    phase1_results = run_phase1()
    
    # Phase 2: Feature Engineering
    print("\n" + "▓" * 70)
    print("  PHASE 2: FEATURE ENGINEERING - BUILDING STATIONARY VOCABULARY")
    print("▓" * 70)
    phase2_results = run_phase2()
    
    # Phase 3: Cluster Analysis
    print("\n" + "▓" * 70)
    print("  PHASE 3: CLUSTER ANALYSIS - DISCOVERING HIDDEN STATES")
    print("▓" * 70)
    phase3_results = run_phase3()
    
    # Phase 4: Strategy Synthesis
    print("\n" + "▓" * 70)
    print("  PHASE 4: STRATEGY SYNTHESIS - GENERATING EXECUTABLE LOGIC")
    print("▓" * 70)
    phase4_results = run_phase4(phase3_results)
    
    # Final Summary
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 70)
    print("   ANALYSIS COMPLETE")
    print("=" * 70)
    print(f"\nTotal runtime: {elapsed/60:.1f} minutes")
    
    output_path = Path(__file__).parent / "outputs"
    print(f"\nOutputs saved to: {output_path}")
    print("\nGenerated files:")
    for f in sorted(output_path.glob("*")):
        print(f"  - {f.name}")
    
    # Print strategy summary
    if phase4_results:
        print("\n" + "-" * 70)
        print("DISCOVERED STRATEGIES:")
        print("-" * 70)
        
        for symbol, strat in phase4_results.items():
            m = strat['metrics']
            print(f"\n{symbol}:")
            print(f"  Hit Rate:    {m['hit_rate']:.1%} (95% CI: [{m['hit_rate_ci'][0]:.1%}, {m['hit_rate_ci'][1]:.1%}])")
            print(f"  Edge Ratio:  {m['edge_ratio']:.2f} (95% CI: [{m['edge_ratio_ci'][0]:.2f}, {m['edge_ratio_ci'][1]:.2f}])")
            print(f"  Expectancy:  ${m['expectancy']:.4f} per trade")
            print(f"  Signals:     {m['total_signals']:,}")
    
    return phase4_results


if __name__ == "__main__":
    results = run_full_pipeline()
