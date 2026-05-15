"""
One-shot orchestration for 7 manually-designed tables:
  Meta Ads:  meta_ad_performance, meta_campaigns, meta_ad_sets
  Gorgias:   gorgias_tickets, gorgias_ticket_messages, gorgias_tags
  TikTok:    tiktok_ad_performance

Schema authority:
  Meta    — Airbyte GitHub JSON schemas (ads_insights, campaigns,
             ad_sets) + Section 8 breaking changes applied
  Gorgias — developers.gorgias.com/reference/the-ticket-object
  TikTok  — TikTok Business API, Supermetrics field reference

Steps run per table:
  1. CREATE TABLE (DDL in this file)
  2. ALTER TABLE to add is_synthetic (idempotent)
  3. Verify table exists
  4. schema_discovery
  5. python_transformer run 1 (first load)
  6. python_transformer run 2 (incremental test)
  7. Row count verification (raw vs staging)
  8. Summary report
"""

import contextlib
import io
import logging
import os
import sys
import time

import psycopg2
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from connectors.schema_discovery import discover_and_update_schema
from connectors.python_transformer import transform_table

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s %(levelname)-8s %(message)s',
)

CLIENT_ID = 'azure_co'
SCHEMA    = 'client_azure_co'
SEP       = '=' * 66

# Source name for schema_discovery registration
TABLE_SOURCE_MAP = {
    'meta_ad_performance':      'meta',
    'meta_campaigns':           'meta',
    'meta_ad_sets':             'meta',
    'gorgias_tickets':          'gorgias',
    'gorgias_ticket_messages':  'gorgias',
    'gorgias_tags':             'gorgias',
    'tiktok_ad_performance':    'tiktok',
}

ALL_TABLES = list(TABLE_SOURCE_MAP.keys())

DDL = {

    # ------------------------------------------------------------------
    # META ADS
    # ------------------------------------------------------------------

    'meta_ad_performance': """
        CREATE TABLE IF NOT EXISTS client_azure_co.meta_ad_performance (
            account_id                          text,
            account_name                        text,
            account_currency                    text,
            campaign_id                         text,
            campaign_name                       text,
            adset_id                            text,
            adset_name                          text,
            ad_id                               text,
            ad_name                             text,
            date_start                          text,
            date_stop                           text,
            created_time                        text,
            updated_time                        text,
            attribution_setting                 text,
            buying_type                         text,
            objective                           text,
            optimization_goal                   text,
            quality_ranking                     text,
            engagement_rate_ranking             text,
            conversion_rate_ranking             text,
            spend                               text,
            impressions                         text,
            clicks                              text,
            ctr                                 text,
            cpm                                 text,
            cpc                                 text,
            cpp                                 text,
            reach                               text,
            frequency                           text,
            social_spend                        text,
            inline_link_clicks                  text,
            inline_link_click_ctr               text,
            inline_post_engagement              text,
            unique_clicks                       text,
            unique_ctr                          text,
            unique_inline_link_clicks           text,
            unique_link_clicks_ctr              text,
            cost_per_inline_link_click          text,
            cost_per_inline_post_engagement     text,
            cost_per_unique_click               text,
            cost_per_unique_inline_link_click   text,
            full_view_impressions               text,
            full_view_reach                     text,
            estimated_ad_recallers              text,
            cost_per_estimated_ad_recallers     text,
            qualifying_question_qualify_answer_rate text,
            auction_bid                         text,
            auction_competitiveness             text,
            auction_max_competitor_bid          text,
            canvas_avg_view_percent             text,
            canvas_avg_view_time                text,
            instant_experience_clicks_to_open   text,
            instant_experience_clicks_to_start  text,
            actions                             jsonb,
            action_values                       jsonb,
            conversions                         jsonb,
            conversion_values                   jsonb,
            converted_product_quantity          jsonb,
            converted_product_value             jsonb,
            cost_per_action_type                jsonb,
            ad_click_actions                    jsonb,
            ad_impression_actions               jsonb,
            purchase_roas                       jsonb,
            website_purchase_roas               jsonb,
            mobile_app_purchase_roas            jsonb,
            catalog_segment_actions             jsonb,
            catalog_segment_value               jsonb,
            catalog_segment_value_mobile_purchase_roas  jsonb,
            catalog_segment_value_omni_purchase_roas    jsonb,
            catalog_segment_value_website_purchase_roas jsonb,
            website_ctr                         jsonb,
            outbound_clicks                     jsonb,
            outbound_clicks_ctr                 jsonb,
            cost_per_outbound_click             jsonb,
            unique_outbound_clicks              jsonb,
            unique_outbound_clicks_ctr          jsonb,
            cost_per_unique_outbound_click      jsonb,
            instant_experience_outbound_clicks  jsonb,
            video_play_actions                  jsonb,
            video_p25_watched_actions           jsonb,
            video_p50_watched_actions           jsonb,
            video_p75_watched_actions           jsonb,
            video_p95_watched_actions           jsonb,
            video_p100_watched_actions          jsonb,
            video_15_sec_watched_actions        jsonb,
            video_30_sec_watched_actions        jsonb,
            video_continuous_2_sec_watched_actions  jsonb,
            video_avg_time_watched_actions      jsonb,
            video_time_watched_actions          jsonb,
            video_play_curve_actions            jsonb,
            video_play_retention_0_to_15s_actions   jsonb,
            video_play_retention_20_to_60s_actions  jsonb,
            video_play_retention_graph_actions      jsonb,
            cost_per_thruplay                   jsonb,
            cost_per_2_sec_continuous_video_view    jsonb,
            cost_per_15_sec_video_view          jsonb,
            stored_before_retention_limit       boolean default false,
            _airbyte_extracted_at               timestamptz,
            is_synthetic                        boolean default false,
            UNIQUE (ad_id, date_start, date_stop)
        )
    """,

    'meta_campaigns': """
        CREATE TABLE IF NOT EXISTS client_azure_co.meta_campaigns (
            id                          text primary key,
            account_id                  text,
            name                        text,
            status                      text,
            configured_status           text,
            effective_status            text,
            objective                   text,
            buying_type                 text,
            bid_strategy                text,
            daily_budget                text,
            lifetime_budget             text,
            budget_remaining            text,
            spend_cap                   text,
            budget_rebalance_flag       text,
            smart_promotion_type        text,
            source_campaign_id          text,
            boosted_object_id           text,
            special_ad_category         text,
            special_ad_category_country jsonb,
            adlabels                    jsonb,
            issues_info                 jsonb,
            start_time                  text,
            stop_time                   text,
            created_time                text,
            updated_time                text,
            _airbyte_extracted_at       timestamptz,
            is_synthetic                boolean default false
        )
    """,

    'meta_ad_sets': """
        CREATE TABLE IF NOT EXISTS client_azure_co.meta_ad_sets (
            id                      text primary key,
            account_id              text,
            campaign_id             text,
            name                    text,
            status                  text,
            effective_status        text,
            daily_budget            text,
            lifetime_budget         text,
            budget_remaining        text,
            bid_amount              text,
            bid_strategy            text,
            bid_info                jsonb,
            bid_constraints         jsonb,
            start_time              text,
            end_time                text,
            created_time            text,
            updated_time            text,
            targeting               jsonb,
            promoted_object         jsonb,
            adlabels                jsonb,
            learning_stage_info     jsonb,
            _airbyte_extracted_at   timestamptz,
            is_synthetic            boolean default false
        )
    """,

    # ------------------------------------------------------------------
    # GORGIAS
    # ------------------------------------------------------------------

    'gorgias_tickets': """
        CREATE TABLE IF NOT EXISTS client_azure_co.gorgias_tickets (
            id                              bigint primary key,
            created_datetime                text,
            updated_datetime                text,
            opened_datetime                 text,
            closed_datetime                 text,
            snooze_datetime                 text,
            last_message_datetime           text,
            last_received_message_datetime  text,
            status                          text,
            channel                         text,
            via                             text,
            subject                         text,
            external_id                     text,
            language                        text,
            from_agent                      boolean,
            is_unread                       boolean,
            spam                            boolean,
            uri                             text,
            messages_count                  integer,
            customer                        jsonb,
            assignee_user                   jsonb,
            assignee_team                   jsonb,
            tags                            jsonb,
            meta                            jsonb,
            _airbyte_extracted_at           timestamptz,
            is_synthetic                    boolean default false
        )
    """,

    'gorgias_ticket_messages': """
        CREATE TABLE IF NOT EXISTS client_azure_co.gorgias_ticket_messages (
            id                  bigint primary key,
            ticket_id           bigint,
            created_datetime    text,
            updated_datetime    text,
            sent_datetime       text,
            failed_datetime     text,
            deleted_datetime    text,
            opened_datetime     text,
            channel             text,
            via                 text,
            subject             text,
            body_text           text,
            body_html           text,
            stripped_text       text,
            is_from_customer    boolean,
            from_agent          boolean,
            replied_to_id       bigint,
            uri                 text,
            source              jsonb,
            sender              jsonb,
            receiver            jsonb,
            attachments         jsonb,
            macros_applied      jsonb,
            _airbyte_extracted_at   timestamptz,
            is_synthetic            boolean default false
        )
    """,

    'gorgias_tags': """
        CREATE TABLE IF NOT EXISTS client_azure_co.gorgias_tags (
            id                  bigint primary key,
            name                text,
            created_datetime    text,
            updated_datetime    text,
            uri                 text,
            decoration          jsonb,
            _airbyte_extracted_at   timestamptz,
            is_synthetic            boolean default false
        )
    """,

    # ------------------------------------------------------------------
    # TIKTOK
    # ------------------------------------------------------------------

    'tiktok_ad_performance': """
        CREATE TABLE IF NOT EXISTS client_azure_co.tiktok_ad_performance (
            advertiser_id               text,
            campaign_id                 text,
            campaign_name               text,
            campaign_type               text,
            objective_type              text,
            adgroup_id                  text,
            adgroup_name                text,
            ad_id                       text,
            ad_name                     text,
            stat_time_day               text,
            spend                       text,
            impressions                 text,
            clicks                      text,
            ctr                         text,
            cpc                         text,
            cpm                         text,
            reach                       text,
            frequency                   text,
            conversions                 text,
            conversion_rate             text,
            cost_per_conversion         text,
            result                      text,
            result_rate                 text,
            cost_per_result             text,
            real_time_conversions       text,
            real_time_conversion_rate   text,
            video_play_actions          text,
            video_watched_2s            text,
            video_watched_6s            text,
            average_video_play          text,
            average_video_play_per_user text,
            video_views_p25             text,
            video_views_p50             text,
            video_views_p75             text,
            video_views_p100            text,
            likes                       text,
            comments                    text,
            shares                      text,
            follows                     text,
            profile_visits              text,
            engagements                 text,
            app_install                 text,
            cost_per_app_install        text,
            is_spark_ad                 boolean,
            spark_ad_type               text,
            promotion_type              text,
            identity_id                 text,
            identity_type               text,
            identity_authorized_bc_id   text,
            post_id                     text,
            video_id                    text,
            creative_format             text,
            landing_page_url            text,
            utm_source                  text,
            utm_medium                  text,
            utm_campaign                text,
            _airbyte_extracted_at       timestamptz,
            is_synthetic                boolean default false,
            UNIQUE (ad_id, stat_time_day)
        )
    """,
}


def add_is_synthetic(cur, table: str) -> str:
    try:
        cur.execute(
            f"ALTER TABLE {SCHEMA}.{table} "
            f"ADD COLUMN IF NOT EXISTS is_synthetic boolean default false"
        )
        cur.execute(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = %s
              AND table_name   = %s
              AND column_name  = 'is_synthetic'
            """,
            (SCHEMA, table),
        )
        return 'present' if cur.fetchone() else 'missing_after_alter'
    except Exception as exc:
        return f'ERROR: {exc}'


def get_row_count(cur, qualified: str):
    try:
        cur.execute(f'SELECT COUNT(*) FROM {qualified}')
        return cur.fetchone()[0]
    except Exception as exc:
        return f'ERROR: {exc}'


def get_registry_count(cur, table: str) -> int:
    cur.execute(
        """
        SELECT COUNT(*) FROM public.source_schema_registry
        WHERE client_id  = %s AND table_name = %s
        """,
        (CLIENT_ID, table),
    )
    return cur.fetchone()[0]


def _parse(text: str, label: str) -> str:
    for line in text.splitlines():
        if label in line and ':' in line:
            return line.split(':', 1)[1].strip()
    return '?'


def main():
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print('ERROR: DATABASE_URL not in .env')
        sys.exit(1)

    conn = psycopg2.connect(database_url, sslmode='require')
    conn.autocommit = False
    cur = conn.cursor()
    results = {t: {} for t in ALL_TABLES}

    # ------------------------------------------------------------------
    # STEP 1 — create tables
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 1 -- Creating Meta / Gorgias / TikTok tables')
    print(SEP)
    for table, stmt in DDL.items():
        try:
            cur.execute(stmt)
            print(f'  OK   {table}')
        except Exception as exc:
            print(f'  ERR  {table}')
            print(f'       {exc}')
    conn.commit()
    print()

    # ------------------------------------------------------------------
    # STEP 2 — add is_synthetic (idempotent — already in DDL but
    # mirrors the pattern used for Airbyte-created tables)
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 2 -- Confirming is_synthetic column')
    print(SEP)
    for table in ALL_TABLES:
        status = add_is_synthetic(cur, table)
        results[table]['is_synthetic'] = status
        print(f'  {table:<35}  is_synthetic: {status}')
    conn.commit()
    print()

    # ------------------------------------------------------------------
    # STEP 3 — verify tables exist
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 3 -- Verifying all tables exist')
    print(SEP)
    cur.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = %s
          AND table_name = ANY(%s)
        ORDER BY table_name
        """,
        (SCHEMA, ALL_TABLES),
    )
    found   = [r[0] for r in cur.fetchall()]
    missing = [t for t in ALL_TABLES if t not in found]
    for t in found:
        print(f'  EXISTS  {t}')
    if missing:
        print(f'\n  MISSING: {missing}')
        print('  Aborting — fix table creation before continuing.')
        conn.close()
        sys.exit(1)
    print()

    # ------------------------------------------------------------------
    # STEP 4 — schema discovery
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 4 -- Schema discovery')
    print(SEP)
    for table in ALL_TABLES:
        source_name = TABLE_SOURCE_MAP[table]
        t0 = time.time()
        summary = discover_and_update_schema(
            client_id=CLIENT_ID,
            table_name=table,
            source_name=source_name,
            conn=conn,
        )
        elapsed = time.time() - t0
        reg = get_registry_count(conn.cursor(), table)
        results[table]['reg_cols']  = reg
        results[table]['discovery'] = summary
        err_count = len(summary['errors'])
        print(
            f'  {table:<35}  '
            f'found={summary["found"]:>3}  '
            f'new={summary["new"]:>3}  '
            f'changed={summary["changed"]:>2}  '
            f'errors={err_count}  '
            f'registered={reg}  '
            f'({elapsed:.1f}s)'
        )

    # Per-source registry totals
    print()
    for src in ('meta', 'gorgias', 'tiktok'):
        cur2 = conn.cursor()
        cur2.execute(
            """
            SELECT COUNT(*) FROM public.source_schema_registry
            WHERE client_id = %s AND source_name = %s
            """,
            (CLIENT_ID, src),
        )
        print(f'  Total {src:<8} columns in registry: {cur2.fetchone()[0]}')
    print()

    # ------------------------------------------------------------------
    # STEP 5 — first load
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 5 -- First load (transform_table run 1)')
    print(SEP)
    for table in ALL_TABLES:
        buf = io.StringIO()
        t0 = time.time()
        with contextlib.redirect_stdout(buf):
            success = transform_table(
                client_id=CLIENT_ID,
                table_name=table,
                conn=conn,
            )
        elapsed = time.time() - t0
        out      = buf.getvalue()
        mode     = _parse(out, 'Load mode')
        rows     = _parse(out, 'Rows inserted')
        fallback = _parse(out, 'Cast-fallback columns')
        results[table].update({
            'run1_mode': mode, 'run1_rows': rows,
            'run1_fallbacks': fallback, 'run1_ok': success,
        })
        status = 'OK' if success else 'FAIL'
        print(
            f'  {table:<35}  {status}  '
            f'mode={mode}  rows={rows}  fallbacks={fallback}  ({elapsed:.1f}s)'
        )
    print()

    # ------------------------------------------------------------------
    # STEP 6 — incremental test (run 2)
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 6 -- Incremental test (transform_table run 2)')
    print(SEP)
    for table in ALL_TABLES:
        buf = io.StringIO()
        t0 = time.time()
        with contextlib.redirect_stdout(buf):
            success = transform_table(
                client_id=CLIENT_ID,
                table_name=table,
                conn=conn,
            )
        elapsed = time.time() - t0
        out    = buf.getvalue()
        mode   = _parse(out, 'Load mode')
        rows   = _parse(out, 'Rows inserted')
        wm_col = _parse(out, 'Watermark column')
        wm_val = _parse(out, 'Watermark value')
        inc_pass = (
            success
            and mode   == 'incremental'
            and rows   == '0'
            and wm_col == '_airbyte_extracted_at'
        )
        results[table].update({
            'run2_mode': mode, 'run2_rows': rows,
            'run2_wm_col': wm_col, 'run2_wm_val': wm_val,
            'run2_ok': success, 'inc_pass': inc_pass,
        })
        status = 'PASS' if inc_pass else 'FAIL'
        print(
            f'  {table:<35}  {status}  '
            f'mode={mode}  rows={rows}  wm_col={wm_col}  ({elapsed:.1f}s)'
        )
        if not inc_pass:
            print(f'    >> success={success}  wm_val={wm_val}')
    print()

    # ------------------------------------------------------------------
    # STEP 7 — row count verification
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 7 -- Row count verification (raw vs staging)')
    print(SEP)
    cur3 = conn.cursor()
    for table in ALL_TABLES:
        raw     = get_row_count(cur3, f'{SCHEMA}.{table}')
        staging = get_row_count(cur3, f'{SCHEMA}.stg_{table}')
        match   = (raw == staging) and not isinstance(raw, str)
        results[table]['raw_count']     = raw
        results[table]['staging_count'] = staging
        results[table]['count_match']   = match
        status = 'MATCH' if match else 'MISMATCH'
        print(
            f'  {table:<35}  '
            f'raw={raw!s:<6}  staging={staging!s:<6}  {status}'
        )
    print()

    conn.close()

    # ------------------------------------------------------------------
    # STEP 8 — summary
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 8 -- Summary')
    print(SEP)
    print(
        f'  {"Table":<35}  {"Cols":>4}  '
        f'{"Raw":>5}  {"Stg":>5}  '
        f'{"Counts":>7}  {"2-run":>6}  Fallbacks'
    )
    print('  ' + '-' * 72)
    all_pass = True
    for table in ALL_TABLES:
        r        = results[table]
        cols     = r.get('reg_cols', '?')
        raw      = r.get('raw_count', '?')
        stg      = r.get('staging_count', '?')
        counts   = 'MATCH' if r.get('count_match') else 'FAIL'
        two_run  = 'PASS'  if r.get('inc_pass')    else 'FAIL'
        fallback = r.get('run1_fallbacks', '?')
        if counts == 'FAIL' or two_run == 'FAIL':
            all_pass = False
        print(
            f'  {table:<35}  {cols!s:>4}  '
            f'{raw!s:>5}  {stg!s:>5}  '
            f'{counts:>7}  {two_run:>6}  {fallback}'
        )
    print()
    print(f'  Overall: {"ALL PASS" if all_pass else "SEE FAILURES ABOVE"}')
    print(SEP)
    return results


if __name__ == '__main__':
    main()
