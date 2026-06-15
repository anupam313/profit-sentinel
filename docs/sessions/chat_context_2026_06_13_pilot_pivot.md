# Profit Sentinel — Chat Context (reasoning narrative)
## Date: 2026-06-13
## Session: PILOT PIVOT — pairs with state_2026_06_13_pilot_pivot.md

This file carries the WHY behind the decisions. The state file carries the WHAT.
Read both into the next chat. Nothing here is canonical.

---

## The pivot, in one line
We moved PS from "fully specify and build the autonomous 57-alert platform, then launch"
to "launch a thin-but-real BETA in 6 weeks, then run a free pilot for 3–4+ months on real
brand data, and build the rest from what real data teaches." The product the founder sees is
real and automated; the only concession to thinness is a limited alert set plus one human
relevance-gate before alerts reach founders.

## Why pivot (the load-bearing reasoning)
The single unvalidated assumption under the whole product — *will founders act on proactive
cross-source alerts they didn't ask for?* — cannot be resolved by more spec. Only real brands
on real data resolve it. The 57-alert library, 50 suppression rules, 13 gates, and the
multi-file spec system were over-building ahead of demand. The market is crowded (Triple Whale
etc.) and PS's moats are network/future ones that only accrue with many clients, so
speed-to-learning matters most. And the plan can't hinge on one cold contact (Aman).

## What "pilot" precisely means (corrected hard, twice)
Claude repeatedly mis-stated this and Anupam corrected it. The pilot is NOT a manual product
and NOT "Claude/Anupam supplies the reasoning by hand." It is the FULL product, automated
end-to-end — connectors, detection, system-GENERATED reasoning, checks, Evidence Stack, alert
language, Shopify app, NLQ, email. The ONLY two differences from full PS: (1) a limited alert
set instead of the deep causal graph across all 57; (2) ONE human relevance-gate — the system
fires the alert to Anupam, he checks the reasoning fits that specific brand, then releases it.
He is a relevance/release check on automated output, not a manual brain. This distinction is
the spine of everything; if a future chat drifts back to "manual," it is wrong.

## Point 1 — why each piece
- The founder-friction fear was real, but the fix isn't CSV — it's two developer-side approvals
  (read_all_orders + PCD) done once, after which install is a normal OAuth click. The surprise
  was PCD: reading orders at all triggers it (orders are customer PII), so it's a precondition,
  not a "later" item. That's why PII is on the critical path.
- Custom distribution beats admin-custom-apps (clunky, founder must create it) and beats public
  listing (heavy review, post-pilot). Its cost is the "not on the App Store" notice, which is
  structural to the light path — you can't remove it, only neutralize it with concierge onboarding.
  For 4–5 hand-held installs that's a non-event if pre-empted.
- Entity: NOT needed for Shopify approvals (individual path is explicit). The "need a company"
  noise online is about Shopify Payments. But register the Indian entity in parallel anyway,
  because the Google Ads token, VC-backed-brand DPAs, and liability all want it.

## Point 2 — the attribution thread (this drove a lot of the chat)
- The big realization: we should NOT compute our own per-channel ROAS. It would be lower than
  the founder's number (no Meta view-through post-Jan-12; lossy click capture), unverifiable, and
  it contradicts the founder's agency — the worst combo for a no-track-record tool, and Anupam
  flagged that this trust break was exactly why we'd parked it. So we ANCHOR to the founder's own
  number and add the returns truth on top.
- Blended-after-returns ROAS works because it's TOTAL revenue ÷ total spend — no attribution claim,
  so none of the lossy machinery is needed. View-only campaigns' spend just sits in the denominator;
  their effect is already in total revenue. (Anupam initially thought blended used "marketing revenue";
  the correction is that it's total revenue and makes no marketing-attribution claim.)
- The actionable returns alert is built to route AROUND lossy attribution: product return rate +
  reason (Shopify ground truth) × product-level SPEND (Meta product_id / Google shopping_performance_view,
  directly counted, not attributed) × campaign→product link (catalog/destination URL). A return RATE
  is a ratio, so lossy capture shrinks numerator and denominator together — robust where a ROAS sum
  is not. Anupam pushed hard on "isn't actionability also lossy?" and the answer is no: the action
  lives on the returns side (Shopify is ground truth, including sizing reasons), not the attribution side.
- Triple Whale / Hyros research confirmed: nobody reconstructs Meta view-through from the standard API
  post-Jan-12; Triple Whale uses its own server-side pixel for clicks and a recently-launched
  partnership integration for "deterministic views" — infrastructure PS doesn't have and shouldn't
  build for the pilot. Claude had earlier overstated "deterministic views are impossible"; corrected.

## The broad-campaign reckoning (Anupam was right)
Claude first said "focused campaigns only." Research showed ~70–80% of Meta spend is Advantage+/broad,
and Meta is ~63% of DTC spend — so broad campaigns are where the money is. We CAN see inside them:
Meta's API returns SPEND per product_id (directly counted, reliable), which is exactly what we need
(returns come from Shopify). Then a further correction: product_id only covers the catalog-served
portion; static creative is destination-URL-only; pure awareness maps to nothing. So coverage is
tiered, not total — strongest on catalog, partial on static-link, absent on generic. Honest.

## The "is this a small product?" reckoning (the make-or-break thread)
Running all 57 alerts through the filter: the differentiated MOAT concentrates almost entirely on
cross-source RETURNS intelligence. The entire B-series (creative/campaign) is commodity (visible in
Meta). D-margin is COGS-gated. F-conversion is Sentry-gated (Sentry is developer-skewed, not ubiquitous
at this tier — validated). H-series is plumbing. So the "57-alert platform" is oversold.
BUT — and Anupam's challenge forced this correction — Claude had conflated MOAT with VALUE and judged
the SHALLOW version of alerts. Dashboards DISPLAY but don't ALERT; single-source metrics still need
inference founders skip (overstock); and DEPTH (is-it-abnormal / precedent / which-cohort / why) makes
a number actionable — and that depth is usually itself cross-source. So on VALUE many more alerts survive;
on MOAT the density is cross-source returns. The product isn't shallow — its depth is concentrated, and
the differentiation is conditional on EXECUTION DEPTH (answer why, cross-source), not threshold-pings.

## Files / structure reasoning
- agent_d_build_spec is mis-named — it's the alert-LANGUAGE spec (G/F/E/D1), and the pilot reuses a lot
  of it (G1 language is literally in it). d1_validation_gates is a gate FRAMEWORK (reused) with
  D1/COGS-specific content (parked). cross_alert is the alert-INTERACTION map (reused as the manual-gate
  reference) + the automated-resolution engine (deferred). Agent B = the causal-graph traversal engine =
  the "deeper causal graph" that's deferred. Claude's earlier "parked foundations" label was too coarse;
  corrected to "design reused, autonomous execution deferred."
- One project, not a fork: memory and chat-search are project-scoped, so a fork duplicates files and
  risks the stale-mirror trap. Preserve the pre-pilot state with a git tag instead. Promotion-back path
  so PS doesn't rot while the pilot accumulates the real learning.

## On the save itself (why this file set, this way)
The chat was long and reversed itself several times, so the real save risk is capturing a SUPERSEDED
decision, not a dropped line. Mitigations used: a turn-by-turn coverage map, a supersession list (what
changed and what won), and three cross-checks (against memory, against canonical files, forward-vs-backward).
Cross-checks caught: memory's stale day-one alert set (#12), the carried-forward E5/E6 + namespace open
items, and that "returns-identity" and the alert disposition are NOT locked (forward-only, no user
confirmation) → tagged PROVISIONAL/OPEN. Only additive files were created; canonical edits deferred to
next session against live files. The honest residual: completeness still rests on Claude having read the
whole chat — the cross-checks shrink that risk but can't eliminate it.

## Working-relationship notes that held this session
Anupam corrected Claude on several reversals (manual-pipe, per-campaign ROAS, parked-files, single-source,
alert count). Mutual error-correction is working — but Claude's back-and-forth eroded confidence, and the
fix committed to going forward is: tag each claim by source (files / searched / inference) and mark
confidence per claim, separating doc-confirmed from brand-specific-unmeasurable. Honor "three genuine passes,"
plain language, no calcifying provisional items.
