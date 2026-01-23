# Scanner Upgrade: FMP Ultimate Integration Plan

## Executive Summary
This document outlines a phased roadmap to upgrade the **Momentum Scanner Pro** ("Scanner") by leveraging the **FMP Ultimate** and **Alpaca Algo Trader Plus** plans. The primary goal is to transition from basic data scraping (yfinance) to institutional-grade data feeds (FMP WebSockets, Transcripts, Insider Trading) to improve signal quality, speed, and catalyst detection.

---

## 1. News & Catalyst Engine (Major Upgrade)

**Current Status:**  
`news_bot.py` uses `yfinance` (polling) and simple keyword matching. It is slow, rate-limited, and misses deep context.

**FMP Ultimate Enhancement:**
*   **Real-time Streaming:** Replace polling with FMP **WebSocket API** for instant news delivery.
*   **Earnings Transcripts:** Use `/v4/earning_call_transcript` to scan full text of earnings calls for keywords (e.g., "guidance raised", "AI demand") rather than just headlines.
*   **Insider Trading:** Integrate `/v4/insider-trading` to flag "Cluster Buys" (multiple officers buying) as a high-conviction catalyst.

**Implementation Plan:**
1.  Create `FMPNewsStream` class to handle WebSocket connections.
2.  Build `TranscriptAnalyzer` to fetch and NLP-scan earnings calls for top gap candidates.
3.  Enhance `news_bot.py` to query FMP instead of yfinance.

---

## 2. Fundamental & "Smart Money" Data

**Current Status:**  
`gap_hunter.py` only fetches Float data. It misses institutional context.

**FMP Ultimate Enhancement:**
*   **Institutional Holdings (13F):** Use `/v4/institutional-ownership/symbol-ownership` to see if a gapper is being accumulated by top funds.
*   **ETF Exposure:** Use `/v3/etf-stock-exposure` to detect if a move is driven by ETF rebalancing flows.
*   **Float Accuracy:** Use `/v4/shares_float` for more precise tradable float numbers than basic quotes.

**Implementation Plan:**
1.  Update `enrich_float` in `gap_hunter.py` to also fetch **Institutional %** and **Short Interest**.
2.  Add a "Smart Money Score" to the ranking algorithm.

---

## 3. Intraday Data & 1-Minute Granularity

**Current Status:**  
`gap_hunter.py` calculates RVOL using Daily bars from Alpaca. This is effective but lacks intraday precision (e.g., "How heavy is the volume in the first 5 mins vs. history?").

**FMP Ultimate Enhancement:**
*   **1-Minute History:** Use `/v3/historical-chart/1min/{symbol}` to calculate **Intraday RVOL** profiles.
*   **Pre-Market Volume:** Accurately measure pre-market volume relative to historical pre-market averages (difficult with standard daily bars).

**Implementation Plan:**
1.  Modify `get_history_and_rvol` to request 1-minute bars for the top 10 candidates.
2.  Calculate "Opening Drive Strength" metric.

---

## 4. Economic Awareness (Risk Management)

**Current Status:**  
The scanner is unaware of macro events. It might flag a gap right before a CPI drop.

**FMP Ultimate Enhancement:**
*   **Economic Calendar:** Use `/v3/economic_calendar` to blacklist times around high-impact events (NFP, CPI, FOMC).

**Implementation Plan:**
1.  Add `MarketConditions` class.
2.  Check for "Red Folder" events within +/- 15 minutes of scan time.
3.  Display a warning in the Streamlit UI: "⚠️ HIGH IMPACT EVENT IMMINENT".

---

## 5. Reliability & Architecture

**Current Status:**  
Uses raw `requests` with manual error handling.

**FMP Enhancement:**
*   **FMP SDK:** Mitigate rate limit handling and connection reuse by adopting the official Python SDK.
*   **WebSockets:** Move from "Push Button to Scan" to "Always-On Monitor" (optional future state).

---

## Proposed Roadmap

### Phase 1: Catalyst Intelligence (High ROI)
- [ ] Replace `news_bot.py` internals with FMP `stock_news` and `sentiment`.
- [ ] Add **Insider Trading** flags to the UI.

### Phase 2: Data Precision
- [ ] Upgrade `gap_hunter.py` to use FMP for Share Float & Institutional Ownership.
- [ ] Implement Economic Calendar warnings.

### Phase 3: Intraday Alpha
- [ ] Implement 1-minute Intraday RVOL for sharper "Gap" scoring.
- [ ] Experiment with Transcript Analysis for earnings gappers.

---

**Next Steps:**
1. Approve this plan.
2. Begin Phase 1 by refactoring `news_bot.py`.
