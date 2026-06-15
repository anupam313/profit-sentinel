# Profit Sentinel — State: Session 2 (remove outdated wording → C2 collapse → pre-pilot baseline)
## Date: 2026-06-14 · Session: session2 · Status: EDITS APPLIED + Phase-B mechanical checks PASS.
##   Awaiting founder ACCEPT of the 3 edited files + this pair, THEN git tag "pre-pilot-baseline" (Task 7).
## RELATIONSHIP: This file EXECUTES Session 2 of the 2-session plan in state_2026_06_14_edit_plan.md
##   (the parent plan). Session 1 (state_2026_06_14_session1.md) is done. The parent plan is NOT retired
##   until Task 7 (tag) is applied; keep both as audit trail.

> NEXT SESSION — LOAD FIRST: the 7 canonical files + save_protocol.md + this file + its chat_context
> (chat_context_2026_06_14_session2.md). Run the VERIFICATION GATE (line counts at the bottom) BEFORE
> any edit. If Task 7 (the git tag) was NOT yet applied when this session ended, apply it first.

---

## WHAT THIS SESSION DID (Tasks 1–6 of the parent plan's Session 2; all applied to working copies)
1. **Task 1 — retired the "FIVE PROACTIVE ALERTS" framing** (depth (a), light). product_strategy line 54
   title `The Five Proactive Alerts` → `The Five Day-One Alerts`; line 124 `five core alerts` →
   `five day-one alerts`; line 1110 connector header `Five Core Alerts` → `the Five Launch Alerts`.
   LEFT untouched (deliberate): the §3 scope note (already de-framed), the §11 interview-yardstick lines
   (1258/1271/1303/1306), the two unrelated "five" usages (margin "five components"; "Five-tier COGS"),
   and the two closed-decision referents (Geographic CLOSED; Competitor/auction CLOSED) — accurate
   referents, not stale framing.
2. **Task 2 — retired the "SIX ATTRIBUTION MODELS" promise.** §5 Q3: dropped "We'll compute all models",
   inserted a **Pilot status — DEFERRED** note stating the pilot's single fixed basis (click-based,
   time-decay, 14-day), and KEPT the six-model + custom-weights chooser as the recorded post-pilot
   full-product design. Line 67 attribution note → pilot fixed basis. §12 closed decision (now line
   ~1338) → ANNOTATED with a dated pilot update (six-model design retained as post-pilot target).
3. **Task 3 — technical_architecture §11 (File Locations):** added a git-backed `docs/` folder entry
   (commit 7402434) + a 2026-06-14 changelog stamp.
4. **Task 4 — removed the stale §3C patch-cruft header** in product_strategy (the leftover `---` +
   duplicate doc-title + 3 PATCH lines + `---`). Real §3B/§3C/§3D/§3E all intact; duplicate doc-title
   resolved to 1.
5. **Task 5 — collapsed the two C2 summary-table rows into one** `(2-stage)` row at the Stage-1 gating
   floor (55%). Day-7/day-21 + 70% detail stays authoritative in C2's BODY. **Alert count unchanged at
   58; the §3D summary-table block now has rows = distinct ids = 58.**
6. **Task 6 — pilot_scope.md (non-canonical):** the two stale full-library references `57-alert library`
   (line 21) and `57-signal platform` (line 98) → `58`. In-place, 0 net. pilot_scope added to the
   Check-8 count-home list.
7. **Phase B:** built a fresh executable checker (save_check.sh, Checks 1–8 — there was NO committed
   save_check.sh; authored fresh). All mechanical checks PASS after a self-caught checker bug was fixed
   (Check 4 was counting the changelog retirement note as a live hit). Judgment digest handed to founder.

## TASK 7 — STILL PENDING (do after founder ACCEPT)
Apply the git tag **`pre-pilot-baseline`** with an accurate annotation, e.g.: "Clean design-docs baseline
at Session-2 close: wording cleaned, count settled at 58, roster clean (C2 collapsed). Registry, pilot
build, the cross-file count reconciliation (41/56 stale homes), and the deferred reconciliations
(1368/O-15, O-26 floor) still ahead."

## THE SETTLED COUNT (unchanged)
**58 alerts = 39 business (A1–G4) + 19 system (H1–H19).** Single figure. After the C2 collapse, the §3D
summary-table rows now equal the distinct ids (both 58) — C2 is no longer counted as two rows.

## LOCKED (decided this session, hard to reopen)
1. Alert codes are NOT renamed — A–G + H stay stable for pilot/main-product consistency. (A founder
   challenge this session confirmed: an "L###" notation in an earlier response was line-numbers, not a
   new code series. No code changed.)
2. Reword depth = (a) LIGHT. The line-54 title was the one load-bearing framing fix; "core" referents
   are accurate and were only lightly aligned; closed-decision referents left as-is.
3. C2 stays ONE alert (one id) measured at two confidence stages. Classifying rule (carried): same
   quantity re-measured later → ONE id with stages (C2); different signals that escalate → DISTINCT ids.
4. The six-model attribution chooser is the POST-PILOT design (retained, not deleted); the pilot ships
   one fixed basis: click-based, time-decay, 14-day.

## CONFIRMED (stable, build on it)
- Save mechanism: save_protocol.md authoritative; Phase 0 ledger drives Check-4/Check-8 lists; executable
  checker (save_check.sh, authored fresh this session) re-runs Checks 1–8; judgment digest covers what no
  check can verify; human review is the floor.
- Edited counts (verified this session): product_strategy 1427→1422 (−5: Task2 +2, Task4 −6, Task5 −1);
  technical_architecture 3815→3818 (+3); pilot_scope 122→122 (0).

## OPEN (carries what closes it)
- **NEW — cross-file stale roster counts (Check-8 finding, DEFERRED):** roster counts contradicting 58
  still live in three OTHER canonical files — `technical_architecture.md:1348` ("41-type library"),
  `cross_alert_orchestration.md:11/38/643` ("41-type library" ×3), `pre_agent_build_checklist.md:111/229`
  ("56 alert codes" ×2, plus the known "37" at line 21). NOT fixed this session by design: Session-1
  reconciliation was product_strategy-only; the parent plan defers other-file cleanup; the registry
  validator is chartered to reconcile cross-file counts. Resolution (what each 41/56 becomes) is DESIGN
  work — 41 was itself a wrong historical figure. Fix ALL count-homes together in the consolidated/registry
  pass, not piecemeal.
- **1368/O-15 reconciliation flip (parked, consolidated doc pass):** product_strategy's E-series
  reconciliation row + its cross_alert O-15 mirror still describe the E5/E6 gap as open; flip BOTH
  together. (Line ~1368 was pre-Session-2; re-locate by content — Session-2 edits shifted lines below the
  §3D table.)
- **O-26 hardcoded-floor revisit (after Gap 6):** the E5 75% deliverability floor + confidence-floors-as-a
  -class. Add to the existing O-26 list.
- **D6 single-seasonal-authority question (pre-existing):** is D6 the one seasonal authority every alert
  consults, or does each alert run its own check? Logged in cross_alert "resolve at orchestration pass".
- **pilot_scope Check-2 stamp:** intentionally not added (non-canonical, 0-net instruction). If a stamp is
  wanted later, add it inline to the Date/Status header to stay 0-net.

## CARRY-FORWARD — DEFERRED REGISTRY DESIGN (do NOT lose; build in its own scoped pass)
The "create the status-file registry" step is DEFERRED to its own pass — the design was under-specified
and the roster wasn't clean until the C2 collapse this session. Carry this design:
- **PRINCIPLE:** one canonical roster, many VALIDATED projections. §3D summary table stays the human-
  authoritative design home; the roster (ids + design columns) is EXTRACTED from it; prose counts, the
  registry, and any build-time roster are generated-from / validated-against that one extraction. Nothing
  hand-maintains a 2nd roster copy.
- **THREE ARTIFACTS:** (a) §3D summary table = canonical roster, human-edited. (b) a small hand-edited
  OVERLAY owning ONLY what §3D doesn't — per-alert lifecycle status + routing-pointer for deferred items;
  restates NO §3D field. (c) a GENERATED registry = join of (a)+(b), build output, NEVER hand-edited.
- **KEY:** key by alert id, one row per alert (keeps count = distinct ids clean). Status defaults to one
  value per alert; an alert re-measuring the SAME quantity at multiple confidence points (only C2 today)
  MAY split status per stage; if not split, stages share it. Overlay ergonomic (scalar or per-stage map);
  generated registry normalises to a uniform shape. Stage labels owned by §3D's body; overlay must match.
- **CONSUMER (corrected):** primary consumer is the SCALED product's per-alert-type lifecycle tracking
  across the full 58 + the later automated-routing code. NOT the pilot (pilot verification is a simple
  per-firing correctness LOG over a limited alert set). So registry = post-pilot SCALE infra, not
  pilot-launch infra. Do NOT shape the schema around the deferred router. Schema = id (+optional stage) /
  status / routing_pointer. No verification-log pointer yet (that log isn't designed).
- **VALIDATOR (build in Claude Code; fold into save_protocol Check 8 as the FIRST concrete O-26 instance):**
  extract the roster SCOPED to the §3D table block (NOT a whole-file grep — the "| X# |" pattern appears in
  other tables); FAIL LOUDLY on any unparseable line in the block; count DISTINCT ids; discover multi-stage
  ids by id-multiplicity; assert overlay ids ⊆ roster ids and every roster id has an overlay entry; status
  ∈ closed enum; routing-pointer present iff status==deferred and resolves to a real target; overlay carries
  NO §3D-owned field; regenerate the registry from (a)+(b) and DIFF (any hand edit fails). ALSO reconcile
  the cross-file count references — pilot_scope (now 58), the checklist "37"/"56", and the tech-arch +
  cross_alert "41-type" homes (the new Check-8 finding above).
- **WHAT WOULD MAKE THIS WRONG:** if C2's two stages ever need genuinely independent design (different
  action/suppression, not just different confidence) they become two ids. And keep overlay LIFECYCLE status
  distinct from cross_alert RUNTIME state (suppression/bypass).

## CLASSIFYING PRINCIPLE for future alerts
Same quantity re-measured later → ONE id with stages (C2). Different signals that escalate → DISTINCT ids
(the sizing → return-initiation → return chain, already modelled correctly as separate ids).

## PARALLEL NON-GATED TRACKS (recruitment is the binding constraint — do NOT let doc work crowd these out)
- Respondent.io paid discovery study (5 participants: fashion/apparel/footwear, Shopify-primary, active
  founders).
- Aman (Ministry of Supply) follow-up: single CTA, reference his own offer to reconnect.
- Shopify PCD + read_all_orders approval; Google Ads developer token (the long pole); Indian entity
  registration. (B-9: Google Ads cost_micros ÷ 1,000,000 when reading into the mart column.)

## WORKING RULES (standing — carry forward unchanged)
- Three genuine deep passes before any recommendation; Anupam flags if skipped.
- Pushback when disagreement exists; hold correct positions, revise only on a valid challenge.
- One open item at a time with explicit sign-off before moving on.
- CHECK-BEFORE-ANSWER: verify every number/line/claim with a tool THIS turn (stale-by-turn); tag
  verified/inference/unchecked; list what an edit forces before editing; end with what was checked + the
  one thing most likely still wrong.
- Verify before propose: show the greps / actual lines first. Complete files, never patches. Design here,
  build in Claude Code. Plain language; gloss any code inline.

## HONEST FLOOR (what the checks cannot verify)
- The save protocol cannot mechanically verify Phase 0 read the whole conversation — irreducible human floor.
- The new wording (pilot "fixed basis", DEFERRED notes, the 2-stage label) reads correctly to Claude, but
  founder-voice fit is a human call.
- The Check-8 stale-count finding is real and logged; its correct resolution (what 41/56 become) is design
  work not done this session.
- save_check.sh Check 8 is a heuristic grep for count tokens — could miss a count phrased differently; the
  registry/consolidated pass must not rely on this grep alone.

---

## NEXT SESSION — VERIFICATION GATE (canonical line counts; STOP if any differs)
product_strategy and technical_architecture CHANGED this session. The other five canonical files are
unchanged. (pilot_scope is non-canonical but listed as a count-home.)
agent_d_build_spec=2710 · technical_architecture=3818 · cross_alert_orchestration=840 ·
product_strategy=1422 · d1_validation_gates=386 · pre_agent_build_checklist=389 · save_protocol=149.
pilot_scope=122 (non-canonical count-home).
(This pair's own line counts are handed over in the session report / digest.)
