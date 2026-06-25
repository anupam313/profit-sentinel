# Chat Context — 2026-06-25 — Durable RLS B+C + validate_sync defer

## What this session was
Two things after the Phase E close: (1) decide validate_sync.py (Phase F), and (2) make the
suppression_log RLS protection durable (owed items B+C). Both followed the C/D/E lesson —
read-only discovery first, then a gated write.

## 1. validate_sync.py — DEFERRED (not built)
Discovery found no orchestrator (manual _run_*.py runners) and no volume/freshness history table
to baseline against. Retrieval found the real spec — DEBT-004 (state_2026_05_14.md): compare live
source-API counts vs staging, >1% = fail, write public.sync_validation_log, suppress Agent A on
fail; its own trigger says "build before going live with any real client."
DECISION: defer to first live Airbyte connection. The ground-truth side (live API counts) does not
exist in seed-only pre-pilot, there is no API-fetch layer, and the count mechanism may change at
connection (Airbyte job-stats may replace API re-query) — building blind risks reworking the table
at connection. No pre-pilot gap: validate_seed() covers seed integrity; nothing live to validate
yet. Reconciled spec recorded in the state file (owed G).
Position change flagged case (a): a new fact (no live API + DEBT-004's own trigger) the earlier
"build Phase F now" call missed — the work is unchanged, its timing moved.

## 2. Durable RLS B+C — DONE + committed (8a57c4b)
Phase E enabled RLS live but it was live-DB-only (lost on a from-scratch rebuild), and the
anon/authenticated table grants still sat under the row-level deny. Discovery's load-bearing find
(§C9): Supabase pg_default_acl re-grants anon/authenticated full DML on EVERY new public-table
CREATE, from both `postgres` and `supabase_admin`. So a one-time REVOKE is undone by the next
CREATE, and `ALTER DEFAULT PRIVILEGES` is the wrong tool (postgres is not superuser, can't alter
the supabase_admin default; altering the postgres default hits every future table).
DESIGN (architect's call): co-locate an idempotent ENABLE RLS + owner REVOKE right after the
CREATE in seed_tiktok.create_tables() (durable on every rebuild, owner-authorized regardless of
granting role) + a one-time live REVOKE to close the current exposure. Built, verified
(anon/auth = 0 grants; postgres/service_role retain; RLS on; rolled-back write probe = 1),
committed as 8a57c4b (1 file, 6 insertions).

## The systemic finding (recorded, routed — bigger than B+C)
§C11: the same default-ACL exposes 15 public tables identically; RLS covers only a subset.
Sensitive tables WITHOUT an RLS backstop — client_config, alert_log, thread_context,
brand_event_calendar — are live RULE 8 violations and cross-tenant B2B exposure. NOT folded into
B+C (one-item discipline + needs its own blast-radius discovery). Recommended as the next phase.

## Why we recorded before expanding
B+C done, the validate_sync defer, and §C9/§C11 were all memory-only after the commit. A
continuity save now (write-light, no DB) makes them durable before opening the bigger
systemic-sweep write phase — so the sweep starts from an accurate base, not a stale one.

## Open for the founder (not architecture)
NEXT: systemic public-schema RLS + grant sweep [architect's recommendation], led by read-only
discovery — vs defer to post-pilot and do the canonical-corrections pass (E) instead. Risk call.

## Method notes carried
- Mount untrusted; reason only from HEAD / pasted live files. save_protocol live this session (149).
- Continuity pair authored in chat, critiqued x3, verified by Claude Code, committed by explicit
  path, no push. Re-upload-to-Project retired.
