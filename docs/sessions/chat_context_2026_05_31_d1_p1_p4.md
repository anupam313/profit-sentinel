# Profit Sentinel — Chat Context
## Date: 2026-05-31
## Session: D1 Gap 3 — Principles 1–4
## Previous context: chat_context_2026_05_26_d1_gap2.md

---

## SESSION PURPOSE

Continue D1 gap review from Gap 2 (locked 2026-05-26).
This session: full deliberation of Gap 3 causal decomposition,
covering Principles 1–4 from the original Gap 3 proposal.
All four principles locked. Next session starts at Gap 4.

---

## GOVERNING PRINCIPLES REINFORCED THIS SESSION

### Action-First Principle (repeatedly applied)
Every driver named in D1 must produce a specific same-day action.
Observations that are not actionable same-day belong in the
weekly Profit Audit, not in a D1 alert.
This principle killed the Tier 2/3 category flag entirely.

### No Hardcoding Principle (applied to thresholds)
The 4pp ceiling on margin_mix_shift_threshold was challenged
and removed. The 80% SKU count floor for sku_cost_master
coverage was challenged and replaced with 85% revenue coverage.
Both were arbitrary. Both were wrong.

---

## PRINCIPLE 1 DELIBERATION PATH

### Opening framing: revenue-side vs cost-side split
Original proposal: segment compression into revenue-side
(AOV, returns, discounts) vs cost-side (CPM, fulfilment, COGS)
before naming drivers. Give founder a directional lens.

### Challenge 1: does the split produce a distinct action?
No. "Revenue-side" tells the founder to look at discounting
and returns — but which one? The split reduces search space
from 6 to 3 drivers but does not name a specific action.
If Gap 8 (action per driver) is never reached, Principle 1
is pure framing overhead.

### Challenge 2: the timing problem (most important)
Trigger A fires after a complete clean 7-day window falls
below p25. The alert arrives at the founder at start of
week N+1. By then, CPM spikes (3–7 days on Meta) may have
already normalised. Creative may have been refreshed.
Return wave may have cleared.
The alert is only worth sending if:
(a) driver is still active, OR
(b) structural damage persists (returns locked in), OR
(c) pattern needs to be known for recurrence prevention.

The revenue-side/cost-side label does not tell the founder
which of these three cases applies.

### Challenge 3: the mixed case breaks the taxonomy
CPM rise → poor-fit traffic → higher return rate.
One upstream cause showing up on both sides.
"Mixed" label produces no sharper action than no label.

### Resolution
Split retained as internal decomposition logic only.
Never surfaces as founder-facing label.
Founder-facing output: drivers ranked by measured impact,
each with live-vs-passed status (24–48 hour current read)
and reversibility indicator.
Agent D reads current-period data per driver before formatting.

---

## PRINCIPLE 2 DELIBERATION PATH

### Original proposal: two-axis confidence table
Measurement confidence (HIGH/MEDIUM/LOW) ×
Causal confidence (HIGH/MEDIUM/LOW) per driver.

### Challenge 1: logical contradiction
Fulfilment cost listed as MEDIUM measurement / HIGH causal.
Not defensible — high causal confidence requires reliable
measurement. Two-axis table produces contradictions.

### Challenge 2: static table vs runtime reality
Confidence is a property of the data pipeline at alert
generation time, not a static property of the driver type.
CPM is HIGH measurement confidence — unless Meta sync failed
and we're reading 36-hour-old data. The table cannot capture
this. What matters is data freshness at render time.

### Challenge 3: two parallel confidence frameworks
Causal confidence already handled by causal_pattern_validation
(candidate / provisional / core). Adding a second parallel
taxonomy creates two overlapping frameworks that will diverge.

### Challenge 4: cognitive load on founder
A founder reading "CPM: HIGH measurement, MEDIUM causal"
in a Slack alert adds confusion without adding actionability.

### Resolution
Two-axis taxonomy dropped entirely.
Replaced with three inline disclosure types:
1. Data staleness (per-source thresholds, runtime check)
2. Estimation flag (static — fulfilment cost, COGS)
3. Data completeness (per-client runtime — Loop return_reason)
Staleness thresholds: use existing per-source thresholds
already defined in technical_architecture.md. No new definition.

---

## PRINCIPLE 3 DELIBERATION PATH

### Original proposal: directed contribution (not additive)
State each driver's delta independently. Compare total
measured impact to total CM gap. Disclose residual if >30%.

### Challenge 1: common unit conversion undefined
CPM rise = cost per order increase ($/order).
Return rate rise = revenue lost ($/week).
These cannot be compared without converting to a common unit.
The conversion formula per driver was not specified.
Resolved: five explicit formulas locked. Isolation principle
defined (hold all other variables at BAU).

### Challenge 2: interaction terms
If CPM + return rate + discount depth all move simultaneously,
attributing CM impact to each independently triple-counts a
single upstream cause (creative fatigue).
Resolved: Layer 0 interaction check fires before driver list.
Three hardcoded patterns. AI-discovered patterns via extended
historical_pattern_scan.py with mandatory practitioner gate.

### Challenge 3: 30% residual threshold is arbitrary
Why 30%? No empirical basis. A brand at 29% unexplained
gets no disclosure; 31% gets one.
Resolved: threshold governs firing, not disclosure presence.
Disclosure always present. Firing gate:
<40% → fire normally. 40-70% → fire with elevated disclosure,
urgency drops. >70% → blind spot diagnostic, not standard D1.

### Challenge 4 (from founder): high residual destroys trust
"If 70-80% is unexplained, won't that make them doubt the
product?" — correct challenge.
Sending a D1 alert where the product cannot explain the
majority of the compression is a failed alert, not an
honest one. "Monitoring" is a cop-out.
Resolved: >70% residual → D1 does not fire.
Blind spot diagnostic runs instead — five-step structured
check that names the most likely unexplained cause with a
specific investigation brief.
Target: <10% of Outcome B cases reach Step 5 (genuine unknown).
Cause frequency analysis: COGS unmeasured ~50-60%,
revenue mix shift ~20-25%, fulfilment cost step change ~10-15%,
payment processing ~5%, genuine unknown <5%.

### Challenge 5: practitioner gate for AI interaction patterns
AI-discovered interaction patterns can reflect seasonality,
not causation. A practitioner looking at 7 instances might
immediately see 5 of 7 were BFCM.
Resolved: practitioner_approved = true required before any
AI-discovered interaction pattern absorbs into live library.
calendar_clustered = true patterns flagged prominently.
Not blocked — but reviewed first.

---

## PRINCIPLE 4 DELIBERATION PATH

### Original proposal: SKU mix shift for Tier 1/1.5
2pp hardcoded threshold. 80% SKU count coverage floor.
Tier 2/3 directional flag for category revenue share shift.
product_type as primary category proxy.

### Challenge 1: 4pp ceiling on adaptive threshold
Original: MIN(MAX(SD × 1.5, 1.5pp), 4pp ceiling).
Challenge: a drops-based brand with naturally high mix
volatility gets their normal operation flagged constantly.
The ceiling protects against the wrong failure mode —
Trigger A handles CM-level detection regardless.
Resolution: ceiling removed. MAX(SD × 1.5, 1.5pp floor) only.

### Challenge 2: 80% SKU count floor
Challenge: wrong metric. If 20% of SKUs missing unit_cost
but they are all low-volume accessories, the calculation is
reliable. If 20% missing but they include the hero SKU,
the calculation is meaningless. SKU count tells you nothing
about whether the calculation is trustworthy.
Resolution: replaced with 85% revenue coverage.
Additional check: if the single largest revenue SKU this
week is missing unit_cost → flag regardless of overall rate.

### Challenge 3: Tier 2/3 category flag and actionability
Original: directional flag for category revenue share shift.
Challenge 1: new collection launch in Cat A → Cat A spikes.
Founder knows. They launched it. Not actionable.
Challenge 2: even for organic unexplained shifts (Scenario 3),
the action is "check why this category is being searched."
Founder cannot stop organic search. Cannot reprice same-day.
Non-actionable same-day → belongs in Profit Audit.
Full scenario enumeration (7 scenarios):
- Scenario 4 (spend misallocation): actionable but belongs
  in CPM/ROAS driver set + A-series, not category shift flag.
- All other scenarios: either covered by existing drivers,
  suppressed by event/season logic, or non-actionable.
Resolution: Tier 2/3 category flag dropped entirely.
No scenario produces a unique same-day action from category
shift alone without unit costs.

### Challenge 4: AI category inference and vocabulary mismatch
Challenge: Claude infers "Dresses", "Tops", "Accessories."
Founder calls them "Hero", "Core", "Seasonal Drop."
Alert uses vocabulary the founder doesn't recognise →
immediate credibility loss.
Resolution: Collections primary (founder-created, brand-native).
AI inference with mandatory founder rename as fallback.
product_type retired as primary proxy.

---

## KEY DECISIONS CHALLENGED AND REVERSED THIS SESSION

| Proposal | Challenge | Resolution |
|----------|-----------|------------|
| Revenue-side/cost-side as founder label | Adds taxonomy, no action | Internal logic only. Never shown to founder. |
| Two-axis confidence table | Contradictions, parallel frameworks, cognitive load | Three inline disclosures. Per-source staleness thresholds. |
| 30% as residual disclosure gate | Arbitrary threshold, no empirical basis | Firing gate: 40%/70% bands. Disclosure always present. |
| "We are monitoring" for high residual | Cop-out. Destroys trust. | Blind spot diagnostic with 5-step named cause investigation. |
| 4pp ceiling on mix shift threshold | Correct normal brand behaviour flagged constantly | Ceiling removed. Floor only. |
| 80% SKU count coverage floor | Wrong metric — count ≠ revenue reliability | 85% revenue coverage. Hero SKU check added. |
| 2pp hardcoded mix shift threshold | No Hardcoding Principle violation | Brand-adaptive: MAX(SD × 1.5, 1.5pp floor) |
| Tier 2/3 category directional flag | No scenario produces unique same-day action | Dropped entirely |
| product_type as primary category proxy | Founder-inconsistent, not brand-native | Collections primary. AI inference + rename as fallback. |
| AI category inference labels | Vocabulary mismatch destroys alert credibility | Mandatory founder rename step before any label used in alerts |

---

## WHAT IS NOW LOCKED — COMPLETE SUMMARY

**Principle 1:**
- Revenue-side/cost-side = internal only
- Founder sees: ranked drivers + live-vs-passed status +
  reversibility indicator per driver
- Agent D reads 24–48h current data per driver before formatting

**Principle 2:**
- Three inline disclosure types only
- Per-source staleness thresholds from existing architecture
- No second confidence framework

**Principle 3:**
- Five driver formulas with isolation principle
- Three-layer output (Layer 0 interaction → Layer 1 drivers →
  Layer 2 residual)
- Three hardcoded interaction patterns
- AI-discovered patterns via multivariate sweep +
  mandatory practitioner gate
- Residual as firing gate: 40%/70% bands
- >70% → blind spot diagnostic (5 steps, target <10% reach Step 5)
- connector_gap_map new table

**Principle 4:**
- Adaptive threshold, ceiling removed
- 85% revenue coverage floor, hero SKU check
- Tier 2/3 category flag dropped
- Tier 1/1.5 formula retained with full suppression conditions
- Collections primary, AI inference + rename fallback,
  graceful skip
- category_inference.py new onboarding script
- Two Gap 6 dependencies noted and locked

---

## NEXT SESSION STARTING POINT

1. Load: state_2026_05_31_d1_p1_p4.md, this file,
         agent_d_build_spec.md (updated),
         technical_architecture_additions_2026_05_31.md,
         product_strategy.md
2. Start: D1 Gap 4 — CPM causal chain intermediate steps
3. Work through Gaps 5–9 in order
4. Write D1 alert language after all 9 gaps resolved
5. Then D2 → D3 → D4 → D5 → D6 → C → B → A → H
6. Consolidated Claude Code prompt after H-series only
