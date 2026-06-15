# Profit Sentinel — Chat Context
## Date: 2026-06-10
## Session: C3 returns-baseline FOUNDATION — defining "abnormal" and "big enough"

This file is the reasoning trail (the WHY). Its companion is
`state_2026_06_10_c3_foundation_abnormal_bigenough.md` (the WHAT/status). The two are
written to cross-check by purpose: every AGREED item in the state file should have its
reasoning here; if a decision is explained here but missing from the state list, that's a
gap to catch. Neither is a canonical save (link dropped; 11-check protocol not run).

---

## WHAT THIS SESSION WAS FOR

The session set out to work Foundation Question 1 (period-aware "normal" returns) for the
return-spike alert (C3). It ended up resolving Q1 *and* most of the "make abnormal/thin
concrete" question — but in doing so it surfaced that the whole thing rests on an
unresolved GROUPING decision, which is now the single load-bearing open item.

The return-spike alert tells a founder "returns on this product are running abnormally
high." Two things had to be pinned: how it decides something is **abnormal**, and how it
decides something is **big enough to bother the founder**. Almost the entire session lives
inside those two questions.

---

## THE LOAD-BEARING CONCERN (verbatim framing for next session — O1)

Anupam, near the end, recalled that earlier sessions designed product grouping using an
**LLM-based clustering** that leaned on **return behaviour** to club products together. He
now worries this is **circular**: forming groups from return behaviour and then judging
return behaviour against those groups. He also worries the **shared-return-reason-profile**
coherence test we agreed this session is **too thin for small brands** (reason-code data
is sparse and uneven). His exact stance: this is "by far the most important decision"
because "a lot of downstream alerts depend on this" and "we can't go wrong here."

This was deliberately deferred to the next session rather than rushed. It is O1, and it is
the root dependency for most of the return-alert spine. Do not let it be paraphrased into
something smaller — the circularity question and the small-brand thinness question are
both live and unanswered.

---

## REASONING TRAIL (oldest-first, the order it actually happened)

### Q1 — period comparability (resolved by dissolving it, not solving it)
The first instinct (RETIRED, R1) was four separate "normal" bands — ordinary days, the
run-up to a sale, the sale, after the sale. Two problems killed it. First, returns LAG the
sale: returns filed during a sale week are mostly from earlier orders, and the sale's own
returns arrive weeks later — so a band keyed to the calendar day of arrival is built on
mis-attributed returns. The fix is to key returns to the ORDER COHORT (the period the order
was placed in), which collapses "post-sale" into "the sale cohort's returns arriving late"
— there are really three order regimes (ordinary, pre-sale run-up, sale), not four. Second,
sale cohorts return structurally higher than ordinary ones, so comparing them to the
ordinary band would false-alarm every sale.

I initially proposed (RETIRED, R2) building a "sale normal" and comparing this sale to past
comparable sales. The uploaded files showed this CONTRADICTS a locked finding, **O-24a**:
the prior-sale comparator is too context-sensitive at this brand tier (each sale differs on
discount depth, quality cohort, delivery delay, competitive context, design novelty). So
sale-to-sale comparison was already rejected — Anupam's instinct ("we cannot compare sale
to sale") was the existing position, and I had drifted. Retracted.

The consistent, already-locked answer (A1): the sale is detected by the data-derived event
calendar ("Approach B," cancelled on 23-May with E2 then RE-RETAINED as live infra because
D1/C6 depend on it); a detected window carries a residual threshold + decay and defaults to
**narrate-don't-suppress** (O-23) for uncorroborated/one-off sales; abnormality is judged
against the GROUP's OWN band (not a sale comparator), via the three brand-relative tests
(level / exposure / trajectory), with thin history falling back to exposure+trajectory. The
event window is what stops every category firing during a sale (returns are expected
elevated, so we narrate unless the movement exceeds what the event explains). I also briefly
proposed (RETIRED, R3) a cross-sectional/leave-one-out category comparison to get a sale
adjustment; it's unnecessary because group-own-band + the event window already handle it.

### Contamination (bad past stretch inflating the benchmark) — A4
Anupam raised that a bad batch last season inflates a category's "normal," hiding a genuine
new spike. Verified in the files: the band IS robust by construction (IQR-percentile method,
explicitly no z-score/SD — confirmed by reference to the mix-shift seasonal grade), plus
admissibility (a stretch severe enough to break the series is discarded) and a season-count
confidence ladder. So transient contamination is largely clipped. The residual is a FLAT,
SUSTAINED elevation that never breaks the series — that one we DISCLOSE rather than fix.

My first fix included an onboarding founder question (RETIRED, R9). Anupam killed it: founders
won't remember, the question list is bloating, and crucially the GTM runs through fractional
CFOs who generate a Profit Audit from data BEFORE the founder engages — so a question asked
of nobody can't gate core function. This produced the **refine-not-gate** principle (A10):
onboarding questions may refine, never gate. The contamination fix then leaned on the
band-INDEPENDENT doors (trajectory and exposure don't need the historical level), so a real
spike still fires through a contaminated band — contamination degrades the explanation, not
the detection. ("Keep vs exclude" therefore demoted to minor, A6.) I also showed "default to
keep (wider band)" is NOT universally safe — keep is wrong for the transient case (it bakes
the bad batch into normal), exclude is wrong for the permanent-shift case; there's no safe
default, which is why the band can't be the sole gate.

### No auto-exclusion at beta — A5
"Fired event → auto-exclude from forward baselines" is an O-31 violation: it assumes every
fired spike is transient, so for a permanent shift the baseline never updates and the alert
fires forever (fatigue); and a live system reshaping its own comparison basis is the
self-tuning O-31 forbids. So: log fired events, calibrate by deliberate human decision.

### Lever-availability — A12, A13, and the guarded bundle (O9)
Anupam's "isn't a late return alert just FYI?" pushback was right that we're late for the
orders already placed, but the levers are FORWARD: pause the spend feeding the SKU, pull/hide
it, file the supplier credit while the window is open, fix the root cause, convert
refunds to exchanges. So the alert should fire when a forward lever is open and go to digest
when none is. Deep validatability check (with the real connector stack): pull-SKU is strong
(Shopify product status); exchange-mix is observable (Loop, A14); pause-spend is reliable
only at campaign/category grain (SKU-level spend is unreliable — G3 was deferred for exactly
this); root-cause-fix is outcome-validatable (O-30 cohort) even when the action is invisible;
supplier-credit is BLIND (no connector). The lever gate is therefore the already-logged
O-19(D), with its predicted "surface-the-lever, founder judges" degradation. Honest ceiling:
on a defect, PS's value is speed + reason, not validating the claim.

Cross-category common-cause ranking (RETIRED, R4): I'd proposed "look for the common cause
first," but the causal graph has NO cross-category common-cause detector, and the likeliest
common cause (delivery delay) is invisible without 3PL. So ranking of simultaneous fires =
top-one-or-two by exposure-and-open-lever + a single digest tail (O-19(E)); common-cause
synthesis is Horizon-2.

### 3PL / supplier / agentic research — A8, A9, A12
3PL: market is fragmented (50+ providers), ShipBob/ShipHero DO expose per-shipment cost via
API but there's no native Airbyte connector (custom build each), and 3PL doesn't unblock the
real blocker (COGS/O-28). So not in beta — demand-driven post-discovery, with a discovery
question added. Supplier-credit: research confirmed it's off-platform (email/spreadsheets/
debit notes/portals; claim window in the contract) — reject the connector. Agentic ("isn't
'go check 5 places' half-knowledge?"): real point, but full execution breaks the
deterministic-detection moat and the safety line (auto-pausing spend with real money). So the
beta posture is **prepare the action, don't execute it** (copy-paste/deep-linked, assembled
evidence package for the supplier claim); supervised one-click execution is a Horizon-2 fork.

### content_id / SKU capture — A15 (corrected twice)
I first overstated that PS "knows the campaigns and content_ids driving the SKU." File +
web checks corrected it: Meta gives product *conversions* but per-product *spend* inside
Advantage+/DPA is a black box; TikTok Shop/GMV Max gives spend-by-product (with attribution-
window quirks) but thins off-Shop; Google is the surprise — `shopping_performance_view` now
gives per-product spend/conversions for Shopping AND PMAX (v24 added item-level CartDataSales
View; expands to all campaign types 2026-06-15) — which means our synthetic seed is STALE
(it models PMAX as withholding product data). Hence the ad-platform product-data bundle
(A15): per-platform fact sheet, refresh Google seed, make `campaign_sku_return_rate_7d` read
Google, and scope the pause-spend prepared action honestly (clean on Google/TikTok-Shop, not
on Meta DPA).

### Sizing the problem: sales value, not cost — A16, A17, A19/A30, A21
Cost (RETIRED, R8) was rejected for sizing: COGS misses SKUs and goes stale, and it's parked
anyway (O-28). Sales value is clean, complete, current — and is the right measure for THIS
alert, not a placeholder for margin (margin belongs to the parked profit alert). Anupam's
shipping-cost insight strengthened the either-or materiality gate (A17): a low-cost tee
carries per-return costs (label, inspection, processing fee) that are roughly per-unit and
invisible to us, so VOLUME is our proxy for those hidden costs — volume catches cheap-high-
quantity problems, sales value catches expensive-low-quantity ones. Neither alone is safe.

"Normal" and "floor" were being blurred. Split: **anomaly** = rate clearly above the group's
own robust band (RETIRED R6: the "multiplier × spread" upper line → replaced by rarity-
against-own-history, a high percentile of the group's OWN history, which removes the
hardcoded multiplier; one honest, interpretable sensitivity choice remains). **Materiality**
= absolute size (either-or, A17). **Trust gate** (A19) = the confidence band of the rate
(standard error sqrt(p(1-p)/n)); fire only when the pessimistic end still clears normal —
this is inherently proportion-aware (RETIRED R7: flat count floor → proportion-aware), with
an absolute hard minimum beneath (one expensive return never fires alone; sales value never
waives it). The math conclusion: a $1.5–2M brand has ~60 orders/product/year, so it won't
clear the trust gate at SKU level — **alert grain follows brand size** (A26): small brands
read at collection/type level. Trajectory (A21) must be a cohort RATE curve, not an absolute
count (absolute count is polluted by promotion timing), sitting behind an absolute size gate.

### Grouping — A22/A23/A24/A25/A26, and why O1 is open
New products (A22): we do NOT invent a normal; silent watch → size/direction alert if they
bleed hard early → full machinery once history exists; narrate with raw numbers + the
founder's own language, never an internal cluster name. Peer groups for new products
(RETIRED R12) were dropped as overengineering — A22 + roll-up handle it. The coarser group
(A24) is the brand's own product → style → type ladder from Shopify structure; lower rungs
(product + variants) are trusted by construction, merchandising/collection rungs are
candidates. The coherence test I first proposed — "members return at similar rates"
(RETIRED R5) — is WRONG because categories are Pareto-shaped (a fitted dress at 35% and a
shift at 8% are both legitimately dresses). Replaced (A25) by **shared return-reason
profile** coherence (judge by why things come back, not by similar rates); stay structural
when reason data is too thin. This Pareto reality also makes the inside-the-group
concentration check load-bearing (A29) — a group average lies when a few products drive it.

BUT A25's reason-profile test, and the whole grouping mechanism, is exactly what Anupam then
flagged as the load-bearing open question (O1): is the earlier LLM-clustering circular
(return behaviour forming the groups), and is reason-profile too thin for small brands?
Unresolved — next session.

### Calibration register — A28 (and the dial-method gap)
Anupam's fear: at pilot-start there'll be a hundred things to set and a critical dial will be
forgotten. Fix: build the MECHANISM now even though VALUES wait — a calibration register
listing every dial with its setting-METHOD and a status flag, plus a hard rule that the
alert can't go live while any dial it depends on is "unset" (turns "we'll remember" into
"the system refuses to run"). Pushing further, Anupam was right that the register is only
real if each dial's METHOD is defined now (the value can wait, the method can't). Honest
audit of the four dials: confidence-level (method defined — strict standard choice, no brand
data) and rarity-cutoff (method defined — a high percentile of own history, inactive until
enough history) are ready; **recency-window (O7) and size-gate-fraction (O8) have only
sketched methods** — these are OPEN-METHOD design items, not deferred values. Carried to next
session.

### Tuning objective — A27
Make the objective itself asymmetric: false alarms far costlier than misses (the pilot builds
credibility as much as it learns). Freeze dials at pilot start; log every fire/near-fire/
held-back + 7/14-day outcomes; loosen ONLY on logged evidence by deliberate human decision;
never auto-tune the live system.

---

## REVERSALS THIS SESSION (where I changed my own earlier answer — see state-file R-list)
R1 four-band; R2 sale-to-sale; R3 cross-section; R4 common-cause-first; R5 rate-spread
coherence; R6 multiplier×spread; R7 flat count floor; R8 cost-for-sizing; R9 founder
question; R10 three clean closes → bundle; R11 exposure modulator; R12 peer groups. Several
were Anupam-driven corrections of my errors (R2, R5, R8 especially). Recorded so a future
reader doesn't reinstate a dead version.

---

## VERIFICATIONS DONE vs STILL OWED
**Done (file/web):** line counts at session start (all exact); event calendar re-retained
as live infra; C3 provisional lock + the three brand-relative tests; O-23 / O-24a; robust
IQR band method; causal graph has no cross-category common-cause; content_id coverage per
platform; Loop resolution-type NOT ingested; Google API product reporting (seed stale);
3PL/supplier landscape; Loop outcome capability.
**Owed (see state-file Unverified register U2–U7):** Loop ingestion build; Google seed
refresh; O-19 materiality calibration (open); return-band window (O5); content_id figures are
synthetic; ShipBob/ShipHero connectors not acted.

---

## HOW TO RESUME (cold-reader test)
Load both continuity files + canonical files; re-verify line counts; run the 11-check save
protocol to write the AGREED items (two-file save for C3). Then OPEN O1 (grouping) FIRST —
it is the root, and most of the return-alert definition is provisional on it. One item at a
time, three passes, explicit sign-off, as per the working discipline. Do not build anything
tagged "provisional pending O1" until O1 closes.
