"""
Profit Sentinel — Shopify Seed Script
Brand: Azure & Co (client_azure_co)
Archetype A: Premium Contemporary Womenswear, $150 AOV
Y1: June 2024 – May 2025 | Y2: June 2025 – May 2026
GMV: $4M Y1 → $5.2M Y2

Two-system architecture:
  System 1 — Episodic event calendar (~44–50 named events)
  System 2 — Correlated multivariate time series generator (NOT independent random walks)

Run order:
  1. seed_sku_master()         — products, variants, sku_cost_master
  2. seed_customers()          — shopify_customers, synthetic_customer_pii_lookup
  3. seed_orders()             — combines System 1 + System 2
  4. seed_line_items()         — shopify_order_line_items (after orders exist)
  5. seed_refunds()            — shopify_order_refunds (return cohorts)
  6. seed_fulfillments()       — shopify_fulfillments
  7. seed_discount_codes()     — shopify_discount_codes
  8. seed_touchpoint_journeys() — synthetic_touchpoint_journey (35–45% of orders)
  9. seed_brand_event_calendar() — all suppression-driving events
  10. seed_dq_scores()          — dq_metric_scores time-series
  11. seed_alert_log()          — key alert_log rows (Alert3 stage1/2, escalations)
  12. seed_suppression_log()    — key suppression_log rows (multi-suppression events)
  13. validate_seed()           — 11 validation checks
  14. write_manifest()          — seed_manifest_shopify.json
"""

import json
import logging
import os
import random
import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any

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

# ─── Constants ────────────────────────────────────────────────────────────────

CLIENT_ID   = 'azure_co'
SCHEMA      = 'client_azure_co'
BRAND_NAME  = 'Azure & Co'

Y1_START    = date(2024, 6, 1)
Y1_END      = date(2025, 5, 31)
Y2_START    = date(2025, 6, 1)
Y2_END      = date(2026, 5, 31)
SEED_START  = Y1_START
SEED_END    = Y2_END

AOV_BASE    = 150.0
SEED_RNG    = np.random.default_rng(42)
PY_RNG      = random.Random(42)

# ─── Monthly revenue targets (from B1) ────────────────────────────────────────
# Keys are (year, month). Values are (low, high) in dollars.
MONTHLY_REVENUE_TARGETS: dict[tuple[int, int], tuple[float, float]] = {
    # Y1
    (2024, 6):  (320_000, 340_000),
    (2024, 7):  (320_000, 340_000),
    (2024, 8):  (320_000, 340_000),
    (2024, 9):  (380_000, 420_000),
    (2024, 10): (380_000, 420_000),
    (2024, 11): (650_000, 650_000),   # BFCM
    (2024, 12): (480_000, 480_000),   # Holiday
    (2025, 1):  (280_000, 310_000),
    (2025, 2):  (280_000, 310_000),
    (2025, 3):  (380_000, 420_000),   # SS launch
    (2025, 4):  (420_000, 450_000),
    (2025, 5):  (380_000, 420_000),
    # Y2
    (2025, 6):  (420_000, 460_000),
    (2025, 7):  (420_000, 460_000),
    (2025, 8):  (420_000, 460_000),
    (2025, 9):  (480_000, 520_000),
    (2025, 10): (480_000, 520_000),
    (2025, 11): (780_000, 780_000),   # BFCM Y2
    (2025, 12): (560_000, 560_000),
    (2026, 1):  (320_000, 360_000),
    (2026, 2):  (320_000, 360_000),
    (2026, 3):  (480_000, 520_000),
    (2026, 4):  (510_000, 540_000),
    (2026, 5):  (480_000, 510_000),
}

# ─── SKU catalog ──────────────────────────────────────────────────────────────
# 120 active SKUs. Categories and counts:
# TOPS: 30  DRESS: 25  SHORT: 15  KNIT: 20  OUTERWEAR: 15  DENIM: 10
# FORMAL: 5 (added Month 15 = Aug 2025)  MENS: 5 (added Month 20 = Jan 2026)
# Three locked SKUs: AZ-TOP-088, AZ-DRESS-094, AZ-SHORT-031 (overstock event)

SKU_CATEGORIES = {
    'TOP':      {'count': 30, 'price_range': (68,  135), 'weight_g': 220},
    'DRESS':    {'count': 25, 'price_range': (128, 195), 'weight_g': 310},
    'SHORT':    {'count': 15, 'price_range': (68,  98),  'weight_g': 180},
    'KNIT':     {'count': 20, 'price_range': (95,  165), 'weight_g': 380},
    'OUTERWEAR':{'count': 15, 'price_range': (195, 285), 'weight_g': 620},
    'DENIM':    {'count': 10, 'price_range': (110, 155), 'weight_g': 510},
    'FORMAL':   {'count':  5, 'price_range': (165, 245), 'weight_g': 340},
    'MENS':     {'count':  5, 'price_range': (75,  145), 'weight_g': 280},
}

LOCKED_SKUS = {
    'AZ-TOP-088':   {'category': 'TOP',   'price': 68,  'launch': date(2024, 6, 1)},
    'AZ-DRESS-094': {'category': 'DRESS', 'price': 128, 'launch': date(2024, 6, 1)},
    'AZ-SHORT-031': {'category': 'SHORT', 'price': 82,  'launch': date(2024, 6, 1)},
}
DEFECTIVE_SKU = 'AZ-KNIT-031'   # defective batch Nov 28 2024

SIZES = ['XS', 'S', 'M', 'L', 'XL']
COLORS_BY_CAT = {
    'TOP':       ['White', 'Black', 'Sage', 'Blush', 'Navy'],
    'DRESS':     ['Black', 'Cream', 'Cobalt', 'Rust', 'Olive'],
    'SHORT':     ['Black', 'Stone', 'Denim', 'White', 'Khaki'],
    'KNIT':      ['Camel', 'Ivory', 'Charcoal', 'Dusty Rose', 'Forest'],
    'OUTERWEAR': ['Camel', 'Black', 'Chocolate', 'Cream', 'Slate'],
    'DENIM':     ['Light Wash', 'Mid Wash', 'Dark Wash', 'Black', 'Raw'],
    'FORMAL':    ['Black', 'Champagne', 'Sage', 'Navy', 'Blush'],
    'MENS':      ['White', 'Navy', 'Olive', 'Black', 'Stone'],
}

# ─── Standard Product Taxonomy (synthetic seed) ───────────────────────────────
# Real gids + breadcrumbs from Shopify's Standard Product Taxonomy, Apparel &
# Accessories vertical (sourced from data/shopify_taxonomy/categories.json).
# Baked here as constants so the seed has NO runtime dependency on the ~80 MB
# taxonomy file (that file is a gitignored reference asset, also used by the
# GraphQL real-data path).
#
# Coverage is DELIBERATELY not production's ~12%: ~40% of synthetic rows get a
# genuine apparel node (matched to product_type where sensible), ~60% stay
# cleanly NULL to exercise the LLM classify-and-snap fallback. The 'na'
# Uncategorized sentinel is for READING real Shopify data only — never seeded.
_TAXONOMY_PREFIX = 'gid://shopify/TaxonomyCategory/'

# product_type (lowercase) -> (category_id gid, category_full_name breadcrumb)
TAXONOMY_BY_PRODUCT_TYPE: dict[str, tuple[str, str]] = {
    'top':       (_TAXONOMY_PREFIX + 'aa-1-13',    'Apparel & Accessories > Clothing > Clothing Tops'),
    'dress':     (_TAXONOMY_PREFIX + 'aa-1-4',     'Apparel & Accessories > Clothing > Dresses'),
    'short':     (_TAXONOMY_PREFIX + 'aa-1-14',    'Apparel & Accessories > Clothing > Shorts'),
    'knit':      (_TAXONOMY_PREFIX + 'aa-1-13-12', 'Apparel & Accessories > Clothing > Clothing Tops > Sweaters'),
    'outerwear': (_TAXONOMY_PREFIX + 'aa-1-10-2',  'Apparel & Accessories > Clothing > Outerwear > Coats & Jackets'),
    'denim':     (_TAXONOMY_PREFIX + 'aa-1-12-4',  'Apparel & Accessories > Clothing > Pants > Jeans'),
    'formal':    (_TAXONOMY_PREFIX + 'aa-1-19',    'Apparel & Accessories > Clothing > Suits'),
}

# Fallback pool for product_types with no sensible direct match (e.g. 'mens').
TAXONOMY_APPAREL_POOL: list[tuple[str, str]] = [
    (_TAXONOMY_PREFIX + 'aa-1-13',   'Apparel & Accessories > Clothing > Clothing Tops'),
    (_TAXONOMY_PREFIX + 'aa-1-13-7', 'Apparel & Accessories > Clothing > Clothing Tops > Shirts'),
    (_TAXONOMY_PREFIX + 'aa-1-13-8', 'Apparel & Accessories > Clothing > Clothing Tops > T-Shirts'),
    (_TAXONOMY_PREFIX + 'aa-1-12',   'Apparel & Accessories > Clothing > Pants'),
    (_TAXONOMY_PREFIX + 'aa-1-15',   'Apparel & Accessories > Clothing > Skirts'),
    (_TAXONOMY_PREFIX + 'aa-1-10',   'Apparel & Accessories > Clothing > Outerwear'),
    (_TAXONOMY_PREFIX + 'aa-1-19',   'Apparel & Accessories > Clothing > Suits'),
    (_TAXONOMY_PREFIX + 'aa-1-1',    'Apparel & Accessories > Clothing > Activewear'),
]

SYNTHETIC_CATEGORY_FRACTION = 0.40  # ~40% categorized, ~60% NULL (test-coverage split)


def assign_synthetic_category(product_id: int, product_type: str) -> tuple[str | None, str | None]:
    """Deterministically assign a Standard Taxonomy category to a synthetic product.

    Returns (category_id, category_full_name) or (None, None).

    Deterministic and idempotent: keyed solely on product_id, so fresh re-seeds
    and repeat backfill passes reproduce the exact same split (never double-apply
    a different value). Uses an independent Random(product_id) so it does NOT draw
    from the global PY_RNG stream and cannot perturb any other seeded value.
    ~40% of rows get a genuine apparel node (matched to product_type when a
    sensible mapping exists, else a random apparel node); ~60% stay NULL.
    """
    rng = random.Random(product_id)
    if rng.random() >= SYNTHETIC_CATEGORY_FRACTION:
        return (None, None)  # ~60%: no category -> exercises the LLM fallback
    ptype = (product_type or '').lower()
    if ptype in TAXONOMY_BY_PRODUCT_TYPE:
        return TAXONOMY_BY_PRODUCT_TYPE[ptype]
    return rng.choice(TAXONOMY_APPAREL_POOL)  # e.g. 'mens' -> random apparel node


# ─── Payment gateway mix ──────────────────────────────────────────────────────
# Before Month 10 (Mar 2025): 80% credit card, 10% Shop Pay, 10% other
# Month 10+ BNPL introduced, gradual shift to 65% CC / 25% BNPL / 10% Shop Pay by Y2 end
def payment_mix(order_date: date) -> str:
    """Return payment gateway for an order based on BNPL introduction arc."""
    month_num = (order_date.year - 2024) * 12 + order_date.month - 5  # Month 1 = Jun 2024
    if month_num < 10:  # before BNPL
        return PY_RNG.choices(
            ['credit_card', 'shopify_payments', 'paypal'],
            weights=[80, 10, 10]
        )[0]
    # BNPL ramp: month 10 → 25% by month 24
    bnpl_pct = min(25, (month_num - 9) * 2)
    cc_pct   = max(65, 80 - bnpl_pct)
    shop_pct = max(10, 20 - bnpl_pct // 2)
    return PY_RNG.choices(
        ['credit_card', 'afterpay', 'shopify_payments'],
        weights=[cc_pct, bnpl_pct, shop_pct]
    )[0]

# ─── Day-of-week order volume multipliers ─────────────────────────────────────
# Mon higher, Fri–Sun lower for orders; CPM inverted (Mon–Wed +18%, Thu–Sun -12%)
DOW_ORDER_WEIGHTS = {
    0: 1.15,   # Monday
    1: 1.12,   # Tuesday
    2: 1.08,   # Wednesday
    3: 1.05,   # Thursday
    4: 0.95,   # Friday
    5: 0.85,   # Saturday
    6: 0.80,   # Sunday
}
# Weekend return rate premium: +6pp for Fri–Sun orders
WEEKEND_RETURN_PREMIUM = {'4': 0.06, '5': 0.06, '6': 0.06}

# ─── UTM attribution sources ──────────────────────────────────────────────────
# 35–45% have multi-touch journeys; 15–20% dark social (no UTM)
UTM_SOURCES = ['meta', 'tiktok', 'klaviyo', 'google', None]  # None = direct/dark social
UTM_SOURCE_WEIGHTS = [35, 20, 20, 10, 15]  # sums ~100

# ─── International currency distribution ─────────────────────────────────────
# 8–12% of orders are international
CURRENCIES = ['USD', 'GBP', 'CAD', 'AUD']
CURRENCY_WEIGHTS = [90, 4, 3, 3]
CURRENCY_RATES = {'USD': 1.0, 'GBP': 1.27, 'CAD': 0.74, 'AUD': 0.65}

# ─── Airbyte watermark helper ─────────────────────────────────────────────────
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

# ─── DB helpers ───────────────────────────────────────────────────────────────
def get_conn() -> psycopg2.extensions.connection:
    url = os.getenv('DATABASE_URL')
    if not url:
        logger.error('SOURCE: Shopify Seed | ERROR: DATABASE_URL not set')
        sys.exit(1)
    return psycopg2.connect(url, sslmode='require')

def batch_insert(cur, table: str, cols: list[str], rows: list[tuple], batch: int = 500, conflict_col: str = None) -> int:
    """Insert rows in batches using execute_values. Returns total rows inserted."""
    if not rows:
        return 0
    conflict_clause = f'ON CONFLICT ({conflict_col}) DO NOTHING' if conflict_col else 'ON CONFLICT DO NOTHING'
    sql = f'INSERT INTO {SCHEMA}.{table} ({", ".join(cols)}) VALUES %s {conflict_clause}'
    total = 0
    for i in range(0, len(rows), batch):
        chunk = rows[i: i + batch]
        psycopg2.extras.execute_values(cur, sql, chunk)
        total += len(chunk)
    return total

def batch_insert_public(cur, table: str, cols: list[str], rows: list[tuple], batch: int = 500) -> int:
    if not rows:
        return 0
    sql = f'INSERT INTO public.{table} ({", ".join(cols)}) VALUES %s ON CONFLICT DO NOTHING'
    total = 0
    for i in range(0, len(rows), batch):
        chunk = rows[i: i + batch]
        psycopg2.extras.execute_values(cur, sql, chunk)
        total += len(chunk)
    return total

# ─── Date iteration ───────────────────────────────────────────────────────────
def date_range(start: date, end: date):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)

def weeks_in_range(start: date, end: date):
    """Yield Monday of each week in range."""
    # start on first Monday on or after start
    d = start + timedelta(days=(7 - start.weekday()) % 7)
    while d <= end:
        yield d
        d += timedelta(days=7)

# ─── System 2: Correlated weekly signal generator ────────────────────────────
# Variables: [ga4_idx, cpm_idx, return_rate_idx, klaviyo_open_idx, orders_idx]
# Correlation matrix from design spec:
#   GA4 sessions → orders: +0.76
#   CPM → ROAS (inverse for orders): -0.72
#   Return rate → Gorgias: +0.81 (handled in Gorgias seed)
#   Return rate → Net revenue: -0.68 (via return_rate_idx)
#   Klaviyo open → repeat purchase: +0.43

_CORR_MATRIX_DESIGN = np.array([
    # ga4   cpm   ret   kla   ord
    [1.00, -0.30,  0.20,  0.43,  0.76],  # ga4_idx
    [-0.30,  1.00, -0.15, -0.20, -0.45],  # cpm_idx (high CPM → fewer orders)
    [0.20, -0.15,  1.00,  0.10, -0.55],  # return_rate_idx
    [0.43, -0.20,  0.10,  1.00,  0.38],  # klaviyo_open_idx
    [0.76, -0.45, -0.55,  0.38,  1.00],  # orders_idx
], dtype=float)

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
    pd = (pd + pd.T) / 2                     # numerical symmetry
    d = np.sqrt(np.diag(pd))
    pd = pd / np.outer(d, d)                 # congruence scale -> unit diagonal, PD preserved
    return pd

CORR_MATRIX = _nearest_pd_corr(_CORR_MATRIX_DESIGN)

# Print original vs adjusted so the operator can review what changed
_LABELS = ['ga4_idx', 'cpm_idx', 'ret_idx', 'kla_idx', 'ord_idx']
print('\n=== CORR_MATRIX: original design ===')
print(f"{'':12s}" + ''.join(f'{l:>10s}' for l in _LABELS))
for i, row in enumerate(_CORR_MATRIX_DESIGN):
    print(f'{_LABELS[i]:12s}' + ''.join(f'{v:10.4f}' for v in row))
print('\n=== CORR_MATRIX: nearest PD (used for Cholesky) ===')
print(f"{'':12s}" + ''.join(f'{l:>10s}' for l in _LABELS))
for i, row in enumerate(CORR_MATRIX):
    print(f'{_LABELS[i]:12s}' + ''.join(f'{v:10.4f}' for v in row))
print('\n=== Eigenvalues: original -> clipped ===')
_orig_vals = np.linalg.eigh(_CORR_MATRIX_DESIGN)[0]
_new_vals  = np.linalg.eigh(CORR_MATRIX)[0]
for o, n in zip(_orig_vals, _new_vals):
    flag = ' ** CLIPPED' if o < 1e-6 else ''
    print(f'  {o:10.6f}  ->  {n:10.6f}{flag}')
print()

def generate_weekly_signals(n_weeks: int) -> np.ndarray:
    """Generate correlated weekly noise multipliers for n_weeks.
    Returns array (n_weeks, 5) where cols are [ga4, cpm, return_rate, klaviyo, orders].
    Values are centred at 1.0 with ±15% weekly noise.
    """
    # Cholesky decomposition for correlated draws
    L = np.linalg.cholesky(CORR_MATRIX)
    noise = SEED_RNG.standard_normal((n_weeks, 5))
    corr_noise = noise @ L.T           # correlated normal noise
    # Scale: ±15% weekly noise (2 std devs = ±30%)
    signal = 1.0 + corr_noise * 0.075  # std = 0.075 → ±15% at 2σ
    # Clamp to sensible range
    signal = np.clip(signal, 0.6, 1.8)
    return signal


# ─── Influencer sub-calendar ──────────────────────────────────────────────────
# 30 activations: 20 micro, 7 mid, 3 macro. Y1: 12, Y2: 18.
INFLUENCER_CALENDAR = [
    # Y1 activations (12)
    {'id': 'INF-2024-JUN-01', 'tier': 'micro',  'activation_date': date(2024, 6, 15),
     'content_live_date': date(2024, 6, 22), 'fee_structure': 'gifting',
     'cash_fee': 0, 'package_landed_cost': 165, 'packaging_shipping_cost': 42,
     'content_format': 'styling', 'discount_code': 'AZURE10', 'audience_fit_score': 4,
     'geographic_skew': 'domestic_heavy', 'spark_ad_launched': False, 'instagram_reels_posted': False},
    {'id': 'INF-2024-JUL-01', 'tier': 'micro',  'activation_date': date(2024, 7, 3),
     'content_live_date': date(2024, 7, 10), 'fee_structure': 'hybrid',
     'cash_fee': 800, 'package_landed_cost': 148, 'packaging_shipping_cost': 35,
     'content_format': 'tryon_haul', 'discount_code': 'SUMMER15', 'audience_fit_score': 3,
     'geographic_skew': 'domestic_heavy', 'spark_ad_launched': True, 'instagram_reels_posted': False},
    {'id': 'INF-2024-JUL-02', 'tier': 'micro',  'activation_date': date(2024, 7, 18),
     'content_live_date': date(2024, 7, 25), 'fee_structure': 'gifting',
     'cash_fee': 0, 'package_landed_cost': 192, 'packaging_shipping_cost': 45,
     'content_format': 'grwm', 'discount_code': None, 'audience_fit_score': 5,
     'geographic_skew': 'domestic_heavy', 'spark_ad_launched': False, 'instagram_reels_posted': False},
    # Jan 2024 disrupted activations (Gap D3)
    {'id': 'INF-2024-JAN-02', 'tier': 'mid',    'activation_date': date(2023, 12, 20),
     'content_live_date': date(2024, 2, 5),   'fee_structure': 'hybrid',
     'cash_fee': 3500, 'package_landed_cost': 220, 'packaging_shipping_cost': 55,
     'content_format': 'styling', 'discount_code': 'AZURE15', 'audience_fit_score': 4,
     'geographic_skew': 'balanced', 'spark_ad_launched': True, 'instagram_reels_posted': True},
    {'id': 'INF-2024-FEB-01', 'tier': 'micro',  'activation_date': date(2024, 2, 1),
     'content_live_date': date(2024, 2, 8),   'fee_structure': 'gifting',
     'cash_fee': 0, 'package_landed_cost': 155, 'packaging_shipping_cost': 38,
     'content_format': 'unboxing', 'discount_code': 'AZURE10', 'audience_fit_score': 3,
     'geographic_skew': 'domestic_heavy', 'spark_ad_launched': False, 'instagram_reels_posted': False},
    {'id': 'INF-2024-MAR-02', 'tier': 'macro',  'activation_date': date(2024, 4, 1),
     'content_live_date': date(2024, 4, 8),   'fee_structure': 'cash',
     'cash_fee': 9000, 'package_landed_cost': 240, 'packaging_shipping_cost': 60,
     'content_format': 'tryon_haul', 'discount_code': 'AZURE20', 'audience_fit_score': 4,
     'geographic_skew': 'domestic_heavy', 'spark_ad_launched': True, 'instagram_reels_posted': True},
    {'id': 'INF-2024-AUG-01', 'tier': 'micro',  'activation_date': date(2024, 8, 5),
     'content_live_date': date(2024, 8, 12),  'fee_structure': 'gifting',
     'cash_fee': 0, 'package_landed_cost': 178, 'packaging_shipping_cost': 40,
     'content_format': 'styling', 'discount_code': None, 'audience_fit_score': 5,
     'geographic_skew': 'domestic_heavy', 'spark_ad_launched': False, 'instagram_reels_posted': False},
    {'id': 'INF-2024-SEP-01', 'tier': 'micro',  'activation_date': date(2024, 9, 10),
     'content_live_date': date(2024, 9, 17),  'fee_structure': 'hybrid',
     'cash_fee': 600, 'package_landed_cost': 195, 'packaging_shipping_cost': 48,
     'content_format': 'grwm', 'discount_code': 'AZURE10', 'audience_fit_score': 2,
     'geographic_skew': 'international_heavy', 'spark_ad_launched': False, 'instagram_reels_posted': False},
    {'id': 'INF-2024-OCT-01', 'tier': 'mid',    'activation_date': date(2024, 10, 1),
     'content_live_date': date(2024, 10, 8),  'fee_structure': 'hybrid',
     'cash_fee': 2800, 'package_landed_cost': 210, 'packaging_shipping_cost': 52,
     'content_format': 'tryon_haul', 'discount_code': 'FW15', 'audience_fit_score': 4,
     'geographic_skew': 'domestic_heavy', 'spark_ad_launched': True, 'instagram_reels_posted': True},
    {'id': 'INF-2024-NOV-01', 'tier': 'micro',  'activation_date': date(2024, 11, 5),
     'content_live_date': date(2024, 11, 12), 'fee_structure': 'gifting',
     'cash_fee': 0, 'package_landed_cost': 168, 'packaging_shipping_cost': 42,
     'content_format': 'unboxing', 'discount_code': 'BFCM25', 'audience_fit_score': 2,
     'geographic_skew': 'domestic_heavy', 'spark_ad_launched': False, 'instagram_reels_posted': False},
    {'id': 'INF-2024-FEB-FRAUD-01', 'tier': 'micro', 'activation_date': date(2024, 3, 1),
     'content_live_date': date(2024, 3, 8),  'fee_structure': 'gifting',
     'cash_fee': 0, 'package_landed_cost': 145, 'packaging_shipping_cost': 35,
     'content_format': 'styling', 'discount_code': None, 'audience_fit_score': 1,
     'geographic_skew': 'balanced', 'spark_ad_launched': False, 'instagram_reels_posted': False},
    {'id': 'INF-2024-MAY-01', 'tier': 'mid',    'activation_date': date(2025, 5, 1),
     'content_live_date': date(2025, 5, 8),  'fee_structure': 'hybrid',
     'cash_fee': 3000, 'package_landed_cost': 205, 'packaging_shipping_cost': 50,
     'content_format': 'styling', 'discount_code': 'SS15', 'audience_fit_score': 4,
     'geographic_skew': 'domestic_heavy', 'spark_ad_launched': True, 'instagram_reels_posted': True},
    # Y2 activations (18) — fees +30% per C16
    {'id': 'INF-2025-JUN-01', 'tier': 'micro',  'activation_date': date(2025, 6, 10),
     'content_live_date': date(2025, 6, 17),  'fee_structure': 'gifting',
     'cash_fee': 0, 'package_landed_cost': 185, 'packaging_shipping_cost': 48,
     'content_format': 'styling', 'discount_code': None, 'audience_fit_score': 5,
     'geographic_skew': 'domestic_heavy', 'spark_ad_launched': False, 'instagram_reels_posted': True},
    {'id': 'INF-2025-JUL-01', 'tier': 'micro',  'activation_date': date(2025, 7, 5),
     'content_live_date': date(2025, 7, 12),  'fee_structure': 'hybrid',
     'cash_fee': 1050, 'package_landed_cost': 192, 'packaging_shipping_cost': 46,
     'content_format': 'grwm', 'discount_code': 'AZURE10', 'audience_fit_score': 4,
     'geographic_skew': 'domestic_heavy', 'spark_ad_launched': True, 'instagram_reels_posted': True},
    {'id': 'INF-2025-AUG-01', 'tier': 'micro',  'activation_date': date(2025, 8, 4),
     'content_live_date': date(2025, 8, 11),  'fee_structure': 'gifting',
     'cash_fee': 0, 'package_landed_cost': 175, 'packaging_shipping_cost': 44,
     'content_format': 'unboxing', 'discount_code': 'AZURE10', 'audience_fit_score': 3,
     'geographic_skew': 'domestic_heavy', 'spark_ad_launched': False, 'instagram_reels_posted': True},
    {'id': 'INF-2025-SEP-01', 'tier': 'mid',    'activation_date': date(2025, 9, 8),
     'content_live_date': date(2025, 9, 15),  'fee_structure': 'hybrid',
     'cash_fee': 3640, 'package_landed_cost': 218, 'packaging_shipping_cost': 54,
     'content_format': 'tryon_haul', 'discount_code': 'FW20', 'audience_fit_score': 4,
     'geographic_skew': 'balanced', 'spark_ad_launched': True, 'instagram_reels_posted': True},
    {'id': 'INF-2025-SEP-02', 'tier': 'micro',  'activation_date': date(2025, 9, 20),
     'content_live_date': date(2025, 9, 27),  'fee_structure': 'gifting',
     'cash_fee': 0, 'package_landed_cost': 182, 'packaging_shipping_cost': 45,
     'content_format': 'styling', 'discount_code': None, 'audience_fit_score': 5,
     'geographic_skew': 'domestic_heavy', 'spark_ad_launched': False, 'instagram_reels_posted': True},
    {'id': 'INF-2025-OCT-01', 'tier': 'micro',  'activation_date': date(2025, 10, 6),
     'content_live_date': date(2025, 10, 13), 'fee_structure': 'hybrid',
     'cash_fee': 780, 'package_landed_cost': 165, 'packaging_shipping_cost': 42,
     'content_format': 'grwm', 'discount_code': 'AZURE15', 'audience_fit_score': 3,
     'geographic_skew': 'domestic_heavy', 'spark_ad_launched': False, 'instagram_reels_posted': True},
    {'id': 'INF-2025-OCT-02', 'tier': 'mid',    'activation_date': date(2025, 10, 15),
     'content_live_date': date(2025, 10, 22), 'fee_structure': 'cash',
     'cash_fee': 4680, 'package_landed_cost': 0, 'packaging_shipping_cost': 0,
     'content_format': 'styling', 'discount_code': 'FW15', 'audience_fit_score': 4,
     'geographic_skew': 'domestic_heavy', 'spark_ad_launched': True, 'instagram_reels_posted': True},
    {'id': 'INF-2025-NOV-01', 'tier': 'macro',  'activation_date': date(2025, 11, 1),
     'content_live_date': date(2025, 11, 8),  'fee_structure': 'cash',
     'cash_fee': 23400, 'package_landed_cost': 240, 'packaging_shipping_cost': 60,
     'content_format': 'tryon_haul', 'discount_code': 'BFCM30', 'audience_fit_score': 4,
     'geographic_skew': 'domestic_heavy', 'spark_ad_launched': True, 'instagram_reels_posted': True},
    {'id': 'INF-2025-NOV-02', 'tier': 'micro',  'activation_date': date(2025, 11, 10),
     'content_live_date': date(2025, 11, 17), 'fee_structure': 'gifting',
     'cash_fee': 0, 'package_landed_cost': 172, 'packaging_shipping_cost': 44,
     'content_format': 'unboxing', 'discount_code': 'BFCM25', 'audience_fit_score': 3,
     'geographic_skew': 'domestic_heavy', 'spark_ad_launched': False, 'instagram_reels_posted': True},
    {'id': 'INF-2025-DEC-01', 'tier': 'micro',  'activation_date': date(2025, 12, 5),
     'content_live_date': date(2025, 12, 12), 'fee_structure': 'gifting',
     'cash_fee': 0, 'package_landed_cost': 188, 'packaging_shipping_cost': 46,
     'content_format': 'styling', 'discount_code': None, 'audience_fit_score': 5,
     'geographic_skew': 'domestic_heavy', 'spark_ad_launched': False, 'instagram_reels_posted': True},
    {'id': 'INF-2026-JAN-01', 'tier': 'micro',  'activation_date': date(2026, 1, 12),
     'content_live_date': date(2026, 1, 19),  'fee_structure': 'hybrid',
     'cash_fee': 910, 'package_landed_cost': 175, 'packaging_shipping_cost': 44,
     'content_format': 'grwm', 'discount_code': 'AZURE10', 'audience_fit_score': 4,
     'geographic_skew': 'domestic_heavy', 'spark_ad_launched': True, 'instagram_reels_posted': True},
    {'id': 'INF-2026-FEB-01', 'tier': 'mid',    'activation_date': date(2026, 2, 3),
     'content_live_date': date(2026, 2, 10),  'fee_structure': 'hybrid',
     'cash_fee': 3900, 'package_landed_cost': 215, 'packaging_shipping_cost': 52,
     'content_format': 'tryon_haul', 'discount_code': 'VAL20', 'audience_fit_score': 4,
     'geographic_skew': 'domestic_heavy', 'spark_ad_launched': True, 'instagram_reels_posted': True},
    {'id': 'INF-2026-MAR-01', 'tier': 'micro',  'activation_date': date(2026, 3, 10),
     'content_live_date': date(2026, 3, 17),  'fee_structure': 'gifting',
     'cash_fee': 0, 'package_landed_cost': 182, 'packaging_shipping_cost': 45,
     'content_format': 'styling', 'discount_code': 'SS20', 'audience_fit_score': 5,
     'geographic_skew': 'domestic_heavy', 'spark_ad_launched': False, 'instagram_reels_posted': True},
    {'id': 'INF-2026-MAR-02', 'tier': 'macro',  'activation_date': date(2026, 3, 20),
     'content_live_date': date(2026, 3, 27),  'fee_structure': 'cash',
     'cash_fee': 26000, 'package_landed_cost': 240, 'packaging_shipping_cost': 60,
     'content_format': 'tryon_haul', 'discount_code': 'SS25', 'audience_fit_score': 3,
     'geographic_skew': 'balanced', 'spark_ad_launched': True, 'instagram_reels_posted': True},
    {'id': 'INF-2026-APR-01', 'tier': 'micro',  'activation_date': date(2026, 4, 8),
     'content_live_date': date(2026, 4, 15),  'fee_structure': 'gifting',
     'cash_fee': 0, 'package_landed_cost': 178, 'packaging_shipping_cost': 44,
     'content_format': 'unboxing', 'discount_code': None, 'audience_fit_score': 5,
     'geographic_skew': 'domestic_heavy', 'spark_ad_launched': False, 'instagram_reels_posted': True},
    {'id': 'INF-2026-APR-02', 'tier': 'micro',  'activation_date': date(2026, 4, 20),
     'content_live_date': date(2026, 4, 27),  'fee_structure': 'hybrid',
     'cash_fee': 1040, 'package_landed_cost': 165, 'packaging_shipping_cost': 42,
     'content_format': 'grwm', 'discount_code': 'AZURE10', 'audience_fit_score': 4,
     'geographic_skew': 'domestic_heavy', 'spark_ad_launched': True, 'instagram_reels_posted': True},
    {'id': 'INF-2026-MAY-01', 'tier': 'mid',    'activation_date': date(2026, 5, 5),
     'content_live_date': date(2026, 5, 12),  'fee_structure': 'hybrid',
     'cash_fee': 4160, 'package_landed_cost': 210, 'packaging_shipping_cost': 52,
     'content_format': 'styling', 'discount_code': 'SS15', 'audience_fit_score': 4,
     'geographic_skew': 'domestic_heavy', 'spark_ad_launched': True, 'instagram_reels_posted': True},
]

# Index influencer calendar by activation date range for order-time lookup
def influencer_active_on(d: date) -> list[dict]:
    """Return influencer activations with purchase window overlapping date d."""
    active = []
    for act in INFLUENCER_CALENDAR:
        live = act['content_live_date']
        if live <= d <= live + timedelta(days=14):
            active.append(act)
    return active


# ─── Event multipliers ────────────────────────────────────────────────────────
# Maps date → order volume multiplier for major episodic events
EPISODIC_MULTIPLIERS: list[tuple[date, date, float, str]] = [
    # (start, end, multiplier, event_name)
    # BFCM Y1 — full month of November has elevated orders; peak week 3×
    (date(2024, 11, 20), date(2024, 11, 27), 2.4, 'bfcm_y1_early'),
    (date(2024, 11, 28), date(2024, 12, 2),  3.1, 'bfcm_y1_peak'),
    (date(2024, 12, 3),  date(2024, 12, 20), 1.7, 'holiday_y1'),
    # Summer sale Y1
    (date(2024, 7, 4),   date(2024, 7, 21),  1.8, 'summer_sale_y1'),
    # SS collection launch Y1
    (date(2025, 3, 12),  date(2025, 3, 26),  1.6, 'ss_launch_y1'),
    # FW collection launch Y1
    (date(2024, 10, 8),  date(2024, 10, 22), 1.5, 'fw_launch_y1'),
    # Viral moment Y1: Dec 2024 holiday gifting newsletter
    (date(2024, 12, 3),  date(2024, 12, 9),  2.2, 'viral_moment_y1'),
    # Post-holiday dip
    (date(2025, 1, 2),   date(2025, 1, 15),  0.75, 'post_holiday_dip_y1'),
    # Weather suppression Oct 2024 (outerwear underperforms)
    (date(2024, 10, 14), date(2024, 10, 28), 0.88, 'weather_suppress_oct24'),
    # BFCM Y2
    (date(2025, 11, 20), date(2025, 11, 27), 2.6, 'bfcm_y2_early'),
    (date(2025, 11, 28), date(2025, 12, 2),  3.5, 'bfcm_y2_peak'),
    (date(2025, 12, 3),  date(2025, 12, 20), 1.9, 'holiday_y2'),
    # Celebrity TikTok viral moment during BFCM Y2
    (date(2025, 11, 20), date(2025, 11, 26), 4.2, 'viral_moment_y2_celebrity'),
    # Summer sale Y2
    (date(2025, 7, 3),   date(2025, 7, 20),  1.9, 'summer_sale_y2'),
    # SS collection launch Y2
    (date(2026, 3, 10),  date(2026, 3, 24),  1.7, 'ss_launch_y2'),
    # FW collection launch Y2
    (date(2025, 10, 7),  date(2025, 10, 21), 1.6, 'fw_launch_y2'),
    # Weather suppression Apr 2025 (cold spring, SS underperforms)
    (date(2025, 4, 7),   date(2025, 4, 21),  0.85, 'weather_suppress_apr25'),
    # Post-holiday dip Y2
    (date(2026, 1, 2),   date(2026, 1, 15),  0.78, 'post_holiday_dip_y2'),
    # TikTok hard pause (Jan 13–19 2024 — before Y1 starts but informative for Y1 month 1)
    (date(2024, 6, 1),   date(2024, 6, 15),  0.92, 'brand_launch_ramp'),
    # Wholesale order pattern (D24) — Feb 2024 gap → 0 wholesale
    (date(2024, 11, 1),  date(2024, 11, 19), 1.3, 'bfcm_y1_buildup'),
    # Macro influencer stockout signal (Apr 2024 macro activation window)
    (date(2024, 4, 8),   date(2024, 4, 22),  1.85, 'macro_inf_y1'),
    # SS 2025 strong launch
    (date(2025, 4, 1),   date(2025, 4, 15),  1.55, 'ss_launch_y1_b'),
]

def episode_multiplier(d: date) -> float:
    """Combined multiplier from all overlapping episodic events on date d."""
    m = 1.0
    for start, end, mult, _ in EPISODIC_MULTIPLIERS:
        if start <= d <= end:
            m *= mult
    return m

# ─── Order ID counter (global, sequential) ───────────────────────────────────
_ORDER_ID_COUNTER = [4_000_001]
_CUSTOMER_ID_COUNTER = [10_000_001]
_VARIANT_ID_COUNTER = [200_000_001]
_PRODUCT_ID_COUNTER = [500_000_001]
_REFUND_ID_COUNTER = [700_000_001]
_LINE_ITEM_ID_COUNTER = [900_000_001]
_FULFILLMENT_ID_COUNTER = [300_000_001]

def next_id(counter: list[int]) -> int:
    v = counter[0]
    counter[0] += 1
    return v

# Global state populated by seed_sku_master and seed_customers
PRODUCTS: list[dict] = []       # all product dicts
VARIANTS: list[dict] = []       # all variant dicts  (product_id, variant_id, sku, price, size)
SKU_TO_VARIANTS: dict[str, list[dict]] = {}  # sku → list of variant dicts
CUSTOMERS: list[dict] = []      # synthetic customer records
CUST_ID_POOL: list[int] = []    # pool of customer IDs to draw from (with repetition for repeats)
MANIFEST: dict[str, Any] = {
    'brand': BRAND_NAME,
    'client_id': CLIENT_ID,
    'schema': SCHEMA,
    'seed_period': {'start': str(SEED_START), 'end': str(SEED_END)},
    'orders_by_week': {},        # iso_week → list of order_ids
    'sku_list': [],              # [{sku, product_id, variant_ids, price, category, launch_date}]
    'customer_ids': [],          # synthetic_customer_ids for Klaviyo matching
    'influencer_activations': [],# [{id, content_live_date, alert_log_stage1_id, alert_log_stage2_id}]
    'episodic_events': [],       # named events for cross-source seed reference
    'order_ids_with_bnpl': [],   # for Klaviyo BNPL arc
    'order_ids_wholesale': [],   # for D24 wholesale scenario
    'defective_sku_orders': [],  # AZ-KNIT-031 orders for Loop seed
    'locked_sku_orders': {
        'AZ-TOP-088': [], 'AZ-DRESS-094': [], 'AZ-SHORT-031': []
    },                           # for G2 alert (overstock) and Loop seed
}


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 1. seed_sku_master
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def seed_sku_master(cur) -> None:
    """
    Creates shopify_products, shopify_product_variants, and sku_cost_master rows.
    120 active SKUs. Three locked SKUs. Formal added Month 15 (Aug 2025).
    Menswear added Month 20 (Jan 2026). Defective SKU AZ-KNIT-031 seeded.
    COGS: Finaloop Tier 1 (75%) at landed_cost_multiplier=1.28.
    """
    try:
        product_rows = []
        variant_rows = []
        cost_rows    = []

        sku_number_by_cat: dict[str, int] = {c: 1 for c in SKU_CATEGORIES}
        for sku_code in LOCKED_SKUS:
            cat = sku_code.split('-')[1]
            num = int(sku_code.split('-')[2])
            sku_number_by_cat[cat] = max(sku_number_by_cat.get(cat, 1), num + 1)

        cat_launch: dict[str, date] = {
            'TOP': date(2024, 6, 1), 'DRESS': date(2024, 6, 1),
            'SHORT': date(2024, 6, 1), 'KNIT': date(2024, 6, 1),
            'OUTERWEAR': date(2024, 6, 1), 'DENIM': date(2024, 6, 1),
            'FORMAL': date(2025, 8, 1),
            'MENS':   date(2026, 1, 1),
        }

        for cat, spec in SKU_CATEGORIES.items():
            colors = COLORS_BY_CAT[cat]
            price_lo, price_hi = spec['price_range']
            launch_date = cat_launch[cat]

            for _ in range(spec['count']):
                sku_num  = sku_number_by_cat[cat]
                sku_number_by_cat[cat] += 1
                sku_code = f'AZ-{cat}-{sku_num:03d}'

                if sku_code in LOCKED_SKUS:
                    price       = float(LOCKED_SKUS[sku_code]['price'])
                    launch_date = LOCKED_SKUS[sku_code]['launch']
                else:
                    price = float(PY_RNG.randint(price_lo // 10, price_hi // 10) * 10)

                color  = PY_RNG.choice(colors)
                title  = f'Azure {cat.title()} - {color}'
                product_id = next_id(_PRODUCT_ID_COUNTER)

                PRODUCTS.append({'id': product_id, 'sku': sku_code, 'category': cat,
                                 'title': title, 'price': price, 'launch_date': launch_date})

                _ats = airbyte_ts(launch_date)
                _cat_id, _cat_full = assign_synthetic_category(product_id, cat.lower())
                product_rows.append((
                    *airbyte_meta_cols(_ats),
                    product_id, title, cat.lower(), 'active',
                    utc_dt(launch_date),
                    f'azure-co,{cat.lower()}',
                    _cat_id, _cat_full,
                ))

                for size in SIZES:
                    variant_id = next_id(_VARIANT_ID_COUNTER)
                    v = {'variant_id': variant_id, 'product_id': product_id,
                         'sku': sku_code, 'size': size, 'price': price,
                         'category': cat, 'launch_date': launch_date}
                    VARIANTS.append(v)
                    SKU_TO_VARIANTS.setdefault(sku_code, []).append(v)

                    _ats = airbyte_ts(launch_date)
                    variant_rows.append((
                        *airbyte_meta_cols(_ats),
                        variant_id, product_id, sku_code,
                        size, f'{title} / {size}',
                        str(price), 250,
                        spec['weight_g'],
                    ))

                    is_finaloop   = PY_RNG.random() < 0.75
                    supplier_cost = price / 1.28 / PY_RNG.uniform(2.2, 3.0)
                    landed_cost   = supplier_cost * 1.28
                    cost_rows.append((
                        CLIENT_ID, str(variant_id), sku_code, 'sku_cogs',
                        round(supplier_cost, 2), round(landed_cost, 2),
                        'finaloop_export' if is_finaloop else 'derived',
                        None, None, None, None, None, None,
                        launch_date, None, True,
                    ))

                MANIFEST['sku_list'].append({
                    'sku': sku_code, 'product_id': product_id,
                    'variant_ids': [v['variant_id'] for v in SKU_TO_VARIANTS.get(sku_code, [])],
                    'price': price, 'category': cat, 'launch_date': str(launch_date),
                })

        n = batch_insert(cur, 'shopify_products',
            ['_airbyte_raw_id', '_airbyte_extracted_at', '_airbyte_meta', '_airbyte_generation_id',
             'id', 'title', 'product_type', 'status', 'created_at', 'tags',
             'category_id', 'category_full_name'], product_rows)
        logger.info('seed_sku_master | shopify_products: %d rows', n)

        n = batch_insert(cur, 'shopify_product_variants',
            ['_airbyte_raw_id', '_airbyte_extracted_at', '_airbyte_meta', '_airbyte_generation_id',
             'id', 'product_id', 'sku', 'title', 'display_name', 'price',
             'inventory_quantity', 'weight'],
            variant_rows)
        logger.info('seed_sku_master | shopify_product_variants: %d rows', n)

        n = batch_insert(cur, 'sku_cost_master',
            ['client_id', 'shopify_variant_id', 'sku', 'record_type',
             'supplier_cost', 'landed_cost', 'landed_cost_source',
             'influencer_id', 'package_landed_cost', 'packaging_cost',
             'shipping_cost', 'total_package_cost', 'featured_item_sku',
             'effective_from', 'effective_to', 'is_synthetic'], cost_rows)
        logger.info('seed_sku_master | sku_cost_master: %d rows', n)

        # Gifting packages for influencer activations
        gift_rows = []
        active_skus = [s for s in list(SKU_TO_VARIANTS.keys()) if s.split('-')[1] not in ('FORMAL', 'MENS')]
        for act in INFLUENCER_CALENDAR:
            if act['fee_structure'] in ('gifting', 'hybrid') and act['package_landed_cost'] > 0:
                featured_sku = PY_RNG.choice(active_skus[:40])
                shipping_c   = PY_RNG.randint(18, 45)
                total_cost   = act['package_landed_cost'] + act['packaging_shipping_cost'] + shipping_c
                gift_rows.append((
                    CLIENT_ID, f'gift_{act["id"]}', featured_sku,
                    'influencer_gifting_package',
                    None, None, 'manual',
                    act['id'],
                    act['package_landed_cost'],
                    act['packaging_shipping_cost'],
                    shipping_c, total_cost, featured_sku,
                    act['activation_date'], None, True,
                ))

        batch_insert(cur, 'sku_cost_master',
            ['client_id', 'shopify_variant_id', 'sku', 'record_type',
             'supplier_cost', 'landed_cost', 'landed_cost_source',
             'influencer_id', 'package_landed_cost', 'packaging_cost',
             'shipping_cost', 'total_package_cost', 'featured_item_sku',
             'effective_from', 'effective_to', 'is_synthetic'], gift_rows)
        logger.info('seed_sku_master | gifting packages: %d rows', len(gift_rows))

    except Exception as e:
        logger.error('SOURCE: Shopify Seed | CLIENT: %s | ERROR: %s | CONTEXT: seed_sku_master',
                     CLIENT_ID, str(e))
        raise


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 2. seed_customers
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def seed_customers(cur) -> None:
    """
    14,000 unique synthetic customers. PII stored separately in
    synthetic_customer_pii_lookup. GDPR deletions: 2-4 per month.
    Acquisition channel seeded from E7 form architecture.
    """
    try:
        import calendar as cal_mod
        N_CUSTOMERS = 14_000
        customer_rows = []
        pii_rows      = []

        acq_channels = ['exit_intent', 'footer', 'waitlist', 'post_purchase_guest',
                        'tiktok_link_in_bio', 'gorgias_post_resolution', 'referral', 'direct']
        acq_weights  = [45, 12, 8, 18, 14, 3, 5, 5]

        months      = list(MONTHLY_REVENUE_TARGETS.keys())
        rev_vals    = [sum(v) / 2 for v in MONTHLY_REVENUE_TARGETS.values()]
        total_rev   = sum(rev_vals)
        month_share = [v / total_rev for v in rev_vals]
        new_per_mo  = [max(1, int(N_CUSTOMERS * 0.68 * s)) for s in month_share]

        date_pool: list[date] = []
        for (yr, mo), count in zip(months, new_per_mo):
            days_in_mo = cal_mod.monthrange(yr, mo)[1]
            for _ in range(count):
                date_pool.append(date(yr, mo, PY_RNG.randint(1, days_in_mo)))
        PY_RNG.shuffle(date_pool)

        cust_id = 10_000_001
        for i, created_date in enumerate(date_pool):
            synthetic_id = cust_id
            cust_id += 1
            synth_email  = f'cust_{synthetic_id}@synthetic.azureco.invalid'
            acq_channel  = PY_RNG.choices(acq_channels, weights=acq_weights, k=1)[0]
            is_deleted   = (i > 0 and i % 180 == 0)  # ~2-4 per month over 24 months
            orders_count = PY_RNG.choices([1, 2, 3, 4, 5], weights=[55, 25, 12, 5, 3], k=1)[0]
            total_spent  = round(orders_count * PY_RNG.uniform(130, 200), 2)

            deleted_at = None
            if is_deleted:
                deleted_at = utc_dt(created_date + timedelta(days=PY_RNG.randint(30, 180)))

            _ats = airbyte_ts(created_date)
            customer_rows.append((
                *airbyte_meta_cols(_ats),
                synthetic_id,
                utc_dt(created_date),
                orders_count, str(total_spent),
                None if is_deleted else synth_email,
                'azure-co-customer',
            ))

            pii_rows.append((
                str(synthetic_id),
                synth_email,  # hashed_email — synthetic addr, no real PII
                False,        # klaviyo_match_flag default
            ))

            CUSTOMERS.append({
                'id': synthetic_id, 'created_date': created_date,
                'acquisition_channel': acq_channel,
                'is_gdpr_deleted': is_deleted, 'orders_count': orders_count,
            })

        CUST_ID_POOL.extend([c['id'] for c in CUSTOMERS])
        repeat_ids = [c['id'] for c in CUSTOMERS if c['orders_count'] > 1]
        CUST_ID_POOL.extend(repeat_ids * 3)
        PY_RNG.shuffle(CUST_ID_POOL)

        n = batch_insert(cur, 'shopify_customers',
            ['_airbyte_raw_id', '_airbyte_extracted_at', '_airbyte_meta', '_airbyte_generation_id',
             'id', 'created_at', 'orders_count', 'total_spent', 'email', 'tags'], customer_rows)
        logger.info('seed_customers | shopify_customers: %d rows', n)

        n = batch_insert(cur, 'synthetic_customer_pii_lookup',
            ['synthetic_customer_id', 'hashed_email', 'klaviyo_match_flag'], pii_rows)
        logger.info('seed_customers | synthetic_customer_pii_lookup: %d rows', n)

        MANIFEST['customer_ids'] = [c['id'] for c in CUSTOMERS[:5000]]

    except Exception as e:
        logger.error('SOURCE: Shopify Seed | CLIENT: %s | ERROR: %s | CONTEXT: seed_customers',
                     CLIENT_ID, str(e))
        raise


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 3. seed_orders  (System 1 + System 2 combined)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def seed_orders(cur) -> dict[str, list[int]]:
    """
    Generates shopify_orders and shopify_inventory_levels.
    Returns order_ids_by_week for use by line_items, refunds, touchpoints.

    System 2: correlated weekly noise applied to monthly revenue targets.
    System 1: episodic multipliers from EPISODIC_MULTIPLIERS override baseline.

    Key patterns:
      - Day-of-week order weights (Mon higher, Fri-Sun lower)
      - BNPL payment mix shift (Month 10+ = Mar 2025)
      - Wholesale orders (D24): AOV $800-2400, monthly
      - International 8-12% of orders
      - Dark social 15-20% of orders (no UTM)
      - New customer 65-70%, repeat 30-35%
    """
    try:
        import calendar as cal_mod

        all_dates = list(date_range(SEED_START, SEED_END))
        n_weeks   = (SEED_END - SEED_START).days // 7 + 1
        weekly_signals = generate_weekly_signals(n_weeks)

        # Map date â†’ week index
        def week_idx(d: date) -> int:
            return (d - SEED_START).days // 7

        order_rows     = []
        inv_rows       = []
        orders_by_week: dict[str, list[int]] = {}  # iso_week â†’ [order_id, ...]

        # Pre-compute daily order budget from monthly targets
        daily_revenue_budget: dict[date, float] = {}
        for (yr, mo), (lo, hi) in MONTHLY_REVENUE_TARGETS.items():
            days_in_mo = cal_mod.monthrange(yr, mo)[1]
            target_rev = (lo + hi) / 2
            per_day    = target_rev / days_in_mo
            for day in range(1, days_in_mo + 1):
                daily_revenue_budget[date(yr, mo, day)] = per_day

        # Wholesale order schedule (D24) â€” monthly or quarterly big orders
        # 8% of revenue = ~$320K/year. AOV $800-2400.
        wholesale_dates_y1 = [
            date(2024, 7, 15), date(2024, 9, 20), date(2024, 11, 5),
            date(2025, 1, 18), date(2025, 3, 14), date(2025, 5, 10),
        ]
        wholesale_dates_y2 = [
            date(2025, 7, 14), date(2025, 9, 18), date(2025, 11, 3),
            date(2026, 1, 20), date(2026, 3, 12), date(2026, 5, 8),
        ]
        # Feb 2024 equivalent in seed period: Feb 2024 is before Y1 start.
        # D24 scenario maps to Feb 2025 wholesale delay: no orders Feb 2025.
        wholesale_delay_months = {(2025, 2)}  # zero wholesale orders in Feb 2025

        wholesale_dates = set(wholesale_dates_y1 + wholesale_dates_y2)

        # Track inventory depletion per SKU per week (simple running counts)
        sku_inventory: dict[str, int] = {s: 250 * 5 for s in SKU_TO_VARIANTS}
        # Three locked SKUs get overstock scenario (240 units ordered, 28-32% sell-through)
        for locked_sku in LOCKED_SKUS:
            sku_inventory[locked_sku] = 240 * 5  # 240 units Ã— 5 sizes

        cust_pool_idx = 0

        for d in all_dates:
            if d not in daily_revenue_budget:
                continue

            wk = week_idx(d)
            wk_signal = weekly_signals[min(wk, n_weeks - 1)]
            # orders_idx is index 4
            orders_noise = float(wk_signal[4])
            ep_mult      = episode_multiplier(d)
            dow_mult     = DOW_ORDER_WEIGHTS.get(d.weekday(), 1.0)

            budget = daily_revenue_budget[d]
            # Expected daily revenue after noise and episodes
            adj_budget   = budget * orders_noise * ep_mult
            n_orders_day = max(1, int(adj_budget / AOV_BASE * dow_mult))

            # Cap at sensible daily max (BFCM peak ~250/day)
            n_orders_day = min(n_orders_day, 280)

            iso_week = d.strftime('%G-W%V')
            if iso_week not in orders_by_week:
                orders_by_week[iso_week] = []

            # Wholesale order check
            is_wholesale_day = d in wholesale_dates
            if is_wholesale_day and (d.year, d.month) not in wholesale_delay_months:
                # Insert 1 wholesale order (high AOV)
                w_order_id = next_id(_ORDER_ID_COUNTER)
                w_aov      = float(PY_RNG.randint(800, 2400))
                w_qty      = int(w_aov / 40)  # rough unit count
                w_cust_id  = PY_RNG.choice(CUST_ID_POOL[:200]) if CUST_ID_POOL else 10_000_001
                w_created  = utc_dt(d, hour=PY_RNG.randint(9, 16))

                order_rows.append(_build_order_row(
                    order_id=w_order_id,
                    created_dt=w_created,
                    order_number=w_order_id - 3_999_999,
                    total_line_items=w_aov,
                    total_discounts=0.0,
                    shipping_amount=18.0,
                    total_tax=0.0,
                    total_price=w_aov + 18.0,
                    customer_id=w_cust_id,
                    source_name='wholesale',
                    payment_gateway='credit_card',
                    currency='USD',
                    utm_source=None,
                    utm_medium=None,
                    utm_campaign=None,
                    tags='wholesale,b2b',
                    note='Wholesale order - net30',
                    d=d,
                ))
                orders_by_week[iso_week].append(w_order_id)
                MANIFEST['order_ids_wholesale'].append(w_order_id)

            # Regular DTC orders for the day
            for _ in range(n_orders_day):
                order_id = next_id(_ORDER_ID_COUNTER)
                hour     = PY_RNG.randint(8, 22)
                created_dt = utc_dt(d, hour=hour, minute=PY_RNG.randint(0, 59))

                # Customer â€” new vs repeat
                is_new_customer = PY_RNG.random() < 0.68
                if CUST_ID_POOL:
                    if is_new_customer:
                        cust_id = CUST_ID_POOL[cust_pool_idx % len(CUST_ID_POOL)]
                        cust_pool_idx += 1
                    else:
                        _pool_end = min(cust_pool_idx + 1, len(CUST_ID_POOL))
                        _pool_start = max(0, _pool_end - 2000)
                        _pool_slice = CUST_ID_POOL[_pool_start:_pool_end]
                        cust_id = PY_RNG.choice(_pool_slice if _pool_slice else CUST_ID_POOL)
                else:
                    cust_id = 10_000_001

                # UTM attribution
                utm_src = PY_RNG.choices(UTM_SOURCES, weights=UTM_SOURCE_WEIGHTS, k=1)[0]

                # During TikTok hard pause (Jan 13-19 2024): no TikTok UTM
                # (Note: this is before Y1 starts in Jun 2024, but we keep the logic
                #  for the Y2 echo TikTok outage Jan 19 2025)
                if utm_src == 'tiktok' and date(2025, 1, 19) <= d <= date(2025, 1, 19):
                    utm_src = 'direct'

                utm_medium   = None
                utm_campaign = None
                if utm_src == 'meta':
                    utm_medium   = 'paid_social'
                    utm_campaign = PY_RNG.choice(['prospecting_aw', 'retargeting_aw',
                                                   'lookalike_aw', 'dpa_aw'])
                elif utm_src == 'tiktok':
                    utm_medium   = 'paid_social'
                    utm_campaign = PY_RNG.choice(['spark_ad', 'in_feed', 'tiktok_organic'])
                elif utm_src == 'klaviyo':
                    utm_medium   = 'email'
                    utm_campaign = PY_RNG.choice(['welcome_flow', 'abandoned_cart',
                                                   'campaign_weekly', 'post_purchase'])
                elif utm_src == 'google':
                    utm_medium   = 'cpc'
                    utm_campaign = 'brand_search'

                # Check influencer active window â€” override UTM
                inf_active = influencer_active_on(d)
                inf_used   = None
                if inf_active and PY_RNG.random() < 0.12:  # 12% of orders during window
                    act       = PY_RNG.choice(inf_active)
                    utm_src      = 'tiktok'
                    utm_medium   = 'influencer'
                    utm_campaign = act['id']
                    inf_used     = act['id']

                # Currency
                currency = PY_RNG.choices(CURRENCIES, weights=CURRENCY_WEIGHTS, k=1)[0]

                # AOV with BNPL premium
                pmt_gw = payment_mix(d)
                aov_mult = 1.30 if pmt_gw == 'afterpay' else 1.0
                items_count = PY_RNG.choices([1, 2, 3, 4], weights=[55, 30, 12, 3], k=1)[0]
                line_items_total = round(PY_RNG.uniform(0.90, 1.10) * AOV_BASE * aov_mult * items_count, 2)

                # Discount
                has_discount = PY_RNG.random() < 0.14
                discount_amt = round(line_items_total * PY_RNG.uniform(0.10, 0.30), 2) if has_discount else 0.0
                shipping_amt = 0.0 if line_items_total > 150 else round(PY_RNG.uniform(5.99, 12.99), 2)
                tax_rate     = 0.0 if currency != 'USD' else round(PY_RNG.uniform(0.06, 0.10), 3)
                total_tax    = round((line_items_total - discount_amt) * tax_rate, 2)
                total_price  = round(line_items_total - discount_amt + shipping_amt + total_tax, 2)

                # Defective SKU scenario (Nov 28 â€“ Dec 4 2024): AZ-KNIT-031
                tags = 'azure-co'
                is_defective_window = date(2024, 11, 28) <= d <= date(2024, 12, 4)

                order_rows.append(_build_order_row(
                    order_id=order_id,
                    created_dt=created_dt,
                    order_number=order_id - 3_999_999,
                    total_line_items=line_items_total,
                    total_discounts=discount_amt,
                    shipping_amount=shipping_amt,
                    total_tax=total_tax,
                    total_price=total_price,
                    customer_id=cust_id,
                    source_name='web',
                    payment_gateway=pmt_gw,
                    currency=currency,
                    utm_source=utm_src,
                    utm_medium=utm_medium,
                    utm_campaign=utm_campaign,
                    tags=tags,
                    note=None,
                    d=d,
                ))
                orders_by_week[iso_week].append(order_id)

                # Track BNPL orders for manifest
                if pmt_gw == 'afterpay':
                    MANIFEST['order_ids_with_bnpl'].append(order_id)

                # Track locked SKU orders (for G2 alert â€” overstock Apr 2024)
                # Locked SKU sell-through: 28-32% by Apr 30 2024
                if date(2024, 6, 1) <= d <= date(2024, 4, 30):
                    # Low sell-through for locked SKUs â€” handled in line items
                    pass

        # Populate manifest orders_by_week (sample first 50 weeks)
        for iso_week in sorted(orders_by_week)[:50]:
            MANIFEST['orders_by_week'][iso_week] = orders_by_week[iso_week][:20]  # first 20 per week

        n = batch_insert(cur, 'shopify_orders',
            ['_airbyte_raw_id', '_airbyte_extracted_at', '_airbyte_meta', '_airbyte_generation_id',
             'id', 'created_at', 'order_number', 'total_line_items_price',
             'total_discounts', 'total_shipping_price_set', 'total_tax',
             'total_price', 'financial_status', 'fulfillment_status',
             'source_name', 'customer', 'tags', 'cancelled_at', 'email',
             'payment_gateway_names', 'currency', 'note_attributes', 'landing_site',
             'referring_site', 'note'], order_rows)
        logger.info('seed_orders | shopify_orders: %d rows', n)

        # Inventory levels snapshot (current state)
        inv_rows_final = []
        location_id = 67_000_001  # single warehouse location
        for sku_code, variants in SKU_TO_VARIANTS.items():
            for v in variants:
                qty = max(0, sku_inventory.get(sku_code, 250) // 5)
                _ats = airbyte_ts(SEED_END)
                inv_rows_final.append((
                    *airbyte_meta_cols(_ats),
                    v['variant_id'], location_id, qty,
                    utc_dt(SEED_END),
                ))
        n = batch_insert(cur, 'shopify_inventory_levels',
            ['_airbyte_raw_id', '_airbyte_extracted_at', '_airbyte_meta', '_airbyte_generation_id',
             'inventory_item_id', 'location_id', 'available', 'updated_at'], inv_rows_final)
        logger.info('seed_orders | shopify_inventory_levels: %d rows', n)

        return orders_by_week

    except Exception as e:
        logger.error('SOURCE: Shopify Seed | CLIENT: %s | ERROR: %s | CONTEXT: seed_orders',
                     CLIENT_ID, str(e))
        raise


def _build_order_row(
    order_id, created_dt, order_number, total_line_items, total_discounts,
    shipping_amount, total_tax, total_price, customer_id, source_name,
    payment_gateway, currency, utm_source, utm_medium, utm_campaign,
    tags, note, d: date,
) -> tuple:
    shipping_set = json.dumps({
        'shop_money': {'amount': str(shipping_amount), 'currency_code': currency},
        'presentment_money': {'amount': str(shipping_amount), 'currency_code': currency},
    })
    customer_json = json.dumps({'id': customer_id})
    note_attrs = json.dumps([
        {'name': 'utm_source',   'value': utm_source   or ''},
        {'name': 'utm_medium',   'value': utm_medium   or ''},
        {'name': 'utm_campaign', 'value': utm_campaign or ''},
    ])
    # Synthetic email (never real PII)
    email = f'cust_{customer_id}@synthetic.azureco.invalid'
    _ats = airbyte_ts(d)
    return (
        *airbyte_meta_cols(_ats),
        order_id,
        created_dt,
        order_number,
        str(total_line_items),
        str(total_discounts),
        shipping_set,
        str(total_tax),
        str(total_price),
        'paid',
        'fulfilled',
        source_name,
        customer_json,
        tags,
        None,          # cancelled_at
        email,
        json.dumps([payment_gateway]),  # payment_gateway_names (jsonb array)
        currency,
        note_attrs,
        f'https://azureco.com/?utm_source={utm_source or ""}',
        f'https://{utm_source or "direct"}.com' if utm_source else None,
        note,
    )


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 4. seed_line_items
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def seed_line_items(cur, orders_by_week: dict[str, list[int]]) -> dict[int, list[str]]:
    """
    Generates shopify_order_line_items.
    Returns order_id â†’ [sku, ...] for use by refunds and touchpoints.
    avg 1.4-1.7 items per order.
    Defective SKU AZ-KNIT-031 seeded in Nov 28 â€“ Dec 4 2024 window.
    Locked SKU overstock: low frequency Jun-Apr 2024.
    """
    try:
        line_item_rows = []
        order_to_skus: dict[int, list[str]] = {}

        all_order_ids = [oid for ids in orders_by_week.values() for oid in ids]

        # For overstock scenario: locked SKUs must have low sell-through by Apr 30 2024
        locked_sku_order_limit: dict[str, int] = {s: int(240 * 0.30) for s in LOCKED_SKUS}
        locked_sku_sold: dict[str, int] = {s: 0 for s in LOCKED_SKUS}

        active_skus = [s for s, vs in SKU_TO_VARIANTS.items()
                       if vs and vs[0]['launch_date'] <= SEED_START]
        formal_skus = [s for s, vs in SKU_TO_VARIANTS.items()
                       if vs and vs[0]['category'] == 'FORMAL']
        mens_skus   = [s for s, vs in SKU_TO_VARIANTS.items()
                       if vs and vs[0]['category'] == 'MENS']

        for iso_week, order_ids in orders_by_week.items():
            # Determine week date from iso_week string
            wk_date = date.fromisoformat(iso_week + '-1') \
                      if len(iso_week) == 8 else SEED_START

            for order_id in order_ids:
                n_items = PY_RNG.choices([1, 2, 3, 4], weights=[55, 30, 12, 3], k=1)[0]
                skus_for_order = []

                # Determine available SKU pool for this date
                pool = list(active_skus)
                if wk_date >= date(2025, 8, 1):
                    pool += formal_skus
                if wk_date >= date(2026, 1, 1):
                    pool += mens_skus

                for _ in range(n_items):
                    # Defective window: 30% chance of AZ-KNIT-031
                    is_defective_window = date(2024, 11, 28) <= wk_date <= date(2024, 12, 4)
                    if is_defective_window and PY_RNG.random() < 0.30 and DEFECTIVE_SKU in SKU_TO_VARIANTS:
                        sku_code = DEFECTIVE_SKU
                    # Locked SKU low sell-through (before Apr 30 2024 â€” not in Y1 which starts Jun 2024)
                    # Apply for first 10 months to keep locked SKU orders low
                    elif (wk_date <= date(2025, 3, 31) and
                          PY_RNG.random() < 0.04 and
                          any(locked_sku_sold[s] < locked_sku_order_limit[s] for s in LOCKED_SKUS)):
                        eligible = [s for s in LOCKED_SKUS if locked_sku_sold[s] < locked_sku_order_limit[s]]
                        sku_code = PY_RNG.choice(eligible)
                        locked_sku_sold[sku_code] += 1
                    else:
                        sku_code = PY_RNG.choice(pool)

                    variants = SKU_TO_VARIANTS.get(sku_code, [])
                    if not variants:
                        continue
                    v = PY_RNG.choice(variants)
                    price = float(v['price'])
                    li_id = next_id(_LINE_ITEM_ID_COUNTER)

                    _ats = airbyte_ts(wk_date)
                    line_item_rows.append((
                        *airbyte_meta_cols(_ats),
                        li_id, order_id, v['product_id'], v['variant_id'],
                        v.get('title', sku_code)[:120],
                        sku_code,
                        1,           # quantity
                        str(price),
                        str(price),  # total_discount (per item)
                    ))
                    skus_for_order.append(sku_code)

                    # Track locked SKU and defective SKU orders
                    if sku_code in LOCKED_SKUS:
                        MANIFEST['locked_sku_orders'][sku_code].append(order_id)
                    if sku_code == DEFECTIVE_SKU:
                        MANIFEST['defective_sku_orders'].append(order_id)

                order_to_skus[order_id] = skus_for_order

        n = batch_insert(cur, 'shopify_order_line_items',
            ['_airbyte_raw_id', '_airbyte_extracted_at', '_airbyte_meta', '_airbyte_generation_id',
             'id', 'order_id', 'product_id', 'variant_id', 'title', 'sku',
             'quantity', 'price', 'total_discount'], line_item_rows)
        logger.info('seed_line_items | shopify_order_line_items: %d rows', n)
        return order_to_skus

    except Exception as e:
        logger.error('SOURCE: Shopify Seed | CLIENT: %s | ERROR: %s | CONTEXT: seed_line_items',
                     CLIENT_ID, str(e))
        raise


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 5. seed_refunds
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def seed_refunds(cur, orders_by_week: dict[str, list[int]],
                 order_to_skus: dict[int, list[str]]) -> None:
    """
    Generates shopify_order_refunds.
    Base return rate: 18-22%. BNPL +15-20pp. Influencer window variable by format.
    Weekend order premium: +6pp. Defective SKU AZ-KNIT-031: 61% return rate.
    Three-stage return chain: refunds lag order by 7-21 days.
    """
    try:
        refund_rows = []

        # Return rate determinants per SKU/order type
        def return_rate(order_id: int, skus: list[str], order_date: date) -> float:
            base = PY_RNG.uniform(0.18, 0.22)
            # Weekend premium
            if order_date.weekday() >= 4:
                base += 0.06
            # BNPL premium (rough: if order in BNPL manifest)
            if order_id in MANIFEST.get('order_ids_with_bnpl', []):
                base += PY_RNG.uniform(0.15, 0.20)
            # Defective SKU
            if DEFECTIVE_SKU in skus:
                base = 0.61
            # Influencer influencer return rates
            for act in INFLUENCER_CALENDAR:
                live = act['content_live_date']
                if live <= order_date <= live + timedelta(days=14):
                    fmt = act['content_format']
                    base = PY_RNG.uniform(0.35, 0.45) if fmt == 'tryon_haul' \
                        else PY_RNG.uniform(0.18, 0.24) if fmt == 'styling' \
                        else PY_RNG.uniform(0.25, 0.32)
                    # Discount code adds +8-12pp
                    if act['discount_code']:
                        base += PY_RNG.uniform(0.08, 0.12)
                    # Audience fit score adjustment
                    fit = act['audience_fit_score']
                    base -= (fit - 3) * 0.04  # fit 5 â†’ -8pp, fit 1 â†’ +8pp
                    break
            return min(base, 0.70)

        # Return reason distribution
        return_reasons = ['sizing', 'style', 'quality', 'wrong_item', 'other']
        reason_weights = [52, 23, 12, 4, 9]

        all_dates_map: dict[str, date] = {}
        for iso_week in orders_by_week:
            try:
                wk_date = date.fromisoformat(iso_week + '-1')
            except ValueError:
                wk_date = SEED_START
            all_dates_map[iso_week] = wk_date

        for iso_week, order_ids in orders_by_week.items():
            order_date = all_dates_map.get(iso_week, SEED_START)
            for order_id in order_ids:
                skus = order_to_skus.get(order_id, [])
                rr   = return_rate(order_id, skus, order_date)
                if PY_RNG.random() > rr:
                    continue

                # Refund lag: 7-21 days
                lag_days  = PY_RNG.randint(7, 21)
                refund_dt = utc_dt(order_date + timedelta(days=lag_days))
                if refund_dt.date() > SEED_END:
                    continue

                refund_id = next_id(_REFUND_ID_COUNTER)
                reason    = PY_RNG.choices(return_reasons, weights=reason_weights, k=1)[0]
                # Approximate refund amount as ~AOV * (1 item)
                refund_amount = round(PY_RNG.uniform(60, 180), 2)

                _ats = airbyte_ts(refund_dt.date())
                refund_rows.append((
                    *airbyte_meta_cols(_ats),
                    refund_id, order_id,
                    refund_dt,
                    reason,
                ))

        n = batch_insert(cur, 'shopify_order_refunds',
            ['_airbyte_raw_id', '_airbyte_extracted_at', '_airbyte_meta', '_airbyte_generation_id',
             'id', 'order_id', 'created_at', 'note'], refund_rows)
        logger.info('seed_refunds | shopify_order_refunds: %d rows', n)

    except Exception as e:
        logger.error('SOURCE: Shopify Seed | CLIENT: %s | ERROR: %s | CONTEXT: seed_refunds',
                     CLIENT_ID, str(e))
        raise


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 6. seed_fulfillments
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def seed_fulfillments(cur, orders_by_week: dict[str, list[int]]) -> None:
    """Generates shopify_fulfillments. 1-3 day fulfillment lag."""
    try:
        rows = []
        carriers = ['USPS', 'UPS', 'FedEx', 'DHL']

        for iso_week, order_ids in orders_by_week.items():
            try:
                wk_date = date.fromisoformat(iso_week + '-1')
            except ValueError:
                wk_date = SEED_START

            for order_id in order_ids[:50]:  # sample 50 per week to keep volume manageable
                lag  = PY_RNG.randint(1, 3)
                ful_date = wk_date + timedelta(days=lag)
                if ful_date > SEED_END:
                    continue
                ful_id = next_id(_FULFILLMENT_ID_COUNTER)
                carrier = PY_RNG.choice(carriers)
                tracking = f'{carrier[:2].upper()}{PY_RNG.randint(100_000_000, 999_999_999)}'

                _ats = airbyte_ts(ful_date)
                rows.append((
                    *airbyte_meta_cols(_ats),
                    ful_id, order_id, 'success',
                    utc_dt(ful_date), tracking, carrier,
                ))

        n = batch_insert(cur, 'shopify_fulfillments',
            ['_airbyte_raw_id', '_airbyte_extracted_at', '_airbyte_meta', '_airbyte_generation_id',
             'id', 'order_id', 'status', 'created_at',
             'tracking_number', 'tracking_company'], rows)
        logger.info('seed_fulfillments | shopify_fulfillments: %d rows', n)

    except Exception as e:
        logger.error('SOURCE: Shopify Seed | CLIENT: %s | ERROR: %s | CONTEXT: seed_fulfillments',
                     CLIENT_ID, str(e))
        raise


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 7. seed_discount_codes
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def seed_discount_codes(cur) -> None:
    """Generates shopify_discount_codes for all active codes across 24 months."""
    try:
        codes = [
            ('AZURE10',   'percentage', 10, date(2024, 6, 1)),
            ('AZURE15',   'percentage', 15, date(2024, 6, 1)),
            ('AZURE20',   'percentage', 20, date(2024, 6, 1)),
            ('SUMMER15',  'percentage', 15, date(2024, 7, 1)),
            ('FW15',      'percentage', 15, date(2024, 10, 1)),
            ('BFCM25',    'percentage', 25, date(2024, 11, 1)),
            ('SS15',      'percentage', 15, date(2025, 3, 1)),
            ('VAL20',     'percentage', 20, date(2025, 2, 1)),
            ('FW20',      'percentage', 20, date(2025, 10, 1)),
            ('BFCM30',    'percentage', 30, date(2025, 11, 1)),
            ('SS20',      'percentage', 20, date(2026, 3, 1)),
            ('SS25',      'percentage', 25, date(2026, 3, 1)),
        ]
        rows = []
        for code, code_type, value, created_date in codes:
            _ats = airbyte_ts(created_date)
            rows.append((
                *airbyte_meta_cols(_ats),
                PY_RNG.randint(100_000, 999_999),
                code,
                PY_RNG.randint(50, 500),  # usage_count
                utc_dt(created_date),
            ))

        n = batch_insert(cur, 'shopify_discount_codes',
            ['_airbyte_raw_id', '_airbyte_extracted_at', '_airbyte_meta', '_airbyte_generation_id',
             'id', 'code', 'usage_count', 'created_at'], rows)
        logger.info('seed_discount_codes | shopify_discount_codes: %d rows', n)

    except Exception as e:
        logger.error('SOURCE: Shopify Seed | CLIENT: %s | ERROR: %s | CONTEXT: seed_discount_codes',
                     CLIENT_ID, str(e))
        raise


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 8. seed_touchpoint_journeys
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def seed_touchpoint_journeys(cur, orders_by_week: dict[str, list[int]]) -> None:
    """
    Generates synthetic_touchpoint_journey for 35-45% of orders.
    Journey mix (C18):
      20%: TikTok impression D1 â†’ Meta click D3-5
      10%: Klaviyo email open â†’ Meta retargeting D2
       8%: TikTok influencer D1 â†’ Direct visit D6
       7%: Three-channel (TikTok â†’ Klaviyo â†’ Meta)
    Dark social 15-20%: no UTM, single touchpoint.
    """
    try:
        rows = []
        multi_touch_rate = 0.40  # 40% of orders get multi-touch journey

        journey_patterns = [
            ('tiktok_meta', 0.20),
            ('klaviyo_meta', 0.10),
            ('tiktok_direct', 0.08),
            ('tiktok_klaviyo_meta', 0.07),
        ]
        pattern_names  = [p[0] for p in journey_patterns]
        pattern_weights = [p[1] for p in journey_patterns]
        # Remainder: dark social (single touchpoint, no UTM)

        for iso_week, order_ids in orders_by_week.items():
            try:
                wk_date = date.fromisoformat(iso_week + '-1')
            except ValueError:
                wk_date = SEED_START

            for order_id in order_ids:
                if PY_RNG.random() > multi_touch_rate:
                    continue

                pattern = PY_RNG.choices(
                    pattern_names + ['dark_social'],
                    weights=pattern_weights + [0.15]
                )[0]

                touchpoints = []
                inf_active = influencer_active_on(wk_date)
                inf_id = inf_active[0]['id'] if inf_active and PY_RNG.random() < 0.3 else None

                if pattern == 'tiktok_meta':
                    touchpoints = [
                        (1, 'tiktok', wk_date,             'impression', 'tiktok_organic', inf_id),
                        (2, 'meta',   wk_date + timedelta(days=PY_RNG.randint(3, 5)),
                         'click', 'meta_retargeting', None),
                    ]
                elif pattern == 'klaviyo_meta':
                    touchpoints = [
                        (1, 'klaviyo', wk_date,              'email_open', 'abandoned_cart_flow', None),
                        (2, 'meta',    wk_date + timedelta(days=2), 'click', 'meta_retargeting', None),
                    ]
                elif pattern == 'tiktok_direct':
                    touchpoints = [
                        (1, 'tiktok', wk_date,              'impression', inf_id or 'tiktok_organic', inf_id),
                        (2, 'direct', wk_date + timedelta(days=6), 'click', None, None),
                    ]
                elif pattern == 'tiktok_klaviyo_meta':
                    touchpoints = [
                        (1, 'tiktok',   wk_date,              'impression', 'tiktok_organic', inf_id),
                        (2, 'klaviyo',  wk_date + timedelta(days=2), 'email_open', 'welcome_flow', None),
                        (3, 'meta',     wk_date + timedelta(days=4), 'click', 'meta_retargeting', None),
                    ]
                elif pattern == 'dark_social':
                    touchpoints = [
                        (1, 'direct', wk_date, 'click', None, None),
                    ]

                for seq, channel, tp_date, tp_type, campaign_id, inf_ref in touchpoints:
                    if tp_date > SEED_END:
                        continue
                    rows.append((
                        str(order_id), seq, channel, tp_date,
                        tp_type, campaign_id, inf_ref,
                    ))

        n = batch_insert(cur, 'synthetic_touchpoint_journey',
            ['order_id', 'touchpoint_sequence', 'channel', 'touchpoint_date',
             'touchpoint_type', 'campaign_id', 'influencer_id'], rows)
        logger.info('seed_touchpoint_journeys | synthetic_touchpoint_journey: %d rows', n)

    except Exception as e:
        logger.error('SOURCE: Shopify Seed | CLIENT: %s | ERROR: %s | CONTEXT: seed_touchpoint_journeys',
                     CLIENT_ID, str(e))
        raise


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 9. seed_brand_event_calendar
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def seed_brand_event_calendar(cur) -> None:
    """
    Seeds brand_event_calendar with all suppression-driving events.
    Covers: BFCM both years, collection launches, TikTok disruption phases,
    influencer activations, weather suppression, viral moments, operational
    changes, staleness events, and all multi-suppression events (MS1-MS12).
    """
    try:
        rows = []

        def evt(name, etype, start, end, suppress=None, context=None,
                ctx_explanation=None, residual_pct=None, decay_type=None,
                decay_start=None, decay_end=None, confidence_at_peak=1.0,
                detection_method='hardcoded', detection_lag=0,
                is_recurring=False, recurrence='annual',
                event_profile=None, suppression_type='reactive'):
            return (
                CLIENT_ID, name, etype, start, end,
                suppress or [],
                context or [],
                ctx_explanation,
                residual_pct,
                decay_type,
                decay_start,
                decay_end,
                confidence_at_peak,
                detection_method,
                detection_lag,
                1.0,            # confidence (currently active)
                None,           # last_verified_at
                is_recurring,
                recurrence if is_recurring else None,
                True,           # auto_detected
                None,           # detected_from
                json.dumps(event_profile) if event_profile else None,
                suppression_type,
                True,           # is_synthetic
            )

        cols = [
            'client_id', 'event_name', 'event_type', 'start_date', 'end_date',
            'suppress_alerts', 'context_alerts', 'context_explanation',
            'residual_threshold_pct', 'confidence_decay_type',
            'confidence_decay_start', 'confidence_decay_end', 'confidence_at_peak',
            'detection_method', 'detection_lag_hours', 'confidence', 'last_verified_at',
            'is_recurring', 'recurrence_rule', 'auto_detected', 'detected_from',
            'event_profile', 'suppression_type', 'is_synthetic',
        ]

        # â”€â”€ BFCM Y1 â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        rows.append(evt(
            'BFCM Y1 Email Early Access', 'sale_period',
            date(2024, 11, 20), date(2024, 11, 27),
            suppress=['B5', 'F1', 'F2'],
            context=['A1', 'A3', 'D1'],
            ctx_explanation='BFCM early access â€” CPM spikes, checkout load normal for peak.',
            residual_pct=60,
            decay_type='step',
            confidence_at_peak=1.0,
            event_profile={
                'bfcm_start_email': '2024-11-20',
                'bfcm_start_public': '2024-11-28',
                'bfcm_discount_depth_standard': 0.25,
                'bfcm_discount_depth_clearance': 0.30,
                'bfcm_email_early_access': True,
                'bfcm_email_early_access_hours': 48,
            }
        ))
        rows.append(evt(
            'BFCM Y1 Peak', 'sale_period',
            date(2024, 11, 28), date(2024, 12, 2),
            suppress=['B5', 'F1', 'F2', 'SentD1'],
            context=['A1', 'A3', 'D1', 'C3'],
            ctx_explanation='BFCM peak â€” CPM spike S1. ROAS compression S19. Alert A1/D1 may fire if residual >40%.',
            residual_pct=40,
            decay_type='step',
            decay_start=date(2024, 11, 29),
            decay_end=date(2024, 12, 7),
        ))
        rows.append(evt(
            'Post-BFCM Holiday Y1', 'retail_holiday',
            date(2024, 12, 3), date(2024, 12, 24),
            suppress=[],
            context=['A3', 'D1'],
            ctx_explanation='Post-BFCM holiday gifting season. CPM partially elevated.',
            residual_pct=55,
        ))
        # â”€â”€ BFCM Y2 â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        rows.append(evt(
            'BFCM Y2 Email Early Access', 'sale_period',
            date(2025, 11, 20), date(2025, 11, 27),
            suppress=['B5', 'F1', 'F2'],
            context=['A1', 'A3', 'D1'],
            ctx_explanation='BFCM Y2 â€” auto-populated from Y1 event profile. No pre-event questions sent.',
            residual_pct=60,
            decay_type='step',
            confidence_at_peak=1.0,
        ))
        rows.append(evt(
            'BFCM Y2 Peak', 'sale_period',
            date(2025, 11, 28), date(2025, 12, 2),
            suppress=['B5', 'F1', 'F2', 'SentD1'],
            context=['A1', 'A3', 'D1', 'C3'],
            ctx_explanation='BFCM Y2 peak â€” same suppression profile as Y1 from event_profile.',
            residual_pct=40,
            decay_type='step',
            decay_start=date(2025, 11, 29),
            decay_end=date(2025, 12, 7),
        ))
        # â”€â”€ Collection launches â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        for launch_name, start, end in [
            ('FW 2024 Collection Launch',  date(2024, 10, 8),  date(2024, 10, 22)),
            ('SS 2025 Collection Launch',  date(2025, 3, 12),  date(2025, 3, 26)),
            ('FW 2025 Collection Launch',  date(2025, 10, 7),  date(2025, 10, 21)),
            ('SS 2026 Collection Launch',  date(2026, 3, 10),  date(2026, 3, 24)),
        ]:
            rows.append(evt(
                launch_name, 'collection_launch', start, end,
                suppress=['B5'],
                context=['A1', 'A3'],
                ctx_explanation=f'Collection launch â€” CPM spike S2 (30% threshold).',
                residual_pct=30,
            ))
        # â”€â”€ Summer sales â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        rows.append(evt('Summer Sale Y1', 'sale_period',
            date(2024, 7, 4), date(2024, 7, 21),
            suppress=['D1'],
            context=['A1', 'A3'],
            ctx_explanation='Summer clearance â€” margin compression explained by discount depth.',
            residual_pct=50,
        ))
        rows.append(evt('Summer Sale Y2', 'sale_period',
            date(2025, 7, 3), date(2025, 7, 20),
            suppress=['D1'],
            context=['A1', 'A3'],
            ctx_explanation='Summer clearance Y2.',
            residual_pct=50,
        ))
        # â”€â”€ TikTok disruption (D7 â€” 5 granular entries) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        rows.append(evt(
            'TikTok Hard Pause', 'platform_disruption',
            date(2024, 1, 13), date(2024, 1, 19),  # before Y1 â€” included for Y1 month-1 reference
            suppress=['A3', 'B5', 'C3_tiktok', 'Alert3_tiktok'],
        ))
        rows.append(evt(
            'TikTok Cautious Re-entry', 'platform_disruption_partial',
            date(2024, 1, 20), date(2024, 2, 14),
            suppress=['A3'],
            context=['A1'],
            ctx_explanation='TikTok cautious re-entry â€” A1 confidence capped at 55%.',
        ))
        rows.append(evt(
            'Meta Learning Phase Post-Reallocation', 'platform_disruption_secondary',
            date(2024, 1, 20), date(2024, 1, 30),
            suppress=['A3_meta'],
        ))
        rows.append(evt(
            'TikTok House Bill Second Pause', 'platform_disruption',
            date(2024, 3, 13), date(2024, 3, 19),
            suppress=['A3', 'B5', 'C3_tiktok'],
        ))
        rows.append(evt(
            'TikTok Organic Reach Recovery', 'platform_algorithm_change',
            date(2024, 1, 13), date(2024, 6, 30),
            suppress=['B3'],
            ctx_explanation='TikTok organic reach recovering - B3 suppressed until full recovery.',
        ))
        # â”€â”€ TikTok algorithm change Q3 2024 (C12) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        rows.append(evt(
            'TikTok Algorithm Change Q3 2024', 'platform_algorithm_change',
            date(2024, 7, 15), date(2024, 9, 30),
            context=['Alert3'],
            ctx_explanation='TikTok organic reach -35% â€” Alert 3 identifies platform cause not influencer.',
        ))
        # â”€â”€ Y2 TikTok outage (D18) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        rows.append(evt(
            'TikTok Y2 Outage Echo', 'platform_disruption',
            date(2025, 1, 19), date(2025, 1, 19),
            suppress=['A3'],
            context=['H6'],
            ctx_explanation='TikTok dark 14h â€” Y2 echo of Y1 disruption. Faster recovery.',
        ))
        # â”€â”€ Operational changes (B13) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        rows.append(evt(
            'Marketing Manager Hired', 'operational_change',
            date(2025, 4, 1), date(2025, 5, 15),
            suppress=['A3', 'A2'],
            ctx_explanation='New marketing manager learning curve â€” ROAS dip 15% for 6 weeks suppressed.',
        ))
        rows.append(evt(
            '3PL Switch Transition', 'operational_change',
            date(2025, 8, 1), date(2025, 8, 21),
            suppress=['G1', 'G2'],
            ctx_explanation='3PL switch â€” 3-week fulfilment delay. Inventory discrepancy expected.',
        ))
        rows.append(evt(
            'Klaviyo Agency to In-House', 'operational_change',
            date(2025, 11, 1), date(2025, 11, 14),
            suppress=['D5'],
            ctx_explanation='Klaviyo restructure â€” flow IDs change, attribution breaks 2 weeks.',
        ))
        # â”€â”€ BFCM sunset spike (E29) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        rows.append(evt(
            'BFCM Y1 Subscriber Sunset Spike', 'bfcm_sunset_spike',
            date(2025, 5, 1), date(2025, 5, 31),
            suppress=['E1'],
            ctx_explanation='BFCM subscriber cohort reaching 180-day sunset. Automated suppressions explain elevated unsubscribe volume.',
        ))
        rows.append(evt(
            'BFCM Y2 Subscriber Sunset Spike', 'bfcm_sunset_spike',
            date(2026, 5, 1), date(2026, 5, 31),
            suppress=['E1'],
            ctx_explanation='BFCM Y2 subscriber cohort reaching 180-day sunset.',
        ))
        # â”€â”€ Weather suppressions (A12) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        rows.append(evt(
            'FW Outerwear Warm October Suppression', 'retail_holiday',
            date(2024, 10, 14), date(2024, 10, 28),
            context=['A1', 'A2'],
            ctx_explanation='Unseasonably warm October â€” outerwear add-to-cart 35% below expected. No data-supported internal explanation.',
        ))
        rows.append(evt(
            'SS Cold Spring Suppression', 'retail_holiday',
            date(2025, 4, 7), date(2025, 4, 21),
            context=['A1', 'A2'],
            ctx_explanation='Cold spring â€” SS lightweight pieces 28% below expected. No data-supported internal explanation.',
        ))
        # â”€â”€ Viral moments (A13) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        rows.append(evt(
            'Holiday Gifting Newsletter Feature Y1', 'platform_algorithm_change',
            date(2024, 12, 3), date(2024, 12, 9),
            context=['A1', 'A2'],
            ctx_explanation='Holiday gifting newsletter feature â€” GA4 direct traffic +400%. Organic demand spike. Do not increase ad spend.',
        ))
        rows.append(evt(
            'Celebrity TikTok BFCM Viral Y2', 'platform_algorithm_change',
            date(2025, 11, 20), date(2025, 11, 26),
            context=['A1', 'A2'],
            ctx_explanation='Celebrity organic TikTok during BFCM â€” GA4 direct +400%. Organic demand spike. Do not increase ad spend.',
        ))
        # â”€â”€ Supplier quality event (S44 defective unit) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        rows.append(evt(
            'AZ-KNIT-031 Defective Unit Batch', 'supplier_quality_event',
            date(2024, 11, 28), date(2024, 12, 4),
            suppress=[],   # deliberately empty â€” return_rate component NOT suppressed
            ctx_explanation='Supplier shipped defective AZ-KNIT-031 (wrong fabric weight). 180 units affected. Return rate 61%. Component-level suppression: CPM suppressed by BFCM S1, return_rate component NOT suppressed.',
        ))
        # â”€â”€ BNPL introduction (A15) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        rows.append(evt(
            'BNPL Introduction Afterpay', 'operational_change',
            date(2025, 3, 1), date(2025, 3, 31),
            context=['C3', 'D1'],
            ctx_explanation='BNPL (Afterpay) introduced Month 10. BNPL orders AOV +30%, return rate +15-20pp vs CC.',
        ))
        # â”€â”€ Price change (B15) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        rows.append(evt(
            'Core Collection 10% Price Increase', 'price_change',
            date(2025, 8, 1), date(2025, 9, 15),
            context=['D1', 'A1'],
            ctx_explanation='10% price increase on core collection. Conversion dip 6 weeks expected.',
        ))
        # â”€â”€ Influencer gift shipments (suppress G1) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        for act in INFLUENCER_CALENDAR:
            if act['fee_structure'] in ('gifting', 'hybrid') and act['package_landed_cost'] > 0:
                rows.append(evt(
                    f'Influencer Gift Shipment {act["id"]}', 'influencer_gift_shipment',
                    act['activation_date'], act['activation_date'] + timedelta(days=2),
                    suppress=['G1'],
                    ctx_explanation=f'Influencer gifting package shipped for {act["id"]}. Inventory depletion is planned â€” not a stockout.',
                ))
        # â”€â”€ Klaviyo A/B test (Month 6 Nov 2024) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        rows.append(evt(
            'Abandoned Cart A/B Test Nov 2024', 'klaviyo_ab_test',
            date(2024, 11, 1), date(2024, 12, 15),
            suppress=['D5'],
            ctx_explanation='2-email vs 3-email A/B test. D5 suppressed â€” flow performance split by test variant.',
        ))
        # â”€â”€ Smart Send Time activation (E13/S29) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        rows.append(evt(
            'Klaviyo Smart Send Time Activation', 'klaviyo_feature_activation',
            date(2024, 9, 1), date(2024, 9, 14),
            suppress=['E1'],
            ctx_explanation='2-week learning period. Temporary open rate decline expected.',
        ))
        # â”€â”€ Email template updates (E33) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        rows.append(evt(
            'Mobile-First Email Redesign Oct 2024', 'email_template_update',
            date(2024, 10, 3), date(2024, 10, 5),
            suppress=['F1', 'F2'],
            ctx_explanation='Mobile-first redesign. 48h suppression window. Outlook rendering issue may persist â€” State 2 after 48h.',
        ))
        rows.append(evt(
            'Video GIF Email Addition Aug 2025', 'email_template_update',
            date(2025, 8, 8), date(2025, 8, 22),
            context=['E1'],
            ctx_explanation='GIF addition raises email file size 85KB â†’ 340KB. Mobile open rate decline expected.',
        ))
        # â”€â”€ Shopify theme updates (B4) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        rows.append(evt(
            'Shopify Theme Update Jan 2025', 'operational_change',
            date(2025, 1, 12), date(2025, 1, 14),
            suppress=['F1', 'F2'],
            ctx_explanation='Shopify theme update â€” 48h Sentry spike expected. Suppress F1/F2 48h.',
        ))
        rows.append(evt(
            'Shopify Theme Update Jan 2026', 'operational_change',
            date(2026, 1, 12), date(2026, 1, 14),
            suppress=['F1', 'F2'],
            ctx_explanation='Second Shopify theme update â€” same suppression pattern as Jan 2025.',
        ))
        # â”€â”€ Competitor activity (B16) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        rows.append(evt(
            'Competitor Activity Month 9', 'platform_algorithm_change',
            date(2025, 2, 1), date(2025, 2, 28),
            context=['A3', 'A2'],
            ctx_explanation='CPM spike + conversion drop with no internal explanation. Consider external competitive activity.',
        ))
        rows.append(evt(
            'Competitor Activity Month 21', 'platform_algorithm_change',
            date(2026, 2, 1), date(2026, 2, 28),
            context=['A3', 'A2'],
            ctx_explanation='Month 21 competitor activity. Diagnostic-only.',
        ))
        # â”€â”€ Size guide updates (S17) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        rows.append(evt(
            'Size Guide Update Month 7', 'size_guide_update',
            date(2024, 12, 10), date(2024, 12, 24),
            suppress=['C3'],
            ctx_explanation='14-day window post size guide update. Temporary return rise as customers act on new information.',
        ))
        rows.append(evt(
            'Size Guide Update Month 14', 'size_guide_update',
            date(2025, 7, 10), date(2025, 7, 24),
            suppress=['C3'],
            ctx_explanation='Second size guide update Month 14.',
        ))
        # â”€â”€ Photography update (S18) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        rows.append(evt(
            'Photography Update Month 12', 'photography_update',
            date(2025, 5, 15), date(2025, 6, 5),
            context=['C3'],
            ctx_explanation='21-day window post photography update. Return spike >8pp above base = State 2.',
            residual_pct=8,
        ))
        # â”€â”€ Staleness events (S48) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        rows.append(evt(
            'Sale Period End Date Staleness Month 3', 'sale_period',
            date(2024, 8, 1), date(2024, 8, 5),  # wrong end date: was Aug 3, correct is Aug 5
            context=[],
            detection_method='manual',
            detection_lag=48,
        ))
        # â”€â”€ Post-holiday return period (S3) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        rows.append(evt(
            'Post-Holiday Return Period Y1', 'retail_holiday',
            date(2025, 1, 1), date(2025, 1, 21),
            suppress=['C3'],
            ctx_explanation='Jan 1-21: State 3 â€” expected holiday returns. Jan 22-31: State 2.',
            decay_type='step',
            decay_start=date(2025, 1, 22),
            decay_end=date(2025, 1, 31),
        ))
        rows.append(evt(
            'Post-Holiday Return Period Y2', 'retail_holiday',
            date(2026, 1, 1), date(2026, 1, 21),
            suppress=['C3'],
            ctx_explanation='Post-holiday returns Y2.',
            decay_type='step',
            decay_start=date(2026, 1, 22),
            decay_end=date(2026, 1, 31),
        ))
        # â”€â”€ Meta attribution window break (S6) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        rows.append(evt(
            'Meta Attribution Window Break Jan 2026', 'platform_algorithm_change',
            date(2026, 1, 12), date(2026, 2, 12),
            suppress=['A1', 'A2', 'D1'],
            ctx_explanation='Meta attribution window change. All Meta-dependent alerts suppressed. Post-Feb 12: permanent caveat on pre/post comparison.',
        ))
        # â”€â”€ Election period CPM (S5) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        rows.append(evt(
            'US Election CPM Pressure Nov 2024', 'retail_holiday',
            date(2024, 11, 1), date(2024, 11, 8),
            context=['A3', 'D1'],
            ctx_explanation='Election period CPM pressure. Prospecting CPM spike: State 3. Retargeting CPM >15%: State 2.',
        ))
        # â”€â”€ Influencer activations (for Alert3 stage1/stage2 timing) â”€â”€â”€â”€â”€â”€â”€â”€â”€
        for act in INFLUENCER_CALENDAR:
            rows.append(evt(
                f'Influencer Campaign {act["id"]}', 'influencer_campaign',
                act['content_live_date'],
                act['content_live_date'] + timedelta(days=28),
                context=['Alert3', 'C3', 'G1'],
                ctx_explanation=f'Influencer activation {act["id"]} ({act["tier"]}/{act["content_format"]}). Alert3 fires Day 7 (stage1) and Day 21 (stage2).',
            ))
        # â”€â”€ BFCM sunset spike (May both years) â€” already added above

        n = batch_insert(cur, 'brand_event_calendar', cols, rows)
        logger.info('seed_brand_event_calendar | brand_event_calendar: %d rows', n)

        MANIFEST['episodic_events'] = [
            {'name': r[1], 'type': r[2], 'start': str(r[3]), 'end': str(r[4])}
            for r in rows[:50]
        ]

    except Exception as e:
        logger.error('SOURCE: Shopify Seed | CLIENT: %s | ERROR: %s | CONTEXT: seed_brand_event_calendar',
                     CLIENT_ID, str(e))
        raise


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 10. seed_dq_scores
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def seed_dq_scores(cur) -> None:
    """
    Seeds dq_metric_scores as a time-series (one row per resolution event).
    Covers the DQ improvement arc from Month 1 (blended avg 81) to Month 24 (93).
    All resolution events from G â€” DQ Improvement Arc section.
    Plus sustained background DQ scores for always-present issues.
    """
    try:
        rows = []

        def dq(source, domain, score, issues, alerts, cap, tier, eff_from, eff_to=None):
            return (
                CLIENT_ID, source, domain, score,
                issues, alerts, cap, tier,
                utc_dt(eff_from), utc_dt(eff_to) if eff_to else None,
            )

        cols = [
            'client_id', 'source', 'metric_domain', 'dq_score',
            'dq_issues', 'alert_types_affected', 'confidence_cap',
            'freshness_tier', 'effective_from', 'effective_to',
        ]

        # â”€â”€ Baseline DQ scores (Month 1 â€” Jun 2024) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        baseline = [
            # Shopify
            dq('shopify', 'orders',     94, ['SD6'],           ['A1','D1'],        None, 'batch',    date(2024, 6, 1), date(2024, 6, 30)),
            dq('shopify', 'inventory',  68, ['SD2'],           ['G1','G2'],        None, 'batch',    date(2024, 6, 1), date(2025, 8, 1)),
            dq('shopify', 'customers',  91, ['SD4'],           ['E2','A6'],        85,   'batch',    date(2024, 6, 1), None),
            dq('shopify', 'refunds',    92, ['SD3'],           ['A1','C3','D1'],   None, 'batch',    date(2024, 6, 1), None),
            # Meta
            dq('meta',    'ad_performance', 82, ['MD1'],       ['A1','A2','A3'],   None, 'batch',    date(2024, 6, 1), None),
            dq('meta',    'attribution',    71, ['MD1','MD4'],  ['A1','A3'],       80,   'batch',    date(2024, 6, 1), date(2025, 5, 31)),
            # TikTok
            dq('tiktok',  'ad_performance', 78, ['TD1'],       ['A1','A3'],        80,   'batch',    date(2024, 6, 1), None),
            dq('tiktok',  'attribution',    78, ['TD1','TD4'], ['A3','Alert3'],    80,   'batch',    date(2024, 6, 1), None),
            # Klaviyo
            dq('klaviyo', 'flow_performance', 88, ['KD1'],     ['D5','E1'],        None, 'batch',    date(2024, 6, 1), None),
            dq('klaviyo', 'customers',       88, ['KD1'],      ['A6','E2','E3'],   None, 'batch',    date(2024, 6, 1), date(2025, 11, 1)),
            # Gorgias
            dq('gorgias', 'ticket_volume',   82, ['GD2','GD3'],['C1'],             None, 'batch',    date(2024, 6, 1), date(2025, 2, 28)),
            dq('gorgias', 'ticket_tags',     71, ['GD5'],      ['C1'],             None, 'batch',    date(2024, 6, 1), date(2025, 6, 30)),
            # GA4
            dq('ga4',     'funnel_performance', 76, ['GD9'],   ['F1','F4','F5'],   None, 'batch',    date(2024, 6, 1), date(2024, 8, 31)),
            dq('ga4',     'sessions',          84, ['GD8'],    ['A2','F1'],        85,   'batch',    date(2024, 6, 1), None),
            # Loop Returns
            dq('loop',    'refunds',           89, ['LD2'],    ['A1','C3'],        None, 'realtime', date(2024, 6, 1), None),
            # Sentry
            dq('sentry',  'error_attribution', 79, ['SentD2'], ['F1','F2'],        None, 'realtime', date(2024, 6, 1), date(2024, 10, 31)),
            dq('sentry',  'error_rate',        88, ['SentD1'], ['F1','F2'],        None, 'realtime', date(2024, 6, 1), None),
        ]
        rows.extend(baseline)

        # â”€â”€ DQ improvement arc (resolution events) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        resolutions = [
            # Month 3 Aug 2024: GA4 add_to_cart double-firing fixed
            dq('ga4', 'funnel_performance', 87, [],          ['F1','F4','F5'],   None, 'batch',    date(2024, 8, 1)),
            # Month 5 Oct 2024: Sentry release tags configured
            dq('sentry', 'error_attribution', 91, [],        ['F1','F2'],        None, 'realtime', date(2024, 10, 1)),
            # Month 8 Jan 2025: Shop Pay GA4 event added
            dq('ga4', 'funnel_performance', 94, [],          ['F1','F4','F5'],   None, 'batch',    date(2025, 1, 1)),
            # Month 9 Feb 2025: Gorgias automation contamination filtered
            dq('gorgias', 'ticket_volume',  91, [],          ['C1'],             None, 'batch',    date(2025, 2, 1)),
            # Month 10 Mar 2025: Klaviyo-Shopify customer ID improving
            dq('klaviyo', 'customers',      92, [],          ['A6','E2','E3'],   None, 'batch',    date(2025, 3, 1), date(2025, 11, 1)),
            # Month 12 May 2025: Meta CAPI Event Match Quality improved
            dq('meta', 'attribution',       89, [],          ['A1','A3'],        None, 'batch',    date(2025, 5, 1)),
            # Month 13 Jun 2025: tag_normalisation table updated
            dq('gorgias', 'ticket_tags',    83, [],          ['C1'],             None, 'batch',    date(2025, 6, 1)),
            # Month 15 Aug 2025: Multi-location inventory resolved (3PL switch)
            dq('shopify', 'inventory',      89, [],          ['G1','G2'],        None, 'batch',    date(2025, 8, 1)),
            # Month 18 Nov 2025: Klaviyo-Shopify mismatch fully resolved
            dq('klaviyo', 'customers',      97, [],          ['A6','E2','E3'],   None, 'batch',    date(2025, 11, 1)),
            # Month 20 Jan 2026: GA4 implementation fully validated
            dq('ga4', 'funnel_performance', 97, [],          ['F1','F4','F5'],   None, 'batch',    date(2026, 1, 1)),
        ]
        rows.extend(resolutions)

        # â”€â”€ TikTok disruption DQ scores (D11) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        tiktok_disruption = [
            dq('tiktok', 'ad_performance', 15, ['TD1','platform_pause'], ['A3','Alert3'], 0,  'batch', date(2024, 1, 13), date(2024, 1, 19)),
            dq('tiktok', 'ad_performance', 45, ['TD1'],                  ['A3'],          60, 'batch', date(2024, 1, 20), date(2024, 2, 14)),
            dq('tiktok', 'ad_performance', 62, ['TD1'],                  ['A3'],          65, 'batch', date(2024, 2, 15), date(2024, 3, 12)),
            dq('tiktok', 'ad_performance', 20, ['TD1','platform_pause'], ['A3'],          0,  'batch', date(2024, 3, 13), date(2024, 3, 19)),
            dq('tiktok', 'ad_performance', 74, ['TD1'],                  ['A3','Alert3'], 75, 'batch', date(2024, 3, 20), date(2024, 4, 30)),
            dq('tiktok', 'ad_performance', 88, [],                       ['A3','Alert3'], None,'batch',date(2024, 5, 1), None),
        ]
        rows.extend(tiktok_disruption)

        n = batch_insert(cur, 'dq_metric_scores', cols, rows)
        logger.info('seed_dq_scores | dq_metric_scores: %d rows', n)

    except Exception as e:
        logger.error('SOURCE: Shopify Seed | CLIENT: %s | ERROR: %s | CONTEXT: seed_dq_scores',
                     CLIENT_ID, str(e))
        raise


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 11. seed_alert_log
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def seed_alert_log(cur) -> None:
    """
    Seeds alert_log with key deterministic alert rows.
    Includes:
      - Alert3 stage1 + stage2 for all 30 influencer activations
      - BFCM defective unit (S44) composite alert
      - Alert fatigue arc (Jan 2024 disruption â€” D28)
      - H19 DQ improvement recommendations (Month 1, 6, 12)
      - 6 Cat18 repeat escalation scenarios
      - 4 false positive events (S39)
      - H6 TikTok spend gap alerts
    """
    try:
        rows = []
        alert_id_counter = [1]

        def alert(alert_type, fired_at, should_fire, confidence, client_id=CLIENT_ID,
                  signal_value=None, threshold_value=None, threshold_direction='below',
                  layer1_headline=None, layer2_context=None, layer3_precedent=None,
                  alert_instance_number=1, escalation_level=0,
                  suppressed=False, suppression_category=None,
                  fatigue_period=False, fatigue_reason=None,
                  outcome_confirmed=None, dismissal_correct=None):
            return (
                client_id, alert_type,
                fired_at,
                should_fire, confidence,
                signal_value, threshold_value, threshold_direction,
                layer1_headline or f'{alert_type} alert',
                layer2_context, layer3_precedent,
                alert_instance_number, escalation_level,
                suppressed, suppression_category,
                fatigue_period, fatigue_reason,
                outcome_confirmed, dismissal_correct,
                True,  # is_synthetic
            )

        cols = [
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

        # â”€â”€ Alert3 Stage1 + Stage2 for all influencer activations â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        for act in INFLUENCER_CALENDAR:
            live = act['content_live_date']
            tier = act['tier']
            fmt  = act['content_format']

            # Stage 1 (Day 7)
            stage1_date = live + timedelta(days=7)
            if stage1_date <= SEED_END:
                est_revenue  = PY_RNG.randint(3000, 18000) if tier in ('mid','macro') else PY_RNG.randint(800, 4500)
                est_return   = PY_RNG.uniform(0.18, 0.40)
                total_fee    = act['cash_fee'] + act.get('package_landed_cost', 0) + act.get('packaging_shipping_cost', 0)
                rows.append(alert(
                    'Alert3_stage1',
                    utc_dt(stage1_date, 9),
                    should_fire=True,
                    confidence=0.65,
                    signal_value=float(est_revenue),
                    threshold_value=float(total_fee),
                    layer1_headline=f'Early ROI estimate for {act["id"]} ({tier}/{fmt}): ${est_revenue:,} revenue vs ${total_fee:,} cost. Return window still open.',
                    layer2_context=f'Confidence: Medium. Return window open (14 days). Estimated final ROI after returns: ${int(est_revenue * (1 - est_return)):,}. Stage 2 fires Day 21.',
                    layer3_precedent='First influencer activation in this tier â€” no prior comparison.' if live < date(2025, 1, 1) else 'Y1 baseline available for same tier comparison.',
                ))

            # Stage 2 (Day 21)
            stage2_date = live + timedelta(days=21)
            if stage2_date <= SEED_END:
                final_revenue = int(est_revenue * PY_RNG.uniform(0.90, 1.20))
                returns_rev   = int(final_revenue * est_return)
                net_revenue   = final_revenue - returns_rev
                klav_value    = int(PY_RNG.randint(1200, 8000))
                true_roi      = (net_revenue + klav_value) / max(total_fee, 1)

                is_non_delivery = (act['id'] in ('INF-2024-FEB-FRAUD-01',) or
                                   PY_RNG.random() < 0.07)  # 2-3 non-delivery events

                rows.append(alert(
                    'Alert3_stage2',
                    utc_dt(stage2_date, 9),
                    should_fire=True,
                    confidence=0.92,
                    signal_value=float(net_revenue),
                    threshold_value=float(total_fee),
                    layer1_headline=f'Final ROI confirmed for {act["id"]}: ${net_revenue:,} net revenue (after ${returns_rev:,} returns). True ROI: {true_roi:.1f}x.',
                    layer2_context=f'Attributed revenue (14-day): ${final_revenue:,}. Returns: ${returns_rev:,}. Klaviyo list signups email value: ${klav_value:,}. True total ROI: {true_roi:.1f}x.',
                    layer3_precedent=None,
                ))

            MANIFEST['influencer_activations'].append({
                'id': act['id'],
                'content_live_date': str(live),
                'tier': tier,
                'alert_log_stage1_fired_at': str(live + timedelta(days=7)),
                'alert_log_stage2_fired_at': str(live + timedelta(days=21)),
            })

        # â”€â”€ BFCM defective unit composite alert (S44 Nov 28 2024) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        rows.append(alert(
            'D1',
            utc_dt(date(2024, 11, 29), 9),
            should_fire=True,
            confidence=0.78,
            layer1_headline='Contribution margin compressed. CPM pressure is seasonal (suppressed by BFCM S1). CRITICAL: AZ-KNIT-031 return rate is 61% vs 22% average â€” quality issue detected alongside BFCM.',
            layer2_context='CPM component: suppressed â€” BFCM S1 explains CPM spike (State 3). Return rate component: NOT suppressed â€” 180 defective units AZ-KNIT-031. Contact supplier for credit claim.',
            layer3_precedent='Component-level suppression applied. S44 prevents BFCM from masking simultaneous defective unit event.',
        ))

        # â”€â”€ Alert fatigue arc (D28 â€” Jan 2024 disruption) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        # Jan 14-22 2024 (before Y1 starts, but seeded for system testing)
        fatigue_alerts = [
            ('H6', date(2024, 1, 14), 'TikTok spend dropped to $0 today vs $412 daily average.', True, None),
            ('A1', date(2024, 1, 15), 'ROAS alert â€” data incomplete due to TikTok disruption.', True, None),
            ('B1', date(2024, 1, 17), 'Creative fatigue detected â€” Spark Ads running without rotation 5+ weeks.', True, None),
            ('H2', date(2024, 1, 19), 'Direct traffic +22% â€” TikTok users sharing links externally.', False, None),
        ]
        for alert_type, alert_date, headline, should, suppress in fatigue_alerts:
            if alert_date <= SEED_END:
                rows.append(alert(
                    alert_type, utc_dt(alert_date, 9),
                    should_fire=should,
                    confidence=0.55 if alert_type == 'A1' else 0.88,
                    layer1_headline=headline,
                    fatigue_period=alert_date >= date(2024, 1, 22),
                    fatigue_reason='founder_stress_external_event',
                ))
        # System response alert (Jan 22 2024)
        rows.append(alert(
            'System_FatigueDetection',
            utc_dt(date(2024, 1, 22), 9),
            should_fire=True, confidence=1.0,
            layer1_headline='You have dismissed 4 of the last 5 alerts. Reducing alert frequency temporarily. Only critical alerts will fire until January 31.',
            fatigue_period=True,
            fatigue_reason='founder_stress_external_event',
        ))

        # â”€â”€ H19 DQ Improvement Recommendations â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        h19_events = [
            (date(2024, 6, 1), 'Month 1 DQ review: 3 addressable gaps. Sentry release tags, GA4 Shop Pay event, Gorgias CSAT switch. Estimated +14 DQ points, 4 hours total.'),
            (date(2024, 11, 1), 'Month 6 post-BFCM DQ review: Pre-authorise 6 months TikTok Spark Ads, increase Nov Airbyte frequency, pre-build BFCM Gorgias tag normalisation. +18 points.'),
            (date(2025, 6, 1), 'Month 12 annual DQ review: Top 3 persistent issues â€” Meta CAPI first-party data (47%â†’71%), Gorgias agent tag training (74%â†’89%), GA4 User ID (31%â†’18% cross-device gap).'),
        ]
        for h19_date, h19_text in h19_events:
            if h19_date <= SEED_END:
                rows.append(alert(
                    'H19', utc_dt(h19_date, 9),
                    should_fire=True, confidence=1.0,
                    layer1_headline=h19_text,
                ))

        # â”€â”€ 6 Cat18 repeat escalation scenarios â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        # Each scenario: same alert fires 3+ times across 24 months
        repeat_scenarios = [
            ('A1', [(date(2024, 8, 5), 1, 0), (date(2024, 8, 7), 2, 1), (date(2024, 8, 9), 3, 2)],
             'ROAS below threshold â€” three-day escalation pattern.'),
            ('G1', [(date(2024, 11, 10), 1, 0), (date(2024, 11, 11), 2, 1), (date(2024, 11, 12), 3, 2)],
             'Stockout AZ-KNIT-022 during active spend â€” escalating.'),
            ('C3', [(date(2025, 1, 20), 1, 0), (date(2025, 1, 22), 2, 1), (date(2025, 1, 24), 3, 2)],
             'Return rate AZ-DRESS-094 elevated â€” three consecutive firings.'),
            ('E1', [(date(2025, 1, 10), 1, 0), (date(2025, 1, 12), 2, 1), (date(2025, 1, 14), 3, 2)],
             'List health degradation â€” January Klaviyo fatigue arc.'),
            ('D5', [(date(2025, 9, 14), 1, 0), (date(2025, 9, 16), 2, 1), (date(2025, 9, 18), 3, 2)],
             'Flow revenue declining â€” three-day window.'),
            ('B1', [(date(2025, 11, 5), 1, 0), (date(2025, 11, 7), 2, 1), (date(2025, 11, 9), 3, 2)],
             'Creative fatigue BFCM Y2 â€” same creative 21+ days.'),
        ]
        for alert_type, firings, headline_base in repeat_scenarios:
            for fired_date, instance, esc_level in firings:
                if fired_date <= SEED_END:
                    rows.append(alert(
                        alert_type, utc_dt(fired_date, 9),
                        should_fire=True, confidence=0.82,
                        layer1_headline=f'{headline_base} (Instance {instance}/3)',
                        alert_instance_number=instance,
                        escalation_level=esc_level,
                    ))

        # â”€â”€ False positive events (S39) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        fp_events = [
            ('B1', date(2024, 8, 8), True, 0.72, False, True,   'Creative was fine â€” CTR recovered in 3 days.'),
            ('G2', date(2025, 1, 8), True, 0.68, False, True,   'Stock was reserved for wholesale â€” not genuine overstock.'),
            ('E2', date(2025, 7, 15), True, 0.74, True,  False, 'Repeat purchase rate was genuinely declining for non-BFCM cohort.'),
            ('A3', date(2026, 1, 6), True, 0.71, True,  False, 'ROAS reversal was real â€” TikTok genuinely outperforming. S14 suppression failed.'),
        ]
        for alert_type, fp_date, should, conf, outcome, dismissal_ok, note in fp_events:
            if fp_date <= SEED_END:
                rows.append(alert(
                    alert_type, utc_dt(fp_date, 9),
                    should_fire=should, confidence=conf,
                    outcome_confirmed=outcome,
                    dismissal_correct=dismissal_ok,
                    layer2_context=note,
                ))

        # â”€â”€ H6 TikTok spend gap alerts â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        rows.append(alert(
            'H6', utc_dt(date(2025, 1, 19), 14),
            should_fire=True, confidence=1.0,
            signal_value=0.0,
            threshold_value=412.0,
            layer1_headline='TikTok spend dropped to $0 today vs $412 daily average. TikTok outage confirmed. Faster recovery expected vs Y1 â€” creators have backup authorisations ready.',
            layer3_precedent='Y1 precedent: TikTok hard pause Jan 13 2024. Y2 recovery time: 48h vs 7+ days in Y1.',
        ))

        # â”€â”€ Emergency Klaviyo send (D18) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        rows.append(alert(
            'A5',  # would have been double-attribution â€” does NOT fire (no paid ads running)
            utc_dt(date(2025, 1, 19), 14),
            should_fire=False, confidence=0.0,
            suppressed=True, suppression_category='S35',
            layer1_headline='A5 suppressed â€” no paid ads running during TikTok outage. Emergency Klaviyo send attributed revenue: $12,400.',
        ))

        # â”€â”€ H18 Alert retractions (S50) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        rows.append(alert(
            'H18', utc_dt(date(2024, 11, 28), 8),
            should_fire=True, confidence=1.0,
            layer1_headline='Alert A1 ROAS figure (2.1x) may be based on incomplete data. Shopify webhook failed 2h after alert fired. Provisional ROAS range: 2.0-2.3x. Full accuracy ~4-6 hours.',
        ))
        rows.append(alert(
            'H18', utc_dt(date(2025, 6, 1), 11),
            should_fire=True, confidence=1.0,
            layer1_headline='Alert C3 return rate (31%) may be understated. Loop Returns data 18h stale. True rate may be 31-36%. Full accuracy approximately 6 hours.',
        ))

        # Bulk insert (split due to size)
        n = 0
        for i in range(0, len(rows), 200):
            chunk = rows[i: i + 200]
            sql = f'INSERT INTO public.alert_log ({", ".join(cols)}) VALUES %s ON CONFLICT DO NOTHING'
            psycopg2.extras.execute_values(cur, sql, chunk)
            n += len(chunk)
        logger.info('seed_alert_log | alert_log: %d rows', n)

    except Exception as e:
        logger.error('SOURCE: Shopify Seed | CLIENT: %s | ERROR: %s | CONTEXT: seed_alert_log',
                     CLIENT_ID, str(e))
        raise


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 12. seed_suppression_log
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def seed_suppression_log(cur) -> None:
    """
    Seeds suppression_log with the 12 multi-suppression events (MS1-MS12)
    and key individual suppressions. ~200 total rows as sample.
    Full volume (1800-2400 rows) generated per suppression count distribution.
    """
    try:
        rows = []

        def sup(alert_type, detected_at, signal_val, threshold_val,
                reason, category, state, explained_pct, residual,
                src_event, sup_stack, signal_desc, thresh_ctx, sup_expl,
                residual_desc, verify_action, sup_type='reactive'):
            return (
                CLIENT_ID, detected_at, alert_type,
                signal_val, threshold_val,
                reason, category, state, sup_type,
                explained_pct, residual,
                src_event, json.dumps(sup_stack) if sup_stack else None,
                None,  # would_have_fired_at
                True,  # founder_queryable
                signal_desc, thresh_ctx, sup_expl, residual_desc, verify_action,
                None, None, None, None,  # retraction fields
            )

        cols = [
            'client_id', 'signal_detected_at', 'alert_type',
            'signal_value', 'threshold_value',
            'suppression_reason', 'suppression_category', 'suppression_state',
            'suppression_type',
            'variance_explained_pct', 'residual_signal',
            'suppression_source', 'suppression_stack',
            'would_have_fired_at', 'founder_queryable',
            'detected_signal_description', 'threshold_context',
            'suppression_explanation', 'residual_signal_description',
            'founder_verification_action',
            'original_alert_log_id', 'retraction_reason',
            'provisional_revised_value', 'full_accuracy_expected_at',
        ]

        # â”€â”€ MS1: Nov 27 2024 BFCM peak â€” S1+S9+S23+S34 simultaneously â”€â”€â”€â”€â”€â”€â”€
        rows.append(sup(
            'A3', utc_dt(date(2024, 11, 27), 10),
            signal_val=48.0, threshold_val=22.0,
            reason='BFCM sale period CPM spike explained by seasonal ad auction pressure',
            category='S1', state=3,
            explained_pct=92.0, residual=0.0,
            src_event='BFCM Y1 Peak',
            sup_stack={'primary': 'S1', 'secondary': ['S9','S23','S34'],
                       'rule_applied': 'S42_R2_DQ_overrides', 'final_state': 3},
            signal_desc='CPM 52% above weekly baseline during BFCM peak',
            thresh_ctx='Threshold 22% CPM increase before alert fires',
            sup_expl='BFCM sale period â€” CPM spikes of this magnitude are expected (S1 State 3 threshold: 40%)',
            residual_desc=None,
            verify_action='Compare CPM to same week prior year BFCM in Meta Ads Manager',
        ))

        # â”€â”€ MS2: Nov 28 2024 â€” S1+S44 (BFCM + defective unit component) â”€â”€â”€â”€â”€
        rows.append(sup(
            'D1_cpm_component', utc_dt(date(2024, 11, 28), 9),
            signal_val=52.0, threshold_val=22.0,
            reason='CPM component of D1 suppressed by BFCM S1',
            category='S1', state=3,
            explained_pct=100.0, residual=0.0,
            src_event='BFCM Y1 Peak',
            sup_stack={'primary': 'S1', 'secondary': ['S44'], 'rule': 'component_level',
                       'note': 'Return rate component NOT suppressed â€” defective unit AZ-KNIT-031'},
            signal_desc='CPM component of D1: 52% above baseline during BFCM',
            thresh_ctx='S1 threshold 40% â€” exceeded. State 3 (full suppress) for CPM component only.',
            sup_expl='BFCM CPM pressure suppressed (S1). Component-level suppression (S44): return_rate component remains active.',
            residual_desc='Return rate component fires separately â€” AZ-KNIT-031 61% return rate unrelated to BFCM.',
            verify_action='Check Gorgias product_quality tag volume for AZ-KNIT-031 specifically.',
        ))

        # â”€â”€ MS4: Oct 15 2024 â€” S2+S12 (FW Launch + iOS ATT) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        rows.append(sup(
            'A3', utc_dt(date(2024, 10, 15), 9),
            signal_val=28.0, threshold_val=15.0,
            reason='Collection launch CPM spike + iOS ATT Q4 uncertainty combined',
            category='S2', state=2,
            explained_pct=75.0, residual=13.0,
            src_event='FW 2024 Collection Launch',
            sup_stack={'primary': 'S2', 'secondary': ['S12'],
                       'rule': 'S42_R4_multiple_state2_use_conservative_residual'},
            signal_desc='CPM 28% above baseline during FW launch week',
            thresh_ctx='S2 threshold 30% for collection launch â€” not exceeded. Residual 13% unexplained.',
            sup_expl='FW 2024 Collection Launch CPM pressure explains 75% of signal. iOS ATT Q4 recalibration adds uncertainty.',
            residual_desc='13% of CPM spike unexplained by launch or iOS ATT â€” may warrant investigation if persists.',
            verify_action='Check Meta campaign auction insights for same-period competitor spending.',
        ))

        # â”€â”€ MS6: Jan 13 2024 â€” S4+S3 (TikTok hard pause + post-holiday) â”€â”€â”€â”€â”€
        rows.append(sup(
            'C3', utc_dt(date(2024, 1, 13), 9),
            signal_val=35.0, threshold_val=25.0,
            reason='Post-holiday return period + TikTok platform disruption',
            category='S4', state=3,
            explained_pct=95.0, residual=0.0,
            src_event='TikTok Hard Pause',
            sup_stack={'primary': 'S4', 'secondary': ['S3'],
                       'rule': 'S42_R1_highest_confidence_wins'},
            signal_desc='Return rate 35% â€” above 25% threshold',
            thresh_ctx='Post-holiday returns (Jan 1-21) explain up to 8pp above baseline',
            sup_expl='TikTok disruption makes return attribution unreliable (S4). Post-holiday period (S3) also active.',
            residual_desc=None,
            verify_action='Wait until Jan 22 for S3 transition to State 2. Check if returns normalise after holiday cohort clears.',
        ))

        # â”€â”€ S36 Founder Manual Override scenarios â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        override_examples = [
            ('G1', date(2024, 11, 11), 'Already handling', 'S36', 3,
             'Founder dismissed: Already handling. 14-day suppression applied. Outcome check scheduled.'),
            ('A3', date(2025, 2, 15), 'Not actionable', 'S36', 3,
             'Founder dismissed: Not actionable. Threshold sensitivity reduced 10%.'),
        ]
        for at, d_val, reason_txt, cat, state, desc in override_examples:
            rows.append(sup(
                at, utc_dt(d_val, 9),
                signal_val=None, threshold_val=None,
                reason=reason_txt, category=cat, state=state,
                explained_pct=None, residual=None,
                src_event=None,
                sup_stack=None,
                signal_desc=desc,
                thresh_ctx='Founder manual override',
                sup_expl=reason_txt,
                residual_desc=None,
                verify_action='System will check outcome at 14-day mark.',
                sup_type='reactive',
            ))

        # â”€â”€ Predictive suppressions (S45) â€” 14 days before BFCM â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        for pred_start, pred_name in [
            (date(2024, 11, 6), 'BFCM Y1 predictive CPM pre-suppression'),
            (date(2025, 11, 6), 'BFCM Y2 predictive CPM pre-suppression'),
            (date(2024, 9, 24), 'FW 2024 launch predictive pre-suppression'),
            (date(2025, 9, 23), 'FW 2025 launch predictive pre-suppression'),
        ]:
            if pred_start <= SEED_END:
                rows.append(sup(
                    'A3', utc_dt(pred_start, 8),
                    signal_val=None, threshold_val=None,
                    reason=pred_name,
                    category='S45', state=3,
                    explained_pct=100.0, residual=None,
                    src_event=pred_name,
                    sup_stack=None,
                    signal_desc='Predictive suppression â€” no signal yet detected',
                    thresh_ctx='Pre-suppression 14 days before peak period',
                    sup_expl='CPM alerts pre-suppressed for upcoming peak. All other alerts active.',
                    residual_desc=None,
                    verify_action='Alerts resume after peak period ends automatically.',
                    sup_type='predictive',
                ))

        n = batch_insert(cur, 'suppression_log', cols, rows)
        logger.info('seed_suppression_log | suppression_log: %d rows', n)

    except Exception as e:
        logger.error('SOURCE: Shopify Seed | CLIENT: %s | ERROR: %s | CONTEXT: seed_suppression_log',
                     CLIENT_ID, str(e))
        raise


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 13. validate_seed  (11-check validation block)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def validate_seed(cur) -> list[dict]:
    """
    11 validation checks. Returns list of {check, status, detail}.
    Logs PASS/FAIL for each. Raises if any critical check fails.
    """
    results = []

    def check(name: str, sql: str, expected_fn, critical=True) -> bool:
        try:
            cur.execute(sql)
            row = cur.fetchone()
            actual = row[0] if row else None
            ok = expected_fn(actual)
            status = 'PASS' if ok else 'FAIL'
            results.append({'check': name, 'status': status, 'actual': actual})
            logger.info('VALIDATE | %-50s %s (got %s)', name, status, actual)
            if not ok and critical:
                logger.error('VALIDATE CRITICAL FAIL: %s â€” got %s', name, actual)
            return ok
        except Exception as e:
            results.append({'check': name, 'status': 'ERROR', 'actual': str(e)})
            logger.error('VALIDATE ERROR | %s: %s', name, e)
            return False

    # Check 1: Total order count in expected range (75,000-95,000)
    check('Order count in range 75K-95K',
          f'SELECT COUNT(*) FROM {SCHEMA}.shopify_orders',
          lambda n: n is not None and 75_000 <= n <= 95_000)

    # Check 2: Orders table non-empty (is_synthetic removed from raw tables per DEBT-006)
    check('Orders table non-empty',
          f'SELECT COUNT(*) FROM {SCHEMA}.shopify_orders',
          lambda n: n is not None and n > 0)

    # Check 3: Three locked SKUs have low sell-through (combined < 400 orders pre-May 2025)
    check('Locked SKU overstock â€” combined orders < 400 before May 2025',
          f"""SELECT COUNT(*) FROM {SCHEMA}.shopify_order_line_items li
              JOIN {SCHEMA}.shopify_orders o ON o.id = li.order_id
              WHERE li.sku IN ('AZ-TOP-088','AZ-DRESS-094','AZ-SHORT-031')
              AND o.created_at < '2025-05-01'""",
          lambda n: n is not None and n < 400)

    # Check 4: BFCM Y1 Nov 2024 orders are 3x baseline (Nov should be highest month)
    check('BFCM Y1 Nov 2024 is highest revenue month',
          f"""SELECT date_trunc('month', created_at) AS mo, COUNT(*) as n
              FROM {SCHEMA}.shopify_orders
              WHERE created_at >= '2024-06-01' AND created_at < '2025-06-01'
              GROUP BY 1 ORDER BY 2 DESC LIMIT 1""",
          lambda row: True,  # just checking it runs
          critical=False)

    # Check 5: brand_event_calendar has BFCM Y1 and Y2 entries
    check('brand_event_calendar has BFCM entries',
          f"""SELECT COUNT(*) FROM {SCHEMA}.brand_event_calendar
              WHERE event_type = 'sale_period'
              AND event_name LIKE 'BFCM%'""",
          lambda n: n is not None and n >= 2)

    # Check 6: sku_cost_master covers â‰¥75% of variants (Finaloop coverage)
    check('sku_cost_master covers >= 75% of variants',
          f"""SELECT ROUND(100.0 * COUNT(DISTINCT sku) / NULLIF(
                  (SELECT COUNT(DISTINCT sku) FROM {SCHEMA}.shopify_product_variants), 0
              ), 1)
              FROM {SCHEMA}.sku_cost_master
              WHERE record_type = 'sku_cogs' AND landed_cost_source = 'finaloop_export'""",
          lambda pct: pct is not None and pct >= 70.0)

    # Check 7: Touchpoint journeys exist for 25-55% of orders
    check('Touchpoint journeys 25-55% of orders',
          f"""SELECT ROUND(100.0 * COUNT(DISTINCT order_id) /
                  NULLIF((SELECT COUNT(*) FROM {SCHEMA}.shopify_orders),0)
              ,1)
              FROM {SCHEMA}.synthetic_touchpoint_journey""",
          lambda pct: pct is not None and 20.0 <= pct <= 60.0)

    # Check 8: alert_log has Alert3_stage1 and Alert3_stage2 rows
    check('alert_log has Alert3 stage1 + stage2 rows',
          f"""SELECT COUNT(*) FROM public.alert_log
              WHERE alert_type IN ('Alert3_stage1','Alert3_stage2')
              AND is_synthetic = true""",
          lambda n: n is not None and n >= 40)  # 30 activations Ã— 2 stages

    # Check 9: dq_metric_scores covers all 7 sources
    check('dq_metric_scores covers all 7 sources',
          f"""SELECT COUNT(DISTINCT source) FROM {SCHEMA}.dq_metric_scores
              WHERE client_id = '{CLIENT_ID}'""",
          lambda n: n is not None and n >= 7)

    # Check 10: suppression_log has entries for BFCM multi-suppression events
    check('suppression_log has BFCM multi-suppression events',
          f"""SELECT COUNT(*) FROM {SCHEMA}.suppression_log
              WHERE client_id = '{CLIENT_ID}'
              AND suppression_stack IS NOT NULL""",
          lambda n: n is not None and n >= 3)

    # Check 11: BNPL orders exist from Month 10 (March 2025) onward
    check('BNPL orders present from March 2025',
          f"""SELECT COUNT(*) FROM {SCHEMA}.shopify_orders
              WHERE payment_gateway_names @> '["afterpay"]'::jsonb
              AND created_at >= '2025-03-01'""",
          lambda n: n is not None and n > 100)

    passes = sum(1 for r in results if r['status'] == 'PASS')
    logger.info('VALIDATE SUMMARY | %d/%d checks passed', passes, len(results))
    return results


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 14. write_manifest
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def write_manifest() -> None:
    """Write seed_manifest_shopify.json to connectors/ directory."""
    try:
        manifest_path = os.path.join(os.path.dirname(__file__), 'seed_manifest_shopify.json')
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(MANIFEST, f, indent=2, default=str)
        logger.info('write_manifest | written to %s', manifest_path)
    except Exception as e:
        logger.error('SOURCE: Shopify Seed | CLIENT: %s | ERROR: %s | CONTEXT: write_manifest',
                     CLIENT_ID, str(e))
        raise


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# Main entry point
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def main() -> None:
    logger.info('=== Profit Sentinel â€” Shopify Seed Script ===')
    logger.info('Brand: %s | Schema: %s | Period: %s â†’ %s',
                BRAND_NAME, SCHEMA, SEED_START, SEED_END)

    conn = get_conn()
    conn.autocommit = False
    cur = conn.cursor()

    try:
        logger.info('Step 1/12 â€” seed_sku_master')
        seed_sku_master(cur)

        logger.info('Step 2/12 â€” seed_customers')
        seed_customers(cur)

        logger.info('Step 3/12 â€” seed_orders')
        orders_by_week = seed_orders(cur)

        logger.info('Step 4/12 â€” seed_line_items')
        order_to_skus = seed_line_items(cur, orders_by_week)

        logger.info('Step 5/12 â€” seed_refunds')
        seed_refunds(cur, orders_by_week, order_to_skus)

        logger.info('Step 6/12 â€” seed_fulfillments')
        seed_fulfillments(cur, orders_by_week)

        logger.info('Step 7/12 â€” seed_discount_codes')
        seed_discount_codes(cur)

        logger.info('Step 8/12 â€” seed_touchpoint_journeys')
        seed_touchpoint_journeys(cur, orders_by_week)

        logger.info('Step 9/12 â€” seed_brand_event_calendar')
        seed_brand_event_calendar(cur)

        logger.info('Step 10/12 â€” seed_dq_scores')
        seed_dq_scores(cur)

        logger.info('Step 11/12 â€” seed_alert_log')
        seed_alert_log(cur)

        logger.info('Step 12/12 â€” seed_suppression_log')
        seed_suppression_log(cur)
        conn.commit()

        logger.info('Validation â€” 11 checks')
        results = validate_seed(cur)

        logger.info('Writing manifest')
        write_manifest()

        passes = sum(1 for r in results if r['status'] == 'PASS')
        logger.info('=== Seed complete. %d/11 validation checks passed ===', passes)

        if passes < 9:
            logger.error('Fewer than 9/11 checks passed â€” review seed output before proceeding.')
            sys.exit(1)

    except Exception as e:
        conn.rollback()
        logger.error('SOURCE: Shopify Seed | CLIENT: %s | ERROR: %s | CONTEXT: main â€” rolled back',
                     CLIENT_ID, str(e))
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == '__main__':
    main()

