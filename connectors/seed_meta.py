"""
Profit Sentinel — Meta Ads Seed Script
Brand: Azure & Co (client_azure_co)
Archetype A: Premium Contemporary Womenswear, $150 AOV
Y1: June 2024 – May 2025 | Y2: June 2025 – May 2026

Seeded tables:
  client_azure_co.meta_campaigns       — 18 stable campaigns (deterministic UUIDs)
  client_azure_co.meta_ad_sets         — 36 ad sets (base + BFCM × 2 + conquest)
  client_azure_co.meta_ad_performance  — 1 row per ad_set per day (~7,000–8,000 rows)
  client_azure_co.meta_billing_statement — INSERT ONLY, 24 rows (table pre-exists)

Alert log rows seeded:
  B1 (creative fatigue) × 8   (6 Y1, 2 Y2 — from gap_abc_decisions.md B3)
  D1 (audience saturation) × 1 (Sep 2025 / Month 16)
  A1 (ROAS drop) — fires when ROAS drops >20% for >3 consecutive days
      suppressed during BFCM and Jan 12–26 2026 (attribution window)
  Competitor diagnostic × 2   (Feb 2025 Month 9, Feb 2026 Month 21)

brand_event_calendar entries:
  meta_attribution_window_change (Jan 12 2026, suppresses A1/A3 for 14 days)
  meta_learning_phase_mgmt_change (Apr 1 – May 12 2025, suppresses A1)

Six fixes from seed_shopify.py applied:
  FIX 1 — No is_synthetic on raw table inserts
  FIX 2 — airbyte_meta_cols() on every raw table row (exact copy from seed_shopify.py)
  FIX 3 — Single transaction boundary, ON CONFLICT DO NOTHING (bare form)
  FIX 4 — Nearest PD projection before Cholesky (3×3 Meta signal matrix)
  FIX 5 — identity_generation check before inserting into meta_billing_statement
  FIX 6 — CREATE TABLE IF NOT EXISTS before inserts
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

# ─── Constants ─────────────────────────────────────────────────────────────────

CLIENT_ID  = 'azure_co'
SCHEMA     = 'client_azure_co'
BRAND_NAME = 'Azure & Co'

SEED_START = date(2024, 6, 1)
SEED_END   = date(2026, 5, 31)

# Key event dates
ATTRIBUTION_CHANGE_DATE = date(2026, 1, 12)   # Meta window break: 28d→7d click
ATTRIBUTION_SUPPRESS_END = date(2026, 1, 26)  # 14-day suppression window
MGMT_CHANGE_DATE        = date(2025, 4, 1)    # Marketing manager hired (Month 11)
MGMT_DIP_END            = date(2025, 5, 12)   # 6 weeks after Apr 1
SATURATION_DATE         = date(2025, 9, 1)    # Month 16 — audience saturation starts
BFCM_Y1_START           = date(2024, 11, 1)
BFCM_Y1_END             = date(2024, 11, 30)
BFCM_Y2_START           = date(2025, 11, 1)
BFCM_Y2_END             = date(2025, 11, 30)
COMPETITOR_1_START      = date(2025, 2, 1)    # Month 9 (Feb 2025)
COMPETITOR_1_END        = date(2025, 2, 28)
COMPETITOR_2_START      = date(2026, 2, 1)    # Month 21 (Feb 2026)
COMPETITOR_2_END        = date(2026, 2, 28)

SEED_RNG = np.random.default_rng(42)   # match seed_shopify.py for reproducibility
PY_RNG   = random.Random(99)

# ─── Monthly Meta spend targets (B2 — non-linear scaling) ─────────────────────

MONTHLY_META_SPEND: dict[tuple[int, int], float] = {
    (2024, 6):  35_000.0,
    (2024, 7):  35_000.0,
    (2024, 8):  35_000.0,
    (2024, 9):  35_000.0,
    (2024, 10): 35_000.0,
    (2024, 11): 52_000.0,   # BFCM Y1
    (2024, 12): 35_000.0,
    (2025, 1):  36_500.0,
    (2025, 2):  38_000.0,   # competitor activity — CPM up, not spend
    (2025, 3):  39_500.0,
    (2025, 4):  41_000.0,   # marketing manager hired
    (2025, 5):  42_000.0,
    (2025, 6):  43_500.0,
    (2025, 7):  45_000.0,
    (2025, 8):  46_500.0,
    (2025, 9):  48_000.0,   # Month 16 saturation threshold crossed
    (2025, 10): 48_000.0,
    (2025, 11): 62_000.0,   # BFCM Y2
    (2025, 12): 48_000.0,
    (2026, 1):  48_000.0,
    (2026, 2):  48_000.0,   # competitor activity Month 21
    (2026, 3):  48_000.0,
    (2026, 4):  48_000.0,
    (2026, 5):  48_000.0,
}

# Baseline CPM ranges (Mon–Wed +18%, Thu–Sun -12% — A10)
CPM_BASE_LOW, CPM_BASE_HIGH = 16.0, 19.0
CTR_BASE_LOW, CTR_BASE_HIGH = 0.011, 0.014
ROAS_BASE_LOW, ROAS_BASE_HIGH = 2.8, 3.4
FREQ_PROSP_LOW, FREQ_PROSP_HIGH = 1.4, 1.8
FREQ_RETARG_LOW, FREQ_RETARG_HIGH = 2.1, 2.6

DOW_CPM_MULT = {0: 1.18, 1: 1.18, 2: 1.18, 3: 0.88, 4: 0.88, 5: 0.88, 6: 0.88}

# ─── Pre-defined creative fatigue dates (B3) ───────────────────────────────────
# 6 Y1 events + 2 Y2 events — each is the alert_fire_date (day frequency crossed 2.8
# AND CTR had declined >15% over prior 7 days).
CREATIVE_FATIGUE_DATES: list[date] = [
    date(2024, 8,  15),   # Y1 #1 — Month 3
    date(2024, 10,  1),   # Y1 #2 — Month 5
    date(2024, 12, 10),   # Y1 #3 — Month 7
    date(2025,  1, 22),   # Y1 #4 — Month 8
    date(2025,  3,  8),   # Y1 #5 — Month 10
    date(2025,  5, 15),   # Y1 #6 — Month 12
    date(2025,  8, 10),   # Y2 #1 — Month 15 (founder rotated after Month 8, less frequent)
    date(2025, 10, 20),   # Y2 #2 — Month 17
]
FATIGUE_DATE_SET = set(CREATIVE_FATIGUE_DATES)

# ─── Nearest PD helper (FIX 4 — exact copy from seed_shopify.py) ───────────────

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
    pd = (pd + pd.T) / 2                    # numerical symmetry
    d = np.sqrt(np.diag(pd))
    pd = pd / np.outer(d, d)                # congruence scale → unit diagonal, PD preserved
    return pd


# ─── Meta signal correlation matrix ────────────────────────────────────────────
# 3 variables: [cpm_idx, freq_idx, ctr_idx]
# Design correlations from spec:
#   spend  ↔ frequency:  +0.68  (higher spend → faster saturation)
#   CTR    ↔ frequency:  -0.61  (creative fatigue — rising frequency kills CTR)
#   CPM    ↔ ROAS:       -0.72  (handled via 4-day lag in performance loop)
#   CPM    ↔ frequency:  +0.35  (high-CPM auction pressure → audience overlap)
#   CPM    ↔ CTR:        -0.25  (high CPM → ad seen more → lower novelty CTR)

_META_CORR_DESIGN = np.array([
    #  cpm    freq    ctr
    [ 1.00,   0.35,  -0.25],
    [ 0.35,   1.00,  -0.61],
    [-0.25,  -0.61,   1.00],
], dtype=float)

_META_LABELS = ['cpm_idx', 'freq_idx', 'ctr_idx']

META_CORR = _nearest_pd_corr(_META_CORR_DESIGN)

print('\n=== META_CORR: original design ===')
print(f"{'':12s}" + ''.join(f'{l:>10s}' for l in _META_LABELS))
for i, row in enumerate(_META_CORR_DESIGN):
    print(f'{_META_LABELS[i]:12s}' + ''.join(f'{v:10.4f}' for v in row))
print('\n=== META_CORR: nearest PD (used for Cholesky) ===')
print(f"{'':12s}" + ''.join(f'{l:>10s}' for l in _META_LABELS))
for i, row in enumerate(META_CORR):
    print(f'{_META_LABELS[i]:12s}' + ''.join(f'{v:10.4f}' for v in row))
print('\n=== Eigenvalues: original → clipped ===')
_orig_vals = np.linalg.eigh(_META_CORR_DESIGN)[0]
_new_vals  = np.linalg.eigh(META_CORR)[0]
for o, n in zip(_orig_vals, _new_vals):
    flag = ' ** CLIPPED' if o < 1e-6 else ''
    print(f'  {o:10.6f}  →  {n:10.6f}{flag}')
print()


def generate_daily_meta_signals(n_days: int) -> np.ndarray:
    """Generate correlated daily noise multipliers for n_days + 5 (lag buffer).

    Returns array (n_days + 5, 3): cols [cpm_noise, freq_noise, ctr_noise].
    Centred at 1.0 with ±16% noise at 2σ.
    """
    L = np.linalg.cholesky(META_CORR)
    noise = SEED_RNG.standard_normal((n_days + 5, 3))
    corr_noise = noise @ L.T
    signal = 1.0 + corr_noise * 0.08   # std=0.08 → ±16% at 2σ
    signal = np.clip(signal, 0.65, 1.60)
    return signal


# ─── Airbyte helpers (FIX 2 — exact copy from seed_shopify.py) ─────────────────

def airbyte_ts(d: date) -> datetime:
    """Simulate Airbyte extraction timestamp — next-day batch, 3am UTC."""
    return datetime(d.year, d.month, d.day + 1 if d.day < 28 else d.day,
                    3, 0, 0, tzinfo=timezone.utc)


def airbyte_meta_cols(extracted_at: datetime) -> tuple:
    """Return the four required Airbyte metadata values for a raw table row.

    Column order: _airbyte_raw_id, _airbyte_extracted_at, _airbyte_meta, _airbyte_generation_id
    """
    return (str(uuid.uuid4()), extracted_at, '{}', 0)


def utc_dt(d: date, hour: int = 14, minute: int = 0) -> datetime:
    return datetime(d.year, d.month, d.day, hour, minute, 0, tzinfo=timezone.utc)


# ─── DB helpers ─────────────────────────────────────────────────────────────────

def get_conn() -> psycopg2.extensions.connection:
    url = os.getenv('DATABASE_URL')
    if not url:
        logger.error('SOURCE: Meta Seed | ERROR: DATABASE_URL not set')
        sys.exit(1)
    return psycopg2.connect(url, sslmode='require')


def batch_insert(cur, table: str, cols: list[str], rows: list[tuple],
                 batch: int = 500) -> int:
    if not rows:
        return 0
    sql = (f'INSERT INTO {SCHEMA}.{table} ({", ".join(cols)}) VALUES %s '
           f'ON CONFLICT DO NOTHING')
    total = 0
    for i in range(0, len(rows), batch):
        chunk = rows[i: i + batch]
        psycopg2.extras.execute_values(cur, sql, chunk)
        total += len(chunk)
    return total


def batch_insert_public(cur, table: str, cols: list[str], rows: list[tuple],
                        batch: int = 500) -> int:
    if not rows:
        return 0
    sql = (f'INSERT INTO public.{table} ({", ".join(cols)}) VALUES %s '
           f'ON CONFLICT DO NOTHING')
    total = 0
    for i in range(0, len(rows), batch):
        chunk = rows[i: i + batch]
        psycopg2.extras.execute_values(cur, sql, chunk)
        total += len(chunk)
    return total


# ─── Date helpers ───────────────────────────────────────────────────────────────

def date_range(start: date, end: date):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def days_in_month(year: int, month: int) -> int:
    if month == 12:
        return (date(year + 1, 1, 1) - date(year, month, 1)).days
    return (date(year, month + 1, 1) - date(year, month, 1)).days


def month_num(d: date) -> int:
    """Month number relative to seed start. Month 1 = Jun 2024."""
    return (d.year - 2024) * 12 + d.month - 5


# ─── Campaign definitions ────────────────────────────────────────────────────────

_META_NS = uuid.UUID('a0a0a0a0-beef-cafe-1234-000000000001')


def _camp_id(key: str) -> str:
    return str(uuid.uuid5(_META_NS, f'campaign:{key}'))


def _adset_id(key: str) -> str:
    return str(uuid.uuid5(_META_NS, f'adset:{key}'))


CAMPAIGNS: list[dict] = [
    {'campaign_id': _camp_id('prosp_general'),       'campaign_name': 'Azure — Prospecting General',           'objective': 'CONVERSIONS', 'status': 'ACTIVE',   'created_at': utc_dt(date(2024, 6,  1), 8)},
    {'campaign_id': _camp_id('prosp_lookalike'),     'campaign_name': 'Azure — Prospecting Lookalike',         'objective': 'CONVERSIONS', 'status': 'ACTIVE',   'created_at': utc_dt(date(2024, 6,  1), 8)},
    {'campaign_id': _camp_id('prosp_interest'),      'campaign_name': 'Azure — Prospecting Interest Based',    'objective': 'CONVERSIONS', 'status': 'ACTIVE',   'created_at': utc_dt(date(2024, 6,  1), 8)},
    {'campaign_id': _camp_id('prosp_broad_scale'),   'campaign_name': 'Azure — Prospecting Broad Scale',       'objective': 'CONVERSIONS', 'status': 'ACTIVE',   'created_at': utc_dt(date(2025, 1,  1), 8)},
    {'campaign_id': _camp_id('retarg_site'),         'campaign_name': 'Azure — Retargeting Site Visitors',     'objective': 'RETARGETING', 'status': 'ACTIVE',   'created_at': utc_dt(date(2024, 6,  1), 8)},
    {'campaign_id': _camp_id('retarg_cart'),         'campaign_name': 'Azure — Retargeting Abandoned Cart',    'objective': 'RETARGETING', 'status': 'ACTIVE',   'created_at': utc_dt(date(2024, 6,  1), 8)},
    {'campaign_id': _camp_id('retarg_purchasers'),   'campaign_name': 'Azure — Retargeting Purchasers',        'objective': 'RETARGETING', 'status': 'ACTIVE',   'created_at': utc_dt(date(2024, 6,  1), 8)},
    {'campaign_id': _camp_id('klaviyo_sync_retarg'), 'campaign_name': 'Azure — Klaviyo Audience Retargeting',  'objective': 'RETARGETING', 'status': 'ACTIVE',   'created_at': utc_dt(date(2024, 9,  1), 8)},
    {'campaign_id': _camp_id('reach_awareness'),     'campaign_name': 'Azure — Reach Brand Awareness',         'objective': 'REACH',       'status': 'ACTIVE',   'created_at': utc_dt(date(2024, 6,  1), 8)},
    {'campaign_id': _camp_id('bfcm_y1'),             'campaign_name': 'Azure — BFCM 2024',                     'objective': 'CONVERSIONS', 'status': 'ARCHIVED', 'created_at': utc_dt(date(2024, 11, 1), 8)},
    {'campaign_id': _camp_id('bfcm_y2'),             'campaign_name': 'Azure — BFCM 2025',                     'objective': 'CONVERSIONS', 'status': 'ARCHIVED', 'created_at': utc_dt(date(2025, 11, 1), 8)},
    {'campaign_id': _camp_id('holiday_y1'),          'campaign_name': 'Azure — Holiday Gifting 2024',          'objective': 'CONVERSIONS', 'status': 'ARCHIVED', 'created_at': utc_dt(date(2024, 12, 1), 8)},
    {'campaign_id': _camp_id('holiday_y2'),          'campaign_name': 'Azure — Holiday Gifting 2025',          'objective': 'CONVERSIONS', 'status': 'ARCHIVED', 'created_at': utc_dt(date(2025, 12, 1), 8)},
    {'campaign_id': _camp_id('fw_launch_y1'),        'campaign_name': 'Azure — FW24 Collection Launch',        'objective': 'CONVERSIONS', 'status': 'ARCHIVED', 'created_at': utc_dt(date(2024, 10, 1), 8)},
    {'campaign_id': _camp_id('fw_launch_y2'),        'campaign_name': 'Azure — FW25 Collection Launch',        'objective': 'CONVERSIONS', 'status': 'ARCHIVED', 'created_at': utc_dt(date(2025, 9,  1), 8)},
    {'campaign_id': _camp_id('ss_launch_y1'),        'campaign_name': 'Azure — SS25 Collection Launch',        'objective': 'CONVERSIONS', 'status': 'ARCHIVED', 'created_at': utc_dt(date(2025, 3,  1), 8)},
    {'campaign_id': _camp_id('ss_launch_y2'),        'campaign_name': 'Azure — SS26 Collection Launch',        'objective': 'CONVERSIONS', 'status': 'ACTIVE',   'created_at': utc_dt(date(2026, 3,  1), 8)},
    {'campaign_id': _camp_id('conquest_comp'),       'campaign_name': 'Azure — Competitor Conquest',           'objective': 'CONVERSIONS', 'status': 'ACTIVE',   'created_at': utc_dt(date(2025, 2,  1), 8)},
]

# ─── Ad set definitions ─────────────────────────────────────────────────────────
# Each dict carries _active_from/_active_to for performance loop filtering.

AD_SETS: list[dict] = []


def _adset(key: str, camp_key: str, name: str, targeting: str, budget: float,
           active_from: date, active_to: date, status: str = 'ACTIVE') -> dict:
    row = {
        'ad_set_id':      _adset_id(key),
        'campaign_id':    _camp_id(camp_key),
        'ad_set_name':    name,
        'daily_budget':   budget,
        'targeting_type': targeting,
        'status':         status,
        'created_at':     utc_dt(active_from, 9),
        '_active_from':   active_from,
        '_active_to':     active_to,
    }
    AD_SETS.append(row)
    return row


# Phase 1 base ad sets (Jun 2024 – Mar 2025, old naming convention)
_adset('p1_w2544_broad',   'prosp_general',     'Prospecting Women 25-44 Broad',       'prospecting', 800.0, date(2024, 6, 1), date(2025, 3, 31))
_adset('p1_w2534_fash',    'prosp_interest',    'Prospecting Women 25-34 Fashion',      'prospecting', 600.0, date(2024, 6, 1), date(2025, 3, 31))
_adset('p1_w3554_prem',    'prosp_general',     'Prospecting Women 35-54 Premium',      'prospecting', 500.0, date(2024, 6, 1), date(2025, 3, 31))
_adset('p1_lal_1pct',      'prosp_lookalike',   'Lookalike 1pct Purchasers',            'lookalike',   700.0, date(2024, 6, 1), date(2025, 3, 31))
_adset('p1_lal_25pct',     'prosp_lookalike',   'Lookalike 2-5pct Purchasers',          'lookalike',   500.0, date(2024, 6, 1), date(2025, 3, 31))
_adset('p1_retg_site',     'retarg_site',       'Retargeting Site Visitors 30d',        'retargeting', 400.0, date(2024, 6, 1), date(2025, 3, 31))
_adset('p1_retg_cart',     'retarg_cart',       'Retargeting Abandoned Cart 7d',        'retargeting', 350.0, date(2024, 6, 1), date(2025, 3, 31))
_adset('p1_kla_sync',      'klaviyo_sync_retarg','Klaviyo Audience Retargeting',        'retargeting', 300.0, date(2024, 9, 1), date(2025, 3, 31))

# Phase 2 base ad sets (Apr 2025 – May 2026, manager naming convention)
_adset('p2_prosp_broad',   'prosp_broad_scale', 'P_W2544_BRD_SCALE_Apr25',             'prospecting', 900.0, date(2025, 4, 1), date(2026, 5, 31))
_adset('p2_prosp_fash',    'prosp_interest',    'P_W2534_FASH_INT_Apr25',               'prospecting', 700.0, date(2025, 4, 1), date(2026, 5, 31))
_adset('p2_prosp_prem',    'prosp_general',     'P_W3554_PREM_SEG_Apr25',               'prospecting', 600.0, date(2025, 4, 1), date(2026, 5, 31))
_adset('p2_lal_1pct',      'prosp_lookalike',   'L_LAL1PCT_PURCH_Apr25',                'lookalike',   800.0, date(2025, 4, 1), date(2026, 5, 31))
_adset('p2_lal_25pct',     'prosp_lookalike',   'L_LAL25PCT_ENG_Apr25',                 'lookalike',   600.0, date(2025, 4, 1), date(2026, 5, 31))
_adset('p2_retg_site',     'retarg_site',       'R_RETG_SITE30D_Apr25',                 'retargeting', 450.0, date(2025, 4, 1), date(2026, 5, 31))
_adset('p2_retg_cart',     'retarg_cart',       'R_RETG_CART7D_Apr25',                  'retargeting', 400.0, date(2025, 4, 1), date(2026, 5, 31))
_adset('p2_kla_sync',      'klaviyo_sync_retarg','R_KLA_SYNC_AUD_Apr25',                'retargeting', 350.0, date(2025, 4, 1), date(2026, 5, 31))
_adset('p2_retg_video',    'retarg_purchasers', 'R_RETG_VID25PCT_Apr25',                'retargeting', 250.0, date(2025, 4, 1), date(2026, 5, 31))
_adset('p2_reach_aware',   'reach_awareness',   'P_REACH_BRAND_WW_Apr25',               'prospecting', 200.0, date(2025, 4, 1), date(2026, 5, 31))

# BFCM Y1 ad sets (Nov 2024, 12 sets → 8 base + 12 = 20 total during BFCM)
for _i, (_n, _t, _b) in enumerate([
    ('BFCM24 Prospecting Holiday Gift',    'prospecting', 500.0),
    ('BFCM24 Prospecting Last Min Buyers', 'prospecting', 450.0),
    ('BFCM24 Lookalike High Spenders',     'lookalike',   400.0),
    ('BFCM24 Lookalike Gift Purchasers',   'lookalike',   350.0),
    ('BFCM24 Retargeting Site 7d Urgent',  'retargeting', 500.0),
    ('BFCM24 Retargeting Cart VIP Offer',  'retargeting', 450.0),
    ('BFCM24 Retargeting Wishlist 14d',    'retargeting', 350.0),
    ('BFCM24 Retargeting Video Viewers',   'retargeting', 300.0),
    ('BFCM24 Prosp Competitive Audience',  'prospecting', 300.0),
    ('BFCM24 Prosp Broad Top Funnel',      'prospecting', 250.0),
    ('BFCM24 Reach Early Access',          'prospecting', 200.0),
    ('BFCM24 Retarg Purchasers 90d',       'retargeting', 250.0),
], start=1):
    _adset(f'bfcm24_{_i:02d}', 'bfcm_y1', _n, _t, _b,
           date(2024, 11, 1), date(2024, 11, 30), status='ARCHIVED')

# BFCM Y2 ad sets (Nov 2025, 12 sets)
for _i, (_n, _t, _b) in enumerate([
    ('BFCM25 Prospecting Holiday Gift',    'prospecting', 600.0),
    ('BFCM25 Prospecting Last Min Buyers', 'prospecting', 550.0),
    ('BFCM25 Lookalike High Spenders',     'lookalike',   500.0),
    ('BFCM25 Lookalike Gift Purchasers',   'lookalike',   400.0),
    ('BFCM25 Retargeting Site 7d Urgent',  'retargeting', 600.0),
    ('BFCM25 Retargeting Cart VIP Offer',  'retargeting', 550.0),
    ('BFCM25 Retargeting Wishlist 14d',    'retargeting', 400.0),
    ('BFCM25 Retargeting Video Viewers',   'retargeting', 350.0),
    ('BFCM25 Prosp Competitive Audience',  'prospecting', 350.0),
    ('BFCM25 Prosp Broad Top Funnel',      'prospecting', 300.0),
    ('BFCM25 Reach Early Access',          'prospecting', 250.0),
    ('BFCM25 Retarg Purchasers 90d',       'retargeting', 300.0),
], start=1):
    _adset(f'bfcm25_{_i:02d}', 'bfcm_y2', _n, _t, _b,
           date(2025, 11, 1), date(2025, 11, 30), status='ARCHIVED')

# Competitor conquest (Feb 2025, Feb 2026)
_adset('conq_feb25', 'conquest_comp', 'Conquest Competitor Audience Feb25', 'prospecting', 300.0,
       date(2025, 2, 1), date(2025, 2, 28))
_adset('conq_feb26', 'conquest_comp', 'Conquest Competitor Audience Feb26', 'prospecting', 350.0,
       date(2026, 2, 1), date(2026, 2, 28))


# ─── Episode multipliers ────────────────────────────────────────────────────────
# (start, end, cpm_mult, roas_mult, freq_mult_prosp, ctr_mult, label)
EPISODE_MULTS: list[tuple[date, date, float, float, float, float, str]] = [
    # BFCM Y1 — CPM +72% avg, ROAS inflated last-touch, frequency rises
    (date(2024, 11, 1),  date(2024, 11, 30),  1.72, 3.9/3.1,  1.7, 0.95, 'bfcm_y1'),
    # Holiday Y1
    (date(2024, 12, 1),  date(2024, 12, 31),  1.30, 1.05,     1.3, 0.98, 'holiday_y1'),
    # Summer sale Y1 — lower CPM, higher conversion
    (date(2024, 7, 4),   date(2024, 7, 21),   0.88, 1.12,     1.1, 1.05, 'summer_sale_y1'),
    # FW launch Y1 — CPM spike, high intent
    (date(2024, 10, 8),  date(2024, 10, 22),  1.25, 1.08,     1.2, 1.02, 'fw_launch_y1'),
    # SS launch Y1
    (date(2025, 3, 12),  date(2025, 3, 26),   1.15, 1.06,     1.1, 1.04, 'ss_launch_y1'),
    # BFCM Y2 — CPM +77% avg
    (date(2025, 11, 1),  date(2025, 11, 30),  1.77, 4.2/3.1,  1.8, 0.94, 'bfcm_y2'),
    # Holiday Y2
    (date(2025, 12, 1),  date(2025, 12, 31),  1.32, 1.06,     1.3, 0.98, 'holiday_y2'),
    # FW launch Y2
    (date(2025, 9, 15),  date(2025, 9, 30),   1.20, 1.07,     1.2, 1.03, 'fw_launch_y2'),
    # SS launch Y2
    (date(2026, 3, 12),  date(2026, 3, 26),   1.18, 1.05,     1.1, 1.04, 'ss_launch_y2'),
    # Competitor activity Month 9 (Feb 2025) — CPM +30%, CTR/conv hold
    (date(2025, 2, 1),   date(2025, 2, 28),   1.30, 0.94,     1.1, 0.98, 'competitor_y1'),
    # Competitor activity Month 21 (Feb 2026) — CPM +28%
    (date(2026, 2, 1),   date(2026, 2, 28),   1.28, 0.95,     1.1, 0.98, 'competitor_y2'),
    # Marketing manager learning dip (Apr 1 – May 12 2025) — ROAS -15%
    (date(2025, 4, 1),   date(2025, 5, 12),   1.00, 0.85,     1.0, 0.97, 'mgmt_learning'),
    # Audience saturation (Sep 2025+) — ROAS compresses 17%
    (date(2025, 9, 1),   date(2026, 5, 31),   1.00, 0.83,     1.25, 0.93, 'saturation'),
    # Post-attribution-window change (Jan 12 2026) — ROAS drops 20% mechanically
    (date(2026, 1, 12),  date(2026, 5, 31),   1.00, 0.80,     1.0, 1.00, 'attribution_window'),
]


def _get_episode_multipliers(d: date) -> tuple[float, float, float, float]:
    """Return (cpm_mult, roas_mult, freq_mult_prosp, ctr_mult) for date d.
    Multiple episodes combine multiplicatively.
    """
    cpm = roas = freq = ctr = 1.0
    for start, end, c, r, f, ct, _ in EPISODE_MULTS:
        if start <= d <= end:
            cpm  *= c
            roas *= r
            freq *= f
            ctr  *= ct
    return cpm, roas, freq, ctr


def _creative_fatigue_window(d: date) -> bool:
    """True if d falls in the 7-day run-up to a creative fatigue event."""
    for fd in CREATIVE_FATIGUE_DATES:
        if fd - timedelta(days=7) <= d <= fd:
            return True
    return False


def _creative_fatigue_severity(d: date) -> float:
    """Return CTR suppression factor during fatigue run-up (0 = no effect, 1 = max)."""
    for fd in CREATIVE_FATIGUE_DATES:
        window_start = fd - timedelta(days=7)
        if window_start <= d <= fd:
            days_in = (d - window_start).days
            return 1.0 - (0.15 * days_in / 7.0)  # linear CTR decline up to -15%
    return 1.0


# ─── Load Shopify manifest for purchase alignment ───────────────────────────────

def load_manifest() -> dict:
    manifest_path = os.path.join(os.path.dirname(__file__), 'seed_manifest_shopify.json')
    if not os.path.exists(manifest_path):
        logger.warning('SOURCE: Meta Seed | CLIENT: %s | Manifest not found — purchases estimated', CLIENT_ID)
        return {}
    try:
        with open(manifest_path, encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error('SOURCE: Meta Seed | CLIENT: %s | ERROR: %s | CONTEXT: load_manifest', CLIENT_ID, str(e))
        return {}


def _build_weekly_order_counts(manifest: dict) -> dict[str, int]:
    """Return {iso_week_str: order_count} from manifest orders_by_week."""
    result = {}
    for week_key, order_ids in manifest.get('orders_by_week', {}).items():
        result[week_key] = len(order_ids)
    return result


def _iso_week_key(d: date) -> str:
    iso = d.isocalendar()
    return f'{iso[0]}-W{iso[1]:02d}'


# ─── FIX 6 — CREATE TABLE IF NOT EXISTS ────────────────────────────────────────

def ensure_tables(cur) -> None:
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {SCHEMA}.meta_campaigns (
            campaign_id               text PRIMARY KEY,
            campaign_name             text NOT NULL,
            objective                 text,
            status                    text,
            created_at                timestamp with time zone,
            _airbyte_raw_id           text NOT NULL,
            _airbyte_extracted_at     timestamp with time zone NOT NULL,
            _airbyte_meta             jsonb NOT NULL DEFAULT '{{}}',
            _airbyte_generation_id    integer NOT NULL DEFAULT 0
        )
    """)
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {SCHEMA}.meta_ad_sets (
            ad_set_id                 text PRIMARY KEY,
            campaign_id               text,
            ad_set_name               text,
            daily_budget              numeric,
            targeting_type            text,
            status                    text,
            created_at                timestamp with time zone,
            _airbyte_raw_id           text NOT NULL,
            _airbyte_extracted_at     timestamp with time zone NOT NULL,
            _airbyte_meta             jsonb NOT NULL DEFAULT '{{}}',
            _airbyte_generation_id    integer NOT NULL DEFAULT 0
        )
    """)
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {SCHEMA}.meta_ad_performance (
            ad_set_id                 text,
            date                      date,
            spend                     numeric,
            impressions               integer,
            clicks                    integer,
            purchases                 integer,
            revenue                   numeric,
            cpm                       numeric,
            ctr                       numeric,
            roas                      numeric,
            frequency                 numeric,
            reach                     integer,
            attribution_window        text,
            _airbyte_raw_id           text NOT NULL,
            _airbyte_extracted_at     timestamp with time zone NOT NULL,
            _airbyte_meta             jsonb NOT NULL DEFAULT '{{}}',
            _airbyte_generation_id    integer NOT NULL DEFAULT 0
        )
    """)
    logger.info('ensure_tables | DDL complete (meta_campaigns, meta_ad_sets, meta_ad_performance)')


# ─── 1. Seed campaigns ──────────────────────────────────────────────────────────

def seed_meta_campaigns(cur) -> None:
    try:
        cols = [
            'campaign_id', 'campaign_name', 'objective', 'status', 'created_at',
            '_airbyte_raw_id', '_airbyte_extracted_at', '_airbyte_meta', '_airbyte_generation_id',
        ]
        rows = []
        for c in CAMPAIGNS:
            ab = airbyte_meta_cols(c['created_at'])
            rows.append((
                c['campaign_id'], c['campaign_name'], c['objective'],
                c['status'], c['created_at'],
                *ab,
            ))
        n = batch_insert(cur, 'meta_campaigns', cols, rows)
        logger.info('seed_meta_campaigns | rows: %d', n)
    except Exception as e:
        logger.error('SOURCE: Meta Seed | CLIENT: %s | ERROR: %s | CONTEXT: seed_meta_campaigns',
                     CLIENT_ID, str(e))
        raise


# ─── 2. Seed ad sets ────────────────────────────────────────────────────────────

def seed_meta_ad_sets(cur) -> None:
    try:
        cols = [
            'ad_set_id', 'campaign_id', 'ad_set_name', 'daily_budget',
            'targeting_type', 'status', 'created_at',
            '_airbyte_raw_id', '_airbyte_extracted_at', '_airbyte_meta', '_airbyte_generation_id',
        ]
        rows = []
        for a in AD_SETS:
            ab = airbyte_meta_cols(a['created_at'])
            rows.append((
                a['ad_set_id'], a['campaign_id'], a['ad_set_name'], a['daily_budget'],
                a['targeting_type'], a['status'], a['created_at'],
                *ab,
            ))
        n = batch_insert(cur, 'meta_ad_sets', cols, rows)
        logger.info('seed_meta_ad_sets | rows: %d', n)
    except Exception as e:
        logger.error('SOURCE: Meta Seed | CLIENT: %s | ERROR: %s | CONTEXT: seed_meta_ad_sets',
                     CLIENT_ID, str(e))
        raise


# ─── 3. Seed ad performance ─────────────────────────────────────────────────────

def seed_meta_ad_performance(cur, manifest: dict) -> dict[tuple[int, int], float]:
    """
    Generates one row per (ad_set_id, date). Returns monthly_spend_actual dict.

    Consistency invariants enforced on every row:
      spend / (impressions / 1000) = cpm
      clicks / impressions = ctr
      revenue / spend = roas
    """
    try:
        all_days = list(date_range(SEED_START, SEED_END))
        n_days   = len(all_days)

        # Pre-generate correlated daily signals (n_days + 5 for 4-day lag buffer)
        signals = generate_daily_meta_signals(n_days)
        # signals shape: (n_days+5, 3) — [cpm_noise, freq_noise, ctr_noise]

        # Build weekly Meta-attributed purchase lookup from manifest
        weekly_orders = _build_weekly_order_counts(manifest)
        META_ATTR_RATE = 0.35   # 35% of Shopify orders attributed to Meta (UTM_SOURCE_WEIGHTS)

        cols = [
            'ad_set_id', 'date', 'spend', 'impressions', 'clicks', 'purchases',
            'revenue', 'cpm', 'ctr', 'roas', 'frequency', 'reach', 'attribution_window',
            '_airbyte_raw_id', '_airbyte_extracted_at', '_airbyte_meta', '_airbyte_generation_id',
        ]

        # Build ad_set lookup: ad_set_id → (active_from, active_to, daily_budget, targeting_type)
        adset_index: list[dict] = AD_SETS

        # Accumulate monthly spend for billing statement
        monthly_spend_actual: dict[tuple[int, int], float] = {}

        # CPM history for 4-day lag (ring buffer)
        cpm_history: list[float] = [17.5] * 10   # initialise to midpoint

        rows: list[tuple] = []

        for day_idx, d in enumerate(all_days):
            sig_idx = day_idx  # signals array index (0-based, has 5-row buffer)

            cpm_noise  = float(signals[sig_idx, 0])
            freq_noise = float(signals[sig_idx, 1])
            ctr_noise  = float(signals[sig_idx, 2])

            # Episode multipliers
            ep_cpm, ep_roas, ep_freq_prosp, ep_ctr = _get_episode_multipliers(d)

            # Day-of-week CPM multiplier (A10)
            dow_mult = DOW_CPM_MULT[d.weekday()]

            # Attribution window
            attr_window = ('7d_click_1d_view' if d >= ATTRIBUTION_CHANGE_DATE
                           else '28d_click_7d_view')

            # Base CPM for this day
            base_cpm = CPM_BASE_LOW + (CPM_BASE_HIGH - CPM_BASE_LOW) * 0.5
            day_cpm  = round(base_cpm * cpm_noise * dow_mult * ep_cpm, 2)
            day_cpm  = max(8.0, min(45.0, day_cpm))

            cpm_history.append(day_cpm)

            # Lagged CPM for ROAS anti-correlation (4-day lag, -0.72)
            lagged_cpm = cpm_history[-5] if len(cpm_history) >= 5 else cpm_history[0]
            lagged_cpm_norm = lagged_cpm / base_cpm   # normalise
            roas_cpm_factor = 1.0 - 0.36 * (lagged_cpm_norm - 1.0)  # ≈ -0.72 corr

            # Base ROAS
            base_roas = (ROAS_BASE_LOW + ROAS_BASE_HIGH) / 2.0
            day_roas  = base_roas * roas_cpm_factor * ep_roas
            day_roas  = round(max(1.2, min(6.0, day_roas)), 3)

            # Creative fatigue CTR suppression
            fatigue_ctr_factor = _creative_fatigue_severity(d)

            # Base CTR
            base_ctr = (CTR_BASE_LOW + CTR_BASE_HIGH) / 2.0
            day_ctr  = base_ctr * ctr_noise * ep_ctr * fatigue_ctr_factor
            day_ctr  = round(max(0.004, min(0.035, day_ctr)), 5)

            # Monthly spend target
            key = (d.year, d.month)
            monthly_target  = MONTHLY_META_SPEND.get(key, 35_000.0)
            daily_target    = monthly_target / days_in_month(d.year, d.month)

            # Determine active ad sets for this day
            active_adsets = [a for a in adset_index
                             if a['_active_from'] <= d <= a['_active_to']]
            if not active_adsets:
                continue

            # Distribute daily spend across ad sets by budget weight
            total_weight  = sum(a['daily_budget'] for a in active_adsets)
            # Guard: NULL/MISSING check — all ad sets have budget > 0 by definition,
            # but if total_weight is somehow 0, distribute equally.
            if total_weight <= 0:
                total_weight = len(active_adsets)
                weights = [1.0] * len(active_adsets)
            else:
                weights = [a['daily_budget'] / total_weight for a in active_adsets]

            # Meta-attributed purchases for this week, distributed by day spend weight
            week_key    = _iso_week_key(d)
            week_orders = weekly_orders.get(week_key, 0)
            meta_orders_this_week = week_orders * META_ATTR_RATE
            # Approximate per-day share (uniform across 7 days — refined by spend below)
            meta_orders_today = meta_orders_this_week / 7.0

            day_total_spend = 0.0

            for adset, weight in zip(active_adsets, weights):
                adset_spend = round(daily_target * weight, 2)
                if adset_spend < 0.01:
                    continue

                # ROAS: prospecting sets slightly lower than retargeting
                targeting = adset['targeting_type']
                roas_type_adj = 0.90 if targeting == 'prospecting' else (1.10 if targeting == 'retargeting' else 1.00)
                adset_roas = round(day_roas * roas_type_adj, 3)

                # Frequency: retargeting higher than prospecting
                if targeting == 'retargeting':
                    base_freq = (FREQ_RETARG_LOW + FREQ_RETARG_HIGH) / 2.0
                else:
                    base_freq = (FREQ_PROSP_LOW + FREQ_PROSP_HIGH) / 2.0
                adset_freq = round(base_freq * freq_noise * ep_freq_prosp, 2)
                # Force fatigue signature on fatigue dates (prospecting only)
                if d in FATIGUE_DATE_SET and targeting == 'prospecting':
                    adset_freq = round(max(2.82, adset_freq * 1.6), 2)
                adset_freq = max(1.0, min(4.5, adset_freq))

                # Derive consistent metrics from spend + CPM + CTR + ROAS
                adset_cpm = round(day_cpm, 2)
                impressions = max(1, round(adset_spend / adset_cpm * 1000))
                adset_ctr   = round(day_ctr, 5)
                clicks      = max(0, round(impressions * adset_ctr))
                revenue     = round(adset_spend * adset_roas, 2)

                # Purchases: proportional share of today's Meta-attributed orders
                # weighted by this ad set's share of today's total spend
                purchases = max(0, round(meta_orders_today * weight * roas_type_adj))

                # Reach = impressions / frequency
                reach = max(1, round(impressions / adset_freq))

                ab = airbyte_meta_cols(airbyte_ts(d))
                rows.append((
                    adset['ad_set_id'],
                    d,
                    adset_spend,
                    impressions,
                    clicks,
                    purchases,
                    revenue,
                    adset_cpm,
                    adset_ctr,
                    adset_roas,
                    adset_freq,
                    reach,
                    attr_window,
                    *ab,
                ))

                day_total_spend += adset_spend

            # Accumulate monthly spend
            monthly_spend_actual[key] = monthly_spend_actual.get(key, 0.0) + day_total_spend

        # Bulk insert in batches (FIX 3 — within caller's transaction)
        n = batch_insert(cur, 'meta_ad_performance', cols, rows)
        logger.info('seed_meta_ad_performance | rows: %d', n)
        return monthly_spend_actual

    except Exception as e:
        logger.error('SOURCE: Meta Seed | CLIENT: %s | ERROR: %s | CONTEXT: seed_meta_ad_performance',
                     CLIENT_ID, str(e))
        raise


# ─── 4. Seed billing statement (INSERT ONLY — FIX 5) ───────────────────────────

def seed_meta_billing_statement(cur, monthly_spend: dict[tuple[int, int], float]) -> None:
    """
    Inserts one row per calendar month into the pre-existing meta_billing_statement table.
    FIX 5: queries identity_generation to exclude GENERATED ALWAYS columns.
    """
    try:
        # Check table exists
        cur.execute("""
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_schema = %s AND table_name = 'meta_billing_statement'
        """, (SCHEMA,))
        if cur.fetchone()[0] == 0:
            logger.error(
                'SOURCE: Meta Seed | CLIENT: %s | ERROR: meta_billing_statement not found — skip',
                CLIENT_ID)
            return

        # FIX 5 — get insertable columns (exclude GENERATED ALWAYS identity)
        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = %s
              AND table_name = 'meta_billing_statement'
              AND (identity_generation IS NULL OR identity_generation != 'ALWAYS')
            ORDER BY ordinal_position
        """, (SCHEMA,))
        actual_cols = [row[0] for row in cur.fetchall()]

        if not actual_cols:
            logger.error('SOURCE: Meta Seed | CLIENT: %s | ERROR: no insertable columns in meta_billing_statement', CLIENT_ID)
            return

        # Build one row per calendar month (24 months)
        rows: list[tuple] = []
        seen_months = set()

        # Enumerate all calendar months in seed range
        y, m = SEED_START.year, SEED_START.month
        while date(y, m, 1) <= SEED_END:
            key = (y, m)
            if key not in seen_months:
                seen_months.add(key)
                billing_month   = date(y, m, 1)
                total_spend     = round(monthly_spend.get(key, 0.0), 2)
                statement_id    = f'META-{CLIENT_ID.upper()}-{y}{m:02d}'
                invoice_date    = date(y, m, 1)
                extracted_at    = airbyte_ts(date(y, m, 28 if m != 2 else 27))
                ab              = airbyte_meta_cols(extracted_at)
                created_at_val  = utc_dt(date(y, m, 28 if m != 2 else 27), 12)

                # Map of all plausible column names → values
                col_map: dict[str, object] = {
                    'client_id':               CLIENT_ID,
                    'billing_month':           billing_month,
                    'statement_month':         billing_month,
                    'billing_date':            billing_month,
                    'total_spend':             total_spend,
                    'amount':                  total_spend,
                    'total_amount':            total_spend,
                    'currency':                'USD',
                    'payment_method':          'automatic',
                    'billing_status':          'PAID',
                    'status':                  'PAID',
                    'statement_id':            statement_id,
                    'invoice_id':              statement_id,
                    'invoice_date':            invoice_date,
                    'created_at':              created_at_val,
                    '_airbyte_raw_id':         ab[0],
                    '_airbyte_extracted_at':   ab[1],
                    '_airbyte_meta':           ab[2],
                    '_airbyte_generation_id':  ab[3],
                }

                row = tuple(col_map.get(c) for c in actual_cols)
                rows.append(row)

            # Advance month
            if m == 12:
                y += 1
                m  = 1
            else:
                m += 1

        if rows:
            sql = (f'INSERT INTO {SCHEMA}.meta_billing_statement '
                   f'({", ".join(actual_cols)}) VALUES %s ON CONFLICT DO NOTHING')
            psycopg2.extras.execute_values(cur, sql, rows)
            logger.info('seed_meta_billing_statement | rows: %d', len(rows))

    except Exception as e:
        logger.error(
            'SOURCE: Meta Seed | CLIENT: %s | ERROR: %s | CONTEXT: seed_meta_billing_statement',
            CLIENT_ID, str(e))
        raise


# ─── 5. Seed alert_log and brand_event_calendar ─────────────────────────────────

def seed_meta_alerts(cur) -> None:
    """
    Seeds alert_log with Meta-sourced alerts:
      - B1 (creative fatigue) × 8  (6 Y1, 2 Y2)
      - D1 (audience saturation)   Sep 2025
      - A1 (ROAS drop)             when ROAS drops >20% >3 days, with suppression
      - Competitor diagnostics × 2 (Feb 2025, Feb 2026)

    Seeds brand_event_calendar with:
      - meta_attribution_window_change (Jan 12 2026, suppress A1/A3 for 14 days)
      - meta_learning_phase_mgmt (Apr 1 – May 12 2025, suppress A1)
    """
    try:
        # ── alert_log helper (matches seed_shopify.py column order) ──────────────
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

        def alert(alert_type, fired_at, should_fire, confidence,
                  signal_value=None, threshold_value=None, threshold_direction='below',
                  layer1_headline=None, layer2_context=None, layer3_precedent=None,
                  alert_instance_number=1, escalation_level=0,
                  suppressed=False, suppression_category=None,
                  fatigue_period=False, fatigue_reason=None,
                  outcome_confirmed=None, dismissal_correct=None):
            return (
                CLIENT_ID, alert_type,
                fired_at,
                should_fire, confidence,
                signal_value, threshold_value, threshold_direction,
                layer1_headline or f'{alert_type} alert',
                layer2_context, layer3_precedent,
                alert_instance_number, escalation_level,
                suppressed, suppression_category,
                fatigue_period, fatigue_reason,
                outcome_confirmed, dismissal_correct,
                True,  # is_synthetic — alert_log IS a public table (not a raw table)
            )

        alert_rows: list[tuple] = []

        # ── B1: Creative fatigue × 8 ─────────────────────────────────────────────
        for idx, fd in enumerate(CREATIVE_FATIGUE_DATES, start=1):
            year_label  = 'Y1' if fd < date(2025, 6, 1) else 'Y2'
            severity    = round(PY_RNG.uniform(0.72, 0.88), 2)
            freq_val    = round(PY_RNG.uniform(2.82, 3.15), 2)
            ctr_decline = round(PY_RNG.uniform(0.15, 0.24), 2)

            alert_rows.append(alert(
                'B1',
                utc_dt(fd, 9),
                should_fire=True,
                confidence=severity,
                signal_value=freq_val,
                threshold_value=2.8,
                threshold_direction='above',
                layer1_headline=(
                    f'Creative fatigue detected — prospecting frequency reached {freq_val:.2f} '
                    f'(threshold: 2.8) and CTR declined {ctr_decline*100:.0f}% over 7 days.'
                ),
                layer2_context=(
                    f'This is creative fatigue event {idx} of the {year_label} dataset. '
                    f'Rotate prospecting creative immediately to reset frequency. '
                    f'Retargeting ad sets unaffected (running on separate audience pool).'
                ),
                layer3_precedent=(
                    'No prior Y1 baseline for this creative rotation cycle.'
                    if fd < CREATIVE_FATIGUE_DATES[1]
                    else 'Prior fatigue events resolved within 5–7 days of creative rotation. '
                         'Rotate and monitor CTR recovery.'
                ),
                fatigue_period=(fd in CREATIVE_FATIGUE_DATES[-2:]),  # Y2 events
            ))

        # ── D1: Audience saturation (Sep 2025 / Month 16) ────────────────────────
        alert_rows.append(alert(
            'D1',
            utc_dt(date(2025, 9, 15), 9),
            should_fire=True,
            confidence=0.84,
            signal_value=48_000.0,
            threshold_value=42_000.0,
            threshold_direction='above',
            layer1_headline=(
                'Audience saturation detected. Meta spend crossed $42K/month threshold '
                '(Month 16) and ROAS has compressed 17% over 6 weeks despite stable CPM. '
                'This is saturation, not creative fatigue.'
            ),
            layer2_context=(
                'Prospecting frequency has sustained at 2.9–3.1 for 4 consecutive weeks. '
                'CPM is stable ($17.20 avg), confirming demand-side saturation rather than '
                'auction competition. ROAS decline is structural — expanding to new audiences '
                'required before scaling spend further.'
            ),
            layer3_precedent=(
                'First saturation event in dataset (Month 16). No prior Y1 precedent. '
                'Industry benchmark: prospecting saturation typically occurs at 2.8–3.2× '
                'average weekly reach vs addressable audience size.'
            ),
        ))

        # ── A1: ROAS drop alerts (suppress during BFCM and Jan 12–26 2026) ────────
        # Pre-defined ROAS drop events — each is a 4-day consecutive drop >20%
        roas_drop_events: list[tuple[date, float, float, bool, str | None, str]] = [
            # (fire_date, signal_roas, threshold_roas, suppressed, sup_cat, context)
            (date(2024, 8,  12), 2.18, 2.80, False, None,
             'CPM spike (+22%) compressed ROAS below threshold. Creative fatigue co-occurring. '
             'Check ad creative frequency — rotate to recover ROAS.'),
            (date(2024, 10,  8), 2.31, 2.80, False, None,
             'FW24 launch CPM spike (+25%) during active campaign window. '
             'ROAS compression expected to recover within 14–21 days as algorithm optimises.'),
            (date(2025,  2, 15), 2.24, 2.80, False, None,
             'CPM elevated +30% (competitor activity Feb 2025 — Month 9). '
             'CTR and conversion rate holding — spend efficiency compressed, not performance.'),
            (date(2025,  4, 10), 2.38, 2.80, False, None,
             'New marketing manager onboarded Apr 1. Campaign restructure in learning phase. '
             'ROAS dip 15% expected for 6 weeks. Suppression not triggered — learning expected.'),
            (date(2025,  9, 15), 2.44, 2.80, False, None,
             'Audience saturation (Month 16). ROAS compressed 17% despite stable CPM. '
             'See concurrent D1 alert for full causal chain.'),
            # Jan 12 2026 window — ROAS drop is mechanical, SUPPRESS A1 for 14 days
            (date(2026,  1, 13), 2.28, 2.80, True,  'S_meta_attribution_window',
             'A1 suppressed: ROAS decline on Jan 13 is a mechanical artefact of attribution '
             'window change on Jan 12 (28d→7d click). Not a real performance decline. '
             'See brand_event_calendar: meta_attribution_window_change.'),
            (date(2026,  2, 12), 2.29, 2.80, False, None,
             'CPM spike +28% (competitor activity Feb 2026 — Month 21). '
             'Pattern matches Month 9 competitor event. CTR and conversion stable.'),
        ]

        for rd in roas_drop_events:
            fire_date, sig_roas, thresh_roas, suppressed, sup_cat, ctx = rd

            # Check if in BFCM window — suppress additional A1s during BFCM
            in_bfcm = (BFCM_Y1_START <= fire_date <= BFCM_Y1_END or
                       BFCM_Y2_START <= fire_date <= BFCM_Y2_END)
            if in_bfcm:
                suppressed  = True
                sup_cat     = 'S_bfcm_cpm_expected'
                ctx         = 'A1 suppressed — BFCM CPM spike expected (State 3 suppression). ' + ctx

            alert_rows.append(alert(
                'A1',
                utc_dt(fire_date, 9),
                should_fire=not suppressed,
                confidence=0.0 if suppressed else 0.82,
                signal_value=sig_roas,
                threshold_value=thresh_roas,
                threshold_direction='below',
                layer1_headline=(
                    f'ROAS has dropped below threshold: {sig_roas:.2f}x vs {thresh_roas:.2f}x '
                    f'for 3+ consecutive days.'
                    if not suppressed
                    else f'A1 suppressed (ROAS: {sig_roas:.2f}x). See suppression context.'
                ),
                layer2_context=ctx,
                layer3_precedent=(
                    'ROAS recovery pattern: drops occur over 3–4 days, recovery takes 14–21 days. '
                    'Asymmetric recovery curve — do not panic-pause spend during recovery window.'
                    if not suppressed else None
                ),
                suppressed=suppressed,
                suppression_category=sup_cat,
            ))

        # ── Competitor activity diagnostics ───────────────────────────────────────
        for comp_date, month_label in [
            (date(2025, 2, 10), 'Month 9 (Feb 2025)'),
            (date(2026, 2, 10), 'Month 21 (Feb 2026)'),
        ]:
            cpm_spike = round(PY_RNG.uniform(1.26, 1.33), 2)
            alert_rows.append(alert(
                'A3',
                utc_dt(comp_date, 10),
                should_fire=True,
                confidence=0.68,
                signal_value=cpm_spike,
                threshold_value=1.20,
                threshold_direction='above',
                layer1_headline=(
                    f'CPM spike +{(cpm_spike-1)*100:.0f}% in {month_label} with no internal '
                    f'causal explanation. CTR and conversion rate holding — external activity suspected.'
                ),
                layer2_context=(
                    'Spend efficiency compressed but no campaign or creative changes logged. '
                    'Pattern is consistent with competitor auction activity. '
                    'Consider external competitive activity as primary hypothesis.'
                ),
                layer3_precedent=(
                    'No prior competitor activity baseline — first event.'
                    if comp_date.year == 2025
                    else 'Prior competitor activity: Feb 2025 (Month 9). Same CPM spike pattern. '
                         'Confirmed recurring seasonal competitor activity window.'
                ),
            ))

        # Bulk insert alert_log rows
        n_alerts = 0
        for i in range(0, len(alert_rows), 200):
            chunk = alert_rows[i: i + 200]
            sql = (f'INSERT INTO public.alert_log ({", ".join(alert_cols)}) '
                   f'VALUES %s ON CONFLICT DO NOTHING')
            psycopg2.extras.execute_values(cur, sql, chunk)
            n_alerts += len(chunk)
        logger.info('seed_meta_alerts | alert_log: %d rows', n_alerts)

        # ── brand_event_calendar entries ──────────────────────────────────────────
        bec_cols = [
            'client_id', 'event_name', 'event_type', 'start_date', 'end_date',
            'suppress_alerts', 'context_alerts', 'context_explanation',
            'residual_threshold_pct', 'confidence_decay_type',
            'confidence_decay_start', 'confidence_decay_end', 'confidence_at_peak',
            'detection_method', 'detection_lag_hours', 'confidence', 'last_verified_at',
            'is_recurring', 'recurrence_rule', 'auto_detected', 'detected_from',
            'event_profile', 'suppression_type', 'is_synthetic',
        ]

        def bec_evt(name, etype, start, end, suppress=None, context=None,
                    ctx_explanation=None, residual_pct=None,
                    confidence_at_peak=1.0, suppression_type='reactive',
                    event_profile=None):
            return (
                CLIENT_ID, name, etype, start, end,
                suppress or [],
                context or [],
                ctx_explanation,
                residual_pct,
                None,   # confidence_decay_type
                None,   # confidence_decay_start
                None,   # confidence_decay_end
                confidence_at_peak,
                'hardcoded',
                0,      # detection_lag_hours
                1.0,    # confidence
                None,   # last_verified_at
                False,  # is_recurring
                None,   # recurrence_rule
                True,   # auto_detected
                None,   # detected_from
                json.dumps(event_profile) if event_profile else None,
                suppression_type,
                True,   # is_synthetic
            )

        bec_rows: list[tuple] = [
            # Meta attribution window change Jan 12 2026
            bec_evt(
                'Meta Attribution Window Change', 'platform_change',
                date(2026, 1, 12), date(2026, 1, 26),
                suppress=['A1', 'A3'],
                context=['D1'],
                ctx_explanation=(
                    'Meta changed default attribution window from 28-day click / 7-day view '
                    'to 7-day click / 1-day view on Jan 12 2026. Reported ROAS drops 18–22% '
                    'mechanically. This is NOT a real performance decline — it is a measurement '
                    'change. A1 and A3 suppressed for 14 days post-change.'
                ),
                residual_pct=100,
                confidence_at_peak=1.0,
                suppression_type='proactive',
                event_profile={
                    'window_before': '28d_click_7d_view',
                    'window_after':  '7d_click_1d_view',
                    'expected_roas_decline_pct': 20,
                    'suppress_days': 14,
                },
            ),
            # Marketing manager hired — learning phase ROAS dip
            bec_evt(
                'Marketing Manager Onboarded', 'operational_change',
                date(2025, 4, 1), date(2025, 5, 12),
                suppress=['A1'],
                context=['B2'],
                ctx_explanation=(
                    'New marketing manager hired Apr 1 2025. Campaign restructure and ad set '
                    'renaming initiated. Meta learning phase causes ROAS dip of ~15% for 6 weeks. '
                    'A1 suppressed during learning period — dip is structural, not actionable.'
                ),
                residual_pct=60,
                confidence_at_peak=1.0,
                suppression_type='proactive',
            ),
        ]

        n_bec = batch_insert(cur, 'brand_event_calendar', bec_cols, bec_rows)
        logger.info('seed_meta_alerts | brand_event_calendar: %d rows', n_bec)

    except Exception as e:
        logger.error('SOURCE: Meta Seed | CLIENT: %s | ERROR: %s | CONTEXT: seed_meta_alerts',
                     CLIENT_ID, str(e))
        raise


# ─── 6. Validation checks ───────────────────────────────────────────────────────

def validate_meta_seed(conn) -> None:
    """
    Seven validation checks. Prints actual vs expected. Never raises.
    """
    print('\n' + '═' * 68)
    print('META SEED VALIDATION')
    print('═' * 68)

    def check(label: str, sql: str, expected_low: float, expected_high: float,
              transform=None) -> None:
        try:
            cur = conn.cursor()
            cur.execute(sql)
            raw = cur.fetchone()
            actual = raw[0] if raw else None
            if transform and actual is not None:
                actual = transform(actual)
            ok = (actual is not None and expected_low <= actual <= expected_high)
            status = 'PASS' if ok else 'FAIL'
            print(f'[{status}] {label}')
            print(f'       expected: {expected_low:,.1f} – {expected_high:,.1f} | '
                  f'actual: {actual:,.2f}' if actual is not None
                  else f'       expected: {expected_low:,.1f} – {expected_high:,.1f} | '
                       f'actual: None')
        except Exception as e:
            print(f'[ERR ] {label} — {e}')

    # 1. Total rows in meta_ad_performance
    check(
        'meta_ad_performance total rows',
        f"SELECT COUNT(*) FROM {SCHEMA}.meta_ad_performance",
        expected_low=6_500, expected_high=9_500,
    )

    # 2. Monthly spend Nov 2024 — expect ~$52,000
    check(
        'meta_ad_performance monthly spend Nov 2024',
        f"""SELECT SUM(spend) FROM {SCHEMA}.meta_ad_performance
            WHERE date >= '2024-11-01' AND date <= '2024-11-30'""",
        expected_low=46_000, expected_high=58_000,
    )

    # 3. Monthly spend Nov 2025 — expect ~$62,000
    check(
        'meta_ad_performance monthly spend Nov 2025',
        f"""SELECT SUM(spend) FROM {SCHEMA}.meta_ad_performance
            WHERE date >= '2025-11-01' AND date <= '2025-11-30'""",
        expected_low=55_000, expected_high=69_000,
    )

    # 4. ROAS average before Jan 12 2026 — expect 2.8–3.4x
    check(
        'ROAS avg before attribution change (< 2026-01-12)',
        f"""SELECT AVG(roas) FROM {SCHEMA}.meta_ad_performance
            WHERE date < '2026-01-12'""",
        expected_low=2.50, expected_high=3.80,
    )

    # 5. ROAS average after Jan 12 2026 — expect ~18–22% lower
    # After change: 2.8–3.4 × 0.80 = 2.24–2.72
    check(
        'ROAS avg after attribution change (>= 2026-01-12)',
        f"""SELECT AVG(roas) FROM {SCHEMA}.meta_ad_performance
            WHERE date >= '2026-01-12'""",
        expected_low=1.90, expected_high=3.20,
    )

    # 6. B1 creative fatigue alert count — expect 8
    check(
        "B1 creative fatigue alerts in alert_log",
        f"""SELECT COUNT(*) FROM public.alert_log
            WHERE client_id = '{CLIENT_ID}' AND alert_type = 'B1'
            AND is_synthetic = true""",
        expected_low=8, expected_high=20,   # seed_shopify.py also seeds B1 — allow total >8
    )

    # 7. meta_billing_statement row count — expect 24 (one per month)
    check(
        'meta_billing_statement row count',
        f"SELECT COUNT(*) FROM {SCHEMA}.meta_billing_statement",
        expected_low=24, expected_high=30,  # table may have rows from other seeds
    )

    print('═' * 68 + '\n')


# ─── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    logger.info('SOURCE: Meta Seed | CLIENT: %s | Starting meta seed', CLIENT_ID)

    conn = get_conn()
    try:
        manifest = load_manifest()

        # FIX 3 — single transaction boundary wraps ALL inserts
        with conn:
            cur = conn.cursor()

            logger.info('Step 1/6 — ensure_tables')
            ensure_tables(cur)

            logger.info('Step 2/6 — seed_meta_campaigns')
            seed_meta_campaigns(cur)

            logger.info('Step 3/6 — seed_meta_ad_sets')
            seed_meta_ad_sets(cur)

            logger.info('Step 4/6 — seed_meta_ad_performance')
            monthly_spend_actual = seed_meta_ad_performance(cur, manifest)

            logger.info('Step 5/6 — seed_meta_billing_statement')
            seed_meta_billing_statement(cur, monthly_spend_actual)

            logger.info('Step 6/6 — seed_meta_alerts')
            seed_meta_alerts(cur)

        # Validation runs outside the transaction (read-only, never raises)
        validate_meta_seed(conn)

        logger.info('SOURCE: Meta Seed | CLIENT: %s | Seed complete', CLIENT_ID)

    except Exception as e:
        logger.error('SOURCE: Meta Seed | CLIENT: %s | ERROR: %s | CONTEXT: main',
                     CLIENT_ID, str(e))
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    main()
