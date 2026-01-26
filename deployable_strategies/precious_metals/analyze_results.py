"""Analyze optimization results"""
import pandas as pd

df = pd.read_csv('optimization_results.csv')
print(f"Total combinations tested: {len(df)}")
print()

for symbol in ['GCUSD', 'SIUSD']:
    sym = df[df['symbol'] == symbol]
    print(f"{'='*50}")
    print(f"{symbol}")
    print(f"{'='*50}")
    
    # Best that meets target with lowest leverage
    target = sym[sym['meets_target'] == True]
    if len(target) > 0:
        best = target.loc[target['leverage'].idxmin()]
        print(f"LOWEST LEVERAGE for $200/day:")
        print(f"  RSI Period: {int(best['rsi_period'])}")
        print(f"  Entry Band: {int(best['entry_band'])}")
        print(f"  Exit Band: {int(best['exit_band'])}")
        print(f"  Leverage: {int(best['leverage'])}x")
        print(f"  Daily P&L: ${best['avg_daily_pnl']:.0f}")
        print(f"  Sharpe: {best['sharpe']:.2f}")
        print(f"  Max DD: {best['max_dd']:.0f}%")
        print(f"  Trades: {int(best['total_trades'])}")
    else:
        print("  No configuration hit $200/day target")
    
    # Best Sharpe overall
    best_sharpe = sym.loc[sym['sharpe'].idxmax()]
    print(f"\nBEST SHARPE:")
    print(f"  RSI Period: {int(best_sharpe['rsi_period'])}")
    print(f"  Entry Band: {int(best_sharpe['entry_band'])}")
    print(f"  Exit Band: {int(best_sharpe['exit_band'])}")
    print(f"  Leverage: {int(best_sharpe['leverage'])}x")
    print(f"  Daily P&L: ${best_sharpe['avg_daily_pnl']:.0f}")
    print(f"  Sharpe: {best_sharpe['sharpe']:.2f}")
    print()
