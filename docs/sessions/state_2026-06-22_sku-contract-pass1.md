# Profit Sentinel — State — 2026-06-22 — SKU-Namespace Contract (Pass One committed)
## Session: SKU-namespace contract realignment — conform built, re-seeded, COMMITTED (8a707a1)
## Status: PASS ONE COMMITTED (not pushed). Pass Two (assertion) is the next item.

---

## NEXT SESSION — LOAD
- Load save_protocol.md FIRST (authoritative; 149 lines).
- Re-verify canonical line-count handles AGAINST REPO HEAD before any design/edit work.
  The Project mount has been proven stale repeatedly — HEAD is source of truth.
  Expected @ HEAD (8a707a1), all verified live this session:
    product_strategy 1424 · technical_architecture 3929 · agent_d_build_spec 2722 ·
    cross_alert_orchestration 847 · d1_validation_gates 399 · pre_agent_build_checklist 389 ·
    save_protocol 149 · pilot_scope 122.
  Treat any mismatch as a real signal.
- Canonical files live under docs/ in the repo.
- MOUNT REFRESH DONE THIS UPLOAD: product_strategy.md (was 1422) + technical_architecture.md
  (was 3815) re-uploaded to HEAD versions. If a future mount check shows the old numbers, the
  re-upload did not take.
- Deliberation mode: tag load-bearing claims [verified—file:line] / [inference] / [guess];
  verify THIS turn in Claude Code, never from memory or the mount; one item at a time with
  sign-off; design here, build in Claude Code (read-only mount; no repo/DB/git from chat).

---

## ENTERING STATE — what is DONE and COMMITTED
- Pass One (SKU-namespace conform) COMMITTED — 8a707a1 (on master, AHEAD of origin, NOT pushed;
  sits on ae8a2d5 + b8fec19, both also local-only). 2 files, +269/−47.
  - connectors/seed_sku_cost_master.py (NEW, sole owner of sku_cost_master, both record_types):
    reads the catalog (shopify_product_variants, the 125 AZ- style SKUs) via load_canonical_skus()
    as its cost universe -> cost can never drift from the catalog SKU contract. One sku_cogs row
    PER STYLE (125), price-derived (supplier_cost = price/1.28/uniform(2.2,3.0); landed_cost =
    supplier_cost*1.28), landed_cost_source='derived', effective_to=NULL. No hero/STD tier.
    Category columns NOT written here. validate() asserts 125 sku_cogs / 125 active / 0 orphans /
    0 uncovered. Docstring rewritten to match (old one described the retired AZR-/428/hero design).
  - connectors/seed_shopify.py (M, −47/+3): BOTH sku_cost_master writers removed (sku_cogs +
    gifting); products/variants/orders/SKU_TO_VARIANTS untouched.
- Live DB re-seeded: 133 rows (125 sku_cogs + 8 gifting). 54 cost rows now resolve to a real
  category (grouping_key == category_id), UP FROM 0/428 — the two-universe mismatch is fixed.
  71 sit at brand_level_floor (see below — by design, NOT a defect).
- B-8 (sku_cost_master reseed) functionally complete at the new counts.

## WHY 71 FLOOR IS NOT A DEFECT (verified — do not "fix" by raising coverage)
- The synthetic catalog's 54-categorized / 71-NULL split is DELIBERATE — set during OP-1 to
  mirror production shape (real Shopify stores carry Step-0 on only a minority of products).
  [verified — state_2026-06-19_op1-close.md]
- Production model: Step-0 = cheap win for the minority; the LLM-classify-and-snap fallback is
  THE WORKHORSE for the rest; brand-level floor = genuine residual only.
- The 71 floored ONLY because the LLM snap has NEVER been run (--no-llm every time, including
  this session — anthropic SDK not installed in the seed env). In a production-faithful run most
  of the 71 would resolve to ai_inferred.
- DO NOT raise synthetic Step-0 coverage toward 100% — it destroys the deliberate production-
  mirror. (This option was offered then RETRACTED this session.)

## LOCKED DECISIONS THIS SESSION (do not reopen without new evidence)
1. Authoritative namespace = catalog AZ-{cat}-{NNN}; cost conforms. [verified live: 137k order
   lines + 625 variants + products all AZ-; cost the lone AZR- outlier]
2. seed_sku_cost_master.py = SOLE writer of sku_cost_master (BOTH record_types); seed_shopify.py
   stops writing it. (Dual-writer was the real root cause.)
3. Shared contract = the cost seed READS the catalog from the DB (not a new module, not a
   re-listed set) -> drift-proof by construction.
4. Per-style grain (mart uses distinct on (sku)); the catalog's 8 categories; NO hero tier.
5. Price-derived cost (ported from seed_shopify L719); landed_cost_source='derived' for all (the
   75/25 finaloop/derived split dropped — no fired-set alert reads provenance).
6. shopify_variant_id = real representative SKU_TO_VARIANTS[sku][0].id (NOT NULL; not a join key
   — the mart joins on sku). Single active row per style; cost history flattened.
7. Mart join key is sku (string), NOT shopify_variant_id. [verified — mart_return_rate_by_sku.sql:54]

## NEXT ITEMS (ordered)
1. PASS TWO — the assertion (the contract guard, separate save-protocol pass): a re-runnable
   build-time check — every distinct order_line_items.sku (trimmed) in the catalog set; every
   record_type='sku_cogs' row's sku in the catalog set; ZERO sku_cogs floors-for-lack-of-cost;
   reject whitespace/control-char SKUs (catches the AD-04 class); influencer_gifting_package
   EXEMPT. Restores sku_cost_coverage_by_revenue (D1's >=0.85 gate). NOTE: "0 floors" here means
   0 floors FOR LACK OF A COST ROW — distinct from the category-floor of 71 (the LLM-not-run
   state, a different axis).
2. LLM / fan-out pass (pilot-readiness gate, NOT deferrable fidelity): the LLM-snap is the
   production WORKHORSE and has never run. OPENS by READING category_inference.py's LLM-snap code
   to confirm it is BUILT (not a stub) before switching it on. Bundles R8 (fan-out fix) — must
   precede the LLM run or it's 5x the calls. Proves the workhorse end-to-end on synthetic data
   before a real brand's catalog hits it.
3. Marts/D1 rebind category_id -> category_grouping_key. The rebind gate (cost reaches a
   category) is now CLEARED on the 54 placed rows. Verify on production-faithful data after the
   LLM pass. WATCH the fan-out CLASS hazard: per-style sku x per-size variant joins fan out 5x —
   any rebind join touching variants can hit it.
4. C8 (HERO return-driver) edit — still pending, separate save-protocol pass.

## ROUTING LEDGER (Check-11 — recorded so nothing evaporates)
- R1 assertion -> Pass Two (item 1 above).
- R2 top_sku_inventory_pct re-enable @ mart_causal_chain_daily.sql:506 -> later mart edit (a
  documented payoff: cost is now AZ-, so it can re-enable).
- R3 label->SKU bridge (B-4 semantic labels in loop/gorgias/meta/tiktok) -> OUT of scope;
  CONFIRMED off the rebind critical path (label<->label in one mart; no category aggregation
  routes through it). Only needed if attributing the promotion/return label signal back to
  cost/category. Entangled with C8/hero.
- R4 effective-dated cost history -> deliberate later pass IF a margin-compression-over-cost-
  trend signal is built.
- R5 AD-04 \n -OS-blue SKU newline -> transform/staging trim (python_transformer.py), NOT a seed
  fix (it's a real synced product, no seed origin). Never reaches order lines, so not load-
  bearing for Pass One/Two.
- R6 a REAL Adidas product (id 7698713116768) sitting in the synthetic schema -> horizon
  doc-vs-DB hygiene sweep (data contamination).
- R7 B-8 / tech-arch staleness: pre_agent_build_checklist.md:207 (B-8 "428 rows") and the
  tech-arch reseed annotation (~L1297, "428 / 380 active / FW25 step-change") are now stale
  (counts are 125, no hero) -> canonical doc pass once final counts settle (after LLM pass).
- R8 category_inference._READ_SQL fan-out (v.sku = scm.sku, per-style x per-size = 5x) ->
  bundled into the LLM/fan-out pass. Real bug the conform surfaced; final state idempotent.

## HORIZON / FLAGS (do not chase in the next session)
- Local-only commit stack (8a707a1 + ae8a2d5 + b8fec19) not pushed — decide push timing as ONE
  coherent set after Pass Two + LLM pass, not piecemeal.
- OneDrive corruption risk on the repo path — ongoing; stop-don't-force on lock errors.
- O-26 full design-consistency / doc-vs-DB audit — scheduled, separate cadence.

## FILES TO SAVE / UPLOAD THIS SESSION
- state_2026-06-22_sku-contract-pass1.md (this file)
- chat_context_2026-06-22_sku-contract-pass1.md (paired narrative)
- RE-UPLOAD (de-stale the mount): docs/product_strategy.md (HEAD 1424) +
  docs/technical_architecture.md (HEAD 3929) — the real repo versions.
Save -> commit the two continuity files -> re-upload all four to the Project (one-way sync).
