"""
Information Coefficient (IC) Analysis Script

Purpose: Identify which features actually predict future returns.
This is CRITICAL for diagnosing why validation is failing (<51% hit rate).

Usage:
    python inspect_ic.py

Output:
    - IC for each feature (Spearman rank correlation with forward returns)
    - Interpretation: IC > 0.05 is useful, IC < 0.02 is noise

Next Steps Based on Results:
    - If all IC < 0.02: Strategy fundamentally broken, needs redesign
    - If 1-2 features have IC > 0.05: Focus on those, delete others
    - If RSI has highest IC: Increase RSI weight to 0.9+
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy.stats import spearmanr

# Import Magellan components
from src.data_handler import AlpacaDataClient, FMPDataClient
from src.features import FeatureEngineer, add_technical_indicators
from src.discovery import calculate_ic

def fetch_nvda_data(days=365):
    """Fetch NVDA historical data for IC analysis."""
    print("[IC] Fetching NVDA data...")
    
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    alpaca = AlpacaDataClient()
    bars = alpaca.fetch_historical_bars(
        symbol='NVDA',
        start_date=start_date,
        end_date=end_date,
        timeframe='5Min'
    )
    
    print(f"[IC] Fetched {len(bars)} bars ({start_date} to {end_date})")
    return bars

def generate_features(bars):
    """Generate all features using FeatureEngineer."""
    print("[IC] Generating features...")
    
    # Add technical indicators
    df = add_technical_indicators(bars, ticker='NVDA')
    
    # Add forward return (our target)
    df['forward_return'] = df['close'].shift(-15) / df['close'] - 1.0
    
    # Drop NaN rows
    df = df.dropna()
    
    print(f"[IC] Generated features for {len(df)} valid bars")
    return df

def analyze_ic(df):
    """Calculate IC for each feature."""
    print("\n" + "="*70)
    print("INFORMATION COEFFICIENT ANALYSIS")
    print("="*70)
    
    # Features to analyze
    features = [
        'rsi_14',
        'volume_zscore', 
        'log_return',
        'rvol',
        'parkinson_vol'
    ]
    
    # Check for sentiment if available
    if 'sentiment' in df.columns:
        features.append('sentiment')
    
    results = []
    
    for feature in features:
        if feature not in df.columns:
            print(f"[SKIP] {feature:20s} - Not in dataframe")
            continue
        
        try:
            # Calculate IC using Spearman rank correlation
            ic, p_value = spearmanr(df[feature], df['forward_return'], nan_policy='omit')
            
            # Interpret significance
            if abs(ic) > 0.05:
                significance = "⭐ STRONG"
            elif abs(ic) > 0.02:
                significance = "✓ WEAK"
            else:
                significance = "❌ NOISE"
            
            results.append({
                'feature': feature,
                'ic': ic,
                'p_value': p_value,
                'significance': significance
            })
            
            print(f"{feature:20s} IC = {ic:+.4f}  (p={p_value:.4f})  {significance}")
            
        except Exception as e:
            print(f"[ERROR] {feature:20s} - {e}")
    
    return results

def interpret_results(results):
    """Provide interpretation and next steps."""
    print("\n" + "="*70)
    print("INTERPRETATION")
    print("="*70)
    
    # Sort by absolute IC
    results_sorted = sorted(results, key=lambda x: abs(x['ic']), reverse=True)
    
    strong_features = [r for r in results_sorted if abs(r['ic']) > 0.05]
    weak_features = [r for r in results_sorted if 0.02 < abs(r['ic']) <= 0.05]
    noise_features = [r for r in results_sorted if abs(r['ic']) <= 0.02]
    
    print(f"\n📊 Feature Categories:")
    print(f"   STRONG (IC > 0.05):  {len(strong_features)} features")
    print(f"   WEAK (0.02 < IC ≤ 0.05): {len(weak_features)} features")
    print(f"   NOISE (IC ≤ 0.02):   {len(noise_features)} features")
    
    print(f"\n🎯 Recommended Actions:")
    
    if len(strong_features) == 0:
        print("   ⚠️  NO STRONG FEATURES FOUND")
        print("   → Strategy fundamentally broken")
        print("   → Options:")
        print("      1. Try different features (MACD, Bollinger, volume profile)")
        print("      2. Try different timeframes (15Min, 1Hour instead of 5Min)")
        print("      3. Consider mean-reversion instead of momentum")
        print("      4. Add machine learning (XGBoost, LSTM)")
    else:
        print(f"   ✅ Found {len(strong_features)} strong feature(s):")
        for r in strong_features:
            print(f"      • {r['feature']:20s} (IC = {r['ic']:+.4f})")
        
        print("\n   → Next Steps:")
        print("      1. Update alpha_weights to focus on strong features")
        
        best_feature = strong_features[0]['feature']
        print(f"      2. Try simple strategy with ONLY {best_feature}")
        print("      3. Delete weak/noise features to reduce overfitting")
    
    if len(noise_features) > 0:
        print(f"\n   🗑️  Consider removing these noise features:")
        for r in noise_features[:3]:  # Show top 3 worst
            print(f"      • {r['feature']:20s} (IC = {r['ic']:+.4f})")
    
    print("\n" + "="*70)

def save_results(results):
    """Save results to CSV for further analysis."""
    df_results = pd.DataFrame(results)
    output_file = 'ic_analysis_results.csv'
    df_results.to_csv(output_file, index=False)
    print(f"\n💾 Results saved to: {output_file}")

def main():
    """Main IC analysis workflow."""
    print("\n" + "="*70)
    print("MAGELLAN IC ANALYSIS - FEATURE PREDICTIVE POWER TEST")
    print("="*70)
    print("\nThis script will:")
    print("1. Fetch 1 year of NVDA 5Min data")
    print("2. Generate all features (RSI, volume, etc.)")
    print("3. Calculate IC (correlation with 15-bar forward returns)")
    print("4. Recommend which features to keep/delete")
    print("\n" + "="*70 + "\n")
    
    try:
        # Step 1: Fetch data
        bars = fetch_nvda_data(days=365)
        
        # Step 2: Generate features
        df = generate_features(bars)
        
        # Step 3: Analyze IC
        results = analyze_ic(df)
        
        # Step 4: Interpret
        interpret_results(results)
        
        # Step 5: Save
        save_results(results)
        
        print("\n✅ IC Analysis Complete!")
        print("\nNext: Review recommendations above and adjust strategy accordingly.")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
