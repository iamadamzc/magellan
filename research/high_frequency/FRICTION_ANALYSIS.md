# Trading Friction Analysis - Why HFT Failed

**Detailed breakdown of trading costs and their impact on high-frequency strategies**

---

## Friction Components

### 1. **Slippage** (Price Impact)

**Definition**: Difference between expected execution price and actual fill price

**67ms Latency Scenario** (Fast Execution):
- **1 basis point (bps)** = 0.01% per side
- Entry slip: 1 bps
- Exit slip: 1 bps
- **Total: 2 bps round-trip**

**500ms Latency Scenario** (Slow Execution):
- **3 bps** = 0.03% per side
- Entry slip: 3 bps
- Exit slip: 3 bps
- **Total: 6 bps round-trip**

**Why latency matters**:
```
At 67ms:  Order hits market before price moves
At 500ms: Market sees your order coming, front-runs you
Result: 67ms saves 4 bps per round-trip (0.04%)
```

---

### 2. **Bid-Ask Spread**

**SPY Typical Spread**:
- Normal hours: 1-2 cents on $550 stock = ~0.2-0.4 bps
- Volatile periods: Up to 5 cents = ~1 bps

**Impact per trade**:
- Market orders: Pay full spread (cross from bid to ask)
- Limit orders: Save spread but risk no fill

For HFT using market orders:
- **Additional ~0.5 bps** on average

---

### 3. **Commission Costs**

**Alpaca Commission Structure** (typical):
- Free for retail (but SEC fees apply)
- SEC fee: $0.0000278 per $1 traded
- For $10,000 position: ~$0.28 = **0.28 bps**

**Professional/Volume Traders**:
- Tiered pricing: $0.001-0.005 per share
- For 18 SPY shares @ $550: $0.018-0.09
- Works out to ~**0.3-1.5 bps**

---

### 4. **Market Impact** (Hidden Cost)

**For positions >$10k**:
- Your order moves the market
- Especially on volatile stocks (NVDA, TSLA)
- Estimate: Additional **0.5-1.0 bps** for $25k positions

---

## Total Friction Calculation

### Scenario A: 67ms Latency (Our System)

| Cost Component | Per Side | Round-Trip |
|----------------|----------|------------|
| Slippage       | 1.0 bps  | 2.0 bps    |
| Bid-Ask Spread | 0.5 bps  | 0.5 bps    |
| Commissions    | 0.3 bps  | 0.6 bps    |
| Market Impact  | 0.5 bps  | 1.0 bps    |
| **TOTAL**      | **2.3 bps** | **4.1 bps** |

**= 0.041% per round-trip trade**

---

### Scenario B: 500ms Latency (Legacy Assumption)

| Cost Component | Per Side | Round-Trip |
|----------------|----------|------------|
| Slippage       | 3.0 bps  | 6.0 bps    |
| Bid-Ask Spread | 0.5 bps  | 0.5 bps    |
| Commissions    | 0.3 bps  | 0.6 bps    |
| Market Impact  | 1.0 bps  | 2.0 bps    |
| **TOTAL**      | **4.8 bps** | **9.1 bps** |

**= 0.091% per round-trip trade**

**67ms saves 5 bps (0.05%) per trade** ✅

---

## Impact on Strategy Profitability

### RSI Mean Reversion Example

**Strategy Parameters**:
- Target profit: 0.15%
- Stop loss: 0.15%
- Expected win rate: 50%

**P&L Calculation (67ms)**:

**Before Friction**:
```
Winning trade:  +0.15%
Losing trade:   -0.15%
Expected value: (0.5 × 0.15%) + (0.5 × -0.15%) = 0.00%
```

**After 4.1 bps Friction**:
```
Winning trade:  +0.15% - 0.041% = +0.109%
Losing trade:   -0.15% - 0.041% = -0.191%
Expected value: (0.5 × 0.109%) + (0.5 × -0.191%) = -0.041%
```

**Result**: Strategy loses 4.1 bps per trade on average ❌

---

### To Break Even at 50% Win Rate

Need to overcome 4.1 bps friction:

**Option 1**: Increase profit target
```
Target needed: 0.15% + 0.041% = 0.191% (27% larger target)
But: Larger targets = lower probability of hitting them
```

**Option 2**: Increase win rate
```
Win rate needed with 0.15% targets:
Let W = win rate
W × (0.15% - 0.041%) + (1-W) × (-0.15% - 0.041%) = 0
W × 0.109% + (1-W) × -0.191% = 0
W × 0.109% - 0.191% + W × 0.191% = 0
W × 0.300% = 0.191%
W = 63.7%

Need 63.7% win rate (vs current 33.3%) = impossible
```

**Option 3**: Better risk/reward ratio
```
If target = 0.30% and stop = 0.15% (2:1 ratio):
Winners: +0.30% - 0.041% = +0.259%
Losers:  -0.15% - 0.041% = -0.191%

Break-even win rate:
W × 0.259% + (1-W) × -0.191% = 0
W = 42.4%

Still hard to achieve with noisy signals!
```

---

## Frequency Amplification Effect

**Key Insight**: Friction compounds with trade frequency!

### Event-Driven Strategy (FOMC)

**FOMC Straddles**:
- Trades per year: **8**
- Friction per trade: 4.1 bps
- **Annual friction: 8 × 0.041% = 0.33%**
- Avg profit per trade: 12.84%
- **Net annual return: (8 × 12.84%) - 0.33% = 102.4%** ✅

---

### High-Frequency Strategy (RSI)

**RSI Mean Reversion**:
- Trades per day: **15** (75 trades in 5 days)
- Trading days per year: **252**
- **Total trades/year: 15 × 252 = 3,780**
- Friction per trade: 4.1 bps
- **Annual friction: 3,780 × 0.041% = 155%** 💀

Even if strategy had 1% edge per trade:
```
Gross return: 3,780 × 1% = 37.8%
Friction cost: -155%
Net return: -117.2% (CATASTROPHIC)
```

This is why HFT needs:
1. **Extremely high win rates** (>60%)
2. **Very tight spreads** (<1 bps)
3. **Sub-millisecond latency** (<1ms, not 67ms)
4. **Maker rebates** (get paid to provide liquidity)
5. **Huge volume** (billions per day to make fractions of pennies matter)

---

## Real-World Comparison

### Retail/Small Fund (Our Case)

| Feature | Our Reality |
|---------|-------------|
| Latency | 67ms (good but not HFT-grade) |
| Friction | 4.1 bps per trade |
| Capital | $10k-100k per position |
| Volume | Market taker (pay spread) |
| **Viable frequency** | **<50 trades/year** |

---

### Professional HFT Firm

| Feature | Their Reality |
|---------|-------------|
| Latency | 0.1-1.0ms (100x faster than us) |
| Friction | 0.1-0.5 bps (maker rebates!) |
| Capital | $100M+ |
| Volume | Market maker (collect spread) |
| **Viable frequency** | **Millions of trades/year** |

**They make 0.01% per trade × 1M trades = $10M profit**  
**We lose 0.041% per trade × 3,780 trades = -$15.5k loss**

---

## Why 67ms Helped But Wasn't Enough

### RSI Strategy Performance

| Metric | 500ms | 67ms | Improvement |
|--------|-------|------|-------------|
| Friction | 9.1 bps | 4.1 bps | **-5.0 bps** ✅ |
| Win Rate | 22.7% | 33.3% | **+10.7%** ✅ |
| Sharpe | -51.34 | -5.51 | **+45.82** ✅ |

**67ms cut friction in half and doubled win rate!**

But:
- Starting from -51.34 Sharpe
- Even 45-point improvement still leaves us at -5.51
- Need to overcome 4.1 bps × trade frequency

---

## Break-Even Analysis

**How good does a strategy need to be?**

At 4.1 bps friction and various trade frequencies:

| Trades/Year | Annual Friction | Min Edge/Trade Needed | Feasible? |
|-------------|----------------|----------------------|-----------|
| 10 (events) | 0.41% | **0.041%** | ✅ YES (FOMC: 12.84%) |
| 100 | 4.1% | 0.041% | ⚠️  MAYBE |
| 500 | 20.5% | 0.041% | ❌ NO |
| 2,000 | 82% | 0.041% | ❌ NO |
| 5,000 | 205% | 0.041% | 💀 IMPOSSIBLE |

**Conclusion**: At our friction level (4.1 bps), max viable frequency is ~100 trades/year

FOMC (8 trades/year) pays:
- 8 × 0.041% = 0.33% annual friction
- 8 × 12.84% = 102.7% annual return
- **Net: 102.4% with minimal friction impact** ✅

---

## Summary: The Friction Trap

### Why HFT Failed

1. **Base friction is 4.1 bps** (even with 67ms)
2. **Trade frequency kills**: 3,780 trades/year = 155% friction
3. **Signal quality is poor**: RSI extremes are noisy, not predictive
4. **Risk/reward is tight**: 0.15% targets don't overcome 4.1 bps costs

### Why Event-Driven Works

1. **Same friction** (4.1 bps per trade)
2. **Low frequency**: 8 trades/year = 0.33% friction only
3. **Clean signals**: Fed announcements = guaranteed volatility
4. **Large moves**: 12.84% avg profit easily covers 0.041% friction

### Mathematical Proof

**Break-even frequency**:
```
At 12.84% edge per trade:
Max trades = 100% ÷ 0.041% = 2,439 trades/year

But our strategies have 0% edge (before friction)
Max trades = 0 trades/year
```

**FOMC has 12.84% edge, pays 0.33% friction**:
```
Net edge = 12.84% - 0.041% = 12.80% per trade
Annual = 8 × 12.80% = 102.4%
Sharpe = 1.17 ✅
```

---

## Recommendation

**Stick with event-driven strategies** where:
- Signal quality is high (>10% edge)
- Frequency is low (<100 trades/year)
- Friction impact is minimal (<1% annually)

**Avoid high-frequency** where:
- Need >63% win rate to overcome friction
- Annual costs exceed 100%
- Competing against sub-millisecond algos

**Our sweet spot**: 8-50 trades/year, event-driven, clean signals
