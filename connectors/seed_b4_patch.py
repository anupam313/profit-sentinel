"""
B-4 Patch Script — SKU-to-Ad Attribution + Cross-Source Chain Hardening
Brand: Azure & Co (client_azure_co)

Applies ALTER TABLE + UPDATE to four existing tables:
  FIX 1 — meta_ad_performance:   campaign_objective, attribution_type,
                                  click_only_purchase_value, content_ids,
                                  conversion_value, date_day
  FIX 2 — tiktok_ad_performance: campaign_objective, content_ids,
                                  attribution_window, content_id_confidence
  FIX 4 — gorgias_tickets:       product_id, order_id, ticket_date,
                                  ticket_category, customer_email
  FIX 5 — loop_returns:          product_id, customer_email

FIX 3 (Google Ads) is handled by re-running seed_google_ads.py.

Semantic product_id labels (used in loop_returns, gorgias, and meta/tiktok content_ids):
  HERO_DRESS     → AZR-KNIT-STD-11-S  shopify_variant_id 8000658689  (top by landed_cost)
  HERO_DRESS_V2  → AZR-KNIT-STD-16-S  shopify_variant_id 8000717868
  KNIT_CLASSIC_M → AZR-KNIT-STD-10-M  shopify_variant_id 8000648397
  KNIT_PREMIUM_XL→ AZR-KNIT-STD-04-XL shopify_variant_id 8000576353
  KNIT_SEASONAL_M→ AZR-KNIT-STD-16-M  shopify_variant_id 8000720441

Three-source chain (A1 check):
  Gorgias sizing_issue ticket (Oct 28–Nov 14 2024)
  → stg_shopify_orders email join
  → Loop return with product_id='HERO_DRESS' (Nov 2024, 34–38%)
"""

import logging
import os
import sys

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)-8s %(message)s',
)
logger = logging.getLogger(__name__)

CLIENT_ID = 'azure_co'
SCHEMA    = 'client_azure_co'


def get_conn():
    url = os.getenv('DATABASE_URL')
    if not url:
        logger.error('SOURCE: B4 Patch | ERROR: DATABASE_URL not set')
        sys.exit(1)
    return psycopg2.connect(url, sslmode='require')


# ─── FIX 1 — meta_ad_performance ──────────────────────────────────────────────

def fix1_meta(cur) -> None:
    logger.info('FIX 1 — meta_ad_performance: adding B-4 columns')

    # Step 1a: Add columns (idempotent)
    cur.execute(f"""
        ALTER TABLE {SCHEMA}.meta_ad_performance
            ADD COLUMN IF NOT EXISTS campaign_objective         varchar,
            ADD COLUMN IF NOT EXISTS attribution_type          varchar,
            ADD COLUMN IF NOT EXISTS click_only_purchase_value numeric,
            ADD COLUMN IF NOT EXISTS content_ids               text[],
            ADD COLUMN IF NOT EXISTS conversion_value          numeric,
            ADD COLUMN IF NOT EXISTS date_day                  date
    """)
    logger.info('FIX 1 — ALTER TABLE done')

    # Step 1b: date_day = date_start::date
    cur.execute(f"""
        UPDATE {SCHEMA}.meta_ad_performance
        SET date_day = date_start::date
        WHERE date_day IS NULL
    """)

    # Step 1c: conversion_value from action_values JSONB
    cur.execute(f"""
        UPDATE {SCHEMA}.meta_ad_performance
        SET conversion_value = (action_values->0->>'value')::numeric
        WHERE conversion_value IS NULL
          AND action_values IS NOT NULL
    """)

    # Step 1d: campaign_objective from meta_campaigns.objective
    cur.execute(f"""
        UPDATE {SCHEMA}.meta_ad_performance m
        SET campaign_objective = CASE mc.objective
            WHEN 'CONVERSIONS' THEN 'OUTCOME_SALES'
            WHEN 'RETARGETING' THEN 'OUTCOME_SALES'
            WHEN 'REACH'       THEN 'OUTCOME_AWARENESS'
            ELSE                    'OUTCOME_SALES'
        END
        FROM {SCHEMA}.meta_campaigns mc
        WHERE m.campaign_id = mc.id
          AND m.campaign_objective IS NULL
    """)
    logger.info('FIX 1 — campaign_objective populated')

    # Step 1e: attribution_type
    cur.execute(f"""
        UPDATE {SCHEMA}.meta_ad_performance
        SET attribution_type = CASE
            WHEN campaign_objective = 'OUTCOME_AWARENESS' THEN 'view_through'
            ELSE 'click_through'
        END
        WHERE attribution_type IS NULL
    """)

    # Step 1f: click_only_purchase_value
    # OUTCOME_SALES: purchase_value × 0.72 (removes view-through inflation ~28%)
    # OUTCOME_AWARENESS: NULL (no purchase signal)
    cur.execute(f"""
        UPDATE {SCHEMA}.meta_ad_performance
        SET click_only_purchase_value = CASE
            WHEN campaign_objective = 'OUTCOME_AWARENESS' THEN NULL
            ELSE round((action_values->0->>'value')::numeric * 0.72, 2)
        END
        WHERE click_only_purchase_value IS NULL
          AND action_values IS NOT NULL
    """)

    # Step 1g: content_ids — derived from adset name + campaign objective
    #
    # BFCM prospecting/lookalike (Nov 2024 / Nov 2025): HERO_DRESS must be in array
    # Regular prospecting/lookalike: secondary SKU mix
    # Retargeting: narrow HERO_DRESS list
    # AWARENESS: NULL
    #
    # Adset name patterns (from seed_meta.py):
    #   Prospecting / Lookalike / BFCM…Prosp / BFCM…Looka / P_W / L_LAL
    #   Retargeting / Klaviyo / R_RETG / R_KLA
    #   Reach → objective=OUTCOME_AWARENESS → NULL already handled

    cur.execute(f"""
        UPDATE {SCHEMA}.meta_ad_performance m
        SET content_ids = CASE
            -- AWARENESS campaigns: no content_ids
            WHEN m.campaign_objective = 'OUTCOME_AWARENESS'
                THEN NULL

            -- BFCM Y1 prospecting/lookalike: HERO_DRESS is the promoted hero product
            WHEN m.date_start::date BETWEEN '2024-11-01' AND '2024-11-30'
                 AND (mas.name ILIKE '%prospecting%'
                      OR mas.name ILIKE '%lookalike%'
                      OR mas.name ILIKE '%prosp%'
                      OR mas.name ILIKE '%lal%')
                THEN ARRAY['HERO_DRESS', 'HERO_DRESS_V2', 'KNIT_CLASSIC_M']

            -- BFCM Y2 prospecting/lookalike
            WHEN m.date_start::date BETWEEN '2025-11-01' AND '2025-11-30'
                 AND (mas.name ILIKE '%prospecting%'
                      OR mas.name ILIKE '%lookalike%'
                      OR mas.name ILIKE '%prosp%'
                      OR mas.name ILIKE '%lal%')
                THEN ARRAY['HERO_DRESS', 'HERO_DRESS_V2', 'KNIT_CLASSIC_M', 'KNIT_SEASONAL_M']

            -- Regular prospecting / lookalike (outside BFCM)
            WHEN mas.name ILIKE '%prospecting%'
                 OR mas.name ILIKE '%lookalike%'
                 OR mas.name ILIKE 'p_%'
                 OR mas.name ILIKE 'l_%lal%'
                THEN ARRAY['HERO_DRESS_V2', 'KNIT_CLASSIC_M', 'KNIT_PREMIUM_XL', 'KNIT_SEASONAL_M']

            -- Retargeting / Klaviyo
            WHEN mas.name ILIKE '%retarg%'
                 OR mas.name ILIKE '%klaviyo%'
                 OR mas.name ILIKE 'r_%'
                THEN ARRAY['HERO_DRESS', 'HERO_DRESS_V2']

            -- Fallback for any SALES rows not matched above
            ELSE ARRAY['HERO_DRESS_V2', 'KNIT_CLASSIC_M']
        END
        FROM {SCHEMA}.meta_ad_sets mas
        WHERE m.adset_id = mas.id
          AND m.content_ids IS NULL
    """)
    logger.info('FIX 1 — content_ids populated')

    cur.execute(
        f"SELECT COUNT(*), SUM(CASE WHEN content_ids IS NOT NULL THEN 1 ELSE 0 END) "
        f"FROM {SCHEMA}.meta_ad_performance"
    )
    total, with_cids = cur.fetchone()
    logger.info('FIX 1 — meta_ad_performance: %d rows, %d with content_ids', total, with_cids)


# ─── FIX 2 — tiktok_ad_performance ────────────────────────────────────────────

def fix2_tiktok(cur) -> None:
    logger.info('FIX 2 — tiktok_ad_performance: adding B-4 columns')

    cur.execute(f"""
        ALTER TABLE {SCHEMA}.tiktok_ad_performance
            ADD COLUMN IF NOT EXISTS campaign_objective    varchar,
            ADD COLUMN IF NOT EXISTS content_ids          text[],
            ADD COLUMN IF NOT EXISTS attribution_window   varchar,
            ADD COLUMN IF NOT EXISTS content_id_confidence varchar
    """)
    logger.info('FIX 2 — ALTER TABLE done')

    # campaign_objective by campaign_type
    cur.execute(f"""
        UPDATE {SCHEMA}.tiktok_ad_performance
        SET campaign_objective = CASE campaign_type
            WHEN 'spark_ad_existing' THEN 'VIDEO_VIEWS'
            WHEN 'spark_ad_new'      THEN 'PRODUCT_SALES'
            WHEN 'in_feed_paid'      THEN 'PRODUCT_SALES'
            ELSE                          'PRODUCT_SALES'
        END
        WHERE campaign_objective IS NULL
    """)

    # attribution_window: TikTok standard
    cur.execute(f"""
        UPDATE {SCHEMA}.tiktok_ad_performance
        SET attribution_window = '7d_click_1d_view'
        WHERE attribution_window IS NULL
    """)

    # content_id_confidence (deterministic via hashtext):
    #   VIDEO_VIEWS (spark_ad_existing): 10% high / 15% low / 75% none
    #   PRODUCT_SALES (spark_ad_new, in_feed_paid): 43% high / 29% low / 28% none
    # Weighted overall: ~35% high / ~25% low / ~40% none
    cur.execute(f"""
        UPDATE {SCHEMA}.tiktok_ad_performance
        SET content_id_confidence = CASE
            WHEN campaign_type = 'spark_ad_existing' THEN
                CASE
                    WHEN ABS(hashtext(campaign_id || date::text)) % 100 < 10 THEN 'high'
                    WHEN ABS(hashtext(campaign_id || date::text)) % 100 < 25 THEN 'low'
                    ELSE NULL
                END
            ELSE  -- PRODUCT_SALES
                CASE
                    WHEN ABS(hashtext(campaign_id || date::text)) % 100 < 43 THEN 'high'
                    WHEN ABS(hashtext(campaign_id || date::text)) % 100 < 72 THEN 'low'
                    ELSE NULL
                END
        END
        WHERE content_id_confidence IS NULL
    """)

    # content_ids from confidence level
    cur.execute(f"""
        UPDATE {SCHEMA}.tiktok_ad_performance
        SET content_ids = CASE content_id_confidence
            WHEN 'high' THEN ARRAY['HERO_DRESS', 'HERO_DRESS_V2', 'KNIT_CLASSIC_M', 'KNIT_PREMIUM_XL']
            WHEN 'low'  THEN ARRAY['HERO_DRESS']
            ELSE NULL
        END
        WHERE content_ids IS NULL
    """)
    logger.info('FIX 2 — tiktok content_ids populated')

    cur.execute(
        f"SELECT campaign_type, "
        f"       SUM(CASE WHEN content_ids IS NOT NULL THEN 1 ELSE 0 END) as with_cids, "
        f"       COUNT(*) as total "
        f"FROM {SCHEMA}.tiktok_ad_performance "
        f"GROUP BY campaign_type ORDER BY campaign_type"
    )
    for row in cur.fetchall():
        logger.info('FIX 2 — %s: %d/%d with content_ids', row[0], row[1], row[2])


# ─── FIX 4 — gorgias_tickets ──────────────────────────────────────────────────

def fix4_gorgias(cur) -> None:
    logger.info('FIX 4 — gorgias_tickets: adding B-4 columns')

    cur.execute(f"""
        ALTER TABLE {SCHEMA}.gorgias_tickets
            ADD COLUMN IF NOT EXISTS product_id     text,
            ADD COLUMN IF NOT EXISTS order_id       text,
            ADD COLUMN IF NOT EXISTS ticket_date    date,
            ADD COLUMN IF NOT EXISTS ticket_category text,
            ADD COLUMN IF NOT EXISTS customer_email text
    """)
    logger.info('FIX 4 — ALTER TABLE done')

    # ticket_date = created_at::date
    cur.execute(f"""
        UPDATE {SCHEMA}.gorgias_tickets
        SET ticket_date = created_at::date
        WHERE ticket_date IS NULL
    """)

    # ticket_category = last_ticket_reason
    cur.execute(f"""
        UPDATE {SCHEMA}.gorgias_tickets
        SET ticket_category = last_ticket_reason
        WHERE ticket_category IS NULL
    """)

    # customer_email = 'cust_' || customer_id || '@synthetic.azureco.invalid'
    # gorgias customer_id IS the Shopify customer_id (8-digit integer)
    cur.execute(f"""
        UPDATE {SCHEMA}.gorgias_tickets
        SET customer_email = 'cust_' || customer_id || '@synthetic.azureco.invalid'
        WHERE customer_email IS NULL
          AND customer_id IS NOT NULL
    """)
    logger.info('FIX 4 — ticket_date, ticket_category, customer_email populated')

    # BFCM sizing_issue window: Oct 28 – Nov 14 2024 → product_id = 'HERO_DRESS'
    cur.execute(f"""
        UPDATE {SCHEMA}.gorgias_tickets
        SET product_id = 'HERO_DRESS'
        WHERE last_ticket_reason = 'sizing_issue'
          AND created_at::date BETWEEN '2024-10-28' AND '2024-11-14'
          AND product_id IS NULL
    """)
    cur.execute(
        f"SELECT COUNT(*) FROM {SCHEMA}.gorgias_tickets "
        f"WHERE last_ticket_reason = 'sizing_issue' "
        f"AND created_at::date BETWEEN '2024-10-28' AND '2024-11-14' "
        f"AND product_id = 'HERO_DRESS'"
    )
    bfcm_gg = cur.fetchone()[0]
    logger.info('FIX 4 — BFCM HERO_DRESS sizing tickets: %d', bfcm_gg)

    # Broader product_id coverage for other reasons (coverage targets from spec):
    # sizing_issue outside BFCM: 85% coverage
    cur.execute(f"""
        UPDATE {SCHEMA}.gorgias_tickets
        SET product_id = CASE
            WHEN ABS(hashtext(ticket_id)) % 10 < 3 THEN 'HERO_DRESS'
            WHEN ABS(hashtext(ticket_id)) % 10 < 6 THEN 'HERO_DRESS_V2'
            WHEN ABS(hashtext(ticket_id)) % 10 < 8 THEN 'KNIT_CLASSIC_M'
            ELSE NULL
        END
        WHERE last_ticket_reason = 'sizing_issue'
          AND product_id IS NULL
          AND ABS(hashtext(ticket_id)) % 100 < 85
    """)

    # product_quality: 70% coverage
    cur.execute(f"""
        UPDATE {SCHEMA}.gorgias_tickets
        SET product_id = CASE
            WHEN ABS(hashtext(ticket_id)) % 10 < 5 THEN 'HERO_DRESS'
            WHEN ABS(hashtext(ticket_id)) % 10 < 8 THEN 'HERO_DRESS_V2'
            ELSE 'KNIT_CLASSIC_M'
        END
        WHERE last_ticket_reason = 'product_quality'
          AND product_id IS NULL
          AND ABS(hashtext(ticket_id)) % 100 < 70
    """)

    # return_request: 60% coverage
    cur.execute(f"""
        UPDATE {SCHEMA}.gorgias_tickets
        SET product_id = CASE
            WHEN ABS(hashtext(ticket_id)) % 10 < 5 THEN 'HERO_DRESS'
            ELSE 'HERO_DRESS_V2'
        END
        WHERE last_ticket_reason = 'return_request'
          AND product_id IS NULL
          AND ABS(hashtext(ticket_id)) % 100 < 60
    """)
    logger.info('FIX 4 — gorgias_tickets product_id populated')

    cur.execute(
        f"SELECT last_ticket_reason, "
        f"       COUNT(*) as total, "
        f"       SUM(CASE WHEN product_id IS NOT NULL THEN 1 ELSE 0 END) as with_pid "
        f"FROM {SCHEMA}.gorgias_tickets "
        f"GROUP BY last_ticket_reason ORDER BY last_ticket_reason"
    )
    for row in cur.fetchall():
        logger.info('FIX 4 — %-20s total=%d with_product_id=%d', row[0], row[1], row[2])


# ─── FIX 5 — loop_returns ────────────────────────────────────────────────────

def fix5_loop_returns(cur) -> None:
    logger.info('FIX 5 — loop_returns: adding B-4 columns')

    cur.execute(f"""
        ALTER TABLE {SCHEMA}.loop_returns
            ADD COLUMN IF NOT EXISTS product_id     text,
            ADD COLUMN IF NOT EXISTS customer_email text
    """)
    logger.info('FIX 5 — ALTER TABLE done')

    # customer_email: derive via JOIN to shopify_orders
    # loop_returns.order_id = shopify_orders.id::text
    # shopify_orders.customer = JSONB with 'id' key (e.g., {"id": 10003305})
    cur.execute(f"""
        UPDATE {SCHEMA}.loop_returns lr
        SET customer_email = 'cust_' || (so.customer->>'id') || '@synthetic.azureco.invalid'
        FROM {SCHEMA}.shopify_orders so
        WHERE so.id::text = lr.order_id
          AND lr.customer_email IS NULL
          AND so.customer IS NOT NULL
          AND so.customer->>'id' IS NOT NULL
    """)
    cur.execute(f"SELECT COUNT(*) FROM {SCHEMA}.loop_returns WHERE customer_email IS NOT NULL")
    email_count = cur.fetchone()[0]
    logger.info('FIX 5 — customer_email set on %d rows', email_count)

    # HERO_DRESS elevation for Nov 2024 (target 34–38% of ~158 rows ≈ 54–60 rows)
    # Step 1: guarantee the 3 known chain-closing returns are set first
    # (returns from customers who also have Gorgias sizing tickets Oct 28–Nov 14)
    # gorgias.customer_id = Shopify customer_id (8-digit); shopify_orders.customer->>'id' = same
    cur.execute(f"""
        UPDATE {SCHEMA}.loop_returns lr
        SET product_id = 'HERO_DRESS'
        FROM {SCHEMA}.shopify_orders so
        WHERE so.id::text = lr.order_id
          AND lr.return_initiated_at::date BETWEEN '2024-11-01' AND '2024-11-30'
          AND (so.customer->>'id') IN (
              SELECT DISTINCT customer_id
              FROM {SCHEMA}.gorgias_tickets
              WHERE last_ticket_reason = 'sizing_issue'
                AND created_at::date BETWEEN '2024-10-28' AND '2024-11-14'
          )
          AND lr.product_id IS NULL
    """)
    cur.execute(
        f"SELECT COUNT(*) FROM {SCHEMA}.loop_returns "
        f"WHERE return_initiated_at::date BETWEEN '2024-11-01' AND '2024-11-30' "
        f"AND product_id = 'HERO_DRESS'"
    )
    chain_set = cur.fetchone()[0]
    logger.info('FIX 5 — HERO_DRESS set on %d chain-closing Nov 2024 returns', chain_set)

    # Step 2: extend HERO_DRESS to hit 36% of Nov 2024 total using hashtext
    cur.execute(f"""
        UPDATE {SCHEMA}.loop_returns
        SET product_id = 'HERO_DRESS'
        WHERE return_initiated_at::date BETWEEN '2024-11-01' AND '2024-11-30'
          AND product_id IS NULL
          AND ABS(hashtext(return_id)) % 100 < 36
    """)

    cur.execute(
        f"SELECT COUNT(*) FROM {SCHEMA}.loop_returns "
        f"WHERE return_initiated_at::date BETWEEN '2024-11-01' AND '2024-11-30'"
    )
    nov_total = cur.fetchone()[0]
    cur.execute(
        f"SELECT COUNT(*) FROM {SCHEMA}.loop_returns "
        f"WHERE return_initiated_at::date BETWEEN '2024-11-01' AND '2024-11-30' "
        f"AND product_id = 'HERO_DRESS'"
    )
    hero_count = cur.fetchone()[0]
    hero_pct = round(hero_count / nov_total * 100, 1) if nov_total else 0
    logger.info('FIX 5 — Nov 2024: %d total returns, %d HERO_DRESS (%.1f%%)',
                nov_total, hero_count, hero_pct)
    if not (34 <= hero_pct <= 40):
        logger.warning('FIX 5 — HERO_DRESS pct %.1f%% outside target 34–38%%', hero_pct)

    # Step 3: set secondary SKU product_ids for other Nov 2024 returns (optional realism)
    cur.execute(f"""
        UPDATE {SCHEMA}.loop_returns
        SET product_id = CASE
            WHEN ABS(hashtext(return_id)) % 3 = 0 THEN 'HERO_DRESS_V2'
            WHEN ABS(hashtext(return_id)) % 3 = 1 THEN 'KNIT_CLASSIC_M'
            ELSE 'KNIT_SEASONAL_M'
        END
        WHERE return_initiated_at::date BETWEEN '2024-11-01' AND '2024-11-30'
          AND product_id IS NULL
          AND ABS(hashtext(return_id)) % 100 < 55
    """)

    # Step 4: BFCM Y2 (Nov 2025) — similar elevation for HERO_DRESS
    cur.execute(f"""
        UPDATE {SCHEMA}.loop_returns
        SET product_id = 'HERO_DRESS'
        WHERE return_initiated_at::date BETWEEN '2025-11-01' AND '2025-11-30'
          AND product_id IS NULL
          AND ABS(hashtext(return_id || 'y2')) % 100 < 32
    """)
    logger.info('FIX 5 — loop_returns HERO_DRESS elevation complete')


# ─── Verification: 8 cross-source chain checks ─────────────────────────────────

def run_chain_checks(conn) -> None:
    print('\n' + '=' * 72)
    print('B-4 CROSS-SOURCE CHAIN VERIFICATION — 8 CHECKS')
    print('=' * 72)

    c = conn.cursor()

    def check(label: str, sql: str, params=None, expect_gt: int = 0):
        try:
            c.execute(sql, params or ())
            row = c.fetchone()
            val = row[0] if row else 0
            ok = val > expect_gt
            print(f'\n[{"PASS" if ok else "FAIL"}] {label}')
            print(f'       result={val}  expected > {expect_gt}')
            return val
        except Exception as e:
            print(f'\n[ERR ] {label}: {e}')
            return 0

    def check_exact(label: str, sql: str):
        try:
            c.execute(sql)
            rows = c.fetchall()
            print(f'\n[INFO] {label}')
            for r in rows:
                print(f'       {r}')
            return rows
        except Exception as e:
            print(f'\n[ERR ] {label}: {e}')
            return []

    # CHECK 1: Three-source chain closure
    # Gorgias sizing Oct28–Nov14 → Shopify email join → Loop HERO_DRESS Nov
    check(
        'CHECK 1 -- Three-source chain: Gorgias sizing + Shopify email + Loop HERO_DRESS',
        f"""
        SELECT COUNT(DISTINCT g.ticket_id)
        FROM {SCHEMA}.gorgias_tickets g
        JOIN {SCHEMA}.shopify_orders so
            ON 'cust_' || (so.customer->>'id') || '@synthetic.azureco.invalid' = g.customer_email
        JOIN {SCHEMA}.loop_returns lr
            ON lr.order_id = so.id::text
           AND lr.product_id = 'HERO_DRESS'
           AND lr.return_initiated_at::date BETWEEN '2024-11-01' AND '2024-11-30'
        WHERE g.ticket_category = 'sizing_issue'
          AND g.ticket_date BETWEEN '2024-10-28' AND '2024-11-14'
        """,
        expect_gt=0,
    )

    # CHECK 2: BFCM sizing tickets have product_id = HERO_DRESS
    check(
        'CHECK 2 — Gorgias BFCM sizing tickets with HERO_DRESS product_id',
        f"""
        SELECT COUNT(*)
        FROM {SCHEMA}.gorgias_tickets
        WHERE ticket_category = 'sizing_issue'
          AND ticket_date BETWEEN '2024-10-28' AND '2024-11-14'
          AND product_id = 'HERO_DRESS'
        """,
        expect_gt=0,
    )

    # CHECK 3: Meta content_ids chain (adsets with HERO_DRESS content_ids + loop returns)
    check(
        'CHECK 3 — Meta content_ids: adsets join to HERO_DRESS loop returns Nov 2024',
        f"""
        SELECT COUNT(DISTINCT m.adset_id)
        FROM {SCHEMA}.meta_ad_performance m
        JOIN {SCHEMA}.loop_returns lr
            ON lr.product_id = ANY(m.content_ids)
           AND lr.return_initiated_at::date
               BETWEEN m.date_start::date - 7 AND m.date_start::date
        WHERE m.content_ids IS NOT NULL
          AND m.date_start::date BETWEEN '2024-11-01' AND '2024-11-30'
        """,
        expect_gt=0,
    )

    # CHECK 4: TikTok content_ids non-null distribution
    check_exact(
        'CHECK 4 — TikTok content_id_confidence distribution',
        f"""
        SELECT content_id_confidence,
               COUNT(*)                                   as rows,
               ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as pct
        FROM {SCHEMA}.tiktok_ad_performance
        GROUP BY content_id_confidence
        ORDER BY content_id_confidence NULLS LAST
        """,
    )

    # CHECK 5: Meta campaign_objective coverage
    check_exact(
        'CHECK 5 — Meta campaign_objective distribution',
        f"""
        SELECT campaign_objective,
               COUNT(*) as rows,
               ROUND(AVG((purchase_roas->0->>'value')::numeric), 3) as avg_roas
        FROM {SCHEMA}.meta_ad_performance
        GROUP BY campaign_objective
        ORDER BY campaign_objective
        """,
    )

    # CHECK 6: Loop returns Nov 2024 HERO_DRESS rate (target 34–38%)
    c.execute(f"""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN product_id = 'HERO_DRESS' THEN 1 ELSE 0 END) as hero_count
        FROM {SCHEMA}.loop_returns
        WHERE return_initiated_at::date BETWEEN '2024-11-01' AND '2024-11-30'
    """)
    r = c.fetchone()
    total, hero = (r[0] or 0), (r[1] or 0)
    pct = round(hero / total * 100, 1) if total else 0
    ok = 34 <= pct <= 40
    print(f'\n[{"PASS" if ok else "FAIL"}] CHECK 6 — Loop HERO_DRESS elevation Nov 2024')
    print(f'       total={total}  hero_dress={hero}  rate={pct}%  target=34-38%')

    # CHECK 7: customer_email join rate between gorgias and loop_returns
    check(
        'CHECK 7 — customer_email present on loop_returns',
        f"SELECT COUNT(*) FROM {SCHEMA}.loop_returns WHERE customer_email IS NOT NULL",
        expect_gt=1000,
    )

    # CHECK 8: Gorgias ticket_date, ticket_category, customer_email all populated
    c.execute(f"""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN ticket_date IS NOT NULL THEN 1 ELSE 0 END)     as has_date,
               SUM(CASE WHEN ticket_category IS NOT NULL THEN 1 ELSE 0 END) as has_cat,
               SUM(CASE WHEN customer_email IS NOT NULL THEN 1 ELSE 0 END)  as has_email
        FROM {SCHEMA}.gorgias_tickets
    """)
    r = c.fetchone()
    total, has_d, has_c, has_e = r
    ok = (has_d == total and has_c == total and has_e == total)
    print(f'\n[{"PASS" if ok else "FAIL"}] CHECK 8 — Gorgias new columns fully populated')
    print(f'       total={total}  ticket_date={has_d}  ticket_category={has_c}  '
          f'customer_email={has_e}')

    print('\n' + '=' * 72 + '\n')


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    logger.info('SOURCE: B4 Patch | CLIENT: %s | Starting', CLIENT_ID)
    conn = get_conn()
    try:
        with conn:
            cur = conn.cursor()
            fix1_meta(cur)
            fix2_tiktok(cur)
            fix4_gorgias(cur)
            fix5_loop_returns(cur)
        run_chain_checks(conn)
        logger.info('SOURCE: B4 Patch | CLIENT: %s | Complete', CLIENT_ID)
    except Exception as e:
        logger.error('SOURCE: B4 Patch | CLIENT: %s | ERROR: %s', CLIENT_ID, str(e))
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    main()
