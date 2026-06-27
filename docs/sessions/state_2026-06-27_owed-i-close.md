## SESSION OPEN — LOAD FIRST (do this before any work)
- THIS PAIR'S SELF-HANDLES: state_2026-06-27_owed-i-close.md = 190 lines;
  chat_context_2026-06-27_owed-i-close.md = 61 lines. If either file's real wc -l differs
  from these, a stale/truncated copy is mounted: STOP and ask for the live copy.
- Load docs/save_protocol.md FIRST (governs every save; handle 149 — re-verify at HEAD).

- ##### PRIOR FRAGILE FLAG — NOW DISCHARGED (read once, then it's retired) #####
  Last session's #1 risk — Unit B's DQ-gate fix living ONLY in an UNTRACKED historical_pattern_scan.py —
  is RESOLVED. The file was first-added in commit c180401 and pushed to origin/master. No fragile
  untracked fix remains. The survival tripwire (tokens staging_schema / stg_staging_absent /
  dq_check_failed) is retired — the fix is durable in git history. Nothing to recover this session.

- Re-verify the 9 canonical line-count handles AGAINST REPO HEAD before any design/edit work:
    product_strategy 1424 · technical_architecture 3987 · agent_d_build_spec 2722 ·
    cross_alert_orchestration 847 · d1_validation_gates 399 · pre_agent_build_checklist 389 ·
    save_protocol 149 · pilot_scope 122 · CLAUDE.md 271.
  NONE were edited this session (only CODE + CONTINUITY files changed). Carried, not re-counted —
  treat as re-verify-at-HEAD; flag any drift.

- Repo state: the owed-I coherent push LANDED. The prior session pushed the 22-commit set to
  origin/master @ 489d29a (7d5c2e7..489d29a, clean fast-forward). THIS session added two commits:
    b2e3688 — track connectors/seed_google_ads.py (canonical RUN PATH seed; reproducibility gap closed)
    <CLOSE>  — this continuity pair (state + chat_context)
  Both pushed together at close -> expect origin/master = <CLOSE>, 0 ahead. VERIFY LIVE at open:
  `git log --oneline -3` and `git rev-list --count origin/master..HEAD` (expect 0). If >0, the
  close-pair push did not happen — reconcile before any work.

- MOUNT IS UNTRUSTED (Project content-cache bug serves stale copies). HEAD is the only source of truth.
  Founder will NOT rename files. When a canonical doc is needed, ASK the founder to paste the live copy.
  Canonical files live under docs/ (CLAUDE.md at repo root); continuity pairs under docs/sessions/.

## DONE THIS SESSION — owed-I DISCHARGED (the coherent push + the lockdown) + seed_google_ads tracked
owed-I's job: protect the accumulated LOCAL work and get it onto the remote as ONE coherent set, after
the C1 signal-rewire arc closed earlier the same day. Done. The owed-I COHERENT push = the 22-commit set
(20 prior-session backlog + Commit 1 + Commit 2), pushed at 489d29a. seed_google_ads (b2e3688) + this
close pair are a SECOND, smaller push at session close — NOT part of the owed-I coherent set. The fragile
Unit B fix is now durable in git; the continuity chain is reconciled.

### The push (the core owed-I act)
- Reconciled the stack LIVE: confirmed 20 ahead of origin/master (NOT 21 — the continuity pair was
  uncommitted at owed-I open). HEAD was 7293420 (Unit A) at open.
- Repo confirmed PUBLIC (github.com/anupam313/profit-sentinel) -> ran a pre-push secret scan over the
  actual commit CONTENT (`git log -p origin/master..HEAD`), not just working files: Tier-A CLEAN (no
  connection string / JWT / key / inline credential). 20-commit coherence CLEAN (the lone "WIP
  checkpoint" 8292b02 is the intentional, founder-ruled split of pre-existing mart work).
- Founder pushed the 22-commit coherent set (20 backlog + Commit 1 + Commit 2): 7d5c2e7..489d29a, clean
  fast-forward. owed-I push DISCHARGED.

### Commit 1 — c180401 — historical_pattern_scan.py first-add (Unit B lockdown)
- First-add of the whole ~2,086-line Onboarding-Step-11 historical pattern scan (previously UNTRACKED).
  Carries Unit B: the 6 stg_ DQ-prechecks now read {client_schema}_staging (was the suffix-less base
  schema); fail-closed skip_map["C1"]='stg_staging_absent'/'dq_check_failed' so C1 suppresses rather
  than fires unguarded when its DQ gate cannot run. Tokens verified in the committed blob. The prior
  session's #1 FRAGILE risk is DISCHARGED.
- HONEST BOUNDARY (carry): the fail-closed branches AND the A+B end-to-end fire/suppress integration were
  verified read-only ONLY; the first controlled scan run on azure synthetic is still their live test.

### Commit 2 — 489d29a — continuity reconciliation
- Added the 2026-06-27 c1-rewire-close pair (first-add, committed VERBATIM as that session's snapshot).
  Recorded the 2026-06-26 post-close addendum (+57/-2: seeding-completeness + fidelity audits + new owed
  J). 2026-06-26 self-handles reconciled to reality (202/74 — no owed-E drift).
- SNAPSHOT-INTEGRITY RULING (architectural, mine): the 2026-06-27 state file's line-76 "(UNTRACKED)" for
  historical_pattern_scan.py was LEFT AS-IS — a faithful point-in-time record. The forward status
  (tracked in c180401) is recorded HERE, not back-dated into the prior snapshot. Dated pairs are
  immutable session snapshots; later events go in later pairs.

### seed_google_ads.py tracked — b2e3688 — reproducibility gap CLOSED
- First-add of the previously-untracked canonical Google Ads seed. NOT scratch: referenced in the RUN
  PATH (CLAUDE.md:225), technical_architecture.md:1338 (API v24.1, cost_micros bigint), and
  pre_agent_build_checklist B-7. A fresh clone can now run the full seed sequence. Tracked as-is, NO
  behavioral change. cost_micros (bigint) store unchanged; the B-9 mart conversion
  google_spend = cost_micros/1e6 in mart_causal_chain_daily is unaffected. Encodes the G_SHOP_001 14-day
  zero-spend window for G1 chain testing.

## DECISIONS LOCKED THIS SESSION (Phase-0 ledger)
1. seed_meta.py = SAFE-to-build + DOC-DRIFT, NOT build-breaking. Static (read-only) chain: staging casts
   spend::numeric and parses purchase_roas->0->>'value' (matches the seed's emitted jsonb shape); the 6
   columns staging reads that the seed does not populate are defined in the table DDL home
   _run_meta_gorgias_tiktok.py (resolve to NULL, handled). python_transformer has NO Meta logic — casts
   live in dbt staging (RULE 4 documented interim). DOC-DRIFT: tech_arch documents Meta as numeric;
   reality is text+jsonb-with-casts. ROUTED to seed_meta's OWN ARC (NOT committed). PRECONDITION for
   that arc: a LIVE psql confirm of meta_ad_performance column types (this env had no psql/DATABASE_URL,
   so the verdict rests on static staging+DDL evidence). Feeds Alerts 1 & 2 (true post-return ROAS;
   ROAS-drop root cause) -> pilot-critical, hence its own arc rather than a loose commit.
2. onboarding_flow.py = additive (Q1b blended gross margin %), ROUTED to the onboarding stream
   (CD-10/N1). blended_gross_margin_pct is already READ by mart_causal_chain_daily (committed 8292b02)
   with 51/51 tests green -> the public.client_config column is effectively present. NOT committed.
3. Group B disposal (owed-I) = both routed (1 + 2); NEITHER rides any push as-is.
4. seed_google_ads PULLED from owed-I scope (position change (b): owed-I's literal definition never
   included it — it was carried as a recommended commit without checking scope). Then tracked as its OWN
   item once read-only discovery CONFIRMED it canonical (b2e3688).
5. Scratch set (13 _*.py incl. the 3 RLS probes + seed_b4_patch.py) = LEAVE UNTRACKED. Read-only
   verified: none imported by tracked code; none a canonical RUN-PATH/spec step (every doc hit is a
   docs/sessions/* continuity log). NEVER add a `_*.py` gitignore rule — it would SHADOW 15 TRACKED
   _*.py files incl. _harden_public_schema.py (RUN PATH 1b hardener) and the _run_* connector runners.
   Disposition = explicit-path discipline (Option C), not a glob ignore.
6. line-76 snapshot ruling (architectural, mine): leave prior snapshots immutable; forward status in the
   new pair (see Commit 2).

## POSITION CHANGES NAMED
- (b) 2026-06-26 "CRLF-only" claim DE-ESCALATED: round-2 discovery proved the edits were a real
  POST-CLOSE ADDENDUM whose content was already carried forward into the 2026-06-27 pair -> a
  git-hygiene lag, not a continuity-integrity hole.
- (a) NEW FACT — repo is PUBLIC (round 2): extended the secret scan from working-tree files to the actual
  commit CONTENT being pushed (a public push exposes commit diffs, not just filenames).
- (b) seed_google_ads PULLED from owed-I (decision 4) — under-tested prior; owed-I's literal scope
  excluded it.

## ROUTED FORWARD / CARRIED OWED
> NEXT SESSION: diff this ENTIRE owed set against state_2026-06-27_c1-rewire-close.md across ALL its
> owed-bearing sections (CARRIED OWED + ROUTED FORWARD + POST-CLOSE ADDENDUM) before committing the next
> pair — the completeness-verify prompt does this against HEAD.
> UNDISCHARGED DEEPER RECONCILIATION (carry until done): the owed chain was never reconciled line-by-line
> all the way back to state_2026-06-25_durable-rls-bc.md, so an item dropped before 2026-06-26 could still
> be invisible. A session with repo access should reconcile the FULL chain back to 2026-06-25. This is the
> likeliest structural source of recurring missed items — and it nearly bit THIS pair: the first draft
> dropped this very note and re-compressed owed G; the 3-pass critique caught both.
> owed-I is DISCHARGED except two non-blocking remnants (RLS-probe keep/delete; suppression_log REVOKE).
- Group B own-arc + onboarding stream (decisions 1, 2). seed_meta PRECONDITION: live psql Meta-types.
- RLS-probe keep/delete (3 scripts) — founder pending; never enter a commit. (owed-I remnant, non-blocking.)
- suppression_log co-located REVOKE -> _harden_public_schema.py — COSMETIC, someday. (owed-I remnant.)
- 3 older session pairs (op1-close, prepilot-hardening, buildstate_c8) untracked — durability backfill;
  content already carried via the continuity chain. Leave; sweep someday.
- FULL-PUBLIC-HISTORY secret scan — NEW someday item: this session scanned only origin/master..HEAD; the
  pre-origin public history was never scanned. If a secret ever landed there it is already exposed -> a
  one-time full-history scan + rotate-if-found pass.
- Carried from c1-rewire-close (verify none dropped):
- D. Per-client client_id RLS POLICY on public tables — needs JWT/GUC session context (does not exist)
     -> post-pilot, codebase-wide security debt. (RLS currently deny-all / no-policy.)
- E. DOC-SYNC (RULE 9) canonical-corrections pass — sub-items (full text: c1-rewire-close owed E):
     suppression_log DDL; RULE 3 is_synthetic; the "Agent A only" writer comment (true set = Agent A +
     tiktok/sentry/loop seeds); R10/R11/DEBT-004 ID drift; seed_tiktok RLS note; pg_default_acl
     constraint; R1 supabase_admin residual; public RLS posture + RUN PATH 1b; the 9 R9 corrected facts;
     D-A..D-F landings. AUGMENTED prior: + N3 (a-d).
- F. WATCH WINDOW (operational): (a) next Agent A suppression write + next seed run exercise the live
     public-table write path under the new RLS/REVOKE — monitor for permission-denied / RLS-denial;
     (b) the RUN PATH 1b manual-step footgun (a rebuild running seeds but SKIPPING 1b yields an
     unhardened schema); (c) Unit B's fail-closed branches are inspection-only — the first scan run that
     hits a genuinely-absent stg_ table is their live test.
- G. validate_sync.py — BUILD AT FIRST LIVE AIRBYTE CONNECTION (pilot onboarding), NOT pre-pilot.
     DEBT-004 spec (carried VERBATIM — DO NOT re-compress):
       - Scope: Airbyte-synced sources only (Shopify, Klaviyo, Gorgias, Loop, TikTok). Meta / GA4 /
         Sentry / Google Ads = manual seeds, OUT of sync scope.
       - OPEN mechanism (resolve at first connection): source-API count query vs Airbyte native
         job-stats as ground-truth — decides sync_validation_log shape.
       - Failure action: route through the existing run_dq_prechecks skip_map / suppression path,
         NOT a parallel mechanism.
       - Write target: public.sync_validation_log (NEW) — inherits the hardened public-table RLS +
         REVOKE pattern (via _harden_public_schema.py's explicit table list — ADD it there when the
         table is created).
       - Pattern: mirror validate_seed() (SAVEPOINT-per-check, 120s timeout, retry-once,
         CRITICAL/ADVISORY result structure; RULE 5/6).
       - Threshold >1% variance = fail (original DEBT-004) — revisit vs brand-derived bands.
- J. HERO reason-source rewire (Shopify-native primary, Loop supplement; parser targets the stable
     returnReasonDefinition.HANDLE — native returnReason enum DEPRECATED 2026-01). FIRED pilot alert;
     read-only discovery prompt ready. Part of the NEXT-ACTION alert sweep.
- R2. REPRODUCIBILITY — seed_google_ads NOW TRACKED (b2e3688) closes the seed half; the 5 foundational
     public tables with NO repo CREATE site REMAIN: client_config, alert_log, thread_context,
     config_change_log, brand_event_calendar (doc-only / dashboard-born; durability LIVE-DB-ONLY until
     real DDLs are captured). client_config especially is read by ~everything. Its own deliberate pass.
- PostgREST. Founder-check (carried; does NOT block — fix shipped either way): Supabase Data API /
     PostgREST toggle (Settings -> API). If ON, the historical anon/auth grants were a LIVE REST breach
     until owed-H; if OFF, latent. Record which, for the file.
- N1. CD-10 per-client C1 threshold calibration -> onboarding stream; manual p90 interim at first
     connect. (Carried.)
- N2. azure_co / client_azure_co namespace split — synthetic-only seed-normalization. (Carried.)
- N3. DOC-SYNC additions (a-d) -> folded into owed E. (Carried.)
- N4. chain-registry static 30% -> chain-registry / historical-scan scope. (Carried.)
- N5. STALE ORPHAN SCHEMAS cleanup (doubled-config + dev-target dupes). (Carried.)
- ADD-1 (GA4 secondary tables empty — S3-P1/P2), ADD-2 (fidelity connect-notes: Google Ads per-stream
  split; Meta static-snapshot, no 28-day restatement). Carried.

## NEXT ACTION — the remaining FIRED-alert plug-and-play sweep
The owed-I protect-the-work arc is done. Per the c1-rewire NEXT ACTION, the next product-readiness work
is the same plug-and-play sweep C1 got, on the remaining FIRED pilot alerts — to catch invented-column /
schema / DQ surprises before a real connect:
- HERO (owed J — reason-source rewire: Shopify-native primary, Loop supplement; discovery prompt ready)
- C6 (high-return new collection), G1 (stockout during spend — its seed_google_ads is now tracked),
  C2 (influencer ROI — found UNBUILT/proxy in earlier discovery).
This is where the next real surprises hide. Lower-stakes after: N2 namespace, N3/owed-E doc-sync, N5
orphans. Recruitment remains the TRUE launch gate (pilot_scope §8) — product-readiness has been the
founder's consistent priority.

## METHOD / CADENCE (non-negotiable)
- READ-ONLY discovery before every write. Writes gated, fail-closed, reversible, staged by EXPLICIT path
  (never git add -A/.), paste-before-commit, NO push from Claude Code (founder pushes).
- Continuity pair authored in chat (downloadable), critiqued x3, Claude-Code-VERIFIED (handles only —
  CC never authors continuity files and never "updates project memory"), committed by explicit path.
- save_protocol.md governs every save. Mount untrusted -> reason from HEAD / pasted live files.
- One item at a time with founder sign-off. Position changes named (a) new fact / (b) under-tested prior.
