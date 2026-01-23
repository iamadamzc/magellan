# A/B Dataset Strategy - Bear Trap ML Scanner

## 🎯 Strategic Rationale

**Problem**: Traditional ML approaches train and test on the same symbols, leading to overfitting.

**Solution**: A/B dataset split with completely disjoint symbol sets.

---

## 📊 Dataset Structure

### **Dataset A: "Validated" (Training Set)**
```
Purpose: Learn patterns from known-good Bear Trap symbols
Symbols: 14 validated tickers (MULN, ONDS, AMC, NKLA, WKHS, etc.)
Period: 2022-2024 (3 years)
Events: ~2,500 (after first-cross deduplication)
Labels: Known to work with Bear Trap strategy
```

**Characteristics**:
- ✅ Historical validation
- ✅ Known reversal rates
- ✅ Diverse volatility profiles
- ⚠️ Potential MULN-bias (will weight-balance)

### **Dataset B: "Discovery" (Test Set)**
```
Purpose: Test generalization to UNSEEN symbols
Symbols: 50 random volatile small-caps (NOT in Dataset A)
Period: 2022-2024 (same 3 years)
Events: ~500-1,000 (first-cross only)
Labels: Unknown performance - to be discovered
```

**Symbol Categories**:
- Meme/retail: BBBY, DWAC, CLOV, SPCE, etc.
- Crypto-related: MSTR, COIN
- EV specs: LCID, RIVN, FSR
- Biotech: SAVA, SRNE, VXRT
- Cannabis: SNDL, HEXO, CGC
- Other volatiles: SOFI, HOOD, DKNG

**Characteristics**:
- ✅ Completely independent from training
- ✅ Diverse sectors and market caps
- ✅ Realistic production scenario
- ✅ True out-of-sample test

---

## 🧪 A/B Testing Framework

### **Phase 1: Feature Engineering** ✅ IN PROGRESS
- Extract identical features for both datasets
- Ensure no data leakage between A and B

### **Phase 2: Exploratory Analysis**
```python
# Compare distributions
compare_datasets(dataset_a, dataset_b, features=[
    'drop_pct',
    'pct_from_52w_low',
    'volume_spike',
    'market_cap',
])

# Goal: Verify A and B are comparable
# If too different, adjust sampling
```

### **Phase 3: Model Training**
```python
# Train ONLY on Dataset A
X_train, X_test = train_test_split(dataset_a, test_size=0.2)

model = XGBClassifier()
model.fit(X_train, y_train)

# Validation on held-out A
val_accuracy_a = model.score(X_test_a, y_test_a)
print(f"Dataset A accuracy: {val_accuracy_a:.1%}")
```

### **Phase 4: Out-of-Sample Testing**
```python
# THE REAL TEST: Dataset B (never seen before)
test_accuracy_b = model.score(X_test_b, y_test_b)
print(f"Dataset B accuracy: {test_accuracy_b:.1%}")

# Only deploy if B performance is acceptable
if test_accuracy_b >= 0.60:
    deploy_to_production()
else:
    model_is_overfit()  # Back to feature engineering
```

---

## 📈 Success Criteria Matrix

| Scenario | Train A | Test A | Test B | Interpretation | Action |
|----------|---------|--------|--------|----------------|--------|
| **Overfit** | 85% | 83% | 52% | ❌ Symbol-specific | Reject |
| **Underfit** | 58% | 57% | 56% | ⚠️ No edge detected | Rethink features |
| **Good** | 72% | 69% | 66% | ✅ Generalizes | Deploy with caution |
| **Excellent** | 78% | 75% | 71% | ✅✅ Production ready | Full deployment |

**Critical metric**: **Test B performance**

- <60%: Model doesn't generalize, do not deploy
- 60-65%: Marginal, deploy with reduced risk
- 65-70%: Good generalization, standard deployment
- >70%: Excellent, can expand scanner aggressively

---

## 🎯 Deduplication Strategy

**Problem** (from advisor feedback):
- One day can produce many "events" if price stays below -15%
- Creates autocorrelation and inflates sample size

**Solution**:
```python
EVENT_DEFINITION = {
    'dedup_rule': 'first_cross_only',
    'timestamp': 'FIRST 1-minute bar where low <= -15% vs session open',
    'session_open': 'First bar at 9:30 AM ET (regular hours only)',
    'extended_hours': False,
}
```

**Impact**:
- Dataset A: 9,278 events → ~2,500 unique events
- Dataset B: ~500-1,000 unique events
- Each event is independent (one per symbol per day max)

---

## 🔬 Validation Steps

### **1. Distribution Comparison**
Ensure A and B are comparable:
- Similar drop % distributions
- Similar volume spike patterns
- Similar market cap ranges
- Similar time-of-day distributions

### **2. Symbol Balancing** (Dataset A only)
Cap per-symbol contributions:
```python
# Prevent MULN dominance
max_events_per_symbol = 300
dataset_a_balanced = dataset_a.groupby('symbol').head(max_events_per_symbol)
```

### **3. Leave-One-Symbol-Out (LOSO) Validation**
```python
# For each symbol in Dataset A
for holdout_symbol in dataset_a_symbols:
    train = dataset_a[dataset_a.symbol != holdout_symbol]
    test = dataset_a[dataset_a.symbol == holdout_symbol]
    
    model.fit(train)
    accuracy = model.score(test)
    
    # All symbols should have >60% accuracy
    # If one symbol fails badly, it's an outlier
```

---

## 💡 Production Deployment Logic

### **Confidence Tiers Based on Testing**
```python
def get_confidence_multiplier(symbol, ml_prediction):
    base_confidence = ml_prediction
    
    if symbol in DATASET_A_SYMBOLS:
        # Trained on this symbol
        multiplier = 1.2
    elif symbol in DATASET_B_SYMBOLS:
        # Validated on this symbol (out-of-sample)
        multiplier = 1.0
    else:
        # Completely new symbol (production discovery)
        multiplier = 0.8  # Conservative
    
    final_confidence = base_confidence * multiplier
    return final_confidence
```

### **Risk Allocation**
```python
if final_confidence >= 0.80:
    risk_pct = 0.025  # 2.5%
elif final_confidence >= 0.65:
    risk_pct = 0.020  # 2.0% (standard)
elif final_confidence >= 0.50:
    risk_pct = 0.015  # 1.5%
else:
    SKIP_TRADE  # Too low confidence
```

---

## 📋 Current Status

- [x] Dataset A collected (9,278 raw events, needs deduplication)
- [⏳] Dataset B collecting (ETA: 20 minutes)
- [ ] Deduplication of both datasets
- [ ] Feature extraction for Dataset B
- [ ] Distribution comparison
- [ ] ML model training
- [ ] A/B performance validation

---

## 🎯 Why This Approach is Superior

**Typical quant mistakes**:
- ❌ Train on AAPL, test on AAPL (overfit)
- ❌ Train on 2020-2023, test on 2024 (regime shift)
- ❌ Use all data, no holdout (no validation)

**Our approach**:
- ✅ Train on Symbol Set A, test on Symbol Set B
- ✅ Same time periods (no regime bias)
- ✅ Proper statistical independence
- ✅ Matches production reality (new symbols discovered daily)

**This is institutional-grade validation.**

---

*Based on feedback from quant advisor - January 21, 2026*
