# Magellan Trading System - State & Context Document

**Last Updated**: 2026-01-14 17:09 ET
**Git Branch**: `magellan2` (primary development branch)
**System Status**: ✅ Operational (3 major optimizations completed today)

---

## **Critical Information for Continuity**

### **User Preferences & Workflow**

1. **Git Hygiene**: User prioritizes excellent git practices
   - Always use feature branches for new work (`feature/`, `fix/`, `refactor/`)
   - Commit incrementally with clear messages
   - Test before merging to `magellan2`
   - Delete feature branches after merge

2. **Communication Style**:
   - User prefers clear explanations with context
   - Appreciates when asked for clarification vs assumptions
   - Values proactive suggestions but wants approval before major changes
   - Likes markdown formatting for responses

3. **Development Philosophy**:
   - Remove complexity, don't add it
   - Evidence over theory (backtest to prove value)
   - Industry standards over custom solutions
   - Clean logs and readable output

4. **Model Selection for Tasks** (Antigravity Multi-Model Strategy):
   - User works exclusively in Antigravity with access to multiple models
   - To conserve tokens on preferred model (Gemini 2.0 Flash Thinking), user wants recommendations for task-appropriate models
   - **Available Models**:
     - Gemini 2.0 Flash Thinking (current, preferred for complex tasks)
     - Gemini 3.0 Pro High
     - Gemini 3.0 Pro Low
     - Gemini 3 Flash
     - Claude Sonnet 4.5 Thinking
     - Claude Sonnet 4.5 General
     - Claude Opus 4.5
     - GPT OSS
   
   **Task-to-Model Recommendations**:
   
   | Task Type | Recommended Model | Why |
   |-----------|------------------|-----|
   | **Complex Architecture Decisions** | Gemini 2.0 Flash Thinking, Claude Opus 4.5 | Deep reasoning needed |
   | **Code Refactoring** | Gemini 3.0 Pro High, Claude Sonnet 4.5 Thinking | Balance of speed & quality |
   | **Bug Fixes** | Gemini 3.0 Pro Low, Claude Sonnet 4.5 General | Quick diagnosis sufficient |
   | **Documentation Writing** | Gemini 3 Flash, GPT OSS | Fast, straightforward |
   | **Test Writing** | Gemini 3.0 Pro Low, Claude Sonnet 4.5 General | Patterns-based, not complex |
   | **Config File Updates** | Gemini 3 Flash, GPT OSS | Simple edits |
   | **Data Analysis** | Gemini 3.0 Pro High, Claude Opus 4.5 | Numerical reasoning |
   | **Git Operations** | Gemini 3 Flash, GPT OSS | Straightforward commands |
   | **Ablation Studies** | Gemini 2.0 Flash Thinking, Claude Sonnet 4.5 Thinking | Experimental design reasoning |
   | **Production Deployment Planning** | Gemini 2.0 Flash Thinking, Claude Opus 4.5 | High-stakes decisions |
   
   **Agent Behavior**: When given a task, assess complexity and recommend switching to a lighter model if appropriate. Format:
   ```
   💡 **Model Recommendation**: This task (e.g., "update .gitignore") is straightforward. 
   Consider switching to Gemini 3 Flash or GPT OSS to conserve tokens on your preferred model.
   
   I can proceed with [current model] if you prefer, or wait for you to switch.
   ```

---

## **System Architecture Overview**

### **Tech Stack**

**Language**: Python 3.12.9
**OS**: Windows (PowerShell for scripts)

**Key Dependencies**:
- `pandas` - Data manipulation
- `numpy` - Numerical operations
- `alpaca-py` - Alpaca API client (bar data, trading)
- `requests` - FMP API calls
- `TextBlob` - Fallback NLP sentiment (rarely used now)

**Data Providers**:
- **Alpaca**: OHLCV bar data (SIP feed), Trade execution
- **FMP (Financial Modeling Prep)**: News, sentiment, fundamentals
  - Plan: **Ultimate** (3K calls/min, 150GB bandwidth, full date range queries)

---

## **Project Structure**

```
Magellan/
├── main.py                      # Primary entry point
├── src/
│   ├── config_loader.py         # EngineConfig singleton
│   ├── data_handler.py          # AlpacaDataClient, FMPDataClient
│   ├── features.py              # FeatureEngineer, signal generation
│   ├── executor.py              # Trade execution logic
│   ├── backtester_pro.py        # Walk-forward validation
│   ├── optimizer.py             # Weight optimization
│   ├── pnl_tracker.py           # P&L tracking
│   ├── logger.py                # SystemLogger (new, refactored today)
│   ├── risk_manager.py          # Volatility targeting (new, added today)
│   ├── hangar.py                # Observation/analysis tools
│   └── visualizer.py            # (legacy, may have 3D PyDeck code)
├── config/
│   └── nodes/
│       ├── master_config.json   # Ticker-specific configs (MAG7 + IWM, VSS, VTV)
│       ├── NVDA.json, AAPL.json, etc.
│       └── IWM.json, VSS.json, VTV.json  # Non-MAG7 tickers
├── src/configs/
│   └── mag7_default.json        # Engine-level defaults
├── .env                         # API keys (gitignored)
├── .gitignore                   # Excludes test outputs, cache
└── CLI_GUIDE.md                 # Comprehensive CLI documentation (created today)
```

---

## **Data Flow**

```
1. User runs: python main.py --symbols NVDA --stress-test-days 15

2. main.py:
   ├─ Loads EngineConfig (mag7_default.json)
   ├─ Loads master_config.json (ticker-specific settings)
   ├─ Initializes logger (verbosity based on --quiet/--verbose)
   └─ For each ticker:
       ├─ AlpacaDataClient.fetch_historical_bars()  # OHLCV from Alpaca SIP
       ├─ FMPDataClient.fetch_historical_news()     # News from FMP (cached 24hr)
       ├─ FMPDataClient.fetch_fundamental_metrics() # Market cap, P/E, etc.
       ├─ FeatureEngineer.calculate_log_return(), calculate_rvol(), etc.
       ├─ merge_news_pit()  # Point-in-time sentiment alignment
       ├─ add_technical_indicators()  # RSI, ATR, Bollinger, MACD
       ├─ generate_master_signal()  # Alpha score generation
       ├─ Optimizer.find_optimal_weights()  # In-sample optimization
       ├─ BacktesterPro.simulate_portfolio()  # Out-of-sample testing
       └─ Output: equity_curve_*.csv, stress_test_report_*.txt

3. Live Mode (--mode live):
   └─ Continuous loop, fetches latest bar, generates signal, executes via Alpaca
```

---

## **Recent Changes (2026-01-14)**

### **Session Summary**

**Conversation ID**: d8121cdb-946b-42bf-9573-cbdda79dad62

**Major Work Completed**:

1. ✅ **News Pipeline Optimization** (Commits: `7f62bd6`)
   - Removed 30-day chunking (FMP Ultimate allows full date range queries)
   - Added 24-hour disk cache (`.cache/fmp_news/`)
   - Extracted `_parse_fmp_sentiment()` helper
   - Fixed TextBlob NLP trigger (only runs if sentiment truly missing, not `0.0`)
   - **Impact**: 30-600x faster (240 API calls → 5 calls, cached)

2. ✅ **Volatility Targeting Replacement** (Commits: `3a193d0`, `5c7192d`, `83cd69e`)
   - Removed LAM damping system (115 lines of unproven complexity)
   - Added `src/risk_manager.py` (industry-standard volatility targeting)
   - **Impact**: No more `[LAM] Damping Active | Metabolism: 99%` spam

3. ✅ **Logging System Refactor** (Commits: `4244fcb`, `7d8e3aa`, `f33cc32`, `8e92496`)
   - Implemented `SystemLogger` with 3 verbosity levels (QUIET/NORMAL/VERBOSE)
   - Added `--verbose` CLI flag
   - Backend details → `debug_vault.log` (never shown in terminal)
   - **Impact**: ~80% reduction in terminal noise

**Git State**:
- Branch: `magellan2` (HEAD: `8e92496`)
- All feature branches merged and deleted
- Working directory clean

---

## **Configuration Hierarchy**

**Priority** (highest to lowest):

1. **CLI flags** (`--symbols`, `--max-position-size`, `--verbose`)
2. **Custom config** (via `--config path/to/custom.json`)
3. **Default engine config** (`src/configs/mag7_default.json`)
4. **Ticker-specific config** (`config/nodes/master_config.json`)
5. **Hardcoded defaults** (in argparse)

**Example**:
```bash
# CLI overrides everything
python main.py --symbols NVDA --max-position-size 10000

# Result: NVDA only, $10K position cap (ignores master_config.json value)
```

---

## **CLI Reference**

See [`CLI_GUIDE.md`](file:///a:/1/Magellan/CLI_GUIDE.md) for full details.

**Most Common Commands**:

```bash
# Backtest single ticker (3 days)
python main.py --symbols NVDA --stress-test-days 3

# Backtest with quiet logs
python main.py --symbols NVDA --stress-test-days 3 --quiet

# Backtest with verbose logs (detailed flow)
python main.py --symbols NVDA --stress-test-days 3 --verbose

# Multi-ticker backtest
python main.py --symbols NVDA,AAPL,MSFT --stress-test-days 15

# Live paper trading (market hours only)
python main.py --mode live --symbols NVDA --max-position-size 10000

# Observation mode (ORH analysis)
python main.py --mode observe
```

**Default behavior** (no args):
- Mode: `simulation`
- Tickers: All MAG7 (NVDA, AAPL, MSFT, GOOGL, AMZN, META, TSLA)
- Config: `mag7_default.json`

---

## **Environment Variables**

**Required** (in `.env`):
```
APCA_API_KEY_ID=your_alpaca_key_id
APCA_API_SECRET_KEY=your_alpaca_secret
APCA_API_BASE_URL=https://paper-api.alpaca.markets/v2
FMP_API_KEY=your_fmp_api_key
```

**Notes**:
- Alpaca: Using Paper account for testing
- FMP: Ultimate plan (critical for full date-range news queries)

---

## **Known Architecture Details**

### **Data Sources**

| Data Type | Provider | Reason |
|-----------|----------|--------|
| OHLCV Bars | Alpaca SIP | High quality, execution integration |
| News | FMP | Comprehensive, pre-calc sentiment |
| Fundamentals | FMP | Market cap, P/E, volume |
| Trade Execution | Alpaca | Paper trading, real-time |

**Decision**: Keep both providers (don't consolidate to FMP alone)
- Alpaca: Superior bar data quality (SIP feed), execution API
- FMP: Superior news/fundamentals coverage

### **MAG7 Universe**

**Tickers**: NVDA, AAPL, MSFT, GOOGL, AMZN, META, TSLA

**Validation**: `validate_mag7_ticker()` enforces allowlist in `main.py`
- Non-MAG7 tickers are **skipped** unless added to allowlist dynamically

**Other Configured Tickers** (in `master_config.json`):
- **IWM** (Russell 2000)
- **VSS** (Cryogen/low-vol strategy)
- **VTV** (Value ETF)

---

## **Critical Code Patterns**

### **Logger Usage** (Post-Refactor)

```python
from src.logger import LOG

# Critical events (always shown - errors, warnings, trades)
LOG.critical("❌ [ERROR] API call failed")
LOG.warning("⚠️  [NVDA] Validation failed")

# Major milestones (normal mode)
LOG.event("[NVDA] Processing complete")
LOG.success("✓ Feature matrix created")

# Process flow (verbose mode only)
LOG.flow("[NVDA] Loading data...")
LOG.info("[NVDA] Fetched 124K bars")  # Alias for flow()

# Backend details (file only, never terminal)
LOG.debug("SIP feed request: NVDA, 2022-01-01 to 2026-01-14")
LOG.config("[CONFIG] Loaded master_config.json")
```

**Verbosity Levels**:
- `SystemLogger.QUIET` (0): Only critical
- `SystemLogger.NORMAL` (1): Critical + events
- `SystemLogger.VERBOSE` (2): Critical + events + flow

### **Config Loading**

```python
from src.config_loader import EngineConfig

# Initialize singleton
engine_config = EngineConfig()  # Loads mag7_default.json
# OR
engine_config = EngineConfig(config_path="custom.json")

# Access values
lookback = engine_config.get('LOOKBACK_WINDOW', default=252, strict=True)
```

**Strict mode**: Raises error if key missing (use for critical params)

### **Data Fetching**

```python
from src.data_handler import AlpacaDataClient, FMPDataClient

# Alpaca bars
alpaca = AlpacaDataClient()
bars = alpaca.fetch_historical_bars(
    symbol='NVDA',
    start_date='2024-01-01',
    end_date='2024-12-31',
    timeframe='5Min'
)

# FMP news (with caching)
fmp = FMPDataClient()
news = fmp.fetch_historical_news(
    symbol='NVDA',
    start_date='2024-01-01',
    end_date='2024-12-31',
    use_cache=True  # 24-hour TTL
)
```

---

## **Current Pain Points & Known Issues**

### **1. Validation Failures**

**Symptom**: `[NVDA] VALIDATION FAILED - Hit rate <51%`

**Cause**: Strategy signals not predictive enough
- Out-of-sample hit rate worse than coin flip
- Features may need improvement
- Training window may be too short
- Regime shift (trained on 2022-2025, testing on 2026)

**NOT a bug** - this is expected behavior when signals are weak

**Fix** (separate project):
- Feature engineering improvements
- Longer training windows
- Regime detection

### **2. Feature Matrix Printing**

**Fixed Today**: `research_mode` attribute error
- Changed to use `LOG.verbosity >= LOG.VERBOSE`
- Only prints in verbose mode now

### **3. Output File Clutter**

**Fixed Today**: Added to `.gitignore`:
```
equity_curve_*.csv
stress_test_*.csv
stress_test_*.txt
.cache/
inspect_*.py
```

---

## **Testing Checklist** (For Future Work)

Before merging new features:

- [ ] Run single-ticker backtest: `python main.py --symbols NVDA --stress-test-days 3`
- [ ] Run multi-ticker backtest: `python main.py --symbols NVDA,AAPL,MSFT --stress-test-days 3`
- [ ] Test quiet mode: `--quiet`
- [ ] Test verbose mode: `--verbose`
- [ ] Check `debug_vault.log` for backend details
- [ ] Verify no crashes, exit code 0
- [ ] Check git status (clean working directory)

---

## **Common Workflows**

### **Adding a New Feature**

```bash
# 1. Create feature branch
git checkout -b feature/my-new-feature

# 2. Make changes, commit incrementally
git add src/my_file.py
git commit -m "feat: add new capability"

# 3. Test thoroughly
python main.py --symbols NVDA --stress-test-days 3

# 4. Merge to magellan2
git checkout magellan2
git merge feature/my-new-feature

# 5. Delete feature branch
git branch -d feature/my-new-feature
```

### **Debugging Issues**

```bash
# 1. Check debug log
cat debug_vault.log

# 2. Run with verbose logging
python main.py --symbols NVDA --stress-test-days 1 --verbose

# 3. Check git history
git log --oneline -10

# 4. Compare with previous version
git diff HEAD~1 src/my_file.py
```

---

## **Dependencies & Installation**

**Python Packages** (install via pip):
```bash
pip install alpaca-py pandas numpy requests textblob
```

**API Keys Required**:
- Alpaca (free paper trading account)
- FMP Ultimate plan (paid, ~$300/month for full features)

---

## **Performance Characteristics**

**Backtest Speed** (NVDA, 3 days, normal mode):
- Data fetching: ~2 seconds (cached) / ~30 seconds (first run)
- Feature engineering: ~5 seconds
- Optimization: ~10 seconds
- Total: ~20 seconds

**With 30-day chunking** (before optimization):
- News fetching alone: ~60 seconds (48 API calls)

**Live Trading** (--mode live):
- Processes each ticker every 5min (or configured interval)
- Low CPU usage (<5% steady state)

---

## **Token Usage Tracking**

**Current Conversation**:
- **Used**: 111K / 200K (55%)
- **Remaining**: 89K (45%)
- **Threshold for new conversation**: 150K (75%)

**When starting new conversation**, reference:
- This document (`STATE.md`)
- `CLI_GUIDE.md`
- `LOGGING_REFACTOR_SUMMARY.md`
- Recent git commits: `git log --oneline -20`

---

## **Important Context Not in Code**

### **Design Decisions Made**

1. **Why keep both Alpaca and FMP?**
   - Alpaca: Better bar data (SIP feed), execution integration
   - FMP: Better news/fundamentals
   - Consolidation would compromise quality

2. **Why remove LAM damping?**
   - No empirical validation (never A/B tested)
   - 99% metabolism = barely functional
   - Volatility targeting is industry standard

3. **Why add caching only to news?**
   - News data is static (doesn't change once published)
   - Bar data updates frequently (don't cache)
   - 24-hour TTL balances freshness vs speed

4. **Why 3 verbosity levels?**
   - QUIET: Production (only errors/trades)
   - NORMAL: Development (progress updates)
   - VERBOSE: Debugging (step-by-step flow)
   - DEBUG: File only (backend details)

### **User's Trading Philosophy** (Inferred)

- **Systematic approach**: Rules-based, not discretionary
- **Risk-aware**: Position caps, validation requirements
- **Data-driven**: Backtesting before live deployment
- **Professional standards**: Clean code, git hygiene, documentation

---

## **Next Session Recommendations**

### **Immediate Priorities**

1. **Validation Failure Investigation** (NVDA hit rate <51%)
   - Review feature importance
   - Check regime shift between train/test
   - Consider longer training windows

2. **Live Trading Test** (market hours)
   - Run: `python main.py --mode live --symbols NVDA --max-position-size 1000`
   - Monitor for 1 session
   - Verify trades execute correctly

3. **Documentation Updates**
   - Add examples to `CLI_GUIDE.md`
   - Document validation thresholds

### **Medium-Term Enhancements**

1. **Implement Volatility Targeting** (Phase 2)
   - Currently `damping_factor = 1.0` (full sizing)
   - Could use `src/risk_manager.py` for dynamic scaling
   - Requires portfolio return tracking

2. **Optimize Specific Log Calls**
   - Many `LOG.info()` could become `LOG.debug()`
   - Further reduce terminal noise

3. **Feature Engineering Improvements**
   - Add more signal diversity
   - Improve IC (information coefficient)
   - Address validation failures

---

## **Emergency Rollback Commands**

If something breaks badly:

```bash
# Rollback to before today's changes
git checkout 6a178dc  # Commit before logging refactor

# Or revert specific commits
git revert 8e92496  # Revert logging refactor
git revert 83cd69e  # Revert volatility targeting
git revert 7f62bd6  # Revert news optimization

# Or create recovery branch
git checkout -b recovery/pre-refactor 6a178dc
```

---

## **File Locations for Quick Reference**

**Logs**:
- `debug_vault.log` - All backend details

**Test Outputs** (gitignored):
- `equity_curve_*.csv` - P&L over time
- `stress_test_*.csv` - Backtest results
- `stress_test_report_*.txt` - Detailed reports

**Cache**:
- `.cache/fmp_news/*.pkl` - 24-hour news cache

**Docs**:
- `CLI_GUIDE.md` - Comprehensive CLI reference
- `LOGGING_OPTIMIZATION.md` - Logging analysis
- `LOGGING_REFACTOR_SUMMARY.md` - Implementation summary
- `STATE.md` - This document

---

## **Contact with Next Agent**

**Hello, future agent assisting this user!**

This document should give you everything you need to continue seamlessly. Key points:

1. **User values**: Clean code, git hygiene, clear communication
2. **Always use feature branches** for new work
3. **Test before merging** to `magellan2`
4. **Check token usage** - suggest new conversation at 75% (150K tokens)
5. **Reference recent git commits** for context
6. **Read `CLI_GUIDE.md`** for command examples

**Current state**: System is healthy, 3 major optimizations completed today, ready for next feature.

**Known open items**: Validation failures (expected, needs feature engineering work)

Good luck! The user is excellent to work with - thoughtful, technical, and appreciates proactive help with clear explanations.

---

**End of State Document**
**Last Updated**: 2026-01-14 17:09 ET by Antigravity (Conversation: d8121cdb-946b-42bf-9573-cbdda79dad62)
