# Bear Trap ML Scanner - Enhancement Backlog

## 🎯 **Phase 3: GenAI Enhancements** (Future)

### **Priority 1: News Catalyst Death Spiral Filter** ⭐⭐⭐⭐⭐
**Objective**: Avoid trading on fundamental collapses (bankruptcy, fraud, delisting)

**Implementation**:
- Use LLM (GPT-4 or Claude) to classify news sentiment
- Input: Last 24h news headlines for symbol
- Output: Classification (TECHNICAL / FUNDAMENTAL-TEMPORARY / FUNDAMENTAL-TERMINAL)
- Integration point: Pre-trade gate in scanner

**Value**: Prevents 90%+ of death spiral trades

**Estimated effort**: 1-2 days

---

### **Priority 2: Market Regime Synthesizer** ⭐⭐⭐⭐
**Objective**: Adjust risk based on macro conditions

**Implementation**:
- Daily LLM synthesis of: VIX, SPY trend, Fed calendar, earnings season, sector rotation
- Output: Risk multiplier (0.5x - 1.5x)
- Integration point: Position sizing logic

**Value**: Reduce risk on fragile market days

**Estimated effort**: 2-3 days

---

### **Priority 3: Multimodal Chart Pattern Recognition** ⭐⭐⭐⭐
**Objective**: Use vision models to identify visual reversal patterns

**Implementation**:
- Generate chart images for each selloff
- GPT-4V / Gemini analyzes for capitulation wicks, V-patterns
- Output: Visual pattern confidence boost
- Integration point: ML confidence adjuster

**Value**: Catches patterns traditional features miss

**Estimated effort**: 3-4 days

---

### **Priority 4: Post-Trade Explainer** ⭐⭐⭐
**Objective**: Build audit trail and learning corpus

**Implementation**:
- After each trade, LLM generates 2-sentence rationale
- Logs explanation to trade journal
- Build searchable database of explained outcomes

**Value**: Transparency, pattern learning, compliance

**Estimated effort**: 1 day

---

### **Priority 5: Dynamic Feature Engineering Assistant** ⭐⭐⭐
**Objective**: Automated research suggestions

**Implementation**:
- Feed recent trade results to LLM
- Ask for new feature suggestions
- Human validates and backtests

**Value**: Continuous strategy improvement

**Estimated effort**: 2-3 days

---

### **Priority 6: Similarity Search via Embeddings** ⭐⭐
**Objective**: Find non-obvious historical analogues

**Implementation**:
- Embed selloff events as text descriptions
- Use vector DB (Pinecone/Weaviate) for similarity search
- Check historical success rate of similar events

**Value**: Contextual confidence boosting

**Estimated effort**: 3-4 days

---

## 📋 **Implementation Notes**

- All GenAI features are **optional enhancements**
- Core ML model (XGBoost) remains primary predictor
- LLMs provide context, not predictions
- Focus on explainability and risk reduction

---

**Status**: Backlog  
**Next review**: After Phase 2 (ML model) is validated
