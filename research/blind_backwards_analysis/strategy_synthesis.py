"""
Phase 4: Strategy Synthesis - Translate Hidden States to Executable Logic

Converts discovered clusters into:
- Boolean entry/exit rules
- Edge Ratio and Hit Rate calculations
- Confidence intervals for pattern recurrence
- Python pseudocode output
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from scipy import stats
import json
import warnings
warnings.filterwarnings('ignore')


def translate_cluster_to_rules(
    centroid: np.ndarray,
    feature_names: list,
    std_threshold: float = 0.5
) -> dict:
    """
    Translate cluster centroid into Boolean rules.
    
    For each feature, create a rule based on whether the centroid
    value is significantly above or below 0 (standardized).
    """
    rules = []
    
    for i, (feat, val) in enumerate(zip(feature_names, centroid)):
        if abs(val) > std_threshold:
            operator = '>' if val > 0 else '<'
            threshold = val * 0.8  # Conservative threshold
            rules.append({
                'feature': feat,
                'operator': operator,
                'threshold': threshold,
                'centroid_value': val
            })
    
    # Sort by absolute importance
    rules = sorted(rules, key=lambda x: abs(x['centroid_value']), reverse=True)
    
    return rules[:8]  # Top 8 most important rules


def calculate_edge_metrics(
    features_df: pd.DataFrame,
    rules: list,
    scaler: StandardScaler
) -> dict:
    """
    Apply rules to historical data and calculate edge metrics.
    """
    # Get feature columns used in rules
    rule_features = [r['feature'] for r in rules]
    
    # Check which rows meet all conditions
    X = features_df[rule_features].values
    X_valid = ~np.isnan(X).any(axis=1)
    
    # Scale features
    all_feature_cols = [c for c in features_df.columns if '_mean' in c or '_std' in c]
    X_full = features_df[all_feature_cols].fillna(0).values
    X_scaled = scaler.transform(X_full)
    
    # Create feature name to index mapping
    feat_to_idx = {f: i for i, f in enumerate(all_feature_cols)}
    
    # Apply rules
    signals = np.ones(len(features_df), dtype=bool)
    for rule in rules:
        if rule['feature'] not in feat_to_idx:
            continue
        idx = feat_to_idx[rule['feature']]
        if rule['operator'] == '>':
            signals &= X_scaled[:, idx] > rule['threshold']
        else:
            signals &= X_scaled[:, idx] < rule['threshold']
    
    signals &= X_valid
    
    # Calculate metrics
    total_signals = signals.sum()
    
    if 'is_winning' in features_df.columns and total_signals > 0:
        wins = (features_df['is_winning'] & signals).sum()
        hit_rate = wins / total_signals if total_signals > 0 else 0
        
        # Get magnitude data for edge ratio
        if 'magnitude' in features_df.columns:
            win_magnitudes = features_df.loc[signals & features_df['is_winning'], 'magnitude']
            avg_win = win_magnitudes.mean() if len(win_magnitudes) > 0 else 0
            
            # Estimate avg loss (assume 50% of avg win based on stop placement)
            avg_loss = avg_win * 0.5
            
            edge_ratio = avg_win / avg_loss if avg_loss > 0 else 0
        else:
            avg_win = 0
            avg_loss = 0
            edge_ratio = 0
        
        # Expectancy
        expectancy = (hit_rate * avg_win) - ((1 - hit_rate) * avg_loss)
        
        return {
            'total_signals': total_signals,
            'wins': wins,
            'hit_rate': hit_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'edge_ratio': edge_ratio,
            'expectancy': expectancy
        }
    
    return {'total_signals': total_signals, 'hit_rate': 0, 'edge_ratio': 0}


def bootstrap_confidence_interval(
    features_df: pd.DataFrame,
    rules: list,
    scaler: StandardScaler,
    n_iterations: int = 1000,
    confidence: float = 0.95
) -> dict:
    """
    Bootstrap confidence intervals for hit rate and edge ratio.
    """
    hit_rates = []
    edge_ratios = []
    
    n_samples = min(len(features_df), 50000)
    
    for _ in range(n_iterations):
        sample = features_df.sample(n=n_samples, replace=True)
        metrics = calculate_edge_metrics(sample, rules, scaler)
        if metrics['hit_rate'] > 0:
            hit_rates.append(metrics['hit_rate'])
        if metrics['edge_ratio'] > 0:
            edge_ratios.append(metrics['edge_ratio'])
    
    alpha = (1 - confidence) / 2
    
    hr_ci = (
        np.percentile(hit_rates, alpha * 100) if hit_rates else 0,
        np.percentile(hit_rates, (1 - alpha) * 100) if hit_rates else 0
    )
    
    er_ci = (
        np.percentile(edge_ratios, alpha * 100) if edge_ratios else 0,
        np.percentile(edge_ratios, (1 - alpha) * 100) if edge_ratios else 0
    )
    
    return {
        'hit_rate_ci': hr_ci,
        'hit_rate_mean': np.mean(hit_rates) if hit_rates else 0,
        'edge_ratio_ci': er_ci,
        'edge_ratio_mean': np.mean(edge_ratios) if edge_ratios else 0
    }


def generate_python_pseudocode(rules: list, metrics: dict, symbol: str) -> str:
    """Generate executable Python pseudocode for the strategy."""
    
    conditions = []
    for r in rules[:5]:  # Top 5 conditions
        sign = ">" if r['operator'] == '>' else "<"
        conditions.append(f"    {r['feature']} {sign} {r['threshold']:.3f}")
    
    code = f'''"""
AUTO-GENERATED STRATEGY: {symbol} Hidden State Alpha
Generated from blind backwards analysis on 4-year 1-minute data

PERFORMANCE METRICS (Historical):
- Hit Rate: {metrics.get('hit_rate', 0):.1%}
- Edge Ratio: {metrics.get('edge_ratio', 0):.2f}
- Expectancy: ${metrics.get('expectancy', 0):.4f} per trade

CONFIDENCE INTERVALS (95%):
- Hit Rate: [{metrics.get('hit_rate_ci', (0,0))[0]:.1%}, {metrics.get('hit_rate_ci', (0,0))[1]:.1%}]
- Edge Ratio: [{metrics.get('edge_ratio_ci', (0,0))[0]:.2f}, {metrics.get('edge_ratio_ci', (0,0))[1]:.2f}]
"""

def check_entry_conditions(features: dict) -> bool:
    """
    Check if current bar meets Hidden State entry conditions.
    All conditions must be TRUE for entry.
    """
    return all([
{chr(10).join(conditions)}
    ])


def calculate_exit(entry_price: float, atr: float) -> dict:
    """
    Calculate exit parameters based on historical analysis.
    """
    return {{
        'target': entry_price + (1.5 * atr),  # 1.5 ATR target
        'stop': entry_price - (0.75 * atr),   # 0.75 ATR stop (2:1 R:R)
        'max_bars': 60                        # 60-minute max hold
    }}


# BOOLEAN LOGIC SUMMARY:
# Entry = Hidden State conditions met
# Target = 1.5σ move from entry
# Stop = 50% of target (2:1 R:R)
# Time Exit = 60 bars (1 hour)
'''
    
    return code


def process_symbol(
    symbol: str,
    features_path: Path,
    cluster_results: dict,
    output_path: Path
) -> dict:
    """Synthesize strategy for a symbol."""
    
    print(f"\n{'='*60}")
    print(f"Strategy Synthesis: {symbol}")
    print(f"{'='*60}")
    
    # Load features
    features_file = features_path / f"{symbol}_features.parquet"
    if not features_file.exists():
        print(f"No features file for {symbol}")
        return None
    
    df = pd.read_parquet(features_file)
    
    # Get hidden states from cluster analysis
    if not cluster_results or 'hidden_states' not in cluster_results:
        print("No hidden states found for this symbol")
        return None
    
    hidden_states = cluster_results['hidden_states']
    if not hidden_states:
        print("Empty hidden states list")
        return None
    
    scaler = cluster_results['scaler']
    feature_cols = [c for c in df.columns if '_mean' in c or '_std' in c]
    feature_cols = [c for c in feature_cols if not df[c].isna().all()]
    
    # Use the best hidden state (highest lift)
    best_hs = max(hidden_states, key=lambda x: x['lift'])
    print(f"\nUsing Cluster {best_hs['cluster_id']} (Lift: {best_hs['lift']:.2f}x)")
    
    # Translate to rules
    print("\nTranslating to Boolean rules...")
    rules = translate_cluster_to_rules(
        best_hs['centroid'],
        feature_cols,
        std_threshold=0.3
    )
    
    print("\nEntry Conditions:")
    for r in rules[:5]:
        print(f"  IF {r['feature']} {r['operator']} {r['threshold']:.3f}")
    
    # Calculate edge metrics
    print("\nCalculating edge metrics...")
    metrics = calculate_edge_metrics(df, rules, scaler)
    print(f"  Total signals: {metrics['total_signals']:,}")
    print(f"  Hit Rate: {metrics['hit_rate']:.1%}")
    print(f"  Edge Ratio: {metrics['edge_ratio']:.2f}")
    print(f"  Expectancy: ${metrics['expectancy']:.4f}")
    
    # Bootstrap confidence intervals
    print("\nBootstrapping confidence intervals...")
    ci = bootstrap_confidence_interval(df, rules, scaler, n_iterations=500)
    metrics.update(ci)
    print(f"  Hit Rate 95% CI: [{ci['hit_rate_ci'][0]:.1%}, {ci['hit_rate_ci'][1]:.1%}]")
    print(f"  Edge Ratio 95% CI: [{ci['edge_ratio_ci'][0]:.2f}, {ci['edge_ratio_ci'][1]:.2f}]")
    
    # Generate pseudocode
    print("\nGenerating strategy pseudocode...")
    pseudocode = generate_python_pseudocode(rules, metrics, symbol)
    
    # Save outputs
    code_file = output_path / f"{symbol}_strategy.py"
    with open(code_file, 'w') as f:
        f.write(pseudocode)
    print(f"Saved to {code_file}")
    
    # Save metrics
    metrics_file = output_path / f"{symbol}_metrics.json"
    metrics_json = {
        'symbol': symbol,
        'cluster_id': best_hs['cluster_id'],
        'lift': best_hs['lift'],
        'rules': rules,
        'hit_rate': metrics['hit_rate'],
        'edge_ratio': metrics['edge_ratio'],
        'expectancy': metrics['expectancy'],
        'hit_rate_ci': list(metrics['hit_rate_ci']),
        'edge_ratio_ci': list(metrics['edge_ratio_ci']),
        'total_signals': metrics['total_signals']
    }
    with open(metrics_file, 'w') as f:
        json.dump(metrics_json, f, indent=2, default=str)
    
    return {
        'rules': rules,
        'metrics': metrics,
        'pseudocode': pseudocode
    }


def main(cluster_results: dict = None):
    """Run Phase 4 strategy synthesis."""
    
    output_path = Path(__file__).parent / "outputs"
    output_path.mkdir(exist_ok=True)
    
    symbols = ['SPY', 'QQQ', 'IWM']
    
    print("=" * 60)
    print("PHASE 4: STRATEGY SYNTHESIS - EXECUTABLE LOGIC")
    print("=" * 60)
    
    # If no cluster results provided, try to load from previous run
    if cluster_results is None:
        print("\nNote: Run cluster_analysis.py first to generate cluster results")
        return None
    
    all_strategies = {}
    
    for symbol in symbols:
        if symbol in cluster_results:
            strategy = process_symbol(
                symbol, output_path, cluster_results[symbol], output_path
            )
            if strategy:
                all_strategies[symbol] = strategy
    
    # Final summary
    print("\n" + "=" * 60)
    print("STRATEGY SYNTHESIS COMPLETE")
    print("=" * 60)
    
    for symbol, strat in all_strategies.items():
        m = strat['metrics']
        print(f"\n{symbol}:")
        print(f"  Hit Rate: {m['hit_rate']:.1%} [{m['hit_rate_ci'][0]:.1%}, {m['hit_rate_ci'][1]:.1%}]")
        print(f"  Edge Ratio: {m['edge_ratio']:.2f} [{m['edge_ratio_ci'][0]:.2f}, {m['edge_ratio_ci'][1]:.2f}]")
        print(f"  Expectancy: ${m['expectancy']:.4f} per trade")
    
    return all_strategies


if __name__ == "__main__":
    print("Run via run_analysis.py for full pipeline")
