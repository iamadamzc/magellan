"""
Hourly Swing Extended Test - 2020-2024 RVOL Filter Validation

Tests RVOL enhancement across 5 years to validate December 2024 findings
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

# Test periods (5 years)
TEST_PERIODS = [
    ('2020-01-01', '2020-12-31'),
    ('2021-01-01', '2021-12-31'),
    ('2022-01-01', '2022-12-31'),
    ('2023-01-01', '2023-12-31'),
    ('2024-01-01', '2024-12-31'),
]

SYMBOLS = ['TSLA', 'NVDA']

CONFIGS = {
    "TSLA": {"rsi_period": 14, "upper_band": 60, "lower_band": 40},
    "NVDA": {"rsi_period": 28, "upper_band": 55, "lower_band": 45},
}

def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)
    avg_gain = gains.ewm(span=period, adjust=False).mean()
    avg_loss = losses.ewm(span=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.inf)
    rsi = 100 - (100 / (1 + rs))
    return rsi.replace([np.inf, -np.inf], np.nan).fillna(50)

def run_backtest(symbol, config, start, end, use_rvol_filter=False, min_rvol=1.5):
    try:
        lookback_start = pd.to_datetime(start) - pd.Timedelta(days=60)
        df = cache.get_or_fetch_equity(symbol, '1hour', lookback_start.strftime('%Y-%m-%d'), end)
        
        if df is None or len(df) < 100:
            return None
        
        df['rsi'] = calculate_rsi(df['close'], period=config['rsi_period'])
        df['avg_volume'] = df['volume'].rolling(20).mean()
        df['rvol'] = df['volume'] / df['avg_volume']
        
        position = 0
        signals = []
        
        for i in range(len(df)):
            rsi_val = df['rsi'].iloc[i]
            rvol_val = df['rvol'].iloc[i]
            
            if pd.isna(rsi_val) or pd.isna(rvol_val):
                signals.append(position)
                continue
            
            if position == 0:
                if rsi_val > config['upper_band']:
                    if not use_rvol_filter:
                        position = 1
                    elif rvol_val >= min_rvol:
                        position = 1
            elif position == 1:
                if rsi_val < config['lower_band']:
                    position = 0
            
            signals.append(position)
        
        df['signal'] = signals
        df['returns'] = df['close'].pct_change()
        df['strategy_returns'] = df['signal'].shift(1) * df['returns']
        
        df_test = df[df.index >= start].copy()
        
        trades = (df_test['signal'].diff() != 0).sum()
        friction = trades * 0.0005
        total_return = (1 + df_test['strategy_returns']).prod() - 1 - friction
        
        winning_bars = (df_test['strategy_returns'] > 0).sum()
        total_bars_in_market = (df_test['signal'] > 0).sum()
        win_rate = (winning_bars / total_bars_in_market * 100) if total_bars_in_market > 0 else 0
        
        if df_test['strategy_returns'].std() > 0:
            sharpe = (df_test['strategy_returns'].mean() / df_test['strategy_returns'].std()) * np.sqrt(1638)
        else:
            sharpe = 0
        
        cum_returns = (1 + df_test['strategy_returns']).cumprod()
        running_max = cum_returns.expanding().max()
        drawdown = (cum_returns - running_max) / running_max
        max_dd = drawdown.min() * 100
        
        return {
            'symbol': symbol,
            'year': start[:4],
            'return_pct': total_return * 100,
            'trades': int(trades),
            'win_rate': win_rate,
            'sharpe': sharpe,
            'max_dd': max_dd,
        }
        
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    print("="*80)
    print("HOURLY SWING - EXTENDED VALIDATION (2020-2024)")
    print("="*80)
    print("Testing RVOL filter across 5 years\n")
    
    all_results = []
    
    for symbol in SYMBOLS:
        config = CONFIGS[symbol]
        print(f"\n{'='*80}")
        print(f"{symbol} - RSI-{config['rsi_period']}, Bands {config['upper_band']}/{config['lower_band']}")
        print(f"{'='*80}")
        
        for start, end in TEST_PERIODS:
            year = start[:4]
            print(f"\n{year}:")
            
            # Baseline
            baseline = run_backtest(symbol, config, start, end, use_rvol_filter=False)
            if baseline:
                print(f"  Baseline: {baseline['return_pct']:+6.2f}% | {baseline['trades']:2d} trades | Sharpe {baseline['sharpe']:+.2f}")
                baseline['version'] = 'baseline'
                all_results.append(baseline)
            
            # Enhanced
            enhanced = run_backtest(symbol, config, start, end, use_rvol_filter=True, min_rvol=1.5)
            if enhanced:
                print(f"  Enhanced: {enhanced['return_pct']:+6.2f}% | {enhanced['trades']:2d} trades | Sharpe {enhanced['sharpe']:+.2f}")
                enhanced['version'] = 'enhanced'
                all_results.append(enhanced)
            
            if baseline and enhanced:
                delta_return = enhanced['return_pct'] - baseline['return_pct']
                delta_sharpe = enhanced['sharpe'] - baseline['sharpe']
                print(f"  Delta:    {delta_return:+6.2f}% | Sharpe Δ {delta_sharpe:+.2f}")
    
    # Save results
    if all_results:
        df = pd.DataFrame(all_results)
        output_path = Path('research/strategy_enhancements_v2/results/hourly_swing_extended_2020_2024.csv')
        df.to_csv(output_path, index=False)
        
        print(f"\n{'='*80}")
        print("SUMMARY - 5 YEAR RESULTS")
        print(f"{'='*80}\n")
        
        for symbol in SYMBOLS:
            symbol_data = df[df['symbol'] == symbol]
            
            baseline_avg = symbol_data[symbol_data['version'] == 'baseline']['return_pct'].mean()
            enhanced_avg = symbol_data[symbol_data['version'] == 'enhanced']['return_pct'].mean()
            
            baseline_sharpe = symbol_data[symbol_data['version'] == 'baseline']['sharpe'].mean()
            enhanced_sharpe = symbol_data[symbol_data['version'] == 'enhanced']['sharpe'].mean()
            
            print(f"{symbol}:")
            print(f"  Baseline: {baseline_avg:+.2f}% avg return | Sharpe {baseline_sharpe:+.2f}")
            print(f"  Enhanced: {enhanced_avg:+.2f}% avg return | Sharpe {enhanced_sharpe:+.2f}")
            print(f"  Improvement: {enhanced_avg - baseline_avg:+.2f}% | Sharpe Δ {enhanced_sharpe - baseline_sharpe:+.2f}\n")
        
        print(f"✓ Full results saved to: {output_path}")
    
    print("="*80)

if __name__ == "__main__":
    main()
