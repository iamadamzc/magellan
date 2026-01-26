"""
Virtual P&L Tracker
Simulates portfolio performance using trading signals as if using real capital.
"""

import pandas as pd
import numpy as np
from typing import Dict


def simulate_portfolio(df: pd.DataFrame, initial_capital: float = 100000.0) -> Dict:
    """
    Simulate portfolio performance using signal column to buy/sell SPY.
    
    Process:
    1. Use signal column (-1, 0, +1) to determine position direction
    2. Calculate position-adjusted returns (signal * log_return)
    3. Track cumulative equity starting from initial_capital
    4. Compute performance metrics: returns, drawdown, Sharpe ratio
    
    Args:
        df: DataFrame with 'close', 'signal', and 'log_return' columns
        initial_capital: Starting portfolio value in dollars
    
    Returns:
        Dict with performance metrics and equity curve
    """
    # Create working copy
    working_df = df[['close', 'signal', 'log_return']].copy()
    working_df = working_df.dropna()
    
    if len(working_df) == 0:
        return {
            'initial_capital': initial_capital,
            'final_equity': initial_capital,
            'total_return_dollars': 0.0,
            'total_return_pct': 0.0,
            'max_drawdown_pct': 0.0,
            'sharpe_ratio': 0.0,
            'num_trades': 0,
            'equity_curve': pd.Series(dtype=float)
        }
    
    # Calculate position-adjusted returns
    # When signal = 1 (long), we earn +log_return
    # When signal = -1 (short), we earn -log_return
    # When signal = 0 (neutral), we earn 0
    working_df['position_return'] = working_df['signal'] * working_df['log_return']
    
    # Calculate cumulative returns (multiplicative)
    working_df['equity_multiplier'] = (1 + working_df['position_return']).cumprod()
    working_df['equity'] = initial_capital * working_df['equity_multiplier']
    
    # Extract equity curve
    equity_curve = working_df['equity']
    
    # Calculate metrics
    final_equity = equity_curve.iloc[-1]
    total_return_dollars = final_equity - initial_capital
    total_return_pct = (total_return_dollars / initial_capital) * 100
    
    max_drawdown_pct = calculate_max_drawdown(equity_curve)
    sharpe_ratio = calculate_sharpe_ratio(working_df['position_return'])
    
    # Count trades (signal changes)
    num_trades = (working_df['signal'].diff() != 0).sum()
    
    return {
        'initial_capital': initial_capital,
        'final_equity': final_equity,
        'total_return_dollars': total_return_dollars,
        'total_return_pct': total_return_pct,
        'max_drawdown_pct': max_drawdown_pct,
        'sharpe_ratio': sharpe_ratio,
        'num_trades': int(num_trades),
        'equity_curve': equity_curve
    }


def calculate_max_drawdown(equity_curve: pd.Series) -> float:
    """
    Calculate maximum drawdown as peak-to-trough decline.
    
    Args:
        equity_curve: Series of equity values over time
    
    Returns:
        Maximum drawdown as negative percentage
    """
    if len(equity_curve) == 0:
        return 0.0
    
    # Calculate running maximum
    running_max = equity_curve.expanding().max()
    
    # Calculate drawdown at each point
    drawdown = (equity_curve - running_max) / running_max
    
    # Maximum drawdown is the most negative value
    max_dd = drawdown.min() * 100  # Convert to percentage
    
    return max_dd


def calculate_sharpe_ratio(returns: pd.Series, periods_per_year: int = 252 * 390) -> float:
    """
    Calculate annualized Sharpe Ratio.
    
    Assumes 1-minute bars, 390 bars per trading day, 252 trading days per year.
    
    Args:
        returns: Series of period returns (log returns)
        periods_per_year: Number of periods in a year (default: 98,280 for 1-min bars)
    
    Returns:
        Annualized Sharpe Ratio (higher is better)
    """
    if len(returns) == 0 or returns.std() == 0:
        return 0.0
    
    mean_return = returns.mean()
    std_return = returns.std()
    
    # Annualize both mean and std
    annualized_return = mean_return * periods_per_year
    annualized_std = std_return * np.sqrt(periods_per_year)
    
    if annualized_std == 0:
        return 0.0
    
    sharpe = annualized_return / annualized_std
    
    return sharpe


def generate_equity_curve_ascii(equity_curve: pd.Series, height: int = 10, width: int = 60) -> str:
    """
    Generate simple ASCII representation of equity curve.
    
    Args:
        equity_curve: Series of equity values over time
        height: Number of rows in visualization
        width: Number of columns in visualization
    
    Returns:
        String containing ASCII art of equity curve
    """
    if len(equity_curve) < 2:
        return "[Insufficient data for visualization]"
    
    # Normalize equity curve to 0-1 range
    eq_min = equity_curve.min()
    eq_max = equity_curve.max()
    eq_range = eq_max - eq_min
    
    if eq_range == 0:
        # Flat line
        normalized = pd.Series([0.5] * len(equity_curve))
    else:
        normalized = (equity_curve - eq_min) / eq_range
    
    # Sample points to fit width
    if len(equity_curve) > width:
        indices = np.linspace(0, len(equity_curve) - 1, width).astype(int)
        sampled = normalized.iloc[indices]
    else:
        sampled = normalized
    
    # Create grid
    grid = []
    for _ in range(height):
        grid.append([' '] * len(sampled))
    
    # Plot points
    for i, value in enumerate(sampled):
        row = int((1 - value) * (height - 1))  # Invert y-axis
        row = max(0, min(height - 1, row))
        grid[row][i] = '█'
    
    # Convert grid to string
    lines = []
    lines.append(f"Equity: ${eq_max:,.0f} ┤" + "─" * width)
    for row in grid:
        lines.append("         │" + "".join(row))
    lines.append(f"        ${eq_min:,.0f} ┤" + "─" * width)
    lines.append("         └" + "─" * width)
    lines.append(f"         Start{' ' * (width - 11)}End")
    
    return "\n".join(lines)


def print_virtual_trading_statement(metrics: Dict) -> None:
    """
    Print formatted Virtual Trading Statement with performance metrics.
    
    Args:
        metrics: Dict returned from simulate_portfolio()
    """
    print("\n" + "=" * 60)
    print("[VIRTUAL TRADING STATEMENT] Out-of-Sample Performance")
    print("=" * 60)
    
    print(f"Initial Capital:        ${metrics['initial_capital']:,.2f}")
    print(f"Final Equity:           ${metrics['final_equity']:,.2f}")
    
    ret_sign = '+' if metrics['total_return_pct'] >= 0 else ''
    print(f"Total Return:           ${metrics['total_return_dollars']:,.2f} ({ret_sign}{metrics['total_return_pct']:.2f}%)")
    
    print(f"Max Drawdown:           {metrics['max_drawdown_pct']:.2f}%")
    print(f"Sharpe Ratio:           {metrics['sharpe_ratio']:.2f}")
    print(f"Total Trades:           {metrics['num_trades']}")
    
    print("=" * 60)
    
    # Risk check
    if abs(metrics['max_drawdown_pct']) > 5.0:
        print("⚠ [RISK WARNING] Max Drawdown exceeds 5% threshold!")
        print("⚠ Recommendation: Tighten risk controls before live trading.")
    else:
        print("✓ [RISK CHECK] Max Drawdown within acceptable range (<5%)")
    
    print("=" * 60)
    
    # Display ASCII equity curve
    if len(metrics['equity_curve']) > 1:
        print("\n[EQUITY CURVE]")
        print(generate_equity_curve_ascii(metrics['equity_curve']))
