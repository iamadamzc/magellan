import pandas as pd

# Read the corrected results
df = pd.read_csv('buy_low_signals_mfe_mae.csv')

print("=" * 70)
print("CORRECTED EDGE ANALYSIS RESULTS")
print("=" * 70)
print()
print(f"Total Trade Signals Found: {len(df):,}")
print()

# Calculate statistics
mean_mfe = df['mfe'].mean()
mean_mae = df['mae'].mean()
median_mfe = df['mfe'].median()
median_mae = df['mae'].median()

print(f"MFE (Profit Potential):")
print(f"  Mean:   {mean_mfe:.2f} points (${mean_mfe * 2:.2f})")
print(f"  Median: {median_mfe:.2f} points")

print(f"\nMAE (Drawdown Risk):")
print(f"  Mean:   {mean_mae:.2f} points (${mean_mae * 2:.2f})")
print(f"  Median: {median_mae:.2f} points")

# Real Win Rate
win_rate = len(df[df['mfe'] > 2 * df['mae']]) / len(df) * 100
print(f"\n{'*' * 70}")
print(f"REAL Win Rate (MFE > 2x MAE): {win_rate:.2f}%")
print(f"{'*' * 70}")

# Additional metrics
positive_mfe = len(df[df['mfe'] > 0]) / len(df) * 100
avg_rr = (df['mfe'] / df['mae']).mean()
median_rr = (df['mfe'] / df['mae']).median()

print(f"\nPositive MFE Rate: {positive_mfe:.2f}%")
print(f"Average Risk:Reward: {avg_rr:.2f}x")
print(f"Median Risk:Reward:  {median_rr:.2f}x")
print()
print("=" * 70)
