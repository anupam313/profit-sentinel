# Profit Sentinel — Session State
## Date: 2026-06-02
## Session: D1 Gap 6 WIP — 2 dependencies CLOSED, return-rate component PARTIAL
## Supersedes: state_2026_06_01_d1_gap5_closed.md (KEEP both — prior retained as audit trail)

---

## SESSION SUMMARY

Worked D1 Gap 6 (Seasonality suppression + the Gap-6 half of O-14). **Gap 6 is
NOT closed — roughly half done.** Both named dependencies are CLOSED. Of the four
non-CPM S44 components owed the O-14 reconciliation, only **return-rate** was
worked, and it has two open seams. Three components (COGS/S21, discount-depth/S19,
operational-cost/S20) are untouched. A large amount of supporting design was
settled: category resolution, event-calendar sourcing, the Phase-1 seed question,
and the weekly digest.

The discipline that "return-rate is a near-mechanical repeat" was explicitly
WRONG — the component held substantial hidden structure (three rules of three
different shapes, two unlisted rules). Do not assume the remaining three are clean.

Three of my own earlier positions were RETRACTED during the session and must not
be re-litigated as if still live (detail in chat_context):
1. "Organic virality is margin-accretive, nothing to suppress" — WRONG. It
   compresses CM% via discount-depth (new-customer welcome codes) and return-rate.
2. The three-state cold-start→blend→mature threshold *lifecycle* — RETRACTED for
   Phase 1. No trustworthy seed exists pre-benchmark; use brand-own-data or
   narrate-don't-suppress.
3. The viral "modeled return-echo window" + overlap handling — RETRACTED. Observe
   the tagged cohort, don't model an echo; one-off virals get no forward tracking.

---

## GOVERNING PRINCIPLES — LOCKED (cumulative)

Carried forward (unchanged):
- Monitor-and-Wait Principle (2026-05-23)
- Action-First Principle (2026-05-23)
- No Margin Figure Without Reliable COGS (2026-05-26 Gap 1)
- No Hardcoding Principle (2026-05-26 Gap 2)

Added this session (refinements / new):
- **Phase-1 No-Seed Principle (2026-06-02).** A threshold may not be a guessed
  constant used to *suppress*. Either it is derived from the brand's own admissible
  history, or — where there is no history and no cross-client benchmark (Phase 1) —
  the system NARRATES and does not suppress. Seed-blending returns only in Phase 2
  when the Fashion Intelligence Network supplies a real benchmark. Constants that
  remain (e.g. classifier cutoffs) are labelled provisional placeholders, never
  hardened.
- **Measure-Before-Build (2026-06-02).** When a design rests on an unproven
  empirical assumption (e.g. "text clustering is stable enough"), do not design a
  fallback around the assumption — build a per-brand measurement gate that tests it
  and discloses the result, and never fall back silently to a coarser answer that
  produces confident-wrong output.
- **Observe-Don't-Predict (2026-06-02).** For events with no stable repeatable
  pattern (viral), measure the actual cohort/outcome rather than modelling a
  predicted window.

---

## WHAT PROGRESSED IN GAP 6

### Dependency 1 — SKU mix-shift seasonal suppression — CLOSED
Grade the mix-shift driver, but grade its **margin impact**, not the category-share
shift, and do it with **IQR percentile position inside the brand's own prior
same-season margin band** — NO z-score (z-score fails: a brand observes a given
season ~once/year, so small-n is the permanent regime, not a cold-start phase; and
category share is the wrong quantity — D1 cares about CM%).
- State carried in a **separate `seasonal_typicality_state` field**, mapped to the
  same State 3/2/1 labels and decayed by S41 (the smooth-decay rule). MUST NOT be
  written into `variance_explained_pct` (that field means seasonal *attribution*;
  typicality is a different quantity — overloading it corrupts S42 stacking + S39
  learning).
- **Spend-reallocation disqualifier runs BEFORE the seasonal grade**: a shift that
  co-moves with a deliberate spend reallocation is not eligible for seasonal
  suppression at all. (This is a piece of Gap 8 Finding B pulled forward — BOUNDARY
  STILL FOUNDER'S CALL: keep in Gap 6 or return wholly to Gap 8. Logged, unresolved.)
- **Admissibility — a prior season counts only if BOTH:** (a) no structural break
  separates it from now (reuse the locked structural-break rule; a pivot/category
  addition discards pre-break seasons), AND (b) cost coverage ≥ 0.85 for those weeks.
- **State ceiling by admissible-season count:** 0 → no band → narrate/disclose
  fallback; 1 → fragile band → State-2 ceiling (fire-with-context, NEVER suppress);
  2+ → full band → State 3 available. Suppression (State 3) is the HIGHEST-confidence
  claim, not the lowest — a fragile band removes the right to suppress.
- **Event-anchored band, NOT calendar-anchored** — "prior-year same season" = same
  N weeks relative to the prior-year launch in `brand_event_calendar` (match S2/S46),
  so the CPM and mix-shift seasonal lenses can never point at different weeks for the
  same launch (O-14 guarantee).
- **Per-event prior-year coverage**, not per-account history: a NEW drop type has no
  analog even for a 2-year-old brand → fallback for that event.
- One calibrated **sensitivity multiplier** (State-2↔State-1 edge) — provisional
  placeholder, outcome-calibrated, guardrailed (Gap 2 pattern). NOT a 6th S44
  component (Gap 5 locked S44 at five).

### Dependency 2 — Organic-viral detection — CLOSED (D1-scoped part); rewrite → O-11
- **Reframe: NOT blanket suppression.** D1-scoped behaviour = (a) exclude surge days
  from the BAU baseline + (b) **concurrent discount-depth read**, surfaced WITH viral
  context, gated by the O-19 materiality + actionability floor. Blanket suppression is
  wrong because the discount-depth compression (new-customer welcome codes) is the one
  actionable lever and suppression would hide it.
- **Detect via S33's brand-level new-customer-pct surge signal** (>15% surge), NOT the
  spec's single-SKU `+2SD` revenue test. Virality is multi-product / brand-level; the
  seed scenarios themselves are brand-level (800 / 1,200 new customers).
- **Founder confirmation = the organic-vs-engineered discriminator** (the no-spend
  signal can misread an engineered push). Default to provisionally-locked-and-tracking
  if unconfirmed — confirmation is not a blocking dead-end.
- **DROPPED:** forward 30/60/90 repeat tracking in D1 (no actionability for a one-off,
  non-repeatable event); viral-specific returns model (returns flow through the normal
  return-rate component); overlap handling (it was an artifact of the abandoned echo
  model). Repeat maturation stays entirely with S33/E2.
- **S33's 20% viral-cohort repeat-rate cutoff is HARDCODED → make brand-relative**
  (below the brand's own new-customer-cohort repeat-rate band). Logged against S33.
- **Routed to O-11 (shared detector rewrite, NOT a Gap 6 edit):** separate
  `organic_viral` from `collection_launch` (different metrics — new-SKU *count* vs
  single-SKU *revenue*; different recovery clocks); fix the spec self-contradiction
  ("spend optional" vs "no-spend required"); C6 is *corrupted* by the conflation
  (watches a viral existing SKU as a new collection); E2 is *double-suppressed*
  (launch logic + S33). Neither C6 nor E2 relies on viral being actively suppressed —
  verified. Detector lives in causal_graph.py (batched) + is shared D1/C6/E2.

### Return-rate component (O-14) — PARTIAL
- **Two-stage consumption** (unlike CPM's one stage):
  - **Stage 1 — expected return rate by category mix** = S15's real job. S15 is a
    BASELINE-SETTER (a *level*), not a suppression state-producer (a *delta*). A new
    high-return category (formalwear ~38%) raises the resting expectation permanently;
    treating S15 as a decaying suppressor would either fire forever or blanket-mute a
    category and miss a real defect inside it.
  - **Stage 2 — grade the RESIDUAL** (actual − expected) via S3/S16 → S38 → S41. D1
    reads only the Stage-2 verdict.
- **S15 reclassified from "suppression rule" to "baseline rule"** in how D1 uses it —
  diverges from S44's literal listing. LOGGED for the orchestration pass (S-series
  semantics), resolved on the D1 side now.
- **S3 re-anchored** (the post-holiday rule): retire hardcoded Jan 1–21 / Jan 22
  cliff. Derive the brand's actual holiday SELLING window from its own revenue
  concentration + `brand_event_calendar`, **width-matched**, push forward by the
  brand's `return_window_days` → that is the expected return-spike window. State 3
  across it; **S41 owns the decay** (no date cliff). First-holiday-with-no-prior-year
  → narrate/disclose (per-event coverage gate).
- **Component isolation already PROVEN** (good news): the S44 block's Nov-2024
  BFCM-plus-defective-units scenario shows CPM suppressed (seasonal) while return-rate
  FIRES (defect, not seasonal). Core consumer pattern is sound for this bucket.
- **OPEN — Seam 2 (S17/S18 cross-alert gap):** S44 maps only S3/S15/S16 to the
  return bucket, but S17 (size-guide rule) and S18 (photography rule) also move
  returns and are scoped to C3. A size-guide return spike would suppress for C3 but
  NOT be recognised by D1 → D1/C3 disagreement = the O-14 contradiction across alerts.
  UNRESOLVED.
- **OPEN — C3 consistency check:** does C3 also apply S15 as its return baseline? If
  so the two-stage model must be consistent across D1 and C3. UNRESOLVED.

### Category resolution — DECIDED (verified existing logic; extension, not net-new)
- **Exists already:** `connectors/category_inference.py` populating
  `sku_cost_master.founder_category` (display label) + `ai_inferred_category` (Claude
  API from title/tags/vendor/collection/product_type) + `category_inference_confidence`.
  product_type is already the LEAST-trusted input.
- **Use AI clustering for INTERNAL grouping** (Stage 1, mix-shift) — the spec is
  collection-FIRST, which is risky because collections in this segment are often
  promotional ("Bestsellers", "Sale"). Keep collection/`founder_category` for DISPLAY;
  internal grouping uses the AI clustering. Internal clustering does NOT need the
  founder rename (rename is a display gate only).
- **STRIKE "mandatory founder rename step"** as written — cannot ask founders to label
  hundreds–thousands of SKUs.
- **New-category CLASSIFICATION + sub-category depth → DEFERRED to multi-client /
  Phase 2** (needs cross-client taxonomy; can't calibrate the new-vs-drift parameter
  on one brand). Phase-1 gap is covered by **structural-break + narrate**: the break
  detector (which already lists "category addition") sees the shift; the digest says
  "margin moved, traces to a group we haven't seen before" — no naming, no founder
  labelling, no wrong suppression.
- **Clustering-quality gate (Measure-Before-Build):** per-brand at onboarding, scored
  on **return-rate coherence within clusters** (tight intra-cluster return distribution
  = real category; bimodal = junk cluster) + cross-signal agreement. Verdict:
  category-granular Stage 1, OR brand-level Stage 1 WITH DISCLOSURE. NEVER a silent
  coarse fallback (that produces confident-wrong attribution in the beta window).
- **Text-only clustering for Phase 1.** Images would add correlated noise (vision
  clusters on colour/silhouette/lookbook style → groups by campaign/season, the wrong
  latent variable) at real cost. Images DEFERRED to a Phase-2, discovery-gated
  *return-causation* probe (fit/fabric/colour mismatch), NOT category grouping.
  Logged reopen condition: "catalogue copy too sparse to cluster" (named-not-described
  catalogues).
- **0.70 confidence gate redefined:** it should be **cross-signal AGREEMENT**
  (title/description/tags/vendor/collection concurring), NOT the model's self-reported
  confidence (uncalibrated). The existing onboarding review is the calibration set.
  0.70 = provisional placeholder, outcome-calibrated. Honest residual: signals can be
  confidently wrong in unison (text usually breaks the tie → text stays heaviest).

### Event calendar — VERIFIED + DECIDED
- **Auto-populated by `historical_pattern_scan.py`** at onboarding + monthly
  incremental (Approach B: qualify high-order-volume days, classify by the brand's own
  discount-depth p50/p75, cluster consecutive days bridging ≤2-day gaps). **No founder
  input.** So "brands change dates/durations" is already handled — the window follows
  behaviour and re-derives monthly.
- **Confound guard needed (logged):** Approach B will mislabel an unplanned
  competitor-reaction markdown or a viral-driven discount as a planned `sale_period`
  and let it earn suppression. Require corroboration / founder-confirm (same viral
  path) before treating a detected window as a *planned* seasonal event; uncorroborated
  → narrate-don't-suppress.
- **Event naming:** auto-label generically (date lookup names BFCM/holiday/seasonal
  launches for free); the engine depends on the window+depth, not the name. Earn real
  names LAZILY — ask one targeted question on the SECOND occurrence of an idiosyncratic
  recurring event ("you ran this last year too; what do you call it?"). Never block
  onboarding on naming.

### Weekly digest — ROUTED to Gap 8 / Gap 9
Suppressed (expected) leaks SHOULD appear in a weekly digest (not as alerts): show
**magnitude + reason**, never the internal mechanics, gated by suppression confidence
(don't expose fragile cold-start suppression to scrutiny it can't survive). This is
the Gap 8 ("explained ≠ can't act") + Gap 9 ($-impact display) question — logged as
input there, not designed now.

---

## PARKED FOR POST-H SPEC (stored, not for resolution now)

- **Clustering-coherence validation — additional factors beyond return-rate.**
  Candidates to evaluate at post-H spec: price-band tightness within a cluster,
  margin-rate coherence, discount-behaviour similarity, size/fit-complaint profile,
  AOV consistency. (Founder request, 2026-06-02.)

---

## OPEN IN GAP 6 (must close before Gap 6 is done)

1. Return-rate **Seam 2** — S17/S18 vs C3 cross-alert gap.
2. Return-rate **C3 consistency check** — does C3 apply S15 as its baseline.
3. **COGS / S21** component — untouched (seam check, not assert-clean).
4. **discount-depth / S19** component — untouched (expect heavy interaction with the
   viral welcome-discount + auto-populated sale calendar work).
5. **operational-cost / S20** component — untouched.
6. **Final cross-component residual-disclosure consistency pass** — confirm all five
   suppressed components feed `total_measured_impact` / the residual gate identically
   (flagged back in the mix-shift work, never returned to).

---

## PENDING SPEC EDITS (itemized — apply to canonical files; nothing lost if 3–7 not rewritten this session)

**agent_d_build_spec.md**
- GAP 6 DEPENDENCIES: mark Dependency 1 (mix-shift) and Dependency 2 (organic-viral)
  RESOLVED, with the full resolutions above (esp. grade-margin-impact / IQR / separate
  `seasonal_typicality_state` / admissibility / state ceiling / event-anchor /
  per-event coverage; and viral = baseline-exclusion + concurrent discount read via
  S33 signal, forward tracking dropped).
- Add "RETURN-RATE COMPONENT (O-14) — TWO-STAGE CONSUMPTION (PARTIAL)" with Stage 1 /
  Stage 2, the S15 baseline-setter reclassification, S3 re-anchoring, and the two OPEN
  seams (S17/S18 vs C3; C3 consistency).
- Record the Phase-1 No-Seed retraction (S15 thresholds dormant Phase 1; S16 tiers
  brand-own; S3 dates event-derived).

**cross_alert_orchestration.md**
- **O-11** — expand: separate organic_viral from collection_launch; spec
  self-contradiction; new-SKU-count vs single-SKU-revenue metric split; C6 corruption;
  E2 double-suppression; detector shared D1/C6/E2 + batched. Add the S33-window /
  D1-cadence alignment note (D1 consumes S33's surge *event*, not its 90-day window).
- **O-14** — mark Gap-6 half PARTIAL: CPM done (Gap 4); return-rate partial (2 seams
  open); COGS/discount-depth/operational-cost untouched.
- **O-19** — add inputs: viral concurrent-discount surface needs a materiality floor +
  an **actionability gate** (is a lever still available — harder than magnitude, may
  degrade to "surface the lever, founder judges"); weekly-digest-of-suppressed-leaks
  belongs here + Gap 9.
- Add **S15 relabel** (suppression rule → baseline rule) as an orchestration-pass item.
- Add **S33 20%-cutoff → brand-relative** as an item.
- Add **brand_event_calendar confound guard** (unplanned markdown / viral mislabeled
  `sale_period`).
- Add **final cross-component residual-disclosure consistency pass** as a Gap 6 closeout
  item.

**technical_architecture.md**
- `sku_cost_master`: STRIKE "Mandatory founder rename step before any alert uses this
  label" for `ai_inferred_category`; note internal grouping uses AI clustering without
  rename (rename = display gate only); note `category_inference_confidence` is to be
  redefined as cross-signal agreement, 0.70 provisional.
- Add **clustering-quality gate** (onboarding; return-rate-coherence scored; per-brand
  granularity verdict; brand-level-with-disclosure as the explicit low-quality path).
- Add **`seasonal_typicality_state`** field for the mix-shift driver (separate from
  `variance_explained_pct`).
- S3 / post-holiday return window: replace fixed Jan dates with the event-derived
  (sales-concentration + `brand_event_calendar`, width-matched, + `return_window_days`)
  window; S41 owns decay.
- Note the brand_event_calendar Approach-B confound guard.

**product_strategy.md**
- Section 12: add weekly-digest-of-suppressed-leaks (routed to Gap 8/9); add Phase-1
  vs Phase-2 category sequencing (internal clustering now; confident new-category
  classification deferred to the multi-client / Fashion Intelligence Network phase).

**d1_validation_gates.md**
- New gates: clustering-quality gate (sets Stage 1 granularity per brand); per-event
  prior-year coverage gate; two-admissible-seasons gate for State 3 (mix-shift +
  return-rate seasonal suppression).

**NOT now:** causal_graph.py (batched post-H); seed_decisions_gap_f_g.md S-rule
definition edits (S15/S3/S16/S33 reclassifications logged for orchestration pass).

---

## D1 GAP STATUS

| Gap | Status |
|-----|--------|
| Gap 1 — COGS tier disclosure | LOCKED ✓ |
| Gap 2 — Threshold (Trigger A + B) | LOCKED ✓ |
| Gap 3 — Causal decomposition | LOCKED ✓ |
| Gap 4 — CPM → margin intermediate steps | DESIGN-COMPLETE ✓ (blocked on schema gate D1-G1) |
| Gap 5 — AOV decline retired as a driver | LOCKED ✓ 2026-06-01 |
| Gap 6 — Seasonality suppression | **WIP** — 2 dependencies CLOSED; return-rate PARTIAL (2 seams open); COGS/discount-depth/opex untouched; final residual pass owed |
| Gap 7 — "Entirely explained" framing retired | PENDING (inherits Gap 5 "AOV moved but margin held"; + S3 "abnormal-for-season" residual trap) |
| Gap 8 — No action named per driver | PENDING (inherits "explained ≠ can't act" + O-19 Findings A/B + floor + actionability gate + digest) |
| Gap 9 — No $ revenue impact (display) | PENDING (inherits Gap 5 note + digest) |

---

## ALERT REVIEW STATUS (unchanged except D1 Gap 6)

G COMPLETE ✓ · F COMPLETE ✓ · E1 COMPLETE ✓ · E2/E3/E4 DEFERRED Phase 2 · E5/E6
reconcile (O-15) · D1 IN PROGRESS (Gaps 1–5 done; 6 WIP; 7–9 pending) · D2–D6 pending
· C pending · B pending · A pending · orchestration resolution pass AFTER A · H last.

---

## PENDING CLAUDE CODE ACTIONS (accumulate — execute after H-series)

Carry forward all prior. New this session (all BATCHED, none built now):
- suppression_log component column — ship-blocker, gate D1-G1 (Gap 4, carried).
- Do NOT add a CTR delta mart column (Gap 4, carried).
- Register D1↔B1/B4 router as proposed S35 addition (O-13, carried).
- `seasonal_typicality_state` field (mix-shift) — separate from variance_explained_pct.
- Clustering-quality gate at onboarding (return-rate-coherence scored).
- S3 event-derived return-window logic (replace fixed Jan dates).
- Shared launch-detector rewrite (O-11) — organic_viral vs collection_launch.
- Make S33 20% cutoff brand-relative.
- No consolidated Claude Code prompt until after H-series.

---

## NEXT SESSION STARTING POINT

New chat. Load: this file · agent_d_build_spec.md · cross_alert_orchestration.md ·
product_strategy.md · technical_architecture.md · d1_validation_gates.md · plus
chat_context_2026_06_02_d1_gap6_wip.md.

**FIRST: apply the PENDING SPEC EDITS above to files 3–7** (clean chat, low error
risk), re-upload, then continue.

**Then resume Gap 6, one-by-one:** close return-rate Seam 2 (S17/S18 vs C3) + the C3
consistency check → then COGS/S21 → discount-depth/S19 → operational-cost/S20 → final
cross-component residual-disclosure pass. Verify each against source before proposing;
do NOT assume any component is clean.

Sequence after Gap 6: 7 → 8 → 9 → D1 alert language → D2 → D3 → D5 → D6 → C → B → A →
orchestration resolution pass → H → consolidated CC prompt. (No alert language until
all 9 D1 gaps resolved.)
