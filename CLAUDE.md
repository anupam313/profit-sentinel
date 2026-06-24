# Profit Sentinel — Engineering Standards for Claude Code

## PROJECT CONTEXT
Profit Sentinel is a proactive profit intelligence platform 
for Shopify fashion brands ($1M-$10M GMV). Stack: 
Supabase (PostgreSQL) + Airbyte + dbt Cloud + LangGraph 
+ Slack Bolt SDK + Next.js.

Read these two files before starting any task:
- docs/technical_architecture.md — authoritative source 
  for schema design, data flow, agent design, and the 
  nine agreed architectural changes
- docs/product_strategy.md — ICP, five alerts, onboarding 
  architecture, product vision, and connector 
  prioritisation framework (§7)

## CURRENT BUILD STATE
Check technical_architecture.md Section 10 (Build Sequence) 
to confirm which step is currently in progress before 
writing any code. Do not skip steps or build ahead of the 
current sequence.

Current schema status:
- public schema: application tables only (client_config, 
  alert_log, thread_context, source_schema_registry, 
  schema_versions, config_change_log)
- client_azure_co: Airbyte source tables + PS application 
  tables (dbt var client_schema; macro base)
- client_azure_co_staging: dbt staging models 
  (+schema: staging)
- client_azure_co_marts: dbt mart tables, incl. 
  mart_causal_chain_daily (+schema: marts)
- Schema names derive from generate_schema_name.sql: 
  base = var('client_schema'); custom schemas append 
  as {client_schema}_{custom}. No other schemas exist yet.

## RULE 1 — DISCOVERY BEFORE TRANSFORMATION
Before writing any transformation logic, staging model, 
or type cast, run this first:

```sql
-- [target_schema] is one of: client_azure_co (sources + app
-- tables), client_azure_co_staging (stg_* models), or
-- client_azure_co_marts (mart_* tables). Pick the schema the
-- table actually lives in — marts are NOT in client_azure_co.
SELECT column_name, data_type 
FROM information_schema.columns
WHERE table_schema = '[target_schema]' 
AND table_name = '[target_table]'
ORDER BY ordinal_position;

SELECT * FROM [target_schema].[target_table] LIMIT 5;
```

Never assume a column's data type. Check the 
source_schema_registry if the table has been previously 
registered. If not registered, run discovery first.

## RULE 2 — MULTI-TENANCY IS NON-NEGOTIABLE
Every SQL statement, Python query, and dbt model must 
use schema-qualified table references:

```sql
-- CORRECT
SELECT * FROM client_azure_co.shopify_orders;

-- WRONG — never use unqualified table names
SELECT * FROM shopify_orders;
```

The schema name is always `client_{brand_name}`. In dbt, 
use `{{ var('client_schema') }}` — never hardcode the 
schema name in model SQL.

Cross-client data access is a catastrophic security 
failure. Any query that could touch multiple client 
schemas must be challenged and redesigned before running.

## RULE 3 — SYNTHETIC DATA TOGGLE
NOT every source table has a stored `is_synthetic` column 
(86 of 169 client_azure_co tables do; the raw `shopify_*` 
spine does NOT — DEBT-006). Provenance comes from two places:

- Airbyte-managed Shopify sources: `is_synthetic` is DERIVED 
  in staging from the seed isolation predicates — the same 
  predicates `seed_shopify.py` uses to isolate its own rows: 
  orders / refunds `id < 1e12`; line items `order_id < 1e12`; 
  inventory_levels `NOT (inventory_item_id::text ~ '^[0-9]{13,}$')`; 
  variants `sku ~ '^AZ-[A-Z]+-[0-9]+'`; products 
  `product_type = ANY(seed categories)`; discounts 
  `code = ANY(seed codes)`.
- Stored column: manually-managed sources that have it 
  (meta_ad_performance, google_ads_performance, sku_cost_master, 
  ga4_*, sentry_*) and PS application tables (alert_log, 
  brand_event_calendar, suppression_log — seed-set).

Every staging model and query that reads source tables must 
respect the toggle using the PER-CLIENT form — filter on the 
`client_config` TABLE value, never the dbt var:

```sql
-- canonical per-client filter, applied at the staging boundary
WHERE (
  is_synthetic = false 
  OR (SELECT use_synthetic_data FROM public.client_config 
      WHERE client_id = '{{ var("client_id") }}') = true
)
```

`use_synthetic_data` lives in `public.client_config` (per-client, 
PK on `client_id`) — the source of truth. Do NOT use the 
connector-staging form `is_synthetic = {{ var('use_synthetic_data', 
true) }}`: it keys off the dbt var, not the client, and can 
expose real data on a wrong toggle. That divergence (meta/ga4/ 
sentry staging still use the var-form) is PENDING reconciliation.

Marts must NOT read raw source tables directly — they read 
filtered staging, so synthetic rows never reach a client.

Never write code that mixes synthetic and real data 
without this guard.

## RULE 4 — TYPE HANDLING — NO HARDCODED CASTS IN DBT
Casting logic lives exclusively in python_transformer.py, 
driven by source_schema_registry. dbt models receive 
pre-typed data from staging tables and contain only 
business logic (joins, aggregations, metric definitions).

If a dbt model needs a cast, that is a signal that the 
Python transformer is not handling that column correctly. 
Fix the transformer, not the dbt model.

The one exception: explicit NULL handling in dbt 
(`COALESCE`, `NULLIF`) is acceptable business logic, 
not type casting.

## RULE 5 — ERROR HANDLING STANDARD
Every function must follow this pattern:

```python
import logging
logger = logging.getLogger(__name__)

def function_name(client_id: str, ...):
    try:
        # implementation
    except SpecificException as e:
        logger.error(
            "SOURCE: [component_name] | "
            "CLIENT: %s | "
            "ERROR: %s | "
            "CONTEXT: %s",
            client_id, str(e), {relevant_context}
        )
        # Do not re-raise unless the caller needs to handle it.
        # Log and return a safe fallback or None.
        # Never silently swallow errors.
```

The SOURCE field must identify the component: 
"Airbyte Schema Sync", "Python Transformer", 
"Agent A Threshold Scan", "dbt Mart Run", etc. 
This feeds Layer 0 of the Evidence Stack.

Schema drift and type changes must be logged to 
schema_versions, not just to the console.

## RULE 6 — PRE-COMPLETION SELF-REVIEW
Before declaring any task complete, identify and address 
these three failure scenarios for the code just written:

1. NULL / MISSING DATA: What happens if a key column 
   is null, a table has zero rows, or an API returns 
   an empty response?
2. SCHEMA DRIFT: What happens if Shopify or Airbyte 
   changes a column name or type in the next sync?
3. RATE LIMITS / TIMEOUTS: What happens if an external 
   API (Meta, TikTok, GA4, Sentry) is slow or returns 
   a 429?

Guards for all three must be implemented, not just noted.

## RULE 7 — AGENT A NEVER CALLS CLAUDE API
Agent A (threshold scanning) runs on pure Python — no 
LLM calls. Threshold checks are deterministic comparisons 
against values in client_config. Claude API is called 
only by Agents B, C, and D.

If you are writing Agent A code that includes an API 
call to Claude, stop and redesign.

## RULE 8 — RLS ON ALL PUBLIC TABLES
Every table in the public schema must have Row-Level 
Security enabled and a policy applied. No exceptions.

```sql
ALTER TABLE public.alert_log ENABLE ROW LEVEL SECURITY;
-- Policy must reference client_id matching 
-- the authenticated session context
```

## RULE 9 — DOCUMENTATION SYNC
After completing any of these, update 
docs/technical_architecture.md to reflect the new state:
- A new table is created or modified
- A new connector is added or its schema changes
- A dbt model is added or its logic changes materially
- An agent's trigger condition or output changes
- A build sequence step is completed

Update the specific section, not a general changelog. 
The document must always reflect what is actually built, 
not what was planned.

## RUN PATH — SEED THEN DBT (canonical)
The pipeline is run manually (no Makefile / 
orchestrator — intentional pre-pilot).

1. Seeds — each a standalone, idempotent script 
   (key-scoped delete-then-insert). Run 
   `python connectors/seed_shopify.py`, then the 
   connector seeds (seed_meta, seed_klaviyo, 
   seed_gorgias, seed_ga4, seed_tiktok, 
   seed_loop_returns, seed_sentry, 
   seed_sku_cost_master, seed_google_ads). 
   Seed order is NOT fixed.

2. dbt — from `warehouse/`, the canonical command 
   is `dbt build` (run + test in one): 
   `cd warehouse && dbt build`. `dbt build` 
   materialises each model BEFORE testing it, so a 
   uniqueness / not_null violation fails the run. 
   Do NOT ship on `dbt run` alone — it skips tests. 
   Scope with `dbt build --select staging` while 
   iterating.

Durable raw-data integrity is enforced at TWO 
independent layers:
- dbt staging tests: unique / not_null on every 
  staging key column; composite keys via native 
  singular tests in `warehouse/tests/`.
- The seed-time gate in 
  `seed_shopify.py::validate_seed()` — runs BEFORE 
  `conn.commit()`; commit is conditional. It gates 
  ONLY on integrity seed_shopify itself OWNS 
  (Shopify spine + touchpoint + pii + 
  discount_codes presence-bands and per-key 
  uniqueness; BEC dup-excess). Cross-source / 
  not-seed-owned checks are ADVISORY (logged, never 
  roll back), so the gate is ORDER-INDEPENDENT — a 
  missing connector never rolls back good Shopify 
  data. The gate emits its rollback record in the 
  RULE 5 log format, but it is a data-integrity 
  control, not part of the RULE 5 error-handling 
  standard.

No UNIQUE constraints are added to Airbyte-managed 
raw tables (DEBT-006); the two layers above are the 
durable controls.

## FILE LOCATIONS (AUTHORITATIVE)