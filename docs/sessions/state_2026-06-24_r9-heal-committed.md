# Profit Sentinel — State — 2026-06-24 — R9 Double-Seed HEALED + COMMITTED (recovery from data-loss incident)
## Session: continues the 2026-06-23 pre-pilot-hardening session. Began as "execute the R9 re-seed"; a data-loss incident occurred mid-heal and was fully recovered.
## Status: PHASE A COMMITTED (eb21af2). Live DB single-copy + verified. Recovery complete. No push. Local commits accumulate (now 5-deep).
## NOTE TO VERIFIER: confirm/correct this file's date stamp against the actual session date (Check 2). Commit/heal timestamps observed in-session were times only.

---

## NEXT SESSION — LOAD
- Load save_protocol.md FIRST (authoritative; 149 lines).
- Re-verify canonical line-count handles AGAINST REPO HEAD before any design/edit work.
  Mount has been stale repeatedly; HEAD is source of truth. This session edited NO canonical
  spec (only seed_shopify.py + seed_manifest_shopify.json) — any change to these is an error to flag:
    product_strategy 1424 · technical_architecture 3929 · agent_d_build_spec 2722 ·
    cross_alert_orchestration 847 · d1_validation_gates 399 · pre_agent_build_checklist 389 ·
    save_protocol 149 · pilot_scope 122.
- Canonical files live under docs/ in the repo. Continuity pairs live under docs/sessions/.
- HEAD is now **eb21af2** (was a307b81). Local-only commit stack (not pushed, 5-deep):
  **eb21af2 → a307b81 → 8a707a1 → ae8a2d5 → b8fec19** (`master...origin/master [ahead 5]`).
  Push as ONE coherent set later (after hardening lands), not piecemeal.
- Deliberation mode: tag load-bearing claims [verified—file:line] / [inference] / [guess];
  verify THIS turn in Claude Code, never from memory or the mount; one item at a time with
  sign-off; design here, build in Claude Code (read-only mount; no repo/DB/git from chat).
- NEXT ACTION: pre-pilot hardening **Phase B** (Egnition island purge/keep), then C → D → E → F
  (see HARDENING PHASES). The R9 double-seed is DONE.

---

## WHAT THIS SESSION ACTUALLY DID (in one breath)
Executed the R9 fix: made seed_shopify.py idempotent (per-table key-scoped delete-then-insert at
all 14 write targets + deterministic discount id) and healed the live double-seed to single-copy.
A **data-loss incident** occurred mid-way (a throwaway test harness silently dropped all INSERTs
while DELETEs ran, committing a near-empty state). It was caught, scoped, and **fully recovered**
by regenerating the seed universe through the production path. Phase A is committed at eb21af2.
The only canonical/state corrections needed (R12 etc.) are recorded below and ROUTED to a later
canonical pass — they were NOT written into canonical specs this session.

---

## THE INCIDENT + ROOT CAUSE (recorded so it never recurs)
- A throwaway harness `_heal_run.py` monkeypatched `psycopg2.extras.execute_values` to a no-op for
  a dry pre-check, then ran the live pass IN THE SAME PROCESS. `importlib.reload(seed_shopify)`
  restored `seed_shopify.batch_insert` but NOT the **global** `psycopg2.extras.execute_values`.
  Result: in the live pass the real `batch_insert` called the still-no-op `execute_values` →
  **every INSERT silently skipped while DELETEs ran for real → committed a near-empty state.**
- **THE VACUOUS-PASS HOLE (the real lesson):** the gate's assertions passed *vacuously* — an empty
  table trivially satisfies `COUNT(*)==COUNT(DISTINCT key)`, "island present," and "connectors
  preserved." A corruption check is NOT a presence check. **Presence-band assertions (fail loudly
  on empty/under-populated) are mandatory alongside uniqueness checks.**
- The seed_shopify.py EDITS themselves were always correct (determinism passed, golden matched);
  the harness destroyed the data, not the fix.

## THE RECOVERY (Option 3 — regenerate via production path)
- Backup `ps_full.dump` (36,743,848 bytes, custom/gzip, created pre-heal) was content-verified via
  `pg_restore -l` (1266 TOC entries, 229 TABLE DATA incl. shopify_order_line_items) → golden content.
- Restore-from-dump was ATTEMPTED but the machine's link could not sustain large COPYs: both the
  transaction pooler (6543) AND session pooler (5432) dropped SSL on klaviyo_email_events (~67k
  rows / ~8MB). The failed restore + every failed dump left **zombie "idle in transaction"
  backends** (8, ages 9–16h) holding locks; a blocked `DROP public.suppression_log` (pid 335885)
  piled up behind them → reads timed out. Cleared with `pg_terminate_backend` (the 8; 335885 cleared
  on its own once the chain released). This was the OneDrive/pooler "stop-don't-force" risk MATERIALIZING.
- **DECISION: Option 3** — regenerate via the production `seed_shopify.py main()` (NOT a file
  restore), because seed data is deterministically regenerable from the golden and the ONLY
  non-regenerable rows (the Egnition island) were confirmed intact. Restore-from-dump was abandoned
  because the link couldn't carry it; the dump remains a valid on-disk restore point regardless.
- Run was gated (production path, real execute_values, **no harness**) with **presence-band +
  dup-excess** assertions added (closing the vacuous-pass hole). First run ROLLED BACK on a BEC
  false-fail (mis-keyed assertion — see corrected facts). Re-keyed and re-ran: **32/32 assertions
  passed, COMMITTED.**
- Post-commit `validate_seed` (the seed's pre-existing 11 heavy-aggregation checks) timed out on the
  network → reported 2/11. This is **post-commit and informational** — integrity was proven by the
  32 gated assertions BEFORE commit. ROUTED (query tuning / faster connection), non-blocking.

## VERIFIED HEALED STATE (live COUNT(*), single-copy)
| table | healed count |
|---|---|
| shopify_orders | 84230 |
| shopify_order_line_items | 137006 |
| shopify_customers | 9509 |
| shopify_products | 168 (125 seed + 43 island) |
| shopify_product_variants | 626 |
| shopify_order_refunds | 22979 |
| shopify_fulfillments | 5250 |
| synthetic_touchpoint_journey | 63293 |
| shopify_inventory_levels | 626 |
| synthetic_customer_pii_lookup | 9508 |
| shopify_discount_codes | 13 (12 seed + 1 island) |
| brand_event_calendar | 116 |
| dq_metric_scores | 42 |
| client_azure_co.suppression_log | 10 |
| public.alert_log | 177 |
Every seed table: COUNT(*) == COUNT(DISTINCT key) (doubling healed).
Connectors INTACT (real COUNT, not n_live_tup): klaviyo_email_events 67840 · gorgias_tickets 10296 ·
meta_ad_performance 7376 · public.suppression_log 29.
Egnition ISLAND intact: order 6438993559648 · customer 8824697159776 · 43 real products ·
AD-04\n-OS-blue variant · CODE_BXGY_DISCOUNT_SUMMERBOGO discount.
Manifest in-memory golden = `55aba735219d5f06ce0f17deb807a7fc79fa0a53e115dc75ce3fe88d2335451c`.

---

## CORRECTED FACTS — retire the old wording (ROUTED to a later canonical save-protocol pass; NOT written into canonical specs this session)
These overturn statements written into the 06-23 state file and/or canonical record. Each lists the
retired wording (for the Check-4 retired-wording scan when the canonical pass runs).

1. **R12 RETRACTED.** Retire: *"DB is Shopify + cost ONLY; 8 of 10 source connectors built-but-unrun
   (0 rows)."* FALSE — `pg_stat_user_tables.n_live_tup` reports 0 for non-ANALYZEd tables; real
   COUNT(*) shows ALL connectors populated (klaviyo 67840, gorgias 10296, meta 7376, tiktok 2190,
   loop 2226/2691, ga4 14802/2190, sentry 7826, google_ads 5137).
2. **n_live_tup family (same artifact).** Retire: *"staging stg_* = 0 rows"* and *"the 3 shared
   tables are populated only by seed_shopify."* Both were n_live_tup artifacts. Shared tables
   (BEC / dq_metric_scores / suppression_log / alert_log) are genuinely **multi-writer** (seed +
   connectors).
3. **R9 discount_codes "clean control."** Retire: *"discount_codes 25/25 CLEAN — working unique
   constraint dedup'd."* FALSE — there are **ZERO PK/UNIQUE constraints on any core table**;
   discount_codes was doubled (1.923× by `code`); the apparent 1.0 was an RNG-id artifact.
4. **R5 ≡ R6 (collapse to one item).** The `AD-04\n-OS-blue` newline SKU (R5) is the lone variant of
   the real Adidas product 7698713116768 (R6). The real "island" is **classic Shopify dev-store /
   Egnition sample data = 43 products + 1 variant + 1 discount + 1 order (6438993559648) + 1 customer
   (8824697159776)** — NOT "1 Adidas product" (that was an undercount). Reference-clean: 0 synthetic
   order/line refs to any island row.
5. **BEC delete/uniqueness key.** `(client_id, event_name)` is NOT a valid unique key — BEC `id` is an
   IDENTITY column (useless for doubling detection) and the **connector data has 2 native
   (client_id,event_name) duplicates.** Correct guard = presence band + **dup-excess invariant** (heal
   adds no NEW duplicate keys beyond the connector's pre-existing 2). The seed's own delete keys on
   the emitted `(client_id, event_name)` set.
6. **suppression_log seed key = `signal_detected_at`** (NOT `would_have_fired_at`, which is hardcoded
   None/NULL on all 20 seed rows). The client_azure_co table (seed, 26-col, richer) and public table
   (connectors, 20-col, leaner) are DIFFERENT-schema tables — R13 split, still open (Phase E).
7. **Golden hash.** The true golden is `55aba735…` (the `\n`/LF in-memory serialization). The earlier
   `2f27ff24…` was never a golden (non-reproducible run + it's just the Windows CRLF serialization of
   the same content). Asserting against `2f27ff24` was wrong. (Repo `core.autocrlf=true` stores LF, so
   the committed manifest blob hashes to `55aba735…`.)
8. **RULE 3 (is_synthetic) broadly violated.** Retire any claim that shopify_* raw OR staging derive
   is_synthetic. `is_synthetic` is ABSENT on the 10 shopify base tables (CLAUDE.md:79-80 violated) AND
   the shopify staging spine (orders/line_items/inventory) derives/filters NONE — the synthetic/real
   boundary is currently **unbuilt** for the shopify spine. (Present on 86 tables, absent on 83.)
9. **dbt schema.yml name-drift = FALSE.** Retire: *"stg_shopify_refunds vs stg_shopify_order_refunds
   name-drift / declared-but-nonexistent models."* All 13 declared models have files. Real R11 gap =
   **5 untested staging models** (stg_klaviyo_flows, stg_klaviyo_profiles, stg_shopify_inventory_items,
   stg_shopify_inventory_levels, stg_synthetic_touchpoint_journey) + marts bypassing tested stg layer.

---

## RECON FACTS THAT REMAIN VALID (design inputs for Phases B–F; verified read-only this session)
- **G1 seed-isolating predicates** (now IMPLEMENTED in committed seed): products `product_type ∈
  {top,dress,short,knit,outerwear,denim,formal,mens}`; variants `sku ~ '^AZ-[A-Z]+-[0-9]+'`;
  customers/orders/refunds/fulfillments `id < 1e12`; line_items `order_id < 1e12`; inventory_levels
  `NOT (inventory_item_id::text ~ '^[0-9]{13,}$')`; touchpoint non-13-digit order_id; pii_lookup
  `synthetic_customer_id < 1e12` (text-safe); discount `code ∈ 12-seed-list`; discount id now
  deterministic `920_000_000 + seq`.
- **G3 mart bypasses** (Phase C target): mart_causal_chain_daily reads raw `shopify_orders`(342,459),
  `shopify_order_line_items`(458), `shopify_inventory_levels`(450), `google_ads_performance`(327, no
  stg model), `meta_ad_performance`(368/401/529), `tiktok_ad_performance`(540);
  mart_return_rate_by_sku reads `loop_return_line_items`(21), `sku_cost_master`(32).
- **G4 constraint-key validity** (Phase D): `order_line_items.id` is NOT unique even single-copy
  (colliding seed id space; natkey has legit collisions) → needs a surrogate/fix before a unique
  constraint; `klaviyo_email_events` must key on `message_id` (natkey has 374 legit collisions); all
  others id==natkey OK.
- **G5 is_synthetic placement** (Phase C): DERIVE in staging (per existing connector-stg pattern),
  do NOT ALTER raw shopify_* tables (Airbyte full-refresh would clobber the column).
- **G7 FKs**: only 2 in the whole DB (alert_data_lineage.alert_log_id → alert_log; thread_context
  .alert_id → alert_log); both child tables are EMPTY → delete-order unconstrained.
- **S7**: seed_sku_cost_master filters catalog to `sku ~ '^AZ-...'` → excludes the real island →
  the island does NOT re-enter sku_cost_master on re-seed (OP-1 clean). NOTE per OP-1: "no mart joins
  shopify_products for category" — category grouping reads the resolved node in sku_cost_master.

---

## HARDENING PHASES (forward plan — separate gated commits, R9/Phase A is DONE)
- **Phase A — R9 idempotency + heal — DONE, committed eb21af2.**
- **Phase B — Egnition island purge vs keep.** Reference-safe either way (G2). Recommended: PURGE as a
  conscious R6 resolution — but once the Phase-C boundary is built, is_synthetic excludes it anyway,
  so purge is cosmetic. Founder decision pending. (If purge: delete the 43 products + 1 variant + 1
  discount + order 6438993559648 + customer 8824697159776; snapshot first.)
- **Phase C — build the is_synthetic boundary (R6 / RULE 3).** Derive is_synthetic in the shopify
  staging spine (per G5) + add `where is_synthetic = var('use_synthetic_data')` + **re-route the
  bypassing marts (G3) through filtered staging** (restoring the staging filter alone is insufficient
  because marts read raw). Resolve the Airbyte sync-mode/coexistence question.
- **Phase D — make controls real (R11).** Add unique constraints on G4-validated keys (fix
  order_line_items key; klaviyo message_id); add schema.yml test entries for the 5 untested stg models;
  wire `dbt test` into the run path. **CRITICAL: relocate the durable presence/uniqueness validation
  into `validate_seed`** — the temporary heal gate that provided this was removed for the permanent
  commit, so the production seed's bare `conn.commit()` currently has NO such guard. This is where that
  protection permanently lives.
- **Phase E — R13 suppression_log canonicalization.** Pick the richer (client) schema as canonical;
  migrate the public connector rows; repoint all writers; one home.
- **Phase F — R10 build validate_sync.py** (the absent post-sync variance guard).
- **THEN — canonical state-file corrections pass** (the 9 corrected facts above + D-A..D-F landings),
  written once against this verified healed state under the save protocol (Checks 4/7/8/10/11).

---

## LOCKED DECISIONS (carry forward; do NOT reopen) — from 06-23
- D-A: two-bar connector model.
- D-B: Bar-2 fired sources = Shopify / Gorgias / Meta / Google Ads / TikTok; cost is plumbing.
- D-C: Loop / Klaviyo / GA4 / Sentry opportunistic.
- D-D: Loop fallback until Shopify-native returns proven.
- D-E: weekly founder digest IN pilot via email through the relevance gate (DOC CONFLICT: canonical
  docs vs Horizon-2 — reconcile in the canonical pass).
- D-F: HARD 7-condition pre-pilot gate (incl. a deliberate fault-injection drill — note: this session
  was an UNINTENTIONAL real-world instance of exactly that failure mode; the gate's value is proven).
- D-G: hardening ranks ahead of Pass Two / C8 / taxonomy; Pass Two folded into hardening.

---

## ROUTING (future passes — recorded so they don't evaporate)
- **R13 alert_log distinct(id) doubling check** (was "fold into re-seed recon") → **RESOLVED**: the heal
  healed public.alert_log to 177 single-copy (seed alerts de-doubled, connector alerts preserved).
- Canonical-doc landings for D-A..D-F (incl. the D-E Horizon-2 conflict) → the later canonical
  save-protocol pass (the scheduled pilot_scope reconciliation). STILL OPEN. NOW ALSO carries the 9
  corrected facts above.
- O-26 full design-consistency / doc-vs-DB audit → scheduled, separate cadence (unchanged). STILL OPEN.
- validate_seed heavy-aggregation timeout over this network → query tuning / faster connection. OPEN.
- Pass Two (SKU-contract assertion) → folded into hardening per D-G; the Pass-One set-membership
  contract remains intact and unaffected by the row inflation.
- C8 HERO return-driver alert + taxonomy versioning → unchanged Horizon items, not this stream.

---

## HORIZON / FLAGS (do not chase next session)
- Local-only commit stack (eb21af2 → a307b81 → 8a707a1 → ae8a2d5 → b8fec19) not pushed — one coherent
  push later. **NOTE: bulk transfer over this machine's link is unreliable** (transaction + session
  poolers both drop large COPYs; local NAT/idle/TLS-inspection suspected). A push of small commits is
  fine; any future bulk dump/restore needs a stable network or a cloud shell near AWS us-east-1.
- OneDrive corruption risk on the repo path — ongoing; stop-don't-force on lock errors. (Materialized
  this session as the zombie-backend lock pile-up.)
- The whole platform has the RIGHT controls designed (R10 sync guard, R11 dbt tests, RULE 3
  is_synthetic boundary) but NONE are in the enforcement path — the systemic story. Phases C/D/F move
  them in.
- Backup `ps_full.dump` exists on disk (D:\ps_backups\, verified golden content) — a valid restore
  point, though the DB was regenerated (Option 3) rather than restored from it.

---

## WORKING-TREE / FILE STATE (verify in Phase B)
- Committed (eb21af2, 2 files): connectors/seed_shopify.py (permanent R9 fix only — temporary heal gate
  removed), connectors/seed_manifest_shopify.json (re-baselined to golden 55aba735…, stored LF).
- `_heal_run.py` DELETED (the buggy monkeypatch harness — never reuse).
- Untracked kept: `_dryrun_determinism.py` (reusable golden check), `_passtwo_orphan_probe.py`.
- Pre-existing stash WIP UNTOUCHED/unstaged: seed_meta.py, onboarding_flow.py, mart_causal_chain_daily.sql,
  mart_cross_source_daily.sql, schema.yml, stg_loop_returns.sql. (Not part of Phase A.)

---

## DECISION LEDGER (Phase 0 — read from this session's conversation; for Check-11 reconciliation)
| # | decision (one line) | target / home | retires wording? | routed? |
|---|---|---|---|---|
| 1 | R9 fix authored: 14-site key-scoped delete-then-insert + deterministic discount id | seed_shopify.py (committed eb21af2) | — | — |
| 2 | Live double-seed healed to single-copy via Option-3 production-path regenerate | live DB (done) | — | — |
| 3 | Phase A committed `eb21af2` on a307b81; stack now 5-deep; NOT pushed | this state file + git | — | push routed (one set later) |
| 4 | Temporary heal gate removed from main(); bare conn.commit() restored | seed_shopify.py (committed) | — | durable validation → Phase D |
| 5 | `_heal_run.py` deleted (incident cause) | working tree | — | — |
| 6 | Incident root cause + vacuous-pass hole recorded | this state file | — | — |
| 7–15 | The 9 corrected facts (R12, n_live_tup family, discount_codes, R5≡R6, BEC key, suppression key, golden, RULE 3, schema.yml) | this state file | YES (see CORRECTED FACTS) | canonical pass |
| 16 | R13 alert_log doubling sub-item RESOLVED by heal | this state file ROUTING | — | — |
| 17 | Phases B–F forward plan defined | this state file | — | next sessions |
| 18 | Locked decisions D-A..D-G carried forward | this state file | — | D-A..D-F landings routed |
| 19 | validate_seed timeout + network bulk-transfer limit recorded | HORIZON/ROUTING | — | routed |

---

## FILES TO SAVE / UPLOAD THIS SESSION
- state_2026-06-24_r9-heal-committed.md (this file)
- chat_context_2026-06-24_r9-heal-committed.md (paired narrative)
- No canonical spec edited this session → no canonical re-upload required.
- seed_shopify.py + seed_manifest_shopify.json were already committed as eb21af2 (Phase A).
Save → (founder approves text) → commit the two continuity files only → re-upload the pair to the
Project (one-way sync). The canonical-corrections pass (the 9 facts above) is a SEPARATE later save.

## SANITY HANDLES (write real post-edit counts here in Phase B — Check 12)
- state_2026-06-24_r9-heal-committed.md: 271 lines
- chat_context_2026-06-24_r9-heal-committed.md: 117 lines
