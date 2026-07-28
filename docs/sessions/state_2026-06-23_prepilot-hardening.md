# Profit Sentinel — State — 2026-06-23 — Pre-Pilot Hardening (R9–R13 + locked decisions)
## Session: opened as "Pass Two — SKU-contract assertion"; a live-data integrity investigation took over.
## Status: RECON COMPLETE, captured. No data fix run. No canonical spec edited. No push. Local commits accumulate.

---

## NEXT SESSION — LOAD
- Load save_protocol.md FIRST (authoritative; 149 lines).
- Re-verify canonical line-count handles AGAINST REPO HEAD before any design/edit work.
  Mount has been stale repeatedly; HEAD is source of truth. Expected @ HEAD (this session
  edited NONE of them — any change is an error to flag):
    product_strategy 1424 · technical_architecture 3929 · agent_d_build_spec 2722 ·
    cross_alert_orchestration 847 · d1_validation_gates 399 · pre_agent_build_checklist 389 ·
    save_protocol 149 · pilot_scope 122.
- Canonical files live under docs/ in the repo. Continuity pairs live under docs/sessions/.
- Local-only commit stack (not pushed): a307b81 + 8a707a1 + ae8a2d5 + b8fec19. Push as ONE
  coherent set later (after hardening lands), not piecemeal.
- Deliberation mode: tag load-bearing claims [verified—file:line] / [inference] / [guess];
  verify THIS turn in Claude Code, never from memory or the mount; one item at a time with
  sign-off; design here, build in Claude Code (read-only mount; no repo/DB/git from chat).
- NEXT ACTION: pre-pilot hardening, NOT Pass Two in isolation (see PRIORITY D-G). Open the
  re-seed work (R9 fix) by MAPPING THE CONNECTOR RUN-ORDER first.

---

## WHAT THIS SESSION ACTUALLY DID
Began as Pass Two (the SKU-contract + uniqueness assertion, old R1). A read-only live-DB
investigation — triggered by the order-line/catalog orphan probe — uncovered a chain of
integrity + control-plane gaps (R9–R13) and prompted a set of pre-pilot scoping decisions
(D-A..D-G). All findings are read-only/verified; NO truncate, re-seed, or data fix was run;
NO canonical spec was edited. This file + its chat_context are the sole home of this work.

Recon entry point that still stands: every distinct order_line_items.sku resolves to the
catalog — 0 orphans (Pass One contract intact; set-membership checks are immune to the row
inflation found below).

---

## R12 RESOLUTION (cited, not asserted) — LABEL: GAP (cause TBD)
Question: is "only seed_shopify.py + seed_sku_cost_master.py have run; the other 8 source
connectors are built but at 0 rows" the EXPECTED build stage or a gap?
- Build Sequence (technical_architecture.md §10, lines 1216–1232) intends a FULLY-POPULATED
  multi-source warehouse: Step 5 "comprehensive seed script (all 6 sources)", Step 6 "staging
  models for all 6 sources … dbt run — all models green", Step 7 "5 cross-source narrative
  scenarios … confirm causal chains detectable".
- pre_agent_build_checklist.md records multi-source data as previously seeded + validated:
  A-7h "stg_klaviyo_flows … 14 distinct flows, $188,719 revenue" (line 35); A-1 "626 rows"
  (line 15); G1 "626 items, 3 alert rows seeded" (line 73).
- The build has progressed FAR past Step 7 (B-series, C-series, OP-1, taxonomy versioning,
  SKU contract). At this point the documented state assumes all sources populated.
=> The current live DB (8 connectors at 0 rows) is a GAP vs documented state. Whether multi-
   source data was once loaded into THIS db and later wiped (a regression) or was never loaded
   here (never-loaded) is UNRESOLVED — the GAP label holds either way; only the cause differs.
   Most-likely (inference, not fact): a DB reset where only shopify + cost were re-run during
   the SKU-contract work. Closing it is part of the hardening re-seed (R9 fix).

---

## ROUTING LEDGER (Check-11 — recorded so nothing evaporates)

### Carried forward from state_2026-06-22_sku-contract-pass1.md (R1–R8):
- R1 assertion -> Pass Two. NOTE: under D-G this is REFRAMED as a piece of hardening (the
  uniqueness assertion IS the missing warehouse-layer guard), not a standalone next step. Full
  design preserved below under "PASS TWO GUARD DESIGN".
- R2 top_sku_inventory_pct re-enable @ mart_causal_chain_daily.sql:506 -> later mart edit
  (cost is now AZ-, so it can re-enable).
- R3 label->SKU bridge (B-4 semantic labels in loop/gorgias/meta/tiktok) -> OUT of scope;
  off the rebind critical path (label<->label in one mart). Entangled with C8/hero.
- R4 effective-dated cost history -> deliberate later pass IF a margin-compression-over-cost-
  trend signal is built.
- R5 AD-04 \n -OS-blue SKU newline -> transform/staging trim (python_transformer.py), NOT a
  seed fix. Never reaches order lines; not load-bearing for Pass One/Two.
- R6 a REAL Adidas product (id 7698713116768) in the synthetic schema -> horizon doc-vs-DB
  hygiene sweep (data contamination).
- R7 B-8 / tech-arch staleness: pre_agent_build_checklist.md:207 (B-8 "428 rows") and tech-arch
  reseed annotation (~L1297, "428 / 380 active / FW25 step-change") now stale (counts are 125,
  no hero) -> canonical doc pass once final counts settle (after LLM pass).
- R8 category_inference._READ_SQL fan-out (v.sku = scm.sku, per-style x per-size = 5x) ->
  bundled into the LLM/fan-out pass. Real bug the conform surfaced; final state idempotent.

### Added this session (R9–R13):

- R9 — seed_shopify.py is APPEND-ONLY. No TRUNCATE/DELETE/DROP anywhere. Its ON CONFLICT DO
  NOTHING is UNTARGETED (signature/builder at seed_shopify.py:270/274; no call site passes
  conflict_col) -> inert on the constraint-less Airbyte raw tables. Running it twice appended a
  second full universe. VERIFIED inflation (total / distinct-id):
    order_line_items 274029/137023 · orders 168459/84230 · order_refunds 45972/22993 ·
    customers 19017/9509 · fulfillments 10500/5250 · product_variants 1251/626  (all ~2.000x);
    inventory_levels 1251 doubled (id degenerate, distinct=1); products 293/168 = 1.744x
    (PARTIAL — 125 catalog styles doubled, 43 non-catalog single); synthetic_touchpoint_journey
    126687 = 1.204x at grain (order_id, touchpoint_sequence) (FRACTIONAL, RNG-divergent ->
    NOT recoverable by deletion); discount_codes 25/25 CLEAN (control case — it has a working
    unique constraint, so the bare ON CONFLICT actually dedup'd).
  Key consequence: COUNT(DISTINCT ...) / ratio gates survive; absolute SUM(quantity|revenue)
  are 2x inflated; mart_causal_chain_daily is ~4x (doubled li x doubled orders inner-join,
  mart_causal_chain_daily.sql:~458 — re-confirm line at edit time). Pass One contract UNAFFECTED.
  FIX = per-table clear-before-insert guards mirroring seed_sku_cost_master.py's
  DELETE-WHERE-is_synthetic pattern (KEY-SCOPED delete for the 3 shared tables, NOT
  is_synthetic), then ONE clean re-run. seed_shopify is the pipeline ROOT and is self-contained
  (no read-to-generate dependency — verified: its only SELECTs are post-seed validation checks;
  MANIFEST is built in-memory and written once). Selective dedup is NOT viable (touchpoint +
  products cannot be reconstructed by deletion) -> full clean re-seed is the only reliable path.
  POST-RESEED VERIFICATION TARGETS (clean single-run counts = the distinct-id column):
    order_line_items ~137023 · orders ~84230 · order_refunds ~22993 · customers ~9509 ·
    fulfillments ~5250 · product_variants 626 · products ~168 · discount_codes 25 ·
    touchpoint at its (order_id, touchpoint_sequence) grain. After the fix, re-verify id
    UNIQUENESS explicitly (total = distinct id) per table — do NOT assume the truncate fixed it.

- R10 — Production SYNC-VARIANCE GUARD is specified but UNBUILT. connectors/validate_sync.py
  does not exist; no module enforces a post-sync row-count variance limit (>1%) or agent
  suppression (verified across connectors/ — only incidental "reconcile" matches in
  _validate_meta/seed_meta/category_inference). Spec lives in docs only (DEBT-004 /
  technical_architecture data-flow). This is the control that would catch a production Airbyte
  double-load — i.e. the production analog of R9. Pilot-readiness item.

- R11 — dbt data tests EXIST but are NOT ENFORCED. staging/schema.yml + marts/schema.yml carry
  `unique`+`not_null` on exactly the violated keys (stg_shopify_order_line_items.line_item_id
  staging/schema.yml:29-30; stg_shopify_orders.order_id :7-8) — yet they never fired, because:
  (a) tests are not run as a gate after seeds; (b) staging is UNMATERIALIZED (all stg_* = 0 rows
  -> unique test passes vacuously); (c) mart_causal_chain_daily reads the RAW
  shopify_order_line_items directly (mart_causal_chain_daily.sql:~458), BYPASSING the tested
  layer; (d) schema.yml NAME-DRIFT — e.g. `stg_shopify_refunds` (schema.yml:16) vs the real
  stg_shopify_order_refunds, plus models that don't exist -> inert tests.
  FIX = gate dbt tests post-build; materialize staging; point marts at the tested staging layer;
  fix the name-drift.

- R12 — DB is SHOPIFY + COST ONLY; 8 of 10 source connectors built-but-unrun (0 rows):
  google_ads, ga4, meta, tiktok, klaviyo, gorgias, loop_returns, sentry. Confirmed across BOTH
  schemas (client_azure_co + public; google_ads not hiding in public). Shared tables
  (brand_event_calendar 216, dq_metric_scores 33, suppression_log 10) populated only by
  seed_shopify's writes; public holds only alert_log (264). LABEL: GAP — currently unloaded;
  cause (prior-state wiped vs never-loaded into THIS db) TBD (see R12 RESOLUTION above —
  tech-arch §10 Steps 5–7 + checklist A-7h/A-1/G1).

- R13 — suppression_log SCHEMA-SPLIT. seed_shopify writes client_azure_co.suppression_log
  (default batch_insert, seed_shopify.py:2455) while seed_tiktok/seed_sentry/seed_loop_returns
  write public.suppression_log (seed_tiktok CREATEs it with a unique constraint, DDL :374).
  Same logical table, two schemas -> data would split, no consumer sees the union. Canonical
  home UNSPECIFIED (not in the public-table list); RULE 8 (RLS) implication. CORRECTION ON
  RECORD: an earlier turn this session attributed the clean 10-row count to "public + unique
  constraint"; the populated 10-row table is actually client_azure_co.suppression_log
  (seed_shopify's), whose constraints are unverified. Sub-item: public.alert_log = 264 rows;
  confirm distinct(id) (it uses ON CONFLICT DO NOTHING at seed_shopify.py:2285) to rule out
  doubling.

---

## DECISIONS LOCKED THIS SESSION
- D-A  TWO-BAR connector model.
       BAR 1 (built + integrity-checked: schema discovery, two-run incremental test, dbt tests
       enforced+materialized, sync-variance guard) for EVERY source a brand can connect,
       including opportunistic ones.
       BAR 2 (rich synthetic data + proven end-to-end on synthetic before pilot) for the
       fired-alert sources only.
- D-B  BAR-2 fired-alert sources = Shopify, Gorgias, Meta, Google Ads, TikTok. (TikTok CONFIRMED
       IN by founder this session — major source, not optional.) Cost (sku_cost_master) is
       foundational plumbing, already clean, read by no fired alert.
- D-C  OPPORTUNISTIC (Bar 1 only) = Loop, Klaviyo, GA4, Sentry.
- D-D  Loop = opportunistic enrichment; Shopify-native returns is the PRIMARY spine. Founder
       agreed Loop stays the fallback UNTIL Shopify-native returns ingestion is proven reliable.
       "Prove Shopify-native returns ingestion" is a pre-pilot GATE line item.
- D-E  WEEKLY FOUNDER DIGEST is IN the pilot (email is the Phase-1 primary surface). It carries
       everything the FINAL-PRODUCT digest would capture, instantiated over the PILOT-MONITORED
       signal set — the fired pilot alerts + the in-app metrics (blended post-return ROAS,
       serial-offenders, return-rate+reason) + a suppressed-leaks summary. I.e. full-product
       digest INTENT, scoped to what the pilot monitors — NOT a fixed shortlist, NOT the full
       58-alert scope. Routed THROUGH the relevance gate (the gating mechanism for a WEEKLY
       cadence is an OPEN design item — the per-alert gate has 1-day latency + a fast-lane,
       which may not map cleanly to a weekly digest). DOC CONFLICT TO RECONCILE: canonical docs
       currently route weekly-digest-of-suppressed-leaks to Horizon-2; this pulls it INTO pilot.
       Reconcile in a future canonical pass (see ROUTING).
- D-F  PRE-PILOT HARDENING GATE (HARD — no brand connects until ALL hold):
       (1) R9 seeds idempotent;
       (2) R10 sync-variance guard built + wired to suppress agents;
       (3) R11 dbt tests gated + staging materialized + marts behind staging + name-drift fixed;
       (4) the 5 Bar-2 sources proven end-to-end on synthetic through the enforced controls;
       (5) all connectable sources pass Bar 1;
       (6) Shopify-native returns ingestion proven;
       (7) a deliberate FAULT-INJECTION DRILL — double-load one source on purpose, confirm the
           pipeline catches it and freezes the alerts.
- D-G  PRIORITY: pre-pilot hardening + connector completion ranks AHEAD of Pass Two, the C8 edit,
       and taxonomy-versioning. Pass Two's SKU-contract + uniqueness assertion (old R1) is NOT
       dropped — it BECOMES a piece of the hardening (the uniqueness assertion is the missing
       warehouse-layer guard, R11). Full design preserved below.

---

## PASS TWO GUARD DESIGN (decided early-session; folded into hardening per D-G / R11 — preserve so it is not re-derived)
This is the design reached BEFORE the data investigation took over. Pass Two never ran, but the
design is DECIDED and must not be re-derived next session.
- HOME: a STANDALONE validator (e.g. connectors/assert_sku_contract.py) that REUSES
  seed_sku_cost_master.validate()'s cost<->catalog checks (cost_orphans + catalog_uncovered)
  rather than duplicating them, and ADDS the order-side + whitespace checks on top. NOT folded
  into the cost seed (orders are out of its scope); NOT a fresh-each-session shell script. It
  asserts a 3-table CONTRACT (orders <-> cost <-> catalog), so it must run independently.
- TRIGGER: post-seed, EVERY time, as a HARD gate (wire into CI additively if/when CI exists).
- ASSERTS (4):
  (1) every distinct order_line_items.sku (trimmed) is in the catalog set;
  (2) every record_type='sku_cogs' row's sku is in the catalog set  [ALREADY in validate()];
  (3) ZERO sku_cogs floors FOR LACK OF A COST ROW  [~ validate()'s catalog_uncovered] — this is
      DISTINCT from the 71 category-floor (the LLM-not-run axis); keep the two axes separate;
  (4) reject whitespace/control-char SKUs (the AD-04 class).
  influencer_gifting_package is EXEMPT.
- FAIL-HARD on the 3 genuine contract invariants ONLY (cost-orphan / junk SKU / missing-cost-row).
- COVERAGE (sku_cost_coverage_by_revenue, the D1 >=0.85 gate) is REPORTED, NOT enforced — below
  0.85 is a DESIGNED fall-back state (drop to Tier 2/3 + disclose), NOT a crash. Enforcing it
  would turn valid product behaviour into a build failure (would bite the first realistic
  low-coverage brand).
- EXCLUSIONS BY KIND, NOT COUNT: exempt gifting by record_type; ignore the category axis entirely.
  NEVER hardcode 71 or 8 — the LLM pass changes the 71.
- Use NOT EXISTS, not NOT IN (NULL-robust); validate() already does.
- BUILD-ONLY (synthetic). NEVER point this hard guard, unchanged, at a real client's cost upload —
  real Finaloop / founder CSVs legitimately mismatch (~75% coverage) and route to review /
  reconcile, not a halt. The PRODUCTION equivalent of this guard is R10 (sync-variance) + R11
  (enforced dbt tests), NOT this script.
- NEW REQUIREMENT (from R9): ADD a PRIMARY-KEY / row-uniqueness assertion — total = distinct id
  per table. This is the single check that would have caught the double-seed on day one; it is
  the piece D-G folds into hardening.

---

## ROUTING (future passes — recorded so they don't evaporate)
- Canonical-doc landings for D-A..D-F (including the D-E Horizon-2 conflict) -> a later canonical
  save-protocol pass (the scheduled pilot_scope reconciliation). NOT this session.
- Re-seed execution (R9 fix) -> next session; OPEN by mapping the connector run-order.
- R13 sub-item (public.alert_log distinct(id) doubling check) -> fold into the re-seed recon.
- O-26 full design-consistency / doc-vs-DB audit -> scheduled, separate cadence (unchanged).

## HORIZON / FLAGS (do not chase next session)
- Local-only commit stack (a307b81 + 8a707a1 + ae8a2d5 + b8fec19) not pushed — one coherent push later.
- OneDrive corruption risk on the repo path — ongoing; stop-don't-force on lock errors.
- The whole platform has the RIGHT controls designed (R10 sync guard, R11 dbt tests) but NONE are
  in the enforcement path — that is the systemic story, not three isolated bugs.

## FILES TO SAVE / UPLOAD THIS SESSION
- state_2026-06-23_prepilot-hardening.md (this file)
- chat_context_2026-06-23_prepilot-hardening.md (paired narrative)
- No canonical spec edited this session -> no canonical re-upload required.
Save -> (founder approves text) -> commit the two continuity files only -> re-upload the pair
to the Project (one-way sync).
