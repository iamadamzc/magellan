# PROMPT FOR NEXT AGENT

Copy and paste this to the next agent:

---

**PROJECT**: Magellan Trading System - Strategy Validation & Canonization

**YOUR TASK**: Continue validating and canonizing the remaining 2 trading strategies (FOMC Event Straddles and Earnings Straddles) using the exact same process established in the previous session.

**HANDOFF DOCUMENT**: Read `STRATEGY_VALIDATION_HANDOFF.md` in the project root - it contains everything you need.

**CONTEXT**: 
- 2 of 4 strategies have been validated and canonized (Daily Trend Hysteresis, Hourly Swing Trading)
- Critical bugs in the backtester have been fixed (data resolution, warmup buffer, date range)
- All strategies are located in `docs/operations/strategies/`
- Each strategy has a README, backtest script, and results CSV

**YOUR OBJECTIVES**:

1. **Test FOMC Event Straddles** (Options strategy)
   - Claims: +102.7% annual return, Sharpe 1.17
   - Challenge: Requires options data (may not be available)
   - If options data unavailable, document and defer to paper trading

2. **Test Earnings Straddles** (Options strategy)
   - Claims: +79.1% annual return, Sharpe 2.25
   - Same challenge as FOMC

3. **Canonize Results**
   - Create directory: `docs/operations/strategies/[strategy_name]/`
   - Add README.md (strategy guide)
   - Add backtest.py (validation test)
   - Add results.csv (validated results)

4. **Update Main README**
   - Add links to all 4 strategies
   - Update status (2/4 complete → 4/4 complete)

**PROCESS TO FOLLOW**:

See `STRATEGY_VALIDATION_HANDOFF.md` Section: "THE VALIDATION PROCESS (FOLLOW EXACTLY)"

**EXAMPLES TO REFERENCE**:
- `docs/operations/strategies/daily_trend_hysteresis/` - Full example with 11 assets
- `docs/operations/strategies/hourly_swing/` - Simpler example with 2 assets

**CRITICAL NOTES**:
- DO NOT modify the bug fixes in `src/backtester_pro.py` or `main.py`
- Always verify data resolution (daily should be ~500 bars, not 300,000+)
- Test on 2024-2025 data (2 full years minimum)
- Compare actual results to claimed results

**EXPECTED BLOCKER**:
Options strategies require historical options data. Check if Alpaca provides this. If not, document the strategies as "requires options data for validation" and recommend paper trading validation instead.

**SUCCESS CRITERIA**:
- All 4 strategies tested and documented
- Each strategy has its own directory under `docs/operations/strategies/`
- Main README updated
- All work committed with clear commit messages

**QUESTIONS?** Everything is in `STRATEGY_VALIDATION_HANDOFF.md`

Start by reading that document thoroughly, then begin with FOMC Event Straddles.

---

**END OF PROMPT**
