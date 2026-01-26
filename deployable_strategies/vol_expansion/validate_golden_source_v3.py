"""
Golden Source Validation V3 - CLUSTER ASSIGNMENT

CRITICAL FINDING: The research used CLUSTER MEMBERSHIP to identify signals,
NOT a Boolean AND of all thresholds.

The 'signal_frequency' in research = proportion of BALANCED SAMPLE in cluster,
not proportion of all bars passing all Boolean conditions.

This version replicates the EXACT cluster assignment logic.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
import json
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))


class GoldenSourceValidatorV3:
    """
    Golden source validator using cluster assignment (matches research exactly).
    """
    
    def __init__(self):
        results_path = project_root / "research" / "blind_backwards_analysis" / "outputs" / "FINAL_STRATEGY_RESULTS.json"
        with open(results_path) as f:
            self.research_thresholds = json.load(f)
        print("✓ Loaded research thresholds")
        
    def load_golden_source(self, symbol: str) -> pd.DataFrame:
        """Load pre-computed research features."""
        features_path = project_root / "research" / "blind_backwards_analysis" / "outputs" / f"{symbol}_features.parquet"
        df = pd.read_parquet(features_path)
        print(f"✓ Loaded golden source for {symbol}: {len(df):,} bars")
        return df
    
    def load_price_data(self, symbol: str) -> pd.DataFrame:
        """Load raw OHLCV price data."""
        data_path = project_root / "data" / "cache" / "equities"
        files = sorted(data_path.glob(f"{symbol}_1min_202*.parquet"), 
                      key=lambda x: x.stat().st_size, reverse=True)
        df = pd.read_parquet(files[0])
        print(f"✓ Loaded price data: {len(df):,} bars")
        return df
    
    def replicate_research_clustering(self, features: pd.DataFrame, symbol: str) -> tuple:
        """
        Replicate EXACT research clustering logic from final_analysis.py.
        
        Steps:
        1. Sample 30k wins + 30k non-wins (balanced)
        2. Fit StandardScaler on this sample
        3. Fit KMeans with k=6 on scaled sample
        4. Identify best cluster
        5. Apply to ALL data
        """
        print(f"\n📊 Replicating research clustering for {symbol}...")
        
        # Get feature columns (same as research)
        feat_cols = [c for c in features.columns if '_mean' in c][:15]
        print(f"  Using {len(feat_cols)} features")
        
        # Load strict events (same as research)
        strict_path = project_root / "research" / "blind_backwards_analysis" / "outputs" / f"{symbol}_winning_events_strict.parquet"
        strict = pd.read_parquet(strict_path)
        strict_ts = pd.to_datetime(strict['timestamp'])
        features['is_strict_win'] = features.index.isin(strict_ts[strict['is_winning']])
        
        # Sample data (exactly like research)
        np.random.seed(42)
        wins_df = features[features['is_strict_win']].dropna(subset=feat_cols)
        non_wins_df = features[~features['is_strict_win']].dropna(subset=feat_cols)
        
        n_sample = min(30000, len(wins_df), len(non_wins_df))
        wins = wins_df.sample(n=n_sample)
        non_wins = non_wins_df.sample(n=n_sample)
        print(f"  Sampled {n_sample:,} wins + {n_sample:,} non-wins")
        
        X_win = wins[feat_cols].values
        X_non = non_wins[feat_cols].values
        
        # Combine and scale
        X_all = np.vstack([X_win, X_non])
        labels = np.array(['win']*len(X_win) + ['non']*len(X_non))
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_all)
        
        # Cluster (same as research: k=6)
        kmeans = KMeans(n_clusters=6, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(X_scaled)
        
        # Find best cluster (highest lift)
        best_cluster = None
        best_lift = 0
        
        print(f"\n  Cluster Analysis:")
        for c in range(6):
            mask = clusters == c
            wins_in = (labels[mask] == 'win').sum()
            total_in = mask.sum()
            win_rate_c = wins_in / total_in if total_in > 0 else 0
            
            prev_win = (clusters[labels=='win'] == c).mean()
            prev_non = (clusters[labels=='non'] == c).mean()
            lift = prev_win / (prev_non + 0.001)
            
            print(f"    Cluster {c}: WinRate={win_rate_c:.1%}, Lift={lift:.2f}x, Size={total_in}")
            
            if lift > best_lift:
                best_lift = lift
                best_cluster = c
                best_win_rate = win_rate_c
        
        print(f"\n  ✓ Best cluster: {best_cluster} (Lift: {best_lift:.2f}x, WinRate: {best_win_rate:.1%})")
        
        return scaler, kmeans, feat_cols, best_cluster, best_win_rate
    
    def assign_clusters_to_full_data(self, features: pd.DataFrame, prices: pd.DataFrame,
                                      scaler, kmeans, feat_cols, best_cluster) -> tuple:
        """
        Assign cluster labels to FULL dataset and identify signals.
        """
        print(f"\n📈 Assigning clusters to full dataset...")
        
        # Merge with prices
        merged = features.join(prices[['open', 'high', 'low', 'close', 'volume']], how='inner')
        
        # Get valid rows
        X_full = merged[feat_cols].fillna(0).values
        valid_mask = ~np.isnan(X_full).any(axis=1)
        X_valid = X_full[valid_mask]
        
        # Scale using same scaler (fitted on sample)
        X_scaled = scaler.transform(X_valid)
        
        # Predict clusters
        cluster_labels = kmeans.predict(X_scaled)
        
        # Create signal mask (bars in best cluster)
        signal_mask = np.zeros(len(merged), dtype=bool)
        signal_mask[valid_mask] = (cluster_labels == best_cluster)
        
        signal_count = signal_mask.sum()
        signal_freq = signal_count / len(merged)
        
        print(f"  Signals in best cluster: {signal_count:,} ({signal_freq:.1%})")
        
        # Add cluster labels to merged
        merged_valid = merged.loc[valid_mask].copy()
        merged_valid['cluster'] = cluster_labels
        merged_valid['signal'] = (cluster_labels == best_cluster)
        
        return merged_valid
    
    def run_backtest(self, symbol: str, merged: pd.DataFrame) -> list:
        """Run backtest using cluster membership as signal."""
        print(f"\n{'='*70}")
        print(f"GOLDEN SOURCE BACKTEST V3 (CLUSTER): {symbol}")
        print(f"{'='*70}")
        
        # Calculate ATR
        tr1 = merged['high'] - merged['low']
        tr2 = (merged['high'] - merged['close'].shift(1)).abs()
        tr3 = (merged['low'] - merged['close'].shift(1)).abs()
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr_series = true_range.rolling(20).mean()
        
        # Filter to valid bars
        valid_mask = ~atr_series.isna()
        merged = merged.loc[valid_mask].copy()
        atr_series = atr_series.loc[valid_mask]
        print(f"Bars after ATR warmup: {len(merged):,}")
        
        # Count signals
        signal_count = merged['signal'].sum()
        signal_freq = signal_count / len(merged)
        expected_freq = self.research_thresholds[symbol]['signal_frequency']
        print(f"Signal frequency: {signal_freq:.1%} (Research: {expected_freq:.1%})")
        
        # Run backtest
        position = None
        trades = []
        signals = 0
        
        target_mult = 2.5
        stop_mult = 1.25
        max_hold_bars = 30
        
        price_array = merged[['open', 'high', 'low', 'close']].values
        atr_array = atr_series.values
        signal_array = merged['signal'].values
        index_array = merged.index
        
        for idx in range(len(merged)):
            if position is None:
                # Entry: bar is in winning cluster
                if signal_array[idx]:
                    signals += 1
                    atr = atr_array[idx]
                    close_price = price_array[idx, 3]
                    
                    position = {
                        'entry_idx': idx,
                        'entry_time': index_array[idx],
                        'entry_price': close_price,
                        'target': close_price + (target_mult * atr),
                        'stop': close_price - (stop_mult * atr),
                        'atr': atr,
                        'highest': close_price
                    }
            else:
                # Manage position
                high = price_array[idx, 1]
                low = price_array[idx, 2]
                close = price_array[idx, 3]
                
                if high > position['highest']:
                    position['highest'] = high
                
                exit_signal = False
                exit_reason = None
                exit_price = None
                
                if low <= position['stop']:
                    exit_signal = True
                    exit_reason = "STOP_LOSS"
                    exit_price = position['stop']
                elif high >= position['target']:
                    exit_signal = True
                    exit_reason = "TARGET_HIT"
                    exit_price = position['target']
                elif idx - position['entry_idx'] >= max_hold_bars:
                    exit_signal = True
                    exit_reason = "TIME_STOP"
                    exit_price = close
                
                if exit_signal:
                    pnl_dollars = exit_price - position['entry_price']
                    risk = position['entry_price'] - position['stop']
                    pnl_r = pnl_dollars / risk if risk > 0 else 0
                    
                    trades.append({
                        'entry_time': position['entry_time'],
                        'exit_time': index_array[idx],
                        'entry_price': position['entry_price'],
                        'exit_price': exit_price,
                        'pnl_r': pnl_r,
                        'is_win': pnl_dollars > 0,
                        'exit_reason': exit_reason
                    })
                    position = None
        
        # Close remaining
        if position is not None:
            close = price_array[-1, 3]
            pnl_dollars = close - position['entry_price']
            risk = position['entry_price'] - position['stop']
            pnl_r = pnl_dollars / risk if risk > 0 else 0
            trades.append({
                'entry_time': position['entry_time'],
                'exit_time': index_array[-1],
                'entry_price': position['entry_price'],
                'exit_price': close,
                'pnl_r': pnl_r,
                'is_win': pnl_dollars > 0,
                'exit_reason': "END_OF_DATA"
            })
        
        return trades
    
    def analyze_results(self, trades: list, symbol: str, cluster_win_rate: float):
        """Analyze results comparing to cluster win rate."""
        if not trades:
            print(f"\n⚠️ No trades for {symbol}")
            return None
        
        df_trades = pd.DataFrame(trades)
        
        total_trades = len(df_trades)
        wins = df_trades['is_win'].sum()
        hit_rate = wins / total_trades
        
        avg_win = df_trades[df_trades['is_win']]['pnl_r'].mean() if wins > 0 else 0
        avg_loss = df_trades[~df_trades['is_win']]['pnl_r'].mean() if (total_trades - wins) > 0 else 0
        expectancy = (hit_rate * avg_win) + ((1 - hit_rate) * avg_loss)
        
        print(f"\n{'='*70}")
        print(f"RESULTS V3 (CLUSTER): {symbol}")
        print(f"{'='*70}")
        print(f"Total Trades:     {total_trades}")
        print(f"Wins:             {wins} ({hit_rate:.1%})")
        print(f"Avg Win:          {avg_win:.3f}R")
        print(f"Avg Loss:         {avg_loss:.3f}R")
        print(f"Expectancy:       {expectancy:.3f}R")
        
        # Compare to cluster win rate (more appropriate comparison)
        expected_hr = cluster_win_rate
        hr_diff = (hit_rate - expected_hr) * 100
        
        print(f"\n{'Cluster Comparison':-^70}")
        print(f"Cluster Win Rate:  {expected_hr:.1%}")
        print(f"Backtest Hit Rate: {hit_rate:.1%} ({hr_diff:+.1f}pp)")
        
        # Exit breakdown
        print(f"\n{'Exit Reasons':-^70}")
        exit_counts = df_trades['exit_reason'].value_counts()
        for reason, count in exit_counts.items():
            pct = (count / total_trades) * 100
            reason_trades = df_trades[df_trades['exit_reason'] == reason]
            reason_hr = reason_trades['is_win'].mean()
            print(f"{reason:15s}: {count:5d} ({pct:5.1f}%) | Win Rate: {reason_hr:.1%}")
        
        # Verdict
        print(f"\n{'DIAGNOSIS':-^70}")
        if abs(hr_diff) < 10:
            print("✅ CLUSTER MEMBERSHIP VALIDATES!")
            print("   Exit logic is working correctly")
            print("   → The issue was using Boolean AND instead of cluster assignment")
        else:
            print("❌ Still significant gap")
            print("   → Exit logic may need adjustment")
        
        return {'hit_rate': hit_rate, 'expected': expected_hr, 'diff_pp': hr_diff}


def main():
    print("="*70)
    print("GOLDEN SOURCE VALIDATION V3 (CLUSTER ASSIGNMENT)")
    print("FIX: Use cluster membership, not Boolean AND of thresholds")
    print("="*70)
    
    validator = GoldenSourceValidatorV3()
    
    for symbol in ['SPY']:
        try:
            features = validator.load_golden_source(symbol)
            prices = validator.load_price_data(symbol)
            
            # Replicate research clustering
            scaler, kmeans, feat_cols, best_cluster, cluster_win_rate = \
                validator.replicate_research_clustering(features, symbol)
            
            # Assign clusters to full data
            merged = validator.assign_clusters_to_full_data(
                features, prices, scaler, kmeans, feat_cols, best_cluster
            )
            
            # Run backtest
            trades = validator.run_backtest(symbol, merged)
            
            # Analyze
            validator.analyze_results(trades, symbol, cluster_win_rate)
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
