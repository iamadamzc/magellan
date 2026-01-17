"""
Hourly Swing Regime Sentiment Filter Strategy
----------------------------------------------
Applies the validated Regime Sentiment Filter logic to hourly timeframe.

This is a salvage attempt for the failed Hourly Swing strategy by adding:
1. SPY 200 MA regime filter (bear market protection)
2. News sentiment filter (avoid bad entries, trigger fast exits)
3. Dual-path entry logic (bull regime + strong breakout)

Original Hourly Swing Results:
- NVDA: +52% (worked)
- TSLA: -18% (failed)
- Most others: negative

Hypothesis: Adding protective filters will improve success rate across MAG7.
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_cache import cache

def calculate_rsi(prices, period=28):
    """Calculate RSI indicator"""
    delta = prices.diff()
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)
    avg_gain = gains.ewm(span=period, adjust=False).mean()
    avg_loss = losses.ewm(span=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.inf)
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.replace([np.inf, -np.inf], np.nan).fillna(50)
    return rsi

def merge_news_sentiment(df, news_data):
    """
    Merge news sentiment with hourly bars.
    Uses 4-hour lookback window to avoid look-ahead bias.
    """
    if not news_data or len(news_data) == 0:
        df['sentiment'] = 0.0
        return df
    
    news_df = pd.DataFrame(news_data)
    news_df['publishedDate'] = pd.to_datetime(news_df['publishedDate'])
    news_df = news_df.set_index('publishedDate')
    
    # For each bar, get average sentiment from news published in the 4 hours BEFORE bar close
    sentiments = []
    for timestamp in df.index:
        lookback_start = timestamp - pd.Timedelta(hours=4)
        relevant_news = news_df[(news_df.index >= lookback_start) & (news_df.index < timestamp)]
        
        if len(relevant_news) > 0:
            avg_sentiment = relevant_news['sentimentScore'].mean()
        else:
            avg_sentiment = 0.0
        
        sentiments.append(avg_sentiment)
    
    df['sentiment'] = sentiments
    return df

def run_backtest(symbol, period_name, start_date, end_date):
    """
    Run backtest for Hourly Swing Regime Sentiment Filter
    
    Entry Path 1 (Bull Regime):
    - Hourly RSI(28) > 55
    - SPY > 200 MA (daily)
    - News Sentiment > -0.2
    
    Entry Path 2 (Strong Breakout):
    - Hourly RSI(28) > 65
    - News Sentiment > 0.0
    
    Exit:
    - Hourly RSI(28) < 45 OR
    - News Sentiment < -0.3
    """
    
    print(f"Testing {symbol} {period_name}...")
    
    # Fetch hourly data for the symbol
    df = cache.get_or_fetch_equity(symbol, '1hour', start_date, end_date)
    
    if len(df) < 200:
        raise ValueError(f"Insufficient data: {len(df)} bars")
    
    # Fetch SPY daily data for regime filter
    spy_daily = cache.get_or_fetch_equity('SPY', '1day', start_date, end_date)
    spy_daily['ma_200'] = spy_daily['close'].rolling(200).mean()
    spy_daily['regime'] = (spy_daily['close'] > spy_daily['ma_200']).astype(int)
    
    # Merge SPY regime to hourly bars (forward fill)
    df['date'] = df.index.date
    spy_regime_map = spy_daily['regime'].to_dict()
    df['spy_regime'] = df['date'].map(lambda d: spy_regime_map.get(pd.Timestamp(d), 0))
    df = df.drop('date', axis=1)
    
    # Fetch news sentiment
    news_data = cache.get_or_fetch_historical_news(symbol, start_date, end_date)
    df = merge_news_sentiment(df, news_data)
    
    # Calculate RSI
    df['rsi_28'] = calculate_rsi(df['close'], period=28)
    
    # Entry conditions
    # Path 1: Bull Regime
    entry_bull = (df['rsi_28'] > 55) & (df['spy_regime'] == 1) & (df['sentiment'] > -0.2)
    
    # Path 2: Strong Breakout (no regime requirement)
    entry_strong = (df['rsi_28'] > 65) & (df['sentiment'] > 0.0)
    
    # Combined entry (OR logic)
    entry_condition = entry_bull | entry_strong
    
    # Exit conditions
    exit_condition = (df['rsi_28'] < 45) | (df['sentiment'] < -0.3)
    
    # State machine for position tracking
    position = 0
    signals = []
    
    for i in range(len(df)):
        if position == 0:  # Flat
            if entry_condition.iloc[i]:
                position = 1
        elif position == 1:  # Long
            if exit_condition.iloc[i]:
                position = 0
        
        signals.append(position)
    
    df['signal'] = signals
    
    # Calculate returns
    df['returns'] = df['close'].pct_change()
    df['strategy_returns'] = df['signal'].shift(1) * df['returns']
    
    # Apply friction (10 bps for hourly trading)
    trades = (df['signal'].diff() != 0).sum()
    friction_per_trade = 0.0010  # 10 bps
    total_friction = trades * friction_per_trade
    
    # Performance metrics
    total_return = (1 + df['strategy_returns']).prod() - 1 - total_friction
    buy_hold_return = (df['close'].iloc[-1] / df['close'].iloc[0]) - 1
    
    # Sharpe ratio (annualized for hourly data: sqrt(252 * 6.5))
    sharpe = (df['strategy_returns'].mean() / df['strategy_returns'].std()) * np.sqrt(252 * 6.5) if df['strategy_returns'].std() > 0 else 0
    
    # Max drawdown
    cum_returns = (1 + df['strategy_returns']).cumprod()
    running_max = cum_returns.expanding().max()
    drawdown = (cum_returns - running_max) / running_max
    max_dd = drawdown.min()
    
    # Trade statistics
    winning_hours = (df[df['signal'] == 1]['returns'] > 0).sum()
    total_hours_in_market = (df['signal'] == 1).sum()
    win_rate = (winning_hours / total_hours_in_market * 100) if total_hours_in_market > 0 else 0
    
    print(f"✓ {symbol} {period_name}: {total_return*100:+.2f}% | Sharpe: {sharpe:.2f} | Trades: {trades}")
    
    return {
        'symbol': symbol,
        'period': period_name,
        'strategy_return': total_return * 100,
        'buy_hold_return': buy_hold_return * 100,
        'sharpe': sharpe,
        'max_dd': max_dd * 100,
        'trades': trades,
        'win_rate': win_rate,
        'hours_in_market': total_hours_in_market
    }

if __name__ == '__main__':
    # Test on a single asset
    import argparse
    
    parser = argparse.ArgumentParser(description='Hourly Swing Regime Sentiment Filter')
    parser.add_argument('--symbol', type=str, default='NVDA', help='Symbol to test')
    parser.add_argument('--period', type=str, default='Primary', help='Period name')
    parser.add_argument('--start', type=str, default='2024-01-01', help='Start date')
    parser.add_argument('--end', type=str, default='2025-12-31', help='End date')
    
    args = parser.parse_args()
    
    result = run_backtest(args.symbol, args.period, args.start, args.end)
    
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    print(f"Symbol: {result['symbol']}")
    print(f"Period: {result['period']}")
    print(f"Strategy Return: {result['strategy_return']:+.2f}%")
    print(f"Buy & Hold Return: {result['buy_hold_return']:+.2f}%")
    print(f"Sharpe Ratio: {result['sharpe']:.2f}")
    print(f"Max Drawdown: {result['max_dd']:.2f}%")
    print(f"Total Trades: {result['trades']}")
    print(f"Win Rate: {result['win_rate']:.1f}%")
    print(f"Hours in Market: {result['hours_in_market']}")
