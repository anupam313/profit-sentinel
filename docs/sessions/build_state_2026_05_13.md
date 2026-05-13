# Profit Sentinel — Claude Code Build State
Date: 2026-05-13
Instructions: Read CLAUDE.md first, then this file, before 
writing any code. Confirm current state before beginning.

---

## Current Build Step

**Step 2 — Schema registry and transformer**

Files to create this session:
- connectors/schema_discovery.py
- connectors/python_transformer.py

Do not build anything outside these two files this session.

---

## What Was Built Before This Session

**Database tables (all verified working):**

public.client_config
- 135 columns
- 2 triggers: tier_limits_trigger, client_config_change_log
- Test row exists: client_id = 'client_azure_co'

public.alert_log — exists, empty
public.config_change_log — exists, 1 row (test threshold change)
public.thread_context — exists, empty

**client_azure_co schema:**
- 47 Shopify tables synced via Airbyte
- Real data from Shopify dev store
- is_synthetic column NOT YET added to any table
- No staging tables yet
- No mart tables yet

**dbt models (from previous session — need updating):**
- stg_shopify_order_source_attribution.sql — exists but 
  still pointing at old public schema, needs updating
- stg_shopify_orders.sql — same issue
- stg_shopify_refunds.sql — same issue
- stg_shopify_net_sales_validation.sql — same issue
- mart_net_revenue_daily.sql — same issue
DO NOT run dbt until schema references are fixed in Step 6.

---

## File Locations

Project root:
C:\Users\Anupam\OneDrive\Desktop\Profit Sentinel\
profit-sentinel-product\profit-sentinel\

Files to create this session:
[project root]\connectors\schema_discovery.py
[project root]\connectors\python_transformer.py

Existing files (do not modify this session):
[project root]\.env  (DATABASE_URL and secrets)
[project root]\CLAUDE.md  (engineering rules)
[project root]\warehouse\  (dbt project — do not touch)

---

## Step 2 Specification

### schema_discovery.py

Purpose: Runs after every Airbyte sync. Reads actual column 
types from information_schema. Compares to 
source_schema_registry. Detects new columns, type changes, 
removed columns. Updates registry. Writes changes to 
schema_versions.

Key function signature:
def discover_and_update_schema(client_id: str, 
                                table_name: str, 
                                conn) -> dict:

Logic:
1. Query information_schema.columns for 
   client_{client_id}.{table_name}
2. Query source_schema_registry for existing registrations
3. Diff the two — detect new, changed, removed columns
4. For new/changed: call infer_transformation() and 
   infer_target_type() to determine handling
5. Update source_schema_registry
6. Write changes to schema_versions
7. Return summary dict: {new: N, changed: N, removed: N}

Error handling per CLAUDE.md Rule 5:
- Source tag: "Airbyte Schema Discovery"
- Log schema drift to schema_versions, not just console
- If information_schema query fails: log and return None, 
  do not crash

### python_transformer.py

Purpose: Reads source_schema_registry and generates dynamic 
SELECT applying correct transformation per column. Writes 
to staging tables in client schema. Zero hardcoded casts.

Key functions:

def infer_transformation(column_name: str, 
                          data_type: str) -> str:
    # Returns one of:
    # 'none' / 'cast_text_to_numeric' / 
    # 'cast_text_to_timestamp' / 'jsonb_extract' / 
    # 'jsonb_extract_from_text'

def infer_target_type(data_type: str) -> str:
    # Maps raw postgres type to target type

def transform_table(client_id: str, 
                    table_name: str, 
                    conn) -> bool:
    # Reads registry, builds SELECT, writes to staging
    # Returns True on success, False on failure

Staging table naming convention:
client_azure_co.stg_{table_name}
e.g. client_azure_co.stg_shopify_orders

Error handling per CLAUDE.md Rule 5:
- Source tag: "Python Transformer"
- If registry has no entries for table: log warning, 
  run schema_discovery first, then retry once
- If staging write fails: log full error with table name 
  and column that caused failure

---

## Verification Steps After Step 2

Run these after both files are built and executed:

1. Confirm source_schema_registry has rows:
SELECT count(*), source_name 
FROM public.source_schema_registry
WHERE client_id = 'client_azure_co'
GROUP BY source_name;

2. Confirm staging table created:
SELECT count(*) 
FROM information_schema.tables
WHERE table_schema = 'client_azure_co'
AND table_name = 'stg_shopify_orders';

3. Confirm staging table has correct types:
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'client_azure_co'
AND table_name = 'stg_shopify_orders'
ORDER BY ordinal_position;

4. Confirm row count matches source:
SELECT 
  (SELECT count(*) FROM client_azure_co.shopify_orders) 
    as raw_count,
  (SELECT count(*) FROM client_azure_co.stg_shopify_orders) 
    as staging_count;
-- These should match exactly

5. Confirm schema_versions is empty (no drift detected 
   on first run is expected):
SELECT * FROM public.schema_versions
WHERE client_id = 'client_azure_co';

All 5 must pass before moving to Step 3.

---

## Rules Reminder (from CLAUDE.md)

- RULE 1: Run information_schema discovery before any 
  transformation logic
- RULE 2: All queries schema-qualified 
  (client_azure_co.table_name)
- RULE 3: Synthetic data toggle guard on every source query
- RULE 4: Zero casts in dbt — casting lives in 
  python_transformer.py only
- RULE 5: Structured error logging with SOURCE field
- RULE 6: Pre-completion review — NULL, schema drift, 
  rate limits
- RULE 7: Agent A never calls Claude API (not relevant 
  this session)
- RULE 8: RLS on public tables (already done)
- RULE 9: Update technical_architecture.md after Step 2 
  completes
