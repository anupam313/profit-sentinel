# Profit Sentinel — State — 2026-06-19 — OP-1 Close
## Session: OP-1 (returns-baseline category grouping) — CANONICAL EDITS COMPLETE + SIGNED OFF
## Status: All 6 canonical edits landed & verified. PENDING: scoped commit (uncommitted in master working tree). Handle refresh = DONE (this file).

---

## NEXT SESSION — LOAD
- Load `save_protocol.md` first (INVARIANT; 149 lines).
- Re-verify line-count handles before any edit (post-OP-1 expected counts; re-verify at session start, treat a mismatch as a real signal):
  - product_strategy.md = **1424**   (was 1422; +2, OP-1 supersession note)
  - technical_architecture.md = **3827**  (was 3818; +9)
  - agent_d_build_spec.md = **2722**  (was 2710; +12)
  - cross_alert_orchestration.md = **847**  (was 840; +7)
  - d1_validation_gates.md = **399**  (was 386; +13)
  - pre_agent_build_checklist.md = **389**  (unchanged; within-line edits)
  - save_protocol.md = **149**  (untouched)
  - pilot_scope.md = **122**  (untouched)
- **NEXT CHAT STARTS HERE → the TAXONOMY REFRESH + VERSIONING open item (below).**

---

## WHAT HAPPENED (one paragraph)
Resolved the Shopify Admin API access path post-Jan-2026 legacy-app deprecation (Path A still worked → permanent read_products token). Probe CONFIRMED `Product.category` on API 2026-04 (na-gid sentinel; UI suggestion NOT API-fetchable). Updated the synthetic seed to mirror production shape (54 categorized / 71 NULL). Finalized the OP-1 decision set incl. revised #18 (sub-category depth dynamic, not Phase-2-deferred). Then propagated the decisions through the save protocol, ONE FILE AT A TIME with byte-exact verification: d1_validation_gates, agent_d_build_spec, technical_architecture, cross_alert_orchestration, pre_agent_build_checklist (incl. a missed-then-caught D-28 schema mirror), product_strategy. Confirmed `source_schema_registry` needs NO edit (runtime auto-populated table, not a design dictionary). All clean; uncommitted in the master working tree.

---

## OP-1 — LOCKED DECISION SET
1. ONE shared SEMANTIC grouping for D1 + returns (C3/C6/C8/C2). No parallel mechanism.
2. Grouping is SEMANTIC (what the product IS), never from return behaviour/rate similarity. AL-25 rate-spread retired; return-rate-coherence validator rejected.
3. Vocabulary = Shopify Standard Product Taxonomy (snap to existing nodes).
4. Step 0 (primary): Shopify-assigned `category` via GraphQL post-sync enrichment → category_id + category_full_name. (Airbyte connector v3.5.0 cannot carry it — verified.)
5. Unassigned = category_id = 'gid://shopify/TaxonomyCategory/na' OR category_full_name IS NULL.
6. Fallback: LLM classification snapped to a taxonomy node (no free-text/invented names).
7. Shopify UI suggestion: evaluated & REJECTED — UI-only, not API-fetchable. LLM fallback is functionally equivalent.
8. Signals reliability-tiered (NOT equal-vote): description (STRONG; added) > categorical tags/collections (promo-filtered) > title, product_type (weak). VENDOR dropped (single-brand DTC).
9. product_type = weak fallback input only. Collections = display label only if verified categorical; never a grouping key, never default.
10. Weights/qualification = registered calibrated dials (AL-27/28), not hardcoded.
11. Grouping confidence = semantic cross-signal AGREEMENT. AL-19 governs FIRING reliability, NOT grouping.
12. 0.70 threshold ELIMINATED → tag at the DEEPEST taxonomy level where qualified signals concur (depth = confidence).
13. GROUP at the finest semantically-confident level.
14. FIRE at the finest level where AL-19 passes; roll up for volume CARRYING the AL-3/AL-29 concentration down-drill; brand-level-with-disclosure = never-silent floor; AL-22 watch for thin/new.
15. Display label = taxonomy-node label + optional non-blocking founder rename (display-only).
16. Persisted columns: founder_category, category_source, ai_inferred_category, category_inference_confidence, + category_id, category_full_name (resolved node, on sku_cost_master).
17. category_source values: shopify_assigned / ai_inferred / manual; default 'shopify_assigned'.
18. (REVISED, supersedes 2026-06-02 deferral) Sub-category depth is DYNAMIC, not Phase-2-deferred — snap to Shopify's cross-merchant-validated taxonomy, so single-brand data need not validate a fine taxonomy. Tag as deep as signals confidently support; fire as deep as AL-19 permits. New-category NAMING is not done (always map to existing nodes). Only cross-client assignment-ACCURACY is a Phase-2 enhancement. Unblocks deep TAGGING, not deep ALERTING.

---

## VERIFIED FACTS
- Product.category → TaxonomyCategory{id, fullName, name, level, isLeaf}; API 2026-04; fullName = breadcrumb.
- Unassigned sentinel = gid://shopify/TaxonomyCategory/na.
- UI category suggestion NOT exposed by Admin API (Product type: only `category` matches).
- Airbyte Shopify connector v3.5.0 (latest) does not carry the taxonomy node → GraphQL enrichment is the durable fix.
- Synthetic seed: 54 categorized / 71 NULL (43%); real rows untouched; gids baked in seed_shopify.py; independent Random(product_id).
- Two-table split (verified via read-path): shopify_products = RAW Shopify-assigned category (Step-0 input, from enrichment); sku_cost_master = RESOLVED grouping node (all grouping reads here; 4 sibling columns + roll-up grain already there). No mart joins shopify_products for category.
- `source_schema_registry` = a PostgreSQL table (public schema), NOT a file. Runtime cast-manifest auto-populated by schema_discovery.py after each Airbyte sync (reads information_schema). Scope = Airbyte SOURCE tables only.

---

## CANONICAL EDITS LANDED & SIGNED OFF (this session)
| File | → handle | What changed |
|---|---|---|
| d1_validation_gates.md | 399 | D1-G3 rewritten: semantic grouping + AL-19 firing depth (retired return-rate-coherence basis + binary verdict); :206 "clustering-certified" → "semantically-confident taxonomy level". |
| agent_d_build_spec.md | 2722 | sku_cost_master schema block + category_inference.py spec rewritten: Step 0 + snap, +description −vendor, 0.70→deepest-agreement, category_source default 'shopify_assigned', continuous. |
| technical_architecture.md | 3827 | Mirror of agent_d (schema block + python spec) + CLUSTERING-QUALITY GATE section renamed/rewritten → "CATEGORY GROUPING + FIRING-DEPTH GATE". Header changelog (L6) left as history. |
| cross_alert_orchestration.md | 847 | Additive forward-note after the C3 reconcile: pointer to D1-G3/the renamed gate; "category" in the SKU→style→category grain = resolved taxonomy node. C3 reconcile stays OPEN for the C-series review. |
| pre_agent_build_checklist.md | 389 | D-29 + D-GAP6-3 rewritten (semantic + AL-19; gate reference renamed); D-GAP6-11 "clustering-certified"→"semantically-confident taxonomy level"; **D-28** schema mirror realigned (was missed then caught: +category_id/full_name, drop vendor, default shopify_assigned, retire 0.70, DDL pointer fixed). |
| product_strategy.md | 1424 | Append-only supersession note after the 2026-06-02 entry (L1342): #18 revised; clustering-quality/return-rate basis retired; points to D1-G3 + the renamed gate. Original text retained as history. |

**source_schema_registry — NO EDIT (decisions #4/#5/#16 re-routed):** it's a runtime auto-populated cast-manifest for Airbyte SOURCE columns. sku_cost_master is an app table (out of registry scope); the resolved columns live in tech-arch's ALTERED TABLE block (done); the na-gid rule is interpretation logic in the category_inference.py spec, not a cast manifest entry. The raw category_id/full_name on shopify_products will AUTO-register via schema_discovery when the enrichment creates them at build time.

**Safety grep (repo-wide) clean:** every surviving `default 'collection'` / `0.70 provisional` / `category_granularity_floor` hit is an OP-1 retirement note, the do-not-touch tech-arch header changelog, or immutable docs/sessions history. No live stale schema mirror survives.

---

## OPEN ITEMS

### >>> TAXONOMY REFRESH + VERSIONING — UNDESIGNED — NEXT CHAT STARTS HERE <<<
Shopify's Standard Product Taxonomy is a versioned, updated upstream (2026-05 release; 2026-02 added return-reason mappings). Two dependents: the LLM-snap fallback (needs the current node list) and the gids baked into seed_shopify.py.
- **RISK:** taxonomy releases can re-id / merge / split / retire nodes → a resolved or baked gid can later point to a renamed/moved/deleted node. Category data therefore has a VERSION dimension ("SKU = aa-1-4" only means something "as of release X").
- **PRE-REQ (do FIRST next chat):** VERIFY Shopify's gid / node-stability + re-id policy from their taxonomy release notes / changelog. This fact most shapes the design and is currently an INFERENCE, not verified.
- **CANDIDATES (none chosen):** (a) pull-on-build — always current, runtime dependency on upstream format/availability; (b) pinned-version-committed trimmed apparel subset + deliberate, tested migration on upgrade — reproducible, needs a migration step [CURRENT LEAN]; (c) regardless of a/b, store a `taxonomy_version` stamp alongside category_id so resolved nodes are interpretable/re-mappable across releases.
- SUBSUMES the earlier "80MB categories.json: trimmed-subset-committed vs load-from-source" durability item (that was WHERE the file lives; this is the larger WHEN-upstream-moves question).

### Other open items
- Deepest-agreement node-mapping algorithm = principle locked, ALGORITHM UNBUILT (the "map each signal to a node, compute deepest concurring level" mechanics).
- BUILD-TIME verification: when the GraphQL enrichment is built, confirm category_id/full_name flow shopify_products → schema_discovery (auto-register as passthrough) → python_transformer → stg_shopify_products, so Step 0 can read them. (One residual inference: schema_discovery auto-ADDS new columns rather than rejecting via allowlist — header says add; not full-code-verified.)
- C8 (HERO return-driver) edit = SEPARATE save-protocol pass AFTER OP-1: causal_graph.py +C8 entry; pilot_scope.md "58"→"59"; product_strategy count reconciliation. Do NOT merge into the OP-1 commit.
- Deferred roster-count fixes (tech-arch:1348; cross_alert:11/38/643; checklist:111/229/21) — remain deferred.
- Persistent paid Supabase + keep-alive before pilot onboarding.
- Long-lead tracks per pilot_scope: Shopify public-app + OAuth + review; entity registration; Google Ads developer token.
- O-26 full design-consistency audit + design-ownership map — still scheduled after Gap 6.
- `.claude/worktrees/sleepy-bassi-35c693` — benign: clean, 29 commits BEHIND master, strict ancestor, never edited. Cannot revert OP-1. Ignore or clean up later.

---

## COMMIT PLAN (uncommitted in master working tree — 15 modified tracked files)
SCOPED staging, NOT `git add -A`. Two logical commits:
1. Category seed + probe: connectors/seed_shopify.py, connectors/_apply_synthetic_categories.py, the probe scripts, `.gitignore`. CONFIRM the 80MB data/shopify_taxonomy/categories.json is gitignored before committing.
2. OP-1 spec close: the 6 docs above + these two continuity files (state + chat_context).
- KEEP C8 scaffolding (causal_graph.py / agent_a.py) OUT of these commits — it's the separate C8 pass.
- Commit on master or a fresh branch (worktree does not block).

---

## NEXT ACTIONS (in order)
1. Scoped commit (per plan).
2. (New chat) TAXONOMY REFRESH + VERSIONING — start with the Shopify gid-stability verification.
3. C8 edit as its own save-protocol pass.
