"""
Hourly Swing Expanded Test - 2022-2025 Multiple Symbols

Tests RVOL enhancement on broader symbol set (post-split era)
Avoids NVDA split issues, adds more validation symbols
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

# Test period (recent, post-COVID)
TEST_PERIODS = [
    ('2022-01-01', '2022-12-31'),
    ('2023-01-01', '2023-12-31'),
    ('2024-01-01', '2024-12-31'),
    ('2025-01-01', '2025-01-18'),  # YTD 2025
]

# Expanded symbol list (high-volume tech stocks)
SYMBOLS = {
    'TSLA': {'rsi_period': 14, 'upper_band': 60, 'lower_band': 40},  # Already tested
    'AAPL': {'rsi_period': 14, 'upper_band': 60, 'lower_band': 40},  # Stable tech
    'MSFT': {'rsi_period': 14, 'upper_band': 60, 'lower_band': 40},  # Stable tech
    'META': {'rsi_period': 14, 'upper_band': 60, 'lower_band': 40},  # Volatile
    'GOOGL': {'rsi_period': 14, 'upper_band': 60, 'lower_band': 40}, # Volatile
    'AMD': {'rsi_period': 14, 'upper_band': 60, 'lower_band': 40},   # Volatile (NVDA replacement)
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
            'period': start[:4] if start[:4] != '2025' else '2025 YTD',
            'return_pct': total_return * 100,
            'trades': int(trades),
            'win_rate': win_rate,
            'sharpe': sharpe,
            'max_dd': max_dd,
        }
        
    except Exception as e:
        print(f"Error {symbol} {start[:4]}: {e}")
        return None

def main():
    print("="*80)
    print("HOURLY SWING - EXPANDED VALIDATION (2022-2025)")
    print("="*80)
    print(f"Symbols: {', '.join(SYMBOLS.keys())}")
    print("Testing RVOL filter across recent years\n")
    
    all_results = []
    
    for symbol, config in SYMBOLS.items():
        print(f"\n{'='*80}")
        print(f"{symbol} - RSI-{config['rsi_period']}, Bands {config['upper_band']}/{config['lower_band']}")
        print(f"{'='*80}")
        
        for start, end in TEST_PERIODS:
            period = start[:4] if start[:4] != '2025' else '2025 YTD'
            print(f"\n{period}:")
            
            # Baseline
            baseline = run_backtest(symbol, config, start, end, use_rvol_filter=False)
            if baseline:
                print(f"  Baseline: {baseline['return_pct']:+6.2f}% | {baseline['trades']:3d} trades | Sharpe {baseline['sharpe']:+.2f}")
                baseline['version'] = 'baseline'
                all_results.append(baseline)
            
            # Enhanced
            enhanced = run_backtest(symbol, config, start, end, use_rvol_filter=True, min_rvol=1.5)
            if enhanced:
                print(f"  Enhanced: {enhanced['return_pct']:+6.2f}% | {enhanced['trades']:3d} trades | Sharpe {enhanced['sharpe']:+.2f}")
                enhanced['version'] = 'enhanced'
                all_results.append(enhanced)
            
            if baseline and enhanced:
                delta_return = enhanced['return_pct'] - baseline['return_pct']
                delta_sharpe = enhanced['sharpe'] - baseline['sharpe']
                print(f"  Delta:    {delta_return:+6.2f}% | Sharpe Δ {delta_sharpe:+.2f}")
    
    # Save results
    if all_results:
        df = pd.DataFrame(all_results)
        output_path = Path('research/strategy_enhancements_v2/results/hourly_swing_expanded_2022_2025.csv')
        df.to_csv(output_path, index=False)
        
        print(f"\n{'='*80}")
        print("SUMMARY - BY SYMBOL (2022-2025 Average)")
        print(f"{'='*80}\n")
        
        summary_rows = []
        
        for symbol in SYMBOLS.keys():
            symbol_data = df[df['symbol'] == symbol]
            
            baseline_avg_return = symbol_data[symbol_data['version'] == 'baseline']['return_pct'].mean()
            enhanced_avg_return = symbol_data[symbol_data['version'] == 'enhanced']['return_pct'].mean()
            
            baseline_avg_sharpe = symbol_data[symbol_data['version'] == 'baseline']['sharpe'].mean()
            enhanced_avg_sharpe = symbol_data[symbol_data['version'] == 'enhanced']['sharpe'].mean()
            
            baseline_trades = symbol_data[symbol_data['version'] == 'baseline']['trades'].sum()
            enhanced_trades = symbol_data[symbol_data['version'] == 'enhanced']['trades'].sum()
            
            sharpe_delta = enhanced_avg_sharpe - baseline_avg_sharpe
            sharpe_pct_change = (sharpe_delta / baseline_avg_sharpe * 100) if baseline_avg_sharpe != 0 else 0
            
            verdict = "✅ DEPLOY" if sharpe_pct_change > 5 else ("❌ SKIP" if sharpe_pct_change < -5 else "⚠️ NEUTRAL")
            
            print(f"{symbol}:")
            print(f"  Baseline: {baseline_avg_return:+6.2f}% return | Sharpe {baseline_avg_sharpe:+.2f} | {baseline_trades} trades")
            print(f"  Enhanced: {enhanced_avg_return:+6.2f}% return | Sharpe {enhanced_avg_sharpe:+.2f} | {enhanced_trades} trades")
            print(f"  Delta:    {enhanced_avg_return - baseline_avg_return:+6.2f}% | Sharpe Δ {sharpe_delta:+.2f} ({sharpe_pct_change:+.1f}%)")
            print(f"  {verdict}\n")
            
            summary_rows.append({
                'symbol': symbol,
                'baseline_sharpe': baseline_avg_sharpe,
                'enhanced_sharpe': enhanced_avg_sharpe,
                'sharpe_delta': sharpe_delta,
                'sharpe_pct_change': sharpe_pct_change,
                'verdict': verdict
            })
        
        # Overall portfolio view
        print(f"{'='*80}")
        print("PORTFOLIO AGGREGATE")
        print(f"{'='*80}\n")
        
        all_baseline = df[df['version'] == 'baseline']
        all_enhanced = df[df['version'] == 'enhanced']
        
        portfolio_baseline_sharpe = all_baseline['sharpe'].mean()
        portfolio_enhanced_sharpe = all_enhanced['sharpe'].mean()
        portfolio_delta = portfolio_enhanced_sharpe - portfolio_baseline_sharpe
        
        print(f"Portfolio Avg Sharpe:")
        print(f"  Baseline: {portfolio_baseline_sharpe:.2f}")
        print(f"  Enhanced: {portfolio_enhanced_sharpe:.2f}")
        print(f"  Delta:    {portfolio_delta:+.2f} ({portfolio_delta/portfolio_baseline_sharpe*100:+.1f}%)")
        
        winners = len([s for s in summary_rows if '✅' in s['verdict']])
        losers = len([s for s in summary_rows if '❌' in s['verdict']])
        neutral = len([s for s in summary_rows if '⚠️' in s['verdict']])
        
        print(f"\nScore: {winners} winners, {losers} losers, {neutral} neutral")
        
        if winners > losers:
            print("\n✅ OVERALL: RVOL enhancement is NET POSITIVE")
            print("   Deploy selectively to winners only")
        elif losers > winners:
            print("\n❌ OVERALL: RVOL enhancement is NET NEGATIVE")
            print("   Keep baseline for most symbols")
        else:
            print("\n⚠️ OVERALL: RVOL enhancement is NEUTRAL")
            print("   Deploy conservatively") 
        
        print(f"\n✓ Full results saved to: {output_path}")
    
    print("="*80)

if __name__ == "__main__":
    main()
