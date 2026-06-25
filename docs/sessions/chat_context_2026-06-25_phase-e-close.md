# Chat Context — 2026-06-25 — Phase E close (RLS on public.suppression_log)

## What this session was
The deferred tail of Phase E: decide and apply the RLS posture on public.suppression_log, then
close. Method followed the C/D/E lesson — read-only discovery first, paste findings, gated
write, verify, only then close.

## The arc, in order
1. READ-ONLY DISCOVERY on public.suppression_log: schema, columns + identity, constraints,
   FK in/out, triggers, indexes, RLS state, grants, view deps, every code reader/writer + its
   connection role, gate/test refs. Built to enumerate writers EMPIRICALLY rather than trust the
   docs — which proved necessary.
2. Discovery resolved two doc contradictions:
   - tech_arch DDL comment "Agent A writes..." names ONLY Agent A. WRONG: 4 writers (Agent A +
     tiktok/sentry/loop seeds), all DATABASE_URL->postgres (bypass).
   - RULE 3 / tech_arch ~720 say the table keeps a stored is_synthetic column. WRONG: absent
     live. And the whole tech_arch CREATE block is stale (12 vs live 20 cols, a FK that doesn't
     exist, a missing UNIQUE).
3. FAIL-CLOSED VERDICT: SAFE to ENABLE RLS (no policy) — all writers bypass (owner/service_role);
   anon/authenticated (the actual exposure) get row-denied; no FK/trigger/view cascade surface.
4. GATED WRITE: ALTER ... ENABLE ROW LEVEL SECURITY ran behind gates G1-G3; verifies V1-V3
   passed (enabled-not-forced; postgres still writes via a rolled-back probe; anon/auth denied).
   No policy, no force, no grants changed, no repo artifact, no commit.
5. BLIND SPOT — out-of-repo writers. The founder could not confirm a negative from memory
   (correct — wrong instrument). Resolved by (a) reasoning: the architecture has no anon write
   path (Next.js is config/audit-only and unbuilt; all writes are backend), (b) a repo-wide scan
   that found ZERO client/anon/edge/JS-TS surface, (c) reversibility + a watch window. Residual =
   out-of-band only.

## The decision that matters, and why it holds
KEEP RLS ENABLED. The load-bearing reason is the ASYMMETRY, which does not depend on any doc
being right: reverting = a CERTAIN cross-tenant customer-data read-breach; keeping it on risks
only a HYPOTHETICAL, internal-audit-only, loud, reversible write-break. Architecture + the scan
are corroboration, not the foundation — deliberately, because the docs have been wrong all phase.

## Why we did NOT do the durable fix this session
The live exposure is already shut, fail-closed. REVOKE (C), reseed-durability (B), and the
client_id policy (D) are hardening on top of a secure state, and the state file routes them to
ONE coherent RULE 8 pass. Bolting them onto a close is the churn the one-item discipline exists
to prevent. Reseed-durability (B) is deferrable ONLY because it is now recorded loudly — RLS is
lost on a from-scratch rebuild; normal reseeds keep it (CREATE IF NOT EXISTS).

## Open for the founder (not architecture)
Priority knob: Phase F (R10 validate_sync.py) next [architect's recommendation] vs the durable
RLS pass first. Decided by risk appetite on the narrow from-scratch-rebuild window, not by
correctness.

## Method notes carried
- Mount untrusted; reason only from HEAD / pasted live files. save_protocol pasted live this
  session (149, matches).
- Continuity pair authored in chat, critiqued x3, verified by Claude Code, committed by explicit
  path, no push. Re-upload-to-Project retired.
