"""
Phase 3: Cluster Analysis - Hidden State Discovery

Uses unsupervised clustering to identify mathematical states
that precede winning events with high frequency.

Target: Find clusters appearing in >60% of wins, <20% of non-wins
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from scipy import stats
import warnings
warnings.filterwarnings('ignore')


def prepare_clustering_data(
    features_df: pd.DataFrame,
    feature_cols: list,
    sample_non_wins: int = None
) -> tuple:
    """
    Prepare data for clustering: separate wins and non-wins.
    
    Returns:
    - X_win: Feature matrix for winning events
    - X_non: Feature matrix for non-winning events (sampled)
    - feature_names: List of feature column names
    """
    # Get winning and non-winning samples
    wins = features_df[features_df['is_winning'] == True].copy()
    non_wins = features_df[features_df['is_winning'] == False].copy()
    
    print(f"Winning events: {len(wins):,}")
    print(f"Non-winning bars: {len(non_wins):,}")
    
    # Sample non-wins to balance (default: 3x wins)
    if sample_non_wins is None:
        sample_non_wins = min(len(wins) * 3, len(non_wins))
    
    non_wins_sample = non_wins.sample(n=sample_non_wins, random_state=42)
    print(f"Sampled non-wins: {len(non_wins_sample):,}")
    
    # Extract feature matrices
    X_win = wins[feature_cols].values
    X_non = non_wins_sample[feature_cols].values
    
    # Remove NaN rows
    win_valid = ~np.isnan(X_win).any(axis=1)
    non_valid = ~np.isnan(X_non).any(axis=1)
    
    X_win = X_win[win_valid]
    X_non = X_non[non_valid]
    
    print(f"Valid win samples: {len(X_win):,}")
    print(f"Valid non-win samples: {len(X_non):,}")
    
    return X_win, X_non, feature_cols


def find_optimal_clusters(X: np.ndarray, k_range: range = range(4, 15), max_samples: int = 10000) -> int:
    """Find optimal number of clusters using silhouette score on sampled data."""
    
    # Sample to avoid memory issues with large datasets
    if len(X) > max_samples:
        np.random.seed(42)
        sample_idx = np.random.choice(len(X), max_samples, replace=False)
        X_sample = X[sample_idx]
        print(f"  Using {max_samples:,} samples for cluster optimization")
    else:
        X_sample = X
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_sample)
    
    scores = []
    for k in k_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X_scaled)
        score = silhouette_score(X_scaled, labels)
        scores.append((k, score))
        print(f"  k={k}: silhouette={score:.4f}")
    
    best_k = max(scores, key=lambda x: x[1])[0]
    print(f"\nOptimal k: {best_k}")
    return best_k


def identify_hidden_states(
    X_win: np.ndarray,
    X_non: np.ndarray,
    n_clusters: int = 8,
    min_win_rate: float = 0.6,
    max_non_rate: float = 0.20,
    max_samples: int = 50000
) -> dict:
    """
    Cluster combined data and identify hidden states.
    
    Hidden State criteria:
    - Appears in >60% of winning events
    - Appears in <20% of non-winning events
    """
    # Sample to manageable sizes
    np.random.seed(42)
    if len(X_win) > max_samples:
        win_idx = np.random.choice(len(X_win), max_samples, replace=False)
        X_win_sample = X_win[win_idx]
        print(f"  Sampled {max_samples:,} from {len(X_win):,} wins")
    else:
        X_win_sample = X_win
    
    if len(X_non) > max_samples:
        non_idx = np.random.choice(len(X_non), max_samples, replace=False)
        X_non_sample = X_non[non_idx]
        print(f"  Sampled {max_samples:,} from {len(X_non):,} non-wins")
    else:
        X_non_sample = X_non
    
    # Combine and scale
    X_all = np.vstack([X_win_sample, X_non_sample])
    labels = np.array(['win'] * len(X_win_sample) + ['non'] * len(X_non_sample))
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_all)
    
    # Cluster
    print(f"\nClustering with k={n_clusters}...")
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(X_scaled)
    
    # Analyze each cluster
    hidden_states = []
    cluster_stats = []
    
    print("\nCluster Analysis:")
    print("-" * 70)
    print(f"{'Cluster':>8} {'Win Count':>10} {'Non Count':>10} {'Win Rate':>10} {'Win Prev':>10} {'Non Prev':>10}")
    print("-" * 70)
    
    for c in range(n_clusters):
        mask = clusters == c
        
        # Counts in this cluster
        wins_in_cluster = (labels[mask] == 'win').sum()
        non_in_cluster = (labels[mask] == 'non').sum()
        total_in_cluster = mask.sum()
        
        # Win rate within cluster
        win_rate = wins_in_cluster / total_in_cluster if total_in_cluster > 0 else 0
        
        # Prevalence in wins vs non-wins
        prevalence_in_wins = (clusters[labels == 'win'] == c).mean()
        prevalence_in_non = (clusters[labels == 'non'] == c).mean()
        
        cluster_stats.append({
            'cluster_id': c,
            'total_count': total_in_cluster,
            'win_count': wins_in_cluster,
            'non_count': non_in_cluster,
            'win_rate': win_rate,
            'prevalence_in_wins': prevalence_in_wins,
            'prevalence_in_non': prevalence_in_non,
            'lift': prevalence_in_wins / (prevalence_in_non + 0.001)
        })
        
        print(f"{c:>8} {wins_in_cluster:>10} {non_in_cluster:>10} {win_rate:>10.2%} {prevalence_in_wins:>10.2%} {prevalence_in_non:>10.2%}")
        
        # Check if this is a hidden state
        if prevalence_in_wins >= min_win_rate or (win_rate > 0.7 and prevalence_in_wins > 0.15):
            hidden_states.append({
                'cluster_id': c,
                'centroid': kmeans.cluster_centers_[c],
                'centroid_unscaled': scaler.inverse_transform([kmeans.cluster_centers_[c]])[0],
                'win_rate': win_rate,
                'prevalence_in_wins': prevalence_in_wins,
                'prevalence_in_non': prevalence_in_non,
                'lift': prevalence_in_wins / (prevalence_in_non + 0.001)
            })
    
    print("-" * 70)
    
    return {
        'hidden_states': hidden_states,
        'cluster_stats': pd.DataFrame(cluster_stats),
        'kmeans': kmeans,
        'scaler': scaler,
        'clusters': clusters,
        'labels': labels
    }


def statistical_significance_test(cluster_stats: pd.DataFrame, n_wins: int, n_non: int) -> pd.DataFrame:
    """
    Test statistical significance of cluster-outcome association.
    Uses chi-square test for independence.
    """
    results = []
    
    for _, row in cluster_stats.iterrows():
        # Build contingency table
        # [in_cluster_wins, in_cluster_non]
        # [not_in_cluster_wins, not_in_cluster_non]
        
        in_cluster_wins = row['win_count']
        in_cluster_non = row['non_count']
        not_in_cluster_wins = n_wins - in_cluster_wins
        not_in_cluster_non = n_non - in_cluster_non
        
        contingency = np.array([
            [in_cluster_wins, in_cluster_non],
            [not_in_cluster_wins, not_in_cluster_non]
        ])
        
        # Chi-square test
        chi2, p_value, dof, expected = stats.chi2_contingency(contingency)
        
        results.append({
            'cluster_id': row['cluster_id'],
            'chi2': chi2,
            'p_value': p_value,
            'significant': p_value < 0.05
        })
    
    return pd.DataFrame(results)


def extract_cluster_characteristics(
    hidden_states: list,
    feature_names: list
) -> pd.DataFrame:
    """Extract the defining characteristics of hidden state clusters."""
    
    if not hidden_states:
        return pd.DataFrame()
    
    characteristics = []
    
    for hs in hidden_states:
        centroid = hs['centroid_unscaled']
        
        # Find top positive and negative features
        feature_values = dict(zip(feature_names, centroid))
        sorted_features = sorted(feature_values.items(), key=lambda x: abs(x[1]), reverse=True)
        
        characteristics.append({
            'cluster_id': hs['cluster_id'],
            'win_rate': hs['win_rate'],
            'prevalence_in_wins': hs['prevalence_in_wins'],
            'lift': hs['lift'],
            'top_features': sorted_features[:5]
        })
    
    return characteristics


def process_symbol(symbol: str, features_path: Path, output_path: Path) -> dict:
    """Run cluster analysis for a single symbol."""
    
    features_file = features_path / f"{symbol}_features.parquet"
    if not features_file.exists():
        print(f"No features file for {symbol}")
        return None
    
    print(f"\n{'='*60}")
    print(f"Cluster Analysis: {symbol}")
    print(f"{'='*60}")
    
    df = pd.read_parquet(features_file)
    print(f"Loaded {len(df):,} rows")
    
    # Select aggregated features for clustering (more stable)
    feature_cols = [c for c in df.columns if '_mean' in c or '_std' in c]
    feature_cols = [c for c in feature_cols if not df[c].isna().all()]
    
    print(f"Using {len(feature_cols)} aggregated features for clustering")
    
    if 'is_winning' not in df.columns or df['is_winning'].sum() == 0:
        print("No winning events found - skipping")
        return None
    
    # Prepare data
    X_win, X_non, feature_names = prepare_clustering_data(df, feature_cols)
    
    if len(X_win) < 100:
        print("Insufficient winning samples for clustering")
        return None
    
    # Find optimal clusters
    print("\nFinding optimal cluster count...")
    X_combined = np.vstack([X_win, X_non[:len(X_win)]])  # Balanced sample for k selection
    optimal_k = find_optimal_clusters(X_combined)
    
    # Identify hidden states
    results = identify_hidden_states(X_win, X_non, n_clusters=optimal_k)
    
    # Statistical significance
    print("\nStatistical Significance Tests:")
    sig_results = statistical_significance_test(
        results['cluster_stats'],
        n_wins=len(X_win),
        n_non=len(X_non)
    )
    print(sig_results.to_string(index=False))
    
    # Extract characteristics
    if results['hidden_states']:
        print(f"\n✓ Found {len(results['hidden_states'])} hidden state(s)")
        chars = extract_cluster_characteristics(results['hidden_states'], feature_names)
        for c in chars:
            print(f"\nCluster {c['cluster_id']} (Win Rate: {c['win_rate']:.1%}, Lift: {c['lift']:.1f}x):")
            for feat, val in c['top_features']:
                print(f"  {feat}: {val:.4f}")
    else:
        print("\n⚠ No clear hidden states found with current thresholds")
    
    # Save results
    results['cluster_stats'].to_csv(output_path / f"{symbol}_cluster_stats.csv", index=False)
    sig_results.to_csv(output_path / f"{symbol}_significance.csv", index=False)
    
    return results


def main():
    """Run Phase 3 cluster analysis."""
    
    output_path = Path(__file__).parent / "outputs"
    output_path.mkdir(exist_ok=True)
    
    symbols = ['SPY', 'QQQ', 'IWM']
    
    print("=" * 60)
    print("PHASE 3: CLUSTER ANALYSIS - HIDDEN STATE DISCOVERY")
    print("=" * 60)
    
    all_results = {}
    
    for symbol in symbols:
        results = process_symbol(symbol, output_path, output_path)
        if results:
            all_results[symbol] = results
    
    print("\n" + "=" * 60)
    print("PHASE 3 COMPLETE")
    print("=" * 60)
    
    return all_results


if __name__ == "__main__":
    main()
