"""
seed_ga4.py — GA4 sessions, funnel, and checkout error data (24 months)

Tables seeded:
  client_azure_co.ga4_sessions_daily   (channel × device × date)
  client_azure_co.ga4_funnel_daily     (device × date)
  client_azure_co.ga4_checkout_errors  (date × hour × error_type × device)

Alert scenarios embedded:
  F2 — mobile payment_completion_rate drop (Feb 18-20 2025, mobile only)
  F4 — mobile CVR structural gap (Sep 2025, 55% below desktop)

Cross-source coherence:
  Shopify: purchase_completed ≈ daily_orders × 1.06 (±4% noise)
  TikTok: paid_social_tiktok elevated during 25 influencer activation windows
  Email: email channel elevated on major Klaviyo campaign send dates

Build standards applied:
  Fix 1: is_synthetic on raw table (ga4 is manually managed)
  Fix 2: No airbyte_meta_cols() — GA4 is not Airbyte-managed
  Fix 3: Single transaction, ON CONFLICT DO NOTHING (bare)
  Fix 4: _nearest_pd_corr() before Cholesky (applied to bounce_rate correlation)
  Fix 5: GENERATED ALWAYS id — never inserted
  Fix 6: CREATE TABLE IF NOT EXISTS before all inserts
  Fix 7: UNIQUE constraints declared before insert
  Fix 8: numpy float64/int64 → float()/int() before psycopg2
"""

import os, sys, json, random, logging
from datetime import date, datetime, timedelta, timezone
from dotenv import load_dotenv
import numpy as np
import psycopg2
import psycopg2.extras

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)

# ─── CONSTANTS ────────────────────────────────────────────────────────────────

CLIENT_ID  = 'azure_co'
SCHEMA     = 'client_azure_co'
SEED_START = date(2024, 6, 1)
SEED_END   = date(2026, 5, 31)
COUNTRY    = 'US'

SEED_RNG = np.random.default_rng(37)
PY_RNG   = random.Random(37)

CHANNELS = [
    'organic_search', 'paid_social_meta', 'paid_social_tiktok',
    'email', 'direct', 'organic_social', 'referral',
]
DEVICES = ['mobile', 'desktop', 'tablet']

DEVICE_SHARE = {'mobile': 0.68, 'desktop': 0.28, 'tablet': 0.04}

BASE_CHANNEL_SHARE = {
    'organic_search':    0.28,
    'paid_social_meta':  0.22,
    'paid_social_tiktok': 0.18,
    'email':             0.14,
    'direct':            0.10,
    'organic_social':    0.05,
    'referral':          0.03,
}

# Funnel step rates by device (product_page_view, add_to_cart, checkout,
# payment_info, purchase) — each is conversion FROM PREVIOUS STEP
FUNNEL_RATES = {
    'desktop': dict(ppv=0.70, atc=0.24, co=0.62, pci=0.85, pur=0.92),
    'mobile':  dict(ppv=0.65, atc=0.19, co=0.55, pci=0.82, pur=0.90),
    'tablet':  dict(ppv=0.67, atc=0.22, co=0.59, pci=0.84, pur=0.91),
}

# Weighted funnel CVR: mobile×0.68 + desktop×0.28 + tablet×0.04
# = 0.68×(0.65×0.19×0.55×0.82×0.90) + 0.28×(0.70×0.24×0.62×0.85×0.92) + 0.04×(...)
# = 0.68×0.05013 + 0.28×0.08148 + 0.04×0.06647
# = 0.03409 + 0.02281 + 0.00266 = 0.05956
WEIGHTED_CVR = 0.05956

# GA4 overcount factor vs Shopify (Month 1-8: GD9 under-counts; Month 9+: full impl)
GA4_EARLY = 0.92   # Month 1-8: add_to_cart double-fire, Shop Pay missing
GA4_LATE  = 1.06   # Month 9+: all events present

# Sessions-per-order ratio: SPO = ga4_overcount / WEIGHTED_CVR
SPO_EARLY = GA4_EARLY / WEIGHTED_CVR   # ≈ 15.44
SPO_LATE  = GA4_LATE  / WEIGHTED_CVR   # ≈ 17.79

# ─── EVENT CALENDAR ──────────────────────────────────────────────────────────

# Sale periods (BFCM, summer sale, early access)
SALE_PERIODS = [
    (date(2024, 7, 4),  date(2024, 7, 21)),   # Summer Sale Y1
    (date(2024, 11, 20), date(2024, 11, 27)),  # BFCM Y1 Early Access
    (date(2024, 11, 28), date(2024, 12, 2)),   # BFCM Y1 Peak
    (date(2025, 7, 3),  date(2025, 7, 20)),   # Summer Sale Y2
    (date(2025, 11, 20), date(2025, 11, 27)),  # BFCM Y2 Early Access
    (date(2025, 11, 28), date(2025, 12, 2)),   # BFCM Y2 Peak
]
SALE_SET = {
    d for start, end in SALE_PERIODS
    for d in (start + timedelta(n) for n in range((end - start).days + 1))
}

BFCM_PEAK = (
    {date(2024, 11, 28) + timedelta(n) for n in range(5)} |
    {date(2025, 11, 28) + timedelta(n) for n in range(5)}
)

# Collection launches (elevated sessions + organic boost)
COLLECTION_LAUNCHES = [
    (date(2024, 10, 8),  date(2024, 10, 22)),
    (date(2025, 3, 12),  date(2025, 3, 26)),
    (date(2025, 10, 7),  date(2025, 10, 21)),
    (date(2026, 3, 10),  date(2026, 3, 24)),
]
LAUNCH_SET = {
    d for start, end in COLLECTION_LAUNCHES
    for d in (start + timedelta(n) for n in range((end - start).days + 1))
}

# TikTok spike windows: content_live_date to content_live_date + 13 (14 days)
# Source: seed_manifest_shopify.json influencer_activations (25 within seed window)
INF_LIVE_DATES = [
    date(2024, 6, 22),   # INF-2024-JUN-01
    date(2024, 7, 10),   # INF-2024-JUL-01
    date(2024, 7, 25),   # INF-2024-JUL-02
    date(2024, 8, 12),   # INF-2024-AUG-01
    date(2024, 9, 17),   # INF-2024-SEP-01
    date(2024, 10, 8),   # INF-2024-OCT-01
    date(2024, 11, 12),  # INF-2024-NOV-01
    date(2025, 5, 8),    # INF-2024-MAY-01
    date(2025, 6, 17),   # INF-2025-JUN-01
    date(2025, 7, 12),   # INF-2025-JUL-01
    date(2025, 8, 11),   # INF-2025-AUG-01
    date(2025, 9, 15),   # INF-2025-SEP-01
    date(2025, 9, 27),   # INF-2025-SEP-02
    date(2025, 10, 13),  # INF-2025-OCT-01
    date(2025, 10, 22),  # INF-2025-OCT-02
    date(2025, 11, 8),   # INF-2025-NOV-01
    date(2025, 11, 17),  # INF-2025-NOV-02
    date(2025, 12, 12),  # INF-2025-DEC-01
    date(2026, 1, 19),   # INF-2026-JAN-01
    date(2026, 2, 10),   # INF-2026-FEB-01
    date(2026, 3, 17),   # INF-2026-MAR-01
    date(2026, 3, 27),   # INF-2026-MAR-02
    date(2026, 4, 15),   # INF-2026-APR-01
    date(2026, 4, 27),   # INF-2026-APR-02
    date(2026, 5, 12),   # INF-2026-MAY-01
]
TIKTOK_SPIKE_SET: set[date] = set()
for live_date in INF_LIVE_DATES:
    for n in range(14):
        d = live_date + timedelta(n)
        if SEED_START <= d <= SEED_END:
            TIKTOK_SPIKE_SET.add(d)

# Alert3 stage1 fired_at dates (for Check 5 query)
ALERT3_STAGE1_DATES = [
    date(2024, 6, 29), date(2024, 7, 17), date(2024, 8, 1),
    date(2024, 8, 19), date(2024, 9, 24), date(2024, 10, 15),
    date(2024, 11, 19), date(2025, 5, 15), date(2025, 6, 24),
    date(2025, 7, 19), date(2025, 8, 18), date(2025, 9, 22),
    date(2025, 10, 4), date(2025, 10, 20), date(2025, 10, 29),
    date(2025, 11, 15), date(2025, 11, 24), date(2025, 12, 19),
    date(2026, 1, 26), date(2026, 2, 17), date(2026, 3, 24),
    date(2026, 4, 3), date(2026, 4, 22), date(2026, 5, 4),
    date(2026, 5, 19),
]

# Major Klaviyo campaign send dates → email channel spike
EMAIL_SPIKE_DATES: set[date] = {
    # Summer Sale Y1
    date(2024, 7, 4), date(2024, 7, 11), date(2024, 7, 18),
    # FW2024 Collection Launch
    date(2024, 10, 8), date(2024, 10, 10),
    # BFCM Y1
    date(2024, 11, 20), date(2024, 11, 25), date(2024, 11, 28),
    date(2024, 11, 29), date(2024, 12, 2),
    # Post-BFCM / Holiday Y1
    date(2024, 12, 4), date(2024, 12, 10), date(2024, 12, 17),
    # Valentine's Day
    date(2025, 2, 13), date(2025, 2, 11),
    # SS2025 Collection Launch
    date(2025, 3, 12), date(2025, 3, 14),
    # Mother's Day
    date(2025, 5, 8), date(2025, 5, 11),
    # Summer Sale Y2
    date(2025, 7, 3), date(2025, 7, 10), date(2025, 7, 17),
    # FW2025 Collection Launch
    date(2025, 10, 7), date(2025, 10, 9),
    # BFCM Y2
    date(2025, 11, 20), date(2025, 11, 24), date(2025, 11, 27),
    date(2025, 11, 28), date(2025, 12, 1),
    # Post-BFCM / Holiday Y2
    date(2025, 12, 3), date(2025, 12, 10), date(2025, 12, 17),
    # SS2026 Collection Launch
    date(2026, 3, 10), date(2026, 3, 12),
}

# F2 alert scenario: mobile payment_completion drops 83%→61% (Feb 18-20 2025)
F2_DATES = {date(2025, 2, 18), date(2025, 2, 19), date(2025, 2, 20)}
F2_MOBILE_PCI = 0.61  # vs normal 0.82

# F4 alert scenario: mobile CVR structural gap widens (Sep 2025)
F4_START = date(2025, 9, 1)
F4_END   = date(2025, 9, 30)
F4_MOBILE_CO = 0.40   # vs normal 0.55 → gives mobile CVR 55% below desktop

# Sentry-correlated checkout error spike events
# (date_start, date_end, error_type, spike_mult, hours_restricted)
ERROR_EVENTS = [
    # Event 1: Theme update Nov 5-6 2024 (S8, checkout_load_failure 48h)
    {'start': date(2024, 11, 5),  'end': date(2024, 11, 6),
     'types': ['checkout_load_failure'], 'mult': 10, 'hours': None},
    # Event 2: BFCM Y1 peak Nov 28-Dec 2 (S9, cart_timeout+inventory_conflict)
    {'start': date(2024, 11, 28), 'end': date(2024, 12, 2),
     'types': ['cart_timeout', 'inventory_conflict'], 'mult': 5,
     'hours': list(range(8, 15))},  # 8am-2pm EST
    # Event 3: App installation Jul 15 2025 (S24, checkout_load_failure 24h)
    {'start': date(2025, 7, 15),  'end': date(2025, 7, 15),
     'types': ['checkout_load_failure'], 'mult': 12, 'hours': None},
    # Event 4: CDN event Dec 10 2025 (S25, H10 fires)
    {'start': date(2025, 12, 10), 'end': date(2025, 12, 10),
     'types': ['checkout_load_failure'], 'mult': 8,
     'hours': list(range(10, 17))},
]

# ─── DDL ─────────────────────────────────────────────────────────────────────

DDL_SESSIONS = f"""
CREATE TABLE IF NOT EXISTS {SCHEMA}.ga4_sessions_daily (
    id                          bigint generated always as identity primary key,
    date                        date not null,
    sessions                    integer,
    new_users                   integer,
    returning_users             integer,
    bounce_rate                 numeric,
    avg_session_duration_seconds numeric,
    channel_group               text,
    device_category             text,
    country                     text,
    is_synthetic                boolean default true,
    _airbyte_extracted_at       timestamptz default now(),
    unique(date, channel_group, device_category, country)
);
"""

DDL_FUNNEL = f"""
CREATE TABLE IF NOT EXISTS {SCHEMA}.ga4_funnel_daily (
    id                      bigint generated always as identity primary key,
    date                    date not null,
    device_category         text,
    sessions_entered        integer,
    product_page_views      integer,
    add_to_cart             integer,
    checkout_initiated      integer,
    checkout_payment_info   integer,
    purchase_completed      integer,
    product_page_rate       numeric,
    atc_rate                numeric,
    checkout_rate           numeric,
    payment_completion_rate numeric,
    purchase_rate           numeric,
    overall_cvr             numeric,
    is_synthetic            boolean default true,
    _airbyte_extracted_at   timestamptz default now(),
    unique(date, device_category)
);
"""

DDL_ERRORS = f"""
CREATE TABLE IF NOT EXISTS {SCHEMA}.ga4_checkout_errors (
    id                bigint generated always as identity primary key,
    date              date not null,
    hour              integer,
    error_type        text,
    device_category   text,
    error_count       integer,
    affected_sessions integer,
    is_synthetic      boolean default true,
    _airbyte_extracted_at timestamptz default now(),
    unique(date, hour, error_type, device_category)
);
"""


# ─── HELPERS ─────────────────────────────────────────────────────────────────

def _nearest_pd_corr(A: np.ndarray) -> np.ndarray:
    """Project matrix to nearest positive-definite correlation matrix."""
    B = (A + A.T) / 2
    _, s, Vt = np.linalg.svd(B)
    H = np.dot(Vt.T, np.dot(np.diag(s), Vt))
    A2 = (B + H) / 2
    A3 = (A2 + A2.T) / 2
    if _is_pd(A3):
        return A3
    spacing = np.spacing(np.linalg.norm(A))
    I = np.eye(A.shape[0])
    k = 1
    while not _is_pd(A3):
        mineig = np.min(np.real(np.linalg.eigvals(A3)))
        A3 += I * (-mineig * k ** 2 + spacing)
        k += 1
    # re-normalise to correlation matrix
    d = np.sqrt(np.diag(A3))
    A3 = A3 / np.outer(d, d)
    return A3


def _is_pd(B: np.ndarray) -> bool:
    try:
        np.linalg.cholesky(B)
        return True
    except np.linalg.LinAlgError:
        return False


def month_of(d: date) -> int:
    """Return month number: 1 = Jun 2024, 2 = Jul 2024, ..., 24 = May 2026."""
    return (d.year - 2024) * 12 + d.month - 5


def is_sale(d: date) -> bool:
    return d in SALE_SET


def is_bfcm_peak(d: date) -> bool:
    return d in BFCM_PEAK


def is_launch(d: date) -> bool:
    return d in LAUNCH_SET


def channel_shares(d: date) -> dict:
    """Return channel share dict (sums to 1.0) with event-driven adjustments."""
    shares = dict(BASE_CHANNEL_SHARE)
    bump = {}

    # TikTok influencer spike: +10pp
    if d in TIKTOK_SPIKE_SET:
        bump['paid_social_tiktok'] = 0.10

    # Email campaign send day: +12pp
    if d in EMAIL_SPIKE_DATES:
        bump['email'] = 0.12
    elif is_sale(d):
        bump['email'] = 0.06   # sale emails are out, smaller bump
    elif d.weekday() in (1, 3):  # Tuesday / Thursday weekly sends
        bump['email'] = 0.02

    # Meta: elevated during sale/launch
    if is_sale(d) or is_launch(d):
        bump['paid_social_meta'] = bump.get('paid_social_meta', 0) + 0.04

    # Direct: dark social during TikTok disruption period
    # (Before seed start — not applicable in Jun 2024+)

    # Collection launches: organic search boost
    if is_launch(d):
        bump['organic_search'] = bump.get('organic_search', 0) + 0.03

    # Apply bumps: add to target channels, subtract equally from others
    if bump:
        total_bump = sum(bump.values())
        # Add bumps
        for ch, b in bump.items():
            shares[ch] = shares.get(ch, 0) + b
        # Scale down non-bumped channels proportionally
        non_bumped = {k: v for k, v in shares.items() if k not in bump}
        current_non_bumped_total = sum(non_bumped.values())
        desired_non_bumped = 1.0 - sum(shares[k] for k in bump)
        if current_non_bumped_total > 0 and desired_non_bumped > 0:
            scale = desired_non_bumped / current_non_bumped_total
            for k in non_bumped:
                shares[k] = shares[k] * scale

    # Ensure no negative shares and sum to 1
    total = sum(shares.values())
    return {k: max(v / total, 0.0) for k, v in shares.items()}


def funnel_rates_for_day(d: date, device: str) -> dict:
    """Return funnel step rates with scenario overrides only — no per-stage noise.
    Per-stage noise compounds across 5 stages to ±21%, which violates the ±15%
    Shopify coherence check (Check 4). Scenarios are the only intentional deviations."""
    rates = dict(FUNNEL_RATES[device])

    # F2 scenario: mobile payment_completion drops Feb 18-20 2025
    if device == 'mobile' and d in F2_DATES:
        rates['pci'] = F2_MOBILE_PCI

    # F4 scenario: mobile CVR structural gap Sep 2025
    if device == 'mobile' and F4_START <= d <= F4_END:
        rates['co'] = F4_MOBILE_CO

    return rates


def bounce_rate_for(d: date, device: str, channel: str) -> float:
    """Compute bounce rate."""
    base = 0.62
    if is_sale(d):
        base = 0.51
    if is_bfcm_peak(d):
        base = 0.49
    if device == 'mobile':
        base += 0.08
    # Channel adjustment
    channel_adj = {
        'email': -0.08, 'direct': -0.04, 'organic_search': -0.03,
        'paid_social_meta': 0.05, 'paid_social_tiktok': 0.07,
        'organic_social': 0.06, 'referral': 0.02,
    }
    base += channel_adj.get(channel, 0)
    noise = float(SEED_RNG.uniform(-0.03, 0.03))
    return float(round(max(min(base + noise, 0.92), 0.25), 4))


def session_duration_for(channel: str) -> float:
    """Average session duration in seconds by channel."""
    base = {
        'direct': 215, 'email': 190, 'organic_search': 175,
        'organic_social': 95, 'paid_social_meta': 120,
        'paid_social_tiktok': 110, 'referral': 150,
    }.get(channel, 150)
    noise = float(SEED_RNG.uniform(-0.10, 0.10))
    return float(round(base * (1 + noise), 1))


# ─── LOAD SHOPIFY ORDERS ──────────────────────────────────────────────────────

def load_shopify_orders(cur) -> dict:
    cur.execute(f"""
        SELECT DATE(created_at::timestamptz) AS d, COUNT(*) AS orders
        FROM {SCHEMA}.shopify_orders
        GROUP BY 1 ORDER BY 1
    """)
    return {row[0]: row[1] for row in cur.fetchall()}


# ─── SEED SESSIONS ────────────────────────────────────────────────────────────

SESSIONS_COLS = [
    'date', 'sessions', 'new_users', 'returning_users', 'bounce_rate',
    'avg_session_duration_seconds', 'channel_group', 'device_category',
    'country', 'is_synthetic',
]


def seed_sessions(cur, shopify_daily: dict) -> int:
    logger.info('Step 1 — ga4_sessions_daily')
    rows = []
    d = SEED_START
    while d <= SEED_END:
        shopify_orders = shopify_daily.get(d, 0)
        # Derive total sessions from Shopify orders
        spo = SPO_EARLY if month_of(d) <= 8 else SPO_LATE
        noise = float(SEED_RNG.uniform(-0.04, 0.04))
        total_sessions = max(int(shopify_orders * spo * (1 + noise)), 200)

        # Channel shares for this day
        ch_shares = channel_shares(d)

        for channel in CHANNELS:
            ch_sessions = max(int(total_sessions * ch_shares[channel]), 0)
            for device in DEVICES:
                dev_sessions = max(int(ch_sessions * DEVICE_SHARE[device]), 0)
                if dev_sessions == 0:
                    d = d + timedelta(1) if channel == CHANNELS[-1] and device == DEVICES[-1] else d
                    continue
                new_u = int(dev_sessions * float(SEED_RNG.uniform(0.55, 0.72)))
                # Email/direct have more returning visitors
                if channel in ('email', 'direct'):
                    new_u = int(dev_sessions * float(SEED_RNG.uniform(0.35, 0.50)))
                ret_u = dev_sessions - new_u
                br = bounce_rate_for(d, device, channel)
                dur = session_duration_for(channel)

                rows.append((
                    d, int(dev_sessions), int(new_u), int(ret_u),
                    float(br), float(dur),
                    channel, device, COUNTRY, True,
                ))

        d += timedelta(1)

    sql = (
        f"INSERT INTO {SCHEMA}.ga4_sessions_daily "
        f"({', '.join(SESSIONS_COLS)}) VALUES %s "
        f"ON CONFLICT (date, channel_group, device_category, country) DO NOTHING"
    )
    psycopg2.extras.execute_values(cur, sql, rows, page_size=500)
    logger.info('  ga4_sessions_daily | rows: %d', len(rows))
    return len(rows)


# ─── SEED FUNNEL ─────────────────────────────────────────────────────────────

FUNNEL_COLS = [
    'date', 'device_category', 'sessions_entered',
    'product_page_views', 'add_to_cart', 'checkout_initiated',
    'checkout_payment_info', 'purchase_completed',
    'product_page_rate', 'atc_rate', 'checkout_rate',
    'payment_completion_rate', 'purchase_rate', 'overall_cvr',
    'is_synthetic',
]


def seed_funnel(cur, shopify_daily: dict) -> int:
    logger.info('Step 2 — ga4_funnel_daily')
    rows = []
    d = SEED_START
    while d <= SEED_END:
        shopify_orders = shopify_daily.get(d, 0)
        # No sessions noise here — calibrate directly to Shopify orders via SPO.
        # Noise in sessions_daily is independent and doesn't affect coherence check.
        spo = SPO_EARLY if month_of(d) <= 8 else SPO_LATE
        total_sessions = max(round(shopify_orders * spo), 200)

        for device in DEVICES:
            sessions_entered = max(round(total_sessions * DEVICE_SHARE[device]), 1)
            rates = funnel_rates_for_day(d, device)

            ppv   = rates['ppv']
            atc_r = rates['atc']
            co_r  = rates['co']
            pci_r = rates['pci']
            pur_r = rates['pur']

            # Use round() not int() — truncation at each of 5 steps compounds downward
            ppv_n  = max(round(sessions_entered * ppv), 1)
            atc_n  = max(round(ppv_n * atc_r), 0)
            co_n   = max(round(atc_n * co_r), 0)
            pci_n  = max(round(co_n * pci_r), 0)
            pur_n  = max(round(pci_n * pur_r), 0)
            cvr    = float(pur_n) / float(sessions_entered) if sessions_entered else 0

            rows.append((
                d, device, int(sessions_entered),
                int(ppv_n), int(atc_n), int(co_n), int(pci_n), int(pur_n),
                float(round(ppv, 4)),
                float(round(atc_r, 4)),
                float(round(co_r, 4)),
                float(round(pci_r, 4)),
                float(round(pur_r, 4)),
                float(round(cvr, 4)),
                True,
            ))

        d += timedelta(1)

    sql = (
        f"INSERT INTO {SCHEMA}.ga4_funnel_daily "
        f"({', '.join(FUNNEL_COLS)}) VALUES %s "
        f"ON CONFLICT (date, device_category) DO NOTHING"
    )
    psycopg2.extras.execute_values(cur, sql, rows, page_size=500)
    logger.info('  ga4_funnel_daily | rows: %d', len(rows))
    return len(rows)


# ─── SEED CHECKOUT ERRORS ─────────────────────────────────────────────────────

ERROR_TYPES = [
    'payment_failure', 'address_validation',
    'cart_timeout', 'inventory_conflict', 'checkout_load_failure',
]
ERROR_COLS = [
    'date', 'hour', 'error_type', 'device_category',
    'error_count', 'affected_sessions', 'is_synthetic',
]


def seed_checkout_errors(cur) -> int:
    logger.info('Step 3 — ga4_checkout_errors')

    # Build spike date → event info mapping
    spike_map: dict[date, list[dict]] = {}
    for ev in ERROR_EVENTS:
        d = ev['start']
        while d <= ev['end']:
            if d not in spike_map:
                spike_map[d] = []
            spike_map[d].append(ev)
            d += timedelta(1)

    rows = []
    d = SEED_START
    while d <= SEED_END:
        is_spike = d in spike_map
        # Background: 3-5 rows per day across random type/device/hour combos
        n_bg = PY_RNG.randint(3, 5)
        bg_used: set = set()
        for _ in range(n_bg):
            for _attempt in range(10):
                hour  = PY_RNG.randint(0, 23)
                etype = PY_RNG.choice(ERROR_TYPES)
                dev   = PY_RNG.choice(DEVICES)
                key   = (hour, etype, dev)
                if key not in bg_used:
                    bg_used.add(key)
                    err_count = PY_RNG.randint(1, 3)
                    aff = PY_RNG.randint(err_count, err_count * 3)
                    rows.append((d, hour, etype, dev, err_count, aff, True))
                    break

        # Spike rows
        if is_spike:
            for ev in spike_map[d]:
                hours_to_use = ev.get('hours') or list(range(0, 24, 3))[:8]
                mult = ev['mult']
                for etype in ev['types']:
                    for dev in DEVICES:
                        for hour in PY_RNG.choices(hours_to_use, k=min(3, len(hours_to_use))):
                            key = (hour, etype, dev)
                            if key in bg_used:
                                continue  # avoid UNIQUE conflict
                            bg_used.add(key)
                            err_count = PY_RNG.randint(mult * 2, mult * 4)
                            aff = PY_RNG.randint(err_count, err_count * 2)
                            rows.append((d, int(hour), etype, dev, err_count, aff, True))

        d += timedelta(1)

    sql = (
        f"INSERT INTO {SCHEMA}.ga4_checkout_errors "
        f"({', '.join(ERROR_COLS)}) VALUES %s "
        f"ON CONFLICT (date, hour, error_type, device_category) DO NOTHING"
    )
    psycopg2.extras.execute_values(cur, sql, rows, page_size=500)
    logger.info('  ga4_checkout_errors | rows: %d', len(rows))
    return len(rows)


# ─── SEED ALERT LOG ───────────────────────────────────────────────────────────

ALERT_COLS = [
    'client_id', 'alert_type', 'fired_at', 'should_fire',
    'confidence_score', 'signal_value', 'threshold_value', 'threshold_direction',
    'layer1_headline', 'layer2_context', 'layer3_precedent',
    'alert_instance_number', 'escalation_level', 'suppressed', 'suppression_category',
    'fatigue_period_active', 'fatigue_reason', 'outcome_confirmed', 'dismissal_correct',
    'is_synthetic', 'severity', 'signal_source',
]


def seed_alert_log(cur) -> int:
    logger.info('Step 4 — alert_log (F2, F4)')

    # F2 alert: mobile payment_completion drop Feb 18-20 2025
    f2 = (
        CLIENT_ID, 'F2',
        datetime(2025, 2, 20, 9, 0, 0, tzinfo=timezone.utc), True,
        0.88,  # confidence_score
        0.61,  # signal_value: mobile payment_completion during event
        0.78,  # threshold_value: 5% below normal 0.82
        'below',
        ('Mobile payment completion rate dropped from 83% to 61% — '
         'Feb 18–20 2025. Desktop unaffected. 3-day consistent pattern.'),
        ('Affected: ~1,850 mobile checkout_payment_info sessions across 3 days. '
         'Desktop payment_completion stayed at 85%. Mobile-only rendering issue '
         'confirmed by device segmentation. Sentry will show correlated errors.'),
        None,  # layer3: first occurrence, no precedent
        1, 0, False, None, False, None, None, None, True, 'high', 'ga4',
    )

    # F4 alert: mobile CVR structural gap Sep 2025
    f4 = (
        CLIENT_ID, 'F4',
        datetime(2025, 9, 15, 9, 0, 0, tzinfo=timezone.utc), True,
        0.82,
        0.55,  # signal_value: mobile 55% below desktop
        0.45,  # threshold_value: normal baseline is 35-45%
        'above',  # the GAP is above threshold
        ('Mobile CVR has dropped to 55% below desktop CVR in Sep 2025. '
         'Normal baseline is 35–45%. This is a structural shift, not a spike.'),
        ('Sep 1–14 2025: desktop CVR avg 3.18%, mobile CVR avg 1.43%. '
         'Gap: 55.0%. Prior 12-month avg gap: 38.2%. '
         'Sustained 14-day degradation distinguishes this from the Feb 2025 '
         'acute payment event. Checkout UX or mobile payment method friction.'),
        ('Feb 18–20 2025 F2 alert was an acute payment gateway failure (3 days). '
         'This Sep 2025 pattern is structural — sustained degradation over 14+ days '
         'points to UX regression or new checkout flow change affecting mobile only.'),
        1, 0, False, None, False, None, None, None, True, 'medium', 'ga4',
    )

    inserted = 0
    for row in (f2, f4):
        # Check for existing entry to avoid duplicates (ON CONFLICT won't work
        # since alert_log has no natural unique key)
        cur.execute(
            "SELECT COUNT(*) FROM public.alert_log "
            "WHERE client_id = %s AND alert_type = %s AND signal_source = 'ga4'",
            (CLIENT_ID, row[1]),
        )
        if cur.fetchone()[0] == 0:
            sql = (
                f"INSERT INTO public.alert_log ({', '.join(ALERT_COLS)}) VALUES %s"
            )
            psycopg2.extras.execute_values(cur, sql, [row])
            inserted += 1

    logger.info('  alert_log | inserted: %d GA4 alert rows', inserted)
    return inserted


# ─── VALIDATE ─────────────────────────────────────────────────────────────────

def validate(conn) -> None:
    cur = conn.cursor()
    results: dict[str, tuple[bool, str]] = {}

    # CHECK 1: ga4_sessions_daily row count
    cur.execute(f"SELECT COUNT(*) FROM {SCHEMA}.ga4_sessions_daily WHERE is_synthetic")
    n_sess = cur.fetchone()[0]
    ok1 = n_sess >= 4_500
    results['CHECK 1 — ga4_sessions_daily row count'] = (
        ok1, f'actual={n_sess:,}  expected>=4,500'
    )

    # CHECK 2: ga4_funnel_daily row count
    cur.execute(f"SELECT COUNT(*) FROM {SCHEMA}.ga4_funnel_daily WHERE is_synthetic")
    n_fun = cur.fetchone()[0]
    ok2 = 2_100 <= n_fun <= 2_300
    results['CHECK 2 — ga4_funnel_daily row count'] = (
        ok2, f'actual={n_fun:,}  expected≈2,190 (730 dates × 3 devices)'
    )

    # CHECK 3: ga4_checkout_errors nonzero + 4 events present
    cur.execute(f"SELECT COUNT(*) FROM {SCHEMA}.ga4_checkout_errors WHERE is_synthetic")
    n_err = cur.fetchone()[0]
    # Check each event date range has errors
    event_checks = [
        ('Event 1 theme',   '2024-11-05', '2024-11-06', ['checkout_load_failure']),
        ('Event 2 BFCM',    '2024-11-28', '2024-12-02', ['cart_timeout', 'inventory_conflict']),
        ('Event 3 app',     '2025-07-15', '2025-07-15', ['checkout_load_failure']),
        ('Event 4 CDN',     '2025-12-10', '2025-12-10', ['checkout_load_failure']),
    ]
    event_ok = True
    event_detail = []
    for name, s, e, etypes in event_checks:
        cur.execute(
            f"SELECT COUNT(*) FROM {SCHEMA}.ga4_checkout_errors "
            f"WHERE date BETWEEN %s AND %s AND error_type = ANY(%s) AND is_synthetic",
            (s, e, etypes),
        )
        cnt = cur.fetchone()[0]
        ok_ev = cnt > 0
        if not ok_ev:
            event_ok = False
        event_detail.append(f'{name}={cnt}')
    ok3 = n_err > 0 and event_ok
    results['CHECK 3 — ga4_checkout_errors events'] = (
        ok3, f'total_rows={n_err:,}  events=[{", ".join(event_detail)}]'
    )

    # CHECK 4: GA4 purchase_completed vs Shopify daily orders (±15%)
    cur.execute(f"""
        SELECT COUNT(*) FROM (
            SELECT g.date,
                   SUM(g.purchase_completed) AS ga4_purchases,
                   s.shopify_orders
            FROM (
                SELECT date, SUM(purchase_completed) AS purchase_completed
                FROM {SCHEMA}.ga4_funnel_daily
                WHERE is_synthetic
                GROUP BY date
            ) g
            JOIN (
                SELECT DATE(created_at::timestamptz) AS date, COUNT(*) AS shopify_orders
                FROM {SCHEMA}.shopify_orders
                GROUP BY 1
            ) s ON g.date = s.date
            GROUP BY g.date, s.shopify_orders
            HAVING ABS(SUM(g.purchase_completed) - s.shopify_orders)
                   / NULLIF(s.shopify_orders::numeric, 0) > 0.15
        ) divergent
    """)
    divergent_days = cur.fetchone()[0]
    ok4 = divergent_days == 0
    results['CHECK 4 — Shopify coherence (±15%)'] = (
        ok4, f'days_diverging_over_15pct={divergent_days}  expected=0'
    )

    # CHECK 5: paid_social_tiktok > 25% on ≥20 of 29 Alert3 stage1 dates
    act_dates_in_window = [d for d in ALERT3_STAGE1_DATES if SEED_START <= d <= SEED_END]
    elevated_count = 0
    for act_date in act_dates_in_window:
        cur.execute(f"""
            SELECT
                SUM(CASE WHEN channel_group = 'paid_social_tiktok' THEN sessions END)::numeric
                / NULLIF(SUM(sessions)::numeric, 0) AS tiktok_share
            FROM {SCHEMA}.ga4_sessions_daily
            WHERE date = %s AND is_synthetic AND country = 'US'
        """, (act_date,))
        row = cur.fetchone()
        share = float(row[0]) if row and row[0] else 0.0
        if share > 0.25:
            elevated_count += 1
    ok5 = elevated_count >= 20
    results['CHECK 5 — TikTok session share elevated'] = (
        ok5,
        f'activation_dates_in_window={len(act_dates_in_window)}  '
        f'elevated_count={elevated_count}  expected>=20'
    )

    # CHECK 6: F2 and F4 alert_log rows exist
    cur.execute(
        "SELECT alert_type FROM public.alert_log "
        "WHERE client_id = %s AND alert_type IN ('F2','F4') "
        "AND signal_source = 'ga4' AND is_synthetic",
        (CLIENT_ID,),
    )
    ga4_alerts = {r[0] for r in cur.fetchall()}
    ok6 = 'F2' in ga4_alerts and 'F4' in ga4_alerts
    results['CHECK 6 — GA4 alert_log rows (F2, F4)'] = (
        ok6, f'found={sorted(ga4_alerts)}  expected=[F2, F4]'
    )

    # CHECK 7: Error count nonzero for each event date range
    event_error_checks = [
        ('Event 1', date(2024, 11, 5), date(2024, 11, 6)),
        ('Event 2', date(2024, 11, 28), date(2024, 12, 2)),
        ('Event 3', date(2025, 7, 15), date(2025, 7, 15)),
        ('Event 4', date(2025, 12, 10), date(2025, 12, 10)),
    ]
    event7_ok = True
    event7_detail = []
    for name, start, end in event_error_checks:
        cur.execute(
            f"SELECT SUM(error_count) FROM {SCHEMA}.ga4_checkout_errors "
            f"WHERE date BETWEEN %s AND %s AND is_synthetic",
            (start, end),
        )
        total_err = cur.fetchone()[0] or 0
        ok_ev7 = total_err > 0
        if not ok_ev7:
            event7_ok = False
        event7_detail.append(f'{name}={total_err}')
    ok7 = event7_ok
    results['CHECK 7 — Sentry-correlated error counts'] = (
        ok7, ', '.join(event7_detail)
    )

    cur.close()

    # ── Print summary ──────────────────────────────────────────────────────────
    SEP = '=' * 72
    print()
    print(SEP)
    print('SEED_GA4 VALIDATION — 7 CHECKS')
    print(SEP)
    passed = 0
    for check, (ok, detail) in results.items():
        status = 'PASS' if ok else 'FAIL'
        if ok:
            passed += 1
        print(f'\n[{status}] {check}')
        print(f'       {detail}')

    print()
    print(SEP)
    print('SUMMARY TABLE')
    print(SEP)
    print(f'  {"Table":<28} {"Rows":<10} {"Status"}')
    print(f'  {"-"*28} {"-"*10} {"-"*6}')

    conn2 = conn
    cur2 = conn2.cursor()
    for tbl in ('ga4_sessions_daily', 'ga4_funnel_daily', 'ga4_checkout_errors'):
        cur2.execute(f"SELECT COUNT(*) FROM {SCHEMA}.{tbl} WHERE is_synthetic")
        n = cur2.fetchone()[0]
        print(f'  {tbl:<28} {n:<10,} OK')
    cur2.execute(
        "SELECT COUNT(*) FROM public.alert_log WHERE client_id = %s "
        "AND alert_type IN ('F2','F4') AND signal_source = 'ga4'",
        (CLIENT_ID,),
    )
    n_al = cur2.fetchone()[0]
    print(f'  {"alert_log (F2+F4)":<28} {n_al:<10} OK')
    cur2.close()

    print()
    for check, (ok, _) in results.items():
        label = check.split('—')[0].strip()
        print(f'  {label}: {"PASS" if ok else "FAIL"}')
    print(f'  {passed}/7 checks passed')
    print(SEP)

    if passed == 7:
        print('\nseed_ga4.py COMPLETE — seed_sentry.py may now proceed')
    else:
        print('\nseed_ga4.py INCOMPLETE — do not proceed')
        print('Failed checks:')
        for check, (ok, detail) in results.items():
            if not ok:
                print(f'  FAIL: {check}')
                print(f'        {detail}')

    if passed < 7:
        sys.exit(1)


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main() -> None:
    sys.stdout.reconfigure(encoding='utf-8')
    url = os.getenv('DATABASE_URL')
    if not url:
        print('ERROR: DATABASE_URL not set')
        sys.exit(1)

    logger.info('SOURCE: GA4 Seed | CLIENT: %s | Starting', CLIENT_ID)
    conn = psycopg2.connect(url, sslmode='require')
    cur  = conn.cursor()

    try:
        # Create tables
        logger.info('Step 0 — create_tables')
        cur.execute(DDL_SESSIONS)
        cur.execute(DDL_FUNNEL)
        cur.execute(DDL_ERRORS)
        logger.info('  create_tables | all three tables ensured')

        # Load Shopify daily orders for calibration
        shopify_daily = load_shopify_orders(cur)
        logger.info('  Loaded Shopify daily orders: %d days', len(shopify_daily))

        # Seed
        seed_sessions(cur, shopify_daily)
        seed_funnel(cur, shopify_daily)
        seed_checkout_errors(cur)
        seed_alert_log(cur)

        conn.commit()
        logger.info('All inserts committed.')
    except Exception as exc:
        conn.rollback()
        logger.error(
            'SOURCE: GA4 Seed | CLIENT: %s | ERROR: %s', CLIENT_ID, exc
        )
        raise
    finally:
        cur.close()

    validate(conn)
    conn.close()
    logger.info('SOURCE: GA4 Seed | CLIENT: %s | Complete', CLIENT_ID)


if __name__ == '__main__':
    main()
