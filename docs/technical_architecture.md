# Profit Sentinel — Technical Architecture
*Version: Post-critique redesign | Status: Pre-implementation of 9 agreed changes*

---

## 1. System Overview

Profit Sentinel is a proactive profit intelligence platform for Shopify fashion brands ($1M–$10M GMV). It monitors signals upstream of financial impact across 6 data sources, traverses a Fashion Causal Graph when a signal moves, and delivers a specific recommendation with full data proof in plain English via Slack — before the P&L is impacted.

**Data flow:**
```
Shopify / Meta / Klaviyo / Gorgias / GA4 / Sentry APIs
        ↓ (Airbyte Cloud — extract and load)
client_{brand_name} schema in Supabase (raw tables)
        ↓ (schema_discovery.py — detects types and changes)
source_schema_registry table (transformation instructions)
        ↓ (python_transformer.py — applies transformations)
staging tables in client schema (clean, typed data)
        ↓ (dbt Cloud — business logic and metrics)
mart tables (mart_net_revenue_daily, mart_cross_source_daily etc.)
        ↓ (LangGraph agents — threshold checks and RCA)
Evidence Stack alert → Slack Bolt SDK → founder's Slack
```

---

## 2. Tech Stack

| Tool | Purpose | Why chosen |
|---|---|---|
| **Supabase (PostgreSQL)** | Cloud database for all raw and transformed data | Cloud-hosted PostgreSQL with built-in RLS, real-time, and free tier. Airbyte has native connector. |
| **Airbyte Cloud** | Extract data from Shopify/Meta/Klaviyo/Gorgias APIs and load into Supabase | Pre-built connectors for all Phase 1 sources. No-code setup. Handles incremental syncs automatically. |
| **dbt Cloud** | Transform raw source tables into clean business metric tables | Dependency management, built-in testing, documentation, scheduled runs after Airbyte syncs. |
| **LangGraph** | Orchestrate the four-agent loop | Explicit graph-based control flow essential for causal graph traversal. Chosen over CrewAI. |
| **Slack Bolt SDK** | Primary interaction surface for alerts and conversations | Founder never leaves Slack. Handles push alerts, thread reasoning, NL queries, and action buttons. |
| **Next.js / Vercel** | Web frontend for configuration and audit only | Configuration (Sentinel Sensitivity), onboarding, and Alert History. Not the primary surface. |
| **Claude API** | Powers all four agents | SQL generation, causal reasoning, Evidence Stack formatting, conversational thread responses. |
| **Claude Code** | Primary development tool | Non-technical founder can direct code generation in plain English. Handles all file creation and debugging. |

---

## 3. Database Architecture

### 3.1 Multi-Tenancy Model

**Schema-per-client architecture.** Each brand gets its own Supabase schema.

```
public schema                    — Profit Sentinel application tables only
client_azure_co schema           — Azure & Co raw + staging data
client_blue_wave schema          — Blue Wave raw + staging data
client_{brand_name} schema       — Any future client
```

**Why schema-per-client over shared tables with client_id:**
- Complete data isolation — no row-level filter errors possible
- RLS policies simpler — schema-level isolation
- Performance — queries never scan other clients' data
- Security — misconfigured query cannot leak cross-client data

**Airbyte configuration per client:**
Each client gets their own Airbyte source (their Shopify credentials) and their own destination (pointing to `client_{brand_name}` schema). In production this is automated via Airbyte API.

```python
# Production automation (not yet built — manual for now)
def create_client_airbyte_connection(client_id, shopify_token):
    # 1. Create Shopify source with client credentials
    # 2. Create Postgres destination with schema=client_{client_id}
    # 3. Create connection linking source to destination
    # 4. Trigger first sync
```

### 3.2 Public Schema — Application Tables Only

Six tables live in `public`. These are Profit Sentinel's own data. Airbyte never touches this schema.

#### client_config
```sql
CREATE TABLE public.client_config (
    -- Identity
    client_id                           text primary key,
    brand_name                          text not null,
    shopify_store_url                   text not null,
    created_at                          timestamptz default now(),
    updated_at                          timestamptz default now(),

    -- Onboarding state (full resumable state in JSONB)
    -- Updated after every single step so founder can drop off and resume
    onboarding_state                    jsonb default '{
        "current_step": "not_started",
        "steps_completed": [],
        "last_active": null,
        "sync_completed": false,
        "attribution_completed": false,
        "validation_completed": false,
        "gap_resolutions": [],
        "semantic_answers": {},
        "questions_remaining": [],
        "sensitivity_configured": false,
        "slack_connected": false,
        "go_live": false
    }'::jsonb,
    onboarding_step                     text default 'not_started',
    -- values: not_started → syncing → validating →
    --         confirming → sensitivity → slack → live
    is_live                             boolean default false,
    go_live_date                        timestamptz,

    -- Connector activation flags
    -- Agents check these before firing alerts
    -- Set automatically when connector established
    shopify_connected                   boolean default false,
    meta_connected                      boolean default false,
    tiktok_connected                    boolean default false,
    klaviyo_connected                   boolean default false,
    gorgias_connected                   boolean default false,
    ga4_connected                       boolean default false,
    sentry_connected                    boolean default false,
    finaloop_connected                  boolean default false,

    -- Last sync timestamps per connector
    last_shopify_sync                   timestamptz,
    last_meta_sync                      timestamptz,
    last_tiktok_sync                    timestamptz,
    last_klaviyo_sync                   timestamptz,
    last_gorgias_sync                   timestamptz,
    last_ga4_sync                       timestamptz,
    last_sentry_sync                    timestamptz,

    -- Revenue definition (founder confirms these at onboarding)
    -- Q: "Does your revenue include shipping charges?"
    include_shipping_in_revenue         boolean default false,
    -- Q: "How do you treat gift card sales?"
    -- (only shown if gift card orders detected)
    gift_card_revenue_timing            text default 'when_sold',
    -- Q: "Should tax collected be excluded from revenue?"
    exclude_tax_from_revenue            boolean default true,
    -- Q: "Do you collect tips at checkout?"
    -- (only shown if tips detected)
    include_tips_in_revenue             boolean default false,

    -- Order scope (only asked if detected in data)
    -- Q: "We found B2B orders totalling $X. Track separately?"
    exclude_b2b_orders                  boolean default false,
    b2b_tag_values                      text[] default array['wholesale','b2b'],
    -- Q: "We found POS orders. Include in metrics?"
    include_pos_orders                  boolean default true,
    excluded_source_systems             text[] default array[]::text[],

    -- Exchange and return handling
    -- Q: "How does Shopify record exchanges?"
    exchange_handling_method            text default 'refund_plus_new_order',
    -- values: refund_plus_new_order / single_exchange / outside_shopify
    -- Q: "Count exchanges as returns in return rate?"
    count_exchanges_as_returns          boolean default false,
    -- Derived from data, founder confirms
    return_window_days                  integer default 30,
    return_window_confirmed             boolean default false,

    -- COGS and margin
    -- Set automatically based on active connector
    cogs_source                         text default 'shopify_cost_field',
    -- low / medium / high
    -- low = no cost data → suppress margin alerts
    -- medium = shopify cost field proxy
    -- high = Finaloop real landed cost
    cogs_confidence_level               text default 'low',
    shopify_cost_field_coverage_pct     numeric default 0,
    -- Q: "Include payment processing fees in cost calculations?"
    include_payment_fees_in_cogs        boolean default true,
    payment_fee_pct                     numeric default 2.9,

    -- Reporting preferences
    -- Q: "What time do you start your day?"
    morning_brief_time                  text default '08:00',
    reporting_timezone                  text default 'America/New_York',
    reporting_currency                  text default 'USD',
    fiscal_year_start_month             integer default 1,

    -- Alert suppression (controlled from Slack commands, not onboarding)
    suppress_all_alerts                 boolean default false,
    suppress_until                      timestamptz,
    suppressed_alert_types              text[] default array[]::text[],

    -- Sentinel sensitivity
    -- Q: "How sensitive should alerts be? (conservative/medium/aggressive)"
    alert_sensitivity                   text default 'medium',
    -- Thresholds auto-calculated from 90-day historical data
    -- then adjusted by alert_sensitivity level
    return_rate_threshold_pp            numeric default 3.0,
    cpm_spike_threshold_pct             numeric default 20.0,
    margin_floor_pct                    numeric default 5.0,
    ga4_funnel_drop_threshold           numeric default 8.0,
    sentry_error_threshold_pct          numeric default 2.0,
    gorgias_sentiment_threshold         numeric default 15.0,
    -- Statistical minimums — agents suppress below these
    min_order_count_for_alerts          integer default 5,
    min_sessions_for_ga4_alerts         integer default 500,
    min_tickets_for_gorgias_alerts      integer default 20,

    -- Synthetic data toggle
    -- true during testing, false when real connectors go live
    use_synthetic_data                  boolean default false
);
```

**Important:** `client_config` has a trigger (`client_config_change_log`) that automatically logs every field change to `config_change_log`. Agent A reads this table to suppress false alerts when a metric moves due to a definition change not a real business signal.

#### alert_log
```sql
CREATE TABLE public.alert_log (
    id                  bigint generated always as identity primary key,
    client_id           text not null,
    fired_at            timestamptz default now(),
    signal_type         text not null,
    signal_values       jsonb,
    confidence_score    numeric,
    projected_impact    numeric,
    alert_message       text,
    evidence_stack      jsonb,
    action_taken        text,          -- approve / snooze / dismiss
    action_taken_at     timestamptz,
    outcome_metric      text,
    outcome_value_7d    numeric,       -- filled by scheduled dbt model 7 days later
    outcome_value_14d   numeric,       -- filled 14 days later
    outcome_checked_at  timestamptz,
    is_false_positive   boolean,
    suppressed          boolean default false,
    suppression_reason  text
);
```

#### thread_context
```sql
CREATE TABLE public.thread_context (
    id              bigint generated always as identity primary key,
    client_id       text not null,
    slack_thread_ts text not null,
    slack_channel   text not null,
    created_at      timestamptz default now(),
    updated_at      timestamptz default now(),
    context         jsonb,             -- full Evidence Stack payload
    alert_log_id    bigint references public.alert_log(id)
);
```

#### source_schema_registry
```sql
-- Stores actual column types and transformation instructions
-- Populated by schema_discovery.py after every Airbyte sync
-- Python transformer reads this to apply correct transformations
CREATE TABLE public.source_schema_registry (
    id                  bigint generated always as identity primary key,
    client_id           text not null,
    source_name         text not null,    -- 'shopify', 'meta', 'ga4'
    table_name          text not null,
    column_name         text not null,
    raw_data_type       text not null,    -- actual type from information_schema
    target_data_type    text not null,    -- what we want after transformation
    transformation      text not null,    -- 'none' / 'cast_text_to_numeric' /
                                          -- 'cast_text_to_timestamp' /
                                          -- 'jsonb_extract' /
                                          -- 'jsonb_extract_from_text'
    json_path           text,             -- for jsonb extractions
    default_value       text,             -- coalesce fallback
    is_nullable         boolean default true,
    is_removed          boolean default false,  -- column removed in new API version
    last_validated      timestamptz default now(),
    unique(client_id, table_name, column_name)
);
```

#### schema_versions
```sql
-- Written by schema_discovery.py when a column type changes
-- Agent A reads this to suppress false alerts during schema transitions
CREATE TABLE public.schema_versions (
    id              bigint generated always as identity primary key,
    client_id       text not null,
    table_name      text not null,
    column_name     text not null,
    old_type        text,
    new_type        text,
    change_type     text not null,    -- 'new_column' / 'type_changed' / 'column_removed'
    detected_at     timestamptz default now(),
    is_resolved     boolean default false,
    resolved_at     timestamptz
);
```

#### config_change_log
```sql
-- Auto-populated by trigger on client_config
-- Agent A reads this to suppress false alerts when definition changed
CREATE TABLE public.config_change_log (
    id              bigint generated always as identity primary key,
    client_id       text not null,
    changed_at      timestamptz default now(),
    field_name      text not null,
    old_value       text,
    new_value       text,
    changed_by      text,
    reason          text
);
```

### 3.3 Client Schema — Raw Source Tables

Tables created automatically by Airbyte. Schema name: `client_{brand_name}`.

All source tables have one additional column added after Airbyte creates them:
```sql
ALTER TABLE client_azure_co.shopify_orders
ADD COLUMN is_synthetic boolean default false;
```

`is_synthetic = true` for seed script data. `is_synthetic = false` (or null) for real Airbyte data. Toggle via `use_synthetic_data` in `client_config`.

**Shopify tables (created by Airbyte — ~50 tables):**
```
shopify_orders                    shopify_order_refunds
shopify_order_line_items          shopify_products
shopify_product_variants          shopify_customers
shopify_inventory_levels          shopify_inventory_items
shopify_fulfillments              shopify_discount_codes
shopify_metafield_orders          shopify_metafield_products
... (all with shopify_ prefix)
```

**Other source tables (created manually, connectors built later):**
```
meta_ad_performance               meta_campaigns
meta_ad_sets                      tiktok_ad_performance
klaviyo_campaigns                 klaviyo_flows_daily
klaviyo_subscribers               gorgias_tickets
ga4_sessions_daily                ga4_funnel_daily
sentry_errors_daily
```

---

## 4. Data Flow — Step by Step

### Step 1: Airbyte Sync
Airbyte pulls from Shopify API every 6 hours using incremental sync. Creates/updates raw tables in `client_{brand_name}` schema. New columns get propagated automatically (schema propagation setting: "Propagate field changes only").

### Step 2: Schema Discovery
`connectors/schema_discovery.py` runs post-sync. Queries `information_schema.columns` for the raw table. Compares to `source_schema_registry`. Detects new columns, type changes, removed columns. Updates registry. Writes changes to `schema_versions`.

**Watermark column:** Airbyte Destinations V2 renamed `_airbyte_emitted_at` to `_airbyte_extracted_at`. `python_transformer.py` checks V2 name first, V1 as fallback.

```python
def discover_and_update_schema(client_id, table_name, conn):
    # Read actual schema from information_schema
    current_schema = query_information_schema(client_id, table_name)
    # Read what was registered before
    registered_schema = query_registry(client_id, table_name)
    # Detect changes
    changes = diff_schemas(current_schema, registered_schema)
    # Update registry and schema_versions
    apply_changes(changes, client_id, table_name)
```

### Step 3: Type Inference
Two functions determine the correct transformation for each column:

```python
def infer_transformation(column_name, data_type):
    if data_type in ('jsonb', 'json'):
        return 'jsonb_extract'
    if any(p in column_name for p in ['price_set', 'money', 'client_details']):
        return 'jsonb_extract_from_text'
    if data_type == 'text' and any(p in column_name for p in
        ['price', 'amount', 'total', 'discount', 'tax', 'shipping']):
        return 'cast_text_to_numeric'
    if data_type == 'text' and any(p in column_name for p in
        ['_at', '_date', 'date', 'time']):
        return 'cast_text_to_timestamp'
    return 'none'

def infer_target_type(data_type):
    mapping = {
        'text': 'text', 'bigint': 'bigint',
        'numeric': 'numeric', 'boolean': 'boolean',
        'jsonb': 'jsonb', 'json': 'jsonb',
        'timestamp with time zone': 'timestamptz',
    }
    return mapping.get(data_type, 'text')
```

### Step 4: Python Transformer
`connectors/python_transformer.py` reads the registry and generates a dynamic SELECT statement applying the correct transformation per column. Writes to staging tables in the client schema. No hardcoded casting logic anywhere.

**Incremental load pattern:** on first run, creates staging table and does full load. On subsequent runs, finds `MAX(_airbyte_extracted_at)` in staging table as watermark and inserts only rows newer than watermark. Never drops staging table after first load. If watermark column absent, aborts with explicit error — no silent full refresh fallback.

```python
def transform_table(client_id, table_name, conn):
    columns = query_registry(client_id, table_name)
    select_parts = build_select_clause(columns)
    execute_insert_into_staging(client_id, table_name, select_parts)
```

### Step 5: dbt Models
dbt reads from clean staging tables. No casting in dbt — data is already correctly typed. dbt only does business logic: joins, aggregations, metric calculations. All mart models read from `client_config` to apply founder-confirmed definitions.

### Step 6: Agents Query Marts
Agent A runs every 6 hours scanning `mart_causal_chain_daily`. On threshold breach, fires Agent B for RCA. Agent C generates suggestions. Agent D formats Evidence Stack and posts to Slack.

---

## 5. dbt Project Structure

```
warehouse/
├── dbt_project.yml
├── profiles.yml                    (at C:\Users\Anupam\.dbt\profiles.yml)
├── models/
│   ├── sources/
│   │   ├── shopify_sources.yml     (all Shopify raw tables)
│   │   └── other_sources.yml       (Meta, GA4, Gorgias etc. — TBD)
│   ├── staging/
│   │   ├── schema.yml              (column descriptions and tests)
│   │   ├── stg_shopify_order_source_attribution.sql
│   │   ├── stg_shopify_orders.sql
│   │   ├── stg_shopify_refunds.sql
│   │   ├── stg_shopify_net_sales_validation.sql
│   │   ├── stg_meta_ad_performance.sql     (to be created)
│   │   ├── stg_klaviyo_campaigns.sql       (to be created)
│   │   ├── stg_gorgias_tickets.sql         (to be created)
│   │   ├── stg_ga4_funnel_daily.sql        (to be created)
│   │   └── stg_sentry_errors_daily.sql     (to be created)
│   └── marts/
│       ├── schema.yml
│       ├── mart_net_revenue_daily.sql
│       ├── mart_return_rate_by_sku.sql     (to be created)
│       ├── mart_cross_source_daily.sql     (to be created)
│       ├── mart_influencer_roi.sql         (to be created)
│       └── mart_causal_chain_daily.sql     (to be created)
└── tests/
    └── generic/
```

**dbt_project.yml key config:**
```yaml
name: 'profit_sentinel'
vars:
  client_id: 'client_azure_co'
  client_schema: 'client_azure_co'

models:
  profit_sentinel:
    staging:
      +materialized: view
      +schema: "{{ var('client_schema') }}"
    marts:
      +materialized: table
      +schema: "{{ var('client_schema') }}_marts"
```

### Existing dbt Models (currently working)

**stg_shopify_order_source_attribution**
- Reads from: `shopify_orders`
- Classifies every order by originating system (shopify_web, pos, recharge, tiktok_shop, wholesale_portal, unknown_app_{id}, unclassified)
- Adds: `attribution_confidence` (high/medium/low), `has_dedicated_connector` (boolean)

**stg_shopify_orders**
- Reads from: `shopify_orders`
- Cleans types, excludes cancelled and voided orders
- Key fix: `total_shipping_price_set::jsonb -> 'shop_money' ->> 'amount'` for shipping extraction
- Key fix: `(customer::jsonb ->> 'id')::bigint` for customer_id

**stg_shopify_refunds**
- Reads from: `shopify_order_refunds`
- One row per refund event

**stg_shopify_net_sales_validation**
- Reads from: `stg_shopify_orders`, `stg_shopify_refunds`
- Implements Shopify's exact Net Sales formula for validation
- Formula: `Gross Sales - Discounts` (excludes tax and shipping)
- Additional columns: `pos_revenue`, `b2b_revenue`, `unconnected_source_revenue` for gap diagnosis

**mart_net_revenue_daily**
- Reads from: `stg_shopify_orders`, `stg_shopify_order_source_attribution`
- Daily aggregation: order_count, gross_revenue, total_discounts, net_revenue, average_order_value, data_completeness_pct
- Currently: no client_config join (to be added in architectural rebuild)

---

## 6. Dynamic Staging Architecture

### Why Not Hardcoded dbt Staging

Hardcoded dbt staging models assume data types. When reality differs the model breaks. Shopify API changes across versions. Airbyte's type inference is not always correct. Every new source connector would repeat the same trial-and-error.

**The casting logic lives in the Python transformer driven by the registry — not in dbt SQL.**

### schema_discovery.py Full Logic

```python
def discover_and_update_schema(client_id, table_name, conn):
    cursor = conn.cursor()

    # Read actual current schema
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position
    """, (f"client_{client_id}", table_name))
    current_schema = {row[0]: row[1] for row in cursor.fetchall()}

    # Read previously registered schema
    cursor.execute("""
        SELECT column_name, raw_data_type
        FROM public.source_schema_registry
        WHERE client_id = %s AND table_name = %s
    """, (client_id, table_name))
    registered_schema = {row[0]: row[1] for row in cursor.fetchall()}

    # Detect and handle each change type
    for col_name, current_type in current_schema.items():
        if col_name not in registered_schema:
            handle_new_column(col_name, current_type, client_id, table_name, cursor)
        elif registered_schema[col_name] != current_type:
            handle_type_change(col_name, registered_schema[col_name],
                             current_type, client_id, table_name, cursor)

    for col_name in registered_schema:
        if col_name not in current_schema:
            handle_column_removed(col_name, client_id, table_name, cursor)

    conn.commit()
```

### What Happens When Shopify Changes a Field Type

Example: `total_price` changes from `text` to `numeric` in new Shopify API version.

```
1. Airbyte syncs — total_price now numeric in raw table

2. schema_discovery.py runs:
   - Reads information_schema: total_price = numeric
   - Reads registry: total_price was text
   - Detects: type_changed
   - Updates registry: raw_data_type = numeric,
     transformation = none (no cast needed anymore)
   - Writes to schema_versions: change_type = 'type_changed'

3. Agent A reads schema_versions at next scan:
   - Fires Slack alert:
     "Schema change on shopify_orders.total_price:
      text → numeric. Staging updated automatically."

4. python_transformer.py runs next cycle:
   - Reads updated registry
   - transformation is now 'none' for total_price
   - Column passed through directly
   - Model works correctly

5. dbt runs on clean staging table:
   - No changes needed in any dbt model
   - mart_net_revenue_daily produces correct output
```

---

## 7. Synthetic Data Architecture

### Purpose
Generate 24 months of realistic interconnected data across all 6 sources to test agents before any real client data exists.

### is_synthetic Column
Added to every raw source table after Airbyte creates it:
```sql
ALTER TABLE client_azure_co.shopify_orders
ADD COLUMN is_synthetic boolean default false;
```

### use_synthetic_data Toggle
In `client_config`. When `true`, dbt models include synthetic rows. When `false`, filters them out. Flip once real connectors go live — zero code changes.

### Shared Event Calendar
One Python dictionary defines all events. Every source generator reads from the same calendar so timestamps correlate correctly across sources.

**Events defined:**
- Collection launches (Spring/Summer/Fall/Holiday × 2 years)
- Sale periods (Summer sale July 1-21, BFCM last Friday November)
- Influencer campaigns (3 across 24 months)
- Supplier quality issue (AZ-JEAN-015, month 14, 45 days)
- Checkout JS error (month 9, 6 hours, mobile-heavy)
- Meta Q4 CPM inflation (October-December each year)
- Sync outage (month 6, 3 consecutive days zero orders)

### Cross-Source Causal Timing (Critical)
```
Collection launch (Day 0)
  → Shopify orders spike +40% (Day 0-5)
  → GA4 sessions spike +35% (Day 0-7)
  → Klaviyo campaign sent (Day 0)
  → Gorgias pre-purchase questions +60% (Day 1-5)
  → Meta CPM rises +25% (Day 7-21)
  → Gorgias sizing complaints +180% (Day 8-16)  ← KEY LEADING SIGNAL
  → Shopify return rate rises +20% (Day 10-21)  ← LAGS GORGIAS BY 6-13 DAYS
  → ROAS compression visible (Day 14-21)
```

This 6-13 day lag between Gorgias sentiment and return spike is the core causal signal Agent B must detect. The synthetic data must maintain this timing relationship precisely.

### SKU Structure
- 25 base styles across 5 categories (dresses, tops, bottoms, jackets, accessories)
- 5 sizes × 3-4 colours per style = ~380-400 active variant SKUs
- SKU format: `AZ-{CATEGORY}-{NUM}-{SIZE}-{COLOR_CODE}`
- Each variant has: price, cost, base_return_rate, size-specific return adjustment

### Data Quality Issues (76 total across 6 sources)

**Shopify (18 issues):** null source_name (8%), null shipping JSON (12%), duplicate order IDs (3 dates), orphaned refunds (5), refund exceeds order (3), cancelled with paid status (8), null customer (5%), future-dated refunds (2), zero-value orders (6), sync outage gap (3 days), timezone date shift, inconsistent SKU format (15), payment processor mismatch, bot traffic, consent blocking, ghost app scripts, multi-currency confusion, API rate limit during peak.

**Meta Ads (17 issues):** iOS ATT modeled conversions (35% of iOS rows flagged), iOS UTM stripping, API vs UI reach mismatch, attribution window timing break (pre/post June 2025), 7/28-day view window deprecated (Jan 2026), 100+ metrics deprecated, 13-month historical data limit, CAPI deduplication failure (3 dates), AEM 8-event cap, attribution window not pinned (15%), zero spend with impressions (8 rows), duplicate date rows (4), null adset_name (5%), currency inconsistency (6 rows), delayed reporting (last 3 days), CAPI vs pixel double counting.

**GA4 (14 issues):** 20% order loss rate (ad blockers), checkout steps 2/3 missing (15% of days), bot traffic inflation (10%), TikTok UTM stripping (all TikTok → direct), EU consent blocking (8% session reduction), 72-hour processing delay, duplicate purchase events (5% of days), cross-device attribution loss (20%), sampling at low traffic, null landing page (12%), timezone inconsistency vs Shopify.

**Klaviyo (11 issues):** duplicate profiles (12%), null campaign revenue (18%), double attribution campaign+flow (8%), AddToCart missing variant_id, Checkout_create event delayed, opt-in records not syncing, Shopify Customer ID vs Klaviyo Profile ID mismatch, timezone offset, bounce type inconsistency, flow step misattribution, Product_view schema mismatch.

**Gorgias (11 issues):** inconsistent tag names (sizing/runs_small/size_issue), missing tags (30%), duplicate tickets same customer (4%), null order reference (18%), CSAT missing (45%), wrong sentiment classification (5%), ticket re-open toggle, peak period tagging drop (30% rate during BFCM), retrospective count changes, AI auto-resolution errors, 1-year analytics data limit.

**Sentry (5 issues):** rate limiting during BFCM (30-40% underreporting), stale instrumentation (14 days zero errors post-theme-update), duplicate error events (15% inflated), environment confusion (3% staging tagged as prod), missing release version (20%).

---

## 8. Airbyte Configuration

### Phase 1 Connectors

| Connector | Method | Schema target | Sync frequency |
|---|---|---|---|
| Shopify | Airbyte Cloud native | `client_{brand_name}` | Every 6 hours |
| Meta Ads | Airbyte Cloud native | `client_{brand_name}` | Every 6 hours |
| Klaviyo | Airbyte Cloud native | `client_{brand_name}` | Every 6 hours |
| Gorgias | Airbyte Cloud native | `client_{brand_name}` | Every 6 hours |
| GA4 | Custom Python connector | `client_{brand_name}` | Daily |
| Sentry | Custom Python connector | `client_{brand_name}` | Every hour |
| TikTok | TikTok Marketing API | `client_{brand_name}` | Every 6 hours |

### Destination Configuration
- Host: `aws-1-us-east-1.pooler.supabase.com`
- Port: 5432
- Database: `postgres`
- Schema: `client_{brand_name}` (per-client, not `public`)
- SSL: required

### Schema Propagation Setting
Set to **"Propagate field changes only"** — new columns added automatically, destructive changes flagged for review.

---

## 9. The Nine Agreed Architectural Changes

**Change 1 — Multi-tenancy (schema per client)**
Each client gets `client_{brand_name}` schema. Airbyte destination schema set per client. dbt uses `var('client_schema')` at runtime.

**Change 2 — Remove manual placeholder tables**
Only 3 application tables created manually in public: `alert_log`, `thread_context`, `client_config`. The 5 source placeholder tables previously created were a mistake — drop them.

**Change 3 — Dynamic staging via schema registry**
Replace hardcoded dbt staging SQL with `source_schema_registry` table + `schema_discovery.py` + `python_transformer.py`. dbt models have zero casting logic — only business logic on pre-cleaned data.

**Change 4 — Synthetic data into real source tables**
Synthetic data goes into the same Airbyte-created tables. `is_synthetic boolean default false` column on all source tables. `use_synthetic_data` toggle in `client_config`.

**Change 5 — Connect other sources before seed script**
Connect Meta Ads, Klaviyo, Gorgias via Airbyte to get real schemas. Design GA4, Sentry, TikTok schemas manually. Then seed script populates all real tables.

**Change 6 — Revised client_config (clean slate)**
Maximum 8 onboarding questions. Full resumable `onboarding_state` JSONB. Connector activation flags. Derived fields not asked. config_change_log trigger for audit trail.

**Change 7 — config_change_log trigger**
Automatic logging of every client_config change. Agent A reads this to suppress false alerts when metric moves due to definition change not real business signal.

**Change 8 — Founder metric confirmation flow**
Happens after staging runs, before marts run for first time. Maximum 8 dynamic questions. Answers write to client_config. Definition change later triggers dbt full-refresh recomputing all historical marts.

**Change 9 — Slack personal workspace for testing**
Create at slack.com for personal testing of onboarding flow and alert formats before any real client sees them.

---

## 10. Build Sequence from Current State

```
CURRENT STATE:
✓ Supabase database exists (wrong schema structure)
✓ Airbyte connected to Shopify dev store (wrong destination schema)
✓ dbt Cloud connected to Supabase and GitHub
✓ 5 dbt staging/mart models written and running
✓ 1 row of validated data in mart_net_revenue_daily
✗ Multi-tenancy not implemented
✗ Schema registry not built
✗ Dynamic transformer not built
✗ Other sources not connected
✗ Synthetic data not seeded

IMMEDIATE NEXT STEPS:

Step 1 (Multi-tenancy):
  - Run Claude Code prompt to create 6 public application tables
  - Create client_azure_co schema
  - Change Airbyte destination schema to client_azure_co
  - Resync Shopify → all tables land in client_azure_co
  - Drop old public schema source tables

Step 2 (Schema registry and transformer):
  - Build schema_discovery.py
  - Build python_transformer.py with infer_transformation()
  - Run against client_azure_co.shopify_orders
  - Verify staging tables created correctly

Step 3 (Other sources):
  - Connect Meta Ads via Airbyte → client_azure_co
  - Connect Klaviyo via Airbyte → client_azure_co
  - Connect Gorgias via Airbyte → client_azure_co
  - Design GA4, Sentry, TikTok table schemas manually
  - Create those tables in client_azure_co

Step 4 (Add is_synthetic column):
  - ALTER TABLE to add is_synthetic to all source tables

Step 5 (Seed script):
  - Write comprehensive seed script (all 6 sources)
  - Shared event calendar across all sources
  - Insert 24 months synthetic data with 76 DQ issues
  - Validate 5 cross-source narrative scenarios

Step 6 (dbt rebuild):
  - Update dbt_project.yml with client_schema variable
  - Update shopify staging models to read from client_azure_co
  - Write staging models for all 6 sources
  - Write mart_cross_source_daily and mart_causal_chain_daily
  - Run dbt run — all models green

Step 7 (Validate):
  - Run 5 scenario validation queries
  - Confirm causal chains are detectable
  - Confirm DQ issues are testable

Step 8 (Confirmation flow):
  - Build Python CLI confirmation script
  - Test 8-question flow
  - Verify client_config populated correctly

Step 9 (Agent A):
  - Build LangGraph Agent A
  - Pure Python threshold checks (no LLM calls)
  - Test against synthetic CPM spike scenario
  - Verify alert fires before ROAS drops

Step 10 (Slack personal workspace):
  - Create Slack workspace
  - Build Slack Bolt bot
  - Connect to workspace
  - Test Evidence Stack alert format
  - Test Approve/Snooze/Dismiss buttons
```

---

## 11. File Locations

```
Project root:
C:\Users\Anupam\OneDrive\Desktop\Profit Sentinel\profit-sentinel-product\profit-sentinel\

.env (DATABASE_URL and other secrets):
[project root]\.env

profiles.yml (dbt Supabase credentials):
C:\Users\Anupam\.dbt\profiles.yml

dbt project:
[project root]\warehouse\

dbt models:
[project root]\warehouse\models\staging\
[project root]\warehouse\models\marts\
[project root]\warehouse\models\sources\

Connectors (to be built):
[project root]\connectors\schema_discovery.py
[project root]\connectors\python_transformer.py
[project root]\connectors\ga4_connector.py
[project root]\connectors\sentry_connector.py

Agents (to be built):
[project root]\agents\agent_a.py
[project root]\agents\agent_b.py
[project root]\agents\agent_c.py
[project root]\agents\agent_d.py

Seed scripts:
[project root]\tests\seed_all_sources.py

Slack bot (to be built):
[project root]\slack-bot\

Frontend (to be built):
[project root]\frontend\

GitHub repository:
https://github.com/anupam313/profit-sentinel
```

---

## 12. Supabase Connection Details

```
Host: aws-1-us-east-1.pooler.supabase.com
Port: 5432
Database: postgres
Username: postgres.ebazniykhcbgwdukdezl
Schema: public (application tables) / client_azure_co (source data)
SSL: require
```

*Note: Rotate password after this document is shared.*

---

## 13. Key Design Decisions and Rationale

**Why ELT not ETL:** Transform after loading means raw data is always preserved. If transformation logic changes, rerun dbt on the same raw data — no re-extraction needed.

**Why Python transformer not dbt for casting:** dbt models are static SQL compiled at build time. They cannot read the schema registry at runtime and adapt. Python runs at execution time and can make decisions based on what the registry says.

**Why dbt at all if Python does the transformation:** dbt handles business logic (joins, aggregations, metric definitions), testing (not_null, unique), documentation, dependency management, and scheduling. Python handles the messy reality of type inference and schema drift. Clear separation of concerns.

**Why LangGraph not CrewAI for agents:** Explicit graph-based control flow. You can see exactly which agent is running and why. Essential for the causal graph traversal where Agent B must traverse a specific path. CrewAI's agent autonomy is too unpredictable for deterministic causal reasoning.

**Why Slack-first not dashboard-first:** Switching from Slack to a web app to investigate an alert breaks the workflow at exactly the moment the product should be most useful. All operational interaction happens in Slack. Web app is configuration and audit only.
