V2: ML Deployment Options for Your Validated Strategy Stack
Core Deployment Principle

Keep existing strategy entry/exit logic unchanged.

Use ML to condition risk, not to generate signals.

ML outputs should map to deterministic actions (size, skip, exposure caps).

ML Insertion Points
1) Post-Signal Trade Quality Scoring (Gate)

Where

Immediately after a rule-based entry signal is produced and before order placement.

How

Compute a feature vector at decision time.

ML model outputs a score used to:

approve the trade,

skip the trade,

or reduce size.

Output Forms

p_win (probability trade finishes positive)

p_tail_loss (probability of large adverse move)

E[return] (expected return over holding window)

risk_score in [0,1] (lower = riskier)

Deterministic Policy Examples

Skip trade if p_tail_loss > threshold

Reduce size if risk_score < 0.4

Full size if risk_score >= 0.7

Best Fit

Hourly Swing (most sensitive to micro-friction and regime changes)

Daily Trend (optional, lower urgency)

2) Dynamic Position Sizing (Risk Multiplier)

Where

After signal validation, before position sizing is finalized.

Can be applied per-asset and/or portfolio-wide.

How

ML predicts risk over the trade’s expected holding period.

Convert prediction to a size multiplier.

Output Forms

size_multiplier ∈ [0, 1]

vol_forecast (conditional volatility forecast)

MAE_forecast (max adverse excursion forecast)

stop_hit_prob

Deterministic Policy Examples

position_size = base_size * size_multiplier

If stop_hit_prob > 0.35, cap size at 0.5x

If MAE_forecast exceeds configured limit, reduce size or skip

Best Fit

Daily Trend (reduce drawdown during chop/regime shift)

Hourly Swing (reduce risk during high-toxicity sessions)

Options (size per event, not continuous)

3) Regime Confidence Scoring (Strategy Throttle)

Where

Portfolio layer above all strategies.

Evaluated daily (Daily Trend / Earnings) and intraday (Hourly Swing).

How

ML estimates how similar current conditions are to historical “good” regimes for the strategy.

Output gates new entries and/or reduces exposure.

Output Forms

regime_confidence ∈ [0,1]

good_regime_prob

drawdown_risk_prob

Deterministic Policy Examples

If regime_confidence < 0.3: no new entries

If 0.3 ≤ regime_confidence < 0.6: half size

If regime_confidence ≥ 0.6: normal size

Best Fit

Daily Trend (trend persistence varies by regime)

Hourly Swing (intraday volatility / mean reversion regimes)

Earnings (quarter-to-quarter variance)

FOMC (minimal value relative to fixed rules)

4) Event Options: Execution/Risk Conditioning (Not Direction)
4A) FOMC Straddles

Where

Pre-event sizing decision layer.

How

ML predicts execution and tail risk around the event, not direction.

Output adjusts event allocation and/or enforces no-trade thresholds.

Output Forms

spread_risk_score

iv_environment_score

liquidity_risk_prob

Deterministic Policy Examples

Reduce event capital if spread_risk_score below threshold

Skip if predicted spreads exceed configured maximum

4B) Earnings Straddles

Where

Pre-entry sizing and ticker selection layer.

How

ML predicts earnings “environment” and tail-move likelihood.

Output adjusts size and/or which tickers are eligible.

Output Forms

tail_move_prob

expected_move_ratio (realized/IV expectation)

event_risk_score

Deterministic Policy Examples

Full size only if tail_move_prob above threshold

Skip if event_risk_score indicates high IV crush / low realized move likelihood

Recommended ML Targets (What to Predict)
Equity Strategies

MAE over holding window (risk)

stop_hit_prob

conditional_volatility

p_tail_loss (loss beyond a configured cutoff)

expected_return (optional; higher overfit risk than MAE/vol)

Options Event Strategies

spread_width_forecast (execution risk proxy)

realized_move_vs_IV expectation

tail_move_prob (large post-event move likelihood)

Feature Sets (What to Use)
Universal Features

ATR percentile / volatility percentile

realized volatility (short/medium lookbacks)

gap size vs ATR

trend strength metrics (returns over multiple horizons)

correlation spikes (portfolio-level)

drawdown state (strategy and portfolio)

time-of-day / day-of-week

proximity to major macro events (calendar flags)

Strategy-Specific Features

RSI value and distance to bands

hysteresis state (hold zone vs boundary crossings)

time since last signal change

current position duration / time in trade

recent signal flip frequency (chop indicator)

Model Families (Practical Choices)

Gradient-boosted trees (XGBoost/LightGBM/CatBoost)

Regularized logistic regression (baseline gate model)

Quantile regression (predict MAE/vol percentiles)

Calibrated probability models (Platt/Isotonic calibration)

Deployment Architecture Pattern
Shared ML Risk Module (Recommended)

One ML service/module produces:

risk_score

size_multiplier

regime_confidence

Strategies consume outputs deterministically.

Logging includes:

features snapshot

ML outputs

final action taken (trade/skip/size)

realized outcomes for retraining

Validation Requirements for ML Additions

Walk-forward training and evaluation (time-split)

Perturbation on:

feature noise

1-bar decision delay (intraday)

slippage/spread stress (options)

“Remove best year” robustness check

Ablation:

baseline strategy vs strategy+ML gate vs strategy+ML sizing

Calibration verification for probabilities (Brier score / reliability curve)

V2 Rollout Sequence

Implement ML position sizing for Hourly Swing (highest sensitivity).

Add ML regime throttle for Daily Trend (reduce chop drawdown).

Add ML earnings environment score for Earnings Straddles (ticker/size conditioning).

Optional: ML gate for Daily Trend (only if it materially reduces tail losses without collapsing trade count).