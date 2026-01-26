#!/usr/bin/env python3
"""
Phase 1.1: Baseline Backtest (2024-2025)
Intraday Alpha Strategy - Clean Room Test

Tests the V1.0 "Laminar DNA" strategy on SPY/QQQ/IWM with:
- Period: Jan 1, 2024 → Jan 10, 2026
- Standard execution assumptions (+1 bar lag, 5 bps slippage)
- $25,000 initial capital
- FMP sentiment data (if available)

This is the "smoke test" to determine if there's a viable core before
investing in the full 6-phase testing battery.
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()  # Loads from current directory's .env file

# Map credential variable names if needed
# The .env might use ALPACA_* but SDK expects APCA_*
if not os.getenv('APCA_API_KEY_ID') and os.getenv('ALPACA_API_KEY'):
    os.environ['APCA_API_KEY_ID'] = os.getenv('ALPACA_API_KEY')
if not os.getenv('APCA_API_SECRET_KEY') and os.getenv('ALPACA_SECRET_KEY'):
    os.environ['APCA_API_SECRET_KEY'] = os.getenv('ALPACA_SECRET_KEY')
if not os.getenv('APCA_API_BASE_URL'):
    os.environ['APCA_API_BASE_URL'] = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from src.features import calculate_rsi
from src.data_cache import DataCache
from sentiment_cache import SentimentCache


class IntradayAlphaBacktest:
    """Clean-room backtest of Intraday Alpha V1.0 strategy"""
    
    def __init__(self, config_path, start_date, end_date, initial_capital=25000):
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.capital = initial_capital
        
        # Load strategy configuration
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.symbols = self.config['symbols']
        self.params = self.config['strategy_parameters']
        
        # Initialize data cache (automatically uses Magellan's data infrastructure)
        # Credentials loaded from environment variables: APCA_API_KEY_ID, APCA_API_SECRET_KEY, APCA_API_BASE_URL
        self.data_cache = DataCache()
        print("📦 Using Magellan DataCache infrastructure")
        
        # Initialize sentiment cache
        self.sentiment_cache = SentimentCache()
        self.sentiment_data = {}  # Will store {symbol: DataFrame} with date->sentiment mapping
        print("📰 Loading sentiment data...")
        for symbol in self.symbols:
            # Convert datetime to string format for sentiment cache
            start_str = start_date.strftime('%Y-%m-%d') if hasattr(start_date, 'strftime') else str(start_date)
            end_str = end_date.strftime('%Y-%m-%d') if hasattr(end_date, 'strftime') else str(end_date)
            sent_df = self.sentiment_cache.get_or_fetch(symbol, start_str, end_str)
            self.sentiment_data[symbol] = sent_df.set_index('date')['sentiment'].to_dict()
            non_zero = sum(1 for v in self.sentiment_data[symbol].values() if v != 0)
            print(f"   {symbol}: {len(sent_df)} days ({non_zero} non-zero)")
        
        # Trading state
        self.positions = {}  # {symbol: {'qty': X, 'entry_price': Y, 'entry_time': Z}}
        self.trades = []  # List of completed trades
        self.equity_curve = []  # Daily equity tracking
        
        # Execution assumptions
        self.slippage_bps = 5  # 5 basis points per trade
        
    def fetch_data(self, symbol, interval):
        """Fetch historical data for a symbol at specified interval"""
        print(f"📥 Fetching data for {symbol} ({interval})...")
        
        # Use DataCache to get 1-minute data (handles caching automatically)
        df = self.data_cache.get_or_fetch_equity(
            symbol,
            timeframe="1min",
            start=(self.start_date - timedelta(days=10)).strftime("%Y-%m-%d"),
            end=self.end_date.strftime("%Y-%m-%d"),
            feed="sip"
        )
        
        # Resample to target interval
        if interval == "3Min":
            df = df.resample('3T').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
        elif interval == "5Min":
            df = df.resample('5T').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
        elif interval == "15Min":
            df = df.resample('15T').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
        elif interval == "1Hour":
            df = df.resample('1H').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
        else:
            raise ValueError(f"Unsupported interval: {interval}")
        
        print(f"✅ Fetched {len(df)} bars for {symbol}")
        return df
    
    def calculate_alpha_score(self, symbol, df_row_index, df):
        """
        Calculate multi-factor alpha score at a specific timestamp.
        
        Uses data UP TO (but not including) the current bar to avoid look-ahead bias.
        """
        params = self.params[symbol]
        
        # Get historical data up to (not including) current bar
        hist_data = df.loc[:df_row_index].iloc[:-1]
        
        if len(hist_data) < params['rsi_lookback'] + 20:  # Need warmup
            return 0.0, None, None  # Not enough data
        
        # Calculate RSI
        rsi = calculate_rsi(hist_data['close'], period=params['rsi_lookback'])
        current_rsi = rsi.iloc[-1]
        
        # Normalize RSI to [-1, 1] range (RSI > 50 = positive signal)
        rsi_signal = (current_rsi - 50) / 50.0
        
        # Volume signal (compare to 20-bar moving average)
        vol_ma = hist_data['volume'].rolling(window=20).mean()
        current_vol = hist_data['volume'].iloc[-1]
        vol_ratio = current_vol / vol_ma.iloc[-1] if vol_ma.iloc[-1] > 0 else 1.0
        vol_signal = min(max((vol_ratio - 1.0), -1.0), 1.0)
        
        # Sentiment signal (from FMP news data)
        # df_row_index is already a timestamp
        current_date = df_row_index.date() if hasattr(df_row_index, 'date') else df_row_index
        sent_signal = self.sentiment_data[symbol].get(current_date, 0.0)
        
        # Combine signals with weights
        alpha = (
            params['rsi_wt'] * rsi_signal +
            params['vol_wt'] * vol_signal +
            params['sent_wt'] * sent_signal
        )
        
        # Apply sentry gate (sentiment threshold)
        sentiment = sent_signal
        if sentiment < params['sentry_gate']:
            alpha = 0.0  # Kill alpha if sentiment below gate
            alpha = 0.0  # Kill alpha if sentiment below gate
        
        return alpha, current_rsi, vol_ratio
    
    def generate_signal(self, symbol, df_row_index, df):
        """
        Generate trading signal based on configured strategy logic.
        
        Strategy Types:
        - 'momentum' (Default): Buy when Alpha > buy_threshold, Sell when Alpha < sell_threshold
        - 'reversion': Buy when Alpha < buy_threshold (Oversold), Sell when Alpha > sell_threshold (Overbought)
        """
        alpha, rsi, vol_ratio = self.calculate_alpha_score(symbol, df_row_index, df)
        params = self.params[symbol]
        
        # Get thresholds (default to V1.0 hardcoded values if not in config)
        strategy_type = params.get('strategy_type', 'momentum')
        buy_threshold = params.get('buy_threshold', 0.5)
        sell_threshold = params.get('sell_threshold', -0.5)
        
        # Generate base signal based on strategy type
        signal = 0
        if strategy_type == 'momentum':
            if alpha > buy_threshold:
                signal = 1
            elif alpha < sell_threshold:
                signal = -1
        elif strategy_type == 'reversion':
            if alpha < buy_threshold:
                signal = 1
            elif alpha > sell_threshold:
                signal = -1
        
        # Apply Trend Filter (if enabled)
        # Block BUYs if Price < SMA
        if signal == 1 and params.get('use_trend_filter', False):
            # Get history
            hist_data = df.loc[:df_row_index].iloc[:-1]
            sma_period = params.get('trend_filter_period', 200)
            
            if len(hist_data) >= sma_period:
                sma = hist_data['close'].rolling(window=sma_period).mean().iloc[-1]
                current_price = hist_data['close'].iloc[-1]
                
                if current_price < sma:
                    signal = 0  # Veto the Buy
                    
        return signal, alpha, rsi, vol_ratio
    
    def execute_trade(self, symbol, signal, current_bar, next_bar):
        """
        Execute trade with +1 bar lag and slippage.
        
        Signal generated on current_bar close → Fill on next_bar open
        """
        if signal == 0:
            return  # No trade
        
        # Check if already have position
        has_position = symbol in self.positions
        
        if signal == 1 and not has_position:
            # BUY signal and no position → Enter long
            # Fill at next bar open + slippage
            fill_price = next_bar['open'] * (1 + self.slippage_bps / 10000)
            
            # Position sizing: 25% of capital, capped at config limit
            params = self.params[symbol]
            allocated_capital = self.capital * 0.25
            position_cap = params['position_cap_usd']
            
            if allocated_capital > position_cap:
                allocated_capital = position_cap
            
            # Calculate quantity
            qty = int(allocated_capital / fill_price)
            
            if qty < 1:
                return  # Position too small
            
            # Execute entry
            cost = qty * fill_price
            self.capital -= cost
            
            self.positions[symbol] = {
                'qty': qty,
                'entry_price': fill_price,
                'entry_time': next_bar.name,
                'entry_bar': current_bar.name  # Signal bar
            }
            
            print(f"  📈 LONG {symbol}: {qty} shares @ ${fill_price:.2f} (cost: ${cost:,.2f})")
        
        elif signal == -1 and has_position:
            # SELL signal and have position → Exit long
            # Fill at next bar open - slippage (adverse for exit)
            fill_price = next_bar['open'] * (1 - self.slippage_bps / 10000)
            
            position = self.positions[symbol]
            qty = position['qty']
            entry_price = position['entry_price']
            
            # Execute exit
            proceeds = qty * fill_price
            self.capital += proceeds
            
            # Record trade
            pnl = proceeds - (qty * entry_price)
            pnl_pct = (fill_price - entry_price) / entry_price * 100
            hold_duration = next_bar.name - position['entry_time']
            
            trade = {
                'symbol': symbol,
                'entry_time': position['entry_time'],
                'exit_time': next_bar.name,
                'entry_price': entry_price,
                'exit_price': fill_price,
                'qty': qty,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'hold_duration': hold_duration
            }
            self.trades.append(trade)
            
            print(f"  📉 EXIT {symbol}: {qty} shares @ ${fill_price:.2f} | PnL: ${pnl:+,.2f} ({pnl_pct:+.2f}%) | Hold: {hold_duration}")
            
            # Remove position
            del self.positions[symbol]
    
    def run_backtest(self):
        """Execute full backtest across all symbols and timeframe"""
        print(f"\n{'='*80}")
        print(f"🚀 PHASE 1.1: BASELINE BACKTEST (2024-2025)")
        print(f"{'='*80}")
        print(f"Period: {self.start_date.date()} → {self.end_date.date()}")
        print(f"Symbols: {', '.join(self.symbols)}")
        print(f"Initial Capital: ${self.initial_capital:,.2f}")
        print(f"Slippage: {self.slippage_bps} bps per trade")
        print(f"{'='*80}\n")
        
        # Fetch data for all symbols
        data = {}
        for symbol in self.symbols:
            interval = self.params[symbol]['interval']
            data[symbol] = self.fetch_data(symbol, interval)
        
        # Get unified timeline (all bar timestamps across symbols)
        all_timestamps = set()
        for df in data.values():
            all_timestamps.update(df.index)
        
        timeline = sorted(all_timestamps)
        timeline = [ts for ts in timeline if self.start_date <= ts <= self.end_date]
        
        print(f"\n📊 Processing {len(timeline)} bars across {len(self.symbols)} symbols...")
        print(f"{'='*80}\n")
        
        # Main backtest loop
        for i, current_time in enumerate(timeline[:-1]):  # -1 because we need next bar
            next_time = timeline[i + 1]
            
            # Process each symbol at this timestamp
            for symbol in self.symbols:
                df = data[symbol]
                
                # Check if this symbol has data at current_time
                if current_time not in df.index:
                    continue
                
                # Get current and next bar
                try:
                    current_bar = df.loc[current_time]
                    next_bar = df.loc[next_time] if next_time in df.index else None
                except KeyError:
                    continue
                
                if next_bar is None:
                    continue
                
                # Generate signal
                signal, alpha, rsi, vol_ratio = self.generate_signal(symbol, current_time, df)
                
                # Execute trade logic (Entry, Exit, TP, SL)
                self.execute_trade(symbol, signal, current_bar, next_bar)
                
            # Log progress to console every 30 days of data (approx 2340 bars) for visibility
            if i % 2340 == 0:
                percent_complete = (i / len(timeline)) * 100
                current_date = current_time.date()
                print(f"⏳ Progress: {percent_complete:.1f}% ({current_date}) | Equity: ${self.capital:,.0f}")
        
        # Force close all remaining positions at end
        print(f"\n{'='*80}")
        print("🔒 Closing all remaining positions at test end...")
        print(f"{'='*80}\n")
        
        for symbol in list(self.positions.keys()):
            df = data[symbol]
            final_bar = df.iloc[-1]
            fill_price = final_bar['close'] * (1 - self.slippage_bps / 10000)
            
            position = self.positions[symbol]
            qty = position['qty']
            entry_price = position['entry_price']
            
            proceeds = qty * fill_price
            self.capital += proceeds
            
            pnl = proceeds - (qty * entry_price)
            pnl_pct = (fill_price - entry_price) / entry_price * 100
            
            trade = {
                'symbol': symbol,
                'entry_time': position['entry_time'],
                'exit_time': final_bar.name,
                'entry_price': entry_price,
                'exit_price': fill_price,
                'qty': qty,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'exit_reason': 'Force Close'
            }
            self.trades.append(trade)
            
            print(f"  📉 FORCE EXIT {symbol}: {qty} shares @ ${fill_price:.2f} | PnL: {pnl_pct:+.2f}%")
        
        self.positions = {}

    def execute_trade(self, symbol, signal, current_bar, next_bar):
        """
        Execute trade with advanced management (TP, SL, Time-based)
        """
        # Check if already have position
        has_position = symbol in self.positions
        
        # Get parameters
        params = self.params[symbol]
        tp_pct = params.get('take_profit_pct', 0.0)
        sl_pct = params.get('stop_loss_pct', 0.0)
        
        # --- ENTRY LOGIC ---
        if signal == 1 and not has_position:
            # BUY signal and no position → Enter long
            fill_price = next_bar['open'] * (1 + self.slippage_bps / 10000)
            
            # Position sizing
            allocated_capital = self.capital * 0.25
            position_cap = params.get('position_cap_usd', 50000)
            if allocated_capital > position_cap:
                allocated_capital = position_cap
            
            qty = int(allocated_capital / fill_price)
            if qty < 1: return
            
            # Execute entry
            cost = qty * fill_price
            self.capital -= cost
            
            self.positions[symbol] = {
                'qty': qty,
                'entry_price': fill_price,
                'entry_time': next_bar.name,
                'entry_bar': current_bar.name,
                'high_water_mark': fill_price  # Track MFE
            }
            # print(f"  📈 LONG {symbol}: {qty} shares @ ${fill_price:.2f}")

        # --- EXIT / MANAGEMENT LOGIC ---
        elif has_position:
            position = self.positions[symbol]
            qty = position['qty']
            entry_price = position['entry_price']
            current_high = current_bar['high']
            current_low = current_bar['low']
            
            # Update High Water Mark
            if current_high > position['high_water_mark']:
                position['high_water_mark'] = current_high
            
            exit_reason = None
            exit_price = 0.0
            
            # 1. Take Profit Check (Intraday High > TP Target)
            if tp_pct > 0:
                target_price = entry_price * (1 + tp_pct)
                if current_high >= target_price:
                    exit_reason = "TP"
                    exit_price = target_price
            
            # 2. Stop Loss Check (Intraday Low < SL Target)
            if not exit_reason and sl_pct > 0:
                stop_price = entry_price * (1 - sl_pct)
                if current_low <= stop_price:
                    exit_reason = "SL"
                    exit_price = stop_price
            
            # 3. Signal Exit (Bearish Signal)
            if not exit_reason and signal == -1:
                exit_reason = "Signal"
                exit_price = next_bar['open'] * (1 - self.slippage_bps / 10000)
            
            # Execute Exit if Triggered
            if exit_reason:
                proceeds = qty * exit_price
                self.capital += proceeds
                
                pnl = proceeds - (qty * entry_price)
                pnl_pct = (exit_price - entry_price) / entry_price * 100
                hold_duration = next_bar.name - position['entry_time']
                
                trade = {
                    'symbol': symbol,
                    'entry_time': position['entry_time'],
                    'exit_time': next_bar.name,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'qty': qty,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'hold_duration': hold_duration,
                    'exit_reason': exit_reason
                }
                self.trades.append(trade)
                
                print(f"  📉 EXIT {symbol} ({exit_reason}): {qty} @ ${exit_price:.2f} | PnL: {pnl_pct:+.2f}%")
                
                del self.positions[symbol]
        

    
    def calculate_metrics(self):
        """Calculate comprehensive performance metrics"""
        if not self.trades:
            print("\n⚠️ WARNING: No trades executed!")
            return {
                'total_trades': 0,
                'final_equity': self.capital,
                'total_pnl': self.capital - self.initial_capital,
                'total_return_pct': (self.capital - self.initial_capital) / self.initial_capital * 100
            }
        
        df_trades = pd.DataFrame(self.trades)
        
        # Basic metrics
        total_trades = len(self.trades)
        winning_trades = len(df_trades[df_trades['pnl'] > 0])
        losing_trades = len(df_trades[df_trades['pnl'] < 0])
        win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
        
        total_pnl = df_trades['pnl'].sum()
        final_equity = self.capital
        total_return_pct = (final_equity - self.initial_capital) / self.initial_capital * 100
        
        # Profit factor
        gross_profit = df_trades[df_trades['pnl'] > 0]['pnl'].sum() if winning_trades > 0 else 0
        gross_loss = abs(df_trades[df_trades['pnl'] < 0]['pnl'].sum()) if losing_trades > 0 else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Average trade
        avg_win = df_trades[df_trades['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
        avg_loss = df_trades[df_trades['pnl'] < 0]['pnl'].mean() if losing_trades > 0 else 0
        avg_trade = df_trades['pnl'].mean()
        
        # Sharpe Ratio (annualized)
        returns = df_trades['pnl'].values
        if len(returns) > 1:
            # Estimate trading days (assume ~252 days, trades distributed)
            days_elapsed = (self.end_date - self.start_date).days
            trades_per_day = total_trades / max(days_elapsed, 1)
            
            mean_return = np.mean(returns)
            std_return = np.std(returns, ddof=1)
            
            if std_return > 0:
                sharpe = (mean_return / std_return) * np.sqrt(trades_per_day * 252)
            else:
                sharpe = 0.0
        else:
            sharpe = 0.0
        
        # Max Drawdown (from equity curve)
        if self.equity_curve:
            eq_series = pd.Series([e['equity'] for e in self.equity_curve])
            cummax = eq_series.cummax()
            drawdown = (eq_series - cummax) / cummax * 100
            max_drawdown = drawdown.min()
        else:
            max_drawdown = 0.0
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'total_pnl': total_pnl,
            'total_return_pct': total_return_pct,
            'final_equity': final_equity,
            'sharpe_ratio': sharpe,
            'profit_factor': profit_factor,
            'max_drawdown': max_drawdown,
            'gross_profit': gross_profit,
            'gross_loss': gross_loss,
            'avg_trade': avg_trade,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
        }
    
    def print_results(self, metrics):
        """Print formatted results"""
        print(f"\n{'='*80}")
        print(f"📊 BACKTEST RESULTS")
        print(f"{'='*80}\n")
        
        print(f"💰 FINANCIAL PERFORMANCE")
        print(f"  Initial Capital:    ${self.initial_capital:>12,.2f}")
        print(f"  Final Equity:       ${metrics['final_equity']:>12,.2f}")
        print(f"  Total P&L:          ${metrics['total_pnl']:>12,.2f}")
        print(f"  Total Return:       {metrics['total_return_pct']:>12.2f}%")
        print(f"  Sharpe Ratio:       {metrics['sharpe_ratio']:>12.2f}")
        print(f"  Max Drawdown:       {metrics['max_drawdown']:>12.2f}%")
        
        print(f"\n📈 TRADE STATISTICS")
        print(f"  Total Trades:       {metrics['total_trades']:>12,}")
        print(f"  Winning Trades:     {metrics['winning_trades']:>12,}")
        print(f"  Losing Trades:      {metrics['losing_trades']:>12,}")
        print(f"  Win Rate:           {metrics['win_rate']:>12.2f}%")
        print(f"  Profit Factor:      {metrics['profit_factor']:>12.2f}")
        
        print(f"\n💵 TRADE AVERAGES")
        print(f"  Avg Trade:          ${metrics['avg_trade']:>12,.2f}")
        print(f"  Avg Win:            ${metrics['avg_win']:>12,.2f}")
        print(f"  Avg Loss:           ${metrics['avg_loss']:>12,.2f}")
        print(f"  Gross Profit:       ${metrics['gross_profit']:>12,.2f}")
        print(f"  Gross Loss:         ${metrics['gross_loss']:>12,.2f}")
        
        print(f"\n{'='*80}")
        print(f"🚦 PHASE 1.1 ASSESSMENT")
        print(f"{'='*80}\n")
        
        # Gate checks
        gates_passed = 0
        gates_total = 5
        
        print("Gate Checks:")
        
        # Gate 1: Sharpe > 1.0
        if metrics['sharpe_ratio'] > 1.0:
            print("  ✅ Sharpe Ratio > 1.0")
            gates_passed += 1
        else:
            print(f"  ❌ Sharpe Ratio < 1.0 (actual: {metrics['sharpe_ratio']:.2f})")
        
        # Gate 2: Win Rate > 45%
        if metrics['win_rate'] > 45:
            print("  ✅ Win Rate > 45%")
            gates_passed += 1
        else:
            print(f"  ❌ Win Rate < 45% (actual: {metrics['win_rate']:.1f}%)")
        
        # Gate 3: Profit Factor > 1.3
        if metrics['profit_factor'] > 1.3:
            print("  ✅ Profit Factor > 1.3")
            gates_passed += 1
        else:
            print(f"  ❌ Profit Factor < 1.3 (actual: {metrics['profit_factor']:.2f})")
        
        # Gate 4: Max Drawdown < 20%
        if metrics['max_drawdown'] > -20:
            print("  ✅ Max Drawdown < 20%")
            gates_passed += 1
        else:
            print(f"  ❌ Max Drawdown > 20% (actual: {metrics['max_drawdown']:.1f}%)")
        
        # Gate 5: Trade Count > 100
        if metrics['total_trades'] > 100:
            print("  ✅ Trade Count > 100")
            gates_passed += 1
        else:
            print(f"  ❌ Trade Count < 100 (actual: {metrics['total_trades']})")
        
        print(f"\n{'='*80}")
        print(f"Gates Passed: {gates_passed}/{gates_total} ({gates_passed/gates_total*100:.0f}%)")
        print(f"{'='*80}\n")
        
        # Recommendation
        if gates_passed >= 4:
            print("✅ RECOMMENDATION: PASS - Proceed to full Phase 1-2 testing")
        elif gates_passed >= 3:
            print("⚠️ RECOMMENDATION: CONDITIONAL - Review results before proceeding")
        else:
            print("❌ RECOMMENDATION: FAIL - Consider early kill or strategy modification")
        
        print()
    
    def save_results(self, output_dir):
        """Save detailed results to CSV"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save trades
        if self.trades:
            trades_df = pd.DataFrame(self.trades)
            trades_path = output_dir / "phase1_baseline_trades.csv"
            trades_df.to_csv(trades_path, index=False)
            print(f"💾 Saved trades to: {trades_path}")
        
        # Save equity curve
        if self.equity_curve:
            equity_df = pd.DataFrame(self.equity_curve)
            equity_path = output_dir / "phase1_baseline_equity.csv"
            equity_df.to_csv(equity_path, index=False)
            print(f"💾 Saved equity curve to: {equity_path}")


def main():
    """Run Phase 1.1 baseline backtest"""
    
    # Set required environment variables for Magellan infrastructure
    # APCA_API_BASE_URL is required by AlpacaDataClient
    if not os.getenv('APCA_API_BASE_URL'):
        os.environ['APCA_API_BASE_URL'] = 'https://paper-api.alpaca.markets'  # Paper trading endpoint
    
    # Configuration
    if len(sys.argv) > 1:
        config_path = Path(sys.argv[1])
    else:
        config_path = Path(__file__).parent / "config.json"
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2026, 1, 10)  # Original deployment date
    initial_capital = 25000  # User's target allocation
    
    # Run backtest
    backtest = IntradayAlphaBacktest(config_path, start_date, end_date, initial_capital)
    backtest.run_backtest()
    
    # Calculate and display results
    metrics = backtest.calculate_metrics()
    backtest.print_results(metrics)
    
    # Save results
    output_dir = Path(__file__).parent / "results"
    backtest.save_results(output_dir)
    
    return metrics


if __name__ == "__main__":
    main()
