"""
Test 2022 performance with regime filter
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import json
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import warnings
warnings.filterwarnings('ignore')

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Load final configs
with open(project_root / "test" / "vol_expansion" / "FINAL_OPTIMIZED_CONFIGS.json") as f:
    CONFIGS = json.load(f)

# Load regime signatures
with open(project_root / "test" / "vol_expansion" / "regime_signatures.json") as f:
    REGIME_DATA = json.load(f)

SIGNATURES = REGIME_DATA['signatures']


def calculate_atr(df: pd.DataFrame, period: int = 20) -> pd.Series:
    tr1 = df['high'] - df['low']
    tr2 = (df['high'] - df['close'].shift(1)).abs()
    tr3 = (df['low'] - df['close'].shift(1)).abs()
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return true_range.rolling(period).mean()


def build_features(df: pd.DataFrame, lookback: int = 20) -> pd.DataFrame:
    features = pd.DataFrame(index=df.index)
    features['velocity_1'] = df['close'].pct_change(1)
    features['velocity_4'] = df['close'].pct_change(4)
    
    tr = pd.concat([
        df['high'] - df['low'],
        (df['high'] - df['close'].shift(1)).abs(),
        (df['low'] - df['close'].shift(1)).abs()
    ], axis=1).max(axis=1)
    
    atr_5 = tr.rolling(5).mean()
    atr_20 = tr.rolling(20).mean()
    features['volatility_ratio'] = (atr_5 / (atr_20 + 0.0001)).clip(0, 5)
    
    vol_mean = df['volume'].rolling(20).mean()
    vol_std = df['volume'].rolling(20).std()
    features['volume_z'] = ((df['volume'] - vol_mean) / (vol_std + 1)).clip(-5, 5)
    
    pct_change_abs = df['close'].pct_change().abs()
    features['effort_result'] = (features['volume_z'] / (pct_change_abs + 0.0001)).clip(-100, 100)
    
    full_range = df['high'] - df['low']
    body = (df['close'] - df['open']).abs()
    features['range_ratio'] = (full_range / (body + 0.0001)).clip(0, 20)
    
    for col in ['velocity_1', 'volatility_ratio', 'effort_result', 'range_ratio', 'volume_z']:
        features[f'{col}_mean'] = features[col].rolling(lookback).mean()
        features[f'{col}_std'] = features[col].rolling(lookback).std()
    
    return features


def train_model(df_train: pd.DataFrame) -> tuple:
    features = build_features(df_train, lookback=20)
    atr = calculate_atr(df_train)
    
    target_atr = 2.0
    max_dd_atr = 1.0
    max_bars = 8
    
    is_winning = []
    for idx in range(len(df_train) - max_bars):
        entry = df_train['close'].iloc[idx]
        current_atr = atr.iloc[idx]
        
        if pd.isna(current_atr) or current_atr <= 0:
            is_winning.append(False)
            continue
        
        target = entry + target_atr * current_atr
        max_allowed_dd = max_dd_atr * current_atr
        
        winner = False
        max_dd = 0
        
        for j in range(idx + 1, min(idx + max_bars + 1, len(df_train))):
            dd = entry - df_train['low'].iloc[j]
            max_dd = max(max_dd, dd)
            if df_train['high'].iloc[j] >= target and max_dd <= max_allowed_dd:
                winner = True
                break
        is_winning.append(winner)
    
    is_winning.extend([False] * max_bars)
    features['is_winning'] = is_winning
    
    feat_cols = [c for c in features.columns if '_mean' in c or '_std' in c]
    feat_cols = [c for c in feat_cols if not features[c].isna().all()]
    
    wins_df = features[features['is_winning']].dropna(subset=feat_cols)
    non_wins_df = features[~features['is_winning']].dropna(subset=feat_cols)
    
    n_sample = min(5000, len(wins_df), len(non_wins_df))
    np.random.seed(42)
    wins = wins_df.sample(n=n_sample)
    non_wins = non_wins_df.sample(n=n_sample)
    
    X_win = wins[feat_cols].values
    X_non = non_wins[feat_cols].values
    X_all = np.vstack([X_win, X_non])
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_all)
    
    kmeans = KMeans(n_clusters=8, random_state=42, n_init=10)
    kmeans.fit(X_scaled)
    
    return scaler, kmeans, feat_cols


def calculate_regime_features(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate regime characteristics."""
    daily = df.resample('1D').agg({
        'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
    }).dropna()
    
    regime = pd.DataFrame(index=daily.index)
    atr_daily = calculate_atr(daily, period=20)
    regime['volatility'] = atr_daily / daily['close']
    regime['trend'] = daily['close'].rolling(20).apply(
        lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) == 20 else 0
    )
    atr_50 = calculate_atr(daily, period=50)
    regime['atr_expansion'] = atr_daily / (atr_50 + 0.0001)
    regime['volume_trend'] = daily['volume'].rolling(20).mean() / daily['volume'].rolling(50).mean()
    regime['price_range'] = (daily['high'] - daily['low']) / daily['close']
    
    return regime.dropna()


def match_regime(current_features: dict, signature: dict, tolerance: float = 0.3) -> bool:
    matches = 0
    total = 0
    
    for feature, bounds in signature.items():
        if feature not in current_features:
            continue
        
        current_val = current_features[feature]
        min_val = bounds['min']
        max_val = bounds['max']
        
        range_size = max_val - min_val
        min_expanded = min_val - (range_size * tolerance)
        max_expanded = max_val + (range_size * tolerance)
        
        total += 1
        if min_expanded <= current_val <= max_expanded:
            matches += 1
    
    return (matches / total) >= 0.8 if total > 0 else False


def backtest_with_regime_filter(df_test: pd.DataFrame, model: tuple, config: dict) -> dict:
    scaler, kmeans, feat_cols = model
    
    features = build_features(df_test, lookback=20)
    atr = calculate_atr(df_test)
    sma_50 = df_test['close'].rolling(50).mean()
    in_uptrend = df_test['close'] > sma_50
    
    X_full = features[feat_cols].fillna(0).values
    X_scaled = scaler.transform(X_full)
    clusters = kmeans.predict(X_scaled)
    
    # Strategy signals
    signal_mask = pd.Series(clusters == config['cluster'], index=df_test.index)
    if config['trend_filter']:
        signal_mask = signal_mask & in_uptrend
    
    # Regime filter
    regime_features = calculate_regime_features(df_test)
    regime_allowed = {}
    
    for date in regime_features.index:
        current = regime_features.loc[date].to_dict()
        allowed = False
        for window in ['90day', '60day', '30day']:
            if window in SIGNATURES:
                if match_regime(current, SIGNATURES[window]):
                    allowed = True
                    break
        regime_allowed[date] = allowed
    
    # Convert to intraday
    regime_series = pd.Series(regime_allowed)
    regime_series.index = pd.to_datetime(regime_series.index)
    
    # Results trackers
    results_no_filter = {'trades': 0, 'winners': 0, 'balance': 25000}
    results_with_filter = {'trades': 0, 'winners': 0, 'block ed_trades': 0, 'balance': 25000}
    
    position = None
    risk_pct = 0.01
    slippage = 0.02
    
    for idx in range(len(df_test)):
        date = df_test.index[idx].date()
        regime_ok = regime_series.get(pd.Timestamp(date), False)
        
        current_atr = atr.iloc[idx]
        if pd.isna(current_atr):
            continue
        
        if position is None:
            if signal_mask.iloc[idx]:
                # No filter backtest
                results_no_filter['trades'] += 1
                
                # With filter
                if regime_ok:
                    results_with_filter['trades'] += 1
                else:
                    results_with_filter['blocked_trades'] += 1
                    continue  # Skip this trade
                
                risk_dollars = results_with_filter['balance'] * risk_pct
                stop_distance = config['stop_atr'] * current_atr
                shares = int(risk_dollars / stop_distance)
                
                if shares > 0:
                    raw_entry = df_test['close'].iloc[idx]
                    position = {
                        'entry_idx': idx,
                        'raw_entry': raw_entry,
                        'entry_price': raw_entry + slippage/2,
                        'shares': shares,
                        'target': raw_entry + config['target_atr'] * current_atr,
                        'stop': raw_entry - config['stop_atr'] * current_atr,
                    }
        else:
            high = df_test['high'].iloc[idx]
            low = df_test['low'].iloc[idx]
            close = df_test['close'].iloc[idx]
            
            exit_signal = False
            raw_exit = None
            
            if low <= position['stop']:
                exit_signal = True
                raw_exit = position['stop']
            elif high >= position['target']:
                exit_signal = True
                raw_exit = position['target']
            elif idx - position['entry_idx'] >= config['time_stop_bars']:
                exit_signal = True
                raw_exit = close
            
            if exit_signal:
                exit_price = raw_exit - slippage/2
                pnl_net = (exit_price - position['entry_price']) * position['shares']
                
                results_with_filter['balance'] += pnl_net
                if pnl_net > 0:
                    results_with_filter['winners'] += 1
                
                position = None
    
    return {
        'no_filter': results_no_filter,
        'with_filter': results_with_filter
    }


symbol = 'IVV'
print("="*70)
print(f"2022 BACKTEST - {symbol}")
print("="*70)

# Load data
data_path = project_root / "data" / "cache" / "equities"
files = list(data_path.glob(f"{symbol}_1min_*.parquet"))
file = max(files, key=lambda x: x.stat().st_size)
df_1m = pd.read_parquet(file)

df_15m = df_1m.resample('15min').agg({
    'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
}).dropna()
df_15m = df_15m.between_time('09:30', '15:45')

# Train on everything before 2022, test on 2022
df_train = df_15m[df_15m.index < '2022-01-01']
df_test = df_15m[(df_15m.index >= '2022-01-01') & (df_15m.index < '2023-01-01')]

if len(df_train) < 1000 or len(df_test) < 100:
    print("Insufficient data")
    sys.exit(1)

print(f"\nTraining: {df_train.index[0].date()} to {df_train.index[-1].date()}")
print(f"Testing: {df_test.index[0].date()} to {df_test.index[-1].date()}")
print(f"Test bars: {len(df_test)}")

model = train_model(df_train)
config = CONFIGS[symbol]['workhorse']

results = backtest_with_regime_filter(df_test, model, config)

print(f"\n{'='*70}")
print("RESULTS")
print(f"{'='*70}")

nf = results['no_filter']
wf = results['with_filter']

print(f"\nWITHOUT Regime Filter:")
print(f"  Total Signals: {nf['trades']}")

print(f"\nWITH Regime Filter:")
print(f"  Signals Fired: {nf['trades']}")
print(f"  Blocked by Regime: {wf['blocked_trades']}")
print(f"  Trades Taken: {wf['trades']}")
print(f"  Winners: {wf['winners']}")
print(f"  Win Rate: {wf['winners']/wf['trades']:.1%}" if wf['trades'] > 0 else "  Win Rate: N/A")
print(f"  Final Balance: ${wf['balance']:,.0f}")
print(f"  Return: {(wf['balance']/25000-1)*100:.1f}%")

pct_blocked = wf['blocked_trades'] / nf['trades'] * 100 if nf['trades'] > 0 else 0
print(f"\n  Regime Filter Blocked: {pct_blocked:.1f}% of signals")
