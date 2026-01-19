Executive Diagnosis

Your biggest problem is not stop width, pyramiding, or volume multipliers.

It’s this:

You’re entering impulse moves and exiting during equilibrium.

That’s why:

96.7% of exits are time stops

0.3% ever reach 1R

Win rate stalls around 41% no matter what you tweak

That pattern is mathematically incompatible with:

fixed R targets

time-based exits

OR breakouts on noisy small caps

This is classic ORB decay behavior, especially in crypto miners and meme stocks.

ORB_PARAMETER_TUNING_SUMMARY

Structural Problems (Ranked by Severity)
1. Time Stop Is Killing the Strategy

This is non-negotiable.

If 97% of exits are time-based, your strategy is not failing to win.
It’s being forcibly closed before resolution.

Action:

Remove MAX_HOLD_MINUTES entirely for the next test

Replace with volatility-based exit only

You already trail. Let it work.

If a trade goes nowhere, the trail will take it out anyway. Time stops only make sense when:

you expect mean reversion

or you’re market making

ORB is neither.

2. ORB on Small Caps Is a One-Bar Game

Your own stats prove this.

Most trades:

break OR

spike briefly

then compress

So when you enter:

on the breakout bar

with volume confirmation

after 10 minutes of discovery

You are late by definition.

Fix the entry, not the filters.

Replace breakout entries with one of these:

Option A (Highest Priority): OR High Retest Entry

Detect breakout

Wait for pullback to:

OR high ± 0.1 ATR

Enter on reclaim + volume stabilization

This alone typically:

increases win rate by 6–10%

reduces time-stop exits dramatically

Yes, fewer trades. You have plenty.

3. Your R Math Assumes Trends That Don’t Exist

You’re targeting:

1R

2R

pyramids at 0.8R

But your data shows:

most moves top out at 0.4–0.7R

then chop

So your scale logic is mathematically mismatched.

Fix:

Scale earlier

Trail tighter sooner

Accept smaller R wins

This is scalping. Not trend following.

Parameter-Level Recommendations
Entry

Keep OR_MINUTES = 10

Keep VOL_MULT = 1.5

Change entry trigger:

Breakout → pullback → reclaim

Optional:

Require reclaim above OR high and VWAP

VWAP is not a filter here. It’s a location sanity check.

Stops

Your stop logic is mostly fine, but slightly mismatched.

Change:

Initial stop:
min(OR_low, entry - 0.5 ATR)

After +0.3R:

Trail to entry - 0.2 ATR

After +0.6R:

Trail to high - 0.6 ATR

Stop trying to be elegant. Be practical.

Exits

Delete the time stop.

Replace with:

ATR trail only

Optional hard kill switch at EOD - 10 min

You don’t need more exits. You need fewer forced ones.

Scaling & Pyramiding

Right now pyramiding helps, but it’s mistimed.

Change:

Scale 30–40% at 0.4R

Pyramid only if:

price holds above OR high for 3–5 bars

volume does not collapse

If a move can’t hold OR high, adding is pointless.

What NOT to Do (Important)

Do not add more indicators

Do not chase higher VOL_MULT

Do not widen stops further

Do not optimize on RIOT/MARA alone

Those symbols exaggerate impulse decay. They’re good stress tests, not calibration tools.

Expected Impact (Realistic)

If you implement only:

OR retest entry

removal of time stop

earlier scaling

You should expect:

Win rate: ~47–50%

Avg win: smaller

Avg loss: unchanged

Net expectancy: slightly positive after friction

That clears your +0.015% hurdle.

Final Verdict

This strategy is not “almost working.”

It’s doing exactly what ORB scalps do, and your exit logic is fighting that reality.

Stop forcing trends.
Start harvesting impulses.

You’re closer than the P&L suggests.