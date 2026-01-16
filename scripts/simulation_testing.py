"""
Simulation Testing Framework for Validated Strategies
Generates comprehensive PnL reports with monthly/annual breakdowns and key statistics
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json

class StrategySimulator:
    """Base class for strategy simulation testing"""
    
    def __init__(self, initial_capital: float = 10000, start_date: str = "2024-01-01", end_date: str = "2025-12-31"):
        self.initial_capital = initial_capital
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.trades = []
        self.equity_curve = []
        
    def calculate_statistics(self, returns: pd.Series) -> Dict:
        """Calculate comprehensive performance statistics"""
        
        # Basic metrics
        total_return = (returns + 1).prod() - 1
        annual_return = (1 + total_return) ** (252 / len(returns)) - 1 if len(returns) > 0 else 0
        
        # Sharpe Ratio (assuming 252 trading days, 0% risk-free rate)
        sharpe = np.sqrt(252) * returns.mean() / returns.std() if returns.std() > 0 else 0
        
        # Drawdown calculation
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Win rate
        winning_trades = len([r for r in returns if r > 0])
        total_trades = len(returns)
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # Profit factor
        gross_profit = returns[returns > 0].sum() if len(returns[returns > 0]) > 0 else 0
        gross_loss = abs(returns[returns < 0].sum()) if len(returns[returns < 0]) > 0 else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else np.inf
        
        # Average win/loss
        avg_win = returns[returns > 0].mean() if len(returns[returns > 0]) > 0 else 0
        avg_loss = returns[returns < 0].mean() if len(returns[returns < 0]) > 0 else 0
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': total_trades - winning_trades,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'best_trade': returns.max() if len(returns) > 0 else 0,
            'worst_trade': returns.min() if len(returns) > 0 else 0
        }
    
    def generate_monthly_pnl(self, equity_curve: pd.DataFrame) -> pd.DataFrame:
        """Generate monthly PnL breakdown"""
        equity_curve['year_month'] = equity_curve['date'].dt.to_period('M')
        
        monthly = equity_curve.groupby('year_month').agg({
            'equity': ['first', 'last', 'min', 'max']
        })
        
        monthly.columns = ['start_equity', 'end_equity', 'min_equity', 'max_equity']
        monthly['pnl'] = monthly['end_equity'] - monthly['start_equity']
        monthly['return_pct'] = (monthly['end_equity'] / monthly['start_equity'] - 1) * 100
        monthly['intra_month_dd'] = (monthly['min_equity'] / monthly['start_equity'] - 1) * 100
        
        return monthly.reset_index()
    
    def generate_annual_pnl(self, equity_curve: pd.DataFrame) -> pd.DataFrame:
        """Generate annual PnL breakdown"""
        equity_curve['year'] = equity_curve['date'].dt.year
        
        annual = equity_curve.groupby('year').agg({
            'equity': ['first', 'last', 'min', 'max']
        })
        
        annual.columns = ['start_equity', 'end_equity', 'min_equity', 'max_equity']
        annual['pnl'] = annual['end_equity'] - annual['start_equity']
        annual['return_pct'] = (annual['end_equity'] / annual['start_equity'] - 1) * 100
        annual['max_dd_pct'] = (annual['min_equity'] / annual['max_equity'] - 1) * 100
        
        return annual.reset_index()


class DailyTrendHysteresisSimulator(StrategySimulator):
    """Simulator for Daily Trend Hysteresis strategy"""
    
    def __init__(self, symbol: str, rsi_period: int, upper_band: int, lower_band: int, **kwargs):
        super().__init__(**kwargs)
        self.symbol = symbol
        self.rsi_period = rsi_period
        self.upper_band = upper_band
        self.lower_band = lower_band
        
    def calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def simulate(self, price_data: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """
        Run simulation on price data
        
        Args:
            price_data: DataFrame with columns ['date', 'close']
        
        Returns:
            Tuple of (equity_curve, statistics)
        """
        # Calculate RSI
        price_data['rsi'] = self.calculate_rsi(price_data['close'], self.rsi_period)
        
        # Generate signals
        position = 0  # 0 = flat, 1 = long
        equity = self.initial_capital
        trades = []
        equity_curve = []
        
        for i in range(len(price_data)):
            row = price_data.iloc[i]
            
            if pd.isna(row['rsi']):
                equity_curve.append({'date': row['date'], 'equity': equity, 'position': position})
                continue
            
            # Hysteresis logic
            if row['rsi'] > self.upper_band and position == 0:
                # Enter long
                position = 1
                entry_price = row['close']
                entry_date = row['date']
                
            elif row['rsi'] < self.lower_band and position == 1:
                # Exit long
                exit_price = row['close']
                exit_date = row['date']
                trade_return = (exit_price / entry_price) - 1
                
                # Apply friction (5 bps round-trip)
                trade_return -= 0.0005
                
                equity *= (1 + trade_return)
                trades.append({
                    'entry_date': entry_date,
                    'exit_date': exit_date,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'return': trade_return,
                    'equity': equity
                })
                position = 0
            
            equity_curve.append({'date': row['date'], 'equity': equity, 'position': position})
        
        # Convert to DataFrames
        equity_df = pd.DataFrame(equity_curve)
        
        # Calculate statistics
        if len(trades) > 0:
            returns = pd.Series([t['return'] for t in trades])
            stats = self.calculate_statistics(returns)
        else:
            stats = self.calculate_statistics(pd.Series([]))
        
        stats['final_equity'] = equity
        stats['total_pnl'] = equity - self.initial_capital
        
        return equity_df, stats, trades


class HourlySwingSimulator(StrategySimulator):
    """Simulator for Hourly Swing strategy"""
    
    def __init__(self, symbol: str, rsi_period: int, upper_band: int, lower_band: int, **kwargs):
        super().__init__(**kwargs)
        self.symbol = symbol
        self.rsi_period = rsi_period
        self.upper_band = upper_band
        self.lower_band = lower_band
    
    def calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def simulate(self, price_data: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """Run simulation on hourly price data"""
        # Calculate RSI
        price_data['rsi'] = self.calculate_rsi(price_data['close'], self.rsi_period)
        
        # Generate signals
        position = 0
        equity = self.initial_capital
        trades = []
        equity_curve = []
        
        for i in range(len(price_data)):
            row = price_data.iloc[i]
            
            if pd.isna(row['rsi']):
                equity_curve.append({'date': row['date'], 'equity': equity, 'position': position})
                continue
            
            # Hysteresis logic (same as daily)
            if row['rsi'] > self.upper_band and position == 0:
                position = 1
                entry_price = row['close']
                entry_date = row['date']
                
            elif row['rsi'] < self.lower_band and position == 1:
                exit_price = row['close']
                exit_date = row['date']
                trade_return = (exit_price / entry_price) - 1
                
                # Apply friction (5 bps)
                trade_return -= 0.0005
                
                equity *= (1 + trade_return)
                trades.append({
                    'entry_date': entry_date,
                    'exit_date': exit_date,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'return': trade_return,
                    'equity': equity
                })
                position = 0
            
            equity_curve.append({'date': row['date'], 'equity': equity, 'position': position})
        
        equity_df = pd.DataFrame(equity_curve)
        
        if len(trades) > 0:
            returns = pd.Series([t['return'] for t in trades])
            stats = self.calculate_statistics(returns)
        else:
            stats = self.calculate_statistics(pd.Series([]))
        
        stats['final_equity'] = equity
        stats['total_pnl'] = equity - self.initial_capital
        
        return equity_df, stats, trades


class FOMCStraddleSimulator(StrategySimulator):
    """Simulator for FOMC Event Straddles"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def simulate(self, fomc_events: List[Dict]) -> Tuple[pd.DataFrame, Dict]:
        """
        Simulate FOMC straddle trades
        
        Args:
            fomc_events: List of dicts with keys ['date', 'spy_move', 'pnl_pct']
        """
        equity = self.initial_capital
        trades = []
        equity_curve = []
        
        for event in fomc_events:
            # Each trade returns pnl_pct on the capital
            trade_return = event['pnl_pct'] / 100
            
            # Apply friction (minimal for options, ~2 bps)
            trade_return -= 0.0002
            
            equity *= (1 + trade_return)
            
            trades.append({
                'date': event['date'],
                'spy_move': event['spy_move'],
                'return': trade_return,
                'equity': equity
            })
            
            equity_curve.append({'date': pd.to_datetime(event['date']), 'equity': equity, 'position': 0})
        
        equity_df = pd.DataFrame(equity_curve)
        
        if len(trades) > 0:
            returns = pd.Series([t['return'] for t in trades])
            stats = self.calculate_statistics(returns)
        else:
            stats = self.calculate_statistics(pd.Series([]))
        
        stats['final_equity'] = equity
        stats['total_pnl'] = equity - self.initial_capital
        
        return equity_df, stats, trades


class EarningsStraddleSimulator(StrategySimulator):
    """Simulator for Earnings Straddles"""
    
    def __init__(self, symbol: str, **kwargs):
        super().__init__(**kwargs)
        self.symbol = symbol
    
    def simulate(self, earnings_events: List[Dict]) -> Tuple[pd.DataFrame, Dict]:
        """
        Simulate earnings straddle trades
        
        Args:
            earnings_events: List of dicts with keys ['date', 'move_pct', 'pnl_pct']
        """
        equity = self.initial_capital
        trades = []
        equity_curve = []
        
        for event in earnings_events:
            # Each trade returns pnl_pct on the capital
            trade_return = event['pnl_pct'] / 100
            
            # Apply friction (~5 bps for options)
            trade_return -= 0.0005
            
            equity *= (1 + trade_return)
            
            trades.append({
                'date': event['date'],
                'move_pct': event['move_pct'],
                'return': trade_return,
                'equity': equity
            })
            
            equity_curve.append({'date': pd.to_datetime(event['date']), 'equity': equity, 'position': 0})
        
        equity_df = pd.DataFrame(equity_curve)
        
        if len(trades) > 0:
            returns = pd.Series([t['return'] for t in trades])
            stats = self.calculate_statistics(returns)
        else:
            stats = self.calculate_statistics(pd.Series([]))
        
        stats['final_equity'] = equity
        stats['total_pnl'] = equity - self.initial_capital
        
        return equity_df, stats, trades
