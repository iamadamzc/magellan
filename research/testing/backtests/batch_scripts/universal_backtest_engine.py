"""
UNIVERSAL BACKTEST ENGINE - CLEAN ROOM TESTING
Parameterized testing framework for all Magellan strategies

Supports:
- Strategy 1: Daily Trend Hysteresis (RSI 55/45)
- Strategy 2: Hourly Swing (RSI 60/40)
- Strategy 3: Earnings Volatility (T-2 to T+1)
- Strategy 4: FOMC Event Volatility (±5 min)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path
import json
import argparse

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_handler import AlpacaDataClient
from alpaca.data.timeframe import TimeFrame
import requests
import os


class UniversalBacktester:
    """Universal backtesting engine for all Magellan strategies"""
    
    def __init__(self, config):
        self.config = config
        self.strategy_type = config['strategy_type']
        self.symbol = config['symbol']
        self.asset_type = config['asset_type']
        self.test_periods = config['test_periods']
        self.friction_scenarios = config['friction_scenarios']
        
    def calculate_rsi(self, prices, period=14):
        """Calculate RSI using standard Wilder's smoothing"""
        delta = prices.diff()
        gains = delta.where(delta > 0, 0.0)
        losses = (-delta).where(delta < 0, 0.0)
        
        avg_gain = gains.ewm(span=period, adjust=False).mean()
        avg_loss = losses.ewm(span=period, adjust=False).mean()
        
        rs = avg_gain / avg_loss.replace(0, np.inf)
        rsi = 100 - (100 / (1 + rs))
        
        rsi = rsi.replace([np.inf, -np.inf], np.nan)
        rsi = rsi.fillna(50)
        
        return rsi
    
    def fetch_data(self, symbol, timeframe, start, end, asset_type):
        """Fetch data based on asset type"""
        
        if asset_type in ['equity', 'etf']:
            # Use Alpaca for equities and ETFs
            client = AlpacaDataClient()
            
            if timeframe == 'daily':
                tf = TimeFrame.Day
            elif timeframe == 'hourly':
                tf = TimeFrame.Hour
            elif timeframe == '1min':
                tf = TimeFrame.Minute
            else:
                raise ValueError(f"Unsupported timeframe: {timeframe}")
            
            df = client.fetch_historical_bars(
                symbol=symbol,
                timeframe=tf,
                start=start,
                end=end,
                feed='sip'
            )
            
            # Resample to ensure correct timeframe
            if timeframe == 'daily':
                df = df.resample('1D').agg({
                    'open': 'first',
                    'high': 'max',
                    'low': 'min',
                    'close': 'last',
                    'volume': 'sum'
                }).dropna()
            elif timeframe == 'hourly':
                df = df.resample('1H').agg({
                    'open': 'first',
                    'high': 'max',
                    'low': 'min',
                    'close': 'last',
                    'volume': 'sum'
                }).dropna()
            
            return df
            
        elif asset_type == 'crypto':
            # Use FMP for crypto
            api_key = os.getenv('FMP_API_KEY')
            
            if timeframe == 'daily':
                endpoint = f"https://financialmodelingprep.com/stable/historical-price-eod/full/{symbol}"
            elif timeframe == 'hourly':
                endpoint = f"https://financialmodelingprep.com/stable/historical-chart/1hour"
            else:
                raise ValueError(f"Unsupported crypto timeframe: {timeframe}")
            
            params = {'apikey': api_key, 'from': start, 'to': end}
            if timeframe == 'hourly':
                params['symbol'] = symbol
            
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            
            data = response.json()
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date').sort_index()
            
            return df[['open', 'high', 'low', 'close', 'volume']]
            
        elif asset_type == 'futures':
            # Use FMP for futures
            api_key = os.getenv('FMP_API_KEY')
            
            # Map common symbols to FMP format
            symbol_map = {
                'ES': 'ESUSD',
                'NQ': 'NQUSD',
                'CL': 'CLUSD',
                'GC': 'GCUSD',
                'SI': 'SIUSD'
            }
            
            fmp_symbol = symbol_map.get(symbol, symbol)
            
            if timeframe == 'hourly':
                endpoint = f"https://financialmodelingprep.com/stable/historical-chart/1hour"
            elif timeframe == 'daily':
                endpoint = f"https://financialmodelingprep.com/stable/historical-price-eod/full/{fmp_symbol}"
            else:
                raise ValueError(f"Unsupported futures timeframe: {timeframe}")
            
            params = {'apikey': api_key, 'from': start, 'to': end}
            if timeframe == 'hourly':
                params['symbol'] = fmp_symbol
            
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            
            data = response.json()
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date').sort_index()
            
            return df[['open', 'high', 'low', 'close', 'volume']]
        
        else:
            raise ValueError(f"Unsupported asset type: {asset_type}")
    
    def run_rsi_strategy(self, df, entry_threshold, exit_threshold, friction_bps, position_size):
        """Run RSI crossover strategy"""
        
        # Calculate RSI
        df['rsi'] = self.calculate_rsi(df['close'], period=28)
        df['rsi_prev'] = df['rsi'].shift(1)
        
        # Initialize tracking
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
            
            if pd.isna(current_rsi) or pd.isna(prev_rsi):
                equity_curve.append(cash)
                continue
            
            # ENTRY: Strict crossover above threshold
            if position == 'flat':
                if prev_rsi <= entry_threshold and current_rsi > entry_threshold:
                    friction_cost = (friction_bps / 10000) * current_price * position_size
                    entry_price = current_price
                    entry_date = current_date
                    position = 'long'
                    cash -= (current_price * position_size + friction_cost)
            
            # EXIT: Strict crossover below threshold
            elif position == 'long':
                if prev_rsi >= exit_threshold and current_rsi < exit_threshold:
                    friction_cost = (friction_bps / 10000) * current_price * position_size
                    proceeds = current_price * position_size - friction_cost
                    pnl_dollars = proceeds - (entry_price * position_size)
                    pnl_pct = ((current_price / entry_price) - 1) * 100
                    hold_time = (current_date - entry_date).total_seconds() / 3600
                    
                    trades.append({
                        'entry_date': entry_date,
                        'exit_date': current_date,
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'pnl_dollars': pnl_dollars,
                        'pnl_pct': pnl_pct,
                        'hold_hours': hold_time
                    })
                    
                    cash += proceeds
                    position = 'flat'
                    entry_price = None
                    entry_date = None
            
            # Track equity
            if position == 'long':
                unrealized_pnl = (current_price - entry_price) * position_size
                equity_curve.append(cash + unrealized_pnl)
            else:
                equity_curve.append(cash)
        
        # Close any open position
        if position == 'long':
            current_price = df.iloc[-1]['close']
            current_date = df.index[-1]
            friction_cost = (friction_bps / 10000) * current_price * position_size
            proceeds = current_price * position_size - friction_cost
            pnl_dollars = proceeds - (entry_price * position_size)
            pnl_pct = ((current_price / entry_price) - 1) * 100
            hold_time = (current_date - entry_date).total_seconds() / 3600
            
            trades.append({
                'entry_date': entry_date,
                'exit_date': current_date,
                'entry_price': entry_price,
                'exit_price': current_price,
                'pnl_dollars': pnl_dollars,
                'pnl_pct': pnl_pct,
                'hold_hours': hold_time
            })
            
            cash += proceeds
        
        return self.calculate_metrics(trades, equity_curve, initial_capital, df)
    
    def calculate_metrics(self, trades, equity_curve, initial_capital, df):
        """Calculate performance metrics"""
        
        if not equity_curve:
            return None
        
        final_equity = equity_curve[-1]
        total_return = ((final_equity / initial_capital) - 1) * 100
        
        # Buy & Hold
        bh_return = ((df.iloc[-1]['close'] / df.iloc[0]['close']) - 1) * 100
        
        # Max Drawdown
        equity_series = pd.Series(equity_curve)
        running_max = equity_series.expanding().max()
        drawdown = (equity_series - running_max) / running_max
        max_dd = drawdown.min() * 100
        
        # Sharpe Ratio
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
            profit_factor = abs(winning_trades['pnl_dollars'].sum() / losing_trades['pnl_dollars'].sum()) if len(losing_trades) > 0 and losing_trades['pnl_dollars'].sum() != 0 else np.inf
        else:
            trades_df = pd.DataFrame()
            win_rate = 0
            avg_win = 0
            avg_loss = 0
            profit_factor = 0
        
        return {
            'total_return': total_return,
            'bh_return': bh_return,
            'max_dd': max_dd,
            'sharpe': sharpe,
            'total_trades': len(trades),
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'trades_df': trades_df,
            'equity_curve': equity_series
        }
    
    def run(self):
        """Execute backtest for all periods and friction scenarios"""
        
        print(f"\n{'=' * 80}")
        print(f"UNIVERSAL BACKTEST: {self.config['name']}")
        print(f"{'=' * 80}")
        print(f"Symbol: {self.symbol}")
        print(f"Strategy: {self.strategy_type}")
        print(f"Asset Type: {self.asset_type}")
        print(f"{'=' * 80}\n")
        
        all_results = []
        
        for period in self.test_periods:
            print(f"\n{'#' * 80}")
            print(f"TEST PERIOD: {period['name']} ({period['start']} to {period['end']})")
            print(f"{'#' * 80}\n")
            
            try:
                # Fetch data
                df = self.fetch_data(
                    self.symbol,
                    self.config['timeframe'],
                    period['start'],
                    period['end'],
                    self.asset_type
                )
                
                print(f"✓ Fetched {len(df)} bars")
                
                # Run for each friction scenario
                for friction_name, friction_bps in self.friction_scenarios.items():
                    print(f"\nRunning: {period['name']} - {friction_name} ({friction_bps} bps)")
                    
                    result = self.run_rsi_strategy(
                        df.copy(),
                        self.config['entry_threshold'],
                        self.config['exit_threshold'],
                        friction_bps,
                        self.config['position_size']
                    )
                    
                    if result:
                        result['test_name'] = f"{period['name']} - {friction_name}"
                        result['period'] = period['name']
                        result['friction'] = friction_name
                        all_results.append(result)
                        
                        print(f"  Return: {result['total_return']:+.2f}%")
                        print(f"  Sharpe: {result['sharpe']:.2f}")
                        print(f"  Trades: {result['total_trades']}")
                
            except Exception as e:
                print(f"❌ ERROR in {period['name']}: {str(e)}")
                import traceback
                traceback.print_exc()
        
        return all_results


def main():
    """Main execution"""
    
    parser = argparse.ArgumentParser(description='Universal Backtest Engine')
    parser.add_argument('--config', required=True, help='Path to config JSON file')
    args = parser.parse_args()
    
    # Load config
    with open(args.config, 'r') as f:
        config = json.load(f)
    
    # Run backtest
    backtester = UniversalBacktester(config)
    results = backtester.run()
    
    # Save results
    output_dir = Path(config['output_dir'])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save summary
    summary_df = pd.DataFrame([{
        'Test': r['test_name'],
        'Return (%)': f"{r['total_return']:+.2f}",
        'B&H (%)': f"{r.get('bh_return', 0):+.2f}",
        'Sharpe': f"{r['sharpe']:.2f}",
        'Max DD (%)': f"{r['max_dd']:.2f}",
        'Trades': r['total_trades'],
        'Win Rate (%)': f"{r['win_rate']:.1f}",
        'Profit Factor': f"{r['profit_factor']:.2f}"
    } for r in results])
    
    summary_df.to_csv(output_dir / 'summary.csv', index=False)
    print(f"\n✓ Results saved to: {output_dir}")
    print("\n" + summary_df.to_string(index=False))


if __name__ == '__main__':
    main()
