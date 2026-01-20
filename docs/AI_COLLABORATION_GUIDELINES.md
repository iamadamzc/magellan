# AI-Assisted Development - Keeping Code Clean

**Based on lessons from Magellan cleanup (326 → 45 Python files)**

---

## The Problem We Just Solved

**Code sprawl from AI development:**
- 280+ test scripts (test_orb_v4, v5, v6... v12, analyze_*, debug_*, etc.)
- 12 research folders with failed experiments
- Root directory became a dumping ground (~100 files)
- Multiple duplicate files and handoffs
- No clear production vs experimental separation

**Result:** 91% of files were non-production clutter

---

## Golden Rules for AI Collaboration

### 1. **Start Every Session with Structure Clarity**

**Add this to your prompts:**

```
"Before creating any new files, follow our project structure:
- Production code: src/, scripts/, config/
- Experiments: research/experiments/[experiment-name]/
- Tests: tests/ (only validated tests)
- Results: research/results/[date-experiment-name]/
- Never put test files in root directory"
```

### 2. **Enforce Immediate Cleanup**

**After each experiment, add:**

```
"Now that we've tested [feature], please:
1. If it worked → Move to appropriate production folder
2. If it failed → Move to research/archive/failed-[name]/
3. Delete any temporary test files
4. Update the relevant documentation
Do not leave test files in root or src/"
```

### 3. **Use Session-Based Organization**

**Instead of:** test_v1.py, test_v2.py, test_v3.py in root  
**Do this:**

```
research/experiments/2026-01-18-orb-refinement/
├── README.md (what we're testing)
├── test_v1.py
├── test_v2.py
├── results.csv
└── findings.md
```

**Prompt:**
```
"Create a dated experiment folder: research/experiments/YYYY-MM-DD-[topic]/
Put all related files there. Include a README explaining the experiment."
```

### 4. **Prevent Root Directory Pollution**

**Add this rule:**

```
"NEVER create these in root directory:
- test_*.py, analyze_*.py, debug_*.py
- equity_curve*.csv, stress_test*.csv
- *_results.json, optimization_*.txt
- SESSION_*.md, HANDOFF_*.md

Instead:
- Tests → research/experiments/[date-topic]/
- Results → research/results/[date-topic]/
- Docs → docs/ or research/codebase_cleanup/"
```

### 5. **Version Control Discipline**

**After each working feature:**

```
"Please commit this to git with a clear message:
git add [specific files]
git commit -m 'Add [feature]: [brief description]'

Then archive any experimental files we created."
```

**Avoid:** Letting 50 uncommitted files accumulate

### 6. **Single Source of Truth**

**Prevent duplicates:**

```
"Before creating a new config/parameter file:
1. Check if one already exists
2. If it exists, update it (don't create a duplicate)
3. If we're unsure, show me what exists first"
```

**Example from cleanup:** We had 3 copies of BEAR_TRAP_PARAMETERS.md

### 7. **Research vs Production Separation**

**Make this explicit:**

```
"Organize by maturity:
- research/experiments/ → Active testing
- research/validated/ → Passed tests, ready for prod
- src/, scripts/, config/ → Production only
- research/archive/ → Failed experiments

Move code through these stages explicitly."
```

### 8. **End-of-Session Cleanup**

**Every session should end with:**

```
"Before we end this session:
1. Show me what files we created today
2. Categorize them: Production, Experiment, or Trash
3. Move experiments to research/experiments/[date-topic]/
4. Commit production code
5. Delete/archive trash
6. Update the main README if we added features"
```

---

## Specific Prompts to Use

### Starting a New Experiment

```
"I want to test [idea]. Please:
1. Create research/experiments/YYYY-MM-DD-[short-name]/
2. Put all test code there (not in root)
3. Include a README.md explaining what we're testing
4. Save results in that folder
5. After testing, we'll decide: promote to prod, iterate, or archive"
```

### Working on Production Code

```
"We're modifying production code in src/[file].
1. Make changes
2. Test with existing test suite
3. Commit immediately with clear message
4. Do NOT create temp files in root"
```

### Adding a New Strategy

```
"New strategy: [name]
1. Create research/strategies/[name]/
2. Include: strategy.py, parameters.md, test_validation.py, README.md
3. No files in root
4. Once validated, we'll move to production Perturbations folder"
```

### Debugging Production Issues

```
"Debug issue in [file]:
1. Create research/debug/YYYY-MM-DD-[issue]/
2. Put diagnostic scripts there
3. Document findings in README.md
4. Once fixed, commit fix and archive debug folder"
```

### End of Day/Session

```
"Session cleanup:
1. List all uncommitted files
2. Categorize each: keep/experiment/trash
3. Organize experiments into dated folders
4. Commit production changes
5. Show me final git status and directory structure"
```

---

## Directory Structure Template

**Ask AI to maintain this:**

```
your-project/
│
├── src/                    # Production code ONLY
├── scripts/                # Production utilities ONLY
├── config/                 # Production configs ONLY
├── tests/                  # Validated tests ONLY
│
├── research/
│   ├── experiments/        # Active experiments
│   │   └── YYYY-MM-DD-topic/
│   ├── validated/          # Passed validation, ready for prod
│   ├── archive/            # Failed/old experiments
│   └── results/            # Test results
│       └── YYYY-MM-DD-topic/
│
├── docs/                   # Documentation
│
├── README.md               # Main entry point
├── ARCHITECTURE.md         # System design
└── .gitignore              # Ignore temp files
```

---

## Red Flags to Watch For

**If you see these, it's time to clean up:**

1. **Root directory** has more than 10 files
2. **Multiple versions** of same file (test_v1, test_v2, test_v3...)
3. **CSV/JSON files in root** (results should be in research/results/)
4. **No commits in 2+ hours** of active development
5. **"temp", "old", "backup"** in filenames
6. **Can't find** where a specific test/experiment lives

---

## Weekly Maintenance Prompt

**Every Friday:**

```
"Weekly cleanup:
1. Show me all files in root directory
2. Show me research/experiments/ folders older than 2 weeks
3. For each old experiment:
   - Is it still relevant? Keep in experiments/
   - Was it validated? Move to validated/
   - Failed/obsolete? Move to archive/
4. Commit any uncommitted production code
5. Show final directory tree"
```

---

## Example: Good vs Bad

### ❌ Bad (What We Just Cleaned Up)

```
root/
├── test_orb_v4.py
├── test_orb_v5.py
├── test_orb_v6.py
...
├── test_orb_v12.py
├── equity_curve_baseline.csv
├── equity_curve_variant_f.csv
├── stress_test_NVDA.csv
├── comprehensive_ic_scan.csv
├── SESSION_2026_01_17.md
├── FINAL_VALIDATION_REPORT.md
├── NEXT_AGENT_PROMPT.md
... (100+ files)
```

**Problems:**
- No organization
- Root is cluttered
- Hard to find anything
- Which version is current?
- Which files are production?

### ✅ Good (Clean Structure)

```
your-project/
├── main.py
├── README.md
├── requirements.txt
│
├── src/
│   └── [production modules]
│
├── research/
│   ├── experiments/
│   │   ├── 2026-01-15-orb-optimization/
│   │   │   ├── README.md (goal, findings)
│   │   │   ├── test_versions_v4_to_v12.py
│   │   │   ├── results.csv
│   │   │   └── analysis.md
│   │   │
│   │   └── 2026-01-17-slippage-study/
│   │       ├── README.md
│   │       ├── test_slippage.py
│   │       └── results/
│   │
│   └── validated/
│       └── orb_v12_final/
│           ├── orb.py (ready for production)
│           └── validation_report.md
```

**Benefits:**
- Clear organization
- Easy to find things
- Root stays clean
- Know what's production vs experiment
- Each experiment is self-contained

---

## Your Personal AI Collaboration Rules

**Create a file: `.ai-rules.md` in your repo:**

```markdown
# AI Collaboration Rules

When you help me develop:

1. **Never put test files in root** - Use research/experiments/YYYY-MM-DD-topic/
2. **No duplicate files** - Check if file exists before creating
3. **Immediate cleanup** - After each experiment, organize or archive
4. **Clear naming** - research/experiments/[date-topic]/ for all experiments
5. **Single source of truth** - One config, one parameter file per feature
6. **End session cleanup** - List uncommitted files, organize, commit
7. **Production separation** - Only validated code in src/, scripts/, config/

Ask me to review this file before each session.
```

**Then prompt:** "Review .ai-rules.md and follow those guidelines for this session"

---

## TL;DR - The Essential Habit

**Add this to EVERY prompt where you create files:**

```
"Follow our structure:
- Production → src/, scripts/, config/
- Experiments → research/experiments/YYYY-MM-DD-topic/
- Results → research/results/YYYY-MM-DD-topic/
- Never create test files in root
- After testing: commit, move, or delete
- No duplicates - check first"
```

**And end every session:**

```
"Session cleanup:
1. Organize today's files
2. Commit production code
3. Show final structure"
```

---

## Result

**Before (what we had):**
- 326 Python files, 100+ in root
- Hard to find anything
- Unclear what's production
- Massive cleanup required

**After (what you'll maintain):**
- ~45 production Python files
- <10 files in root
- Clear organization
- Easy to navigate
- No cleanup debt

---

**The secret:** Make organization habits explicit in your prompts, not implicit assumptions.

**Save this file as:** `docs/AI_COLLABORATION_GUIDELINES.md`  
**Reference it:** At the start of each session with AI
