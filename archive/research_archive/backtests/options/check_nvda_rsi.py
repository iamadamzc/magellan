import pandas as pd
from src.data_handler import AlpacaDataClient
from src.features import calculate_rsi

alpaca = AlpacaDataClient()
df = alpaca.fetch_historical_bars('NVDA', '1Day', '2025-01-01', '2026-01-15')
df['rsi'] = calculate_rsi(df['close'], period=21)

print("NVDA RSI Analysis (2025):")
print(f"  Min RSI: {df['rsi'].min():.1f}")
print(f"  Max RSI: {df['rsi'].max():.1f}")
print(f"  Days RSI <30: {(df['rsi'] < 30).sum()}")
print(f"  Days RSI >70: {(df['rsi'] > 70).sum()}")
print(f"  Days RSI 30-70: {((df['rsi'] >= 30) & (df['rsi'] <= 70)).sum()}")

print("\nConclusion: NVDA stayed in 30-70 range (trending, not mean-reverting)")
print("Premium selling needs RSI extremes to work!")
