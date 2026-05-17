"""
Profit Sentinel -- Klaviyo Seed Script
Brand: Azure & Co (client_azure_co)
Archetype A: Premium Contemporary Womenswear, $150 AOV
Y1: June 2024 -- May 2025 | Y2: June 2025 -- May 2026

Seeded tables (FIX 6 -- CREATE TABLE IF NOT EXISTS with UNIQUE constraints):
  client_azure_co.klaviyo_profiles           -- ~18,200 profiles (Month 1 cohort)
  client_azure_co.klaviyo_email_events       -- cohort-sampled flow/campaign events
  client_azure_co.klaviyo_sms_events         -- Flow 7 SMS events
  client_azure_co.klaviyo_flows              -- 15 flows
  client_azure_co.klaviyo_campaigns          -- weekly campaigns + special sends
  client_azure_co.klaviyo_flow_id_history    -- Month 18 agency transition

Also inserts/updates:
  public.alert_log                -- Klaviyo-specific alerts (E1, E5, D5, H9, H1_variant, etc.)
  client_azure_co.brand_event_calendar  -- flow_modification + email_template_pause entries

Architecture rules:
  FIX 1 -- No is_synthetic on raw table rows.
  FIX 2 -- airbyte_meta_cols() on every row (copied exactly from seed_shopify.py).
  FIX 3 -- Single transaction boundary wraps all table inserts; ON CONFLICT DO NOTHING.
  FIX 4 -- _nearest_pd_corr() before Cholesky on 3x3 email signal matrix.
  FIX 5 -- GENERATED ALWAYS identity columns excluded from INSERT cols.
  FIX 6 -- CREATE TABLE IF NOT EXISTS with UNIQUE constraints (idempotency).

NEW STANDARD: Every table declares UNIQUE constraints in DDL.
  klaviyo_profiles:        UNIQUE(profile_id) -- also PK
  klaviyo_email_events:    UNIQUE(message_id, profile_id, event_type)
  klaviyo_sms_events:      UNIQUE(message_id, profile_id, event_type)
  klaviyo_flows:           UNIQUE(flow_id)    -- also PK
  klaviyo_campaigns:       UNIQUE(campaign_id) -- also PK
  klaviyo_flow_id_history: UNIQUE(flow_id_old, effective_from)
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s')
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CLIENT_ID  = 'azure_co'
SCHEMA     = 'client_azure_co'
SEED_START = date(2024, 6, 1)
SEED_END   = date(2026, 5, 31)

SEED_RNG = np.random.default_rng(55)   # distinct from Shopify(42), Meta(42/99), TikTok(77)
PY_RNG   = random.Random(55)

_KL_NS = uuid.UUID('d0d0d0d0-fade-beef-9abc-000000000004')

def _kl_id(key: str) -> str:
    return str(uuid.uuid5(_KL_NS, f'klaviyo:{key}'))

# Monthly Klaviyo revenue targets (weekly) by month name
KLAVIYO_WEEKLY_REVENUE = {
    1:  (3200,  4100),   # January
    2:  (4800,  6200),   # February (Valentine's)
    3:  (5100,  6800),   # March (SS teaser)
    4:  (8200,  11400),  # April (SS launch)
    5:  (5400,  7100),   # May (Mother's Day)
    6:  (3800,  5200),   # June (markdown)
    7:  (7800,  10200),  # July (summer sale)
    8:  (3400,  4600),   # August (quietest)
    9:  (5200,  6900),   # September (FW teaser)
    10: (7400,  9800),   # October (FW launch)
    11: (18000, 24000),  # November (BFCM)
    12: (9200,  12400),  # December (holiday)
}

# Deliverability arc: (month_number, open_rate_low, open_rate_high, spam_rate)
# month_number = months since SEED_START (1=Jun2024, 13=Jun2025, etc.)
def _deliverability(month_num: int):
    """Return (reported_open_rate, spam_rate, inbox_placement_rate) for a given month."""
    if month_num <= 8:                          # Months 1-8: healthy
        return PY_RNG.uniform(0.24, 0.28), PY_RNG.uniform(0.0003, 0.0005), PY_RNG.uniform(0.91, 0.94)
    elif month_num <= 12:                       # Months 9-12: degradation
        return PY_RNG.uniform(0.17, 0.21), PY_RNG.uniform(0.0007, 0.0009), PY_RNG.uniform(0.82, 0.88)
    elif month_num == 13:                       # Month 13: list clean, recovery starts
        return PY_RNG.uniform(0.19, 0.23), PY_RNG.uniform(0.0004, 0.0006), PY_RNG.uniform(0.88, 0.92)
    else:                                       # Months 14-24: recovery to 24-26%
        t = min(1.0, (month_num - 13) / 10.0)
        rate = 0.19 + t * 0.07
        return (rate + PY_RNG.uniform(-0.01, 0.01),
                PY_RNG.uniform(0.0003, 0.0005),
                PY_RNG.uniform(0.91, 0.94))

def _month_num(d: date) -> int:
    return (d.year - SEED_START.year) * 12 + (d.month - SEED_START.month) + 1

def _weekly_revenue_target(d: date) -> float:
    lo, hi = KLAVIYO_WEEKLY_REVENUE[d.month]
    return PY_RNG.uniform(lo, hi)

# ---------------------------------------------------------------------------
# FIX 4 -- Nearest PD correlation matrix (copied exactly from seed_shopify.py)
# ---------------------------------------------------------------------------

def _nearest_pd_corr(m: np.ndarray, eps: float = 1e-4) -> np.ndarray:
    vals, vecs = np.linalg.eigh(m)
    vals_clipped = np.maximum(vals, eps)
    pd = vecs @ np.diag(vals_clipped) @ vecs.T
    pd = (pd + pd.T) / 2
    d = np.sqrt(np.diag(pd))
    pd = pd / np.outer(d, d)
    return pd

_KL_CORR_DESIGN = np.array([
    [1.00, 0.72, 0.65],   # open_rate
    [0.72, 1.00, 0.78],   # click_rate
    [0.65, 0.78, 1.00],   # revenue_mult
], dtype=float)
KL_CORR = _nearest_pd_corr(_KL_CORR_DESIGN)

def _generate_email_signals(n: int) -> list:
    """Return (n, 3) list of correlated noise multipliers [open, click, revenue] as Python floats."""
    L = np.linalg.cholesky(KL_CORR)
    noise = SEED_RNG.standard_normal((n, 3))
    corr = noise @ L.T
    return np.clip(1.0 + corr * 0.12, 0.50, 1.60).tolist()

# ---------------------------------------------------------------------------
# FIX 2 -- Airbyte helpers (copied exactly from seed_shopify.py)
# ---------------------------------------------------------------------------

def airbyte_meta_cols(extracted_at: datetime) -> tuple:
    """_airbyte_raw_id, _airbyte_extracted_at, _airbyte_meta, _airbyte_generation_id"""
    return (str(uuid.uuid4()), extracted_at, '{}', 0)

def utc_dt(d: date, hour: int = 9, minute: int = 0) -> datetime:
    return datetime(d.year, d.month, d.day, hour, minute, 0, tzinfo=timezone.utc)

# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def get_conn() -> psycopg2.extensions.connection:
    url = os.getenv('DATABASE_URL')
    if not url:
        logger.error('SOURCE: Klaviyo Seed | ERROR: DATABASE_URL not set')
        sys.exit(1)
    return psycopg2.connect(url, sslmode='require')

def batch_insert(cur, schema: str, table: str, cols: list[str],
                 rows: list[tuple], batch: int = 500) -> int:
    if not rows:
        return 0
    q = f'INSERT INTO {schema}.{table} ({", ".join(cols)}) VALUES %s ON CONFLICT DO NOTHING'
    total = 0
    for i in range(0, len(rows), batch):
        psycopg2.extras.execute_values(cur, q, rows[i: i + batch])
        total += len(rows[i: i + batch])
    return total

def weeks_in_range(start: date, end: date):
    d = start + timedelta(days=(7 - start.weekday()) % 7)
    while d <= end:
        yield d
        d += timedelta(days=7)

def first_day_of_month(y: int, m: int) -> date:
    return date(y, m, 1)

def months_in_range(start: date, end: date):
    y, m = start.year, start.month
    while date(y, m, 1) <= end:
        yield date(y, m, 1)
        m += 1
        if m > 12:
            m = 1; y += 1

# ---------------------------------------------------------------------------
# FIX 6 -- DDL for all six tables (with UNIQUE constraints)
# ---------------------------------------------------------------------------

DDL_PROFILES = f"""
CREATE TABLE IF NOT EXISTS {SCHEMA}.klaviyo_profiles (
    profile_id               text        PRIMARY KEY,
    signup_source            text,
    signup_form_id           text,
    acquisition_channel      text,
    acquisition_date         date,
    consent_method           text,
    consent_timestamp        timestamptz,
    ccpa_opt_out             boolean     DEFAULT false,
    gdpr_consent             boolean     DEFAULT true,
    subscription_status      text        DEFAULT 'subscribed',
    segment_memberships      jsonb,
    shopify_customer_id      text,
    is_purchaser             boolean     DEFAULT false,
    birthday_date            date,
    ltv_12m_estimated        numeric,
    last_ticket_reason       text,
    ticket_count_lifetime    integer     DEFAULT 0,
    csat_score_last          numeric,
    _airbyte_raw_id          text,
    _airbyte_extracted_at    timestamptz,
    _airbyte_meta            text,
    _airbyte_generation_id   bigint,
    CONSTRAINT uq_klaviyo_profiles UNIQUE (profile_id)
);
"""

DDL_EMAIL_EVENTS = f"""
CREATE TABLE IF NOT EXISTS {SCHEMA}.klaviyo_email_events (
    message_id                        text,
    profile_id                        text,
    event_type                        text        DEFAULT 'sent',
    flow_id                           text,
    campaign_id                       text,
    flow_step                         integer,
    sent_at                           timestamptz,
    email_type                        text        DEFAULT 'marketing',
    reported_opens                    integer     DEFAULT 0,
    effective_opens                   integer     DEFAULT 0,
    clicks                            integer     DEFAULT 0,
    revenue_attributed                numeric     DEFAULT 0,
    attribution_confidence            text,
    klaviyo_native_revenue            numeric     DEFAULT 0,
    profit_sentinel_adjusted_revenue  numeric     DEFAULT 0,
    spam_complaint_count              integer     DEFAULT 0,
    hard_bounce_count                 integer     DEFAULT 0,
    inbox_placement_rate              numeric,
    email_file_size_kb                numeric,
    outlook_compatible                boolean     DEFAULT true,
    review_submitted                  boolean     DEFAULT false,
    _airbyte_raw_id                   text,
    _airbyte_extracted_at             timestamptz,
    _airbyte_meta                     text,
    _airbyte_generation_id            bigint,
    CONSTRAINT uq_klaviyo_email_events UNIQUE (message_id, profile_id, event_type)
);
"""

DDL_SMS_EVENTS = f"""
CREATE TABLE IF NOT EXISTS {SCHEMA}.klaviyo_sms_events (
    message_id                text,
    profile_id                text,
    event_type                text        DEFAULT 'sent',
    flow_id                   text,
    sent_at                   timestamptz,
    recovery_attributed       boolean     DEFAULT false,
    double_attributed         boolean     DEFAULT false,
    revenue_attributed        numeric     DEFAULT 0,
    _airbyte_raw_id           text,
    _airbyte_extracted_at     timestamptz,
    _airbyte_meta             text,
    _airbyte_generation_id    bigint,
    CONSTRAINT uq_klaviyo_sms_events UNIQUE (message_id, profile_id, event_type)
);
"""

DDL_FLOWS = f"""
CREATE TABLE IF NOT EXISTS {SCHEMA}.klaviyo_flows (
    flow_id               text    PRIMARY KEY,
    flow_name             text,
    flow_type             text,
    trigger_type          text,
    status                text    DEFAULT 'live',
    created_at            timestamptz,
    implemented_at        date,
    step_count            integer,
    avg_open_rate         numeric,
    avg_click_rate        numeric,
    avg_conversion_rate   numeric,
    revenue_per_recipient numeric,
    _airbyte_raw_id         text,
    _airbyte_extracted_at   timestamptz,
    _airbyte_meta           text,
    _airbyte_generation_id  bigint,
    CONSTRAINT uq_klaviyo_flows UNIQUE (flow_id)
);
"""

DDL_CAMPAIGNS = f"""
CREATE TABLE IF NOT EXISTS {SCHEMA}.klaviyo_campaigns (
    campaign_id                       text    PRIMARY KEY,
    campaign_name                     text,
    campaign_type                     text    DEFAULT 'standard',
    send_date                         date,
    subject_line                      text,
    segment_id                        text,
    send_size                         integer,
    reported_opens                    integer DEFAULT 0,
    effective_opens                   integer DEFAULT 0,
    clicks                            integer DEFAULT 0,
    revenue_attributed                numeric DEFAULT 0,
    klaviyo_native_revenue            numeric DEFAULT 0,
    profit_sentinel_adjusted_revenue  numeric DEFAULT 0,
    spam_complaint_count              integer DEFAULT 0,
    _airbyte_raw_id                   text,
    _airbyte_extracted_at             timestamptz,
    _airbyte_meta                     text,
    _airbyte_generation_id            bigint,
    CONSTRAINT uq_klaviyo_campaigns UNIQUE (campaign_id)
);
"""

DDL_FLOW_ID_HISTORY = f"""
CREATE TABLE IF NOT EXISTS {SCHEMA}.klaviyo_flow_id_history (
    flow_id_old     text,
    flow_id_new     text,
    flow_name       text,
    client_id       text,
    effective_from  date,
    effective_to    date,
    reason          text,
    created_at      timestamptz DEFAULT now(),
    CONSTRAINT uq_klaviyo_flow_id_history UNIQUE (flow_id_old, effective_from)
);
"""

# ---------------------------------------------------------------------------
# Flow definitions (15 flows)
# ---------------------------------------------------------------------------

FLOWS = [
    {'key': 'welcome',         'name': 'Welcome Series',            'type': 'welcome',           'trigger': 'list_join',        'steps': 3, 'open_rate': 0.52, 'click_rate': 0.048, 'conversion': 0.08,  'rev_per_rec': 15.0,   'impl': date(2024, 6, 1)},
    {'key': 'abandoned_cart',  'name': 'Abandoned Cart',            'type': 'abandoned_cart',    'trigger': 'checkout_started', 'steps': 2, 'open_rate': 0.47, 'click_rate': 0.095, 'conversion': 0.08,  'rev_per_rec': 22.0,   'impl': date(2024, 6, 1)},
    {'key': 'post_purchase',   'name': 'Post-Purchase',             'type': 'post_purchase',     'trigger': 'order_placed',     'steps': 3, 'open_rate': 0.60, 'click_rate': 0.038, 'conversion': 0.12,  'rev_per_rec': 18.0,   'impl': date(2024, 6, 1)},
    {'key': 'win_back',        'name': 'Win-Back',                  'type': 'win_back',          'trigger': 'inactivity_60d',   'steps': 2, 'open_rate': 0.15, 'click_rate': 0.021, 'conversion': 0.12,  'rev_per_rec': 8.0,    'impl': date(2024, 6, 1)},
    {'key': 'back_in_stock',   'name': 'Back-in-Stock',             'type': 'back_in_stock',     'trigger': 'restock',          'steps': 1, 'open_rate': 0.65, 'click_rate': 0.120, 'conversion': 0.18,  'rev_per_rec': 28.0,   'impl': date(2024, 6, 1)},
    {'key': 'browse_abandon',  'name': 'Browse Abandonment',        'type': 'browse_abandonment','trigger': 'product_viewed',   'steps': 1, 'open_rate': 0.38, 'click_rate': 0.052, 'conversion': 0.032, 'rev_per_rec': 6.5,    'impl': date(2024, 6, 1)},
    {'key': 'sms_welcome',     'name': 'SMS Welcome + Abandoned Cart','type': 'sms',             'trigger': 'sms_subscribe',    'steps': 1, 'open_rate': 0.98, 'click_rate': 0.145, 'conversion': 0.14,  'rev_per_rec': 19.0,   'impl': date(2024, 6, 1)},
    {'key': 'vip',             'name': 'VIP / High-LTV Customer',   'type': 'vip',               'trigger': 'vip_threshold',    'steps': 2, 'open_rate': 0.48, 'click_rate': 0.082, 'conversion': 0.22,  'rev_per_rec': 42.0,   'impl': date(2024, 6, 1)},
    {'key': 'post_return',     'name': 'Post-Return Recovery',      'type': 'post_return',       'trigger': 'refund_processed', 'steps': 3, 'open_rate': 0.44, 'click_rate': 0.061, 'conversion': 0.19,  'rev_per_rec': 14.0,   'impl': date(2025, 1, 1)},
    {'key': 'loyalty',         'name': 'Loyalty / Rewards',         'type': 'loyalty',           'trigger': 'points_earned',    'steps': 2, 'open_rate': 0.52, 'click_rate': 0.094, 'conversion': 0.18,  'rev_per_rec': 21.0,   'impl': date(2024, 6, 1)},
    {'key': 'collection_launch','name': 'Collection Launch Announcement','type': 'collection', 'trigger': 'segment_trigger',  'steps': 4, 'open_rate': 0.42, 'click_rate': 0.071, 'conversion': 0.11,  'rev_per_rec': 32.0,   'impl': date(2024, 6, 1)},
    {'key': 'waitlist',        'name': 'Pre-Launch Waitlist',        'type': 'waitlist',          'trigger': 'waitlist_signup',  'steps': 3, 'open_rate': 0.67, 'click_rate': 0.145, 'conversion': 0.28,  'rev_per_rec': 48.0,   'impl': date(2024, 6, 1)},
    {'key': 'size_guide',      'name': 'Size Guide / Fit Education', 'type': 'educational',       'trigger': 'page_view',        'steps': 1, 'open_rate': 0.41, 'click_rate': 0.068, 'conversion': 0.12,  'rev_per_rec': 9.5,    'impl': date(2024, 6, 1)},
    {'key': 'birthday',        'name': 'Birthday / Gift Card',       'type': 'birthday',          'trigger': 'birthday_minus7',  'steps': 1, 'open_rate': 0.62, 'click_rate': 0.110, 'conversion': 0.18,  'rev_per_rec': 26.0,   'impl': date(2024, 6, 1)},
    {'key': 'sunset',          'name': 'Sunset / Re-engagement',     'type': 'sunset',            'trigger': 'inactivity_180d',  'steps': 2, 'open_rate': 0.12, 'click_rate': 0.018, 'conversion': 0.04,  'rev_per_rec': 2.0,    'impl': date(2024, 6, 1)},
]

FLOW_IDS = {f['key']: _kl_id(f'flow:{f["key"]}') for f in FLOWS}

# ---------------------------------------------------------------------------
# 0. Create tables
# ---------------------------------------------------------------------------

def create_tables(cur) -> None:
    for ddl in [DDL_PROFILES, DDL_EMAIL_EVENTS, DDL_SMS_EVENTS,
                DDL_FLOWS, DDL_CAMPAIGNS, DDL_FLOW_ID_HISTORY]:
        cur.execute(ddl)
    # FIX 5: add severity column to alert_log if missing (needed for E5 emergency check)
    cur.execute("""
        ALTER TABLE public.alert_log
        ADD COLUMN IF NOT EXISTS severity text DEFAULT 'standard'
    """)
    logger.info('create_tables | all six tables ensured + alert_log.severity column')

# ---------------------------------------------------------------------------
# 1. Seed Klaviyo profiles
# ---------------------------------------------------------------------------

SIGNUP_SOURCES = ['exit_intent', 'footer', 'waitlist',
                  'post_purchase_guest', 'tiktok', 'gorgias_post_resolution']
SIGNUP_WEIGHTS = [0.45, 0.12, 0.08, 0.18, 0.14, 0.03]

def _signup_source(launch_month: bool = False) -> str:
    if launch_month:
        # Waitlist spikes to 35% during collection launch months (April, October)
        weights = [0.32, 0.10, 0.35, 0.12, 0.09, 0.02]
    else:
        weights = SIGNUP_WEIGHTS
    return PY_RNG.choices(SIGNUP_SOURCES, weights=weights, k=1)[0]

def _base_segment_memberships(is_purchaser: bool, acquisition_date: date) -> dict:
    segs = []
    if is_purchaser:
        segs.append('active_subscribers')
        if PY_RNG.random() < 0.04:
            segs.append('vip')
        if PY_RNG.random() < 0.03:
            segs.append('at_risk')
    else:
        if PY_RNG.random() < 0.65:
            segs.append('active_subscribers')
        if PY_RNG.random() < 0.18:
            segs.append('engaged_non_purchasers')
    if PY_RNG.random() < 0.12:
        segs.append('tiktok_acquired')
    return {'segments': segs, 'as_of': str(acquisition_date)}

def seed_profiles(cur, manifest_customer_ids: list[int]) -> int:
    try:
        cols = [
            'profile_id', 'signup_source', 'signup_form_id', 'acquisition_channel',
            'acquisition_date', 'consent_method', 'consent_timestamp',
            'ccpa_opt_out', 'gdpr_consent', 'subscription_status',
            'segment_memberships', 'shopify_customer_id', 'is_purchaser',
            'birthday_date', 'ltv_12m_estimated',
            '_airbyte_raw_id', '_airbyte_extracted_at', '_airbyte_meta', '_airbyte_generation_id',
        ]

        rows = []
        # 5,000 purchasers from manifest customer_ids
        for cid in manifest_customer_ids:
            acq_date = SEED_START - timedelta(days=PY_RNG.randint(0, 730))
            source   = _signup_source(acq_date.month in (4, 10))
            is_eu    = PY_RNG.random() < 0.08
            consent_ts = utc_dt(acq_date, PY_RNG.randint(8, 22))
            birthday = (date(PY_RNG.randint(1960, 2000), PY_RNG.randint(1, 12),
                             PY_RNG.randint(1, 28))
                        if PY_RNG.random() < 0.34 else None)
            segs = _base_segment_memberships(True, acq_date)
            ltv  = round(PY_RNG.uniform(140, 320), 2)
            profile_id = _kl_id(f'customer:{cid}')
            raw_id, ext_at, meta, gen = airbyte_meta_cols(consent_ts)
            rows.append((
                profile_id, source, f'form_{source}', source,
                acq_date,
                'double_optin' if is_eu else 'single_optin',
                consent_ts,
                PY_RNG.random() < 0.02,   # ccpa_opt_out (~2% of CA customers)
                True,
                'subscribed',
                json.dumps(segs),
                str(cid),
                True,
                birthday,
                ltv,
                raw_id, ext_at, meta, gen,
            ))

        # 13,200 non-purchaser subscribers to reach ~18,200 initial list
        for i in range(13_200):
            acq_date = SEED_START - timedelta(days=PY_RNG.randint(0, 720))
            source   = _signup_source(acq_date.month in (4, 10))
            is_eu    = PY_RNG.random() < 0.08
            consent_ts = utc_dt(acq_date, PY_RNG.randint(8, 22))
            birthday = (date(PY_RNG.randint(1960, 2002), PY_RNG.randint(1, 12),
                             PY_RNG.randint(1, 28))
                        if PY_RNG.random() < 0.34 else None)
            segs = _base_segment_memberships(False, acq_date)
            ltv  = round(PY_RNG.uniform(0, 180), 2)
            profile_id = _kl_id(f'nonpurchaser:{i}')
            raw_id, ext_at, meta, gen = airbyte_meta_cols(consent_ts)
            rows.append((
                profile_id, source, f'form_{source}', source,
                acq_date,
                'double_optin' if is_eu else 'single_optin',
                consent_ts,
                PY_RNG.random() < 0.02,
                True,
                'subscribed',
                json.dumps(segs),
                None,
                False,
                birthday,
                ltv,
                raw_id, ext_at, meta, gen,
            ))

        n = batch_insert(cur, SCHEMA, 'klaviyo_profiles', cols, rows)
        logger.info('seed_profiles | rows: %d', n)
        return n
    except Exception as e:
        logger.error('SOURCE: Klaviyo Seed | CLIENT: %s | ERROR: %s | CONTEXT: profiles',
                     CLIENT_ID, str(e))
        raise

# ---------------------------------------------------------------------------
# 2. Seed flows
# ---------------------------------------------------------------------------

def seed_flows(cur) -> None:
    try:
        cols = [
            'flow_id', 'flow_name', 'flow_type', 'trigger_type', 'status',
            'created_at', 'implemented_at', 'step_count',
            'avg_open_rate', 'avg_click_rate', 'avg_conversion_rate', 'revenue_per_recipient',
            '_airbyte_raw_id', '_airbyte_extracted_at', '_airbyte_meta', '_airbyte_generation_id',
        ]
        rows = []
        for f in FLOWS:
            fid = FLOW_IDS[f['key']]
            impl_ts = utc_dt(f['impl'], 8)
            raw_id, ext_at, meta, gen = airbyte_meta_cols(impl_ts)
            rows.append((
                fid, f['name'], f['type'], f['trigger'], 'live',
                impl_ts, f['impl'], f['steps'],
                f['open_rate'], f['click_rate'], f['conversion'], f['rev_per_rec'],
                raw_id, ext_at, meta, gen,
            ))
        n = batch_insert(cur, SCHEMA, 'klaviyo_flows', cols, rows)
        logger.info('seed_flows | rows: %d', n)
    except Exception as e:
        logger.error('SOURCE: Klaviyo Seed | CLIENT: %s | ERROR: %s | CONTEXT: flows',
                     CLIENT_ID, str(e))
        raise

# ---------------------------------------------------------------------------
# 3. Seed campaigns
# ---------------------------------------------------------------------------

CAMPAIGN_SUBJECTS = [
    'New arrivals just landed',
    'Your weekend wardrobe, sorted',
    'The pieces selling out fast',
    'We made this for you',
    'Back by popular demand',
    'Styled 3 ways: your new hero piece',
    "Last chance: this won't last",
    'Exclusively for our community',
    "The edit you've been waiting for",
    "This week's obsession",
]

def seed_campaigns(cur) -> None:
    try:
        cols = [
            'campaign_id', 'campaign_name', 'campaign_type', 'send_date',
            'subject_line', 'segment_id', 'send_size',
            'reported_opens', 'effective_opens', 'clicks',
            'revenue_attributed', 'klaviyo_native_revenue', 'profit_sentinel_adjusted_revenue',
            'spam_complaint_count',
            '_airbyte_raw_id', '_airbyte_extracted_at', '_airbyte_meta', '_airbyte_generation_id',
        ]
        rows = []
        list_size = 18_200  # starts at Month 1 size; grows gradually

        # Weekly standard campaigns (2-3 per week)
        for week_start in weeks_in_range(SEED_START, SEED_END):
            n_campaigns = PY_RNG.randint(2, 3)
            # List grows from 18,200 → 28,200 over 24 months
            months_in  = _month_num(week_start) - 1
            list_size  = int(18_200 + (28_200 - 18_200) * min(1.0, months_in / 24.0))
            send_size  = int(list_size * PY_RNG.uniform(0.40, 0.70))  # segmented sends

            for i in range(n_campaigns):
                send_date = week_start + timedelta(days=PY_RNG.randint(0, 6))
                if send_date > SEED_END:
                    break
                month_n = _month_num(send_date)
                rep_open_rate, spam_rate, _ = _deliverability(month_n)

                # BFCM period: more sends, higher open rate
                is_bfcm = (send_date.month == 11 and send_date.day >= 20
                           or send_date.month == 12 and send_date.day <= 2)
                if is_bfcm:
                    rep_open_rate = min(0.38, rep_open_rate * 1.35)
                    spam_rate = PY_RNG.uniform(0.0008, 0.0011)

                signals = _generate_email_signals(1)[0]
                rep_opens = int(send_size * rep_open_rate * signals[0])
                eff_opens = int(rep_opens * 0.65)
                clicks    = int(eff_opens * PY_RNG.uniform(0.08, 0.18) * signals[1])

                weekly_rev = _weekly_revenue_target(send_date) / max(1, n_campaigns)
                kl_native  = round(weekly_rev * signals[2], 2)
                # Double-attribution gap: 18-32% during campaigns
                dbl_pct    = PY_RNG.uniform(0.18, 0.32)
                adjusted   = round(kl_native * (1 - dbl_pct), 2)

                cid   = _kl_id(f'campaign:{send_date.isoformat()}:{i}')
                subj  = PY_RNG.choice(CAMPAIGN_SUBJECTS)
                ext_ts = utc_dt(send_date, 14)
                raw_id, ext_at, meta, gen = airbyte_meta_cols(ext_ts)
                rows.append((
                    cid,
                    f'Azure Campaign {send_date.isoformat()}-{i+1}',
                    'standard',
                    send_date,
                    subj,
                    'seg_active',
                    send_size,
                    rep_opens, eff_opens, clicks,
                    adjusted, kl_native, adjusted,
                    int(send_size * spam_rate),
                    raw_id, ext_at, meta, gen,
                ))

        # Special: TikTok outage emergency send Jan 19 2025 (D18)
        outage_date = date(2025, 1, 19)
        ext_ts = utc_dt(outage_date, 20)
        raw_id, ext_at, meta, gen = airbyte_meta_cols(ext_ts)
        send_size_em = 18_800
        rep_opens_em = int(send_size_em * 0.38)
        eff_opens_em = int(rep_opens_em * 0.65)
        rows.append((
            _kl_id('campaign:emergency:tiktok_outage_2025_01_19'),
            'Azure -- Shop Our Collection Directly (TikTok Outage Emergency)',
            'campaign',
            outage_date,
            'Shop our collection directly -- Azure & Co',
            'seg_all_active',
            send_size_em,
            rep_opens_em, eff_opens_em,
            int(eff_opens_em * 0.081),
            12_400.0, 12_400.0, 12_400.0,  # no double attribution (no paid ads running)
            int(send_size_em * 0.0002),
            raw_id, ext_at, meta, gen,
        ))

        n = batch_insert(cur, SCHEMA, 'klaviyo_campaigns', cols, rows)
        logger.info('seed_campaigns | rows: %d', n)
    except Exception as e:
        logger.error('SOURCE: Klaviyo Seed | CLIENT: %s | ERROR: %s | CONTEXT: campaigns',
                     CLIENT_ID, str(e))
        raise

# ---------------------------------------------------------------------------
# 4. Seed email events (cohort sampling per flow per quarter)
# ---------------------------------------------------------------------------

# Profile IDs used for cohort sampling (first 5000 from purchasers, then non-purchasers)
def _get_cohort_profile_ids(manifest_customer_ids: list[int],
                             cohort_size: int = 300, seed: int = 0) -> list[str]:
    rng = random.Random(seed)
    pool = [_kl_id(f'customer:{cid}') for cid in manifest_customer_ids]
    pool += [_kl_id(f'nonpurchaser:{i}') for i in range(13_200)]
    return rng.sample(pool, min(cohort_size, len(pool)))

def seed_email_events(cur, manifest_customer_ids: list[int]) -> None:
    try:
        cols = [
            'message_id', 'profile_id', 'event_type',
            'flow_id', 'campaign_id', 'flow_step', 'sent_at', 'email_type',
            'reported_opens', 'effective_opens', 'clicks',
            'revenue_attributed', 'attribution_confidence',
            'klaviyo_native_revenue', 'profit_sentinel_adjusted_revenue',
            'spam_complaint_count', 'hard_bounce_count', 'inbox_placement_rate',
            'email_file_size_kb', 'outlook_compatible', 'review_submitted',
            '_airbyte_raw_id', '_airbyte_extracted_at', '_airbyte_meta', '_airbyte_generation_id',
        ]

        rows = []

        # Quarterly cohorts for each flow
        quarters = [
            (date(2024, 6, 1),  date(2024, 8, 31)),   # Q1 Y1
            (date(2024, 9, 1),  date(2024, 11, 30)),  # Q2 Y1
            (date(2024, 12, 1), date(2025, 2, 28)),   # Q3 Y1
            (date(2025, 3, 1),  date(2025, 5, 31)),   # Q4 Y1
            (date(2025, 6, 1),  date(2025, 8, 31)),   # Q1 Y2
            (date(2025, 9, 1),  date(2025, 11, 30)),  # Q2 Y2
            (date(2025, 12, 1), date(2026, 2, 28)),   # Q3 Y2
            (date(2026, 3, 1),  date(2026, 5, 31)),   # Q4 Y2
        ]

        for q_idx, (q_start, q_end) in enumerate(quarters):
            # Representative send date mid-quarter
            q_mid = q_start + (q_end - q_start) // 2
            month_n = _month_num(q_mid)
            rep_or, spam_rate, inbox_rate = _deliverability(month_n)

            for f_idx, flow in enumerate(FLOWS):
                fid  = FLOW_IDS[flow['key']]
                impl = flow['impl']

                # Flow 9 (post-return) not before Jan 2025
                if flow['key'] == 'post_return' and q_start < date(2025, 1, 1):
                    continue
                # Skip SMS flow (handled separately)
                if flow['type'] == 'sms':
                    continue

                cohort_size = PY_RNG.randint(200, 400)
                cohort_pids = _get_cohort_profile_ids(
                    manifest_customer_ids, cohort_size,
                    seed=q_idx * 100 + f_idx
                )

                signals = _generate_email_signals(len(cohort_pids))

                for p_idx, pid in enumerate(cohort_pids):
                    sig = signals[p_idx]

                    for step in range(1, flow['steps'] + 1):
                        # Step day offsets
                        step_days = {1: 0, 2: 3, 3: 7, 4: 14}
                        send_date = q_mid + timedelta(days=step_days.get(step, (step-1)*7))
                        if send_date > SEED_END:
                            continue

                        # For non-promotional flows: attribution_confidence = 'low'
                        is_promotional = flow['type'] not in ('educational', 'loyalty', 'sunset')
                        attr_conf = ('high' if is_promotional and PY_RNG.random() < 0.65
                                     else 'medium' if is_promotional
                                     else 'low')

                        # Revenue only for promotional flows
                        base_rev = (flow['rev_per_rec'] * sig[2]
                                    if is_promotional and PY_RNG.random() < flow['conversion']
                                    else 0.0)

                        # iOS MPP: among reported opens, 35% are machine pre-loads.
                        # reported=1 when Klaviyo counts any open (human or machine).
                        # effective=1 only when a human actually opened (65% of reported opens).
                        if PY_RNG.random() < (flow['open_rate'] * sig[0]):
                            reported_opens = 1
                            effective_opens = 1 if PY_RNG.random() < 0.65 else 0
                        else:
                            reported_opens = 0
                            effective_opens = 0

                        clicks = (1 if reported_opens > 0 and
                                  PY_RNG.random() < flow['click_rate'] * sig[1]
                                  else 0)

                        kl_native  = round(base_rev, 2)
                        dbl_pct    = PY_RNG.uniform(0.18, 0.32) if kl_native > 0 else 0.0
                        adjusted   = round(kl_native * (1 - dbl_pct), 2)

                        # Email file size (after Month 15 GIF addition: 340KB)
                        base_size = (340.0 if send_date >= date(2025, 8, 8) else 85.0)
                        file_size = round(base_size * PY_RNG.uniform(0.85, 1.15), 1)

                        # Outlook compatibility: broken Oct 3-6 2024 for all emails
                        outlook_ok = not (date(2024, 10, 3) <= send_date <= date(2024, 10, 6))

                        # Review submitted: Day 14 post-purchase only
                        review = (PY_RNG.random() < 0.08 if step == 2 and
                                  flow['key'] == 'post_purchase' else False)

                        msg_id = _kl_id(f'msg:{fid}:q{q_idx}:s{step}:p{p_idx}')
                        sent_ts = utc_dt(send_date, PY_RNG.randint(7, 20))
                        raw_id, ext_at, meta, gen = airbyte_meta_cols(
                            sent_ts + timedelta(hours=1))

                        rows.append((
                            msg_id, pid, 'sent',
                            fid, None, step, sent_ts, 'marketing',
                            reported_opens, effective_opens, clicks,
                            adjusted, attr_conf,
                            kl_native, adjusted,
                            1 if spam_rate > 0 and PY_RNG.random() < spam_rate else 0,
                            1 if PY_RNG.random() < 0.008 else 0,  # hard bounce ~0.8%
                            round(inbox_rate, 4),
                            file_size, outlook_ok, review,
                            raw_id, ext_at, meta, gen,
                        ))

                        if len(rows) >= 2000:
                            batch_insert(cur, SCHEMA, 'klaviyo_email_events', cols, rows)
                            rows.clear()

        if rows:
            batch_insert(cur, SCHEMA, 'klaviyo_email_events', cols, rows)

        # Count total
        cur.execute(f'SELECT COUNT(*) FROM {SCHEMA}.klaviyo_email_events')
        total = cur.fetchone()[0]
        logger.info('seed_email_events | total rows in table: %d', total)

    except Exception as e:
        logger.error('SOURCE: Klaviyo Seed | CLIENT: %s | ERROR: %s | CONTEXT: email_events',
                     CLIENT_ID, str(e))
        raise

# ---------------------------------------------------------------------------
# 5. Seed SMS events (Flow 7 -- SMS Welcome + Abandoned Cart)
# ---------------------------------------------------------------------------

def seed_sms_events(cur, manifest_customer_ids: list[int]) -> None:
    try:
        cols = [
            'message_id', 'profile_id', 'event_type', 'flow_id', 'sent_at',
            'recovery_attributed', 'double_attributed', 'revenue_attributed',
            '_airbyte_raw_id', '_airbyte_extracted_at', '_airbyte_meta', '_airbyte_generation_id',
        ]
        fid  = FLOW_IDS['sms_welcome']
        rows = []

        # SMS subscribers: 4,200 Y1 start -> 7,800 Y2 end
        # Seed one cohort per quarter
        quarters = [
            (date(2024, 6, 1),  4200, 0.37),   # q_mid, sms_list_size, abandonment_rate
            (date(2024, 9, 1),  5000, 0.38),
            (date(2024, 12, 1), 5600, 0.40),
            (date(2025, 3, 1),  6000, 0.38),
            (date(2025, 6, 1),  6400, 0.37),
            (date(2025, 9, 1),  7000, 0.39),
            (date(2025, 12, 1), 7400, 0.40),
            (date(2026, 3, 1),  7800, 0.38),
        ]
        for q_idx, (q_date, sms_list, aband_rate) in enumerate(quarters):
            cohort_size = min(300, sms_list // 14)
            cohort_pids = _get_cohort_profile_ids(
                manifest_customer_ids, cohort_size, seed=900 + q_idx)

            for p_idx, pid in enumerate(cohort_pids):
                if PY_RNG.random() > aband_rate:
                    continue
                send_date = q_date + timedelta(days=PY_RNG.randint(0, 89))
                if send_date > SEED_END:
                    continue
                sent_ts = utc_dt(send_date, PY_RNG.randint(8, 20))
                recovered = PY_RNG.random() < 0.14
                # 3-5% of recoveries are double-attributed (also has email at 1h)
                dbl_attr  = recovered and PY_RNG.random() < 0.04
                rev       = round(PY_RNG.uniform(120, 190), 2) if recovered else 0.0
                msg_id    = _kl_id(f'sms:{fid}:q{q_idx}:p{p_idx}')
                raw_id, ext_at, meta, gen = airbyte_meta_cols(sent_ts)
                rows.append((
                    msg_id, pid, 'sent', fid, sent_ts,
                    recovered, dbl_attr, rev,
                    raw_id, ext_at, meta, gen,
                ))

        n = batch_insert(cur, SCHEMA, 'klaviyo_sms_events', cols, rows)
        logger.info('seed_sms_events | rows: %d', n)
    except Exception as e:
        logger.error('SOURCE: Klaviyo Seed | CLIENT: %s | ERROR: %s | CONTEXT: sms_events',
                     CLIENT_ID, str(e))
        raise

# ---------------------------------------------------------------------------
# 6. Seed flow ID history (Month 18 -- agency -> in-house transition)
# ---------------------------------------------------------------------------

def seed_flow_id_history(cur) -> None:
    try:
        cols = [
            'flow_id_old', 'flow_id_new', 'flow_name', 'client_id',
            'effective_from', 'effective_to', 'reason', 'created_at',
        ]
        transition_date = date(2025, 11, 15)  # Week 3 of Month 18 agency transition
        flows_changed = ['welcome', 'abandoned_cart', 'post_purchase', 'win_back', 'browse_abandon']
        rows = []
        for key in flows_changed:
            flow = next(f for f in FLOWS if f['key'] == key)
            old_id = FLOW_IDS[key]
            new_id = _kl_id(f'flow:{key}:new_2025_nov')
            rows.append((
                old_id, new_id, flow['name'], CLIENT_ID,
                transition_date, None,
                'Klaviyo account restructured: agency -> in-house. '
                'All active flow IDs regenerated. Historical attribution '
                'mapping requires flow_id_history join from this date.',
                utc_dt(transition_date, 10),
            ))

        n = batch_insert(cur, SCHEMA, 'klaviyo_flow_id_history', cols, rows)
        logger.info('seed_flow_id_history | rows: %d', n)
    except Exception as e:
        logger.error('SOURCE: Klaviyo Seed | CLIENT: %s | ERROR: %s | CONTEXT: flow_id_history',
                     CLIENT_ID, str(e))
        raise

# ---------------------------------------------------------------------------
# 7. Seed brand_event_calendar Klaviyo-specific entries (not already seeded)
# ---------------------------------------------------------------------------

def seed_brand_event_calendar_klaviyo(cur) -> None:
    try:
        cols = [
            'client_id', 'event_name', 'event_type', 'start_date', 'end_date',
            'suppress_alerts', 'context_alerts', 'context_explanation',
            'residual_threshold_pct', 'detection_method', 'detection_lag_hours',
            'confidence', 'is_synthetic', 'created_at',
        ]

        new_events = [
            # Month 9 (Feb 2025): Abandoned cart rebuilt -- D5 fires but suppressed
            (CLIENT_ID, 'Abandoned Cart Flow Rebuild Feb 2025', 'flow_modification',
             date(2025, 2, 10), date(2025, 2, 24),
             ['D5'], None,
             'Abandoned cart flow rebuilt with new 3-email sequence. '
             '34% revenue drop expected for 2 weeks during subscriber re-engagement.',
             34.0, 'manual', 0, 1.0, True, utc_dt(date(2025, 2, 10), 9)),

            # Month 13 (Jun 2025): Win-back trigger 60d -> 45d -- E3 suppressed 3 weeks
            (CLIENT_ID, 'Win-Back Trigger Change Jun 2025', 'flow_modification',
             date(2025, 6, 1), date(2025, 6, 21),
             ['E3'], None,
             'Win-back trigger changed from 60 days to 45 days inactivity. '
             'E3 suppressed for 3 weeks while subscriber pool stabilises.',
             None, 'manual', 0, 1.0, True, utc_dt(date(2025, 6, 1), 9)),

            # Month 16 (Sep 2025): Browse abandonment personalised -- positive D5 variant
            (CLIENT_ID, 'Browse Abandonment Personalisation Sep 2025', 'flow_modification',
             date(2025, 9, 1), date(2025, 9, 14),
             None, ['D5'],
             'Browse abandonment personalised by product category. '
             'Conversion rate improved 3.2% -> 5.8%. Positive performance alert expected.',
             None, 'manual', 0, 1.0, True, utc_dt(date(2025, 9, 1), 9)),

            # Month 14 (Jul 2025): Email template pause -- photographer takedown notice
            (CLIENT_ID, 'Welcome Series Template Pause Jul 2025', 'email_template_pause',
             date(2025, 7, 8), date(2025, 7, 11),
             None, None,
             'Photographer takedown notice -- welcome series images removed for 3 days. '
             '340 subscribers missed Email 1, impacting first-purchase conversion.',
             None, 'manual', 2, 1.0, True, utc_dt(date(2025, 7, 8), 9)),

            # Month 20 (Jan 2026): Men's casualwear added to same Klaviyo account
            (CLIENT_ID, 'Multi-Brand Architecture Problem Jan 2026', 'multi_brand_event',
             date(2026, 1, 15), date(2026, 2, 15),
             None, ['E1'],
             'Men\'s casualwear segment added to same Klaviyo account as womenswear. '
             'Womenswear subscribers receiving menswear recommendations. '
             'Unsubscribe rate 3.2%/send (14.5x baseline). E1-variant fires.',
             None, 'auto', 0, 1.0, True, utc_dt(date(2026, 1, 15), 9)),

            # Month 18 Week 1 (Nov 2025): API key change sync gap (supplement to operational_change)
            (CLIENT_ID, 'Klaviyo API Key Change Sync Gap Nov 2025', 'platform_disruption_partial',
             date(2025, 11, 1), date(2025, 11, 2),
             ['H1_variant'], None,
             'New API key rotated during agency handover. '
             '48-hour Klaviyo sync gap. H1-variant fires. Flow data incomplete for 2 days.',
             None, 'auto', 1, 1.0, True, utc_dt(date(2025, 11, 1), 9)),
        ]

        # Pre-check: which events already exist (check by event_name)
        cur.execute(
            "SELECT event_name FROM client_azure_co.brand_event_calendar WHERE client_id = %s",
            (CLIENT_ID,)
        )
        existing_names = {r[0] for r in cur.fetchall()}

        to_insert = [e for e in new_events if e[1] not in existing_names]
        if not to_insert:
            logger.info('seed_brand_event_calendar_klaviyo | all entries already exist, skipping')
            return

        # Use direct execute (no PK/unique on brand_event_calendar except id)
        insert_cols = ', '.join(cols)
        placeholders = ', '.join(['%s'] * len(cols))
        sql = (f'INSERT INTO {SCHEMA}.brand_event_calendar ({insert_cols}) VALUES ({placeholders})')
        for row in to_insert:
            cur.execute(sql, row)

        logger.info('seed_brand_event_calendar_klaviyo | inserted: %d', len(to_insert))
    except Exception as e:
        logger.error('SOURCE: Klaviyo Seed | CLIENT: %s | ERROR: %s | CONTEXT: brand_event_calendar',
                     CLIENT_ID, str(e))
        raise

# ---------------------------------------------------------------------------
# 8. Seed alert_log Klaviyo-specific entries
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

def _alert(atype: str, fired_at: datetime, should_fire: bool,
           confidence: float, signal_value: float = None,
           threshold_value: float = None, threshold_direction: str = 'above',
           layer1: str = None, layer2: str = None, layer3: str = None,
           instance: int = 1, escalation: int = 0,
           suppressed: bool = False, sup_cat: str = None,
           fatigue_period: bool = False, fatigue_reason: str = None,
           outcome: bool = None, dismissal: bool = None,
           severity: str = 'standard') -> tuple:
    return (
        CLIENT_ID, atype, fired_at,
        should_fire, round(confidence, 2),
        signal_value, threshold_value, threshold_direction,
        layer1, layer2, layer3,
        instance, escalation,
        suppressed, sup_cat,
        fatigue_period, fatigue_reason,
        outcome, dismissal,
        True, severity,
    )

def seed_alert_log_klaviyo(cur) -> None:
    try:
        # Pre-check existing Klaviyo alert types to avoid duplicates
        klaviyo_alert_types = [
            'E1', 'E1_variant', 'E5', 'D5_klaviyo', 'D5_positive',
            'H9', 'H1_variant', 'E12_strategic', 'F1_variant',
            'email_ip_risk',
        ]
        cur.execute(
            "SELECT client_id, alert_type, fired_at FROM public.alert_log "
            "WHERE client_id = %s AND alert_type = ANY(%s)",
            (CLIENT_ID, klaviyo_alert_types),
        )
        existing_keys = {(r[0], r[1], r[2]) for r in cur.fetchall()}

        alerts_to_seed = [
            # E5 -- Deliverability Risk Month 10 (Mar 2025)
            _alert(
                'E5', utc_dt(date(2025, 3, 15), 9),
                should_fire=True, confidence=0.88,
                signal_value=0.0008, threshold_value=0.0008, threshold_direction='above',
                layer1=('Spam complaint rate 0.08% -- at Gmail\'s threshold. '
                        'Emails will start landing in spam within 7 days.'),
                layer2=('Complaint rate has risen from 0.03% (Jun 2024) to 0.08% over 9 months. '
                        'Primary driver: BFCM Y1 low-engagement cohort (18-22 emails in Nov). '
                        'Immediate action: suppress unengaged subscribers before next send. '
                        'Premium womenswear benchmark: 0.03-0.05% (E30).'),
                layer3=('No prior E5 precedent for this account. '
                        'Industry: Gmail treats >0.10% as high risk with inbox placement consequences. '
                        'Klaviyo recommends suppressing subscribers with no open in 90 days.'),
                severity='warning',
            ),

            # E5 -- Emergency Month 12 (May 2025): suppressed profiles reactivated
            _alert(
                'E5', utc_dt(date(2025, 5, 22), 9),
                should_fire=True, confidence=0.97,
                signal_value=0.0018, threshold_value=0.0008, threshold_direction='above',
                layer1=('EMERGENCY: Spam complaint rate 0.18% -- 4.5x Gmail threshold. '
                        'Immediate send suspension recommended.'),
                layer2=('Suppressed profiles accidentally reactivated in Klaviyo admin. '
                        '2,400 previously suppressed subscribers received last 3 campaigns. '
                        'Complaint rate: 0.04% -> 0.18% within 72 hours. '
                        'Action: re-suppress segment, contact Klaviyo support for '
                        'deliverability remediation.'),
                layer3=('Month 10 E5 warning (Mar 2025) preceded this -- complaint rate was '
                        'already elevated. Reactivation of suppressed list compounded existing '
                        'deliverability weakness. Comparable events take 4-8 weeks to recover '
                        'inbox placement rates.'),
                severity='emergency',
            ),

            # D5_klaviyo -- Flow revenue decline Month 9 (Feb 2025): abandoned cart rebuild
            _alert(
                'D5_klaviyo', utc_dt(date(2025, 2, 14), 9),
                should_fire=True, confidence=0.82,
                signal_value=0.34, threshold_value=0.20, threshold_direction='above',
                layer1=('Abandoned cart flow revenue down 34% vs prior 2-week average. '
                        'Flow rebuild in progress -- suppressed by flow_modification event.'),
                layer2=('New 3-email abandoned cart sequence deployed Feb 10. '
                        'Recovery rate dropped from 8% to 5.3% during re-engagement window. '
                        'Seasonally-adjusted benchmark (Feb): $4,800-6,200/week. '
                        'Revenue per email sent: $0.06 vs benchmark $0.08-0.14 (E32).'),
                layer3=('Month 6 A/B test (Nov 2024) suggested 3-email sequence outperforms '
                        '2-email. Current dip is flow-rebuild friction (normal 14-day window). '
                        'Monitor: if revenue per email sent remains below $0.07 by Feb 28, '
                        'rebuild has not achieved expected improvement.'),
                suppressed=True, sup_cat='S7_flow_modification',
            ),

            # D5_klaviyo -- Month 18 (Nov 2025): agency transition
            _alert(
                'D5_klaviyo', utc_dt(date(2025, 11, 8), 9),
                should_fire=True, confidence=0.79,
                signal_value=0.28, threshold_value=0.20, threshold_direction='above',
                layer1=('Klaviyo flow revenue declined 28% during agency-to-in-house transition. '
                        'Attribution mapping broken for 2 weeks. Suppressed: flow_modification.'),
                layer2=('Week 1 API key rotation caused 48h sync gap. '
                        'Week 2: 3 flows paused for investigation (welcome, abandoned cart, post-purchase). '
                        'Week 3: Flow IDs changed -- historical attribution requires '
                        'klaviyo_flow_id_history join from Nov 15 2025. '
                        'BFCM context: Nov revenue target $18-24K/week. '
                        'Current flow revenue tracking at $13K/week -- 2 weeks suppressed.'),
                layer3=('Month 9 D5 (Feb 2025) -- cart rebuild -- resolved within 14-day window. '
                        'Agency transition scope is larger: 5 flows + API change. '
                        'Expect 3-4 week normalisation vs 2-week norm.'),
                suppressed=True, sup_cat='S7_flow_modification',
            ),

            # D5_positive -- Month 16 (Sep 2025): browse abandonment personalisation
            _alert(
                'D5_positive', utc_dt(date(2025, 9, 8), 9),
                should_fire=True, confidence=0.89,
                signal_value=0.82, threshold_value=0.20, threshold_direction='above',
                layer1=('Positive: Browse abandonment conversion improved 82% '
                        '(3.2% -> 5.8%) after personalisation by product category. '
                        'Estimated additional revenue: $2,100/month.'),
                layer2=('Month 16 personalisation update (Sep 1 2025): '
                        'browse abandonment now segments by last product category viewed. '
                        'Conversion 3.2% -> 5.8% (vs 3.2-3.8% industry benchmark for browse flows). '
                        'Revenue per recipient: $6.50 -> $11.20.'),
                layer3=('First positive D5 variant in Klaviyo dataset. '
                        'Demonstrates flow optimisation compound return: '
                        'each 1pp conversion improvement = ~$700/month at current browse volume.'),
            ),

            # H9 -- Duplicate profiles Month 8 (Jan 2025)
            _alert(
                'H9', utc_dt(date(2025, 1, 28), 9),
                should_fire=True, confidence=0.95,
                signal_value=840, threshold_value=100, threshold_direction='above',
                layer1=('840 duplicate Klaviyo profiles detected (4.7% of 18,000-subscriber list). '
                        'Recommend profile merge before next send.'),
                layer2=('Duplicates created by: guest checkout email variants (67%), '
                        'TikTok link-in-bio signup with different email capitalisation (21%), '
                        'Gorgias-Klaviyo sync creating secondary profile (12%). '
                        'Impact: 840 subscribers receiving duplicate emails -- '
                        'doubles complaint risk for affected profiles.'),
                layer3=('No prior H9 precedent. Industry: 3-5% duplicate rate typical at '
                        'this list size. Klaviyo merge tool resolves in <2h for <1,000 profiles. '
                        'Recommendation: merge + add email normalisation to signup forms.'),
                severity='warning',
            ),

            # H1_variant -- Month 18 Week 1 (Nov 2025): API key sync gap
            _alert(
                'H1_variant', utc_dt(date(2025, 11, 1), 16),
                should_fire=True, confidence=0.98,
                signal_value=48, threshold_value=4, threshold_direction='above',
                layer1=('Klaviyo sync gap detected: 48 hours of missing flow trigger data. '
                        'Cause: API key rotated during agency handover.'),
                layer2=('New API key activated Nov 1 14:00 UTC. '
                        'Klaviyo sync resumed Nov 3 10:00 UTC after new key authorised. '
                        'Missing data window: Nov 1 14:00 -- Nov 3 10:00 (48h). '
                        'Flows paused during gap: welcome series, abandoned cart. '
                        'Estimated missed revenue: $1,200-1,800 (Nov baseline week 1).'),
                layer3=('Shopify webhook failure (SD1) Month 4 caused similar 6h gap. '
                        'This 48h gap is 8x longer and affects attribution for entire window. '
                        'H1-variant precedent: data gap should be flagged in alert_log '
                        'so D5 calculations exclude the 48h window.'),
                severity='warning',
            ),

            # E12 strategic -- Month 6 (Nov 2024): zero-party data finding
            _alert(
                'E12_strategic', utc_dt(date(2024, 11, 15), 9),
                should_fire=True, confidence=0.85,
                signal_value=0.28, threshold_value=0.10, threshold_direction='above',
                layer1=('Strategic insight: 28% of subscribers declared $200+ budget in '
                        'preference survey. Expanding price ceiling could capture '
                        'additional revenue.'),
                layer2=('Zero-party data survey launched Nov 2024. 34% response rate (4 weeks). '
                        'Budget distribution: <$100 (18%), $100-150 (31%), $150-200 (23%), $200+ (28%). '
                        'Current max product price: $185. Opportunity: 28% of engaged subscribers '
                        'willing to pay above current ceiling.'),
                layer3=('Survey responders have 1.4x higher LTV vs non-responders (engagement proxy). '
                        '28% who declared $200+ budget have 68% open rate vs 24% list average. '
                        'Consider $220-250 premium tier or exclusive capsule collection.'),
            ),

            # E1 -- Month 12 (May 2025): list health degradation
            _alert(
                'E1', utc_dt(date(2025, 5, 10), 9),
                should_fire=True, confidence=0.84,
                signal_value=0.38, threshold_value=0.40, threshold_direction='below',
                layer1=('List health degradation: active subscribers dropped below 40% of list. '
                        'Effective open rate 11.4% (vs 24% benchmark at Month 1).'),
                layer2=('Active subscribers (opens/clicks in 90 days): 9,100 of 24,800 (36.7%). '
                        'Threshold: 40% triggers E1. '
                        'Root cause (4-month arc): BFCM Y1 added 4,400 low-engagement subscribers. '
                        'BFCM cohort open rate: 12-15% (vs 24-28% legacy list). '
                        'May 2025 list clean scheduled -- will improve metric.'),
                layer3=('Month 7 (Dec 2024): holiday gifting newsletter feature added 800 '
                        'new customers in 72h (S33 denominator effect). '
                        'Month 9 (Feb 2025): E5 spam complaint warning. '
                        'Month 10 (Mar 2025): E5 deliverability risk fired. '
                        'All three signal the same root cause: BFCM over-sending in November.'),
                severity='warning',
            ),

            # E1_variant -- Month 20 (Jan 2026): multi-brand architecture problem
            _alert(
                'E1_variant', utc_dt(date(2026, 1, 22), 9),
                should_fire=True, confidence=0.92,
                signal_value=0.032, threshold_value=0.0022, threshold_direction='above',
                layer1=('Unsubscribe spike: 3.2% per send (14.5x baseline of 0.22%). '
                        'Root cause: menswear recommendations sent to womenswear subscribers.'),
                layer2=('Men\'s casualwear segment added to same Klaviyo account Jan 15 2026. '
                        'Audience overlap: 0% -- completely different customer base. '
                        'Sends Jan 17-20: 3.2% unsubscribe rate on womenswear list. '
                        'Estimated list damage: 840 unsubscribes in 4 days '
                        '(vs baseline 65/week). Immediate segmentation fix required.'),
                layer3=('Multi-brand Klaviyo architecture requires strict audience separation. '
                        'Recommended fix: separate Klaviyo accounts or mandatory '
                        'product_category filter on all sends. '
                        'Revenue impact of list damage: 840 unsubscribes × $218 LTV = $183K lost.'),
                severity='warning',
            ),

            # F1_variant -- Month 5 (Oct 2024 Day 3 post-redesign): Outlook rendering failure
            _alert(
                'F1_variant', utc_dt(date(2024, 10, 6), 9),
                should_fire=True, confidence=0.86,
                signal_value=0.34, threshold_value=0.10, threshold_direction='above',
                layer1=('Click rate dropped 34% on Outlook clients (8% of audience). '
                        'New CSS in mobile-first redesign not supported by Outlook.'),
                layer2=('Email redesign launched Oct 3 2024. '
                        'Mobile click rate: 1.8% -> 2.9% (improvement). '
                        'Outlook click rate: 2.1% -> 1.4% (34% decline over 3 days). '
                        'Outlook-affected subscribers: ~1,500 (8% of active list). '
                        'Action: add Outlook-specific fallback CSS using conditional comments.'),
                layer3=('S8 suppression applied first 48h (Oct 3-5). '
                        'Outlook error persisted past 48h -> State 2 alert fires Oct 6. '
                        'Outlook rendering issues typically require VML fallback for '
                        'CSS grid layouts. Previous template (pre-Oct 3) was Outlook-safe -- '
                        'rollback available as immediate mitigation.'),
                severity='warning',
            ),

            # Email IP risk -- Month 14 (Jul 2025): welcome series paused
            _alert(
                'email_ip_risk', utc_dt(date(2025, 7, 8), 11),
                should_fire=True, confidence=0.91,
                signal_value=340, threshold_value=0, threshold_direction='above',
                layer1=('Welcome series paused 3 days (Jul 8-11): photographer takedown notice. '
                        '340 new subscribers missed Email 1. Send retroactive welcome.'),
                layer2=('Photographer DMCA takedown notice received Jul 8 2025. '
                        'Welcome series Email 1 contained affected images. '
                        'Flow paused while legal/design team removed images. '
                        '340 subscribers who joined Jul 8-11 missed Email 1. '
                        'Estimated revenue recovery from retroactive send: $4,100 '
                        '(340 × $12 average Email 1 conversion value).'),
                layer3=('No direct precedent. Welcome series Email 1 is highest-converting '
                        'Klaviyo touchpoint ($12-18/recipient). 340-subscriber gap at '
                        'standard 8% conversion = 27 orders × $150 AOV = $4,050. '
                        'Retroactive send window: within 7 days for maximum effectiveness.'),
            ),
        ]

        # Filter against existing
        new_rows = [r for r in alerts_to_seed
                    if (r[0], r[1], r[2]) not in existing_keys]

        if not new_rows:
            logger.info('seed_alert_log_klaviyo | all entries already exist, skipping')
            return

        sql = f'INSERT INTO public.alert_log ({", ".join(ALERT_COLS)}) VALUES %s'
        psycopg2.extras.execute_values(cur, sql, new_rows)
        logger.info('seed_alert_log_klaviyo | inserted: %d (skipped %d existing)',
                    len(new_rows), len(alerts_to_seed) - len(new_rows))

    except Exception as e:
        logger.error('SOURCE: Klaviyo Seed | CLIENT: %s | ERROR: %s | CONTEXT: alert_log',
                     CLIENT_ID, str(e))
        raise

# ---------------------------------------------------------------------------
# 9. Validation (10 checks)
# ---------------------------------------------------------------------------

def validate_klaviyo_seed(conn) -> None:
    print('\n' + '=' * 72)
    print('KLAVIYO SEED VALIDATION -- 10 CHECKS')
    print('=' * 72)

    results = {}

    def run(sql, params=None):
        try:
            c = conn.cursor()
            c.execute(sql, params or ())
            return c.fetchall()
        except Exception as e:
            return [('ERR', str(e))]

    # CHECK 1 -- Profile count
    rows = run(f'SELECT COUNT(*) FROM {SCHEMA}.klaviyo_profiles')
    cnt  = rows[0][0]
    ok   = 18_000 <= cnt <= 18_500
    results[1] = 'PASS' if ok else 'FAIL'
    print(f'\n[{results[1]}] CHECK 1 -- Profile count (Month 1 proxy)')
    print(f'       actual={cnt:,}  expected=18,000-18,500')

    # CHECK 2 -- Flow count
    rows = run(f'SELECT COUNT(*) FROM {SCHEMA}.klaviyo_flows')
    cnt  = rows[0][0]
    ok   = cnt == 15
    results[2] = 'PASS' if ok else 'FAIL'
    print(f'\n[{results[2]}] CHECK 2 -- Flow count')
    print(f'       actual={cnt}  expected=15')

    # CHECK 3 -- BFCM sunset spike suppression (2 entries)
    rows = run(
        "SELECT event_type, event_name, start_date, end_date "
        "FROM client_azure_co.brand_event_calendar "
        "WHERE event_type = 'bfcm_sunset_spike' "
        "ORDER BY start_date"
    )
    ok = len(rows) >= 2
    results[3] = 'PASS' if ok else 'FAIL'
    print(f'\n[{results[3]}] CHECK 3 -- BFCM sunset spike suppression entries')
    print(f'       actual={len(rows)}  expected=2')
    for r in rows:
        print(f'       {r[0]}: {r[1]} ({r[2]} to {r[3]})')

    # CHECK 4 -- Alert3 pairs (30 activations x 2 stages = 60 rows)
    rows = run(
        "SELECT alert_type, COUNT(*) FROM public.alert_log "
        "WHERE alert_type IN ('Alert3_stage1','Alert3_stage2') "
        "GROUP BY alert_type ORDER BY alert_type"
    )
    s1_cnt = next((int(r[1]) for r in rows if r[0] == 'Alert3_stage1'), 0)
    s2_cnt = next((int(r[1]) for r in rows if r[0] == 'Alert3_stage2'), 0)
    total  = s1_cnt + s2_cnt
    ok = s1_cnt >= 28 and s2_cnt >= 28
    results[4] = 'PASS' if ok else 'FAIL'
    print(f'\n[{results[4]}] CHECK 4 -- Alert3 pairs')
    print(f'       Alert3_stage1={s1_cnt}  Alert3_stage2={s2_cnt}  '
          f'total={total}  expected>=56 (29 activations x 2)')

    # CHECK 5 -- E5 emergency alert
    rows = run(
        "SELECT severity, fired_at::date FROM public.alert_log "
        "WHERE alert_type = 'E5' ORDER BY fired_at"
    )
    has_emergency = any(r[0] == 'emergency' for r in rows)
    ok = len(rows) >= 1 and has_emergency
    results[5] = 'PASS' if ok else 'FAIL'
    print(f'\n[{results[5]}] CHECK 5 -- E5 deliverability alert (emergency severity in May 2025)')
    print(f'       rows={len(rows)}  has_emergency={has_emergency}')
    for r in rows:
        print(f'       severity={r[0]}  fired_at={r[1]}')

    # CHECK 6 -- Flow ID history
    rows = run(f'SELECT COUNT(*) FROM {SCHEMA}.klaviyo_flow_id_history')
    cnt  = rows[0][0]
    ok   = cnt >= 3
    results[6] = 'PASS' if ok else 'FAIL'
    print(f'\n[{results[6]}] CHECK 6 -- Flow ID history rows (Month 18 agency transition)')
    print(f'       actual={cnt}  expected>=3')

    # CHECK 7 -- Effective open rate calculation (effective = reported x 0.65)
    rows = run(
        f'SELECT AVG(effective_opens::numeric / NULLIF(reported_opens, 0)) '
        f'FROM {SCHEMA}.klaviyo_email_events '
        f'WHERE reported_opens > 0'
    )
    ratio = float(rows[0][0] or 0)
    ok    = 0.60 <= ratio <= 0.70
    results[7] = 'PASS' if ok else 'FAIL'
    print(f'\n[{results[7]}] CHECK 7 -- Effective open rate (effective/reported ratio)')
    print(f'       actual={ratio:.4f}  expected=~0.65 (0.60-0.70)')

    # CHECK 8 -- Double-attribution gap
    rows = run(
        f'SELECT AVG((klaviyo_native_revenue - profit_sentinel_adjusted_revenue) '
        f'/ NULLIF(klaviyo_native_revenue, 0)) '
        f'FROM {SCHEMA}.klaviyo_email_events '
        f'WHERE klaviyo_native_revenue > 0'
    )
    gap = float(rows[0][0] or 0)
    ok  = 0.18 <= gap <= 0.32
    results[8] = 'PASS' if ok else 'FAIL'
    print(f'\n[{results[8]}] CHECK 8 -- Double-attribution gap '
          f'(klaviyo_native vs profit_sentinel_adjusted)')
    print(f'       actual={gap:.4f}  expected=0.18-0.32')

    # CHECK 9 -- SMS events exist
    rows = run(f'SELECT COUNT(*) FROM {SCHEMA}.klaviyo_sms_events')
    cnt  = rows[0][0]
    ok   = cnt > 0
    results[9] = 'PASS' if ok else 'FAIL'
    print(f'\n[{results[9]}] CHECK 9 -- SMS events (Flow 7)')
    print(f'       actual={cnt}  expected>0')

    # CHECK 10 -- Compliance fields (single_optin majority, double_optin ~8%)
    rows = run(
        f'SELECT consent_method, COUNT(*) '
        f'FROM {SCHEMA}.klaviyo_profiles '
        f'GROUP BY consent_method ORDER BY consent_method'
    )
    methods = {r[0]: int(r[1]) for r in rows}
    total_p = sum(methods.values())
    dbl_pct = methods.get('double_optin', 0) / max(1, total_p)
    ok = 'single_optin' in methods and 'double_optin' in methods and 0.05 <= dbl_pct <= 0.12
    results[10] = 'PASS' if ok else 'FAIL'
    print(f'\n[{results[10]}] CHECK 10 -- Compliance fields (consent_method)')
    for method, cnt in sorted(methods.items()):
        print(f'       {method}: {cnt:,} ({cnt/max(1,total_p)*100:.1f}%)')
    print(f'       double_optin pct={dbl_pct:.3f}  expected=0.05-0.12 (~8%)')

    # Summary
    print()
    print('=' * 72)
    print('SUMMARY')
    print('=' * 72)
    for k, v in results.items():
        print(f'  CHECK {k:2d}: {v}')
    passed = sum(1 for v in results.values() if v == 'PASS')
    print(f'  {passed}/{len(results)} checks passed')
    print('=' * 72)

# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def load_manifest() -> list[int]:
    manifest_path = os.path.join(os.path.dirname(__file__), 'seed_manifest_shopify.json')
    try:
        with open(manifest_path) as f:
            m = json.load(f)
        cids = m.get('customer_ids', [])
        logger.info('Loaded manifest: %d customer_ids', len(cids))
        return cids
    except Exception as e:
        logger.warning('Could not load manifest (%s) -- using sequential IDs', e)
        return list(range(10_000_001, 10_005_001))

def main():
    logger.info('SOURCE: Klaviyo Seed | CLIENT: %s | Starting', CLIENT_ID)
    conn = get_conn()

    try:
        cur = conn.cursor()

        manifest_cids = load_manifest()

        logger.info('Step 0/8 -- create_tables (FIX 6)')
        create_tables(cur)
        conn.commit()

        logger.info('Step 1/8 -- seed_profiles')
        seed_profiles(cur, manifest_cids)
        conn.commit()

        logger.info('Step 2/8 -- seed_flows')
        seed_flows(cur)
        conn.commit()

        logger.info('Step 3/8 -- seed_campaigns')
        seed_campaigns(cur)
        conn.commit()

        logger.info('Step 4/8 -- seed_email_events')
        seed_email_events(cur, manifest_cids)
        conn.commit()

        logger.info('Step 5/8 -- seed_sms_events')
        seed_sms_events(cur, manifest_cids)
        conn.commit()

        logger.info('Step 6/8 -- seed_flow_id_history')
        seed_flow_id_history(cur)
        conn.commit()

        logger.info('Step 7/8 -- seed_brand_event_calendar_klaviyo')
        seed_brand_event_calendar_klaviyo(cur)
        conn.commit()

        logger.info('Step 8/8 -- seed_alert_log_klaviyo')
        seed_alert_log_klaviyo(cur)
        conn.commit()

        logger.info('SOURCE: Klaviyo Seed | CLIENT: %s | Complete', CLIENT_ID)

    except Exception as e:
        conn.rollback()
        logger.error('SOURCE: Klaviyo Seed | CLIENT: %s | ERROR: %s | CONTEXT: main',
                     CLIENT_ID, str(e))
        cur.close()
        conn.close()
        raise

    validate_klaviyo_seed(conn)
    cur.close()
    conn.close()

if __name__ == '__main__':
    main()
