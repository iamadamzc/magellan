"""
Compare original Decision Tree vs Enhanced XGBoost model.
"""
import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from sklearn.metrics import accuracy_score, roc_auc_score

def load_model(path):
    with open(path, 'rb') as f:
        data = pickle.load(f)
    return data

def get_cyclical_features(df):
    minutes = df['entry_hour'] * 60 + df['entry_minute']
    day_minutes = 1440
    return np.sin(2 * np.pi * minutes / day_minutes), np.cos(2 * np.pi * minutes / day_minutes)

def compare_models():
    # Load Data
    data_path = Path('research/ml_position_sizing/data/labeled_regimes_v2.csv')
    df = pd.read_csv(data_path)
    
    # 1. Prepare Features for Old Model
    # Re-create binned features logic from train_entry_only_model.py
    df['entry_datetime'] = pd.to_datetime(df['entry_date'])
    df['entry_hour'] = df['entry_datetime'].dt.hour
    df['entry_day_of_week'] = df['entry_datetime'].dt.dayofweek
    
    df['time_score'] = (df['entry_hour'] >= 15).astype(int)
    df['is_midweek'] = ((df['entry_day_of_week'] >= 1) & (df['entry_day_of_week'] <= 3)).astype(int)
    df['high_volume'] = (df['volume_ratio'] > 2.0).astype(int)
    df['big_drop'] = (df['day_change_pct'] < -20).astype(int)
    df['high_volatility'] = (df['atr_percentile'] > 0.7).astype(int)
    
    old_features = ['time_score', 'is_midweek', 'high_volume', 'big_drop', 'high_volatility']
    
    # 2. Prepare Features for New Model
    df['time_sin'], df['time_cos'] = get_cyclical_features(df)
    df['volume_ratio'] = df['volume_ratio'].fillna(1.0)
    df['atr_percentile'] = df['atr_percentile'].fillna(0.5)
    df['day_change_pct'] = df['day_change_pct'].astype(float)
    df['vol_volatility_ratio'] = df['atr_percentile'] / (df['volume_ratio'] + 0.001)
    
    new_features = ['time_sin', 'time_cos', 'volume_ratio', 'day_change_pct', 'atr_percentile', 'vol_volatility_ratio']
    
    # Load Models
    old_model_data = load_model('research/ml_position_sizing/models/bear_trap_entry_only_classifier.pkl')
    new_model_data = load_model('research/ml_position_sizing/models/bear_trap_enhanced_xgb.pkl')
    
    old_model = old_model_data['model']
    new_model = new_model_data['model']
    
    # Predict
    # Old model predicts classes directly: 0, 1, 2 (NO_ADD, ADD_NEUTRAL, ADD_ALLOWED) or strings?
    # Let's check predictions.
    
    X_old = df[old_features].fillna(0)
    y_pred_old = old_model.predict(X_old)
    
    X_new = df[new_features]
    y_prob_new = new_model.predict_proba(X_new)[:, 1] # Prob of ADD_ALLOWED
    
    # Evaluation
    # Ground Truth: ADD_ALLOWED is the target
    y_true = (df['regime_label_v2'] == 'ADD_ALLOWED').astype(int)
    
    # Old model might output strings. Map to binary for fair comparison if possible.
    # If old model outputs 'ADD_ALLOWED', 'ADD_NEUTRAL', 'NO_ADD'
    print("Old Prediction Sample:", y_pred_old[:5])
    
    # Assume strings. High conviction = 'ADD_ALLOWED'
    y_pred_old_binary = (y_pred_old == 'ADD_ALLOWED').astype(int)
    
    # Metrics
    acc_old = accuracy_score(y_true, y_pred_old_binary)
    # AUC for old is hard without probas, but trees have predict_proba
    y_prob_old = old_model.predict_proba(X_old)
    # Finding index of 'ADD_ALLOWED'
    class_idx = np.where(old_model.classes_ == 'ADD_ALLOWED')[0][0]
    y_prob_old_pos = y_prob_old[:, class_idx]
    auc_old = roc_auc_score(y_true, y_prob_old_pos)
    
    auc_new = roc_auc_score(y_true, y_prob_new)
    
    print("\n--- Model Comparison ---")
    print(f"Original DT (Binned) AUC: {auc_old:.4f}")
    print(f"Enhanced XGB (Cont.) AUC: {auc_new:.4f}")
    
    print(f"\nImprovement: +{(auc_new - auc_old)*100:.2f}% AUC")
    
    # Bucket Analysis
    df['new_prob'] = y_prob_new
    df['target'] = y_true
    df['new_bucket'] = pd.qcut(df['new_prob'], 5, labels=False, duplicates='drop')
    
    print("\nNew Model Performance by Probability Quintile:")
    summary = df.groupby('new_bucket').agg({
        'r_multiple': 'mean',
        'target': ['mean', 'count'] # Win Rate approx (precision of regime)
    })
    print(summary)

if __name__ == "__main__":
    compare_models()
