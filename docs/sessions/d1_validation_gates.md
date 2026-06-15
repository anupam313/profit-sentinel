# Profit Sentinel — Alert Validation Gates
## Created: 2026-05-31 (D1 Gap 4 close)
## Status: LIVING DOCUMENT — go-live gates accumulate here across all alerts
## Last updated: 2026-06-08 — D1 Gap 6 residual pass: GATE D1-G13 added (BAU baseline excludes pre-sale ramps + onboarding two-pass backfill complete before D1 ships); D1-G5 scope extended to the CPM component's S38 explained-away suppression (universal go-quiet ceiling caps all components); the two still-open discount-depth/S19 items keep their deferred gates. | prior: 2026-06-04 — D1-G12 (Gorgias NLP parser per-brand accuracy) added; discount-depth/S19 interaction gates deferred to the cross-component residual pass

---

## PURPOSE

A go-live gate is a pass/fail acceptance test that **must pass before an alert
ships**. Gates exist so that a load-bearing dependency cannot be silently
forgotten in the post-H consolidated build — a failing test breaks loudly; a
priority label in a 30-item list gets skimmed past.

This file is separate from `agent_d_build_spec.md` on purpose:
- The spec defines *behaviour*. This file defines *pass/fail*.
- Gates will accumulate across every alert (D2–D6, C, B, A series), so they are
  a cross-alert artifact, not part of any single alert's spec.
- A gate's whole job is to be found at ship time — not buried at the end of a
  2,000-line spec.

Each alert's spec carries a one-line pointer to its gates here.

---

## GATE STATUS LEGEND

- **OPEN** — gate defined; the capability it tests does not yet exist (expected
  pre-build). Will fail until the dependency is built.
- **ENFORCED** — gate is wired into the validation run.
- **PASSED** — gate has passed against synthetic seed data.

---

# D1 — Contribution Margin Compression with Causal Driver

## GATE D1-G1 — S44 component-level suppression (BFCM + defective unit)
### Status: OPEN — blocked on schema (suppression_log component column)
### Source of truth: S44 worked example, seed_decisions_gap_f_g.md (BFCM + AZ-KNIT-031)

**Why this gate exists.** S44 (locked) requires D1 to be decomposed into
components and suppressed *per component*, so that a harmless seasonal
explanation for one component (CPM) cannot silence a real problem in another
(return rate). The single most important proof that Profit Sentinel is
intelligence and not a dashboard is that it catches the real problem during the
highest-suppression week of the year (BFCM) while correctly ignoring the
seasonal noise. If D1 goes fully silent during BFCM, it is indistinguishable
from a broken product.

**The scenario (from the seed data — do not invent values):**
- Date: November 28 2024 (BFCM peak).
- CPM spike: ~52% above baseline → seasonal, suppressible by S1.
- Simultaneously: supplier shipped 180 defective units of AZ-KNIT-031 (FW hero
  knitwear, wrong fabric weight). Gorgias `product_quality` tags rise 4% → 18%;
  Loop `return_reason = 'quality_issue'` spikes on AZ-KNIT-031 only; return rate
  on that SKU 61% vs 22% catalogue average.
- `brand_event_calendar`: the defect is seeded as `supplier_quality_event`, NOT
  as a sale/seasonal event — so S1 suppression does NOT reach the return-rate
  component.

**PASS criteria — ALL must hold:**
1. D1's **CPM component** is suppressed as seasonal (State 3 under S1) — NOT
   ranked as an actionable margin driver in the output.
2. D1's **return-rate component** is NOT suppressed and **fires** (defective unit
   is not seasonal).
3. D1 therefore **fires overall** (it does not go silent just because CPM is
   seasonal), surfacing the AZ-KNIT-031 return problem and the at-risk units.
4. The suppression is recorded **per component** in `suppression_log` (CPM →
   State 3; return-rate → not suppressed / State 1).

**FAIL by construction (the thing this gate guards against):**
- `suppression_log` keys suppression by `alert_type` only and has **no component
  field**. With the table as currently built, criterion 4 cannot be satisfied —
  there is nowhere to record "CPM component State 3, return-rate component
  State 1." A single whole-alert suppression row would suppress D1 entirely on
  the seasonal CPM read, the defective batch would go undetected, and the
  supplier-credit window would close. **This gate fails until a component
  discriminator is added** (`alert_component text`, or one row per component).

**Unblock requirement (BATCHED — post-H, no code now):**
- Claude Code schema change to `suppression_log`: add a component discriminator.
- This stays in the batched post-H build queue. It is NOT built early. This gate
  is the enforcement mechanism — the change cannot be skipped because the gate
  fails without it.

---

## GATE D1-G2 — Render-time suppression-state read (staleness)
### Status: OPEN
### Source: Gap 4 Step 2; FP4 / S48 staleness precedent

**PASS criteria:** D1 reads each component's `suppression_state` **as of the
alert week**, never a cached/stale value. Test by seeding a suppression window
that has already decayed (S41) by D1 render time and confirming D1 reads the
decayed state, not the original. (Mirrors the FP4 failure where a stale S14
suppression let A3 misfire.)

---

## GATE D1-G3 — Clustering-quality gate sets Stage-1 granularity (no silent brand-level fallback)
### Status: OPEN — blocked on the onboarding clustering-quality scorer + client_config granularity flag
### Source: Gap 6 (clustering-quality gate); technical_architecture.md "CLUSTERING-QUALITY GATE (onboarding)"

**Why this gate exists.** D1's return-rate component depends on category grouping.
If the AI clustering groups SKUs that do not behave alike on returns, category-level
diagnosis is noise dressed as precision. The gate guards against the product silently
degrading to brand-level without telling the founder — a silent degrade looks like
"no category problem" when the truth is "we couldn't trust the categories."

**PASS criteria — ALL must hold:**
1. At onboarding, clustering quality is scored on **return-rate coherence within
   clusters** (within-cluster SKU return-rate dispersion vs the brand-wide
   no-grouping baseline).
2. The score produces an explicit **per-brand granularity verdict** stored on
   `client_config`: category-granular **or** brand-level-with-disclosure.
3. When the verdict is brand-level, D1 operates at brand level **and emits the
   disclosure** that per-category diagnosis was withheld because the catalogue did
   not cluster cleanly enough to trust category attribution.
4. The brand-level path is **never silent**: a brand-level run with the granularity
   verdict set but no disclosure surfaced is a FAIL.

**FAIL by construction (the thing this gate guards against):**
- D1 returns a brand-level result with no granularity verdict recorded, or with a
  brand-level verdict but no founder-facing disclosure — i.e. a silent degrade.

**Unblock requirement (BATCHED — post-H, no code now):**
- Onboarding clustering-quality scorer + `client_config` granularity flag + the
  brand-level disclosure string. Stays in the batched post-H queue.

---

## GATE D1-G4 — Per-event prior-year coverage (account age is necessary, not sufficient)
### Status: OPEN — blocked on per-event prior-year analog lookup against brand_event_calendar
### Source: Gap 6 Dependency 1 (per-event prior-year coverage)

**Why this gate exists.** Seasonal suppression of a driver requires a prior-year
analog **for that specific event**. Account age ≥ 12 months is necessary but NOT
sufficient: a brand that has run for two years but is launching a NEW drop type
(e.g. its first outerwear collection) has no prior-year analog for that event, so
there is no admissible band to suppress against. The gate guards against treating
"the brand is old enough" as "this event has history."

**PASS criteria — ALL must hold:**
1. Before any seasonal suppression is applied to an event, D1 confirms a prior-year
   analog for **that event** exists in `brand_event_calendar` (event-anchored, not
   calendar-anchored).
2. An event with no prior-year analog → **fallback for that event** (narrate/disclose;
   no suppression), even when account age ≥ 12 months.
3. Account age alone never authorises suppression of an event that lacks its own
   prior-year analog.

**FAIL by construction:**
- D1 suppresses a NEW drop type as "seasonal/expected" purely because the account is
  ≥ 12 months old, with no prior-year analog for that specific event.

---

## GATE D1-G5 — Two-admissible-seasons gate for State 3 (mix-shift, return-rate, AND CPM explained-away seasonal suppression)
### Status: OPEN — blocked on the admissible-season counter + state-ceiling logic
### Source: Gap 6 Dependency 1 + return-rate component; matches agent_d_build_spec.md and technical_architecture.md state ceiling

**Why this gate exists.** State 3 ("suppress / stay silent") is the
highest-confidence claim D1 can make about a driver, not the lowest. Suppressing on a
single noisy prior season is how a real margin problem gets silenced as "seasonal."
This gate enforces the resolved state ceiling so the gate file does not drift from the
spec files.

**Scope.** This gate governs the **Gap-6 seasonal-typicality / explained-away suppression**
of the mix-shift driver, the return-rate component (the `seasonal_typicality_state` band),
AND — added 2026-06-08 (universal go-quiet ceiling) — the CPM component's S38 explained-away
suppression state. The admissible-season ceiling now caps EVERY component's go-quiet state,
so the S38 explained-away % can no longer suppress on its own. It still does NOT govern S1
calendar-EVENT suppression of the CPM component (an event either occurred or did not) — that
separate path is tested by D1-G1 and is unchanged.

**PASS criteria — ALL must hold (state ceiling by admissible-season count):**
1. **2+ admissible prior seasons** → State 3 (suppress / stay silent) is available.
2. **Exactly 1 admissible season** → ceiling is **State 2** (fire-with-context,
   **never** suppress).
3. **0 admissible seasons** → **narrate / disclose** (no band).
4. "Admissible" = **post-structural-break AND cost-coverage ≥ 0.85** for those weeks
   (a pivot / category addition discards pre-break seasons).
5. The grade is carried in `seasonal_typicality_state`, separate from
   `variance_explained_pct`.

**FAIL by construction (the thing this gate guards against):**
- A driver suppressed at State 3 with only 1 admissible prior season, or with a
  prior season that is pre-structural-break or below 0.85 cost coverage counted as
  admissible.

---

## GATE D1-G6 — "Extreme" magnitude defeats the size/photo softener (defect can't be masked)
### Status: OPEN — blocked on the group-own-band counter + materiality-floor (O-19)
### Source: Gap 6 Seam 2 (2026-06-03)

**Why this gate exists.** A recent size-guide/photography change may DOWNGRADE the
urgency of a return-driven margin finding to a watch-and-defer — but never when the
movement is too big to be a sizing reaction, or when the reason is quality/defect.
Mislabelling a defect as "probably settles" would lull the founder past the
supplier-credit window — the exact failure D1-G1 protects against.

**PASS criteria — the softener is FORBIDDEN if ANY one holds:**
1. Dominant return reason is quality/defect (Loop reason / Gorgias text).
2. **Level** — return residual in the far upper tail of the GROUP's own historical band
   (own-band method, finest clustering-certified granularity; NOT blended brand average,
   NOT a fixed pp / fixed ×).
3. **Exposure** — units / margin $ at risk cross the upper end of the brand's materiality
   band.
4. **Trajectory** — still climbing through the return window instead of cresting.

**FAIL by construction:** a "probably settles" softener applied to a quality/defect-coded
spike, or to a spike that clears any of tests 2–4.

---

## GATE D1-G7 — Thin group history → exposure fallback, not blended-average judgment
### Status: OPEN — blocked on per-group history sufficiency check
### Source: Gap 6 Seam 2 (2026-06-03)

**Why this gate exists.** When a group (e.g. a new line) has too little history to form
its own return band, the level test is unreliable. The system must NOT silently fall back
to judging it against the blended brand average (that both false-alarms and masks).

**PASS criteria:**
1. Insufficient group history → withhold the level judgment; decide on the EXPOSURE test
   (units / margin at risk) instead.
2. Never judge a group's return rate against the blended brand average.
3. Withhold-when-unsure resolves toward ACTION (surface), not toward silence.

**FAIL by construction:** a new line's return rate judged "normal" or "extreme" by
comparison to the brand blend; or a thin-history group silenced for want of a band.

---

## GATE D1-G8 — Brand-action quiet must be EARNED, never silent on an unconfirmed edit
### Status: OPEN — blocked on Tier-1 detection + content-diff
### Source: Gap 6 Seam 2 (2026-06-03)

**Why this gate exists.** Size-guide/photography change events have no reliable uniform
source. Quiet (suppression) granted on an unconfirmed or undetectable edit risks silently
muting a real return-driven margin leak.

**PASS criteria:**
1. A brand-action return event writes to context_alerts (narrate), never suppress_alerts
   (silent), unless corroborated — by reliable detection (Tier-1 metaobject webhook +
   content-diff above threshold) or founder confirmation.
2. Window = `return_window_days`, never a fixed 14/21.
3. A residual beyond the size-change explanation still fires (component isolation).
4. Without an affected_category, quiet is brand-wide WITH DISCLOSURE — never a silent
   brand-wide mute.

**FAIL by construction:** D1 goes silent on returns brand-wide off an unconfirmed
size-guide edit, with no disclosure and no residual escape hatch.

---

## GATE D1-G9 — No margin figure without a trustworthy cost feed
### Status: OPEN — Gap 6 COGS (2026-06-03)
### Note: depends on the FLAGGED Gap 1 tightening (component-only) — not yet confirmed

**Why this gate exists.** A margin VERDICT ("your margin is compressing") implies a
computed margin. Without trustworthy cost that figure can't be defended; the
cost-increase driver itself is structurally invisible without a feed.

**PASS criteria:**
1. `cogs_confidence_level = high` (trustworthy feed) → full margin alert permitted,
   including the cost-increase driver.
2. Not high → NO margin verdict and NO cost-increase driver. Brand receives component
   signals only (returns / CPM / discounting), which need no cost. *(Tightens Gap 1
   "driver-only" → "component-only"; FLAGGED PROPOSAL, gate is provisional until the
   founder confirms.)*
3. A cost-increase is never asserted for a non-feed brand on any inferred basis.

**FAIL by construction:** a margin % or $ shown, or a "supplier cost rose" driver fired,
for a brand without a trustworthy feed.

---

## GATE D1-G10 — Staleness-decay: claims narrow as cost ages
### Status: OPEN — Gap 6 COGS (2026-06-03)

**Why this gate exists.** Cost goes stale silently; a confidently wrong (stale) cost
produces false reassurance — a healthy-looking margin while the brand bleeds.

**PASS criteria:**
1. Staleness = today − `cogs_last_confirmed_at`, compared to the founder's own
   `cogs_refresh_rhythm_days` (never a fixed interval).
2. Within rhythm → full margin figures, no footnote.
3. Past rhythm → live caveat naming the cost date and age; figures still shown but
   flagged.
4. Well past rhythm → NO margin figure; component signals only until reconfirmed.
5. Disclosure is STATE-DRIVEN — never a footnote on every alert; basis available on
   demand even on clean alerts.

**FAIL by construction:** a full-confidence margin figure on cost older than the brand's
stated rhythm, or a footnote stapled to every alert regardless of freshness.

---

## GATE D1-G11 — Revenue-weighted cost coverage, not blanket confirmation
### Status: OPEN — Gap 6 COGS (2026-06-03)

**Why this gate exists.** "Is your Shopify cost right?" is one yes/no over hundreds of
SKUs; it's typically right for top sellers and stale/zero on the long tail.

**PASS criteria:**
1. Treat cost confirmation as coverage — `sku_cost_coverage_by_revenue` (reuse Gap 1) —
   not a brand-level boolean.
2. The alert speaks confidently only for the revenue actually costed; uncovered revenue
   is excluded from any margin figure and disclosed.

**FAIL by construction:** a margin figure stated for revenue whose SKUs have no cost, on
the strength of a blanket "it's fine."

---

## GATE D1-G12 — Gorgias NLP parser accuracy verified per brand before any pilot client
### Status: OPEN — Gap 6 discount-depth/S19 (2026-06-04)
### Source: technical_architecture.md 2026-06-04 appendix (Gorgias NLP parser)

The parser feeds multiple alerts (sizing-complaint velocity, return-reason context, the
retrospective sale review, the sale-period channel). Because the product's moat is
precision, the parser's accuracy on a brand's ACTUAL ticket language must be MEASURED,
not assumed, before that brand sees any parser-derived output.

**PASS requires, per brand at onboarding:**
1. Parser intent/reason labels checked against a human-labelled sample of that brand's
   real tickets; accuracy clears a stated bar on the load-bearing classes (sizing
   direction, quality/defect, not-as-pictured).
2. A stated multi-intent rule is applied (a ticket carrying multiple signals is not
   double- or under-counted).
3. The parser reads the customer's own messages only (not macros/canned replies) and
   reports LOW-SIGNAL when a brand's tickets are mostly templated — dependent alerts then
   degrade honestly rather than fire on thin signal.

**FAIL by construction:** a parser-derived alert shown to a pilot client on the strength
of "the model is generally good," with no per-brand accuracy measurement; or a velocity
alert firing off a live window below the minimum ticket count (small-sample handling is a
firing floor, not historical depth).

**NOT gated here (still deferred, O-24):** TWO discount-depth/S19 interaction items remain
design-deferred because they are STILL OPEN as of 2026-06-08 — the new-vs-existing customer
split for a suppressed sale's downstream returns, and the thin-baseline confidence handling.
Their gates are written when they close (which also closes Gap 6). The rest of the 2026-06-08
residual pass DID lock: the BAU pre-sale-ramp exclusion + onboarding backfill is now gated by
D1-G13 below; fulfilment retirement, the measured-not-explained rule, the all-explained
two-door fire, and the universal go-quiet ceiling are spec-level invariants (the ceiling's
enforcement rides D1-G5).

---

## GATE D1-G13 — BAU baseline excludes pre-sale ramps before D1 ships
### Status: OPEN — blocked on the pre-sale-ramp detector + onboarding two-pass backfill
### Source: Gap 6 residual pass (2026-06-08); agent_d_build_spec.md BAU definition + technical_architecture.md qualifying BAU day; build items D-GAP6-25

**Why this gate exists.** A pre-sale awareness ramp (spend up, traffic up, conversion soft,
no discount yet) is caught by none of the event / echo / launch / influencer / peak
exclusions. Left in the BAU set it drags the margin band DOWN, lowering the firing bar
everywhere the baseline is read — Trigger A, Trigger B, the structural-break comparison, and
the seasonal bands. The first baseline must be certified clean of historical ramps before any
D1 alert ships, or the product fires (or stays silent) against a polluted reference.

**PASS requires:**
1. `pre_sale_ramp_active` is in the qualifying-BAU-day exclusion list AND honoured by the live
   scan (no ramp day enters the baseline).
2. The onboarding TWO-PASS backfill has run: pass 1 detected historical ramps on raw history;
   pass 2 rebuilt the baseline excluding them. The first certified baseline reflects pass 2.
3. The ramp detector's thresholds are LEARNED from the brand's own past ramps (not a fixed
   multiple) and gated by the same admissibility ladder used elsewhere — a brand with too
   little history to detect ramps reliably is disclosed, not silently trusted.

**FAIL by construction (the thing this gate guards against):** a first baseline certified
clean while a known pre-sale ramp sits inside it, so the firing bar is quietly depressed and a
real compression later reads as "within band."

---

## NOTES FOR FUTURE GATES

- D1's F2 Step-0 branch is NOT yet gated — the F2-vs-S44 precedence conflict is
  unresolved (O-5, orchestration pass). Add a gate once ratified.
- B/C/A series gates to be added as those reviews complete.
