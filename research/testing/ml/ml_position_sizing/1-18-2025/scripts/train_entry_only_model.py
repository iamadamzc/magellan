"""
Retrain ML model with ONLY entry-time features (no outcome data)
"""
import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
import pickle
from pathlib import Path

df = pd.read_csv('research/ml_position_sizing/data/labeled_regimes_v2.csv')

print('='*80)
print('RETRAINING ML MODEL - ENTRY-TIME FEATURES ONLY')
print('='*80)

# Calculate ONLY entry-time features (no outcome data!)
df['entry_datetime'] = pd.to_datetime(df['entry_date'])
df['entry_hour'] = df['entry_datetime'].dt.hour
df['entry_day_of_week'] = df['entry_datetime'].dt.dayofweek

# Feature 1: Time of day (late = better)
df['time_score'] = (df['entry_hour'] >= 15).astype(int)

# Feature 2: Day of week (avoid Monday/Friday?)
df['is_midweek'] = ((df['entry_day_of_week'] >= 1) & (df['entry_day_of_week'] <= 3)).astype(int)

# Feature 3: Volume (high volume = better)
df['high_volume'] = (df['volume_ratio'] > 2.0).astype(int)

# Feature 4: Day change magnitude (bigger drop = better setup?)
df['big_drop'] = (df['day_change_pct'] < -20).astype(int)

# Feature 5: ATR percentile (from original features if available)
if 'atr_percentile' in df.columns:
    df['high_volatility'] = (df['atr_percentile'] > 0.7).astype(int)
else:
    df['high_volatility'] = 0

feature_cols = ['time_score', 'is_midweek', 'high_volume', 'big_drop', 'high_volatility']

print(f'\nFeatures (ENTRY-TIME ONLY): {feature_cols}')
print('NO outcome data (max_profit, bars_held) used!')

X = df[feature_cols].fillna(0)
y = df['regime_label_v2']

print(f'\nFeature matrix shape: {X.shape}')
print(f'\nLabel distribution:')
print(y.value_counts())

# Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# Train
print('\nTraining DecisionTreeClassifier...')
model = DecisionTreeClassifier(
    max_depth=4,
    min_samples_split=100,
    min_samples_leaf=50,
    random_state=42
)

model.fit(X_train, y_train)

# Evaluate
train_acc = model.score(X_train, y_train)
test_acc = model.score(X_test, y_test)

print(f'\nTrain accuracy: {train_acc:.1%}')
print(f'Test accuracy: {test_acc:.1%}')

# Test set performance
y_pred = model.predict(X_test)
test_df = df.iloc[X_test.index].copy()
test_df['predicted'] = y_pred

print('\nTest set performance by predicted regime:')
for regime in ['ADD_ALLOWED', 'ADD_NEUTRAL', 'NO_ADD']:
    subset = test_df[test_df['predicted'] == regime]
    if len(subset) > 0:
        avg_r = subset['r_multiple'].mean()
        wr = (subset['r_multiple'] > 0).mean() * 100
        print(f'  {regime}: {len(subset)} trades, WR={wr:.0f}%, Avg R={avg_r:.2f}')

# Feature importance
print('\nFeature importance:')
for feat, imp in zip(feature_cols, model.feature_importances_):
    print(f'  {feat}: {imp:.3f}')

# Save model
model_path = Path('research/ml_position_sizing/models/bear_trap_entry_only_classifier.pkl')
model_path.parent.mkdir(parents=True, exist_ok=True)

with open(model_path, 'wb') as f:
    pickle.dump({
        'model': model,
        'features': feature_cols,
    }, f)

print(f'\n✓ Model saved to: {model_path}')
print('\n' + '='*80)
print('ENTRY-TIME MODEL TRAINING COMPLETE')
print('='*80)
