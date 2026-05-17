"""
Profit Sentinel -- TikTok Seed Script
Brand: Azure & Co (client_azure_co)
Archetype A: Premium Contemporary Womenswear, $150 AOV
Y1: June 2024 -- May 2025 | Y2: June 2025 -- May 2026

Seeded tables (FIX 6 -- CREATE TABLE IF NOT EXISTS before all inserts):
  client_azure_co.tiktok_campaigns           -- 3 campaigns (deterministic UUIDs)
  client_azure_co.tiktok_ad_performance      -- 1 row per campaign per day (~2,190 rows)
  client_azure_co.tiktok_organic_performance -- 1 row per week (~104 rows)
  public.suppression_log                     -- S14 attribution reset (24 entries)

Also inserts into pre-existing tables:
  public.alert_log              -- B1_tiktok x5, D1_tiktok x1, H6 x1
  client_azure_co.brand_event_calendar -- tiktok_outage_y2 (1 entry)

Architecture rules (all six fixes from seed_shopify.py applied):
  FIX 1 -- No is_synthetic on raw tiktok table rows.
  FIX 2 -- airbyte_meta_cols() on every raw row (copied exactly from seed_shopify.py).
  FIX 3 -- Single transaction boundary wraps all table inserts; ON CONFLICT DO NOTHING.
  FIX 4 -- _nearest_pd_corr() before Cholesky on 4x4 TikTok signal matrix.
  FIX 5 -- GENERATED ALWAYS identity column excluded from suppression_log insert.
  FIX 6 -- CREATE TABLE IF NOT EXISTS before all inserts.

Scope note:
  TikTok disruption (Jan--Apr 2024): pre-seed window. Permanent effects baked
  into the $352/day baseline. brand_event_calendar disruption entries already
  seeded by seed_shopify.py -- not duplicated here.
  Y2 echo outage (Jan 19 2025, 14h): in-scope, seeded explicitly.
  TikTok Shop: excluded (D10).
"""

import json
import logging
import os
import random
import sys
import uuid
from datetime import date, datetime, timedelta, timezone

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

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CLIENT_ID  = 'azure_co'
SCHEMA     = 'client_azure_co'

SEED_START = date(2024, 6, 1)
SEED_END   = date(2026, 5, 31)

# Post-disruption permanent baseline (D8)
TIKTOK_DAILY_SPEND = 352.0   # 88% of pre-disruption $400/day
TIKTOK_CPM_BASE    = 10.0    # midpoint $8--12
TIKTOK_CTR_BASE    = 0.0100  # 1.0% baseline
TIKTOK_ROAS_BASE   = 2.10    # midpoint 1.8--2.4x
TIKTOK_FREQ_BASE   = 1.80    # baseline prospecting frequency
TIKTOK_DQ_BASE     = 88      # permanent ceiling post-disruption (D11)
ORGANIC_REACH_BASE = 0.96    # Jun 2024 stable level; never reaches 1.00 (D5)

# Episode boundaries
BFCM_Y1_START   = date(2024, 11,  1)
BFCM_Y1_END     = date(2024, 11, 30)
BFCM_Y2_START   = date(2025, 11,  1)
BFCM_Y2_END     = date(2025, 11, 30)
SATURATION_DATE = date(2025,  9,  1)   # Month 16 -- audience saturation (D1_tiktok)
OUTAGE_Y2       = date(2025,  1, 19)   # Y2 14h outage (D18)

# TikTok creative fatigue dates (B1_tiktok -- separate from Meta's B1 dates)
# 4 Y1 events + 1 Y2 event; founder improved rotation after Month 8 warning
TIKTOK_FATIGUE_DATES: list[date] = [
    date(2024,  9, 12),   # Y1 event 1 -- Month 4
    date(2024, 12, 18),   # Y1 event 2 -- Month 7 (post-BFCM recovery)
    date(2025,  2,  6),   # Y1 event 3 -- Month 9
    date(2025,  4, 17),   # Y1 event 4 -- Month 11
    date(2025,  9, 22),   # Y2 event 1 -- Month 16 (residual)
]
TIKTOK_FATIGUE_SET = set(TIKTOK_FATIGUE_DATES)

SEED_RNG = np.random.default_rng(77)   # separate seed from Shopify (42) and Meta (42/99)
PY_RNG   = random.Random(77)

# ---------------------------------------------------------------------------
# Episode multipliers
# (start, end, cpm_mult, roas_mult, spend_mult, freq_mult, ctr_mult)
# Multiplicative -- all apply together if date falls in multiple windows.
# ---------------------------------------------------------------------------
EPISODE_MULTS: list[tuple] = [
    # BFCM Y1 -- +57% spend, ROAS 3.5x/2.1x=1.67 of base
    (BFCM_Y1_START,      BFCM_Y1_END,        1.45, 3.5/2.1, 1.57, 1.40, 0.95),
    # BFCM Y2 -- +65% spend, larger brand + better creative
    (BFCM_Y2_START,      BFCM_Y2_END,        1.48, 3.9/2.1, 1.65, 1.50, 0.94),
    # Holiday tail Y1
    (date(2024, 12,  1), date(2024, 12, 31), 1.20, 1.04,    1.10, 1.20, 0.97),
    # Holiday tail Y2
    (date(2025, 12,  1), date(2025, 12, 31), 1.22, 1.05,    1.10, 1.20, 0.97),
    # Audience saturation Month 16 -- ROAS compressed 12--15% (less than Meta's 17%)
    (SATURATION_DATE,    SEED_END,            1.00, 0.875,   1.00, 1.15, 0.93),
    # Competitor activity Month 9 (Feb 2025) -- CPM spike, ROAS compressed
    (date(2025,  2,  1), date(2025,  2, 28), 1.20, 0.96,    1.00, 1.10, 0.98),
    # Competitor activity Month 21 (Feb 2026)
    (date(2026,  2,  1), date(2026,  2, 28), 1.18, 0.97,    1.00, 1.10, 0.98),
    # Marketing manager learning phase (Month 11 -- Apr 1 to May 12 2025)
    (date(2025,  4,  1), date(2025,  5, 12), 1.00, 0.87,    1.00, 1.00, 0.97),
]


def _get_episode_mults(d: date) -> tuple[float, float, float, float, float]:
    """Compound all episode multipliers active on date d."""
    cpm = roas = spend = freq = ctr = 1.0
    for s, e, c, r, sp, f, ct in EPISODE_MULTS:
        if s <= d <= e:
            cpm *= c; roas *= r; spend *= sp; freq *= f; ctr *= ct
    return cpm, roas, spend, freq, ctr


def _ctr_fatigue_factor(d: date) -> float:
    """Linear CTR decay in 7-day window before each TikTok fatigue event (max -15%)."""
    for fd in TIKTOK_FATIGUE_DATES:
        ws = fd - timedelta(days=7)
        if ws <= d <= fd:
            return 1.0 - 0.15 * (d - ws).days / 7.0
    return 1.0


# ---------------------------------------------------------------------------
# Campaign definitions (3 campaigns, stable deterministic IDs)
# ---------------------------------------------------------------------------

_TT_NS = uuid.UUID('b1b1b1b1-fade-beef-5678-000000000002')


def _camp_id(key: str) -> str:
    return str(uuid.uuid5(_TT_NS, f'tiktok:campaign:{key}'))


CAMPAIGNS: list[dict] = [
    {
        'id':          _camp_id('spark_exist'),
        'name':        'Azure TikTok -- Spark Ads Legacy',
        'type':        'spark_ad_existing',
        'status':      'ACTIVE',
        'created_at':  datetime(2024, 6, 1, 8, 0, 0, tzinfo=timezone.utc),
        'spend_share': 0.25,
    },
    {
        'id':          _camp_id('spark_new'),
        'name':        'Azure TikTok -- Spark Ads New Auth',
        'type':        'spark_ad_new',
        'status':      'ACTIVE',
        'created_at':  datetime(2024, 6, 1, 8, 0, 0, tzinfo=timezone.utc),
        'spend_share': 0.20,
    },
    {
        'id':          _camp_id('infeed'),
        'name':        'Azure TikTok -- In-Feed Paid',
        'type':        'in_feed_paid',
        'status':      'ACTIVE',
        'created_at':  datetime(2024, 6, 1, 8, 0, 0, tzinfo=timezone.utc),
        'spend_share': 0.55,
    },
]

# ---------------------------------------------------------------------------
# FIX 4 -- Nearest PD correlation matrix (copied exactly from seed_shopify.py)
# ---------------------------------------------------------------------------

_TT_CORR_DESIGN = np.array([
    # cpm    freq   reach  ctr
    [ 1.00,  0.45,  0.05, -0.30],   # cpm:  positively corr with freq (auction pressure)
    [ 0.45,  1.00,  0.00, -0.58],   # freq: CTR<->freq = -0.58 (creative fatigue dynamic)
    [ 0.05,  0.00,  1.00,  0.44],   # reach: organic momentum -> paid CTR = +0.44
    [-0.30, -0.58,  0.44,  1.00],   # ctr
], dtype=float)
_TT_LABELS = ['cpm_idx', 'freq_idx', 'reach_idx', 'ctr_idx']


def _nearest_pd_corr(m: np.ndarray, eps: float = 1e-4) -> np.ndarray:
    """Return the nearest positive-definite correlation matrix to m.

    Method: eigenvalue clipping (set any eigenvalue < eps to eps),
    reconstruct, re-symmetrise, then scale via congruence transformation
    (divide each entry by sqrt(diag[i]) * sqrt(diag[j])) to restore the
    unit diagonal.  Congruence scaling preserves positive definiteness;
    naively setting np.fill_diagonal(m, 1.0) does not.
    """
    vals, vecs = np.linalg.eigh(m)
    vals_clipped = np.maximum(vals, eps)
    pd = vecs @ np.diag(vals_clipped) @ vecs.T
    pd = (pd + pd.T) / 2
    d = np.sqrt(np.diag(pd))
    pd = pd / np.outer(d, d)
    return pd


TT_CORR = _nearest_pd_corr(_TT_CORR_DESIGN)

print('\n=== TT_CORR: original design ===')
print(f"{'':12s}" + ''.join(f'{l:>10s}' for l in _TT_LABELS))
for i, row in enumerate(_TT_CORR_DESIGN):
    print(f'{_TT_LABELS[i]:12s}' + ''.join(f'{v:10.4f}' for v in row))
print('\n=== TT_CORR: nearest PD (used for Cholesky) ===')
print(f"{'':12s}" + ''.join(f'{l:>10s}' for l in _TT_LABELS))
for i, row in enumerate(TT_CORR):
    print(f'{_TT_LABELS[i]:12s}' + ''.join(f'{v:10.4f}' for v in row))
print('\n=== Eigenvalues: original -> clipped ===')
for o, n in zip(np.linalg.eigh(_TT_CORR_DESIGN)[0], np.linalg.eigh(TT_CORR)[0]):
    flag = ' ** CLIPPED' if o < 1e-6 else ''
    print(f'  {o:10.6f}  ->  {n:10.6f}{flag}')
print()


def generate_daily_tt_signals(n_days: int) -> np.ndarray:
    """Generate correlated daily noise multipliers. Returns (n_days, 4) array.
    Columns: [cpm_noise, freq_noise, reach_noise, ctr_noise].
    """
    L = np.linalg.cholesky(TT_CORR)
    noise = SEED_RNG.standard_normal((n_days, 4))
    corr_noise = noise @ L.T
    signal = 1.0 + corr_noise * 0.08
    return np.clip(signal, 0.60, 1.60)


# ---------------------------------------------------------------------------
# FIX 2 -- Airbyte helpers (copied exactly from seed_shopify.py)
# ---------------------------------------------------------------------------

def airbyte_ts(d: date) -> datetime:
    """Simulate Airbyte extraction timestamp -- next-day batch, 3am UTC."""
    return datetime(d.year, d.month, d.day + 1 if d.day < 28 else d.day,
                    3, 0, 0, tzinfo=timezone.utc)


def airbyte_meta_cols(extracted_at: datetime) -> tuple:
    """Return the four required Airbyte metadata values for a raw table row.

    Column order: _airbyte_raw_id, _airbyte_extracted_at, _airbyte_meta, _airbyte_generation_id
    """
    return (str(uuid.uuid4()), extracted_at, '{}', 0)


def utc_dt(d: date, hour: int = 9, minute: int = 0) -> datetime:
    return datetime(d.year, d.month, d.day, hour, minute, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def get_conn() -> psycopg2.extensions.connection:
    url = os.getenv('DATABASE_URL')
    if not url:
        logger.error('SOURCE: TikTok Seed | ERROR: DATABASE_URL not set')
        sys.exit(1)
    return psycopg2.connect(url, sslmode='require')


def batch_insert(cur, schema: str, table: str, cols: list[str],
                 rows: list[tuple], batch: int = 500) -> int:
    if not rows:
        return 0
    sql = (f'INSERT INTO {schema}.{table} ({", ".join(cols)}) VALUES %s '
           f'ON CONFLICT DO NOTHING')
    total = 0
    for i in range(0, len(rows), batch):
        psycopg2.extras.execute_values(cur, sql, rows[i: i + batch])
        total += len(rows[i: i + batch])
    return total


def date_range(start: date, end: date):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def weeks_in_range(start: date, end: date):
    """Yield Monday of each week in range."""
    d = start + timedelta(days=(7 - start.weekday()) % 7)
    while d <= end:
        yield d
        d += timedelta(days=7)


def days_in_month(y: int, m: int) -> int:
    if m == 12:
        return (date(y + 1, 1, 1) - date(y, m, 1)).days
    return (date(y, m + 1, 1) - date(y, m, 1)).days


def iso_week_key(d: date) -> str:
    iso = d.isocalendar()
    return f'{iso[0]}-W{iso[1]:02d}'


# ---------------------------------------------------------------------------
# FIX 6 -- CREATE TABLE IF NOT EXISTS (all four tables)
# ---------------------------------------------------------------------------

DDL_TIKTOK_CAMPAIGNS = f"""
CREATE TABLE IF NOT EXISTS {SCHEMA}.tiktok_campaigns (
    campaign_id             text        PRIMARY KEY,
    campaign_name           text,
    campaign_type           text,
    status                  text,
    created_at              timestamptz,
    _airbyte_raw_id         text,
    _airbyte_extracted_at   timestamptz,
    _airbyte_meta           text,
    _airbyte_generation_id  bigint
);
"""

DDL_TIKTOK_AD_PERF = f"""
CREATE TABLE IF NOT EXISTS {SCHEMA}.tiktok_ad_performance (
    campaign_id             text,
    date                    date,
    spend                   numeric,
    spend_cash              numeric,
    spend_accrued           numeric,
    impressions             integer,
    clicks                  integer,
    purchases               integer,
    revenue                 numeric,
    cpm                     numeric,
    ctr                     numeric,
    roas                    numeric,
    frequency               numeric,
    campaign_type           text,
    dq_score                integer,
    _airbyte_raw_id         text,
    _airbyte_extracted_at   timestamptz,
    _airbyte_meta           text,
    _airbyte_generation_id  bigint,
    CONSTRAINT uq_tiktok_adperf_camp_date UNIQUE (campaign_id, date)
);
"""

DDL_TIKTOK_ORGANIC = f"""
CREATE TABLE IF NOT EXISTS {SCHEMA}.tiktok_organic_performance (
    week_start              date,
    posts_published         integer,
    total_views             integer,
    total_likes             integer,
    total_shares            integer,
    total_comments          integer,
    organic_reach_rate      numeric,
    avg_watch_time_seconds  numeric,
    profile_visits          integer,
    link_clicks             integer,
    _airbyte_raw_id         text,
    _airbyte_extracted_at   timestamptz,
    _airbyte_meta           text,
    _airbyte_generation_id  bigint,
    CONSTRAINT uq_tiktok_organic_week UNIQUE (week_start)
);
"""

# FIX 5 -- id column is GENERATED ALWAYS AS IDENTITY; not included in INSERT cols
DDL_SUPPRESSION_LOG = """
CREATE TABLE IF NOT EXISTS public.suppression_log (
    id                          bigint generated always as identity primary key,
    client_id                   text        not null,
    signal_detected_at          timestamptz,
    alert_type                  text,
    signal_value                numeric,
    threshold_value             numeric,
    suppression_reason          text,
    suppression_category        text,
    suppression_state           integer,
    variance_explained_pct      numeric,
    residual_signal             numeric,
    suppression_source          text,
    would_have_fired_at         timestamptz,
    founder_queryable           boolean     default true,
    detected_signal_description text,
    threshold_context           text,
    suppression_explanation     text,
    residual_signal_description text,
    founder_verification_action text,
    created_at                  timestamptz default now(),
    CONSTRAINT uq_suppression_log_signal UNIQUE (client_id, alert_type, would_have_fired_at)
);
"""


def create_tables(cur) -> None:
    for ddl in [DDL_TIKTOK_CAMPAIGNS, DDL_TIKTOK_AD_PERF,
                DDL_TIKTOK_ORGANIC, DDL_SUPPRESSION_LOG]:
        cur.execute(ddl)
    logger.info('create_tables | all four tables ensured')


# ---------------------------------------------------------------------------
# 1. Seed campaigns
# ---------------------------------------------------------------------------

def seed_tiktok_campaigns(cur) -> None:
    try:
        cols = ['campaign_id', 'campaign_name', 'campaign_type', 'status',
                'created_at',
                '_airbyte_raw_id', '_airbyte_extracted_at',
                '_airbyte_meta', '_airbyte_generation_id']
        rows = []
        for c in CAMPAIGNS:
            raw_id, ext_at, meta, gen = airbyte_meta_cols(
                airbyte_ts(c['created_at'].date()))
            rows.append((
                c['id'], c['name'], c['type'], c['status'], c['created_at'],
                raw_id, ext_at, meta, gen,
            ))
        n = batch_insert(cur, SCHEMA, 'tiktok_campaigns', cols, rows)
        logger.info('seed_tiktok_campaigns | rows: %d', n)
    except Exception as e:
        logger.error('SOURCE: TikTok Seed | CLIENT: %s | ERROR: %s | CONTEXT: campaigns',
                     CLIENT_ID, str(e))
        raise


# ---------------------------------------------------------------------------
# 2. Seed ad performance
# ---------------------------------------------------------------------------

def seed_tiktok_ad_performance(cur, manifest: dict) -> None:
    """One row per (campaign, date).

    Internal consistency enforced before insert:
      impressions = spend / cpm * 1000
      clicks      = impressions * ctr
      revenue     = spend * roas
      purchases back-distributed from manifest weekly TikTok attribution (~20%)
      spend_cash == spend_accrued (normal operation; both=0 on Jan 19 2025)

    ROAS derived from CPM via anti-correlation (-0.68):
      roas_noise = 1 - 0.68 * (cpm_noise - 1)
    This preserves the designed CPM<->ROAS anti-correlation without adding
    ROAS to the Cholesky matrix.
    """
    try:
        # Weekly TikTok-attributed orders (~20% of Shopify)
        TIKTOK_ATTR_RATE = 0.20
        weekly_orders: dict[str, int] = {
            wk: len(ids)
            for wk, ids in manifest.get('orders_by_week', {}).items()
        }
        # Y2 weeks (Jun 2025+) not in manifest -- scale from Y1 average (~20/wk * 1.30)
        Y2_ORDERS_PER_WEEK = 26

        all_days = list(date_range(SEED_START, SEED_END))
        n_days   = len(all_days)
        signals  = generate_daily_tt_signals(n_days)

        cols = [
            'campaign_id', 'date',
            'spend', 'spend_cash', 'spend_accrued',
            'impressions', 'clicks', 'purchases', 'revenue',
            'cpm', 'ctr', 'roas', 'frequency',
            'campaign_type', 'dq_score',
            '_airbyte_raw_id', '_airbyte_extracted_at',
            '_airbyte_meta', '_airbyte_generation_id',
        ]

        rows: list[tuple] = []

        for day_idx, d in enumerate(all_days):
            cpm_noise   = float(signals[day_idx, 0])
            freq_noise  = float(signals[day_idx, 1])
            reach_noise = float(signals[day_idx, 2])  # used for organic reach, affects CTR
            ctr_noise   = float(signals[day_idx, 3])

            ep_cpm, ep_roas, ep_spend, ep_freq, ep_ctr = _get_episode_mults(d)

            # Outage day: all spend = 0 (D18)
            is_outage = (d == OUTAGE_Y2)

            # Daily spend across all campaigns
            base_daily = TIKTOK_DAILY_SPEND * ep_spend
            day_dq = 55 if is_outage else TIKTOK_DQ_BASE

            # Day-level CPM and ROAS
            day_cpm = max(5.0, min(30.0,
                          TIKTOK_CPM_BASE * cpm_noise * ep_cpm))
            # ROAS anti-correlated with CPM: roas_noise = 1 - 0.68 * (cpm_noise - 1)
            roas_cpm_noise = 1.0 - 0.68 * (cpm_noise - 1.0)
            day_roas = max(1.0, min(5.5,
                           TIKTOK_ROAS_BASE * roas_cpm_noise * ep_roas))

            # Day-level CTR (with organic momentum from reach_noise + fatigue decay)
            organic_boost = 1.0 + 0.44 * (reach_noise - 1.0)  # reach<->CTR = +0.44
            day_ctr = max(0.003, min(0.025,
                          TIKTOK_CTR_BASE * ctr_noise * organic_boost
                          * ep_ctr * _ctr_fatigue_factor(d)))

            # Frequency (fatigue signature on fatigue dates)
            day_freq = max(1.0, min(4.0,
                           TIKTOK_FREQ_BASE * freq_noise * ep_freq))
            if d in TIKTOK_FATIGUE_SET:
                day_freq = round(max(2.55, day_freq * 1.5), 2)

            # Weekly purchases
            wk = iso_week_key(d)
            if wk in weekly_orders:
                week_orders_total = weekly_orders[wk]
            else:
                week_orders_total = Y2_ORDERS_PER_WEEK
            tiktok_orders_today = week_orders_total * TIKTOK_ATTR_RATE / 7.0

            extracted_at = airbyte_ts(d)
            date_str = d

            for camp in CAMPAIGNS:
                share = camp['spend_share']

                if is_outage:
                    adv_spend = 0.0
                    imp = 0; clk = 0; rev = 0.0; purch = 0
                    s_cpm = 0.0; s_ctr = 0.0; s_roas = 0.0; s_freq = 0.0
                else:
                    adv_spend = round(base_daily * share, 2)
                    if adv_spend < 0.01:
                        continue

                    # ROAS varies by campaign type
                    camp_roas_adj = {
                        'spark_ad_existing': 1.12,
                        'spark_ad_new':      1.05,
                        'in_feed_paid':      0.93,
                    }.get(camp['type'], 1.0)
                    adv_roas = max(1.0, min(5.5, day_roas * camp_roas_adj))

                    # Derive consistent metrics
                    imp   = max(1, round(adv_spend / day_cpm * 1000))
                    clk   = max(0, round(imp * day_ctr))
                    rev   = round(adv_spend * adv_roas, 2)
                    purch = max(0, round(tiktok_orders_today * share))

                    # Stored CPM and CTR derived from actuals for exact consistency
                    s_cpm  = round(adv_spend / imp * 1000, 2) if imp > 0 else 0.0
                    s_ctr  = round(clk / imp, 5) if imp > 0 else 0.0
                    s_roas = round(adv_roas, 4)
                    s_freq = round(day_freq, 4)

                # spend_cash == spend_accrued in normal operation (D19 wallet scope is
                # pre-seed; post-Jun-2024 wallet is normally pre-funded)
                raw_id, ext_at, meta, gen = airbyte_meta_cols(extracted_at)
                rows.append((
                    camp['id'], date_str,
                    adv_spend, adv_spend, adv_spend,   # spend, spend_cash, spend_accrued
                    imp if not is_outage else 0,
                    clk if not is_outage else 0,
                    purch if not is_outage else 0,
                    rev if not is_outage else 0.0,
                    s_cpm, s_ctr, s_roas, s_freq,
                    camp['type'], day_dq,
                    raw_id, ext_at, meta, gen,
                ))

        n = batch_insert(cur, SCHEMA, 'tiktok_ad_performance', cols, rows)
        logger.info('seed_tiktok_ad_performance | rows: %d', n)
    except Exception as e:
        logger.error('SOURCE: TikTok Seed | CLIENT: %s | ERROR: %s | CONTEXT: ad_performance',
                     CLIENT_ID, str(e))
        raise


# ---------------------------------------------------------------------------
# 3. Seed organic performance (weekly cadence)
# ---------------------------------------------------------------------------

def seed_tiktok_organic_performance(cur) -> None:
    """One row per week. organic_reach_rate indexed at 0.96 (D5 arc settled).
    Never exceeds 0.98 (permanent ceiling -- organic reach never fully recovers).
    """
    try:
        cols = [
            'week_start', 'posts_published',
            'total_views', 'total_likes', 'total_shares', 'total_comments',
            'organic_reach_rate', 'avg_watch_time_seconds',
            'profile_visits', 'link_clicks',
            '_airbyte_raw_id', '_airbyte_extracted_at',
            '_airbyte_meta', '_airbyte_generation_id',
        ]

        rows: list[tuple] = []
        all_weeks = list(weeks_in_range(SEED_START, SEED_END))
        n_weeks   = len(all_weeks)

        # Generate reach noise for organic (using the reach_idx dimension of daily signals
        # -- we resample weekly by taking Monday's daily signal for that week)
        all_days = list(date_range(SEED_START, SEED_END))
        day_index = {d: i for i, d in enumerate(all_days)}
        week_signals = generate_daily_tt_signals(n_weeks + 5)   # fresh draw for organic

        for w_idx, ws in enumerate(all_weeks):
            reach_noise = float(week_signals[w_idx, 2])  # reach dimension
            ctr_noise   = float(week_signals[w_idx, 3])

            # Posts per week
            in_bfcm_y1 = (BFCM_Y1_START <= ws <= BFCM_Y1_END + timedelta(days=6))
            in_bfcm_y2 = (BFCM_Y2_START <= ws <= BFCM_Y2_END + timedelta(days=6))
            if in_bfcm_y2:
                posts = 6
            elif in_bfcm_y1:
                posts = 5
            else:
                posts = 3

            # Organic reach rate: 0.96 stable, small variance, never exceeds 0.98
            reach_rate = round(min(0.98, max(0.94,
                               ORGANIC_REACH_BASE * reach_noise)), 4)

            # Views: ~18,000 per post at baseline reach (indexed to 0.96)
            views_per_post = 18_000 * reach_rate / ORGANIC_REACH_BASE
            # Boost during BFCM and holiday from content quality / viral momentum
            if in_bfcm_y1:
                views_per_post *= 1.6
            elif in_bfcm_y2:
                views_per_post *= 1.9
            elif (date(2024, 12, 1) <= ws <= date(2024, 12, 31) or
                  date(2025, 12, 1) <= ws <= date(2025, 12, 31)):
                views_per_post *= 1.3
            views_per_post *= max(0.7, min(1.4, ctr_noise))   # weekly content quality

            total_views = max(1, round(views_per_post * posts))
            total_likes    = max(0, round(total_views * 0.048))   # ~4.8% like rate
            total_shares   = max(0, round(total_views * 0.009))   # ~0.9% share rate
            total_comments = max(0, round(total_views * 0.005))   # ~0.5% comment rate
            profile_visits = max(0, round(total_views * 0.032))   # ~3.2% of viewers
            link_clicks    = max(0, round(profile_visits * 0.18)) # ~18% of profile visitors

            # avg watch time: 8--14 seconds for fashion TikTok, better during BFCM
            watch_base = 11.0
            if in_bfcm_y1 or in_bfcm_y2:
                watch_base = 13.5
            avg_watch = round(max(6.0, min(22.0,
                              watch_base * max(0.8, min(1.3, reach_noise)))), 1)

            raw_id, ext_at, meta, gen = airbyte_meta_cols(airbyte_ts(ws))
            rows.append((
                ws, posts,
                total_views, total_likes, total_shares, total_comments,
                reach_rate, avg_watch, profile_visits, link_clicks,
                raw_id, ext_at, meta, gen,
            ))

        n = batch_insert(cur, SCHEMA, 'tiktok_organic_performance', cols, rows)
        logger.info('seed_tiktok_organic_performance | rows: %d', n)
    except Exception as e:
        logger.error('SOURCE: TikTok Seed | CLIENT: %s | ERROR: %s | CONTEXT: organic',
                     CLIENT_ID, str(e))
        raise


# ---------------------------------------------------------------------------
# 4. Seed brand_event_calendar -- TikTok Y2 outage only (D18)
#    Disruption events (D7) already seeded by seed_shopify.py
# ---------------------------------------------------------------------------

def seed_tiktok_brand_event_calendar(cur) -> None:
    try:
        bec_cols = [
            'client_id', 'event_name', 'event_type', 'start_date', 'end_date',
            'suppress_alerts', 'context_alerts', 'context_explanation',
            'residual_threshold_pct', 'confidence_decay_type',
            'confidence_decay_start', 'confidence_decay_end', 'confidence_at_peak',
            'detection_method', 'detection_lag_hours', 'confidence', 'last_verified_at',
            'is_recurring', 'recurrence_rule', 'auto_detected', 'detected_from',
            'event_profile', 'suppression_type', 'is_synthetic',
        ]
        rows = [
            (
                CLIENT_ID,
                'TikTok Y2 Outage Jan 2025',
                'platform_disruption',
                OUTAGE_Y2,         # start_date
                OUTAGE_Y2,         # end_date (14h -- single day event)
                ['A3'],            # suppress_alerts: A3 suppressed (H6 fires to explain it)
                ['H6'],            # context_alerts: H6 fires with Y1 precedent reference
                ('TikTok 14h outage Jan 19 2025. Faster recovery than Y1 -- '
                 'creators maintained backup authorisations. '
                 'Spend restored to 80% within 48 hours. No Spark Ad freeze.'),
                None,              # residual_threshold_pct
                'step',            # confidence_decay_type
                OUTAGE_Y2,
                OUTAGE_Y2 + timedelta(days=2),  # recovery by Jan 21
                1.0,
                'auto_detected',
                0,
                1.0,
                None,
                False, None, True, None,
                json.dumps({
                    'y1_precedent_date':    '2024-01-13',
                    'outage_duration_hours': 14,
                    'recovery_pct_48h':      80,
                    'spark_ad_freeze':       False,
                }),
                'reactive',
                True,
            ),
        ]
        n = batch_insert(cur, SCHEMA, 'brand_event_calendar', bec_cols, rows)
        logger.info('seed_tiktok_brand_event_calendar | rows: %d', n)
    except Exception as e:
        logger.error('SOURCE: TikTok Seed | CLIENT: %s | ERROR: %s | CONTEXT: bec',
                     CLIENT_ID, str(e))
        raise


# ---------------------------------------------------------------------------
# 5. Seed alert_log entries
# ---------------------------------------------------------------------------

def seed_tiktok_alerts(cur) -> None:
    try:
        alert_cols = [
            'client_id', 'alert_type', 'fired_at',
            'should_fire', 'confidence_score',
            'signal_value', 'threshold_value', 'threshold_direction',
            'layer1_headline', 'layer2_context', 'layer3_precedent',
            'alert_instance_number', 'escalation_level',
            'suppressed', 'suppression_category',
            'fatigue_period_active', 'fatigue_reason',
            'outcome_confirmed', 'dismissal_correct',
            'is_synthetic',
        ]

        def alert(atype, fired_at, should_fire, confidence,
                  signal_value=None, threshold_value=None, threshold_direction='above',
                  layer1=None, layer2=None, layer3=None,
                  instance=1, escalation=0,
                  suppressed=False, sup_cat=None,
                  fatigue_period=False, fatigue_reason=None,
                  outcome=None, dismissal=None):
            return (
                CLIENT_ID, atype, fired_at,
                should_fire, confidence,
                signal_value, threshold_value, threshold_direction,
                layer1 or f'{atype} alert', layer2, layer3,
                instance, escalation,
                suppressed, sup_cat,
                fatigue_period, fatigue_reason,
                outcome, dismissal,
                True,
            )

        rows: list[tuple] = []

        # ── B1_tiktok: Creative fatigue (4 Y1, 1 Y2) ───────────────────────────
        # fatigue_period_active = True for Y1 (founder has NOT fixed rotation)
        #                       = False for Y2 (founder fixed rotation post Month 8)
        for idx, fd in enumerate(TIKTOK_FATIGUE_DATES, start=1):
            year_label  = 'Y1' if fd < date(2025, 6, 1) else 'Y2'
            conf        = round(PY_RNG.uniform(0.70, 0.87), 2)
            freq_v      = round(PY_RNG.uniform(2.55, 2.95), 2)
            ctr_dec_pct = round(PY_RNG.uniform(15, 26), 0)
            is_y1       = (year_label == 'Y1')
            rows.append(alert(
                'B1_tiktok', utc_dt(fd, 9), should_fire=True, confidence=conf,
                signal_value=freq_v, threshold_value=2.5, threshold_direction='above',
                layer1=(
                    f'TikTok creative fatigue -- in-feed frequency {freq_v:.2f} '
                    f'(threshold 2.5) and CTR declined {ctr_dec_pct:.0f}% over 7 days.'
                ),
                layer2=(
                    f'Fatigue event {idx} ({year_label}). Rotate TikTok creative '
                    f'to reset frequency. Spark Ads use separate creator authorisations '
                    f'-- less affected; focus rotation on in-feed paid campaigns.'
                ),
                layer3=(
                    'No prior TikTok fatigue baseline.' if idx == 1
                    else (
                        'Prior TikTok fatigue events resolved within 5--7 days of '
                        'creative rotation (same pattern as Meta B1).'
                        if is_y1
                        else
                        'Y1: 4 fatigue events resolved by weekly rotation protocol '
                        'implemented Month 8. Y2 event is residual -- rotation '
                        'cadence now prevents sustained fatigue.'
                    )
                ),
                fatigue_period=is_y1,   # True=Y1 (unresolved era), False=Y2 (fixed)
                fatigue_reason='tiktok_creative_rotation_not_systematised' if is_y1 else None,
            ))

        # ── D1_tiktok: Audience saturation (Month 16 -- Sep 2025) ──────────────
        rows.append(alert(
            'D1_tiktok', utc_dt(date(2025, 9, 15), 9), should_fire=True, confidence=0.81,
            signal_value=TIKTOK_DAILY_SPEND,
            threshold_value=TIKTOK_DAILY_SPEND * 0.88,
            threshold_direction='above',
            layer1=(
                'TikTok audience saturation (Month 16). ROAS compressed 13% over '
                '6 weeks despite stable CPM. Spend at scale ceiling for current '
                'audience size -- structural, not creative.'
            ),
            layer2=(
                'In-feed frequency sustained 2.6--2.9 for 4 weeks. CPM stable '
                '($10.20 avg). TikTok audience pool is smaller than Meta -- '
                'saturation threshold reached faster at 13% of total budget. '
                'Concurrent Meta D1 event (same month) confirms cross-platform '
                'audience exhaustion.'
            ),
            layer3=(
                'First TikTok saturation event. No Y1 precedent at this spend level. '
                'Meta audience saturation (same month, Month 16) provides cross-platform '
                'benchmark: expect ROAS compression 12--20% until audience expansion.'
            ),
        ))

        # ── H6: Platform spend gap -- Y2 outage Jan 19 2025 (D18) ──────────────
        # Most powerful Layer 3 demonstration: references Y1 precedent explicitly
        rows.append(alert(
            'H6', utc_dt(OUTAGE_Y2, 9), should_fire=True, confidence=0.98,
            signal_value=0.0,        # spend = $0
            threshold_value=TIKTOK_DAILY_SPEND * 0.50,  # >50% drop triggers H6
            threshold_direction='below',
            layer1=(
                f'TikTok spend $0 on Jan 19 2025 vs ${TIKTOK_DAILY_SPEND:.0f} '
                f'daily average. Platform outage confirmed (14 hours). '
                f'No action required -- spend expected to restore by Jan 21.'
            ),
            layer2=(
                'TikTok experienced a 14-hour service outage Jan 19 2025. '
                'Creators with backup authorisations maintained ready status -- '
                'no Spark Ad freeze required (unlike Jan 2024). '
                'A3 (channel ROAS comparison) suppressed for 48 hours as spend '
                'is $0 -- no meaningful ROAS comparison possible.'
            ),
            layer3=(
                'PRECEDENT: Jan 13 2024 (14 months ago). TikTok went dark during '
                'Senate Judiciary hearing. Recovery was full within 72 hours at that time. '
                'Current outage is shorter (14h vs 7-day threat window in Jan 2024) '
                'and brand has backup creator authorisations now. '
                'Based on Jan 13 2024 precedent, recovery expected within 48 hours. '
                'No action required if spend restored by Jan 21. '
                '[layer_3_precedent_date: 2024-01-13]'
            ),
        ))

        # Skip rows that already exist (alert_log has no unique constraint beyond PK)
        existing_keys: set[tuple] = set()
        cur.execute(
            "SELECT client_id, alert_type, fired_at FROM public.alert_log "
            "WHERE client_id = %s AND alert_type = ANY(%s)",
            (CLIENT_ID, ['B1_tiktok', 'D1_tiktok', 'H6']),
        )
        for row in cur.fetchall():
            existing_keys.add((row[0], row[1], row[2]))

        # fired_at is col index 2 in alert_cols (client_id=0, alert_type=1, fired_at=2)
        new_rows = [r for r in rows
                    if (r[0], r[1], r[2]) not in existing_keys]
        n = 0
        for i in range(0, len(new_rows), 200):
            sql = f'INSERT INTO public.alert_log ({", ".join(alert_cols)}) VALUES %s'
            psycopg2.extras.execute_values(cur, sql, new_rows[i: i + 200])
            n += len(new_rows[i: i + 200])
        logger.info('seed_tiktok_alerts | alert_log rows: %d (skipped %d existing)',
                    n, len(rows) - n)

    except Exception as e:
        logger.error('SOURCE: TikTok Seed | CLIENT: %s | ERROR: %s | CONTEXT: alerts',
                     CLIENT_ID, str(e))
        raise


# ---------------------------------------------------------------------------
# 6. Seed suppression_log -- S14: TikTok attribution monthly reset
#    Days 1--5 of each month, Alert A3 does not fire.
#    24 entries (1 per month). FIX 5: id column excluded (GENERATED ALWAYS).
# ---------------------------------------------------------------------------

def seed_suppression_log_s14(cur) -> None:
    try:
        # FIX 5 -- no 'id' column; GENERATED ALWAYS handles it
        cols = [
            'client_id', 'signal_detected_at', 'alert_type',
            'signal_value', 'threshold_value',
            'suppression_reason', 'suppression_category', 'suppression_state',
            'variance_explained_pct', 'residual_signal',
            'suppression_source', 'would_have_fired_at', 'founder_queryable',
            'detected_signal_description', 'threshold_context',
            'suppression_explanation', 'residual_signal_description',
            'founder_verification_action',
        ]

        rows: list[tuple] = []
        y, m = SEED_START.year, SEED_START.month
        while date(y, m, 1) <= SEED_END:
            month_start = date(y, m, 1)
            detected_at = utc_dt(month_start, 9)

            rows.append((
                CLIENT_ID,
                detected_at,                             # signal_detected_at
                'A3',                                    # alert_type
                None,                                    # signal_value (not applicable)
                None,                                    # threshold_value
                'TikTok attribution resets on day 1 of each month. '
                'Days 1--5 ROAS figures are incomplete and not comparable '
                'to prior period.',
                'S14',                                   # suppression_category
                3,                                       # suppression_state (full suppress)
                100.0,                                   # variance_explained_pct
                None,                                    # residual_signal
                'S14_tiktok_attribution_monthly_reset',  # suppression_source
                detected_at,                             # would_have_fired_at
                True,                                    # founder_queryable
                # 5 mandatory explanation fields
                (f'TikTok channel ROAS (A3) flagged as potentially anomalous '
                 f'on {month_start.strftime("%Y-%m-%d")} (day 1 of month).'),
                ('A3 fires when TikTok ROAS deviates significantly from Meta ROAS '
                 'for 3+ consecutive days.'),
                ('TikTok attribution resets each calendar month. Days 1--5 data '
                 'is incomplete as platform recalculates attribution window. '
                 'A3 suppressed for days 1--5 of each month (S14).'),
                None,                                    # residual_signal_description (State 3)
                ('Check TikTok Ads Manager directly on '
                 f'{month_start.strftime("%Y-%m-%d")} to verify spend '
                 f'is running normally. Attribution figures will stabilise by day 6.'),
            ))

            m += 1
            if m > 12:
                m = 1; y += 1

        n = batch_insert(cur, 'public', 'suppression_log', cols, rows)
        logger.info('seed_suppression_log_s14 | rows: %d', n)
    except Exception as e:
        logger.error('SOURCE: TikTok Seed | CLIENT: %s | ERROR: %s | CONTEXT: suppression_log',
                     CLIENT_ID, str(e))
        raise


# ---------------------------------------------------------------------------
# 7. Validation (run outside transaction)
# ---------------------------------------------------------------------------

def validate_tiktok_seed(conn) -> None:
    print('\n' + '=' * 72)
    print('TIKTOK SEED VALIDATION -- 8 CHECKS')
    print('=' * 72)

    def run(label, sql, params=None):
        try:
            c = conn.cursor()
            c.execute(sql, params or ())
            return c.fetchall()
        except Exception as e:
            print(f'[ERR ] {label}: {e}')
            return None

    results = {}

    # CHECK 1 -- Row count
    r = run('CHECK 1', f'SELECT COUNT(*) FROM {SCHEMA}.tiktok_ad_performance')
    cnt = r[0][0] if r else 0
    ok  = 2000 <= cnt <= 2500
    results[1] = 'PASS' if ok else 'FAIL'
    print(f'\n[{results[1]}] CHECK 1 -- tiktok_ad_performance row count')
    print(f'       actual={cnt:,}  expected=2,000-2,500')

    # CHECK 2 -- Jan 19 2025 outage row
    r = run('CHECK 2',
            f"""SELECT spend, spend_cash, spend_accrued, dq_score
                FROM {SCHEMA}.tiktok_ad_performance
                WHERE date = '2025-01-19'""")
    if r:
        spends = [float(row[0]) for row in r]
        dqs    = [int(row[3]) for row in r]
        all_zero   = all(s == 0.0 for s in spends)
        dq_low     = all(d < 88 for d in dqs)
        ok = all_zero and dq_low and len(r) == 3
        results[2] = 'PASS' if ok else 'FAIL'
        print(f'\n[{results[2]}] CHECK 2 -- Jan 19 2025 outage (spend=0, dq<88, 3 rows)')
        for row in r:
            print(f'       spend={row[0]}  spend_cash={row[1]}  '
                  f'spend_accrued={row[2]}  dq_score={row[3]}')
    else:
        results[2] = 'FAIL'
        print(f'\n[FAIL] CHECK 2 -- no rows found for 2025-01-19')

    # CHECK 3 -- Monthly spend Nov 2024 (BFCM Y1: +57% -> ~$16,000-17,000)
    r = run('CHECK 3',
            f"""SELECT SUM(spend)
                FROM {SCHEMA}.tiktok_ad_performance
                WHERE date >= '2024-11-01' AND date < '2024-12-01'""")
    nov24 = float(r[0][0] or 0) if r else 0
    ok = 14_000 <= nov24 <= 18_000
    results[3] = 'PASS' if ok else 'FAIL'
    print(f'\n[{results[3]}] CHECK 3 -- Monthly spend Nov 2024 (BFCM Y1)')
    print(f'       actual=${nov24:,.2f}  expected=$14,000-$18,000 (~$16,500)')
    bfcm_y1_daily = nov24 / 30
    print(f'       implied daily avg = ${bfcm_y1_daily:.2f}  '
          f'(baseline ${TIKTOK_DAILY_SPEND:.0f}/day)')

    # CHECK 4 -- Monthly spend Nov 2025 (BFCM Y2: +65% -> ~$17,000-18,500)
    r = run('CHECK 4',
            f"""SELECT SUM(spend)
                FROM {SCHEMA}.tiktok_ad_performance
                WHERE date >= '2025-11-01' AND date < '2025-12-01'""")
    nov25 = float(r[0][0] or 0) if r else 0
    ok = 15_000 <= nov25 <= 20_000
    results[4] = 'PASS' if ok else 'FAIL'
    print(f'\n[{results[4]}] CHECK 4 -- Monthly spend Nov 2025 (BFCM Y2)')
    print(f'       actual=${nov25:,.2f}  expected=$15,000-$20,000 (~$17,400)')

    # CHECK 5 -- B1_tiktok alert count (expect 5: 4 Y1 + 1 Y2)
    r = run('CHECK 5',
            "SELECT COUNT(*) FROM public.alert_log WHERE alert_type = 'B1_tiktok'")
    b1t = r[0][0] if r else 0
    ok = b1t == 5
    results[5] = 'PASS' if ok else 'FAIL'
    print(f'\n[{results[5]}] CHECK 5 -- B1_tiktok creative fatigue count')
    print(f'       actual={b1t}  expected=5 (4 Y1, 1 Y2)')

    detail = run('CHECK 5 detail',
                 """SELECT alert_type, fired_at::date, confidence_score,
                           fatigue_period_active
                    FROM public.alert_log
                    WHERE alert_type = 'B1_tiktok'
                    ORDER BY fired_at""")
    if detail:
        print(f'       {"type":<12} {"fired_at":<14} {"conf":<8} fatigue_period_active')
        for row in detail:
            yr = 'Y1' if row[1] < date(2025, 6, 1) else 'Y2'
            print(f'       {str(row[0]):<12} {str(row[1]):<14} '
                  f'{str(row[2]):<8} {str(row[3])}  [{yr}]')

    # CHECK 6 -- organic_reach_rate range post-Jul 2024
    r = run('CHECK 6',
            f"""SELECT MIN(organic_reach_rate), MAX(organic_reach_rate)
                FROM {SCHEMA}.tiktok_organic_performance
                WHERE week_start >= '2024-07-01'""")
    if r and r[0][0] is not None:
        rmin, rmax = float(r[0][0]), float(r[0][1])
        ok = (0.90 <= rmin) and (rmax <= 0.98) and (rmax < 1.00)
        results[6] = 'PASS' if ok else 'FAIL'
        print(f'\n[{results[6]}] CHECK 6 -- organic_reach_rate range (post-Jul 2024)')
        print(f'       min={rmin:.4f}  max={rmax:.4f}  '
              f'expected=0.94-0.98, never 1.00')
        if rmax >= 1.00:
            print('       FAIL: reach_rate reached or exceeded 1.00')
    else:
        results[6] = 'FAIL'
        print(f'\n[FAIL] CHECK 6 -- no organic rows found')

    # CHECK 7 -- S14 suppression_log entries (24)
    r = run('CHECK 7',
            """SELECT COUNT(*) FROM public.suppression_log
               WHERE suppression_category = 'S14' AND client_id = %s""",
            (CLIENT_ID,))
    s14 = r[0][0] if r else 0
    ok  = s14 == 24
    results[7] = 'PASS' if ok else 'FAIL'
    print(f'\n[{results[7]}] CHECK 7 -- S14 suppression_log entries')
    print(f'       actual={s14}  expected=24 (1 per month x 24 months)')

    # CHECK 8 -- spend_cash vs spend_accrued consistency
    r = run('CHECK 8',
            f"""SELECT COUNT(*)
                FROM {SCHEMA}.tiktok_ad_performance
                WHERE ABS(spend_cash - spend_accrued) > 50
                  AND date != '2025-01-19'""")
    anomalous = r[0][0] if r else 0
    ok = (anomalous == 0)
    results[8] = 'PASS' if ok else 'FAIL'
    print(f'\n[{results[8]}] CHECK 8 -- spend_cash vs spend_accrued consistency')
    print(f'       rows with |cash-accrued|>$50 (excl Jan 19): {anomalous}  expected=0')

    # Summary
    print('\n' + '=' * 72)
    print('SUMMARY')
    print('=' * 72)
    for k, v in results.items():
        print(f'  CHECK {k}: {v}')
    passed = sum(1 for v in results.values() if v == 'PASS')
    print(f'  {passed}/{len(results)} checks passed')
    print('=' * 72 + '\n')


# ---------------------------------------------------------------------------
# Manifest loader
# ---------------------------------------------------------------------------

def load_manifest() -> dict:
    p = os.path.join(os.path.dirname(__file__), 'seed_manifest_shopify.json')
    if not os.path.exists(p):
        logger.warning('SOURCE: TikTok Seed | CLIENT: %s | Manifest not found -- '
                       'purchases will use Y2 estimate only', CLIENT_ID)
        return {}
    try:
        with open(p, encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error('SOURCE: TikTok Seed | CLIENT: %s | ERROR: %s | CONTEXT: load_manifest',
                     CLIENT_ID, str(e))
        return {}


# ---------------------------------------------------------------------------
# Main -- FIX 3: single transaction wraps all table inserts
# ---------------------------------------------------------------------------

def main() -> None:
    logger.info('SOURCE: TikTok Seed | CLIENT: %s | Starting', CLIENT_ID)
    conn = get_conn()
    try:
        manifest = load_manifest()
        with conn:     # FIX 3 -- single transaction
            cur = conn.cursor()

            logger.info('Step 0/6 -- create_tables (FIX 6)')
            create_tables(cur)

            logger.info('Step 1/6 -- seed_tiktok_campaigns')
            seed_tiktok_campaigns(cur)

            logger.info('Step 2/6 -- seed_tiktok_ad_performance')
            seed_tiktok_ad_performance(cur, manifest)

            logger.info('Step 3/6 -- seed_tiktok_organic_performance')
            seed_tiktok_organic_performance(cur)

            logger.info('Step 4/6 -- seed_tiktok_brand_event_calendar')
            seed_tiktok_brand_event_calendar(cur)

            logger.info('Step 5/6 -- seed_tiktok_alerts')
            seed_tiktok_alerts(cur)

            logger.info('Step 6/6 -- seed_suppression_log_s14')
            seed_suppression_log_s14(cur)

        validate_tiktok_seed(conn)
        logger.info('SOURCE: TikTok Seed | CLIENT: %s | Complete', CLIENT_ID)
    except Exception as e:
        logger.error('SOURCE: TikTok Seed | CLIENT: %s | ERROR: %s | CONTEXT: main',
                     CLIENT_ID, str(e))
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    main()
