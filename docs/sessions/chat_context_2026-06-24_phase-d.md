# Chat Context — 2026-06-24 — Phase D (make controls real, R11)
## Companion to state_2026-06-24_phase-d.md. Narrative of how the session went and why.

---

## THE ARC OF THE SESSION

We opened at the Phase C boundary (Phase C committed at `fe8725b`, session-state commit `5724469`
on top). The session's job was Phase D of pre-pilot hardening: take the data-integrity controls
that were *designed* but never *enforced* and put them in the path — the systemic story this whole
hardening stream is closing.

The method that worked in Phase C carried over: lead with a READ-ONLY discovery pass, paste the
findings back, and only THEN write the build prompt against real code — never against the canonical
docs, which had drifted. That discipline paid off immediately. The discovery surfaced two things
that reshaped the plan before a single edit:

1. The G4 facts in the Phase C state file were STALE. They claimed `order_line_items.id` wasn't
   unique and `klaviyo_email_events.message_id` had 374 collisions. Live at HEAD, both are fully
   unique. So Phase D only had to ADD tests on already-clean keys — no surrogate invention.
2. Reading the real `technical_architecture.md` (which the founder had to upload because the
   project mount was stale at 3815 vs HEAD 3947) confirmed the raw Shopify tables are
   Airbyte-managed. That made raw-table unique constraints the WRONG durable surface (DEBT-006 is
   the exact precedent). The durable controls became: dbt staging uniqueness tests + a pre-commit
   seed gate — both Airbyte-independent.

## THE STALE-MOUNT TAX (and the fix)

A recurring friction this session: the project snapshot kept serving stale copies — tech-arch at
3815 (HEAD 3947), and CLAUDE.md not mounted at all. The chat can read files the founder UPLOADS,
but cannot write the read-only project snapshot, so the fix is for the founder to re-upload the
live canonical docs TO the Project. We did that for tech-arch and CLAUDE.md mid-session, which let
the design be verified against the genuine HEAD. The state file's FILES-TO-UPLOAD section now
carries this as a standing close action.

## WHAT GOT DECIDED (and the reversals, named)

The build went through four honest position changes, each flagged as new-fact (case a) or
under-tested-prior (case b), never slipped in silently:
- Composite-uniqueness via a surrogate `md5(...)` column → reversed to native dbt SINGULAR tests,
  because the surrogate needs `::text` casts and CLAUDE.md RULE 4 forbids casts in dbt. The
  singular test (`group by ... having count(*)>1`) needs no cast and no model edit. (case a — RULE 4.)
- "Add unique constraints on the raw spine tables" → reversed to "add NONE on raw Airbyte tables;
  enforce in staging + seed gate." (case a — Airbyte-managed reality.)
- "Keep all the heavy validate_seed checks critical" → refined to an OWNERSHIP split: the gate
  blocks only on integrity seed_shopify owns and can certify; genuinely cross-source checks (#6
  sku_cost, #9 dq-7-sources) became advisory so a not-yet-loaded connector can never roll back good
  Shopify data. (case a/b.)
- #8 (alert_log Alert3) and #10 (client suppression_log) were first listed advisory off the RULE 3
  label, then the verified writer map showed both are seed-owned → promoted to CRITICAL. (case b.)

The resilience design matters: because the gate now runs PRE-commit and gates the commit, a pooler
timeout on a heavy check could false-roll-back a good seed (the R9 doc recorded exactly that
timeout). So each check sits behind a SAVEPOINT with a generous statement_timeout, a data-assertion
false is a FAIL (rollback), but an exception/timeout retries once and only a persistent error on a
critical check rolls back. That asymmetry is deliberate — a false rollback is safe (the whole seed
transaction reverts to the prior good state), a false commit of doubled data is the R9 disaster.

## TWO SELF-INFLICTED HARNESS SLIPS (worth remembering)

Claude Code made two hand-built-harness mistakes that LOOKED like product bugs but weren't: a
float-floor artifact in the band math (fixed with integer arithmetic), and a wrong `client_id` in
the #10 fault-injection harness (`client_azure_co` instead of the real `CLIENT_ID='azure_co'`),
which made #10 spuriously return 0. The delivered gate was correct in both cases; the harnesses were
wrong. Lesson carried forward: a standalone proof harness is itself code that can be wrong — the
real backstop is the next legitimate re-seed exercising the gate live.

## HOW IT CLOSED

Phase D committed at `2863e5c` — exactly 6 files (+278/−30), no push. Pre-commit we ran the
save-protocol's high-value guards on the two CANONICAL edits only (Check 10 semantic read-back,
Check 4 no-live-"RULE 5"-label, Check 2 date stamp on tech-arch); the heavy full Phase-0/Checks-1–11
machinery is for this session-close save of the continuity pair. The handle registry update is NOT
in the code commit — it lands here, in this pair, mirroring Phase C (`fe8725b` code → `5724469`
docs). Two handles moved: tech-arch 3947→3971, CLAUDE.md 214→260.

## WHERE THE NEXT SESSION PICKS UP

Phase E (R13 suppression_log canonicalization) — in a NEW chat per the per-session cadence. The
writer map is the design input: `client_azure_co.suppression_log` is seed-only, `public.suppression_log`
is connectors-only; pick the richer client schema as canonical, migrate the public rows, repoint
writers, one home. Before that, the founder should: (1) re-upload CLAUDE.md + tech-arch to the
Project, (2) approve this continuity pair so Claude Code verifies + commits it. Still owed across the
stream: Phase F (validate_sync.py), the canonical-corrections pass, and the eventual one-coherent
push (reconcile the 10-vs-11 stack depth first).
