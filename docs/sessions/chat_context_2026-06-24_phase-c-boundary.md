# Chat Context — 2026-06-24 — Phase C boundary
## Companion to state_2026-06-24_phase-c-boundary.md
## Narrative + reasoning trail for the Phase C synthetic-boundary build.

---

## ARC OF THE SESSION

Two phases ran back-to-back: **C-0 discovery** (read-only ground truth) then **Phase C
build** (the is_synthetic real/synthetic boundary for the Shopify spine). This file is the
reasoning trail; the decisions, ledger, and handles live in the state file.

A meta-note for next session: this session's design loop repeatedly "found another miss"
because the build prompt was being finalized against canonical docs that are internally
contradictory and stale relative to the code (RULE 3 / RULE 4 / "to be created" markers). The
fix that broke the cycle was a read-only DISCOVERY pass (C-0) before any build prompt. For the
remaining phases (D/E/F), lead with discovery, not after pushback.

### 1. C-0 discovery (read-only) established the reality the build was written against
- Canonical docs all matched expected line counts exactly (zero drift) at session start.
- **DEBT-006 confirmed:** no raw `shopify_*` table has an `is_synthetic` column. Census:
  `client_azure_co` has 169 base tables — **86 WITH** is_synthetic, **83 WITHOUT**. Of the
  tables the marts read, only `meta_ad_performance`, `google_ads_performance`,
  `sku_cost_master` carry it; the Shopify spine does not.
- RULE 4 (no dbt casts) is unenforced — every stg_shopify_* casts in dbt because
  `python_transformer.py` was never built. Casts were therefore allowed for Phase C.
- `seed_shopify.py` isolates its rows per-table with id-range / regex / ANY() predicates (it is
  idempotent via DELETE-then-insert "R9"). Those predicates became the is_synthetic derivation.
- Only `mart_causal_chain_daily` read raw `shopify_*` directly (orders, inventory_levels,
  order_line_items) — and that turned out to be **uncommitted WIP**, not committed code.

### 2. The WIP gate (0b) — first founder decision
The raw shopify reads Phase C had to re-route were themselves +565 lines of uncommitted WIP
(Session-3/B-9/B-4 columns). Committed HEAD `mart_causal` had no raw shopify reads at all. So
the WIP disposition determined Step 3's whole scope. **Founder ruled: commit Group A separately
first** → checkpoint `8292b02`, isolating the Phase C diff. Group B (seed_meta.py,
onboarding_flow.py, probes, slack_bot/, docs/sessions) was consciously left undisposed (still
dirty in the working tree — see state file repo-state note; tracked as ROUTED/OWED item 6).

### 3. The Egnition island — kept as the boundary fixture (closes prior Phase B)
The prior file left "Phase B — island purge vs keep" pending. Ruled **keep through Phase C**:
the island is the only real-shaped data in the schema and is the only row that can prove the
boundary discriminates real from synthetic. Purging before the boundary existed would have
destroyed the test fixture. The gate (section below) is that proof. (Ledger L8.)

### 4. The toggle conflict (the build's pivotal finding) — second founder decision
A latent contradiction surfaced before any build:
- `public.client_config.use_synthetic_data` (the per-client table the RULE-3 filter reads) was
  **FALSE** for `client_azure_co`.
- The dbt var `use_synthetic_data` (dbt_project.yml) = **true** — what existing connector
  staging (meta/ga4/sentry) filters on.
- The dbt `client_id` var is **`'client_azure_co'`** (not `'azure_co'`), so the subquery DID
  match the row and returned FALSE.

Consequence: building at FALSE would have darked-out synthetic Shopify in the marts
(island-only) while meta/ga4 stayed synthetic → incoherent marts. The current FALSE was stale
(the seed never set it). **Founder ruled: set TRUE as steady state**, authorizing the flag
mutation; the gate would toggle both ways and land on TRUE. This is the var-form-vs-table-form
divergence now logged as a routed reconciliation item.

### 5. Build + gate
- Derived is_synthetic in 5 raw-reading stg models (predicate before any ::text cast), filtered
  with the per-client form; net_sales_validation passes it through via `bool_and` (date-grain
  aggregate, so it means "every order that day is synthetic").
- Re-routed mart_causal's three raw shopify reads to filtered staging. Only one missing column
  needed a pass-through: `discount_codes` on stg_shopify_orders. Join recast to
  `o.order_id::text = li.order_id` (stg order_id is bigint vs the line-item text cast).
- `dbt compile` clean; compiled mart confirmed to read NO raw shopify_*.
- **Gate:** staging are views (filter re-evaluates on flag-flip); marts are tables (need rebuild
  per flip). At TOGGLE-OFF: 0 synthetic survivors across all 5 stg views, island intact,
  mart_net_revenue collapsed to 1 row (the island, $40), mart_causal order_count=1. At
  TOGGLE-ON: synthetic+island, order_count 84,230. Fail-closed criteria all green.

### 6. Build notes / gotchas for next session
- **Transient Supabase pooler timeouts** hit three separate builds ("timeout expired" to
  `aws-1-us-east-1.pooler.supabase.com`). NONE were logic errors — all cleared on retry. One
  caused `stg_klaviyo_profiles` (an ancestor of mart_causal) to fail, which SKIPPED mart_causal;
  a targeted retry rebuilt it at TRUE (730 rows). If a build shows ERROR with "timeout expired",
  just retry the failed/skipped nodes — do not assume a code fault.
- mart_causal at TOGGLE-OFF still has 706 rows (ga4-driven date spine, ga4 still synthetic via
  the var-form). That is expected and is the visible signature of the var-form divergence — NOT
  a leak; Shopify contribution at OFF is island-only (order_count=1).

### 7. Docs (corrected in the Phase C commit, RULE 9 doc-sync)
- CLAUDE.md RULE 3 rewritten: the false "every source table has is_synthetic" replaced with
  two-source provenance (derive-in-staging for shopify; stored for meta/ga4/sentry/
  sku_cost_master + PS app tables), the per-client filter form, and an explicit warning against
  the connector-staging var-form (flagged pending reconciliation). Handle 187 → 214.
- tech-arch §3.3 + §7 updated for DEBT-006 + derive-in-staging + per-client toggle +
  fail-closed-on-drift note. Scope held strictly to those paragraphs. Handle 3929 → 3947.
- These two corrections were thus landed EARLY (ahead of the later canonical-corrections pass).

---

## OPEN THREADS (full detail in the state file's ROUTED/OWED section)
1. Cancelled/voided narrowing → **alert-threshold calibration check owed before pilot.**
2. var-form vs client_config-form toggle divergence → reconciliation phase.
3. loop_return_line_items raw read (no is_synthetic) → Loop-connector boundary phase.
4. stg_shopify_inventory_items island-only/unused → no action.
5. Airbyte sync-mode → founder UI confirmation; predicates assume real ids ≥1e12 / non-AZ SKUs.
6. Group B working-tree disposition → not yet ruled.

## NEXT ACTION
Pre-pilot hardening **Phase D** — constraints + dbt tests in the run path. Do not start until
directed. Do not push (8-deep unpushed stack at HEAD fe8725b).
