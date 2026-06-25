## SESSION OPEN — LOAD FIRST (do this before any work)
- Load docs/save_protocol.md FIRST (authoritative; 149 lines). It governs every save.
- Load the latest continuity pair: state_2026-06-25_phase-e-close.md (96 lines) +
  chat_context_2026-06-25_phase-e-close.md (52 lines). If either file's wc -l differs from
  its handle here, a stale/truncated copy is mounted: STOP and ask for the live copy.
- Re-verify the 9 canonical line-count handles AGAINST REPO HEAD before any design/edit work:
    product_strategy 1424 · technical_architecture 3971 · agent_d_build_spec 2722 ·
    cross_alert_orchestration 847 · d1_validation_gates 399 · pre_agent_build_checklist 389 ·
    save_protocol 149 · pilot_scope 122 · CLAUDE.md 260.
  Phase E (incl. this close) edited NO canonical spec — ALL 9 UNCHANGED at HEAD. Four were
  re-verified live this session (product_strategy 1424, technical_architecture 3971,
  CLAUDE.md 260, save_protocol 149). Any drift is an error to flag.

- Repo state: pre-close HEAD = c7bb84a, unpushed. The Phase-E-close commit (this pair) becomes
  the new HEAD, taking the local-only stack to 15 above remote 7d5c2e7. The live RLS ALTER
  produced NO repo artifact, so HEAD did NOT move from it. The full pre-close commit stack =
  the 14 documented in state_2026-06-25_phase-e.md; this close adds ONE commit on top. Do NOT
  trust any transcription — VERIFY live: `git log --oneline -3` and
  `git rev-list --count 7d5c2e7..HEAD` (expect 14 before the close commit, 15 after).
  Push as ONE coherent set later, never piecemeal.

- Working tree: undisposed Group B remains — seed_meta.py (M), onboarding_flow.py (M), untracked
  connectors/_*.py probes, historical_pattern_scan.py, seed_b4_patch.py, seed_google_ads.py,
  slack_bot/, docs/sessions/* (the new continuity pair lives here). OPTION C DISCIPLINE: stage
  by EXPLICIT path only; never git add -A/.; no Group B file enters a commit. This close stages
  ONLY the two continuity files, by path.

- MOUNT IS UNTRUSTED (Project content-cache bug serves stale copies). HEAD is the only source of
  truth. The founder will NOT rename files. When a canonical doc is needed for design/verify, ASK
  the founder to paste the live copy and reason from that. Verify the 9 handles vs HEAD at open.
- Canonical files live under docs/ (CLAUDE.md at repo root); continuity pairs under docs/sessions/.

## DONE THIS SESSION (Phase E tail — RLS on public.suppression_log)
- RLS ENABLED, live, verified. `ALTER TABLE public.suppression_log ENABLE ROW LEVEL SECURITY`
  ran — NO policy, NO force. Posture = deny-all to non-bypass roles (the founder-mandated B2B
  isolation fix). Closes the RULE 8 "enabled" gap and the prior anon/authenticated cross-tenant
  READ exposure. Gates G1-G3 + verifies V1-V3 all passed; not rolled back.
  REVERSIBLE: `ALTER TABLE public.suppression_log DISABLE ROW LEVEL SECURITY;` (= R1).
- Writers (VERIFIED live): 4 — agent_a.py:651 (Agent A, INSERT-only) + seed_tiktok.py:941 +
  seed_sentry.py:492 + seed_loop_returns.py:839. ALL connect DATABASE_URL -> postgres
  (rolbypassrls=true AND table owner) -> bypass RLS -> unaffected by deny-all. service_role would
  also bypass. NO product reader exists (Agent A never reads the table).
- DECISION (architect's call, OWNED): KEEP RLS ENABLED, do not revert. Reasoning = asymmetry —
  reverting re-opens a CERTAIN known customer-data read-breach; the only downside of keeping it
  on is a HYPOTHETICAL, internal-audit-only, loud, reversible write-break. Robust even if the
  docs are wrong (they have been this phase).
- Out-of-repo write surface = empirically NIL in-repo (scan §A-§E): zero JS/TS/JSX/TSX files,
  no createClient / @supabase/supabase-js, no anon/service_role-key client, no supabase/ dir,
  no edge functions, no PostgREST calls, frontend/ is an EMPTY placeholder, no alt DB connection
  — every path is Python->psycopg2->DATABASE_URL->postgres. Residual = out-of-band ONLY
  (hand-deployed edge fn / dashboard SQL editor / separate app); covered by F (watch + R1).

## LIVE-DB FACTS CAPTURED (suppression_log — these SUPERSEDE the stale tech_arch DDL; correction OWED -> E)
- 20 columns (NOT the 12 in the tech_arch CREATE block). id = bigint IDENTITY ALWAYS, PK.
  UNIQUE(client_id, alert_type, would_have_fired_at) = uq_suppression_log_signal.
  NO FK in or out — tech_arch's brand_event_calendar_id FK does NOT exist live. No triggers,
  no views/matviews depending on it.
- is_synthetic is ABSENT. RULE 3 / tech_arch ~720 "seed-set is_synthetic" claim is STALE for
  THIS table; provenance is implicit (100% seed-authored). Do NOT treat the claim as live.
- Grants: anon, authenticated, postgres, service_role all hold full DML + TRUNCATE/REFERENCES/
  TRIGGER. anon/authenticated do NOT bypass RLS (now row-denied); postgres/service_role bypass.
  CAVEAT: RLS does NOT gate TRUNCATE — the anon/authenticated TRUNCATE grant is LATENT (not
  reachable via PostgREST today); REVOKE it in the durable pass (C).

## NEXT ACTION — OPEN PRIORITY CALL (founder's risk appetite; NOT architecture)
Phase E is closeable now (live exposure shut, fail-closed). Two valid next moves:
  (1) Phase F — R10 build validate_sync.py (the absent post-sync variance guard).
      [architect's recommendation: live exposure already closed; the rest is hardening]
  (2) Durable RLS hardening pass first (items B+C), if risk appetite on the from-scratch-rebuild
      window is low.
Lead either with a READ-ONLY discovery pass (the C/D/E lesson).

## CARRIED OWED
- B. RLS NOT reseed-durable — live-DB-only; LOST on a from-scratch rebuild (DR / fresh env /
     explicit DROP+recreate). Table DDL lives in seed_tiktok.py:374 as CREATE TABLE IF NOT
     EXISTS, so NORMAL reseeds against the existing DB KEEP RLS — only a from-scratch rebuild
     loses it. Durable fix: move the DDL to a shared home + idempotent ENABLE RLS there.
     Breadcrumb: historical_pattern_scan.py:212 already carries a placeholder comment
     "Enable RLS (Supabase service_role bypasses it; required by RULE 8)" — likely the right
     home. -> durable RULE 8 pass.
- C. REVOKE residual anon/authenticated DML + TRUNCATE grants on public.suppression_log
     (removes latent grants + the TRUNCATE escape). Hardening, not a blocker (RLS-no-policy
     already fail-closes). -> durable RULE 8 pass, one coherent pass with B.
- D. Per-client client_id RLS policy — needs JWT/GUC session context that does not exist.
     -> post-pilot, codebase-wide security debt.
- E. DOC-SYNC (RULE 9) -> canonical-corrections pass: replace the wholesale-stale tech_arch
     suppression_log DDL block with the live 20-col shape; correct the RULE 3 / ~720
     is_synthetic claim for this table; correct the "Agent A only" DDL comment (true set =
     Agent A + 3 seeds); record the RLS posture.
- F. WATCH WINDOW (operational): next Agent A suppression write + next seed run exercise the live
     write path — monitor logs/Sentry for any RLS-denial on suppression_log. A clean window =
     out-of-band writer empirically absent. R1 reverses instantly if one surfaces.
- G. Phase F — R10 validate_sync.py (next build, per (1)).
- H. Pre-existing carry: the 9 R9 corrected facts + D-A..D-F doc landings (canonical-corrections
     pass); Group B housekeeping; the ONE coherent push (reconcile the now-15-deep stack live
     first). Re-upload-to-Project is RETIRED — paste-on-request instead.
