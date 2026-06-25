## SESSION OPEN — LOAD FIRST (do this before any work)
- Load docs/save_protocol.md FIRST (authoritative; 149 lines). It governs every save.
- Load the latest continuity pair: state_2026-06-25_durable-rls-bc.md (117 lines) +
  chat_context_2026-06-25_durable-rls-bc.md (52 lines). If either file's wc -l differs from
  its handle here, a stale/truncated copy is mounted: STOP and ask for the live copy.
- Re-verify the 9 canonical line-count handles AGAINST REPO HEAD before any design/edit work:
    product_strategy 1424 · technical_architecture 3971 · agent_d_build_spec 2722 ·
    cross_alert_orchestration 847 · d1_validation_gates 399 · pre_agent_build_checklist 389 ·
    save_protocol 149 · pilot_scope 122 · CLAUDE.md 260.
  This session edited NO canonical spec (only connectors/seed_tiktok.py) — ALL 9 UNCHANGED at
  HEAD. Any drift is an error to flag.

- Repo state: pre-close HEAD = 8a57c4b, unpushed. The close commit (this pair) becomes the new
  HEAD, taking the local-only stack to 17 above remote 7d5c2e7. Two DB-only writes this session
  (the one-time live REVOKE; and Phase E's ENABLE RLS earlier) produced NO repo artifact, so HEAD
  did NOT move from them. Stack top: 8a57c4b (B+C seed_tiktok durable RLS+REVOKE) -> 4c66dc8
  (Phase E close pair) -> c7bb84a (prior Phase E state+context) -> ... -> b8fec19. VERIFY live:
  `git log --oneline -3` and `git rev-list --count 7d5c2e7..HEAD` (expect 16 before this close
  commit, 17 after). Push as ONE coherent set later, never piecemeal.

- Working tree: undisposed Group B UNCHANGED this session — seed_meta.py (M), onboarding_flow.py
  (M), untracked connectors/_*.py probes, historical_pattern_scan.py, seed_b4_patch.py,
  seed_google_ads.py, slack_bot/, docs/sessions/*. NOTE: seed_tiktok.py is NOT Group B (it was
  clean; this session's B+C edit is committed in 8a57c4b). OPTION C DISCIPLINE: stage by EXPLICIT
  path only; never git add -A/.; no Group B file enters a commit. This close stages ONLY the two
  continuity files, by path.

- MOUNT IS UNTRUSTED (Project content-cache bug serves stale copies). HEAD is the only source of
  truth. The founder will NOT rename files. When a canonical doc is needed, ASK the founder to
  paste the live copy and reason from that. Verify the 9 handles vs HEAD at open.
- Canonical files live under docs/ (CLAUDE.md at repo root); continuity pairs under docs/sessions/.

## DONE THIS SESSION

### 1. validate_sync.py (Phase F) — DEFERRED, not built (decision)
- Retrieved the real spec: DEBT-004 in state_2026_05_14.md (committed) — "compare API record
  counts vs Supabase staging counts; >1% variance = fail; write public.sync_validation_log; run
  after every Airbyte sync, before dbt; suppress Agent A on fail." Its own trigger: "build before
  going live with any real client."
- DECISION (architect's call, OWNED): DEFER the build to first live Airbyte connection (pilot
  onboarding). Rationale: the check's ground-truth side (live source-API counts) does NOT exist
  in seed-only pre-pilot — no API-fetch layer in the repo, no orchestrator hook, and the count
  mechanism may change at first connection (Airbyte native job-stats may replace API re-query),
  so building blind risks a table shape that reworks at connection. NO pre-pilot gap: validate_seed()
  gates seed integrity; there is no live sync to validate yet.
- Position change flagged case (a): a NEW fact (no live API + DEBT-004's own trigger) the earlier
  "build Phase F now" recommendation missed — the work is unchanged, its timing moved.
- Reconciled DEBT-004 spec recorded under owed item G (build-at-first-connection).

### 2. Durable RLS pass (B+C) on public.suppression_log — DONE + COMMITTED (8a57c4b)
- B (durability): co-located idempotent `ALTER TABLE public.suppression_log ENABLE ROW LEVEL
  SECURITY` after the CREATE in connectors/seed_tiktok.py::create_tables() — so RLS survives a
  from-scratch rebuild (the reseed-durability gap from Phase E close, now CLOSED).
- DURABILITY IS AIRTIGHT DESPITE THE ODD HOME: suppression_log's ONLY create site is
  seed_tiktok.create_tables(), so there is no code path where the table exists without the
  co-located ENABLE RLS + REVOKE. DEFERRED (housekeeping, routed to owed item I): relocating the
  CREATE to a tidier shared bring-up home (_setup_tables.py-style) — cosmetic only; durability is
  achieved in place. Deferred, not lost.
- C (durable revoke): co-located idempotent `REVOKE ALL ON public.suppression_log FROM anon,
  authenticated` in the same path + a one-time live REVOKE applied & verified.
- VERIFIED live: anon/authenticated grants = 0 rows; postgres + service_role retain; RLS = true /
  not-forced; rolled-back postgres write probe = 1 (write path intact). Reversible:
  `GRANT ALL ON public.suppression_log TO anon, authenticated;` (only if needed).

## KEY FINDINGS THIS SESSION (record so they don't evaporate)
- §C9 — Supabase DEFAULT PRIVILEGES re-grant: pg_default_acl carries entries from BOTH granting
  roles `postgres` AND `supabase_admin` that auto-grant anon/authenticated FULL DML (incl.
  TRUNCATE) on EVERY new public-schema table CREATE. Consequence: a one-time table REVOKE is undone
  by the next fresh CREATE. Durable fix = owner REVOKE co-located in the create path (done for
  suppression_log), NOT `ALTER DEFAULT PRIVILEGES` — postgres is NOT superuser (cannot alter the
  supabase_admin default), and altering the postgres default would change behaviour for EVERY
  future public table (out of scope). RLS-no-policy remains the independent fail-closed backstop.
- §C11 — SYSTEMIC EXPOSURE (routed to owed item H): 15 public tables carry the identical
  anon/authenticated full-DML grant. RLS is enabled on only a subset (suppression_log + the 3 from
  historical_pattern_scan + registry/schema_versions from _setup_tables). Sensitive tables WITHOUT
  an RLS backstop: client_config, alert_log, thread_context, brand_event_calendar — live RULE 8
  violations + cross-tenant B2B exposure. Bigger than B+C; needs its own read-only discovery.

## NEXT ACTION — RECOMMENDED (founder's priority call; NOT architecture)
SYSTEMIC public-schema RLS + grant sweep (owed item H) — lead with a READ-ONLY discovery pass
(blast radius: does anything legitimately reach those 14 other tables via anon/authenticated/
PostgREST before we deny them?). Architect's recommendation, given the live RULE 8 violations on
sensitive tables. Alternative: defer the sweep to post-pilot and do the canonical-corrections
pass (E) instead — founder's risk call.

## CARRIED OWED   (formerly-owed B and C are now DONE — see DONE THIS SESSION §2)
- D. Per-client client_id RLS policy on public tables — needs JWT/GUC session context that does
     not exist. -> post-pilot, codebase-wide security debt.
- E. DOC-SYNC (RULE 9) -> canonical-corrections pass: (a) replace the stale tech_arch
     suppression_log DDL block with the live 20-col shape; (b) correct the RULE 3 / ~720
     is_synthetic claim for this table; (c) correct the "Agent A only" DDL comment (true set =
     Agent A + tiktok/sentry/loop seeds); (d) reconcile the R10/R11/DEBT-004 ID drift for the sync
     guard; (e) record that seed_tiktok.create_tables() now manages suppression_log RLS + REVOKE;
     (f) document the §C9 pg_default_acl re-grant as a known platform constraint.
- F. WATCH WINDOW (operational): next Agent A suppression write + next seed run exercise the live
     suppression_log write path — monitor logs/Sentry for any RLS-denial. Clean = out-of-band
     writer empirically absent. DISABLE RLS reverses instantly if one surfaces.
- G. validate_sync.py — BUILD AT FIRST LIVE AIRBYTE CONNECTION (pilot onboarding), NOT pre-pilot.
     Reconciled DEBT-004 spec:
       - Scope: Airbyte-synced sources only (Shopify, Klaviyo, Gorgias, Loop, TikTok). Meta / GA4 /
         Sentry / Google Ads = manual seeds, OUT of sync scope.
       - OPEN mechanism (resolve at first connection): source-API count query vs Airbyte native
         job-stats as ground-truth — decides sync_validation_log shape.
       - Failure action: route through the existing run_dq_prechecks skip_map / suppression path,
         NOT a parallel mechanism.
       - Write target: public.sync_validation_log (NEW) — inherits the hardened public-table
         RLS + REVOKE pattern (B+C).
       - Pattern: mirror validate_seed() (SAVEPOINT-per-check, 120s timeout, retry-once,
         CRITICAL/ADVISORY result structure; RULE 5/6).
       - Threshold >1% variance = fail (original DEBT-004) — revisit vs brand-derived bands.
- H. SYSTEMIC public-schema RLS + grant sweep — see KEY FINDINGS §C11 + NEXT ACTION. Recommended
     next; own read-only discovery first.
- I. Pre-existing carry + housekeeping: the 9 R9 corrected facts + D-A..D-F doc landings
     (canonical-corrections pass); relocate suppression_log's CREATE from seed_tiktok.py to a
     shared bring-up home (cosmetic — durability already achieved in place; see DONE §2); Group B
     housekeeping; the ONE coherent push (reconcile the now-17-deep stack live first).
     Re-upload-to-Project is RETIRED — paste-on-request instead.
