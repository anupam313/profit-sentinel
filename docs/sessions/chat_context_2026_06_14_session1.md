# Profit Sentinel — Chat Context: Session 1 (Sort the codes + fix the count)
## Date: 2026-06-14 · Session: session1 · Pairs with state_2026_06_14_session1.md

This file is the WHY behind the state file — the reasoning a future session needs so the
decisions don't read as arbitrary.

## THE ARC OF THE SESSION
The job was narrow: the three seed-decision files contain ~50 extra code-names (A8–A18,
B6–B16, E7–E40, plus D-codes) that look like alerts but mostly aren't, and the alert count
was stated three different ways (41, 56, 57) across product_strategy. Session 1 sorts the
codes, pulls out any genuine alert hiding among them, settles ONE count, and writes that
number into every place it lives. Session 2 (still pending) does the heavier wording cleanup
and the snapshot. We deliberately split the two so a long code-sort and a long wording-edit
don't share one chat.

## WHY E5 IS THE ONE REAL ALERT (the dependency test)
The seed files use alert-like labels freely — "new alert", "Alert H8/H9", "strategic alert".
The principled test for whether one is a real library alert is: **does the system's own
orchestration logic already depend on it?** Deliverability Risk passes — it is wired to
suppress two other alerts (E1, D5) and sits on the critical/immediate bypass list. None of
the borderline ideas (loyalty-failure, missing-order-confirmations, duplicate-profiles,
VIP-SLA, the strategic-insight lines) has any such wiring; they are example sentences inside
test-data design. Some also need connectors that aren't in Phase 1. So: one real alert, the
rest are scenarios, insights, variants, or out-of-scope.

This corrected an earlier wrong move (see REVERSALS): Claude first justified "only E5" by
claiming a prior pass had adjudicated the others. It hadn't. The dependency test is the real
reason, and it is file-verifiable.

## WHY 58, AND WHY NOT 59
58 = 39 business (A1–G4, now including the new E5) + 19 system (H1–H19). The mess (41/56/57)
came from a real cause: the seed namespace (E1–E40 etc.) collides with the §3D namespace, so
naive counting was unreliable, and the summary table had silently dropped the A7 row (that
produced the "56"). We settled it by enumerating the actually-DEFINED §3D codes, ignoring the
seed namespace.

The 58-vs-59 question was whether the Klaviyo Revenue Seasonality item counts. It does not —
and the reason matters: we checked whether any counted system item is a pure "background
number with no output". None is; every H-item surfaces something. The seasonality item
surfaces nothing (it feeds another alert's math), so excluding it is the *consistent* call,
not an exception. The "consistency would force 59" worry rested on a premise that turned out
false.

## WHY THE SEASONALITY ITEM GETS NO §3D ROW
Its monthly-revenue targets are a synthetic instance of a methodology the product already
documents in ONE place: the same-week-prior-year seasonal baseline (product_strategy ~line
422) plus the D6 Seasonal Baseline Diagnostic. The standing rule is that product-wide
methodology lives in one authoritative home and copies elsewhere go stale. Copying the
numbers into §3D would manufacture exactly that stale mirror. So nothing to add — the
"reconcile" note just records *why* it has no row.

Separately, Anupam flagged that there are TWO seasonality mechanisms and asked us not to
conflate them. Confirmed: (a) the cyclical same-week-prior-year baseline (a comparison
number) and (b) the brand_event_calendar known-events / sale-period layer (dated event flags
that suppress or contextualise specific sales and launches). They are different kinds of
object — a baseline vs an event registry — and the no-§3D-row decision only touches (a). A
live caveat on (b): when a sale window is auto-detected from discount depth rather than
founder-declared, it can mislabel an unplanned markdown as a planned sale (logged as O-23 —
needs corroboration before it earns suppression).

## WHY THE FLOOR IS 75% (and why it's only provisional)
Every alert carries a confidence floor — the certainty gate below which it stays silent. We
didn't invent 75%; we matched the closest structural twin. Among the High-actionability,
Verification-A alerts, the floors cluster 75–80%. The exact twin is F2 (payment-failure):
immediate delivery, Verification A, single-domain, and a root-cause that suppresses
downstream alerts — the same shape as Deliverability Risk. F2 is 75%, so E5 is 75%. But all
floors are hardcoded product constants, so this — and confidence-floors as a class — is
routed to the O-26 sweep for outcome-calibration later. Singling out only E5's floor as
"provisional" would falsely imply the others are settled, so we treat them as a class.

## WHY THE 1357 STATUS-FLIP IS DEFERRED (the mirror logic)
The reconciliation row at product_strategy ~1368 is mirrored by O-15 in cross_alert; both
currently say "reconcile E5/E6". Now that E5 is physically added, the honest move is to flip
that status — but flipping only the product_strategy side would leave O-15 stale, creating
exactly the two-files-disagree drift we are trying to prevent, and editing cross_alert was
locked out of this session. So we touched only the stale *count word* at 1357 and left the
*status* in both files identical (both still say the gap is open). It closes at the
consolidated doc pass, where both flip together. This is a deliberate mid-state, not a bug —
recorded as an OPEN thread so Session 2 doesn't misread it.

## REVERSALS / CORRECTIONS OWNED THIS SESSION (visible, not buried)
1. Claude asserted a prior pass had adjudicated the borderline alerts; it hadn't. Reasoning
   re-grounded on the dependency test (file-verified), and the conclusion survived.
2. Claude declared the edit delta as +9; it was +11 (the +2 = Delivery + Suppression lines
   in the E5 entry, added for cross_alert consistency). Corrected before accept.
3. The edit manifest missed the Group E header range going stale (E1–E4 → E1–E5 once E5 is
   added). The consistency check caught it; fixed.
Pattern worth keeping: each miss was a fact not yet checked. Verify-before-propose and the
front-loaded failure hunt are the fixes, and they earned their keep this session.

## THE SAVE MECHANISM AND ITS HONEST FLOOR
The save ran from save_protocol.md (not memory): a Phase 0 decision ledger, a Phase A
manifest with per-edit anchors and a declared line-delta, then Phase B's 11 checks plus an
executable checker that re-runs the mechanical ones. The honest floor: no check can verify
that Phase 0 read the whole conversation, and none can judge whether a decision was *sound*
(only that it landed and says what was decided). Those rest on the human review.

## POINTERS
- Parent plan / Session 2 task list: state_2026_06_14_edit_plan.md (NOT retired).
- Authoritative save procedure: save_protocol.md.
- Seasonal-baseline methodology home: product_strategy ~line 422 + D6.
- Hardcoded-constants revisit home: cross_alert O-26 (after Gap 6 closes).
- Reconciliation mirror to flip together later: product_strategy ~1368 + cross_alert O-15.
