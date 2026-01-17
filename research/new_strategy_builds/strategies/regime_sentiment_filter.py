"""
Regime Sentiment Filter Strategy (Daily, MAG7 Equities)

Triple filter to prevent bear market catastrophes:
1. RSI(28) > 60 (momentum)
2. SPY > 200 MA (bull market regime)
3. News sentiment > 0 (positive catalyst)

Exit: RSI < 40 OR SPY < 200 MA
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_cache import cache
from src.features import FeatureEngineer
import argparse

def calculate_rsi(prices, period=28):
    """Calculate RSI"""
    delta = prices.diff()
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)
    
    avg_gain = gains.ewm(span=period, adjust=False).mean()
    avg_loss = losses.ewm(span=period, adjust=False).mean()
    
    rs = avg_gain / avg_loss.replace(0, np.inf)
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.replace([np.inf, -np.inf], np.nan).fillna(50)
    
    return rsi

def merge_news_sentiment(price_df, news_list):
    """Merge news sentiment point-in-time"""
    df = price_df.copy()
    
    if not news_list:
        df['sentiment'] = 0.0
        return df
    
    # Convert news to DataFrame
    news_df = pd.DataFrame(news_list)
    news_df['publishedDate'] = pd.to_datetime(news_df['publishedDate'])
    news_df = news_df.sort_values('publishedDate')
    
    # For each day, get sentiment from news published BEFORE that day
    sentiments = []
    for bar_date in df.index:
        # News before this bar
        mask = news_df['publishedDate'] < bar_date
        recent_news = news_df.loc[mask].tail(10)  # Last 10 articles
        
        if len(recent_news) > 0:
            avg_sent = recent_news['sentiment'].mean()
        else:
            avg_sent = 0.0
        
        sentiments.append(avg_sent)
    
    df['sentiment'] = sentiments
    return df

def run_backtest(symbol, period_name, start, end, friction_bps=1.5):
    """Run Strategy A backtest"""
    
    print(f"\n{'='*80}")
    print(f"Testing {symbol} - {period_name} ({start} to {end})")
    print(f"{'='*80}")
    
    # Load cached data
    df = cache.get_or_fetch_equity(symbol, '1day', start, end)
    spy_df = cache.get_or_fetch_equity('SPY', '1day', start, end)
    news = cache.get_or_fetch_historical_news(symbol, start, end)
    
    print(f"✓ Loaded {len(df)} bars, {len(news)} news articles")
    
    # Calculate features
    df['rsi_28'] = calculate_rsi(df['close'], period=28)
    
    # SPY 200 MA
    spy_df['ma_200'] = spy_df['close'].rolling(200).mean()
    df['spy_regime'] = (spy_df['close'] > spy_df['ma_200']).astype(int)
    
    # Merge news sentiment
    df = merge_news_sentiment(df, news)
    
    # Generate signals
    df['signal'] = 0
    
    # Entry: RSI > 60 AND SPY > 200 MA AND sentiment > 0
    entry_condition = (df['rsi_28'] > 60) & (df['spy_regime'] == 1) & (df['sentiment'] > 0)
    
    # Exit: RSI < 40 OR SPY < 200 MA
    exit_condition = (df['rsi_28'] < 40) | (df['spy_regime'] == 0)
    
    # State machine
    position = 0
    signals = []
    
    for i in range(len(df)):
        if position == 0:  # Flat
            if entry_condition.iloc[i]:
                position = 1  # Enter long
        elif position == 1:  # Long
            if exit_condition.iloc[i]:
                position = 0  # Exit
        
        signals.append(position)
    
    df['signal'] = signals
    
    # Calculate returns
    df['returns'] = df['close'].pct_change()
    df['strategy_returns'] = df['signal'].shift(1) * df['returns']
    
    # Apply friction
    trades = (df['signal'].diff() != 0).sum()
    friction_cost = (friction_bps / 10000) * trades
    
    # Performance metrics
    total_return = (1 + df['strategy_returns']).prod() - 1
    buy_hold_return = (df['close'].iloc[-1] / df['close'].iloc[0]) - 1
    
    # Sharpe ratio
    sharpe = (df['strategy_returns'].mean() / df['strategy_returns'].std()) * np.sqrt(252) if df['strategy_returns'].std() > 0 else 0
    
    # Max drawdown
    cum_returns = (1 + df['strategy_returns']).cumprod()
    running_max = cum_returns.expanding().max()
    drawdown = (cum_returns - running_max) / running_max
    max_dd = drawdown.min()
    
    # Win rate
    winning_days = (df[df['signal'] == 1]['returns'] > 0).sum()
    total_days_in_market = (df['signal'] == 1).sum()
    win_rate = (winning_days / total_days_in_market * 100) if total_days_in_market > 0 else 0
    
    print(f"\nResults:")
    print(f"  Strategy Return: {total_return*100:+.2f}%")
    print(f"  Buy & Hold:      {buy_hold_return*100:+.2f}%")
    print(f"  Sharpe Ratio:    {sharpe:.2f}")
    print(f"  Max Drawdown:    {max_dd*100:.2f}%")
    print(f"  Trades:          {trades}")
    print(f"  Win Rate:        {win_rate:.1f}%")
    print(f"  Days in Market:  {total_days_in_market}")
    
    return {
        'symbol': symbol,
        'period': period_name,
        'strategy_return': total_return * 100,
        'buy_hold_return': buy_hold_return * 100,
        'sharpe': sharpe,
        'max_dd': max_dd * 100,
        'trades': trades,
        'win_rate': win_rate,
        'days_in_market': total_days_in_market
    }

def main():
    parser = argparse.ArgumentParser(description='Test Regime Sentiment Filter Strategy')
    parser.add_argument('--symbol', type=str, default='AAPL', help='Symbol to test')
    parser.add_argument('--period', type=str, default='both', choices=['both', 'primary', 'secondary'])
    args = parser.parse_args()
    
    results = []
    
    if args.period in ['both', 'primary']:
        result = run_backtest(args.symbol, 'Primary', '2024-01-01', '2025-12-31')
        results.append(result)
    
    if args.period in ['both', 'secondary']:
        result = run_backtest(args.symbol, 'Secondary', '2022-01-01', '2023-12-31')
        results.append(result)
    
    # Summary
    if len(results) > 1:
        print(f"\n{'='*80}")
        print("SUMMARY")
        print(f"{'='*80}")
        for r in results:
            print(f"{r['period']:12} Return: {r['strategy_return']:+.2f}% | Sharpe: {r['sharpe']:.2f} | Trades: {r['trades']}")

if __name__ == '__main__':
    main()
