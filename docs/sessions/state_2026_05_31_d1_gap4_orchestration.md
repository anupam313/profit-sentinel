# Profit Sentinel — Session State
## Date: 2026-05-31
## Session: D1 Gap 4 (in progress) + Cross-Alert Orchestration Ledger created
## Previous state file: state_2026_05_31_d1_p1_p4.md

---

## SESSION SUMMARY

Started D1 Gap 4 (CPM → margin causal chain intermediate steps). Surfaced a
gating conflict with B1/B4/A2, resolved the boundary (Sub-Decision 1), locked
the funnel data scope (Sub-Decision 2) and the persistence edge case. Designed
the paid-media baseline-break (agency change) alert. Built
`cross_alert_orchestration.md` in two phases; Phase 2 discovered a pre-existing
50-rule suppression architecture (S-series) the canonical specs never exposed,
including S44 D1 component-level suppression — which Gap 4 must be reconciled
against before it can close. **Gap 4 is NOT complete.**

---

## GOVERNING PRINCIPLES — ALL LOCKED (cumulative, carried forward)

- **Monitor-and-Wait Principle** (2026-05-23)
- **Action-First Principle** (2026-05-23)
- **No Margin Figure Without Reliable COGS** (2026-05-26 Gap 1)
- **No Hardcoding Principle** (2026-05-26 Gap 2)

No new governing principle this session.

---

## SUB-DECISION 1 — D1 CPM Diagnosis Boundary — LOCKED

**The gating conflict:** D1's "CPM inflation" component overlaps B1 (creative
fatigue: CTR↓+CPM↑+freq↑), B4 (audience saturation: freq↑+reach growth↓+CPM↑),
and A2 (four-cause ROAS diagnosis incl. CPM inflation + creative fatigue).
Three+ alerts diagnosing one phenomenon → contradictory verdicts risk.

**Resolution — D1 is a ROUTER, not a diagnostician, for the CPM bucket:**
- D1 owns attribution of the effective-CPA rise to margin ($ impact). It does
  NOT independently compute creative-fatigue vs audience-saturation.
- D1's account-specific branch **reads B1/B4 leading-signal trajectory**
  (data-derived: normalized vs persists), NOT click/feedback state.
- **B-series always fires standalone.** D1 references; B1/B4 diagnose.
- **Shared CPM baseline mandatory** across B-series and D1. They may differ on
  actionability; never on whether the signal exists.
- **Escalation** (signal fired earlier, still active, now cost $X) is
  gated by the seasonal-norm check.
- Branch-4 sub-cases: (1) B1/B4 fired → reference verdict + margin impact;
  (2) neither fired but CPM ranks as margin driver → honest-ambiguity, hand
  buyer the funnel packet, no manufactured verdict; (3) both B1+B4 fired
  (opposite remedies) → surface the conflict, do not pick a side.

**Action-monitoring method (resolved):** monitor the SIGNAL (normalized vs
persists), NOT the founder's action. Click-based states (dismissed/acted) are
unreliable — founders act without clicking. Signal-trajectory is the primary,
data-derived mechanism. Action-trace inference (new ad IDs, spend drops) is a
deferred richer layer with false-positive risk — NOT built now. Explicit
clicks (S36 dismissal dropdown) are enrichment only, never a dependency.

**RELATION TO EXISTING ARCHITECTURE (Phase 2 find):** "suppress with
references" is already locked as **S35** (Duplicate Alert Root Cause graph:
F2→F1/F5/A2/D1; H1→all; E5→E1/D5; H6→A1/A3/Alert3). Sub-Decision 1 is
consistent with S35 but D1↔B1/B4 is NOT yet in the S35 graph. Register
Sub-Decision 1 as a **proposed addition to S35**, ratified at the orchestration
pass (ledger O-13). Do not build a parallel rule.

---

## SUB-DECISION 1a — Persistence Edge Case (dip-and-rise) — LOCKED

- **Continuous elevation** (never reached sustained normal between readings)
  = same instance persisting → escalate (seasonal-gated).
- **Cleared then re-rose** (hit sustained normal, then elevated again) = new
  instance → fresh diagnosis, no escalation, no "you ignored this" framing.
- **"Sustained normal" threshold** is brand-volatility-derived (function of the
  CPM baseline SD), multiplier **outcome-calibrated per client**. No fixed day
  count. Same adaptive-threshold pattern as other locked thresholds.

---

## SUB-DECISION 2 — Funnel Decomposition Data Scope — LOCKED

D1's funnel decomposition is **two-way: acquisition-cost-side (CPM delta) vs
conversion-side (GA4 CVR delta)**. **CTR is OUT of D1's scope** — CTR decline is
the creative-quality signal routed to B1/B4 in Sub-Decision 1; carrying a CTR
delta in D1 would re-import the B1/B4 boundary we removed.

- **No CTR mart column added.** Avoids schema debt; only option consistent with
  Sub-Decision 1.
- Unexplained-residual case (CPM flat, CVR flat, CPA up → CTR is culprit) is
  handled by the B-series state read (Sub-Decision 1), not a column.
- Schema check (2026-05-31): `meta_cpm_change_pct` ✓ present,
  `ga4_cvr_change_pct` ✓ present, CTR delta ✗ not present (and not needed),
  frequency delta ✗ not present (not needed — routed to B1/B4).
- **Limitation logged:** GA4 CVR conflates paid + organic sessions. D1's
  conversion-side leg reads site-level CVR with that disclosure.
- Reversible at the orchestration pass if the B-series reference proves not to
  carry the CTR story cleanly.

---

## BASELINE STRUCTURAL-BREAK ALERT (Agency Change) — DESIGNED, OPEN

- A **baseline structural-break alert**, NOT agency detection. We never assert
  a change occurred.
- Trigger: paid-media baseline shift beyond anything in the brand's history,
  sustained past the seasonal-norm gate.
- Output: surface the cost reality (e.g. CPM X% above prior normal since
  [date]) + question ("new agency / in-housed / restructure?"). Branches:
  yes → restart baseline cleanly (reuse Jan-12-2026 structural-break
  mechanism); no → real unexplained cost event → escalate; no answer → hold
  old baseline, disclose uncertainty.
- NOT at onboarding (agencies churn). Founder-declared resolution primary;
  data-derived campaign-structure churn may PROMPT the question, never triggers
  a silent auto-reset.
- Surface-ownership across paid-media alerts (D1/B1/B4/A-series) is a
  cross-alert item — ledger Cluster 2 / O-4. Added to product_strategy.md
  Section 12 open decisions.

---

## CROSS-ALERT ORCHESTRATION LEDGER — CREATED

New file: `cross_alert_orchestration.md` (capture phase, not resolution).
Resolution = dedicated pass AFTER A-series. Corrected sequence:
**D → C → B → A → orchestration resolution pass → H → consolidated CC prompt.**

### Phase 1 (canonical-spec pass): 8 touchpoint clusters
CPM cost (D1/B1/B4/B2/B5/A2) · baseline-break · conversion/checkout
(F2→F1/F5/A2/D1) · returns chain (C1→C4→C3 + D1 return driver) · paid-spend
waste (G1↔A) · wholesale contamination (A7) · seasonality/events (D6) ·
attribution diagnostics (A4/F3).

### Phase 2 (state/context sweep): 7 findings — HIGH IMPACT
The spec pass missed an entire pre-existing orchestration architecture:
- **S1–S50 suppression series** (seed_decisions_gap_f_g.md) — the real
  orchestration backbone. Section 3D already cited S-rules (F1/F5→S22-24,
  G2→S27-28) without defining them.
- **S35** master alert-dependency graph (above).
- **S44** — **D1 component-level suppression**: D1 decomposed into components
  (CPM/return-rate/COGS/discount/operational), suppression applies PER
  COMPONENT. CPM component suppressible by seasonal S1/S2/S5/S10. Worked
  example: BFCM + defective unit (AZ-KNIT-031) — CPM component suppressed,
  return-rate component fires.
- **S42** suppression stacking (DQ/S9 always overrides; State2+State3→State3).
- **E5 Deliverability Risk + E6** — live alerts absent from Section 3D canon.
- **Three-namespace collision** (Section 3D vs gap_abc decisions vs seed
  numbering).
- **A4 co-movement matrix** (CPM→ROAS −0.72, return→Gorgias +0.81, …).

### CRITICAL FLAG — O-14 (resolve IN-LINE, not deferred)
The seasonal-norm gate designed in Sub-Decision 1 IS, architecturally, the
S1/S2/S5/S10 suppression of D1's CPM component under S44. **Gap 4 and Gap 6
must be rewritten as consumers of S44 component suppression, not as a fresh
seasonal check.** This must be reconciled when Gap 4/6 resume. Gap 4 cannot
close until this is done.

---

## CORRECTIONS LOGGED

1. Four-cause ROAS diagnoser is **A2** (Root Cause of ROAS Drop), NOT A1. A1 =
   True Post-Return ROAS by Channel. (Misstated as "A1" earlier in Gap 4.)
2. product_strategy.md Group A heading was "A1–A6"; **A7** exists. Fixed to
   "A1–A7" this session.

---

## DOCS UPDATED THIS SESSION (re-upload to project to make canonical)

- **agent_d_build_spec.md** — E2 status reconciled: alert DEFERRED Phase 2 (not
  "PARTIAL LOCK / pending"); infrastructure (discount classification,
  collection-launch suppression, new-customer-pct column) relabelled as locked
  cross-alert dependency, not a shippable Phase 1 alert.
- **product_strategy.md** — Group A heading A1→A7; Section 12 gains three open
  decisions: baseline-break alert, E5/E6 canon reconciliation, namespace
  convention.
- **cross_alert_orchestration.md** — NEW file (this session).
- **causal_graph.py** — NOT edited (Claude Code action; post-H rule holds).

---

## D1 GAP STATUS — UPDATED

| Gap | Status |
|-----|--------|
| Gap 1 — COGS tier disclosure | LOCKED ✓ |
| Gap 2 — Threshold (Trigger A + B) | LOCKED ✓ |
| Gap 3 — Causal decomposition (Principles 1–4) | LOCKED ✓ |
| Gap 4 — CPM → margin intermediate steps | **IN PROGRESS** — Sub-Dec 1, 1a, 2 locked; router/funnel/edge-case settled; **NOT closed** — owes S44 reconciliation (O-14) + final chain assembly |
| Gap 5 — AOV decline missing from driver set | PENDING |
| Gap 6 — Seasonality suppression | PENDING (+ S44 reconciliation; + 2 dependencies) |
| Gap 7 — "Entirely explained" framing retired | PENDING |
| Gap 8 — No action named per driver | PENDING |
| Gap 9 — No $ revenue impact (display logic) | PENDING |

---

## ALERT REVIEW STATUS — FULL

| Series | Status |
|--------|--------|
| G-series | COMPLETE ✓ (G1/G2/G4 locked; G3 deferred Phase 2) |
| F-series | COMPLETE ✓ (F1/F2/F4/F5 locked; F3 deferred Phase 2) |
| E1 | COMPLETE ✓ |
| E2/E3/E4 | DEFERRED Phase 2 (E2 has live infrastructure dependencies) |
| E5/E6 | EXIST in seed files, NOT in Section 3D canon — reconcile (O-15) |
| D1 | IN PROGRESS — Gaps 1–3 locked, Gap 4 in progress, Gaps 5–9 pending |
| D2–D6 | Pending |
| C-series | Pending — NEXT |
| B-series | Pending |
| A-series | Pending |
| Orchestration resolution pass | AFTER A-series |
| H-series | Pending — last |

---

## PENDING CLAUDE CODE ACTIONS (accumulate — execute after H-series)

All prior pending actions carry forward unchanged. New/confirmed this session:
- **Verify** E2 `status: deferred_phase2` is in the queue (logged 2026-05-23;
  do not duplicate).
- **Do NOT** add a CTR delta mart column (Sub-Decision 2).
- Register Sub-Decision 1 (D1↔B1/B4 router + reference) as a proposed S35
  addition — to be finalised at the orchestration pass, then encoded.
- Baseline-break alert spec — pending design completion, then CC.
- E5/E6 canon reconciliation + namespace convention — doc actions, not CC.

No consolidated Claude Code prompt until after H-series.

---

## NEXT SESSION STARTING POINT

Load:
- state_2026_05_31_d1_gap4_orchestration.md (this file)
- cross_alert_orchestration.md
- agent_d_build_spec.md (updated — re-upload first)
- product_strategy.md (updated — re-upload first)
- technical_architecture.md

**Resume D1 Gap 4** with the S44 reconciliation (O-14) FIRST: rewrite the CPM
intermediate-step chain (funnel attribution → seasonal → cross-channel →
account-specific handoff) as a consumer of S44 component-level suppression and
the S35 dependency graph, not as fresh mechanisms. Then close Gap 4 and
proceed Gap 5 → 6 → 7 → 8 → 9.

Then: D1 alert language (after all 9 gaps) → D2 → D3 → D4 → D5 → D6 →
C → B → A → orchestration resolution pass → H → consolidated CC prompt.
