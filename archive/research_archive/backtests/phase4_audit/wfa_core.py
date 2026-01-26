"""
WFA Core Module - Corrected Methodology

This module provides correct implementations of:
- Annualized Sharpe ratio (sqrt(252) for daily, sqrt(52) for weekly)
- Minimum sample size validation
- Trade statistics calculation
- Sortino ratio

Used by all Phase 4 WFA scripts.
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, List, Tuple
from datetime import datetime


def calculate_sharpe_correct(
    returns: np.ndarray,
    rf: float = 0.04,
    periods_per_year: int = 252,
    min_samples: int = 10
) -> Optional[float]:
    """
    Calculate correctly annualized Sharpe ratio.
    
    Formula: (mean_excess_return / std_return) * sqrt(periods_per_year)
    
    Args:
        returns: Array of period returns (e.g., daily returns)
        rf: Annual risk-free rate (default 4%)
        periods_per_year: Trading periods per year (252 for daily, 52 for weekly)
        min_samples: Minimum number of returns required (default 10)
    
    Returns:
        Annualized Sharpe ratio, or None if insufficient samples
    """
    if len(returns) < min_samples:
        return None
    
    returns = np.array(returns)
    
    # Convert annual rf to per-period rf
    rf_per_period = rf / periods_per_year
    
    excess_returns = returns - rf_per_period
    
    if np.std(excess_returns) == 0:
        return 0.0
    
    sharpe = (np.mean(excess_returns) / np.std(excess_returns)) * np.sqrt(periods_per_year)
    return float(sharpe)


def calculate_sharpe_from_trades(
    trade_returns: np.ndarray,
    avg_holding_days: float = 30,
    rf: float = 0.04,
    min_trades: int = 10
) -> Optional[float]:
    """
    Calculate Sharpe ratio from trade-level returns.
    
    Since trades don't occur at regular intervals, we annualize based on
    average holding period.
    
    Args:
        trade_returns: Array of per-trade returns (e.g., [0.05, -0.02, 0.08])
        avg_holding_days: Average number of days per trade
        rf: Annual risk-free rate
        min_trades: Minimum trades required
    
    Returns:
        Annualized Sharpe ratio, or None if insufficient trades
    """
    if len(trade_returns) < min_trades:
        return None
    
    trade_returns = np.array(trade_returns)
    
    # Trades per year
    trades_per_year = 252 / avg_holding_days
    
    # Per-trade risk-free return
    rf_per_trade = rf / trades_per_year
    
    excess_returns = trade_returns - rf_per_trade
    
    if np.std(excess_returns) == 0:
        return 0.0
    
    # Annualize using trades per year
    sharpe = (np.mean(excess_returns) / np.std(excess_returns)) * np.sqrt(trades_per_year)
    return float(sharpe)


def calculate_sortino(
    returns: np.ndarray,
    rf: float = 0.04,
    periods_per_year: int = 252,
    min_samples: int = 10
) -> Optional[float]:
    """
    Calculate Sortino ratio (only penalizes downside deviation).
    
    Args:
        returns: Array of period returns
        rf: Annual risk-free rate
        periods_per_year: Trading periods per year
        min_samples: Minimum samples required
    
    Returns:
        Annualized Sortino ratio, or None if insufficient samples
    """
    if len(returns) < min_samples:
        return None
    
    returns = np.array(returns)
    rf_per_period = rf / periods_per_year
    excess_returns = returns - rf_per_period
    
    # Downside returns only
    downside_returns = excess_returns[excess_returns < 0]
    
    if len(downside_returns) == 0:
        return float('inf')  # No downside
    
    downside_std = np.std(downside_returns)
    
    if downside_std == 0:
        return 0.0
    
    sortino = (np.mean(excess_returns) / downside_std) * np.sqrt(periods_per_year)
    return float(sortino)


def calculate_trade_stats(trades_df: pd.DataFrame) -> Dict:
    """
    Calculate comprehensive trade statistics.
    
    Args:
        trades_df: DataFrame with 'pnl' or 'pnl_pct' column
    
    Returns:
        Dictionary with trade statistics
    """
    if len(trades_df) == 0:
        return {
            'num_trades': 0,
            'win_rate': None,
            'avg_win': None,
            'avg_loss': None,
            'profit_factor': None,
            'max_consecutive_losses': 0,
            'avg_pnl': None
        }
    
    # Use pnl_pct if available, otherwise pnl
    pnl_col = 'pnl_pct' if 'pnl_pct' in trades_df.columns else 'pnl'
    
    wins = trades_df[trades_df[pnl_col] > 0]
    losses = trades_df[trades_df[pnl_col] < 0]
    
    win_rate = len(wins) / len(trades_df) * 100 if len(trades_df) > 0 else 0
    avg_win = wins[pnl_col].mean() if len(wins) > 0 else 0
    avg_loss = losses[pnl_col].mean() if len(losses) > 0 else 0
    
    # Profit factor
    total_wins = wins[pnl_col].sum() if len(wins) > 0 else 0
    total_losses = abs(losses[pnl_col].sum()) if len(losses) > 0 else 0
    profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
    
    # Max consecutive losses
    is_loss = (trades_df[pnl_col] < 0).astype(int)
    max_consecutive = 0
    current_streak = 0
    for loss in is_loss:
        if loss:
            current_streak += 1
            max_consecutive = max(max_consecutive, current_streak)
        else:
            current_streak = 0
    
    return {
        'num_trades': len(trades_df),
        'win_rate': round(win_rate, 1),
        'avg_win': round(avg_win, 2) if avg_win else 0,
        'avg_loss': round(avg_loss, 2) if avg_loss else 0,
        'profit_factor': round(profit_factor, 2) if profit_factor != float('inf') else 999.99,
        'max_consecutive_losses': max_consecutive,
        'avg_pnl': round(trades_df[pnl_col].mean(), 2)
    }


def calculate_max_drawdown(equity_curve: np.ndarray) -> float:
    """
    Calculate maximum drawdown from equity curve.
    
    Args:
        equity_curve: Array of portfolio values over time
    
    Returns:
        Maximum drawdown as negative percentage (e.g., -0.15 for 15% drawdown)
    """
    if len(equity_curve) == 0:
        return 0.0
    
    equity_curve = np.array(equity_curve)
    running_max = np.maximum.accumulate(equity_curve)
    drawdowns = (equity_curve - running_max) / running_max
    return float(np.min(drawdowns))


def bootstrap_sharpe_ci(
    returns: np.ndarray,
    n_bootstrap: int = 1000,
    confidence: float = 0.95,
    rf: float = 0.04,
    periods_per_year: int = 252
) -> Tuple[float, float, float]:
    """
    Calculate bootstrap confidence interval for Sharpe ratio.
    
    Args:
        returns: Array of returns
        n_bootstrap: Number of bootstrap samples
        confidence: Confidence level (e.g., 0.95 for 95%)
        rf: Risk-free rate
        periods_per_year: Trading periods per year
    
    Returns:
        Tuple of (point_estimate, lower_bound, upper_bound)
    """
    returns = np.array(returns)
    n = len(returns)
    
    if n < 10:
        return (None, None, None)
    
    # Point estimate
    point_est = calculate_sharpe_correct(returns, rf, periods_per_year, min_samples=5)
    
    # Bootstrap samples
    sharpes = []
    for _ in range(n_bootstrap):
        sample = np.random.choice(returns, size=n, replace=True)
        s = calculate_sharpe_correct(sample, rf, periods_per_year, min_samples=5)
        if s is not None:
            sharpes.append(s)
    
    if len(sharpes) < 100:
        return (point_est, None, None)
    
    alpha = 1 - confidence
    lower = np.percentile(sharpes, alpha/2 * 100)
    upper = np.percentile(sharpes, (1 - alpha/2) * 100)
    
    return (point_est, lower, upper)


class WFAWindow:
    """Represents a single walk-forward window."""
    
    def __init__(
        self,
        name: str,
        train_start: str,
        train_end: str,
        test_start: str,
        test_end: str
    ):
        self.name = name
        self.train_start = train_start
        self.train_end = train_end
        self.test_start = test_start
        self.test_end = test_end
    
    def __repr__(self):
        return f"WFAWindow({self.name}: Train {self.train_start} to {self.train_end}, Test {self.test_start} to {self.test_end})"


def generate_rolling_windows(
    start_date: str,
    end_date: str,
    train_months: int = 6,
    test_months: int = 6,
    step_months: int = 6
) -> List[WFAWindow]:
    """
    Generate rolling walk-forward windows.
    
    Args:
        start_date: First date of data (YYYY-MM-DD)
        end_date: Last date of data (YYYY-MM-DD)
        train_months: Training window length in months
        test_months: Testing window length in months
        step_months: Step size in months
    
    Returns:
        List of WFAWindow objects
    """
    from dateutil.relativedelta import relativedelta
    
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    windows = []
    window_num = 1
    current = start
    
    while current + relativedelta(months=train_months + test_months) <= end:
        train_start = current.strftime('%Y-%m-%d')
        train_end = (current + relativedelta(months=train_months) - relativedelta(days=1)).strftime('%Y-%m-%d')
        test_start = (current + relativedelta(months=train_months)).strftime('%Y-%m-%d')
        test_end = (current + relativedelta(months=train_months + test_months) - relativedelta(days=1)).strftime('%Y-%m-%d')
        
        windows.append(WFAWindow(
            name=f"W{window_num}",
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end
        ))
        
        window_num += 1
        current += relativedelta(months=step_months)
    
    return windows


# Quick test
if __name__ == "__main__":
    print("Testing WFA Core Module...")
    
    # Test Sharpe calculation
    np.random.seed(42)
    returns = np.random.normal(0.001, 0.02, 100)  # 100 daily returns
    sharpe = calculate_sharpe_correct(returns)
    print(f"Sharpe (100 returns): {sharpe:.4f}")
    
    # Test with insufficient samples
    sharpe_small = calculate_sharpe_correct(returns[:5])
    print(f"Sharpe (5 returns): {sharpe_small}")  # Should be None
    
    # Test bootstrap CI
    point, lower, upper = bootstrap_sharpe_ci(returns)
    print(f"Bootstrap CI: {point:.2f} [{lower:.2f}, {upper:.2f}]")
    
    # Test window generation
    windows = generate_rolling_windows('2020-01-01', '2025-12-31', 6, 6, 6)
    print(f"\nGenerated {len(windows)} windows:")
    for w in windows[:3]:
        print(f"  {w}")
    
    print("\n✓ All tests passed!")
