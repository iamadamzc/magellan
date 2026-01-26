"""
Final Cluster Analysis - Stricter Event Labels
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import json

output_path = Path(__file__).parent / "outputs"

results_summary = {}

for symbol in ['SPY', 'QQQ', 'IWM']:
    print(f'\n{"="*60}')
    print(f'ANALYSIS: {symbol}')
    print("="*60)
    
    # Load features and strict events
    features = pd.read_parquet(output_path / f'{symbol}_features.parquet')
    strict = pd.read_parquet(output_path / f'{symbol}_winning_events_strict.parquet')
    
    # Use strict labels
    strict_ts = pd.to_datetime(strict['timestamp'])
    features['is_strict_win'] = features.index.isin(strict_ts[strict['is_winning']])
    
    win_rate = features['is_strict_win'].mean()
    print(f'Strict win rate: {win_rate:.1%}')
    
    # Get feature columns  
    feat_cols = [c for c in features.columns if '_mean' in c][:15]
    print(f'Using {len(feat_cols)} features')
    
    # Sample data
    np.random.seed(42)
    wins_df = features[features['is_strict_win']].dropna(subset=feat_cols)
    non_wins_df = features[~features['is_strict_win']].dropna(subset=feat_cols)
    
    n_sample = min(30000, len(wins_df), len(non_wins_df))
    wins = wins_df.sample(n=n_sample)
    non_wins = non_wins_df.sample(n=n_sample)
    
    X_win = wins[feat_cols].values
    X_non = non_wins[feat_cols].values
    
    # Cluster
    X_all = np.vstack([X_win, X_non])
    labels = np.array(['win']*len(X_win) + ['non']*len(X_non))
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_all)
    
    kmeans = KMeans(n_clusters=6, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(X_scaled)
    
    print(f'\nCluster Analysis:')
    print('-'*60)
    
    best_clusters = []
    for c in range(6):
        mask = clusters == c
        wins_in = (labels[mask] == 'win').sum()
        total_in = mask.sum()
        win_rate_c = wins_in / total_in if total_in > 0 else 0
        
        prev_win = (clusters[labels=='win'] == c).mean()
        prev_non = (clusters[labels=='non'] == c).mean()
        lift = prev_win / (prev_non + 0.001)
        
        best_clusters.append({
            'cluster': c,
            'win_rate': win_rate_c,
            'prev_win': prev_win,
            'prev_non': prev_non,
            'lift': lift,
            'total': total_in
        })
        
        print(f"  Cluster {c}: WinRate={win_rate_c:.1%}, Lift={lift:.2f}x, Size={total_in}")
    
    # Sort by lift
    best_clusters = sorted(best_clusters, key=lambda x: x['lift'], reverse=True)
    
    # Best and worst clusters for strategy
    best = best_clusters[0]
    worst = best_clusters[-1]
    
    print(f'\n*** HIDDEN STATE DETECTED: Cluster {best["cluster"]} ***')
    print(f'    Win Rate: {best["win_rate"]:.1%}')
    print(f'    Lift: {best["lift"]:.2f}x')
    
    # Get centroid
    centroid = kmeans.cluster_centers_[best['cluster']]
    centroid_raw = scaler.inverse_transform([centroid])[0]
    
    print(f'\nDefining Feature Profile:')
    feature_profile = []
    for feat, val in sorted(zip(feat_cols, centroid_raw), key=lambda x: abs(x[1]), reverse=True)[:5]:
        direction = '>' if val > 0 else '<'
        print(f'  {feat} {direction} {abs(val):.4f}')
        feature_profile.append({'feature': feat, 'threshold': val, 'direction': direction})
    
    # Calculate edge metrics
    edge_over_baseline = best['win_rate'] / win_rate - 1
    hit_rate = best['win_rate']
    
    # Assume 2:1 R:R based on our target definition
    avg_win = 1.0
    avg_loss = 0.5
    expectancy = (hit_rate * avg_win) - ((1 - hit_rate) * avg_loss)
    
    print(f'\nEDGE METRICS:')
    print(f'  Hit Rate: {hit_rate:.1%}')
    print(f'  Edge Ratio: {avg_win/avg_loss:.2f} (2:1 R:R)')
    print(f'  Expectancy: {expectancy:.3f}R per trade')
    print(f'  Signal Frequency: {best["total"]} / {len(clusters)} ({best["total"]/len(clusters):.1%})')
    
    results_summary[symbol] = {
        'hit_rate': hit_rate,
        'lift': best['lift'],
        'edge_ratio': avg_win / avg_loss,
        'expectancy': expectancy,
        'signal_frequency': best['total'] / len(clusters),
        'feature_profile': feature_profile
    }

# Final summary
print('\n' + '='*70)
print('FINAL STRATEGY SUMMARY')
print('='*70)

for symbol, res in results_summary.items():
    print(f'\n{symbol}:')
    print(f'  Hit Rate: {res["hit_rate"]:.1%}')
    print(f'  Edge Ratio: {res["edge_ratio"]:.2f}')
    print(f'  Expectancy: {res["expectancy"]:.3f}R per trade')
    print(f'  Lift vs Baseline: {res["lift"]:.2f}x')

# Save final results
with open(output_path / 'FINAL_STRATEGY_RESULTS.json', 'w') as f:
    json.dump(results_summary, f, indent=2, default=str)

print(f'\n✓ Results saved to outputs/FINAL_STRATEGY_RESULTS.json')
