## SESSION OPEN — LOAD FIRST (do this before any work)
- THIS PAIR'S SELF-HANDLES: state_2026-06-26_owed-h-close.md = 202 lines;
  chat_context_2026-06-26_owed-h-close.md = 74 lines. If either file's real wc -l differs from
  these, a stale/truncated copy is mounted: STOP and ask for the live copy.
- Load docs/save_protocol.md FIRST (governs every save). Handle 149 is CARRIED (untouched this
  session, not re-verified here) — re-verify at HEAD like the rest.
- Re-verify the 9 canonical line-count handles AGAINST REPO HEAD before any design/edit work:
    product_strategy 1424 · technical_architecture 3987 · agent_d_build_spec 2722 ·
    cross_alert_orchestration 847 · d1_validation_gates 399 · pre_agent_build_checklist 389 ·
    save_protocol 149 · pilot_scope 122 · CLAUDE.md 271.
  VERIFIED-CHANGED THIS SESSION (the only two I edited + re-counted): technical_architecture
  3971 -> 3987 (+16, RLS posture note); CLAUDE.md 260 -> 271 (+11, RUN PATH 1b). The other 7
  are CARRIED from the prior pair, NOT re-counted this session — treat all 9 as re-verify-at-HEAD,
  not as confirmed. Any drift = flag.

- Repo state: HEAD = a46f541 on master ("Harden public schema: RLS + revoke anon/authenticated
  (owed H)"). 3 files, 303 insertions: connectors/_harden_public_schema.py (new, 276 lines),
  CLAUDE.md (+11), docs/technical_architecture.md (+16). seed_tiktok.py UNCHANGED (clean, matches
  prior HEAD 8a57c4b). VERIFY live at open: `git log --oneline -1` (expect a46f541) and
  `git rev-list --count 7d5c2e7..HEAD`. EXPECTED = 18, but TREAT AS THE ONE NUMBER MOST LIKELY TO
  DRIFT — it reconciles only if the prior Phase-E/B+C close-pair commits already landed. If it is
  not 18, do not panic-edit; reconcile the stack against `git log --oneline -20` before trusting
  any count. Push as ONE coherent set later, never piecemeal — still DEFERRED.

- Working tree (undisposed Group B, UNCHANGED this session): seed_meta.py (M), onboarding_flow.py
  (M); untracked: connectors/seed_google_ads.py, seed_b4_patch.py, historical_pattern_scan.py,
  _check_db_state.py, _dryrun_determinism.py, slack_bot/, docs/sessions/*. PLUS three new untracked
  READ-ONLY probe scripts from this session: _rls_grant_discovery.py, _rls_grant_harden_live.py,
  _harden_precondition_probe.py. OPTION C DISCIPLINE: stage by EXPLICIT path only; never
  git add -A/.; no Group B and no probe script enters a commit.

- MOUNT IS UNTRUSTED (Project content-cache bug serves stale copies). HEAD is the only source of
  truth. The founder will NOT rename files. When a canonical doc is needed, ASK the founder to
  paste the live copy and reason from that. Verify the 9 handles vs HEAD at open.
- Canonical files live under docs/ (CLAUDE.md at repo root); continuity pairs under docs/sessions/.

## DONE THIS SESSION — owed item H: code + live exposure CLOSED; operational watch (F) OPEN
(Headline precisely: the code is committed and the live anon/auth exposure is shut. The operational
tail — confirming no out-of-repo anon consumer breaks under the new RLS/REVOKE — is owed item F
below and is NOT yet verified. Do not treat F as optional cleanup.)

### 1. Live RLS + grant hardening — DONE + COMMITTED TO DB (earlier this session)
- One atomic, fail-closed transaction over the public schema. Discovery found 15 public base
  tables (0 views). CLAUDE.md's "6 application tables" list was STALE — live truth = 15.
- ENABLE ROW LEVEL SECURITY on the 7 that were RLS-off: client_config, brand_event_calendar,
  founder_preference_profile, influencer_profile, network_pattern_benchmarks,
  permanent_dq_limitations, config_change_log.
- REVOKE ALL FROM anon, authenticated on all 14 MUST-FIX tables (closed the TRUNCATE-bypasses-RLS
  hole on the 5 that were RLS-on-but-not-revoked: candidate_signals, causal_pattern_validation,
  onboarding_messages, schema_versions, source_schema_registry).
- DROP POLICY "service role full access" (granted to PUBLIC, qual=true => leaked to anon/auth) on
  alert_log and thread_context. service_role has BYPASSRLS, did not need it.
- suppression_log left untouched (verify-only — already B+C-hardened in 8a57c4b).
- VERIFIED live: all 15 tables RLS=on, anon/auth=0 privs, postgres+service_role retain full (7);
  rolled-back owner-write probe PASS. Reversible (per-table GRANT ... TO anon, authenticated).

### 2. Durable hardener — AUTHORED + COMMITTED (a46f541)
- NEW connectors/_harden_public_schema.py (276 lines) — authoritative, idempotent,
  existence-guarded, fail-closed (rolls back + RAISES on verify failure, like validate_seed()):
  - Lever A: ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public REVOKE ALL ON TABLES
    FROM anon, authenticated. Stops a NEW public CREATE (as postgres) from re-granting anon/auth.
  - Lever B: EXPLICIT hardcoded 15-table list (NOT dynamic pg_class sweep — auditable surface);
    each existing table gets ENABLE RLS (NO FORCE) + REVOKE ALL FROM anon, authenticated; absent
    tables skipped+logged.
  - Standalone main() + _get_conn(); verified clean idempotent no-op smoke-run (applied=15,
    skipped=0, probe=PASS, Lever A already-applied).

### 3. De-wired to RUN PATH 1b — CORRECTED + COMMITTED (a46f541)
- Claude Code initially wired the schema-wide harden call into seed_tiktok.py::main() ("terminal
  seed"). REJECTED: CLAUDE.md RUN PATH says "Seed order is NOT fixed," so seed_tiktok is not
  guaranteed last; an order-DEPENDENT whole-schema sweep cannot ride an order-UNFIXED seed.
  (Contrast suppression_log's REVOKE, which is order-INDEPENDENT — co-located with its own CREATE.)
- FIX: de-wired from seed_tiktok (file reverted to HEAD, clean); added CLAUDE.md RUN PATH step 1b
  = explicit standalone final step (`python connectors/_harden_public_schema.py`), after all seeds,
  before dbt.
- technical_architecture.md: added the RLS-posture note (deny-all, NO policy; not FORCEd;
  postgres/service_role retain write path) and reconciled its wiring clause to RUN PATH 1b
  (the "called from seed_tiktok::main()" phrasing was corrected before commit — no stale clause shipped).

## RESIDUALS — routed forward, NAMED so none is lost (NOT done; deliberate)
- R1. supabase_admin default ACL — still re-grants anon/auth FULL DML on dashboard-created public
      tables. UNTOUCHABLE as postgres (not a member, not superuser; cannot ALTER its default).
      Defense = periodic re-run of harden_public_schema() + a new dashboard table is a manual act.
      Record as a known platform constraint (lands in owed E doc-sync).
- R2. REPRODUCIBILITY GAP — 5 foundational public tables have NO repo CREATE site (doc-only /
      dashboard-born): client_config, alert_log, thread_context, config_change_log,
      brand_event_calendar. Their durability is LIVE-DB-ONLY, not rebuild-safe, until real DDLs
      are captured into the repo. Bigger than RLS; needs the TRUE live DDLs (not the stale doc
      blocks); its own deliberate pass. client_config especially is read by ~everything.

## CARRIED OWED (unchanged unless noted)
> COMPLETENESS CAVEAT: this list (D,E,F,G,I) was reconstructed this session, not diffed line-by-line
> against the prior state file's owed list. B and C closed LAST session (8a57c4b, suppression_log
> durability) — before this session, not by the H work. Before this pair is committed, diff this
> carried set against state_2026-06-25_durable-rls-bc.md's CARRIED OWED to confirm nothing open was
> dropped. (Stage prompt does this.)
- D. Per-client client_id RLS POLICY on public tables — needs JWT/GUC session context that does
     not exist yet. -> post-pilot, codebase-wide security debt. (RLS is currently deny-all/no-policy.)
- E. DOC-SYNC (RULE 9) -> canonical-corrections pass. Carried sub-items a-f from the prior state
     file, UNCHANGED (none dropped): (a) replace the stale tech_arch suppression_log DDL block with
     the live 20-col shape; (b) correct the RULE 3 / ~720 is_synthetic claim for this table;
     (c) correct the "Agent A only" DDL comment (true set = Agent A + tiktok/sentry/loop seeds);
     (d) reconcile the R10/R11/DEBT-004 ID drift for the sync guard; (e) record that
     seed_tiktok.create_tables() now manages suppression_log RLS + REVOKE; (f) document the §C9
     pg_default_acl re-grant as a known platform constraint. ADDED THIS SESSION: (g) R1 — the
     supabase_admin default-ACL residual; (h) document the public-schema RLS posture (deny-all,
     no policy) and the RUN PATH 1b durability home (note already landed in tech_arch this session,
     but the full corrections pass should integrate it). Also still owed from prior I: the 9 R9
     corrected facts + D-A..D-F landings.
- F. WATCH WINDOW (operational) — TWO parts, both open:
     (a) The NEXT Agent A suppression write + NEXT seed run exercise the live public-table write
         path under the new RLS/REVOKE — monitor logs/Sentry for ANY permission-denied / RLS-denial.
         Clean = no out-of-repo (Realtime/Edge/Auth-hook) anon consumer exists. A live REVOKE
         reverses instantly if one surfaces.
     (b) NEW manual-step dependency created by the de-wire: hardening now runs ONLY via the explicit
         RUN PATH 1b step (`python connectors/_harden_public_schema.py`), NOT inside any seed. The
         live DB is already hardened, so no gap today — but a from-scratch rebuild that runs the
         seeds and SKIPS 1b yields an unhardened schema that looks done. In a no-orchestrator manual
         pipeline this is a real footgun; the durable fix is documented in CLAUDE.md 1b. Flag if a
         rebuild path ever automates seeds without 1b.
- G. validate_sync.py — BUILD AT FIRST LIVE AIRBYTE CONNECTION (pilot onboarding), NOT pre-pilot.
     Reconciled DEBT-004 spec (carried verbatim from prior state — do not re-compress):
       - Scope: Airbyte-synced sources only (Shopify, Klaviyo, Gorgias, Loop, TikTok). Meta / GA4 /
         Sentry / Google Ads = manual seeds, OUT of sync scope.
       - OPEN mechanism (resolve at first connection): source-API count query vs Airbyte native
         job-stats as ground-truth — decides sync_validation_log shape.
       - Failure action: route through the existing run_dq_prechecks skip_map / suppression path,
         NOT a parallel mechanism.
       - Write target: public.sync_validation_log (NEW) — inherits the hardened public-table
         RLS + REVOKE pattern (now via _harden_public_schema.py's explicit 15-table list — ADD it
         there when the table is created).
       - Pattern: mirror validate_seed() (SAVEPOINT-per-check, 120s timeout, retry-once,
         CRITICAL/ADVISORY result structure; RULE 5/6).
       - Threshold >1% variance = fail (original DEBT-004) — revisit vs brand-derived bands.
- I. Pre-existing carry + housekeeping: the ONE coherent push (stack depth per SESSION OPEN
     reconciliation above — expect 18, verify vs HEAD; reconcile live first, never piecemeal);
     Group B disposal; consolidate suppression_log's co-located REVOKE into
     _harden_public_schema.py someday (COSMETIC — durability already achieved in place);
     the 3 read-only probe scripts (keep for pre/post re-runs OR delete — FOUNDER DECISION PENDING;
     either way they never enter a commit). Re-upload-to-Project RETIRED — paste-on-request.

## POST-CLOSE ADDENDUM (2026-06-26, later same day) — seeding + fidelity audits + HERO reason-source decision
Authored AFTER the H-close commit (a6f3828); not part of that commit's scope. Records open threads from
later the same day so they survive into the next chat. (Its own commit will increment HEAD + the stack
count again — reconcile live at next open; do not trust a baked number.)

### Seeding completeness audit (read-only) — verdict: PARTIAL
- Data effectively complete: all 10 connectors populated; provenance cleanly isolatable (DEBT-006
  predicates; only 1-row Airbyte probe residuals); 5 marts at full 730-day grain; 51/51 dbt tests PASS.
- Two real gaps: (1) GA4 secondary tables empty (pages/devices/conversions/DAU/events/traffic) = known
  S3-P1/P2 items; (2) repo hygiene — seed_google_ads.py + seed_b4_patch.py UNTRACKED, seed_meta.py
  MODIFIED (Group B, owed I). Seed DATA is live; the seed CODEBASE is not fully committed.

### Seed-vs-current-API fidelity audit (read-only) — Google Ads + Meta FAITHFUL; Shopify = the find
- Google Ads FAITHFUL: cost_micros bigint + product_id present; mart B-9 reads cost_micros/1e6 correctly;
  seed pins v24.1 (= current major v24). Note (not a blocker): seed is ONE blended table vs Airbyte's
  per-stream split (shopping_performance_view separate) — staging may need per-stream awareness at connect.
- Meta FAITHFUL: spend + numeric insights stored as TEXT (matches v25 string contract); cast lives in
  stg_meta_ad_performance (spend::numeric) — real connector also returns strings -> same cast -> types match.
  content_ids ARRAY carries the HERO join. Expected synthetic gap: static snapshot, NO 28-day rolling
  restatement — handle at connector incremental config, not now.

### HERO reason-source — CONTRADICTION found + DECISION made (NEW owed item J)
- CONTRADICTION: the HERO return-driver reason join is wired LOOP-ONLY (mart_return_rate_by_sku reads
  loop_return_line_items.return_reason_primary), but pilot_scope §4/§6 say Shopify-NATIVE is PRIMARY, Loop
  opportunistic. Native reason IS seeded in shopify_order_refunds.return (jsonb) but NEVER parsed. This is
  an internal spec-vs-wiring contradiction, NOT API drift.
- IMPACT: HERO is the lead FIRED pilot alert (pilot_scope §3 defensible core). As wired it silently needs a
  Loop brand; for a native-only (non-Loop) brand the reason join has no source. NOT built to §4 spec.
- DECISION (founder, this session): wire HERO to Shopify-native — native primary, Loop supplement.
- NEW API FINDING (live Shopify docs, 2026-01): the native returnReason ENUM is DEPRECATED in favor of
  returnReasonDefinition {handle,name}. The parser MUST target the stable HANDLE (enum as fallback) — else it
  ships against a sunsetting field (the exact first-connect surprise the fidelity check was hunting).
- STATUS: read-only DISCOVERY PROMPT READY, NOT yet run. It pins: (§1) seeded jsonb shape; (§2 load-bearing)
  whether the seed models returnReasonDefinition/handle vs only the dead enum vs an invented shape — if only
  the dead enum, the SEED itself needs a shape fix FIRST; (§3) line_item_id->sku join path; (§4) native-vs-Loop
  reason taxonomy reconciliation to ONE canonical category; (§5) downstream readers of the Loop-only
  `returned` CTE before any repoint.
- PRIORITY: pilot-critical (HERO is fired) -> when a BUILD session happens this OUTRANKS owed E / R2 as the
  highest-value build follow-on. But NOT on the recruitment critical path — it only bites at first NON-LOOP
  brand connect. Recruitment still gates everything. (This SUPERSEDES the NEXT ACTION "E or R2 highest-value"
  line below.)

## OPEN — founder's check (does not block anything; fix already shipped either way)
- Supabase Data API / PostgREST toggle (Settings -> API). If ON: the historical anon/auth grants
  were a LIVE REST breach until this session. If OFF: latent. Record which, for the file. Identical
  fix either way — already committed.

## NEXT ACTION — RECRUITMENT, not build (founder's call; stated as recommendation)
Security debt is parked at a clean line. Nothing hardened this week matters until real brand data
connects. The binding constraint (pilot_scope §8) is unchanged: Aman cold, zero committed design
partners; recruiting 4–5 brands is slower than any build step and gates the whole timeline. The
next session should open on recruitment — not the next code item. If the founder instead wants a
build item, owed E (canonical-corrections) or R2 (reproducibility gap) are the highest-value
technical follow-ons, but neither is on the launch critical path; recruitment is.

## METHOD / CADENCE (non-negotiable)
- LEAD every phase with READ-ONLY discovery before any write. Writes gated, fail-closed,
  reversible, staged by explicit path, paste-before-commit, NO push from Claude Code.
- Continuity pair authored in chat (downloadable), critiqued x3, Claude-Code-verified, committed by
  explicit path, no push. Re-upload-to-Project RETIRED — paste-on-request instead.
- save_protocol.md governs every save (Phase 0 decision ledger -> Phase A -> Phase B).
