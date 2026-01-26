"""
Train actual ML model for Bear Trap regime classification

Uses sklearn DecisionTreeClassifier trained on the labeled data.
"""
import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
import pickle
from pathlib import Path

# Load labeled data
df = pd.read_csv('research/ml_position_sizing/data/labeled_regimes_v2.csv')

print('='*80)
print('TRAINING ML MODEL FOR BEAR TRAP')
print('='*80)

print(f'\nTotal trades: {len(df)}')
print(f'\nLabel distribution:')
print(df['regime_label_v2'].value_counts())

# Prepare features
# Use the features we calculated during labeling
feature_cols = ['trend_score', 'vol_score', 'volume_score', 'drop_score']

# Check if these columns exist
if not all(col in df.columns for col in feature_cols):
    print('\nFeature columns not found. Using simpler features...')
    
    # Calculate simple features from available data
    df['entry_datetime'] = pd.to_datetime(df['entry_date'])
    df['entry_hour'] = df['entry_datetime'].dt.hour
    
    # Time score: late session (15-24) = 1, else = 0
    df['time_score'] = (df['entry_hour'] >= 15).astype(int)
    
    # Momentum score: fast reclaim = 2, else = 0
    df['momentum_score'] = ((df['max_profit'] / (df.get('bars_held', 30) + 1)) > 0.5).astype(int) * 2
    
    # Volume score: high volume = 1
    df['vol_score'] = (df['volume_ratio'] > 2.0).astype(int)
    
    feature_cols = ['time_score', 'momentum_score', 'vol_score']

X = df[feature_cols].fillna(0)
y = df['regime_label_v2']

print(f'\nFeatures used: {feature_cols}')
print(f'Feature matrix shape: {X.shape}')

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

print(f'\nTrain size: {len(X_train)}')
print(f'Test size: {len(X_test)}')

# Train model
print('\nTraining DecisionTreeClassifier...')
model = DecisionTreeClassifier(
    max_depth=5,
    min_samples_split=50,
    min_samples_leaf=20,
    random_state=42
)

model.fit(X_train, y_train)

# Evaluate
train_acc = model.score(X_train, y_train)
test_acc = model.score(X_test, y_test)

print(f'\nTrain accuracy: {train_acc:.1%}')
print(f'Test accuracy: {test_acc:.1%}')

# Check predictions on test set
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
model_path = Path('research/ml_position_sizing/models/bear_trap_regime_classifier.pkl')
model_path.parent.mkdir(parents=True, exist_ok=True)

with open(model_path, 'wb') as f:
    pickle.dump({
        'model': model,
        'features': feature_cols,
        'label_mapping': {'ADD_ALLOWED': 2, 'ADD_NEUTRAL': 1, 'NO_ADD': 0}
    }, f)

print(f'\n✓ Model saved to: {model_path}')

# Also save feature names for reference
with open(model_path.parent / 'feature_list.txt', 'w') as f:
    f.write('\n'.join(feature_cols))

print('\n' + '='*80)
print('MODEL TRAINING COMPLETE')
print('='*80)
print('\nNext: Use this model in bear_trap_ml_enhanced.py')
