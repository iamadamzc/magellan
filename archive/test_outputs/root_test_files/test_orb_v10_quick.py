"""Quick diagnostic for ORB V10"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print("Testing ORB V10...")
print("Step 1: Import modules")

try:
    from research.new_strategy_builds.strategies.orb_v10 import run_orb_v10
    print("✅ Import successful")
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

print("\nStep 2: Run backtest")
try:
    result = run_orb_v10('RIOT', '2024-11-01', '2024-11-30')
    print(f"✅ Backtest complete")
    print(f"   Trades: {result['total_trades']}")
    print(f"   Win Rate: {result['win_rate']:.1f}%")
    print(f"   Avg P&L: {result['avg_pnl']:+.3f}%")
except Exception as e:
    print(f"❌ Backtest failed: {e}")
    import traceback
    traceback.print_exc()
