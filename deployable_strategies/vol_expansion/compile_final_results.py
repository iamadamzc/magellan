"""
FINAL OPTIMIZATION SUMMARY
Compile results from all phases and generate final deployment configs.
"""

import json
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent

# Load all phase results
with open(project_root / "test" / "vol_expansion" / "phase1_rr_results.json") as f:
    phase1 = json.load(f)

with open(
    project_root / "test" / "vol_expansion" / "phase2_timestop_results.json"
) as f:
    phase2 = json.load(f)

with open(project_root / "test" / "vol_expansion" / "phase4_sniper_results.json") as f:
    phase4 = json.load(f)

print("=" * 80)
print("FINAL OPTIMIZATION RESULTS - ALL PHASES")
print("=" * 80)

print("\n" + "=" * 80)
print("WORKHORSE STRATEGY - FULLY OPTIMIZED (Phase 1 + Phase 2)")
print("=" * 80)

print(
    f"\n{'Symbol':<8} {'Cluster':<8} {'Trend?':<8} {'R:R':<12} {'TimeStop':<15} {'Trades':<8} {'Win%':<8} {'Expect':<10} {'Return':<10}"
)
print("-" * 100)

final_configs = {}

for symbol in sorted(
    phase2.keys(), key=lambda s: phase2[s]["best_timestop"]["return_pct"], reverse=True
):
    p2 = phase2[symbol]
    best_ts = p2["best_timestop"]

    trend_str = "Yes" if p2["trend_filter"] else "No"
    rr_str = f"{p2['target']}:{p2['stop']}"
    ts_str = f"{best_ts['bars']} bars"

    print(
        f"{symbol:<8} {p2['cluster']:<8} {trend_str:<8} {rr_str:<12} {ts_str:<15} {best_ts['trades']:<8} {best_ts['win_rate']:<7.1%} {best_ts['expectancy']:<9.3f}R {best_ts['return_pct']:>8.1f}%"
    )

    final_configs[symbol] = {
        "workhorse": {
            "cluster": p2["cluster"],
            "trend_filter": p2["trend_filter"],
            "target_atr": p2["target"],
            "stop_atr": p2["stop"],
            "time_stop_bars": best_ts["bars"],
            "expected_return": best_ts["return_pct"],
            "expected_trades": best_ts["trades"],
            "expected_win_rate": best_ts["win_rate"],
            "expected_expectancy": best_ts["expectancy"],
        }
    }

# Add Sniper if profitable
print("\n" + "=" * 80)
print("SNIPER STRATEGY - OPTIMIZED (Phase 4)")
print("=" * 80)

print(
    f"\n{'Symbol':<8} {'Pct':<6} {'Trend?':<8} {'Trades':<8} {'Win%':<8} {'Expect':<10} {'Return':<10} {'Status':<10}"
)
print("-" * 80)

for symbol in sorted(
    phase4.keys(), key=lambda s: phase4[s]["best_sniper"]["return_pct"], reverse=True
):
    best = phase4[symbol]["best_sniper"]
    trend_str = "Yes" if best["trend_filter"] else "No"

    status = (
        "✅ DEPLOY"
        if best["return_pct"] > 0 and best["trades"] >= 5
        else "⚠️ LOW FREQ" if best["trades"] > 0 else "❌ SKIP"
    )

    print(
        f"{symbol:<8} {best['percentile']:<6} {trend_str:<8} {best['trades']:<8} {best['win_rate']:<7.1%} {best['expectancy']:<9.3f}R {best['return_pct']:>8.1f}% {status:<10}"
    )

    if symbol in final_configs and best["return_pct"] > 0 and best["trades"] >= 3:
        final_configs[symbol]["sniper"] = {
            "thresholds": best["thresholds"],
            "trend_filter": best["trend_filter"],
            "expected_return": best["return_pct"],
            "expected_trades": best["trades"],
        }

# Final summary
print("\n" + "=" * 80)
print("DEPLOYMENT RECOMMENDATION")
print("=" * 80)

print("\n🏆 TOP PERFORMERS (Workhorse, Fully Optimized):")
for symbol in ["GLD", "IVV", "IWM", "SPY", "QQQ", "VOO"]:
    if symbol in phase2:
        ret = phase2[symbol]["best_timestop"]["return_pct"]
        if ret > 0:
            print(f"  {symbol}: +{ret:.1f}%")

print("\n📊 COMBINED RETURN (if deploying all profitable Workhorse configs):")
total = sum(
    phase2[s]["best_timestop"]["return_pct"]
    for s in phase2
    if phase2[s]["best_timestop"]["return_pct"] > 0
)
print(f"  Total: +{total:.1f}%")

print("\n⚠️ STILL NEED WORK:")
for symbol in phase2:
    if phase2[symbol]["best_timestop"]["return_pct"] <= 0:
        print(f"  {symbol}: {phase2[symbol]['best_timestop']['return_pct']:.1f}%")

# Save final configs
output_file = project_root / "test" / "vol_expansion" / "FINAL_OPTIMIZED_CONFIGS.json"
with open(output_file, "w") as f:
    json.dump(final_configs, f, indent=2)

print(f"\n*** Final configs saved to {output_file} ***")
