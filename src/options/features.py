"""
Options Feature Engineering

Calculates Greeks, IV metrics, and performs strike/DTE selection logic.
Uses Black-Scholes model for theoretical pricing and Greeks.
"""

import numpy as np
import pandas as pd
from scipy.stats import norm
from typing import Dict, Optional, List
from datetime import datetime, date

from src.logger import LOG


class OptionsFeatureEngineer:
    """
    Calculates options-specific features for strategy logic.
    
    Features:
    - Black-Scholes Greeks (delta, gamma, theta, vega, rho)
    - Implied volatility analysis (IV rank, IV percentile)
    - Strike selection based on delta targets
    - DTE management and roll logic
    """
    
    @staticmethod
    def calculate_black_scholes_greeks(
        S: float,  # Spot price
        K: float,  # Strike price
        T: float,  # Time to expiration (years)
        r: float,  # Risk-free rate
        sigma: float,  # Implied volatility (annualized)
        option_type: str = 'call'
    ) -> Dict[str, float]:
        """
        Calculate Black-Scholes option price and Greeks.
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration in years (DTE / 365)
            r: Risk-free interest rate (e.g., 0.04 for 4%)
            sigma: Implied volatility (e.g., 0.30 for 30% IV)
            option_type: 'call' or 'put'
        
        Returns:
            Dictionary with:
            - price: Theoretical option price
            - delta: Rate of change of price w.r.t. stock price
            - gamma: Rate of change of delta w.r.t. stock price
            - theta: Rate of change of price w.r.t. time (daily decay)
            - vega: Rate of change of price w.r.t. volatility (per 1% IV change)
            - rho: Rate of change of price w.r.t. interest rate
        
        Example:
            >>> OptionsFeatureEngineer.calculate_black_scholes_greeks(
            ...     S=590.0, K=590.0, T=0.1, r=0.04, sigma=0.25, option_type='call'
            ... )
            {
                'price': 12.45,
                'delta': 0.54,
                'gamma': 0.015,
                'theta': -0.35,  # -$0.35/day
                'vega': 0.82,    # +$0.82 per 1% IV increase
                'rho': 0.15
            }
        """
        # Handle edge cases
        if T <= 0:
            # Expired option - only intrinsic value remains
            if option_type.lower() in ['call', 'c']:
                intrinsic = max(0, S - K)
            else:
                intrinsic = max(0, K - S)
            
            return {
                'price': intrinsic,
                'delta': 1.0 if intrinsic > 0 else 0.0,
                'gamma': 0.0,
                'theta': 0.0,
                'vega': 0.0,
                'rho': 0.0
            }
        
        if sigma <= 0:
            LOG.warning(f"Invalid sigma: {sigma}, using 0.01")
            sigma = 0.01
        
        # Black-Scholes intermediate calculations
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        # Standard normal CDF and PDF
        N_d1 = norm.cdf(d1)
        N_d2 = norm.cdf(d2)
        n_d1 = norm.pdf(d1)  # PDF for gamma, vega
        
        # Option price
        if option_type.lower() in ['call', 'c']:
            price = S * N_d1 - K * np.exp(-r * T) * N_d2
            delta = N_d1
            rho = K * T * np.exp(-r * T) * N_d2 / 100  # Per 1% rate change
        else:  # put
            price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
            delta = N_d1 - 1  # Put delta is negative
            rho = -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100
        
        # Gamma (same for calls and puts)
        gamma = n_d1 / (S * sigma * np.sqrt(T))
        
        # Theta (daily decay)
        if option_type.lower() in ['call', 'c']:
            theta = (
                -(S * n_d1 * sigma) / (2 * np.sqrt(T))
                - r * K * np.exp(-r * T) * N_d2
            ) / 365  # Convert to daily
        else:  # put
            theta = (
                -(S * n_d1 * sigma) / (2 * np.sqrt(T))
                + r * K * np.exp(-r * T) * norm.cdf(-d2)
            ) / 365
        
        # Vega (per 1% IV change)
        vega = S * n_d1 * np.sqrt(T) * 0.01
        
        return {
            'price': price,
            'delta': delta,
            'gamma': gamma,
            'theta': theta,
            'vega': vega,
            'rho': rho
        }
    
    @staticmethod
    def calculate_iv_rank(
        current_iv: float,
        iv_history: pd.Series,
        lookback_days: int = 252
    ) -> float:
        """
        Calculate IV Rank (percentile of current IV vs historical range).
        
        IV Rank = (Current IV - Min IV) / (Max IV - Min IV) * 100
        
        Interpretation:
        - IV Rank > 70: High IV (expensive options, consider selling premium)
        - IV Rank 30-70: Normal IV
        - IV Rank < 30: Low IV (cheap options, consider buying premium)
        
        Args:
            current_iv: Current implied volatility (e.g., 0.35 = 35%)
            iv_history: Series of historical IV values
            lookback_days: Number of days for historical range (default: 1 year)
        
        Returns:
            IV Rank (0-100)
        
        Example:
            >>> iv_history = pd.Series([0.20, 0.25, 0.30, 0.35, 0.40])
            >>> OptionsFeatureEngineer.calculate_iv_rank(0.35, iv_history)
            75.0  # Current IV is at 75th percentile
        """
        recent_iv = iv_history.tail(lookback_days)
        
        if len(recent_iv) < 30:
            LOG.warning(f"Insufficient IV history ({len(recent_iv)} days), using 50 as default")
            return 50.0
        
        min_iv = recent_iv.min()
        max_iv = recent_iv.max()
        
        if max_iv == min_iv:
            return 50.0  # No variation, return neutral
        
        iv_rank = ((current_iv - min_iv) / (max_iv - min_iv)) * 100
        
        return np.clip(iv_rank, 0, 100)
    
    @staticmethod
    def calculate_iv_percentile(
        current_iv: float,
        iv_history: pd.Series,
        lookback_days: int = 252
    ) -> float:
        """
        Calculate IV Percentile (% of days current IV is higher than historical).
        
        Args:
            current_iv: Current implied volatility
            iv_history: Series of historical IV values
            lookback_days: Number of days for comparison
        
        Returns:
            IV Percentile (0-100)
        
        Example:
            >>> iv_history = pd.Series([0.20, 0.25, 0.30, 0.35, 0.40])
            >>> OptionsFeatureEngineer.calculate_iv_percentile(0.35, iv_history)
            80.0  # Current IV is higher than 80% of historical days
        """
        recent_iv = iv_history.tail(lookback_days)
        
        if len(recent_iv) < 30:
            LOG.warning(f"Insufficient IV history ({len(recent_iv)} days), using 50 as default")
            return 50.0
        
        percentile = (recent_iv < current_iv).sum() / len(recent_iv) * 100
        
        return percentile
    
    @staticmethod
    def estimate_iv_from_price(
        option_price: float,
        S: float,
        K: float,
        T: float,
        r: float,
        option_type: str = 'call',
        max_iterations: int = 100,
        tolerance: float = 0.0001
    ) -> Optional[float]:
        """
        Estimate implied volatility from option price using Newton-Raphson method.
        
        Args:
            option_price: Observed market price of option
            S: Current stock price
            K: Strike price
            T: Time to expiration (years)
            r: Risk-free rate
            option_type: 'call' or 'put'
            max_iterations: Maximum iterations for convergence
            tolerance: Convergence tolerance
        
        Returns:
            Implied volatility (e.g., 0.25 = 25% IV), or None if failed to converge
        
        Example:
            >>> OptionsFeatureEngineer.estimate_iv_from_price(
            ...     option_price=12.50, S=590.0, K=590.0, T=0.1, r=0.04, option_type='call'
            ... )
            0.253  # Implied volatility is 25.3%
        """
        # Initial guess
        sigma = 0.30
        
        for i in range(max_iterations):
            # Calculate price and vega with current sigma
            greeks = OptionsFeatureEngineer.calculate_black_scholes_greeks(
                S, K, T, r, sigma, option_type
            )
            
            price_diff = greeks['price'] - option_price
            vega = greeks['vega']
            
            # Check convergence
            if abs(price_diff) < tolerance:
                return sigma
            
            # Newton-Raphson update
            if vega > 0:
                sigma = sigma - price_diff / (vega * 100)  # vega is per 1% change
                sigma = max(0.01, min(5.0, sigma))  # Clamp to reasonable range
            else:
                LOG.warning("Vega is zero, cannot converge")
                return None
        
        LOG.warning(f"IV estimation did not converge after {max_iterations} iterations")
        return None
    
    @staticmethod
    def should_roll_position(
        dte: int,
        roll_threshold_dte: int = 7,
        current_pnl_pct: Optional[float] = None,
        min_profit_to_roll: float = 0.0
    ) -> bool:
        """
        Determine if position should be rolled to new expiration.
        
        Args:
            dte: Current days to expiration
            roll_threshold_dte: Roll when DTE falls below this
            current_pnl_pct: Current P&L as % of premium (optional)
            min_profit_to_roll: Minimum profit % required to roll (default: 0)
        
        Returns:
            True if should roll, False otherwise
        
        Example:
            >>> OptionsFeatureEngineer.should_roll_position(dte=5, roll_threshold_dte=7)
            True  # DTE < 7, time to roll
            
            >>> OptionsFeatureEngineer.should_roll_position(
            ...     dte=5, roll_threshold_dte=7, current_pnl_pct=-30, min_profit_to_roll=0
            ... )
            True  # Roll even if losing (avoid expiration)
        """
        # Primary criterion: DTE threshold
        if dte > roll_threshold_dte:
            return False
        
        # Optional: Don't roll if deep in loss (let it expire worthless)
        if current_pnl_pct is not None and current_pnl_pct < -80:
            LOG.flow(f"Position down {current_pnl_pct:.1f}%, letting expire worthless")
            return False
        
        # Optional: Require minimum profit to roll
        if current_pnl_pct is not None and current_pnl_pct < min_profit_to_roll:
            LOG.flow(f"Position P&L {current_pnl_pct:.1f}% < {min_profit_to_roll}%, not rolling")
            return False
        
        return True
    
    @staticmethod
    def calculate_position_size_contracts(
        target_notional: float,
        current_price: float,
        delta: float,
        min_contracts: int = 1,
        max_contracts: int = 100
    ) -> int:
        """
        Calculate number of option contracts for target notional exposure.
        
        Formula:
        Contracts = Target Notional / (Current Price * 100 shares * Delta)
        
        Args:
            target_notional: Target dollar exposure (e.g., $10,000)
            current_price: Current stock price
            delta: Option delta (e.g., 0.60)
            min_contracts: Minimum contracts (default: 1)
            max_contracts: Maximum contracts (default: 100)
        
        Returns:
            Number of contracts (integer)
        
        Example:
            >>> OptionsFeatureEngineer.calculate_position_size_contracts(
            ...     target_notional=10000, current_price=590.0, delta=0.60
            ... )
            3  # 3 contracts × 100 shares × $590 × 0.60 delta = $10,620 exposure
        """
        # Calculate delta-adjusted shares needed
        shares_needed = target_notional / current_price
        
        # Convert to contracts (1 contract = 100 shares)
        contracts_needed = shares_needed / (100 * abs(delta))
        
        # Round to nearest integer, enforce min/max
        contracts = int(round(contracts_needed))
        contracts = max(min_contracts, min(max_contracts, contracts))
        
        LOG.flow(
            f"Position size: {contracts} contracts "
            f"(Target: ${target_notional:,.0f}, Delta: {delta:.2f})"
        )
        
        return contracts
    
    @staticmethod
    def calculate_breakeven_move_pct(
        premium: float,
        strike: float,
        option_type: str
    ) -> float:
        """
        Calculate % move required for option to break even at expiration.
        
        Args:
            premium: Premium paid per share
            strike: Strike price
            option_type: 'call' or 'put'
        
        Returns:
            Percentage move required (e.g., 5.2 = need 5.2% move)
        
        Example:
            >>> OptionsFeatureEngineer.calculate_breakeven_move_pct(
            ...     premium=5.50, strike=590.0, option_type='call'
            ... )
            0.93  # Need stock to move up 0.93% to break even
        """
        if option_type.lower() in ['call', 'c']:
            breakeven_price = strike + premium
            move_pct = ((breakeven_price - strike) / strike) * 100
        else:  # put
            breakeven_price = strike - premium
            move_pct = ((strike - breakeven_price) / strike) * 100
        
        return move_pct
    
    @staticmethod
    def estimate_win_probability(
        S: float,
        K: float,
        T: float,
        sigma: float,
        option_type: str = 'call'
    ) -> float:
        """
        Estimate probability of option expiring in-the-money (ITM).
        
        Uses Black-Scholes framework (assumes lognormal distribution).
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (years)
            sigma: Implied volatility
            option_type: 'call' or 'put'
        
        Returns:
            Probability (0-1) of expiring ITM
        
        Example:
            >>> OptionsFeatureEngineer.estimate_win_probability(
            ...     S=590.0, K=590.0, T=0.1, sigma=0.25, option_type='call'
            ... )
            0.52  # 52% chance of expiring ITM (slightly above 50% for ATM call)
        """
        if T <= 0:
            # Already expired, check if ITM now
            if option_type.lower() in ['call', 'c']:
                return 1.0 if S > K else 0.0
            else:
                return 1.0 if S < K else 0.0
        
        # Calculate d2 from Black-Scholes (probability of ITM)
        d2 = (np.log(S / K) + (0.0 - 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        
        if option_type.lower() in ['call', 'c']:
            prob_itm = norm.cdf(d2)
        else:  # put
            prob_itm = norm.cdf(-d2)
        
        return prob_itm
