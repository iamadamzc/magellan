"""
Phase 3: Walk-Forward Analysis for Premium Selling Strategy

Purpose: Validate parameter robustness across multiple time periods and regimes.
Does NOT modify Phase 2 validated results.

Methodology:
1. Rolling 6-month train/test windows (2020-2025)
2. Parameter grid optimization on each training window
3. Out-of-sample testing on each test window
4. Analysis of parameter stability and regime dependence

Expected Runtime: 10-15 minutes
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from itertools import product
import json

project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_handler import AlpacaDataClient
from src.features import calculate_rsi
from src.options.features import OptionsFeatureEngineer

print("="*80)
print("PHASE 3: WALK-FORWARD ANALYSIS - PREMIUM SELLING STRATEGY")
print("="*80)
print("\nObjective: Validate parameter robustness across time periods and regimes")
print("Baseline (Phase 2): RSI 30/70, 60% profit target, 21 DTE exit, -150% stop\n")

# ============================================================================
# CONFIGURATION
# ============================================================================

# Parameter grid to test
PARAM_GRID = {
    'rsi_oversold': [25, 30, 35],
    'rsi_overbought': [65, 70, 75],
    'profit_target_pct': [50, 60, 70],
    'time_exit_dte': [14, 21, 28],
    'stop_loss_pct': [-100, -150, -200]
}

# Walk-forward windows (6-month train, 6-month test)
WFA_WINDOWS = [
    {'name': 'W1', 'train': ('2020-01-01', '2020-06-30'), 'test': ('2020-07-01', '2020-12-31')},
    {'name': 'W2', 'train': ('2020-07-01', '2020-12-31'), 'test': ('2021-01-01', '2021-06-30')},
    {'name': 'W3', 'train': ('2021-01-01', '2021-06-30'), 'test': ('2021-07-01', '2021-12-31')},
    {'name': 'W4', 'train': ('2021-07-01', '2021-12-31'), 'test': ('2022-01-01', '2022-06-30')},
    {'name': 'W5', 'train': ('2022-01-01', '2022-06-30'), 'test': ('2022-07-01', '2022-12-31')},
    {'name': 'W6', 'train': ('2022-07-01', '2022-12-31'), 'test': ('2023-01-01', '2023-06-30')},
    {'name': 'W7', 'train': ('2023-01-01', '2023-06-30'), 'test': ('2023-07-01', '2023-12-31')},
    {'name': 'W8', 'train': ('2023-07-01', '2023-12-31'), 'test': ('2024-01-01', '2024-06-30')},
    {'name': 'W9', 'train': ('2024-01-01', '2024-06-30'), 'test': ('2024-07-01', '2024-12-31')},
    {'name': 'W10', 'train': ('2024-07-01', '2024-12-31'), 'test': ('2025-01-01', '2025-06-30')},
]

# Constants
INITIAL_CAPITAL = 100000
TARGET_NOTIONAL = 10000
SLIPPAGE_PCT = 1.0
CONTRACT_FEE = 0.097
RISK_FREE_RATE = 0.04
IMPLIED_VOL = 0.20  # SPY IV

print(f"Parameter Grid:")
print(f"  RSI Oversold: {PARAM_GRID['rsi_oversold']}")
print(f"  RSI Overbought: {PARAM_GRID['rsi_overbought']}")
print(f"  Profit Target: {PARAM_GRID['profit_target_pct']}%")
print(f"  Time Exit: {PARAM_GRID['time_exit_dte']} DTE")
print(f"  Stop Loss: {PARAM_GRID['stop_loss_pct']}%")
print(f"\nTotal Combinations: {len(list(product(*PARAM_GRID.values())))}")
print(f"Windows: {len(WFA_WINDOWS)}\n")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def backtest_premium_selling(df, params):
    """
    Run premium selling backtest with given parameters.
    Returns metrics dict.
    """
    cash = INITIAL_CAPITAL
    position = None
    trades = []
    
    for date, row in df.iterrows():
        price = row['close']
        rsi = row['rsi']
        
        if pd.isna(rsi):
            continue
        
        # Mark-to-market existing position
        if position:
            dte = (position['expiration'] - date).days
            T = max(dte / 365.0, 0.001)
            
            greeks = OptionsFeatureEngineer.calculate_black_scholes_greeks(
                S=price, K=position['strike'], T=T, r=RISK_FREE_RATE,
                sigma=IMPLIED_VOL, option_type=position['type']
            )
            
            current_price = greeks['price']
            unrealized_pnl = position['premium_collected'] - (current_price * position['contracts'] * 100)
            unrealized_pnl_pct = (unrealized_pnl / position['premium_collected']) * 100
            
            # Exit conditions
            should_exit = False
            exit_reason = None
            
            if unrealized_pnl_pct >= params['profit_target_pct']:
                should_exit, exit_reason = True, 'PROFIT_TARGET'
            elif dte <= params['time_exit_dte']:
                should_exit, exit_reason = True, 'TIME_EXIT'
            elif unrealized_pnl_pct <= params['stop_loss_pct']:
                should_exit, exit_reason = True, 'STOP_LOSS'
            
            if should_exit:
                buyback_cost = current_price * position['contracts'] * 100 * (1 + SLIPPAGE_PCT/100)
                fees = CONTRACT_FEE * position['contracts']
                total_cost = buyback_cost + fees
                
                final_pnl = position['premium_collected'] - total_cost
                
                trades.append({
                    'pnl': final_pnl,
                    'pnl_pct': (final_pnl / position['premium_collected']) * 100,
                    'reason': exit_reason
                })
                
                cash += final_pnl
                position = None
        
        # Enter new position
        if position is None and ((rsi < params['rsi_oversold']) or (rsi > params['rsi_overbought'])):
            option_type = 'put' if rsi < params['rsi_oversold'] else 'call'
            strike = round(price / 5) * 5
            expiration = date + timedelta(days=45)
            T = 45 / 365.0
            
            greeks = OptionsFeatureEngineer.calculate_black_scholes_greeks(
                S=price, K=strike, T=T, r=RISK_FREE_RATE,
                sigma=IMPLIED_VOL, option_type=option_type
            )
            
            sell_price = greeks['price'] * (1 - SLIPPAGE_PCT/100)
            contracts = max(1, int(TARGET_NOTIONAL / (price * abs(greeks['delta']))))
            
            premium_collected = sell_price * contracts * 100
            fees = CONTRACT_FEE * contracts
            net_premium = premium_collected - fees
            
            if net_premium > 0 and net_premium < cash:
                position = {
                    'type': option_type,
                    'strike': strike,
                    'expiration': expiration,
                    'contracts': contracts,
                    'premium_collected': net_premium
                }
                cash += net_premium
    
    # Calculate metrics
    if len(trades) == 0:
        return None
    
    trades_df = pd.DataFrame(trades)
    total_return = (cash / INITIAL_CAPITAL - 1) * 100
    win_rate = (trades_df['pnl'] > 0).mean() * 100
    
    # Sharpe (simplified - using trade returns)
    trade_returns = trades_df['pnl_pct'] / 100
    sharpe = (trade_returns.mean() / trade_returns.std() * np.sqrt(len(trades))) if trade_returns.std() > 0 else 0
    
    return {
        'total_return': total_return,
        'sharpe': sharpe,
        'win_rate': win_rate,
        'num_trades': len(trades),
        'avg_win': trades_df[trades_df['pnl'] > 0]['pnl_pct'].mean() if (trades_df['pnl'] > 0).any() else 0,
        'avg_loss': trades_df[trades_df['pnl'] < 0]['pnl_pct'].mean() if (trades_df['pnl'] < 0).any() else 0
    }

# ============================================================================
# MAIN WFA LOOP
# ============================================================================

print("[1/3] Fetching SPY data (2020-2025)...")
alpaca = AlpacaDataClient()
full_data = alpaca.fetch_historical_bars('SPY', '1Day', '2020-01-01', '2025-12-31')
full_data['rsi'] = calculate_rsi(full_data['close'], period=21)
print(f"✓ Fetched {len(full_data)} bars\n")

print("[2/3] Running Walk-Forward Analysis...")
print("This will take 10-15 minutes...\n")

all_results = []
window_best_params = []

for window in WFA_WINDOWS:
    print(f"\n{'='*80}")
    print(f"Window {window['name']}: Train {window['train'][0]} to {window['train'][1]}")
    print(f"                Test {window['test'][0]} to {window['test'][1]}")
    print(f"{'='*80}")
    
    # Split data
    train_data = full_data[(full_data.index >= window['train'][0]) & (full_data.index <= window['train'][1])]
    test_data = full_data[(full_data.index >= window['test'][0]) & (full_data.index <= window['test'][1])]
    
    print(f"Train: {len(train_data)} bars, Test: {len(test_data)} bars")
    
    # Optimize on training data
    print(f"\nOptimizing {len(list(product(*PARAM_GRID.values())))} parameter combinations...")
    
    best_sharpe = -999
    best_params = None
    
    for combo in product(*PARAM_GRID.values()):
        params = {
            'rsi_oversold': combo[0],
            'rsi_overbought': combo[1],
            'profit_target_pct': combo[2],
            'time_exit_dte': combo[3],
            'stop_loss_pct': combo[4]
        }
        
        metrics = backtest_premium_selling(train_data, params)
        
        if metrics and metrics['sharpe'] > best_sharpe:
            best_sharpe = metrics['sharpe']
            best_params = params.copy()
    
    print(f"✓ Best in-sample Sharpe: {best_sharpe:.2f}")
    print(f"  Params: RSI {best_params['rsi_oversold']}/{best_params['rsi_overbought']}, "
          f"Target {best_params['profit_target_pct']}%, "
          f"Exit {best_params['time_exit_dte']} DTE, "
          f"Stop {best_params['stop_loss_pct']}%")
    
    # Test on out-of-sample data
    oos_metrics = backtest_premium_selling(test_data, best_params)
    
    if oos_metrics:
        print(f"✓ Out-of-sample Sharpe: {oos_metrics['sharpe']:.2f}")
        print(f"  Return: {oos_metrics['total_return']:+.2f}%, Win Rate: {oos_metrics['win_rate']:.1f}%")
        
        all_results.append({
            'window': window['name'],
            'train_start': window['train'][0],
            'train_end': window['train'][1],
            'test_start': window['test'][0],
            'test_end': window['test'][1],
            **{f'param_{k}': v for k, v in best_params.items()},
            **{f'oos_{k}': v for k, v in oos_metrics.items()}
        })
        
        window_best_params.append(best_params)
    else:
        print(f"⚠️  No trades in out-of-sample period")

# ============================================================================
# ANALYSIS
# ============================================================================

print(f"\n\n{'='*80}")
print("[3/3] WALK-FORWARD ANALYSIS RESULTS")
print(f"{'='*80}\n")

results_df = pd.DataFrame(all_results)

# Overall performance
print("📊 Out-of-Sample Performance Summary:")
print(f"  Average Sharpe: {results_df['oos_sharpe'].mean():.2f}")
print(f"  Average Return: {results_df['oos_total_return'].mean():+.2f}%")
print(f"  Average Win Rate: {results_df['oos_win_rate'].mean():.1f}%")
print(f"  Average Trades/Window: {results_df['oos_num_trades'].mean():.1f}")

# Parameter stability
print(f"\n📈 Parameter Stability:")
param_cols = [c for c in results_df.columns if c.startswith('param_')]
for col in param_cols:
    param_name = col.replace('param_', '')
    unique_values = results_df[col].unique()
    most_common = results_df[col].mode()[0] if len(results_df[col].mode()) > 0 else None
    print(f"  {param_name}: {unique_values} (Most common: {most_common})")

# Baseline comparison (Phase 2: RSI 30/70, 60% target, 21 DTE, -150% stop)
baseline_params = {
    'rsi_oversold': 30,
    'rsi_overbought': 70,
    'profit_target_pct': 60,
    'time_exit_dte': 21,
    'stop_loss_pct': -150
}

print(f"\n🎯 Baseline (Phase 2) Comparison:")
print(f"  Baseline Params: RSI 30/70, 60% target, 21 DTE, -150% stop")
print(f"  Baseline Sharpe (2024-2025): 2.26")
print(f"  WFA Average Sharpe (2020-2025): {results_df['oos_sharpe'].mean():.2f}")

# Save results
output_dir = Path('research/backtests/options/phase3_walk_forward/wfa_results')
output_dir.mkdir(parents=True, exist_ok=True)

results_df.to_csv(output_dir / 'wfa_detailed_results.csv', index=False)

summary = {
    'avg_oos_sharpe': float(results_df['oos_sharpe'].mean()),
    'avg_oos_return': float(results_df['oos_total_return'].mean()),
    'avg_oos_win_rate': float(results_df['oos_win_rate'].mean()),
    'baseline_sharpe': 2.26,
    'baseline_params': baseline_params,
    'most_common_params': {
        'rsi_oversold': int(results_df['param_rsi_oversold'].mode()[0]),
        'rsi_overbought': int(results_df['param_rsi_overbought'].mode()[0]),
        'profit_target_pct': int(results_df['param_profit_target_pct'].mode()[0]),
        'time_exit_dte': int(results_df['param_time_exit_dte'].mode()[0]),
        'stop_loss_pct': int(results_df['param_stop_loss_pct'].mode()[0])
    }
}

with open(output_dir / 'wfa_summary.json', 'w') as f:
    json.dump(summary, f, indent=2)

print(f"\n📁 Results saved to: {output_dir}/")
print(f"  - wfa_detailed_results.csv")
print(f"  - wfa_summary.json")

print(f"\n{'='*80}")
print("WALK-FORWARD ANALYSIS COMPLETE")
print(f"{'='*80}\n")

# Final recommendation
if results_df['oos_sharpe'].mean() >= 1.5:
    print("✅ RECOMMENDATION: Strategy is ROBUST across time periods")
    print("   Deploy with confidence (baseline or optimized parameters)")
elif results_df['oos_sharpe'].mean() >= 1.0:
    print("⚠️  RECOMMENDATION: Strategy is MODERATELY ROBUST")
    print("   Consider regime filtering or parameter adjustment")
else:
    print("❌ RECOMMENDATION: Strategy is NOT ROBUST")
    print("   Do NOT deploy - requires further research")

print(f"\n{'='*80}\n")
