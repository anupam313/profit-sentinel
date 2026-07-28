# Profit Sentinel — State — 2026-06-19 — OP-1 Close
## Session: OP-1 (returns-baseline category grouping) finalized for canonical propagation
## Status: DECISION SET LOCKED. Continuity files written. Canonical propagation NOT yet applied.

---

## NEXT SESSION — LOAD

- Load `save_protocol.md` first (INVARIANT; 149 lines verified 2026-06-19).
- Re-verify line-count handles before any edit (stale-by-turn). Session-start reference handles:
  - product_strategy.md = 1422
  - technical_architecture.md = 3818  *(authoritative upload; project mount was a stale 3815)*
  - agent_d_build_spec.md = 2710
  - cross_alert_orchestration.md = 840
  - d1_validation_gates.md = 386
  - pre_agent_build_checklist.md = 389
  - save_protocol.md = 149
  - pilot_scope.md = 122
- OP-1 design is LOCKED below. The remaining work is **propagation through the save protocol**, then the **C8 edit as a separate pass**.

---

## WHAT HAPPENED THIS SESSION (one-paragraph)

Resolved the Shopify Admin API access path after the Jan-1-2026 legacy-custom-app deprecation (Path A — the partner-pre-transfer legacy button — still worked on the dev store, yielding a permanent `read_products` token). Ran a GraphQL probe that **confirmed `Product.category` resolves on API 2026-04** and returns the Standard Taxonomy path; measured coverage on the (generic) test store at **5/43 genuine paths, 26 `Uncategorized`, rest NULL** — directional only, not a real-fashion-brand fill rate. Confirmed via introspection that Shopify's **UI category suggestion is not API-fetchable** (the `Product` type exposes exactly one taxonomy field, `category`, returning the `na` sentinel until accepted). Updated the synthetic seed to mirror production shape (**54 categorized / 71 NULL**, real rows provably untouched). Finalized the OP-1 decision set, including two progressive corrections to the Phase-2 framing that culminated in **revised #18**.

---

## OP-1 — LOCKED DECISION SET

**Grouping basis**
1. ONE shared semantic grouping for D1 (margin) + returns (C3/C6/C8/C2). No parallel mechanism.
2. Grouping is **semantic** (what the product *is*) — never formed from return behaviour or return-rate similarity. `AL-25` rate-spread **retired**; return-rate-coherence validator **rejected** (Pareto inside a genuine category ≠ incoherence).
3. Vocabulary = **Shopify Standard Product Taxonomy** (snap to existing nodes).

**Category source priority (per SKU)**
4. **Step 0 (primary):** Shopify-assigned `category`, landed via a **GraphQL post-sync enrichment** writing `category_id` + `category_full_name`. (Airbyte Shopify connector v3.5.0 — latest — CANNOT carry the taxonomy node; verified. The enrichment is the durable mechanism, not an Airbyte config change.)
5. **Unassigned** = `category_id = 'gid://shopify/TaxonomyCategory/na'` OR `category_full_name IS NULL` (gid sentinel, not the localizable "Uncategorized" string).
6. **Fallback:** LLM classification **snapped to a Standard Taxonomy node** (no free-text / invented names).
7. **Shopify UI category suggestion: evaluated and REJECTED** — UI-only, not API-fetchable (introspection: `Product` exposes only `category`). LLM fallback is functionally equivalent. Recorded so it is not re-litigated.

**Classification signals (reliability-tiered, NOT equal-vote)**
8. description (**strong; newly added**) > categorical tags / collections (promo-filtered) > title, product_type (weak). **Vendor dropped** for single-brand DTC (`COUNT(DISTINCT vendor) ≈ 1 → drop`).
9. product_type = weak/low-agreement fallback input only, never a trusted key. Collections = only if verified categorical; never display-default; never a grouping key.
10. Weights / qualification = **registered calibrated dials (AL-27/28)**, not hardcoded constants.

**Validation & confidence (no calibrated threshold)**
11. Grouping confidence = **semantic cross-signal agreement** among qualified signals — NOT return-rate coherence. **AL-19 governs firing reliability, NOT grouping** (distinct concerns; conflation is a documented past error).
12. **0.70 threshold ELIMINATED.** Tag at the **deepest taxonomy level where qualified signals concur** (depth = confidence). Principle locked; the node-mapping algorithm is an unbuilt build detail.

**Degradation (two axes)**
13. **GROUP** at the finest semantically-confident level.
14. **FIRE** at the finest level where AL-19 passes; roll up only for volume, **carrying the AL-3/AL-29 concentration down-drill** (so a hot SKU is not masked); brand-level-with-disclosure = floor; AL-22 watch/no-fire for genuinely thin/new.

**Display & storage**
15. Display label = taxonomy-node label + optional **non-blocking founder rename** (display-only).
16. Persisted columns: `founder_category`, `category_source`, `ai_inferred_category`, `category_inference_confidence`, plus `category_id`, `category_full_name` (+ source taxonomy path / level).

**Scope (REVISED #18 — supersedes 2026-06-02 deferral at product_strategy.md:1342)**
17. **Sub-category depth is dynamic, NOT Phase-2-deferred.** Because we snap to Shopify's published, cross-merchant-validated taxonomy, fine nodes are valid and available now — we do not invent or validate a taxonomy from one brand. Tag as deep as Shopify's nodes + qualified signals confidently support (merchant-assigned depth is free via Step 0; LLM-assigned depth self-limits via the deepest-agreement rule); fire as deep as AL-19 permits. **New-category naming is not "deferred" — it is simply not done** (always map to existing nodes). The **only** genuine cross-client (Phase-2) item is improving LLM **assignment accuracy** at depth — an enhancement, not a blocker. The 2026-06-02 "single-brand data cannot validate a fine sub-category taxonomy" rationale was specific to the **retired self-clustering** approach and is dissolved by snap-to-taxonomy. Honesty caveat: this unblocks deep **tagging**, not deep **alerting** (per-brand volume still gates firing depth via AL-19).

**Cross-alert**
18. The D1-G3 rework touches **D1 (margin) too** — log the cross-alert reconciliation.

---

## VERIFIED FACTS (this session)

- `Product.category` → `TaxonomyCategory { id, fullName, name, level, isLeaf }`, resolves on **API 2026-04** on the real test store. `fullName` = breadcrumb path.
- Unassigned sentinel = `gid://shopify/TaxonomyCategory/na` (`fullName` "Uncategorized").
- UI category suggestion is **NOT** exposed by the Admin API (`Product` type: 60 fields, only `category` matches `suggest|recommend|categor|taxonom`).
- Airbyte Shopify connector v3.5.0 (latest) does not carry the taxonomy node — GraphQL enrichment is the durable fix.
- Jan-1-2026: new legacy custom apps disabled in admin; Dev Dashboard / CLI is the path. Path A (partner pre-transfer) still worked here → permanent `read_products` token. **Pilot implication:** real-brand onboarding needs a public app + OAuth + Shopify review (lead time) — start the Shopify-app track now.
- Synthetic seed now: **54 categorized / 71 NULL** (43%), real rows untouched (fingerprint `eaf8b51147bd`). type→node map baked into `seed_shopify.py`; independent `Random(product_id)` (global `PY_RNG(42)` untouched). No `na` sentinel written to synthetic rows (cleanly categorized-or-NULL).

---

## PHASE-0 DECISION LEDGER (drives the Check-4 retired-scan and Check-8 mirror lists)

> Exact retired-wording strings and line ranges to be CONFIRMED against the real files when building the Claude Code change-specs (mount may be stale; ranges drift).

| # | Decision (plain) | Target file(s) | Mirrors | Retires (wording to scan) |
|---|---|---|---|---|
| 1 | One shared semantic grouping (D1+returns) | cross_alert_orchestration; pre_agent_build_checklist | cross_alert + checklist + agent_d | — |
| 2 | Grouping semantic, not behaviour-based | technical_architecture; agent_d_build_spec; d1_validation_gates | tech-arch + agent_d + d1_gates | "AL-25" rate-spread; return-rate-coherence validator |
| 3 | Vocabulary = Shopify Standard Taxonomy | technical_architecture; agent_d_build_spec | — | — |
| 4 | Step 0 = Shopify category via GraphQL enrichment | technical_architecture; source_schema_registry; agent_d_build_spec | tech-arch + registry + agent_d | "Airbyte carries category" (if asserted anywhere) |
| 5 | Unassigned = na-gid OR NULL | technical_architecture; source_schema_registry; agent_d_build_spec | tech-arch + registry + agent_d | "Uncategorized"-string normalization (do not introduce) |
| 6 | Fallback = LLM snapped to taxonomy node | agent_d_build_spec; technical_architecture | agent_d + tech-arch | free-text/invented category names |
| 7 | Shopify UI suggestion rejected (UI-only) | technical_architecture (note) | — | — |
| 8 | Signals reliability-tiered; +description; −vendor | agent_d_build_spec | — | equal-vote weighting; vendor-as-signal |
| 9 | product_type weak only; collections not a key | agent_d_build_spec | — | product_type-as-key; collections-as-default |
| 10 | Weights = AL-27/28 dials, not hardcoded | agent_d_build_spec (+ AL registry) | — | any hardcoded weight constant |
| 11 | Grouping confidence = semantic agreement; AL-19 = firing gate only | agent_d_build_spec; d1_validation_gates; technical_architecture | agent_d + d1_gates + tech-arch | return-rate-coherence as grouping confidence; AL-19/grouping conflation |
| 12 | 0.70 eliminated → deepest-agreement | agent_d_build_spec (~1979) | — | "0.70" provisional threshold |
| 13 | Group at finest semantically-confident level | agent_d_build_spec; technical_architecture | agent_d + tech-arch | — |
| 14 | Fire at finest AL-19-passing level; roll up + AL-3/AL-29 down-drill; brand floor; AL-22 thin | d1_validation_gates; cross_alert_orchestration; agent_d_build_spec | d1_gates + cross_alert + agent_d | — |
| 15 | Display label + non-blocking founder rename | product_strategy (founder-facing); technical_architecture (storage) | product_strategy + tech-arch | rename-as-blocking-gate (if asserted) |
| 16 | Persisted columns (6) + taxonomy path/level | source_schema_registry; technical_architecture | registry + tech-arch | — |
| 17 (#18) | Sub-category depth dynamic; supersede 2026-06-02 deferral | product_strategy:1342 (MANUAL); technical_architecture (if mirrored) | product_strategy + tech-arch | 2026-06-02 "DEFERRED to Phase 2 ... sub-category depth ... single-brand cannot validate a fine sub-category taxonomy" → mark superseded, keep as historical |
| 18 (#19) | D1-G3 rework knock-on to D1 | d1_validation_gates; cross_alert_orchestration | d1_gates + cross_alert | D1-G3 return-rate test |
| — | pre_agent_build_checklist:365 "clustering-certified granularity" | pre_agent_build_checklist | — | "clustering-certified" (decide reword vs historical) |

**Routed / deferred (Check-11 landing targets):**
- 80MB gitignored taxonomy file durability (trimmed-subset-committed vs load-from-source) → **open item, this state file** (+ tech-arch noted dependency-debt). NOT resolved this pass.
- Deepest-agreement node-mapping algorithm = **unbuilt**; principle locked → open build item, this state file.
- **C8 edit** (causal_graph.py +C8 entry; pilot_scope.md "58"→"59"; product_strategy count reconciliation) → **separate save-protocol pass AFTER OP-1**. Do not merge.
- Deferred roster-count fixes (tech-arch:1348; cross_alert:11/38/643; checklist:111/229/21) → **remain deferred**; scoped diff must exclude them even though tech-arch/cross_alert are edited for OP-1.

---

## EXECUTION SPLIT

- **Claude Code (repo edits + mechanical checks 1,3,4,6,7,9):** technical_architecture.md, agent_d_build_spec.md, d1_validation_gates.md, cross_alert_orchestration.md, source_schema_registry; likely pre_agent_build_checklist.md.
- **Manual (founder):** product_strategy.md — the 1342 supersession (#18) + founder-facing display-label/rename (#15). Upload for semantic read-back.
- **Chat (Claude — checks 8,10,11 + Phase 0):** the ledger above; semantic read-back; mirror + routing reconciliation.

---

## OPEN ITEMS

- Persistent paid Supabase + keep-alive before pilot onboarding (dev was paused/restored; data regenerable).
- Long-lead parallel tracks per pilot_scope: Shopify public-app + OAuth + review; entity registration (Google Ads token/DPAs); Google Ads developer token.
- 80MB taxonomy durability decision (above).
- Deepest-agreement algorithm build (above).
- Recruitment-outreach-timing debate (PARKED; founder's "build first" vs pilot_scope:121-122 "recruitment is the binding constraint").

---

## NEXT ACTIONS (in order)
1. Build the Claude Code save-protocol prompt + exact change-specs from the real file content (confirm ranges + retired strings).
2. Claude Code applies the 5 repo edits; runs Phase B mechanical checks; reports PASS/FAIL + fresh handles.
3. Founder edits product_strategy.md manually; uploads; Claude semantic read-back.
4. C8 edit as its own save-protocol pass.
