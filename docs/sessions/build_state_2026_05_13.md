# Profit Sentinel — Claude Code Build State
Date: 2026-05-13
Instructions: Read CLAUDE.md first, then this file, before 
writing any code. Confirm current state before beginning.

---

## Current Build Step

**Step 3 — Other sources (Meta, Klaviyo, Gorgias via Airbyte)**

Step 2 is complete. Do not re-run or modify Step 2 files 
this session unless fixing a listed debt item.

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
- No mart tables yet

---

## What Was Built This Session (Step 2 — COMPLETE)

**New tables created in public schema:**

public.source_schema_registry
- Populated: 101 rows for shopify_orders (source = shopify)
- Unique constraint on (client_id, table_name, column_name)
- RLS enabled

public.schema_versions
- 101 rows with change_type = 'new_column' (first registration)
- RLS enabled

**New files created:**

connectors/schema_discovery.py
- discover_and_update_schema(client_id, table_name, source_name, conn)
- Reads information_schema, diffs against source_schema_registry
- Detects: new columns, type changes, removed columns, 
  transformation rule changes (not just raw type changes)
- Writes all changes to schema_versions
- Batch commits every 50 columns
- Error per column is caught and logged — one bad column 
  does not abort the whole table
- Airbyte discovery: character varying normalised to text 
  before inference rules are applied

connectors/python_transformer.py
- transform_table(client_id, table_name, conn)
- Reads registry, builds dynamic typed SELECT
- First run: CREATE TABLE stg_{table} + full INSERT
- Subsequent runs: watermark-based incremental INSERT
  - Watermark column: _airbyte_extracted_at (Destinations V2)
    or _airbyte_emitted_at (Destinations V1) — checked in 
    that order from source_schema_registry
  - Watermark value: MAX(_airbyte_extracted_at) from staging
  - On missing watermark column: abort with error — 
    never silent full refresh
- Cast validation: each non-trivial expression tested on 
  LIMIT 100 sample before full INSERT; failed columns 
  fall back to raw and are logged
- Synthetic data toggle guard per RULE 3 (currently 
  inactive — is_synthetic not yet added to source tables)

**Staging table created:**

client_azure_co.stg_shopify_orders
- 101 columns, 1 row
- Row count matches client_azure_co.shopify_orders exactly

**Two-run incremental test — PASSED:**

Run 1 (first load):
  load_mode = first_load
  rows inserted = 1
  cast-fallback columns = 0

Run 2 (incremental):
  load_mode = incremental
  watermark column = _airbyte_extracted_at
  watermark value = 2026-05-13 13:42:02.927000+00:00
  rows inserted = 0 (correct — no new Airbyte sync between runs)

**Key column type verification (stg_shopify_orders):**

  total_price               → numeric       PASS
  subtotal_price            → numeric       PASS
  created_at                → timestamptz   PASS
  processed_at              → timestamptz   PASS
  total_shipping_price_set  → jsonb         PASS
  customer                  → jsonb         PASS

---

## Known Debt (do not forget before going live)

**DEBT-001 — Duties-set columns incorrectly typed**
Columns affected:
  client_azure_co.shopify_orders.current_total_duties_set
  client_azure_co.shopify_orders.original_total_duties_set
Current state: registered as cast_text_to_numeric because 
  column names contain 'total'
Correct type: jsonb (these are Shopify price-set objects, 
  same structure as total_price_set)
Fix required: add 'duties_set' to _JSONB_TEXT_PATTERNS in 
  connectors/schema_discovery.py, then re-run 
  schema_discovery.py — transformation will update from 
  cast_text_to_numeric to jsonb_extract_from_text, then 
  re-run python_transformer.py to rebuild staging
When to fix: before onboarding any client with 
  international orders or duties. Safe to leave for 
  domestic-only clients on the dev store.

**DEBT-002 — is_synthetic column not yet added**
Source tables in client_azure_co do not have the 
  is_synthetic column. The synthetic data filter in 
  python_transformer.py logs a warning and skips the 
  filter. This is expected until Step 4 runs.
Fix required: Step 4 (ALTER TABLE to add is_synthetic 
  to all source tables).
Risk: synthetic and real data could be mixed if seed 
  script is run before Step 4. Do not run seed script 
  before Step 4.

**DEBT-003 — dbt staging models point at wrong schema**
The four existing dbt staging models still reference 
  the old public schema. Do not run dbt until Step 6 
  fixes schema references.
Files:
  warehouse/models/staging/stg_shopify_orders.sql
  warehouse/models/staging/stg_shopify_refunds.sql
  warehouse/models/staging/stg_shopify_order_source_attribution.sql
  warehouse/models/staging/stg_shopify_net_sales_validation.sql
  warehouse/models/marts/mart_net_revenue_daily.sql

---

## File Locations

Project root:
C:\Users\Anupam\OneDrive\Desktop\Profit Sentinel\
profit-sentinel-product\profit-sentinel\

Files created this session:
[project root]\connectors\schema_discovery.py
[project root]\connectors\python_transformer.py

Existing files (do not modify unless noted):
[project root]\.env  (DATABASE_URL and secrets)
[project root]\CLAUDE.md  (engineering rules)
[project root]\warehouse\  (dbt project — do not touch)

---

## Step 3 Specification (next session)

Connect Meta Ads, Klaviyo, Gorgias via Airbyte into 
client_azure_co schema. Run schema_discovery.py against 
each new table set. Run python_transformer.py against 
each. Verify staging tables.

Also: design GA4, Sentry, TikTok table schemas manually 
and create those tables in client_azure_co.

See docs/technical_architecture.md Section 10 Step 3 
for the full specification.

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
- RULE 8: RLS on public tables (done)
- RULE 9: Update technical_architecture.md after each 
  step completes
