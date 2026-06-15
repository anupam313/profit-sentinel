# Profit Sentinel — Chat Context: Pilot-Pivot Documentation Edit Plan
## Date: 2026-06-14 · Session: edit_plan · Pairs with state_2026_06_14_edit_plan.md

This file is the WHY behind the state file — the reasoning a future session needs so the
decisions don't read as arbitrary.

---

## THE ARC OF THE SESSION
Two days had gone into figuring out HOW to document the pilot pivot without losing anything.
This session closed that: it produced a 2-session edit plan and corrected a string of earlier
mistakes. No canonical file was touched — the work was planning and verification only.

The repeated failure mode this session (worth carrying forward): Claude gave several
confidently-wrong answers by reasoning from memory/summary instead of opening the files. Each
was caught only when Anupam pushed back. The fix is the standing rule — verify from the file
BEFORE proposing — applied harder, plus a multi-pass self-critique before any recommendation.

## WHY TWO SESSIONS, NOT ONE
- The files (both the pivot and the structure session) assumed ONE edit session. Claude
  initially mis-stated the current narrow scope as "a deliberate session-1 subset" — that was
  inference, not in the files. Re-examined: the right unit isn't one-vs-many by preference; the
  classification work and the heavy wording edits are different in kind, and reliability
  degrades as a single chat grows long (the documented cause of this session's own misses).
- The natural seam is the git snapshot label. So: Session 1 = sort the codes + settle the
  count; Session 2 = remove outdated wording → snapshot label → build the status file.

## WHY THE CLASSIFICATION STAYS MINIMAL (this reversed an earlier Claude recommendation)
- Claude first recommended a central lookup table, then proposed putting it in cross_alert.
  Both were wrong, and the files showed why:
  (a) The ~50 extra code-names (A8–A18, B6–B16, E7–E40) are SEED DESIGN DECISIONS, not alerts.
      Their three files are titled "Profit Sentinel — Seed Script Design Decisions" — they
      self-identify on the cover.
  (b) Those decision codes do NOT leak into the canonical documents as live references — the
      only place any appears is inside the single paragraph that DESCRIBES the naming clash.
- So there is no scattered set needing a central index. A lookup table would be a second copy
  of facts that already have a home → the exact stale-mirror this whole discipline avoids.
- Therefore the real work is tiny: confirm the ~50 are decisions (a READ, not an edit), and
  pull the genuine new alerts (confirmed: "Deliverability Risk" / E5) into the alert library.
  The naming rule for future loose references (ALERT- vs DEC- prefix) lives in the status-file
  header, built in Session 2 — it fixes the cross-reference case without touching the seed files.

## WHY THE COUNT IS A REAL ITEM (and what the true number is)
- The alert count appears in product_strategy as a CONTRADICTORY mix: 41 (lines 232, 236, 1357,
  1414), 56 (lines 58, 1087), and 57 (line 250). Counting the actual alert definitions gives
  the truth: 38 business (A1–A7=7, B1–B5=5, C1–C7=7, D1–D6=6, E1–E4=4, F1–F5=5, G1–G4=4) + 19
  system (H1–H19) = 57.
- The "56" is explained: the summary table SKIPS "A7 — Wholesale Order Contamination Warning"
  (defined at line 302, but the table jumps A6 → B1), so it lists 56 rows. Adding that row
  fixes the table; the true count is 57.
- The "41" is stale leftover, wrong on every reading — even its own explanation at line 250
  ("41 = the A–G business groups") is wrong, because A–G business = 38.
- Adding "Deliverability Risk" makes it 58; whether the "Klaviyo Revenue Seasonality" background
  signal also counts (system-health plumbing IS counted) is the rule to settle in Session 1.

## WHY THE TWO INTERVIEW LINES ARE LEFT ALONE
- Lines 1260 and 1295 sit in the Customer Discovery Framework (§11) and use "the five alerts"
  as an INTERVIEW SCORING YARDSTICK ("if 6+ founders want things outside these five, that's a
  pivot signal"), not as product copy.
- The pivot's own pending-edit list named §3/§3D/§5/§12/§3C for editing — it did NOT include
  §11. So discovery was never meant to change. Re-pointing the yardstick to the new pilot set
  would actually weaken the test (you'd be measuring founders against the answer you pivoted to).
  Decision: leave them; confirm one line; off the stale-fix list.

## THE ATTRIBUTION DECISION (the "six models" item), plainly
- Meta removed 7-day and 28-day VIEW attribution on Jan 12 2026; only 1-day view survives
  (clicks untouched). Multi-touch, view-inclusive models can't be honestly reconstructed from
  the standard API (Triple Whale/Hyros confirm nobody does). So "we'll compute six models"
  became a promise PS can't keep on real data.
- Resolution (from the pivot session): PS does NOT compute its own ROAS — it anchors to the
  founder's own number and adds the returns truth on top. For the pilot, ONE default basis:
  click-based, time-decay, 14-day; the six-model chooser is DEFERRED to post-pilot, the design
  KEPT as the full-product target. The edit target is the §5 chooser + its two mirrors (line 67,
  line 1332) — NOT the synthetic test-data table (that's build data) and NOT the multi-touch
  category example in technical_architecture (that's a correct illustration of unverifiability).

## THE SAVE MECHANISM (and its honest floor)
- Reaffirmed from the prior session: run save_protocol.md; make mechanical Checks 1–9 an
  executable, re-runnable script; hand a 3–5 line judgment digest of only what no check can
  verify. Anupam reviews the list + digest — the minimal human floor — not the whole file.
- The irreducible limit (the protocol states it itself): no check can verify that the decision
  ledger was built EXHAUSTIVELY (a decision never noticed never enters the ledger and passes
  every check invisibly), nor that a decision is CORRECT (a misread of intent corrupts file and
  check alike). That is exactly why the human floor stays and is not dropped to zero.

## REVERSALS OWNED THIS SESSION (visible, not buried)
1. Six-model target was backwards (chooser vs test-data table); corrected.
2. Claimed "Klaviyo Revenue Seasonality" had no §3D home; it has one (H-series pattern).
3. "Session-1 subset" framing was inference, not file-grounded.
4. Oversized the ~50 codes as "alerts to classify"; they are seed decisions.
5. Contradicted own read-back by calling the git backup stale; it is DONE (commit 7402434).
6. Briefly dropped the executable checker + digest from the save mechanism; restored.

## POINTERS
- Full decision list + LOCKED/CONFIRMED/OPEN + the 2-session plan: state_2026_06_14_edit_plan.md.
- Save procedure: save_protocol.md (3 phases, 11 checks).
- The pivot's broader other-files pending edits: state_2026_06_13_pilot_pivot.md lines 168–183.
- Prior session's structure decisions (registry schema, status values): state_2026_06_13_pilot_structure.md.
