# ML-Enhanced Position Sizing - Research Framework

**Created:** 2026-01-19  
**Concept:** ML regime classification for intelligent position scaling  
**Philosophy:** ML provides STATE, not SIGNALS

---

## 🎯 **Core Concept**

**Traditional Approach:**
```
Entry → Fixed position size → Predefined exits
```

**ML-Enhanced Approach:**
```
ML Regime Analysis → Select Scaling Template → Entry → Dynamic position management
```

**Key Principle:**
> **ML doesn't trade. ML advises on HOW MUCH to risk.**

---

## 🧠 **ML Role: Regime Classifier**

### **What ML Predicts:**

**Position Scaling Regime:**
1. **ADD_ALLOWED** - Environment supports progressive exposure
   - Historical: Trend continuation likely
   - Action: Allow scaling in on pullbacks/confirmation
   
2. **ADD_NEUTRAL** - Mixed signals
   - Historical: Choppy, unpredictable
   - Action: Normal position, no adds
   
3. **NO_ADD** - Environment punishes adding risk
   - Historical: Mean reversion, whipsaw
   - Action: Conservative, take profits early

**Exit Bias Regime:**
1. **CONTINUATION** - Trend likely to persist
   - Action: Hold for larger targets, partial exits only
   
2. **MEAN_REVERSION** - Reversal likely
   - Action: Take profits earlier, scale out aggressively

---

## 📋 **Scaling Templates**

### **Template 1: Conservative (No Adds)**
```python
CONSERVATIVE = {
    'initial_size': 0.5,      # Start with half position
    'add_1': None,            # No adds
    'add_2': None,
    'max_position': 0.5,
    'take_profit_1': 0.8,     # Exit 50% at 0.8R
    'take_profit_2': 1.5,     # Exit remaining at 1.5R
}
```

### **Template 2: Normal (One Add)**
```python
NORMAL = {
    'initial_size': 0.5,      # Start with half position
    'add_1': 0.5,             # Add at +0.5R
    'add_1_size': 0.25,       # Add quarter position
    'add_2': None,
    'max_position': 0.75,
    'take_profit_1': 1.0,     # Exit 40% at 1.0R
    'take_profit_2': 2.0,     # Exit remaining at 2.0R
}
```

### **Template 3: Aggressive (Two Adds)**
```python
AGGRESSIVE = {
    'initial_size': 0.33,     # Start with third position
    'add_1': 0.5,             # Add at +0.5R
    'add_1_size': 0.33,
    'add_2': 1.0,             # Add at +1.0R
    'add_2_size': 0.34,
    'max_position': 1.0,      # Full position
    'take_profit_1': 1.5,     # Exit 30% at 1.5R
    'take_profit_2': 3.0,     # Exit remaining at 3.0R
}
```

---

## 🔬 **ML Features (Regime Inputs)**

### **Market State Features:**

1. **Trend Strength**
   - ADX (Directional strength)
   - MA slope
   - Higher highs/lower lows count

2. **Volatility Regime**
   - ATR percentile (last 20 days)
   - Bollinger Band width
   - Historical vol vs realized vol

3. **Mean Reversion Tendency**
   - RSI at extremes frequency
   - Quick reversals count
   - Correlation with SPY (for individual stocks)

4. **Volume Pattern**
   - Breakout volume sustainability
   - Volume profile shape
   - Climax volume detection

5. **Recent Strategy Performance**
   - Last 5 trades win rate
   - Average R-multiple
   - Consecutive wins/losses

### **Target Labels (Historical):**

For each past trade, label the regime:
- **ADD_ALLOWED**: Trade went 2R+ with smooth uptrend
- **NO_ADD**: Trade whipsawed, adding would have hurt
- **ADD_NEUTRAL**: Mixed, adds didn't help/hurt

---

## 🏗️ **Implementation Architecture**

```python
# Trade Flow

1. ENTRY SIGNAL DETECTED
   ↓
2. ML REGIME CLASSIFIER
   features = calculate_regime_features(market_data)
   regime = ml_model.predict(features)  # ADD_ALLOWED, NO_ADD, etc.
   ↓
3. SELECT SCALING TEMPLATE
   if regime == 'ADD_ALLOWED':
       template = AGGRESSIVE
   elif regime == 'NO_ADD':
       template = CONSERVATIVE
   else:
       template = NORMAL
   ↓
4. ENTER WITH INITIAL SIZE
   position_size = template['initial_size'] * base_risk
   ↓
5. POSITION MANAGEMENT
   if price hits add_1 level AND template allows:
       add to position
   
   if price hits take_profit_1:
       if exit_regime == 'CONTINUATION':
           take partial (30%)
       else:  # MEAN_REVERSION
           take partial (50%)
```

---

## 📊 **Training Data Structure**

```python
# For each historical trade:
{
    'entry_date': '2024-01-15',
    'symbol': 'AMC',
    
    # Features (at entry)
    'adx': 35,                    # Strong trend
    'atr_percentile': 0.75,       # High volatility
    'rsi_extremes_5d': 2,         # Some mean reversion
    'volume_breakout': True,
    'last_5_trades_wr': 0.60,
    
    # Outcome (for labeling)
    'max_r': 2.5,                 # Hit 2.5R
    'smooth_path': True,          # No major drawdown
    'added_at_0.5r_result': +1.2, # Adding was profitable
    
    # Label
    'regime': 'ADD_ALLOWED'       # Environment supported scaling
}
```

---

## 🎯 **Test Strategy: Bear Trap**

**Why Bear Trap?**
- Best performing (+17.59% in December)
- Already has multi-stage exits
- Intraday volatility (ML can help navigate)
- Clear R-multiples (session low to stop)

**Current Bear Trap Position Sizing:**
```python
# Fixed 2% risk per trade
shares = (capital * 0.02) / risk_per_share
```

**ML-Enhanced Bear Trap:**
```python
# ML decides template
regime = ml_classifier.predict(market_features)
template = select_template(regime)

# Initial position
shares = (capital * 0.02 * template['initial_size']) / risk_per_share

# Dynamic scaling
if price_r >= template['add_1'] and template['add_1'] is not None:
    add_shares = (capital * 0.02 * template['add_1_size']) / risk_per_share
```

---

## 🧪 **Testing Protocol**

### **Phase 1: Baseline (No ML)**
```python
# Run Bear Trap with fixed position sizing
# December 2024: +17.59%
baseline_result = run_bear_trap_baseline()
```

### **Phase 2: Oracle ML (Perfect Foresight)**
```python
# Label each trade correctly using hindsight
# "If I knew the outcome, what template should I have used?"
# This sets the upper bound
oracle_result = run_with_perfect_regime_labels()
```

### **Phase 3: Trained ML**
```python
# Train on 2020-2023
# Test on 2024
# Compare vs baseline and oracle
ml_result = run_with_ml_regime_classifier()
```

### **Success Criteria:**
1. ✅ ML version > Baseline return
2. ✅ ML version < Oracle (can't be perfect, but should be closer)
3. ✅ ML version has better Sharpe (even if same return)
4. ✅ Works across multiple symbols (not overfitted)

---

## 📝 **Simple ML Model (Start Here)**

**Don't overcomplicate!** Start with decision tree:

```python
from sklearn.tree import DecisionTreeClassifier

# Features (simple start)
features = [
    'adx',                  # Trend strength
    'atr_percentile',       # Volatility regime
    'last_5_wr',           # Recent performance
    'volume_ratio',         # Volume confirmation
]

# Labels
labels = ['ADD_ALLOWED', 'ADD_NEUTRAL', 'NO_ADD']

# Train
model = DecisionTreeClassifier(max_depth=3)  # Keep shallow!
model.fit(X_train, y_train)

# Predict
regime = model.predict(current_features)
```

**Why Decision Tree?**
- Interpretable (you can see the rules)
- Fast
- Doesn't require normalization
- Works well with <1000 samples
- Easy to debug

**Later:** Can upgrade to Random Forest, XGBoost

---

## 🎯 **Minimum Viable Product (MVP)**

### **Step 1: Label Historical Trades**
```python
# Go through Bear Trap trades from 2020-2024
# For each:
#   - Did it hit 2R+? → YES: ADD_ALLOWED candidate
#   - Did it whipsaw? → YES: NO_ADD
#   - Mixed? → ADD_NEUTRAL
```

### **Step 2: Extract Features at Entry**
```python
# For each labeled trade:
#   - Calculate ADX at entry
#   - Calculate ATR percentile
#   - Calculate recent win rate
#   - Save as training data
```

### **Step 3: Train Simple Model**
```python
# Fit decision tree
# Check accuracy on holdout set
# If >55% accuracy, proceed
```

### **Step 4: Backtest**
```python
# Run Bear Trap with ML regime selection
# Compare vs baseline
# Document results
```

---

## 📂 **Directory Structure**

```
research/ml_position_sizing/
├── README.md                      # This file
├── data/
│   ├── bear_trap_trades_2020_2024.csv    # Historical trades
│   └── labeled_regimes.csv               # ML training data
├── models/
│   ├── regime_classifier_v1.pkl          # Trained model
│   └── feature_scaler.pkl                # If needed
├── notebooks/
│   ├── 01_label_historical_trades.ipynb  # Labeling
│   ├── 02_feature_engineering.ipynb      # Feature extraction
│   ├── 03_train_model.ipynb              # Model training
│   └── 04_backtest_ml_enhanced.ipynb     # Testing
└── scripts/
    ├── extract_bear_trap_trades.py       # Get historical trades
    ├── label_regime.py                   # Auto-label helper
    ├── train_regime_model.py             # Train ML
    └── backtest_ml_bear_trap.py          # ML-enhanced backtest
```

---

## 🚀 **Quick Start (Next Session)**

### **To Begin:**
1. Run Bear Trap on 2020-2024, save all trades to CSV
2. Manually label ~50 trades (ADD_ALLOWED, NO_ADD, NEUTRAL)
3. Extract features for those 50 trades
4. Train simple decision tree
5. Test on held-out trades
6. If promising, scale up

### **Expected Timeline:**
- **Week 1:** Label data, extract features
- **Week 2:** Train model, validate
- **Week 3:** Backtest ML-enhanced version
- **Week 4:** Compare vs baseline, decide deployment

---

## 💡 **Why This Will Work**

1. **ML isn't predicting price** - Just regime (easier)
2. **Small decision space** - 3 classes, not continuous
3. **Validated baseline** - Bear Trap already works
4. **Clear features** - ADX, ATR, volume (proven indicators)
5. **Interpretable** - Can inspect decision tree rules
6. **Fail-safe** - Defaults to NORMAL if unsure

---

## ⚠️ **What Could Go Wrong**

1. **Overfitting** - Keep model simple (max_depth=3)
2. **Look-ahead bias** - Only use data BEFORE entry
3. **Too few samples** - Need 100+ labeled trades minimum
4. **Regime changes** - 2020-2023 may not predict 2024

**Mitigation:**
- Cross-validation
- Out-of-sample testing
- Simple features
- Walk-forward validation

---

## 🎯 **Expected Improvement**

**Conservative Estimate:**
- Baseline: +17.59% (December 2024)
- ML-Enhanced: +20-25% (better position sizing)
- Sharpe: +20-30% improvement

**Why?**
- Avoid scaling in choppy markets (reduce losses)
- Aggressive in trends (maximize winners)
- Early exits in reversions (lock profits)

---

**This is a GAME CHANGER if executed properly!** 🚀

Want me to start building this framework?
