"""
Train Enhanced XGBoost Model for Bear Trap Regime Filtering.
Features:
- Continuous inputs (no binning)
- Cyclical time encoding
- Probability calibration
- XGBoost Classifier
"""
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import roc_auc_score, log_loss, classification_report
import pickle
import joblib
from pathlib import Path
import math

def calculate_cyclical_features(df, col_hour, col_minute):
    """Encodes time as cyclical sin/cos features."""
    # Normalize time to 0-2pi. 
    # Market hours approx 9:30 - 16:00 (390 mins). 
    # Or just use 24h cycle for simplicity/robustness.
    minutes_since_midnight = df[col_hour] * 60 + df[col_minute]
    
    # 24 * 60 = 1440 minutes in a day
    day_minutes = 1440
    
    df['time_sin'] = np.sin(2 * np.pi * minutes_since_midnight / day_minutes)
    df['time_cos'] = np.cos(2 * np.pi * minutes_since_midnight / day_minutes)
    return df

def feature_engineering(df):
    """Creates enhanced continuous features."""
    df = df.copy()
    
    # 1. Cyclical Time
    df = calculate_cyclical_features(df, 'entry_hour', 'entry_minute')
    
    # 2. Volatility/Volume Interaction
    # Handle pot. div by zero or missing
    df['volume_ratio'] = df['volume_ratio'].fillna(1.0)
    df['atr_percentile'] = df['atr_percentile'].fillna(0.5)
    
    df['vol_volatility_ratio'] = df['atr_percentile'] / (df['volume_ratio'] + 0.001)
    
    # 3. Raw Continuous Features (ensure float)
    df['day_change_pct'] = df['day_change_pct'].astype(float)
    
    return df

def train_enhanced_model():
    # Load Data
    data_path = Path('research/ml_position_sizing/data/labeled_regimes_v2.csv')
    df = pd.read_csv(data_path)
    
    print(f"Loaded {len(df)} samples from {data_path}")
    
    # Preprocess
    df = feature_engineering(df)
    
    # Define features
    feature_cols = [
        'time_sin', 'time_cos', 
        'volume_ratio', 
        'day_change_pct', 
        'atr_percentile',
        'vol_volatility_ratio'
    ]
    
    # Target
    # Map ADD_ALLOWED/ADD_NEUTRAL -> 1, NO_ADD -> 0?
    # Or strict: ADD_ALLOWED -> 1, others -> 0?
    # Expert critique says "Neutral is a graveyard". 
    # Let's target strictly ADD_ALLOWED as 1 (Prime Setup) vs Rest.
    # But wait, original model had 3 classes. 
    # Expert suggested "Is this a Bear Trap? (Binary: Yes/No)" then Conviction.
    # Let's try Binary: 1 if regime_label_v2 == 'ADD_ALLOWED', else 0.
    
    df['target'] = (df['regime_label_v2'] == 'ADD_ALLOWED').astype(int)
    
    X = df[feature_cols]
    y = df['target']
    
    print(f"\nFeatures: {feature_cols}")
    print(f"Target Distribution:\n{y.value_counts()}")
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Base XGBoost
    xgb_clf = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        objective='binary:logistic',
        eval_metric='logloss',
        use_label_encoder=False,
        random_state=42,
        n_jobs=-1
    )
    
    # Calibrated Classifier
    # 'isotonic' usually better with enough data, 'sigmoid' for smaller datasets.
    # With ~2000 samples, sigmoid might be safer, but let's try isotonic.
    calibrated_clf = CalibratedClassifierCV(xgb_clf, method='isotonic', cv=5)
    
    print("\nTraining Calibrated XGBoost...")
    calibrated_clf.fit(X_train, y_train)
    
    # Evaluate
    y_prob = calibrated_clf.predict_proba(X_test)[:, 1]
    y_pred = (y_prob > 0.5).astype(int)
    
    auc = roc_auc_score(y_test, y_prob)
    loss = log_loss(y_test, y_prob)
    
    print(f"\nTest AUC: {auc:.4f}")
    print(f"Test LogLoss: {loss:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    # Feature Importance (Extract from base estimator of first fold if possible, 
    # but CalibratedClassifierCV makes this tricky. We fit a standalone XGB for viz.)
    xgb_viz = xgb.XGBClassifier(
        n_estimators=100, max_depth=4, learning_rate=0.1, 
        subsample=0.8, colsample_bytree=0.8, random_state=42
    )
    xgb_viz.fit(X_train, y_train)
    importances = pd.Series(xgb_viz.feature_importances_, index=feature_cols).sort_values(ascending=False)
    print("\nFeature Importances (Proxy):")
    print(importances)
    
    # Save Model
    output_path = Path('research/ml_position_sizing/models/bear_trap_enhanced_xgb.pkl')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save the calibrated wrapper
    with open(output_path, 'wb') as f:
        pickle.dump({
            'model': calibrated_clf,
            'features': feature_cols,
            'description': 'Calibrated XGBoost (Isotonic) with continuous features'
        }, f)
        
    print(f"\nSaved model to {output_path}")

if __name__ == "__main__":
    train_enhanced_model()
