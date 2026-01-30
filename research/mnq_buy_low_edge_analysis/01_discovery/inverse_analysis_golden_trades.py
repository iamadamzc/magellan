"""
=============================================================================
MNQ INVERSE ANALYSIS: Discovering the Statistical DNA of a Winning Trade
=============================================================================

Role: Senior Data Scientist (Quant Research)
Objective: Perform an inverse analysis to find the "Golden Target" conditions
           that consistently produce low-drawdown, high-reward entries.

Methodology:
1. Define "Golden Target" - Perfect trades with +40pt reward, <-12pt max drawdown
2. Generate candidate features (time, trend, stretch, momentum, volatility, panic)
3. Comparative analysis: Golden Rows vs Normal Noise

Author: Magellan Quant Research
Date: 2026-01-30
"""

import pandas as pd
import numpy as np
import glob
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# CONFIGURATION
# =============================================================================

# Define the "Golden Target" parameters
REWARD_TARGET_POINTS = 40    # Minimum high reached in next 20 bars
RISK_LIMIT_POINTS = 12       # Maximum drawdown allowed in next 20 bars
FORWARD_WINDOW = 20          # 20 minutes forward look

# Technical indicator parameters
EMA_PERIOD = 200
RSI_PERIOD = 14
ATR_PERIOD = 14
VOLUME_AVG_PERIOD = 20

# Data paths
DATA_DIR = Path(r"a:\1\Magellan\data\cache\futures")
MNQ_CSV = Path(r"A:\1\Magellan\data\cache\futures\MNQ\glbx-mdp3-20210129-20260128.ohlcv-1m.csv")
OUTPUT_DIR = Path(r"a:\1\Magellan\research\mnq_buy_low_edge_analysis")

# =============================================================================
# TECHNICAL INDICATOR FUNCTIONS
# =============================================================================

def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """Calculate Exponential Moving Average."""
    return series.ewm(span=period, adjust=False).mean()

def calculate_rsi(series: pd.Series, period: int) -> pd.Series:
    """Calculate Relative Strength Index."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    
    avg_gain = gain.ewm(span=period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(span=period, min_periods=period, adjust=False).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int) -> pd.Series:
    """Calculate Average True Range."""
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return true_range.ewm(span=period, adjust=False).mean()

def calculate_vwap_cumulative(df: pd.DataFrame) -> pd.Series:
    """Calculate session-based VWAP (resets each day)."""
    df = df.copy()
    df['date'] = df.index.date if hasattr(df.index, 'date') else pd.to_datetime(df['datetime']).dt.date
    df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
    df['tp_volume'] = df['typical_price'] * df['volume']
    
    # Cumulative within each day
    df['cum_tp_vol'] = df.groupby('date')['tp_volume'].cumsum()
    df['cum_vol'] = df.groupby('date')['volume'].cumsum()
    
    vwap = df['cum_tp_vol'] / df['cum_vol']
    return vwap

def count_consecutive_candles(df: pd.DataFrame) -> pd.DataFrame:
    """Count consecutive red/green candles."""
    df = df.copy()
    df['is_green'] = df['close'] > df['open']
    df['direction_change'] = df['is_green'] != df['is_green'].shift(1)
    df['streak_group'] = df['direction_change'].cumsum()
    
    # Count within each streak
    df['streak_count'] = df.groupby('streak_group').cumcount() + 1
    
    # Positive for green streaks, negative for red streaks
    df['consecutive_candles'] = df['streak_count'] * df['is_green'].map({True: 1, False: -1})
    
    return df['consecutive_candles']

# =============================================================================
# MAIN ANALYSIS FUNCTIONS
# =============================================================================

def load_all_data() -> pd.DataFrame:
    """Load the full MNQ 1-minute dataset from CSV."""
    print(f"Loading full MNQ dataset from: {MNQ_CSV.name}")
    
    # Load CSV
    df = pd.read_csv(MNQ_CSV)
    print(f"  Raw rows loaded: {len(df):,}")
    
    # Parse timestamp and set as index
    df['datetime'] = pd.to_datetime(df['ts_event'].str[:19])
    df = df.set_index('datetime')
    
    # Rename columns to standard OHLCV
    df = df.rename(columns={
        'open': 'open',
        'high': 'high', 
        'low': 'low',
        'close': 'close',
        'volume': 'volume'
    })
    
    # Keep only OHLCV columns
    df = df[['open', 'high', 'low', 'close', 'volume', 'symbol']].copy()
    
    # Get unique symbols to understand the data
    symbols = df['symbol'].unique()
    print(f"  Unique contract symbols: {len(symbols)}")
    
    # Group by timestamp and aggregate (use front-month - highest volume per timestamp)
    # For OHLCV aggregation across contracts at same timestamp
    df_agg = df.groupby(df.index).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min', 
        'close': 'last',
        'volume': 'sum'
    })
    
    df_agg = df_agg.sort_index()
    df_agg = df_agg[~df_agg.index.duplicated(keep='first')]
    
    # Get trading days count
    unique_days = len(set(df_agg.index.date))
    
    print(f"\n[DATA] Total rows after aggregation: {len(df_agg):,}")
    print(f"[DATA] Unique trading days: {unique_days:,}")
    print(f"[DATA] Date range: {df_agg.index.min()} to {df_agg.index.max()}")
    
    return df_agg


def calculate_golden_target(df: pd.DataFrame) -> pd.DataFrame:
    """
    Define the "Golden Target" - a perfect sniper entry.
    
    Criteria:
    - REWARD: High of next 20 bars reaches +40 points above entry Close
    - RISK: Low of next 20 bars never drops more than -12 points below entry Close
    """
    print("\n[TARGET] Calculating Golden Target (Sniper Entries)...")
    
    df = df.copy()
    
    # Pre-calculate rolling max high and min low for next 20 bars
    # Using shift to look FORWARD (negative shift)
    df['future_max_high'] = df['high'].shift(-1).rolling(window=FORWARD_WINDOW, min_periods=FORWARD_WINDOW).max().shift(-(FORWARD_WINDOW-1))
    df['future_min_low'] = df['low'].shift(-1).rolling(window=FORWARD_WINDOW, min_periods=FORWARD_WINDOW).min().shift(-(FORWARD_WINDOW-1))
    
    # Calculate MFE (Maximum Favorable Excursion) and MAE (Maximum Adverse Excursion)
    df['MFE'] = df['future_max_high'] - df['close']  # How high price goes
    df['MAE'] = df['close'] - df['future_min_low']   # How low price goes (positive = bad)
    
    # Define Golden Target
    df['Target'] = (df['MFE'] >= REWARD_TARGET_POINTS) & (df['MAE'] <= RISK_LIMIT_POINTS)
    
    # Statistics
    valid_mask = df['MFE'].notna() & df['MAE'].notna()
    total_valid = valid_mask.sum()
    golden_count = df.loc[valid_mask, 'Target'].sum()
    
    print(f"  [OK] Total valid rows (with full forward window): {total_valid:,}")
    print(f"  [GOLDEN] Golden Target rows: {golden_count:,} ({100*golden_count/total_valid:.2f}%)")
    
    return df

def calculate_features(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate all candidate features."""
    print("\n[FEATURES] Calculating Candidate Features...")
    
    df = df.copy()
    
    # Ensure we have a datetime index
    if not isinstance(df.index, pd.DatetimeIndex):
        if 'datetime' in df.columns:
            df.index = pd.to_datetime(df['datetime'])
        else:
            raise ValueError("Cannot determine datetime index")
    
    # 1. TIME: Hour of day
    df['Hour'] = df.index.hour
    print("  [+] Hour of day")
    
    # 2. TREND: Distance from 200-period EMA
    df['EMA200'] = calculate_ema(df['close'], EMA_PERIOD)
    df['Trend_Distance'] = df['close'] - df['EMA200']
    print(f"  [+] Trend (Distance from {EMA_PERIOD}-period EMA)")
    
    # 3. STRETCH: Distance from VWAP
    df['VWAP'] = calculate_vwap_cumulative(df)
    df['Stretch_VWAP'] = df['close'] - df['VWAP']
    print("  [+] Stretch (Distance from VWAP)")
    
    # 4. MOMENTUM: RSI (14-period)
    df['RSI'] = calculate_rsi(df['close'], RSI_PERIOD)
    print(f"  [+] Momentum (RSI {RSI_PERIOD})")
    
    # 5. VOLATILITY: ATR (14-period)
    df['ATR'] = calculate_atr(df['high'], df['low'], df['close'], ATR_PERIOD)
    print(f"  [+] Volatility (ATR {ATR_PERIOD})")
    
    # 6. PANIC: Volume Ratio
    df['Rolling_Avg_Vol'] = df['volume'].rolling(window=VOLUME_AVG_PERIOD).mean()
    df['Volume_Ratio'] = df['volume'] / df['Rolling_Avg_Vol']
    df['Volume_Ratio'] = df['Volume_Ratio'].replace([np.inf, -np.inf], np.nan)
    print(f"  [+] Panic (Volume Ratio vs {VOLUME_AVG_PERIOD}-bar avg)")
    
    # 7. CONSECUTIVE CANDLES: Count of consecutive red/green candles
    df['Consecutive_Candles'] = count_consecutive_candles(df)
    print("  [+] Consecutive Candles (+ for green, - for red)")
    
    # 8. Bonus: Price range (high-low)
    df['Range'] = df['high'] - df['low']
    print("  [+] Range (High - Low)")
    
    return df

def analyze_feature_divergence(df: pd.DataFrame) -> dict:
    """
    Compare statistics of Golden Rows vs Normal Rows.
    """
    print("\n" + "="*80)
    print("[REPORT] FEATURE IMPORTANCE REPORT: The Statistical DNA of a Winning Trade")
    print("="*80)
    
    # Filter to valid rows only
    valid_mask = df['Target'].notna() & df['RSI'].notna() & df['EMA200'].notna()
    df_valid = df[valid_mask].copy()
    
    golden = df_valid[df_valid['Target'] == True]
    normal = df_valid[df_valid['Target'] == False]
    
    print(f"\n[SUMMARY] Dataset Summary:")
    print(f"  * Total valid rows: {len(df_valid):,}")
    print(f"  * Golden Trade rows: {len(golden):,} ({100*len(golden)/len(df_valid):.3f}%)")
    print(f"  * Normal Market rows: {len(normal):,}")
    
    # Features to analyze
    features = [
        ('RSI', 'RSI (Momentum)'),
        ('Volume_Ratio', 'Volume Ratio (Panic)'),
        ('Stretch_VWAP', 'Distance from VWAP (Stretch)'),
        ('Trend_Distance', 'Distance from EMA200 (Trend)'),
        ('ATR', 'ATR (Volatility)'),
        ('Consecutive_Candles', 'Consecutive Candles'),
        ('Range', 'Bar Range (High-Low)'),
    ]
    
    results = {}
    
    print("\n" + "-"*80)
    print("[COMPARE] FEATURE COMPARISON: Golden Trades vs Normal Market")
    print("-"*80)
    
    for col, name in features:
        golden_mean = golden[col].mean()
        normal_mean = normal[col].mean()
        golden_median = golden[col].median()
        normal_median = normal[col].median()
        golden_std = golden[col].std()
        normal_std = normal[col].std()
        
        # Calculate divergence
        if normal_mean != 0:
            divergence_pct = abs(golden_mean - normal_mean) / abs(normal_mean) * 100
        else:
            divergence_pct = 0
        
        results[col] = {
            'name': name,
            'golden_mean': golden_mean,
            'normal_mean': normal_mean,
            'golden_median': golden_median,
            'normal_median': normal_median,
            'divergence_pct': divergence_pct,
            'direction': 'HIGHER' if golden_mean > normal_mean else 'LOWER'
        }
        
        print(f"\n[FEATURE] {name}:")
        print(f"   When Golden Trades happen, the average {col} is: {golden_mean:.2f}")
        print(f"   (vs Normal Market: {normal_mean:.2f})")
        print(f"   Divergence: {divergence_pct:.1f}% {results[col]['direction']}")
    
    # Time of Day Analysis
    print("\n" + "-"*80)
    print("[TIME] TIME OF DAY DISTRIBUTION: When Do Golden Trades Occur?")
    print("-"*80)
    
    golden_by_hour = golden.groupby('Hour').size()
    normal_by_hour = normal.groupby('Hour').size()
    
    # Calculate rate per hour
    total_by_hour = df_valid.groupby('Hour').size()
    golden_rate_by_hour = (golden_by_hour / total_by_hour * 100).fillna(0)
    
    print(f"\n{'Hour':<6} | {'Golden Trades':<15} | {'Total Bars':<12} | {'Golden Rate':>12}")
    print("-" * 55)
    
    for hour in range(24):
        golden_count = golden_by_hour.get(hour, 0)
        total_count = total_by_hour.get(hour, 0)
        rate = golden_rate_by_hour.get(hour, 0)
        bar = "#" * int(rate * 10) if rate > 0 else ""
        print(f"{hour:>4}:00 | {golden_count:>13,} | {total_count:>10,} | {rate:>10.3f}% {bar}")
    
    best_hour = golden_rate_by_hour.idxmax()
    best_rate = golden_rate_by_hour.max()
    
    print(f"\n[BEST] BEST HOUR: {best_hour}:00 with {best_rate:.3f}% Golden Trade rate")
    
    # Rank features by divergence
    print("\n" + "="*80)
    print("[RANK] FEATURE IMPORTANCE RANKING (by divergence from normal)")
    print("="*80)
    
    ranked = sorted(results.items(), key=lambda x: x[1]['divergence_pct'], reverse=True)
    
    for i, (col, data) in enumerate(ranked, 1):
        print(f"\n{i}. {data['name']}")
        print(f"   Divergence: {data['divergence_pct']:.1f}% {data['direction']}")
        print(f"   Golden Mean: {data['golden_mean']:.2f} | Normal Mean: {data['normal_mean']:.2f}")
    
    # Store time analysis
    results['_time_analysis'] = {
        'best_hour': best_hour,
        'best_rate': best_rate,
        'golden_by_hour': golden_by_hour.to_dict(),
        'golden_rate_by_hour': golden_rate_by_hour.to_dict()
    }
    
    return results

def generate_report(df: pd.DataFrame, results: dict) -> str:
    """Generate the final markdown report."""
    
    report = f"""# MNQ Inverse Analysis: The Statistical DNA of a Winning Trade

## Executive Summary

**Objective:** Discover what conditions are present when "perfect" trades occur.

**Definition of "Golden Trade" (Sniper Entry):**
- **REWARD**: Price reaches **+{REWARD_TARGET_POINTS} points** within next {FORWARD_WINDOW} minutes
- **RISK**: Max drawdown stays **under {RISK_LIMIT_POINTS} points** (tight stop survived)

---

## Dataset Overview

| Metric | Value |
|--------|-------|
| **Total Rows Analyzed** | {len(df):,} |
| **Date Range** | {df.index.min().strftime('%Y-%m-%d')} to {df.index.max().strftime('%Y-%m-%d')} |
| **Golden Trades Found** | {df['Target'].sum():,} |
| **Golden Trade Rate** | {100*df['Target'].sum()/len(df[df['Target'].notna()]):.4f}% |

---

## Feature Importance Report

### Key Findings

When a "Golden Trade" occurs, here's how the market conditions differ from normal:

"""
    
    # Add feature findings
    features_to_report = ['RSI', 'Volume_Ratio', 'Stretch_VWAP', 'Trend_Distance', 'ATR', 'Consecutive_Candles']
    
    for col in features_to_report:
        if col in results:
            data = results[col]
            report += f"""
#### {data['name']}

> **"When Golden Trades happen, the average {col} is {data['golden_mean']:.2f}"**  
> *(vs Normal Market: {data['normal_mean']:.2f})*  
> **Divergence: {data['divergence_pct']:.1f}% {data['direction']}**

"""
    
    # Time analysis
    time_data = results.get('_time_analysis', {})
    report += f"""
---

## Time of Day Analysis

**Best Hour for Golden Trades: {time_data.get('best_hour', 'N/A')}:00**  
Golden Trade Rate: {time_data.get('best_rate', 0):.3f}%

### Hourly Distribution

| Hour | Golden Rate |
|------|-------------|
"""
    
    for hour in range(24):
        rate = time_data.get('golden_rate_by_hour', {}).get(hour, 0)
        report += f"| {hour:02d}:00 | {rate:.3f}% |\n"
    
    # Ranking
    report += """
---

## Feature Importance Ranking

**Ranked by divergence from normal market conditions:**

"""
    
    ranked = sorted([(k, v) for k, v in results.items() if not k.startswith('_')], 
                    key=lambda x: x[1]['divergence_pct'], reverse=True)
    
    for i, (col, data) in enumerate(ranked, 1):
        report += f"{i}. **{data['name']}** - {data['divergence_pct']:.1f}% {data['direction']}\n"
    
    report += """
---

## Strategic Implications

Based on this inverse analysis, the statistical "DNA" of a winning trade shows:

1. **Focus on the most divergent features** - These provide the clearest signal differentiation
2. **Time your entries** - Certain hours have significantly higher Golden Trade rates
3. **Combine multiple signals** - Look for confluence of the top divergent features

---

*Generated by Magellan Quant Research - Inverse Analysis Module*
*Date: {date}*
"""
    
    report = report.replace("{date}", pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    return report

def main():
    """Main execution function."""
    print("="*80)
    print("[MNQ] INVERSE ANALYSIS: Discovering the DNA of a Winning Trade")
    print("="*80)
    print(f"\n[CONFIG] Target Definition:")
    print(f"   * REWARD: +{REWARD_TARGET_POINTS} points in next {FORWARD_WINDOW} mins")
    print(f"   * RISK: Max -{RISK_LIMIT_POINTS} points drawdown")
    
    # Step 1: Load data
    df = load_all_data()
    
    # Ensure proper columns
    required_cols = ['open', 'high', 'low', 'close', 'volume']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        # Try lowercase
        df.columns = [c.lower() for c in df.columns]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
    
    # Step 2: Calculate features
    df = calculate_features(df)
    
    # Step 3: Calculate Golden Target
    df = calculate_golden_target(df)
    
    # Step 4: Analyze divergence
    results = analyze_feature_divergence(df)
    
    # Step 5: Generate report
    report = generate_report(df, results)
    
    # Save outputs
    report_path = OUTPUT_DIR / "INVERSE_ANALYSIS_GOLDEN_TRADES.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n[SAVED] Report saved to: {report_path}")
    
    # Save detailed CSV
    csv_path = OUTPUT_DIR / "golden_trades_analysis.csv"
    export_cols = ['Hour', 'RSI', 'ATR', 'Volume_Ratio', 'Stretch_VWAP', 'Trend_Distance', 
                   'Consecutive_Candles', 'Range', 'MFE', 'MAE', 'Target']
    df[export_cols].to_csv(csv_path)
    print(f"[SAVED] Detailed data saved to: {csv_path}")
    
    print("\n" + "="*80)
    print("[DONE] INVERSE ANALYSIS COMPLETE")
    print("="*80)
    
    return df, results

if __name__ == "__main__":
    df, results = main()
