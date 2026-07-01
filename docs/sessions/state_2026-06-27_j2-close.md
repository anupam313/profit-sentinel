## SESSION OPEN — LOAD FIRST (do this before any work)
- THIS PAIR'S SELF-HANDLES: state_2026-06-27_j2-close.md = 87 lines;
  chat_context_2026-06-27_j2-close.md = 60 lines. If either
  file's real wc -l differs from these, a stale/truncated copy is mounted: STOP and ask for the live copy.
- Load docs/save_protocol.md FIRST (governs every save; handle 149 — re-verify at HEAD).
- Re-verify the 9 canonical handles AGAINST HEAD. THREE changed this session (J-2 doc-sync):
    product_strategy 1424 · technical_architecture 3999 · agent_d_build_spec 2722 ·
    cross_alert_orchestration 847 · d1_validation_gates 399 · pre_agent_build_checklist 389 ·
    save_protocol 149 · pilot_scope 122 · CLAUDE.md 271.
  (technical_architecture edited +12; pilot_scope and pre_agent_build_checklist were edited too, but
  via in-line appends so their line counts are UNCHANGED — 122 and 389 are correct, not stale. The
  scoped diff confirmed both regions changed. The other six carried unchanged — flag any drift.)
- MOUNT IS UNTRUSTED (Project content-cache bug serves stale copies). HEAD is the only source of truth.
  When a canonical doc is needed, ASK the founder to paste the live copy. Canonical files live under
  docs/ (CLAUDE.md at repo root); continuity pairs under docs/sessions/.
- Repo state: at open expect HEAD = the J-2 doc-sync commit (Track A; hash assigned at commit, sits on
  top of bd46884), origin/master = same, 0 ahead — IF the J-2 code commit (bd46884) AND this doc-sync
  commit were both pushed. VERIFY LIVE: `git log --oneline -4`
  and `git rev-list --count origin/master..HEAD`. NOTE: bd46884 (J-2 code) was UNPUSHED at this pair's
  authoring (1 ahead); if the founder batched it with the doc-sync push, expect both on origin at open.
  If the count is >0, reconcile before any new work — never start the sweep with continuity unpushed.

## DONE THIS SESSION — J-2 shipped (bd46884) + doc-synced (Track A)
J-2 = HERO native-ready reason plumbing + the J-3 RULE-3 leak fix. Code committed bd46884 (3 files:
new stg_loop_return_line_items; mart_return_rate_by_sku rewrite; staging tests). This session then
doc-synced it (Track A): technical_architecture.md (added the reason-derivation note; retired the stale
"(to be created)" mart stub), pilot_scope.md §4 (HERO native-primary / inert-until-J-1 addendum),
pre_agent_build_checklist.md (D-GAP6-11 annotated — the Agent-D consumer of J-2's plumbing).
Behavior-preserving on synthetic PROVEN (125 rows, sha256 0316b4f7…, identical before/after). GATE 1
confirmed sku_cost_master has 0 real rows, so the costs var-form→per-client change is output-identical.

### What J-2 actually changed
- NEW stg_loop_return_line_items: RULE-3 per-client synthetic filter applied at the staging boundary;
  provenance is TRANSITIVE via the parent loop_returns.order_id (the line-item table carries NO
  order_id, NO numeric id, NO stored is_synthetic). Regex band (`~ '^[0-9]+$' AND length < 13`),
  fail-closed on orphans (COALESCE(is_synthetic, false) => an orphan is treated REAL, never leaked as
  synthetic) + a not_null test on return_id as the loud tripwire. stg_loop_returns NOT modified
  (it is shared with the C1 sizing-complaint path).
- mart_return_rate_by_sku: the returned CTE reads the filtered staging model (no raw Loop read remains);
  the costs CTE moved var-form → per-client client_config form; an INERT native-primary COALESCE
  scaffold (`where false`) was added with NO guessed handle shape.
- C1 (Gorgias-tag sizing path) confirmed untouched — separate from HERO's Loop reason path.

## CARRY-FORWARD / OWED (do not lose)
- J-1 NATIVE-HANDLE SLOT (connect-day task): fill the inert native_reason CTE in
  mart_return_rate_by_sku — unnest refund_line_items → sku, extract the return→…→>'handle' reason,
  map to canonical handles, filter via staging. Nesting/casing is OWED: shopify_order_refunds.return
  is 100% NULL pre-pilot; do NOT assert casing from memory — confirm against real data or the Airbyte
  Shopify stream catalog at first connect.
- REGEX-BAND ASSUMPTION (known boundary): synthetic Loop order_ids are 7-digit; the provenance guard
  is `~ '^[0-9]+$' AND length < 13`. A future seed that widens the id range would silently widen the
  guard. Revisit the band if seed id ranges ever change.
- INNER-JOIN UNDERCOUNT (J-1 review candidate; PRE-EXISTING, not J-2-introduced): the mart's returned
  CTE inner-joins stg_loop_returns — a filtered or absent header silently drops that return from the
  rate. Zero rows today (0 orphans; both sides fully present on synthetic). Recorded continuity-only
  per founder call; review at J-1 alongside the native-handle wiring.
- J-3-STYLE AUDIT (standing sweep item): C6, G1, C2 each get the same raw-read / var-form-toggle check
  J-2 ran on HERO. CLAUDE.md RULE 3 already flags meta/ga4/sentry staging as still var-form +
  "PENDING reconciliation" — the var-form leak is a PATTERN, so J-3 is closed for HERO ONLY, not
  globally. Fold this check into each remaining sweep alert.
- HONEST BOUNDARY: all J-2 correctness was proven on synthetic-toggle-ON data only. The native leg,
  the regex band, and the orphan fail-closed path are verified by inspection / inert behavior, never
  by real data. J-1 (first live connect) is their first live test.
- CARRIED FROM owed-i-close (verify none dropped): the FULL owed set in
  state_2026-06-27_owed-i-close.md remains carried and was NOT re-reconciled this pair —
  the deeper owed-chain reconciliation back to state_2026-06-25_durable-rls-bc.md; seed_meta own-arc
  (live psql Meta-types precondition); RLS-probe keep/delete; suppression_log co-located REVOKE;
  full-public-history secret scan; owed D/E/F/G; R2 five foundational public-table DDLs
  (client_config, alert_log, thread_context, config_change_log, brand_event_calendar); N1–N5; ADD-1/2.
  Diff THIS pair against state_2026-06-27_owed-i-close.md across all its owed-bearing sections before
  the next continuity commit.

## NEXT ACTION — the FIRED-alert sweep continues
J-2 (HERO / owed-J) is closed and doc-synced. Remaining sweep, same plug-and-play read-only-discovery
treatment C1 and HERO got, to catch invented-column / schema / DQ surprises before a real connect:
- C6 (high-return new collection), G1 (stockout during active spend), C2 (influencer ROI — found
  UNBUILT/proxy in earlier discovery).
Fold the J-3-style audit (raw-read / var-form check) into each. Recruitment remains the TRUE launch
gate (pilot_scope §8) — product-readiness has been the founder's consistent priority.

## METHOD / CADENCE (non-negotiable)
- READ-ONLY discovery before every write. Writes gated, fail-closed, reversible, staged by EXPLICIT
  path (never git add -A/.), paste-before-commit, NO push from Claude Code (founder runs all pushes).
- Continuity pair authored in chat (downloadable), critiqued x3, Claude-Code-VERIFIED (handles +
  scoped diffs only — Claude Code never authors continuity files and never "updates project memory").
- save_protocol.md governs every save. Mount untrusted → reason from HEAD / pasted live files.
- One item at a time with founder sign-off. Position changes named (a) new fact / (b) under-tested prior.
