"""
Run 2024 Backtest on Top 3 Tickers (GOEV, MULN, NKLA).

The user requested a "backtest on 2024 using the same tickers as the previous".
The previous Handoff mentioned "Baseline (2024, 3 symbols)".
Our data shows GOEV, MULN, NKLA are the top 3 by trade count in 2024.

This script compares Baseline vs ML Filtered performance for this specific subset.
"""
import pandas as pd
import numpy as np
import pickle
from pathlib import Path

def get_cyclical_features(df):
    minutes = df['entry_hour'] * 60 + df['entry_minute']
    day_minutes = 1440
    return np.sin(2 * np.pi * minutes / day_minutes), np.cos(2 * np.pi * minutes / day_minutes)

def load_model(path):
    with open(path, 'rb') as f:
        data = pickle.load(f)
    return data

def run_2024_backtest():
    print("="*80)
    print("2024 BACKTEST: GOEV, MULN, NKLA")
    print("="*80)
    
    # 1. Load Data
    data_path = Path('research/ml_position_sizing/data/labeled_regimes_v2.csv')
    df = pd.read_csv(data_path)
    
    # 2. Filter for 2024 and Top 3 Tickers
    df['year'] = pd.to_datetime(df['entry_date']).dt.year
    target_tickers = ['GOEV', 'MULN', 'NKLA']
    
    df_2024 = df[(df['year'] == 2024) & (df['symbol'].isin(target_tickers))].copy()
    
    if len(df_2024) == 0:
        print("No trades found for 2024 + Top 3 Tickers.")
        return

    # 3. Calculate Baseline Performance
    baseline_count = len(df_2024)
    baseline_r = df_2024['r_multiple'].mean()
    baseline_win_rate = (df_2024['r_multiple'] > 0).mean() * 100
    baseline_pnl = df_2024['r_multiple'].sum() # Assuming 1R risk per trade
    
    print(f"\n--- BASELINE (2024: GOEV, MULN, NKLA) ---")
    print(f"Trades: {baseline_count}")
    print(f"Avg R:   {baseline_r:>6.2f} R")
    print(f"Total R: {baseline_pnl:>6.1f} R")
    print(f"Win Rate: {baseline_win_rate:>5.1f}%")
    
    # 4. Apply ML Filter
    # Feature Eng
    df_2024['time_sin'], df_2024['time_cos'] = get_cyclical_features(df_2024)
    df_2024['volume_ratio'] = df_2024['volume_ratio'].fillna(1.0)
    df_2024['atr_percentile'] = df_2024['atr_percentile'].fillna(0.5)
    df_2024['day_change_pct'] = df_2024['day_change_pct'].astype(float)
    df_2024['vol_volatility_ratio'] = df_2024['atr_percentile'] / (df_2024['volume_ratio'] + 0.001)
    
    features = ['time_sin', 'time_cos', 'volume_ratio', 'day_change_pct', 'atr_percentile', 'vol_volatility_ratio']
    
    # Load Model
    model_path = Path('research/ml_position_sizing/models/bear_trap_enhanced_xgb.pkl')
    model_data = load_model(model_path)
    model = model_data['model']
    
    # Predict
    probs = model.predict_proba(df_2024[features])[:, 1]
    df_2024['ml_prob'] = probs
    
    # Filter > 0.50
    df_ml = df_2024[df_2024['ml_prob'] >= 0.50]
    
    ml_count = len(df_ml)
    ml_r = df_ml['r_multiple'].mean()
    ml_total_r = df_ml['r_multiple'].sum()
    ml_win_rate = (df_ml['r_multiple'] > 0).mean() * 100
    
    print(f"\n--- ML ENHANCED (Prob >= 0.50) ---")
    print(f"Trades:   {ml_count} (Filter Rate: {ml_count/baseline_count:.1%})")
    print(f"Avg R:     {ml_r:>6.2f} R")
    print(f"Total R:   {ml_total_r:>6.1f} R")
    print(f"Win Rate:  {ml_win_rate:>5.1f}%")
    
    # 5. Comparison
    print(f"\n--- RESULTS SUMMARY ---")
    improvement_r = ml_r - baseline_r
    if improvement_r > 0:
        print(f"✅ PROFITABILITY INCREASED per trade: +{improvement_r:.2f} R")
    else:
        print(f"❌ PROFITABILITY DECREASED")
        
    print(f"Total PnL Change: {baseline_pnl:.1f} R -> {ml_total_r:.1f} R")
    
    # Breakdown by Ticker
    print(f"\n--- BREAKDOWN BY TICKER ---")
    for ticker in target_tickers:
        ticker_base = df_2024[df_2024['symbol'] == ticker]
        ticker_ml = ticker_base[ticker_base['ml_prob'] >= 0.50]
        
        if len(ticker_base) > 0:
            base_r = ticker_base['r_multiple'].mean()
            ml_r_tk = ticker_ml['r_multiple'].mean() if len(ticker_ml) > 0 else 0.0
            print(f"{ticker:>4}: Base {base_r:>5.2f} R ({len(ticker_base)}) -> ML {ml_r_tk:>5.2f} R ({len(ticker_ml)})")

if __name__ == "__main__":
    run_2024_backtest()
