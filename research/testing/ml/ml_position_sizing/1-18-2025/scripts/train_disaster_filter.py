"""
Train Disaster-Prediction Model for Bear Trap Strategy.

INVERSION APPROACH:
Instead of predicting winners, predict DISASTERS (R < -0.5).
Rationale: Baseline has edge. We just need to avoid catastrophic losses.

Target: DISASTER = 1 if r_multiple < -0.5, else 0
Usage: Reject trade if prob(disaster) > threshold (e.g., 0.7)
"""
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import roc_auc_score, log_loss, classification_report, confusion_matrix
import pickle
from pathlib import Path

def calculate_cyclical_features(df, col_hour, col_minute):
    """Encodes time as cyclical sin/cos features."""
    minutes_since_midnight = df[col_hour] * 60 + df[col_minute]
    day_minutes = 1440
    df['time_sin'] = np.sin(2 * np.pi * minutes_since_midnight / day_minutes)
    df['time_cos'] = np.cos(2 * np.pi * minutes_since_midnight / day_minutes)
    return df

def feature_engineering(df):
    """Creates continuous features matching simulation."""
    df = df.copy()
    
    # Cyclical Time
    df = calculate_cyclical_features(df, 'entry_hour', 'entry_minute')
    
    # Time-of-Day flag (NEW: Based on user insight)
    df['is_late_day'] = (df['entry_hour'] >= 14).astype(int)  # After 2pm
    
    # Volatility/Volume features
    df['volume_ratio'] = df['volume_ratio'].fillna(1.0)
    df['atr_percentile'] = df['atr_percentile'].fillna(0.5)
    df['vol_volatility_ratio'] = df['atr_percentile'] / (df['volume_ratio'] + 0.001)
    
    # Raw continuous
    df['day_change_pct'] = df['day_change_pct'].astype(float)
    
    return df

def train_disaster_model():
    # Load Data
    data_path = Path('research/ml_position_sizing/data/labeled_regimes_v2.csv')
    df = pd.read_csv(data_path)
    
    print(f"Loaded {len(df)} samples from {data_path}")
    
    # Feature Engineering
    df = feature_engineering(df)
    
    # INVERTED LABELING: Predict DISASTERS
    # Disaster = trades that lost >= 0.5R (catastrophic)
    df['target_disaster'] = (df['r_multiple'] < -0.5).astype(int)
    
    print(f"\nDisaster Distribution:")
    print(df['target_disaster'].value_counts())
    disaster_rate = df['target_disaster'].sum() / len(df) * 100
    print(f"Disaster Rate: {disaster_rate:.1f}%")
    
    # Analyze disaster characteristics
    disasters = df[df['target_disaster'] == 1]
    safe_trades = df[df['target_disaster'] == 0]
    
    print(f"\n{'='*60}")
    print("DISASTER PROFILE ANALYSIS")
    print(f"{'='*60}")
    print(f"\nDisasters (R < -0.5): {len(disasters)} trades")
    print(f"  Avg ATR%: {disasters['atr_percentile'].mean():.2f}")
    print(f"  Avg VolRat: {disasters['volume_ratio'].mean():.2f}")
    print(f"  Late Day %: {disasters['is_late_day'].mean()*100:.1f}%")
    print(f"  Avg R: {disasters['r_multiple'].mean():.2f}")
    
    print(f"\nSafe Trades (R >= -0.5): {len(safe_trades)} trades")
    print(f"  Avg ATR%: {safe_trades['atr_percentile'].mean():.2f}")
    print(f"  Avg VolRat: {safe_trades['volume_ratio'].mean():.2f}")
    print(f"  Late Day %: {safe_trades['is_late_day'].mean()*100:.1f}%")
    print(f"  Avg R: {safe_trades['r_multiple'].mean():.2f}")
    
    # Define Features
    feature_cols = [
        'time_sin', 'time_cos',
        'is_late_day',  # NEW
        'volume_ratio',
        'day_change_pct',
        'atr_percentile',
        'vol_volatility_ratio'
    ]
    
    X = df[feature_cols]
    y = df['target_disaster']
    
    print(f"\nFeatures: {feature_cols}")
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # XGBoost for Disaster Prediction
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
        scale_pos_weight=(len(y_train) - y_train.sum()) / y_train.sum(),  # Handle imbalance
        n_jobs=-1
    )
    
    # Calibrated Classifier
    calibrated_clf = CalibratedClassifierCV(xgb_clf, method='isotonic', cv=5)
    
    print("\nTraining Disaster-Prediction Model...")
    calibrated_clf.fit(X_train, y_train)
    
    # Evaluate
    y_prob = calibrated_clf.predict_proba(X_test)[:, 1]
    y_pred = (y_prob > 0.5).astype(int)
    
    auc = roc_auc_score(y_test, y_prob)
    loss = log_loss(y_test, y_prob)
    
    print(f"\n{'='*60}")
    print("MODEL PERFORMANCE")
    print(f"{'='*60}")
    print(f"Test AUC: {auc:.4f}")
    print(f"Test LogLoss: {loss:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['Safe', 'Disaster']))
    
    print("\nConfusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(f"               Predicted Safe  Predicted Disaster")
    print(f"Actual Safe    {cm[0,0]:>14}  {cm[0,1]:>18}")
    print(f"Actual Disaster{cm[1,0]:>14}  {cm[1,1]:>18}")
    
    # Critical Metric: Disaster Recall (catching real disasters)
    disaster_recall = cm[1,1] / (cm[1,0] + cm[1,1])
    disaster_precision = cm[1,1] / (cm[0,1] + cm[1,1]) if (cm[0,1] + cm[1,1]) > 0 else 0
    
    print(f"\n🎯 DISASTER DETECTION:")
    print(f"   Recall: {disaster_recall*100:.1f}% (caught {disaster_recall*100:.1f}% of disasters)")
    print(f"   Precision: {disaster_precision*100:.1f}% (of flagged trades, {disaster_precision*100:.1f}% were disasters)")
    
    # Feature Importance
    xgb_viz = xgb.XGBClassifier(
        n_estimators=100, max_depth=4, learning_rate=0.1,
        subsample=0.8, colsample_bytree=0.8, random_state=42
    )
    xgb_viz.fit(X_train, y_train)
    importances = pd.Series(xgb_viz.feature_importances_, index=feature_cols).sort_values(ascending=False)
    print("\nFeature Importances:")
    print(importances)
    
    # Save Model
    output_path = Path('research/ml_position_sizing/models/bear_trap_disaster_filter.pkl')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'wb') as f:
        pickle.dump({
            'model': calibrated_clf,
            'features': feature_cols,
            'description': 'Disaster Filter (Inverted): Predicts R < -0.5',
            'disaster_recall': disaster_recall,
            'disaster_precision': disaster_precision,
            'auc': auc
        }, f)
    
    print(f"\nSaved model to {output_path}")
    
    # Probability Distribution Analysis
    print(f"\n{'='*60}")
    print("PROBABILITY DISTRIBUTION")
    print(f"{'='*60}")
    
    # Bucket by probability
    test_df = pd.DataFrame({
        'prob_disaster': y_prob,
        'actual_disaster': y_test,
        'r_multiple': df.loc[X_test.index, 'r_multiple']
    })
    
    test_df['prob_bucket'] = pd.qcut(test_df['prob_disaster'], q=5, labels=['Very Low', 'Low', 'Med', 'High', 'Very High'], duplicates='drop')
    
    print("\nBy Disaster Probability Bucket:")
    for bucket in test_df['prob_bucket'].unique():
        subset = test_df[test_df['prob_bucket'] == bucket]
        disaster_pct = subset['actual_disaster'].mean() * 100
        avg_r = subset['r_multiple'].mean()
        print(f"  {bucket:>10}: {len(subset):>4} trades | {disaster_pct:>5.1f}% disasters | Avg R: {avg_r:>+6.2f}")

if __name__ == "__main__":
    train_disaster_model()
