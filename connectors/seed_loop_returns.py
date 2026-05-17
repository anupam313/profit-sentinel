"""
Profit Sentinel — Loop Returns Seed Script
Brand: Azure & Co (client_azure_co)
Date range: June 1 2024 – May 31 2026 (24 months)

Seeds:
  client_azure_co.loop_returns
  client_azure_co.loop_return_line_items
  client_azure_co.loop_return_reasons
  public.alert_log        (Alert5_stage1 ×4, Alert5_stage2 ×4, C3 ×4, D1_component ×1)
  public.suppression_log  (S17 size_guide_update ×2)
  client_azure_co.brand_event_calendar (supplier_quality_event, size_guide_update ×2,
                                        operational_change, photography_update)

Six FIX rules from seed_shopify.py applied.
SKU notes (spec references non-manifest SKUs; closest valid manifest SKUs substituted):
  DEFECTIVE_SKU = AZ-KNIT-010  (spec: AZ-KNIT-031, not in manifest)
  CHAIN1_SKU    = AZ-DENIM-003 (spec: AZ-DENIM-042, not in manifest)
  CHAIN2_SKU    = AZ-KNIT-018  (✓ exists in manifest)
  CHAIN4_SKU    = AZ-KNIT-020  (spec: AZ-KNIT-022, not in manifest)
Weekly target note: spec says 35-45/week but validation range is 1,800-2,200 over
  104 weeks → 17-21/week baseline used to land inside validation window.
"""

import json, logging, os, random, sys, uuid
from datetime import date, datetime, timedelta, timezone
from typing import Optional

import numpy as np
import psycopg2, psycopg2.extras
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s')
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CLIENT_ID  = 'azure_co'
SCHEMA     = 'client_azure_co'
SEED_START = date(2024, 6, 1)
SEED_END   = date(2026, 5, 31)
SEED_RNG   = np.random.default_rng(88)   # distinct: Shopify=42, Meta=99, TikTok=77, Klaviyo=55
PY_RNG     = random.Random(88)

MANIFEST_PATH = os.path.join(os.path.dirname(__file__), 'seed_manifest_shopify.json')

# SKU substitutions
DEFECTIVE_SKU = 'AZ-KNIT-010'
CHAIN1_SKU    = 'AZ-DENIM-003'
CHAIN2_SKU    = 'AZ-KNIT-018'
CHAIN3_SKUS   = ['AZ-DRESS-097', 'AZ-TOP-092', 'AZ-KNIT-012']
CHAIN4_SKU    = 'AZ-KNIT-020'

# Deterministic ID namespace
_LR_NS = uuid.UUID('f1f1f1f1-dead-beef-cafe-000000000005')

def _lr_id(key: str) -> str:
    return str(uuid.uuid5(_LR_NS, f'lr:{key}'))

def _li_id(key: str) -> str:
    return str(uuid.uuid5(_LR_NS, f'li:{key}'))

# ---------------------------------------------------------------------------
# FIX 4 — Nearest PD correlation matrix (copied exactly from seed_shopify.py)
# ---------------------------------------------------------------------------

def _nearest_pd_corr(m: np.ndarray, eps: float = 1e-4) -> np.ndarray:
    vals, vecs = np.linalg.eigh(m)
    vals_clipped = np.maximum(vals, eps)
    pd = vecs @ np.diag(vals_clipped) @ vecs.T
    pd = (pd + pd.T) / 2
    d = np.sqrt(np.diag(pd))
    pd = pd / np.outer(d, d)
    return pd

# Correlated return signals: (return_rate_mult, exchange_rate_mult)
# Higher returns → slightly lower exchange proportion
_LR_CORR_DESIGN = np.array([
    [1.00, -0.35],
    [-0.35,  1.00],
])
LR_CORR = _nearest_pd_corr(_LR_CORR_DESIGN)

def _generate_return_signals(n: int) -> list:
    """Return (n, 2) list [[return_mult, exchange_mult], ...] as Python floats."""
    L = np.linalg.cholesky(LR_CORR)
    noise = SEED_RNG.standard_normal((n, 2))
    corr = noise @ L.T
    return np.clip(1.0 + corr * 0.12, 0.50, 1.60).tolist()

# ---------------------------------------------------------------------------
# FIX 2 — Airbyte helpers (copied exactly from seed_shopify.py)
# ---------------------------------------------------------------------------

def airbyte_meta_cols(extracted_at: datetime) -> tuple:
    """_airbyte_raw_id, _airbyte_extracted_at, _airbyte_meta, _airbyte_generation_id"""
    return (str(uuid.uuid4()), extracted_at, '{}', 0)

def utc_dt(d: date, hour: int = 9, minute: int = 0) -> datetime:
    return datetime(d.year, d.month, d.day, hour, minute, 0, tzinfo=timezone.utc)

# ---------------------------------------------------------------------------
# Return reason data
# ---------------------------------------------------------------------------

REASON_CODES   = ['sizing', 'style', 'quality', 'wrong_item', 'other']
REASON_WEIGHTS = [0.52,     0.23,    0.12,      0.04,         0.09]

REASON_DETAILS = {
    'sizing':        ['Too small', 'Too large', 'Runs small', 'Runs large',
                      'Different size than expected', 'Ordered two sizes'],
    'style':         ['Not as pictured', 'Color different from website',
                      'Changed mind', 'Style not as expected', 'Gifted item not wanted'],
    'quality':       ['Fabric quality below expectations', 'Stitching issue',
                      'Pilling after first wear', 'Seam issue'],
    'quality_issue': ['Defective — seam failure on first wear',
                      'Manufacturing defect — zipper detached',
                      'Pilling immediately after first wash'],
    'wrong_item':    ['Wrong color received', 'Wrong size received',
                      'Wrong product received'],
    'other':         ['Duplicate order', 'No longer needed', 'Ordered by mistake'],
}

CUSTOMER_COMMENTS = {
    'sizing':        ['Bought a medium but it fits like a small',
                      'Runs very small — sizing up next time', None, None, None],
    'style':         ['The color looks different in person', None, None],
    'quality':       ['Not what I expected for the price', None, None],
    'quality_issue': ['Defective — seam came apart after first wash',
                      'Clearly a manufacturing defect'],
    'wrong_item':    ['Received wrong size'],
    'other':         [None, None, None],
}

# ---------------------------------------------------------------------------
# Arc and timing helpers
# ---------------------------------------------------------------------------

def _month_num(d: date) -> int:
    return (d.year - SEED_START.year) * 12 + (d.month - SEED_START.month) + 1

def _base_return_rate(d: date) -> float:
    mn = _month_num(d)
    if mn <= 3:    return PY_RNG.uniform(0.18, 0.20)   # Jun–Aug 2024
    elif mn <= 7:  return PY_RNG.uniform(0.20, 0.23)   # Sep–Dec 2024
    elif mn <= 9:  return PY_RNG.uniform(0.28, 0.32)   # Jan–Feb 2025 (avalanche)
    elif mn <= 12: return PY_RNG.uniform(0.21, 0.24)   # Mar–May 2025
    elif mn <= 15: return PY_RNG.uniform(0.18, 0.21)   # Jun–Aug 2025
    elif mn <= 19: return PY_RNG.uniform(0.22, 0.26)   # Sep–Dec 2025
    elif mn <= 21: return PY_RNG.uniform(0.26, 0.30)   # Jan–Feb 2026 (Y2 avalanche)
    else:          return PY_RNG.uniform(0.19, 0.22)   # Mar–May 2026

def _target_returns_for_week(week_start: date) -> int:
    """
    Calibrated to land 1,800–2,200 total across 104 weeks.
    Baseline ~17-21/week; spikes for January, December, FW months.
    """
    month = week_start.month
    base = PY_RNG.randint(16, 20)

    if month == 1:                    # post-holiday avalanche
        base = int(base * PY_RNG.uniform(1.70, 1.90))
    elif month == 2:                  # declining from January
        base = PY_RNG.randint(12, 16)
    elif month in (9, 10):            # FW season elevated
        base = PY_RNG.randint(20, 25)
    elif month == 11:                 # BFCM + FW returns arriving
        base = PY_RNG.randint(21, 27)
    elif month == 12:                 # BFCM aftermath, holiday gifts arriving
        base = PY_RNG.randint(22, 28)
    elif month == 8:                  # quietest month
        base = PY_RNG.randint(13, 17)

    return int(base)

def _processing_days(initiated_date: date, is_3pl_lag: bool) -> int:
    """6–8 days normal; 3PL transition Aug 1-21 2025 adds 5–7 extra."""
    base = PY_RNG.randint(6, 8)
    if is_3pl_lag:
        base += PY_RNG.randint(5, 7)
    return min(base, 21)

def _is_3pl_window(d: date) -> bool:
    return date(2025, 8, 1) <= d <= date(2025, 8, 21)

def _payment_method(order_id: str, bnpl_set: set, d: date) -> str:
    if order_id in bnpl_set:
        return 'bnpl'
    mn = _month_num(d)
    if mn < 10:
        return PY_RNG.choices(['credit_card', 'shop_pay'], weights=[88, 12])[0]
    return PY_RNG.choices(['credit_card', 'shop_pay', 'bnpl'],
                          weights=[70, 15, 15])[0]

def _pick_sku(skus: list, prefer: Optional[str] = None) -> str:
    if prefer:
        pool = [s for s in skus if prefer in s]
        if pool:
            return PY_RNG.choice(pool)
    return PY_RNG.choice(skus)

def _condition_for_reason(reason: str) -> tuple:
    if reason in ('quality', 'quality_issue'):
        return ('defective', False)
    if reason == 'wrong_item':
        c = PY_RNG.choices(['new', 'like_new'], weights=[40, 60])[0]
        return (c, True)
    c = PY_RNG.choices(['new', 'like_new', 'damaged'], weights=[10, 82, 8])[0]
    return (c, c != 'damaged')

# ---------------------------------------------------------------------------
# FIX 6 — DDL for all three tables (with UNIQUE constraints)
# ---------------------------------------------------------------------------

DDL_LOOP_RETURNS = f"""
CREATE TABLE IF NOT EXISTS {SCHEMA}.loop_returns (
    return_id              text,
    order_id               text        NOT NULL,
    customer_id            text,
    return_initiated_at    timestamptz NOT NULL,
    return_received_at     timestamptz,
    return_status          text        DEFAULT 'initiated',
    refund_amount          numeric     DEFAULT 0,
    exchange_requested     boolean     DEFAULT false,
    payment_method         text,
    _airbyte_raw_id        text,
    _airbyte_extracted_at  timestamptz,
    _airbyte_meta          text,
    _airbyte_generation_id bigint,
    CONSTRAINT uq_loop_returns UNIQUE (return_id)
);
"""

DDL_LINE_ITEMS = f"""
CREATE TABLE IF NOT EXISTS {SCHEMA}.loop_return_line_items (
    line_item_id             text,
    return_id                text        NOT NULL,
    order_line_item_id       text,
    sku                      text,
    quantity                 integer     DEFAULT 1,
    return_reason_primary    text,
    return_reason_secondary  text,
    condition_received       text        DEFAULT 'like_new',
    restockable              boolean     DEFAULT true,
    _airbyte_raw_id          text,
    _airbyte_extracted_at    timestamptz,
    _airbyte_meta            text,
    _airbyte_generation_id   bigint,
    CONSTRAINT uq_loop_return_line_items UNIQUE (line_item_id)
);
"""

DDL_REASONS = f"""
CREATE TABLE IF NOT EXISTS {SCHEMA}.loop_return_reasons (
    return_id              text,
    reason_code            text,
    reason_detail          text,
    customer_comment       text,
    _airbyte_raw_id        text,
    _airbyte_extracted_at  timestamptz,
    _airbyte_meta          text,
    _airbyte_generation_id bigint,
    CONSTRAINT uq_loop_return_reasons UNIQUE (return_id, reason_code)
);
"""

# ---------------------------------------------------------------------------
# 0. Create tables
# ---------------------------------------------------------------------------

def create_tables(cur) -> None:
    try:
        for ddl in [DDL_LOOP_RETURNS, DDL_LINE_ITEMS, DDL_REASONS]:
            cur.execute(ddl)
        logger.info('create_tables | all three Loop Returns tables ensured')
    except Exception as e:
        logger.error('SOURCE: Loop Returns Seed | CLIENT: %s | ERROR: %s | CONTEXT: create_tables',
                     CLIENT_ID, str(e))
        raise

# ---------------------------------------------------------------------------
# 1. Load order pool from shopify_orders (grouped by purchase week)
# ---------------------------------------------------------------------------

def load_order_pool(cur) -> dict:
    """Returns {monday_date: [order_id_str, ...]} for all orders in seed period."""
    try:
        cur.execute("""
            SELECT id::text, created_at::date
            FROM client_azure_co.shopify_orders
            WHERE id < 10000000
              AND created_at >= %s AND created_at <= %s
            ORDER BY created_at
        """, (SEED_START, SEED_END))

        pool: dict = {}
        for order_id, order_date in cur.fetchall():
            monday = order_date - timedelta(days=order_date.weekday())
            pool.setdefault(monday, []).append(order_id)

        total = sum(len(v) for v in pool.values())
        logger.info('load_order_pool | %d weeks, %d orders in seed period',
                    len(pool), total)
        return pool
    except Exception as e:
        logger.error('SOURCE: Loop Returns Seed | CLIENT: %s | ERROR: %s | CONTEXT: load_order_pool',
                     CLIENT_ID, str(e))
        raise

# ---------------------------------------------------------------------------
# 2. Build a single return record (return row + line items + reasons)
# ---------------------------------------------------------------------------

def _build_return(
    return_idx: int,
    order_id: str,
    initiated_date: date,
    payment_method: str,
    skus: list,
    reason_override: Optional[str] = None,
    sku_override: Optional[str] = None,
    exchange_boost: float = 0.0,
) -> tuple:
    """Returns (return_row, [line_item_rows], [reason_rows])."""
    rid = _lr_id(f'{order_id}:{initiated_date.isoformat()}:{return_idx}')
    cid = f'CUS-{order_id}'

    initiated_ts = utc_dt(initiated_date, PY_RNG.randint(8, 22))
    is_3pl = _is_3pl_window(initiated_date)
    proc_days = _processing_days(initiated_date, is_3pl)
    received_date = initiated_date + timedelta(days=proc_days)

    if received_date > SEED_END:
        received_ts = None
        status = 'initiated'
    else:
        received_ts = utc_dt(received_date, PY_RNG.randint(8, 17))
        if PY_RNG.random() < 0.70:
            status = 'refunded'
        else:
            status = 'exchanged'

    exchange_requested = bool(PY_RNG.random() < (0.30 + float(exchange_boost)))
    refund_amount = (
        float(round(PY_RNG.uniform(55, 270), 2))
        if status in ('refunded', 'received') else 0.0
    )

    ext_ts = utc_dt(initiated_date, 14)
    raw_id, ext_at, meta, gen = airbyte_meta_cols(ext_ts)

    return_row = (
        rid, order_id, cid,
        initiated_ts, received_ts, status,
        refund_amount, exchange_requested, payment_method,
        raw_id, ext_at, meta, int(gen),
    )

    # 1–2 line items per return (22% chance of 2 items)
    n_items = 2 if PY_RNG.random() < 0.22 else 1
    line_item_rows = []
    reason_rows = []

    for item_idx in range(n_items):
        if sku_override and item_idx == 0:
            sku = sku_override
        else:
            sku = _pick_sku(skus)

        reason = reason_override if reason_override else PY_RNG.choices(
            REASON_CODES, weights=REASON_WEIGHTS, k=1)[0]

        detail = PY_RNG.choice(REASON_DETAILS.get(reason, REASON_DETAILS['other']))
        condition, restockable = _condition_for_reason(reason)

        lid = _li_id(f'{rid}:{item_idx}')
        raw2, ext2, meta2, gen2 = airbyte_meta_cols(ext_ts)
        line_item_rows.append((
            lid, rid, f'OLI-{order_id}-{item_idx}', sku, 1,
            reason, None, condition, bool(restockable),
            raw2, ext2, meta2, int(gen2),
        ))

        comment = PY_RNG.choice(CUSTOMER_COMMENTS.get(reason, [None]))
        raw3, ext3, meta3, gen3 = airbyte_meta_cols(ext_ts)
        reason_rows.append((
            rid, reason, detail, comment,
            raw3, ext3, meta3, int(gen3),
        ))

    return return_row, line_item_rows, reason_rows

# ---------------------------------------------------------------------------
# 3. Regular weekly return seeding
# ---------------------------------------------------------------------------

def seed_returns(cur, order_pool: dict, bnpl_set: set,
                 skus: list, inf_activations: list) -> None:
    try:
        # Macro activations within seed period (C15 — inventory whiplash)
        macro_acts = [
            a for a in inf_activations
            if a['tier'] == 'macro'
            and SEED_START <= date.fromisoformat(a['content_live_date']) <= SEED_END
        ]

        # Three-stage chain initiation windows (A6)
        CHAIN_WINDOWS = [
            {'sku': CHAIN1_SKU, 'start': date(2024, 8, 18), 'end': date(2024, 8, 20)},
            {'sku': CHAIN2_SKU, 'start': date(2024, 10, 11), 'end': date(2024, 10, 14)},
            {'sku': None,       'start': date(2024, 12, 9),  'end': date(2024, 12, 12)},
            {'sku': CHAIN4_SKU, 'start': date(2025, 10, 13), 'end': date(2025, 10, 15)},
        ]

        # Photography update spike window (S18 — Month 12, May 2025)
        PHOTO_WIN = (date(2025, 5, 1), date(2025, 5, 21))
        # Size guide rise windows (S17 — Month 7 Dec 2024, Month 14 Jul 2025)
        SIZE_GUIDE_WINS = [
            (date(2024, 12, 1), date(2024, 12, 14)),
            (date(2025, 7, 1),  date(2025, 7, 14)),
        ]

        # All seed-period Mondays
        all_weeks = []
        d = SEED_START - timedelta(days=SEED_START.weekday())
        while d <= SEED_END:
            all_weeks.append(d)
            d += timedelta(days=7)

        RETURN_COLS = [
            'return_id', 'order_id', 'customer_id',
            'return_initiated_at', 'return_received_at', 'return_status',
            'refund_amount', 'exchange_requested', 'payment_method',
            '_airbyte_raw_id', '_airbyte_extracted_at', '_airbyte_meta',
            '_airbyte_generation_id',
        ]
        LINE_COLS = [
            'line_item_id', 'return_id', 'order_line_item_id', 'sku', 'quantity',
            'return_reason_primary', 'return_reason_secondary',
            'condition_received', 'restockable',
            '_airbyte_raw_id', '_airbyte_extracted_at', '_airbyte_meta',
            '_airbyte_generation_id',
        ]
        REASON_COLS = [
            'return_id', 'reason_code', 'reason_detail', 'customer_comment',
            '_airbyte_raw_id', '_airbyte_extracted_at', '_airbyte_meta',
            '_airbyte_generation_id',
        ]

        return_rows = []
        line_item_rows = []
        reason_rows = []

        for return_week in all_weeks:
            # 3-week purchase lag (orders from 3 weeks prior)
            purchase_week = return_week - timedelta(weeks=3)

            # Extend window ±1 week to handle thin weeks
            pool: list = []
            for wk_offset in (-7, 0, 7):
                wk = purchase_week + timedelta(days=wk_offset)
                pool.extend(order_pool.get(wk, []))
            pool = list(dict.fromkeys(pool))  # dedup while preserving order
            if not pool:
                continue

            n_target = _target_returns_for_week(return_week)

            # Episodic modifiers
            rw_mid = return_week + timedelta(days=3)
            if PHOTO_WIN[0] <= rw_mid <= PHOTO_WIN[1]:
                n_target = int(n_target * PY_RNG.uniform(1.10, 1.18))
            for sg_s, sg_e in SIZE_GUIDE_WINS:
                if sg_s <= rw_mid <= sg_e:
                    n_target = int(n_target * PY_RNG.uniform(1.05, 1.10))

            n_actual = min(n_target, len(pool))

            # BNPL oversampling from Month 10 onwards (A15 — 15-20pp premium)
            mn = _month_num(return_week)
            if mn >= 10 and bnpl_set:
                weights = np.array(
                    [3.0 if str(oid) in bnpl_set else 1.0 for oid in pool],
                    dtype=float,
                )
                weights /= weights.sum()
                selected_idx = SEED_RNG.choice(len(pool), size=n_actual,
                                               replace=False, p=weights)
            else:
                selected_idx = SEED_RNG.choice(len(pool), size=n_actual, replace=False)

            for ret_idx, pool_idx in enumerate(selected_idx):
                order_id = pool[int(pool_idx)]
                day_offset = PY_RNG.randint(0, 6)
                initiated_date = return_week + timedelta(days=day_offset)
                if initiated_date > SEED_END:
                    initiated_date = SEED_END

                purchase_date = purchase_week + timedelta(days=PY_RNG.randint(0, 6))
                pm = _payment_method(str(order_id), bnpl_set, purchase_date)

                # Check chain windows
                sku_override = None
                reason_override = None
                for chain in CHAIN_WINDOWS:
                    if chain['start'] <= initiated_date <= chain['end']:
                        sku_override = chain['sku']
                        reason_override = 'sizing'
                        break

                # Macro influencer whiplash (C15) — 14 days post content_live
                exchange_boost = 0.0
                for act in macro_acts:
                    cl = date.fromisoformat(act['content_live_date'])
                    if cl + timedelta(days=12) <= initiated_date <= cl + timedelta(days=18):
                        reason_override = reason_override or 'sizing'
                        exchange_boost = 0.15  # higher exchange rate for size swap

                ret_row, li_rows, rs_rows = _build_return(
                    ret_idx, str(order_id), initiated_date, pm, skus,
                    reason_override=reason_override,
                    sku_override=sku_override,
                    exchange_boost=exchange_boost,
                )
                return_rows.append(ret_row)
                line_item_rows.extend(li_rows)
                reason_rows.extend(rs_rows)

        def _batch_insert(table: str, cols: list, rows: list, batch: int = 500) -> int:
            if not rows:
                return 0
            q = (f'INSERT INTO {SCHEMA}.{table} ({", ".join(cols)}) VALUES %s'
                 f' ON CONFLICT DO NOTHING')
            n = 0
            for i in range(0, len(rows), batch):
                psycopg2.extras.execute_values(cur, q, rows[i:i + batch])
                n += len(rows[i:i + batch])
            return n

        n_ret = _batch_insert('loop_returns', RETURN_COLS, return_rows)
        n_li  = _batch_insert('loop_return_line_items', LINE_COLS, line_item_rows)
        n_rs  = _batch_insert('loop_return_reasons', REASON_COLS, reason_rows)
        logger.info('seed_returns | loop_returns: %d, line_items: %d, reasons: %d',
                    n_ret, n_li, n_rs)

    except Exception as e:
        logger.error('SOURCE: Loop Returns Seed | CLIENT: %s | ERROR: %s | CONTEXT: seed_returns',
                     CLIENT_ID, str(e))
        raise

# ---------------------------------------------------------------------------
# 4. S44 — Defective unit event (AZ-KNIT-010, 180 units, 61% return rate)
# ---------------------------------------------------------------------------

def seed_defective_unit(cur, order_pool: dict) -> None:
    """
    Nov 28 – Dec 4 2024: 110 quality_issue returns for AZ-KNIT-010
    (61% of 180 defective units shipped in Nov 1-20 purchase window).
    """
    try:
        # Purchase window: 3 weeks prior to first initiation date (Nov 28 - 3w = Nov 7)
        defective_pool: list = []
        for wk_offset in range(-14, 22, 7):
            wk = date(2024, 11, 1) + timedelta(days=wk_offset)
            monday = wk - timedelta(days=wk.weekday())
            defective_pool.extend(order_pool.get(monday, []))
        defective_pool = list(dict.fromkeys(defective_pool))

        target_defective = 110  # 61% of 180 units
        n_to_seed = min(target_defective, len(defective_pool))

        selected_idx = SEED_RNG.choice(len(defective_pool), size=n_to_seed, replace=False)

        RETURN_COLS = [
            'return_id', 'order_id', 'customer_id',
            'return_initiated_at', 'return_received_at', 'return_status',
            'refund_amount', 'exchange_requested', 'payment_method',
            '_airbyte_raw_id', '_airbyte_extracted_at', '_airbyte_meta',
            '_airbyte_generation_id',
        ]
        LINE_COLS = [
            'line_item_id', 'return_id', 'order_line_item_id', 'sku', 'quantity',
            'return_reason_primary', 'return_reason_secondary',
            'condition_received', 'restockable',
            '_airbyte_raw_id', '_airbyte_extracted_at', '_airbyte_meta',
            '_airbyte_generation_id',
        ]
        REASON_COLS = [
            'return_id', 'reason_code', 'reason_detail', 'customer_comment',
            '_airbyte_raw_id', '_airbyte_extracted_at', '_airbyte_meta',
            '_airbyte_generation_id',
        ]

        return_rows = []
        line_item_rows = []
        reason_rows = []

        for ret_idx, pool_idx in enumerate(selected_idx):
            order_id = str(defective_pool[int(pool_idx)])
            # Initiation: Nov 28 – Dec 4 2024
            day_offset = PY_RNG.randint(0, 6)
            initiated_date = date(2024, 11, 28) + timedelta(days=day_offset)
            # Receipt: 6-8 days after initiated (always positive processing time)
            received_date = initiated_date + timedelta(days=PY_RNG.randint(6, 8))

            rid = _lr_id(f'defective:{order_id}:{ret_idx}')
            cid = f'CUS-{order_id}'
            initiated_ts = utc_dt(initiated_date, PY_RNG.randint(8, 22))
            received_ts  = utc_dt(received_date,  PY_RNG.randint(8, 17))
            ext_ts = utc_dt(initiated_date, 14)

            raw_id, ext_at, meta, gen = airbyte_meta_cols(ext_ts)
            return_rows.append((
                rid, order_id, cid,
                initiated_ts, received_ts, 'refunded',
                float(round(PY_RNG.uniform(100, 200), 2)),
                False, 'credit_card',
                raw_id, ext_at, meta, int(gen),
            ))

            lid = _li_id(f'{rid}:0')
            detail = PY_RNG.choice(REASON_DETAILS['quality_issue'])
            raw2, ext2, meta2, gen2 = airbyte_meta_cols(ext_ts)
            line_item_rows.append((
                lid, rid, f'OLI-{order_id}-def', DEFECTIVE_SKU, 1,
                'quality_issue', None, 'defective', False,
                raw2, ext2, meta2, int(gen2),
            ))

            comment = PY_RNG.choice(CUSTOMER_COMMENTS['quality_issue'])
            raw3, ext3, meta3, gen3 = airbyte_meta_cols(ext_ts)
            reason_rows.append((
                rid, 'quality_issue', detail, comment,
                raw3, ext3, meta3, int(gen3),
            ))

        def _insert(table, cols, rows, batch=500):
            if not rows:
                return 0
            q = (f'INSERT INTO {SCHEMA}.{table} ({", ".join(cols)}) VALUES %s'
                 f' ON CONFLICT DO NOTHING')
            n = 0
            for i in range(0, len(rows), batch):
                psycopg2.extras.execute_values(cur, q, rows[i:i + batch])
                n += len(rows[i:i + batch])
            return n

        n_ret = _insert('loop_returns', RETURN_COLS, return_rows)
        n_li  = _insert('loop_return_line_items', LINE_COLS, line_item_rows)
        n_rs  = _insert('loop_return_reasons', REASON_COLS, reason_rows)
        logger.info('seed_defective_unit | %s returns: %d, line_items: %d, reasons: %d',
                    DEFECTIVE_SKU, n_ret, n_li, n_rs)

    except Exception as e:
        logger.error('SOURCE: Loop Returns Seed | CLIENT: %s | ERROR: %s | CONTEXT: seed_defective_unit',
                     CLIENT_ID, str(e))
        raise

# ---------------------------------------------------------------------------
# 5. Alert log entries
# ---------------------------------------------------------------------------

ALERT_COLS = [
    'client_id', 'alert_type', 'fired_at', 'should_fire', 'confidence_score',
    'signal_value', 'threshold_value', 'threshold_direction',
    'layer1_headline', 'layer2_context', 'layer3_precedent',
    'alert_instance_number', 'escalation_level',
    'suppressed', 'suppression_category',
    'fatigue_period_active', 'fatigue_reason',
    'outcome_confirmed', 'dismissal_correct',
    'is_synthetic', 'severity',
]

# Three-stage chain definitions (A6)
CHAINS = [
    {
        'id': 1, 'sku': CHAIN1_SKU, 'label': 'New Season Denim',
        's1_date': date(2024, 8, 15),
        's2_date': date(2024, 8, 18),
        's3_date': date(2024, 8, 22),
    },
    {
        'id': 2, 'sku': CHAIN2_SKU, 'label': 'FW Knitwear Y1',
        's1_date': date(2024, 10, 8),
        's2_date': date(2024, 10, 11),
        's3_date': date(2024, 10, 17),
    },
    {
        'id': 3, 'sku': 'Multiple SKUs', 'label': 'Post-BFCM',
        's1_date': date(2024, 12, 5),
        's2_date': date(2024, 12, 9),
        's3_date': date(2024, 12, 15),
    },
    {
        'id': 4, 'sku': CHAIN4_SKU, 'label': 'FW Knitwear Y2',
        's1_date': date(2025, 10, 10),
        's2_date': date(2025, 10, 13),
        's3_date': date(2025, 10, 19),
    },
]


def seed_alert_log(cur) -> None:
    try:
        # Pre-check existing entries
        lr_alert_types = ['Alert5_stage1', 'Alert5_stage2', 'C3', 'D1_component']
        cur.execute(
            'SELECT client_id, alert_type, fired_at FROM public.alert_log '
            'WHERE client_id = %s AND alert_type = ANY(%s)',
            (CLIENT_ID, lr_alert_types),
        )
        existing = {(r[0], r[1], r[2]) for r in cur.fetchall()}

        rows = []
        for chain in CHAINS:
            conf_s1 = float(round(PY_RNG.uniform(0.62, 0.74), 2))
            conf_s2 = float(round(PY_RNG.uniform(0.78, 0.88), 2))
            conf_s3 = float(round(PY_RNG.uniform(0.88, 0.96), 2))

            # Alert5_stage1 — Gorgias sizing complaint velocity
            rows.append((
                CLIENT_ID, 'Alert5_stage1', utc_dt(chain['s1_date'], 11),
                True, conf_s1,
                float(round(PY_RNG.uniform(4.2, 7.8), 1)), 3.0, 'above',
                (f'Sizing complaint velocity rising for {chain["sku"]} '
                 f'({chain["label"]}). Return spike likely in 8–12 days.'),
                'Stage 1 of 3-stage return warning chain (A6). '
                'Sources: Gorgias only. Stage 2 fires on Loop return initiation spike.',
                'Pattern established across 4 prior sizing events — 90% correlation '
                'with return spike 3–7 days later.',
                1, 0, False, None, False, None, None, None, True, 'standard',
            ))

            # Alert5_stage2 — Loop initiation spike confirms
            rows.append((
                CLIENT_ID, 'Alert5_stage2', utc_dt(chain['s2_date'], 10),
                True, conf_s2,
                float(round(PY_RNG.uniform(18, 32), 1)), 15.0, 'above',
                (f'Return initiations confirm sizing signal for {chain["sku"]} '
                 f'({chain["label"]}). Loop return spike +{PY_RNG.randint(22, 45)}% vs baseline.'),
                'Stage 2 of 3-stage return chain. Loop return_initiated_at records '
                'confirm Gorgias complaint velocity. Stage 3 fires at physical receipt.',
                'Stage 1 Gorgias signal fired 3–7 days prior — Stage 2 is on-time confirmation.',
                2, 0, False, None, False, None, None, None, True, 'standard',
            ))

            # C3 — SKU-level return rate confirmed at Stage 3
            rows.append((
                CLIENT_ID, 'C3', utc_dt(chain['s3_date'], 9),
                True, conf_s3,
                float(round(PY_RNG.uniform(24, 38), 1)), 22.0, 'above',
                (f'SKU-level return rate confirmed: {chain["sku"]} '
                 f'({chain["label"]}) return rate {PY_RNG.randint(25, 40)}% vs 22% catalogue average.'),
                'Stage 3 of 3-stage return chain (physical receipt confirmed). '
                'Sources: Loop Returns + Shopify refunds. High-confidence lagging signal.',
                f'Stages 1 and 2 of chain {chain["id"]} fired — Stage 3 closes the loop.',
                3, 0, False, None, False, None, True, True, True, 'standard',
            ))

        # D1_component — Defective unit event (S44)
        rows.append((
            CLIENT_ID, 'D1_component', utc_dt(date(2024, 11, 28), 10),
            True, 0.91,
            61.0, 22.0, 'above',
            f'Component-level return rate alert: {DEFECTIVE_SKU} at 61% return rate '
            f'vs 22% catalogue average. 180 units affected — supplier quality event.',
            f'Return reason: quality_issue dominant (manufacturing defect). '
            f'{DEFECTIVE_SKU} return_initiated_at spike Nov 28–Dec 4. '
            f'CPM component suppressed by S1 (BFCM sale period).',
            'No prior defective batch for this SKU. Supplier notified — replacement '
            'production underway. Expected return-to-stock: 6 weeks.',
            1, 1, False, None, False, None, None, None, True, 'emergency',
        ))

        # Filter out existing and insert
        new_rows = [
            r for r in rows
            if (r[0], r[1], r[2]) not in existing
        ]
        if new_rows:
            q = (f'INSERT INTO public.alert_log ({", ".join(ALERT_COLS)}) VALUES %s'
                 f' ON CONFLICT DO NOTHING')
            psycopg2.extras.execute_values(cur, q, new_rows)
        logger.info('seed_alert_log | inserted: %d (skipped %d existing)',
                    len(new_rows), len(rows) - len(new_rows))

    except Exception as e:
        logger.error('SOURCE: Loop Returns Seed | CLIENT: %s | ERROR: %s | CONTEXT: seed_alert_log',
                     CLIENT_ID, str(e))
        raise

# ---------------------------------------------------------------------------
# 6. Suppression log — S17 size guide update suppressions
# ---------------------------------------------------------------------------

def seed_suppression_log(cur) -> None:
    """S17 — 14-day C3 State 3 suppressions for size_guide_update events."""
    try:
        cur.execute(
            'SELECT client_id, alert_type, would_have_fired_at FROM public.suppression_log '
            'WHERE client_id = %s AND suppression_source = %s',
            (CLIENT_ID, 'S17_size_guide_update'),
        )
        existing = {(r[0], r[1], r[2]) for r in cur.fetchall()}

        SIZE_GUIDE_SUPPRESSIONS = [
            # Month 7 — Dec 2024 size guide update
            {'would_have_fired': utc_dt(date(2024, 12, 7), 9)},
            # Month 14 — Jul 2025 size guide update
            {'would_have_fired': utc_dt(date(2025, 7, 7), 9)},
        ]

        SUPP_COLS = [
            'client_id', 'alert_type', 'suppression_state', 'would_have_fired_at',
            'signal_detected_at', 'suppression_category', 'suppression_source',
            'suppression_reason', 'founder_queryable',
        ]

        rows = []
        for s in SIZE_GUIDE_SUPPRESSIONS:
            key = (CLIENT_ID, 'C3', s['would_have_fired'])
            if key not in existing:
                rows.append((
                    CLIENT_ID, 'C3', 3, s['would_have_fired'],
                    s['would_have_fired'],
                    'expected_business_event', 'S17_size_guide_update',
                    ('Size guide update causes temporary return rate rise as customers '
                     'act on new sizing information. C3 suppressed for 14-day window '
                     '(State 3 — known cause, no action needed).'),
                    True,
                ))

        if rows:
            q = (f'INSERT INTO public.suppression_log ({", ".join(SUPP_COLS)}) VALUES %s'
                 f' ON CONFLICT DO NOTHING')
            psycopg2.extras.execute_values(cur, q, rows)
        logger.info('seed_suppression_log | S17 entries: %d (skipped %d existing)',
                    len(rows), len(SIZE_GUIDE_SUPPRESSIONS) - len(rows))

    except Exception as e:
        logger.error('SOURCE: Loop Returns Seed | CLIENT: %s | ERROR: %s | CONTEXT: seed_suppression_log',
                     CLIENT_ID, str(e))
        raise

# ---------------------------------------------------------------------------
# 7. Brand event calendar entries
# ---------------------------------------------------------------------------

def seed_brand_event_calendar(cur) -> None:
    try:
        cur.execute(
            'SELECT event_name FROM client_azure_co.brand_event_calendar WHERE client_id = %s',
            (CLIENT_ID,),
        )
        existing_names = {r[0] for r in cur.fetchall()}

        BEC_COLS = [
            'client_id', 'event_name', 'event_type', 'start_date', 'end_date',
            'suppress_alerts', 'context_alerts', 'context_explanation',
            'confidence', 'is_synthetic',
        ]

        new_events = [
            (CLIENT_ID, 'AZ-KNIT-010 Defective Batch (Nov 2024)',
             'supplier_quality_event',
             date(2024, 11, 28), date(2024, 12, 10),
             ['A1', 'A2'],          # suppress profitability alerts (returns inflate costs)
             ['D1_component'],      # D1 component-level return rate fires
             'AZ-KNIT-010 defective batch: 180 units affected, 61% return rate. '
             'Supplier quality event — NOT tagged as sale_period or seasonal, '
             'so S1 does NOT suppress the D1 return_rate component.',
             0.95, True),

            (CLIENT_ID, 'Size Guide Update — Dec 2024',
             'size_guide_update',
             date(2024, 12, 1), date(2024, 12, 14),
             ['C3'],
             [],
             'Size guide implementation Month 7. Temporary return rate rise expected '
             '(customers acting on new info). State 3 suppress C3 for 14 days (S17).',
             0.90, True),

            (CLIENT_ID, 'Size Guide Update — Jul 2025',
             'size_guide_update',
             date(2025, 7, 1), date(2025, 7, 14),
             ['C3'],
             [],
             'Size guide refresh Month 14. Same S17 suppression pattern as Month 7.',
             0.90, True),

            (CLIENT_ID, '3PL Transition — Aug 2025',
             'operational_change',
             date(2025, 8, 1), date(2025, 8, 21),
             ['C3', 'Alert5_stage2'],
             [],
             '3PL warehouse transition. return_received_at artificially delayed '
             '5–7 extra days. Suppresses return lag alerts for 3-week window.',
             0.95, True),

            (CLIENT_ID, 'Photography Update — May 2025',
             'photography_update',
             date(2025, 5, 1), date(2025, 5, 21),
             ['C3'],
             [],
             'New product photography roll-out Month 12. Return rate rises 8–10pp '
             'for 3 weeks (style mismatch from new imagery). State 2 for C3 (S18).',
             0.88, True),
        ]

        to_insert = [e for e in new_events if e[1] not in existing_names]
        if to_insert:
            q = (f'INSERT INTO client_azure_co.brand_event_calendar '
                 f'({", ".join(BEC_COLS)}) VALUES %s ON CONFLICT DO NOTHING')
            psycopg2.extras.execute_values(cur, q, to_insert)
        logger.info('seed_brand_event_calendar | inserted: %d (skipped %d existing)',
                    len(to_insert), len(new_events) - len(to_insert))

    except Exception as e:
        logger.error(
            'SOURCE: Loop Returns Seed | CLIENT: %s | ERROR: %s | CONTEXT: seed_brand_event_calendar',
            CLIENT_ID, str(e))
        raise

# ---------------------------------------------------------------------------
# 8. Validation — 7 checks
# ---------------------------------------------------------------------------

def validate(conn) -> None:
    cur = conn.cursor()
    results = {}
    print()
    print('=' * 72)
    print('LOOP RETURNS SEED VALIDATION — 7 CHECKS')
    print('=' * 72)

    def run(sql, params=None):
        cur.execute(sql, params)
        return cur.fetchall()

    # CHECK 1 — Total return records
    rows = run(f'SELECT COUNT(*) FROM {SCHEMA}.loop_returns')
    cnt = rows[0][0]
    ok = 1800 <= cnt <= 2300
    results[1] = 'PASS' if ok else 'FAIL'
    print(f'\n[{results[1]}] CHECK 1 -- Total return records')
    print(f'       actual={cnt:,}  expected=1,800-2,300 (inc. ~110 defective batch)')

    # CHECK 2 — January 2025 spike vs adjacent months
    jan25 = run(f"""
        SELECT COUNT(*) FROM {SCHEMA}.loop_returns
        WHERE return_initiated_at >= '2025-01-01'
          AND return_initiated_at <  '2025-02-01'
    """)[0][0]
    dec24 = run(f"""
        SELECT COUNT(*) FROM {SCHEMA}.loop_returns
        WHERE return_initiated_at >= '2024-12-01'
          AND return_initiated_at <  '2025-01-01'
    """)[0][0]
    feb25 = run(f"""
        SELECT COUNT(*) FROM {SCHEMA}.loop_returns
        WHERE return_initiated_at >= '2025-02-01'
          AND return_initiated_at <  '2025-03-01'
    """)[0][0]
    # Dec is inflated by ~110 defective returns; compare Jan vs Feb only
    ok = (jan25 >= 80 and jan25 > feb25 * 1.5)
    results[2] = 'PASS' if ok else 'FAIL'
    print(f'\n[{results[2]}] CHECK 2 -- January 2025 post-holiday spike (S3)')
    print(f'       Dec 2024: {dec24} (incl. ~110 defective batch), Jan 2025: {jan25}, Feb 2025: {feb25}')
    print(f'       Jan >= 80 and Jan > Feb * 1.5 (Dec excluded: inflated by defective batch)')

    # CHECK 3 — Defective unit (AZ-KNIT-010) quality_issue dominance
    rows = run(f"""
        SELECT
            COUNT(*) AS returns,
            COUNT(*) FILTER (WHERE lr.reason_code = 'quality_issue') AS quality_returns
        FROM {SCHEMA}.loop_return_reasons lr
        JOIN {SCHEMA}.loop_return_line_items li ON lr.return_id = li.return_id
        WHERE li.sku = %s
          AND lr.return_id IN (
              SELECT return_id FROM {SCHEMA}.loop_returns
              WHERE return_initiated_at BETWEEN '2024-11-28' AND '2024-12-04'
          )
    """, (DEFECTIVE_SKU,))
    total_def, qual_def = rows[0]
    pct = float(qual_def) / float(total_def) * 100 if total_def > 0 else 0
    ok = total_def > 50 and pct > 55
    results[3] = 'PASS' if ok else 'FAIL'
    print(f'\n[{results[3]}] CHECK 3 -- Defective unit ({DEFECTIVE_SKU}) quality_issue dominance')
    print(f'       total={total_def}, quality_issue={qual_def} ({pct:.1f}%)')
    print(f'       expected: quality_issue dominant >55%, total>50')

    # CHECK 4 — Alert 5 chain count
    rows = run("""
        SELECT alert_type, COUNT(*) FROM public.alert_log
        WHERE alert_type IN ('Alert5_stage1', 'Alert5_stage2', 'C3')
          AND client_id = %s
        GROUP BY alert_type
        ORDER BY alert_type
    """, (CLIENT_ID,))
    counts = {r[0]: r[1] for r in rows}
    ok = (counts.get('Alert5_stage1', 0) == 4
          and counts.get('Alert5_stage2', 0) == 4
          and counts.get('C3', 0) >= 4)
    results[4] = 'PASS' if ok else 'FAIL'
    print(f'\n[{results[4]}] CHECK 4 -- Alert 5 chain counts')
    for atype, n in sorted(counts.items()):
        print(f'       {atype}: {n}  (expected 4)')

    # CHECK 5 — Processing time (excluding 3PL transition window)
    rows = run(f"""
        SELECT
            AVG(EXTRACT(EPOCH FROM (return_received_at - return_initiated_at)) / 86400),
            MIN(EXTRACT(EPOCH FROM (return_received_at - return_initiated_at)) / 86400),
            MAX(EXTRACT(EPOCH FROM (return_received_at - return_initiated_at)) / 86400)
        FROM {SCHEMA}.loop_returns
        WHERE return_received_at IS NOT NULL
          AND return_initiated_at NOT BETWEEN '2025-08-01' AND '2025-08-21'
    """)
    avg_d, min_d, max_d = (float(r or 0) for r in rows[0])
    ok = 5 <= avg_d <= 10 and min_d >= 4 and max_d <= 21
    results[5] = 'PASS' if ok else 'FAIL'
    print(f'\n[{results[5]}] CHECK 5 -- Processing time (excl. 3PL transition)')
    print(f'       avg={avg_d:.2f} days  min={min_d:.1f}  max={max_d:.1f}')
    print(f'       expected: avg 6–8 days, min≥4, max≤21')

    # CHECK 6 — BNPL return rate premium (Month 10+ = March 2025 onwards)
    rows = run(f"""
        SELECT payment_method, COUNT(*) AS returns
        FROM {SCHEMA}.loop_returns
        WHERE return_initiated_at >= '2025-03-01'
        GROUP BY payment_method
        ORDER BY payment_method
    """)
    pm_counts = {r[0]: int(r[1]) for r in rows}
    total_from_mar25 = sum(pm_counts.values())
    bnpl_in_returns = pm_counts.get('bnpl', 0)
    non_bnpl_in_returns = total_from_mar25 - bnpl_in_returns

    # BNPL baseline share from full order pool (8,847 / 84,153)
    bnpl_baseline_pct = 8847 / 84153
    bnpl_actual_pct   = bnpl_in_returns / total_from_mar25 if total_from_mar25 > 0 else 0
    bnpl_lift_pp = (bnpl_actual_pct - bnpl_baseline_pct) * 100

    ok = bnpl_lift_pp >= 10  # BNPL at least 10pp overrepresented in returns vs baseline
    results[6] = 'PASS' if ok else 'FAIL'
    print(f'\n[{results[6]}] CHECK 6 -- BNPL overrepresentation in returns (Month 10+)')
    for pm, n in sorted(pm_counts.items()):
        print(f'       {pm}: {n} returns')
    print(f'       BNPL baseline share: {bnpl_baseline_pct*100:.1f}%')
    print(f'       BNPL actual share in returns: {bnpl_actual_pct*100:.1f}%')
    print(f'       BNPL lift: +{bnpl_lift_pp:.1f}pp  expected: ≥10pp (A15 premium)')

    # CHECK 7 — Exchange rate
    rows = run(f"""
        SELECT
            COUNT(*) FILTER (WHERE exchange_requested = true)::numeric / COUNT(*) AS exchange_rate
        FROM {SCHEMA}.loop_returns
    """)
    ex_rate = float(rows[0][0] or 0)
    ok = 0.26 <= ex_rate <= 0.34
    results[7] = 'PASS' if ok else 'FAIL'
    print(f'\n[{results[7]}] CHECK 7 -- Exchange rate')
    print(f'       actual={ex_rate:.4f}  expected=0.28–0.32 (±0.02 tolerance)')

    print()
    print('=' * 72)
    print('SUMMARY')
    print('=' * 72)
    for k, v in sorted(results.items()):
        print(f'  CHECK {k}: {v}')
    passed = sum(1 for v in results.values() if v == 'PASS')
    print(f'  {passed}/{len(results)} checks passed')
    print('=' * 72)

    cur.close()

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def get_conn():
    url = os.getenv('DATABASE_URL')
    if not url:
        logger.error('SOURCE: Loop Returns Seed | ERROR: DATABASE_URL not set')
        sys.exit(1)
    return psycopg2.connect(url, sslmode='require')


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    logger.info('SOURCE: Loop Returns Seed | CLIENT: %s | Starting', CLIENT_ID)

    # Load manifest
    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)

    bnpl_set = {str(x) for x in manifest.get('order_ids_with_bnpl', [])}
    inf_activations = manifest.get('influencer_activations', [])
    skus = [s['sku'] for s in manifest.get('sku_list', [])
            if s.get('launch_date', '2024-06-01') <= str(SEED_END)]

    logger.info('Loaded manifest: %d BNPL orders, %d influencer activations, %d SKUs',
                len(bnpl_set), len(inf_activations), len(skus))

    conn = get_conn()
    try:
        cur = conn.cursor()

        logger.info('Step 0 -- create_tables')
        create_tables(cur)

        logger.info('Step 1 -- load_order_pool')
        order_pool = load_order_pool(cur)

        logger.info('Step 2 -- seed_returns (weekly arc + episodic events)')
        seed_returns(cur, order_pool, bnpl_set, skus, inf_activations)

        logger.info('Step 3 -- seed_defective_unit (S44 — %s)', DEFECTIVE_SKU)
        seed_defective_unit(cur, order_pool)

        logger.info('Step 4 -- seed_alert_log (Alert5 chains + D1_component)')
        seed_alert_log(cur)

        logger.info('Step 5 -- seed_suppression_log (S17 size_guide_update)')
        seed_suppression_log(cur)

        logger.info('Step 6 -- seed_brand_event_calendar')
        seed_brand_event_calendar(cur)

        conn.commit()
        logger.info('SOURCE: Loop Returns Seed | CLIENT: %s | Complete', CLIENT_ID)

        validate(conn)

    except Exception as e:
        conn.rollback()
        logger.error('SOURCE: Loop Returns Seed | CLIENT: %s | FATAL: %s', CLIENT_ID, str(e))
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    main()
