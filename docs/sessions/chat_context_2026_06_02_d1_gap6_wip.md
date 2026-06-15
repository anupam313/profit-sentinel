# Profit Sentinel — Chat Context (Reasoning Log)
## Date: 2026-06-02
## Session: D1 Gap 6 WIP — dependencies closed, return-rate partial
## Pairs with: state_2026_06_02_d1_gap6_wip.md

Purpose: preserve the *reasoning* (not just the decisions) so the next chat does
not re-litigate settled arguments. Decisions and pending edits are in the state file.

---

## ARC OF THE SESSION

Opened on Gap 6 = write D1's seasonality suppression as a CONSUMER of the S-series
(S44 decompose → S38 grade explainability → S41 decay), the same move Gap 4 made for
CPM, for the rest of D1's components — plus the two logged dependencies.

The session never produced alert language (constraint: not until all 9 gaps close).
Everything stayed at design/spec level; all code batches to post-H.

---

## DEPENDENCY 1 — MIX-SHIFT — HOW WE GOT THERE

Started from the spec's pre-condition 6 (binary: "suppress if within prior-year
same-season ±1 SD"). Decided to GRADE it. Then four successive corrections, each
driven by founder pushback, reshaped *what* we grade:

1. **z-score is the wrong tool.** A brand sees a given season ~once a year, so you
   never escape small-n — it is the permanent regime, not a cold-start. With 12
   months history you have ONE same-season observation, so `prior_year_same_season_sd`
   is within-season week noise, not year-over-year variability. So no z-score.
2. **Category share is the wrong quantity.** D1 fires on CM% rate. So grade the mix
   driver's MARGIN IMPACT, not its category-share shift. Share is observed yearly
   (starved); margin is observed weekly (rich). Use IQR percentile position in the
   brand's own prior same-season *margin* band (matches D1's existing IQR baselining,
   which deliberately avoids SD/z and avoids 180-day windows for seasonal contamination).
3. **Don't overload `variance_explained_pct`.** That field = seasonal *attribution*;
   a typicality percentile is a different type. Overloading corrupts S42 stacking
   ("most conservative residual") and S39 learning. Use a separate
   `seasonal_typicality_state`, same State 3/2/1 labels, same S41 decay.
4. **Typicality ≠ causation (the confound).** "Typical magnitude for the season" does
   not mean "caused by the season." A founder-driven outerwear push lands inside the
   band. So the spend-reallocation co-movement check (Gap 8 Finding B) runs BEFORE the
   grade as a disqualifier. (Boundary to Gap 8 left as founder's call.)

Then the "comparing wrong time periods because the brand has moved on" worry was
reframed as an ADMISSIBILITY problem, not a tuning problem:
- A prior season is admissible only if (a) no structural break separates it from now
  (the locked break rule already discards pre-break data — a pivot excludes its prior
  seasons; this is detection, not a guessed staleness window) AND (b) cost coverage
  ≥0.85.
- Admissible-season count sets the ceiling: 0 → narrate; 1 → State-2 (fragile band
  can't earn the right to SUPPRESS, because State 3 is the highest-confidence claim,
  not the lowest); 2+ → full.
- Band must be EVENT-anchored (launch window in brand_event_calendar, matching S2/S46),
  not calendar-anchored, or D1's CPM lens and mix lens point at different weeks for the
  same launch and contradict each other (the O-14 failure). Coverage is PER-EVENT (a
  new drop type has no analog even for an old brand).

---

## DEPENDENCY 2 — ORGANIC-VIRAL — THE WALK-BACK

My first analysis said virality is margin-ACCRETIVE (full-price organic demand, no
CAC) so there's little for D1 to suppress. Founder objected on two fronts and was
right on both:
1. Virality is multi-product / brand-level, not single-SKU (the spec's single-SKU
   +2SD detector is wrong; the seed scenarios are brand-level — 800 and 1,200 new
   customers from a newsletter and a celebrity post).
2. The new-customer flood redeems first-purchase/welcome discounts and returns at a
   higher rate → CM% DOES compress via the discount-depth and return-rate channels.

So I RETRACTED "accretive, nothing to suppress." But the correction *strengthened* the
anti-suppression conclusion for a better reason: since real compression exists,
blanket suppression would HIDE the one actionable lever (welcome-discount exposure).
So D1-scoped behaviour = baseline-exclusion + a CONCURRENT discount-depth read,
surfaced with viral context, gated by O-19 materiality + actionability.

Key discovery: **S33** (new-customer-pct surge >15% → suppress E2 90 days for cohort
maturity) is the existing, locked, BRAND-LEVEL signal for exactly this dynamic —
better than the single-SKU detector. D1 should consume S33's surge SIGNAL.

Then two more simplifications, both founder-driven:
- The S33 90-day window is a *cohort-maturity* (retention) clock, not a *margin* clock.
  Don't borrow it. D1 consumes the surge EVENT, applies its own concurrent discount
  read. (Originally I proposed reusing the launch return-echo machinery — RETRACTED:
  viral has no stable pattern to model; observe the tagged cohort instead.)
- For a true ONE-OFF viral event, forward 30/60/90 repeat tracking in D1 derives NO
  founder action (can't re-run the celebrity post, can't un-give the discount). So
  drop it — repeat maturation stays with S33/E2. With forward tracking gone, the
  "overlapping surges" residual disappears (it was an artifact of the echo model).
  Concurrent discount read survives because it IS actionable in real time.

Founder confirmation kept as the organic-vs-engineered discriminator (the no-spend
signal can misread an engineered push); default to provisionally-tracking if
unconfirmed.

Shared-detector rewrite routed to O-11 (verified: C6 is corrupted by the conflation —
it would watch a viral existing SKU as a new collection; E2 is double-suppressed by
launch logic + S33; neither relies on viral being actively suppressed). Detector is
in causal_graph.py and shared D1/C6/E2, so it's an orchestration decision, not a
unilateral Gap 6 edit.

---

## RETURN-RATE COMPONENT — WHY IT WASN'T "CLEAN"

I had earlier called the four non-CPM components a "near-mechanical repeat." Verifying
return-rate against source disproved that:
- The S44 block already PROVES component isolation works (Nov-2024 BFCM + defective
  AZ-KNIT-031: CPM suppressed seasonal, return-rate FIRES on the defect). Good.
- BUT the three mapped rules are three different SHAPES: S3 grades a spike by DATE
  (calendar-anchored, own decay cliff), S16 grades by MAGNITUDE (pp tiers), and S15 is
  not a spike-grader at all — it sets the EXPECTED return rate per category (a level).
- And two rules that move returns (S17 size-guide, S18 photography) are scoped to C3,
  NOT listed under D1's return bucket → potential D1/C3 disagreement.

So the consumption is TWO-STAGE: Stage 1 sets expected return rate by category mix
(S15's real job — a new high-return category raises the resting expectation
permanently, which a decaying suppressor can't represent); Stage 2 grades the residual
(actual − expected) via S3/S16 → S38 → S41, which is what D1 reads. S15 is therefore a
BASELINE rule, not a suppression rule — reclassification logged for orchestration.

S3 re-anchored (founder: brands run events 3 days / 5 days / 2 weeks — fixed Jan dates
are dangerous): derive the holiday selling window from the brand's own revenue
concentration + brand_event_calendar, width-matched, + return_window_days; S41 owns
decay; retire the Jan-22 cliff.

OPEN: S17/S18 vs C3 seam; whether C3 also applies S15 (two-stage must be consistent
across D1/C3).

---

## THE SEED RETRACTION (applies broadly)

I proposed a three-state threshold lifecycle (cold-start seed → blend → mature
brand-derived). Founder pushed: (a) onboarding ALREADY pulls brand history, so an
established brand isn't really "cold-start" for existing slices; (b) in Phase 1 there
is no cross-client benchmark, so a seed like "formalwear returns 0.38" is a guess, and
a guess that SUPPRESSES is worse than silence. RETRACTED for Phase 1.

Phase-1 model is two states, not three: brand-own admissible history when available
(the dominant case for the ICP); narrate-don't-suppress for a genuinely new slice or a
first-time event. Seed-blending returns only in Phase 2 with a real Fashion
Intelligence Network benchmark. This became the **Phase-1 No-Seed Principle**.

Consequence: S15 thresholds dormant Phase 1; S16 tiers → brand-own influencer-cohort
uplift; S3 dates → event-derived.

---

## CATEGORY RESOLUTION — VERIFIED, NOT NET-NEW

Verified `category_inference.py` already exists (founder_category for display;
ai_inferred_category from title/tags/vendor/collection/product_type; a confidence
column; product_type already the least-trusted input). So the founder's NLP-from-
catalogue idea is ~80% already specced.

Refinements decided:
- Internal leakage grouping should use the AI CLUSTERING (semantically stable), not
  the spec's collection-FIRST default (collections here are often promotional junk).
  Collection stays for display only. Internal clustering needs the cluster, not the
  renamed label, so it is NOT blocked on the founder rename.
- STRIKE the "mandatory founder rename" step — can't ask a founder to label
  hundreds–thousands of SKUs.
- Confident NEW-CATEGORY CLASSIFICATION (and sub-category depth) DEFERRED to the
  multi-client phase — the new-vs-drift boundary is a parameter you can't calibrate on
  one brand; cross-client taxonomy (Fashion Intelligence Network) is what makes it
  tractable, so deferring is sequencing, not a detour. Phase-1 gap covered by
  structural-break (already triggers on "category addition") + narrate-don't-suppress.
- Images: text descriptions carry the categorical signal; vision adds CORRELATED noise
  (clusters by colour/silhouette/lookbook → groups by campaign/season, the wrong latent
  variable) at real cost. Text-only for Phase-1 grouping; images deferred to a Phase-2
  return-CAUSATION probe (fit/fabric/colour), not grouping. Reopen condition logged:
  "catalogue copy too sparse" (named-not-described catalogues).
- The 0.70 gate: redefine as cross-signal AGREEMENT (signals concurring), not the
  model's self-reported confidence (uncalibrated, clusters high). Founder onboarding
  review = the calibration set. 0.70 provisional. Residual: signals can be confidently
  wrong in unison; text usually breaks the tie, so text stays heaviest.

The decisive move on the "is text good enough?" question (which I'd been flagging
Medium for several turns) was **Measure-Before-Build**: don't design a fallback around
the unproven assumption — build a per-brand clustering-quality gate (scored on
return-rate coherence: a real category cluster has a tight intra-cluster return
distribution; a junk cluster is bimodal) that decides per brand between category-
granular Stage 1 and brand-level-Stage-1-WITH-DISCLOSURE. Never a SILENT coarse
fallback — that produces confident-wrong attribution in the beta window, the worst
failure for an analytics tool. The gate's own coherence threshold is still to be
calibrated on beta catalogues, but it is now a defined, measurable quantity, and it
produces its own validation data as a byproduct.

---

## EVENT CALENDAR — VERIFIED

`historical_pattern_scan.py` auto-populates brand_event_calendar (onboarding + monthly)
via Approach B (qualify high-volume days, classify by the brand's own discount-depth
p50/p75, cluster consecutive days bridging ≤2-day gaps). No founder input — so the
"brands change dates/durations" worry is structurally handled (window follows
behaviour, re-derives monthly; this is the per-brand calendar precision the moat wants).

The genuine residual is a CONFOUND: Approach B will label an unplanned competitor/viral
markdown as a planned sale_period and let it earn suppression. Require corroboration /
founder-confirm (same viral path) before treating a detected window as a planned
seasonal event; uncorroborated → narrate-don't-suppress.

Event naming: auto-generic is fine (engine depends on window+depth, not the string);
earn real names lazily on the SECOND occurrence of idiosyncratic recurring events;
never block onboarding.

---

## STANDING METHOD (held throughout)

Three-pass critique before every proposal; founder test on every proposal; pushback
not softened; verify against source before asserting (the "near-mechanical" claim and
the "no S-rule for viral" claim were both corrected by actually reading the files —
S33, category_inference.py, the Approach-B auto-population, the S44 isolation block
were all found by checking, not memory). No alert language; engineering as spec;
code batched to post-H.
