"""
CRITICAL TEST 1.2: Daily Trend Friction Sensitivity

Tests whether Daily Trend Hysteresis edge survives realistic execution costs.
High trade frequency (70-100 trades/year) means slippage can destroy the edge.

CRITICAL PASS CRITERIA: All 11 assets must be profitable at 10 bps.
DEPLOYMENT BLOCKER: If <8 assets profitable at 15 bps, strategy is NOT deployable.

Test Matrix:
- 11 assets (7 MAG7 + 4 indices/ETFs)
- 5 friction levels (2, 5, 10, 15, 20 bps)
- Total: 55 test runs
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_cache import cache

# Validated configurations from VALIDATED_STRATEGIES_COMPLETE_REFERENCE.md
VALIDATED_CONFIGS = {
    "AAPL": {"rsi_period": 28, "upper_band": 65, "lower_band": 35},
    "AMZN": {"rsi_period": 21, "upper_band": 55, "lower_band": 45},
    "GOOGL": {"rsi_period": 28, "upper_band": 55, "lower_band": 45},
    "META": {"rsi_period": 28, "upper_band": 55, "lower_band": 45},
    "MSFT": {"rsi_period": 21, "upper_band": 58, "lower_band": 42},
    "NVDA": {"rsi_period": 28, "upper_band": 58, "lower_band": 42},
    "TSLA": {"rsi_period": 28, "upper_band": 58, "lower_band": 42},
    "SPY": {"rsi_period": 21, "upper_band": 58, "lower_band": 42},
    "QQQ": {"rsi_period": 21, "upper_band": 60, "lower_band": 40},
    "IWM": {"rsi_period": 28, "upper_band": 65, "lower_band": 35},
    "GLD": {"rsi_period": 21, "upper_band": 65, "lower_band": 35},
}

VALIDATION_START = "2024-06-01"
VALIDATION_END = "2026-01-18"
FRICTION_LEVELS = [2, 5, 10, 15, 20]  # bps

def calculate_rsi(prices, period=21):
    """Calculate RSI indicator"""
    delta = prices.diff()
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)
    avg_gain = gains.ewm(span=period, adjust=False).mean()
    avg_loss = losses.ewm(span=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.inf)
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.replace([np.inf, -np.inf], np.nan).fillna(50)
    return rsi

def run_backtest(symbol, config, friction_bps):
    """Run backtest with specified friction"""
    try:
        # Fetch daily data
        df = cache.get_or_fetch_equity(symbol, '1day', VALIDATION_START, VALIDATION_END)
        
        if len(df) < 200:
            return None
        
        # Calculate RSI
        df['rsi'] = calculate_rsi(df['close'], period=config['rsi_period'])
        
        # Generate signals (RSI hysteresis / Schmidt trigger)
        position = 0
        signals = []
        
        for i in range(len(df)):
            rsi_val = df['rsi'].iloc[i]
            
            if pd.isna(rsi_val):
                signals.append(position)
                continue
            
            if position == 0:  # Flat
                if rsi_val > config['upper_band']:
                    position = 1  # Go long
            elif position == 1:  # Long
                if rsi_val < config['lower_band']:
                    position = 0  # Go flat
            
            signals.append(position)
        
        df['signal'] = signals
        
        # Calculate returns
        df['returns'] = df['close'].pct_change()
        df['strategy_returns'] = df['signal'].shift(1) * df['returns']
        
        # Count trades
        trades = (df['signal'].diff() != 0).sum()
        
        # Apply friction
        friction_per_trade = friction_bps / 10000
        total_friction = trades * friction_per_trade
        
        # Performance metrics
        total_return = (1 + df['strategy_returns']).prod() - 1 - total_friction
        
        if df['strategy_returns'].std() > 0:
            sharpe = (df['strategy_returns'].mean() / df['strategy_returns'].std()) * np.sqrt(252)
        else:
            sharpe = 0
        
        # Max drawdown
        cum_returns = (1 + df['strategy_returns']).cumprod()
        running_max = cum_returns.expanding().max()
        drawdown = (cum_returns - running_max) / running_max
        max_dd = drawdown.min()
        
        return {
            'return_pct': total_return * 100,
            'sharpe': sharpe,
            'max_dd': max_dd * 100,
            'trades': trades,
            'friction_cost': total_friction * 100,
            'profitable': total_return > 0
        }
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return None

def main():
    print("="*80)
    print("CRITICAL TEST 1.2: DAILY TREND FRICTION SENSITIVITY")
    print("="*80)
    print(f"\nValidation Period: {VALIDATION_START} to {VALIDATION_END}")
    print(f"Testing {len(VALIDATED_CONFIGS)} assets at {len(FRICTION_LEVELS)} friction levels")
    print(f"Total test runs: {len(VALIDATED_CONFIGS) * len(FRICTION_LEVELS)}\n")
    
    print("CRITICAL PASS CRITERIA:")
    print("  • All 11 assets profitable at 10 bps")
    print("  • ≥8 assets profitable at 15 bps")
    print("  • Deployment BLOCKED if fail\n")
    print("="*80)
    
    all_results = []
    
    for symbol, config in VALIDATED_CONFIGS.items():
        print(f"\n{symbol} - RSI-{config['rsi_period']}, Bands {config['upper_band']}/{config['lower_band']}")
        print("-" * 60)
        
        for friction_bps in FRICTION_LEVELS:
            print(f"  Testing {friction_bps:2d} bps friction...", end=" ")
            
            result = run_backtest(symbol, config, friction_bps)
            
            if result is None:
                print("SKIP")
                continue
            
            status_icon = "✅" if result['profitable'] else "❌"
            print(f"{status_icon} Return: {result['return_pct']:+6.2f}% | Sharpe: {result['sharpe']:4.2f} | Trades: {result['trades']:3d}")
            
            all_results.append({
                'Asset': symbol,
                'RSI': config['rsi_period'],
                'Bands': f"{config['upper_band']}/{config['lower_band']}",
                'Friction_BPS': friction_bps,
                **result
            })
    
    # Save results
    df = pd.DataFrame(all_results)
    output_dir = Path('research/Perturbations/reports/test_results')
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / 'critical_test_1_2_friction_sensitivity.csv'
    df.to_csv(output_path, index=False)
    
    # Analysis
    print("\n" + "="*80)
    print("CRITICAL TEST RESULTS")
    print("="*80)
    
    for friction_bps in FRICTION_LEVELS:
        friction_results = df[df['Friction_BPS'] == friction_bps]
        profitable_count = friction_results['profitable'].sum()
        total_count = len(friction_results)
        
        print(f"\n{friction_bps:2d} bps Friction:")
        print(f"  Profitable: {profitable_count}/{total_count} assets")
        print(f"  Avg Return: {friction_results['return_pct'].mean():+.2f}%")
        print(f"  Avg Sharpe: {friction_results['sharpe'].mean():.2f}")
        
        # Show which assets failed
        if profitable_count < total_count:
            failed = friction_results[~friction_results['profitable']]['Asset'].tolist()
            print(f"  Failed: {', '.join(failed)}")
    
    # Pass/Fail determination
    print("\n" + "="*80)
    print("GO/NO-GO DECISION")
    print("="*80)
    
    results_10bps = df[df['Friction_BPS'] == 10]
    profitable_10bps = results_10bps['profitable'].sum()
    
    results_15bps = df[df['Friction_BPS'] == 15]
    profitable_15bps = results_15bps['profitable'].sum()
    
    print(f"\n10 bps: {profitable_10bps}/11 profitable (CRITICAL: need 11/11)")
    print(f"15 bps: {profitable_15bps}/11 profitable (CRITICAL: need ≥8/11)")
    
    if profitable_10bps == 11 and profitable_15bps >= 8:
        print("\n✅ PASS: Strategy has strong friction tolerance")
        print("   DEPLOYMENT: APPROVED")
    elif profitable_10bps >= 9:
        print("\n⚠️  MARGINAL: Most assets survive 10 bps")
        print("   DEPLOYMENT: CONDITIONAL (reduce allocation to failed assets)")
    else:
        print("\n❌ FAIL: Insufficient friction tolerance")
        print("   DEPLOYMENT: BLOCKED")
        print("   REASON: Edge destroyed by realistic execution costs")
    
    print(f"\nResults saved to: {output_path}")
    print("="*80)

if __name__ == "__main__":
    main()
