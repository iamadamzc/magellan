"""
Phase 2 Validation: SPY Baseline Backtest

Tests options strategy on SPY (2024-2026) with base parameters:
- Delta: 0.60 (slightly ITM for less theta decay)
- DTE: 45-60 days (balance theta vs roll frequency)
- RSI: 21 period with 58/42 hysteresis (proven from System 1)
- Slippage: 1.0% (realistic for liquid SPY options)

Success Criteria:
- Sharpe ratio > 1.0
- Total return > SPY buy-hold
- Max drawdown < 50% (vs 100% = total wipeout)
- Win rate > 55%
- No temporal leaks

Run: python research/backtests/options/phase2_validation/test_spy_baseline.py

Expected Runtime: 5-10 minutes
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_handler import AlpacaDataClient
from src.features import calculate_rsi
from src.options.features import OptionsFeatureEngineer
from src.logger import LOG

# Set logger to normal verbosity
LOG.verbosity = LOG.NORMAL


class SPYOptionsBacktester:
    """
    Backtest SPY options strategy with System 1 (Daily Hysteresis) signals.
    
    Strategy:
    - RSI > 58: Buy CALL (delta 0.60, 45-60 DTE)
    - RSI < 42: Buy PUT (delta 0.60, 45-60 DTE)
    - 42 <= RSI <= 58: Close all options, hold cash
    - Auto-roll when DTE < 7
    """
    
    def __init__(self, config: dict):
        """
        Initialize backtester.
        
        Args:
            config: Backtest configuration dict
        """
        self.config = config
        self.initial_capital = config.get('initial_capital', 100000)
        self.target_notional = config.get('target_notional', 10000)
        self.slippage_pct = config.get('slippage_pct', 1.0)
        self.contract_fee = config.get('contract_fee', 0.097)
        
        # Strategy params
        self.rsi_period = config.get('rsi_period', 21)
        self.rsi_buy_threshold = config.get('rsi_buy_threshold', 58)
        self.rsi_sell_threshold = config.get('rsi_sell_threshold', 42)
        self.target_delta = config.get('target_delta', 0.60)
        self.min_dte = config.get('min_dte', 45)
        self.max_dte = config.get('max_dte', 60)
        self.roll_threshold_dte = config.get('roll_threshold_dte', 7)
        
        LOG.event(f"[BACKTEST] Initialized SPY Options Backtest")
        LOG.event(f"  Capital: ${self.initial_capital:,.0f}")
        LOG.event(f"  RSI: {self.rsi_period} period, {self.rsi_buy_threshold}/{self.rsi_sell_threshold} thresholds")
        LOG.event(f"  Delta: {self.target_delta}, DTE: {self.min_dte}-{self.max_dte}")
        LOG.event(f"  Slippage: {self.slippage_pct}%, Fees: ${self.contract_fee}/contract\n")
    
    def fetch_spy_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch SPY daily OHLCV data."""
        LOG.flow("[DATA] Fetching SPY daily bars...")
        
        alpaca = AlpacaDataClient()
        df = alpaca.fetch_historical_bars(
            symbol='SPY',
            timeframe='1Day',
            start=start_date,
            end=end_date
        )
        
        if df is None or len(df) == 0:
            raise ValueError("Failed to fetch SPY data")
        
        LOG.success(f"[DATA] Fetched {len(df)} daily bars ({df.index[0]} to {df.index[-1]})")
        
        return df
    
    def calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate RSI and generate BUY/SELL/HOLD signals.
        
        Returns:
            DataFrame with 'rsi' and 'signal' columns
        """
        LOG.flow("[SIGNALS] Calculating RSI and hysteresis signals...")
        
        # Calculate RSI
        df['rsi'] = calculate_rsi(df['close'], period=self.rsi_period)
        
        # Hysteresis logic (Schmidt Trigger) - FIXED VERSION
        signals = []
        current_position = 'HOLD'  # Start in cash
        
        for idx, row in df.iterrows():
            rsi = row['rsi']
            
            if pd.isna(rsi):
                signals.append('HOLD')
                continue
            
            # State transitions with TRUE hysteresis
            if rsi > self.rsi_buy_threshold:
                # Strong bullish signal → Enter call
                current_position = 'BUY'
            elif rsi < self.rsi_sell_threshold:
                # Strong bearish signal → Enter put
                current_position = 'SELL'
            elif self.rsi_sell_threshold <= rsi <= self.rsi_buy_threshold:
                # Quiet zone (42-58) → Exit to cash to avoid theta decay
                # This is the KEY fix: don't maintain position in neutral zone!
                if current_position in ['BUY', 'SELL']:
                    current_position = 'HOLD'
            # else: maintain current_position if outside all zones (shouldn't happen)
            
            signals.append(current_position)
        
        df['signal'] = signals
        
        # Count signals
        buy_count = (df['signal'] == 'BUY').sum()
        sell_count = (df['signal'] == 'SELL').sum()
        hold_count = (df['signal'] == 'HOLD').sum()
        
        LOG.success(f"[SIGNALS] Generated {len(df)} signals:")
        LOG.event(f"  BUY (calls): {buy_count} days ({buy_count/len(df)*100:.1f}%)")
        LOG.event(f"  SELL (puts): {sell_count} days ({sell_count/len(df)*100:.1f}%)")
        LOG.event(f"  HOLD (cash): {hold_count} days ({hold_count/len(df)*100:.1f}%)\n")
        
        return df
    
    def simulate_options_trading(self, df: pd.DataFrame) -> dict:
        """
        Simulate options trading with realistic friction.
        
        Simplified backtest logic:
        - Uses Black-Scholes to estimate option prices
        - Applies slippage and fees
        - Tracks position P&L daily
        - Auto-rolls when DTE < 7
        
        Returns:
            Dictionary with backtest results
        """
        LOG.event("[BACKTEST] Starting simulation...\n")
        
        # Initialize tracking
        cash = self.initial_capital
        position = None  # Current options position
        equity_curve = []
        trades = []
        
        # Risk-free rate assumption (for Black-Scholes)
        r = 0.04
        
        # IV assumption (simplified - in reality, fetch from market)
        # SPY IV typically 15-25%, use 20% as baseline
        sigma = 0.20
        
        for date, row in df.iterrows():
            current_price = row['close']
            signal = row['signal']
            
            # Mark-to-market existing position
            position_value = 0
            if position:
                # Calculate current option value
                dte = (position['expiration'] - date).days
                T = max(dte / 365.0, 0.001)  # Avoid T=0
                
                greeks = OptionsFeatureEngineer.calculate_black_scholes_greeks(
                    S=current_price,
                    K=position['strike'],
                    T=T,
                    r=r,
                    sigma=sigma,
                    option_type=position['type']
                )
                
                current_option_price = greeks['price']
                position_value = current_option_price * position['contracts'] * 100
                
                # Check if need to roll
                if dte < self.roll_threshold_dte:
                    LOG.flow(f"[{date.date()}] Rolling position (DTE={dte})")
                    
                    # Close current position (sell at bid)
                    exit_price = current_option_price * (1 - self.slippage_pct / 100)
                    proceeds = exit_price * position['contracts'] * 100
                    fees = self.contract_fee * position['contracts']
                    cash += proceeds - fees
                    
                    # Record trade
                    pnl = proceeds - position['cost']
                    pnl_pct = (pnl / position['cost']) * 100
                    
                    trades.append({
                        'entry_date': position['entry_date'],
                        'exit_date': date,
                        'type': position['type'],
                        'strike': position['strike'],
                        'contracts': position['contracts'],
                        'entry_price': position['entry_price'],
                        'exit_price': exit_price,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'reason': 'ROLL'
                    })
                    
                    # Open new position with same signal
                    position = self._open_position(
                        date, current_price, signal, cash, r, sigma
                    )
                    
                    if position:
                        cash -= position['cost']
            
            # Handle signal changes
            if position is None and signal in ['BUY', 'SELL']:
                # Open new position
                position = self._open_position(
                    date, current_price, signal, cash, r, sigma
                )
                
                if position:
                    cash -= position['cost']
            
            elif position and signal == 'HOLD':
                # Close position (exit to cash)
                dte = (position['expiration'] - date).days
                T = max(dte / 365.0, 0.001)
                
                greeks = OptionsFeatureEngineer.calculate_black_scholes_greeks(
                    S=current_price,
                    K=position['strike'],
                    T=T,
                    r=r,
                    sigma=sigma,
                    option_type=position['type']
                )
                
                exit_price = greeks['price'] * (1 - self.slippage_pct / 100)
                proceeds = exit_price * position['contracts'] * 100
                fees = self.contract_fee * position['contracts']
                cash += proceeds - fees
                
                # Record trade
                pnl = proceeds - position['cost']
                pnl_pct = (pnl / position['cost']) * 100
                
                trades.append({
                    'entry_date': position['entry_date'],
                    'exit_date': date,
                    'type': position['type'],
                    'strike': position['strike'],
                    'contracts': position['contracts'],
                    'entry_price': position['entry_price'],
                    'exit_price': exit_price,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'reason': 'SIGNAL_EXIT'
                })
                
                LOG.flow(f"[{date.date()}] Closed {position['type']} position: P&L ${pnl:,.0f} ({pnl_pct:+.1f}%)")
                
                position = None
            
            elif position and signal in ['BUY', 'SELL']:
                # Signal changed (e.g., BUY → SELL or SELL → BUY)
                # Close old position first
                if (position['type'] == 'call' and signal == 'SELL') or \
                   (position['type'] == 'put' and signal == 'BUY'):
                    
                    dte = (position['expiration'] - date).days
                    T = max(dte / 365.0, 0.001)
                    
                    greeks = OptionsFeatureEngineer.calculate_black_scholes_greeks(
                        S=current_price,
                        K=position['strike'],
                        T=T,
                        r=r,
                        sigma=sigma,
                        option_type=position['type']
                    )
                    
                    exit_price = greeks['price'] * (1 - self.slippage_pct / 100)
                    proceeds = exit_price * position['contracts'] * 100
                    fees = self.contract_fee * position['contracts']
                    cash += proceeds - fees
                    
                    # Record trade
                    pnl = proceeds - position['cost']
                    pnl_pct = (pnl / position['cost']) * 100
                    
                    trades.append({
                        'entry_date': position['entry_date'],
                        'exit_date': date,
                        'type': position['type'],
                        'strike': position['strike'],
                        'contracts': position['contracts'],
                        'entry_price': position['entry_price'],
                        'exit_price': exit_price,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'reason': 'SIGNAL_CHANGE'
                    })
                    
                    LOG.flow(f"[{date.date()}] Signal changed, closed {position['type']}: P&L ${pnl:,.0f} ({pnl_pct:+.1f}%)")
                    
                    # Open new position with new signal
                    position = self._open_position(
                        date, current_price, signal, cash, r, sigma
                    )
                    
                    if position:
                        cash -= position['cost']
            
            # Calculate total equity
            total_equity = cash + position_value
            
            equity_curve.append({
                'date': date,
                'equity': total_equity,
                'cash': cash,
                'position_value': position_value,
                'spy_price': current_price
            })
        
        # Close any remaining position at end
        if position:
            final_date = df.index[-1]
            final_price = df.iloc[-1]['close']
            
            dte = (position['expiration'] - final_date).days
            T = max(dte / 365.0, 0.001)
            
            greeks = OptionsFeatureEngineer.calculate_black_scholes_greeks(
                S=final_price,
                K=position['strike'],
                T=T,
                r=r,
                sigma=sigma,
                option_type=position['type']
            )
            
            exit_price = greeks['price'] * (1 - self.slippage_pct / 100)
            proceeds = exit_price * position['contracts'] * 100
            fees = self.contract_fee * position['contracts']
            cash += proceeds - fees
            
            pnl = proceeds - position['cost']
            pnl_pct = (pnl / position['cost']) * 100
            
            trades.append({
                'entry_date': position['entry_date'],
                'exit_date': final_date,
                'type': position['type'],
                'strike': position['strike'],
                'contracts': position['contracts'],
                'entry_price': position['entry_price'],
                'exit_price': exit_price,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'reason': 'END_OF_BACKTEST'
            })
        
        # Calculate metrics
        equity_df = pd.DataFrame(equity_curve).set_index('date')
        metrics = self._calculate_metrics(equity_df, df, trades)
        
        return {
            'equity_curve': equity_df,
            'trades': pd.DataFrame(trades),
            'metrics': metrics
        }
    
    def _open_position(self, date, current_price, signal, available_cash, r, sigma):
        """Open new options position."""
        # Determine option type
        option_type = 'call' if signal == 'BUY' else 'put'
        
        # Calculate strike based on delta target
        # Delta approximation: 
        # - Call delta 0.50 (ATM) ≈ strike = spot
        # - Call delta 0.60 ≈ strike = spot * 0.92 (8% ITM)
        # - Call delta 0.70 ≈ strike = spot * 0.85 (15% ITM)
        # - Put delta -0.60 ≈ strike = spot * 1.08 (8% ITM)
        
        if option_type == 'call':
            # For calls: higher delta = lower strike (more ITM)
            if self.target_delta >= 0.70:
                strike_multiplier = 0.85  # Deep ITM
            elif self.target_delta >= 0.60:
                strike_multiplier = 0.92  # Moderately ITM
            else:  # delta 0.50
                strike_multiplier = 1.00  # ATM
        else:  # put
            # For puts: higher delta (in abs value) = higher strike (more ITM)
            if abs(self.target_delta) >= 0.70:
                strike_multiplier = 1.15  # Deep ITM
            elif abs(self.target_delta) >= 0.60:
                strike_multiplier = 1.08  # Moderately ITM
            else:  # delta 0.50
                strike_multiplier = 1.00  # ATM
        
        strike = current_price * strike_multiplier
        
        # Round strike to nearest $5
        strike = round(strike / 5) * 5
        
        # Calculate expiration (45-60 DTE, use 52 as midpoint)
        expiration = date + timedelta(days=52)
        T = 52 / 365.0
        
        # Calculate option price
        greeks = OptionsFeatureEngineer.calculate_black_scholes_greeks(
            S=current_price,
            K=strike,
            T=T,
            r=r,
            sigma=sigma,
            option_type=option_type
        )
        
        # Apply slippage (buy at ask)
        entry_price = greeks['price'] * (1 + self.slippage_pct / 100)
        
        # Calculate position size
        contracts = OptionsFeatureEngineer.calculate_position_size_contracts(
            target_notional=self.target_notional,
            current_price=current_price,
            delta=greeks['delta']
        )
        
        # Calculate cost
        premium_cost = entry_price * contracts * 100
        fees = self.contract_fee * contracts
        total_cost = premium_cost + fees
        
        # Check if we have enough cash
        if total_cost > available_cash:
            LOG.warning(f"[{date.date()}] Insufficient cash (need ${total_cost:,.0f}, have ${available_cash:,.0f})")
            return None
        
        LOG.flow(
            f"[{date.date()}] Opened {option_type.upper()} position: "
            f"{contracts} contracts @ ${entry_price:.2f}, Strike ${strike:.0f}, "
            f"Delta {greeks['delta']:.2f}, Cost ${total_cost:,.0f}"
        )
        
        return {
            'entry_date': date,
            'type': option_type,
            'strike': strike,
            'expiration': expiration,
            'contracts': contracts,
            'entry_price': entry_price,
            'delta': greeks['delta'],
            'cost': total_cost
        }
    
    def _calculate_metrics(self, equity_df, price_df, trades):
        """Calculate performance metrics."""
        # Returns
        returns = equity_df['equity'].pct_change().dropna()
        
        total_return_pct = (equity_df['equity'].iloc[-1] / self.initial_capital - 1) * 100
        
        # Sharpe ratio
        sharpe = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
        
        # Max drawdown
        cummax = equity_df['equity'].cummax()
        drawdown = (equity_df['equity'] / cummax - 1) * 100
        max_dd = drawdown.min()
        
        # Buy & hold comparison
        spy_return_pct = (price_df['close'].iloc[-1] / price_df['close'].iloc[0] - 1) * 100
        
        # Trade statistics
        if len(trades) > 0:
            trades_df = pd.DataFrame(trades)
            win_rate = (trades_df['pnl'] > 0).sum() / len(trades_df) * 100
            avg_win = trades_df[trades_df['pnl'] > 0]['pnl_pct'].mean() if (trades_df['pnl'] > 0).any() else 0
            avg_loss = trades_df[trades_df['pnl'] < 0]['pnl_pct'].mean() if (trades_df['pnl'] < 0).any() else 0
        else:
            win_rate = 0
            avg_win = 0
            avg_loss = 0
        
        return {
            'total_return_pct': total_return_pct,
            'sharpe_ratio': sharpe,
            'max_drawdown_pct': max_dd,
            'spy_buy_hold_pct': spy_return_pct,
            'outperformance_pct': total_return_pct - spy_return_pct,
            'final_equity': equity_df['equity'].iloc[-1],
            'num_trades': len(trades),
            'win_rate_pct': win_rate,
            'avg_win_pct': avg_win,
            'avg_loss_pct': avg_loss
        }


def main():
    """Run SPY baseline backtest."""
    print("=" * 70)
    print("SPY OPTIONS BASELINE BACKTEST (Phase 2 Validation)")
    print("=" * 70)
    print()
    
    # Configuration
    config = {
        'initial_capital': 100000,
        'target_notional': 10000,
        'slippage_pct': 1.0,
        'contract_fee': 0.097,
        'rsi_period': 21,
        'rsi_buy_threshold': 58,
        'rsi_sell_threshold': 42,
        'target_delta': 0.60,
        'min_dte': 45,
        'max_dte': 60,
        'roll_threshold_dte': 7
    }
    
    # Date range (2 years)
    start_date = '2024-01-01'
    end_date = '2026-01-15'
    
    # Run backtest
    backtester = SPYOptionsBacktester(config)
    
    # Fetch data
    df = backtester.fetch_spy_data(start_date, end_date)
    
    # Calculate signals
    df = backtester.calculate_signals(df)
    
    # Simulate trading
    results = backtester.simulate_options_trading(df)
    
    # Print results
    print("\n" + "=" * 70)
    print("BACKTEST RESULTS")
    print("=" * 70)
    
    metrics = results['metrics']
    
    print(f"\n📊 Performance Metrics:")
    print(f"  Total Return: {metrics['total_return_pct']:+.2f}%")
    print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"  Max Drawdown: {metrics['max_drawdown_pct']:.2f}%")
    print(f"  Final Equity: ${metrics['final_equity']:,.2f}")
    
    print(f"\n📈 vs Buy & Hold:")
    print(f"  SPY Buy & Hold: {metrics['spy_buy_hold_pct']:+.2f}%")
    print(f"  Outperformance: {metrics['outperformance_pct']:+.2f}%")
    
    print(f"\n📋 Trade Statistics:")
    print(f"  Number of Trades: {metrics['num_trades']}")
    print(f"  Win Rate: {metrics['win_rate_pct']:.1f}%")
    print(f"  Avg Win: {metrics['avg_win_pct']:+.2f}%")
    print(f"  Avg Loss: {metrics['avg_loss_pct']:+.2f}%")
    
    # Success criteria
    print(f"\n✅ Success Criteria:")
    print(f"  Sharpe > 1.0: {'✅ PASS' if metrics['sharpe_ratio'] > 1.0 else '❌ FAIL'} ({metrics['sharpe_ratio']:.2f})")
    print(f"  Return > Buy-Hold: {'✅ PASS' if metrics['outperformance_pct'] > 0 else '❌ FAIL'} ({metrics['outperformance_pct']:+.2f}%)")
    print(f"  Max DD < 50%: {'✅ PASS' if metrics['max_drawdown_pct'] > -50 else '❌ FAIL'} ({metrics['max_drawdown_pct']:.2f}%)")
    print(f"  Win Rate > 55%: {'✅ PASS' if metrics['win_rate_pct'] > 55 else '❌ FAIL'} ({metrics['win_rate_pct']:.1f}%)")
    
    passed = sum([
        metrics['sharpe_ratio'] > 1.0,
        metrics['outperformance_pct'] > 0,
        metrics['max_drawdown_pct'] > -50,
        metrics['win_rate_pct'] > 55
    ])
    
    print(f"\n{'🎉 BACKTEST PASSED!' if passed >= 3 else '⚠️  BACKTEST NEEDS WORK'} ({passed}/4 criteria met)")
    
    # Save results
    output_dir = Path('results/options')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results['equity_curve'].to_csv(output_dir / 'spy_baseline_equity_curve.csv')
    results['trades'].to_csv(output_dir / 'spy_baseline_trades.csv', index=False)
    
    print(f"\n📁 Results saved to: {output_dir}/")
    print("=" * 70)


if __name__ == "__main__":
    main()
