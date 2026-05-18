"""
seed_sentry.py — Sentry errors 24 months (2024-06-01 to 2026-05-31)

Tables seeded:
  client_azure_co.sentry_errors_daily

Alert scenarios embedded:
  S8  — Theme update 2024-11-05 to 2024-11-06 (48h theme_render_error spike)
         State 3 full suppression first 48h. State 2 at hour 49 (Safari only).
  S9  — BFCM Y1 Sentry rate limiting 2024-11-28 to 2024-11-29.
         H1 fires instead of F1/F2. F1/F2 fully suppressed.
  S24 — App installation 2025-07-15 (24h third_party_script + checkout_js spike).
         F1, F2, F5 suppressed. suppression_log rows seeded.
  S25 — CDN/hosting event 2025-12-10 hours 10-16.
         H10 fires. Business alerts suppressed.
  F2  — Month 9 payment_gateway_timeout mobile/safari (2025-02-18 to 2025-02-20).
         Evidence layer for GA4 F2 payment_completion_rate drop.

GA4-confirmed spike dates:
  Event 1 (Theme, S8):  2024-11-05 to 2024-11-06
  Event 2 (BFCM, S9):  2024-11-28 to 2024-11-29 (peak hours 8-14)
  Event 3 (App, S24):  2025-07-15
  Event 4 (CDN, S25):  2025-12-10 hours 10,11,13,15,16
  F2 window:           2025-02-18 to 2025-02-20

Build standards applied:
  Fix 1: is_synthetic on raw table (Sentry is manually managed, not Airbyte)
  Fix 2: No airbyte_meta_cols() — Sentry is not Airbyte-managed
  Fix 3: Single transaction, ON CONFLICT DO NOTHING (bare)
  Fix 4: _nearest_pd_corr() defined (Sentry uses independent draws — no Cholesky needed)
  Fix 5: GENERATED ALWAYS id — never inserted explicitly
  Fix 6: CREATE TABLE IF NOT EXISTS before all inserts
  Fix 7: Named UNIQUE constraint declared and checked before insert
  Fix 8: numpy float64/int64 → float()/int() before psycopg2
"""

import os
import sys
import json
import random
import logging
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

SEED_RNG = np.random.default_rng(42)
PY_RNG   = random.Random(42)

# ─── GA4-CONFIRMED SPIKE EVENT DATES ─────────────────────────────────────────

EVENT1_START = date(2024, 11, 5)
EVENT1_END   = date(2024, 11, 6)

EVENT2_DATES      = [date(2024, 11, 28), date(2024, 11, 29)]
EVENT2_PEAK_HOURS = list(range(8, 15))   # 8am–2pm EST inclusive

EVENT3_DATE  = date(2025, 7, 15)
EVENT4_DATE  = date(2025, 12, 10)
EVENT4_HOURS = [10, 11, 13, 15, 16]     # from GA4 checkout_errors data

F2_DATES = [date(2025, 2, 18), date(2025, 2, 19), date(2025, 2, 20)]

# ─── RELEASE VERSIONS (8-12 deploys across 24 months) ────────────────────────

_RELEASES = [
    (date(2024,  6,  1), 'v1.0.0'),
    (date(2024,  7, 15), 'v1.1.0'),
    (date(2024,  8, 20), 'v1.2.0'),
    (date(2024, 10,  1), 'v1.3.0'),
    (date(2024, 11,  5), 'v1.4.0'),   # theme update event — must coincide
    (date(2025,  1, 15), 'v1.5.0'),
    (date(2025,  3,  1), 'v1.6.0'),
    (date(2025,  5,  1), 'v1.7.0'),
    (date(2025,  7, 15), 'v1.8.0'),   # app installation event — must coincide
    (date(2025,  9,  1), 'v1.9.0'),
    (date(2025, 11,  1), 'v2.0.0'),
    (date(2026,  1, 15), 'v2.1.0'),
    (date(2026,  3,  1), 'v2.2.0'),
]


def _release(d: date, nullable: bool = True) -> str | None:
    """Active release version for date d. 20% null rate for background (DQ issue 5)."""
    if nullable and PY_RNG.random() < 0.20:
        return None
    ver = _RELEASES[0][1]
    for rel_date, rel_ver in _RELEASES:
        if d >= rel_date:
            ver = rel_ver
        else:
            break
    return ver


# ─── BACKGROUND ERROR RATES ───────────────────────────────────────────────────

_RATES = {
    'checkout_js_error':          (2, 6),
    'payment_gateway_timeout':    (1, 4),
    'cart_api_failure':           (1, 3),
    'inventory_sync_error':       (0, 2),
    'theme_render_error':         (0, 2),
    'third_party_script_timeout': (2, 8),
}

_BROWSERS = ['chrome', 'safari', 'firefox', 'samsung_internet']
_BWEIGHTS  = [0.55, 0.25, 0.15, 0.05]

_DEVICES  = ['desktop', 'mobile', 'tablet']
_DWEIGHTS  = [0.45, 0.45, 0.10]

_URLS     = ['/checkout', '/cart', '/products/*']
_UWEIGHTS  = [0.45, 0.30, 0.25]

# Weighted toward 8am-10pm; near-zero overnight
_HWEIGHTS = ([0.1] * 8) + [2, 3, 5, 6, 7, 8, 8, 8, 8, 8, 8, 7, 5, 4, 3, 2]


def _browser():  return PY_RNG.choices(_BROWSERS, weights=_BWEIGHTS)[0]
def _device():   return PY_RNG.choices(_DEVICES,  weights=_DWEIGHTS)[0]
def _url():      return PY_RNG.choices(_URLS,     weights=_UWEIGHTS)[0]
def _hour():     return PY_RNG.choices(range(24), weights=_HWEIGHTS)[0]


def _mobile_mult(etype: str, device: str) -> float:
    """Mobile 1.4x for checkout_js_error and theme_render_error."""
    return 1.4 if device == 'mobile' and etype in (
        'checkout_js_error', 'theme_render_error') else 1.0


def _safari_mult(etype: str, browser: str) -> float:
    """Safari 1.3x for theme_render_error (CSS rendering differences)."""
    return 1.3 if browser == 'safari' and etype == 'theme_render_error' else 1.0


# ─── FIX 4: NEAREST POSITIVE-DEFINITE CORRECTION (Fix 4 compliance) ──────────

def _nearest_pd_corr(m: np.ndarray, eps: float = 1e-4) -> np.ndarray:
    """Project m onto nearest positive-definite correlation matrix (Higham 2002).
    Required before np.linalg.cholesky() to prevent LinAlgError.
    Sentry uses independent draws so Cholesky is not called here, but the
    function is defined per Fix 4 standard.
    """
    B = (m + m.T) / 2
    _, s, Vt = np.linalg.svd(B)
    H = Vt.T @ np.diag(s) @ Vt
    B2 = (B + H) / 2
    B3 = (B2 + B2.T) / 2
    n = B3.shape[0]
    np.fill_diagonal(B3, 1.0)
    ev = np.linalg.eigvalsh(B3)
    if ev.min() > 0:
        return B3
    B3 += np.eye(n) * (eps - ev.min())
    scale = np.sqrt(np.diag(B3))
    return B3 / np.outer(scale, scale)


# ─── SPIKE DATE GUARD ─────────────────────────────────────────────────────────

def _is_spike(d: date, etype: str) -> bool:
    """True when background generation should skip this (date, error_type) pair."""
    if d in (EVENT1_START, EVENT1_END) and etype == 'theme_render_error':
        return True
    if d in EVENT2_DATES and etype in ('cart_api_failure', 'inventory_sync_error'):
        return True
    if d == EVENT3_DATE and etype in ('third_party_script_timeout', 'checkout_js_error'):
        return True
    if d == EVENT4_DATE and etype in ('theme_render_error', 'checkout_js_error'):
        return True
    if d in F2_DATES and etype == 'payment_gateway_timeout':
        return True
    return False


# ─── ROW TUPLE FORMAT ─────────────────────────────────────────────────────────
# Matches INSERT column order:
# (date, hour, error_type, environment, release_version,
#  error_count, affected_users, p50_duration_ms, p95_duration_ms,
#  browser, device_category, url_path, resolved, is_synthetic)

def _mk_row(d, hour, etype, release, count, browser, device, url,
            resolved, p50_base=1100):
    """Build a row tuple with Fix 8 casts applied."""
    p50 = float(SEED_RNG.normal(p50_base, p50_base * 0.18))
    p50 = max(150.0, p50)
    p95 = float(p50 * SEED_RNG.uniform(1.8, 3.2))
    aff = max(1, int(count * float(SEED_RNG.uniform(0.55, 0.90))))
    return (
        d,
        int(hour),
        etype,
        'production',
        release,
        int(count),
        int(aff),
        round(p50, 2),
        round(p95, 2),
        browser,
        device,
        url,
        bool(resolved),
        True,   # is_synthetic
    )


# ─── GENERATORS ───────────────────────────────────────────────────────────────

def build_background() -> list:
    rows = []
    d = SEED_START
    while d <= SEED_END:
        for etype, (lo, hi) in _RATES.items():
            if _is_spike(d, etype):
                continue
            daily_total = PY_RNG.randint(lo, hi)
            if daily_total == 0:
                continue
            n_rows = PY_RNG.randint(1, min(3, daily_total))
            # Distribute daily_total across n_rows buckets
            buckets = [1] * n_rows
            for _ in range(daily_total - n_rows):
                buckets[PY_RNG.randrange(n_rows)] += 1
            for cnt in buckets:
                br  = _browser()
                dev = _device()
                url = _url()
                cnt = max(1, int(cnt
                               * _mobile_mult(etype, dev)
                               * _safari_mult(etype, br)))
                rows.append(_mk_row(
                    d, _hour(), etype, _release(d),
                    cnt, br, dev, url,
                    resolved=True, p50_base=1100,
                ))
        d += timedelta(days=1)
    return rows


def build_event1() -> list:
    """S8 — theme update 2024-11-05 to 2024-11-06 (48h), theme_render_error."""
    rows = []
    # Day 1 (hours 0-23): both Safari and Chrome affected
    # Day 2 (hours 0-23, i.e. event hours 24-47): Safari only
    plan = [
        (EVENT1_START, ['safari', 'chrome']),
        (EVENT1_END,   ['safari']),
    ]
    for d, browsers in plan:
        urls    = ['/checkout', '/products/*']
        devices = _DEVICES
        n_combos = len(browsers) * len(devices) * len(urls)
        for hour in range(24):
            target = PY_RNG.randint(180, 240)
            base   = max(5, target // n_combos)
            for br in browsers:
                for dev in devices:
                    for url in urls:
                        cnt = int(base
                                  * _mobile_mult('theme_render_error', dev)
                                  * _safari_mult('theme_render_error', br))
                        cnt = max(4, cnt)
                        rows.append(_mk_row(
                            d, hour, 'theme_render_error', 'v1.4.0',
                            cnt, br, dev, url,
                            resolved=False,   # unresolved during 48h window
                            p50_base=2800,
                        ))
    return rows


def build_event2() -> list:
    """S9 — BFCM Y1 2024-11-28 to 2024-11-29. cart_api_failure + inventory_sync_error."""
    rows = []
    # Mobile 72%, desktop 18%, tablet 10%
    # /checkout 90%, /cart 10%
    # One fixed browser per device category for uniqueness
    dev_cfg = [
        ('mobile',  'samsung_internet', 0.72),
        ('desktop', 'chrome',           0.18),
        ('tablet',  'safari',           0.10),
    ]
    url_cfg = [('/checkout', 0.90), ('/cart', 0.10)]
    for d in EVENT2_DATES:
        for hour in EVENT2_PEAK_HOURS:
            target = PY_RNG.randint(400, 600)
            for etype in ['cart_api_failure', 'inventory_sync_error']:
                for dev, br, dshare in dev_cfg:
                    for url, ushare in url_cfg:
                        cnt = max(3, int(target * dshare * ushare / 2))
                        rows.append(_mk_row(
                            d, hour, etype, _release(d, nullable=False),
                            cnt, br, dev, url,
                            resolved=True,   # resolved within 6h of BFCM end
                            p50_base=3200,
                        ))
    return rows


def build_event3() -> list:
    """S24 — app installation 2025-07-15, 24h. third_party_script_timeout + checkout_js_error."""
    rows = []
    for hour in range(24):
        target   = PY_RNG.randint(80, 120)
        n_combos = 2 * len(_BROWSERS) * len(_DEVICES)   # 2 types × 4 browsers × 3 devices
        base     = max(2, target // n_combos)
        for etype in ['third_party_script_timeout', 'checkout_js_error']:
            for br in _BROWSERS:
                for dev in _DEVICES:
                    cnt = base + PY_RNG.randint(-1, 1)
                    cnt = max(1, cnt)
                    rows.append(_mk_row(
                        EVENT3_DATE, hour, etype, 'v1.8.0',
                        cnt, br, dev, '/checkout',
                        resolved=True,   # resolved at end of 24h window
                        p50_base=2000,
                    ))
    return rows


def build_event4() -> list:
    """S25 — CDN event 2025-12-10 hours 10,11,13,15,16. theme_render_error + checkout_js_error."""
    rows = []
    urls     = ['/checkout', '/cart', '/products/*']
    n_combos = 2 * len(_BROWSERS) * len(_DEVICES) * len(urls)   # 72
    for hour in EVENT4_HOURS:
        target = PY_RNG.randint(300, 500)
        base   = max(3, target // n_combos)
        for etype in ['theme_render_error', 'checkout_js_error']:
            for br in _BROWSERS:
                for dev in _DEVICES:
                    for url in urls:
                        cnt = base + PY_RNG.randint(0, 3)
                        cnt = max(1, cnt)
                        rows.append(_mk_row(
                            EVENT4_DATE, hour, etype,
                            _release(EVENT4_DATE, nullable=False),
                            cnt, br, dev, url,
                            resolved=True,
                            p50_base=4000,
                        ))
    return rows


def build_f2() -> list:
    """Month 9 F2 — payment_gateway_timeout, mobile Safari, 3 days 60-90/hr."""
    rows = []
    for d in F2_DATES:
        for hour in range(8, 24):   # 16 business hours
            cnt = PY_RNG.randint(60, 90)
            rows.append(_mk_row(
                d, hour, 'payment_gateway_timeout',
                _release(d, nullable=False),
                cnt, 'safari', 'mobile', '/checkout',
                resolved=True,   # resolved at end of 3-day window
                p50_base=5500,
            ))
    return rows


# ─── DEDUPLICATION ────────────────────────────────────────────────────────────

def _dedup(rows: list) -> list:
    """Keep first occurrence per natural key. Spikes prepended → they win."""
    seen: dict = {}
    for row in rows:
        # Natural key matches UNIQUE constraint: (date, hour, error_type, browser, device, url)
        key = (row[0], row[1], row[2], row[9], row[10], row[11])
        if key not in seen:
            seen[key] = row
    return list(seen.values())


# ─── INSERT SQL ───────────────────────────────────────────────────────────────

_INSERT = f"""
INSERT INTO {SCHEMA}.sentry_errors_daily
    (date, hour, error_type, environment, release_version,
     error_count, affected_users, p50_duration_ms, p95_duration_ms,
     browser, device_category, url_path, resolved, is_synthetic)
VALUES %s
ON CONFLICT DO NOTHING
"""


# ─── ALERT LOG / SUPPRESSION LOG ─────────────────────────────────────────────

def _insert_alert_log(cur):
    """Seed 3 alert_log rows from Sentry scenarios (F1 State2, H1, H10)."""

    # Event 1 S8: State 2 fires at hour 49 (2024-11-07 01:00 UTC)
    cur.execute("""
        INSERT INTO public.alert_log
            (client_id, alert_type, signal_source, confidence_score,
             fired_at, suppressed, suppression_category, suppression_type,
             layer1_headline, layer2_context, should_fire, is_synthetic)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        CLIENT_ID, 'F1', 'sentry', 0.71,
        datetime(2024, 11, 7, 1, 0, tzinfo=timezone.utc),
        False,   # State 2 = fires
        'S8', 'theme_update_browser_specific',
        'Checkout errors persisting on Safari only after theme update cleared Chrome',
        ('Theme update v1.4.0 deployed 2024-11-05. Errors cleared for Chrome at hour 48 '
         'but persist on Safari only — browser-specific CSS rendering issue confirmed. '
         'Test checkout flow on Safari specifically. Confidence reduced 0.85→0.71 (S8 '
         'State 2 partial suppression: theme update partially explains signal).'),
        True, True,
    ))

    # Event 2 S9: H1 fires during BFCM (Sentry rate-limiting DQ alert)
    cur.execute("""
        INSERT INTO public.alert_log
            (client_id, alert_type, signal_source, confidence_score,
             fired_at, suppressed, suppression_category,
             layer1_headline, layer2_context, evidence_stack_json,
             should_fire, is_synthetic)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        CLIENT_ID, 'H1', 'sentry', 0.95,
        datetime(2024, 11, 28, 10, 0, tzinfo=timezone.utc),
        False,   # H1 fires instead of F1/F2
        'S9',
        'Sentry rate limiting during BFCM — checkout signals unreliable',
        ('Sentry error volume 400–600/hr on cart_api_failure and inventory_sync_error '
         'during BFCM peak hours (est. 30–40% underreporting due to S9 rate limiting). '
         'F1 and F2 suppressed — use Shopify order completion rate as ground truth.'),
        json.dumps({'layer_1': (
            'Sentry error volume 400–600/hr across cart_api_failure and '
            'inventory_sync_error on 2024-11-28 to 2024-11-29 (BFCM peak hours '
            '8am–2pm EST). Mobile dominant (72% affected_users). Volume pattern '
            'consistent with Sentry rate limiting (S9) — est. 30–40% underreporting. '
            'F1/F2 checkout alerts suppressed (State 4 — DQ score triggers H-series).'
        )}),
        True, True,
    ))

    # Event 4 S25: H10 fires for CDN/hosting infrastructure event
    cur.execute("""
        INSERT INTO public.alert_log
            (client_id, alert_type, signal_source, confidence_score,
             fired_at, suppressed, suppression_category,
             layer1_headline, layer2_context, evidence_stack_json,
             should_fire, is_synthetic)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        CLIENT_ID, 'H10', 'sentry', 0.93,
        datetime(2025, 12, 10, 10, 0, tzinfo=timezone.utc),
        False,   # H10 fires
        'S25',
        'CDN/hosting infrastructure event — Sentry spike uniform across all browsers and paths',
        ('Sentry errors 300–500/hr spiking uniformly across Chrome, Safari, Firefox, '
         'Samsung Internet on /checkout, /cart, /products/* simultaneously on '
         '2025-12-10 hours 10–16. Uniform cross-browser cross-path spike = '
         'infrastructure event not application error. Check Shopify Status page and CDN provider.'),
        json.dumps({'layer_1': (
            'Sentry error spike 300–500/hr across all browsers (Chrome, Safari, Firefox, '
            'Samsung Internet) and all paths (/checkout, /cart, /products/*) '
            'simultaneously on 2025-12-10 hours 10–16. theme_render_error and '
            'checkout_js_error both elevated. Simultaneous cross-browser cross-path '
            'spike = CDN or hosting infrastructure event, not application error (S25). '
            'H10 fires. Business alerts F1, F2, F5 suppressed.'
        )}),
        True, True,
    ))

    logger.info('Inserted 3 alert_log rows (F1/S8 State2, H1/S9, H10/S25)')


def _insert_suppression_log(cur):
    """Seed suppression_log for Event 3 S24 (app installation — F1, F2, F5 suppressed)."""
    for alert_type in ['F1', 'F2', 'F5']:
        cur.execute("""
            INSERT INTO public.suppression_log
                (client_id, signal_detected_at, alert_type,
                 signal_value, threshold_value,
                 suppression_reason, suppression_category, suppression_state,
                 variance_explained_pct, residual_signal,
                 suppression_source, would_have_fired_at,
                 founder_queryable,
                 detected_signal_description, threshold_context,
                 suppression_explanation, residual_signal_description,
                 founder_verification_action)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            CLIENT_ID,
            datetime(2025, 7, 15, 0, 0, tzinfo=timezone.utc),
            alert_type,
            100.0,   # signal_value: errors/hr
            20.0,    # threshold_value: errors/hr that would trigger alert
            'shopify_app_installation',
            'S24',
            3,       # State 3: full suppression
            100.0,
            0.0,     # fully explained, no residual
            'brand_event_calendar:app_installation_2025-07-15:release_v1.8.0',
            datetime(2025, 7, 15, 1, 0, tzinfo=timezone.utc),
            True,
            ('third_party_script_timeout and checkout_js_error spiked 80–120/hr on '
             '2025-07-15 across all browsers (Chrome, Safari, Firefox, Samsung Internet) '
             'uniformly — script-level not rendering-level'),
            (f'{alert_type} threshold crossed: checkout error rate elevated uniformly '
             'across all browsers on 2025-07-15 for 24 hours'),
            ('Shopify app installation on 2025-07-15 (release v1.8.0 deployment) '
             'explains script timeout errors across all browsers. S24: 24-hour '
             'suppression window post-app-change. F1, F2, F5 suppressed.'),
            None,    # residual_signal_description: fully explained
            ('Check Shopify app install logs for 2025-07-15. Errors should resolve '
             'within 24h without action. If errors persist past 2025-07-16 00:00, '
             'review app compatibility with current theme version v1.8.0.'),
        ))
    logger.info('Inserted 3 suppression_log rows (S24 app installation — F1, F2, F5)')


# ─── VALIDATION CHECKS ────────────────────────────────────────────────────────

def run_checks(cur) -> list:
    results = []

    # Check 1: Total row count nonzero
    cur.execute(f"SELECT COUNT(*) FROM {SCHEMA}.sentry_errors_daily")
    total = cur.fetchone()[0]
    results.append(('Check 1', 'PASS' if total > 0 else 'FAIL',
                    f'Total rows: {total:,}'))

    # Check 2: Background noise >90% of all rows have error_count 0-15
    cur.execute(f"""
        SELECT
            COUNT(*) FILTER (WHERE error_count BETWEEN 0 AND 15) AS bg,
            COUNT(*) AS tot
        FROM {SCHEMA}.sentry_errors_daily
    """)
    bg, tot = cur.fetchone()
    pct = bg / tot * 100 if tot else 0
    results.append(('Check 2', 'PASS' if pct > 90 else 'FAIL',
                    f'Rows error_count 0-15: {bg:,}/{tot:,} = {pct:.1f}%'))

    # Check 3: Event 1 coherence — Safari-only rows exist on day 2; Chrome on day 1 only
    cur.execute(f"""
        SELECT
            COUNT(*) FILTER (
                WHERE date = '{EVENT1_END}' AND browser = 'chrome'
                AND error_type = 'theme_render_error') AS chrome_day2,
            COUNT(*) FILTER (
                WHERE date = '{EVENT1_START}' AND browser = 'chrome'
                AND error_type = 'theme_render_error') AS chrome_day1,
            COUNT(*) FILTER (
                WHERE date = '{EVENT1_END}' AND browser = 'safari'
                AND error_type = 'theme_render_error') AS safari_day2
        FROM {SCHEMA}.sentry_errors_daily
    """)
    cd2, cd1, sd2 = cur.fetchone()
    ok3 = cd2 == 0 and cd1 > 0 and sd2 > 0
    results.append(('Check 3', 'PASS' if ok3 else 'FAIL',
                    f'Event1: chrome_day1={cd1} chrome_day2={cd2} safari_day2={sd2}'))

    # Check 4: BFCM spike — both error types present; mobile >70% of affected_users
    cur.execute(f"""
        SELECT
            COUNT(*) FILTER (WHERE error_type='cart_api_failure')     AS cart,
            COUNT(*) FILTER (WHERE error_type='inventory_sync_error') AS inv,
            SUM(affected_users) FILTER (WHERE device_category='mobile') AS mob_aff,
            SUM(affected_users)                                          AS tot_aff
        FROM {SCHEMA}.sentry_errors_daily
        WHERE date IN ('{EVENT2_DATES[0]}','{EVENT2_DATES[1]}')
          AND error_type IN ('cart_api_failure','inventory_sync_error')
    """)
    cart, inv, mob_aff, tot_aff = cur.fetchone()
    mob_pct = (mob_aff or 0) / (tot_aff or 1) * 100
    ok4 = cart > 0 and inv > 0 and mob_pct > 70
    results.append(('Check 4', 'PASS' if ok4 else 'FAIL',
                    f'BFCM: cart={cart} inv={inv} mobile_affected={mob_pct:.1f}%'))

    # Check 5: Month 9 F2 — payment_gateway_timeout on mobile/safari/checkout, all 3 days
    cur.execute(f"""
        SELECT COUNT(DISTINCT date) FROM {SCHEMA}.sentry_errors_daily
        WHERE date IN ('{F2_DATES[0]}','{F2_DATES[1]}','{F2_DATES[2]}')
          AND error_type = 'payment_gateway_timeout'
          AND device_category = 'mobile'
          AND browser = 'safari'
          AND url_path = '/checkout'
    """)
    f2_days = cur.fetchone()[0]
    results.append(('Check 5', 'PASS' if f2_days == 3 else 'FAIL',
                    f'F2 payment_gateway_timeout mobile/safari/checkout: {f2_days}/3 days'))

    # Check 6: Alert log — H1, H10, F1/S8 exist; no F1/F2 for BFCM or app-install dates
    cur.execute("""
        SELECT
            COUNT(*) FILTER (WHERE alert_type='H1'  AND signal_source='sentry') AS h1,
            COUNT(*) FILTER (WHERE alert_type='H10' AND signal_source='sentry') AS h10,
            COUNT(*) FILTER (
                WHERE alert_type='F1' AND signal_source='sentry'
                AND suppression_type='theme_update_browser_specific') AS f1_s8
        FROM public.alert_log
        WHERE client_id=%s AND is_synthetic=true
    """, (CLIENT_ID,))
    h1, h10, f1_s8 = cur.fetchone()

    cur.execute("""
        SELECT COUNT(*) FROM public.alert_log
        WHERE client_id=%s AND is_synthetic=true
          AND alert_type IN ('F1','F2')
          AND fired_at::date IN (%s,%s,%s)
          AND (suppression_type IS NULL
               OR suppression_type != 'theme_update_browser_specific')
    """, (CLIENT_ID,
          str(EVENT2_DATES[0]), str(EVENT2_DATES[1]), str(EVENT3_DATE)))
    bad = cur.fetchone()[0]

    ok6 = h1 >= 1 and h10 >= 1 and f1_s8 >= 1 and bad == 0
    results.append(('Check 6', 'PASS' if ok6 else 'FAIL',
                    f'H1={h1} H10={h10} F1_S8={f1_s8} unwanted_F1F2={bad}'))

    # Check 7: resolved flag — Event 1 rows unresolved during window; others resolved
    cur.execute(f"""
        SELECT
            COUNT(*) FILTER (
                WHERE date IN ('{EVENT1_START}','{EVENT1_END}')
                AND error_type='theme_render_error' AND resolved=false) AS e1_unres,
            COUNT(*) FILTER (
                WHERE date IN ('{EVENT2_DATES[0]}','{EVENT2_DATES[1]}')
                AND error_type IN ('cart_api_failure','inventory_sync_error')
                AND resolved=true) AS e2_res,
            COUNT(*) FILTER (WHERE date='{EVENT3_DATE}' AND resolved=true) AS e3_res,
            COUNT(*) FILTER (WHERE date='{EVENT4_DATE}' AND resolved=true) AS e4_res
        FROM {SCHEMA}.sentry_errors_daily
    """)
    e1u, e2r, e3r, e4r = cur.fetchone()
    ok7 = e1u > 0 and e2r > 0 and e3r > 0 and e4r > 0
    results.append(('Check 7', 'PASS' if ok7 else 'FAIL',
                    f'Event1_unresolved={e1u} Event2_res={e2r} Event3_res={e3r} Event4_res={e4r}'))

    return results, total


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.error('DATABASE_URL not set')
        sys.exit(1)

    logger.info('Connecting...')
    conn = psycopg2.connect(db_url)
    conn.autocommit = False

    try:
        cur = conn.cursor()

        # Fix 6: CREATE TABLE IF NOT EXISTS
        logger.info('Creating sentry_errors_daily if not exists...')
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {SCHEMA}.sentry_errors_daily (
                id                    bigint generated always as identity primary key,
                date                  date not null,
                hour                  integer,
                error_type            text not null,
                environment           text default 'production',
                release_version       text,
                error_count           integer not null,
                affected_users        integer,
                p50_duration_ms       numeric,
                p95_duration_ms       numeric,
                browser               text,
                device_category       text,
                url_path              text,
                resolved              boolean default false,
                is_synthetic          boolean default true,
                _airbyte_extracted_at timestamptz default now(),
                CONSTRAINT sentry_err_natural_key
                    UNIQUE (date, hour, error_type, browser, device_category, url_path)
            )
        """)

        # Fix 7: Ensure constraint exists if table pre-existed without it
        cur.execute(f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conrelid = '{SCHEMA}.sentry_errors_daily'::regclass
                      AND conname  = 'sentry_err_natural_key'
                ) THEN
                    ALTER TABLE {SCHEMA}.sentry_errors_daily
                    ADD CONSTRAINT sentry_err_natural_key
                    UNIQUE (date, hour, error_type, browser, device_category, url_path);
                END IF;
            END$$;
        """)
        conn.commit()
        logger.info('Table and constraint ready.')

        # Build rows — spikes first so dedup keeps spike values on key clash
        logger.info('Generating spike rows...')
        spike_rows = (build_event1() + build_event2() +
                      build_event3() + build_event4() + build_f2())
        logger.info('Spike rows: %d', len(spike_rows))

        logger.info('Generating background rows...')
        bg_rows = build_background()
        logger.info('Background rows (pre-dedup): %d', len(bg_rows))

        all_rows = _dedup(spike_rows + bg_rows)
        logger.info('Total rows after dedup: %d', len(all_rows))

        # Fix 3: Single transaction, ON CONFLICT DO NOTHING (bare)
        logger.info('Inserting into sentry_errors_daily...')
        psycopg2.extras.execute_values(cur, _INSERT, all_rows, page_size=500)
        logger.info('Insert complete.')

        _insert_alert_log(cur)
        _insert_suppression_log(cur)

        conn.commit()
        logger.info('Transaction committed.')

        # ── Validation ────────────────────────────────────────────────────────
        results, total = run_checks(cur)

        print('\n' + '=' * 60)
        print('VALIDATION — seed_sentry.py')
        print('=' * 60)
        print(f'\n{"Table":<40} {"Rows":>10}  Status')
        print('-' * 56)
        print(f'{SCHEMA}.sentry_errors_daily{"":<12} {total:>10,}  {"OK" if total > 0 else "EMPTY"}')

        print(f'\n{"Check":<10} {"Result":<8}  Details')
        print('-' * 70)
        all_pass = True
        for name, status, detail in results:
            print(f'{name:<10} {status:<8}  {detail}')
            if status != 'PASS':
                all_pass = False

        print()
        if all_pass:
            print('seed_sentry.py COMPLETE — patch_script_final.py '
                  '(Patches 1, 2, 3) may now proceed')
        else:
            fails = [r for r in results if r[1] != 'PASS']
            print('seed_sentry.py INCOMPLETE — do not proceed')
            print(f'\nFailed ({len(fails)}):')
            for name, _, detail in fails:
                print(f'  {name}: {detail}')

        cur.close()

    except Exception as exc:
        conn.rollback()
        logger.error(
            'SOURCE: seed_sentry.py | CLIENT: %s | ERROR: %s',
            CLIENT_ID, str(exc),
        )
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    main()
