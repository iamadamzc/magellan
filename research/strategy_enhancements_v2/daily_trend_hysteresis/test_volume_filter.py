"""
Daily Trend Hysteresis - Volume Filter Enhancement Test
Tests if adding volume confirmation improves strategy performance
"""
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Go up to project root (3 levels: daily_trend_hysteresis -> strategy_enhancements_v2 -> research -> root)
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_cache import cache

# Test configuration
TEST_START = '2024-12-01'
TEST_END = '2024-12-31'
LOOKBACK_START = '2024-10-01'  # For indicator warmup

# Symbols to test
SYMBOLS = ['SPY', 'QQQ', 'IWM', 'GLD']

# Baseline configs (from validated strategy)
CONFIGS = {
    "SPY": {"rsi_period": 21, "upper_band": 58, "lower_band": 42},
    "QQQ": {"rsi_period": 21, "upper_band": 60, "lower_band": 40},
    "IWM": {"rsi_period": 28, "upper_band": 65, "lower_band": 35},
    "GLD": {"rsi_period": 21, "upper_band": 65, "lower_band": 35},
}

def calculate_rsi(prices, period=21):
    """Calculate RSI indicator"""
    delta = prices.diff()
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)
    avg_gain = gains.ewm(span=period, adjust=False).mean()
    avg_loss = losses.ewm(span=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.inf)
    rsi = 100 - (100 / (1 + rs))
    return rsi.replace([np.inf, -np.inf], np.nan).fillna(50)

def run_backtest(symbol, config, use_volume_filter=False, min_volume_ratio=1.2):
    """
    Run Daily Trend backtest with optional volume filter
    
    Args:
        symbol: Stock symbol
        config: RSI configuration
        use_volume_filter: If True, apply volume filter
        min_volume_ratio: Minimum volume ratio for BUY signals (e.g., 1.2 = 120% of average)
    
    Returns:
        Dict with performance metrics
    """
    try:
        # Fetch data with lookback
        df = cache.get_or_fetch_equity(symbol, '1day', LOOKBACK_START, TEST_END)
        if df is None or len(df) < 30:
            return None
        
        # Calculate RSI
        df['rsi'] = calculate_rsi(df['close'], period=config['rsi_period'])
        
        # Calculate volume metrics (for enhanced version)
        df['avg_volume'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['avg_volume']
        
        # Generate signals with RSI Hysteresis
        position = 0
        signals = []
        
        for i in range(len(df)):
            rsi_val = df['rsi'].iloc[i]
            vol_ratio = df['volume_ratio'].iloc[i]
            
            if pd.isna(rsi_val) or pd.isna(vol_ratio):
                signals.append(position)
                continue
            
            # Entry logic
            if position == 0:
                if rsi_val > config['upper_band']:
                    # Volume filter (if enabled)
                    if not use_volume_filter:
                        position = 1  # BUY (baseline)
                    elif vol_ratio >= min_volume_ratio:
                        position = 1  # BUY (enhanced - with volume confirmation)
                    # else: skip low-volume signal
            
            # Exit logic (no volume filter needed for exits)
            elif position == 1:
                if rsi_val < config['lower_band']:
                    position = 0  # SELL
            
            signals.append(position)
        
        df['signal'] = signals
        df['returns'] = df['close'].pct_change()
        df['strategy_returns'] = df['signal'].shift(1) * df['returns']
        
        # Filter to test period only
        df_test = df[df.index >= TEST_START].copy()
        
        # Calculate metrics
        trades = (df_test['signal'].diff() != 0).sum()
        friction = trades * 0.001  # 10 bps per trade
        total_return = (1 + df_test['strategy_returns']).prod() - 1 - friction
        
        # Win rate
        winning_days = (df_test['strategy_returns'] > 0).sum()
        total_days_in_market = (df_test['signal'] > 0).sum()
        win_rate = (winning_days / total_days_in_market * 100) if total_days_in_market > 0 else 0
        
        # Sharpe ratio
        if df_test['strategy_returns'].std() > 0:
            sharpe = (df_test['strategy_returns'].mean() / df_test['strategy_returns'].std()) * np.sqrt(252)
        else:
            sharpe = 0
        
        # Max drawdown
        cum_returns = (1 + df_test['strategy_returns']).cumprod()
        running_max = cum_returns.expanding().max()
        drawdown = (cum_returns - running_max) / running_max
        max_dd = drawdown.min() * 100
        
        return {
            'symbol': symbol,
            'return_pct': total_return * 100,
            'trades': int(trades),
            'win_rate': win_rate,
            'sharpe': sharpe,
            'max_dd': max_dd,
            'days_in_market': int(total_days_in_market),
            'total_days': len(df_test)
        }
        
    except Exception as e:
        print(f"Error testing {symbol}: {e}")
        return None

def main():
    print("="*80)
    print("DAILY TREND HYSTERESIS - VOLUME FILTER ENHANCEMENT TEST")
    print("="*80)
    print(f"Test Period: {TEST_START} to {TEST_END}")
    print(f"Lookback for Indicators: {LOOKBACK_START}\n")
    
    baseline_results = []
    enhanced_results = []
    
    for symbol in SYMBOLS:
        config = CONFIGS[symbol]
        
        print(f"\n{'='*80}")
        print(f"Testing {symbol}")
        print(f"Config: RSI-{config['rsi_period']}, Bands {config['upper_band']}/{config['lower_band']}")
        print(f"{'='*80}")
        
        # Baseline (no volume filter)
        print("\n[BASELINE] RSI Only:")
        baseline = run_backtest(symbol, config, use_volume_filter=False)
        if baseline:
            print(f"  Return: {baseline['return_pct']:+.2f}%")
            print(f"  Trades: {baseline['trades']}")
            print(f"  Win Rate: {baseline['win_rate']:.1f}%")
            print(f"  Sharpe: {baseline['sharpe']:.2f}")
            print(f"  Max DD: {baseline['max_dd']:.2f}%")
            baseline_results.append(baseline)
        
        # Enhanced (with volume filter 1.2x)
        print("\n[ENHANCED] RSI + Volume Filter (1.2x):")
        enhanced = run_backtest(symbol, config, use_volume_filter=True, min_volume_ratio=1.2)
        if enhanced:
            print(f"  Return: {enhanced['return_pct']:+.2f}%")
            print(f"  Trades: {enhanced['trades']}")
            print(f"  Win Rate: {enhanced['win_rate']:.1f}%")
            print(f"  Sharpe: {enhanced['sharpe']:.2f}")
            print(f"  Max DD: {enhanced['max_dd']:.2f}%")
            enhanced_results.append(enhanced)
        
        # Comparison
        if baseline and enhanced:
            print("\n[COMPARISON] Enhanced vs Baseline:")
            print(f"  Return Δ: {enhanced['return_pct'] - baseline['return_pct']:+.2f}%")
            print(f"  Trades Δ: {enhanced['trades'] - baseline['trades']:+d}")
            print(f"  Win Rate Δ: {enhanced['win_rate'] - baseline['win_rate']:+.1f}%")
            print(f"  Sharpe Δ: {enhanced['sharpe'] - baseline['sharpe']:+.2f}")
    
    # Summary
    print("\n" + "="*80)
    print("PORTFOLIO SUMMARY")
    print("="*80)
    
    if baseline_results:
        df_baseline = pd.DataFrame(baseline_results)
        print("\n[BASELINE] Portfolio:")
        print(df_baseline[['symbol', 'return_pct', 'trades', 'win_rate', 'sharpe']].to_string(index=False))
        print(f"\nAverage Return: {df_baseline['return_pct'].mean():+.2f}%")
        print(f"Total Trades: {df_baseline['trades'].sum()}")
        print(f"Average Sharpe: {df_baseline['sharpe'].mean():.2f}")
    
    if enhanced_results:
        df_enhanced = pd.DataFrame(enhanced_results)
        print("\n[ENHANCED] Portfolio:")
        print(df_enhanced[['symbol', 'return_pct', 'trades', 'win_rate', 'sharpe']].to_string(index=False))
        print(f"\nAverage Return: {df_enhanced['return_pct'].mean():+.2f}%")
        print(f"Total Trades: {df_enhanced['trades'].sum()}")
        print(f"Average Sharpe: {df_enhanced['sharpe'].mean():.2f}")
    
    # Save results
    if baseline_results and enhanced_results:
        df_baseline['version'] = 'baseline'
        df_enhanced['version'] = 'enhanced'
        df_all = pd.concat([pd.DataFrame(baseline_results), pd.DataFrame(enhanced_results)])
        
        output_path = Path('research/strategy_enhancements_v2/results/daily_trend_volume_test.csv')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_all.to_csv(output_path, index=False)
        print(f"\n✓ Results saved to: {output_path}")
    
    print("="*80)

if __name__ == "__main__":
    main()
