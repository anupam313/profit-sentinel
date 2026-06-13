# Profit Sentinel — Save Protocol
## Created: 2026-06-04
## Updated: 2026-06-08 — added PHASE 0 (decision capture), Check 10 (semantic read-back),
## Check 11 (decision + routing landing reconciliation). Original Checks 1–9 are
## un-renumbered (so external "Check N" references remain valid) and their core verification
## is unchanged; Checks 4, 7 and 8 gained additive clarifying clauses tying them to Phase 0.
## Status: INVARIANT — the standing procedure for every file save. Replace this same
## file (same filename) when a check is added or changed; do NOT fork per session.

---

## PURPOSE

A reusable, three-phase integrity procedure run on every save of the canonical files, so
that nothing is skipped, missed, half-applied, replaced incorrectly, left inconsistent
across files, recorded wrongly, or decided-but-never-written-down. Load this file at the
start of every session (it is pointed to from each state file's "next session — load"
block). The checks below are not process for its own sake — each maps to a way this
workflow has failed or could.

The procedure now guards three things, not one: (a) MECHANICAL integrity — the edit landed,
intact, in the right place (Checks 1–9); (b) SEMANTIC fidelity — the edit says what was
decided, not its opposite (Check 10); and (c) COMPLETENESS of capture — every decision and
every routed item reached a file at all (Phase 0 + Check 11). Mechanical checks alone pass
a clean edit that is wrong, and pass a save that silently dropped a whole decision — the new
layers close both.

These checks are TRANSACTIONAL (they verify *this* save). They are distinct from the
one-time, project-wide **full design-consistency audit + design-ownership map**, which is
logged separately (cross_alert_orchestration.md O-26) and runs AFTER Gap 6 closes. Do not
fold that audit in here — different cadence, cost, and trigger.

---

## PHASE 0 — DECISION CAPTURE (build the bridge before the manifest)

0. **Decision ledger from the conversation.** Before anything else, enumerate EVERY
   decision locked this session, read straight from the conversation — not from memory of
   what "feels" already covered. For each decision record:
   (i)   a one-line plain statement of what was decided;
   (ii)  the target file(s) it must land in;
   (iii) if it must appear in more than one file, each home, explicitly (e.g. "fulfilment
         retired → agent_d at 3 sites + tech-arch + checklist");
   (iv)  if it retires a mechanic, the exact retired wording(s) it replaces;
   (v)   if it was routed/deferred (to the orchestration pass, the O-26 audit, Horizon-2,
         a later gap), the ledger/target file that must record the routing.
   Two downstream lists are DERIVED from this ledger, never from recall: the Check-4
   retired-wording scan list (from the (iv) entries) and the Check-8 mirror list (from the
   (iii) entries). The Phase-A manifest must then account for every decision here; a
   decision with no target is either out of scope (say why) or a miss (fix it).

   WHY this is first: every other check verifies the save against the manifest, so a
   decision that never reached the manifest is invisible to all of them. This step is the
   only thing that catches a whole decision — or a routed item, or a retired phrasing —
   being dropped before it can propagate. It also makes Check 8 concrete (a listed set to
   verify) rather than reasoned recall, which matters most precisely when the
   design-ownership map (O-26) that would automate it does not yet exist.

   LIMIT (state honestly): the protocol cannot mechanically verify that Phase 0 itself was
   done exhaustively — it rests on the conversation being read in full. Phase 0 is the
   irreducible human floor the rest of the procedure stands on; treat it as the step most
   worth slowing down on.

---

## PHASE A — PRE-SAVE (declare before editing)

1. **File manifest.** List every file to be UPDATED (same filename, replace) and every
   file to be ADDED (new name). Confirm replacements keep the exact filename; new files
   get new dated names (`state_YYYY-MM-DD_[session].md`, `chat_context_YYYY-MM-DD_[session].md`).
   The manifest must account for every decision in the Phase-0 ledger.

2. **Expected line-delta per file (with reasons).** For each file to be updated, record
   `pre-edit count + N lines for [reasons]`. The target is "old + N for these reasons,"
   never a bare number — so a mismatch tells you *what* broke (double-applied edit,
   over-delete, truncation), not merely that something did.

3. **Content anchors.** For every intended edit, write a unique signature phrase that must
   be PRESENT exactly once after the edit (the positive half of the retired-wording scan).

---

## PHASE B — POST-SAVE (verify before the founder accepts)

4. **Line-count handles (Check 1).** Each updated file's real post-edit count equals the
   declared `old + N`. If a file shows the OLD count, the wrong/older copy is mounted →
   STOP.

5. **Header / date stamp (Check 2).** Each updated file's header or changelog carries the
   current session date; spot-check the stamp matches the edits.

6. **File presence (Check 3).** All canonical spec files are actually present in the
   project (guards the sync-lag we have hit before).

7. **Retired-wording scan (Check 4).** No *live* mechanic uses retired wording; every hit
   is a retirement note, changelog header, or open-item description only. Scan list is the
   set of (iv) entries from the Phase-0 ledger — not assembled from recall at verify-time.

8. **Content anchors present (Check 6).** Each Phase-A anchor phrase is present EXACTLY
   ONCE in its file. (A str_replace can silently fail to apply or land in the wrong place
   while the count and header still look fine — this is the positive half check 4 lacks.)

9. **Expected-delta reconciliation (Check 5).** Confirm the actual delta equals the
   declared delta per file; investigate any difference before accepting.

10. **Scoped diff — no collateral change (Check 7).** Diff each edited file against its
    untouched original; confirm the only differing regions are the intended ones, and that
    the first line and the changelog tail are intact. Direct guard against partial-replace
    corruption, truncation, and adjacent-block clobbering. Strongest single MECHANICAL check.

11. **Cross-file referential check (Check 8).** Every decision that lives in more than one
    file must appear in all of them (a deferred item in agent_d AND cross_alert; a build
    item in tech-arch AND the checklist). In a multi-file save the likeliest real miss is
    updating one place and forgetting its mirror. Verify against the (iii) mirror list from
    the Phase-0 ledger.
    *NOTE: this check is BEST-EFFORT until the design-ownership map exists (O-26). Once the
    map is built, it lists which decisions are multi-file and where, making this check
    mechanical rather than reasoned. Until then, enumerate mirrors by hand — Phase 0 (iii)
    is that hand-enumeration.*

12. **New-file completeness + handles match reality (Check 9).** The added files exist, are
    non-empty, and carry the next-session handoff; and the sanity handles written INTO the
    new state file equal the real post-edit counts — so next session's tripwire is itself
    correct.

13. **Semantic read-back (Check 10).** For each applied edit, re-read the changed region
    against its Phase-0 decision in plain language and confirm it SAYS what was decided —
    not merely that the anchor phrase is present. Checks 6 and 7 confirm an edit landed and
    is placed correctly; neither confirms it is *correct*. A number transcribed wrong, or a
    rule worded to mean its opposite, passes every mechanical check. One plain-language
    sentence of confirmation per edit closes this — the only guard against a clean-but-wrong
    edit. (Out of scope: whether the decision itself was sound — that is the design process,
    not the save.)

14. **Decision + routing landing reconciliation (Check 11).** Walk the Phase-0 ledger end to
    end and confirm EACH decision physically appears in its declared target file(s), AND
    that every routed/deferred item (entry (v): orchestration pass, O-26 audit, Horizon-2, a
    later gap) is actually written into its ledger/target — not merely agreed in
    conversation. A routed item decided but never recorded evaporates with every other check
    green. This closes the omission loop that Phase 0 opens and Check 8 (mirrors) only
    half-covers.

---

## REPORTING

After Phase B, report every file back against Checks 1–11 (PASS/FAIL per file), confirm the
Phase-0 ledger is fully reconciled (every decision AND every routed item landed), and hand
the founder the fresh line-count handles for the next session before they accept.
