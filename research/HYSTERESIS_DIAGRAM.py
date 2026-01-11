"""
HYSTERESIS DEADBAND - VISUAL REFERENCE
Anti-Chatter Logic for Signal Stability
"""

print("""
╔════════════════════════════════════════════════════════════════════════╗
║                    HYSTERESIS DEADBAND DIAGRAM                         ║
║                    Prevents Signal Chatter                             ║
╚════════════════════════════════════════════════════════════════════════╝

                         CARRIER WAVE SCALE
                         ==================

    0.0                0.5 (GATE)               1.0
     |                     |                     |
     |---------------------|---------------------|
     |                     |                     |
   BEARISH             NEUTRAL              BULLISH


                    HYSTERESIS ZONES
                    ================

                 DEADBAND = 0.02

         0.48              0.50              0.52
          |                 |                 |
    ------+-----------------+-----------------+------
          |                 |                 |
       EXIT BUY         NEUTRAL           ENTER BUY
       (to FILTER)                       (from FILTER)


                    STATE TRANSITIONS
                    =================

    FILTER State:
    ┌─────────────────────────────────────────────────┐
    │  Carrier < 0.48  →  Stay FILTER                 │
    │  0.48 ≤ Carrier ≤ 0.52  →  Stay FILTER          │
    │  Carrier > 0.52  →  Flip to BUY                 │
    └─────────────────────────────────────────────────┘

    BUY State:
    ┌─────────────────────────────────────────────────┐
    │  Carrier < 0.48  →  Flip to FILTER              │
    │  0.48 ≤ Carrier ≤ 0.52  →  Stay BUY             │
    │  Carrier > 0.52  →  Stay BUY                    │
    └─────────────────────────────────────────────────┘


                    EXAMPLE SEQUENCE
                    ================

    WITHOUT HYSTERESIS (CHATTER):
    ─────────────────────────────────────────────────
    Time  Carrier  State     Action
    ─────────────────────────────────────────────────
    T1    0.499    FILTER    -
    T2    0.501    BUY       ← FLIP (chatter)
    T3    0.499    FILTER    ← FLIP (chatter)
    T4    0.502    BUY       ← FLIP (chatter)
    T5    0.498    FILTER    ← FLIP (chatter)
    ─────────────────────────────────────────────────
    Result: 4 flips in 5 bars = UNSTABLE


    WITH HYSTERESIS (STABLE):
    ─────────────────────────────────────────────────
    Time  Carrier  State     Action
    ─────────────────────────────────────────────────
    T1    0.499    FILTER    -
    T2    0.501    FILTER    ← STAYS (need 0.52)
    T3    0.510    FILTER    ← STAYS (need 0.52)
    T4    0.521    BUY       ← FLIP (clean)
    T5    0.510    BUY       ← STAYS (need 0.48)
    T6    0.505    BUY       ← STAYS (need 0.48)
    T7    0.479    FILTER    ← FLIP (clean)
    ─────────────────────────────────────────────────
    Result: 2 flips in 7 bars = STABLE


                    NEUTRAL ZONE
                    ============

         [0.48 ─────── 0.50 ─────── 0.52]
              ↑                      ↑
         EXIT THRESHOLD        ENTRY THRESHOLD

    • If in FILTER: Need to cross 0.52 to enter BUY
    • If in BUY: Need to drop below 0.48 to exit to FILTER
    • Neutral zone [0.48, 0.52] = NO STATE CHANGE


                    BENEFITS
                    ========

    ✓ Prevents rapid oscillations at threshold
    ✓ Reduces overtrading (fewer flips = lower costs)
    ✓ Improves signal quality (only strong moves trigger)
    ✓ Stabilizes portfolio (less churn)


                    IMPLEMENTATION
                    ==============

    Code: src/features.py (lines 874-1050)

    HYSTERESIS_DEADBAND = 0.02

    if prev_state == 'FILTER':
        if carrier > (gate + HYSTERESIS_DEADBAND):
            new_state = 'BUY'
        else:
            new_state = 'FILTER'
    
    elif prev_state == 'BUY':
        if carrier < (gate - HYSTERESIS_DEADBAND):
            new_state = 'FILTER'
        else:
            new_state = 'BUY'


╔════════════════════════════════════════════════════════════════════════╗
║  HYSTERESIS = MEMORY OF PREVIOUS STATE                                 ║
║  System "remembers" where it came from to prevent chatter              ║
╚════════════════════════════════════════════════════════════════════════╝
""")
