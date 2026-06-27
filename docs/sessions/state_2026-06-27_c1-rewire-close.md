## SESSION OPEN — LOAD FIRST (do this before any work)
- THIS PAIR'S SELF-HANDLES: state_2026-06-27_c1-rewire-close.md = 246 lines;
  chat_context_2026-06-27_c1-rewire-close.md = 72 lines. If either file's real wc -l differs
  from these, a stale/truncated copy is mounted: STOP and ask for the live copy.
- Load docs/save_protocol.md FIRST (governs every save; handle 149 — re-verify at HEAD).

- ##### FRAGILE — READ THIS BEFORE ANYTHING ELSE #####
  Unit B's gate fix lives ONLY on-disk in the UNTRACKED file `historical_pattern_scan.py`. It is NOT
  committed. If the working tree is reset/cleaned before the owed-I push, the ENTIRE Unit B fix is
  LOST while Unit A (committed 7293420) survives. Do NOT `git clean`, `git checkout .`, `git reset
  --hard`, or `git stash drop` without first preserving this file.
  CONFIRM THE FIX SURVIVED — grep the untracked file for these UNIQUE TOKENS (spacing-independent, so
  no false alarm from a `=` vs `= ` difference):
    `staging_schema`        — Unit B schema repoint (the new variable; expect ~3+ hits incl. the 2 defs)
    `stg_staging_absent`    — fail-closed literal, TABLE_ABSENT branch
    `dq_check_failed`       — fail-closed literal, CHECK_FAILED branch
  Absence of any = the untracked edits were lost — recover before any further work.
  Locking this down (bring the file into git via the owed-I reconciliation) is the #1 NEXT ACTION.

- Re-verify the 9 canonical line-count handles AGAINST REPO HEAD before any design/edit work:
    product_strategy 1424 · technical_architecture 3987 · agent_d_build_spec 2722 ·
    cross_alert_orchestration 847 · d1_validation_gates 399 · pre_agent_build_checklist 389 ·
    save_protocol 149 · pilot_scope 122 · CLAUDE.md 271.
  NONE of the 9 were edited this session (only CODE files changed — see DONE), so all 9 should match
  the prior pair UNCHANGED. They were CARRIED, not re-counted this session — treat as
  re-verify-at-HEAD, not confirmed. Any drift = flag (the verify prompt re-counts all 9 at HEAD).

- Repo state: HEAD = 7293420 on master ("C1 rewire: source Gorgias sizing signal from real tags, not
  invented scalar"). Parent = a6f3828. Unit A commit = 3 files, +49/-25:
  warehouse/models/sources/all_sources.yml, warehouse/models/staging/stg_gorgias_tickets.sql,
  warehouse/models/marts/mart_causal_chain_daily.sql. VERIFY at open: `git log --oneline -1` (expect
  7293420). Push stack: ~20 ahead of origin/master (prior ~18-19 + Unit A) — TREAT THE COUNT AS THE
  NUMBER MOST LIKELY TO DRIFT; reconcile against `git log --oneline -25` before trusting it. Push as
  ONE coherent set later, never piecemeal — DEFERRED (owed I).

- Working tree:
  - ##### historical_pattern_scan.py — UNTRACKED, carries Unit B's edits (the FRAGILE fix above).
  - Undisposed Group B (UNCHANGED this session): seed_meta.py (M), onboarding_flow.py (M).
  - CRLF-only artifacts (content unchanged, committed in a6f3828): the prior pair under docs/sessions/
    (state_2026-06-26_owed-h-close.md (M), chat_context_2026-06-26_owed-h-close.md (M)).
  - Other untracked (carried): connectors/seed_google_ads.py, seed_b4_patch.py, _check_db_state.py,
    _dryrun_determinism.py, slack_bot/, the 3 RLS probe scripts (_rls_grant_discovery.py,
    _rls_grant_harden_live.py, _harden_precondition_probe.py), docs/sessions/*.
  - OPTION C DISCIPLINE: stage by EXPLICIT path only; never `git add -A/.`; no Group B, no probe, and
    no untracked file enters a commit EXCEPT via the deliberate owed-I reconciliation.

- MOUNT IS UNTRUSTED (Project content-cache bug serves stale copies). HEAD is the only source of
  truth. The founder will NOT rename files. When a canonical doc is needed, ASK the founder to paste
  the live copy and reason from that. Verify the 9 handles vs HEAD at open.
- Canonical files live under docs/ (CLAUDE.md at repo root); continuity pairs under docs/sessions/.

## DONE THIS SESSION — C1 SIGNAL REWIRE ARC: Units A + B (signal + gate). Arc CLOSED at A+B; Unit B's COMMIT is OWED (untracked, routed owed-I).
The arc's job: kill the hidden surprises that would make pilot alert C1 (sizing-complaint velocity)
fire wrong at a real client connect. C1 was reading an INVENTED synthetic scalar; its DQ gate was
reading a STALE EMPTY schema. Both fixed. The threshold (Unit C) resolved to a separate, now-unblocked
onboarding item (CD-10) — routed, not built (see DECISIONS).

### Unit A — C1 signal rewire — DONE + COMMITTED (7293420)
- Repointed C1's sizing signal from the synthetic-only `gorgias_tickets.last_ticket_reason='sizing_issue'`
  scalar (ABSENT in the live Gorgias API) to the real `gorgias_ticket_tags` data.
- 3 dbt edits: (1) all_sources.yml — declared `gorgias_ticket_tags` as a dbt source (chosen over a
  var-qualified raw ref, to honour the project's source-registry idiom — also serves Unit B); (2)
  stg_gorgias_tickets.sql — added a 1:ticket `tags` jsonb column (array of {name}) via a `tags_agg` CTE
  + 1:1 LEFT JOIN (NO grain fan-out); (3) mart_causal_chain_daily.sql — `sizing_daily` numerator →
  BOOLEAN-PER-TICKET EXISTS over the tags array against the 12-value sizing-only set.
- VERIFIED: dbt build 15 PASS / 12 tests green; new sizing count 3,368 is a STRICT SUPERSET of the old
  3,343 (+25 new-only, 0 old-only — repoint demonstrably took, not a silent no-op); no fan-out (staging
  10,296 distinct; mart 730->730). The "~3,940" verify-gate number was a Claude OCCURRENCE-SUM
  mis-estimate; the correct one-per-ticket distinct count is 3,368 (cross-checked vs raw
  gorgias_ticket_tags). KEEP, committed. LESSON: semantic gates assert STRUCTURAL INVARIANTS
  (new>=old, !=old, !=0, matches raw count), never a hand-derived magic number.
- `last_ticket_reason` REMAINS in stg_gorgias_tickets (passthrough; no longer read by C1) — routed
  cleanup, deliberately NOT removed this session.

### Unit B — DQ-gate staging_schema repoint + fail-closed — DONE ON-DISK, NOT COMMITTED (routed owed-I)
- historical_pattern_scan.py (UNTRACKED): added `staging_schema = f"{client_schema}_staging"` at :872
  and :1912; repointed the 6 stg_ DQ-precheck refs across 5 SITES (Gorgias :879/:891; Meta :916+:917
  guards / :927+:932 reads [TWO tables]; TikTok :961/:969; Klaviyo :1024/:1029; pending-connectors
  :1914-1915 dynamic `stg_{connector}`) from the suffix-less base `client_schema` to `staging_schema`.
  (Line numbers are PRE-EDIT/approximate — the two staging_schema insertions shift everything below by
  ~1-2; grep the tokens in SESSION OPEN to locate, do not trust the exact line.)
- Raw-source + app refs UNCHANGED on client_schema/public (confirmed stg_-free): Loop :1001, GA4 :1066,
  Sentry :1095, dq_metric_scores :1130, causal_pattern_validation, client_config.
- FAIL-CLOSED (decision 1a) applied to GORGIAS/C1 ONLY — the sole alert gate (it alone sets skip_map):
  added `skip_map["C1"]="stg_staging_absent"` (TABLE_ABSENT branch) + `skip_map["C1"]="dq_check_failed"`
  (CHECK_FAILED branch). Meta/TikTok/Klaviyo set NO skip_map in their normal paths (caveat/monitoring/
  note-only) -> schema-repoint ONLY, no fail-closed (adding it would be an INVENTED mapping).
- VERIFIED read-only (NO scan run — it writes dq_metric_scores + causal_pattern_validation): py_compile
  PASS; the gate's coverage query now returns tag_rate=1.000 on client_azure_co_staging (closed 825,
  tagged 825 -> C1 ALLOWED) vs 0.000 on the old base target; no double-suffix
  (client_id='client_azure_co' -> 'client_azure_co_staging').
- VERIFY-AT-FIRST-RUN (honest boundary): the fail-closed branches AND the A+B end-to-end fire/suppress
  integration were NOT runtime-tested (the scan writes app tables -> no integrated run done). A+B are
  verified at UNIT level read-only only. The first controlled scan run on azure synthetic is the
  integration check: expect C1 to fire on high-velocity dates and the gate to ALLOW at tag_rate=1.0;
  the absent-table fail-closed path executes only when a stg_ table is genuinely missing.
- WHY uncommitted: the file is untracked; a first-add of the whole ~2,070-line file is routed to the
  owed-I coherent push, not a mid-arc piecemeal commit. The on-disk fix is LIVE for the pilot run.

## DECISIONS LOCKED THIS SESSION (Phase-0 ledger)
1. Sizing-tag bucketing = SIZING-ONLY, quality EXCLUDED. The 12 sizing tags: too small, too big,
   runs small, wrong size, fit, sizing, sizing_issue, sizing_issue_tops, runs small -- tops,
   fit issue -- tops, outerwear fit, layering issue. Quality tags (seam issue, pilling, fabric quality,
   not as described, defective, product_quality, wrong fabric weight) -> separate quality reason class
   (used by HERO/D1 per cross_alert:210, d1_gates:54/217), NOT C1. Confirmed NO cross-alert impact:
   nothing but C1 reads gorgias_ticket_tags (the only other "tags" reader is shopify_orders.tags = order
   tags, unrelated). This set is a FROZEN BETA DIAL (cross_alert O-31) — refine post-beta from logged
   data, not hand-tuned now. Home: embedded in the committed mart SQL; recorded here.
2. Decision 1(a) — FAIL-CLOSED on absent staging: when a stg_ table that should exist is absent (or the
   check errors), suppress the gated alert (set skip_map) rather than let it fire unguarded. Rationale:
   the pilot's trust proposition is "the alert is reliable"; an alert firing while its DQ gate silently
   failed is the worst failure mode. Client-facing DQ-transparency message = POST-PILOT (the human
   relevance gate catches it in the pilot). Home: implemented in Unit B (Gorgias/C1 only).
3. Decision 2(a) — Unit B commit ROUTED to owed-I: the on-disk fix lands now; the untracked file's
   first-add joins the one coherent push. Home: owed-I (+ the FRAGILE flag in SESSION OPEN).
4. Unit C / threshold = CD-10, ROUTED to onboarding stream (Decision A). "Recalibrate the number" was
   the WRONG frame. Facts (read-only verified): NO recalibrator exists (grep=0 in the scan; tech_arch's
   "recalibrated monthly" is aspirational/unbuilt for THIS threshold); the rewire caused NO regression
   (new tag-based velocity p90 = 43.08 ~= old 43.61, fires 10% on synthetic); azure's 43.61 is a manual
   placeholder that does NOT leak to real clients — a fresh client gets the 15.0 column DEFAULT, which
   OVER-fires (~30% vs the 15-25% target). The real item is CD-10 (pre_agent_build_checklist:142,
   PENDING): per-client threshold calibration computed from the client's OWN
   sizing_complaint_velocity_pct distribution, as a post-confirmation step in onboarding_flow.py. NOT
   built now — no real-client mart to calibrate against, no multi-client onboarding to host it
   (onboarding is azure-hardcoded). Routed to the onboarding-productionization stream.
   ##### PILOT-CONNECT FLAG: at the FIRST real pilot connect, C1's threshold MUST be manually calibrated
   (p90 of that client's own velocity distribution) — until CD-10 — or C1 over-fires at the 15.0
   default. No-Seed-compliant (derived from their data). Do NOT let a real client run on 15.0 or 43.61.
5. C1-SIGNAL ARC CLOSED at A+B: signal (A) + gate (B) are the complete signal fix; the surprises are
   dead. CD-10 is a known, planned, now-unblocked onboarding step, not a C1-signal bug. (Unit B's COMMIT
   remains owed — the arc's WORK is done; its git hygiene is routed.)

## ROUTED FORWARD — NEW this session (named so none is lost; NOT done; deliberate)
- N1. CD-10 — per-client C1 threshold calibration -> onboarding-productionization stream (decision 4).
      Already PENDING at pre_agent_build_checklist:142; this session ROUTES it + records the manual
      first-connect interim (decision 4 PILOT-CONNECT FLAG). Unblocked by Unit A (signal is now real).
- N2. azure_co / client_azure_co NAMESPACE SPLIT — 306 seeded app rows keyed on 'azure_co' (alert_log
      161 [+16 on client_azure_co = two writers colliding], suppression_log 29, brand_event_calendar
      116) vs the canonical 'client_azure_co' that client_config/dbt/scan use. SYNTHETIC-ONLY artifact;
      does NOT block C1 (C1's path is client_azure_co throughout; a real client's Airbyte data is keyed
      consistently). A read filtering seeded app data by 'client_azure_co' silently misses the
      'azure_co' rows. Route as a separate seed-normalization fix (normalize seed CLIENT_ID to
      'client_azure_co', or add an alias). NOT urgent (synthetic-only).
- N3. DOC-SYNC additions (fold into owed E / RULE 9): (a) tech_arch mart sizing logic changed — now
      tags-based boolean-per-ticket, NOT the last_ticket_reason scalar (the retired wording still lives
      in tech_arch); (b) NEW dbt source gorgias_ticket_tags in all_sources.yml; (c) tech_arch's
      dbt_project.yml shows staging `+schema: "{{ var('client_schema') }}"` but the LIVE file uses
      `+schema: staging` (the drift that produced the doubled client_azure_co_client_azure_co_marts
      schema — see N5); (d) the Python DQ gate now reads `_staging` for the 6 stg_ pre-checks (Unit B).
- N4. CHAIN-REGISTRY static 30% — the historical scan's RETROSPECTIVE C1 chain uses a hardcoded
      `sizing_complaint_rate_7d > 30%` (chain registry ~:720). It now reads the Unit-A-rewired rate
      (improved, not broken). The 30% is a chain-DEFINITION constant belonging to the historical-scan /
      chain-registry scope (D-12/D-17), NOT the C1 firing threshold. Note/route there.
- N5. STALE ORPHAN SCHEMAS — client_azure_co_client_azure_co_marts (doubled-config artifact),
      public_marts, dbt_anupam313_staging/_marts (dev-target dupes). Cleanup; route. (Evidence for N3c.)

## CARRIED OWED (from prior pair — VERIFY none dropped; augmented where noted)
> Diff this set against state_2026-06-26_owed-h-close.md across ALL its owed-bearing sections (CARRIED
> OWED + RESIDUALS + OPEN + POST-CLOSE ADDENDUM) before committing this pair (the verify prompt does this).
> B + C closed two sessions ago (8a57c4b); H closed in a6f3828.
> UNDISCHARGED DEEPER RECONCILIATION (carry until done): the 2026-06-26 pair flagged that ITS owed list was
> never diffed line-by-line against state_2026-06-25_durable-rls-bc.md's CARRIED OWED ("stage prompt does
> this" — UNCONFIRMED). That diff may still be UNDONE, so an item dropped before 2026-06-26 would still be
> invisible -> a session with repo access should reconcile the FULL owed chain back to 2026-06-25 to confirm
> nothing dropped earlier. (This is the likeliest structural source of recurring missed items.)
- D. Per-client client_id RLS POLICY on public tables — needs JWT/GUC session context (does not exist).
     -> post-pilot, codebase-wide security debt. (RLS currently deny-all / no-policy.)
- E. DOC-SYNC (RULE 9) canonical-corrections pass — carried sub-items a-h from prior (suppression_log
     DDL; RULE 3 is_synthetic; "Agent A only" comment [true writer set = Agent A + tiktok/sentry/loop
     seeds]; R10/R11/DEBT-004 ID drift; seed_tiktok RLS note; pg_default_acl constraint; R1 supabase_admin
     residual; public RLS posture + RUN PATH 1b) PLUS the 9 R9 corrected facts + D-A..D-F landings.
     AUGMENTED THIS SESSION: + N3 (a-d).
- F. WATCH WINDOW (operational): (a) next Agent A suppression write + next seed run exercise the live
     public-table write path under the new RLS/REVOKE — monitor for permission-denied / RLS-denial;
     (b) the RUN PATH 1b manual-step footgun (a rebuild running seeds but SKIPPING 1b yields an
     unhardened schema). AUGMENTED THIS SESSION: + Unit B's fail-closed branches are inspection-only —
     the first scan run that hits a genuinely-absent stg_ table is their live test (see VERIFY-AT-FIRST-RUN).
- G. validate_sync.py — BUILD AT FIRST LIVE AIRBYTE CONNECTION (pilot onboarding), NOT pre-pilot.
     Reconciled DEBT-004 spec (carried VERBATIM from prior state — DO NOT re-compress):
       - Scope: Airbyte-synced sources only (Shopify, Klaviyo, Gorgias, Loop, TikTok). Meta / GA4 /
         Sentry / Google Ads = manual seeds, OUT of sync scope.
       - OPEN mechanism (resolve at first connection): source-API count query vs Airbyte native
         job-stats as ground-truth — decides sync_validation_log shape.
       - Failure action: route through the existing run_dq_prechecks skip_map / suppression path,
         NOT a parallel mechanism.
       - Write target: public.sync_validation_log (NEW) — inherits the hardened public-table RLS +
         REVOKE pattern (now via _harden_public_schema.py's explicit 15-table list — ADD it there when
         the table is created).
       - Pattern: mirror validate_seed() (SAVEPOINT-per-check, 120s timeout, retry-once,
         CRITICAL/ADVISORY result structure; RULE 5/6).
       - Threshold >1% variance = fail (original DEBT-004) — revisit vs brand-derived bands.
- I. The ONE coherent push (stack ~20 deep — reconcile live, never piecemeal) + Group B disposal + the
     3 RLS probe scripts (keep-or-delete, founder pending; never enter a commit) + consolidate
     suppression_log's co-located REVOKE into _harden_public_schema.py someday (COSMETIC). AUGMENTED
     THIS SESSION: + Unit B's untracked historical_pattern_scan.py first-add (THE FRAGILE item — SESSION
     OPEN). Re-upload-to-Project RETIRED — paste-on-request.
- J. HERO reason-source rewire (Shopify-native primary, Loop supplement; parser targets the stable
     returnReasonDefinition.HANDLE since the native returnReason enum is DEPRECATED 2026-01). HERO is a
     FIRED pilot alert (pilot_scope §3) — pilot-critical build. Read-only discovery prompt was READY (not
     yet run) at prior close. Carried OPEN — part of the remaining-alerts sweep below.
- R2. REPRODUCIBILITY GAP (carried from prior RESIDUALS — do NOT drop) — 5 foundational public tables
     have NO repo CREATE site (doc-only / dashboard-born): client_config, alert_log, thread_context,
     config_change_log, brand_event_calendar. Their durability is LIVE-DB-ONLY, not rebuild-safe, until
     real DDLs are captured into the repo. Bigger than RLS; needs the TRUE live DDLs (not the stale doc
     blocks); its own deliberate pass. client_config especially is read by ~everything. (R1 — the
     supabase_admin default-ACL residual — is folded into owed E above.)
- PostgREST. OPEN founder-check (carried; does NOT block — fix shipped either way): Supabase Data API /
     PostgREST toggle (Settings -> API). If ON, the historical anon/auth grants were a LIVE REST breach
     until owed-H; if OFF, latent. Record which, for the file.

## CARRIED FROM PRIOR POST-CLOSE ADDENDUM (2026-06-26) — survive-forward threads (do NOT drop)
The prior addendum recorded these explicitly to survive into the next chat; carried here so they are not
lost (J above is the fourth thread from that addendum).
- ADD-1. GA4 SECONDARY TABLES EMPTY (known S3-P1/P2): pages / devices / conversions / DAU / events /
     traffic are unpopulated. This is why the prior seeding-completeness audit verdict was PARTIAL (data
     otherwise effectively complete — 10 connectors populated, provenance cleanly isolatable, 5 marts at
     full 730-day grain, 51/51 dbt tests PASS). Not a C1 item; carry until S3-P1/P2 close.
- ADD-2. FIDELITY connect-notes (first-real-connect considerations, NOT blockers — from the seed-vs-API
     fidelity audit; both seeds were otherwise FAITHFUL on join-critical shape):
     (a) Google Ads — the seed is ONE blended table vs Airbyte's per-stream split
         (shopping_performance_view separate); staging may need per-stream awareness at real connect.
     (b) Meta — the synthetic is a STATIC snapshot with NO 28-day rolling restatement; handle at the
         connector's incremental config at connect, not now.

## NEXT ACTION — owed-I lockdown first, then the remaining-alerts plug-and-play sweep
The C1 arc is closed at a clean line. Recommended order (founder's call):
1. owed-I — LOCK DOWN THE WORK FIRST. Unit B's fix is live but ONLY on-disk in an untracked file;
   reconcile the ~20-commit stack and bring historical_pattern_scan.py into git, then the one coherent
   push. Highest loss-risk; protect it before anything else.
2. Remaining FIRED pilot alerts — same plug-and-play sweep C1 just got, to catch invented-column /
   schema / DQ surprises before real connect: HERO (owed J — reason-source rewire, discovery prompt
   ready), C6 (high-return new collection), G1 (stockout during spend), C2 (influencer ROI — found
   UNBUILT/proxy in earlier discovery). This is where the next real surprises hide.
3. Lower-stakes cleanup: N2 (namespace split), N3/owed-E (doc-sync), N5 (orphan schemas).
Recruitment remains the true launch constraint (pilot_scope §8) — the founder has consistently chosen
product-readiness first; these are the product-readiness items.

## METHOD / CADENCE (non-negotiable)
- LEAD every phase with READ-ONLY discovery before any write. Writes gated, fail-closed, reversible,
  staged by explicit path, paste-before-commit, NO push from Claude Code.
- Continuity pair authored in chat (downloadable), critiqued x3, Claude-Code-verified, committed by
  explicit path, no push. Re-upload-to-Project RETIRED — paste-on-request.
- save_protocol.md governs every save (Phase 0 decision ledger -> Phase A -> Phase B).
- Claude Code reaches for "update project memory" / wants to author continuity files — DISREGARD; CC
  VERIFIES, it does not author. Position changes named as (a) new fact or (b) under-tested prior (the
  3,940->3,368 and "only mart drifted"->"verdict C" reversals were both (b)).
