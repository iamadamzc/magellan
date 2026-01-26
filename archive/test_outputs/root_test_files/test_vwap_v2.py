"""Quick test of VWAP Reclaim V2"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from research.new_strategy_builds.strategies.vwap_reclaim_v2 import run_backtest_v2

# Test on RIOT Recent
result = run_backtest_v2('RIOT', '2024-11-01', '2025-01-17')

print("\n" + "="*80)
print("VWAP RECLAIM V2 - EXPERT-CORRECTED RESULTS")
print("="*80)
print(f"Symbol: {result['symbol']}")
print(f"Total Trades: {result['total_trades']}")
print(f"Win Rate: {result['win_rate']:.1f}%")
print(f"Avg P&L: {result['avg_pnl']:+.2f}%")
print(f"Total P&L: {result['total_pnl']:+.2f}%")
print(f"Sharpe: {result['sharpe']:.2f}")
print(f"Avg Hold: {result['avg_hold']:.1f} min")
