"""
Daily Trend Hysteresis - Futures Baseline Test (FMP EDITION)

Tests RSI hysteresis strategy across 13 micro futures proxies using FMP data.

Data Sources:
- FMP Commodities/Currencies: GCUSD, SIUSD, CLUSD, NGUSD, HGUSD, BTCUSD, EURUSD, GBPUSD, AUDUSD
- Alpaca Index ETFs: SPY, QQQ, DIA, IWM (as proxies for MES, MNQ, MYM, M2K)

Expected Output:
- futures_baseline_results.csv with Sharpe, Return, Max DD for each contract
"""

import pandas as pd
import numpy as np
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parents[5]
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_handler import AlpacaDataClient, FMPDataClient
from alpaca.data.timeframe import TimeFrame

print("="*80)
print("DAILY TREND HYSTERESIS - FUTURES BASELINE TEST (FMP EDITION)")
print("="*80)
print("Asset Class: Micro Futures (using spot/ETF proxies)")
print("Period: 2024-01-01 to 2025-12-31")
print("Strategy: RSI-28, Bands 55/45, Long-Only")
print("="*80)

# Configuration
FUTURES_UNIVERSE = {
    # Index futures → use ETF proxies (Alpaca)
    'MES': {'name': 'Micro E-mini S&P 500', 'proxy': 'SPY', 'source': 'alpaca'},
    'MNQ': {'name': 'Micro E-mini Nasdaq 100', 'proxy': 'QQQ', 'source': 'alpaca'},
    'MYM': {'name': 'Micro E-mini Dow', 'proxy': 'DIA', 'source': 'alpaca'},
    'M2K': {'name': 'Micro E-mini Russell 2000', 'proxy': 'IWM', 'source': 'alpaca'},
    
    # Commodities → use spot prices (FMP)
    'MCL': {'name': 'Micro Crude Oil', 'proxy': 'CLUSD', 'source': 'fmp'},
    'MGC': {'name': 'Micro Gold', 'proxy': 'GCUSD', 'source': 'fmp'},
    'MSI': {'name': 'Micro Silver', 'proxy': 'SIUSD', 'source': 'fmp'},
    'MNG': {'name': 'Micro Natural Gas', 'proxy': 'NGUSD', 'source': 'fmp'},
    'MCP': {'name': 'Micro Copper', 'proxy': 'HGUSD', 'source': 'fmp'},
    
    # Currencies → use spot FX (FMP)
    'M6E': {'name': 'Micro EUR/USD', 'proxy': 'EURUSD', 'source': 'fmp'},
    'M6B': {'name': 'Micro GBP/USD', 'proxy': 'GBPUSD', 'source': 'fmp'},
    'M6A': {'name': 'Micro AUD/USD', 'proxy': 'AUDUSD', 'source': 'fmp'},
    
    # Crypto → use spot (FMP)
    'MBT': {'name': 'Micro Bitcoin', 'proxy': 'BTCUSD', 'source': 'fmp'},
}

START_DATE = '2024-01-01'
END_DATE = '2025-12-31'
RSI_PERIOD = 28
UPPER_BAND = 55
LOWER_BAND = 45
INITIAL_CAPITAL = 10000
TRANSACTION_COST_BPS = 5.0

def calculate_rsi(prices, period=28):
    """Calculate RSI indicator"""
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

def backtest_hysteresis(df, initial_capital=10000, transaction_cost_bps=5.0):
    """Run hysteresis backtest"""
    cash = initial_capital
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
        if position == 'flat' and rsi > UPPER_BAND:
            cost = transaction_cost_bps / 10000
            shares = int(cash / (price * (1 + cost)))
            if shares > 0:
                cash -= shares * price * (1 + cost)
                position = 'long'
                entry_price = price
                entry_date = date
        
        elif position == 'long' and rsi < LOWER_BAND:
            cost = transaction_cost_bps / 10000
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
        cost = transaction_cost_bps / 10000
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
    
    return trades, equity_curve

# Initialize clients
alpaca_client = AlpacaDataClient()
fmp_client = FMPDataClient()

# Test all futures
print(f"\n[1/3] Testing {len(FUTURES_UNIVERSE)} futures proxies...\n")

results = []

for symbol, config in FUTURES_UNIVERSE.items():
    print(f"Testing {symbol} ({config['name']}) via {config['proxy']}...")
    
    try:
        # Fetch data based on source
        if config['source'] == 'alpaca':
            df = alpaca_client.fetch_historical_bars(
                symbol=config['proxy'],
                timeframe=TimeFrame.Day,
                start=START_DATE,
                end=END_DATE,
                feed='sip'
            )
        elif config['source'] == 'fmp':
            df = fmp_client.fetch_historical_bars(
                symbol=config['proxy'],
                interval='1day',
                start=START_DATE,
                end=END_DATE
            )
        else:
            raise ValueError(f"Unknown source: {config['source']}")
        
        print(f"  ✓ Fetched {len(df)} bars")
        
        # Calculate RSI
        df['rsi'] = calculate_rsi(df['close'], RSI_PERIOD)
        
        # Run backtest
        trades, equity_curve = backtest_hysteresis(df, INITIAL_CAPITAL, TRANSACTION_COST_BPS)
        
        # Calculate metrics
        final_equity = equity_curve[-1]
        total_return = (final_equity / INITIAL_CAPITAL - 1) * 100
        
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
        
        results.append({
            'symbol': symbol,
            'name': config['name'],
            'proxy': config['proxy'],
            'total_return': round(total_return, 2),
            'sharpe': round(sharpe, 2),
            'max_dd': round(max_dd, 2),
            'trades': len(trades),
            'win_rate': round(win_rate, 1),
            'status': 'SUCCESS'
        })
        
        status = "✅" if sharpe > 0.7 else "⚠️" if sharpe > 0.3 else "❌"
        print(f"  {status} Return: {total_return:+.1f}% | Sharpe: {sharpe:.2f} | DD: {max_dd:.1f}% | Trades: {len(trades)}\n")
        
    except Exception as e:
        print(f"  ❌ Error: {e}\n")
        results.append({
            'symbol': symbol,
            'name': config['name'],
            'proxy': config['proxy'],
            'total_return': 0,
            'sharpe': 0,
            'max_dd': 0,
            'trades': 0,
            'win_rate': 0,
            'status': f'ERROR: {str(e)[:50]}'
        })

print("="*80)
print("FUTURES BASELINE RESULTS")
print("="*80)

results_df = pd.DataFrame(results)

# Summary stats
successful = results_df[results_df['status'] == 'SUCCESS']
if len(successful) > 0:
    print(f"\n✅ Successful Tests: {len(successful)}/{len(results_df)}")
    print(f"   Average Sharpe: {successful['sharpe'].mean():.2f}")
    print(f"   Average Return: {successful['total_return'].mean():.1f}%")
    print(f"   Contracts with Sharpe > 0.7: {len(successful[successful['sharpe'] > 0.7])}")
    print(f"   Contracts with Sharpe > 1.0: {len(successful[successful['sharpe'] > 1.0])}")

# Save results
output_file = Path(__file__).parent / 'futures_baseline_results.csv'
results_df.to_csv(output_file, index=False)
print(f"\n📁 Results saved to: {output_file}")

# Show top performers
if len(successful) > 0:
    print("\n🏆 Top 5 Performers (by Sharpe):")
    top5 = successful.nlargest(5, 'sharpe')[['symbol', 'name', 'sharpe', 'total_return', 'max_dd']]
    print(top5.to_string(index=False))

print("\n" + "="*80)
print("NEXT STEPS")
print("="*80)
print("1. Review futures_baseline_results.csv")
print("2. For contracts with Sharpe > 0.7, create asset configs")
print("3. For contracts with 0.3 < Sharpe < 0.7, try parameter tuning")
print("4. Proceed to Hourly Swing testing on high-volatility assets (MBT, MCL, MNG)")
print("="*80)
