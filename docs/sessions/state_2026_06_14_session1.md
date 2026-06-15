# Profit Sentinel — State: Session 1 (Sort the codes + fix the count)
## Date: 2026-06-14 · Session: session1 · Status: SESSION 1 COMPLETE — product_strategy.md edited and saved-checked. Session 2 still pending.
## RELATIONSHIP: This file EXECUTES Session 1 of the 2-session plan defined in
##   state_2026_06_14_edit_plan.md. It does NOT retire that file — the Session 2 task
##   (remove outdated wording → snapshot label → build the status file) still lives there
##   and MUST be loaded next session. Edit-plan file kept as the parent plan / audit trail.

> NEXT SESSION — LOAD FIRST: the 7 canonical files + save_protocol.md + this file + its
> chat_context (chat_context_2026_06_14_session1.md) + the parent plan
> (state_2026_06_14_edit_plan.md, for the Session 2 task list). Run the VERIFICATION GATE
> (line counts at the bottom) BEFORE any edit. The next session is SESSION 2 of the
> 2-session plan: remove outdated wording → create the pre-pilot-baseline snapshot tag →
> build the status file.

---

## WHAT THIS SESSION DID
1. Read the ~50 extra code-names (A8–A18, B6–B16, D-codes, E7–E40) in the 3 seed-decision
   files and CONFIRMED they are seed design decisions / scenarios — NOT alerts. No
   relabelling, no central lookup table, no cross_alert edit (LOCKED #2 from parent plan).
2. Found exactly ONE genuine new alert hiding among them: Deliverability Risk. Added it to
   the Section 3D alert library (body entry + summary-table row), coded E5.
3. Added the missing summary-table row for A7 (Wholesale Order Contamination Warning) — it
   was defined in the body but absent from the table, which was the source of the wrong "56".
4. Fixed the broken explanation in the §3D H-series note (it claimed "41 = A–G business",
   which is wrong; A–G business = 39 after E5).
5. SETTLED ONE alert count and reconciled it across every home in product_strategy.
6. Ran the full save protocol (Phase 0 ledger + Phase A manifest + Phase B 11 checks +
   executable checker) against product_strategy.md. All mechanical checks PASS.

## THE SETTLED COUNT
**58 alerts = 39 business (A1–G4) + 19 system (H1–H19).** This is the single figure. The
old 41 / 56 / 57 numbers are all retired. (Pre-edit there were 57 defined; +1 for the new
Deliverability Risk alert = 58. The Klaviyo Revenue Seasonality item is NOT counted — see
SETTLED below.)

## LOCKED (decided this session, hard to reopen)
1. Deliverability Risk is a genuine alert (E5) — it is the only seed-file alert with LIVE
   orchestration dependencies (it suppresses E1 and D5, and is on the critical/immediate
   bypass list with G1/F2). That dependency-wiring is the test for "real alert vs seed
   scenario." Everything else in the seed files failed that test.
2. Count = 58. Single number. No competing figure survives in product_strategy.
3. Deliverability Risk spec as written into §3D: High-actionability · Verification A ·
   Klaviyo only · confidence floor 75% · immediate delivery (bypasses 9am hold) ·
   suppresses E1 and D5 (root-cause). The 75% follows the F2 precedent (the closest
   structural twin: immediate, Verification-A, single-domain root-cause that suppresses
   downstream alerts).

## CONFIRMED (stable, build on it)
- Save mechanism: save_protocol.md is authoritative; Phase 0 ledger drives the Check-4 and
  Check-8 lists; executable checker re-runs Checks 1–8; a judgment digest covers only what
  no check can verify; human review is the floor.
- product_strategy.md edited count = 1427 (was 1416, +11). The +11 = E5 body block (+9) +
  E5 table row (+1) + A7 table row (+1); all count fixes and the line-250 rewrite are
  in-place (0 net).

## OPEN (carries what closes it)
- **Mid-state from D8 (deliberate, not a bug):** E5 is now PHYSICALLY added to §3D, but the
  reconciliation row (product_strategy line ~1368) still reads "lists only E1–E4" and its
  mirror O-15 in cross_alert still says "reconcile E5/E6". Left intentionally so the two
  files stay in the SAME state (both describe the gap as still open). Closes at the
  consolidated doc pass, where the status is flipped in BOTH files together. Do NOT flip one
  without the other.
- **D6-single-authority question (pre-existing, not mine):** is D6 the single seasonal
  authority every alert consults, or does each alert run its own seasonal check? Logged in
  cross_alert "resolve at orchestration pass". Relevant to the one-authoritative-home rule.
- Session 2 task (parent plan): remove outdated wording → snapshot tag → status file.

## SETTLED — recorded so they are NOT re-opened
- **Klaviyo Revenue Seasonality (seed "E6") gets NO §3D row.** It is the seed/synthetic
  instance of the same-week-prior-year seasonal-baseline METHODOLOGY that already has an
  authoritative home (product_strategy line ~422 + the D6 Seasonal Baseline Diagnostic).
  Copying the monthly numbers into §3D would create the stale mirror the rules forbid. It
  is NOT an alert and does NOT count toward 58.
- **Two seasonality mechanisms are separate, not one:** (a) the same-week-prior-year
  cyclical baseline (a comparison number; D6 uses it) and (b) the brand_event_calendar
  known-events / sale-period layer (dated event flags that suppress/contextualise). Do not
  merge them.
- The borderline seed "alerts" (loyalty-Klaviyo failure, missing-order-confirmations,
  duplicate-profiles, VIP-SLA, and the strategic-insight lines) are NOT library alerts:
  none has orchestration wiring; some need connectors absent from Phase 1.
- The ~50 seed codes are NOT renamed (churns dated audit records for no benefit; their
  files already say "Seed Script Design Decisions" on the cover).

## CORRECTIONS OWNED THIS SESSION (audit trail — where Claude was wrong, and the fix)
1. **False inference, caught by founder challenge.** Claude first claimed the May-31
   reconciliation pass had already adjudicated the borderline seed alerts and dismissed
   them. It had not — it only ever examined E5/E6. The correct, file-verified basis is the
   dependency test (live orchestration wiring), not the false "prior pass handled it".
2. **Under-declared line-delta.** Manifest said +9; actual was +11. The +2 is the Delivery
   and Suppression-rule lines added to the E5 entry for cross_alert consistency. Intended,
   disclosed — but the original declaration was wrong and was corrected before accept.
3. **Incomplete manifest, caught by the consistency check.** The manifest missed that the
   Group E header range "(E1–E4)" goes stale when E5 is added. Check 8 caught it; fixed to
   "(E1–E5)" as Edit 12.

## CARRY-FORWARD — DO NOT LOSE
ROUTED / DEFERRED (decided this session, must be acted on later — do not let them evaporate):
- **D5 → consolidated doc pass:** record the WHY for "seasonality = no §3D row" in the
  1357 reconciliation note when its status is flipped.
- **D7 → O-26 hardcoded-constants sweep (runs AFTER Gap 6 closes):** the 75% deliverability
  floor AND confidence-floors-as-a-CLASS are hardcoded product constants to revisit /
  outcome-calibrate. Fold into the existing O-26 list (alongside the 20%-cutoff, the launch
  ≥5-products count, the 21-day persistence, the 85/60 placeholders). NOT edited into
  cross_alert this session (honours the no-cross_alert-edit lock).
- **D8 → consolidated doc pass:** flip the 1357 reconciliation status AND its O-15 mirror
  TOGETHER (E5 added; E6 resolved as methodology-instance). See OPEN mid-state above.

PARALLEL NON-GATED TRACKS (recruitment is the binding constraint — do NOT let doc work
crowd these out):
- Respondent.io paid discovery study (5 participants: fashion/apparel/footwear,
  Shopify-primary, active founders).
- Aman (Ministry of Supply) follow-up: single CTA, reference his own offer to reconnect.

## WORKING RULES (standing — carry forward unchanged)
- Three genuine deep passes before any recommendation; Anupam flags if skipped.
- Pushback when disagreement exists; hold correct positions, revise only on a valid challenge.
- One open item at a time with explicit sign-off before moving on.
- Verify before propose: show the greps / the actual file lines before any recommendation.
- Label every load-bearing claim: verified-from-file / inference / unchecked-assumption;
  treat any unchecked-assumption as a TODO to check before leaning on it.
- State what would make the answer wrong, in the first answer (front-load the failure hunt).
- Plain language; gloss any code inline; design here, build in Claude Code.
- Complete files, never patches.

## HONEST FLOOR (what the checks cannot verify)
- The save protocol cannot mechanically verify that Phase 0 read the whole conversation —
  that is the irreducible human floor; it rests on the read plus Anupam's review.
- The 75% floor is a judgment call (F2 precedent), not a fact. Flagged for O-26.
- The E5 "what it detects" prose is Claude's paraphrase of the seed, not the seed verbatim.

---

## NEXT SESSION — VERIFICATION GATE (canonical line counts; STOP if any differs)
product_strategy CHANGED this session (1416 → 1427). The other six are unchanged.
agent_d_build_spec=2710 · technical_architecture=3815 · cross_alert_orchestration=840 ·
product_strategy=1427 · d1_validation_gates=386 · pre_agent_build_checklist=389 ·
save_protocol=149.
(These two continuity files' own line counts are handed over in the session report / digest.)
