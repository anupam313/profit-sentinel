# Profit Sentinel — Technical Architecture
*Version: Post-critique redesign | Last updated: 2026-06-14 (§11 File Locations — git-backed docs/ design-docs folder added, commit 7402434) | 2026-06-08 (D1 Gap 6 residual pass — BAU baseline now excludes pre-sale ramp windows + onboarding two-pass backfill; structural-break magnitude made brand-relative; D1 estimated fulfilment driver retired [D4 stays Phase-2]; fulfilment is feed-only in CM; see agent_d_build_spec.md + cross_alert_orchestration.md) | prior: 2026-06-04 (discount-depth/S19 PARTIAL: discount/returns/Gorgias-parser build items appended at end; margin_floor_pct flagged orphaned)*

<!-- 2026-06-02 spec-update pass (D1 Gap 6 WIP): rename strike + AI-clustering/
display-gate notes; category_inference_confidence redefined as cross-signal
agreement (0.70 provisional); clustering-quality gate added; seasonal_typicality_state
column added to suppression_log; brand_event_calendar Approach-B confound-guard note
added; GAP 6 DEPENDENCIES block rewritten to the resolved Gap 6 design (retired ±1 SD /
≥12-month / spend-optional / collection_launch_suppression_active wording removed).
NOTE: the S3 post-holiday-return-window edit (state-file edit #4) had NO target in this
file — the only Jan-dated return reference (line ~498, "January returns Jan 5–25") is the
calendar_clustered confound heuristic, not the S3 rule — so edit #4 was intentionally
skipped here (S3 re-anchoring landed in agent_d_build_spec.md; S-rule definition is
out of scope, logged for the orchestration pass). -->


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

    -- COGS and margin (updated 2026-05-26 — 4-tier COGS architecture)
    -- cogs_tier_active determines D1 alert format:
    --   finaloop / founder_csv → full margin alert with % and $ impact
    --   shopify_derived / founder_stated → driver-only cost pressure alert, no margin %
    -- NEVER mix alert formats — one template or the other.
    cogs_tier_active                    text default 'founder_stated',
    -- values: finaloop / founder_csv / shopify_derived / founder_stated
    -- Set automatically based on active connector or confirmed upload
    cogs_source                         text default 'shopify_cost_field',
    cogs_confidence_level               text default 'low',
    -- low = no cost data → suppress margin % in alerts
    -- medium = shopify cost field proxy confirmed at onboarding
    -- high = Finaloop or founder CSV fully reconciled
    shopify_cost_field_coverage_pct     numeric default 0,
    cogs_shopify_confirmed              boolean default false,
    -- true = founder confirmed Shopify cost-per-item is maintained for all products
    cogs_shopify_landed                 boolean default false,
    -- true = founder confirmed Shopify cost is landed cost (not ex-factory)
    cogs_multiplier_confirmed           numeric default 1.28,
    -- Founder-confirmed landed cost multiplier. Used when cogs_shopify_landed = false.
    -- Default 1.28 is assumption — validate at onboarding.
    cogs_owner_contact                  text,
    -- Email of person responsible for COGS maintenance (may be finance team, not founder)
    -- Collected during onboarding contextually after fuzzy/unmatched SKUs detected
    -- Always CC founder on COGS gap alerts — never route exclusively to cogs_owner_contact
    cogs_gap_suppressed                 boolean default false,
    -- true = founder clicked "Don't remind me" on Day 20 final notice
    -- Suppresses existing unmapped SKU reminders. New SKUs still trigger fresh cycle.
    -- When true: one-time note in weekly summary only, then never mentioned again.
    cogs_refresh_rhythm_days            integer,
    -- ADDED 2026-06-03 (Gap 6 COGS). Founder's OWN stated cost-refresh cadence,
    --   captured at onboarding. Drives staleness-decay: once cost is older than this,
    --   the margin alert stops stating a margin figure and drops to component signals
    --   until the founder reconfirms. NULL = not yet stated → treat cost as
    --   confirmation-required before any margin figure. NEVER a hardcoded interval.
    cogs_last_confirmed_at              date,
    -- ADDED 2026-06-03. Date the founder last confirmed / uploaded cost. Staleness =
    --   today - cogs_last_confirmed_at, compared to cogs_refresh_rhythm_days.
    -- STALENESS-DECAY (2026-06-03): fresh (within rhythm) → full margin figures;
    --   aging (past rhythm) → live caveat, "based on cost from [date], ~N months old";
    --   stale (well past) → NO margin figure, component signals only. Disclosure is
    --   STATE-DRIVEN — not a footnote on every alert; basis stays one click away even
    --   on clean alerts.
    -- COST-INCREASE DRIVER IS FEED-ONLY (2026-06-03): "supplier raised costs → margin
    --   compressing" is detectable only when cogs_confidence_level = high (trustworthy
    --   feed). Otherwise structurally invisible (the other four margin drivers are
    --   visible; COGS is held at a stale/assumed value, so a COGS-driven dip yields no
    --   residual). The cost-update ask is PROACTIVE at onboarding, never a reactive
    --   alert. The S21 phase-in is per-product sell-through of pre-increase stock, not a
    --   fixed 60-day window; the phased curve needs an average-cost feed (Finaloop /
    --   Stocky) — Shopify's single non-retroactive cost field cannot represent cost
    --   layers, so absent a feed, narrate the phasing, never fabricate a "% realized".
    -- Q (onboarding): "Do you maintain cost-per-item in Shopify for all products?
    --                  Is it your landed cost?"
    -- Q (onboarding): "Do you have Finaloop set up, or should I use Shopify's product
    --                  cost field?"
    -- Q (onboarding, if fuzzy SKUs found): "We found [X] SKUs we couldn't confidently
    --                  match. Who should we send these to for offline review? [email]"
    -- Q (per CSV upload): "Are all costs in this file in USD?"
    -- Q (per CSV upload): "Are these costs landed (including freight and duties)
    --                  or ex-factory?"
    -- Q (onboarding, ADDED 2026-06-03): "How often do your product costs typically
    --                  change (supplier price updates, new ranges)? Monthly / quarterly
    --                  / rarely? I'll use that to decide when to ask you for a refresh,
    --                  and I'll flag when my numbers are based on cost that may be out
    --                  of date." → write to cogs_refresh_rhythm_days.
    -- COGS escalation cadence (US business days, US federal holiday calendar):
    --   Day 0: Alert to cogs_owner_contact
    --   Day 5: Reminder to cogs_owner_contact
    --   Day 10: Escalation to founder — owner hasn't responded
    --   Day 15: Reminder to founder
    --   Day 20: Final notice to founder with opt-out button → hard stop
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
    -- ⚠ ORPHANED (flagged 2026-06-04, see cross_alert_orchestration.md O-25/O-26).
    --   NOT wired into the locked D1 Trigger A/B firing logic, which is fully
    --   brand-relative (Trigger A: a drop below the brand's own baseline band scaled to
    --   its own volatility; Trigger B: a downward trend in its own weekly CM). This field
    --   is a relic of the pre-Gap-2 absolute-floor design; the "calibrate to ~28%" note
    --   reflects superseded thinking. Remove or consciously re-scope in the post-Gap-6
    --   consistency audit. Do NOT wire it in as-is.
    ga4_funnel_drop_threshold           numeric default 8.0,
    sentry_error_threshold_pct          numeric default 2.0,
    gorgias_sentiment_threshold         numeric default 15.0,
    -- Statistical minimums — agents suppress below these
    min_order_count_for_alerts          integer default 5,
    min_sessions_for_ga4_alerts         integer default 500,
    min_tickets_for_gorgias_alerts      integer default 20,

    -- Synthetic data toggle
    -- true during testing, false when real connectors go live
    use_synthetic_data                  boolean default false,

    -- Historical scan configuration
    -- Set by historical_pattern_scan.py at onboarding — do not edit manually
    historical_scan_completed           boolean default false,
    historical_scan_completed_at        timestamptz,
    historical_scan_status              text default 'pending',
    -- values: pending / running / complete / failed
    -- Polled by onboarding CLI to report completion without blocking
    last_historical_scan_at             timestamptz,
    -- Updated after every run (full sweep and monthly incremental)
    -- Monthly incremental uses this as the start of the incremental window
    -- Per-connector actual lookback used (days) — set after scan completes
    shopify_lookback_days               integer,
    klaviyo_lookback_days               integer,
    gorgias_lookback_days               integer,
    loop_lookback_days                  integer,
    meta_lookback_days                  integer default 395,   -- 13-month hard limit
    ga4_lookback_days                   integer,               -- days since July 2023
    tiktok_lookback_days                integer default 730,   -- 24-month practical limit
    sentry_lookback_days                integer default 90,    -- plan-dependent hard limit

    -- Financial capacity — action re-ranking only (NOT alert suppression)
    -- When true, Agent C re-ranks suggestions: spend-increase actions demoted
    -- Alert always fires. Founder sees all options. Nothing suppressed.
    capital_constraint_active           boolean default false,
    monthly_ad_budget_ceiling           numeric,

    -- Alert delivery timing optimisation
    -- H-series (critical) alerts NEVER held regardless of this setting
    delivery_timing_enabled             boolean default true,
    last_engagement_pattern             jsonb,
    delivery_timing_preference          text default 'optimised',
    -- values: optimised (Agent D decides timing) / immediate (always fire now)

    -- Klaviyo open rate iOS MPP adjustment
    -- Apple Mail Privacy Protection pre-loads tracking pixels regardless of human open.
    -- ~52% of premium womenswear audience uses Apple Mail; ~68% have MPP enabled.
    -- Result: ~35% of reported opens are machine-generated on this audience.
    -- All E-series alert calculations use: effective_open_rate = reported × ios_mpp_multiplier
    -- Set at onboarding from audience device mix. Default 0.65 for premium womenswear.
    -- Brands with Android-heavy audiences should use 0.80–0.85.
    -- NEVER hardcode 0.65 in mart SQL — always read from client_config via subquery.
    ios_mpp_multiplier                  numeric default 0.65,
    -- Added: 2026-05-19 Session 3

    -- Pending connector tracking
    -- Populated at onboarding confirmation flow: "Are you planning to add any sources
    -- in the next 90 days?" — yes/no with free-text for which sources.
    -- Monthly incremental scan checks this flag: if a pending connector is now active,
    -- re-runs any scan_skipped_reason rows for that connector automatically.
    -- Internal notification only — not founder-facing.
    pending_connectors                  text[] default array[]::text[],
    -- e.g. array['gorgias', 'tiktok']
    pending_connectors_noted_at         timestamptz,
    -- When founder indicated pending connectors at onboarding

    -- GMV estimate — derived from Shopify, not founder-stated
    -- Set by historical_pattern_scan.py from total Shopify order revenue in scan window
    -- Used to calculate onboarding leakage threshold (≥1% of GMV required to show $ section)
    -- Updated on every monthly incremental scan
    gmv_derived_annual                  numeric,
    gmv_derived_at                      timestamptz
    -- Added: 2026-05-20 Session Q4–Q6
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
    dismissal_reason    text,          -- capacity_constrained / data_wrong / not_relevant
    -- Populated by one-tap Agent D question on every dismiss:
    -- "Not actionable right now, or doesn't look right?"
    -- capacity_constrained dismissals excluded from precision calculations
    followup_queued     boolean default false,
    -- true when action_taken = dismiss AND outcome later confirms alert was correct
    -- Agent D sends follow-up to original Slack thread when this flips true
    followup_sent_at    timestamptz,
    outcome_metric      text,
    outcome_value_7d    numeric,       -- filled by scheduled dbt model 7 days later
    outcome_value_14d   numeric,       -- filled 14 days later
    outcome_checked_at  timestamptz,
    is_false_positive   boolean,
    suppressed          boolean default false,
    suppression_reason  text,
    verification_category  text        -- A / B / C — see Section 14
    -- A: directionally verifiable in data independent of founder action
    -- B: action-confounded — requires cross-client validation
    -- C: structurally unverifiable — explicit uncertainty always communicated
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

#### causal_pattern_validation
```sql
-- Cross-client causal chain validation table
-- Stores anonymised accuracy rates per causal chain per vertical
-- Agent B reads this to assess confidence before firing alerts
-- Promoted from candidate_signals after threshold met
-- Also populated at onboarding by historical_pattern_scan.py
CREATE TABLE public.causal_pattern_validation (
    id                      bigint generated always as identity primary key,
    causal_chain_id         text not null,       -- which path in Fashion Causal Graph
    vertical_tag            text not null,       -- swimwear/contemporary/premium/activewear
    signal_type             text not null,       -- which alert type (e.g. 'A1', 'B2')
    instance_count          integer default 0,   -- all instances found including recent unobservable
    observable_instance_count integer default 0, -- instances with closed outcome windows (denominator for hit_rate)
    confirmed_count         integer default 0,   -- outcome confirmed instances (hits)
    false_positive_count    integer default 0,   -- outcome not confirmed instances
    confidence_rate         numeric,             -- confirmed_count / NULLIF(observable_instance_count, 0)
    hit_rate                numeric,             -- alias for confidence_rate — same field
    threshold_at_scan_time  jsonb,               -- thresholds active at scan time {leading_signal: x, outcome: y}
    confidence_tier         text default 'candidate',
    -- values: candidate / provisional / core
    -- candidate: <4 observable instances OR <70% hit rate — fires with uncertainty disclosure, gate active
    -- provisional: 4–9 observable instances AND ≥70% hit rate — standard Evidence Stack, gate active
    -- core: ≥10 observable instances AND ≥80% hit rate — gate removed, fires on leading signal alone
    last_promoted_at        timestamptz,         -- when chain was last validated/promoted
    promotion_threshold     integer default 10,  -- cross-network instances needed for promotion
    client_count            integer default 0,   -- distinct clients contributing to this chain
    historical_scan_seeded  boolean default false,
    -- true if confidence_tier was set from historical_pattern_scan.py at onboarding
    -- false if confidence accumulated from live alerts only
    scan_skipped_reason     text,
    -- populated when historical scan cannot run this chain due to missing/insufficient data
    -- values: 'connector_missing' | 'insufficient_history' | 'below_sparsity_threshold'
    -- | 'gorgias_tagging_insufficient' | 'connector_name:{name}'
    -- monthly incremental scan re-attempts skipped chains when connector becomes available
    created_at              timestamptz default now(),
    updated_at              timestamptz default now(),
    unique(causal_chain_id, vertical_tag)
);
```

**Promotion rules:**
- Per-client threshold: 4–9 observable instances at ≥70% hit rate → `provisional` for that client
- Cross-network threshold: ≥10 observable instances at ≥80% hit rate across clients of same vertical_tag → `core` globally for that vertical
- Cross-vertical promotion is explicitly prohibited — a chain validated on contemporary womenswear does NOT auto-promote for swimwear
- `confidence_rate` is recomputed on every update: `confirmed_count::numeric / NULLIF(observable_instance_count, 0)`

**Confidence tier rules:**
- `candidate`: fewer than 4 observable instances OR hit rate below 70% — fires with explicit uncertainty disclosure, multi-signal confirmation gate active, confidence score 0–40
- `provisional`: 4–9 observable instances AND ≥70% hit rate — fires with standard Evidence Stack, multi-signal confirmation gate active, confidence score 41–70
- `core`: ≥10 observable instances AND ≥80% hit rate — fires without multi-signal confirmation gate (fires on leading signal alone), confidence score 71–100. Requires `practitioner_approved = true` on novel/client-specific chains before gate is removed.

**Hit definition (applies to both known chains and novel chain discovery):**
- A "hit" requires BOTH the leading signal AND the outcome metric to cross their respective live-agent thresholds within the lag window (lag_days ± 2 days). Binary — 1 or 0 per instance. No magnitude weighting.
- Denominator is `observable_instance_count` only — instances where the outcome window has fully closed (trigger_date ≤ scan_date − (lag_days + 2)). Recent instances within the unclosed window count toward `instance_count` but are excluded from hit rate computation.
- Threshold values active at scan time are recorded in `threshold_at_scan_time` for auditability. Historical hit rates are not retroactively recalculated if thresholds change.

**Multi-signal confirmation gate:**
- `candidate` and `provisional` chains: Agent B requires at least one corroborating mart column in the same causal chain to be trending in the predicted direction before firing the alert.
- `core` chains: gate removed — alert fires on leading signal alone, same day threshold is crossed.
- Novel client-specific chains at `core` tier retain the gate until `practitioner_approved = true` is manually set.

**Historical scan seeding (historical_pattern_scan.py):**

*Two run modes:*
- **Full sweep (onboarding):** Runs asynchronously as Step 6 of onboarding after dbt full-refresh. Scans full available history per connector. Completes silently — no founder-facing message. Updates `historical_scan_status` in `client_config` on completion.
- **Incremental sweep (monthly):** Scheduled 1st of each month. Scans incremental window since `last_historical_scan_at` only. New novel pairs discovered in the incremental window are validated against full history before writing to `candidate_signals`.

*Per-connector max lookback:* Shopify/Klaviyo/Gorgias/Loop → account creation; Meta → 13 months; GA4 → July 2023; TikTok → 24 months; Sentry → 90 days. Per-connector actual lookback days written to `client_config` on completion.

*Known chain validation (56 chains):*
- Counts instances, computes `observable_instance_count` and `hit_rate` using the hit definition above
- Writes confidence_tier to `causal_pattern_validation` with `historical_scan_seeded = true`
- Cross-source chains limited by the shallowest connector in the chain (e.g. F2 limited by Sentry 90-day window)

*Novel chain discovery (beyond 56):*
- Separate code path from known chain validation — no merging at any stage
- Unconstrained bivariate sweep across all mart column pairs
- Sparsity filter: leading signal must have crossed threshold ≥4 times in full history — pairs below this are not stored
- All candidates written to `candidate_signals` with `source = 'historical_scan'` and `client_specific = true` — nothing auto-promotes to `causal_pattern_validation`
- Pre-filters applied before routing to practitioner review:
  - **Calendar dispersion check:** if >60% of trigger dates fall within known fashion calendar windows (BFCM Nov 15–Dec 5, SS drop Feb–Mar, FW drop Aug–Sep, January returns Jan 5–25), set `calendar_clustered = true`. Cross-client convergence on a `calendar_clustered = true` pair increases confound suspicion, not signal confidence.
  - **Effect size minimum:** outcome metric must move by ≥50% of its live-agent threshold to count as a hit — eliminates weak-effect correlations
- Novel pairs flagged `calendar_clustered = true` but causally plausible set `confound_unresolved = true` — routed to practitioner review with explicit question framing
- Single-client depth track: novel pairs reaching ≥10 observable instances at ≥80% hit rate within one client set `single_client_core = true` — routed to Track 2 practitioner review queue. `practitioner_approved` must be set before core behaviour activates.
- Cross-client convergence track (Track 1): deferred to post-10-client milestone — logged as DEBT-T1. When active: novel pair appearing in 3+ clients of same `vertical_tag` with `calendar_clustered = false` — fast-tracked to practitioner review. `client_specific` set to false only after re-scan confirms chain, not at practitioner approval.
- Monthly post-sweep auto-check: any candidate_signals row with cross_client_instance_count ≥ 3 AND calendar_clustered=false → promotion_status='validated' → practitioner review queue
- Monthly practitioner digest (internal Slack, not founder-facing): shortlisted candidates after pre-filtering, target <10 items/month. Deferred until 5+ beta clients onboarded — manual DB review acceptable until then.
- Category B (action-confounded) patterns carry explicit Layer 0 disclosure regardless of confidence tier: "Outcome may reflect founder action rather than natural resolution — this affects confidence calculation"

#### candidate_signals
```sql
-- Stores anomalies Agent B detects that do not map to any existing validated causal chain
-- Also stores novel patterns discovered by historical_pattern_scan.py at onboarding
-- Instead of silently dropping unrecognised patterns, Agent B logs them here
-- Outcome tracking on candidate_signals drives promotion to causal_pattern_validation
-- This is the mechanism that makes the causal graph self-extending
CREATE TABLE public.candidate_signals (
    id                          bigint generated always as identity primary key,
    client_id                   text not null,
    vertical_tag                text not null,
    signal_description          text not null,   -- plain English description of the anomaly
    leading_signal_column       text,            -- mart column name of leading signal
    outcome_column              text,            -- mart column name of outcome metric
    signal_values               jsonb,           -- raw metric values at detection time
    sources_involved            text[],          -- which connectors produced the signal
    first_detected_at           timestamptz default now(),
    instance_count              integer default 1,  -- all instances including unobservable
    observable_instance_count   integer default 0,  -- denominator for hit_rate
    hit_rate                    numeric,            -- hits / observable_instance_count
    cross_client_instance_count integer default 0,
    outcome_confirmed_count     integer default 0,
    outcome_rejected_count      integer default 0,
    promotion_status            text default 'candidate',
    -- values: candidate / validated / rejected / promoted
    source                      text default 'agent_b',
    -- values: agent_b (live detection) / historical_scan (onboarding or monthly sweep)
    client_specific             boolean default true,
    -- true until cross-network validation confirms pattern generalises
    -- cross-vertical promotion prohibited — remains client_specific until
    -- 10-15 instances across clients of same vertical_tag
    calendar_clustered          boolean default false,
    -- true if >60% of trigger dates fall within known fashion calendar windows
    -- cross-client convergence on calendar_clustered=true increases confound suspicion, not signal confidence
    confound_unresolved         boolean default false,
    -- true when calendar_clustered=true but causally plausible — explicit practitioner question at review
    seasonal_confound_risk      boolean default false,
    -- true when both signals show correlated seasonality with the same calendar anchor
    single_client_core          boolean default false,
    -- true when novel pair reaches ≥10 observable instances at ≥80% hit rate within one client
    -- routes to Track 2 practitioner review — practitioner_approved required before core behaviour activates
    practitioner_approved       boolean default false,
    -- must be manually set true before core behaviour (gate removal) activates on novel/client-specific chains
    promoted_at                 timestamptz,     -- null until promoted
    promoted_to_chain_id        text,            -- causal_chain_id once promoted
    rejection_reason            text,            -- if rejected, why
    created_at                  timestamptz default now(),
    updated_at                  timestamptz default now()
);
```

**How Agent B uses candidate_signals:**
1. Agent B traverses Fashion Causal Graph — no matching chain found
2. Agent B logs anomaly to candidate_signals (does NOT fire an alert to founder)
3. Outcome tracking checks candidate signal 7 and 14 days later against metric trajectory
4. After cross-network threshold met for same vertical_tag (3+ clients, calendar_clustered=false): fast-tracked to practitioner review
5. Promoted chains (practitioner_approved + re-scan confirmed) fire as validated alerts from that point forward

**Two promotion tracks for novel candidate_signals:**
- **Track 1 — Cross-client convergence:** Applies to novel chains only — the 56 hardcoded chains in `causal_pattern_validation` are not subject to this logic. Track 1 global promotion deferred to post-10-client milestone (DEBT-T1). When active: 3+ clients of same vertical_tag, calendar_clustered=false → practitioner review → hardcoded into chain list → re-scan confirms across all 3+ client histories → `client_specific` set to false on `causal_pattern_validation` only after re-scan (NOT at practitioner approval). Applies globally to that vertical only — cross-vertical promotion prohibited.
- **Track 2 — Single-client depth:** single_client_core=true (≥10 observable instances, ≥80% hit rate, one client) → practitioner review → practitioner_approved=true → core behaviour activates for that client only. Remains client_specific=true permanently — never promoted to global list without independent Track 1 validation.
- **Pair matching:** exact string match on leading_signal_column + outcome_column. No alias resolution — mart column names must be standardised before writing to candidate_signals.
- **Monthly auto-check:** After each monthly incremental scan, a post-sweep check runs across all candidate_signals where promotion_status='candidate' and client_specific=true. Any pair where cross_client_instance_count ≥ 3 AND calendar_clustered=false → promotion_status updated to 'validated' → enters practitioner review queue. Review volume monitored as client count grows — threshold to be re-evaluated at 10+ clients (DEBT-T1).
- **Vertical scope:** Novel chains are vertical-specific in both tracks. A chain validated for contemporary_womenswear does not auto-apply to swimwear — each vertical builds its own confidence trajectory independently.
- **Multi-vertical clients:** Clients operating across multiple verticals get separate causal_pattern_validation rows per vertical_tag. Historical scan runs per vertical. Chain assignments follow SKU-to-vertical mapping in sku_cost_master (CD-4 hard dependency).

#### founder_preference_profile
```sql
-- Per-client, per-alert-type decision pattern store
-- Populated from alert_log Approve/Snooze/Dismiss actions
-- Agent C reads this to re-rank suggested actions based on founder history
-- Feeds Moat 3 (Founder Decision DNA) from Month 6
CREATE TABLE public.founder_preference_profile (
    id                          bigint generated always as identity primary key,
    client_id                   text not null,
    alert_type                  text not null,   -- e.g. 'A1', 'B2', 'H5'
    total_fired                 integer default 0,
    approved_count              integer default 0,
    snoozed_count               integer default 0,
    dismissed_count             integer default 0,
    dismissed_correct_count     integer default 0,   -- dismissed AND outcome confirmed alert was right
    dismissed_incorrect_count   integer default 0,   -- dismissed AND outcome confirmed alert was wrong
    capacity_constrained_count  integer default 0,   -- dismissed with reason = 'capacity_constrained'
    avg_response_time_minutes   numeric,
    last_updated                timestamptz default now(),
    unique(client_id, alert_type)
);
```

**Agent C behaviour:** When `dismissed_correct_count >= 3` for a given alert_type, Agent C raises the confidence threshold required before recommending snooze on future alerts of that type. When `dismissed_incorrect_count >= 3`, Agent C reduces urgency framing — founder has demonstrated good judgment in dismissing this type.

#### influencer_profile
```sql
-- Creator-level intelligence across campaigns — not just campaign-level aggregates
-- Populated from tiktok_organic_performance and seed_tiktok data
-- Required for Alert 3 to treat influencers as ongoing relationships not one-off events
-- Second and third campaigns per creator tracked separately from first
CREATE TABLE public.influencer_profile (
    id                              bigint generated always as identity primary key,
    client_id                       text not null,
    creator_id                      text not null,
    platform                        text not null,   -- 'tiktok' / 'instagram' / 'youtube'
    follower_count                  integer,
    follower_tier                   text,            -- micro/mid/macro/mega
    campaigns_run                   integer default 0,
    first_campaign_date             date,
    last_campaign_date              date,
    return_adjusted_roas_avg        numeric,
    return_adjusted_roas_by_season  jsonb,           -- {SS_2024: 1.8, FW_2024: 2.4, ...}
    category_performance            jsonb,           -- {dresses: 2.1, knitwear: 1.4, ...}
    audience_decay_indicator        boolean default false,
    -- true if no post in 90+ days — next campaign should be discounted before budget commitment
    relationship_tier               text default 'one-off',
    -- values: one-off / repeat / ambassador
    total_fee_paid                  numeric default 0,
    total_net_revenue_attributed    numeric default 0,
    lifetime_return_adjusted_roi    numeric,
    created_at                      timestamptz default now(),
    updated_at                      timestamptz default now(),
    unique(client_id, creator_id, platform)
);
```

**Alert 3 extension:** Alert 3 now surfaces creator-level history — "This is @creator's 3rd campaign with you. Return-adjusted ROAS was 1.4 in SS2024 and 2.1 in FW2024. Current campaign targets a dress collection (her strongest category: 2.3 avg ROAS)." No other tool has this longitudinal creator view.

#### onboarding_messages
```sql
-- Onboarding completion message store
-- Written by historical_pattern_scan.py Phase 6 at end of full scan
-- Read by onboarding CLI which sends via Slack Bolt SDK
-- Not written in incremental mode
-- Two variants: 'leakage' ($ threshold crossed) / 'forward_promise' (default)
-- Added: 2026-05-20 Session V3 (created by historical_pattern_scan.py _ensure_tables())
CREATE TABLE public.onboarding_messages (
    id              bigint generated always as identity primary key,
    client_id       text not null,
    message_variant text not null,  -- 'leakage' or 'forward_promise'
    message_text    text not null,
    generated_at    timestamptz default now(),
    sent            boolean default false
);
```

**Variant selection:** leakage variant fires when `gmv_derived_annual` is set
AND ≥2 chains are provisional/core AND estimated leakage ≥1% of
`gmv_derived_annual`. All other cases use forward_promise. Full message text
spec in product_strategy.md Section 5.

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

### Meta Ads API — Breaking Changes (May 2026)

**Change 1 — Attribution Windows Deprecated (January 12, 2026)**
7-day view (7d_view) and 28-day view (28d_view) attribution windows permanently removed from Ads Insights API. Deprecated windows return empty data silently — no error raised. New standard window is 7d_click + 1d_view only.

Impact:
- client_config.meta_attribution_window must default to '7d_click_1d_view' only. Remove 7d_view and 28d_view as valid values.
- Agent A must treat January 12, 2026 as a hard-coded structural break date. Any ROAS drop detected within 30 days of this date must include a caveat in Evidence Stack Layer 2: "Note: Meta attribution window change on January 12, 2026 may account for part of this movement."
- Alert 1 (True post-return ROAS by channel) and Alert 2 (Root cause of ROAS drop) both affected. Reported Meta conversions are structurally 15–40% lower post-January 12 vs pre-January 12 with identical campaign performance.

**Change 2 — Historical Data Retention Limits (January 12, 2026)**
- Unique-count fields (unique_actions, cost_per_unique_action_type): 13-month limit
- Hourly breakdowns: 13-month limit
- Frequency breakdowns: 6-month limit
- MMM breakdowns: asynchronous jobs only, no real-time synchronous access

Impact:
- Supabase is the long-term store for Meta data. Do not rely on Meta API as source of historical truth beyond these windows. Airbyte incremental sync must persist data into Supabase immediately after each pull.
- Evidence Stack Layer 3 historical precedent for Meta signals limited to 13 months lookback maximum.
- Frequency-based creative fatigue signals limited to 6 months lookback in real client data.
- Precision Profit Calendar (Moat 1) for Meta CPM seasonality patterns must be built within first 6 months of client onboarding before frequency data window closes.

**Change 3 — 100+ Metrics Deprecated**
- unique_actions: deprecated — use total actions
- 10-second video view metric: retired January 26, 2026 — use ThruPlay or 2-second continuous views
- Post/Page Reach, Video Impressions, Story Impressions: deprecated June 2026 — use Media Views and Media Viewers metrics

Impact:
- Do not include deprecated fields in manual Meta schema design or synthetic data.
- schema_discovery.py will detect and handle future deprecations automatically via is_removed flag in source_schema_registry.

**Change 4 — Advantage+ Replaces ASC/AAC Campaign Structure**
- ASC and AAC campaign creation disabled from API v24.0 (October 2025) across all versions from May 2026
- existing_customer_budget_percentage field permanently removed

Impact:
- Profit Sentinel reads campaigns, does not create them — no pipeline breakage
- campaign_type field in meta_campaigns now reflects Advantage+ structures only
- Remove existing_customer_budget_percentage from manual schema design and synthetic data
- Synthetic data campaign labels must use Advantage+ campaign structures not ASC/AAC

**Change 5 — Airbyte Connector Must Be v22.0+**
Meta stopped allowing requests to Graph API versions older than v22.0 from September 9, 2025.

Impact:
- Before triggering first Meta sync in Airbyte, verify Facebook Marketing connector version is v22.0 or higher in the source configuration screen.
- Airbyte Cloud should have auto-updated but must be manually confirmed before first sync.

---

**Synthetic Data Updates Required for Meta**

When building the seed script in Step 5, apply these four changes to Meta synthetic data:

1. Attribution windows: Generate rows using 7d_click and 1d_view only. For synthetic dates before January 12 2026, include a step-change drop of 25–35% in reported conversions on January 12 to simulate the real-world measurement break. Add attribution_setting column to flag pre/post break.

2. Historical retention: Add stored_before_retention_limit boolean column to meta_ad_performance. Set true for rows older than 13 months from today. This flags data that would only exist in Supabase because Profit Sentinel stored it before the API retention window closed.

3. Deprecated metrics: Remove unique_actions, 10-second video views, reach/impressions fields. Replace with: total actions, ThruPlay, Media Views equivalents.

4. Campaign structure: Replace ASC/AAC campaign type labels with Advantage+ structures. Remove existing_customer_budget_percentage field entirely.

---

### Destination Configuration
- Host: `aws-1-us-east-1.pooler.supabase.com`
- Port: 5432
- Database: `postgres`
- Schema: `client_{brand_name}` (per-client, not `public`)
- SSL: required

### Schema Propagation Setting
Set to **"Propagate field changes only"** — new columns added automatically, destructive changes flagged for review.

---

### Google Ads API — Real-Data Nuances (Must Handle Before Beta — B-12)

The following gaps are NOT covered by synthetic seed data and will cause failures
when real client Google Ads data connects.

1. Data timing lag: Google Ads conversions lag 24–48 hours. Mart date joins produce false zero-conversion days. Fix: ±1 day tolerance on all cross-source date joins. Add `data_lag_hours` to `client_config` per source.

2. Attribution window mismatch: Google = last-click, Meta = 7d click/1d view. Blended ROAS mixes windows. Fix: Add `attribution_window_note` permanent DQ limitation per source. Disclose in Evidence Stack Layer 0.

3. PMax diagnostic opacity: Google withholds asset-level and search term data for PMax. Agent D cannot populate Evidence Stack Layer 2 for PMax alerts. Fix: permanent DQ limitation `PMAX_DIAGNOSTIC_BLOCKED`. Agent D must disclose: "Google does not provide asset-level reporting for Performance Max campaigns."

4. Stockout date boundary: Google spend for Day N arrives Day N+1. Inventory snapshot at midnight Day N. G1 alert fires a day late or not at all. Fix: same ±1 day tolerance fix as item 1.

5. cost_micros rounding: Summing 50 ad sets in micros then dividing produces fractional differences vs dividing each row. Fix: round `google_spend` to 4 decimal places at mart aggregation.

6. Campaign name instability: Real accounts rename/archive campaigns. Agent D must use `campaign_type` not `campaign_name` in all founder-facing text.

Google Ads seed confirmed 2026-05-21: API v24.1. cost_micros = RAW MICROS. All mart SQL must use SUM(cost_micros)/1000000.0. 14-day zero-spend window: G_SHOP_001 Jul 15–28 2025.

### Inventory Mart Columns — Point-in-Time Limitation (B-9)

mart_causal_chain_daily columns stockout_sku_count through top_sku_inventory_units_pct source from shopify_inventory_levels, which is a point-in-time snapshot (2026-05-31 only), not a time-series. These columns populate as daily Airbyte syncs accumulate. Agent B must not fire G-series inventory alerts until time-series coverage > 30 days.

top_sku_inventory_pct = NULL (pre-B-4): SKU format mismatch between sku_cost_master (AZR-DRESS-HERO-01-XS text) and shopify_inventory_levels (inventory_item_id integer). RESOLVED by B-4 alias map (2026-05-22). Column now populated.


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

Seed scripts (all in connectors/ — tests/ directory does not exist):
[project root]\connectors\seed_shopify.py
[project root]\connectors\seed_meta.py
[project root]\connectors\seed_klaviyo.py
[project root]\connectors\seed_gorgias.py
[project root]\connectors\seed_ga4.py
[project root]\connectors\seed_sentry.py
[project root]\connectors\seed_tiktok.py
[project root]\connectors\seed_loop_returns.py
[project root]\connectors\seed_google_ads.py        ← API v24.1, cost_micros bigint (raw micros ÷ 1,000,000)
[project root]\connectors\seed_sku_cost_master.py   ← 428 rows, 380 active SKUs, FW25 step-change event
[project root]\connectors\patch_script_final.py

Slack bot (to be built):
[project root]\slack-bot\

Frontend (to be built):
[project root]\frontend\

GitHub repository:
https://github.com/anupam313/profit-sentinel

Design docs (git-backed, commit 7402434):
[project root]\docs\
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

---

## 14. Alert Verification Architecture

### Verification Category — Required Field on All Alert Types

Every alert in the 41-type library must be assigned a `verification_category` before Agent B is built. This field is stored in `alert_log` and determines three things: how confidence score is calculated, how outcome is measured, and what language Agent D uses when delivering the alert.

**Category A — Directionally Verifiable**
Outcome is observable in the data independent of what the founder does. The alert's predicted outcome either arrives in the data or it doesn't.

Examples:
- Sizing complaint velocity → return spike (Gorgias fires Day 0, Loop returns arrive Day 8–12 regardless of action)
- CPM trajectory → ROAS drop (both metrics verifiable in data within 5 days)
- Inventory stockout prediction (SKU goes to zero or it doesn't)

Verification: dbt model checks outcome_metric 7 and 14 days post-alert. High confidence accumulation. Can reach 95% precision fastest.

**Category B — Action-Confounded**
Founder's action changes the outcome, making direct verification impossible. If the alert fires and founder acts and ROAS recovers — was it the action or would recovery have happened anyway?

Examples:
- Creative fatigue → refresh creatives
- Contribution margin compression → reduce discount depth
- Email flow degradation → rebuild sequence

Verification: requires cross-client validation (same pattern on brands where founder did NOT act) OR repeated instances on same brand (4th firing has 3 prior instances to assess). Slower confidence accumulation.

**Category C — Structurally Unverifiable**
No clean outcome signal exists. Alert is intelligence, not prediction.

Examples:
- Dark social surge attribution
- Multi-touch journey causal attribution
- Influencer audience decay probability

Verification: probabilistic only. Agent D always communicates explicit uncertainty in plain English — not just a confidence score number. Never presented as high-confidence.

### Pre-Fire Uncertainty Communication (Agent D Requirement)

Every alert must include a plain English uncertainty statement alongside the Layer 0 confidence score. This is enforced at Agent D level — same enforcement as Evidence Stack structure.

Format: "I'm [X]% confident in this signal. What I'm less certain about: [specific element]."

Example for Category B creative fatigue alert:
"I'm 74% confident in this signal. What I'm less certain about: whether the CTR decline reflects genuine creative fatigue or a shift in your target audience composition this week. The pattern matches creative fatigue in 3 of 4 prior occurrences, but audience composition data is limited."

This converts a potentially wrong alert from a trust-killer into a trust-builder. The founder sees intellectual honesty, not false certainty.

### Dismissed Alert Outcome Follow-Up (Agent D Behaviour)

When `action_taken = 'dismiss'` AND `outcome_value_7d` or `outcome_value_14d` confirms the alert was correct:
1. `followup_queued` flips to `true` in alert_log
2. Agent D queues a follow-up message in the original Slack thread
3. Message format: "Following up on the alert you dismissed [N] days ago about [signal]. [Outcome metric] moved [direction] by [amount] — the alert was correct. Estimated impact: $[X]."
4. `followup_sent_at` recorded

No new data model required. Uses existing `alert_log` fields. This is what makes Moat 3 (Founder Decision DNA) tangible — the system shows its track record over time.

### Return Timing Segmentation (Loop Returns)

Loop Returns data must be segmented by return lag in staging tables. Different lag windows indicate different root causes and have different remedies:

| Lag | Segment | Root cause | Remedy |
|-----|---------|-----------|--------|
| Days 1–3 | impulse_regret | Buyer remorse — wrong purchase decision | Post-purchase reassurance email, easy exchange flow |
| Days 7–14 | fit_quality | Product didn't meet expectations on arrival | Size chart accuracy, product photography accuracy |
| Days 21–30 | lifestyle_change | External circumstances changed | Cannot prevent — accept and focus on repurchase |

Add `return_lag_segment` field to Loop staging tables. Alert B-series and return-rate alerts must segment by lag before computing return rate — pooling all three segments produces misleading signal.

**Return reason contamination note:** Loop return reason codes are unreliable. Customers choose the closest available option, not the accurate one. "Didn't like the colour" often means poor product photography. "Too small" often means inaccurate size chart relative to fit model used. When both Gorgias complaint text AND Loop reason code exist for the same order, Agent B weights Gorgias text over Loop reason code for sizing and fit causal chains.

### Self-Extending Graph — Promotion Mechanism

The Fashion Causal Graph is not static. The 41 validated alert types are the seed. The graph grows from real outcome data via the candidate_signals → causal_pattern_validation promotion pipeline.

**Promotion rules:**
- Per-client: 3–5 validated instances on same brand → chain active for that client only
- Cross-network: 10–15 validated instances across clients of same vertical_tag → chain promoted globally for that vertical
- Cross-vertical promotion is prohibited — womenswear validation does not auto-apply to swimwear
- A chain rejected (false positive rate >40% after 10 instances) is marked `rejection_status = 'rejected'` and suppressed permanently until manually reviewed

**Network benchmarks — vertical segmentation requirement:**
`public.network_pattern_benchmarks` must be vertically tagged. All benchmark queries must filter by vertical_tag matching the client's vertical. Pooled cross-vertical benchmarks produce misleading Evidence Stack Layer 3 comparisons — swimwear BFCM behaviour is not comparable to contemporary womenswear BFCM behaviour.

Minimum vertical segments: swimwear / contemporary / premium / activewear / basics

---

## 3.2a — Extended Application Tables (Added May 2026)

These tables were defined during seed script design sessions (May 2026) and are required for the full suppression architecture, DQ intelligence layer, and self-extending causal graph. They are appended here from seed_decisions_gap_f_g.md. All DDLs are locked.

```sql
-- BRAND EVENT CALENDAR
-- Drives all suppression logic in Agent A
-- brand_event_calendar entries are the source of truth for what Agent A
-- treats as contextual vs anomalous. Every suppression scenario (S1–S50)
-- references an entry in this table.
CREATE TABLE public.brand_event_calendar (
    id                      bigint generated always as identity primary key,
    client_id               text not null,
    event_name              text not null,
    event_type              text not null,
    -- Types: collection_launch / sale_period / influencer_activation /
    --        supplier_event / platform_disruption /
    --        platform_disruption_partial / platform_disruption_secondary /
    --        app_change / inventory_event / klaviyo_event /
    --        3pl_transition / photography_update / size_guide_update /
    --        ab_test / cdn_event
    --   (size_guide_update ADDED 2026-06-03, Gap 6 Seam 2 — was missing; it is
    --    a brand-action return event. Brand-action return events
    --    [size_guide_update, photography_update] are written as CONTEXT, never
    --    silent SUPPRESS, while the change-event source is unreliable — see
    --    detection note below and agent_d_build_spec.md GAP 6 Seam 2.)
    start_date              date not null,
    end_date                date,
    affected_category       text[],
    -- Affected product line(s) for scoped events (NULL = brand-wide). ADDED
    --   2026-06-03 (Gap 6 Seam 2): without it a size_guide_update is brand-wide,
    --   forcing brand-wide quiet on a line-specific change (over-suppression).
    --   Until populated, brand-action quiet is brand-wide WITH DISCLOSURE, never
    --   a silent brand-wide mute. Scope governed by the AI-clustering internal
    --   grouping; for metaobject-modeled size charts that reference products,
    --   scope can be derived from those references.
    suppress_alerts         text[],   -- full suppression: State 3
    context_alerts          text[],   -- partial context: State 2
    context_explanation     text,
    residual_threshold_pct  numeric,
    -- Only fire if signal exceeds seasonal explanation by this %
    confidence_decay_type   text,
    -- values: linear / step / exponential
    confidence_decay_start  date,
    confidence_decay_end    date,
    confidence_at_peak      numeric,
    created_at              timestamptz default now()
);

-- BRAND-ACTION RETURN EVENT DETECTION (size_guide_update / photography_update)
-- Added 2026-06-03 (Gap 6 Seam 2). The auto-populate engine
-- (historical_pattern_scan.py) detects events from order volume + discount
-- depth and is BLIND to a size-guide/photography edit (no order/revenue
-- footprint). Detection design, verified against Shopify's current API surface:
--   * Tier 1 — size guide stored as a METAOBJECT (Shopify's standard for size
--     charts): emits an update webhook, filterable by type, with updated-at; can
--     reference specific products (→ affected_category). Silent onboarding probe
--     detects this and subscribes. No founder touch.
--   * Tier 2 — Online Store PAGE: no create/update webhook; detectable only by
--     polling + diff.
--   * Tier 3 — theme code / app: effectively undetectable.
-- A webhook proves an EDIT, not a meaningful change. On an edit, content-diff the
-- size/measurement values → a meaningfulness magnitude (typo ≈ 0; re-measurement
-- high; provisional cutoff, outcome-calibrated). The edit writes a quiet,
-- low-confidence CONTEXT row (event_type = 'size_guide_update'), window =
-- client_config.return_window_days (NOT a fixed 14/21), decaying. It surfaces
-- only if a return-driven margin movement would otherwise fire D1 within the
-- window. NEVER written to suppress_alerts (silent suppress) on an unconfirmed /
-- undetectable edit — context_alerts only. Detection code is a pending Claude
-- Code action (BATCHED post-H), not built here.

-- NETWORK PATTERN BENCHMARKS
-- Cross-client vertical benchmarks for Evidence Stack Layer 3
-- NEVER pool across verticals — swimwear BFCM behaviour is not
-- comparable to contemporary womenswear BFCM behaviour.
-- vertical_tag is mandatory on every query against this table.
CREATE TABLE public.network_pattern_benchmarks (
    id                      bigint generated always as identity primary key,
    archetype_id            text not null,
    vertical_tag            text,
    -- values: contemporary_womenswear / swimwear /
    --         premium / activewear / basics
    metric_name             text not null,
    period_type             text not null,
    -- values: weekly / monthly / seasonal
    period_label            text,
    benchmark_value         numeric,
    benchmark_p25           numeric,
    benchmark_p75           numeric,
    sample_size             integer,
    as_of_date              date,
    created_at              timestamptz default now(),
    unique(archetype_id, vertical_tag, metric_name, period_label)
);

-- SKU COST MASTER
-- Effective-dated landed cost per SKU
-- Four-tier COGS architecture (updated 2026-05-26):
--   Tier 1:   Finaloop CSV export → this table (gold standard, 75% coverage)
--   Tier 1.5: Founder CSV upload — multiple files accepted, SKU-level mapping,
--             fuzzy matching generates reconciliation output for COGS owner review,
--             exact matches written silently, re-upload triggers exact-only matching.
--             Full margin alert enabled after reconciliation complete.
--   Tier 2:   Shopify inventory_items.cost + landed_cost_multiplier (confirmed at
--             onboarding — founder confirms presence and whether it is landed cost)
--   Tier 3:   Founder-stated blended gross margin % by category
-- No Finaloop Airbyte connector exists — CSV export path only.
-- Alert behaviour by tier:
--   Tier 1 / Tier 1.5: Full margin alert with margin % and $ weekly impact
--   Tier 2 / Tier 3:   Driver-only cost pressure alert — no margin % stated,
--                       no $ margin impact. Universal baseline for all brands.
-- NEVER state a margin figure unless cogs_tier is finaloop or founder_csv.
CREATE TABLE public.sku_cost_master (
    id                      bigint generated always as identity primary key,
    client_id               text not null,
    sku                     text not null,
    effective_date          date not null,
    unit_cost               numeric not null,
    landed_cost_multiplier  numeric default 1.28,
    -- 1.28 = +28% for freight, duties, fulfilment (default assumption)
    -- Overridden at onboarding if founder confirms actual multiplier
    landed_cost             numeric generated always as
                              (unit_cost * landed_cost_multiplier) stored,
    cogs_tier               text not null,
    -- values: finaloop / founder_csv / shopify_derived / founder_stated
    source_file             text,
    -- Finaloop or founder CSV filename if cogs_tier = finaloop / founder_csv
    original_currency       text default 'USD',
    -- Currency from source file before USD conversion
    fx_rate_used            numeric,
    -- Founder-stated FX rate applied at upload time. NULL if original_currency = USD.
    -- NEVER use live FX rates — historical COGS locked at PO rate.
    active                  boolean default true,
    -- false = SKU no longer in live Shopify catalogue but retained for history
    -- When inactive SKU relaunches → surface to founder for confirmation
    landed_confirmed        boolean default false,
    -- true = founder confirmed unit_cost is already landed (no multiplier needed)
    upload_batch_id         text,
    -- ties row to specific CSV upload batch for auditability and version conflict resolution
    created_at              timestamptz default now(),
    unique(client_id, sku, effective_date)
);

-- CSV UPLOAD VALIDATION RULES (enforced by /connectors/cogs_csv_processor.py)
-- 1. Format: CSV and .xlsx only. Reject PDFs and images with specific message.
-- 2. Minimum columns: ≥1 SKU-like column + ≥1 cost-like column. Reject if absent.
-- 3. Currency: ask "Are all costs USD?" at upload.
--    If no: ask which currencies + founder-stated FX rate per currency.
--    If currency column in file: use per row. Blank currency rows → flag, write rest.
--    Multiple currencies in cost column with no currency column → reject file.
-- 4. Landed vs ex-factory: ask once per file. Ex-factory → apply multiplier.
-- 5. Zero/negative cost values → flag, do not write.
-- 6. Duplicate SKU in same file with different costs → flag both, ask founder.
-- 7. Version conflict (SKU in prior file, new file has different cost) →
--    surface conflict, ask founder to confirm update. Never silent overwrite.
-- SKU MATCHING:
--   Normalise both sides: lowercase, strip special chars, strip common prefixes.
--   Exact match → write silently to sku_cost_master.
--   Fuzzy match → reconciliation output file only. NEVER auto-write.
--   No match → reconciliation output file, flag as needs cost.
-- RECONCILIATION OUTPUT FILE COLUMNS:
--   Shopify SKU | Shopify Product Name | Match Found | Matched CSV SKU |
--   Confidence | Unit Cost | Currency | Landed/Ex-factory | Action Needed
--   Sent to cogs_owner_contact immediately after upload.
--   Founder sees: "We've sent [X] SKUs to [email] for review."

-- SUPPRESSION LOG
-- Every suppression event logged for auditability
-- Founder can query: "Why didn't I get an alert on [date]?"
-- Agent A writes to this table on every State 2, 3, or 4 suppression.
CREATE TABLE public.suppression_log (
    id                      bigint generated always as identity primary key,
    client_id               text not null,
    suppressed_at           timestamptz default now(),
    alert_type              text not null,
    suppression_state       integer not null,
    -- 2 = Fire with Context, 3 = Suppress+Explain, 4 = Suppress+DQ Flag
    suppression_reason      text not null,
    brand_event_calendar_id bigint references public.brand_event_calendar(id),
    signal_value            numeric,
    threshold_value         numeric,
    variance_explained_pct  numeric,
    -- What % of the signal the calendar event explains (seasonal ATTRIBUTION)
    seasonal_typicality_state integer,
    -- Mix-shift driver ONLY. Carries the seasonal-typicality grade
    --   (State 1 / 2 / 3) of a category margin-mix shift, derived from the
    --   brand's own prior same-season MARGIN band (event-anchored IQR
    --   percentile position; admissibility + state ceiling per Gap 6
    --   Dependency 1). S41-decayed.
    -- SEPARATE from variance_explained_pct on purpose: typicality is a
    --   different quantity from seasonal attribution. Overloading
    --   variance_explained_pct would corrupt S42 stacking / S39 learning.
    -- NULL for any suppression not produced by the mix-shift driver.
    context_explanation     text
);

-- ALERT DATA LINEAGE
-- Which source rows contributed to each alert
-- Required for Agent D Evidence Stack Layer 2 verifiable proof
-- "Verify in Meta Ads Manager — these figures match exactly"
CREATE TABLE public.alert_data_lineage (
    id                      bigint generated always as identity primary key,
    alert_log_id            bigint references public.alert_log(id),
    source_table            text not null,
    source_schema           text not null,
    source_row_ids          text[],
    -- Array of row IDs from source table contributing to this alert
    row_count               integer,
    date_range_start        date,
    date_range_end          date,
    contribution_weight     numeric,
    -- Matches DQ weight for this source in this alert type
    created_at              timestamptz default now()
);

-- DQ METRIC SCORES
-- Multi-dimensional DQ scores per source per client per day
-- Replaces the single dq_score field in client_config
-- One row per client per source per day, updated on each sync cycle
-- Weighted composite drives alert confidence calculations
CREATE TABLE public.dq_metric_scores (
    id                      bigint generated always as identity primary key,
    client_id               text not null,
    source_name             text not null,
    -- values: shopify_orders / meta_ad_performance / klaviyo /
    --         gorgias / ga4 / sentry / tiktok / loop_returns
    score_date              date not null,
    completeness_score      numeric,  -- 0–100
    timeliness_score        numeric,  -- 0–100
    consistency_score       numeric,  -- 0–100
    overall_score           numeric,  -- weighted composite
    issue_count             integer default 0,
    active_issues           text[],
    -- Array of active DQ issue codes (e.g. 'UTM_MISSING', 'CAPI_DEDUP')
    updated_at              timestamptz default now(),
    unique(client_id, source_name, score_date)
);

**Per-source DQ pre-checks (run by historical_pattern_scan.py at onboarding, written to dq_metric_scores):**

All sources receive a DQ pre-check. Results written to `dq_metric_scores` before scan runs. Chains for sources below threshold get `scan_skipped_reason` set on `causal_pattern_validation`.

| Source | Key DQ check | Skip threshold |
|--------|-------------|---------------|
| Gorgias | Tag coverage rate (% closed tickets with ≥1 tag). Tag vocabulary size (flag >100 or <5). Compound tag presence (any `return-*` or `sizing-*` pattern). Return/sizing tag rate vs Loop return rate (large divergence = undertag). Agent tagging variance (if multiple agents). | Tag coverage <50% → `scan_skipped_reason = 'gorgias_tagging_insufficient'` on C1 and Gorgias-dependent chains |
| Meta | Attribution window break (Jan 12 2026 handled). % spend with no matched Shopify order. | >30% unmatched → low DQ score, scan proceeds with caveat |
| TikTok | Creator-to-SKU mapping coverage. | <70% mapped → low DQ score |
| Loop Returns | Return reason code coverage. | >40% null or "Other" → low DQ score |
| Klaviyo | Active post-purchase flow present. | No active flow → D5/E4 chains skipped |
| GA4 | Checkout funnel step completeness. | Missing steps → F1/F5 chains skipped |
| Sentry | Coverage window days. | <30 days → `scan_skipped_reason = 'insufficient_history'` on F2/F4 |

**Note:** NLP classifier for Gorgias ticket bodies (to extract return reasons independently of tags) is discovery-gated — build only after customer discovery validates Alert 5 demand and confirms tagging inconsistency across 3+ beta clients. Do not build until signal.

-- DQ EVENTS
-- Individual DQ issues detected, active, and resolved
-- Feeds DQ improvement arc: 81 (Month 1) → 93 (Month 24)
CREATE TABLE public.dq_events (
    id                      bigint generated always as identity primary key,
    client_id               text not null,
    source_name             text not null,
    issue_code              text not null,
    detected_at             timestamptz not null,
    resolved_at             timestamptz,
    issue_description       text,
    impact_alert_types      text[],
    -- Alert types whose confidence score is affected while issue is active
    severity                text,
    -- values: low / medium / high / critical
    auto_resolved           boolean default false
);

-- PERMANENT DQ LIMITATIONS
-- Structural data limitations that never resolve
-- Disclosed in Evidence Stack Layer 0 of all affected alerts
-- Examples: iOS ATT modeled conversions, dark social unattributable orders
CREATE TABLE public.permanent_dq_limitations (
    id                      bigint generated always as identity primary key,
    client_id               text not null,
    limitation_code         text not null,
    description             text not null,
    affected_alert_types    text[],
    max_confidence_cap      numeric,
    -- Confidence for affected alerts capped at this value permanently
    disclosure_text         text,
    -- Plain English text for Layer 0 Evidence Stack disclosure
    created_at              timestamptz default now(),
    unique(client_id, limitation_code)
);

-- SYNTHETIC TOUCHPOINT JOURNEY
-- Multi-touch order attribution paths for client_azure_co only
-- 35–45% of orders have multi-touch journeys seeded explicitly:
--   20%: TikTok impression Day 1 → Meta click Day 3–5
--   10%: Klaviyo email open → Meta retargeting click Day 2
--    8%: TikTok influencer Day 1 → Direct visit Day 6
--    7%: Three-channel journey (TikTok → Klaviyo → Meta)
CREATE TABLE client_azure_co.synthetic_touchpoint_journey (
    order_id                text not null,
    touchpoint_sequence     integer not null,
    channel                 text,
    touchpoint_date         date,
    touchpoint_type         text,
    -- values: impression / click / email_open
    campaign_id             text,
    influencer_id           text,
    -- nullable — only populated on influencer touchpoints
    primary key (order_id, touchpoint_sequence)
);
```

### alert_log — Additional Fields (ALTER TABLE, May 2026)

The following fields were added to `public.alert_log` during seed script design. They extend the original DDL in Section 3.2 above:

```sql
ALTER TABLE public.alert_log
    ADD COLUMN IF NOT EXISTS alert_type              text,
    -- NOTE: live column is alert_type, not signal_type (schema drift from DDL)
    ADD COLUMN IF NOT EXISTS dismissal_correct       boolean,
    -- true if dismissed AND outcome later confirmed alert was correct
    ADD COLUMN IF NOT EXISTS revenue_impact_missed   numeric,
    -- estimated revenue impact of dismissing a correct alert
    ADD COLUMN IF NOT EXISTS fatigue_period_active   boolean default false,
    -- true when alert fired during a system-detected alert fatigue window
    ADD COLUMN IF NOT EXISTS fatigue_reason          text,
    -- e.g. 'founder_stress_external_event'
    ADD COLUMN IF NOT EXISTS suppression_type        text,
    -- values: state_2 / state_3 / state_4 (if suppressed)
    ADD COLUMN IF NOT EXISTS escalation_level        integer default 1,
    -- 1 = first firing, 2 = 48h repeat, 3 = 72h escalation
    ADD COLUMN IF NOT EXISTS alert_instance_number   integer default 1;
    -- tracks repeat firings of same alert type on same client
```

**Schema drift note:** The live `alert_log` table uses `alert_type` as the column name. The original DDL in Section 3.2 shows `signal_type`. All dbt models and agent code must use `alert_type`. Do not use `signal_type` in any query against the live database.

**Session 3 schema drift additions (2026-05-19):**
- `stg_klaviyo_profiles` actual column names: `profile_id` (not `customer_id`), `vip_status` (not `is_vip`). Any mart model or agent joining this table must use these names.
- `stg_loop_refunds` not present — use `stg_loop_returns` for refund lag calculations.
- `stg_meta_ad_performance` has no `attributed_revenue` column — proxy: `spend × purchase_roas`.
- `stg_klaviyo_flows` has no date column — use `stg_klaviyo_email_events` for all time-series Klaviyo mart CTEs.
- GA4 tables (`ga4_pages`, `ga4_devices`) absent in synthetic data — NULL mart columns expected until real client onboards.

---

## 3.2b — causal_graph.py Structure Definition (Added May 21 2026)

`agents/causal_graph.py` is a structured Python dict. One entry per chain.
Architecture decision: hardcoded registry permanently — not a DAG traversal engine.
Every chain must be practitioner-validated before activation. Novel chains promoted
via `candidate_signals` pipeline, not algorithmic traversal.

### Entry structure

```python
FASHION_CAUSAL_GRAPH = {
    "A1": {
        "causal_chain_id":          "A1",
        "leading_signal_column":    "blended_roas",
        # Exact column name in mart_causal_chain_daily (or mart_table if different)
        "leading_signal_direction": "declining",
        # values: declining / rising / any
        "outcome_column":           "net_revenue",
        "outcome_direction":        "declining",
        "lag_days":                 0,
        # Expected lag between leading signal breach and outcome breach
        "corroborating_signals":    ["return_rate_pct"],
        # List of mart columns Agent B checks to satisfy multi-signal confirmation gate
        # candidate and provisional chains require ≥1 corroborating signal trending
        # in predicted direction before alert fires. core chains: gate removed.
        "mart_table":               "mart_causal_chain_daily",
        # values: mart_causal_chain_daily / mart_customer_segments_daily /
        #         mart_return_rate_by_sku / system_table
        "status":                   "active",
        # values:
        #   active           — leading signal column exists in mart, Agent B queries today
        #   active_proxy     — proxy column used, true signal column missing, uncertainty
        #                      disclosure added to Evidence Stack Layer 0
        #   mart_column_missing — data exists in staging, mart column not yet built,
        #                         Agent B skips with skip reason logged
        "routing":                  None,
        # None for A–G series (business alerts)
        # H-series values: internal / informational / founder_action_required
        # internal: PS infrastructure problem — internal Slack only
        # informational: source platform problem — brief founder message, no action
        # founder_action_required: founder config causing DQ loss — missed opportunity framing
        "verification_category":    "A",
        # A: directionally verifiable in data independent of founder action
        # B: action-confounded — requires cross-client validation
        # C: structurally unverifiable — explicit uncertainty always communicated
    },
    # ... all 56 chains follow same structure
}
```

### H-series routing protocol (Agent D enforcement)

**routing: internal**
- Post to PS internal Slack immediately with full technical detail
- Founder-facing message only if failure persists beyond one sync cycle:
  "We've detected an issue with your data pipeline. We're working on it and
  will update you once it's resolved."
- Resolution message when fixed: "Your data pipeline is back to normal.
  All alerts are live again."
- No time estimates, no technical detail in founder message

**routing: informational**
- Brief contextual message to founder, not an alert
- No action required framing
- Example: "Meta's API is experiencing delays. Your channel data may be up
  to 6 hours behind. We'll alert you once it's resolved."

**routing: founder_action_required**
- Missed opportunity framing, not error framing
- Example: "Your Gorgias tagging rate dropped 40% this week — I can no
  longer reliably predict return spikes from complaint data. Worth a
  5-minute fix."

### H-series routing classification

| Chain | Source table | Routing |
|-------|-------------|---------|
| H1 — Airbyte sync gap | `dq_metric_scores` | `internal` |
| H2 — Unexplained traffic source shift | `dq_metric_scores` | `informational` |
| H3 — UTM coverage degrading | `dq_metric_scores` | `founder_action_required` |
| H4 — Klaviyo/Shopify revenue gap | `dq_metric_scores` | `informational` |
| H5 — GA4/Shopify order count gap | `dq_metric_scores` | `informational` |
| H6 — Paid spend dropped to zero | `dq_metric_scores` | `founder_action_required` |
| H7 — API rate limit | `dq_events` | `informational` |
| H8 — Sentry instrumentation gap | `dq_metric_scores` | `founder_action_required` |
| H9 — Meta CAPI dedup failure | `dq_events` | `founder_action_required` |
| H10 — Shopify infrastructure event | `dq_events` | `informational` |
| H11 — DQ score below threshold | `dq_metric_scores` | `internal` |
| H12 — New DQ issue / schema change | `schema_versions` | `internal` |
| H13 — DQ improvement confirmed | `dq_metric_scores` | `internal` |
| H14 — Cascade DQ chain | `dq_events` | `internal` |
| H15 — Gorgias tag inconsistency | `dq_metric_scores` | `founder_action_required` |
| H16 — Meta attribution window break | `dq_events` | `informational` |
| H17 — iOS ATT modeled conversion | `permanent_dq_limitations` | `informational` |
| H18 — Klaviyo open rate unreliable | `permanent_dq_limitations` | `informational` |
| H19 — Permanent DQ limitation active | `permanent_dq_limitations` | `informational` |
| H20 — New SKU COGS Gap | `sku_cost_master` JOIN `shopify_product_variants` | `founder_action_required` |

---

## 3.2c — mart_customer_segments_daily DDL (Added May 21 2026)

```sql
-- CUSTOMER SEGMENT DAILY MART
-- Grain: date × segment
-- Segments: Explorers / Regulars / Loyalists / Advocates
-- Boundaries: calibrated once at onboarding by historical_pattern_scan.py
--   using percentile breakpoints on client's own order frequency distribution.
--   Written to client_config. Locked after onboarding — never auto-adjusted.
--   Fallback to vertical defaults if repeat_customer_count < 500 at onboarding.
-- Default boundaries (contemporary womenswear):
--   Explorer:  1 order        (client_config.explorer_max_orders default 1)
--   Regular:   2–3 orders     (client_config.regular_max_orders default 3)
--   Loyalist:  4–6 orders     (client_config.loyalist_max_orders default 6)
--   Advocate:  7+ orders      (client_config.advocate_min_orders default 7)
-- Minimum significance: if segment_pct_of_revenue < client_config.segment_significance_min_revenue_pct
--   (default 2%), Agent B suppresses segment-specific alerts and sends informational note instead.
-- Used by: C7, E2, E3, A2 (new_customer component)
CREATE TABLE client_azure_co_marts.mart_customer_segments_daily (
    date                            date not null,
    client_id                       text not null,
    segment                         text not null,
    -- values: explorer / regular / loyalist / advocate
    segment_customer_count          integer,
    -- absolute number of customers in segment on this date
    segment_pct_of_total_customers  numeric,
    -- segment_customer_count / total active customers
    segment_pct_of_total_revenue    numeric,
    -- segment revenue / total revenue (trailing 90 days)
    segment_avg_roas                numeric,
    -- revenue attributed to segment / acquisition cost for segment cohort
    segment_return_rate_7d          numeric,
    -- returns from segment customers / orders from segment customers, trailing 7 days
    segment_aov_7d                  numeric,
    -- average order value for segment, trailing 7 days
    any_source_stale                boolean default false,
    data_as_of                      timestamptz,
    primary key (date, client_id, segment)
);
```

**Onboarding calibration logic (historical_pattern_scan.py addition):**
After completing Phase 2 (known chain validation), run order frequency
distribution analysis:
1. Query all customers with 2+ orders from Shopify staging
2. Compute percentile breakpoints at p33, p66, p90 of order frequency
3. If natural cluster gaps exist (>20% frequency jump at breakpoint), use
   cluster boundaries. Otherwise use percentile defaults.
4. Write computed thresholds to `client_config` segment columns
5. If repeat_customer_count < 500: skip calibration, use vertical defaults,
   log `segment_calibration_status = 'insufficient_data'` in client_config

**Fallback to vertical defaults message (onboarding completion):**
"We don't yet have enough repeat purchase history to calibrate your customer
segments precisely — using contemporary womenswear defaults. We'll recalibrate
after 6 months of data."

---

## 3.2d — client_config ALTER TABLE (Added May 21 2026)

Customer segment threshold columns and calibration status. Run before
building `mart_customer_segments_daily`.

```sql
ALTER TABLE public.client_config
    ADD COLUMN IF NOT EXISTS repeat_customer_order_minimum    integer default 2,
    -- Minimum prior orders to classify as repeat customer for return rate calculations
    -- Used by: repeat_customer_return_rate_7d mart column
    ADD COLUMN IF NOT EXISTS explorer_max_orders              integer default 1,
    ADD COLUMN IF NOT EXISTS regular_max_orders               integer default 3,
    ADD COLUMN IF NOT EXISTS loyalist_max_orders              integer default 6,
    ADD COLUMN IF NOT EXISTS advocate_min_orders              integer default 7,
    ADD COLUMN IF NOT EXISTS segment_significance_min_revenue_pct  numeric default 2.0,
    -- Agent B suppresses segment-specific alerts when segment revenue share
    -- falls below this threshold. Prevents noise from micro-segments.
    ADD COLUMN IF NOT EXISTS segment_calibration_status       text default 'pending';
    -- values: pending / calibrated / insufficient_data (fallback to vertical defaults)
```


---

## 3.2e — B-4 Seed Schema Extensions (Added May 22 2026)

SKU-to-ad attribution via content_ids. All changes landed 2026-05-22.
dbt PASS=65 WARN=0 ERROR=0. All 8 cross-source chain checks pass.

### meta_ad_performance — new columns

| Column | Type | Notes |
|--------|------|-------|
| campaign_objective | text | OUTCOME_SALES / OUTCOME_AWARENESS / OUTCOME_TRAFFIC / OUTCOME_ENGAGEMENT. ROAS = NULL for OUTCOME_AWARENESS rows. |
| attribution_type | text | 'blended_7d_click_1d_view' default. Retargeting has both 'click_7d' and 'blended' rows on same date to demonstrate attribution gap. |
| click_only_purchase_value | numeric | 7d-click-only revenue (strips view-through). Retargeting: 75–85% of conversion_value. Prospecting: 30–45%. Awareness: NULL. Structural disclosure only — no recommendation logic attached. |
| content_ids | text[] | Array of Shopify product_ids from Meta Purchase event. OUTCOME_SALES + conversions: 1–4 IDs. OUTCOME_AWARENESS / zero conversions: empty array {}. |

### tiktok_ad_performance — new columns

| Column | Type | Notes |
|--------|------|-------|
| campaign_objective | text | API field: objective_type. PRODUCT_SALES / TRAFFIC / REACH / VIDEO_VIEWS / LEAD_GENERATION. ROAS = NULL for REACH and VIDEO_VIEWS. |
| content_id | text | Single product_id from CompletePayment event. PRODUCT_SALES: populated. REACH/VIDEO_VIEWS: NULL. TRAFFIC/LEAD_GEN: 20% populated. |
| content_id_confidence | text | high (35%) / low (25%) / none (40%). high = TikTok Shop product tagged. low = inferred from catalogue. none = UGC/awareness campaigns. |
| attribution_window | text | '1d_view_7d_click' for all rows. |

### google_ads_performance — new columns (added to existing 9 B-9 columns)

| Column | Type | Notes |
|--------|------|-------|
| campaign_objective | text | Derived from campaign_type. SEARCH/SHOPPING/PMAX = 'SALES'. VIDEO/DEMAND_GEN = 'AWARENESS_AND_CONSIDERATION'. |
| product_id | text | SHOPPING rows only: Shopify product_id from feed. PMAX/SEARCH/VIDEO/DEMAND_GEN: NULL. |
| reason_product_id_null | text | NULL for SHOPPING. PMAX: 'PMAX_PRODUCT_CONVERSION_WITHHELD'. Others: 'CAMPAIGN_TYPE_NO_PRODUCT_SIGNAL'. |
| video_quartile_p25_rate | numeric | VIDEO rows only. Month 3-4 high-performing: 0.55-0.65. Month 8-9 poor: 0.35-0.45. |
| video_quartile_p50_rate | numeric | VIDEO rows only. |
| video_quartile_p75_rate | numeric | VIDEO rows only. |
| video_quartile_p100_rate | numeric | VIDEO rows only. Month 3-4: 0.16-0.18. Month 8-9 (poor creative): 0.06-0.09. |
| video_view_rate | numeric | VIDEO rows only. Range: 0.15-0.45. |
| average_cpv | numeric | VIDEO rows only. Range: $0.02-$0.06. |

Total rows: 5,137. cost_micros remains raw bigint. All 9 B-9 hardening columns unchanged.

### gorgias_tickets — new columns

| Column | Type | Notes |
|--------|------|-------|
| product_id | text | Coverage: sizing_issue 85% / product_quality 70% / wismo 5% / others 30%. Uses HERO_DRESS product_id pool. |
| order_id | text | 70% of product_id-populated rows also have matching Shopify order_id. |

BFCM window (Oct 28 - Nov 14 2024): sizing_issue tickets 3x baseline (35-42% vs 14-18% baseline). customer_email matches Shopify orders for HERO_DRESS purchases at 84% rate.

### stg_loop_returns — changes

| Change | Detail |
|--------|--------|
| product_id | Added. Uses HERO_DRESS product_id pool. |
| HERO_DRESS BFCM return rate | Elevated to 34-38% (Nov 2024) vs 18-22% brand average. return_reason: 'sizing'. |
| customer_email chain closure | BFCM elevated return rows customer_email matches Gorgias sizing_issue tickets. Three-source chain (Gorgias to Shopify to Loop) verified via CHECK 1. |

### mart_causal_chain_daily — new column

| Column | Type | Notes |
|--------|------|-------|
| campaign_sku_return_rate_7d | numeric | SKU-weighted return rate (trailing 7d) of actively promoted products (Meta + TikTok content_ids). Elevated = high-return SKUs being spent against. Primary signal for A1 and B-series. NULL when no content_ids. No not_null test — NULL condition in schema.yml. |

### Inventory blocker resolved
top_sku_inventory_pct was NULL pre-B-4 due to SKU format mismatch (sku_cost_master text vs shopify_inventory_levels integer). B-4 alias map bridges these. Column now populated.

### Dropped signals — permanently closed
- ROAS < 1.0 pause recommendation: never implement without multi-signal confirmation + Layer 3 historical precedent + financial stake quantified.
- Upper-funnel CPM to organic lift correlation: never implement without matched market design, holdout control, 4-week test window, and statistical disclosure.

### PS white space confirmed
Neither Triple Whale nor Northbeam deducts returns from ROAS or connects campaign content_ids to return velocity by SKU. B-4 builds the data foundation for both PS differentiators.

# Section 10 — Data Quality Intelligence Layer
## Status: Locked — 2026-05-23
## Append to: technical_architecture.md

---

## PURPOSE

The Data Quality Intelligence Layer (DQIL) is a platform-wide architectural
component that sits across every alert PS fires. It is not an error handler
or a warning system. It is an active intelligence system with four
responsibilities:

1. Per-source gap detection at onboarding and monthly
2. Per-alert confidence scoring at fire time
3. Gap quantification with revenue impact estimate
4. Proactive gap alerts separate from causal chain alerts

The goal is to turn data quality gaps into founder-facing opportunities —
not warnings. Every gap is framed as: "Here is what you are missing and
what it is costing you."

---

## EXISTING INFRASTRUCTURE — DQIL BUILDS ON THESE

The following tables already exist in the architecture and feed the DQIL:

| Table | Role in DQIL |
|-------|-------------|
| `dq_metric_scores` | Per-source DQ scores used for confidence classification |
| `permanent_dq_limitations` | Structural limitations that cannot be fixed by connecting a new source |
| `alert_data_lineage` | Maps each alert to its source dependencies |
| `suppression_log` | Records suppressed alerts with reason |
| `dq_events` | Point-in-time DQ incidents per source |

---

## RESPONSIBILITY 1 — PER-SOURCE GAP DETECTION

### At onboarding (one-time full scan)
Runs automatically as part of onboarding Step 6 (historical pattern scan).
For each connected source, checks:
- Is the source connected and syncing?
- Are key tables populated with sufficient rows?
- Are critical columns populated (not NULL > acceptable threshold)?
- Are specific features enabled (e.g. GA4 Enhanced Ecommerce,
  Klaviyo back-in-stock flow, Sentry release tags)?

Results written to `permanent_dq_limitations` per source with:
- `limitation_type`: missing_source / missing_feature / sparse_data /
  structural_gap
- `alert_ids_affected`: which causal chain IDs cannot fire or fire with
  reduced confidence
- `fixable`: boolean — can founder action fix this?
- `fix_instructions`: if fixable, exact steps

### Monthly (incremental scan)
Scheduled 1st of each month. Checks:
- New connectors detected via Airbyte API inventory check
- Any previously fixable gaps now resolved (e.g. GA4 connected,
  Klaviyo flow configured)
- Any new gaps introduced (e.g. Sentry sampling rate changed,
  Meta API version deprecated)

**Connector lifecycle trigger:** When Airbyte inventory check detects
a new source that was absent at onboarding:
1. Trigger partial re-onboarding for that source only
2. Re-run gap detection for alert_ids affected by that source
3. Send founder Slack message: *"We've detected [source] is now connected.
   [N] additional alerts are now active — here's what we found in your
   first week of data."*
4. Update `permanent_dq_limitations` — mark previously missing gaps as resolved

---

## RESPONSIBILITY 2 — PER-ALERT CONFIDENCE SCORING

### Confidence classification
Every alert that fires is classified at fire time based on the DQ scores
of its source dependencies:

| Classification | Condition | Agent D behaviour |
|---------------|-----------|------------------|
| High confidence | All source DQ scores > 80, no active dq_events | Fire cleanly — no disclosure |
| Structural limitation | `permanent_dq_limitations` entry exists for this alert | Collapsed "ⓘ Data note" footnote — always shown |
| Low confidence | Any source DQ score < 50 OR active dq_event affecting this alert | Explicit low confidence disclosure in alert body |

### Critical design principle — no confidence tags on clean alerts
Do NOT show confidence tags, scores, or banners on high-confidence alerts.
A founder receiving a clean alert should see a clean alert. Confidence
infrastructure is invisible when data is good.

Confidence disclosure appears ONLY when:
- Structural limitation exists (collapsed footnote)
- Active DQ event affecting the alert (inline disclosure)
- Low confidence classification (explicit statement)

### Collapsed footnote format (structural limitations)
```
ⓘ Data note [collapsed by default — tap to expand]
[Specific limitation — e.g. "This alert uses channel-level ROAS.
SKU-level attribution requires catalogue feed connection."]
```

Shown on every firing of the affected alert — not just at onboarding.
Collapsed by default — not intrusive. Founder can ignore or investigate.

### Low confidence inline disclosure format
```
⚠️ Data quality note: [specific issue — e.g. "Sentry sampling rate
changed on [date] — error counts may be understated by up to 20%.
Treat directionally."]
```

---

## RESPONSIBILITY 3 — GAP QUANTIFICATION

### Purpose
When a gap exists that prevents an alert from firing, quantify what the
founder is missing in dollar terms. Frame as opportunity, not error.

### Revenue impact estimate construction
**Primary source:** Founder's own historical data always first.
- If the brand has prior data showing the impact: use actual figures
- If insufficient history: use multiplier ranges (see below)

**Range display — always a range, never a single number:**
Upper bound must not exceed 3x lower bound. If it does — insufficient
data to estimate reliably. Show: *"Insufficient data to estimate — 
connect [source] to enable this alert."*

**Multiplier ranges by alert type:**
These are directional starting points — replace with real client data
as it accumulates:

| Alert type | Conservative | Optimistic | Basis |
|-----------|-------------|-----------|-------|
| Back-in-stock (< 2wks waitlist) | 2.0x store CVR | 2.5x store CVR | Intent recency |
| Back-in-stock (2–6wks waitlist) | 1.5x store CVR | 2.0x store CVR | Moderate decay |
| Back-in-stock (> 6wks waitlist) | 1.0x store CVR | 1.5x store CVR | Significant decay |
| Mobile checkout (F1 absent) | Current CVR loss × mobile session share | — | Direct |
| Funnel step (F5 absent) | Step abandonment × AOV | — | Direct |

**Industry benchmark prohibition:** Never use external industry benchmarks
in founder-facing gap quantification. Either use the founder's own data
or use the multiplier ranges above labelled as directional estimates.

### Gap quantification message format
```
💡 Monitoring Gap — [Alert name] Not Active

[N] alert type events may have occurred in the last 30 days that
we couldn't detect.

Estimated missed opportunity: $[X]–$[Y]
Based on: [founder's own data / directional estimate]

To activate this alert: [one specific action required]
[Link to settings or developer instructions]
```

---

## RESPONSIBILITY 4 — PROACTIVE GAP ALERTS

### Gap opportunity ranking
When multiple gaps exist simultaneously, never surface all at once.
Ranked by estimated dollar impact — highest impact gap shown first.
One gap opportunity per weekly summary — progressive disclosure only.

**Never show more than one gap opportunity at a time regardless of how
many gaps exist.** Founder overwhelm leads to no action.

### Weekly summary gap slot
One slot in every weekly Slack summary reserved for the highest-impact
unresolved gap. Format: gap quantification message above.

Once a gap is resolved (new source connected, feature configured):
- Mark resolved in `permanent_dq_limitations`
- Send one-time resolution confirmation to founder
- Surface next highest-impact unresolved gap in following weekly summary

### Gap priority order (default ranking — override by actual dollar impact)
1. GA4 Enhanced Ecommerce step-level events (F1, F5)
2. Klaviyo back-in-stock flow not configured (G4)
3. Meta/TikTok catalogue feed for SKU-level attribution (G1 missed revenue, G3)
4. Sentry release tags not configured (F2, F4 diagnostic depth)
5. UTM coverage below threshold (attribution accuracy across A-series)
6. SKU cost master incomplete (D-series margin accuracy)

---

## MARKETING ATTRIBUTION — SPECIAL HANDLING

### Why marketing sources require special treatment
Meta, TikTok, and Google do not provide reliable SKU-level spend attribution
via standard API connections. Catalogue ads dynamically allocate spend across
SKUs — the platform decides, not the brand.

This is a structural limitation, not a data quality failure. It cannot be
resolved by better tagging or more careful setup. It is permanent at the
API level for Phase 1.

### Consequence for alert confidence
Any alert that depends on SKU-level spend attribution (G1 missed revenue,
G3) carries a permanent structural limitation footnote:
*"Missed revenue estimate uses channel-level ROAS as proxy. SKU-level
spend attribution requires catalogue feed integration."*

ROAS alerts that fire at channel level (A1, A2, A3) are HIGH CONFIDENCE —
channel-level data is reliable. Do not apply structural limitation footnotes
to channel-level ROAS alerts.

### UTM coverage — not a proxy for marketing sophistication
UTM tagging discipline does not predict whether a brand tracks ROAS reliably.
Brands using Meta/TikTok native attribution or Triple Whale/Northbeam do not
need UTM coverage. Do not gate marketing alerts on UTM coverage threshold
unless the specific alert explicitly requires GA4 session-source data.

---

## PERMANENT DQ LIMITATIONS — KNOWN AT BUILD TIME

These are pre-seeded into `permanent_dq_limitations` at synthetic data
build time. Each real client onboarding will produce its own entries.

| Limitation | Affected alerts | Fixable | Fix |
|-----------|----------------|---------|-----|
| GA4 Enhanced Ecommerce absent | F1, F5 | Yes | Developer enables step-level events |
| Klaviyo back-in-stock flow not triggered | G4 | Yes | Configure flow in Klaviyo |
| Sentry release tags absent | F2, F4 (diagnostic depth only) | Yes | Configure in Sentry project settings |
| SKU-level spend mapping absent | G1 (missed revenue), G3 | Partial | Catalogue feed integration (Phase 2) |
| GA4 source absent | F3 (deferred), F1, F5 | Yes | Connect GA4 via Airbyte |
| Sentry 90-day window cap | F2, F4 historical baselines | No — structural | Use rolling baseline only |
| Meta/TikTok device-based attribution | A1, A3, A4 cross-device | No — structural | Noted in alert footnote |

---

## DATA FRESHNESS — STALENESS HANDLING

Existing staleness columns already in mart (`any_source_stale`,
`data_as_of`, per-source `last_synced_at`) feed the DQIL.

**Staleness disclosure rule:**
If `any_source_stale = true` for sources feeding a fired alert:
- Add to alert body: *"Note: [source name] data is [X] hours old —
  figures reflect data as of [data_as_of timestamp]."*
- Do not suppress the alert — stale data alert is better than no alert
- Agent D must check staleness at render time, not at Agent A scan time

**Critical staleness threshold by source:**

| Source | Acceptable staleness | Action if exceeded |
|--------|--------------------|--------------------|
| Sentry | 2 hours | Re-trigger sync before firing F2/F4 |
| Shopify | 6 hours | Disclose in alert |
| Meta/TikTok | 24 hours | Disclose in alert |
| GA4 | 48 hours | Disclose in alert |
| Klaviyo | 6 hours | Disclose in alert |
| Loop Returns | 24 hours | Disclose in alert |

---

## SYNC CADENCE REQUIREMENTS

| Source | Required cadence | Reason |
|--------|-----------------|--------|
| Sentry | 1-hour minimum | F2 checkout errors — 6-hour lag makes alert a post-mortem |
| Shopify | 6-hour | Agent A runs every 6 hours |
| Meta/TikTok/Google | 6-hour | ROAS alerts — daily is too stale |
| Klaviyo | 6-hour | E-series email alerts |
| GA4 | Daily | GA4 data processing lag is 24–48 hours natively |
| Loop Returns | Daily | Return processing lag acceptable at 24 hours |
| Gorgias | 6-hour | C1 sizing complaint velocity — daily too slow |

---

## INTERACTION WITH AGENT B

Agent B reads `permanent_dq_limitations` before traversing any causal chain.

If a limitation exists for the chain being traversed:
- Chain still traverses — do not skip
- Limitation metadata attached to `alert_log` entry
- Agent D reads limitation metadata at render time and applies appropriate
  disclosure format

Agent B does NOT make confidence decisions — it passes metadata to Agent D.
Agent D owns all founder-facing confidence communication.# technical_architecture.md — E-Series Patch
## Date: 2026-05-23
## Instruction: Append this entire file to technical_architecture.md after the last line.
## Also update Section 3.2a brand_event_calendar documentation per note below.

---

## SECTION 3.2a — BRAND EVENT CALENDAR — DOCUMENTATION UPDATE

The brand_event_calendar table (DDL in Section 3.2a) is now auto-populated
by `historical_pattern_scan.py` at onboarding and monthly incremental scan.
It is NOT manually populated by the founder.

Auto-population covers:
- Sale periods: derived from discount depth + order volume spike (Approach B)
- Collection launches: derived from 3-source signature (SKU + spend + GA4)
- Sub-category launches: NOT classified separately — impact score handles duration

Founder manual entries remain possible for:
- Supplier events
- Platform disruptions
- 3PL transitions
- Photography updates

Previous documentation implying manual population for sale periods and
collection launches is superseded by this note.

---

## SECTION 3.2f — E-SERIES CLIENT CONFIG ALTER TABLE (Added 2026-05-23)

E-series alert columns. Run after Section 3.2d ALTER TABLE.

```sql
ALTER TABLE public.client_config
    -- E1
    ADD COLUMN IF NOT EXISTS e1_click_rate_drop_threshold    numeric default 0.30,
    -- Minimum drop from 90d baseline to fire E1. Default 30%.
    -- Beta-calibrate with first 3 real clients.

    -- E2 — Discount classification
    ADD COLUMN IF NOT EXISTS welcome_discount_codes          text[] default array[]::text[],
    -- Confirmed at onboarding. Excluded from discount depth calculations.
    ADD COLUMN IF NOT EXISTS baseline_discount_pct           numeric,
    -- Derived by historical_pattern_scan.py: trimmed mean of order discount depths
    -- excluding welcome codes and top 15% outliers. Written at onboarding.
    ADD COLUMN IF NOT EXISTS discount_classification_status  text default 'pending',
    -- values: pending / active / insufficient_history
    -- insufficient_history: < 12 months order data — E2 fires without exclusion

    -- E2 — Launch suppression
    ADD COLUMN IF NOT EXISTS collection_launch_suppression_days  integer default 28,
    -- Derived from brand's own similar-magnitude launch recovery history.
    -- Fallback: vertical benchmark → 28 days default.
    -- Recalibrated monthly by historical_pattern_scan.py.

    -- E2 — Firing threshold
    ADD COLUMN IF NOT EXISTS e2_repeat_rate_minimum_customers    integer default 50,
    -- Minimum repeat customers in 90d window for E2 to fire.
    -- Below this threshold: suppress, log scan_skipped_reason.

    -- Vertical classification
    ADD COLUMN IF NOT EXISTS vertical_tag                    text,
    -- Set at onboarding via single-tap question.
    -- values: contemporary_womenswear / premium / activewear / swimwear /
    --         basics / multi_category
    -- Required for cross-client benchmark queries in network_pattern_benchmarks.
    -- All benchmark queries must filter by vertical_tag — never pool cross-vertical.

    -- Vertical tag for onboarding
    ADD COLUMN IF NOT EXISTS vertical_tag_confirmed_at       timestamptz;
    -- Timestamp when founder confirmed vertical at onboarding.
```

---

## SECTION 3.2g — E-SERIES MART COLUMNS (Added 2026-05-23)

New columns required in `mart_causal_chain_daily`.
Add to `mart_causal_chain_daily.sql` dbt model.

```sql
-- E1 — List Health
effective_click_rate_28d        numeric,
-- 28-day rolling effective click rate from stg_klaviyo_email_events
-- Formula: SUM(click_count) / SUM(delivered_count) over trailing 28 days
-- Adjusted: × ios_mpp_multiplier from client_config (default 0.65)
-- NULL when fewer than 5 campaign sends in 28-day window
-- Used by: E1 firing condition

-- E2 — Repeat Purchase Rate
new_customer_pct_90d            numeric,
-- New customers as % of total buyers in trailing 90 days
-- Formula: COUNT(DISTINCT customer_id WHERE order_number = 1
--               AND order_date >= date - 90)
--          / COUNT(DISTINCT customer_id WHERE order_date >= date - 90)
-- Source: stg_shopify_orders
-- HARD BLOCKER for E2 — S33 pre-condition depends on this column
-- NULL when fewer than 10 total buyers in window
-- Used by: E2 S33 pre-condition check
```

---

## SECTION 3.2h — BRAND EVENT CALENDAR AUTO-POPULATION LOGIC (Added 2026-05-23)

`historical_pattern_scan.py` auto-populates `brand_event_calendar` at
onboarding and monthly incremental scan. No founder input required for
historical sale periods and collection launches.

### Sale Period Detection (Approach B)

```python
# Step 1: Qualify event days by order volume
median_daily_orders = median(daily_order_count for all days with orders > 0)
qualifying_days = days where daily_order_count > median_daily_orders

# Step 2: Classify by discount depth percentiles
p50_discount = percentile(avg_discount_depth, 50, qualifying_days)
p75_discount = percentile(avg_discount_depth, 75, qualifying_days)

for day in qualifying_days:
    if avg_discount_depth > p75_discount:
        event_type = 'sale_period', sub_type = 'type_1_deep'
    elif avg_discount_depth > p50_discount:
        event_type = 'sale_period', sub_type = 'type_2_moderate'
    else:
        event_type = 'bau'  # not written to calendar

# Step 3: Cluster consecutive event days into periods
# Gaps of ≤2 days between qualifying days are bridged (same event)
```

Thresholds recalibrated monthly. Written to `brand_event_calendar`.

**Confound guard (note — added 2026-06-02; logged as O-23):** Approach B
classifies *any* qualifying high-order-volume, elevated-discount window as a
planned `sale_period`, so it will mislabel an unplanned competitor-reaction
markdown or a viral-driven discount as a planned sale and let it earn seasonal
suppression. Before a detected window is treated as a *planned* seasonal event
for suppression, require corroboration (recurrence in prior years / founder
confirmation); uncorroborated → narrate, do not suppress. This is a guard to be
applied where the calendar feeds suppression — the detector logic above is NOT
changed here (its rewrite is routed, not done in this pass).

### Collection Launch Detection

```python
# 3-source signature — ALL required within same 7-day window:
sku_spike = skus_added_in_window > mean(daily_sku_additions) + 2 * sd(daily_sku_additions)
spend_spike = any_channel_spend > prior_7d_avg * 1.40
ga4_spike = ga4_sessions > prior_7d_avg * 1.30

if sku_spike AND spend_spike AND ga4_spike:
    event_type = 'collection_launch'
    confidence = 'high'
elif sum([sku_spike, spend_spike, ga4_spike]) == 2:
    event_type = 'collection_launch'
    confidence = 'medium'

# Launch impact score for suppression duration calculation
impact_score = weighted_mean([
    sku_spike_magnitude / brand_median_launch_skus,      # weight 0.4
    spend_spike_magnitude / brand_median_spend,           # weight 0.35
    ga4_spike_magnitude / brand_median_sessions           # weight 0.25
])
```

### Suppression Duration Derivation

```python
# For known historical launches (confirmed at onboarding):
suppression_days = actual_recovery_days  # measured from historical data

# For new unknown launches:
similar_launches = historical_launches where:
    impact_score BETWEEN new_impact * 0.7 AND new_impact * 1.3

if len(similar_launches) >= 2:
    suppression_days = mean(recovery_days for similar_launches)
else:
    # Fallback hierarchy:
    # 1. Brand overall mean recovery
    # 2. network_pattern_benchmarks vertical median
    # 3. Default: 28 days
    suppression_days = fallback_value

client_config.collection_launch_suppression_days = suppression_days
```

Recovery measured as: days until `repeat_purchase_rate_90d` returns
within 2 percentage points of pre-launch baseline.


---

## Section 11 — COGS Architecture and D1 Alert Behaviour
## Status: Updated — 2026-05-31 (Tier 0 added, D4 deferred, beta limitations documented)
## Original lock date: 2026-05-26

---

## PURPOSE

Defines the five-tier COGS architecture, CSV upload service spec, COGS
owner escalation cadence, and D1 alert behaviour by COGS tier.
This section governs all margin-related alert formatting in Agent D.

---

## BETA COGS LIMITATIONS — READ BEFORE BUILDING

The following are confirmed NOT available in beta:

- No Finaloop API connector — Finaloop has no public API. CSV export path only.
- No 3PL connector of any kind.
- No supply chain connector of any kind.
- No automated fulfilment cost per order capture.
- No per-SKU landed cost from freight or duties — multiplier assumption only.
- D4 (Fulfilment Cost Anomaly) is DEFERRED to Phase 2. Cannot fire reliably
  in beta without 3PL billing data, which is inaccessible from any current
  connected source. Shopify fulfillment API does not contain what the brand
  paid its 3PL — only customer-facing shipping charges or Shopify-label costs.
  D4 remains in the alert library for Phase 2 design but Agent A must NOT
  activate D4 scan logic in beta.

CSV is the only COGS ingestion path in beta for any founder with SKU-level
cost data. Founders without a cost CSV fall to Tier 0 (single blended number)
or Tier 3 (no cost data at all).

Finaloop adoption rate in the ICP is unvalidated. Must be confirmed in
customer discovery. If fewer than 5 of 10 interviewed brands use Finaloop,
Tier 0 and Tier 3 are the primary beta COGS paths, not Tier 1.

---

## FIVE-TIER COGS ARCHITECTURE

### Tier 0: Founder-Stated Blended Per-Order Cost (NEW — 2026-05-31)
- Added because most $2M–$10M fashion founders cannot produce a per-SKU
  cost CSV. Their landed cost components live across freight invoices, duty
  invoices, and 3PL billing — not in a single structured file.
- Onboarding question: "What does it cost you, fully loaded, to get one
  order out the door — including product cost, freight, duties, and
  fulfilment fees? Give us your best estimate per order."
- Single number. Written to `client_config.founder_stated_cogs_per_order`.
- Used as flat per-order cost deduction in all CM calculations.
- Every CM alert using this figure carries mandatory disclosure:
  "Based on your stated $[X] all-in cost per order. Connect Finaloop
  or upload a cost file for SKU-level accuracy."
- Driver-only alert template. No margin % stated. No $ margin impact.
- `cogs_tier_active = 'founder_stated_per_order'` in client_config
- This tier exists to give D1 a cost basis for every brand regardless
  of how organised their cost records are. It is honest about imprecision.

### Tier 1: Finaloop CSV Export
- Full margin alert enabled: margin % figure + $ weekly impact.
- Gold standard. ~75% SKU coverage when connected.
- NO Finaloop API exists. This is NOT a connector — it is a CSV export
  from the Finaloop platform that the founder downloads and uploads to PS.
  It follows the same CSV upload path as Tier 1.5.
- `cogs_tier_active = 'finaloop'` in client_config.
- Monitor quarterly: if Finaloop releases a public API, PS should be
  first to integrate. Flag as quarterly check item.

### Tier 1.5: Founder CSV Upload
- Full margin alert enabled after reconciliation complete.
- Multiple CSV files accepted. SKU-level mapping. Latest file wins on conflict.
- Exact matches written silently to sku_cost_master.
- Fuzzy matches → reconciliation output file only. NEVER auto-written.
- COGS owner reviews reconciliation file offline, re-uploads corrected version.
- Re-upload triggers exact matching only — no fuzzy logic on corrected file.
- `cogs_tier_active = 'founder_csv'` in client_config.
- Build: /connectors/cogs_csv_processor.py (non-trivial — flag for engineering sprint).
- Reality check: most founders at this GMV tier do NOT have a clean per-SKU
  cost CSV. Freight, duties, and 3PL costs live in separate invoices and are
  not allocated per SKU. Do not assume CSV availability at onboarding —
  offer Tier 0 as the fallback before defaulting to Tier 3.

### Tier 2: Shopify Cost Confirmed at Onboarding
- Onboarding question: "Do you maintain cost-per-item in Shopify for all
  products? Is it your landed cost?"
  → Yes + landed: cogs_shopify_confirmed = true, cogs_shopify_landed = true
  → Yes + ex-factory: cogs_shopify_confirmed = true, apply multiplier,
    founder confirms multiplier → write to cogs_multiplier_confirmed
  → No: offer CSV upload path (Tier 1.5) first, then Tier 0 if no CSV available.
- Driver-only cost pressure alert. No margin % stated. No $ margin impact.
- `cogs_tier_active = 'shopify_derived'` in client_config.

### Tier 3: No Cost Data
- Founder has no cost data in any form — no CSV, no Shopify cost field,
  no blended estimate they are confident in.
- Driver-only cost pressure alert. No margin % stated. No $ margin impact.
- Inline prompt in alert: "Connect your actual cost data to unlock margin tracking."
- `cogs_tier_active = 'founder_stated'` in client_config.
- D1 still fires — cost driver signals fire regardless. Margin figure suppressed.

### Founder COGS Reality Check (Updated 2026-05-31)
Most $2M–$10M fashion founders do NOT maintain COGS diligently.
Finance/buying background → reasonable records. Creative/marketing background →
rough intuition only. Most maintain costs in Excel updated per PO or per season.
Landed cost components (freight, duties, 3PL fees) are almost never allocated
per SKU at this GMV tier — they live in aggregate invoices per shipment.
The correct onboarding flow is: offer Tier 1.5 CSV first → if unavailable,
offer Tier 0 single number → if unwilling, fall to Tier 3.
CSV upload is an enhancement for founders who have structured data.
Tier 0 is the realistic fallback for the majority.
D1 fires on all brands regardless of COGS tier.

---

## D1 ALERT BEHAVIOUR BY COGS TIER

### Agent D pre-condition (mandatory before formatting any D1 alert):
1. Read client_config.cogs_tier_active
2. If 'finaloop' or 'founder_csv' → use FULL MARGIN ALERT template
3. If 'shopify_derived' or 'founder_stated_per_order' or 'founder_stated'
   → use DRIVER-ONLY template
4. Never mix templates. One or the other. Never hybrid.
5. If cogs_tier_active = 'founder_stated_per_order' → prepend disclosure:
   "Based on your stated $[client_config.founder_stated_cogs_per_order]
   all-in cost per order. Connect Finaloop or upload a cost file for
   SKU-level accuracy."

### Universal Baseline Alert (Tier 0, 2, and 3 — all brands without SKU cost):
"Three cost signals are moving against you this week:
[Driver 1 with specific verifiable numbers], [Driver 2], [Driver 3].
Connect your cost data to unlock exact margin impact."
No margin %. No $ impact. Drivers named with verifiable numbers only.

### Full Margin Alert (Tier 1 and 1.5 — after all 9 D1 gaps resolved):
Spec to be written after Gap 2–9 deliberation completes.

### D4 — Fulfilment Cost Anomaly: DEFERRED TO PHASE 2
D4 cannot fire reliably in beta. Root cause: Shopify fulfillment API
does not contain what the brand paid its 3PL. No 3PL connector exists.
No supply chain connector exists. Agent A must NOT activate D4 scan
logic during beta. D4 remains in the alert library for Phase 2 design
once a 3PL connector strategy is defined.

---

## CSV UPLOAD SERVICE — /connectors/cogs_csv_processor.py

### File Validation (in order):
1. Format check: CSV and .xlsx only. Reject PDFs, images.
   Message: "We can only read CSV or Excel files — please re-upload."
2. Minimum column detection: ≥1 SKU-like + ≥1 cost-like column.
   Message: "We couldn't find a SKU column and a cost column in this file.
   Please check the file and re-upload."
3. Currency check: "Are all costs in this file in USD?"
   - Yes → proceed
   - No → ask which currencies → ask founder-stated FX rate per currency
     → convert to USD at upload using stated rate
     → store original_currency and fx_rate_used in sku_cost_master
   - If currency column in file → use per row
   - Blank currency rows → flag as unprocessable, write rest,
     surface blanks in reconciliation output file
   - Multiple currencies in cost column with no currency column →
     reject: "Please add a currency column before re-uploading."
   - NEVER use live FX rates. Historical COGS locked at PO rate.
     FX conversion at upload time using founder-stated rate.
4. Landed vs ex-factory: ask once per file.
   If ex-factory → apply cogs_multiplier_confirmed. Founder confirms multiplier.
5. Zero or negative cost values → flag. Do not write to sku_cost_master.
6. Duplicate SKU within single file with different costs →
   flag both rows. Ask founder which to use. Never auto-resolve.
7. Version conflict (SKU exists in prior file, new cost differs) →
   surface conflict. Ask founder to confirm update. Never silent overwrite.

### SKU Matching Logic:
- Normalise both sides: lowercase, strip special chars, strip common prefixes/suffixes
- Exact match → write silently to sku_cost_master
- Fuzzy match → reconciliation output file only. Confidence score: high/medium/low.
- No match → reconciliation output file. Flag: needs cost.
- NEVER auto-write fuzzy matches regardless of confidence score.

### Reconciliation Output File:
Columns: Shopify SKU | Shopify Product Name | Match Found | Matched CSV SKU |
         Confidence | Unit Cost | Currency | Landed/Ex-factory | Action Needed
- Generated and sent to cogs_owner_contact immediately after upload
- Founder sees: "We've sent [X] SKUs to [email] for review."
- Founder NOT required to review during onboarding — removes bottleneck
- Reconciliation file also serves as COGS owner's internal reference

### Multiple File Handling:
- Unlimited uploads accepted. SKU-level mapping across all files.
- Latest upload wins on conflict. Version tracked via upload_batch_id.
- Historical inactive SKUs retained with active = false.
- When inactive SKU relaunches → check records first:
  "We have cost data for this SKU from a previous file — is it still accurate?"

### Re-upload After Reconciliation:
- COGS owner corrects reconciliation file, re-uploads
- Re-upload triggers exact matching only — no fuzzy logic
- All confirmed SKUs written to sku_cost_master
- Remaining unmatched SKUs → flag to founder, offer manual entry

---

## COGS OWNER ESCALATION CADENCE

### At Onboarding (contextual collection):
After fuzzy/unmatched SKUs detected — NOT as a form field upfront:
"We found [X] SKUs we couldn't confidently match to your cost file.
Who should we send these to for offline review? [Enter email]"
→ Write to client_config.cogs_owner_contact
→ Send reconciliation file immediately
→ Always CC founder on all subsequent COGS gap communications

### Cadence (US business days only, US federal holiday calendar hardcoded):
- Day 0:  Alert to cogs_owner_contact — new unmapped SKUs detected
- Day 5:  Reminder to cogs_owner_contact
- Day 10: Escalation to founder — owner hasn't responded
          "We flagged [X] unmapped SKUs to [name] 10 days ago — no update received."
- Day 15: Single reminder to founder
- Day 20: Final notice to founder with two buttons:
          → "Don't remind me about missing costs"
             Sets cogs_gap_suppressed = true. Existing SKU reminders suppressed.
             New SKU batches still trigger fresh cycle from Day 0.
             Post opt-out: one-time note in weekly summary only.
          → "Update COGS contact"
             Replaces cogs_owner_contact. Restarts cycle from Day 0.
- After Day 20: Hard stop. No further reminders for this SKU batch.

### Second Consecutive Miss Pattern:
If same cogs_owner_contact misses deadline twice in a row:
→ Escalate to founder at Day 5 (not Day 10) on second occurrence
→ Message: "This is the second time we haven't received cost data within
  5 days of new SKUs launching. Consider updating your COGS contact or process."

### Always CC Founder Rule:
NEVER route COGS gap alerts exclusively to cogs_owner_contact.
Founder always receives CC. If employee leaves and contact becomes invalid,
the Day 10/15/20 escalation ensures founder is always the final backstop.

### Post Opt-Out:
- cogs_gap_suppressed = true logged in client_config
- One-time note in weekly summary: "Margin tracking unavailable for [X] SKUs
  — cost data not provided. This affects accuracy of profitability alerts."
- Never mentioned again until new SKU batch triggers fresh cycle.

---

## Section 12 — D1 Threshold Architecture (Gap 2)
## Status: Locked — 2026-05-26
## Append to: technical_architecture.md after Section 11

---

## PURPOSE

Defines the complete threshold architecture for D1 (Contribution Margin
Compression). Two triggers: Trigger A (step change detection) and Trigger B
(slow bleed detection). All thresholds are brand-adaptive — derived from
the brand's own historical data, never hardcoded.

---

## D1 TRIGGER A — STEP CHANGE DETECTION

### Core principle
Fixed comparison windows break in fashion DTC because events, echo periods,
and seasonal transitions mean no two calendar windows are structurally
equivalent. The correct approach is a brand-specific BAU baseline derived
from verified clean days only.

### BAU Baseline Construction

**Qualifying BAU day (all conditions must pass):**
- No active event in brand_event_calendar
- echo_period_active = false
- collection_launch_suppression not active
- influencer_campaign_active = false
- peak_suppression = false
- pre_sale_ramp_active = false (ADDED 2026-06-08, Gap 6 residual pass — an unmarked pre-sale
  ramp carries elevated spend + soft conversion and drags the BAU CM band DOWN, lowering the
  firing bar everywhere this baseline is read; the pre-sale detector marks the window and
  writes it to brand_event_calendar — detector design held in the session state file, build
  item in pre_agent_build_checklist.md)
- Day falls within trailing 90 days (not 180 — seasonal contamination risk)

**Onboarding two-pass backfill (ADDED 2026-06-08):** the FIRST baseline cannot be certified
clean until historical pre-sale ramps are identified and excluded. Pass 1 — detect ramps on
raw history; pass 2 — rebuild the baseline excluding them. Sequencing build item in
pre_agent_build_checklist.md.

**Baseline metric:** IQR band (p25–p75) of daily CM across all qualifying BAU days.
Point estimates replaced by range — acknowledges brand legitimately operates
across a range of CM values on clean days.

**Minimum:** 20 qualifying BAU days. Below this threshold → Trigger A disabled.
Log: scan_skipped_reason = 'insufficient_bau_days'. No founder-facing message.

**Recalculation:** Weekly. Stored in client_config:
- structural_cm_baseline_p25
- structural_cm_baseline_p75
- structural_cm_bau_day_count
- structural_cm_baseline_updated_at
- bau_cm_daily_sd (SD of daily CM across BAU days)

### Firing Condition

```
D1 Trigger A fires when ALL of the following:
1. current_7day_cm < structural_cm_baseline_p25 − threshold
2. No exclusion flag active (event / echo / launch / influencer / peak)
3. Current 7-day window: all 7 days clean
4. Current 7-day window: ≥1 Saturday AND ≥1 Sunday
5. structural_cm_bau_day_count ≥ 20
6. structural_break_detected = false
7. sparse_bau_profile = false
```

**Why 7 clean days with weekend representation:**
Weekends drive 35–45% of weekly fashion DTC orders. Weekend orders skew
toward full-price impulse purchases (higher CM). Weekday orders skew
toward considered purchases with discount codes (lower CM). A CM read
from days that exclude a Saturday or Sunday is directionally biased and
cannot be compared fairly to a baseline that includes weekends.

### Adaptive Threshold

```
threshold = MIN(MAX(bau_cm_daily_sd × 2.0, 3pp floor), 8pp ceiling)
```

| Brand type | SD | 2×SD | Effective threshold |
|------------|-----|------|-------------------|
| Very stable | 0.8pp | 1.6pp | 3pp (floor applies) |
| Typical | 2pp | 4pp | 4pp |
| Volatile (ceiling applies) | 5pp | 10pp | 8pp |

- **2×SD basis:** 2 standard deviations covers ~95% of normal CM variation.
  A drop beyond 2×SD is outside 95% of the brand's normal operating range.
- **3pp floor:** Prevents alert on genuinely noisy single-week fluctuations
  for very stable brands.
- **8pp ceiling:** At $5M GMV and ~32% CM, an 8pp drop = ~$30K/month margin
  erosion. Preventing volatile brands from waiting for a 12pp drop.

**Threshold stored as:** Computed at runtime from bau_cm_daily_sd.
Not stored separately — recalculated on each Trigger A scan.

**Urgency tier:** HIGH (🟠)

---

## ECHO PERIOD — THREE-STATE MODEL

Every day is classified into one of three mutually exclusive states:

**State 1 — Active Event**
- Condition: event exists in brand_event_calendar for this day
- D1: suppressed
- BAU baseline: day excluded

**State 2 — Echo Period**
- Condition: event ended within last N days AND return volume elevated
- echo_period_active = true in brand_event_calendar
- D1: suppressed
- BAU baseline: day excluded

**State 3 — BAU**
- Condition: no active event, echo_period_active = false,
  return volume within normal range
- D1: can fire
- BAU baseline: day qualifies

### Echo Period Open/Close Logic

**Opens when:**
```
Most recent flagged event ended within last N days (N = event-type cap)
AND daily_return_count ≥ 1.5 × structural_bau_return_rate
```

**Closes when:**
```
rolling_7day_avg_return_count < 1.3 × structural_bau_return_rate
for 7 consecutive days
OR event-type cap elapsed (whichever comes first)
```

**Hysteresis (1.5× open, 1.3× close):** Prevents oscillation from secondary
return waves. A brand clearing BFCM returns that has a brief 3-day dip before
a secondary wave does not flip BAU→echo→BAU→echo repeatedly.

**Event-type caps (maximum duration backstop):**

| Event type | Cap | brand_event_calendar flag |
|------------|-----|--------------------------|
| Standard: flash sale, influencer campaign, collection launch | return_window_days (default 21 days) | peak = false |
| Peak: BFCM, Boxing Day, major annual event | return_window_days × 1.5, capped at 45 days | peak = true |

### New Columns Required in brand_event_calendar

```sql
ALTER TABLE public.brand_event_calendar
    ADD COLUMN IF NOT EXISTS echo_period_active     boolean default false,
    ADD COLUMN IF NOT EXISTS echo_expected_end_date date,
    ADD COLUMN IF NOT EXISTS peak                   boolean default false;
    -- peak = true → echo cap = return_window_days × 1.5, max 45 days
    -- peak = false → echo cap = return_window_days (default 21 days)
```

---

## STRUCTURAL BREAK DETECTION

A business pivot, supplier change, category addition, or marketing
channel shift creates a structural break — historical baseline data
becomes incomparable to current operating reality.

### Continuous 30-Day Rolling Detection

```python
# Run every 30 days
recent_bau_days = BAU days in last 30 days
prior_bau_days = BAU days in prior 60 days

recent_p50 = median(daily_cm, recent_bau_days)
prior_p50 = median(daily_cm, prior_bau_days)
recent_p25 = percentile(daily_cm, 25, recent_bau_days)
recent_p75 = percentile(daily_cm, 75, recent_bau_days)
prior_p25 = percentile(daily_cm, 25, prior_bau_days)
prior_p75 = percentile(daily_cm, 75, prior_bau_days)

IF ABS(recent_p50 − prior_p50) > break_magnitude
   # break_magnitude is brand-relative (ADDED 2026-06-08, Gap 6 residual pass): a multiple of
   # the brand's own weekly CM volatility (derived from bau_cm_daily_sd), floored so it cannot
   # get absurdly small for ultra-steady brands — same pattern as Trigger B's
   # magnitude_threshold. NOT a flat 5pp (noise for a volatile brand → false breaks that
   # discard usable history; too deaf for a steady one → real pivots missed).
AND (recent_p25 > prior_p25 AND recent_p75 > prior_p75)
   OR (recent_p25 < prior_p25 AND recent_p75 < prior_p75)
   # Both bounds shifted same direction — band migrated, not just widened
AND shift_has_persisted_bau_days >= 21:
   # 21-day persistence UNCHANGED (a PERMANENT shift should confirm slowly); flagged to the
   # O-26 consistency audit for review only.
    structural_break_detected = true
    structural_break_detected_at = now()
    # Reset baseline: use only BAU days post-break
    # Send founder message
```

**Founder message (one-time per break detection):**
"Your margin profile appears to have shifted structurally around [date].
We've recalibrated your baseline to reflect your current operating pattern.
Was there a business change around that time? [Yes, tell us what changed]
[No, looks like noise]"

Founder response stored in structural_break_confirmed_by_founder.
If founder says noise → manual review flag, do not suppress break detection.

**Baseline reset:** After structural break, baseline uses only BAU days
post-break date. Trigger B cluster history also resets — minimum 8 complete
BAU weeks must reaccumulate before Trigger B can fire again.

### Self-Calibrating 3-Pass Bootstrap

Exclusion filters and BAU day identification are interdependent.
Bootstrap resolves the circular dependency:

```
Pass 1: Exclude only hard event calendar flags
        → Compute rough BAU return rate from remaining days
        → Compute rough structural_cm_baseline from remaining days

Pass 2: Apply echo period filter using rough BAU return rate
        → Recompute BAU return rate from refined day set
        → Recompute structural_cm_baseline from refined days

Pass 3: Final iteration to stabilise
        → Compute seasonal profile from refined BAU day set
        → Write all values to client_config
```

3 iterations is sufficient for convergence in practice.

### BAU Coverage Audit

```python
bau_coverage_rate = qualifying_bau_days / total_days_in_window
```

If bau_coverage_rate < 15% after 3-pass bootstrap:
1. Diagnose: if >60% of exclusions from a single filter → filter may be
   over-broad. If evenly distributed → brand is genuinely event-dense.
2. If filter over-broad: adjust filter threshold, re-run bootstrap.
3. If genuinely event-dense: set sparse_bau_profile = true.

### Permanently Promotional Brands (sparse_bau_profile)

If sparse_bau_profile = true:
- D1 Trigger A: DISABLED (d1_trigger_a_disabled = true)
- D1 Trigger B: DISABLED (d1_trigger_b_disabled = true)
- D2 (Discount Dependency Creep): ELEVATED to primary margin signal
- No founder-facing message about disabled alerts
- Internal flag for customer success team
- trigger_b_disabled_reason = 'sparse_bau_profile'

---

## D1 TRIGGER B — SLOW BLEED DETECTION

### The Slow Bleed Problem

A slow bleed is 0.3–0.5pp per week of structural CM erosion. Individually,
no single week looks alarming. Cumulatively, over 10–14 weeks, the brand
has lost 3–5pp of operating margin — equivalent to $25K–$45K/month at $5M GMV.

The bleed is invisible to founders who compare this week to last week
(which may have been an event or echo period). It is only visible when
comparing clean BAU weeks to clean BAU weeks across time.

### Unit of Analysis: Complete BAU Week

**Definition:** A week (Monday through Sunday) where ALL 7 days are:
- No event active in brand_event_calendar
- echo_period_active = false
- No public holiday falling on any day of the week
- All other BAU exclusion conditions met

**Why complete weeks (not clusters of BAU days):**
Complete weeks always have the same composition: 1 Saturday, 1 Sunday,
5 weekdays. Day-mix contamination is eliminated entirely. No normalisation
needed. No z-scores. No day-type median lookup tables.

Any week containing a public holiday does not qualify — excluded entirely.
Simpler and more robust than positional mapping (Monday holiday vs
Wednesday holiday vs Friday holiday).

**Complete BAU week CM:**
```
weekly_cm = (total_week_revenue − total_week_costs) / total_week_revenue
```
Where costs include: ad spend, COGS (if available at tier 1/1.5),
returns value, and fulfilment costs ONLY when a real cost-side feed exists (3PL invoice /
Shopify-Shipping-Label) — feed-only as of 2026-06-08 (Gap 6 residual pass). The estimated
fulfilment driver is retired, so with no feed, fulfilment is EXCLUDED from CM the same way
COGS is for Tier 2/3 — never estimated from carrier rates.

**Storage:** bau_week_registry table. One row per qualifying complete
BAU week per client.

### Trigger B Disabled Conditions

```
Trigger B = DISABLED when ANY of:
    sparse_bau_profile = true
    available_history < 12 months
    seasonal_profile = 'undetected'
```

Log: d1_trigger_b_disabled = true, trigger_b_disabled_reason.
No founder-facing message. Trigger A still active.

### Season Detection for Trigger B

All 8+ qualifying weeks must be from the same season window.
Season derived from brand's own BAU order volume data — not hardcoded calendar.

**Derivation:**
```python
# Run as Pass 3 output of BAU bootstrap
rolling_28d_median_orders = rolling median of daily BAU order count
# Identify local peaks and troughs in rolling median
# Peaks → high_season_windows
# Troughs → low_season_windows
# Slope-change periods → transition_windows
# Write to client_config.brand_season_profile (JSONB)
```

**Flat profile detection:**
```python
seasonal_signal_strength = (
    rolling_28d_peak_order_count − rolling_28d_trough_order_count
) / SD(daily_bau_order_count)

if seasonal_signal_strength < 2.0:
    seasonal_profile = 'flat'
    # All complete BAU weeks comparable regardless of calendar position
else:
    seasonal_profile = 'seasonal'
    # Only compare weeks from same season window
```

Threshold of 2.0 is consistent with the 2SD framework applied throughout.
No hardcoded percentages.

**Cross-season year-on-year comparison:**
When ≥13 months of history and no structural break between periods:
Compare same-season BAU weeks from year N to year N−1.
Detects secular year-on-year deterioration within same season.
Not deferred to Phase 2 — enabled when data conditions are met.

### Mann-Kendall Trend Test

Non-parametric test for monotonic trend. Does not assume linearity.
Works reliably at N=8–20 (our target range).

```python
from scipy.stats import kendalltau

# Or implement directly:
# For each pair (i, j) where j > i:
#   If cm_week_j > cm_week_i: concordant pair
#   If cm_week_j < cm_week_i: discordant pair
# S = concordant_count − discordant_count
# Significant downward trend when S is significantly negative

p_threshold = 0.10  # Deliberately lenient given small N
# p < 0.05 at N=8 requires very strong signal — misses genuine bleeds
```

Firing requires: significant downward trend at p < 0.10.

### Theil-Sen Slope Estimator

Companion to Mann-Kendall. Estimates the magnitude of the trend.
Robust to outliers — uses median of all pairwise slopes.

```python
# All pairwise slopes
slopes = [
    (cm_week_j − cm_week_i) / (j − i)
    for all pairs (i, j) where j > i
]
theil_sen_slope = median(slopes)  # pp per week
```

### Magnitude Threshold (Brand-Adaptive)

```python
bau_weekly_cm_sd = SD(weekly_cm values across all qualifying BAU weeks
                      in the same window as Mann-Kendall)

magnitude_threshold = MIN(MAX(bau_weekly_cm_sd × 0.20, 0.2), 0.5)
# Units: pp per week
# 0.2pp/week floor: prevents trivially small threshold for stable brands
# 0.5pp/week ceiling: ensures volatile brands alert while still early
```

**Multiplier 0.20 basis:**
A Theil-Sen slope of 0.20 × weekly SD means the brand is losing 20% of
one standard deviation of their natural CM volatility every week,
consistently across all BAU week pairs. Over 8 BAU weeks (roughly
16–20 calendar weeks) = 1.6× their weekly SD of structural deterioration.
Above natural noise floor. Not explainable by random weekly variance.

**Historical calibration at onboarding:**
1. Identify all complete BAU weeks in available history
2. Run Theil-Sen retrospectively across same-season week sequences
3. Cross-reference with known business response events in data
   (spend reduction, discount depth increase, supplier change)
4. Find Theil-Sen slope that consistently preceded those responses by 4–8 weeks
5. Store as trigger_b_theil_sen_multiplier in client_config
6. Default 0.20 applies when history insufficient for calibration
7. Outcome-tracked continuously — refined as real outcomes accumulate

### Complete Firing Condition

```
D1 Trigger B fires when ALL of the following:
1. Minimum 8 complete same-season BAU weeks in bau_week_registry
2. Mann-Kendall test: significant downward trend (p < 0.10)
3. theil_sen_slope < −magnitude_threshold
4. structural_break_detected = false in window
5. sparse_bau_profile = false
6. seasonal_profile ≠ 'undetected'
7. d1_trigger_a_disabled = false
8. Trigger A is not firing this week (Trigger B is early warning,
   not duplicate of acute alert)
```

**Urgency tier:** INFORMATIONAL (🟡)
Trigger B is a trajectory signal — founder needs to act over weeks,
not hours. HIGH urgency framing creates urgency that does not match
the action timeline.

**Scan cadence:** Weekly (Monday morning), not every 6 hours.
Runs after bau_week_registry is updated for the prior complete week.

---

## NEW CLIENT CONFIG COLUMNS REQUIRED (D1 Gap 2)

```sql
ALTER TABLE public.client_config
    ADD COLUMN IF NOT EXISTS structural_cm_baseline_p25          numeric,
    ADD COLUMN IF NOT EXISTS structural_cm_baseline_p75          numeric,
    ADD COLUMN IF NOT EXISTS structural_cm_bau_day_count         integer default 0,
    ADD COLUMN IF NOT EXISTS structural_cm_baseline_updated_at   timestamptz,
    ADD COLUMN IF NOT EXISTS bau_cm_daily_sd                     numeric,
    ADD COLUMN IF NOT EXISTS sparse_bau_profile                  boolean default false,
    ADD COLUMN IF NOT EXISTS bau_coverage_rate                   numeric,
    ADD COLUMN IF NOT EXISTS seasonal_profile                    text default 'undetected',
    -- values: undetected / flat / seasonal
    ADD COLUMN IF NOT EXISTS seasonal_profile_updated_at         timestamptz,
    ADD COLUMN IF NOT EXISTS brand_season_profile                jsonb,
    -- JSONB: {high_season_windows: [...], low_season_windows: [...], transition_windows: [...]}
    ADD COLUMN IF NOT EXISTS trigger_b_theil_sen_multiplier      numeric default 0.20,
    ADD COLUMN IF NOT EXISTS bau_weekly_cm_sd                    numeric,
    ADD COLUMN IF NOT EXISTS trigger_b_disabled_reason           text,
    -- values: sparse_bau_profile / insufficient_history / seasonal_profile_undetected
    ADD COLUMN IF NOT EXISTS d1_trigger_a_disabled               boolean default false,
    ADD COLUMN IF NOT EXISTS d1_trigger_b_disabled               boolean default false,
    ADD COLUMN IF NOT EXISTS structural_break_detected           boolean default false,
    ADD COLUMN IF NOT EXISTS structural_break_detected_at        timestamptz,
    ADD COLUMN IF NOT EXISTS structural_break_confirmed_by_founder boolean default false;
```

---

## NEW TABLE — bau_week_registry

```sql
-- Stores confirmed complete BAU weeks per client
-- A complete BAU week: all 7 Mon-Sun days pass all BAU exclusion filters
-- No event, echo period, public holiday, or exclusion flag on any day
-- Used by D1 Trigger B Mann-Kendall and Theil-Sen computation
-- Written weekly by the BAU week qualification scan
CREATE TABLE public.bau_week_registry (
    id                  bigint generated always as identity primary key,
    client_id           text not null,
    week_start_date     date not null,  -- always a Monday
    week_end_date       date not null,  -- always a Sunday (week_start + 6)
    weekly_cm           numeric,        -- CM for this complete BAU week
    season_window       text,
    -- which brand_season_profile window this week falls in
    -- values: high / low / transition / flat (for flat-profile brands)
    created_at          timestamptz default now(),
    unique(client_id, week_start_date)
);
```

---

## INTERACTION WITH causal_graph.py

D1 entry must include all new pre-conditions from Gap 2:

```python
"D1": {
    "causal_chain_id": "D1",
    "leading_signal_column": "contribution_margin_pct",
    "leading_signal_direction": "declining",
    "outcome_column": "net_revenue",
    "outcome_direction": "declining",
    "lag_days": 0,
    "corroborating_signals": [
        "meta_cpm_change_pct",
        "return_rate_pct",
        "blended_discount_depth_pct"
    ],
    "mart_table": "mart_causal_chain_daily",
    "status": "active",
    "routing": None,
    "verification_category": "B",
    "pre_conditions": [
        "cogs_tier_check",        # Gap 1 — determines alert template
        "trigger_a_or_b_check",   # Gap 2 — which trigger type fired
        "echo_period_check",      # Gap 2 — suppress if echo active
        "structural_break_check", # Gap 2 — suppress if break detected
        "sparse_bau_check"        # Gap 2 — disable if sparse_bau_profile
    ]
}
```

Trigger B runs as a SEPARATE weekly scan entry — not part of the 6-hourly
Agent A scan. Trigger A runs every 6 hours as normal.

---

## D1 ALERT BEHAVIOUR BY TRIGGER TYPE

| Trigger | Urgency | Template |
|---------|---------|----------|
| Trigger A (step change) + Tier 1/1.5 COGS | HIGH 🟠 | Full margin alert with % and $ |
| Trigger A (step change) + Tier 2/3 COGS | HIGH 🟠 | Driver-only, no margin % or $ |
| Trigger B (slow bleed) + Tier 1/1.5 COGS | INFORMATIONAL 🟡 | Full margin trend alert |
| Trigger B (slow bleed) + Tier 2/3 COGS | INFORMATIONAL 🟡 | Driver trend alert, no margin % |

If Trigger A fires in the same week Trigger B would fire → only Trigger A fires.
Trigger B fires only when Trigger A has not fired.

Full alert language pending Gaps 3–9 deliberation.

---

## SECTION 13 — D1 GAP 3 SCHEMA ADDITIONS
## Locked: 2026-05-31
## Accumulate with all other pending build actions.
## Execute in consolidated Claude Code session after H-series complete.

---

### NEW TABLE — public.connector_gap_map

Powers the D1 blind spot diagnostic.
Maps (missing_driver, cogs_tier, residual_band) to
(likely_cause, recommended_connector, action_brief).
NOTE (2026-06-08, Gap 6 residual pass): the `fulfillment_invoice` row is a DIRECTION to check,
never an estimated figure — the blind-spot fulfilment step no longer computes an estimated
cost (see revised Step 3 in agent_d_build_spec.md). Its `cogs_tier = 'any'` scope vs the rule
that only trustworthy-margin brands enter the residual machinery is flagged to the O-26
consistency audit, not changed here.

```sql
CREATE TABLE public.connector_gap_map (
    id                       bigint generated always as identity primary key,
    missing_driver           text not null,
    -- values: cogs / sku_mix / fulfillment_invoice /
    --         payment_processing / structural_unknown
    cogs_tier                text not null,
    -- values: tier1 / tier1_5 / tier2 / tier3 / any
    residual_band            text not null,
    -- values: high (40–70%) / very_high (>70%)
    likely_cause_description text not null,
    recommended_connector    text not null,
    -- e.g. 'finaloop' / '3pl_invoice' / 'founder_csv'
    action_brief             text not null,
    created_at               timestamptz default now()
);
```

Seed rows (minimum viable at launch):

```sql
INSERT INTO public.connector_gap_map
    (missing_driver, cogs_tier, residual_band,
     likely_cause_description, recommended_connector, action_brief)
VALUES
    ('cogs', 'tier2', 'very_high',
     'Supplier or landed cost change not visible in connected data',
     'finaloop',
     'Check purchase orders and supplier invoices for changes in the last 14 days'),
    ('cogs', 'tier3', 'very_high',
     'Supplier or landed cost change not visible in connected data',
     'founder_csv',
     'Check purchase orders and supplier invoices for changes in the last 14 days'),
    ('sku_mix', 'tier2', 'high',
     'Revenue mix shifted toward lower-margin products',
     'sku_cost_master',
     'Upload a product cost CSV to identify which SKUs are driving margin compression'),
    ('fulfillment_invoice', 'any', 'high',
     '3PL rate change or carrier surcharge not captured in Shopify carrier data',
     '3pl_invoice',
     'Review your 3PL invoice for this week for rate changes or new surcharges');
```

---

### ALTERED TABLE — public.candidate_signals

New columns supporting AI-discovered interaction pattern storage.

```sql
ALTER TABLE public.candidate_signals
    ADD COLUMN IF NOT EXISTS pattern_type        text default 'bivariate',
    -- values: bivariate / interaction
    -- bivariate: standard two-column leading_signal + outcome pair
    -- interaction: 3+ drivers moving together in same alert window
    ADD COLUMN IF NOT EXISTS driver_combination  text[];
    -- array of mart column names involved in the interaction pattern
    -- populated for pattern_type = 'interaction' only
    -- example: ARRAY['meta_cpm_change_pct', 'ga4_cvr_change_pct',
    --                 'return_rate_pct']
    -- NULL for pattern_type = 'bivariate'
```

---

### ALTERED TABLE — public.client_config (Gap 3 additions)

```sql
ALTER TABLE public.client_config

    -- SKU mix shift driver threshold (Principle 4)
    ADD COLUMN IF NOT EXISTS margin_mix_shift_threshold
        numeric,
    -- Adaptive threshold for SKU mix shift detection
    -- Formula: MAX(bau_margin_weighted_revenue_sd × 1.5, 1.5pp floor)
    -- NO CEILING — high-volatility brands get threshold reflecting
    --   their actual operating range. Ceiling removed after deliberation.
    -- NULL until first baseline computation at onboarding.
    -- Recalibrated monthly.

    ADD COLUMN IF NOT EXISTS bau_margin_weighted_revenue_sd
        numeric,
    -- SD of margin-weighted revenue across BAU weeks (Tier 1/1.5 only)
    -- Source: margin-weighted revenue calculation on bau_week_registry

    ADD COLUMN IF NOT EXISTS bau_category_revenue_share_sd
        numeric,
    -- SD of category revenue share across BAU weeks
    -- Retained for future reference — not currently used in D1
    -- (Tier 2/3 category flag dropped from D1 after deliberation)

    ADD COLUMN IF NOT EXISTS sku_cost_coverage_by_revenue
        numeric,
    -- Revenue coverage rate for sku_cost_master unit_cost population
    -- Formula: SUM(revenue for SKUs with unit_cost populated this week)
    --          / total revenue this week
    -- Recomputed weekly at Agent A scan time
    -- Floor: 0.85 — below this, fall back to Tier 2/3 treatment
    -- Additional check: if single largest revenue SKU missing unit_cost
    --   → flag regardless of overall coverage rate

    -- CPM diagnostic tree (Layer 0 interaction check)
    ADD COLUMN IF NOT EXISTS creative_fatigue_frequency_multiplier
        numeric default 1.20,
    -- Ad frequency multiplier above BAU that signals creative fatigue
    -- Default 1.20 = 20% above BAU frequency
    -- Outcome-tracked per client — adjusted based on alert accuracy

    ADD COLUMN IF NOT EXISTS creative_fatigue_ctr_floor
        numeric default 0.90,
    -- CTR must fall below this fraction of BAU CTR to confirm fatigue
    -- Default 0.90 = CTR declined more than 10% vs BAU
    -- Used alongside creative_fatigue_frequency_multiplier

    ADD COLUMN IF NOT EXISTS cpm_noise_threshold
        numeric default 0.10;
    -- Minimum fractional CPM rise to surface CPM as a D1 driver
    -- Default 0.10 = 10% above BAU blended CPM
    -- Below this: CPM rise treated as normal auction noise, not surfaced
```

---

### ALTERED TABLE — public.sku_cost_master (Gap 3 additions)

```sql
ALTER TABLE public.sku_cost_master

    ADD COLUMN IF NOT EXISTS founder_category
        text,
    -- Founder-facing DISPLAY label ONLY — never the internal grouping key,
    --   never product_type, never a Shopify collection used as a grouping key.
    -- Display source: the resolved taxonomy-node label, optionally overridden
    --   by a non-blocking founder rename. A Shopify collection may supply the
    --   display label ONLY when verified categorical (never promotional, never
    --   the default).
    -- Populated by connectors/category_inference.py (onboarding backfill + ongoing).

    ADD COLUMN IF NOT EXISTS ai_inferred_category
        text,
    -- The LLM-inferred label when Step 0 (Shopify-assigned category) is absent —
    --   produced by classifying the SKU and SNAPPING to a Shopify Standard
    --   Taxonomy node (never free-text/invented). Internal grouping label when no
    --   Shopify-assigned category exists.
    -- Founder rename is a DISPLAY GATE ONLY: it NEVER blocks internal grouping or
    --   alert computation.
    --   (Retires the prior "AI clustering" basis and "mandatory founder rename".)

    ADD COLUMN IF NOT EXISTS category_id
        text,
    -- RESOLVED Shopify Standard Taxonomy node gid this SKU is grouped at
    --   (gid://shopify/TaxonomyCategory/<code>). Sourced from the Shopify-assigned
    --   category on shopify_products (Step 0, GraphQL enrichment) when present,
    --   else from the LLM snap. Upstream "unassigned" =
    --   'gid://shopify/TaxonomyCategory/na' OR NULL → treated as no assignment.

    ADD COLUMN IF NOT EXISTS category_full_name
        text,
    -- Resolved node breadcrumb path (e.g. "Apparel & Accessories > Shoes > Boots"),
    --   paired with category_id; taxonomy level/depth derivable from the path.

    ADD COLUMN IF NOT EXISTS category_inference_confidence
        numeric,
    -- Cross-signal semantic AGREEMENT score, NOT a raw model self-report. Measures
    --   how strongly the qualified signals (description [STRONG], categorical
    --   tags/collections, title, product_type [weak]) concur on the node. VENDOR is
    --   NOT a signal (single-brand DTC). Range 0.0–1.0.
    -- NO fixed threshold — the SKU is tagged at the DEEPEST taxonomy level where the
    --   qualified signals concur (depth = confidence).
    --   (Retires the "provisional threshold 0.70".)
    -- NULL when category_source = 'shopify_assigned' or 'manual'.

    ADD COLUMN IF NOT EXISTS category_source
        text default 'shopify_assigned';
    -- Tracks how the resolved node / founder_category was determined
    -- values:
    --   shopify_assigned = resolved from the Shopify-assigned category (Step 0)
    --   ai_inferred      = LLM classification snapped to a taxonomy node (Step 0 absent)
    --   manual           = founder relabelled the DISPLAY label in onboarding UI (display only)
    -- product_type is NOT a source — retained as a weak AI-inference input and a
    --   low-agreement internal-grouping fallback only, never a display label, never a key.
```

---

### NEW SCRIPT — connectors/category_inference.py (onboarding backfill + ongoing)

When it runs: onboarding Step 6 (backfill, after historical_pattern_scan.py)
AND continuously on new/changed SKUs, so newly added products are grouped
without a manual re-trigger. Silent completion — internal grouping is automatic.
The only founder-facing touch is an OPTIONAL display-label rename (non-blocking).

```python
# connectors/category_inference.py
# Onboarding Step 6 (backfill) + ongoing on new/changed SKUs
#
# Inputs:  stg_shopify_products (description [STRONG], title, product_type, tags)
#          shopify_products.category_id / category_full_name (Step 0, GraphQL enrichment)
#          shopify_collects / shopify_collection_products (collection membership)
#          NOTE: vendor is NOT used (single-brand DTC → COUNT(DISTINCT vendor) ≈ 1).
# Outputs: sku_cost_master.category_id / category_full_name (resolved node)
#          sku_cost_master.founder_category (display label) per active SKU
#          sku_cost_master.ai_inferred_category (when Step 0 absent)
#          sku_cost_master.category_inference_confidence
#          sku_cost_master.category_source
#
# Logic (per SKU):
# 1. STEP 0 (primary): read the Shopify-assigned Standard Taxonomy category from
#    shopify_products (category_id + category_full_name). If assigned
#    (NOT 'gid://shopify/TaxonomyCategory/na' and NOT NULL) → resolve the SKU to
#    that node; category_source = 'shopify_assigned'.
# 2. FALLBACK (Step 0 absent): classify the SKU and SNAP to a Shopify Standard
#    Taxonomy node (never free-text/invented). Signals are reliability-tiered,
#    NOT equal-vote: description (STRONG) > categorical tags/collections
#    (promo-filtered) > title, product_type (weak). Collections in this segment
#    are frequently promotional ("Bestsellers", "Sale", "New Arrivals") and are
#    unsafe as grouping keys — a SEMANTIC problem high coverage does NOT cure;
#    a collection feeds the DISPLAY label only when verified categorical.
#    category_source = 'ai_inferred'.
#    → Write category_inference_confidence per SKU (cross-signal agreement).
# 3. DEPTH: tag at the DEEPEST taxonomy level where the qualified signals concur
#    (deepest-agreement; depth = confidence). NO fixed agreement threshold.
#    Step-0 (merchant-assigned) depth is taken as-is; LLM depth self-limits to the
#    deepest concurring level.
# 4. DISPLAY label founder_category defaults to the resolved node label.
#    → OPTIONAL display-rename prompt in onboarding checklist:
#      "We've grouped your products into categories —
#       do these names match how you think about your business?
#       Rename any that don't." (display-only; non-blocking)
#    → Founder-renamed labels refine the DISPLAY label only; category_source = 'manual'.
# 5. If founder skips/declines the rename:
#    → keep the resolved node label for display; category_source unchanged
#    → internal grouping AND category-level D1 output PROCEED — rename is never a blocker
#    → (Retires the prior "declined rename → category-level D1 output suppressed".)
# 6. product_type is used ONLY as a weak inference input and a low-agreement
#    internal-grouping fallback for a SKU the signals cannot place — NEVER displayed,
#    NEVER a key.
# 7. Firing DEPTH per category is governed by AL-19 (see CATEGORY GROUPING +
#    FIRING-DEPTH GATE below, and GATE D1-G3 in d1_validation_gates.md): fire at the
#    finest level where AL-19 passes; roll up for volume carrying the AL-3/AL-29
#    concentration down-drill; brand-level-with-disclosure as the never-silent floor.
#    Grouping is SEMANTIC and is NEVER scored or re-split on return-rate behaviour.
#
# New/changed SKUs post-onboarding: the enrichment refreshes Step 0 and this script
# re-resolves the node (Step 0 → LLM snap) automatically — no manual re-trigger.
```

---

### CATEGORY GROUPING + FIRING-DEPTH GATE (onboarding + ongoing)

Runs after category_inference.py resolves groupings. Governs the *granularity*
of D1 output — never whether D1 runs (internal grouping is never blocked). Two
distinct concerns, kept separate: grouping is semantic; firing depth is volume-gated.

```python
# Grouping is SEMANTIC, not behavioural:
#   SKUs are grouped by the resolved Shopify Standard Taxonomy node
#   (Step 0 or LLM snap). Grouping is NEVER scored or re-split on return-rate
#   behaviour — return concentration inside a genuine category is a FINDING,
#   not evidence of a bad group.
#   (Retires the prior "RETURN-RATE COHERENCE within clusters" coherence_score
#    and the category_granularity_floor 0.30.)
#
# Firing depth is governed by AL-19 (NOT by a clustering-quality score):
# 1. D1 fires at the FINEST taxonomy level where AL-19 passes (enough volume
#    for the level to be trusted).
# 2. Where a finer level is too thin, roll up for volume AND carry the
#    AL-3/AL-29 concentration down-drill, so a hot child SKU or sub-node is not
#    masked by the rolled-up level.
# 3. BRAND-LEVEL-WITH-DISCLOSURE is the floor (explicit low-quality path): when
#    no category level passes AL-19, D1 operates at brand level and discloses
#    that per-category diagnosis was withheld for want of volume. Never silently
#    degrade — any degrade to a coarser level (incl. brand) with the level
#    recorded but no disclosure surfaced is a FAIL (go-live gate D1-G3).
#
# Firing-depth verdict is per category and re-evaluated at each monthly
# incremental scan as catalogue/return volume accumulate.
```

---

### HISTORICAL_PATTERN_SCAN.PY — Multivariate Sweep Extension

New capability added in Gap 3. Runs alongside existing bivariate sweep.
SEPARATE code path — must not be merged with bivariate sweep at any stage.

```python
# Extension to historical_pattern_scan.py
# Multivariate sweep for interaction patterns
# Runs after bivariate sweep in full and incremental modes
#
# For each brand at onboarding:
# 1. Identify all weeks where >= 2 mart columns (drivers) moved
#    in the same direction simultaneously
#    (threshold: each driver > 1.5x its BAU SD for that week)
# 2. Test whether a known D1 outcome followed within 7 days:
#    - D1 trigger fired, OR
#    - ROAS drop > 15% vs BAU, OR
#    - Return spike > 2x BAU return rate
# 3. Count instances, compute hit_rate
# 4. If >= 5 instances AND hit_rate >= 0.70:
#    → Write to candidate_signals:
#      pattern_type = 'interaction'
#      driver_combination = ARRAY[mart_col_1, mart_col_2, ...]
#      source = 'historical_scan'
#      client_id = current client
#      promotion_status = 'candidate'
#      practitioner_approved = false  ← ALWAYS false at write time
#    → Routes to practitioner review queue
#
# Practitioner review gate: MANDATORY
# No interaction pattern absorbs into live alert library without
# practitioner_approved = true manually set.
# calendar_clustered = true patterns: flagged prominently at review.
# Not blocked but reviewed first — may reflect seasonality not causation.
#
# Cross-network promotion:
# Same driver_combination across >= 3 brands of same vertical_tag
# AND calendar_clustered = false
# → hardcoded into global interaction library for that vertical
```

---

### DATA FRESHNESS — STALENESS THRESHOLDS (unchanged, reproduced for reference)

These thresholds govern the Principle 2 staleness disclosure in D1.
No new columns needed — reads existing any_source_stale + last_synced_at.

| Source | Acceptable staleness | D1 disclosure if exceeded |
|--------|---------------------|--------------------------|
| Sentry | 2 hours | append "(data from [N] hours ago)" |
| Shopify | 6 hours | append "(data from [N] hours ago)" |
| Meta/TikTok | 24 hours | append "(data from [N] hours ago)" |
| Klaviyo | 6 hours | append "(data from [N] hours ago)" |
| GA4 | 48 hours | append "(data from [N] hours ago)" |
| Loop Returns | 24 hours | append "(data from [N] hours ago)" |
| Gorgias | 6 hours | append "(data from [N] hours ago)" |

---

### GAP 6 DEPENDENCIES — IMPLEMENT IN GAP 6 BUILD, NOT STANDALONE

These describe what D1's Gap 6 build consumes. They do NOT implement the
launch detector here — that rewrite is routed to O-11 and batched to
causal_graph.py.

**Dependency 1 — SKU mix-shift seasonal suppression (RESOLVED):**
Location: SKU mix-shift suppression check in Agent D D1 formatting.
Grade the mix-shift driver on its **margin impact (CM%)**, NOT category-share
shift, by **event-anchored IQR percentile position inside the brand's own prior
same-season MARGIN band** (NO z-score / NO ±SD — a brand sees a season ~once a
year, so small-n is the permanent regime).
- The **spend-reallocation disqualifier runs first**: a shift that co-moves with
  a deliberate spend reallocation is not eligible for seasonal suppression.
- **Admissibility** — a prior season counts only if BOTH: post-structural-break
  (reuse the locked structural-break rule) AND cost-coverage ≥ 0.85 for those
  weeks.
- **State ceiling by admissible-season count:** 0 → no band → narrate/disclose;
  1 → fragile band → State-2 ceiling (fire-with-context, NEVER suppress);
  2+ → full band → State 3 available. Suppression is the highest-confidence
  claim, not the lowest.
- Grade carried in the `seasonal_typicality_state` field (see suppression_log),
  S41-decayed; separate from `variance_explained_pct`.
- **State 3 → suppress** (driver does not surface). **State 2 / State 1 →
  surface**; the State-2-vs-State-1 framing is handled at the D1 alert-language
  pass.
(Retires the prior "seasonal_profile = 'seasonal' AND ≥ 12 months / suppress
within ± 1 SD / adaptive threshold below 12 months" rule entirely.)

**Dependency 2 — Organic-viral detection (RESOLVED; detector rewrite routed to O-11):**
Not blanket suppression. D1-scoped behaviour is (a) exclude the surge days from
the BAU baseline, plus (b) a concurrent discount-depth read surfaced WITH viral
context (gated by the O-19 materiality + actionability floor) — because the
concurrent new-customer welcome-code discount compression is the one actionable
lever and blanket suppression would hide it.
- Detect via **S33's brand-level new-customer-pct surge signal (> 15% surge)**,
  NOT a single-SKU revenue test. Virality is multi-product / brand-level.
- **Founder confirmation** is the organic-vs-engineered discriminator; if
  unconfirmed, default to provisionally-locked-and-tracking.
- **DROPPED:** forward 30/60/90 repeat tracking in D1, any viral-specific
  returns model (returns flow through the normal return-rate component), and
  overlap handling. Repeat maturation stays with S33/E2.
- The **shared launch-detector rewrite** (separate `organic_viral` from
  `collection_launch`; fix the spec self-contradiction; C6 conflation; E2
  double-suppression) is **routed to O-11 and batched to causal_graph.py** —
  described here, NOT implemented in this file.
(Retires the prior "spend spike = optional → single-SKU +2 SD →
collection_launch_suppression_active = true → D1 suppressed for
return_window_days" rule entirely.)

---

## 2026-06-04 — DISCOUNT / RETURNS / GORGIAS-PARSER BUILD ITEMS (BATCHED, post-H)

From the D1 Gap 6 discount-depth/S19 PARTIAL close. All items are batched — none built
now, no consolidated Claude Code prompt until after H-series. Verified against the live
Shopify, Loop, and Airbyte sources (2026-06).

### Per-item discount staging (NEW staging model — our build, not an API/sync gap)
- Shopify's current API exposes the discount allocated to each line item
  (`LineItem.discountAllocations`), including the discount *type* (automatic vs code-based).
  Airbyte's Shopify connector already pulls these inside the orders/line_items array as
  nested data; nothing currently unpacks it.
- BUILD: a line-item staging model that reads `discountAllocations.allocatedAmount` per
  line and the discount type. **LANDMINE:** do NOT read the summary fields
  (`total_discount` / `totalDiscountSet` / `discountedTotalSet`) — Shopify itself
  recommends allocations instead, and the summary fields return empty/zero on
  order-level and code-based discounts.
- USE: feeds the effective-discount *source decomposition* (code/automatic/shipping) that
  rides a real D1 trigger. Dollar margin impact remains cost-feed-only; depth is
  computable without cost (directional, unsized) for non-feed brands.

### Returns ingestion — Shopify Returns API primary, Loop enrichment
- Shopify migrated to a new Returns API (~April 2026); Loop adopted it. Shopify is NOT
  replacing Loop — Loop is the management/exchange-conversion layer built on Shopify's
  rails; Loop explicitly states its admin cannot be replaced by the Shopify API. But
  native returns have matured (admin returns, returnless refunds, self-serve, native
  exchanges, store credit), so the new Shopify Returns API now carries the return object —
  reason, exchange, returnless refund — natively, and Loop writes its returns back into
  Shopify.
- BUILD: read returns from the **new Shopify Returns API as the primary surface** (works
  with or without Loop); treat the **Loop API as enrichment** for Loop brands (Shop-Now /
  advanced-exchange detail, label shipping rates, dispositions). Wrap returns extraction
  behind a thin adapter so a future surface change hits one module. Build post-migration,
  never against the legacy refund endpoints.
- DISTINCTION to keep: a *refund* is the money movement (existing `stg_shopify_refunds`);
  a *return* is the RMA with reason / exchange / disposition (new object). The return
  object is what the reason-and-exchange analysis needs.
- JOIN KEY: order ID (and Shopify's internal numeric customer ID — pseudonymous, not PII).
  Do NOT match returns to orders on email. Returns without an order ID are unlinkable;
  do not fall back to email.

### Loop returns / exchange staging + return-to-replacement link (our build)
- Loop's API exposes structured exchange data: per-line conditions/dispositions, the
  exchange order (the actual replacement item the customer selected), refund objects,
  Shopify refund objects, label rates, and all timestamps. The prior seed's text-note
  shortcut is OUR limitation, not an API one.
- BUILD: clean returns/exchange staging that (a) separates exchange from refund, (b)
  carries the returned variant AND the replacement variant so size DIRECTION (up/down) is
  structural for variant exchanges, (c) captures label shipping cost (quantifies exchange
  reverse-shipping ops cost).
- TWO EXCHANGE PATHS (Loop distinguishes them): **variant exchange** (same product,
  different size) → size-direction logic, revenue-neutral, ops-cost-only; **advanced /
  different-product exchange** (Shop Now) → treat as return-plus-new-purchase, variable
  margin (replacement can be cheaper/pricier). Not an edge case — Loop markets advanced
  exchanges — but the API labels which kind each is, so handle them on separate paths.
- The out-of-stock-exchange-to-refund case (popular size OOS → exchange collapses to a
  refund; double shipping + lost sale, silently margin-negative) belongs in the
  STOCKOUT/inventory workstream, NOT discounting. Loop hides OOS variants from the
  exchange picker, so the failed-exchange reason may not surface as a clean code —
  confirm at build whether Loop exposes it; reverse-shipping cost is cleanly available.

### Gorgias NLP parser (NEAR-TERM CORE INFRA — feeds multiple alerts, not Horizon-2)
- Rationale for core: ticket tag quality is unreliable at this brand tier and worst
  during sales (stretched support, resolution-time KPI), so multiple alerts that rest on
  Gorgias text (sizing-complaint velocity, return-reason context, retrospective review,
  the sale-period channel) need a parser, not tags. Modern models read sarcasm /
  mixed-intent well off the shelf — comprehension is effectively free.
- BUILD a parser that turns ticket text → trustworthy intent/reason label, with:
  (a) a brand-specific label SCHEMA (the model understands "about fit"; the bucket
  boundaries — runs small / runs large / inconsistent / not-as-pictured — are a design
  decision per brand); (b) a stated MULTI-INTENT rule ("love it but too small, arrived
  late" = multiple signals — small counts make mis-splits move the rate); (c) reads the
  CUSTOMER's messages only, not macros/canned replies; (d) reports LOW-SIGNAL when a
  brand's tickets are mostly templated.
- TRAIN the taxonomy on ≥1 yr history (weight recent tickets; re-check schema
  periodically — language/macros/product line drift). History trains the classifier; it
  does NOT enlarge the live weekly window — small-sample live velocity is handled by a
  firing floor + honest "too few tickets to call it" silence, NOT historical depth.
- OUTPUT posture: faithful SUMMARY + link to the raw tickets ("here are the 3 things
  customers are raising, click to read"). NO recommended founder action for this signal —
  the action depends on context we don't hold and can't verify (see O-27, decided
  case-by-case per signal).
- GATE (validation): per-brand accuracy check against a human-labelled sample BEFORE any
  pilot client sees it (see d1_validation_gates.md). Complaint-to-return CONVERSION is a
  slow, data-earned piece — parked, not part of the parser.

### Sale-period informational channel + delivery-label ingestion (PARALLEL — Horizon-2 / probationary)
- A separate, mutable, sale-period channel (NOT the acute margin alert), built minimal for
  beta whose real job is to collect sale-event data; explicitly unvalidated until it fires
  across enough real sales.
- Content: a DELIVERED-cohort complaint pulse (of N delivered, M raised tickets, reason
  XYZ, and the in-transit share showing the sale's own returns haven't landed) — NOT a
  return-rate readout (return lag makes a during-sale return rate a trailing read of the
  prior period). HARD RULE: never show a number the founder's existing dashboards
  (Shopify app / Triple Whale) already show, or the channel dies on arrival.
- REPRESENTATIVENESS GATE: hold the insight dark until the delivered cohort looks like the
  whole sale (spans shipping zones/speeds), not just its fast, near-warehouse front edge —
  a release condition, not a fitted baseline (un-learnable at 4–8 sales/yr). Direction +
  gate, never a precise early percentage.
- Mix-risk signal: history-assisted (per-SKU return history) for established product;
  live-only for NEW collections (no history; comparing a new silhouette to a category
  average is misleading). Requires delivery-label ingestion (delivered timestamps +
  carrier). Honest no-build estimate: the parser code is finite, but its trustworthiness
  for the *conversion* piece is earned over real data, not shipped.
