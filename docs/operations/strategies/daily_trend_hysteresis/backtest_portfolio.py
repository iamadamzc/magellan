"""
Portfolio Backtest - All 11 Daily Hysteresis Assets
Tests MAG7 + 4 ETFs with FIXED code (proper daily resolution)
"""

import pandas as pd
import numpy as np
from datetime import datetime
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_handler import AlpacaDataClient
from alpaca.data.timeframe import TimeFrame
import json

print("="*80)
print("PORTFOLIO BACKTEST - DAILY TREND HYSTERESIS")
print("="*80)
print("Assets: MAG7 (7) + ETFs (4) = 11 total")
print("Period: 2024-01-01 to 2025-12-31")
print("="*80)

# Load config
with open('config/nodes/master_config.json', 'r') as f:
    config = json.load(f)

# Assets to test
ASSETS = ['GOOGL', 'TSLA', 'AAPL', 'NVDA', 'META', 'MSFT', 'AMZN', 'GLD', 'IWM', 'QQQ', 'SPY']

INITIAL_CAPITAL = 10000
TRANSACTION_COST_BPS = 1.5
START_DATE = '2024-01-01'
END_DATE = '2025-12-31'

client = AlpacaDataClient()
results = {}

for symbol in ASSETS:
    print(f"\n{'='*80}")
    print(f"Testing {symbol}")
    print(f"{'='*80}")
    
    # Get config
    if symbol not in config:
        print(f"⚠️  No config for {symbol}, skipping")
        continue
    
    asset_config = config[symbol]
    rsi_period = asset_config.get('rsi_lookback', 28)
    upper_band = asset_config.get('hysteresis_upper_rsi', 55)
    lower_band = asset_config.get('hysteresis_lower_rsi', 45)
    
    print(f"Config: RSI-{rsi_period}, Bands {upper_band}/{lower_band}")
    
    # Fetch data
    try:
        print(f"Fetching daily bars...")
        raw_df = client.fetch_historical_bars(
            symbol=symbol,
            timeframe=TimeFrame.Day,
            start=START_DATE,
            end=END_DATE,
            feed='sip'
        )
        
        # Force resample if needed
        if len(raw_df) > 1000:
            print(f"⚠️  Got {len(raw_df)} bars, resampling to daily...")
            df = raw_df.resample('1D').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
        else:
            df = raw_df
        
        print(f"✓ {len(df)} daily bars")
        
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        continue
    
    # Calculate RSI
    delta = df['close'].diff()
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)
    
    avg_gain = gains.ewm(span=rsi_period, adjust=False).mean()
    avg_loss = losses.ewm(span=rsi_period, adjust=False).mean()
    
    rs = avg_gain / avg_loss.replace(0, np.inf)
    df['rsi'] = 100 - (100 / (1 + rs))
    
    df.loc[avg_loss == 0, 'rsi'] = 100.0
    df.loc[avg_gain == 0, 'rsi'] = 0.0
    
    # Run backtest
    cash = INITIAL_CAPITAL
    shares = 0
    position = 'flat'
    trades = []
    equity_curve = []
    
    entry_price = None
    entry_date = None
    
    for date, row in df.iterrows():
        price = row['close']
        rsi = row['rsi']
        
        if pd.isna(rsi):
            equity_curve.append(cash + shares * price)
            continue
        
        # Hysteresis Logic
        if position == 'flat' and rsi > upper_band:
            cost = TRANSACTION_COST_BPS / 10000
            shares = int(cash / (price * (1 + cost)))
            if shares > 0:
                cash -= shares * price * (1 + cost)
                position = 'long'
                entry_price = price
                entry_date = date
        
        elif position == 'long' and rsi < lower_band:
            cost = TRANSACTION_COST_BPS / 10000
            proceeds = shares * price * (1 - cost)
            pnl = proceeds - (shares * entry_price)
            pnl_pct = (price / entry_price - 1) * 100
            hold_days = (date - entry_date).days
            
            trades.append({
                'entry_date': entry_date,
                'exit_date': date,
                'entry_price': entry_price,
                'exit_price': price,
                'hold_days': hold_days,
                'pnl': pnl,
                'pnl_pct': pnl_pct
            })
            
            cash += proceeds
            shares = 0
            position = 'flat'
            entry_price = None
        
        current_equity = cash + shares * price
        equity_curve.append(current_equity)
    
    # Close any open position
    if position == 'long' and shares > 0:
        price = df.iloc[-1]['close']
        date = df.index[-1]
        cost = TRANSACTION_COST_BPS / 10000
        proceeds = shares * price * (1 - cost)
        pnl = proceeds - (shares * entry_price)
        pnl_pct = (price / entry_price - 1) * 100
        hold_days = (date - entry_date).days
        
        trades.append({
            'entry_date': entry_date,
            'exit_date': date,
            'entry_price': entry_price,
            'exit_price': price,
            'hold_days': hold_days,
            'pnl': pnl,
            'pnl_pct': pnl_pct
        })
        
        cash += proceeds
        shares = 0
    
    # Calculate metrics
    final_equity = equity_curve[-1]
    total_return = (final_equity / INITIAL_CAPITAL - 1) * 100
    bh_return = (df.iloc[-1]['close'] / df.iloc[0]['close'] - 1) * 100
    
    equity_series = pd.Series(equity_curve)
    running_max = equity_series.expanding().max()
    drawdown = (equity_series - running_max) / running_max
    max_dd = drawdown.min() * 100
    
    if len(equity_curve) > 1:
        returns = equity_series.pct_change().dropna()
        sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0
    else:
        sharpe = 0
    
    if trades:
        trades_df = pd.DataFrame(trades)
        winning_trades = trades_df[trades_df['pnl'] > 0]
        win_rate = (len(winning_trades) / len(trades)) * 100
    else:
        win_rate = 0
    
    # Store results
    results[symbol] = {
        'total_return': total_return,
        'bh_return': bh_return,
        'outperformance': total_return - bh_return,
        'sharpe': sharpe,
        'max_dd': max_dd,
        'trades': len(trades),
        'win_rate': win_rate,
        'final_equity': final_equity
    }
    
    # Print results
    print(f"\n{symbol} RESULTS:")
    print(f"  Return:          {total_return:+.1f}%")
    print(f"  Buy & Hold:      {bh_return:+.1f}%")
    print(f"  Sharpe:          {sharpe:.2f}")
    print(f"  Max DD:          {max_dd:.1f}%")
    print(f"  Trades:          {len(trades)}")
    print(f"  Win Rate:        {win_rate:.1f}%")

# Summary
print(f"\n{'='*80}")
print("PORTFOLIO SUMMARY")
print(f"{'='*80}")

summary_df = pd.DataFrame(results).T
summary_df = summary_df.sort_values('total_return', ascending=False)

print(f"\n{'Symbol':<8} | {'Return':>8} | {'Sharpe':>6} | {'Max DD':>7} | {'Trades':>6} | {'Status'}")
print("-" * 70)

for symbol, row in summary_df.iterrows():
    status = "✅" if row['total_return'] > 0 else "❌"
    print(f"{symbol:<8} | {row['total_return']:>7.1f}% | {row['sharpe']:>6.2f} | {row['max_dd']:>6.1f}% | {row['trades']:>6.0f} | {status}")

print(f"\n{'='*80}")
print(f"Profitable Assets: {(summary_df['total_return'] > 0).sum()}/{len(summary_df)}")
print(f"Average Return:    {summary_df['total_return'].mean():.1f}%")
print(f"Average Sharpe:    {summary_df['sharpe'].mean():.2f}")
print(f"Total Trades:      {summary_df['trades'].sum():.0f}")
print(f"{'='*80}")

# Save results
summary_df.to_csv('portfolio_backtest_results.csv')
print(f"\n✅ Results saved to portfolio_backtest_results.csv")
