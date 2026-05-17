"""
patch_script.py — Pre-GA4 database patches (Patches 4, 5, 6)

Patch 4: Fix meta_ad_performance — attribution_setting values and
         stored_before_retention_limit flag.

Patch 5: CREATE + populate public.influencer_profile from 29 Alert3
         activations (15 distinct TikTok creators).

Patch 6: CREATE + populate public.founder_preference_profile with
         43 skeleton rows (all-zero counts) for Agent C first-run.
"""

import os, sys, json, re, logging
from datetime import date, datetime, timezone
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)

CLIENT_ID          = 'azure_co'
TODAY              = date(2026, 5, 17)
RETENTION_CUTOFF   = date(2026, 4, 17)   # 13 months before TODAY
ATTRIBUTION_BREAK  = date(2026, 1, 12)   # Meta attribution window change

# ─── CREATOR MAP ─────────────────────────────────────────────────────────────
# 29 INF campaign IDs → (creator_id, tier, follower_count, primary_category)
# 15 distinct creators: 10 micro, 3 mid, 2 macro
CAMPAIGN_CREATOR_MAP = {
    # micro (10 creators, 19 campaigns)
    'INF-2024-JUN-01':       ('CR-MICRO-001', 'micro',   50_000, 'dresses'),
    'INF-2025-JUN-01':       ('CR-MICRO-001', 'micro',   50_000, 'dresses'),
    'INF-2024-JUL-01':       ('CR-MICRO-002', 'micro',   75_000, 'knitwear'),
    'INF-2025-JUL-01':       ('CR-MICRO-002', 'micro',   75_000, 'knitwear'),
    'INF-2024-FEB-01':       ('CR-MICRO-003', 'micro',   45_000, 'dresses'),
    'INF-2025-NOV-02':       ('CR-MICRO-003', 'micro',   45_000, 'dresses'),
    'INF-2024-AUG-01':       ('CR-MICRO-004', 'micro',   60_000, 'dresses'),
    'INF-2025-AUG-01':       ('CR-MICRO-004', 'micro',   60_000, 'dresses'),
    'INF-2024-SEP-01':       ('CR-MICRO-005', 'micro',   55_000, 'tops'),
    'INF-2025-SEP-02':       ('CR-MICRO-005', 'micro',   55_000, 'tops'),
    'INF-2024-FEB-FRAUD-01': ('CR-MICRO-006', 'micro',   35_000, 'dresses'),
    'INF-2024-JUL-02':       ('CR-MICRO-007', 'micro',   65_000, 'tops'),
    'INF-2025-DEC-01':       ('CR-MICRO-007', 'micro',   65_000, 'tops'),
    'INF-2024-NOV-01':       ('CR-MICRO-008', 'micro',   55_000, 'dresses'),
    'INF-2026-APR-01':       ('CR-MICRO-008', 'micro',   55_000, 'dresses'),
    'INF-2025-OCT-01':       ('CR-MICRO-009', 'micro',   70_000, 'tops'),
    'INF-2026-JAN-01':       ('CR-MICRO-009', 'micro',   70_000, 'tops'),
    'INF-2026-MAR-01':       ('CR-MICRO-010', 'micro',   40_000, 'dresses'),
    'INF-2026-APR-02':       ('CR-MICRO-010', 'micro',   40_000, 'dresses'),
    # mid (3 creators, 7 campaigns)
    'INF-2024-JAN-02':       ('CR-MID-001',   'mid',    200_000, 'dresses'),
    'INF-2024-OCT-01':       ('CR-MID-001',   'mid',    200_000, 'knitwear'),
    'INF-2025-SEP-01':       ('CR-MID-001',   'mid',    200_000, 'knitwear'),
    'INF-2024-MAY-01':       ('CR-MID-002',   'mid',    300_000, 'dresses'),
    'INF-2025-OCT-02':       ('CR-MID-002',   'mid',    300_000, 'dresses'),
    'INF-2026-FEB-01':       ('CR-MID-002',   'mid',    300_000, 'knitwear'),
    'INF-2026-MAY-01':       ('CR-MID-003',   'mid',    250_000, 'dresses'),
    # macro (2 creators, 3 campaigns)
    'INF-2024-MAR-02':       ('CR-MACRO-001', 'macro',  750_000, 'knitwear'),
    'INF-2025-NOV-01':       ('CR-MACRO-001', 'macro',  750_000, 'knitwear'),
    'INF-2026-MAR-02':       ('CR-MACRO-002', 'macro', 1_200_000, 'knitwear'),
}
assert len(CAMPAIGN_CREATOR_MAP) == 29

# ─── 43 ALERT TYPES for founder_preference_profile ───────────────────────────
ALERT_TYPES_43 = [
    'A1', 'A2', 'A3', 'A4', 'A5',
    'B1', 'B2', 'B3', 'B4', 'B5', 'B6',
    'C1', 'C2', 'C3', 'C4', 'C5',
    'D1', 'D2', 'D3', 'D4', 'D5',
    'E1', 'E2', 'E3', 'E4', 'E5',
    'F1', 'F2', 'F3', 'F4', 'F5',
    'G1', 'G2',
    'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'H7',
    'B1_tiktok', 'D1_tiktok', 'Alert3',
]
assert len(ALERT_TYPES_43) == 43


# ─── HELPERS ─────────────────────────────────────────────────────────────────

def get_season(d: date) -> str:
    if 3 <= d.month <= 8:
        return f'SS_{d.year}'
    elif d.month >= 9:
        return f'FW_{d.year}'
    else:                       # Jan / Feb
        return f'FW_{d.year - 1}'


def parse_alert3_rows(cur) -> dict:
    """
    Query alert_log for Alert3 stage1 and stage2, join on INF ID,
    return dict keyed by INF ID with campaign financials and dates.
    """
    cur.execute(
        "SELECT fired_at::date, layer1_headline, layer2_context "
        "FROM public.alert_log "
        "WHERE alert_type = 'Alert3_stage1' ORDER BY fired_at"
    )
    stage1 = {}
    for row in cur.fetchall():
        m = re.search(
            r'(INF-[A-Z0-9-]+)\s+\((\w+)/(\w+)\).*?(\d[\d,]+) revenue vs.*?(\d[\d,]+) cost',
            row[1],
        )
        if m:
            inf_id = m.group(1)
            stage1[inf_id] = {
                'tier':         m.group(2),
                'content_type': m.group(3),
                'fee':          int(m.group(5).replace(',', '')),
                'campaign_date': row[0],
            }

    cur.execute(
        "SELECT fired_at::date, layer1_headline, layer2_context "
        "FROM public.alert_log "
        "WHERE alert_type = 'Alert3_stage2' ORDER BY fired_at"
    )
    stage2 = {}
    for row in cur.fetchall():
        m_id  = re.search(r'INF-[A-Z0-9-]+', row[1] or '')
        m_rev = re.search(r'Attributed revenue[^:]+: \$([0-9,]+)', row[2] or '')
        m_ret = re.search(r'Returns: \$([0-9,]+)', row[2] or '')
        if m_id and m_rev and m_ret:
            inf_id = m_id.group(0)
            stage2[inf_id] = {
                'attr_rev': int(m_rev.group(1).replace(',', '')),
                'returns':  int(m_ret.group(1).replace(',', '')),
            }

    campaigns = {}
    for inf_id, s1 in stage1.items():
        s2 = stage2.get(inf_id)
        net_rev = (s2['attr_rev'] - s2['returns']) if s2 else None
        campaigns[inf_id] = {**s1, 'net_rev': net_rev, 'stage2_fired': s2 is not None}
    return campaigns


def build_creator_profiles(campaigns: dict) -> list[dict]:
    """Aggregate per-creator from 29 campaigns → 15 influencer_profile rows."""
    from collections import defaultdict
    creators: dict[str, dict] = {}

    for inf_id, camp in campaigns.items():
        mapping = CAMPAIGN_CREATOR_MAP.get(inf_id)
        if not mapping:
            continue
        cid, tier, followers, primary_cat = mapping
        d = camp['campaign_date']
        fee = camp['fee']
        net = camp['net_rev']
        content = camp['content_type']

        if cid not in creators:
            creators[cid] = {
                'creator_id':               cid,
                'platform':                 'tiktok',
                'follower_count':           followers,
                'follower_tier':            tier,
                'primary_category':         primary_cat,
                'campaign_dates':           [],
                'fees':                     [],
                'net_revs':                 [],
                'roas_per_campaign':        [],
                'season_roas':              defaultdict(list),
                'category_roas':            defaultdict(list),
            }

        c = creators[cid]
        c['campaign_dates'].append(d)
        c['fees'].append(fee)
        if net is not None:
            c['net_revs'].append(net)
            roas = round(net / fee, 2) if fee else 0.0
            c['roas_per_campaign'].append(roas)
            season = get_season(d)
            c['season_roas'][season].append(roas)
            c['category_roas'][primary_cat].append(roas)

    rows = []
    for cid, c in creators.items():
        n_campaigns    = len(c['campaign_dates'])
        first_date     = min(c['campaign_dates'])
        last_date      = max(c['campaign_dates'])
        total_fee      = sum(c['fees'])
        total_net      = sum(c['net_revs'])
        roas_list      = c['roas_per_campaign']
        roas_avg       = round(sum(roas_list) / len(roas_list), 2) if roas_list else None
        lifetime_roi   = round(total_net / total_fee, 2) if total_fee and total_net else None
        decay          = (TODAY - last_date).days > 90
        if n_campaigns >= 3:
            rel_tier = 'ambassador'
        elif n_campaigns == 2:
            rel_tier = 'repeat'
        else:
            rel_tier = 'one-off'

        season_roas = {
            k: round(sum(v) / len(v), 2)
            for k, v in c['season_roas'].items()
        }
        cat_perf = {
            k: round(sum(v) / len(v), 2)
            for k, v in c['category_roas'].items()
        }

        rows.append({
            'client_id':                    CLIENT_ID,
            'creator_id':                   cid,
            'platform':                     'tiktok',
            'follower_count':               c['follower_count'],
            'follower_tier':                c['follower_tier'],
            'campaigns_run':                n_campaigns,
            'first_campaign_date':          first_date,
            'last_campaign_date':           last_date,
            'return_adjusted_roas_avg':     roas_avg,
            'return_adjusted_roas_by_season': json.dumps(season_roas),
            'category_performance':         json.dumps(cat_perf),
            'audience_decay_indicator':     decay,
            'relationship_tier':            rel_tier,
            'total_fee_paid':               float(total_fee),
            'total_net_revenue_attributed': float(total_net),
            'lifetime_return_adjusted_roi': lifetime_roi,
        })

    return rows


# ─── PATCH 4 ─────────────────────────────────────────────────────────────────

def patch4_meta(cur) -> dict:
    """Fix attribution_setting and stored_before_retention_limit."""
    logger.info('Patch 4 — meta_ad_performance fixes')

    cur.execute(
        "UPDATE client_azure_co.meta_ad_performance "
        "SET attribution_setting = 'pre_window_change' "
        "WHERE attribution_setting = '28d_click_7d_view'"
    )
    pre_updated = cur.rowcount
    logger.info('  attribution pre_window_change updated: %d rows', pre_updated)

    cur.execute(
        "UPDATE client_azure_co.meta_ad_performance "
        "SET attribution_setting = 'post_window_change' "
        "WHERE attribution_setting = '7d_click_1d_view'"
    )
    post_updated = cur.rowcount
    logger.info('  attribution post_window_change updated: %d rows', post_updated)

    cur.execute(
        "UPDATE client_azure_co.meta_ad_performance "
        "SET stored_before_retention_limit = TRUE "
        "WHERE date_start::date < %s AND stored_before_retention_limit = FALSE",
        (RETENTION_CUTOFF,),
    )
    retention_updated = cur.rowcount
    logger.info('  stored_before_retention_limit updated: %d rows', retention_updated)

    return {
        'pre_updated':       pre_updated,
        'post_updated':      post_updated,
        'retention_updated': retention_updated,
    }


# ─── PATCH 5 ─────────────────────────────────────────────────────────────────

INFLUENCER_PROFILE_DDL = """
CREATE TABLE IF NOT EXISTS public.influencer_profile (
    id                              bigint generated always as identity primary key,
    client_id                       text not null,
    creator_id                      text not null,
    platform                        text not null,
    follower_count                  integer,
    follower_tier                   text,
    campaigns_run                   integer default 0,
    first_campaign_date             date,
    last_campaign_date              date,
    return_adjusted_roas_avg        numeric,
    return_adjusted_roas_by_season  jsonb,
    category_performance            jsonb,
    audience_decay_indicator        boolean default false,
    relationship_tier               text default 'one-off',
    total_fee_paid                  numeric default 0,
    total_net_revenue_attributed    numeric default 0,
    lifetime_return_adjusted_roi    numeric,
    created_at                      timestamptz default now(),
    updated_at                      timestamptz default now(),
    unique(client_id, creator_id, platform)
);
"""

INFLUENCER_COLS = [
    'client_id', 'creator_id', 'platform',
    'follower_count', 'follower_tier',
    'campaigns_run', 'first_campaign_date', 'last_campaign_date',
    'return_adjusted_roas_avg',
    'return_adjusted_roas_by_season', 'category_performance',
    'audience_decay_indicator', 'relationship_tier',
    'total_fee_paid', 'total_net_revenue_attributed',
    'lifetime_return_adjusted_roi',
]


def patch5_influencer_profile(cur) -> int:
    """CREATE table and INSERT 15 creator rows."""
    logger.info('Patch 5 — influencer_profile')
    cur.execute(INFLUENCER_PROFILE_DDL)
    logger.info('  table ensured')

    campaigns = parse_alert3_rows(cur)
    profiles  = build_creator_profiles(campaigns)

    sql = (
        f"INSERT INTO public.influencer_profile ({', '.join(INFLUENCER_COLS)}) "
        f"VALUES %s ON CONFLICT (client_id, creator_id, platform) DO NOTHING"
    )
    rows = [
        tuple(p[col] for col in INFLUENCER_COLS)
        for p in profiles
    ]
    psycopg2.extras.execute_values(cur, sql, rows)
    inserted = len([p for p in profiles])
    logger.info('  inserted: %d creator rows', inserted)
    return inserted


# ─── PATCH 6 ─────────────────────────────────────────────────────────────────

FOUNDER_PREF_DDL = """
CREATE TABLE IF NOT EXISTS public.founder_preference_profile (
    id                          bigint generated always as identity primary key,
    client_id                   text not null,
    alert_type                  text not null,
    total_fired                 integer default 0,
    approved_count              integer default 0,
    snoozed_count               integer default 0,
    dismissed_count             integer default 0,
    dismissed_correct_count     integer default 0,
    dismissed_incorrect_count   integer default 0,
    capacity_constrained_count  integer default 0,
    avg_response_time_minutes   numeric,
    last_updated                timestamptz default now(),
    unique(client_id, alert_type)
);
"""


def patch6_founder_preference(cur) -> int:
    """CREATE table and INSERT 43 skeleton rows."""
    logger.info('Patch 6 — founder_preference_profile')
    cur.execute(FOUNDER_PREF_DDL)
    logger.info('  table ensured')

    rows = [(CLIENT_ID, at) for at in ALERT_TYPES_43]
    sql  = (
        "INSERT INTO public.founder_preference_profile (client_id, alert_type) "
        "VALUES %s ON CONFLICT (client_id, alert_type) DO NOTHING"
    )
    psycopg2.extras.execute_values(cur, sql, rows)
    logger.info('  inserted: %d skeleton rows', len(rows))
    return len(rows)


# ─── VALIDATION ──────────────────────────────────────────────────────────────

def validate(conn) -> None:
    cur = conn.cursor()
    results = {}

    # CHECK 1 — retention flag
    cur.execute(
        "SELECT COUNT(*) FROM client_azure_co.meta_ad_performance "
        "WHERE stored_before_retention_limit = TRUE"
    )
    retention_true = cur.fetchone()[0]
    cur.execute(
        "SELECT COUNT(*) FROM client_azure_co.meta_ad_performance "
        "WHERE date_start::date < %s",
        (RETENTION_CUTOFF,),
    )
    before_cutoff = cur.fetchone()[0]
    ok1 = retention_true == before_cutoff
    results['CHECK 1'] = (ok1, f'retention_true={retention_true:,}  cutoff_rows={before_cutoff:,}  expected_equal=True')

    # CHECK 2 — attribution_setting values
    cur.execute(
        "SELECT attribution_setting, COUNT(*) "
        "FROM client_azure_co.meta_ad_performance "
        "GROUP BY 1 ORDER BY 1"
    )
    att_counts = {r[0]: r[1] for r in cur.fetchall()}
    pre  = att_counts.get('pre_window_change', 0)
    post = att_counts.get('post_window_change', 0)
    old  = att_counts.get('7d_click_1d_view', 0) + att_counts.get('28d_click_7d_view', 0)
    ok2  = pre == 5948 and post == 1428 and old == 0
    results['CHECK 2'] = (ok2, f'pre_window_change={pre:,}  post_window_change={post:,}  old_values_remaining={old}')

    # CHECK 3 — influencer_profile row count + ambassador count
    cur.execute("SELECT COUNT(*) FROM public.influencer_profile WHERE client_id = %s", (CLIENT_ID,))
    inf_count = cur.fetchone()[0]
    cur.execute(
        "SELECT COUNT(*) FROM public.influencer_profile "
        "WHERE client_id = %s AND relationship_tier = 'ambassador'",
        (CLIENT_ID,),
    )
    amb_count = cur.fetchone()[0]
    ok3 = inf_count == 15 and amb_count == 2
    results['CHECK 3'] = (ok3, f'creator_rows={inf_count}  expected=15  ambassadors={amb_count}  expected=2')

    # CHECK 4 — influencer_profile macro ROI < 1 (direct attribution limitation)
    cur.execute(
        "SELECT creator_id, follower_tier, lifetime_return_adjusted_roi "
        "FROM public.influencer_profile "
        "WHERE client_id = %s AND follower_tier = 'macro' "
        "ORDER BY creator_id",
        (CLIENT_ID,),
    )
    macro_rows = cur.fetchall()
    macro_low_roi = [r for r in macro_rows if r[2] is not None and float(r[2]) < 1.0]
    ok4 = len(macro_low_roi) >= 1
    macro_desc = ', '.join(f"{r[0]}={float(r[2]):.2f}" for r in macro_rows if r[2] is not None)
    results['CHECK 4'] = (ok4, f'macro_creators ROI: {macro_desc}  (>=1 must have ROI<1.0 for direct-attribution gap)')

    # CHECK 5 — founder_preference_profile row count
    cur.execute(
        "SELECT COUNT(*) FROM public.founder_preference_profile WHERE client_id = %s",
        (CLIENT_ID,),
    )
    fpp_count = cur.fetchone()[0]
    ok5 = fpp_count == 43
    results['CHECK 5'] = (ok5, f'founder_pref_rows={fpp_count}  expected=43')

    # CHECK 6 — all 43 alert types present
    cur.execute(
        "SELECT alert_type FROM public.founder_preference_profile "
        "WHERE client_id = %s ORDER BY alert_type",
        (CLIENT_ID,),
    )
    present = {r[0] for r in cur.fetchall()}
    missing = sorted(set(ALERT_TYPES_43) - present)
    ok6 = len(missing) == 0
    results['CHECK 6'] = (ok6, f'present={len(present)}  missing={missing if missing else "none"}')

    cur.close()

    # ── print summary ──────────────────────────────────────────────────────────
    SEP = '=' * 72
    print()
    print(SEP)
    print('PATCH VALIDATION — 6 CHECKS')
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
    print('SUMMARY')
    print(SEP)
    for check, (ok, _) in results.items():
        print(f'  {check}: {"PASS" if ok else "FAIL"}')
    print(f'  {passed}/6 checks passed')
    print(SEP)

    if passed < 6:
        sys.exit(1)


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main() -> None:
    sys.stdout.reconfigure(encoding='utf-8')
    url = os.getenv('DATABASE_URL')
    if not url:
        print('ERROR: DATABASE_URL not set')
        sys.exit(1)

    logger.info('SOURCE: Patch Script | CLIENT: %s | Starting', CLIENT_ID)
    conn = psycopg2.connect(url, sslmode='require')
    cur  = conn.cursor()

    try:
        patch4_meta(cur)
        patch5_influencer_profile(cur)
        patch6_founder_preference(cur)
        conn.commit()
        logger.info('All patches committed.')
    except Exception as exc:
        conn.rollback()
        logger.error(
            'SOURCE: Patch Script | CLIENT: %s | ERROR: %s',
            CLIENT_ID, exc,
        )
        raise
    finally:
        cur.close()

    validate(conn)
    conn.close()
    logger.info('SOURCE: Patch Script | CLIENT: %s | Complete', CLIENT_ID)


if __name__ == '__main__':
    main()
