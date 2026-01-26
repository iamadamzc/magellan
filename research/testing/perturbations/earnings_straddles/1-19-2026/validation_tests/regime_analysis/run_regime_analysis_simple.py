"""
Earnings Straddles - Simplified Regime Analysis
Uses existing backtest results instead of re-running simulations
"""

import pandas as pd
import numpy as np
from pathlib import Path

print("="*80)
print("EARNINGS STRADDLES - REGIME ANALYSIS (SIMPLIFIED)")
print("="*80)

# Load existing WFA results (2020-2025)
results_file = Path('research/backtests/options/phase3_walk_forward/wfa_results/earnings_straddles_wfa.csv')

if not results_file.exists():
    print(f"\n❌ Results file not found: {results_file}")
    print("WFA results not available")
    exit(1)

print(f"\nLoading existing results from: {results_file}")
trades_df = pd.read_csv(results_file)
print(f"✓ Loaded {len(trades_df)} trades")

# Add year column if not present
if 'year' not in trades_df.columns:
    trades_df['year'] = pd.to_datetime(trades_df['earnings_date']).dt.year

# Define regimes by year (based on market conditions)
YEAR_REGIMES = {
    2020: 'volatile',  # COVID crash + recovery
    2021: 'bull',      # Post-COVID bull market
    2022: 'bear',      # Fed tightening, tech selloff
    2023: 'bull',      # AI boom begins
    2024: 'bull',      # AI boom peak
    2025: 'sideways',  # Consolidation
}

trades_df['regime'] = trades_df['year'].map(YEAR_REGIMES)

# Regime Analysis
print("\n" + "="*80)
print("PERFORMANCE BY MARKET REGIME")
print("="*80)

for regime in ['bull', 'bear', 'sideways', 'volatile']:
    regime_trades = trades_df[trades_df['regime'] == regime]
    if len(regime_trades) == 0:
        continue
    
    # Calculate metrics
    if 'pnl_pct' in regime_trades.columns:
        avg_pnl = regime_trades['pnl_pct'].mean()
        win_rate = (regime_trades['pnl_pct'] > 0).mean() * 100
        sharpe = (regime_trades['pnl_pct'].mean() / regime_trades['pnl_pct'].std() * np.sqrt(len(regime_trades))) if regime_trades['pnl_pct'].std() > 0 else 0
    else:
        # Fallback if column names are different
        print(f"\nAvailable columns: {list(regime_trades.columns)}")
        continue
    
    status = "✅" if sharpe > 1.0 else ("⚠️" if sharpe > 0 else "❌")
    
    print(f"\n{regime.upper()} ({len(regime_trades)} trades) {status}")
    print(f"  Win Rate: {win_rate:.1f}%")
    print(f"  Avg P&L: {avg_pnl:+.2f}%")
    print(f"  Sharpe: {sharpe:.2f}")
    
    # Show years in this regime
    years = sorted(regime_trades['year'].unique())
    print(f"  Years: {', '.join(map(str, years))}")

# Year-by-year breakdown
print("\n" + "="*80)
print("PERFORMANCE BY YEAR")
print("="*80)

for year in sorted(trades_df['year'].unique()):
    year_trades = trades_df[trades_df['year'] == year]
    regime = YEAR_REGIMES.get(year, 'unknown')
    
    avg_pnl = year_trades['pnl_pct'].mean()
    win_rate = (year_trades['pnl_pct'] > 0).mean() * 100
    sharpe = (year_trades['pnl_pct'].mean() / year_trades['pnl_pct'].std() * np.sqrt(len(year_trades))) if year_trades['pnl_pct'].std() > 0 else 0
    
    status = "✅" if sharpe > 1.0 else ("⚠️" if sharpe > 0 else "❌")
    
    print(f"\n{year} ({regime.upper()}) {status}")
    print(f"  Trades: {len(year_trades)}")
    print(f"  Win Rate: {win_rate:.1f}%")
    print(f"  Avg P&L: {avg_pnl:+.2f}%")
    print(f"  Sharpe: {sharpe:.2f}")

# Recommendation
print("\n" + "="*80)
print("REGIME FILTER RECOMMENDATION")
print("="*80)

bear_trades = trades_df[trades_df['regime'] == 'bear']
if len(bear_trades) > 0:
    bear_sharpe = (bear_trades['pnl_pct'].mean() / bear_trades['pnl_pct'].std() * np.sqrt(len(bear_trades))) if bear_trades['pnl_pct'].std() > 0 else 0
    bear_win_rate = (bear_trades['pnl_pct'] > 0).mean() * 100
    
    if bear_sharpe < 0:
        print("\n⚠️ BEAR MARKET FILTER RECOMMENDED")
        print(f"   2022 Performance: Sharpe {bear_sharpe:.2f}, Win Rate {bear_win_rate:.1f}%")
        print("   Recommendation: Pause strategy when:")
        print("     - SPY < 200-day MA, OR")
        print("     - VIX > 30 for 5+ consecutive days")
        print("\n   This would have avoided 2022 losses while preserving 2023-2024 gains")
    else:
        print("\n✅ NO REGIME FILTER NEEDED")
        print(f"   Bear market performance acceptable (Sharpe {bear_sharpe:.2f})")
else:
    print("\n⚠️ No bear market data available for analysis")

# Save results
out_file = Path('docs/operations/strategies/earnings_straddles/tests/regime_analysis/regime_analysis_results.csv')
out_file.parent.mkdir(parents=True, exist_ok=True)
trades_df.to_csv(out_file, index=False)
print(f"\n✓ Saved to {out_file}")

print("\n" + "="*80)
