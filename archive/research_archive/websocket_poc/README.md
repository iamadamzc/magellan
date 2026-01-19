# WebSocket POC - Phase 1

**Status**: In Progress  
**Branch**: feature/websocket-poc  
**Goal**: Test WebSocket streaming locally before AWS deployment

---

## Quick Start

### Task 1: Alpaca WebSocket Test
```bash
python research/websocket_poc/alpaca_ws_poc.py
```

Collects 100 real-time bars, measures latency.  
**Stop**: It will auto-stop after 100 samples (or press Ctrl+C)

---

## Progress

- [x] Git branch created
- [x] Directory structure created
- [x] Alpaca WebSocket POC written
- [ ] Alpaca WebSocket tested
- [ ] FMP WebSocket tested
- [ ] Economic Calendar tested
- [ ] Latency benchmark completed

---

## Results

Results saved to:
- `latency_results.txt` - Alpaca WebSocket latency stats
- (more to come)
