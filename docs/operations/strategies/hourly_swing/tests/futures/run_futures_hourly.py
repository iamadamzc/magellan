"""
Hourly Swing - Futures Baseline Test

Tests hourly RSI hysteresis strategy on high-volatility futures proxies (2024-2025).

Focus Assets:
- Index Futures: MES, MNQ (via SPY, QQQ)
- High-volatility targets for future expansion

Expected Output:
- futures_hourly_results.csv with Sharpe, Return, Max DD for each contract
"""

import pandas as pd
import numpy as np
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path
script_path = Path(__file__).resolve()
project_root = script_path.parents[6]  # Magellan folder
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_handler import AlpacaDataClient
from alpaca.data.timeframe import TimeFrame

print("="*80)
print("HOURLY SWING - FUTURES BASELINE TEST")
print("="*80)
print("Testing futures market proxies using Index ETFs on HOURLY timeframe")
print("Period: 2024-01-01 to 2025-12-31")
print("Strategy: RSI-28, Bands 60/40, Long-Only")
print("="*80)

# Hourly Swing tests high-volatility assets
# Start with index futures, then expand to commodities/crypto
FUTURES_UNIVERSE = {
    'MES': {'name': 'Micro E-mini S&P 500', 'proxy': 'SPY'},
    'MNQ': {'name': 'Micro E-mini Nasdaq 100', 'proxy': 'QQQ'},
    'MYM': {'name': 'Micro E-mini Dow', 'proxy': 'DIA'},
    'M2K': {'name': 'Micro E-mini Russell 2000', 'proxy': 'IWM'},
}

START_DATE = '2024-01-01'
END_DATE = '2025-12-31'
RSI_PERIOD = 28
UPPER_BAND = 60  # Wider bands for hourly (vs 55 for daily)
LOWER_BAND = 40  # Wider bands for hourly (vs 45 for daily)
INITIAL_CAPITAL = 10000
TRANSACTION_COST_BPS = 10.0  # Higher friction for hourly trading

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

def backtest_hysteresis(df, initial_capital=10000, transaction_cost_bps=10.0):
    """Run hysteresis backtest on hourly data"""
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
            hold_hours = (date - entry_date).total_seconds() / 3600
            
            trades.append({
                'entry_date': entry_date,
                'exit_date': date,
                'entry_price': entry_price,
                'exit_price': price,
                'hold_hours': hold_hours,
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
        hold_hours = (date - entry_date).total_seconds() / 3600
        
        trades.append({
            'entry_date': entry_date,
            'exit_date': date,
            'entry_price': entry_price,
            'exit_price': price,
            'hold_hours': hold_hours,
            'pnl': pnl,
            'pnl_pct': pnl_pct
        })
        
        cash += proceeds
        shares = 0
    
    return trades, equity_curve

# Initialize client
client = AlpacaDataClient()

# Test all futures
print(f"\n[1/3] Testing {len(FUTURES_UNIVERSE)} index futures on HOURLY timeframe...\n")

results = []

for symbol, config in FUTURES_UNIVERSE.items():
    print(f"Testing {symbol} ({config['name']}) via {config['proxy']}...")
    
    try:
        # Fetch HOURLY data from Alpaca
        raw_df = client.fetch_historical_bars(
            symbol=config['proxy'],
            timeframe=TimeFrame.Hour,
            start=START_DATE,
            end=END_DATE,
            feed='sip'
        )
        
        # Force resample to hourly if needed
        if len(raw_df) > 10000:  # Likely minute data
            print(f"  ⚠️  Detected {len(raw_df)} bars (likely minute data), resampling to hourly...")
            df = raw_df.resample('1H').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
            print(f"  ✓ Resampled to {len(df)} hourly bars")
        else:
            df = raw_df
        
        print(f"  ✓ Final dataset: {len(df)} hourly bars")
        
        # Calculate RSI
        df['rsi'] = calculate_rsi(df['close'], RSI_PERIOD)
        
        # Run backtest
        trades, equity_curve = backtest_hysteresis(df, INITIAL_CAPITAL, TRANSACTION_COST_BPS)
        
        # Calculate metrics
        final_equity = equity_curve[-1]
        total_return = (final_equity / INITIAL_CAPITAL - 1) * 100
        
        # Buy & Hold
        bh_return = (df.iloc[-1]['close'] / df.iloc[0]['close'] - 1) * 100
        
        equity_series = pd.Series(equity_curve)
        running_max = equity_series.expanding().max()
        drawdown = (equity_series - running_max) / running_max
        max_dd = drawdown.min() * 100
        
        # Annualize Sharpe for hourly (252 days * 6.5 hours)
        if len(equity_curve) > 1:
            returns = equity_series.pct_change().dropna()
            sharpe = (returns.mean() / returns.std()) * np.sqrt(252 * 6.5) if returns.std() > 0 else 0
        else:
            sharpe = 0
        
        if trades:
            trades_df = pd.DataFrame(trades)
            winning_trades = trades_df[trades_df['pnl'] > 0]
            win_rate = (len(winning_trades) / len(trades)) * 100
            avg_hold_hours = trades_df['hold_hours'].mean()
        else:
            win_rate = 0
            avg_hold_hours = 0
        
        results.append({
            'symbol': symbol,
            'name': config['name'],
            'proxy': config['proxy'],
            'total_return': round(total_return, 2),
            'bh_return': round(bh_return, 2),
            'sharpe': round(sharpe, 2),
            'max_dd': round(max_dd, 2),
            'trades': len(trades),
            'win_rate': round(win_rate, 1),
            'avg_hold_hours': round(avg_hold_hours, 1) if avg_hold_hours > 0 else 0,
            'status': 'SUCCESS'
        })
        
        status = "✅" if sharpe > 1.0 else "⚠️" if sharpe > 0.5 else "❌"
        print(f"  {status} Return: {total_return:+.1f}% | Sharpe: {sharpe:.2f} | DD: {max_dd:.1f}% | Trades: {len(trades)} | Win%: {win_rate:.0f}%\n")
        
    except Exception as e:
        print(f"  ❌ Error: {e}\n")
        results.append({
            'symbol': symbol,
            'name': config['name'],
            'proxy': config['proxy'],
            'total_return': 0,
            'bh_return': 0,
            'sharpe': 0,
            'max_dd': 0,
            'trades': 0,
            'win_rate': 0,
            'avg_hold_hours': 0,
            'status': f'ERROR: {str(e)[:50]}'
        })

print("="*80)
print("HOURLY SWING FUTURES RESULTS")
print("="*80)

results_df = pd.DataFrame(results)

# Summary stats
successful = results_df[results_df['status'] == 'SUCCESS']
if len(successful) > 0:
    print(f"\n✅ Successful Tests: {len(successful)}/{len(results_df)}")
    print(f"   Average Sharpe: {successful['sharpe'].mean():.2f}")
    print(f"   Average Return: {successful['total_return'].mean():.1f}%")
    print(f"   Contracts with Sharpe > 1.0: {len(successful[successful['sharpe'] > 1.0])}")
    print(f"   Contracts with Sharpe > 0.5: {len(successful[successful['sharpe'] > 0.5])}")

# Save results
output_file = Path(__file__).parent / 'futures_hourly_results.csv'
results_df.to_csv(output_file, index=False)
print(f"\n📁 Results saved to: {output_file}")

# Show all performers
if len(successful) > 0:
    print("\n📊 All Results (by Sharpe):")
    sorted_results = successful.sort_values('sharpe', ascending=False)[['symbol', 'name', 'sharpe', 'total_return', 'max_dd', 'trades', 'win_rate']]
    print(sorted_results.to_string(index=False))

print("\n" + "="*80)
print("VERDICT")
print("="*80)

approved = successful[successful['sharpe'] > 1.0]
tuning_needed = successful[(successful['sharpe'] >= 0.5) & (successful['sharpe'] <= 1.0)]
rejected = successful[successful['sharpe'] < 0.5]

if len(approved) > 0:
    print(f"\n✅ APPROVED FOR DEPLOYMENT ({len(approved)} contracts):")
    for _, row in approved.iterrows():
        print(f"   {row['symbol']} - Sharpe {row['sharpe']:.2f}, Return {row['total_return']:+.1f}%")

if len(tuning_needed) > 0:
    print(f"\n⚠️  NEEDS TUNING ({len(tuning_needed)} contracts):")
    for _, row in tuning_needed.iterrows():
        print(f"   {row['symbol']} - Sharpe {row['sharpe']:.2f} (try wider bands: 65/35 or 70/30)")

if len(rejected) > 0:
    print(f"\n❌ REJECTED ({len(rejected)} contracts):")
    for _, row in rejected.iterrows():
        print(f"   {row['symbol']} - Sharpe {row['sharpe']:.2f}")

print("\n" + "="*80)
print("NEXT STEPS")
print("="*80)
print("1. Create asset configs for APPROVED contracts")
print("2. Test high-volatility commodities/crypto (if available via FMP)")
print("3. Generate FINAL_VALIDATION_REPORT.md")
print("="*80)
