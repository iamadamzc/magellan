"""
Golden Source Validation V2 - WITH FEATURE SCALING

CRITICAL FIX: The FINAL_STRATEGY_RESULTS.json thresholds are in STANDARDIZED space.
The research used StandardScaler to normalize features before clustering and threshold application.

This version replicates the exact scaling logic from cluster_analysis.py.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
import json
from sklearn.preprocessing import StandardScaler

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))


class GoldenSourceValidatorV2:
    """
    Golden source validator with proper feature scaling.
    
    KEY FIX: Apply StandardScaler to features before threshold comparison.
    """
    
    def __init__(self):
        # Load research thresholds
        results_path = project_root / "research" / "blind_backwards_analysis" / "outputs" / "FINAL_STRATEGY_RESULTS.json"
        with open(results_path) as f:
            self.research_thresholds = json.load(f)
        
        print("✓ Loaded research thresholds (STANDARDIZED SPACE)")
        
    def load_golden_source(self, symbol: str) -> pd.DataFrame:
        """Load pre-computed research features."""
        features_path = project_root / "research" / "blind_backwards_analysis" / "outputs" / f"{symbol}_features.parquet"
        
        if not features_path.exists():
            raise FileNotFoundError(f"Golden source not found: {features_path}")
        
        df = pd.read_parquet(features_path)
        print(f"✓ Loaded golden source for {symbol}: {len(df):,} bars")
        
        return df
    
    def load_price_data(self, symbol: str) -> pd.DataFrame:
        """Load raw OHLCV price data."""
        data_path = project_root / "data" / "cache" / "equities"
        files = sorted(data_path.glob(f"{symbol}_1min_202*.parquet"), 
                      key=lambda x: x.stat().st_size, reverse=True)
        
        if not files:
            raise FileNotFoundError(f"No price data found for {symbol}")
        
        df = pd.read_parquet(files[0])
        print(f"✓ Loaded price data: {len(df):,} bars")
        
        return df
    
    def merge_and_scale(self, features: pd.DataFrame, prices: pd.DataFrame) -> tuple:
        """
        Merge features with prices and apply StandardScaler.
        
        CRITICAL: This replicates the research scaling logic.
        """
        print("\n📊 Preparing data with SCALING...")
        
        # Merge on index
        merged = features.join(prices[['open', 'high', 'low', 'close', 'volume']], how='inner')
        print(f"  Merged: {len(merged):,} bars")
        
        # Identify feature columns (same as research: *_mean and *_std)
        feature_cols = [c for c in merged.columns if '_mean' in c or '_std' in c]
        feature_cols = [c for c in feature_cols if not merged[c].isna().all()]
        print(f"  Feature columns for scaling: {len(feature_cols)}")
        
        # Fit StandardScaler on ALL data (same as research)
        X = merged[feature_cols].fillna(0).values
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        print(f"  ✓ Fitted StandardScaler on {len(X):,} samples")
        print(f"    Feature means: {scaler.mean_[:3]}... (first 3)")
        print(f"    Feature stds:  {scaler.scale_[:3]}... (first 3)")
        
        # Create scaled feature dataframe
        scaled_features = pd.DataFrame(
            X_scaled,
            index=merged.index,
            columns=feature_cols
        )
        
        return merged, scaled_features, feature_cols, scaler
    
    def get_thresholds(self, symbol: str) -> dict:
        """Get entry thresholds from research (these are in SCALED space)."""
        research = self.research_thresholds[symbol]
        thresholds = {}
        
        for feature_data in research['feature_profile']:
            feat = feature_data['feature']
            thresholds[feat] = {
                'value': feature_data['threshold'],
                'direction': feature_data['direction']
            }
        
        return thresholds
    
    def run_backtest(self, symbol: str, merged: pd.DataFrame, 
                     scaled_features: pd.DataFrame, feature_cols: list) -> list:
        """Run backtest using SCALED features for entry signals."""
        print(f"\n{'='*70}")
        print(f"GOLDEN SOURCE BACKTEST V2 (SCALED): {symbol}")
        print(f"{'='*70}")
        
        # Calculate ATR
        tr1 = merged['high'] - merged['low']
        tr2 = (merged['high'] - merged['close'].shift(1)).abs()
        tr3 = (merged['low'] - merged['close'].shift(1)).abs()
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr_series = true_range.rolling(20).mean()
        
        # Filter to valid bars
        valid_mask = ~atr_series.isna()
        merged = merged.loc[valid_mask]
        scaled_features = scaled_features.loc[valid_mask]
        atr_series = atr_series.loc[valid_mask]
        print(f"Bars after ATR warmup: {len(merged):,}")
        
        # Get thresholds (in SCALED space)
        thresholds = self.get_thresholds(symbol)
        print(f"\nEntry thresholds (SCALED SPACE):")
        for feat, data in thresholds.items():
            print(f"  {feat} {data['direction']} {data['value']:.4f}")
        
        # Create feature name to index mapping
        feat_to_idx = {f: i for i, f in enumerate(feature_cols)}
        
        # Check how many bars pass each condition in SCALED space
        print("\nFeature statistics (SCALED):")
        for feat_name, threshold_data in thresholds.items():
            if feat_name in feat_to_idx:
                idx = feat_to_idx[feat_name]
                values = scaled_features.iloc[:, idx]
                threshold = threshold_data['value']
                direction = threshold_data['direction']
                
                if direction == '<':
                    passing = (values < threshold).sum()
                else:
                    passing = (values > threshold).sum()
                
                pct = passing / len(values) * 100
                print(f"  {feat_name}: mean={values.mean():.4f}, "
                      f"threshold={threshold:.4f} ({direction}), "
                      f"passing={passing:,} ({pct:.1f}%)")
            else:
                print(f"  {feat_name}: NOT FOUND!")
        
        # Run backtest
        position = None
        trades = []
        signals = 0
        
        # Exit parameters
        target_mult = 2.5
        stop_mult = 1.25
        max_hold_bars = 30
        
        # Convert to numpy for speed
        scaled_array = scaled_features.values
        price_array = merged[['open', 'high', 'low', 'close']].values
        atr_array = atr_series.values
        index_array = merged.index
        
        for idx in range(len(merged)):
            if position is None:
                # Check entry using SCALED features
                entry_signal = True
                for feat_name, threshold_data in thresholds.items():
                    if feat_name not in feat_to_idx:
                        entry_signal = False
                        break
                    
                    feat_idx = feat_to_idx[feat_name]
                    value = scaled_array[idx, feat_idx]
                    threshold = threshold_data['value']
                    direction = threshold_data['direction']
                    
                    if direction == '<':
                        if not (value < threshold):
                            entry_signal = False
                            break
                    else:
                        if not (value > threshold):
                            entry_signal = False
                            break
                
                if entry_signal:
                    signals += 1
                    atr = atr_array[idx]
                    close_price = price_array[idx, 3]  # close
                    
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
                
                # Check stop loss
                if low <= position['stop']:
                    exit_signal = True
                    exit_reason = "STOP_LOSS"
                    exit_price = position['stop']
                
                # Check target
                elif high >= position['target']:
                    exit_signal = True
                    exit_reason = "TARGET_HIT"
                    exit_price = position['target']
                
                # Check time stop
                elif idx - position['entry_idx'] >= max_hold_bars:
                    exit_signal = True
                    exit_reason = "TIME_STOP"
                    exit_price = close
                
                if exit_signal:
                    pnl_dollars = exit_price - position['entry_price']
                    risk = position['entry_price'] - position['stop']
                    pnl_r = pnl_dollars / risk if risk > 0 else 0
                    
                    trade = {
                        'entry_time': position['entry_time'],
                        'exit_time': index_array[idx],
                        'entry_price': position['entry_price'],
                        'exit_price': exit_price,
                        'pnl_r': pnl_r,
                        'is_win': pnl_dollars > 0,
                        'exit_reason': exit_reason
                    }
                    trades.append(trade)
                    position = None
        
        # Close any remaining position
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
        
        # Calculate signal frequency
        signal_freq = signals / len(merged)
        expected_freq = self.research_thresholds[symbol]['signal_frequency']
        print(f"\n📈 Signal frequency: {signal_freq:.1%} (Research: {expected_freq:.1%})")
        
        freq_diff = abs(signal_freq - expected_freq) * 100
        if freq_diff < 3:
            print("   ✅ Signal frequency MATCHES research!")
        else:
            print(f"   ⚠️ Signal frequency differs by {freq_diff:.1f}pp")
        
        return trades
    
    def analyze_results(self, trades: list, symbol: str):
        """Analyze backtest results."""
        if not trades:
            print(f"\n⚠️ WARNING: No trades for {symbol}")
            return None
        
        df_trades = pd.DataFrame(trades)
        
        total_trades = len(df_trades)
        wins = df_trades['is_win'].sum()
        hit_rate = wins / total_trades
        
        avg_win = df_trades[df_trades['is_win']]['pnl_r'].mean() if wins > 0 else 0
        avg_loss = df_trades[~df_trades['is_win']]['pnl_r'].mean() if (total_trades - wins) > 0 else 0
        expectancy = (hit_rate * avg_win) + ((1 - hit_rate) * avg_loss)
        
        print(f"\n{'='*70}")
        print(f"GOLDEN SOURCE RESULTS V2: {symbol}")
        print(f"{'='*70}")
        print(f"Total Trades:     {total_trades}")
        print(f"Wins:             {wins} ({hit_rate:.1%})")
        print(f"Avg Win:          {avg_win:.3f}R")
        print(f"Avg Loss:         {avg_loss:.3f}R")
        print(f"Expectancy:       {expectancy:.3f}R")
        
        # Compare to research
        research = self.research_thresholds[symbol]
        expected_hr = research['hit_rate']
        expected_exp = research['expectancy']
        
        hr_diff = (hit_rate - expected_hr) * 100
        exp_diff = expectancy - expected_exp
        
        print(f"\n{'Research Comparison':-^70}")
        print(f"Expected Hit Rate:   {expected_hr:.1%}")
        print(f"Actual Hit Rate:     {hit_rate:.1%} ({hr_diff:+.1f}pp)")
        print(f"Expected Expectancy: {expected_exp:.3f}R")
        print(f"Actual Expectancy:   {expectancy:.3f}R ({exp_diff:+.3f}R)")
        
        # Exit reason breakdown
        print(f"\n{'Exit Reasons':-^70}")
        exit_counts = df_trades['exit_reason'].value_counts()
        for reason, count in exit_counts.items():
            pct = (count / total_trades) * 100
            reason_trades = df_trades[df_trades['exit_reason'] == reason]
            reason_hr = reason_trades['is_win'].mean() if len(reason_trades) > 0 else 0
            print(f"{reason:15s}: {count:5d} ({pct:5.1f}%) | Win Rate: {reason_hr:.1%}")
        
        # Verdict
        print(f"\n{'DIAGNOSIS':-^70}")
        if abs(hr_diff) < 5:
            print("✅ GOLDEN SOURCE V2 VALIDATES!")
            print("   Hit rate matches research → Scaling fix worked")
            print("   → Now port exact feature calculation to production")
        else:
            print("❌ GOLDEN SOURCE V2 FAILS!")
            print("   Hit rate still off → Additional issues to investigate")
            print("   → Check exit logic or feature column alignment")
        
        return {
            'symbol': symbol,
            'total_trades': total_trades,
            'hit_rate': hit_rate,
            'expectancy': expectancy,
            'expected_hr': expected_hr,
            'diff_pp': hr_diff
        }


def main():
    """Run golden source validation V2 with scaling."""
    print("="*70)
    print("GOLDEN SOURCE VALIDATION V2 (WITH SCALING)")
    print("FIX: Apply StandardScaler before threshold comparison")
    print("="*70)
    
    validator = GoldenSourceValidatorV2()
    results = {}
    
    for symbol in ['SPY']:
        try:
            # Load golden source features
            features = validator.load_golden_source(symbol)
            
            # Load price data
            prices = validator.load_price_data(symbol)
            
            # Merge AND SCALE
            merged, scaled_features, feature_cols, scaler = validator.merge_and_scale(features, prices)
            
            # Run backtest with scaled features
            trades = validator.run_backtest(symbol, merged, scaled_features, feature_cols)
            
            # Analyze
            result = validator.analyze_results(trades, symbol)
            if result:
                results[symbol] = result
        
        except Exception as e:
            print(f"\n❌ ERROR testing {symbol}: {e}")
            import traceback
            traceback.print_exc()
    
    # Final summary
    print(f"\n\n{'='*70}")
    print("FINAL VERDICT V2")
    print(f"{'='*70}")
    
    for symbol, result in results.items():
        if abs(result['diff_pp']) < 5:
            print(f"✅ {symbol}: Hit rate {result['hit_rate']:.1%} matches research ({result['expected_hr']:.1%})")
            print(f"   → SCALING FIX WORKED! Feature calculation is the root cause.")
        else:
            print(f"❌ {symbol}: Hit rate {result['hit_rate']:.1%} ≠ research ({result['expected_hr']:.1%})")
            print(f"   → Additional investigation needed")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
