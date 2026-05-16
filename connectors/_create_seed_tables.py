"""
Create all seed-support tables required before running seed_shopify.py.

Tables created (in dependency order):
  PUBLIC SCHEMA:
    1. public.network_pattern_benchmarks
    2. public.permanent_dq_limitations

  CLIENT SCHEMA (client_azure_co):
    3.  brand_event_calendar
    4.  sku_cost_master
    5.  synthetic_touchpoint_journey
    6.  dq_metric_scores
    7.  dq_events
    8.  suppression_log
    9.  alert_data_lineage
    10. tiktok_organic_performance
    11. tag_normalisation
    12. klaviyo_flow_id_history
    13. klaviyo_sms_events
    14. meta_billing_statement
    15. tiktok_billing_statement
    16. synthetic_customer_pii_lookup

  ALTER TABLE:
    17. public.alert_log — add 11 new columns (IF NOT EXISTS per column)

Schema fixes applied vs. seed_decisions_gap_f_g.md DDL:
  - suppression_log.signal_detected_at: NOT NULL removed (predictive entries have NULL)
  - alert_data_lineage FK: references public.alert_log(id) not alert_log(id)
  - ALTER TABLE targets public.alert_log not client_azure_co.alert_log
  - synthetic_customer_pii_lookup: user-specified schema
    (synthetic_customer_id text PK, hashed_email text, klaviyo_match_flag boolean)
"""

import os
import sys
import logging
import psycopg2
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
logger = logging.getLogger(__name__)

SCHEMA = 'client_azure_co'

# ---------------------------------------------------------------------------
# DDL definitions — (schema, table, sql)
# ---------------------------------------------------------------------------

TABLES = [
    # ---- 1. public.network_pattern_benchmarks --------------------------------
    ('public', 'network_pattern_benchmarks', """
CREATE TABLE IF NOT EXISTS public.network_pattern_benchmarks (
    id                          bigint generated always as identity primary key,
    alert_type                  text not null,
    archetype                   text not null,
    metric_name                 text,
    pattern_description         text,
    benchmark_median            numeric,
    benchmark_p25               numeric,
    benchmark_p75               numeric,
    benchmark_bfcm_typical      numeric,
    network_confirmation_rate   numeric,
    sample_size                 integer,
    period_type                 text,
    last_updated                timestamptz default now(),
    created_at                  timestamptz default now()
);
"""),

    # ---- 2. public.permanent_dq_limitations ----------------------------------
    ('public', 'permanent_dq_limitations', """
CREATE TABLE IF NOT EXISTS public.permanent_dq_limitations (
    id                  bigint generated always as identity primary key,
    limitation_name     text not null,
    affected_sources    text[],
    affected_alerts     text[],
    estimated_impact    text,
    estimated_magnitude text,
    caveat_text         text,
    is_resolvable       boolean default false,
    resolution_path     text
);
"""),

    # ---- 3. brand_event_calendar ---------------------------------------------
    (SCHEMA, 'brand_event_calendar', f"""
CREATE TABLE IF NOT EXISTS {SCHEMA}.brand_event_calendar (
    id                      bigint generated always as identity primary key,
    client_id               text not null,
    event_name              text not null,
    event_type              text not null,
    start_date              date not null,
    end_date                date not null,
    suppress_alerts         text[],
    context_alerts          text[],
    context_explanation     text,
    residual_threshold_pct  numeric,
    confidence_decay_type   text,
    confidence_decay_start  date,
    confidence_decay_end    date,
    confidence_at_peak      numeric default 1.0,
    detection_method        text default 'auto',
    detection_lag_hours     integer,
    confidence              numeric default 1.0,
    last_verified_at        timestamptz,
    is_recurring            boolean default false,
    recurrence_rule         text,
    auto_detected           boolean default true,
    detected_from           text,
    event_profile           jsonb,
    suppression_type        text default 'reactive',
    is_synthetic            boolean default true,
    created_at              timestamptz default now()
);
"""),

    # ---- 4. sku_cost_master --------------------------------------------------
    (SCHEMA, 'sku_cost_master', f"""
CREATE TABLE IF NOT EXISTS {SCHEMA}.sku_cost_master (
    id                      bigint generated always as identity primary key,
    client_id               text not null,
    shopify_variant_id      text not null,
    sku                     text not null,
    record_type             text not null,
    supplier_cost           numeric,
    landed_cost             numeric,
    landed_cost_source      text,
    influencer_id           text,
    package_landed_cost     numeric,
    packaging_cost          numeric,
    shipping_cost           numeric,
    total_package_cost      numeric,
    featured_item_sku       text,
    non_featured_item_skus  text[],
    effective_from          date not null,
    effective_to            date,
    is_synthetic            boolean default true,
    created_at              timestamptz default now(),
    updated_at              timestamptz default now()
);
"""),

    # ---- 5. synthetic_touchpoint_journey ------------------------------------
    (SCHEMA, 'synthetic_touchpoint_journey', f"""
CREATE TABLE IF NOT EXISTS {SCHEMA}.synthetic_touchpoint_journey (
    order_id            text not null,
    touchpoint_sequence integer not null,
    channel             text,
    touchpoint_date     date,
    touchpoint_type     text,
    campaign_id         text,
    influencer_id       text
);
"""),

    # ---- 6. dq_metric_scores ------------------------------------------------
    (SCHEMA, 'dq_metric_scores', f"""
CREATE TABLE IF NOT EXISTS {SCHEMA}.dq_metric_scores (
    id                   bigint generated always as identity primary key,
    client_id            text not null,
    source               text not null,
    metric_domain        text not null,
    dq_score             numeric not null,
    dq_issues            text[],
    alert_types_affected text[],
    confidence_cap       numeric,
    freshness_tier       text,
    effective_from       timestamptz,
    effective_to         timestamptz,
    created_at           timestamptz default now()
);
"""),

    # ---- 7. dq_events -------------------------------------------------------
    (SCHEMA, 'dq_events', f"""
CREATE TABLE IF NOT EXISTS {SCHEMA}.dq_events (
    id                      bigint generated always as identity primary key,
    client_id               text not null,
    source                  text not null,
    dq_issue_code           text not null,
    metric_domain           text not null,
    started_at              timestamptz not null,
    resolved_at             timestamptz,
    peak_severity           integer,
    recovery_duration_hours integer,
    recovery_dq_curve       jsonb,
    backlog_order_count     integer,
    backlog_processing_lag  integer,
    cascade_to              text[],
    cascade_lag_hours       integer,
    cascade_duration_hours  integer,
    alerts_suppressed       text[],
    alerts_capped           jsonb,
    is_synthetic            boolean default true,
    created_at              timestamptz default now()
);
"""),

    # ---- 8. suppression_log -------------------------------------------------
    # FIX: signal_detected_at is nullable (no NOT NULL) to support predictive entries
    (SCHEMA, 'suppression_log', f"""
CREATE TABLE IF NOT EXISTS {SCHEMA}.suppression_log (
    id                          bigint generated always as identity primary key,
    client_id                   text not null,
    signal_detected_at          timestamptz,
    alert_type                  text not null,
    signal_value                numeric,
    threshold_value             numeric,
    suppression_reason          text not null,
    suppression_category        text not null,
    suppression_state           integer,
    suppression_type            text default 'reactive',
    variance_explained_pct      numeric,
    residual_signal             numeric,
    suppression_source          text,
    suppression_stack           jsonb,
    would_have_fired_at         timestamptz,
    detected_signal_description text,
    threshold_context           text,
    suppression_explanation     text,
    residual_signal_description text,
    founder_verification_action text,
    original_alert_log_id       bigint,
    retraction_reason           text,
    provisional_revised_value   numeric,
    full_accuracy_expected_at   timestamptz,
    founder_queryable           boolean default true,
    created_at                  timestamptz default now()
);
"""),

    # ---- 9. alert_data_lineage ----------------------------------------------
    # FIX: FK references public.alert_log(id) — alert_log lives in public schema
    (SCHEMA, 'alert_data_lineage', f"""
CREATE TABLE IF NOT EXISTS {SCHEMA}.alert_data_lineage (
    id               bigint generated always as identity primary key,
    alert_log_id     bigint references public.alert_log(id),
    source           text not null,
    metric_name      text not null,
    metric_value     numeric,
    source_row_ids   text[],
    source_query     text,
    row_count        integer,
    date_range_start date,
    date_range_end   date,
    created_at       timestamptz default now()
);
"""),

    # ---- 10. tiktok_organic_performance -------------------------------------
    (SCHEMA, 'tiktok_organic_performance', f"""
CREATE TABLE IF NOT EXISTS {SCHEMA}.tiktok_organic_performance (
    id                  bigint generated always as identity primary key,
    client_id           text not null,
    date                date not null,
    organic_reach_rate  numeric,
    posting_frequency   numeric,
    impressions         bigint,
    video_views         bigint,
    engagement_rate     numeric,
    created_at          timestamptz default now()
);
"""),

    # ---- 11. tag_normalisation ----------------------------------------------
    (SCHEMA, 'tag_normalisation', f"""
CREATE TABLE IF NOT EXISTS {SCHEMA}.tag_normalisation (
    id              bigint generated always as identity primary key,
    client_id       text not null,
    raw_tag         text not null,
    canonical_tag   text not null,
    category        text,
    created_at      timestamptz default now()
);
"""),

    # ---- 12. klaviyo_flow_id_history ----------------------------------------
    (SCHEMA, 'klaviyo_flow_id_history', f"""
CREATE TABLE IF NOT EXISTS {SCHEMA}.klaviyo_flow_id_history (
    id              bigint generated always as identity primary key,
    client_id       text not null,
    old_flow_id     text not null,
    new_flow_id     text,
    flow_name       text not null,
    change_reason   text,
    effective_from  date not null,
    effective_to    date,
    created_at      timestamptz default now()
);
"""),

    # ---- 13. klaviyo_sms_events ---------------------------------------------
    (SCHEMA, 'klaviyo_sms_events', f"""
CREATE TABLE IF NOT EXISTS {SCHEMA}.klaviyo_sms_events (
    id                  bigint generated always as identity primary key,
    client_id           text not null,
    profile_id          text not null,
    event_type          text not null,
    flow_id             text,
    campaign_id         text,
    message_type        text,
    sent_at             timestamptz,
    delivered_at        timestamptz,
    clicked_at          timestamptz,
    opted_out_at        timestamptz,
    attributed_order_id text,
    attributed_revenue  numeric,
    is_synthetic        boolean default true,
    created_at          timestamptz default now()
);
"""),

    # ---- 14. meta_billing_statement -----------------------------------------
    (SCHEMA, 'meta_billing_statement', f"""
CREATE TABLE IF NOT EXISTS {SCHEMA}.meta_billing_statement (
    id                  bigint generated always as identity primary key,
    client_id           text not null,
    statement_month     date not null,
    total_spend_exact   numeric(18,6),
    total_spend_api     numeric(10,2),
    rounding_gap        numeric(10,6),
    currency            text default 'USD',
    statement_date      date,
    source              text default 'finaloop',
    is_synthetic        boolean default true,
    created_at          timestamptz default now()
);
"""),

    # ---- 15. tiktok_billing_statement ----------------------------------------
    (SCHEMA, 'tiktok_billing_statement', f"""
CREATE TABLE IF NOT EXISTS {SCHEMA}.tiktok_billing_statement (
    id                  bigint generated always as identity primary key,
    client_id           text not null,
    statement_month     date not null,
    total_spend_exact   numeric(18,6),
    total_spend_api     numeric(10,2),
    rounding_gap        numeric(10,6),
    currency            text default 'USD',
    statement_date      date,
    source              text default 'finaloop',
    is_synthetic        boolean default true,
    created_at          timestamptz default now()
);
"""),

    # ---- 16. synthetic_customer_pii_lookup ----------------------------------
    # Schema per user specification (not from seed_decisions_gap_f_g.md)
    (SCHEMA, 'synthetic_customer_pii_lookup', f"""
CREATE TABLE IF NOT EXISTS {SCHEMA}.synthetic_customer_pii_lookup (
    synthetic_customer_id   text primary key,
    hashed_email            text,
    klaviyo_match_flag      boolean default false
);
"""),
]

# ---------------------------------------------------------------------------
# ALTER TABLE public.alert_log — add 11 new columns
# FIX: targets public.alert_log, not client_azure_co.alert_log
# ---------------------------------------------------------------------------

ALERT_LOG_ALTERS = [
    "ALTER TABLE public.alert_log ADD COLUMN IF NOT EXISTS fatigue_period_active boolean default false",
    "ALTER TABLE public.alert_log ADD COLUMN IF NOT EXISTS fatigue_reason text",
    "ALTER TABLE public.alert_log ADD COLUMN IF NOT EXISTS dismissal_correct boolean",
    "ALTER TABLE public.alert_log ADD COLUMN IF NOT EXISTS revenue_impact_missed numeric",
    "ALTER TABLE public.alert_log ADD COLUMN IF NOT EXISTS delivery_delayed_hours integer",
    "ALTER TABLE public.alert_log ADD COLUMN IF NOT EXISTS delay_reason text",
    "ALTER TABLE public.alert_log ADD COLUMN IF NOT EXISTS klaviyo_native_revenue numeric",
    "ALTER TABLE public.alert_log ADD COLUMN IF NOT EXISTS profit_sentinel_adjusted_revenue numeric",
    "ALTER TABLE public.alert_log ADD COLUMN IF NOT EXISTS alert_instance_number integer default 1",
    "ALTER TABLE public.alert_log ADD COLUMN IF NOT EXISTS escalation_level integer default 1",
    "ALTER TABLE public.alert_log ADD COLUMN IF NOT EXISTS suppression_type text",
]


def table_exists(cur, schema: str, table: str) -> bool:
    cur.execute(
        """
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = %s AND table_name = %s
        """,
        (schema, table),
    )
    return cur.fetchone() is not None


def column_exists(cur, schema: str, table: str, column: str) -> bool:
    cur.execute(
        """
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s AND column_name = %s
        """,
        (schema, table, column),
    )
    return cur.fetchone() is not None


def main():
    url = os.getenv('DATABASE_URL')
    if not url:
        logger.error('SOURCE: _create_seed_tables | ERROR: DATABASE_URL not set')
        sys.exit(1)

    try:
        conn = psycopg2.connect(url, sslmode='require')
        conn.autocommit = False
    except Exception as e:
        logger.error('SOURCE: _create_seed_tables | ERROR: connection failed | %s', e)
        sys.exit(1)

    created = []
    skipped = []
    errors  = []

    cur = conn.cursor()

    # ---- Create tables -------------------------------------------------------
    for schema, table, ddl in TABLES:
        try:
            existed = table_exists(cur, schema, table)
            cur.execute(ddl)
            conn.commit()
            if existed:
                skipped.append(f'{schema}.{table}')
                logger.info('SKIP (already exists): %s.%s', schema, table)
            else:
                created.append(f'{schema}.{table}')
                logger.info('CREATED: %s.%s', schema, table)
        except Exception as e:
            conn.rollback()
            errors.append(f'{schema}.{table}: {e}')
            logger.error(
                'SOURCE: _create_seed_tables | TABLE: %s.%s | ERROR: %s',
                schema, table, e,
            )

    # ---- ALTER TABLE public.alert_log ----------------------------------------
    logger.info('--- Applying ALTER TABLE public.alert_log ---')
    new_cols   = []
    exist_cols = []

    for stmt in ALERT_LOG_ALTERS:
        # Extract column name from statement for logging
        col_name = stmt.split('ADD COLUMN IF NOT EXISTS')[1].strip().split()[0]
        try:
            already = column_exists(cur, 'public', 'alert_log', col_name)
            cur.execute(stmt)
            conn.commit()
            if already:
                exist_cols.append(col_name)
                logger.info('  SKIP column (exists): public.alert_log.%s', col_name)
            else:
                new_cols.append(col_name)
                logger.info('  ADDED column: public.alert_log.%s', col_name)
        except Exception as e:
            conn.rollback()
            errors.append(f'public.alert_log.{col_name}: {e}')
            logger.error(
                'SOURCE: _create_seed_tables | COLUMN: public.alert_log.%s | ERROR: %s',
                col_name, e,
            )

    cur.close()
    conn.close()

    # ---- Final report --------------------------------------------------------
    print('\n' + '=' * 60)
    print('TABLE CREATION REPORT')
    print('=' * 60)

    print(f'\nCREATED ({len(created)}):')
    for t in created:
        print(f'  + {t}')

    print(f'\nSKIPPED — already existed ({len(skipped)}):')
    for t in skipped:
        print(f'  ~ {t}')

    print(f'\nalert_log columns ADDED ({len(new_cols)}):')
    for c in new_cols:
        print(f'  + {c}')

    print(f'\nalert_log columns SKIPPED — already existed ({len(exist_cols)}):')
    for c in exist_cols:
        print(f'  ~ {c}')

    if errors:
        print(f'\nERRORS ({len(errors)}):')
        for e in errors:
            print(f'  ! {e}')
        sys.exit(1)
    else:
        print('\nAll operations completed successfully.')


if __name__ == '__main__':
    main()
