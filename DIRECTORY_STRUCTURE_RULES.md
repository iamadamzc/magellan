# Magellan Directory Structure Rules

**Version:** 2.0  
**Last Updated:** January 19, 2026  
**Status:** MANDATORY - All agents must review and adhere to these rules

---

## Core Principle

**The Magellan project maintains a clean, production-ready directory structure with strict separation of concerns. No exceptions.**

---

## Root Directory Rules

### ✅ ALLOWED in Root (10 Essential Files Only)

1. `.env` - Environment configuration
2. `.env.template` - Environment template
3. `.gitignore` - Git ignore rules
4. `README.md` - Project entry point
5. `ARCHIVE_INDEX.md` - Archive navigation
6. `DIRECTORY_STRUCTURE_RULES.md` - This file
7. `main.py` - Application entry point
8. `requirements.txt` - Python dependencies
9. `simulate_all_strategies_december.py` - Legacy simulation script
10. Runtime logs: `debug_vault.log`, `livetradelog.txt`

### ❌ NEVER ALLOWED in Root

- **Session summaries** → Move to `system_docs/session_logs/`
- **Discovery logs** → Move to `system_docs/session_logs/`
- **Strategy guides** → Move to `system_docs/operations/` or `system_docs/reference/`
- **Architecture docs** → Move to `system_docs/architecture/`
- **Test scripts** → Move to `research/testing/`
- **Temporary files** → Delete or move to appropriate location
- **CSV result files** → Move to `research/testing/backtests/` or `research/testing/perturbations/`
- **Analysis documents** → Move to `research/analysis/`
- **Any .md file except README.md, ARCHIVE_INDEX.md, and this file**

---

## Directory Structure Standards

### `/deployable_strategies/` - Production-Ready Strategy Code

**Purpose:** Contains only validated, deployment-ready strategy implementations and their core documentation.

**Structure:**
```
/deployable_strategies/
├── {strategy_name}/
│   ├── {strategy_name}_strategy.py          # Main implementation
│   ├── backtest_portfolio.py                # Optional: Portfolio backtester
│   ├── parameters_{strategy_name}.md        # Parameter specification
│   ├── README.md                            # Strategy overview
│   ├── VALIDATION_REPORT.md                 # Validation results (optional)
│   ├── {STRATEGY_NAME}_DEPLOYMENT_GUIDE.md  # Deployment guide (optional)
│   └── assets/                              # Per-asset configurations
│       └── {SYMBOL}/
│           └── config.json
```

**Rules:**
- ✅ Only validated, tested strategy files
- ✅ One strategy per folder
- ✅ Asset configs in `assets/` subfolder
- ❌ No test scripts (those go in `research/testing/`)
- ❌ No experimental code
- ❌ No duplicate files

**Current Strategies:**
1. `bear_trap/` - Bear Trap momentum scalping
2. `gsb/` - Gap Squeeze Breakout
3. `daily_trend_hysteresis/` - Daily trend following with hysteresis
4. `earnings_straddles/` - Earnings event straddles
5. `fomc_straddles/` - FOMC event straddles
6. `hourly_swing/` - Hourly swing trading

---

### `/system_docs/` - Centralized System Documentation

**Purpose:** All architectural, operational, and reference documentation.

**Structure:**
```
/system_docs/
├── architecture/           # System architecture documents
├── operations/            # Operational guides and procedures
├── reference/             # Reference materials and compendiums
└── session_logs/          # Session summaries and discovery logs
```

**Rules:**
- ✅ All system-level documentation goes here
- ✅ Organize by category (architecture, operations, reference, session_logs)
- ❌ No code files
- ❌ No test results
- ❌ No temporary files

---

### `/research/` - Research, Testing, and Analysis

**Purpose:** All research activities, testing, and analysis work.

**Structure:**
```
/research/
├── testing/                    # All testing activities
│   ├── backtests/             # General backtesting
│   │   ├── {strategy_name}/   # Strategy-specific backtests
│   │   │   ├── clean_room/    # Clean room validation tests
│   │   │   └── *.csv          # Backtest results
│   │   └── batch_scripts/     # Batch testing scripts
│   ├── wfa/                   # Walk-Forward Analysis
│   │   └── {strategy_name}/
│   ├── perturbations/         # Robustness/sensitivity testing
│   │   ├── {strategy_name}/
│   │   │   └── validation_tests/
│   │   └── reports/           # Aggregate perturbation reports
│   └── ml/                    # ML-specific research
│       └── ml_position_sizing/
├── analysis/                  # Analysis and documentation
│   └── codebase_cleanup/
├── archived_research/         # Historical research (completed)
└── strategy_enhancements_v2/  # Ongoing strategy enhancements
```

**Rules:**
- ✅ All test files organized by test type (backtests, wfa, perturbations, ml)
- ✅ Strategy-specific subfolders within each test type
- ✅ Results stay with their test scripts
- ❌ No deployable strategy implementations (those go in `/deployable_strategies/`)
- ❌ No mixing of test types in same folder

---

### `/src/` - Core System Code

**Purpose:** Production system code only. No strategy implementations.

**Rules:**
- ✅ Core infrastructure only
- ✅ Shared utilities and libraries
- ❌ No strategy-specific code (strategies go in `/deployable_strategies/`)
- ❌ No test files
- ❌ No experimental code

---

### `/config/` - System Configuration

**Purpose:** System-wide configuration files.

**Rules:**
- ✅ System-level configs only
- ❌ No strategy-specific configs (those go in `/deployable_strategies/{strategy}/assets/`)

---

### `/scripts/` - Operational Scripts

**Purpose:** Operational maintenance and utility scripts.

**Rules:**
- ✅ Data prefetching, maintenance, utilities
- ❌ No strategy implementations
- ❌ No test scripts (those go in `/research/testing/`)

---

### `/docs/` - Strategy Operation Documentation

**Purpose:** Detailed operational documentation for strategies (legacy structure, being phased out in favor of `/deployable_strategies/` README files).

**Rules:**
- ✅ Keep existing structure for now
- ⚠️ New strategy docs should go in `/deployable_strategies/{strategy}/README.md`

---

### `/archive/` - Historical Archive

**Purpose:** Archived code, research, and documentation.

**Rules:**
- ✅ Historical content only
- ✅ Use `ARCHIVE_INDEX.md` for navigation
- ❌ No active development files

---

## Session Cleanup Protocol

### At End of Every Session

**MANDATORY:** Before completing any session, agents must:

1. **Scan Root Directory**
   ```powershell
   Get-ChildItem -Path . -File | Where-Object { $_.Name -notmatch '^(\.env|\.gitignore|README\.md|ARCHIVE_INDEX\.md|DIRECTORY_STRUCTURE_RULES\.md|main\.py|requirements\.txt|simulate_all_strategies_december\.py|debug_vault\.log|livetradelog\.txt)$' }
   ```
   - If any files found: Move to appropriate location or delete

2. **Check for Session Documents**
   - Session summaries → `system_docs/session_logs/`
   - Discovery logs → `system_docs/session_logs/`
   - Enhancement opportunities → `system_docs/session_logs/`

3. **Check for Misplaced Test Files**
   - Test scripts in root → `research/testing/`
   - CSV results in root → `research/testing/backtests/` or `research/testing/perturbations/`

4. **Check for Misplaced Documentation**
   - Strategy guides in root → `system_docs/operations/` or `deployable_strategies/{strategy}/`
   - Architecture docs in root → `system_docs/architecture/`
   - Reference docs in root → `system_docs/reference/`

5. **Verify No Duplicates**
   - Check for duplicate strategy files
   - Check for duplicate documentation
   - Remove older versions, keep latest validated files

---

## File Naming Conventions

### Strategy Files
- Main implementation: `{strategy_name}_strategy.py`
- Parameters: `parameters_{strategy_name}.md`
- Deployment guide: `{STRATEGY_NAME}_DEPLOYMENT_GUIDE.md`
- README: `README.md` (in strategy folder)

### Test Files
- Backtest scripts: `test_{strategy_name}_{test_type}.py` or `backtest_{description}.py`
- Results: `{strategy_name}_{test_type}_results.csv`
- Reports: `{TEST_TYPE}_REPORT.md` or `{STRATEGY_NAME}_{TEST_TYPE}_REPORT.md`

### Documentation
- System docs: `{TOPIC}_{DESCRIPTION}.md` (UPPERCASE for major docs)
- Session logs: `SESSION_SUMMARY_{YYYYMMDD}.md`
- Discovery logs: `DISCOVERY_LOG_{TOPIC}.md`

---

## Common Violations and Fixes

### ❌ Violation: Session summary in root
**Fix:** `move SESSION_SUMMARY_20260119.md system_docs\session_logs\`

### ❌ Violation: Test script in root
**Fix:** `move test_strategy.py research\testing\backtests\{strategy_name}\`

### ❌ Violation: Strategy guide in root
**Fix:** `move STRATEGY_GUIDE.md system_docs\operations\`

### ❌ Violation: CSV results in root
**Fix:** `move results.csv research\testing\backtests\{strategy_name}\`

### ❌ Violation: Duplicate strategy files
**Fix:** Compare dates, keep latest, delete older version

### ❌ Violation: Test files in `/deployable_strategies/`
**Fix:** `move deployable_strategies\{strategy}\test_*.py research\testing\backtests\{strategy}\`

---

## Agent Onboarding Checklist

Every agent starting a new session must:

- [ ] Read this document completely
- [ ] Review current root directory state
- [ ] Verify no extraneous files in root
- [ ] Understand the 4-tier structure:
  - `/deployable_strategies/` - Production code
  - `/system_docs/` - Documentation
  - `/research/` - Testing and research
  - `/src/` - Core infrastructure
- [ ] Know where to put new files based on type
- [ ] Commit to session cleanup before completing work

---

## Agent Offboarding Checklist

Before completing any session, agents must:

- [ ] Run root directory scan (see Session Cleanup Protocol)
- [ ] Move any session documents to `system_docs/session_logs/`
- [ ] Move any test files to `research/testing/`
- [ ] Move any documentation to appropriate `system_docs/` subfolder
- [ ] Verify no duplicate files exist
- [ ] Confirm root contains only the 10 allowed files
- [ ] Update this document if new rules are needed

---

## Enforcement

**These rules are MANDATORY and NON-NEGOTIABLE.**

- Agents must review this document at session start
- Agents must enforce these rules during their session
- Agents must clean up before session end
- Violations should be corrected immediately upon discovery

**Rationale:** A clean, organized codebase is essential for:
- Production deployment readiness
- Team collaboration
- Code maintenance
- Testing efficiency
- Professional standards

---

## Version History

**v2.0 - January 19, 2026**
- Complete reorganization after Phase 1 and Phase 2 cleanup
- Established 4-tier structure (deployable_strategies, system_docs, research, src)
- Retired docs/operations/strategies folder
- Added mandatory session cleanup protocol
- Defined strict root directory rules (10 files only)

**v1.0 - January 18, 2026**
- Initial structure after Phase 1 cleanup
- Basic directory organization rules
