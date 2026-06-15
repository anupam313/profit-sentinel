# Profit Sentinel — Chat Context (Spec-Update Execution Pass)
## Date: 2026-06-02
## Session type: Mechanical six-file spec-update pass (NOT design)
## Pairs with: state_2026_06_02_d1_gap6_wip.md (the PENDING SPEC EDITS were the source of truth)
## Sibling: chat_context_2026_06_02_d1_gap6_wip.md (the DESIGN session this pass documents into the canonical files)

Purpose: record what happened when the Gap-6 design decisions were written into the six
canonical files, and — more importantly — the non-obvious calls made DURING the pass, so a
future chat doesn't ask "why did we do X here." No new design was done; every decision below
is either propagation of an already-closed design or a documentation judgment.

---

## WHAT THIS PASS WAS

Applied the PENDING SPEC EDITS from state_2026_06_02_d1_gap6_wip.md to six canonical files,
one at a time, each with the same discipline: read the file from source first; apply only the
itemized edits; run a full-file RETIRED-PHRASE SWEEP; prove DO-NOT-TOUCH by diff against source;
output the complete file. Code (causal_graph.py) and S-rule definitions (seed_decisions_gap_f_g.md)
were NOT edited — they remain ROUTED/BATCHED per the standing rules.

Files updated (all re-uploaded to project, superseding prior copies):
1. agent_d_build_spec.md
2. cross_alert_orchestration.md
3. technical_architecture.md
4. product_strategy.md
5. d1_validation_gates.md
6. pre_agent_build_checklist.md

---

## THE THREE CONTRADICTIONS THE PASS CAUGHT (and how each was resolved)

The retired Gap-6 logic (mix-shift "±1 SD / ≥12 months", viral "spend-optional /
collection_launch_suppression_active", category "mandatory founder rename") turned out to live
in MORE places than the itemized edits named. The full-file sweep caught three un-itemized
copies that would otherwise have shipped as self-contradictions:

1. **agent_d_build_spec.md — pre-condition 6** (Layer-1 mix-shift driver pre-conditions). A
   second copy of the binary ±1 SD rule. RULING: rewriting it is *documentation of a closed
   decision* (Dependency 1 was closed in the design session), not new design. Replaced with the
   graded design; State 3 → suppress (this maps the old binary "suppress" outcome onto the new
   state vocabulary), State 2/1 → surface, with the State-2-vs-State-1 framing-placement deferred
   to the D1 alert-language pass.

2. **technical_architecture.md — GAP 6 DEPENDENCIES block (~line 3558)**. A third copy of both
   retired dependencies. Same ruling — rewritten to match file 1 verbatim on load-bearing parts.

3. **pre_agent_build_checklist.md — D-GAP6-1, D-GAP6-2, D-29**. The ORIGINAL home of the retired
   logic. Full rewrites; old wording removed (retained only inside explicit "(Retires…)" notes
   for legibility).

Lesson recorded: the full-file retired-phrase sweep was non-optional and earned its keep — three
real contradictions across three files. Apply the same sweep to any future file that touches a
decision written in more than one place.

---

## THE ONE NO-OP (do not "fix" it later)

**technical_architecture.md — edit #4 (S3 post-holiday return window) had NO TARGET here.** The
S3 fixed-date rule does not live in tech-arch. The only January-dated return reference (line 498,
"January returns Jan 5–25") is part of the `calendar_clustered` confound heuristic in
historical_pattern_scan.py — a DIFFERENT mechanism. Rewriting it would corrupt the confound check.
So edit #4 was intentionally SKIPPED in this file; the S3 re-anchoring lives in
agent_d_build_spec.md (done, file 1) and the S-rule definition is routed to the orchestration pass.
If a future chat sees "edit #4" unaddressed in tech-arch, it was deliberate — do not add fresh S3
documentation here (that would create a second, driftable home for the rule).

---

## OTHER PER-FILE NOTES WORTH KEEPING

- **File 2 (orchestration):** O-11 expanded (shared detector rewrite + S33-window/D1-cadence note);
  O-14 marked PARTIAL (CPM done, return-rate partial, three components untouched); O-19 extended
  with viral concurrent-discount + actionability gate and the weekly digest (resolve-at = Gap 8,
  + Gap 9 for digest); four new register items O-21 (S15 relabel), O-22 (S33 cutoff → brand-relative),
  O-23 (brand_event_calendar Approach-B confound guard), O-24 (final residual-disclosure pass). Each
  carries the caveat that the S-rule DEFINITIONS in seed_decisions_gap_f_g.md are NOT edited — only
  logged for the orchestration pass. A per-session CHANGELOG entry was added (file convention).

- **File 4 (product_strategy):** two Section 12 → Closed Decisions entries (suppressed-leak weekly
  digest; category Phase-1/Phase-2 sequencing). First file with a clean sweep (no retired copy).
  Diff = additions only; ICP, five alerts, and existing open decisions untouched.

- **File 5 (d1_validation_gates):** three new gates added as D1-G3/G4/G5 (file's existing
  convention). D1-G3 = clustering-quality gate (brand-level-with-disclosure is a FAIL if it runs
  without the disclosure — enforces "never a silent fallback"). D1-G4 = per-event prior-year
  coverage. D1-G5 = two-admissible-seasons gate for State 3, scoped EXPLICITLY to NOT govern
  D1-G1's S1 CPM path (avoids contradicting the locked gate). Diff = pure addition.

- **File 6 (pre_agent_build_checklist):** the five new build rows live as **D-GAP6-3…D-GAP6-7
  inside the "GAP 6 DEPENDENCIES" table** (clustering-quality gate; seasonal_typicality_state field;
  S3 event-derived window; S33 brand-relative cutoff; O-11 detector rewrite). SCOPING NOTE: two of
  these (clustering-quality gate, S3 window) are arguably broader than Gap 6 — when building, look
  for them in the Gap 6 table, not the main D-series build list.

---

## DRIFT CHECK PERFORMED

The founder's local technical_architecture.md (last saved 2026-05-31) was diffed against the
project copy → **byte-for-byte identical**. The "Last updated: 2026-05-22" header was cosmetically
stale on both; content was current. No intervening edits were lost. (The earlier worry that the
file had lagged was a false alarm.)

---

## THE THREE RETRACTIONS (carried from the design session — recorded here too, do not revive)

1. "Organic virality is margin-accretive, nothing to suppress" — WRONG (it compresses CM% via
   discount-depth + return-rate).
2. The three-state cold-start → blend → mature threshold lifecycle — RETRACTED for Phase 1 (no
   trustworthy seed pre-benchmark; use brand-own-data or narrate-don't-suppress).
3. The viral "modeled return-echo window" + overlap handling — RETRACTED (observe the tagged
   cohort; one-off virals get no forward tracking).

---

## STATE AT END OF PASS

Six canonical files updated and consistent; no retired Gap-6 logic survives in any location
(verified by post-edit sweep per file); all detector / S-rule / causal_graph.py work logged as
ROUTED or BATCHED, none done. The D1 Gap 6 WIP handoff is closed and the project is ready for the
next design chat to resume at return-rate Seam 2 (S17/S18 vs C3) per state_2026_06_02_d1_gap6_wip.md.
