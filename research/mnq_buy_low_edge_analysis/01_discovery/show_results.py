import pandas as pd

# Read the results
df = pd.read_csv('buy_low_signals_mfe_mae.csv')

print("=" * 70)
print("EDGE ANALYSIS RESULTS SUMMARY")
print("=" * 70)
print()
print(f"Total Trade Signals Found: {len(df):,}")
print()
win_rate = len(df[df['mfe'] > 2 * df['mae']]) / len(df) * 100
print(f"Win Rate (Trades where MFE > 2x MAE): {win_rate:.2f}%")
print()
print(f"Average MFE (Potential Reward): ${df['mfe'].mean():.2f}")
print(f"Average MAE (Risk/Drawdown):    ${df['mae'].mean():.2f}")
print(f"Average Risk:Reward Ratio:      {(df['mfe']/df['mae']).mean():.2f}x")
print(f"Median Risk:Reward Ratio:       {(df['mfe']/df['mae']).median():.2f}x")
print()
print(f"Positive MFE Rate: {len(df[df['mfe'] > 0]) / len(df) * 100:.2f}%")
print()
print("=" * 70)
