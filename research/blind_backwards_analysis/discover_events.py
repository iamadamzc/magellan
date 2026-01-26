"""
Phase 1: Target Definition - Winning Event Discovery

Identifies "Winning Events" in historical data based on:
- Magnitude: Price move > 1.5σ of trailing volatility
- Timeframe: Move completes within 30-60 bars
- Efficiency: Max drawdown < 50% of target move

NO classic patterns or standard indicators used.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


def calculate_atr(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """Calculate Average True Range without using standard indicator libraries."""
    high = df['high']
    low = df['low']
    close = df['close']
    
    # True Range components
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = true_range.rolling(window=period).mean()
    
    return atr


def identify_winning_events(
    df: pd.DataFrame,
    lookforward: int = 60,
    min_sigma: float = 1.5,
    max_dd_ratio: float = 0.5,
    atr_period: int = 20
) -> pd.DataFrame:
    """
    Scan each bar to identify winning events (significant directional moves).
    
    Parameters:
    -----------
    df : DataFrame with OHLCV data (indexed by timestamp)
    lookforward : Maximum bars to look for the move (default 60 = 1 hour)
    min_sigma : Minimum move in terms of ATR multiples (default 1.5)
    max_dd_ratio : Maximum drawdown as ratio of target move (default 0.5)
    atr_period : Period for ATR calculation (default 20)
    
    Returns:
    --------
    DataFrame with winning event labels and metadata
    """
    print(f"Calculating ATR with period {atr_period}...")
    atr = calculate_atr(df, period=atr_period)
    
    # Dynamic threshold: 1.5 * ATR (in price terms)
    threshold = min_sigma * atr
    
    n_bars = len(df)
    print(f"Scanning {n_bars:,} bars for winning events...")
    
    # Pre-allocate arrays for efficiency
    is_winning_long = np.zeros(n_bars, dtype=bool)
    is_winning_short = np.zeros(n_bars, dtype=bool)
    event_magnitude = np.zeros(n_bars)
    event_duration = np.zeros(n_bars, dtype=int)
    event_efficiency = np.zeros(n_bars)
    event_direction = np.full(n_bars, '', dtype=object)
    
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    thresh = threshold.values
    
    # Vectorized forward scan is complex, so we use optimized loop
    # Process in chunks for memory efficiency
    chunk_size = 10000
    progress_interval = 100000
    
    for i in range(atr_period, n_bars - lookforward):
        if i % progress_interval == 0:
            print(f"  Progress: {i:,} / {n_bars:,} ({100*i/n_bars:.1f}%)")
        
        if np.isnan(thresh[i]) or thresh[i] <= 0:
            continue
            
        entry_price = close[i]
        target_move = thresh[i]  # 1.5σ in price terms
        max_allowed_dd = target_move * max_dd_ratio
        
        # Scan forward for LONG opportunity
        max_high = entry_price
        max_drawdown_long = 0
        for j in range(i + 1, min(i + lookforward + 1, n_bars)):
            max_high = max(max_high, high[j])
            current_dd = max_high - low[j]
            max_drawdown_long = max(max_drawdown_long, entry_price - low[j])
            
            # Check if target reached
            profit = max_high - entry_price
            if profit >= target_move:
                # Check efficiency (drawdown constraint)
                if max_drawdown_long <= max_allowed_dd:
                    is_winning_long[i] = True
                    event_magnitude[i] = profit
                    event_duration[i] = j - i
                    event_efficiency[i] = profit / max(max_drawdown_long, 0.0001)
                    event_direction[i] = 'LONG'
                break
        
        # Scan forward for SHORT opportunity (if no long found)
        if not is_winning_long[i]:
            min_low = entry_price
            max_drawdown_short = 0
            for j in range(i + 1, min(i + lookforward + 1, n_bars)):
                min_low = min(min_low, low[j])
                max_drawdown_short = max(max_drawdown_short, high[j] - entry_price)
                
                # Check if target reached (price drops)
                profit = entry_price - min_low
                if profit >= target_move:
                    if max_drawdown_short <= max_allowed_dd:
                        is_winning_short[i] = True
                        event_magnitude[i] = profit
                        event_duration[i] = j - i
                        event_efficiency[i] = profit / max(max_drawdown_short, 0.0001)
                        event_direction[i] = 'SHORT'
                    break
    
    print(f"  Progress: {n_bars:,} / {n_bars:,} (100.0%)")
    
    # Build results DataFrame
    is_winning = is_winning_long | is_winning_short
    
    results = pd.DataFrame({
        'timestamp': df.index,
        'close': close,
        'atr': atr.values,
        'threshold': thresh,
        'is_winning': is_winning,
        'direction': event_direction,
        'magnitude': event_magnitude,
        'duration': event_duration,
        'efficiency': event_efficiency
    })
    
    win_count = is_winning.sum()
    long_count = is_winning_long.sum()
    short_count = is_winning_short.sum()
    
    print(f"\nResults:")
    print(f"  Total winning events: {win_count:,} ({100*win_count/n_bars:.2f}%)")
    print(f"  Long events: {long_count:,}")
    print(f"  Short events: {short_count:,}")
    
    return results


def process_symbol(
    symbol: str,
    data_path: Path,
    output_path: Path,
    lookforward: int = 60,
    min_sigma: float = 1.5
) -> Optional[pd.DataFrame]:
    """Process a single symbol and save winning events."""
    
    # Find the multi-year file
    pattern = f"{symbol}_1min_*20260124.parquet"
    files = list(data_path.glob(pattern))
    
    if not files:
        # Try alternative pattern
        pattern = f"{symbol}_1min_202*.parquet"
        files = sorted(data_path.glob(pattern), key=lambda x: x.stat().st_size, reverse=True)
    
    if not files:
        print(f"No data file found for {symbol}")
        return None
    
    # Use largest file (most complete dataset)
    file_path = files[0]
    print(f"\n{'='*60}")
    print(f"Processing {symbol} from {file_path.name}")
    print(f"{'='*60}")
    
    df = pd.read_parquet(file_path)
    print(f"Loaded {len(df):,} bars")
    print(f"Date range: {df.index.min()} to {df.index.max()}")
    
    results = identify_winning_events(
        df, 
        lookforward=lookforward, 
        min_sigma=min_sigma
    )
    
    # Save results
    output_file = output_path / f"{symbol}_winning_events.parquet"
    results.to_parquet(output_file, index=False)
    print(f"Saved to {output_file}")
    
    return results


def main():
    """Run Phase 1 event discovery on major indices."""
    
    # Paths
    base_path = Path(__file__).parent.parent.parent
    data_path = base_path / "data" / "cache" / "equities"
    output_path = Path(__file__).parent / "outputs"
    output_path.mkdir(exist_ok=True)
    
    # Symbols to analyze
    symbols = ['SPY', 'QQQ', 'IWM']
    
    # Parameters
    LOOKFORWARD = 60  # 60 minutes max hold
    MIN_SIGMA = 1.5   # 1.5x ATR minimum move
    
    print("=" * 60)
    print("PHASE 1: TARGET DEFINITION - WINNING EVENT DISCOVERY")
    print("=" * 60)
    print(f"Parameters:")
    print(f"  Lookforward window: {LOOKFORWARD} bars")
    print(f"  Minimum move: {MIN_SIGMA}σ (ATR multiples)")
    print(f"  Max drawdown ratio: 0.5")
    
    all_results = {}
    
    for symbol in symbols:
        results = process_symbol(
            symbol=symbol,
            data_path=data_path,
            output_path=output_path,
            lookforward=LOOKFORWARD,
            min_sigma=MIN_SIGMA
        )
        if results is not None:
            all_results[symbol] = results
    
    # Summary statistics
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for symbol, results in all_results.items():
        winning = results[results['is_winning']]
        print(f"\n{symbol}:")
        print(f"  Total bars: {len(results):,}")
        print(f"  Winning events: {len(winning):,} ({100*len(winning)/len(results):.2f}%)")
        if len(winning) > 0:
            print(f"  Avg magnitude: ${winning['magnitude'].mean():.4f}")
            print(f"  Avg duration: {winning['duration'].mean():.1f} bars")
            print(f"  Avg efficiency: {winning['efficiency'].mean():.2f}")
            print(f"  Long/Short split: {(winning['direction']=='LONG').sum()} / {(winning['direction']=='SHORT').sum()}")
    
    print("\n✓ Phase 1 complete. Event files saved to outputs/")
    return all_results


if __name__ == "__main__":
    main()
