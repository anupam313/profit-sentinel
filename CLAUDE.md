# Profit Sentinel — Engineering Standards for Claude Code

## PROJECT CONTEXT
Profit Sentinel is a proactive profit intelligence platform 
for Shopify fashion brands ($1M-$10M GMV). Stack: 
Supabase (PostgreSQL) + Airbyte + dbt Cloud + LangGraph 
+ Slack Bolt SDK + Next.js.

Read these three files before starting any task:
- docs/technical_architecture.md — authoritative source 
  for schema design, data flow, agent design, and the 
  nine agreed architectural changes
- docs/product_strategy.md — ICP, five alerts, onboarding 
  architecture
- docs/blueprint.md — product vision and connector 
  prioritisation framework

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
Every source table has an `is_synthetic boolean` column. 
Every query and dbt model that reads from source tables 
must respect the toggle in client_config:

```sql
-- In dbt models, always filter based on config
WHERE (
  o.is_synthetic = false 
  OR (SELECT use_synthetic_data FROM public.client_config 
      WHERE client_id = '{{ var("client_id") }}') = true
)
```

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

## FILE LOCATIONS (AUTHORITATIVE)