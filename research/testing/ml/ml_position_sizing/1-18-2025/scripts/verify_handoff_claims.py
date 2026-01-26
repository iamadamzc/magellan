"""
Verify new ML Model performance against SESSION_HANDOFF.md baselines.

Handoff Claims:
1. Baseline (All trades): +0.15 R
2. Previous Entry-Only ML: -0.12 R (Failed)
3. Conclusion: "Entry features not predictive enough"

This script tests if the new XGBoost model refutes Claim #3.
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

def run_verification():
    print("="*80)
    print("VERIFYING HANDOFF CLAIMS VS NEW GEN-2 MODEL")
    print("="*80)
    
    # 1. Load Data
    data_path = Path('research/ml_position_sizing/data/labeled_regimes_v2.csv')
    if not data_path.exists():
        print(f"Error: Data file not found at {data_path}")
        return
        
    df = pd.read_csv(data_path)
    print(f"Loaded {len(df)} total trades.")
    
    # 2. Calculate Baseline
    baseline_r = df['r_multiple'].mean()
    baseline_win_rate = (df['r_multiple'] > 0).mean() * 100
    
    print(f"\n--- BASELINE (All Trades) ---")
    print(f"Count: {len(df)}")
    print(f"Avg R: {baseline_r:>6.2f} R  (Handoff says +0.15R)")
    print(f"Win Rate: {baseline_win_rate:>5.1f}%")
    
    # 3. Prepare Features for New Model
    df['time_sin'], df['time_cos'] = get_cyclical_features(df)
    df['volume_ratio'] = df['volume_ratio'].fillna(1.0)
    df['atr_percentile'] = df['atr_percentile'].fillna(0.5)
    df['day_change_pct'] = df['day_change_pct'].astype(float)
    df['vol_volatility_ratio'] = df['atr_percentile'] / (df['volume_ratio'] + 0.001)
    
    features = ['time_sin', 'time_cos', 'volume_ratio', 'day_change_pct', 'atr_percentile', 'vol_volatility_ratio']
    
    # 4. Load & Predict with New Model
    model_path = Path('research/ml_position_sizing/models/bear_trap_enhanced_xgb.pkl')
    try:
        model_data = load_model(model_path)
        model = model_data['model']
    except Exception as e:
        print(f"Error loading model: {e}")
        return

    print(f"\n--- NEW MODEL EVALUATION ---")
    probs = model.predict_proba(df[features])[:, 1]
    df['ml_prob'] = probs
    
    # Apply Threshold > 0.50 (Standard Deployment)
    df_filtered = df[df['ml_prob'] >= 0.50]
    
    new_r = df_filtered['r_multiple'].mean()
    new_win_rate = (df_filtered['r_multiple'] > 0).mean() * 100
    count_filtered = len(df_filtered)
    pct_kept = (count_filtered / len(df)) * 100
    
    print(f"Threshold: Prob >= 0.50")
    print(f"Selected: {count_filtered} trades ({pct_kept:.1f}% of universe)")
    print(f"Avg R: {new_r:>6.2f} R")
    print(f"Win Rate: {new_win_rate:>5.1f}%")
    
    # 5. Verify Handoff Claims
    print(f"\n--- VERDICT ---")
    
    # Check if we beat baseline
    r_improvement = new_r - baseline_r
    if r_improvement > 0.1:
        print(f"✅ BEATS BASELINE: +{r_improvement:.2f}R improvement vs Global Average")
    else:
        print(f"❌ FAILS BASELINE: New model is not significantly better.")
        
    # Check if we beat previous ML failure (-0.12R)
    prev_ml_r = -0.12
    if new_r > prev_ml_r + 0.2:
        print(f"✅ BEATS OLD ML: +{new_r - prev_ml_r:.2f}R improvement vs Previous Attempt") 
        print("   Refutes claim: 'Entry features not predictive enough'")
    else:
        print(f"❌ CONFIRMS OLD ML: Still failing.")

    # 6. Year 2024 Specific Analysis (Apples-to-Apples with Handoff)
    print(f"\n--- 2024 SPECIFIC ANALYSIS (Handoff Cohort) ---")
    df['year'] = pd.to_datetime(df['entry_date']).dt.year
    df_2024 = df[df['year'] == 2024].copy()
    
    if len(df_2024) == 0:
        print("No 2024 data found.")
    else:
        base_2024_r = df_2024['r_multiple'].mean()
        print(f"2024 Baseline Count: {len(df_2024)}")
        print(f"2024 Baseline R:   {base_2024_r:>6.2f} R (Target: +0.15 R)")
        
        # Apply ML Filter to 2024
        df_2024_filtered = df_2024[df_2024['ml_prob'] >= 0.50]
        new_2024_r = df_2024_filtered['r_multiple'].mean()
        count_2024_filt = len(df_2024_filtered)
        
        print(f"ML Filtered Count: {count_2024_filt}")
        print(f"ML Filtered R:     {new_2024_r:>6.2f} R")
        
        if new_2024_r > base_2024_r:
             print(f"✅ ML IMPROVES 2024: +{new_2024_r - base_2024_r:.2f}R")
        else:
             print(f"❌ ML FAILS 2024")

    # 7. Classification Report (Optional)
    print(f"\n[Bonus] Top Conviction (Prob >= 0.75)")
    df_top = df[df['ml_prob'] >= 0.75]
    if len(df_top) > 0:
        top_r = df_top['r_multiple'].mean()
        print(f"Avg R: {top_r:.2f} R (Count: {len(df_top)})")
    else:
        print("No trades found > 0.75 prob")

if __name__ == "__main__":
    run_verification()
