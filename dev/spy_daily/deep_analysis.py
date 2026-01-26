"""
Deep SPY Intraday Pattern Analysis
Analyzes 4+ years of 1-minute data to discover optimal trading patterns

Analysis Areas:
1. Time-of-day return patterns
2. Opening Range Breakout (ORB) characteristics
3. Gap behavior (fade vs follow)
4. Volume profile analysis
5. Volatility clustering
6. First hour momentum persistence
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import time
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "cache" / "equities"


def load_spy_data():
    """Load all SPY 1-minute data."""
    files = sorted(list(DATA_DIR.glob("SPY_1min_*.parquet")))
    print(f"Found {len(files)} SPY data files")
    
    dfs = []
    for f in files:
        df = pd.read_parquet(f)
        dfs.append(df)
        print(f"  Loaded {f.name}: {len(df):,} bars")
    
    df = pd.concat(dfs)
    df = df.sort_index()
    df = df[~df.index.duplicated(keep='last')]
    
    print(f"\nTotal: {len(df):,} bars")
    print(f"Date range: {df.index[0]} to {df.index[-1]}")
    
    return df


def analyze_time_of_day_returns(df):
    """Analyze return patterns by time of day."""
    print("\n" + "=" * 70)
    print("1. TIME-OF-DAY RETURN ANALYSIS")
    print("=" * 70)
    
    df = df.copy()
    df['returns'] = df['close'].pct_change()
    df['time'] = df.index.time
    df['hour'] = df.index.hour
    df['minute'] = df.index.minute
    df['date'] = df.index.date
    
    # Hourly average returns
    hourly = df.groupby('hour')['returns'].agg(['mean', 'std', 'count'])
    hourly['sharpe'] = hourly['mean'] / hourly['std'] * np.sqrt(252 * 60)  # Annualized
    
    print("\nAverage Returns by Hour (EST):")
    print("-" * 50)
    for hour in range(9, 17):
        if hour in hourly.index:
            row = hourly.loc[hour]
            direction = "↑" if row['mean'] > 0 else "↓"
            print(f"  {hour:02d}:00 - {row['mean']*10000:+.2f} bps {direction} | Sharpe: {row['sharpe']:.2f}")
    
    # Find best trading windows
    best_hour = hourly['sharpe'].abs().idxmax()
    print(f"\nMost Signal (highest |Sharpe|): {best_hour}:00 (Sharpe: {hourly.loc[best_hour, 'sharpe']:.2f})")
    
    return hourly


def analyze_opening_range(df, orb_minutes=15):
    """Analyze Opening Range Breakout patterns."""
    print("\n" + "=" * 70)
    print(f"2. OPENING RANGE BREAKOUT ({orb_minutes}-MIN) ANALYSIS")
    print("=" * 70)
    
    df = df.copy()
    df['date'] = df.index.date
    df['time'] = df.index.time
    
    # Get opening range (first N minutes)
    orb_end = time(9, 30 + orb_minutes)
    market_close = time(16, 0)
    
    results = []
    
    for date in df['date'].unique():
        day_data = df[df['date'] == date]
        
        # Opening range
        orb_data = day_data[day_data['time'] <= orb_end]
        if len(orb_data) < 5:
            continue
        
        orb_high = orb_data['high'].max()
        orb_low = orb_data['low'].min()
        orb_range = orb_high - orb_low
        open_price = orb_data.iloc[0]['open']
        
        # Rest of day
        rest_data = day_data[(day_data['time'] > orb_end) & (day_data['time'] <= market_close)]
        if len(rest_data) < 10:
            continue
        
        close_price = rest_data.iloc[-1]['close']
        day_high = rest_data['high'].max()
        day_low = rest_data['low'].min()
        
        # ORB breakout analysis
        broke_above = day_high > orb_high
        broke_below = day_low < orb_low
        
        # Direction from ORB to close
        orb_return = (close_price - orb_data.iloc[-1]['close']) / orb_data.iloc[-1]['close']
        
        results.append({
            'date': date,
            'orb_range_pct': orb_range / open_price * 100,
            'orb_high': orb_high,
            'orb_low': orb_low,
            'close': close_price,
            'broke_above': broke_above,
            'broke_below': broke_below,
            'orb_return': orb_return * 100
        })
    
    results_df = pd.DataFrame(results)
    
    # ORB breakout statistics
    both_break = (results_df['broke_above'] & results_df['broke_below']).mean() * 100
    above_only = (results_df['broke_above'] & ~results_df['broke_below']).mean() * 100
    below_only = (~results_df['broke_above'] & results_df['broke_below']).mean() * 100
    no_break = (~results_df['broke_above'] & ~results_df['broke_below']).mean() * 100
    
    print(f"\nORB Breakout Frequency ({len(results_df)} days):")
    print(f"  Both directions broken: {both_break:.1f}%")
    print(f"  Only above broken:      {above_only:.1f}%")
    print(f"  Only below broken:      {below_only:.1f}%")
    print(f"  No breakout:            {no_break:.1f}%")
    
    # Average ORB range
    avg_orb_range = results_df['orb_range_pct'].mean()
    print(f"\nAverage ORB range: {avg_orb_range:.2f}%")
    
    # Trend following vs mean reversion after ORB
    upward_orb = results_df[results_df['broke_above'] & ~results_df['broke_below']]
    downward_orb = results_df[~results_df['broke_above'] & results_df['broke_below']]
    
    if len(upward_orb) > 10:
        avg_return_after_up_break = upward_orb['orb_return'].mean()
        print(f"\nAvg return after upward ORB break: {avg_return_after_up_break:+.2f}%")
    
    if len(downward_orb) > 10:
        avg_return_after_down_break = downward_orb['orb_return'].mean()
        print(f"Avg return after downward ORB break: {avg_return_after_down_break:+.2f}%")
    
    return results_df


def analyze_gap_behavior(df):
    """Analyze overnight gap fade vs follow patterns."""
    print("\n" + "=" * 70)
    print("3. GAP ANALYSIS (Fade vs Follow)")
    print("=" * 70)
    
    df = df.copy()
    df['date'] = df.index.date
    df['time'] = df.index.time
    
    # Get each day's open, close, prev_close
    days = []
    dates = sorted(df['date'].unique())
    
    for i, date in enumerate(dates[1:], 1):
        prev_date = dates[i-1]
        
        curr_data = df[df['date'] == date]
        prev_data = df[df['date'] == prev_date]
        
        if len(curr_data) < 100 or len(prev_data) < 100:
            continue
        
        open_price = curr_data.iloc[0]['open']
        close_price = curr_data.iloc[-1]['close']
        prev_close = prev_data.iloc[-1]['close']
        
        gap_pct = (open_price - prev_close) / prev_close * 100
        day_return = (close_price - open_price) / open_price * 100
        
        days.append({
            'date': date,
            'gap_pct': gap_pct,
            'day_return': day_return,
            'gap_filled': (gap_pct > 0 and curr_data['low'].min() <= prev_close) or 
                         (gap_pct < 0 and curr_data['high'].max() >= prev_close)
        })
    
    gaps_df = pd.DataFrame(days)
    
    # Gap statistics
    print(f"\nGap Analysis ({len(gaps_df)} days):")
    print(f"  Average gap size: {gaps_df['gap_pct'].abs().mean():.2f}%")
    print(f"  Gap fill rate: {gaps_df['gap_filled'].mean() * 100:.1f}%")
    
    # Gap fade (inverse relationship)
    up_gaps = gaps_df[gaps_df['gap_pct'] > 0.1]
    down_gaps = gaps_df[gaps_df['gap_pct'] < -0.1]
    
    if len(up_gaps) > 20:
        up_gap_return = up_gaps['day_return'].mean()
        print(f"\n  After UP gap (>0.1%): avg return {up_gap_return:+.2f}% ({'FADE' if up_gap_return < 0 else 'FOLLOW'})")
    
    if len(down_gaps) > 20:
        down_gap_return = down_gaps['day_return'].mean()
        print(f"  After DOWN gap (<-0.1%): avg return {down_gap_return:+.2f}% ({'FADE' if down_gap_return > 0 else 'FOLLOW'})")
    
    return gaps_df


def analyze_first_hour_momentum(df):
    """Analyze if first hour direction predicts rest of day."""
    print("\n" + "=" * 70)
    print("4. FIRST HOUR MOMENTUM PERSISTENCE")
    print("=" * 70)
    
    df = df.copy()
    df['date'] = df.index.date
    df['time'] = df.index.time
    
    first_hour_end = time(10, 30)
    
    results = []
    
    for date in df['date'].unique():
        day_data = df[df['date'] == date]
        
        first_hour = day_data[day_data['time'] <= first_hour_end]
        rest_of_day = day_data[day_data['time'] > first_hour_end]
        
        if len(first_hour) < 30 or len(rest_of_day) < 100:
            continue
        
        first_hour_return = (first_hour.iloc[-1]['close'] - first_hour.iloc[0]['open']) / first_hour.iloc[0]['open']
        rest_of_day_return = (rest_of_day.iloc[-1]['close'] - rest_of_day.iloc[0]['open']) / rest_of_day.iloc[0]['open']
        
        results.append({
            'date': date,
            'first_hour_return': first_hour_return * 100,
            'rest_of_day_return': rest_of_day_return * 100,
            'same_direction': (first_hour_return > 0) == (rest_of_day_return > 0)
        })
    
    results_df = pd.DataFrame(results)
    
    # Correlation
    correlation = results_df['first_hour_return'].corr(results_df['rest_of_day_return'])
    persistence = results_df['same_direction'].mean() * 100
    
    print(f"\nFirst Hour vs Rest of Day ({len(results_df)} days):")
    print(f"  Correlation: {correlation:.3f}")
    print(f"  Same direction: {persistence:.1f}%")
    
    # Strong first hours
    strong_up = results_df[results_df['first_hour_return'] > 0.5]
    strong_down = results_df[results_df['first_hour_return'] < -0.5]
    
    if len(strong_up) > 20:
        print(f"\n  After strong UP first hour (>0.5%): {strong_up['rest_of_day_return'].mean():+.2f}% avg")
    if len(strong_down) > 20:
        print(f"  After strong DOWN first hour (<-0.5%): {strong_down['rest_of_day_return'].mean():+.2f}% avg")
    
    return results_df


def analyze_volatility_patterns(df):
    """Analyze intraday volatility clustering."""
    print("\n" + "=" * 70)
    print("5. VOLATILITY ANALYSIS")
    print("=" * 70)
    
    df = df.copy()
    df['returns'] = df['close'].pct_change()
    df['abs_returns'] = df['returns'].abs()
    df['time'] = df.index.time
    df['hour'] = df.index.hour
    
    # Volatility by hour
    hourly_vol = df.groupby('hour')['abs_returns'].mean() * 100
    
    print("\nAverage |Return| by Hour:")
    for hour in range(9, 17):
        if hour in hourly_vol.index:
            vol = hourly_vol[hour]
            bars = "█" * int(vol * 500)
            print(f"  {hour:02d}:00 | {vol:.3f}% {bars}")
    
    peak_hour = hourly_vol.idxmax()
    low_hour = hourly_vol.idxmin()
    print(f"\n  Peak volatility: {peak_hour}:00")
    print(f"  Lowest volatility: {low_hour}:00")
    print(f"  Ratio: {hourly_vol[peak_hour] / hourly_vol[low_hour]:.1f}x")
    
    return hourly_vol


def analyze_intraday_mean_reversion(df):
    """Analyze mean reversion patterns."""
    print("\n" + "=" * 70)
    print("6. INTRADAY MEAN REVERSION ANALYSIS")
    print("=" * 70)
    
    df = df.copy()
    df['returns'] = df['close'].pct_change()
    
    # Calculate running VWAP
    df['vwap'] = (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()
    df['vwap_deviation'] = (df['close'] - df['vwap']) / df['vwap']
    
    # After large moves, does it revert?
    df['prev_return'] = df['returns'].shift(1)
    df['next_return'] = df['returns'].shift(-1)
    
    # Big up moves
    big_up = df[df['returns'] > 0.002]  # 0.2% move
    big_down = df[df['returns'] < -0.002]
    
    if len(big_up) > 100:
        next_after_up = big_up['next_return'].mean() * 10000
        print(f"\nAfter 0.2%+ UP move:")
        print(f"  Average next bar: {next_after_up:+.2f} bps ({'REVERT' if next_after_up < 0 else 'CONTINUE'})")
    
    if len(big_down) > 100:
        next_after_down = big_down['next_return'].mean() * 10000
        print(f"\nAfter 0.2%+ DOWN move:")
        print(f"  Average next bar: {next_after_down:+.2f} bps ({'REVERT' if next_after_down > 0 else 'CONTINUE'})")
    
    # VWAP deviation analysis
    far_above_vwap = df[df['vwap_deviation'] > 0.003]
    far_below_vwap = df[df['vwap_deviation'] < -0.003]
    
    if len(far_above_vwap) > 100:
        revert = far_above_vwap['next_return'].mean() * 10000
        print(f"\nWhen 0.3%+ ABOVE VWAP:")
        print(f"  Average next bar: {revert:+.2f} bps")
    
    if len(far_below_vwap) > 100:
        revert = far_below_vwap['next_return'].mean() * 10000
        print(f"\nWhen 0.3%+ BELOW VWAP:")
        print(f"  Average next bar: {revert:+.2f} bps")


def main():
    print("=" * 70)
    print("DEEP SPY INTRADAY PATTERN ANALYSIS")
    print("4+ Years of 1-Minute Data")
    print("=" * 70)
    
    # Load data
    df = load_spy_data()
    
    # Run analyses
    hourly_returns = analyze_time_of_day_returns(df)
    orb_results = analyze_opening_range(df, orb_minutes=15)
    gap_results = analyze_gap_behavior(df)
    momentum_results = analyze_first_hour_momentum(df)
    volatility = analyze_volatility_patterns(df)
    analyze_intraday_mean_reversion(df)
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY: KEY FINDINGS")
    print("=" * 70)
    
    print("\nMost Promising Patterns to Exploit:")
    print("  1. [TO BE DETERMINED BY ANALYSIS]")
    print("  2. [TO BE DETERMINED BY ANALYSIS]")
    print("  3. [TO BE DETERMINED BY ANALYSIS]")


if __name__ == "__main__":
    main()
