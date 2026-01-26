"""
Golden Source Validation V4 - Exit Optimization Analysis

TASKS:
1. Symmetrical Test: 2.5 ATR stop (1:1 R:R) - Confirm hit rate recovery
2. MAE Forensics: Calculate max drawdown for winning trades to find optimal stop

Author: Magellan Testing Framework
Date: January 25, 2026
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


class ExitOptimizationAnalyzer:
    """
    Analyze exit logic and find optimal stop placement using MAE analysis.
    """
    
    def __init__(self):
        results_path = project_root / "research" / "blind_backwards_analysis" / "outputs" / "FINAL_STRATEGY_RESULTS.json"
        with open(results_path) as f:
            self.research_thresholds = json.load(f)
        print("Loaded research thresholds")
        
    def load_data(self, symbol: str) -> tuple:
        """Load golden source and price data."""
        features_path = project_root / "research" / "blind_backwards_analysis" / "outputs" / f"{symbol}_features.parquet"
        features = pd.read_parquet(features_path)
        print(f"Loaded golden source: {len(features):,} bars")
        
        data_path = project_root / "data" / "cache" / "equities"
        files = sorted(data_path.glob(f"{symbol}_1min_202*.parquet"), 
                      key=lambda x: x.stat().st_size, reverse=True)
        prices = pd.read_parquet(files[0])
        print(f"Loaded price data: {len(prices):,} bars")
        
        return features, prices
    
    def setup_clustering(self, features: pd.DataFrame, symbol: str) -> tuple:
        """Replicate research clustering to identify best cluster."""
        print(f"\nReplicating research clustering for {symbol}...")
        
        feat_cols = [c for c in features.columns if '_mean' in c][:15]
        
        strict_path = project_root / "research" / "blind_backwards_analysis" / "outputs" / f"{symbol}_winning_events_strict.parquet"
        strict = pd.read_parquet(strict_path)
        strict_ts = pd.to_datetime(strict['timestamp'])
        features['is_strict_win'] = features.index.isin(strict_ts[strict['is_winning']])
        
        np.random.seed(42)
        wins_df = features[features['is_strict_win']].dropna(subset=feat_cols)
        non_wins_df = features[~features['is_strict_win']].dropna(subset=feat_cols)
        
        n_sample = min(30000, len(wins_df), len(non_wins_df))
        wins = wins_df.sample(n=n_sample)
        non_wins = non_wins_df.sample(n=n_sample)
        
        X_win = wins[feat_cols].values
        X_non = non_wins[feat_cols].values
        X_all = np.vstack([X_win, X_non])
        labels = np.array(['win']*len(X_win) + ['non']*len(X_non))
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_all)
        
        kmeans = KMeans(n_clusters=6, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(X_scaled)
        
        # Find best cluster
        best_cluster = None
        best_lift = 0
        best_win_rate = 0
        
        for c in range(6):
            mask = clusters == c
            wins_in = (labels[mask] == 'win').sum()
            total_in = mask.sum()
            win_rate_c = wins_in / total_in if total_in > 0 else 0
            prev_win = (clusters[labels=='win'] == c).mean()
            prev_non = (clusters[labels=='non'] == c).mean()
            lift = prev_win / (prev_non + 0.001)
            
            if lift > best_lift:
                best_lift = lift
                best_cluster = c
                best_win_rate = win_rate_c
        
        print(f"Best cluster: {best_cluster} (Win Rate: {best_win_rate:.1%}, Lift: {best_lift:.2f}x)")
        
        return scaler, kmeans, feat_cols, best_cluster, best_win_rate
    
    def assign_signals(self, features: pd.DataFrame, prices: pd.DataFrame,
                       scaler, kmeans, feat_cols, best_cluster) -> pd.DataFrame:
        """Assign cluster labels and create signal column."""
        merged = features.join(prices[['open', 'high', 'low', 'close', 'volume']], how='inner')
        
        X_full = merged[feat_cols].fillna(0).values
        valid_mask = ~np.isnan(X_full).any(axis=1)
        X_valid = X_full[valid_mask]
        
        X_scaled = scaler.transform(X_valid)
        cluster_labels = kmeans.predict(X_scaled)
        
        signal_mask = np.zeros(len(merged), dtype=bool)
        signal_mask[valid_mask] = (cluster_labels == best_cluster)
        
        merged_valid = merged.loc[valid_mask].copy()
        merged_valid['signal'] = (cluster_labels == best_cluster)
        
        print(f"Signals: {merged_valid['signal'].sum():,} ({merged_valid['signal'].mean():.1%})")
        
        return merged_valid
    
    def calculate_atr(self, merged: pd.DataFrame) -> pd.Series:
        """Calculate ATR."""
        tr1 = merged['high'] - merged['low']
        tr2 = (merged['high'] - merged['close'].shift(1)).abs()
        tr3 = (merged['low'] - merged['close'].shift(1)).abs()
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return true_range.rolling(20).mean()
    
    def run_symmetrical_backtest(self, merged: pd.DataFrame, atr_series: pd.Series) -> list:
        """
        TASK 1: Symmetrical 1:1 R:R backtest (2.5 ATR stop = 2.5 ATR target)
        """
        print("\n" + "="*70)
        print("TASK 1: SYMMETRICAL BACKTEST (2.5 ATR Stop = 2.5 ATR Target)")
        print("="*70)
        
        position = None
        trades = []
        
        # SYMMETRICAL: 2.5 ATR target, 2.5 ATR stop (1:1 R:R)
        target_mult = 2.5
        stop_mult = 2.5  # <-- CHANGED from 1.25 to 2.5
        max_hold_bars = 30
        
        price_array = merged[['open', 'high', 'low', 'close']].values
        atr_array = atr_series.values
        signal_array = merged['signal'].values
        index_array = merged.index
        
        for idx in range(len(merged)):
            if position is None:
                if signal_array[idx]:
                    atr = atr_array[idx]
                    close_price = price_array[idx, 3]
                    
                    position = {
                        'entry_idx': idx,
                        'entry_time': index_array[idx],
                        'entry_price': close_price,
                        'target': close_price + (target_mult * atr),
                        'stop': close_price - (stop_mult * atr),
                        'atr': atr
                    }
            else:
                high = price_array[idx, 1]
                low = price_array[idx, 2]
                close = price_array[idx, 3]
                
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
        
        # Analyze
        df_trades = pd.DataFrame(trades)
        total = len(df_trades)
        wins = df_trades['is_win'].sum()
        hit_rate = wins / total
        
        avg_win = df_trades[df_trades['is_win']]['pnl_r'].mean() if wins > 0 else 0
        avg_loss = df_trades[~df_trades['is_win']]['pnl_r'].mean() if (total - wins) > 0 else 0
        expectancy = (hit_rate * avg_win) + ((1 - hit_rate) * avg_loss)
        
        print(f"\nResults (1:1 R:R with 2.5 ATR stop):")
        print(f"  Total Trades:  {total:,}")
        print(f"  Hit Rate:      {hit_rate:.1%}")
        print(f"  Avg Win:       {avg_win:.3f}R")
        print(f"  Avg Loss:      {avg_loss:.3f}R")
        print(f"  Expectancy:    {expectancy:.3f}R per trade")
        
        # Exit breakdown
        print(f"\n  Exit Breakdown:")
        for reason in ['TARGET_HIT', 'STOP_LOSS', 'TIME_STOP']:
            count = (df_trades['exit_reason'] == reason).sum()
            pct = count / total * 100
            reason_hr = df_trades[df_trades['exit_reason'] == reason]['is_win'].mean() if count > 0 else 0
            print(f"    {reason:12s}: {count:5d} ({pct:5.1f}%) | Win Rate: {reason_hr:.1%}")
        
        # Verdict
        print(f"\n  Cluster Win Rate: 57.9%")
        print(f"  Backtest Hit Rate: {hit_rate:.1%}")
        diff = (hit_rate - 0.579) * 100
        if abs(diff) < 5:
            print(f"  --> HIT RATE RECOVERED! (+{diff:.1f}pp)")
        else:
            print(f"  --> Still gap of {diff:.1f}pp")
        
        return trades
    
    def run_mae_analysis(self, merged: pd.DataFrame, atr_series: pd.Series) -> dict:
        """
        TASK 2: MAE (Maximum Adverse Excursion) Analysis
        
        For each bar that WOULD have been a winner (hit 2.5 ATR target eventually),
        calculate the maximum drawdown that occurred before winning.
        """
        print("\n" + "="*70)
        print("TASK 2: MAE (Maximum Adverse Excursion) ANALYSIS")
        print("="*70)
        
        # Parameters
        target_atr = 2.5
        max_bars = 60  # Look ahead up to 60 bars
        
        price_array = merged[['open', 'high', 'low', 'close']].values
        atr_array = atr_series.values
        signal_array = merged['signal'].values
        
        mae_data = []
        
        signal_count = 0
        winner_count = 0
        
        print("\nScanning for winning trades and their MAE...")
        
        for idx in range(len(merged) - max_bars):
            if not signal_array[idx]:
                continue
            
            signal_count += 1
            
            entry_price = price_array[idx, 3]  # Close
            atr = atr_array[idx]
            
            if np.isnan(atr) or atr <= 0:
                continue
            
            target_price = entry_price + (target_atr * atr)
            
            # Track max drawdown and whether target was hit
            max_drawdown = 0  # In ATR units
            target_hit = False
            bars_to_target = 0
            
            for future_idx in range(idx + 1, min(idx + max_bars + 1, len(merged))):
                future_high = price_array[future_idx, 1]
                future_low = price_array[future_idx, 2]
                
                # Calculate drawdown in ATR units
                drawdown = (entry_price - future_low) / atr
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
                
                # Check if target hit
                if future_high >= target_price:
                    target_hit = True
                    bars_to_target = future_idx - idx
                    break
            
            if target_hit:
                winner_count += 1
                mae_data.append({
                    'entry_idx': idx,
                    'entry_price': entry_price,
                    'atr': atr,
                    'mae_atr': max_drawdown,
                    'mae_dollars': max_drawdown * atr,
                    'bars_to_target': bars_to_target
                })
        
        print(f"\nTotal signals analyzed: {signal_count:,}")
        print(f"Winners (hit 2.5 ATR target): {winner_count:,}")
        print(f"Win rate (no stop): {winner_count/signal_count:.1%}")
        
        if not mae_data:
            print("No MAE data collected!")
            return {}
        
        mae_df = pd.DataFrame(mae_data)
        
        # MAE Statistics
        print("\n" + "-"*50)
        print("MAE STATISTICS FOR WINNING TRADES")
        print("-"*50)
        
        print(f"\nMAE Distribution (in ATR units):")
        print(f"  Min:    {mae_df['mae_atr'].min():.3f} ATR")
        print(f"  Mean:   {mae_df['mae_atr'].mean():.3f} ATR")
        print(f"  Median: {mae_df['mae_atr'].median():.3f} ATR")
        print(f"  Max:    {mae_df['mae_atr'].max():.3f} ATR")
        print(f"  Std:    {mae_df['mae_atr'].std():.3f} ATR")
        
        # Percentiles
        percentiles = [50, 60, 70, 75, 80, 85, 90, 95, 99]
        print(f"\nMAE Percentiles (in ATR units):")
        print("  " + "-"*40)
        for p in percentiles:
            val = np.percentile(mae_df['mae_atr'], p)
            print(f"  {p:2d}th percentile: {val:.3f} ATR")
        print("  " + "-"*40)
        
        # Optimal stop analysis
        print("\n" + "-"*50)
        print("OPTIMAL STOP ANALYSIS")
        print("-"*50)
        print("\nIf we set stop at X ATR, we would KEEP Y% of winners:")
        print("  " + "-"*40)
        
        stop_levels = [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 3.0]
        optimal_data = []
        
        for stop in stop_levels:
            kept = (mae_df['mae_atr'] < stop).sum()
            kept_pct = kept / len(mae_df) * 100
            lost = len(mae_df) - kept
            
            # Estimate net expectancy
            # Winners that don't hit stop: kept (win 2.5 ATR each)
            # Winners that DO hit stop: lost (lose 'stop' ATR each)
            # This is rough but directional
            
            total_signals = signal_count
            true_winners = winner_count
            stopped_winners = lost
            surviving_winners = kept
            true_losers = total_signals - true_winners
            
            # Assume losers always hit stop (worst case)
            # Surviving winners: win 2.5 ATR
            # Stopped winners: lose 'stop' ATR
            # True losers: lose 'stop' ATR
            
            gross_wins = surviving_winners * target_atr
            gross_losses = (stopped_winners + true_losers) * stop
            net_pnl = gross_wins - gross_losses
            trades_taken = total_signals
            expectancy = net_pnl / trades_taken
            
            print(f"  Stop {stop:.2f} ATR: Keep {kept_pct:5.1f}% of winners | Est. Expectancy: {expectancy:.3f} ATR/trade")
            
            optimal_data.append({
                'stop_atr': stop,
                'winners_kept_pct': kept_pct,
                'estimated_expectancy': expectancy
            })
        
        print("  " + "-"*40)
        
        # Find optimal stop
        optimal_df = pd.DataFrame(optimal_data)
        best_row = optimal_df.loc[optimal_df['estimated_expectancy'].idxmax()]
        
        print(f"\n*** OPTIMAL STOP: {best_row['stop_atr']:.2f} ATR ***")
        print(f"    Keeps {best_row['winners_kept_pct']:.1f}% of winners")
        print(f"    Estimated Expectancy: {best_row['estimated_expectancy']:.3f} ATR per trade")
        
        # Bars to target distribution
        print(f"\nTime to Target (bars) for Winners:")
        print(f"  Mean:   {mae_df['bars_to_target'].mean():.1f} bars")
        print(f"  Median: {mae_df['bars_to_target'].median():.1f} bars")
        print(f"  90th:   {np.percentile(mae_df['bars_to_target'], 90):.1f} bars")
        
        return {
            'mae_df': mae_df,
            'optimal_data': optimal_data,
            'best_stop': best_row['stop_atr']
        }


def main():
    print("="*70)
    print("GOLDEN SOURCE V4: EXIT OPTIMIZATION ANALYSIS")
    print("="*70)
    
    analyzer = ExitOptimizationAnalyzer()
    
    for symbol in ['SPY']:
        try:
            # Load data
            features, prices = analyzer.load_data(symbol)
            
            # Setup clustering
            scaler, kmeans, feat_cols, best_cluster, cluster_wr = \
                analyzer.setup_clustering(features, symbol)
            
            # Assign signals
            merged = analyzer.assign_signals(features, prices, scaler, kmeans, feat_cols, best_cluster)
            
            # Calculate ATR
            atr_series = analyzer.calculate_atr(merged)
            valid_mask = ~atr_series.isna()
            merged = merged.loc[valid_mask]
            atr_series = atr_series.loc[valid_mask]
            
            # TASK 1: Symmetrical backtest
            trades = analyzer.run_symmetrical_backtest(merged, atr_series)
            
            # TASK 2: MAE Analysis
            mae_results = analyzer.run_mae_analysis(merged, atr_series)
            
            # Final recommendation
            print("\n" + "="*70)
            print("FINAL RECOMMENDATION")
            print("="*70)
            
            if mae_results and 'best_stop' in mae_results:
                print(f"\n1. Use STOP LOSS of {mae_results['best_stop']:.2f} ATR")
                print(f"2. Keep TARGET at 2.5 ATR")
                print(f"3. This gives R:R of {2.5/mae_results['best_stop']:.2f}:1")
                print(f"\nRationale: This stop level preserves maximum edge while")
                print(f"filtering out trades that would hit stop before target.")
            
        except Exception as e:
            print(f"\nERROR: {e}")
            import traceback
            traceback.print_exc()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
