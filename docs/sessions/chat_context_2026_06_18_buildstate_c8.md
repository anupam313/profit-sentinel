# Profit Sentinel — Chat Context: 2026-06-18 (build-state verification · HERO=C8 code decision)
## Companion to state_2026_06_18_buildstate_c8.md. Narrative continuity for the next session (OP-1).

## WHAT THIS SESSION WAS
The first actual pilot-build session after the 2026-06-14 pre-pilot baseline. Per the resume's Step 1, the
job was to VERIFY THE REAL BUILD STATE from the repo before designing any alert — not to trust memory on what
was coded. It turned into a thorough build-state sweep plus a chain of doc-hygiene fixes that surfaced along
the way, and ended with the first real HERO design decision: assigning the return-driver its alert code (C8).
No canonical spec file was edited; all repo changes were code + CLAUDE.md and were committed as we went.

## HOW THE WORK RAN (cadence)
One item at a time, founder sign-off between each. I have no repo access, so the pattern was: I design/decide
in chat and hand the founder a Claude Code block; Claude Code runs it in the repo and pastes the output; I
read the output and interpret. The founder enforced CHECK-BEFORE-ANSWER throughout (verify every number/line
THIS turn, tag verified/inference/unchecked, never reuse a value across turns without re-checking) and asked
me to keep the human-review-then-separate-commit gate intact (I slipped once by merging review+commit into one
block; founder caught it; reverted to review-first).

## HOW WE GOT HERE (the spine of the session)
1. **Verification gate stumbled, then passed.** The mounted technical_architecture.md was 3815 vs the 3818
   handle. Chased it: not a stale handle (local HEAD=disk=3818, clean) — the PROJECT MOUNT was the stale copy.
   Founder re-uploaded; the upload verified at 3818. (The project UI's "3819" was an off-by-one blank-line
   count.) Lesson re-confirmed: always wc -l, and the mount can lag the repo.
2. **Resolved the causal_graph.py contradiction.** Docs disagreed: a May-22/23 trio of state/chat files said
   "built+verified"; the May-31 checklist said "PENDING". Repo truth: the FILE exists (962 lines, real) and
   was imported once (a .pyc), but is uncommitted-until-now, unwired (nothing imports it), and one chain
   behind (57, missing E5). So both old claims were half-right; "built" had conflated authored-with-wired.
   Committed it as a baseline (d52ffde) so 962 lines of real work stopped being at risk.
3. **Mapped Agent A to the fired set.** Agent A scans 8 signals; the fired set overlaps on ONLY C1. Verified
   at the column level. The other 4 (C8/HERO, C6, C2, G1) have no detection in Agent A. Then found the reuse:
   historical_pattern_scan.py already has the rolling-window MATH for the missing signals — but it's an
   onboarding one-shot validator, not a continuous emitter, so the reusable part is the computation, not a
   drop-in alerting path. Settled that the 4 were never "fired" (they're the plan, not a history).
4. **Doc-hygiene chain** (each verified, each committed): schema mismatch flagged then DISPROVEN (both runtime
   components correctly read client_azure_co_marts) → fixed CLAUDE.md's stale schema prose + genericized the
   Rule-1 discovery query (177bb4d); a OneDrive delete-370 scare (git internals, repo intact) → .git-exclusion
   DEFERRED by founder; a phantom docs/blueprint.md reference removed (fd545db).
5. **The HERO code decision** (the real design start). Options A (reuse A2) / B (fresh code + retired-A2
   pointer) / C (plain fresh). Founder leaned C to avoid A2 documentation baggage; I corrected the framing —
   the baggage belongs to A, not B/C, and the time difference between B and C is ONE line, not hours. Founder
   asked whether retiring A2 nets the count back to 58: it doesn't, because A2 leaving the PILOT ≠ A2 leaving
   the LIBRARY, and deleting it to force net-zero would orphan working code. Landed on **B → C8, a clean
   +1 → 59.** Then scoped exactly which files the +1 touches (product_strategy ×7 lines, pilot_scope ×2),
   and the founder offered to do the product_strategy edits manually (upload for validation) — accepted.

## KEY DECISIONS (mirror of the state file's LOCKED block, in prose)
- **C8 = the return-driver's code** (Group C). Clean +1, library count 58 → 59. Option B.
- **A2 retired-from-pilot, NOT deleted** — stays a counted library chain with a one-line "→ C8" lineage note.
- **E5 HELD** out of the pilot (founder first said add, I pushed back, founder agreed to hold). E5 still exists
  in the §3D library; the hold is about the fired set. Don't re-add; don't conflate with causal_graph's
  separate missing-E5.
- **No spec edits before OP-1.** The C8 entry's detection fields ARE the spec and depend on OP-1's
  returns-baseline. So the whole C8 edit (causal_graph + pilot_scope + the manual product_strategy count
  reconciliation) runs as ONE save-protocol pass AFTER OP-1.

## CORRECTIONS OWNED THIS SESSION (audit trail)
1. **save_protocol mischaracterised.** I told the founder save_check.sh was "drift/consistency only, not
   content-preservation." WRONG — I'd spoken from memory. Read the file: Check 7 (scoped diff vs the untouched
   original) IS the content-preservation guard, called the strongest single mechanical check. Corrected, and
   built the C8 validation plan ON the protocol rather than reinventing it.
2. **Merged review+commit into one block.** Founder had earlier asked for review-then-separate-commit; I gave
   a block that did both. Founder flagged it; I reverted to a stop-after-diff block. The earlier pattern was
   right.
3. **"Schema mismatch" false flag (Claude Code's, owned by it).** Claude Code first flagged client_azure_co
   vs _marts as a discrepancy, then disproved it after actually reading agent_a.py's MART_SCHEMA constant.
   Worth raising (cheap to rule out, catastrophic if real), clean to retract.
4. **HERO-as-a-code confusion (founder's catch).** Founder flagged that I'd been treating "HERO" like an
   alert code when it's a nickname — which would confuse the registry. Correct. That catch is what drove the
   whole C8-naming decision this session.

## STATE AT SESSION END
Step 1 (build-state verification) fully CLOSED. The picture: solid deterministic Agent A pipeline + sound
causal-graph registry + healthy verified marts, but only 1 of 5 fired alerts is actually detected today, and
the other 4 need WIRING (reusing existing math). HERO's code is locked as C8 (+1 → 59); the edit to record
that is scaffolded but deliberately UNEXECUTED, waiting on OP-1. Nothing else was built. The OneDrive/.git
risk is live and deferred by choice. Recruitment + the Shopify/Google-Ads/entity long-poles remain non-gated
parallel work. NEXT: open OP-1 — the returns-baseline grouping/abnormality method — which is the gate that
unblocks C8's detection fields and is shared by C3/C6/C2.
