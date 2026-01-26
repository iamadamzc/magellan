# Bear Trap ML Model Upgrade Plan

## Goal
Upgrade the Bear Trap strategy's regime filter from a static Decision Tree to a dynamic XGBoost ensemble, incorporating continuous features and probability calibration as recommended by the expert review.

## 1. Environment Setup
- [x] Install `xgboost` (Done)
- [ ] Verify `scikit-learn` version for `CalibratedClassifierCV` compatibility.

## 2. Feature Engineering
Refactor feature extraction to use raw continuous values instead of binning.

| Old Feature (Binned) | New Feature (Continuous) | Transformation |
|----------------------|--------------------------|----------------|
| `time_score` (Bool) | `time_sin`, `time_cos` | Cyclical encoding of `entry_hour` + `entry_minute` |
| `high_volume` (Bool) | `volume_ratio` | Raw float value from `labeled_regimes_v2.csv` |
| `big_drop` (Bool) | `day_change_pct` | Raw float value |
| `high_volatility` (Bool)| `atr_percentile` | Raw float value |
| *New* | `volatility_volume_ratio` | `atr_percentile` / `volume_ratio` (Interaction) |

## 3. Model Architecture
- **Algorithm**: `XGBClassifier` (Gradient Boosting).
- **Objective**: Binary Classification (`binary:logistic`).
- **Calibration**: `CalibratedClassifierCV` (Isotonic or Sigmoid) to output true probabilities.
- **Validation Strategy**: Stratified K-Fold Cross Validation to ensure robustness.

## 4. Implementation Steps
1.  **Create `scripts/train_enhanced_model.py`**:
    - Load `labeled_regimes_v2.csv`.
    - engineered features (`time_sin`, `time_cos`, interactions).
    - Train XGBoost model.
    - Calibrate probabilities.
    - Save model as `models/bear_trap_enhanced_xgb.pkl`.
    - Output performance report (AUC-ROC, LogLoss, Precision/Recall).

2.  **Create `scripts/compare_old_vs_new.py`**:
    - Load both models (`bear_trap_entry_only_classifier.pkl` vs `bear_trap_enhanced_xgb.pkl`).
    - Run on the same hold-out test set.
    - Compare:
        - Accuracy vs "Neutral" ambiguity.
        - PnL impact (simulated gating).

## 5. Deliverables
- `train_enhanced_model.py` script.
- `models/bear_trap_enhanced_xgb.pkl` artifact.
- `ENHANCED_MODEL_REPORT.md` summarizing findings.

## 6. User Review Required
- **Deployment logic**: The new model outputs probabilities (0.0-1.0). We need to define thresholds for `confidence`.
    - Recommendation: `> 0.6` = Scale In, `> 0.8` = Aggressive.
    - Current logic is discrete (`ADD_ALLOWED`). We will map `Prob > X` to `ADD_ALLOWED`.
