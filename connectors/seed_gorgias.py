"""
Profit Sentinel -- Gorgias Seed Script
Brand: Azure & Co (client_azure_co)
Date range: June 1 2024 -- May 31 2026 (24 months)

Seeds:
  client_azure_co.gorgias_tickets
  client_azure_co.gorgias_ticket_messages
  client_azure_co.gorgias_ticket_tags
  client_azure_co.gorgias_tag_normalisation
  public.alert_log  (vip_ticket_unresolved x10, H14 x2, D1_gorgias_evidence x1, H16 x1)
  client_azure_co.dq_metric_scores  (GD2, GD3, GD6 entries)

Chain dates (from seed_loop_returns.py -- must precede Loop s2_date by 3-7 days):
  Chain 1 s1=2024-08-15  Loop s2=2024-08-18  (Gorgias spike Aug 15-17)
  Chain 2 s1=2024-10-08  Loop s2=2024-10-11  (Gorgias spike Oct 8-10)
  Chain 3 s1=2024-12-05  Loop s2=2024-12-09  (Gorgias spike Dec 5-8)
  Chain 4 s1=2025-10-10  Loop s2=2025-10-13  (Gorgias spike Oct 10-12)
"""

import json, logging, os, random, sys, uuid
from datetime import date, datetime, timedelta, timezone
from typing import Optional

import numpy as np
import psycopg2, psycopg2.extras
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CLIENT_ID     = 'azure_co'
SCHEMA        = 'client_azure_co'
SEED_START    = date(2024, 6, 1)
SEED_END      = date(2026, 5, 31)
SEED_RNG      = np.random.default_rng(76)
PY_RNG        = random.Random(76)
MANIFEST_PATH = os.path.join(os.path.dirname(__file__), 'seed_manifest_shopify.json')

# Month 5 = Oct 2024 (automation enabled)
AUTOMATION_START = date(2024, 10, 1)
# Month 10 = Mar 2025 (CSAT -> NPS transition)
NPS_START        = date(2025, 3, 1)
# Month 3 = Aug 2024 (VIP routing)
VIP_ROUTING_START = date(2024, 8, 1)

# ---------------------------------------------------------------------------
# DDL
# ---------------------------------------------------------------------------

DDL_GORGIAS_TICKETS = f"""
CREATE TABLE IF NOT EXISTS {SCHEMA}.gorgias_tickets (
    ticket_id              text        NOT NULL,
    customer_id            text,
    klaviyo_profile_id     text,
    created_at             timestamptz NOT NULL,
    updated_at             timestamptz,
    resolved_at            timestamptz,
    status                 text        DEFAULT 'resolved',
    channel                text,
    subject                text,
    first_response_at      timestamptz,
    first_response_type    text        DEFAULT 'human',
    resolved_by            text,
    csat_score             numeric,
    nps_score              integer,
    priority_queue         boolean     DEFAULT false,
    last_ticket_reason     text,
    ticket_count_lifetime  integer     DEFAULT 1,
    resolution_hours       numeric,
    _airbyte_raw_id        text,
    _airbyte_extracted_at  timestamptz,
    _airbyte_meta          text,
    _airbyte_generation_id bigint,
    CONSTRAINT uq_gorgias_tickets UNIQUE (ticket_id)
);"""

DDL_GORGIAS_TICKET_MESSAGES = f"""
CREATE TABLE IF NOT EXISTS {SCHEMA}.gorgias_ticket_messages (
    message_id             text        NOT NULL,
    ticket_id              text        NOT NULL,
    created_at             timestamptz NOT NULL,
    message_type           text,
    is_from_customer       boolean     DEFAULT true,
    body_text              text,
    agent_id               text,
    _airbyte_raw_id        text,
    _airbyte_extracted_at  timestamptz,
    _airbyte_meta          text,
    _airbyte_generation_id bigint,
    CONSTRAINT uq_gorgias_ticket_messages UNIQUE (message_id)
);"""

DDL_GORGIAS_TICKET_TAGS = f"""
CREATE TABLE IF NOT EXISTS {SCHEMA}.gorgias_ticket_tags (
    ticket_id              text        NOT NULL,
    tag                    text        NOT NULL,
    tagged_at              timestamptz,
    _airbyte_raw_id        text,
    _airbyte_extracted_at  timestamptz,
    _airbyte_meta          text,
    _airbyte_generation_id bigint,
    CONSTRAINT uq_gorgias_ticket_tags UNIQUE (ticket_id, tag)
);"""

DDL_GORGIAS_TAG_NORMALISATION = f"""
CREATE TABLE IF NOT EXISTS {SCHEMA}.gorgias_tag_normalisation (
    raw_tag        text        NOT NULL,
    canonical_tag  text        NOT NULL,
    category       text,
    created_at     timestamptz DEFAULT now(),
    CONSTRAINT uq_gorgias_tag_normalisation UNIQUE (raw_tag)
);"""

# ---------------------------------------------------------------------------
# Tag normalisation data (40+ entries -- GD5)
# ---------------------------------------------------------------------------

TAG_NORMALISATION = [
    # Sizing
    ('runs small',                 'sizing_issue',         'sizing'),
    ('runs small -- tops',         'sizing_issue_tops',    'sizing'),
    ('fit issue -- tops',          'sizing_issue_tops',    'sizing'),
    ('too small',                  'sizing_issue',         'sizing'),
    ('too big',                    'sizing_issue',         'sizing'),
    ('sizing',                     'sizing_issue',         'sizing'),
    ('fit',                        'sizing_issue',         'sizing'),
    ('wrong size',                 'sizing_issue',         'sizing'),
    ('size exchange',              'sizing_issue',         'sizing'),
    ('runs large',                 'sizing_issue',         'sizing'),
    ('too long',                   'sizing_issue',         'sizing'),
    ('too short',                  'sizing_issue',         'sizing'),
    ('fits small',                 'sizing_issue',         'sizing'),
    ('size guide',                 'sizing_issue',         'sizing'),
    ('sizing_issue_tops',          'sizing_issue_tops',    'sizing'),
    # Product quality
    ('fabric quality',             'product_quality',      'quality'),
    ('defective',                  'product_quality',      'quality'),
    ('not as described',           'product_quality',      'quality'),
    ('color different',            'product_quality',      'quality'),
    ('pilling',                    'product_quality',      'quality'),
    ('seam issue',                 'product_quality',      'quality'),
    ('wrong colour',               'product_quality',      'quality'),
    ('colour fade',                'product_quality',      'quality'),
    ('wrong fabric weight',        'product_quality',      'quality'),
    ('wrong fabric',               'product_quality',      'quality'),
    ('broken zip',                 'product_quality',      'quality'),
    ('missing button',             'product_quality',      'quality'),
    # Order status
    ('where is my order',          'order_status',         'fulfillment'),
    ('wimo',                       'order_status',         'fulfillment'),
    ('tracking',                   'order_status',         'fulfillment'),
    ('order not arrived',          'order_status',         'fulfillment'),
    ('tracking not updating',      'order_status',         'fulfillment'),
    ('delivery attempt failed',    'order_status',         'fulfillment'),
    # Shipping
    ('late delivery',              'shipping_delay',       'shipping'),
    ('not delivered',              'shipping_delay',       'shipping'),
    ('damaged in transit',         'shipping_damage',      'shipping'),
    ('customs held',               'shipping_delay',       'shipping'),
    # Returns / refunds
    ('refund status',              'return_request',       'returns'),
    ('return label',               'return_request',       'returns'),
    ('exchange request',           'return_request',       'returns'),
    ('where is refund',            'return_request',       'returns'),
    # Order management
    ('cancel order',               'order_cancellation',   'orders'),
    ('missing item',               'fulfillment_error',    'orders'),
    ('wrong item',                 'fulfillment_error',    'orders'),
    # Discounts
    ('discount not working',       'discount_code',        'promotions'),
    ('promo code',                 'discount_code',        'promotions'),
    # Product feedback (B6 -- formal occasion)
    ('too casual',                 'product_feedback',     'feedback'),
    ('not occasion appropriate',   'product_feedback',     'feedback'),
    # General
    ('gift wrapping',              'other',                'general'),
    ('account help',               'other',                'general'),
]
# NOT included (intentionally unmapped -- triggers H14):
#   'outerwear fit', 'layering issue'  (Sep 2024 FW launch)
#   'winter weight', 'thermal lining'  (Sep 2025 FW launch)
#   'wrong_brand'  (May 2025 competitor confusion)

# ---------------------------------------------------------------------------
# Ticket content data
# ---------------------------------------------------------------------------

REASON_CODES   = ['sizing_issue', 'order_status', 'return_request',
                   'product_quality', 'shipping_delay', 'discount_code', 'other']
REASON_WEIGHTS = [0.31, 0.18, 0.14, 0.12, 0.09, 0.06, 0.10]

CHANNELS        = ['email', 'chat', 'instagram', 'sms']
CHANNEL_WEIGHTS = [0.58, 0.24, 0.11, 0.07]

REASON_TAGS = {
    'sizing_issue':    ['runs small', 'too small', 'too big', 'sizing', 'wrong size', 'fit'],
    'order_status':    ['where is my order', 'wimo', 'tracking', 'order not arrived'],
    'return_request':  ['refund status', 'return label', 'exchange request'],
    'product_quality': ['fabric quality', 'pilling', 'not as described', 'seam issue'],
    'shipping_delay':  ['late delivery', 'not delivered'],
    'discount_code':   ['discount not working', 'promo code'],
    'other':           ['gift wrapping', 'account help'],
}

SUBJECTS = {
    'sizing_issue':    ['Does this run true to size?', 'Sizing question before I order',
                        'Fit issue with my recent order', 'Need size advice'],
    'order_status':    ['Where is my order?', 'Order update needed',
                        'Tracking number not updating', 'Package not arrived'],
    'return_request':  ['How do I return?', 'Return request', 'Refund status update',
                        'Exchange request'],
    'product_quality': ['Quality issue with my item', 'Item arrived damaged',
                        'Not as shown on website', 'Defective product received'],
    'shipping_delay':  ['Shipping delay?', 'Delivery is very late',
                        'Package has not arrived', 'Customs holding my order'],
    'discount_code':   ['Discount code not working', 'Promo code issue',
                        'Sale price not applying'],
    'other':           ['Question about my order', 'Need help', 'Account question'],
}

AGENT_IDS = [f'AGT-{i:03d}' for i in range(1, 11)]

INBOUND_BODIES = {
    'sizing_issue':    'Hi, I usually wear a medium but I\'m not sure about this item. Does it run true to size? Thanks!',
    'order_status':    'Hi, I placed an order a few days ago and haven\'t received a tracking update. Can you help?',
    'return_request':  'Hi, I\'d like to return my recent order. Could you please send me a return label?',
    'product_quality': 'Hi, my order arrived but there seems to be a quality issue. I\'m quite disappointed.',
    'shipping_delay':  'Hi, my order was supposed to arrive days ago. Could you please check on it?',
    'discount_code':   'Hi, the discount code I have doesn\'t seem to be working at checkout. Can you help?',
    'other':           'Hi, I have a question about my recent order. Could someone assist me?',
}

OUTBOUND_BODIES = {
    'sizing_issue':    'Hi there! Thanks for reaching out. This style does run slightly small -- we\'d recommend sizing up.',
    'order_status':    'Hi! Thanks for your patience. I can see your order is currently in transit. Here\'s your tracking info.',
    'return_request':  'Hi! Of course, I\'d be happy to help you with your return. I\'ve sent the return label to your email.',
    'product_quality': 'Hi, I\'m so sorry to hear about this. I\'ve arranged a replacement and a return label for you.',
    'shipping_delay':  'Hi, I apologise for the inconvenience. I\'ve raised this with our carrier and will update you shortly.',
    'discount_code':   'Hi! No worries -- I can see the code is valid. Let me apply it to your order manually.',
    'other':           'Hi! Happy to help. Could you please provide more details so I can assist you better?',
}

# ---------------------------------------------------------------------------
# Helpers -- copied exactly from seed_shopify.py (FIX 2, FIX 4)
# ---------------------------------------------------------------------------

def airbyte_meta_cols(extracted_at: datetime) -> tuple:
    return (str(uuid.uuid4()), extracted_at, '{}', 0)

def utc_dt(d: date, hour: int = 14, minute: int = 0) -> datetime:
    return datetime(d.year, d.month, d.day, hour, minute, 0, tzinfo=timezone.utc)

def _nearest_pd_corr(m: np.ndarray, eps: float = 1e-4) -> np.ndarray:
    vals, vecs = np.linalg.eigh(m)
    vals_clipped = np.maximum(vals, eps)
    pd_m = vecs @ np.diag(vals_clipped) @ vecs.T
    pd_m = (pd_m + pd_m.T) / 2
    d = np.sqrt(np.diag(pd_m))
    pd_m = pd_m / np.outer(d, d)
    return pd_m

_GG_CORR_DESIGN = np.array([
    [1.00, -0.55],
    [-0.55,  1.00],
])
GG_CORR = _nearest_pd_corr(_GG_CORR_DESIGN)

def _month_num(d: date) -> int:
    return (d.year - SEED_START.year) * 12 + d.month - SEED_START.month + 1

# Deterministic UUID namespace (FIX 5 -- no GENERATED ALWAYS conflict)
_GG_NS = uuid.UUID('f2f2f2f2-dead-beef-cafe-000000000006')

def _ticket_id(key: str) -> str:
    return str(uuid.uuid5(_GG_NS, key))

def _msg_id(key: str) -> str:
    return str(uuid.uuid5(_GG_NS, f'msg:{key}'))

# ---------------------------------------------------------------------------
# Chain spike windows (aligned with seed_loop_returns.py CHAIN s1_date)
# ---------------------------------------------------------------------------

CHAIN_SPIKES = [
    {'start': date(2024,  8, 15), 'end': date(2024,  8, 17),
     'tags': ['sizing_issue', 'runs small'],            'mult': 2.8},
    {'start': date(2024, 10,  8), 'end': date(2024, 10, 10),
     'tags': ['sizing_issue_tops', 'fit issue -- tops'], 'mult': 2.4},
    {'start': date(2024, 12,  5), 'end': date(2024, 12,  8),
     'tags': ['sizing_issue', 'too big', 'too small'],  'mult': 3.2},
    {'start': date(2025, 10, 10), 'end': date(2025, 10, 12),
     'tags': ['sizing_issue_tops', 'runs small -- tops'], 'mult': 2.6},
]

# BFCM windows
BFCM_Y1 = (date(2024, 11, 27), date(2024, 12,  2))
BFCM_Y2 = (date(2025, 11, 27), date(2025, 12,  2))
BFCM_Y1_DIST   = {'order_status': 0.45, 'return_request': 0.22,
                   'discount_code': 0.18, 'sizing_issue': 0.15}
BFCM_Y2_DIST   = {'order_status': 0.40, 'return_request': 0.24,
                   'discount_code': 0.16, 'sizing_issue': 0.20}

# Defective unit window (S44 -- Nov 28-Dec 4 2024, quality complaint spike)
DEFECTIVE_WIN = (date(2024, 11, 28), date(2024, 12, 4))
DEFECTIVE_TAGS = ['defective', 'fabric quality', 'wrong fabric weight']

# H14 unmapped tag windows (new vocabulary triggers, NOT in normalisation table)
H14_WIN_1 = (date(2024, 9,  1), date(2024, 9, 30))  # Sep 2024 FW launch prep
H14_WIN_2 = (date(2025, 9,  1), date(2025, 9, 30))  # Sep 2025 FW launch prep
H14_TAGS_1 = ['outerwear fit', 'layering issue']
H14_TAGS_2 = ['winter weight', 'thermal lining']

# Competitor confusion window (May 2025 -- wrong brand)
WRONG_BRAND_WIN = (date(2025, 5,  1), date(2025, 5, 31))

# ---------------------------------------------------------------------------
# Correlated noise generator for response_time and csat signal
# ---------------------------------------------------------------------------

def _generate_ticket_signals(n: int) -> list:
    """Return (n, 2) list of correlated noise multipliers as Python floats."""
    L = np.linalg.cholesky(GG_CORR)
    noise = SEED_RNG.standard_normal((n, 2))
    corr = noise @ L.T
    return np.clip(1.0 + corr * 0.15, 0.60, 1.60).tolist()

# ---------------------------------------------------------------------------
# 0. Create tables (FIX 6)
# ---------------------------------------------------------------------------

def create_tables(cur) -> None:
    try:
        for ddl in [DDL_GORGIAS_TICKETS, DDL_GORGIAS_TICKET_MESSAGES,
                    DDL_GORGIAS_TICKET_TAGS, DDL_GORGIAS_TAG_NORMALISATION]:
            cur.execute(ddl)
        logger.info('create_tables | all four Gorgias tables ensured')
    except Exception as e:
        logger.error('SOURCE: Gorgias Seed | CLIENT: %s | ERROR: %s | CONTEXT: create_tables',
                     CLIENT_ID, str(e))
        raise

# ---------------------------------------------------------------------------
# 1. Seed tag normalisation (GD5)
# ---------------------------------------------------------------------------

def seed_tag_normalisation(cur) -> None:
    try:
        cur.execute(f'SELECT raw_tag FROM {SCHEMA}.gorgias_tag_normalisation WHERE 1=1')
        existing = {r[0] for r in cur.fetchall()}

        rows = [
            (raw, canonical, category)
            for raw, canonical, category in TAG_NORMALISATION
            if raw not in existing
        ]
        if rows:
            psycopg2.extras.execute_values(
                cur,
                f'INSERT INTO {SCHEMA}.gorgias_tag_normalisation '
                f'(raw_tag, canonical_tag, category) VALUES %s ON CONFLICT DO NOTHING',
                rows,
            )
        logger.info('seed_tag_normalisation | inserted: %d (skipped %d existing)',
                    len(rows), len(TAG_NORMALISATION) - len(rows))
    except Exception as e:
        logger.error('SOURCE: Gorgias Seed | CLIENT: %s | ERROR: %s | CONTEXT: seed_tag_normalisation',
                     CLIENT_ID, str(e))
        raise

# ---------------------------------------------------------------------------
# 2. Seed tickets (main loop -- day by day across 24 months)
# ---------------------------------------------------------------------------

def seed_tickets(cur, customer_ids: list, vip_set: set) -> int:
    try:
        TICKET_COLS = [
            'ticket_id', 'customer_id', 'klaviyo_profile_id',
            'created_at', 'updated_at', 'resolved_at',
            'status', 'channel', 'subject',
            'first_response_at', 'first_response_type', 'resolved_by',
            'csat_score', 'nps_score', 'priority_queue',
            'last_ticket_reason', 'ticket_count_lifetime', 'resolution_hours',
            '_airbyte_raw_id', '_airbyte_extracted_at', '_airbyte_meta',
            '_airbyte_generation_id',
        ]
        MSG_COLS = [
            'message_id', 'ticket_id', 'created_at',
            'message_type', 'is_from_customer', 'body_text', 'agent_id',
            '_airbyte_raw_id', '_airbyte_extracted_at', '_airbyte_meta',
            '_airbyte_generation_id',
        ]
        TAG_COLS = [
            'ticket_id', 'tag', 'tagged_at',
            '_airbyte_raw_id', '_airbyte_extracted_at', '_airbyte_meta',
            '_airbyte_generation_id',
        ]

        # Correlated noise signals -- pre-generate for the full period
        total_days = (SEED_END - SEED_START).days + 1
        max_daily  = 70  # upper bound per day for pre-allocation
        signals = _generate_ticket_signals(total_days * max_daily)
        sig_idx = 0

        # Precompute chain spike lookup: date -> spike info
        chain_days: dict[date, dict] = {}
        for ch in CHAIN_SPIKES:
            d = ch['start']
            while d <= ch['end']:
                chain_days[d] = ch
                d += timedelta(days=1)

        # Precompute BFCM day sets
        bfcm_y1_days: set[date] = set()
        bfcm_y2_days: set[date] = set()
        for bfcm_start, bfcm_end, bfcm_set in [
            (BFCM_Y1[0], BFCM_Y1[1], bfcm_y1_days),
            (BFCM_Y2[0], BFCM_Y2[1], bfcm_y2_days),
        ]:
            d = bfcm_start
            while d <= bfcm_end:
                bfcm_set.add(d)
                d += timedelta(days=1)

        # Defective unit day set
        defective_days: set[date] = set()
        d = DEFECTIVE_WIN[0]
        while d <= DEFECTIVE_WIN[1]:
            defective_days.add(d)
            d += timedelta(days=1)

        # H14 unmapped tag day sets
        h14_days_1: set[date] = set()
        h14_days_2: set[date] = set()
        for win, day_set in [(H14_WIN_1, h14_days_1), (H14_WIN_2, h14_days_2)]:
            d = win[0]
            while d <= win[1]:
                day_set.add(d)
                d += timedelta(days=1)

        # Wrong-brand day set
        wrong_brand_days: set[date] = set()
        d = WRONG_BRAND_WIN[0]
        while d <= WRONG_BRAND_WIN[1]:
            wrong_brand_days.add(d)
            d += timedelta(days=1)

        # Customer ticket count tracker
        cust_ticket_counts: dict[str, int] = {}

        ticket_rows = []
        msg_rows    = []
        tag_rows    = []
        total_inserted = 0

        def _flush(force: bool = False):
            nonlocal total_inserted
            if not ticket_rows and not force:
                return
            if ticket_rows:
                psycopg2.extras.execute_values(
                    cur,
                    f'INSERT INTO {SCHEMA}.gorgias_tickets ({", ".join(TICKET_COLS)}) '
                    f'VALUES %s ON CONFLICT DO NOTHING',
                    ticket_rows,
                )
                total_inserted += len(ticket_rows)
            if msg_rows:
                psycopg2.extras.execute_values(
                    cur,
                    f'INSERT INTO {SCHEMA}.gorgias_ticket_messages ({", ".join(MSG_COLS)}) '
                    f'VALUES %s ON CONFLICT DO NOTHING',
                    msg_rows,
                )
            if tag_rows:
                psycopg2.extras.execute_values(
                    cur,
                    f'INSERT INTO {SCHEMA}.gorgias_ticket_tags ({", ".join(TAG_COLS)}) '
                    f'VALUES %s ON CONFLICT DO NOTHING',
                    tag_rows,
                )
            ticket_rows.clear()
            msg_rows.clear()
            tag_rows.clear()

        current_day = SEED_START
        day_idx     = 0
        wrong_brand_count = 0

        while current_day <= SEED_END:
            mn = _month_num(current_day)

            # Determine daily ticket target
            if current_day in bfcm_y1_days:
                daily_target = PY_RNG.randint(52, 62)   # ~3.8x baseline (13.5/day)
            elif current_day in bfcm_y2_days:
                daily_target = PY_RNG.randint(38, 46)   # ~2.9x baseline
            elif current_day in chain_days:
                daily_target = PY_RNG.randint(32, 42)   # ~2.5x for sizing spike
            else:
                daily_target = PY_RNG.randint(10, 16)   # normal 70-112/week

            # Determine BFCM reason distribution
            bfcm_dist = None
            if current_day in bfcm_y1_days:
                bfcm_dist = BFCM_Y1_DIST
            elif current_day in bfcm_y2_days:
                bfcm_dist = BFCM_Y2_DIST

            # Chain spike for this day
            chain_spike = chain_days.get(current_day)

            # H14 unmapped tag probability (10% of tickets get unmapped tag)
            h14_unmapped_tags = []
            if current_day in h14_days_1:
                h14_unmapped_tags = H14_TAGS_1
            elif current_day in h14_days_2:
                h14_unmapped_tags = H14_TAGS_2

            # Wrong-brand tickets (12 total in May 2025)
            add_wrong_brand = (
                current_day in wrong_brand_days
                and wrong_brand_count < 12
                and PY_RNG.random() < 0.8
            )

            for t_idx in range(daily_target):
                if sig_idx >= len(signals):
                    # Extend signals if needed
                    extra = _generate_ticket_signals(5000)
                    signals.extend(extra)
                sig = signals[sig_idx]
                sig_idx += 1

                cust_id = str(PY_RNG.choice(customer_ids))
                cust_ticket_counts[cust_id] = cust_ticket_counts.get(cust_id, 0) + 1
                lifetime_count = cust_ticket_counts[cust_id]

                # Klaviyo profile ID (84% match rate -- XD1)
                klav_pid = f'KP-{cust_id}' if PY_RNG.random() < 0.84 else None

                # Hour of day (slightly weighted to business hours)
                hour = PY_RNG.choices(range(7, 22), weights=[1,2,3,4,5,5,4,4,4,3,3,3,2,2,1], k=1)[0]
                minute = PY_RNG.randint(0, 59)
                created_ts = utc_dt(current_day, hour, minute)

                # Reason selection
                if chain_spike and t_idx < int(daily_target * 0.65):
                    reason = 'sizing_issue'
                elif bfcm_dist:
                    reason = PY_RNG.choices(
                        list(bfcm_dist.keys()), weights=list(bfcm_dist.values()), k=1
                    )[0]
                else:
                    reason = PY_RNG.choices(REASON_CODES, weights=REASON_WEIGHTS, k=1)[0]

                # Channel
                channel = PY_RNG.choices(CHANNELS, weights=CHANNEL_WEIGHTS, k=1)[0]

                # Subject
                subject = PY_RNG.choice(SUBJECTS[reason])

                # First response type (FIX: automation from Month 5 / Oct 2024)
                if current_day >= AUTOMATION_START and PY_RNG.random() < 0.22:
                    first_response_type = 'automated'
                    resp_delay_h = PY_RNG.uniform(0.01, 0.08)  # ~5 min automated
                else:
                    first_response_type = 'human'
                    # Response time: ~3.2h baseline, degrades during BFCM Y1 to 6.8h
                    if current_day in bfcm_y1_days:
                        resp_delay_h = float(abs(PY_RNG.gauss(6.8, 1.2)))
                    elif current_day in bfcm_y2_days:
                        resp_delay_h = float(abs(PY_RNG.gauss(4.1, 0.8)))
                    else:
                        resp_delay_h = float(abs(PY_RNG.gauss(3.2, 0.9))) * float(sig[0])

                resp_delay_h = max(0.05, resp_delay_h)
                first_response_ts = created_ts + timedelta(hours=resp_delay_h)

                # Resolution time
                if current_day in bfcm_y1_days:
                    resolution_h = float(abs(PY_RNG.gauss(36, 6)))
                elif current_day in bfcm_y2_days:
                    resolution_h = float(abs(PY_RNG.gauss(24, 4)))
                else:
                    resolution_h = float(abs(PY_RNG.gauss(21, 4))) * float(sig[1])
                resolution_h = max(resp_delay_h + 0.5, resolution_h)

                resolved_ts = created_ts + timedelta(hours=resolution_h)
                if resolved_ts.date() > SEED_END:
                    resolved_ts = None
                    status = 'open'
                else:
                    status = 'resolved' if PY_RNG.random() < 0.92 else 'closed'

                updated_ts = resolved_ts or (created_ts + timedelta(hours=resolution_h))

                # CSAT / NPS (GD6 -- Month 10 transition)
                if current_day >= NPS_START:
                    csat_score = None
                    nps_score  = PY_RNG.randint(6, 10)  # 6-10 out of 10
                    if current_day in bfcm_y1_days:
                        nps_score = PY_RNG.randint(4, 7)
                    elif current_day in bfcm_y2_days:
                        nps_score = PY_RNG.randint(6, 9)
                else:
                    nps_score  = None
                    if current_day in bfcm_y1_days:
                        csat_score = float(round(PY_RNG.uniform(3.1, 3.7), 1))
                    else:
                        base_csat = PY_RNG.uniform(4.1, 4.4)
                        # Correlated: worse response time -> lower CSAT
                        csat_score = float(round(min(5.0, max(1.0,
                            base_csat * float(sig[1])
                        )), 1))

                # VIP routing (from Month 3 / Aug 2024)
                priority = (
                    current_day >= VIP_ROUTING_START
                    and cust_id in vip_set
                )

                # Agent
                agent = PY_RNG.choice(AGENT_IDS)

                ext_ts = utc_dt(current_day, 14)
                raw, ext_at, meta, gen = airbyte_meta_cols(ext_ts)

                tid = _ticket_id(f'{cust_id}:{current_day.isoformat()}:{t_idx}:{day_idx}')

                ticket_rows.append((
                    tid, cust_id, klav_pid,
                    created_ts, updated_ts, resolved_ts,
                    status, channel, subject,
                    first_response_ts, first_response_type, agent,
                    csat_score, nps_score, bool(priority),
                    reason, lifetime_count, float(round(resolution_h, 2)),
                    raw, ext_at, meta, int(gen),
                ))

                # Messages (FIX 2 -- airbyte_meta_cols on every row)
                raw2, ext2, meta2, gen2 = airbyte_meta_cols(ext_ts)
                msg_rows.append((
                    _msg_id(f'{tid}:in'), tid, created_ts,
                    'inbound', True, INBOUND_BODIES[reason], None,
                    raw2, ext2, meta2, int(gen2),
                ))
                if first_response_type == 'automated':
                    raw3, ext3, meta3, gen3 = airbyte_meta_cols(ext_ts)
                    msg_rows.append((
                        _msg_id(f'{tid}:auto'), tid, first_response_ts,
                        'outbound', False, 'Thank you for contacting us. A team member will respond shortly.',
                        'AUTOBOT-001',
                        raw3, ext3, meta3, int(gen3),
                    ))
                else:
                    raw3, ext3, meta3, gen3 = airbyte_meta_cols(ext_ts)
                    msg_rows.append((
                        _msg_id(f'{tid}:out'), tid, first_response_ts,
                        'outbound', False, OUTBOUND_BODIES[reason], agent,
                        raw3, ext3, meta3, int(gen3),
                    ))

                # Tags
                raw_tags = []

                # Chain spike: use chain-specific tags for most of these tickets
                if chain_spike and t_idx < int(daily_target * 0.65):
                    raw_tags = list(chain_spike['tags'][:PY_RNG.randint(1, 2)])
                elif reason == 'product_quality' and current_day in defective_days:
                    raw_tags = [PY_RNG.choice(DEFECTIVE_TAGS)]
                else:
                    base_tags = REASON_TAGS.get(reason, ['other'])
                    raw_tags = [PY_RNG.choice(base_tags)]
                    if PY_RNG.random() < 0.25:
                        extra = [t for t in base_tags if t not in raw_tags]
                        if extra:
                            raw_tags.append(PY_RNG.choice(extra))

                # H14 unmapped tag injection (10% of tickets in that window)
                if h14_unmapped_tags and PY_RNG.random() < 0.10:
                    raw_tags.append(PY_RNG.choice(h14_unmapped_tags))

                for tag in set(raw_tags):
                    raw4, ext4, meta4, gen4 = airbyte_meta_cols(ext_ts)
                    tag_rows.append((
                        tid, tag, created_ts,
                        raw4, ext4, meta4, int(gen4),
                    ))

            # Wrong-brand tickets (12 total across May 2025)
            if add_wrong_brand and wrong_brand_count < 12:
                n_wb = min(PY_RNG.randint(0, 2), 12 - wrong_brand_count)
                for wb_i in range(n_wb):
                    cust_id = str(PY_RNG.choice(customer_ids))
                    hour = PY_RNG.randint(9, 18)
                    created_ts = utc_dt(current_day, hour)
                    tid = _ticket_id(f'wrong_brand:{current_day.isoformat()}:{wb_i}:{day_idx}')
                    ext_ts = utc_dt(current_day, 14)
                    raw, ext_at, meta, gen = airbyte_meta_cols(ext_ts)

                    ticket_rows.append((
                        tid, cust_id, None,
                        created_ts, created_ts + timedelta(hours=2),
                        created_ts + timedelta(hours=2),
                        'resolved', 'email',
                        "I think I have the wrong brand's website",
                        created_ts + timedelta(hours=0.5), 'human', AGENT_IDS[0],
                        None if current_day >= NPS_START else 4.0,
                        PY_RNG.randint(7, 9) if current_day >= NPS_START else None,
                        False, 'other', 1, 2.0,
                        raw, ext_at, meta, int(gen),
                    ))
                    raw4, ext4, meta4, gen4 = airbyte_meta_cols(ext_ts)
                    tag_rows.append((
                        tid, 'wrong_brand', created_ts,
                        raw4, ext4, meta4, int(gen4),
                    ))
                    wrong_brand_count += n_wb
                    break

            # Flush every 7 days
            if day_idx % 7 == 6:
                _flush()

            current_day += timedelta(days=1)
            day_idx += 1

        _flush(force=True)
        logger.info('seed_tickets | gorgias_tickets: %d total inserted', total_inserted)
        return total_inserted

    except Exception as e:
        logger.error('SOURCE: Gorgias Seed | CLIENT: %s | ERROR: %s | CONTEXT: seed_tickets',
                     CLIENT_ID, str(e))
        raise

# ---------------------------------------------------------------------------
# 3. Alert log entries
# ---------------------------------------------------------------------------

def seed_alert_log(cur) -> None:
    try:
        # Pre-check existing by (client_id, alert_type, fired_at)
        cur.execute(
            "SELECT alert_type, fired_at::date FROM public.alert_log "
            "WHERE client_id = %s AND alert_type IN "
            "('vip_ticket_unresolved', 'H14', 'D1_gorgias_evidence', 'H16')",
            (CLIENT_ID,),
        )
        existing = {(r[0], r[1]) for r in cur.fetchall()}

        ALERT_COLS = [
            'client_id', 'alert_type', 'fired_at',
            'should_fire', 'confidence_score',
            'signal_value', 'threshold_value', 'threshold_direction',
            'layer1_headline', 'layer2_context', 'layer3_precedent',
            'alert_instance_number', 'escalation_level',
            'suppressed', 'suppression_category',
            'fatigue_period_active', 'fatigue_reason',
            'outcome_confirmed', 'dismissal_correct',
            'is_synthetic', 'severity',
        ]

        rows = []

        # ---- vip_ticket_unresolved: 4 in Y1, 6 in Y2 ----
        vip_dates_y1 = [
            date(2024,  8, 14),
            date(2024, 10, 22),
            date(2024, 12, 18),
            date(2025,  2, 11),
        ]
        vip_dates_y2 = [
            date(2025,  7, 15),
            date(2025,  9,  9),
            date(2025, 11, 12),
            date(2026,  1, 20),
            date(2026,  3, 10),
            date(2026,  5,  6),
        ]
        for vip_date in vip_dates_y1 + vip_dates_y2:
            key = ('vip_ticket_unresolved', vip_date)
            if key in existing:
                continue
            conf = float(round(PY_RNG.uniform(0.82, 0.94), 2))
            rows.append((
                CLIENT_ID, 'vip_ticket_unresolved', utc_dt(vip_date, 10),
                True, conf,
                float(round(PY_RNG.uniform(18.5, 23.8), 1)), 18.0, 'above',
                f'VIP customer ticket unresolved for {PY_RNG.randint(19, 24)}h. '
                f'Customer has 3+ lifetime orders.',
                'Ticket channel: email. Customer segment: Segment 3 (VIP). '
                'Priority queue flagged but still unresolved past 18h threshold.',
                'VIP tickets resolved within SLA 94% of the time. '
                'Current breach is an outlier.',
                1, 0, False, None, False, None, None, None, True, 'warning',
            ))

        # ---- H14: tag normalisation coverage -- 2 instances ----
        h14_entries = [
            (date(2024, 9, 20),
             'Tag normalisation coverage dropped to 79% in September 2024.',
             'New FW collection vocabulary introduced tags: '
             "'outerwear fit', 'layering issue'. These map to sizing_issue "
             'but lack normalisation entries. Alert 5 confidence capped until resolved.',
             'H14 fired Month 4 (Sep 2024) and Month 16 (Sep 2025) both following FW launches.'),
            (date(2025, 9, 22),
             'Tag normalisation coverage dropped to 81% in September 2025.',
             "New FW 2025 vocabulary introduced tags: 'winter weight', 'thermal lining'. "
             'Normalisation table requires update before FW collection launch analysis.',
             'Pattern matches Month 4 incident. Add new tags to normalisation table.'),
        ]
        for h14_date, headline, context, precedent in h14_entries:
            key = ('H14', h14_date)
            if key in existing:
                continue
            rows.append((
                CLIENT_ID, 'H14', utc_dt(h14_date, 9),
                True, 0.95,
                float(round(PY_RNG.uniform(17, 22), 1)), 15.0, 'above',
                headline, context, precedent,
                1, 0, False, None, False, None, True, None, True, 'warning',
            ))

        # ---- D1_gorgias_evidence: 1 instance (Nov 28 2024) ----
        d1_key = ('D1_gorgias_evidence', date(2024, 11, 28))
        if d1_key not in existing:
            rows.append((
                CLIENT_ID, 'D1_gorgias_evidence', utc_dt(date(2024, 11, 28), 11),
                True, 0.88,
                float(round(PY_RNG.uniform(16, 20), 1)), 12.0, 'above',
                'Gorgias quality complaints spiked on AZ-KNIT-031: '
                '18% of tickets tagged product_quality vs 4% catalogue average.',
                'Layer 2 evidence for D1 component-level alert. '
                'Tags: defective, fabric quality, wrong fabric weight. '
                'Return rate component of D1 is NOT suppressed by BFCM S1. '
                '180 units affected -- supplier credit claim window is 30 days.',
                'D1 component-level suppression: CPM component suppressed (BFCM S1). '
                'Return rate component fires regardless. This is the Gorgias evidence source.',
                1, 0, False, None, False, None, True, None, True, 'emergency',
            ))

        # ---- H16: schema change -- Gorgias adds ticket_channel (Feb 2026) ----
        h16_key = ('H16', date(2026, 2, 15))
        if h16_key not in existing:
            rows.append((
                CLIENT_ID, 'H16', utc_dt(date(2026, 2, 15), 9),
                True, 1.0,
                1.0, 0.0, 'above',
                'Gorgias schema change detected: new field ticket_channel added (Month 21).',
                'Additive change -- no Azure Co traffic on WhatsApp channel. '
                'No impact on existing metrics. Normalisation table may need new channel tags.',
                'XD5 schema evolution: Gorgias added ticket_channel in Feb 2026. '
                'Informational only -- no breaking change.',
                1, 0, False, None, False, None, True, None, True, 'info',
            ))

        if rows:
            psycopg2.extras.execute_values(
                cur,
                f'INSERT INTO public.alert_log ({", ".join(ALERT_COLS)}) VALUES %s '
                f'ON CONFLICT DO NOTHING',
                rows,
            )
        logger.info('seed_alert_log | inserted: %d (skipped %d existing)',
                    len(rows),
                    (len(vip_dates_y1) + len(vip_dates_y2) + 2 + 1 + 1) - len(rows))

    except Exception as e:
        logger.error('SOURCE: Gorgias Seed | CLIENT: %s | ERROR: %s | CONTEXT: seed_alert_log',
                     CLIENT_ID, str(e))
        raise

# ---------------------------------------------------------------------------
# 3b. Seed defective unit quality tickets (S44 -- 6-8/day, Nov 28-Dec 4 2024)
# ---------------------------------------------------------------------------

def seed_defective_tickets(cur, customer_ids: list) -> None:
    """
    40-56 additional product_quality tickets for the AZ-KNIT-031 defective batch.
    Seeded on top of the BFCM arc (which has 0% product_quality in its distribution).
    """
    try:
        TICKET_COLS = [
            'ticket_id', 'customer_id', 'klaviyo_profile_id',
            'created_at', 'updated_at', 'resolved_at',
            'status', 'channel', 'subject',
            'first_response_at', 'first_response_type', 'resolved_by',
            'csat_score', 'nps_score', 'priority_queue',
            'last_ticket_reason', 'ticket_count_lifetime', 'resolution_hours',
            '_airbyte_raw_id', '_airbyte_extracted_at', '_airbyte_meta',
            '_airbyte_generation_id',
        ]
        TAG_COLS = [
            'ticket_id', 'tag', 'tagged_at',
            '_airbyte_raw_id', '_airbyte_extracted_at', '_airbyte_meta',
            '_airbyte_generation_id',
        ]
        MSG_COLS = [
            'message_id', 'ticket_id', 'created_at',
            'message_type', 'is_from_customer', 'body_text', 'agent_id',
            '_airbyte_raw_id', '_airbyte_extracted_at', '_airbyte_meta',
            '_airbyte_generation_id',
        ]

        ticket_rows = []
        tag_rows    = []
        msg_rows    = []

        current_day = DEFECTIVE_WIN[0]
        day_idx     = 0
        while current_day <= DEFECTIVE_WIN[1]:
            n_today = PY_RNG.randint(6, 8)
            for t_idx in range(n_today):
                cust_id = str(PY_RNG.choice(customer_ids))
                klav_pid = f'KP-{cust_id}' if PY_RNG.random() < 0.84 else None
                hour    = PY_RNG.randint(8, 21)
                minute  = PY_RNG.randint(0, 59)
                created_ts = utc_dt(current_day, hour, minute)
                resp_delay = float(abs(PY_RNG.gauss(5.5, 1.5)))  # slower during BFCM
                first_resp = created_ts + timedelta(hours=max(0.5, resp_delay))
                resol_h    = float(abs(PY_RNG.gauss(28, 5)))     # longer -- compensation processing
                resolved_ts = created_ts + timedelta(hours=resol_h)

                ext_ts = utc_dt(current_day, 14)
                raw, ext_at, meta, gen = airbyte_meta_cols(ext_ts)
                tid = _ticket_id(f'defective:{cust_id}:{current_day.isoformat()}:{t_idx}:{day_idx}')

                # CSAT is low during defective incident (3.1-3.6)
                csat_score = float(round(PY_RNG.uniform(3.1, 3.6), 1))

                ticket_rows.append((
                    tid, cust_id, klav_pid,
                    created_ts, resolved_ts, resolved_ts,
                    'resolved', 'email',
                    'Quality issue with my order -- defective item',
                    first_resp, 'human', PY_RNG.choice(AGENT_IDS),
                    csat_score, None, False,
                    'product_quality', 1, float(round(resol_h, 2)),
                    raw, ext_at, meta, int(gen),
                ))

                # Tag: one of the defective-specific tags
                tag = PY_RNG.choice(DEFECTIVE_TAGS)
                raw2, ext2, meta2, gen2 = airbyte_meta_cols(ext_ts)
                tag_rows.append((
                    tid, tag, created_ts,
                    raw2, ext2, meta2, int(gen2),
                ))

                # Also add 'product_quality' canonical tag
                raw3, ext3, meta3, gen3 = airbyte_meta_cols(ext_ts)
                tag_rows.append((
                    tid, 'product_quality', created_ts,
                    raw3, ext3, meta3, int(gen3),
                ))

                raw4, ext4, meta4, gen4 = airbyte_meta_cols(ext_ts)
                msg_rows.append((
                    _msg_id(f'defective:{tid}:in'), tid, created_ts,
                    'inbound', True,
                    'Hi, the item I received appears to be defective -- the fabric weight '
                    'is completely wrong. Very disappointed with this purchase.',
                    None, raw4, ext4, meta4, int(gen4),
                ))

            current_day += timedelta(days=1)
            day_idx += 1

        if ticket_rows:
            psycopg2.extras.execute_values(
                cur,
                f'INSERT INTO {SCHEMA}.gorgias_tickets ({", ".join(TICKET_COLS)}) '
                f'VALUES %s ON CONFLICT DO NOTHING',
                ticket_rows,
            )
            psycopg2.extras.execute_values(
                cur,
                f'INSERT INTO {SCHEMA}.gorgias_ticket_tags ({", ".join(TAG_COLS)}) '
                f'VALUES %s ON CONFLICT DO NOTHING',
                tag_rows,
            )
            psycopg2.extras.execute_values(
                cur,
                f'INSERT INTO {SCHEMA}.gorgias_ticket_messages ({", ".join(MSG_COLS)}) '
                f'VALUES %s ON CONFLICT DO NOTHING',
                msg_rows,
            )
        logger.info('seed_defective_tickets | quality tickets: %d', len(ticket_rows))

    except Exception as e:
        logger.error('SOURCE: Gorgias Seed | CLIENT: %s | ERROR: %s | CONTEXT: seed_defective_tickets',
                     CLIENT_ID, str(e))
        raise


# ---------------------------------------------------------------------------
# 4. DQ metric scores (GD1--GD6)
# ---------------------------------------------------------------------------

def seed_dq_metric_scores(cur) -> None:
    try:
        cur.execute(
            'SELECT source, metric_domain, effective_from::date '
            'FROM client_azure_co.dq_metric_scores '
            "WHERE source = 'gorgias'",
        )
        existing = {(r[0], r[1], r[2]) for r in cur.fetchall()}

        DQ_COLS = [
            'client_id', 'source', 'metric_domain', 'dq_score',
            'dq_issues', 'alert_types_affected', 'confidence_cap',
            'freshness_tier', 'effective_from', 'effective_to',
        ]

        dq_entries = [
            # GD2 -- Automation contamination (October 2024 only)
            (CLIENT_ID, 'gorgias', 'ticket_volume', 78,
             ['GD2_automated_response_contamination'],
             ['Alert5_stage1', 'H14'],
             0.78, 'batch',
             utc_dt(date(2024, 10, 1), 0), utc_dt(date(2024, 10, 31), 23, 59)),
            # GD3 -- Multi-channel deduplication (ongoing)
            (CLIENT_ID, 'gorgias', 'ticket_volume', 95,
             ['GD3_multichannel_dedup_5pct'],
             ['Alert5_stage1'],
             0.95, 'batch',
             utc_dt(date(2024, 6, 1), 0), None),
            # GD6 -- CSAT/NPS transition (March 2025 only)
            (CLIENT_ID, 'gorgias', 'ticket_tags', 60,
             ['GD6_csat_nps_transition'],
             ['csat_trend', 'D1'],
             0.60, 'batch',
             utc_dt(date(2025, 3, 1), 0), utc_dt(date(2025, 3, 31), 23, 59)),
        ]

        rows = []
        for entry in dq_entries:
            key = (entry[1], entry[2], entry[8].date())
            if key not in existing:
                rows.append(entry)

        if rows:
            psycopg2.extras.execute_values(
                cur,
                f'INSERT INTO client_azure_co.dq_metric_scores '
                f'({", ".join(DQ_COLS)}) VALUES %s ON CONFLICT DO NOTHING',
                rows,
            )
        logger.info('seed_dq_metric_scores | inserted: %d (skipped %d existing)',
                    len(rows), len(dq_entries) - len(rows))

    except Exception as e:
        logger.error('SOURCE: Gorgias Seed | CLIENT: %s | ERROR: %s | CONTEXT: seed_dq_metric_scores',
                     CLIENT_ID, str(e))
        raise

# ---------------------------------------------------------------------------
# 5. Validation -- 8 checks
# ---------------------------------------------------------------------------

def validate(conn) -> None:
    sys.stdout.reconfigure(encoding='utf-8')
    cur = conn.cursor()
    results = {}

    def run(sql, params=None):
        cur.execute(sql, params)
        return cur.fetchall()

    print()
    print('=' * 72)
    print('GORGIAS SEED VALIDATION -- 8 CHECKS')
    print('=' * 72)

    # CHECK 1 -- Total ticket count
    cnt = run(f'SELECT COUNT(*) FROM {SCHEMA}.gorgias_tickets')[0][0]
    ok = 9000 <= cnt <= 12000
    results[1] = 'PASS' if ok else 'FAIL'
    print(f'\n[{results[1]}] CHECK 1 -- Total ticket count')
    print(f'       actual={cnt:,}  expected=9,000-12,000')

    # CHECK 2 -- Tag normalisation entries
    norm_cnt = run(f'SELECT COUNT(*) FROM {SCHEMA}.gorgias_tag_normalisation')[0][0]
    ok = norm_cnt >= 40
    results[2] = 'PASS' if ok else 'FAIL'
    print(f'\n[{results[2]}] CHECK 2 -- Tag normalisation entries')
    print(f'       actual={norm_cnt}  expected>=40')

    # CHECK 3 -- Alert5_stage1 chain alignment (4 rows, each precedes Loop s2_date)
    rows = run("""
        SELECT fired_at::date, alert_type
        FROM public.alert_log
        WHERE alert_type = 'Alert5_stage1'
          AND client_id = %s
        ORDER BY fired_at
    """, (CLIENT_ID,))
    # Loop s2_dates (from seed_loop_returns.py CHAIN_WINDOWS start dates)
    loop_s2_dates = [
        date(2024,  8, 18),  # Chain 1
        date(2024, 10, 11),  # Chain 2
        date(2024, 12,  9),  # Chain 3
        date(2025, 10, 13),  # Chain 4
    ]
    ok = len(rows) == 4
    if ok:
        for (fired_dt, _), s2 in zip(rows, loop_s2_dates):
            gap = (s2 - fired_dt).days
            if not (3 <= gap <= 7):
                ok = False
    results[3] = 'PASS' if ok else 'FAIL'
    print(f'\n[{results[3]}] CHECK 3 -- Alert5_stage1 chain alignment')
    for r in rows:
        print(f'       {r[0]} ({r[1]})')
    print(f'       expected: 4 rows, each 3-7 days before Loop s2_date')

    # CHECK 4 -- Defective unit Gorgias signal (Nov 28 -- Dec 4 2024)
    qual_rows = run(f"""
        SELECT COUNT(*) as quality_tickets
        FROM {SCHEMA}.gorgias_tickets gt
        JOIN {SCHEMA}.gorgias_ticket_tags gtt ON gt.ticket_id = gtt.ticket_id
        WHERE gt.created_at BETWEEN '2024-11-28' AND '2024-12-05'
          AND gtt.tag IN ('product_quality', 'defective', 'fabric quality',
                          'wrong fabric weight')
    """)
    qual_cnt = qual_rows[0][0]
    ok = 40 <= qual_cnt <= 120
    results[4] = 'PASS' if ok else 'FAIL'
    print(f'\n[{results[4]}] CHECK 4 -- Defective unit Gorgias signal (Nov 28-Dec 4 2024)')
    print(f'       quality_tickets={qual_cnt}  expected=40-120')

    # CHECK 5 -- Automation contamination (Month 5+)
    auto_rows = run(f"""
        SELECT first_response_type, COUNT(*)
        FROM {SCHEMA}.gorgias_tickets
        WHERE created_at >= '2024-10-01'
        GROUP BY first_response_type
        ORDER BY first_response_type
    """)
    auto_counts = {r[0]: int(r[1]) for r in auto_rows}
    total_since_oct = sum(auto_counts.values())
    auto_pct = auto_counts.get('automated', 0) / total_since_oct * 100 if total_since_oct > 0 else 0
    ok = 'automated' in auto_counts and 18 <= auto_pct <= 26
    results[5] = 'PASS' if ok else 'FAIL'
    print(f'\n[{results[5]}] CHECK 5 -- Automation contamination (Month 5+)')
    for rtype, n in sorted(auto_counts.items()):
        print(f'       {rtype}: {n} ({n/total_since_oct*100:.1f}%)')
    print(f'       automated share={auto_pct:.1f}%  expected=~22% (18-26%)')

    # CHECK 6 -- CSAT/NPS transition
    csat_nps = run(f"""
        SELECT
          COUNT(*) FILTER (WHERE csat_score IS NOT NULL) AS csat_tickets,
          COUNT(*) FILTER (WHERE nps_score  IS NOT NULL) AS nps_tickets,
          COUNT(*) FILTER (WHERE csat_score IS NOT NULL
                             AND nps_score  IS NOT NULL) AS both
        FROM {SCHEMA}.gorgias_tickets
    """)
    csat_n, nps_n, both_n = csat_nps[0]
    ok = csat_n > 0 and nps_n > 0 and both_n == 0
    results[6] = 'PASS' if ok else 'FAIL'
    print(f'\n[{results[6]}] CHECK 6 -- CSAT/NPS transition (Month 10)')
    print(f'       csat_tickets={csat_n:,}  nps_tickets={nps_n:,}  overlap={both_n}')
    print(f'       expected: both > 0, no overlap')

    # CHECK 7 -- VIP ticket alerts
    vip_cnt = run("""
        SELECT COUNT(*) FROM public.alert_log
        WHERE alert_type = 'vip_ticket_unresolved'
          AND client_id = %s
    """, (CLIENT_ID,))[0][0]
    ok = vip_cnt == 10
    results[7] = 'PASS' if ok else 'FAIL'
    print(f'\n[{results[7]}] CHECK 7 -- VIP ticket unresolved alerts')
    print(f'       actual={vip_cnt}  expected=10')

    # CHECK 8 -- BFCM Y1 ticket surge
    bfcm_cnt = run(f"""
        SELECT COUNT(*) FROM {SCHEMA}.gorgias_tickets
        WHERE created_at BETWEEN '2024-11-27' AND '2024-12-03'
    """)[0][0]
    # Normal 6-day window = 6 * (97/7) ≈ 83 tickets
    ok = bfcm_cnt >= 200
    results[8] = 'PASS' if ok else 'FAIL'
    print(f'\n[{results[8]}] CHECK 8 -- BFCM Y1 ticket surge (Nov 27-Dec 2)')
    print(f'       bfcm_tickets={bfcm_cnt}  expected>=200 (3-4x normal 6-day window ~83)')

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
        logger.error('SOURCE: Gorgias Seed | ERROR: DATABASE_URL not set')
        sys.exit(1)
    return psycopg2.connect(url, sslmode='require')


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    logger.info('SOURCE: Gorgias Seed | CLIENT: %s | Starting', CLIENT_ID)

    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)

    customer_ids = manifest.get('customer_ids', [])
    # VIP set: every 7th customer (~14% = Segment 3 approximation)
    vip_set = {str(cid) for cid in customer_ids[::7]}

    logger.info('Loaded manifest: %d customers, %d VIP', len(customer_ids), len(vip_set))

    conn = get_conn()
    try:
        cur = conn.cursor()

        logger.info('Step 0 -- create_tables (FIX 6)')
        create_tables(cur)

        logger.info('Step 1 -- seed_tag_normalisation (GD5)')
        seed_tag_normalisation(cur)

        logger.info('Step 2 -- seed_tickets (daily arc, 24 months)')
        seed_tickets(cur, customer_ids, vip_set)

        logger.info('Step 2b -- seed_defective_tickets (S44 -- Nov 28-Dec 4 2024)')
        seed_defective_tickets(cur, customer_ids)

        logger.info('Step 3 -- seed_alert_log')
        seed_alert_log(cur)

        logger.info('Step 4 -- seed_dq_metric_scores (GD2, GD3, GD6)')
        seed_dq_metric_scores(cur)

        conn.commit()
        logger.info('SOURCE: Gorgias Seed | CLIENT: %s | Complete', CLIENT_ID)

        validate(conn)

    except Exception as e:
        conn.rollback()
        logger.error('SOURCE: Gorgias Seed | CLIENT: %s | FATAL: %s', CLIENT_ID, str(e))
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    main()
