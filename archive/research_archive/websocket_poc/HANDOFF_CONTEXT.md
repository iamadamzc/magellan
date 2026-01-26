# HANDOFF CONTEXT - PHASE 1 WEBSOCKET POC

**Last Updated**: 2026-01-16  
**Current Agent**: Claude Sonnet 4.5 Thinking  
**Tokens Used**: ~114k / 200k (57%)  
**Branch**: `feature/websocket-poc` (to be created)

---

## PROJECT CONTEXT

### What We're Doing
Testing WebSocket streaming and new data sources locally to prove viability before AWS deployment.

### Why
Current system uses REST polling (slow, 500ms+). WebSocket streaming can achieve <100ms latency with no infrastructure cost.

### Success Criteria
- WebSocket connections working
- At least one strategy shows Sharpe >1.0 in backtest
- Clear decision on AWS deployment

---

## CURRENT STATE

### Git Status
```
Branch: feature/capabilities-research
Last Commit: ca0d3e7 (capabilities research docs)
Next Step: Create feature/websocket-poc branch
```

### Completed Work
- ✅ Capabilities research (FMP Ultimate, Alpaca Premium)
- ✅ Implementation plan created
- ✅ Task checklist created
- ✅ This handoff doc created

### Not Started
- ❌ POC branch not created yet
- ❌ No code written
- ❌ WebSocket connections not tested

---

## FILES TO READ BEFORE STARTING

### Priority 1 (Must Read)
1. **implementation_plan.md** - Complete Phase 1 plan
2. **task.md** - Task checklist
3. **ITS_NOT_THE_SYSTEM_REMEDIATIONS.md** - Full context on why we're doing this

### Priority 2 (Context)
1. **CAPABILITIES_RESEARCH_SUMMARY.md** - What we learned
2. **fmp_ultimate_audit.md** - FMP features we're not using
3. **alpaca_premium_audit.md** - Alpaca features we're not using

---

## NEXT IMMEDIATE STEPS

### Step 1: Create POC Branch
```bash
cd a:\1\Magellan
git checkout feature/capabilities-research
git pull
git checkout -b feature/websocket-poc
git push -u origin feature/websocket-poc
```

### Step 2: Create Directory Structure
```bash
mkdir research\websocket_poc
mkdir research\websocket_poc\tests
mkdir research\websocket_poc\configs
```

### Step 3: Start Task 1
**File**: `research/websocket_poc/alpaca_ws_poc.py`  
**Code template**: See implementation_plan.md Task 1

---

## PROTECTED AREAS (DO NOT TOUCH)

### Zero Changes Allowed
- `src/` - All production code
- `main.py` - Core system  
- `.env` - Credentials (read-only)
- Any existing strategy files

**WHY**: This is a POC. If it fails, we abandon the branch. We don't risk breaking the working system.

---

## DEPENDENCIES

### Python Packages
```bash
pip install alpaca-py websockets asyncio python-dotenv
pip install requests pandas numpy scipy
```

### API Keys
- Alpaca: `APCA_API_KEY_ID`, `APCA_API_SECRET_KEY` (in .env)
- FMP: `FMP_API_KEY` (in .env)

### Accounts
- Alpaca paper trading enabled
- FMP Ultimate subscription active

---

## KNOWN UNKNOWNS

### FMP WebSocket
**Status**: Unclear if FMP has WebSocket API  
**Research Needed**: Check FMP SDK docs  
**Fallback**: Fast polling (5-10 second intervals) if no WebSocket

### News Latency
**Status**: Unknown how fast news arrives  
**Test Needed**: Measure actual news→receipt time  
**Decision**: If >1 second, news momentum may not work

---

## DECISION GATES

### After Week 1
**Question**: Are WebSocket connections working?  
**If NO**: Pivot to optimized REST polling, document limitations  
**If YES**: Proceed to Week 2

### After Week 2  
**Question**: Do strategies show Sharpe >1.0?  
**If NO**: Don't deploy to AWS, iterate locally or abandon  
**If YES**: Proceed to AWS deployment (Phase 2)

---

## ROLLBACK PROCEDURE

### If POC Fails
```bash
# Delete branch
git checkout feature/capabilities-research
git branch -D feature/websocket-poc

# Clean up
rm -rf research/websocket_poc

# Document
# Add findings to CAPABILITIES_RESEARCH_SUMMARY.md
```

No harm done - main system untouched.

---

## MODEL RECOMMENDATIONS

### For Phase 1
**Use**: Claude Sonnet 4.5 Thinking (current)  
**Why**: Complex async code, debugging needed  
**Tokens**: Should have ~86k remaining (enough for Phase 1)

### If Tokens Run Low
**Switch to**: Claude Opus 4.5  
**Why**: Larger context window for backtesting  
**When**: After Task 4 (when doing heavy backtests)

### For Simple Edits
**Use**: Gemini Flash  
**Why**: Fast, cheap for documentation updates  
**When**: Updating task.md, POC_RESULTS.md

---

## COMMUNICATION PROTOCOL

### Git Commit Messages
**Format**: `poc: [description]`  
**Examples**:
- `poc: Add Alpaca WebSocket connection`
- `poc: Complete economic calendar integration`
- `poc: Document FMP WebSocket not available`

**Purpose**: Easy to identify POC work vs. production code

### Status Updates
**Update task.md** after each completed task:
- Change `[ ]` to `[x]`
- Add notes in Blockers & Notes section
- Update Status field

---

## HANDOFF CHECKLIST

### When Handing Off to Next Agent

**Give them**:
1. Link to implementation_plan.md
2. Link to task.md (with current status)
3. Current git branch name
4. Which task to start on
5. Any blockers discovered

**Don't assume they know**:
- Project context
- What's already been tried
- Why we're doing this

**Always include**:
- Exact file paths
- Exact commands to run
- Expected outputs

---

## TROUBLESHOOTING

### Common Issues

**Issue**: WebSocket connection fails  
**Solution**: Check .env credentials, verify internet connection, try paper API endpoint

**Issue**: FMP API rate limit  
**Solution**: We have 3,000 calls/min, should never hit. Check API key if errors.

**Issue**: Alpaca paper account not working  
**Solution**: Verify paper trading enabled in Alpaca dashboard

---

## SUCCESS EXAMPLES

### What Good Looks Like

**Task 1 Success**:
```
🔌 Connecting to Alpaca WebSocket...
[NVDA] Price: $875.32 | Latency: 82ms
[TSLA] Price: $248.15 | Latency: 76ms
...
✅ Average latency: 85ms
   Min: 45ms
   Max: 210ms
```

**Task 5 Success**:
```
📊 Event Straddle Backtest Results:
2024-01-31 FOMC: +3.2%
2024-03-20 FOMC: +2.8%
...
Sharpe Ratio: 1.45
Win Rate: 65%
Avg Hold: 11 minutes
```

---

## FINAL NOTES

### Philosophy
- **Move fast locally** (no cloud costs)
- **Prove before deploying** (test everything)
- **Document failures** (learning is progress)
- **Protect production** (never touch src/)

### Timeline
- Week 1: WebSocket connections
- Week 2: Strategy testing  
- End of Week 2: GO/NO-GO decision

### Next Phase (If GO)
- Phase 2: AWS deployment
- Phase 3: Live paper trading
- Phase 4: Small capital deployment

---

## QUESTIONS FOR USER

**Before starting**, confirm:
1. OK to create `feature/websocket-poc` branch?
2. OK to test with paper trading account?
3. Any specific strategies to prioritize?
4. Any concerns about approach?

---

**Good luck! You have everything you need to execute Phase 1.**
