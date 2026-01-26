"""
Silver Trend-Following Strategy
Optimized RSI-based position trading for silver bull markets

Strategy: Enter on RSI breakout, hold for extended periods
Asset: Silver (SIUSD spot / MSI micro futures)
Leverage: 6x
Expected: ~$58,000/year on $20k capital
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / ".env")


def load_silver_data(start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """Load silver daily data from cache."""
    cache_dir = project_root / "data" / "cache" / "futures"
    pattern = "SIUSD_1day_*.parquet"
    files = list(cache_dir.glob(pattern))
    
    if not files:
        raise FileNotFoundError(f"No SIUSD data found in {cache_dir}")
    
    dfs = [pd.read_parquet(f) for f in files]
    df = pd.concat(dfs).sort_index()
    df = df[~df.index.duplicated(keep='last')]
    
    if start_date:
        df = df[start_date:]
    if end_date:
        df = df[:end_date]
    
    return df


def calculate_rsi(prices: pd.Series, period: int = 21) -> pd.Series:
    """Calculate RSI indicator."""
    delta = prices.diff()
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)
    
    avg_gain = gains.ewm(span=period, adjust=False).mean()
    avg_loss = losses.ewm(span=period, adjust=False).mean()
    
    rs = avg_gain / avg_loss.replace(0, np.inf)
    rsi = 100 - (100 / (1 + rs))
    
    rsi.loc[avg_loss == 0] = 100.0
    rsi.loc[avg_gain == 0] = 0.0
    
    return rsi


def run_silver_backtest(
    start_date: str = "2024-01-01",
    end_date: str = "2025-01-24",
    initial_capital: float = 20000,
    leverage: float = 6,
    rsi_period: int = 21,
    entry_band: float = 48,
    exit_band: float = 30,
    verbose: bool = True
):
    """Run silver trend-following backtest."""
    
    if verbose:
        print("\n" + "=" * 60)
        print("SILVER TREND-FOLLOWING BACKTEST")
        print("=" * 60)
        print(f"Period: {start_date} to {end_date}")
        print(f"Capital: ${initial_capital:,} | Leverage: {leverage}x")
        print(f"RSI: {rsi_period} | Entry: >{entry_band} | Exit: <{exit_band}")
        print("=" * 60)
    
    # Load data
    df = load_silver_data(start_date, end_date)
    df['rsi'] = calculate_rsi(df['close'], rsi_period)
    df = df.iloc[rsi_period + 5:]  # Warmup
    
    if verbose:
        print(f"Loaded {len(df)} bars")
    
    # Simulation
    cash = initial_capital
    position = 'flat'
    trades = []
    equity_curve = []
    
    transaction_cost_bps = 5.0
    
    for i in range(len(df)):
        row = df.iloc[i]
        date = df.index[i]
        price = row['close']
        rsi = row['rsi']
        
        if pd.isna(rsi):
            continue
        
        # Entry
        if position == 'flat' and rsi > entry_band:
            cost = transaction_cost_bps / 10000
            effective_capital = cash * leverage * (1 - cost)
            entry_price = price
            entry_date = date
            position = 'long'
            
            if verbose:
                print(f"\n  {date.strftime('%Y-%m-%d')} ENTER LONG @ ${price:.2f} (RSI: {rsi:.1f})")
        
        # Exit
        elif position == 'long' and rsi < exit_band:
            cost = transaction_cost_bps / 10000
            position_value = effective_capital * (price / entry_price)
            exit_value = position_value * (1 - cost)
            pnl = exit_value - (cash * leverage)
            hold_days = (date - entry_date).days
            
            trades.append({
                'entry_date': entry_date,
                'exit_date': date,
                'entry_price': entry_price,
                'exit_price': price,
                'hold_days': hold_days,
                'pnl': pnl,
            })
            
            cash = cash + pnl
            position = 'flat'
            
            if verbose:
                win_loss = "✅" if pnl > 0 else "❌"
                print(f"  {date.strftime('%Y-%m-%d')} EXIT @ ${price:.2f} | P&L: ${pnl:+,.2f} | Hold: {hold_days}d {win_loss}")
        
        # Track equity
        if position == 'long':
            current_equity = cash + (effective_capital * (price / entry_price) - cash * leverage)
        else:
            current_equity = cash
        equity_curve.append(current_equity)
    
    # Close final position
    if position == 'long':
        price = df.iloc[-1]['close']
        date = df.index[-1]
        position_value = effective_capital * (price / entry_price)
        pnl = position_value * 0.9995 - (cash * leverage)
        
        trades.append({
            'entry_date': entry_date,
            'exit_date': date,
            'entry_price': entry_price,
            'exit_price': price,
            'hold_days': (date - entry_date).days,
            'pnl': pnl,
        })
        
        cash = cash + pnl
        
        if verbose:
            win_loss = "✅" if pnl > 0 else "❌"
            print(f"  {date.strftime('%Y-%m-%d')} FINAL EXIT @ ${price:.2f} | P&L: ${pnl:+,.2f} {win_loss}")
    
    # Calculate metrics
    if len(trades) == 0:
        if verbose:
            print("\nNO TRADES GENERATED")
        return None
    
    trades_df = pd.DataFrame(trades)
    total_pnl = trades_df['pnl'].sum()
    total_return = (cash - initial_capital) / initial_capital * 100
    win_rate = (trades_df['pnl'] > 0).mean() * 100
    
    # Sharpe
    equity_series = pd.Series(equity_curve)
    daily_returns = equity_series.pct_change().dropna()
    if daily_returns.std() > 0:
        sharpe = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252)
    else:
        sharpe = 0
    
    # Max drawdown
    peak = equity_series.expanding().max()
    drawdown = (equity_series - peak) / peak
    max_dd = drawdown.min() * 100
    
    if verbose:
        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60)
        print(f"Total Trades:    {len(trades)}")
        print(f"Win Rate:        {win_rate:.0f}%")
        print(f"Total P&L:       ${total_pnl:+,.2f}")
        print(f"Total Return:    {total_return:+.1f}%")
        print(f"Sharpe Ratio:    {sharpe:.2f}")
        print(f"Max Drawdown:    {max_dd:.1f}%")
        print(f"Final Equity:    ${cash:,.2f}")
        print("=" * 60)
    
    return {
        'trades': trades_df,
        'total_pnl': total_pnl,
        'total_return': total_return,
        'sharpe': sharpe,
        'max_dd': max_dd,
        'win_rate': win_rate,
        'final_equity': cash
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Silver Trend Strategy Backtest")
    parser.add_argument("--start", default="2024-01-01", help="Start date")
    parser.add_argument("--end", default="2025-01-24", help="End date")
    parser.add_argument("--capital", type=float, default=20000, help="Initial capital")
    parser.add_argument("--leverage", type=float, default=6, help="Leverage multiplier")
    
    args = parser.parse_args()
    
    run_silver_backtest(
        start_date=args.start,
        end_date=args.end,
        initial_capital=args.capital,
        leverage=args.leverage
    )
