"""
Quick summary of earnings straddles backtest results
"""
import pandas as pd
from pathlib import Path

results_dir = Path('deployable_strategies/earnings_straddles')

print("="*100)
print("EARNINGS STRADDLES 2025 - BACKTEST RESULTS SUMMARY")
print("="*100)
print("Starting Capital: $100,000 per event\n")

# Read summary
summary = pd.read_csv(results_dir / 'earnings_2025_all_assets_summary.csv', index_col=0)
print("\nRESULTS BY TICKER:")
print("="*100)
print(f"{'Ticker':<8} {'Trades':>8} {'Win%':>8} {'Avg P&L':>15} {'Total P&L':>16} {'Sharpe':>10} {'Status':>10}")
print("-"*100)

for ticker in summary.index:
    row = summary.loc[ticker]
    status = "WIN" if row['total_pnl'] > 0 else "LOSS"
    print(f"{ticker:<8} {int(row['trades']):8d} {row['win_rate']:7.1f}% ${row['avg_pnl']:14,.0f} ${row['total_pnl']:15,.0f} {row['sharpe']:10.2f} {status:>10}")

print("\n" + "="*100)
print("PORTFOLIO TOTALS:")
print("="*100)
total_pnl = summary['total_pnl'].sum()
total_trades = summary['trades'].sum()
avg_win_rate = summary['win_rate'].mean()

print(f"Total Trades:       {int(total_trades)}")
print(f"Total P&L:          ${total_pnl:,.0f}")
print(f"Average Win Rate:   {avg_win_rate:.1f}%")
print(f"Capital Deployed:   ${int(total_trades) * 100000:,.0f}")
print(f"Portfolio Return:   {(total_pnl / (int(total_trades) * 100000)) * 100:.1f}%")

print("\n" + "="*100)
print("TOP 3 PERFORMERS:")
print("="*100)
top3 = summary.nlargest(3, 'total_pnl')
for i, (ticker, row) in enumerate(top3.iterrows(), 1):
    print(f"{i}. {ticker}: ${row['total_pnl']:,.0f} ({row['trades']:.0f} trades, {row['win_rate']:.1f}% win rate)")

print("\n" + "="*100)
print("BOTTOM 3 PERFORMERS:")
print("="*100)
bottom3 = summary.nsmallest(3, 'total_pnl')
for i, (ticker, row) in enumerate(bottom3.iterrows(), 1):
    print(f"{i}. {ticker}: ${row['total_pnl']:,.0f} ({row['trades']:.0f} trades, {row['win_rate']:.1f}% win rate)")

print("\n" + "="*100)
