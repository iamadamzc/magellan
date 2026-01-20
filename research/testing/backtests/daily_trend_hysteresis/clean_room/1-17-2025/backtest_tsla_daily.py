"""
CLEAN-ROOM BACKTEST: STRATEGY B - TSLA DAILY TREND
Independent implementation - no reference to prior results

Strategy Rules:
- Instrument: TSLA (Equity)
- Timeframe: Daily bars
- Entry: RSI(28)[t-1] <= 55 AND RSI(28)[t] > 55 (strict crossover)
- Exit: RSI(28)[t-1] >= 45 AND RSI(28)[t] < 45 (strict crossover)
- Position: 100 shares, long-only
- Friction: 1.5 bps baseline, 5 bps degraded
"""

import pandas as pd
import numpy as np
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path
# From: clean_room_test -> daily_trend_hysteresis -> strategies -> operations -> docs -> Magellan
project_root = Path(__file__).resolve().parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))
print(f"Project root: {project_root}")

from dotenv import load_dotenv
load_dotenv()

from src.data_handler import AlpacaDataClient
from alpaca.data.timeframe import TimeFrame

print("=" * 80)
print("CLEAN-ROOM BACKTEST: STRATEGY B - TSLA DAILY TREND")
print("=" * 80)
print("Instrument: TSLA (Equity)")
print("Timeframe: Daily bars")
print("Logic: RSI(28) strict crossover, 55/45 bands")
print("=" * 80)

# ============================================================================
# CONFIGURATION
# ============================================================================

SYMBOL = 'TSLA'
RSI_PERIOD = 28
ENTRY_THRESHOLD = 55
EXIT_THRESHOLD = 45
SHARES_PER_TRADE = 100
FRICTION_BASELINE_BPS = 1.5  # 0.015%
FRICTION_DEGRADED_BPS = 5.0  # 0.05%

# Test periods
TEST_PERIODS = [
    {'name': 'Primary', 'start': '2024-01-01', 'end': '2025-12-31'},
    {'name': 'Secondary', 'start': '2022-01-01', 'end': '2023-12-31'}
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_rsi(prices, period=14):
    """Calculate RSI using standard Wilder's smoothing"""
    delta = prices.diff()
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)
    
    avg_gain = gains.ewm(span=period, adjust=False).mean()
    avg_loss = losses.ewm(span=period, adjust=False).mean()
    
    rs = avg_gain / avg_loss.replace(0, np.inf)
    rsi = 100 - (100 / (1 + rs))
    
    # Handle edge cases
    rsi = rsi.replace([np.inf, -np.inf], np.nan)
    rsi = rsi.fillna(50)  # Neutral RSI for NaN values
    
    return rsi


def run_backtest(df, friction_bps, test_name):
    """Run backtest with strict crossover logic"""
    
    print(f"\n{'=' * 80}")
    print(f"Running backtest: {test_name}")
    print(f"Friction: {friction_bps} bps")
    print(f"{'=' * 80}")
    
    # Calculate RSI
    df['rsi'] = calculate_rsi(df['close'], period=RSI_PERIOD)
    df['rsi_prev'] = df['rsi'].shift(1)
    
    # Initialize tracking variables
    position = 'flat'
    entry_price = None
    entry_date = None
    trades = []
    equity_curve = []
    initial_capital = 100000
    cash = initial_capital
    
    # Backtest loop
    for idx in range(1, len(df)):
        current_date = df.index[idx]
        current_price = df.iloc[idx]['close']
        current_rsi = df.iloc[idx]['rsi']
        prev_rsi = df.iloc[idx]['rsi_prev']
        
        # Skip if RSI not available
        if pd.isna(current_rsi) or pd.isna(prev_rsi):
            equity_curve.append(cash)
            continue
        
        # ENTRY LOGIC: Strict crossover above 55
        if position == 'flat':
            if prev_rsi <= ENTRY_THRESHOLD and current_rsi > ENTRY_THRESHOLD:
                # Enter long
                friction_cost = (friction_bps / 10000) * current_price * SHARES_PER_TRADE
                entry_price = current_price
                entry_date = current_date
                position = 'long'
                cash -= (current_price * SHARES_PER_TRADE + friction_cost)
                
        # EXIT LOGIC: Strict crossover below 45
        elif position == 'long':
            if prev_rsi >= EXIT_THRESHOLD and current_rsi < EXIT_THRESHOLD:
                # Exit long
                friction_cost = (friction_bps / 10000) * current_price * SHARES_PER_TRADE
                proceeds = current_price * SHARES_PER_TRADE - friction_cost
                pnl_dollars = proceeds - (entry_price * SHARES_PER_TRADE)
                pnl_pct = ((current_price / entry_price) - 1) * 100
                hold_days = (current_date - entry_date).days
                
                trades.append({
                    'entry_date': entry_date,
                    'exit_date': current_date,
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'pnl_dollars': pnl_dollars,
                    'pnl_pct': pnl_pct,
                    'hold_days': hold_days,
                    'entry_rsi': prev_rsi,
                    'exit_rsi': current_rsi
                })
                
                cash += proceeds
                position = 'flat'
                entry_price = None
                entry_date = None
        
        # Track equity
        if position == 'long':
            unrealized_pnl = (current_price - entry_price) * SHARES_PER_TRADE
            equity_curve.append(cash + unrealized_pnl)
        else:
            equity_curve.append(cash)
    
    # Close any open position at end
    if position == 'long':
        current_price = df.iloc[-1]['close']
        current_date = df.index[-1]
        friction_cost = (friction_bps / 10000) * current_price * SHARES_PER_TRADE
        proceeds = current_price * SHARES_PER_TRADE - friction_cost
        pnl_dollars = proceeds - (entry_price * SHARES_PER_TRADE)
        pnl_pct = ((current_price / entry_price) - 1) * 100
        hold_days = (current_date - entry_date).days
        
        trades.append({
            'entry_date': entry_date,
            'exit_date': current_date,
            'entry_price': entry_price,
            'exit_price': current_price,
            'pnl_dollars': pnl_dollars,
            'pnl_pct': pnl_pct,
            'hold_days': hold_days,
            'entry_rsi': df.iloc[-2]['rsi'],
            'exit_rsi': df.iloc[-1]['rsi']
        })
        
        cash += proceeds
    
    # Calculate metrics
    final_equity = equity_curve[-1] if equity_curve else initial_capital
    total_return = ((final_equity / initial_capital) - 1) * 100
    
    # Buy & Hold comparison
    bh_return = ((df.iloc[-1]['close'] / df.iloc[0]['close']) - 1) * 100
    
    # Max Drawdown
    equity_series = pd.Series(equity_curve)
    running_max = equity_series.expanding().max()
    drawdown = (equity_series - running_max) / running_max
    max_dd = drawdown.min() * 100
    
    # Sharpe Ratio (annualized for daily data)
    if len(equity_curve) > 1:
        returns = equity_series.pct_change().dropna()
        sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0
    else:
        sharpe = 0
    
    # Trade statistics
    if trades:
        trades_df = pd.DataFrame(trades)
        winning_trades = trades_df[trades_df['pnl_dollars'] > 0]
        losing_trades = trades_df[trades_df['pnl_dollars'] <= 0]
        win_rate = (len(winning_trades) / len(trades)) * 100
        avg_win = winning_trades['pnl_pct'].mean() if len(winning_trades) > 0 else 0
        avg_loss = losing_trades['pnl_pct'].mean() if len(losing_trades) > 0 else 0
        avg_hold = trades_df['hold_days'].mean()
        profit_factor = abs(winning_trades['pnl_dollars'].sum() / losing_trades['pnl_dollars'].sum()) if len(losing_trades) > 0 and losing_trades['pnl_dollars'].sum() != 0 else np.inf
    else:
        trades_df = pd.DataFrame()
        win_rate = 0
        avg_win = 0
        avg_loss = 0
        avg_hold = 0
        profit_factor = 0
    
    # Print results
    print(f"\n{'=' * 80}")
    print(f"RESULTS: {test_name}")
    print(f"{'=' * 80}")
    print(f"\nPERFORMANCE:")
    print(f"  Total Return:        {total_return:+.2f}%")
    print(f"  Buy & Hold:          {bh_return:+.2f}%")
    print(f"  Outperformance:      {total_return - bh_return:+.2f}%")
    print(f"  Max Drawdown:        {max_dd:.2f}%")
    print(f"  Sharpe Ratio:        {sharpe:.2f}")
    print(f"\nTRADING STATS:")
    print(f"  Total Trades:        {len(trades)}")
    print(f"  Win Rate:            {win_rate:.1f}%")
    print(f"  Profit Factor:       {profit_factor:.2f}")
    print(f"  Avg Win:             {avg_win:+.2f}%")
    print(f"  Avg Loss:            {avg_loss:+.2f}%")
    print(f"  Avg Hold:            {avg_hold:.1f} days")
    
    return {
        'test_name': test_name,
        'total_return': total_return,
        'bh_return': bh_return,
        'max_dd': max_dd,
        'sharpe': sharpe,
        'total_trades': len(trades),
        'win_rate': win_rate,
        'profit_factor': profit_factor,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'avg_hold_days': avg_hold,
        'trades_df': trades_df,
        'equity_curve': equity_series
    }


# ============================================================================
# MAIN EXECUTION
# ============================================================================

all_results = []

for period in TEST_PERIODS:
    print(f"\n\n{'#' * 80}")
    print(f"TEST PERIOD: {period['name']} ({period['start']} to {period['end']})")
    print(f"{'#' * 80}")
    
    try:
        # Fetch data
        print(f"\nFetching daily data for {SYMBOL}...")
        client = AlpacaDataClient()
        df = client.fetch_historical_bars(
            symbol=SYMBOL,
            timeframe=TimeFrame.Day,
            start=period['start'],
            end=period['end'],
            feed='sip'
        )
        print(f"✓ Fetched {len(df)} daily bars")
        
        # Run baseline test
        baseline_result = run_backtest(df, FRICTION_BASELINE_BPS, f"{period['name']} - Baseline Friction")
        all_results.append(baseline_result)
        
        # Run degraded test
        degraded_result = run_backtest(df, FRICTION_DEGRADED_BPS, f"{period['name']} - Degraded Friction")
        all_results.append(degraded_result)
        
        # Save trades
        output_dir = Path(__file__).parent
        baseline_result['trades_df'].to_csv(output_dir / f"trades_{period['name'].lower()}_baseline.csv", index=False)
        degraded_result['trades_df'].to_csv(output_dir / f"trades_{period['name'].lower()}_degraded.csv", index=False)
        
    except Exception as e:
        print(f"❌ ERROR in {period['name']}: {str(e)}")
        import traceback
        traceback.print_exc()

# ============================================================================
# SUMMARY
# ============================================================================

print(f"\n\n{'#' * 80}")
print("STRATEGY B - SUMMARY OF ALL TESTS")
print(f"{'#' * 80}")

summary_df = pd.DataFrame([{
    'Test': r['test_name'],
    'Return (%)': f"{r['total_return']:+.2f}",
    'B&H (%)': f"{r['bh_return']:+.2f}",
    'Sharpe': f"{r['sharpe']:.2f}",
    'Max DD (%)': f"{r['max_dd']:.2f}",
    'Trades': r['total_trades'],
    'Win Rate (%)': f"{r['win_rate']:.1f}",
    'Profit Factor': f"{r['profit_factor']:.2f}"
} for r in all_results])

print("\n" + summary_df.to_string(index=False))

# Save summary
output_dir = Path(__file__).parent
summary_df.to_csv(output_dir / "summary_strategy_b.csv", index=False)

print(f"\n✓ All results saved to: {output_dir}")
print("\nDone!")
