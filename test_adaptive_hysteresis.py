"""
Daily Trend Hysteresis Optimization Suite (Backlog Items 1-3)

Implements:
1. Adaptive Thresholds: Adjust based on volatility (ATR)
2. Asymmetric Bands: Test 52/48 vs 55/45
3. Baseline Comparison: Verify cost of whipsaw savings

Author: Antigravity
Date: 2026-01-14
"""

import sys
import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load .env file
def load_env_file():
    """Manually load .env file into os.environ."""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

load_env_file()

from src.data_handler import AlpacaDataClient
from src.features import calculate_rsi


# =============================================================================
# CONFIGURATION
# =============================================================================

# Test Parameters
SYMBOL = 'SPY'
START_DATE = '2024-01-14'
END_DATE = '2026-01-14'
INITIAL_CAPITAL = 50000.0
POSITION_SIZE_PCT = 1.0
TRANSACTION_COST_BPS = 1.5  # 1.5 basis points per trade

# Hysteresis Configurations to Test
CONFIGS = {
    'baseline': {
        'name': 'Baseline (No Hysteresis)',
        'mode': 'baseline',
        'description': 'Simple RSI > 50 threshold (whipsaw expected)'
    },
    'variant_f': {
        'name': 'Variant F (Fixed 55/45)',
        'mode': 'fixed',
        'upper': 55,
        'lower': 45,
        'description': 'Original fixed symmetric bands'
    },
    'asymmetric_52_48': {
        'name': 'Asymmetric 52/48',
        'mode': 'fixed',
        'upper': 52,
        'lower': 48,
        'description': 'Tighter bands for more market participation'
    },
    'asymmetric_55_48': {
        'name': 'Asymmetric 55/48',
        'mode': 'fixed',
        'upper': 55,
        'lower': 48,
        'description': 'Conservative entry, faster exit'
    },
    'adaptive_atr': {
        'name': 'Adaptive ATR-Based',
        'mode': 'adaptive',
        'base_upper': 55,
        'base_lower': 45,
        'description': 'Dynamic thresholds based on market volatility (ATR)'
    }
}


# =============================================================================
# CORE FUNCTIONS
# =============================================================================

def calculate_atr(df, period=14):
    """
    Calculate Average True Range (ATR) for volatility measurement.
    
    Args:
        df: DataFrame with 'high', 'low', 'close' columns
        period: ATR smoothing period (default 14)
    
    Returns:
        Series of ATR values
    """
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(window=period, min_periods=1).mean()
    
    return atr


def calculate_adaptive_thresholds(df, base_upper=55, base_lower=45, atr_period=14, atr_lookback=20):
    """
    Calculate adaptive upper/lower thresholds based on ATR volatility regime.
    
    Logic:
    - High Volatility (ATR > 1.5x rolling avg): Widen bands (60/40) to reduce whipsaw
    - Normal Volatility (0.75x < ATR < 1.5x): Use base bands
    - Low Volatility (ATR < 0.75x): Tighten bands (52/48) for better participation
    
    Args:
        df: DataFrame with OHLC data
        base_upper: Base upper threshold (default 55)
        base_lower: Base lower threshold (default 45)
        atr_period: ATR calculation period
        atr_lookback: Rolling window for ATR average
    
    Returns:
        DataFrame with 'upper_threshold' and 'lower_threshold' columns
    """
    df = df.copy()
    
    # Calculate ATR
    df['atr'] = calculate_atr(df, period=atr_period)
    
    # Calculate rolling ATR average (regime baseline)
    df['atr_avg'] = df['atr'].rolling(window=atr_lookback, min_periods=1).mean()
    
    # Calculate volatility ratio
    df['vol_ratio'] = df['atr'] / df['atr_avg']
    
    # Initialize threshold arrays
    upper_thresholds = np.zeros(len(df))
    lower_thresholds = np.zeros(len(df))
    
    for i in range(len(df)):
        vol_ratio = df['vol_ratio'].iloc[i]
        
        if vol_ratio > 1.5:
            # High volatility: Widen bands
            upper_thresholds[i] = 60
            lower_thresholds[i] = 40
        elif vol_ratio < 0.75:
            # Low volatility: Tighten bands
            upper_thresholds[i] = 52
            lower_thresholds[i] = 48
        else:
            # Normal volatility: Use base bands
            upper_thresholds[i] = base_upper
            lower_thresholds[i] = base_lower
    
    df['upper_threshold'] = upper_thresholds
    df['lower_threshold'] = lower_thresholds
    
    return df


def generate_signals(df, config):
    """
    Generate trading signals based on configuration.
    
    Args:
        df: DataFrame with 'rsi_14' column
        config: Configuration dictionary
    
    Returns:
        DataFrame with 'signal' column (0 = FLAT, 1 = LONG)
    """
    df = df.copy()
    
    mode = config['mode']
    
    if mode == 'baseline':
        # Simple threshold at RSI 50 (no hysteresis)
        df['signal'] = np.where(df['rsi_14'] > 50, 1, 0)
    
    elif mode == 'fixed':
        # Fixed hysteresis bands
        upper = config['upper']
        lower = config['lower']
        
        position_state = np.zeros(len(df))
        current_state = 0
        
        for i, (idx, row) in enumerate(df.iterrows()):
            rsi_value = row['rsi_14']
            
            if current_state == 0:  # FLAT
                if rsi_value > upper:
                    current_state = 1
            elif current_state == 1:  # LONG
                if rsi_value < lower:
                    current_state = 0
            
            position_state[i] = current_state
        
        df['signal'] = position_state
    
    elif mode == 'adaptive':
        # Adaptive ATR-based thresholds
        df = calculate_adaptive_thresholds(
            df,
            base_upper=config['base_upper'],
            base_lower=config['base_lower']
        )
        
        position_state = np.zeros(len(df))
        current_state = 0
        
        for i, (idx, row) in enumerate(df.iterrows()):
            rsi_value = row['rsi_14']
            upper = row['upper_threshold']
            lower = row['lower_threshold']
            
            if current_state == 0:  # FLAT
                if rsi_value > upper:
                    current_state = 1
            elif current_state == 1:  # LONG
                if rsi_value < lower:
                    current_state = 0
            
            position_state[i] = current_state
        
        df['signal'] = position_state
    
    return df


def calculate_performance_metrics(df, initial_capital, transaction_cost_bps):
    """
    Calculate comprehensive performance metrics.
    
    Args:
        df: DataFrame with 'signal' and 'close' columns
        initial_capital: Starting capital
        transaction_cost_bps: Transaction cost in basis points
    
    Returns:
        Dictionary of performance metrics
    """
    df = df.copy()
    
    # Calculate returns
    df['daily_return'] = df['close'].pct_change()
    df['strategy_return'] = df['signal'].shift(1) * df['daily_return']
    
    # Apply transaction costs
    df['signal_change'] = df['signal'].diff().fillna(0)
    df['trade_cost'] = 0.0
    df.loc[df['signal_change'] != 0, 'trade_cost'] = transaction_cost_bps / 10000.0
    df['strategy_return_net'] = df['strategy_return'] - df['trade_cost']
    
    # Calculate equity curves
    df['equity'] = initial_capital * (1 + df['strategy_return_net']).cumprod()
    df['buy_hold_equity'] = initial_capital * (1 + df['daily_return']).cumprod()
    
    # Final returns
    final_equity = df['equity'].iloc[-1]
    final_buy_hold = df['buy_hold_equity'].iloc[-1]
    strategy_return = ((final_equity - initial_capital) / initial_capital) * 100
    buy_hold_return = ((final_buy_hold - initial_capital) / initial_capital) * 100
    
    # Max drawdown
    cumulative_max = df['equity'].cummax()
    drawdown = (df['equity'] - cumulative_max) / cumulative_max * 100
    max_drawdown = drawdown.min()
    
    # Sharpe ratio
    daily_returns = df['strategy_return_net'].dropna()
    sharpe_ratio = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252) if daily_returns.std() > 0 else 0
    
    # Trading metrics
    num_trades = (df['signal_change'] != 0).sum()
    total_days_invested = (df['signal'].shift(1) == 1).sum()
    total_cost = (df['trade_cost'] * initial_capital).sum()
    
    # Win rate
    winning_days = (df['strategy_return_net'] > 0).sum()
    win_rate = (winning_days / total_days_invested * 100) if total_days_invested > 0 else 0
    
    return {
        'strategy_return': strategy_return,
        'buy_hold_return': buy_hold_return,
        'outperformance': strategy_return - buy_hold_return,
        'final_equity': final_equity,
        'max_drawdown': max_drawdown,
        'sharpe_ratio': sharpe_ratio,
        'num_trades': num_trades,
        'days_invested': total_days_invested,
        'total_days': len(df),
        'participation_pct': (total_days_invested / len(df)) * 100,
        'win_rate': win_rate,
        'transaction_costs': total_cost,
        'equity_curve': df[['equity', 'buy_hold_equity']].copy()
    }


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    print("=" * 80)
    print("DAILY TREND HYSTERESIS OPTIMIZATION SUITE")
    print("=" * 80)
    print(f"Symbol:  {SYMBOL}")
    print(f"Period:  {START_DATE} to {END_DATE}")
    print(f"Capital: ${INITIAL_CAPITAL:,.2f}")
    print(f"Tests:   {len(CONFIGS)} configurations")
    print("=" * 80)
    
    # Fetch data
    print("\n[1/3] Fetching daily bars from Alpaca...")
    client = AlpacaDataClient()
    bars = client.fetch_historical_bars(
        symbol=SYMBOL,
        timeframe='1Day',
        start=START_DATE,
        end=END_DATE,
        feed='sip'
    )
    print(f"✓ Fetched {len(bars)} daily bars")
    
    # Calculate RSI
    print("\n[2/3] Calculating RSI-14...")
    bars['rsi_14'] = calculate_rsi(bars['close'], period=14)
    bars = bars.dropna()
    print(f"✓ RSI calculated ({len(bars)} bars after warmup)")
    
    # Run all configurations
    print("\n[3/3] Running backtests for all configurations...")
    print("=" * 80)
    
    results = {}
    
    for config_key, config in CONFIGS.items():
        print(f"\nTesting: {config['name']}")
        print(f"  Description: {config['description']}")
        
        # Generate signals
        df = generate_signals(bars.copy(), config)
        
        # Calculate metrics
        metrics = calculate_performance_metrics(df, INITIAL_CAPITAL, TRANSACTION_COST_BPS)
        results[config_key] = metrics
        
        # Print summary
        print(f"  Strategy Return:     {metrics['strategy_return']:+.2f}%")
        print(f"  Max Drawdown:        {metrics['max_drawdown']:.2f}%")
        print(f"  Sharpe Ratio:        {metrics['sharpe_ratio']:.2f}")
        print(f"  Trades:              {metrics['num_trades']}")
        print(f"  Transaction Costs:   ${metrics['transaction_costs']:,.2f}")
    
    print("\n" + "=" * 80)
    print("COMPARATIVE ANALYSIS")
    print("=" * 80)
    
    # Create comparison table
    comparison_df = pd.DataFrame({
        'Configuration': [CONFIGS[k]['name'] for k in results.keys()],
        'Total Return (%)': [results[k]['strategy_return'] for k in results.keys()],
        'vs Buy-Hold (%)': [results[k]['outperformance'] for k in results.keys()],
        'Max DD (%)': [results[k]['max_drawdown'] for k in results.keys()],
        'Sharpe': [results[k]['sharpe_ratio'] for k in results.keys()],
        'Trades': [results[k]['num_trades'] for k in results.keys()],
        'Participation (%)': [results[k]['participation_pct'] for k in results.keys()],
        'TX Costs ($)': [results[k]['transaction_costs'] for k in results.keys()]
    })
    
    print("\n" + comparison_df.to_string(index=False))
    
    # Calculate whipsaw cost (Baseline vs Best Hysteresis)
    print("\n" + "=" * 80)
    print("WHIPSAW COST ANALYSIS")
    print("=" * 80)
    
    baseline = results['baseline']
    variant_f = results['variant_f']
    
    trade_reduction = baseline['num_trades'] - variant_f['num_trades']
    cost_reduction = baseline['transaction_costs'] - variant_f['transaction_costs']
    return_improvement = variant_f['strategy_return'] - baseline['strategy_return']
    
    print(f"\nBaseline (No Hysteresis):")
    print(f"  Trades:              {baseline['num_trades']}")
    print(f"  Transaction Costs:   ${baseline['transaction_costs']:,.2f}")
    print(f"  Net Return:          {baseline['strategy_return']:+.2f}%")
    
    print(f"\nVariant F (Hysteresis 55/45):")
    print(f"  Trades:              {variant_f['num_trades']}")
    print(f"  Transaction Costs:   ${variant_f['transaction_costs']:,.2f}")
    print(f"  Net Return:          {variant_f['strategy_return']:+.2f}%")
    
    print(f"\nWhipsaw Savings:")
    print(f"  Trade Reduction:     {trade_reduction} trades ({trade_reduction/baseline['num_trades']*100:.1f}% reduction)")
    print(f"  Cost Savings:        ${cost_reduction:,.2f}")
    print(f"  Return Impact:       {return_improvement:+.2f}%")
    
    # Identify best configuration
    print("\n" + "=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)
    
    # Rank by risk-adjusted return (combination of return and Sharpe)
    rankings = []
    for key, metrics in results.items():
        if key == 'baseline':
            continue  # Exclude baseline from ranking
        score = (metrics['strategy_return'] * 0.6) + (metrics['sharpe_ratio'] * 10 * 0.4)
        rankings.append((key, score, metrics))
    
    rankings.sort(key=lambda x: x[1], reverse=True)
    
    best_key, best_score, best_metrics = rankings[0]
    
    print(f"\n🏆 BEST CONFIGURATION: {CONFIGS[best_key]['name']}")
    print(f"   {CONFIGS[best_key]['description']}")
    print(f"\n   Total Return:        {best_metrics['strategy_return']:+.2f}%")
    print(f"   vs Buy-Hold:         {best_metrics['outperformance']:+.2f}%")
    print(f"   Max Drawdown:        {best_metrics['max_drawdown']:.2f}%")
    print(f"   Sharpe Ratio:        {best_metrics['sharpe_ratio']:.2f}")
    print(f"   Trades:              {best_metrics['num_trades']}")
    print(f"   Market Participation:{best_metrics['participation_pct']:.1f}%")
    
    # Export results
    print("\n" + "=" * 80)
    print(f"💾 Exporting results...")
    
    comparison_df.to_csv('hysteresis_optimization_results.csv', index=False)
    print(f"   Summary table saved to: hysteresis_optimization_results.csv")
    
    # Export equity curves for each config
    for key, metrics in results.items():
        filename = f"equity_curve_{key}.csv"
        metrics['equity_curve'].to_csv(filename)
        print(f"   Equity curve saved to: {filename}")
    
    print("=" * 80)
    print("✅ OPTIMIZATION SUITE COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    main()
