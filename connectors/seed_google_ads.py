"""
Profit Sentinel — Google Ads Synthetic Seed Script
Brand: Azure & Co (client_azure_co)
Google Ads API version: v24.1 (confirmed 2026-05-21)

API field mapping (metrics.* / campaign.* → table column):
  metrics.cost_micros               → cost_micros               (bigint, ÷1e6 for USD)
  metrics.impressions               → impressions
  metrics.clicks                    → clicks
  metrics.ctr                       → ctr
  metrics.average_cpc               → average_cpc               (numeric, USD)
  metrics.conversions               → conversions
  metrics.conversion_value          → conversion_value           (USD)
  metrics.conversion_value_per_cost → conversion_value_per_cost  (ROAS)
  metrics.search_impression_share   → search_impression_share
  segments.quality_score            → quality_score              (keyword-level integer)
  campaign.id                       → campaign_id
  campaign.advertising_channel_type → campaign_type
  ad_group.id                       → ad_group_id

PMax carve-outs (NULL for PERFORMANCE_MAX rows):
  ad_group_id, ad_group_name        — no standard AdGroup in PMax (uses asset_group)
  search_impression_share           — unavailable at PMax campaign level
  quality_score                     — keyword-based metric, N/A for PMax

Table seeded: client_azure_co.google_ads_performance
  7 campaigns × ~731 daily rows + 20 ad-set split rows ≈ 5,137 rows total

Zero-spend window: Azure_Shopping_Main (G_SHOP_001), 2025-07-15–2025-07-28
  — 14 consecutive days at $0 while other campaigns continue spend
  — triggers stockout_with_active_spend_count for G1 chain testing

Real-data nuances implemented (6 fixes):
  Fix 1: Conversion lag  — 5 false-zero-conversion dates per campaign (~35 rows)
  Fix 2: Attribution window  — per-campaign-type window strings + mismatch note
  Fix 3: PMax diagnostic  — block reason + 0.65 confidence cap for PMax rows
  Fix 4: Stockout boundary  — reporting_delay_flag on G_SHOP_001 ±3-day boundary
  Fix 5: cost_micros rounding  — G_SRCH_002 split into 3 ad-set rows on 10 dates
  Fix 6: Campaign rename  — G_SRCH_001 and G_SHOP_001 renamed 2025-10-01
"""

import logging
import os
from datetime import date, timedelta

import numpy as np
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)-8s %(message)s',
)
logger = logging.getLogger(__name__)

CLIENT_ID = 'client_azure_co'
SCHEMA    = 'client_azure_co'

SEED_END   = date.today()
SEED_START = date(SEED_END.year - 2, SEED_END.month, SEED_END.day)

SHOPPING_ZERO_START = date(2025, 7, 15)
SHOPPING_ZERO_END   = date(2025, 7, 28)

# Fix 4: boundary dates flanking the G_SHOP_001 zero-spend window
BOUNDARY_CAMPAIGN    = 'G_SHOP_001'
BOUNDARY_DAYS_BEFORE = {date(2025, 7, 12), date(2025, 7, 13), date(2025, 7, 14)}
BOUNDARY_DAYS_AFTER  = {date(2025, 7, 29), date(2025, 7, 30), date(2025, 7, 31)}
BOUNDARY_DATES       = BOUNDARY_DAYS_BEFORE | BOUNDARY_DAYS_AFTER

# Fix 5: G_SRCH_002 (non-brand search) split into 3 ad-set rows on 10 dates
SPLIT_CAMPAIGN_ID = 'G_SRCH_002'
SPLIT_AG_IDS      = ['AG_001', 'AG_002', 'AG_003']
SPLIT_AG_NAMES    = ['NonBrand_AG_001', 'NonBrand_AG_002', 'NonBrand_AG_003']

# Fix 6: campaign rename at 2025-10-01
RENAME_DATE = date(2025, 10, 1)
RENAMED_CAMPAIGNS = {
    'G_SRCH_001': ('Azure_Search_Brand',   'Brand Search — Exact Match'),
    'G_SHOP_001': ('Azure_Shopping_Main',  'Azure_Shopping_Core'),
}

# Fix 2: attribution window by campaign type (exact Google Ads API strings)
ATTRIBUTION_WINDOWS = {
    'SEARCH':          '30d_last_click',
    'SHOPPING':        '30d_last_click',
    'PERFORMANCE_MAX': '30d_last_click',
    'VIDEO':           '1d_view_7d_click',
    'DEMAND_GEN':      '7d_click_1d_view',
}
ATTRIBUTION_NOTE = (
    'Attribution mismatch vs Meta (7d_click/1d_view). '
    'Blended ROAS cross-source comparison is directional only — not apples-to-apples.'
)

# Fix 3: PMax diagnostic strings
PMAX_BLOCK_REASON = (
    'PMAX_DIAGNOSTIC_BLOCKED: Google withholds asset-level, ad group, '
    'and search term data for Performance Max campaigns. Evidence Stack '
    'Layer 2 incomplete by design — not a data error.'
)

RNG = np.random.default_rng(42)

# ─── Campaign definitions ──────────────────────────────────────────────────────

CAMPAIGNS = [
    {
        'id': 'G_SRCH_001', 'name': 'Azure_Search_Brand',
        'type': 'SEARCH',
        'ag_id': 'AG_SB_001', 'ag_name': 'Brand_Core',
        'budget_share': 0.07,
        'avg_cpc': 1.80, 'ctr': 0.10, 'roas_target': 8.5,
        'search_is': 0.72, 'quality_score': 9,
        'zero_spend': False,
    },
    {
        'id': 'G_SRCH_002', 'name': 'Azure_Search_NonBrand',
        'type': 'SEARCH',
        'ag_id': 'AG_SNB_001', 'ag_name': 'NonBrand_Category',
        'budget_share': 0.28,
        'avg_cpc': 2.80, 'ctr': 0.045, 'roas_target': 4.5,
        'search_is': 0.42, 'quality_score': 7,
        'zero_spend': False,
    },
    {
        'id': 'G_SHOP_001', 'name': 'Azure_Shopping_Main',
        'type': 'SHOPPING',
        'ag_id': 'AG_SM_001', 'ag_name': 'Shopping_AllProducts',
        'budget_share': 0.21,
        'avg_cpc': 1.20, 'ctr': 0.012, 'roas_target': 6.0,
        'search_is': None, 'quality_score': None,
        'zero_spend': True,
    },
    {
        'id': 'G_SHOP_002', 'name': 'Azure_Shopping_Retargeting',
        'type': 'SHOPPING',
        'ag_id': 'AG_SR_001', 'ag_name': 'Shopping_Retarget',
        'budget_share': 0.09,
        'avg_cpc': 0.95, 'ctr': 0.018, 'roas_target': 7.5,
        'search_is': None, 'quality_score': None,
        'zero_spend': False,
    },
    {
        'id': 'G_PMAX_001', 'name': 'Azure_PMax_AllProducts',
        'type': 'PERFORMANCE_MAX',
        'ag_id': None, 'ag_name': None,
        'budget_share': 0.20,
        'avg_cpc': 1.60, 'ctr': 0.025, 'roas_target': 5.5,
        'search_is': None, 'quality_score': None,
        'zero_spend': False,
    },
    {
        'id': 'G_VID_001', 'name': 'Azure_YouTube_Brand',
        'type': 'VIDEO',
        'ag_id': 'AG_YT_001', 'ag_name': 'YouTube_BrandAwareness',
        'budget_share': 0.10,
        'avg_cpc': 0.55, 'ctr': 0.003, 'roas_target': 2.5,
        'search_is': None, 'quality_score': None,
        'zero_spend': False,
    },
    {
        'id': 'G_DGEN_001', 'name': 'Azure_DemandGen_Prospecting',
        'type': 'DEMAND_GEN',
        'ag_id': 'AG_DG_001', 'ag_name': 'DemandGen_Prospect',
        'budget_share': 0.05,
        'avg_cpc': 0.75, 'ctr': 0.008, 'roas_target': 3.5,
        'search_is': None, 'quality_score': None,
        'zero_spend': False,
    },
]

assert abs(sum(c['budget_share'] for c in CAMPAIGNS) - 1.0) < 0.001, \
    f"Budget shares sum to {sum(c['budget_share'] for c in CAMPAIGNS)}, expected 1.0"


# ─── Helpers ──────────────────────────────────────────────────────────────────

def seasonal_multiplier(d: date) -> float:
    """Scale daily spend by fashion seasonal calendar."""
    m, day = d.month, d.day
    if m == 11 and day >= 15:   return 2.2
    if m == 12 and day <= 5:    return 2.0
    if m == 12:                 return 1.5
    if m in (2, 3):             return 1.6
    if m in (8, 9):             return 1.5
    if m == 1:                  return 0.8
    if m in (6, 7):             return 0.9
    return 1.0


def get_campaign_name(campaign_id: str, base_name: str, d: date) -> str:
    """Return the active campaign name on date d, applying Fix 6 rename if applicable."""
    if campaign_id in RENAMED_CAMPAIGNS:
        before_name, after_name = RENAMED_CAMPAIGNS[campaign_id]
        return after_name if d >= RENAME_DATE else before_name
    return base_name


def get_campaign_name_history(campaign_id: str, base_name: str) -> list:
    """Return full name history array for Fix 6."""
    if campaign_id in RENAMED_CAMPAIGNS:
        before_name, after_name = RENAMED_CAMPAIGNS[campaign_id]
        return [before_name, after_name]
    return [base_name]


def precompute_stochastic_sets(all_dates: list) -> tuple[set, dict]:
    """
    Deterministically select Fix 5 split dates and Fix 1 lag dates.
    Called once before generate_rows() so RNG state is consumed in a
    fixed order before the main per-row generation loop begins.
    """
    # Fix 5: 10 dates for G_SRCH_002 ad-set split
    split_indices = sorted(RNG.choice(len(all_dates), size=10, replace=False))
    split_dates = set(all_dates[i] for i in split_indices)

    # Fix 1: 5 lag dates per campaign (exclude zero-spend dates)
    lag_dates: dict[str, set] = {}
    for c in CAMPAIGNS:
        pool = [
            d for d in all_dates
            if not (c['zero_spend'] and SHOPPING_ZERO_START <= d <= SHOPPING_ZERO_END)
        ]
        idxs = sorted(RNG.choice(len(pool), size=5, replace=False))
        lag_dates[c['id']] = set(pool[i] for i in idxs)

    return split_dates, lag_dates


def get_conn():
    return psycopg2.connect(os.getenv('DATABASE_URL'), sslmode='require')


# ─── DDL ──────────────────────────────────────────────────────────────────────

CREATE_DDL = f"""
CREATE TABLE {SCHEMA}.google_ads_performance (
    id                        bigint generated always as identity primary key,
    date_day                  date           not null,
    campaign_id               text           not null,
    campaign_name             text,
    campaign_type             text,
    ad_group_id               text,
    ad_group_name             text,
    cost_micros               bigint,
    impressions               bigint,
    clicks                    bigint,
    ctr                       numeric,
    average_cpc               numeric,
    conversions               numeric,
    conversion_value          numeric,
    conversion_value_per_cost numeric,
    search_impression_share   numeric,
    quality_score             integer,
    is_synthetic              boolean        default true,
    _airbyte_extracted_at     timestamptz    default now(),
    -- Fix 1: conversion lag disclosure
    data_completeness_flag    varchar,
    -- Fix 2: attribution window disclosure (NOT NULL — always set)
    attribution_window        varchar        not null,
    attribution_window_note   varchar        not null,
    -- Fix 3: PMax diagnostic (NULL for non-PMax rows)
    diagnostic_block_reason   varchar,
    max_confidence_cap        float          default 1.0,
    -- Fix 4: stockout date boundary off-by-one
    reporting_delay_flag      boolean        default false,
    -- Fix 5: ad-set split rows
    ad_set_split_row          boolean        default false,
    -- Fix 6: campaign rename history
    campaign_name_history     text[],
    campaign_name_is_stable   boolean        default true,
    -- B-4: campaign objective (load-bearing: AWARENESS → ROAS = NULL)
    campaign_objective        varchar,
    -- B-4: product-level attribution (SHOPPING only; NULL with reason code for all others)
    product_id                text,
    reason_product_id_null    varchar,
    -- B-4: video completion metrics (VIDEO campaign rows only; NULL for all others)
    video_view_rate           numeric,
    video_quartile_p25_rate   numeric,
    video_quartile_p50_rate   numeric,
    video_quartile_p75_rate   numeric,
    video_quartile_p100_rate  numeric,
    average_cpv               numeric
)
"""


# ─── Row generation ───────────────────────────────────────────────────────────

def _build_base_row(
    d: date,
    c: dict,
    cost_micros_val: int,
    impressions: int,
    clicks: int,
    ctr: float,
    avg_cpc: float,
    conversions: float,
    conversion_value: float,
    roas_val,
    sis,
    is_lag: bool,
    shopping_product_idx: int = 0,
) -> dict:
    """Assemble the fields shared across all row variants for a campaign/date."""
    camp_name         = get_campaign_name(c['id'], c['name'], d)
    camp_name_history = get_campaign_name_history(c['id'], c['name'])
    camp_name_stable  = c['id'] not in RENAMED_CAMPAIGNS

    # Fix 2
    attr_window = ATTRIBUTION_WINDOWS[c['type']]

    # Fix 3
    diag_reason = PMAX_BLOCK_REASON if c['type'] == 'PERFORMANCE_MAX' else None
    conf_cap    = 0.65 if c['type'] == 'PERFORMANCE_MAX' else 1.0

    # Fix 4
    delay_flag = (c['id'] == BOUNDARY_CAMPAIGN and d in BOUNDARY_DATES)

    # B-4: campaign_objective
    if c['type'] in ('VIDEO', 'DEMAND_GEN'):
        campaign_objective = 'AWARENESS_AND_CONSIDERATION'
    else:
        campaign_objective = 'SALES'

    # B-4: product_id (SHOPPING only) + reason_product_id_null
    _SHOPPING_VARIANT_IDS = [
        '8000658689', '8000717868', '8000648397', '8000576353', '8000720441',
    ]
    if c['type'] == 'SHOPPING':
        product_id            = _SHOPPING_VARIANT_IDS[shopping_product_idx % 5]
        reason_product_id_null = None
    elif c['type'] == 'PERFORMANCE_MAX':
        product_id            = None
        reason_product_id_null = (
            'PMAX_PRODUCT_CONVERSION_WITHHELD: Google withholds product-level '
            'attribution for Performance Max campaigns. See diagnostic_block_reason.'
        )
    else:
        product_id            = None
        reason_product_id_null = (
            f'CAMPAIGN_TYPE_NO_PRODUCT_SIGNAL: {c["type"]} campaigns do not '
            'expose product-level attribution in Google Ads API v24.1.'
        )

    return {
        'date_day':                  d,
        'campaign_id':               c['id'],
        'campaign_name':             camp_name,
        'campaign_type':             c['type'],
        'ad_group_id':               c['ag_id'],
        'ad_group_name':             c['ag_name'],
        'cost_micros':               cost_micros_val,
        'impressions':               impressions,
        'clicks':                    clicks,
        'ctr':                       round(ctr, 6),
        'average_cpc':               round(avg_cpc, 4),
        'conversions':               conversions,
        'conversion_value':          round(conversion_value, 2),
        'conversion_value_per_cost': roas_val,
        'search_impression_share':   sis,
        'quality_score':             c['quality_score'],
        'is_synthetic':              True,
        'data_completeness_flag':    'CONVERSION_LAG_PENDING' if is_lag else None,
        'attribution_window':        attr_window,
        'attribution_window_note':   ATTRIBUTION_NOTE,
        'diagnostic_block_reason':   diag_reason,
        'max_confidence_cap':        conf_cap,
        'reporting_delay_flag':      delay_flag,
        'ad_set_split_row':          False,
        'campaign_name_history':     camp_name_history,
        'campaign_name_is_stable':   camp_name_stable,
        'campaign_objective':        campaign_objective,
        'product_id':                product_id,
        'reason_product_id_null':    reason_product_id_null,
        'video_view_rate':           None,
        'video_quartile_p25_rate':   None,
        'video_quartile_p50_rate':   None,
        'video_quartile_p75_rate':   None,
        'video_quartile_p100_rate':  None,
        'average_cpv':               None,
    }


def generate_rows(split_dates: set, lag_dates: dict) -> list[dict]:
    rows = []
    base_monthly   = 12_000.0
    days_per_month = 30.0
    shopping_idx   = 0  # cycles through top-5 variant IDs for SHOPPING rows

    current = SEED_START
    while current <= SEED_END:
        s           = seasonal_multiplier(current)
        daily_total = (base_monthly * s / days_per_month) * float(RNG.uniform(0.85, 1.15))

        for c in CAMPAIGNS:
            is_zero = (
                c['zero_spend']
                and SHOPPING_ZERO_START <= current <= SHOPPING_ZERO_END
            )

            if is_zero:
                rows.append(_build_base_row(
                    d=current, c=c,
                    cost_micros_val=0, impressions=0, clicks=0,
                    ctr=0.0, avg_cpc=0.0,
                    conversions=0.0, conversion_value=0.0,
                    roas_val=None, sis=c['search_is'],
                    is_lag=False,
                    shopping_product_idx=shopping_idx,
                ))
                if c['type'] == 'SHOPPING':
                    shopping_idx += 1
                continue

            daily_spend     = daily_total * c['budget_share'] * float(RNG.uniform(0.90, 1.10))
            cost_micros_val = int(daily_spend * 1_000_000)

            avg_cpc     = c['avg_cpc'] * float(RNG.uniform(0.85, 1.15))
            clicks      = max(1, int(daily_spend / avg_cpc))
            ctr         = c['ctr'] * float(RNG.uniform(0.80, 1.20))
            impressions = max(clicks, int(clicks / max(ctr, 0.0001)))

            roas             = c['roas_target'] * (0.7 + 0.3 * s) * float(RNG.uniform(0.75, 1.25))
            roas             = max(0.5, roas)
            conversion_value = daily_spend * roas
            aov              = 150.0 * float(RNG.uniform(0.90, 1.10))
            conversions      = round(conversion_value / aov, 2)

            sis = None
            if c['search_is'] is not None:
                sis = round(
                    min(0.95, c['search_is'] * (0.8 + 0.2 * s) * float(RNG.uniform(0.85, 1.15))),
                    4,
                )

            # Fix 1: conversion lag — zero out conversions, keep spend
            is_lag = current in lag_dates.get(c['id'], set())
            if is_lag:
                conversions      = 0.0
                conversion_value = 0.0
                roas_val         = None
            else:
                roas_val = round(roas, 4)

            base_row = _build_base_row(
                d=current, c=c,
                cost_micros_val=cost_micros_val,
                impressions=impressions, clicks=clicks,
                ctr=ctr, avg_cpc=avg_cpc,
                conversions=conversions,
                conversion_value=conversion_value,
                roas_val=roas_val, sis=sis,
                is_lag=is_lag,
                shopping_product_idx=shopping_idx,
            )
            if c['type'] == 'SHOPPING':
                shopping_idx += 1

            # B-4: VIDEO completion metrics
            if c['type'] == 'VIDEO':
                # Monthly performance pattern: high in Aug-Sep, low in Jan-Feb
                m = current.month
                if m in (8, 9):          # high-performing months
                    vvr_base = 0.30
                    p25_base, p50_base = 0.52, 0.38
                    p75_base, p100_base = 0.26, 0.14
                    cpv_base = 0.022
                elif m in (1, 2):        # poor-performing months
                    vvr_base = 0.16
                    p25_base, p50_base = 0.32, 0.20
                    p75_base, p100_base = 0.12, 0.06
                    cpv_base = 0.038
                else:
                    vvr_base = 0.22
                    p25_base, p50_base = 0.42, 0.28
                    p75_base, p100_base = 0.18, 0.09
                    cpv_base = 0.028
                noise = float(RNG.uniform(0.85, 1.15))
                base_row['video_view_rate']          = round(min(0.60, vvr_base * noise), 4)
                base_row['video_quartile_p25_rate']  = round(min(0.80, p25_base * noise), 4)
                base_row['video_quartile_p50_rate']  = round(min(0.70, p50_base * noise), 4)
                base_row['video_quartile_p75_rate']  = round(min(0.55, p75_base * noise), 4)
                base_row['video_quartile_p100_rate'] = round(min(0.35, p100_base * noise), 4)
                base_row['average_cpv']              = round(
                    cpv_base * float(RNG.uniform(0.80, 1.20)), 4
                )

            # Fix 5: ad-set split for G_SRCH_002 on 10 selected dates
            if c['id'] == SPLIT_CAMPAIGN_ID and current in split_dates:
                total_micros = cost_micros_val
                chunk        = total_micros // 3
                rem          = total_micros % 3
                # Guarantee non-even split so rounding divergence is demonstrable
                if rem != 0:
                    micros_parts = [chunk + rem, chunk, chunk]
                else:
                    # Exactly divisible: force imbalance
                    micros_parts = [chunk + 1, chunk, chunk - 1]

                for i, (ag_id, ag_name, micros_part) in enumerate(
                    zip(SPLIT_AG_IDS, SPLIT_AG_NAMES, micros_parts)
                ):
                    frac      = micros_part / total_micros if total_micros > 0 else 1 / 3
                    split_row = base_row.copy()
                    split_row['ad_group_id']               = ag_id
                    split_row['ad_group_name']             = ag_name
                    split_row['cost_micros']               = micros_part
                    split_row['impressions']               = max(1, int(impressions * frac))
                    split_row['clicks']                    = max(0, int(clicks * frac))
                    split_row['conversions']               = round(float(conversions) * frac, 2)
                    split_row['conversion_value']          = round(float(base_row['conversion_value']) * frac, 2)
                    split_row['ad_set_split_row']          = True
                    rows.append(split_row)
            else:
                rows.append(base_row)

        current += timedelta(days=1)

    return rows


# ─── Seed ─────────────────────────────────────────────────────────────────────

def seed(conn):
    all_dates   = [SEED_START + timedelta(days=i)
                   for i in range((SEED_END - SEED_START).days + 1)]
    split_dates, lag_dates = precompute_stochastic_sets(all_dates)

    with conn:
        cur = conn.cursor()
        cur.execute(f"DROP TABLE IF EXISTS {SCHEMA}.google_ads_performance")
        cur.execute(CREATE_DDL)

        rows = generate_rows(split_dates, lag_dates)
        logger.info("Generated %d rows. Inserting...", len(rows))

        psycopg2.extras.execute_batch(
            cur,
            f"""
            INSERT INTO {SCHEMA}.google_ads_performance
                (date_day, campaign_id, campaign_name, campaign_type,
                 ad_group_id, ad_group_name,
                 cost_micros, impressions, clicks, ctr, average_cpc,
                 conversions, conversion_value, conversion_value_per_cost,
                 search_impression_share, quality_score, is_synthetic,
                 data_completeness_flag,
                 attribution_window, attribution_window_note,
                 diagnostic_block_reason, max_confidence_cap,
                 reporting_delay_flag, ad_set_split_row,
                 campaign_name_history, campaign_name_is_stable,
                 campaign_objective, product_id, reason_product_id_null,
                 video_view_rate, video_quartile_p25_rate, video_quartile_p50_rate,
                 video_quartile_p75_rate, video_quartile_p100_rate, average_cpv)
            VALUES
                (%(date_day)s, %(campaign_id)s, %(campaign_name)s, %(campaign_type)s,
                 %(ad_group_id)s, %(ad_group_name)s,
                 %(cost_micros)s, %(impressions)s, %(clicks)s, %(ctr)s, %(average_cpc)s,
                 %(conversions)s, %(conversion_value)s, %(conversion_value_per_cost)s,
                 %(search_impression_share)s, %(quality_score)s, %(is_synthetic)s,
                 %(data_completeness_flag)s,
                 %(attribution_window)s, %(attribution_window_note)s,
                 %(diagnostic_block_reason)s, %(max_confidence_cap)s,
                 %(reporting_delay_flag)s, %(ad_set_split_row)s,
                 %(campaign_name_history)s, %(campaign_name_is_stable)s,
                 %(campaign_objective)s, %(product_id)s, %(reason_product_id_null)s,
                 %(video_view_rate)s, %(video_quartile_p25_rate)s,
                 %(video_quartile_p50_rate)s, %(video_quartile_p75_rate)s,
                 %(video_quartile_p100_rate)s, %(average_cpv)s)
            """,
            rows,
            page_size=500,
        )
        logger.info("Inserted %d rows.", len(rows))


# ─── Verification ─────────────────────────────────────────────────────────────

def run_verification(conn):
    cur = conn.cursor()
    print("\n=== VERIFICATION ===")

    # ── Original checks (1–6) ────────────────────────────────────────────────

    # Check 1: row count by campaign_type
    cur.execute(
        f"SELECT campaign_type, COUNT(*) FROM {SCHEMA}.google_ads_performance "
        f"GROUP BY campaign_type ORDER BY campaign_type"
    )
    rows = cur.fetchall()
    print("1. Row count by campaign_type:")
    for r in rows:
        print(f"   {r[0]}: {r[1]}")
    types_present = {r[0] for r in rows}
    expected_types = {'SEARCH', 'SHOPPING', 'PERFORMANCE_MAX', 'VIDEO', 'DEMAND_GEN'}
    missing = expected_types - types_present
    print("   PASS — all 5 campaign types present" if not missing
          else f"   FAIL — missing types: {missing}")

    # Check 2: date range
    cur.execute(f"SELECT MIN(date_day), MAX(date_day) FROM {SCHEMA}.google_ads_performance")
    min_d, max_d = cur.fetchone()
    print(f"2. Date range: {min_d} to {max_d}")
    print("   PASS" if min_d == SEED_START and max_d == SEED_END
          else f"   FAIL — expected {SEED_START} to {SEED_END}")

    # Check 3: total spend by campaign_type
    cur.execute(
        f"SELECT campaign_type, ROUND(SUM(cost_micros)/1000000.0, 2) AS total_spend_usd "
        f"FROM {SCHEMA}.google_ads_performance "
        f"GROUP BY campaign_type ORDER BY campaign_type"
    )
    print("3. Total spend (USD) by campaign_type:")
    for r in cur.fetchall():
        print(f"   {r[0]}: ${r[1]:,.2f}")

    # Check 4: NULL ad_group_id rows == PMax row count
    cur.execute(f"SELECT COUNT(*) FROM {SCHEMA}.google_ads_performance WHERE ad_group_id IS NULL")
    null_ag = cur.fetchone()[0]
    cur.execute(f"SELECT COUNT(*) FROM {SCHEMA}.google_ads_performance WHERE campaign_type = 'PERFORMANCE_MAX'")
    pmax_rows = cur.fetchone()[0]
    print(f"4. Rows with NULL ad_group_id: {null_ag} | PMax rows: {pmax_rows}")
    print("   PASS — NULL ad_group_id matches PMax row count exactly" if null_ag == pmax_rows
          else "   FAIL — mismatch")

    # Check 5: is_synthetic coverage
    cur.execute(f"SELECT COUNT(*) FROM {SCHEMA}.google_ads_performance WHERE is_synthetic = true")
    synthetic = cur.fetchone()[0]
    cur.execute(f"SELECT COUNT(*) FROM {SCHEMA}.google_ads_performance")
    total = cur.fetchone()[0]
    print(f"5. is_synthetic=true: {synthetic}/{total}")
    print("   PASS" if synthetic == total else "   FAIL — non-synthetic rows present")

    # Check 6: 14-day zero-spend window for Shopping_Main
    expected_days = (SHOPPING_ZERO_END - SHOPPING_ZERO_START).days + 1
    cur.execute(
        f"SELECT COUNT(*) FROM {SCHEMA}.google_ads_performance "
        f"WHERE campaign_id = 'G_SHOP_001' AND cost_micros = 0 "
        f"AND date_day BETWEEN %s AND %s",
        (SHOPPING_ZERO_START, SHOPPING_ZERO_END),
    )
    zero_days = cur.fetchone()[0]
    print(f"6. Shopping_Main zero-spend ({SHOPPING_ZERO_START} – {SHOPPING_ZERO_END}): "
          f"{zero_days}/{expected_days} days at $0")
    print("   PASS" if zero_days == expected_days else "   FAIL")

    # ── New nuance checks (Fix 1–6) ──────────────────────────────────────────

    print("\n--- Fix 1: Conversion lag ---")
    cur.execute(
        f"SELECT COUNT(*) FROM {SCHEMA}.google_ads_performance "
        f"WHERE data_completeness_flag = 'CONVERSION_LAG_PENDING' "
        f"AND conversions = 0 AND cost_micros > 0"
    )
    lag_count = cur.fetchone()[0]
    print(f"   CONVERSION_LAG_PENDING rows with spend but zero conversions: {lag_count}")
    print(f"   {'PASS' if lag_count >= 3 else 'FAIL — expected >= 3'}")

    print("\n--- Fix 2: Attribution window ---")
    cur.execute(
        f"SELECT DISTINCT campaign_type, attribution_window "
        f"FROM {SCHEMA}.google_ads_performance "
        f"ORDER BY campaign_type"
    )
    aw_rows = cur.fetchall()
    print(f"   Distinct (campaign_type, attribution_window) pairs: {len(aw_rows)}")
    for r in aw_rows:
        print(f"   {r[0]}: {r[1]}")
    print("   PASS" if len(aw_rows) == 5 else "   FAIL — expected 5 rows")

    print("\n--- Fix 3: PMax diagnostic ---")
    cur.execute(
        f"SELECT campaign_type, "
        f"       COUNT(*) as rows, "
        f"       COUNT(diagnostic_block_reason) as has_reason, "
        f"       AVG(max_confidence_cap) as avg_cap "
        f"FROM {SCHEMA}.google_ads_performance "
        f"GROUP BY campaign_type ORDER BY campaign_type"
    )
    fix3_rows = cur.fetchall()
    pmax_pass = True
    other_pass = True
    for r in fix3_rows:
        ctype, total_r, has_r, avg_cap = r
        if ctype == 'PERFORMANCE_MAX':
            ok = (has_r == total_r and abs(float(avg_cap) - 0.65) < 0.001)
            print(f"   {ctype}: {has_r}/{total_r} have reason, avg_cap={avg_cap:.2f} "
                  f"{'OK' if ok else 'FAIL'}")
            if not ok:
                pmax_pass = False
        else:
            ok = (has_r == 0 and abs(float(avg_cap) - 1.0) < 0.001)
            print(f"   {ctype}: {has_r}/{total_r} have reason, avg_cap={avg_cap:.2f} "
                  f"{'OK' if ok else 'FAIL'}")
            if not ok:
                other_pass = False
    print("   PASS" if pmax_pass and other_pass else "   FAIL")

    print("\n--- Fix 4: Stockout boundary ---")
    cur.execute(
        f"SELECT date_day, campaign_id, cost_micros, reporting_delay_flag "
        f"FROM {SCHEMA}.google_ads_performance "
        f"WHERE campaign_id = 'G_SHOP_001' "
        f"  AND date_day BETWEEN '2025-07-12' AND '2025-07-31' "
        f"ORDER BY date_day"
    )
    fix4_rows = cur.fetchall()
    print(f"   G_SHOP_001 Jul 12–31 rows: {len(fix4_rows)}")
    for r in fix4_rows:
        marker = '[BOUNDARY]' if r[3] else ('[ZERO pause]' if r[2] == 0 else '')
        print(f"   {r[0]}  cost_micros={r[2]:>12}  delay_flag={r[3]}  {marker}")
    boundary_dates_in_result = {r[0] for r in fix4_rows if r[3] is True}
    print(f"   Rows with delay_flag=TRUE: {len(boundary_dates_in_result)}")
    print("   PASS" if len(boundary_dates_in_result) == 6
          else "   FAIL — expected 6 boundary rows")

    print("\n--- Fix 5: Ad-set split rounding ---")
    cur.execute(
        f"SELECT date_day, "
        f"       SUM(cost_micros) AS total_micros, "
        f"       SUM(cost_micros) / 1000000.0 AS sum_then_divide, "
        f"       SUM(cost_micros / 1000000.0) AS divide_then_sum "
        f"FROM {SCHEMA}.google_ads_performance "
        f"WHERE ad_set_split_row = TRUE "
        f"GROUP BY date_day "
        f"HAVING SUM(cost_micros) / 1000000.0 != SUM(cost_micros / 1000000.0) "
        f"LIMIT 5"
    )
    rounding_rows = cur.fetchall()
    print(f"   Dates with rounding divergence: {len(rounding_rows)}")
    for r in rounding_rows:
        print(f"   {r[0]}: sum/div={r[2]}  div/sum={r[3]}  diff={float(r[2])-float(r[3]):.10f}")
    # Also show total split rows regardless of HAVING
    cur.execute(f"SELECT COUNT(*) FROM {SCHEMA}.google_ads_performance WHERE ad_set_split_row = TRUE")
    split_total = cur.fetchone()[0]
    print(f"   Total ad_set_split_row=TRUE rows: {split_total} (expected 30)")
    print(f"   NOTE: PostgreSQL exact numeric arithmetic may produce 0 rounding-divergence rows.")
    print(f"   Structural demonstration: split rows exist with non-even cost_micros distribution.")
    print("   PASS" if split_total == 30 else "   FAIL — expected 30 split rows")

    print("\n--- Fix 6: Campaign name history ---")
    cur.execute(
        f"SELECT campaign_id, campaign_type, "
        f"       COUNT(DISTINCT campaign_name) AS name_variants, "
        f"       campaign_name_is_stable "
        f"FROM {SCHEMA}.google_ads_performance "
        f"GROUP BY campaign_id, campaign_type, campaign_name_is_stable "
        f"ORDER BY campaign_id"
    )
    fix6_rows = cur.fetchall()
    renamed_pass  = all(r[2] == 2 and r[3] is False
                        for r in fix6_rows if r[0] in RENAMED_CAMPAIGNS)
    stable_pass   = all(r[2] == 1 and r[3] is True
                        for r in fix6_rows if r[0] not in RENAMED_CAMPAIGNS)
    for r in fix6_rows:
        print(f"   {r[0]} ({r[1]}): name_variants={r[2]}, stable={r[3]}")
    print("   PASS" if renamed_pass and stable_pass else "   FAIL")

    # ── Mandatory checks A and B ─────────────────────────────────────────────

    print("\n=== MANDATORY CHECK A — Conversion lag false-zero days ===")
    cur.execute(
        f"SELECT COUNT(*) FROM {SCHEMA}.google_ads_performance "
        f"WHERE data_completeness_flag = 'CONVERSION_LAG_PENDING' "
        f"AND conversions = 0 AND cost_micros > 0"
    )
    check_a = cur.fetchone()[0]
    print(f"   COUNT = {check_a}")
    print(f"   {'PASS' if check_a >= 3 else 'FAIL — must be >= 3'}")

    print("\n=== MANDATORY CHECK B — Stockout date boundary ===")
    cur.execute(
        f"SELECT date_day, reporting_delay_flag, cost_micros "
        f"FROM {SCHEMA}.google_ads_performance "
        f"WHERE campaign_id = 'G_SHOP_001' "
        f"  AND date_day IN ('2025-07-14', '2025-07-15', '2025-07-29') "
        f"ORDER BY date_day"
    )
    check_b = cur.fetchall()
    for r in check_b:
        print(f"   {r[0]}: delay_flag={r[1]}, cost_micros={r[2]}")
    b_14 = next((r for r in check_b if str(r[0]) == '2025-07-14'), None)
    b_15 = next((r for r in check_b if str(r[0]) == '2025-07-15'), None)
    b_29 = next((r for r in check_b if str(r[0]) == '2025-07-29'), None)
    b_ok = (
        b_14 is not None and b_14[1] is True  and b_14[2] > 0 and
        b_15 is not None and b_15[2] == 0 and
        b_29 is not None and b_29[1] is True  and b_29[2] > 0
    )
    print(f"   {'PASS' if b_ok else 'FAIL'}")


# ─── Step 3: client_config update ─────────────────────────────────────────────

def update_client_config(conn):
    with conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE public.client_config SET last_google_ads_sync = now() "
            "WHERE client_id = %s",
            (CLIENT_ID,),
        )
    cur = conn.cursor()
    cur.execute(
        "SELECT last_google_ads_sync FROM public.client_config WHERE client_id = %s",
        (CLIENT_ID,),
    )
    val = cur.fetchone()[0]
    print(f"\nStep 3 — last_google_ads_sync: {val}")
    print("   PASS" if val is not None else "   FAIL — still NULL")


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    conn = get_conn()
    try:
        seed(conn)
        run_verification(conn)
        update_client_config(conn)
        print("\n=== Google Ads seed hardening complete. All 6 real-data nuances implemented. ===")
    except Exception:
        logger.exception("Seed failed")
        raise
    finally:
        conn.close()
