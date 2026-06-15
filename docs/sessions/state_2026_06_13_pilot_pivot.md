# Profit Sentinel — Session State
## Date: 2026-06-13
## Session: PILOT PIVOT — define the beta pilot, lock Points 1 & 2, disposition the 57-alert library

---

## READ-ME FIRST (honest scope of this file)

This is a **continuity file, NOT a canonical save.** The project files are read-only in
this environment, so the full save protocol was NOT run on canonical files — nothing
canonical was written this session. Canonical line-count handles are therefore UNCHANGED
(verified equal this session): agent_d=2710, technical_architecture=3815, cross_alert=840,
product_strategy=1416, d1_validation_gates=386, pre_agent=389, save_protocol=149.

This session pivoted the product to a **pilot/beta** posture. Three additive files were
produced (this state file, the matching chat_context file, and `pilot_scope.md`). No
canonical spec was edited — those edits are scheduled for next session under the full
save protocol, against the LIVE files.

NEXT SESSION must: (1) reload canonical files + this file + the chat_context file +
pilot_scope.md, (2) re-verify the canonical line-count handles above, (3) FIRST settle the
pilot file/doc structure (explicitly OPEN — see below), then (4) make the canonical spec
edits via the full save protocol.

**Status labels used throughout:**
- **LOCKED** = Anupam explicitly locked it this session (Point 1, Point 2). Hard to reopen.
- **CONFIRMED** = agreed and stable, not formally "locked"; safe to build on.
- **PROVISIONAL** = actively being shaped; MUST NOT be treated as final. Do not calcify.
- **OPEN** = unresolved; carries "what closes it."
- **SUPERSEDED** = a position taken earlier this chat that was reversed; recorded dead so
  it is never resurrected.
- **PARKED** = deferred; do not touch in the pilot.

---

## THE BINDING REAL-WORLD RISK (not a decision — the top constraint)

**No committed design partners. Aman (MOS) is cold on two emails.** The pilot's premise is
"several brands, not one." Recruiting 4–5 founders willing to connect LIVE financial data
for months is slower than any build step and gates the entire 6-week timeline. Respondent.io
gets discovery interviews, not design partners. SOLVE RECRUITMENT BEFORE/ALONGSIDE BUILD.
This is flagged repeatedly across the chat and is the single thing most likely to slip the date.

---

## LOCKED THIS SESSION

### Point 1 — Shopify history, app distribution, approvals, entity
(Full text in pilot_scope.md / to be written to product_strategy + technical_architecture.)
- Full order history via `read_all_orders` (orders >60 days) **+ Protected Customer Data (PCD)
  approval** — both developer-side, one-time, frictionless for the founder post-install. CSV
  demoted to fallback only.
- Distribution = **custom distribution** (embedded, OAuth, per-store install link). Admin
  custom apps and public App Store listing both rejected for pilot; listing is post-pilot.
- The "not on the App Store" install notice CANNOT be removed on the light path — only
  **neutralized via concierge onboarding** (pre-empt it on the call). Listing (no notice +
  trust badge) is post-pilot.
- **PII/PCD is on the critical path**, not parallel — it's the precondition to reading a
  single order. Start Shopify approvals NOW (Partner account + app shell, dev-store PCD self-select,
  production PCD + read_all_orders requests filed in parallel with the build).
- **No registered entity required for any Shopify approval** (individual path is explicit in
  Shopify's flows). The "must be a company" material online is about Shopify *Payments*, not the
  developer/Partner flow. India adds no incorporation requirement for a free pilot.
- **Register the Indian entity in parallel anyway** — for the Google Ads developer token, DPA
  credibility with VC-backed brands, and a liability shield. Run both tracks; don't sequence.

### Point 2 — Meta attribution + how ROAS/attribution works in the pilot
(Full text in pilot_scope.md / to be written to product_strategy §2/3/3D/5/12 + technical_architecture.)
- Meta removed 7d-view + 28d-view on **Jan 12 2026** (1d-click/7d-click/28d-click/1d-view remain;
  click windows untouched). Already handled in spec: B4 view-through disclosure, H16 diagnostic,
  B-12 DQ entry, attribution_type data model.
- **We do NOT compute our own ROAS.** We anchor to the founder's own platform/agency number
  (Meta `purchase_roas` comes free from the connector; the agency number we ask the founder).
- **Blended (after-returns) ROAS = total revenue (− returns) ÷ total ad spend.** Total revenue,
  NOT marketing-attributed revenue — no attribution claim, view-only spend sits in the denominator.
  Label "ad-spend blended," not MER.
- **Pilot uses ONE default attribution basis: click-based, time-decay, 14-day** — six-model
  chooser deferred to post-pilot. Click-based also makes A1's history robust across the Jan-12 break.
- Product-level ad data: **Meta `product_id` via an Airbyte Custom Insight (spend/impressions/clicks)**
  and **Google `shopping_performance_view`** — both connector CONFIG, no new connector. Platforms
  give SPEND per product, not revenue per product — and the Shopify returns side fills that gap.
- **TikTok product-level is NOT in Airbyte (GMV Max gap) → custom pull, deferred** (TikTok = small
  spend share; destination-URL mapping still works; returns are Shopify-covered).
- Validation needs **no paid test** — mechanism is doc-confirmed; measure a brand's product-level
  coverage by **read-only inspection of their connected account**. Use connector v5.2.7+. Note Meta's
  Q1-2026 deprecation of legacy Advantage Shopping APIs — build on current Advantage+ structures.

---

## CONFIRMED THIS SESSION (stable; safe to build on; not formally "locked")

- **What the pilot IS:** the full product, automated end-to-end — same connectors, detection,
  checks/gates, Evidence Stack reasoning, alert language; full product surface (Shopify app + NLQ +
  email delivery). The system GENERATES ALL REASONING. The ONLY two differences from full PS:
  (1) a limited alert set (top alerts, not all 57), (2) ONE human relevance-gate: the system fires
  the alert TO Anupam automatically, he checks whether the reasoning fits that brand, then releases
  it to the founder. He computes/orchestrates NOTHING by hand — he is a relevance/release check on
  automated output.
- **The gate is a correctness LOG, not a silent switch.** Two columns: my-verdict-vs-system AND
  founder-outcome-vs-system (the second is what later licenses turning the gate off). Three exits:
  send / reject-as-wrong / suppress-as-stale. Max 1-day latency; intraday FAST-LANE for time-sensitive
  (G1). Stale → suppress + log why.
- **NLQ = answer-or-abstain** (never guess); a pilot-launch surface, not post-beta.
- **One project, no fork.** Keep working in the existing PS project; preserve the pre-pilot state via
  a git tag (`pre-pilot-baseline`), NOT a second project (memory/search are project-scoped; forking
  duplicates files and risks stale mirrors). Three file buckets (pilot-only / reused-frozen /
  parked-stays-in-PS) + a promotion-back path so PS doesn't rot.
- **agent_d_build_spec / d1_validation_gates / cross_alert_orchestration stay ACTIVE reference.**
  Only the *autonomous execution* is deferred (Agent B causal traversal, automated orchestration
  resolution, autonomous gate harness). The DESIGN inside them is reused: G1 alert language (agent_d
  lines ~110-215), shared urgency/revenue/formatting infra, the gate framework, the alert-interaction map.
- **Value-vs-moat filter** (corrected): value = is the founder getting this today (proactive alerting +
  inference + cross-source causal DEPTH all add value, even on single-source metrics); moat = can
  Shopify/a cheap app copy it (cross-source = defensible). The deep "why" that makes a single-source
  metric defensible is itself usually cross-source. Differentiation is conditional on EXECUTION DEPTH —
  a shallow threshold ping is commodity.
- **Longer free pilot (3–4+ months) AFTER the 6-week beta LAUNCH.** 6 weeks = launch a beta product;
  the pilot then runs as long as it takes.
- **PS's differentiated MOAT is concentrated in cross-source returns intelligence.** Much of the 57-alert
  "platform" is commodity (all of B-series), dependency-gated (D-margin/COGS, F-Sentry), or plumbing
  (H-series). This is a focused, defensible product — not a broad 57-signal platform.

---

## PROVISIONAL — actively being shaped; DO NOT save as locked

- **Alert disposition (full table in pilot_scope.md).** Pilot fired set: return-driver (HERO),
  C1 sizing-velocity, C6 high-return new collection, G1 stockout, C2 influencer (opportunistic) +
  3 in-app metrics (blended post-return ROAS, serial-offenders list, return-reason table).
  Phase-2-on-real-data: A1/A6 cohort, C4, C7, D1 (COGS-gated), E2/E3 (deep version), F1/F5 (GA4), G4.
  Park: B1-B5, D2/D3/D4/D5, E1/E4, A2/A3/A5/A7, G2/G3, F2/F4. Internal: A4/C5/F3, D6, H-series
  (keep pilot subset H1/H3/H11/H12/H15/H16/H19).
- **"Returns intelligence as PS's identity"** — posed by Claude; Anupam has NOT confirmed. Treat as a
  question, not a position.

---

## OPEN (explicitly deferred; carries what closes it)

- **OP-PILOT-1 — pilot file/doc structure.** Anupam: "not close." This is the FIRST discussion next
  chat. pilot_scope.md holds CONTENT only; how the pilot docs are organized is unresolved. Closes: a
  deliberate structure decision next session.
- **The 7 canonical spec edits** (see cross-file pending) — deferred to next session, full save
  protocol, against LIVE files. Closes: the save session.
- **Graduation threshold** (when an alert leaves the human gate) — parked by Anupam; revisit before launch.

---

## SUPERSEDED THIS CHAT (recorded dead — do NOT resurrect)
1. Manual-pipe-first → **automated pipe** (Anupam rejected; Claude withdrew).
2. Per-campaign/channel post-return ROAS as hero → **blended-TOTAL post-return ROAS as in-app metric**
   (per-channel needs lossy attribution).
3. "Include A2-core in pilot" → **A2 dropped** (collapses into return-driver / commodity causes).
4. Serial offenders as a FIRED alert → **in-app list** (standing state, not an event).
5. C1 shadow-only → **C1 FIRES, validated retrospectively from HISTORICAL Gorgias data.**
6. D1 "Tier-0 or drop" → **dropped from the 6-week pilot** (optional CSV path; revisit Phase-2).
7. agent_d/d1_gates/cross_alert as "parked foundations" → **design REUSED; only autonomous execution deferred.**
8. product_id validation via a "$10 test campaign" → **doc-confirmed + read-only inspection of a real account.**
9. Six-model attribution chooser in pilot → **single click-based default; chooser deferred.**
10. Two projects (fork) → **one project + git baseline tag.**
11. "~14 differentiated alerts" (too harsh) → **value-vs-moat split; many deliver VALUE, moat concentrated in cross-source returns.**
12. Memory's day-one set (A1,A2,C1,C2,D1) → **new pilot set** (return-driver, C1, C6, G1, C2). *(Memory is stale on this.)*
13. G1 "dependency-light, simple" → **scoped: single-product-destination ads; catalog ads self-suppress OOS; static single-product is the real value; needs Day-N/N+1 timing fix.**

---

## CROSS-FILE PENDING EDITS (next session, full save protocol, against LIVE files)
- **product_strategy.md** — §3 (pilot alert set), §3D (annotate every alert pilot/phase-2/park/internal),
  §5 (single default attribution; no six-model chooser), §12 (close now-decided items; add returns-identity
  question), §3C (NLQ confirmed pilot-launch).
- **technical_architecture.md** — Point 1 (Shopify approvals/PCD/custom distribution), Point 2 (blended ROAS,
  Meta product_id custom insight, Google shopping_performance_view, TikTok gap, v5.2.7+), pilot architecture
  (human-gate release flow, correctness log, NLQ answer-or-abstain).
- **cross_alert_orchestration.md** — mark pilot-relevant clusters; flag automated-resolution engine deferred
  (human gate replaces it); tag pilot-vs-parked O-items.
- **agent_d_build_spec.md** — G1 = pilot; F/E + deep-D1 deferred; shared formatting/urgency/revenue infra reused.
- **d1_validation_gates.md** — D1 gates parked with COGS; framework reused; add gates for the pilot alerts.
- **pre_agent_build_checklist.md** — pilot-scope build items vs deferred (Agent B, autonomous orchestration, full gate harness).
- **save_protocol.md** — note lighter pilot discipline (git + one-home); full protocol stays for canonical docs.
- **CARRY FORWARD (pre-existing, untouched this chat — do NOT lose):** product_strategy §12 open items —
  (a) E5/E6 alert-canon reconciliation (E5 has live dependents per S35/S34), (b) the 3-namespace
  alert-numbering collision. Also the B-9 Google Ads `cost_micros ÷ 1,000,000` mart-column flag.

---

## PARKED (do not touch in pilot)
- COGS foundation (O-28), category-baseline foundation / OP-1 grouping, the ~50 non-pilot alerts,
  self-calibration (O-31), automated orchestration governance, the heavy 14-check save protocol
  (replaced for pilot by git + one-home discipline), Agent B (causal-graph traversal).
- NOTE: the pilot GENERATES the real data that later unblocks several of these (esp. OP-1 grouping
  on real returns). Frame as fuel, not waste.

---

## CONFIDENCE / CONTENTION (* = Anupam pushed back and Claude reversed — watch for re-reversal)
- **Locked, hard to reopen:** Point 1, Point 2.
- **Confirmed, stable:** pilot definition, gate-as-log, one-project, files-active, longer pilot.
- **Reversed under Anupam's challenge (watch):** per-campaign ROAS*, serial-offenders-as-alert*,
  C1-shadow*, "parked files"*, single-source=fail*, ~14-alerts*, two-projects*. These were Claude
  errors corrected by Anupam — firm now, but flagged.
- **Provisional, expect change:** alert disposition, returns-identity.

---

## HANDLES
- **Canonical (unchanged this session; verify next session):** agent_d=2710, technical_architecture=3815,
  cross_alert=840, product_strategy=1416, d1_validation_gates=386, pre_agent=389, save_protocol=149.
- **New files this session (verify these equal real counts on reload):**
  state_2026_06_13_pilot_pivot.md = 226,
  chat_context_2026_06_13_pilot_pivot.md = 115,
  pilot_scope.md = 122.

---

## NEXT-SESSION START POINT (a cold reader can resume from here)
1. Reload canonical files + this state file + chat_context_2026_06_13_pilot_pivot.md + pilot_scope.md.
   Re-verify all handles above.
2. **OPEN OP-PILOT-1 FIRST — the pilot file/doc structure** (Anupam said it's not settled). Decide it
   before touching canonical files.
3. Then make the 7 canonical spec edits via the full save protocol, against the LIVE files (start with
   product_strategy to kill the most dangerous staleness: old "five alerts" + six-model attribution).
4. Confirm the PROVISIONAL items (alert disposition, returns-identity) — promote to CONFIRMED only on
   explicit sign-off.
5. In parallel (not gated on the above): design-partner RECRUITMENT (the binding risk) + start Shopify
   approvals + Google Ads token + Indian entity registration.
6. Build sequence per pilot_scope.md once structure + canonical edits are settled.
