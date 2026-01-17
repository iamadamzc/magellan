"""
CORRECTIVE RETEST #2 (REVISED): Strategy 1 - Daily Trend Hysteresis

Purpose: Validate whether Strategy 1 failures were due to:
(a) Execution timing assumptions (look-ahead adjacent)
(b) Insufficient RSI warmup

CHANGES FROM ORIGINAL (2 ONLY):
1. Execution Timing: Signal on close, fill on NEXT OPEN (realistic)
2. RSI Warmup: 84 bars (3× lookback for Wilder smoothing)

UNCHANGED:
- Exit Logic: RSI < 45 (ORIGINAL, not changed to 35)
- Entry Logic: RSI > 55
- All other parameters

This is a CONTROLLED VALIDATION, not exploratory testing.
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Fix project root path
project_root = Path(__file__).resolve().parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))
print(f"Project root: {project_root}")

from dotenv import load_dotenv
load_dotenv()

from src.data_handler import AlpacaDataClient
from alpaca.data.timeframe import TimeFrame

# Configuration - ONLY 2 CHANGES
SYMBOLS = ['AAPL', 'MSFT', 'NVDA', 'META', 'AMZN', 'GOOGL', 'TSLA', 'SPY', 'QQQ']
RSI_PERIOD = 28
RSI_WARMUP = 84  # CHANGE #2: 3× lookback for stability (was 28)
ENTRY_THRESHOLD = 55  # UNCHANGED
EXIT_THRESHOLD = 45  # UNCHANGED (keeping original, NOT 35)
SHARES_PER_TRADE = 100
FRICTION_BASELINE_BPS = 1.5
FRICTION_DEGRADED_BPS = 5.0

TEST_PERIODS = [
    {'name': 'Primary', 'start': '2024-01-01', 'end': '2025-12-31'},
    {'name': 'Secondary', 'start': '2022-01-01', 'end': '2023-12-31'}
]

def calculate_rsi(prices, period=14):
    """Calculate RSI using Wilder's smoothing"""
    delta = prices.diff()
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)
    avg_gain = gains.ewm(span=period, adjust=False).mean()
    avg_loss = losses.ewm(span=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.inf)
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.replace([np.inf, -np.inf], np.nan).fillna(50)
    return rsi

def resample_to_daily(df):
    daily = df.resample('1D').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()
    return daily

def run_backtest_corrected(df, friction_bps):
    """
    CORRECTED BACKTEST with 2 improvements:
    1. Signal on close, fill on next open
    2. 84-bar warmup
    
    UNCHANGED: Exit at RSI < 45 (original)
    """
    
    # Calculate RSI
    df['rsi'] = calculate_rsi(df['close'], period=RSI_PERIOD)
    df['rsi_prev'] = df['rsi'].shift(1)
    df['next_open'] = df['open'].shift(-1)  # CHANGE #1: Next bar open
    
    # Drop warmup period (84 bars)
    df = df.iloc[RSI_WARMUP:].copy()
    
    position = 'flat'
    entry_price = None
    entry_date = None
    trades = []
    equity_curve = []
    initial_capital = 100000
    cash = initial_capital
    
    for idx in range(1, len(df) - 1):  # -1 because we need next_open
        current_date = df.index[idx]
        current_close = df.iloc[idx]['close']
        current_rsi = df.iloc[idx]['rsi']
        prev_rsi = df.iloc[idx]['rsi_prev']
        next_open = df.iloc[idx]['next_open']
        
        if pd.isna(current_rsi) or pd.isna(prev_rsi) or pd.isna(next_open):
            equity_curve.append(cash)
            continue
        
        # ENTRY: Signal on close, execute on NEXT OPEN
        if position == 'flat':
            if prev_rsi <= ENTRY_THRESHOLD and current_rsi > ENTRY_THRESHOLD:
                friction_cost = (friction_bps / 10000) * next_open * SHARES_PER_TRADE
                entry_price = next_open  # CHANGE #1: Next open, not current close
                entry_date = df.index[idx + 1]
                position = 'long'
                cash -= (entry_price * SHARES_PER_TRADE + friction_cost)
        
        # EXIT: Signal on close, execute on NEXT OPEN (ORIGINAL threshold 45)
        elif position == 'long':
            if prev_rsi >= EXIT_THRESHOLD and current_rsi < EXIT_THRESHOLD:
                friction_cost = (friction_bps / 10000) * next_open * SHARES_PER_TRADE
                proceeds = next_open * SHARES_PER_TRADE - friction_cost
                pnl_dollars = proceeds - (entry_price * SHARES_PER_TRADE)
                pnl_pct = ((next_open / entry_price) - 1) * 100
                hold_days = (df.index[idx + 1] - entry_date).days
                
                trades.append({
                    'entry_date': entry_date,
                    'exit_date': df.index[idx + 1],
                    'entry_price': entry_price,
                    'exit_price': next_open,
                    'pnl_dollars': pnl_dollars,
                    'pnl_pct': pnl_pct,
                    'hold_days': hold_days
                })
                
                cash += proceeds
                position = 'flat'
                entry_price = None
                entry_date = None
        
        # Track equity
        if position == 'long':
            unrealized_pnl = (current_close - entry_price) * SHARES_PER_TRADE
            equity_curve.append(cash + unrealized_pnl)
        else:
            equity_curve.append(cash)
    
    # Close any open position at end
    if position == 'long':
        final_close = df.iloc[-1]['close']
        final_date = df.index[-1]
        friction_cost = (friction_bps / 10000) * final_close * SHARES_PER_TRADE
        proceeds = final_close * SHARES_PER_TRADE - friction_cost
        pnl_dollars = proceeds - (entry_price * SHARES_PER_TRADE)
        pnl_pct = ((final_close / entry_price) - 1) * 100
        hold_days = (final_date - entry_date).days
        
        trades.append({
            'entry_date': entry_date,
            'exit_date': final_date,
            'entry_price': entry_price,
            'exit_price': final_close,
            'pnl_dollars': pnl_dollars,
            'pnl_pct': pnl_pct,
            'hold_days': hold_days
        })
        
        cash += proceeds
    
    # Calculate metrics
    final_equity = equity_curve[-1] if equity_curve else initial_capital
    total_return = ((final_equity / initial_capital) - 1) * 100
    bh_return = ((df.iloc[-1]['close'] / df.iloc[0]['close']) - 1) * 100
    
    equity_series = pd.Series(equity_curve)
    running_max = equity_series.expanding().max()
    drawdown = (equity_series - running_max) / running_max
    max_dd = drawdown.min() * 100
    
    returns = equity_series.pct_change().dropna()
    sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0
    
    if trades:
        trades_df = pd.DataFrame(trades)
        winning_trades = trades_df[trades_df['pnl_dollars'] > 0]
        win_rate = (len(winning_trades) / len(trades)) * 100
        profit_factor = abs(winning_trades['pnl_dollars'].sum() / trades_df[trades_df['pnl_dollars'] <= 0]['pnl_dollars'].sum()) if len(trades_df[trades_df['pnl_dollars'] <= 0]) > 0 else np.inf
        avg_hold_days = trades_df['hold_days'].mean()
    else:
        win_rate = 0
        profit_factor = 0
        avg_hold_days = 0
    
    return {
        'total_return': total_return,
        'bh_return': bh_return,
        'max_dd': max_dd,
        'sharpe': sharpe,
        'total_trades': len(trades),
        'win_rate': win_rate,
        'profit_factor': profit_factor,
        'avg_hold_days': avg_hold_days
    }

print("=" * 80)
print("CORRECTIVE RETEST #2 (REVISED): Strategy 1 - Daily Trend")
print("=" * 80)
print("CHANGES (2 ONLY):")
print("1. Execution: Signal on close, fill on NEXT OPEN (realistic)")
print("2. Warmup: 84 bars (was 28)")
print("")
print("UNCHANGED:")
print("- Exit: RSI < 45 (ORIGINAL, not changed)")
print("- Entry: RSI > 55")
print("=" * 80)

all_results = []
client = AlpacaDataClient()

for symbol in SYMBOLS:
    print(f"\n{'#' * 80}")
    print(f"TESTING: {symbol}")
    print(f"{'#' * 80}")
    
    for period in TEST_PERIODS:
        print(f"\n  Period: {period['name']} ({period['start']} to {period['end']})")
        
        try:
            # Fetch with extra buffer for warmup
            buffer_start = (pd.to_datetime(period['start']) - pd.Timedelta(days=120)).strftime('%Y-%m-%d')
            
            raw_df = client.fetch_historical_bars(
                symbol=symbol,
                timeframe=TimeFrame.Day,
                start=buffer_start,
                end=period['end'],
                feed='sip'
            )
            df = resample_to_daily(raw_df)
            print(f"  ✓ Fetched {len(df)} daily bars (includes warmup)")
            
            # Baseline
            result_baseline = run_backtest_corrected(df.copy(), FRICTION_BASELINE_BPS)
            print(f"  Baseline: {result_baseline['total_return']:+.2f}% | B&H: {result_baseline['bh_return']:+.2f}% | Sharpe: {result_baseline['sharpe']:.2f} | Trades: {result_baseline['total_trades']}")
            
            # Degraded
            result_degraded = run_backtest_corrected(df.copy(), FRICTION_DEGRADED_BPS)
            print(f"  Degraded: {result_degraded['total_return']:+.2f}% | B&H: {result_degraded['bh_return']:+.2f}% | Sharpe: {result_degraded['sharpe']:.2f} | Trades: {result_degraded['total_trades']}")
            
            for result, friction_name in [(result_baseline, 'Baseline'), (result_degraded, 'Degraded')]:
                all_results.append({
                    'Symbol': symbol,
                    'Period': period['name'],
                    'Friction': friction_name,
                    'Return (%)': f"{result['total_return']:+.2f}",
                    'B&H (%)': f"{result['bh_return']:+.2f}",
                    'Sharpe': f"{result['sharpe']:.2f}",
                    'Max DD (%)': f"{result['max_dd']:.2f}",
                    'Trades': result['total_trades'],
                    'Win Rate (%)': f"{result['win_rate']:.1f}",
                    'PF': f"{result['profit_factor']:.2f}",
                    'Avg Hold (days)': f"{result['avg_hold_days']:.1f}"
                })
            
        except Exception as e:
            print(f"  ❌ ERROR: {str(e)}")

# Save results
output_dir = Path(__file__).parent / 'batch_results'
output_dir.mkdir(exist_ok=True)

summary_df = pd.DataFrame(all_results)
summary_df.to_csv(output_dir / 'strategy1_corrected_retest_final.csv', index=False)

print(f"\n\n{'=' * 80}")
print("SUMMARY - Strategy 1 Corrected Retest (Final)")
print(f"{'=' * 80}\n")
print(summary_df.to_string(index=False))
print(f"\n✓ Results saved to: {output_dir / 'strategy1_corrected_retest_final.csv'}")
