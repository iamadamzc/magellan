"""
Risk Management Module - Volatility Targeting

Implements portfolio-level dynamic position sizing via volatility targeting.
Industry-standard approach used by AQR, Bridgewater, and other institutional quant funds.

Academic Foundation:
- Moreira & Muir (2017): "Volatility-Managed Portfolios"
- Target constant portfolio volatility for improved risk-adjusted returns
"""

import pandas as pd
import numpy as np
from typing import Optional
from src.logger import SystemLogger

LOG = SystemLogger()


class VolatilityTargeter:
    """
    Dynamic position sizing via volatility targeting.
    
    Maintains constant portfolio volatility by scaling positions inversely
    to realized volatility.
    """
    
    def __init__(self, target_vol: float = 0.15, lookback_days: int = 20):
        """
        Initialize volatility targeter.
        
        Args:
            target_vol: Target annualized volatility (default 15%)
            lookback_days: Rolling window for volatility calculation (default 20 days)
        """
        self.target_vol = target_vol
        self.lookback_days = lookback_days
        self.portfolio_returns = []  # Track returns for vol calculation
        
    def calculate_scaling_factor(
        self,
        recent_returns: Optional[pd.Series] = None
    ) -> dict:
        """
        Calculate position scaling factor based on realized volatility.
        
        Args:
            recent_returns: Series of recent portfolio returns (optional)
                           If None, uses internal tracking
        
        Returns:
            Dict with:
            - 'scaling_factor': Float 0.25-2.0 (1.0 = full size)
            - 'realized_vol': Annualized realized volatility
            - 'target_vol': Target volatility
        """
        # Use provided returns or fall back to internal tracking
        if recent_returns is not None:
            returns = recent_returns
        else:
            if len(self.portfolio_returns) < self.lookback_days:
                # Not enough data, use full size
                return {
                    'scaling_factor': 1.0,
                    'realized_vol': self.target_vol,
                    'target_vol': self.target_vol
                }
            returns = pd.Series(self.portfolio_returns[-self.lookback_days:])
        
        # Calculate realized volatility (annualized)
        realized_vol = returns.std() * np.sqrt(252)
        
        # Handle edge cases
        if realized_vol == 0 or np.isnan(realized_vol):
            LOG.warning("[VOL TARGET] Zero or NaN realized volatility, using full size")
            return {
                'scaling_factor': 1.0,
                'realized_vol': 0.0,
                'target_vol': self.target_vol
            }
        
        # Scale to target volatility
        scaling = self.target_vol / realized_vol
        
        # Safety bounds: don't leverage >2x or de-lever <0.25x
        scaling = np.clip(scaling, 0.25, 2.0)
        
        return {
            'scaling_factor': scaling,
            'realized_vol': realized_vol,
            'target_vol': self.target_vol
        }
    
    def update_returns(self, daily_return: float):
        """
        Update portfolio returns history.
        
        Args:
            daily_return: Today's portfolio return (fraction, e.g., 0.02 for +2%)
        """
        self.portfolio_returns.append(daily_return)
        
        # Keep only recent history (prevent unbounded growth)
        max_history = self.lookback_days * 3  # Keep 3x lookback window
        if len(self.portfolio_returns) > max_history:
            self.portfolio_returns = self.portfolio_returns[-max_history:]
    
    def reset(self):
        """Reset internal state (useful for backtesting)."""
        self.portfolio_returns = []


def get_volatility_scaling(
    portfolio_returns: pd.Series,
    target_vol: float = 0.15,
    lookback_days: int = 20
) -> dict:
    """
    Standalone function for volatility-based position scaling.
    
    Use this for one-off calculations without maintaining state.
    
    Args:
        portfolio_returns: Series of recent daily returns
        target_vol: Target annualized volatility (default 15%)
        lookback_days: Rolling window for volatility calculation (default 20 days)
    
    Returns:
        Dict with:
        - 'scaling_factor': Float 0.25-2.0 (1.0 = full size)
        - 'realized_vol': Annualized realized volatility  
        - 'target_vol': Target volatility
    
    Example:
        >>> returns = pd.Series([0.01, -0.02, 0.015, ...])  # Daily returns
        >>> result = get_volatility_scaling(returns, target_vol=0.15)
        >>> position_size = base_size * result['scaling_factor']
    """
    if len(portfolio_returns) < lookback_days:
        LOG.warning(f"[VOL TARGET] Insufficient data ({len(portfolio_returns)} < {lookback_days}), using full size")
        return {
            'scaling_factor': 1.0,
            'realized_vol': target_vol,
            'target_vol': target_vol
        }
    
    # Use most recent N days
    recent_returns = portfolio_returns.iloc[-lookback_days:]
    
    # Calculate realized volatility (annualized)
    realized_vol = recent_returns.std() * np.sqrt(252)
    
    # Handle edge cases
    if realized_vol == 0 or np.isnan(realized_vol):
        LOG.warning("[VOL TARGET] Zero or NaN realized volatility, using full size")
        return {
            'scaling_factor': 1.0,
            'realized_vol': 0.0,
            'target_vol': target_vol
        }
    
    # Scale to target volatility
    scaling = target_vol / realized_vol
    
    # Safety bounds: don't leverage >2x or de-lever <0.25x
    scaling = np.clip(scaling, 0.25, 2.0)
    
    LOG.info(f"[VOL TARGET] Realized: {realized_vol*100:.1f}% | Target: {target_vol*100:.1f}% | Scaling: {scaling:.2f}x")
    
    return {
        'scaling_factor': scaling,
        'realized_vol': realized_vol,
        'target_vol': target_vol
    }
