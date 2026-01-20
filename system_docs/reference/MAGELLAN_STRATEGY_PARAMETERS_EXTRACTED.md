# Magellan Strategy Rules & Parameters (Extracted)

Source: `TESTING_ASSESSMENT_MASTER.md`  
Scope: **Rules, parameters, and asset coverage only** (no results, no rankings).

---

## Strategy 1 — Daily Trend Hysteresis (Long-Only)

**Logic / Indicator**
- RSI(28) hysteresis bands: **55 / 45**
- Entry: RSI crosses **above 55**
- Exit: RSI crosses **below 45**

**Timeframe**
- **Daily bars**

**Direction**
- **Long-only**

**Assets to Test (per document)**
- **Equities (MAG7 focus):**
  - AAPL
  - MSFT
  - NVDA
  - META
  - AMZN
  - GOOGL
  - TSLA
- **ETFs:**
  - SPY
  - QQQ
- **Crypto (spot proxies):**
  - BTC-USD
  - ETH-USD

---

## Strategy 2 — Hourly Swing (Long-Only)

**Logic / Indicator**
- RSI(28) hysteresis bands: **60 / 40**
- Entry: RSI crosses **above 60**
- Exit: RSI crosses **below 40**

**Timeframe**
- **Hourly bars**

**Direction**
- **Long-only**

**Assets to Test (per document)**
- **Equities (liquid large-cap):**
  - AAPL
  - MSFT
  - NVDA
  - META
  - AMZN
  - TSLA
- **Futures:**
  - ES (S&P 500)
  - NQ (Nasdaq 100)
  - CL (Crude Oil)
  - GC (Gold)
  - SI / MSI (Silver / Micro Silver)

---

## Strategy 3 — Earnings Volatility (Equity, Event-Driven)

**Logic**
- Buy **equity** 2 trading days **before earnings**
- Sell **equity** 1 trading day **after earnings**

**Timeframe**
- **Event-based** (quarterly earnings)

**Direction**
- **Long-only**

**Assets to Test (per document)**
- **Tier 1 (Primary focus):**
  - TSLA
  - NVDA
  - GOOGL
- **Tier 2:**
  - AAPL
- **Tier 3:**
  - META
  - MSFT
  - AMZN
  - NFLX
  - AMD
  - COIN
  - PLTR

---

## Strategy 4 — FOMC Event Volatility (Equity / Index, Event-Driven)

**Logic**
- Buy **equity proxy** 5 minutes **before FOMC**
- Sell **equity proxy** 5 minutes **after FOMC**
- Hold time: ~10 minutes

**Timeframe**
- **Event-based** (8 scheduled FOMC meetings per year)

**Direction**
- **Long-only**

**Assets to Test (per document)**
- **Primary instrument:**
  - SPY
- **Secondary (for robustness, if data allows):**
  - QQQ

---

## Data Sources (as stated in document)

- **Equities / ETFs:** Alpaca Markets (SIP feed)
- **Futures / Commodities / Crypto:** FMP API
- **Event calendars:** Earnings calendars + FOMC schedule

---

## Methodological Constraints (Document-Stated)

- Walk-Forward Analysis (WFA)
- Regime separation (bull / bear / sideways)
- Slippage stress tests (baseline and degraded)
- Strict out-of-sample validation

---

## Portfolio Guardrails (Document-Stated)

- Max **10–15%** allocation per instrument (except event strategies)
- Max **50%** exposure to futures
- Max **15%** exposure to hourly strategies
- Maintain **5% cash reserve**
