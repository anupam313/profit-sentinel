# STATE — DB Verification & Reproducibility (snapshot)
**As of:** 2026-07-27 · **Repo HEAD:** `f191fa7` (origin/master, in sync)
**Companion:** `chat_context_2026-07-27_dbverify-reproducibility.md` (the narrative).
State = where things stand. Context = how we got here.
**Note:** this is the THIRD session pair dated 2026-07-27. The other two are
`_outreach` and `_pilot_readiness`. This one follows `_pilot_readiness` (HEAD was `0a4031c`).

---

## REPO STATUS
- Branch `master` == `origin/master` == `f191fa7`. Clean, in sync, all pushed.
- Four commits this session, in order:
  - `70fd48f` — docs: record 2026-07-27 DB verification pass in the pilot readiness register
  - `1c1130f` — connectors: track B-4 patch and three one-off DB scripts as a reproducibility record
  - `894f9e1` — schema: capture point-in-time DDL snapshot and client_config calibration script
  - `f191fa7` — ci: add Supabase keep-alive workflow to prevent free-tier pause
- Uncommitted working tree, KNOWN and deliberate (HK-1): `seed_meta.py` (M), `onboarding_flow.py` (M),
  nine read-only `connectors/_*.py` probe scripts (untracked), `docs/sessions/*` (untracked),
  `slack_bot/` (untracked, stale since the email pivot — flag, do not delete).

## SANITY HANDLES (verify at next session open)
- `pilot_readiness_register.md` = **151 lines** (was 116; +35 declared and reconciled).
- `CLAUDE.md` = **280 lines** — VERIFIED wc -l = 280, matches (was 271). CRLF throughout, 0 bare LF.
  NOTE: the `/mnt/project/` mount showed 261 — mount is STALE, as always. HEAD is authoritative.
- `sql/schema.sql` = **1489 lines**.
- `connectors/seed_client_config_calibration.py` = **128 lines**.
- Other canonical files unchanged: `pilot_scope.md` (137) · `product_strategy.md` (1440) ·
  `operating_charter.md` (308) · `pre_agent_build_checklist.md` (389) · `technical_architecture.md` (3999).

## NEW IN THE REPO THIS SESSION
- `sql/schema.sql` — catalog-generated DDL. 45 tables (15 `public` + 30 non-Airbyte `client_azure_co`);
  138 Airbyte raw tables excluded. POINT-IN-TIME SNAPSHOT, not a migration. Per-table ordering means
  FKs forward-reference. Excludes comments, triggers, grants.
- `connectors/seed_client_config_calibration.py` — restores the hand-set calibrated values.
  **RUN AND VERIFIED 2026-07-27**: 1 row updated, read-back matched all ten values, idempotent, no trigger writes.
- `connectors/seed_b4_patch.py` — was untracked; the ONLY copy of the B-4 alias map. Now committed.
- `connectors/_delete_stale_alerts.py`, `_reinsert_b1.py`, `_rls_grant_harden_live.py` — historical one-offs,
  committed as records, each carrying a warning header. **`_reinsert_b1.py` is DESTRUCTIVE — reads before running.**
- `.github/workflows/supabase-keepalive.yml` — twice weekly (Tue/Fri 06:14 UTC) + manual dispatch.

## FOUNDER ACTIONS STILL OPEN (only you can do these)
1. Add the `SUPABASE_DATABASE_URL` repository secret (Settings → Secrets and variables → Actions).
   Value = the SESSION POOLER url + `?sslmode=require`. NOT the direct url — that is IPv6-only and
   unreachable from GitHub runners. Until this exists the workflow fails on every run.
2. Trigger one manual run (Actions tab → Supabase keep-alive → Run workflow) to prove it green.
3. Verify GitHub → Settings → Notifications → Actions emails you on failure. That email is the whole alarm.

## WHAT THE LIVE DB ACTUALLY SAYS (verified 2026-07-27, read-only)
- `top_sku_inventory_pct` = **0 non-null of 730**. Mart last built 2026-06-26, so NOT staleness.
  `technical_architecture.md:1160` AND `:2095` both claim it was fixed — BOTH WRONG. → register BT-18.
- Five other B-9 inventory columns carry 1 non-null of 730; `back_in_stock_waitlist_count` 730/730.
- Inventory feed is effectively a single snapshot; only two distinct extraction dates exist
  (2026-05-31, 2026-06-08). `tech_arch:1158`'s "daily Airbyte syncs accumulate" is NOT happening.
- `option1/2/3` on `shopify_product_variants` are **entirely NULL** — no variant carries a size.
  `inventory_policy` is uniformly DENY. → register BT-20.
- Order-line → variant join: **137,006 of 137,006**. BT-16 detection is buildable on synthetic data today.
- `alert_log` 177 rows; `alert_data_lineage` 0 rows. Evidence Stack Layer 2 has never been written.
- `permanent_dq_limitations` 0 rows (Layer 0). `suppression_log` 29 · `dq_metric_scores` 42 ·
  `brand_event_calendar` 116 (in `client_azure_co`; the `public` copy is 0).
- `pg_policies` = **ZERO policies database-wide**; RLS ON for all 15 public tables.
- `client_config` = **159 columns** live, against ~40 documented. Two triggers on it:
  `client_config_change_log`, `tier_limits_trigger` — in NO repo file.
- Four schemas exist that `CLAUDE.md` says do not: `client_azure_co_client_azure_co_marts`,
  `public_marts` (stale 51-column mart copy), `dbt_anupam313_marts`, `dbt_anupam313_staging`. → HK-7.

## REPRODUCIBILITY — WHERE IT LANDED
Five gaps found. Four closed, one was never a gap. Two new ones opened.
- CLOSED: B-4 attribution layer · one-off DB mutations · core-table DDL · calibrated config values.
- NEVER A GAP: RLS policies — live state (RLS on, zero policies, deny-all) IS reproducible from the
  tracked `_harden_public_schema.py`.
- **STILL OPEN:** the two `client_config` triggers (DB-only, and we still do not know what they do —
  the no-op UPDATE test proved only that they do not error). And nothing creates the `client_config`
  ROW except a fallback path inside `onboarding_flow.py`.
- Rebuild order is: schema DDL → the client_config row → the calibration script.

## REGISTER — WHAT CHANGED (all in `70fd48f`)
- NEW build tasks: **BT-16** (G1a/G1b split) · **BT-17** (inventory history backfill) ·
  **BT-18** (top_sku_inventory_pct null) · **BT-19** (checklist sweep) · **BT-20** (seed defects).
- NEW open questions: **OQ-15** (G3 definition conflict, PARKED) · **OQ-16** (creator profit truth).
- NEW: **DH-2** (Blueprint influencer claim overstated) · **HK-7** (schema drift).
- NEW SECTION "PROMOTED FROM pre_agent_build_checklist.md": D-1, CD-5, CD-8, CD-14, D-10, B-12, D-22
  live; CD-6, CD-7, CD-9, D-6 recorded closed so BT-19 does not re-raise them.
- NEW SECTION "HELD": HELD-1 (FC-4 reclassification) · HELD-2 (verification SQL placement) ·
  HELD-3 (Supabase paid-plan trigger).
- AMENDED: BT-4, BT-13, BT-14, BT-15, and the vanish-risk list.

## HELD-3 — RESOLVED BACK TO ITS ORIGINAL TRIGGER
Mid-session the argument for upgrading NOW was that the DB could not be rebuilt from the repo.
This session removed that reason. **Stay on the free tier; upgrade before the FIRST REAL BRAND CONNECTS,
for the encrypted-backups requirement in `pilot_scope.md` §6** — the free tier has zero days of backup
retention and therefore cannot satisfy a commitment already made. The keep-alive covers the interval.

## OPEN — NOT RESOLVED THIS SESSION
- **HK-2 needs REWRITING, not deleting.** Its premise — "the repo is the source of truth" — was FALSE
  this morning. It is closer to true now, but the item as written reassures about a risk it no longer covers.
- **RULE 8 divergence.** `CLAUDE.md` RULE 8 requires RLS enabled AND a policy on every public table.
  Live: RLS on, zero policies. Tenant isolation currently lives in the APPLICATION layer, not the database.
  No exposure at one client; becomes load-bearing at client two, which is a pilot-timeframe event.
- **`technical_architecture.md`** documents ~40 `client_config` columns against a live 159, and reads as canonical.
- The two `client_config` triggers, uncaptured.
- `client_id` split (`client_azure_co` canonical vs `azure_co` in ~306 seeded app rows) — already known,
  routed 2026-06-27, synthetic-only, NOT urgent. Do not re-discover it.

## WORKING ARTIFACTS (NOT in repo — personal)
- `pilot_readiness_27072026.xlsx` — regenerated from the register at `70fd48f`. 60 Build Sequence rows
  (Block A now A1–A37, Block C adds C4/C5, NEW Block D = HELD), 9 Parallel Track, 24 Legend.
  Supersedes `pilot_readiness_24072026.xlsx`. **Not backed up anywhere** — it carries five columns the
  register does not (pipeline stage, effort, Cowork, blocks-pilot, block classification).
- `DTC_Prism_Founder_Discovery_Call_India.docx` — India discovery questionnaire, 5 pages.
- `DTC_Prism_Outreach_Tracker.xlsx` — see the outreach state file.

## NEXT ACTIONS (priority order)
1. **Recruitment — the binding gate.** Nothing today moved it.
2. **A24 / BT-16** — the G1a/G1b split. Detection is buildable on synthetic data now; do the A34 doc
   edits inside the same session, not as a separate pass.
3. **A36 / BT-19** — the checklist sweep. 1–2 hours; treat the register as probably-incomplete until it runs.
4. Any other Block A item.
5. Standing: refresh the live Project instruction from committed `operating_charter.md` when the charter changes.

## STANDING DISCIPLINE
Two-agent split (Claude authors + reviews in chat; Claude Code edits/commits/pushes; founder authorises each).
Locate by quoted text. HK-6 straight quotes. Mount UNTRUSTED — verify against the file, not a summary.
Continuity files authored in chat; Claude Code VERIFIES only, never authors.
**Added this session:** for DATABASE state, the database is the only authority — not a spec, not a session
file. Three claims were corrected this session by querying instead of reading.
