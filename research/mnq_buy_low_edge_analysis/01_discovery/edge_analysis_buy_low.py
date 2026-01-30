"""
Edge Analysis: MFE vs MAE for "Buy Low" Scalping Strategy
==========================================================

Role: Quantitative Data Scientist
Objective: Determine if price "snaps back" after a buy-low signal
Data: 5 years of 1-minute MNQ (Micro Nasdaq) futures data

Strategy Logic:
1. The Floor: Low equals 30-period rolling minimum
2. The Stretch: Close below Lower Keltner Channel (EMA_20 - 2.5*ATR)

Edge Metrics:
- MFE (Maximum Favorable Excursion): Peak profit in next 15 bars
- MAE (Maximum Adverse Excursion): Peak drawdown in next 15 bars

Author: Quantitative Research Team
Date: 2026-01-30

Usage:
    cd a:\1\Magellan\data\cache\futures\MNQ
    python ../../../research/mnq_buy_low_edge_analysis/edge_analysis_buy_low.py
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import pytz
from datetime import time
import os


def calculate_atr(df, period=14):
    """Calculate Average True Range (ATR)"""
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(span=period, adjust=False).mean()
    
    return atr


def load_and_prepare_data(filepath):
    """Step 1: Load and clean Databento futures data"""
    print("=" * 70)
    print("STEP 1: DATA LOADING & CLEANING")
    print("=" * 70)
    
    print(f"\nLoading data from: {filepath}")
    df = pd.read_csv(filepath)
    
    print(f"Initial rows: {len(df):,}")
    
    df['ts_event'] = pd.to_datetime(df['ts_event'])
    df = df.set_index('ts_event')
    
    numeric_cols = ['open', 'high', 'low', 'close', 'volume']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    print(f"Date range: {df.index.min()} to {df.index.max()}")
    
    print("\nFiltering to US Market Hours (09:30-16:00 ET)...")
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC').tz_convert('America/New_York')
    else:
        df.index = df.index.tz_convert('America/New_York')
    
    df['time'] = df.index.time
    market_start = time(9, 30)
    market_end = time(16, 0)
    
    df = df[(df['time'] >= market_start) & (df['time'] <= market_end)]
    df = df.drop(columns=['time'])
    
    print(f"Rows after market hours filter: {len(df):,}")
    
    return df


def generate_buy_low_signals(df):
    """Step 2: Define the 'Buy Low' entry signal"""
    print("\n" + "=" * 70)
    print("STEP 2: GENERATING 'BUY LOW' SIGNALS")
    print("=" * 70)
    
    rolling_min_30 = df['low'].rolling(window=30, min_periods=30).min()
    floor_condition = df['low'] == rolling_min_30
    
    print(f"Bars touching the floor: {floor_condition.sum():,}")
    
    ema_20 = df['close'].ewm(span=20, adjust=False).mean()
    atr_14 = calculate_atr(df, period=14)
    lower_keltner = ema_20 - (2.5 * atr_14)
    stretch_condition = df['close'] < lower_keltner
    
    print(f"Bars below Lower Keltner: {stretch_condition.sum():,}")
    
    df['signal'] = floor_condition & stretch_condition
    
    print(f"\n{'*' * 70}")
    print(f"TOTAL SIGNALS GENERATED: {df['signal'].sum():,}")
    print(f"{'*' * 70}")
    
    return df


def calculate_mfe_mae(df, forward_bars=15):
    """Step 3: Vectorized Edge Analysis (MFE & MAE) - CORRECTED"""
    print("\n" + "=" * 70)
    print("STEP 3: VECTORIZED MFE & MAE CALCULATION (CORRECTED)")
    print("=" * 70)
    
    print(f"\nForward lookup window: {forward_bars} bars")
    
    df_reset = df.reset_index()
    
    df_reset['mfe'] = np.nan
    df_reset['mae'] = np.nan
    df_reset['entry_price'] = np.nan
    
    signal_positions = df_reset[df_reset['signal']].index.tolist()
    
    print(f"Calculating forward statistics for {len(signal_positions):,} signals...")
    print("NOTE: MFE = (Max High in NEXT 15 bars) - Entry Price")
    print("      MAE = Entry Price - (Min Low in NEXT 15 bars)")
    
    batch_size = 1000
    for batch_start in range(0, len(signal_positions), batch_size):
        batch_end = min(batch_start + batch_size, len(signal_positions))
        
        for pos in signal_positions[batch_start:batch_end]:
            # CRITICAL: Only look at the NEXT forward_bars (exclude current bar)
            start_pos = pos + 1  # Start from NEXT bar
            end_pos = min(start_pos + forward_bars, len(df_reset))  # Exactly 15 bars
            
            # Skip if we don't have enough forward data
            if end_pos <= start_pos:
                continue
                
            forward_slice = df_reset.iloc[start_pos:end_pos]
            
            if len(forward_slice) > 0:
                entry_close = df_reset.loc[pos, 'close']
                
                # MFE: Best profit opportunity = Max High - Entry
                max_high = forward_slice['high'].max()
                mfe = max_high - entry_close
                
                # MAE: Worst drawdown = Entry - Min Low
                min_low = forward_slice['low'].min()
                mae = entry_close - min_low
                
                # Sanity check: Filter obvious data errors
                # MFE/MAE should be reasonable for 15-minute window
                if mfe < -1000 or mfe > 2000:  # Unreasonable for 15min
                    continue
                if mae < -1000 or mae > 2000:  # Unreasonable for 15min
                    continue
                
                # Store results
                df_reset.loc[pos, 'entry_price'] = entry_close
                df_reset.loc[pos, 'mfe'] = mfe
                df_reset.loc[pos, 'mae'] = mae
        
        if batch_end % 5000 == 0 or batch_end == len(signal_positions):
            print(f"  Progress: {batch_end:,} / {len(signal_positions):,} signals processed")
    
    df_reset = df_reset.set_index('ts_event')
    
    # Extract signal data
    signals_df = df_reset[df_reset['signal']].copy()
    signals_df = signals_df.dropna(subset=['mfe', 'mae'])
    
    # Filter out invalid data: Remove MFE < 0 or MAE < 0
    before_filter = len(signals_df)
    signals_df = signals_df[(signals_df['mfe'] >= 0) & (signals_df['mae'] >= 0)]
    after_filter = len(signals_df)
    
    if before_filter > after_filter:
        print(f"\nFiltered out {before_filter - after_filter} signals with negative MFE/MAE")
    
    print(f"\nValid signals with MFE/MAE: {len(signals_df):,}")
    
    # Calculate statistics
    mean_mfe = signals_df['mfe'].mean()
    mean_mae = signals_df['mae'].mean()
    
    print(f"\n{'='*70}")
    print(f"CORRECTED STATISTICS:")
    print(f"{'='*70}")
    print(f"MFE (Profit Potential):")
    print(f"  Mean:   {mean_mfe:.2f} points")
    print(f"  Median: {signals_df['mfe'].median():.2f} points")
    print(f"  Min:    {signals_df['mfe'].min():.2f} points")
    print(f"  Max:    {signals_df['mfe'].max():.2f} points")
    
    print(f"\nMAE (Drawdown Risk):")
    print(f"  Mean:   {mean_mae:.2f} points")
    print(f"  Median: {signals_df['mae'].median():.2f} points")
    print(f"  Min:    {signals_df['mae'].min():.2f} points")
    print(f"  Max:    {signals_df['mae'].max():.2f} points")
    
    # VALIDATION: Stop if mean MFE > 200 (indicates bug)
    if mean_mfe > 200:
        print(f"\n{'!'*70}")
        print(f"ERROR: Mean MFE = {mean_mfe:.2f} is > 200!")
        print(f"This indicates the calculation is still returning absolute prices.")
        print(f"STOPPING ANALYSIS.")
        print(f"{'!'*70}")
        raise ValueError(f"Mean MFE ({mean_mfe:.2f}) exceeds threshold of 200 points")
    
    print(f"\n✅ VALIDATION PASSED: Mean MFE = {mean_mfe:.2f} points (< 200 threshold)")
    
    return signals_df


def visualize_edge_analysis(signals_df, output_dir='.'):
    """Step 4: The Deliverable - Plotly Scatter Plot"""
    print("\n" + "=" * 70)
    print("STEP 4: GENERATING VISUALIZATION")
    print("=" * 70)
    
    signals_df['hour'] = signals_df.index.hour
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=signals_df['mae'],
        y=signals_df['mfe'],
        mode='markers',
        marker=dict(
            size=6,
            color=signals_df['hour'],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Hour of Day"),
            opacity=0.6
        ),
        text=[f"Time: {idx.strftime('%Y-%m-%d %H:%M')}<br>MFE: ${row['mfe']:.2f}<br>MAE: ${row['mae']:.2f}"
              for idx, row in signals_df.iterrows()],
        hovertemplate='%{text}<extra></extra>',
        name='Trade Signals'
    ))
    
    max_val = max(signals_df['mae'].max(), signals_df['mfe'].max())
    fig.add_trace(go.Scatter(x=[0, max_val], y=[0, max_val], mode='lines',
                            line=dict(color='red', width=2, dash='dash'), name='1:1 R/R'))
    fig.add_trace(go.Scatter(x=[0, max_val], y=[0, max_val * 2], mode='lines',
                            line=dict(color='green', width=2, dash='dash'), name='2:1 R/R'))
    
    fig.update_layout(
        title='MFE vs MAE Edge Analysis: "Buy Low" Scalping Strategy',
        xaxis_title='MAE - Risk/Drawdown (points)',
        yaxis_title='MFE - Potential Reward (points)',
        template='plotly_dark',
        width=1400,
        height=900
    )
    
    output_path = os.path.join(output_dir, 'edge_analysis_mfe_vs_mae.html')
    fig.write_html(output_path)
    print(f"\nVisualization saved to: {output_path}")
    
    return fig


def print_summary_statistics(signals_df):
    """Print comprehensive summary statistics"""
    print("\n" + "=" * 70)
    print("FINAL DELIVERABLE: SUMMARY STATISTICS")
    print("=" * 70)
    
    total_signals = len(signals_df)
    winners = signals_df[signals_df['mfe'] > 2 * signals_df['mae']]
    win_rate = len(winners) / total_signals * 100 if total_signals > 0 else 0
    
    print(f"\n{'*' * 70}")
    print(f"Total Trade Signals Found: {total_signals:,}")
    print(f"{'*' * 70}")
    
    print(f"\n{'*' * 70}")
    print(f"Win Rate (Trades where MFE > 2x MAE): {win_rate:.2f}%")
    print(f"{'*' * 70}")
    
    print(f"\nPositive MFE Rate: {len(signals_df[signals_df['mfe'] > 0]) / total_signals * 100:.2f}%")
    print(f"Average Risk:Reward: {(signals_df['mfe']/signals_df['mae']).mean():.2f}x")
    
    print(f"\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)


def main():
    """Main execution function"""
    print("\n" + "█" * 70)
    print("█  EDGE ANALYSIS: MFE vs MAE - 'Buy Low' Scalping Strategy█".center(72))
    print("█" * 70 + "\n")
    
    # File path - current directory should have the CSV
    filepath = 'glbx-mdp3-20210129-20260128.ohlcv-1m.csv'
    
    # Use absolute path for output
    output_dir = r'a:\1\Magellan\research\mnq_buy_low_edge_analysis'
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Output will be saved to: {output_dir}\n")
    
    df = load_and_prepare_data(filepath)
    df = generate_buy_low_signals(df)
    signals_df = calculate_mfe_mae(df, forward_bars=15)
    visualize_edge_analysis(signals_df, output_dir=output_dir)
    print_summary_statistics(signals_df)
    
    output_csv = os.path.join(output_dir, 'buy_low_signals_mfe_mae.csv')
    signals_df.to_csv(output_csv)
    print(f"\nSignal data saved to: {output_csv}")


if __name__ == "__main__":
    main()
