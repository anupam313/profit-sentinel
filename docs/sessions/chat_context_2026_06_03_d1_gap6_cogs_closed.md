# Profit Sentinel — Chat Context (D1 Gap 6: COGS / S21)
## Date: 2026-06-03
## Session type: Design (Gap 6 COGS component) + spec application
## Pairs with: state_2026_06_03_d1_gap6_cogs_closed.md

Purpose: record the reasoning so the next chat does not re-litigate settled ground and
resumes correctly (decide the Gap 1 flagged proposal first, then discount-depth/S19).

---

## HOW THE COGS REVIEW UNFOLDED

Started as a routine seam check on S21 (the supplier-cost rule with its 60-day window).
It escalated through founder challenges into a reshaping of the margin alert for
no-cost-data brands.

**Seam check finding:** unlike return-rate (which collided with C3), COGS has no
cross-alert clash — no other alert consumes cost. The seams are D1-vs-reality (the fixed
60-day window is the wrong shape — old stock clears at each SKU's velocity, not on a
calendar) and D1-vs-the-tiers (most brands have no cost feed, so the cost-increase the
rule suppresses around is invisible to begin with).

**Founder challenge 1 — "a supplier raises ALL SKUs, not a few."** Correct. The
"which SKUs" framing was wrong; what survives is the *timing* — all SKUs are hit, but each
reflects the new cost as it cycles through its own old stock. Action is supplier-level
(reprice the line / renegotiate / absorb), sequenced by who's already bleeding.

**Founder challenge 2 — "how do we compute margin / claim it's dipping without correct
COGS, and without that how can we even ask them to update cost?"** This was the decisive
one. Decomposing contribution margin: four of five drivers (ad, returns, discount, mix)
are visible; product cost is the one we can't see without a feed. A COGS-driven dip
against an assumed-constant cost produces NO change in computed margin → undetectable →
the "detect dip then ask to update cost" loop is circular. My earlier "Version B" alert
(detect drop → check invoices) was wrong for no-cost brands and was retracted.

**Shopify facts checked (web):** cost-per-item is a single manual value, usually product
cost only, NOT retroactive; Shopify holds one cost per product, no layers (FIFO/average
lives in accounting/Stocky). So even the phase-in curve isn't computable from Shopify
alone.

**Founder challenge 3 — "expecting unprompted COGS re-uploads is unrealistic; should this
alert even exist; isn't it too corrupt at this stage?"** Pushed back on "kill it
entirely" but agreed with the spirit: scope it. Separated what needs trustworthy COGS
(margin figures + the cost-increase driver) from what doesn't (the other four drivers).
Landed on: margin alert is feed-only; no-trustworthy-COGS brands get component signals,
no margin verdict (this is the Gap 1 tightening — flagged, not locked).

**Founder challenge 4 — the connector question.** Agreed COGS is the most critical input,
but the right response is rigor + honesty about data quality, not building a connector
now: no single clean source at this tier, approximate auto-COGS more dangerous than
honest manual COGS, off the core moat, and can't validate the target tool without
discovery. Deferred, discovery-gated.

**Onboarding capture + staleness + footnote.** Capture cost basis once (Shopify-cost
confirmation, CSV for gaps, ping permission, founder's own refresh rhythm). Updates
proactive, never reactive; new-SKU ping is the reliable nudge. The "90 days" I proposed
for a periodic nudge was made up and retracted — staleness keys off the founder's own
rhythm. Footnote-on-every-alert rejected (fatigue + goes blind when it matters) →
state-driven disclosure (clean / caveat / no-figure), the visible face of staleness-decay.

---

## RETRACTED / CORRECTED THIS SESSION (do not revive as if live)
- "Version B" reactive blind-spot alert for no-cost brands (can't fire for a pure COGS
  increase — undetectable).
- "Reprice the affected SKUs" (it's all SKUs from that supplier; sequence by sell-through
  timing instead).
- The invented "90-day" staleness nudge (no basis; use the founder's own refresh rhythm).
- Driver-only as adequate for no-trustworthy-COGS brands → proposing component-only
  (flagged, pending founder decision).

## CARRIED RETRACTIONS (earlier, still not live)
"no reliable source for size-guide changes"; per-edit founder confirmation; reassurance-
led action wording; virality-is-accretive; three-state seed lifecycle; modeled viral
echo-window.

---

## PROCESS NOTE (founder-requested safeguards, applied this save)
Edited targeted snippets on copies (no large-file regeneration). Checks run before
handoff: changed-region count = declared edits; untouched-region byte-identical;
manifest coverage; no-orphan; line-count deltas; cross-file agreement on shared terms.
Added this batch: a CROSS-FILE orphan sweep for the retired "60-day" concept (it caught
the window restated in product_strategy.md D3 — fixed); and canonical phrasing locked up
front for the new shared terms (trustworthy cost feed / per-product sell-through /
staleness-decay / revenue-weighted cost coverage / component-only). Decision list was
reviewed against the chat and confirmed by the founder before editing.

---

## RESUME POINT
Gap 6: dependencies + return-rate (Seam 2 + C3) + COGS/S21 CLOSED. FIRST next session:
decide the FLAGGED Gap 1 proposal (component-only vs driver-only). Then resume at
discount-depth/S19 seam check (verify against source; do NOT assert clean), then
operational-cost/S20 → final cross-component residual-disclosure pass. After Gap 6:
7 → 8 → 9 → D1 alert language → D2 → D3 → D5 → D6 → C → B → A → orchestration resolution
pass → H → consolidated Claude Code prompt.
