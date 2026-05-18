#!/usr/bin/env python3
"""
Profit Sentinel — Onboarding Flow
Parts: (1) config questions → DB, (2) dbt run, (3) first insight, (4) log.
"""

import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

CLIENT_ID = 'client_azure_co'
DBT_PROJECT_DIR = os.path.join(os.path.dirname(__file__), 'warehouse')


# ─────────────────────────────────────────────────────────────────────────────
# Connection
# ─────────────────────────────────────────────────────────────────────────────

def get_conn():
    url = os.getenv('DATABASE_URL')
    if not url:
        logger.error('SOURCE: Onboarding Flow | CLIENT: %s | ERROR: DATABASE_URL not set', CLIENT_ID)
        sys.exit(1)
    return psycopg2.connect(url, sslmode='require')


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def ask(prompt, options):
    """Re-prompts until the user enters a valid option. Returns the chosen string."""
    option_str = ' / '.join(options)
    while True:
        raw = input(f'\n{prompt}\nOptions: {option_str}\n> ').strip().lower()
        if raw in options:
            return raw
        print(f'  Invalid: "{raw}". Enter one of: {option_str}')


def column_exists(cur, schema, table, column):
    cur.execute(
        '''SELECT 1 FROM information_schema.columns
           WHERE table_schema = %s AND table_name = %s AND column_name = %s''',
        (schema, table, column)
    )
    return cur.fetchone() is not None


def client_row_exists(cur):
    cur.execute('SELECT 1 FROM public.client_config WHERE client_id = %s', (CLIENT_ID,))
    return cur.fetchone() is not None


# ─────────────────────────────────────────────────────────────────────────────
# Part 1 — Questions → public.client_config
# ─────────────────────────────────────────────────────────────────────────────

def run_questions(conn):
    answers = {}
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Q1 — COGS source
    q1 = ask(
        'Q1. Where do your COGS data come from?',
        ['finaloop', 'shopify_cost_field', 'manual_upload']
    )
    confidence_map = {
        'finaloop': 'high',
        'shopify_cost_field': 'medium',
        'manual_upload': 'low',
    }
    answers['cogs_source'] = q1
    answers['cogs_confidence_level'] = confidence_map[q1]

    # Q2 — Business model type (column may not exist)
    q2 = ask(
        'Q2. What is your business model type?',
        ['year_round', 'seasonal', 'event_driven']
    )
    answers['_q2_raw'] = q2
    bmt_exists = column_exists(cur, 'public', 'client_config', 'business_model_type')
    if bmt_exists:
        answers['business_model_type'] = q2
    else:
        print(
            '  WARNING: business_model_type column does not exist in '
            'public.client_config — answer recorded in log only, not written to DB.'
        )

    # Q3 — Attribution philosophy
    q3 = ask(
        'Q3. What is your attribution philosophy?',
        ['last_click', 'assisted', 'platform_reported']
    )
    attr_map = {
        'last_click': '1d_click',
        'assisted': '7d_click_1d_view',
        'platform_reported': 'platform_default',
    }
    answers['meta_attribution_window'] = attr_map[q3]
    answers['_q3_raw'] = q3

    # Q4 — ROAS revenue definition
    q4 = ask(
        'Q4. How do you define revenue for ROAS calculation?',
        ['gross_excl_shipping', 'gross_incl_shipping', 'net_after_returns']
    )
    answers['include_shipping_in_revenue'] = (q4 == 'gross_incl_shipping')
    answers['_q4_raw'] = q4

    # Q5 — Alert sensitivity + threshold scaling
    q5 = ask(
        'Q5. What alert sensitivity level do you prefer?',
        ['conservative', 'medium', 'aggressive']
    )
    answers['alert_sensitivity'] = q5

    multiplier_map = {'conservative': 1.5, 'medium': 1.0, 'aggressive': 0.7}
    multiplier = multiplier_map[q5]

    threshold_cols = [
        'return_rate_threshold_pp',
        'cpm_spike_threshold_pct',
        'margin_floor_pct',
        'ga4_funnel_drop_threshold',
        'sentry_error_threshold_pct',
        'gorgias_sentiment_threshold',
        'roas_drop_threshold_pct',
        'influencer_return_rate_threshold',
        'contribution_margin_drop_threshold',
    ]

    cur.execute(
        'SELECT {} FROM public.client_config WHERE client_id = %s'.format(
            ', '.join(threshold_cols)
        ),
        (CLIENT_ID,)
    )
    threshold_row = cur.fetchone()
    scaled_thresholds = {}
    if threshold_row:
        for col in threshold_cols:
            val = threshold_row.get(col)
            if val is not None:
                scaled_thresholds[col] = round(float(val) * multiplier, 4)

    answers['_scaled_thresholds'] = scaled_thresholds

    # ── Assemble the fields to write ──────────────────────────────────────────
    now_utc = datetime.now(timezone.utc)
    update_fields = {
        'cogs_source': answers['cogs_source'],
        'cogs_confidence_level': answers['cogs_confidence_level'],
        'meta_attribution_window': answers['meta_attribution_window'],
        'include_shipping_in_revenue': answers['include_shipping_in_revenue'],
        'alert_sensitivity': answers['alert_sensitivity'],
        'thresholds_last_calculated_at': now_utc,
    }
    if bmt_exists:
        update_fields['business_model_type'] = q2
    update_fields.update(scaled_thresholds)

    try:
        if client_row_exists(cur):
            set_clause = ', '.join('{} = %({})s'.format(k, k) for k in update_fields)
            sql = 'UPDATE public.client_config SET {} WHERE client_id = %(client_id)s'.format(
                set_clause
            )
            update_fields['client_id'] = CLIENT_ID
            cur.execute(sql, update_fields)
        else:
            update_fields['client_id'] = CLIENT_ID
            cols_str = ', '.join(update_fields.keys())
            placeholders = ', '.join('%({})s'.format(k) for k in update_fields)
            sql = 'INSERT INTO public.client_config ({}) VALUES ({})'.format(
                cols_str, placeholders
            )
            cur.execute(sql, update_fields)

        conn.commit()
        print('\n  Configuration saved to public.client_config.')
    except Exception as e:
        conn.rollback()
        logger.error(
            'SOURCE: Onboarding Flow | CLIENT: %s | ERROR: %s | CONTEXT: DB write failed',
            CLIENT_ID, str(e)
        )
        raise

    cur.close()
    return answers


# ─────────────────────────────────────────────────────────────────────────────
# Part 2 — dbt run --full-refresh
# ─────────────────────────────────────────────────────────────────────────────

def run_dbt():
    border = '-' * 60
    print('\n' + border)
    print('Running: dbt run --full-refresh')
    print(border)

    try:
        proc = subprocess.Popen(
            ['dbt', 'run', '--full-refresh'],
            cwd=DBT_PROJECT_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        for line in proc.stdout:
            print(line, end='', flush=True)
        proc.wait()
    except FileNotFoundError:
        logger.error(
            'SOURCE: Onboarding Flow | CLIENT: %s | ERROR: dbt not found on PATH',
            CLIENT_ID
        )
        sys.exit(1)

    if proc.returncode != 0:
        print(f'\n  ERROR: dbt exited with code {proc.returncode}. Aborting.')
        sys.exit(proc.returncode)

    print(border)
    print('  dbt run complete (exit code 0).')
    return proc.returncode


# ─────────────────────────────────────────────────────────────────────────────
# Part 3 — First insight from mart_cross_source_daily
# ─────────────────────────────────────────────────────────────────────────────

def _avg(rows, col):
    vals = [float(r[col]) for r in rows if r.get(col) is not None]
    return sum(vals) / len(vals) if vals else None


def _total(rows, col):
    vals = [float(r[col]) for r in rows if r.get(col) is not None]
    return sum(vals) if vals else None


def _pct_change(new_val, old_val):
    if old_val is None or new_val is None or old_val == 0:
        return None
    return ((new_val - old_val) / abs(old_val)) * 100


def _print_recipe_diagnostic(recent, prior, existing):
    div = '-' * 68
    print('\n' + div)
    print('INSIGHT RECIPE DIAGNOSTIC')
    print('recent window: {} days | prior window: {} days'.format(len(recent), len(prior)))
    print(div)

    def _chk(col, recent_rows, prior_rows):
        r = _avg(recent_rows, col)
        p = _avg(prior_rows, col)
        chg = _pct_change(r, p)
        return r, p, chg

    def _row(col, r_val, p_val, chg, threshold_dir, threshold_val):
        r_str  = '{:.4f}'.format(r_val)  if r_val  is not None else 'NULL'
        p_str  = '{:.4f}'.format(p_val)  if p_val  is not None else 'NULL'
        chg_str = '{:+.2f}%'.format(chg) if chg    is not None else 'NULL'
        if chg is None:
            verdict = 'SKIP (NULL)'
        elif threshold_dir == '<':
            verdict = 'PASS' if chg < threshold_val else 'FAIL'
        else:
            verdict = 'PASS' if chg > threshold_val else 'FAIL'
        print('    {:<32} recent={:>10}  prior={:>10}  chg={:>9}  threshold {} {}  [{}]'.format(
            col, r_str, p_str, chg_str, threshold_dir, threshold_val, verdict))

    # Recipe A
    print('\nRecipe A: Meta ROAS drop + Sentry errors rising  (Meta Ads + Sentry)')
    if 'meta_roas' in existing and 'sentry_error_count' in existing:
        roas_r, roas_p, roas_chg = _chk('meta_roas', recent, prior)
        sent_r, sent_p, sent_chg = _chk('sentry_error_count', recent, prior)
        _row('meta_roas',          roas_r, roas_p, roas_chg, '<', -5)
        _row('sentry_error_count', sent_r, sent_p, sent_chg, '>', 10)
        triggered = (roas_chg is not None and roas_chg < -5 and
                     sent_chg is not None and sent_chg > 10)
        print('    => {}'.format('TRIGGERED' if triggered else 'NOT TRIGGERED'))
    else:
        print('    SKIPPED — missing columns: {}'.format(
            [c for c in ['meta_roas', 'sentry_error_count'] if c not in existing]))

    # Recipe B
    print('\nRecipe B: Returns rising + Gorgias tickets rising  (Shopify + Gorgias)')
    if 'return_count' in existing and 'ticket_count' in existing:
        ret_r, ret_p, ret_chg   = _chk('return_count', recent, prior)
        tick_r, tick_p, tick_chg = _chk('ticket_count', recent, prior)
        _row('return_count', ret_r,  ret_p,  ret_chg,  '>', 10)
        _row('ticket_count', tick_r, tick_p, tick_chg, '>', 10)
        triggered = (ret_chg is not None and ret_chg > 10 and
                     tick_chg is not None and tick_chg > 10)
        print('    => {}'.format('TRIGGERED' if triggered else 'NOT TRIGGERED'))
    else:
        print('    SKIPPED — missing columns: {}'.format(
            [c for c in ['return_count', 'ticket_count'] if c not in existing]))

    # Recipe C
    print('\nRecipe C: Checkout errors rising + CVR falling  (GA4 + Sentry)')
    if 'checkout_error_count' in existing and 'avg_cvr' in existing:
        err_r, err_p, err_chg = _chk('checkout_error_count', recent, prior)
        cvr_r, cvr_p, cvr_chg = _chk('avg_cvr', recent, prior)
        _row('checkout_error_count', err_r, err_p, err_chg, '>', 5)
        _row('avg_cvr',              cvr_r, cvr_p, cvr_chg, '<', -3)
        triggered = (err_chg is not None and err_chg > 5 and
                     cvr_chg is not None and cvr_chg < -3)
        print('    => {}'.format('TRIGGERED' if triggered else 'NOT TRIGGERED'))
    else:
        print('    SKIPPED — missing columns: {}'.format(
            [c for c in ['checkout_error_count', 'avg_cvr'] if c not in existing]))

    # Recipe D
    print('\nRecipe D: Blended ROAS declining  (Meta Ads + Shopify)')
    if 'blended_roas' in existing:
        br_r, br_p, br_chg = _chk('blended_roas', recent, prior)
        _row('blended_roas', br_r, br_p, br_chg, '<', -5)
        triggered = br_chg is not None and br_chg < -5
        print('    => {}'.format('TRIGGERED' if triggered else 'NOT TRIGGERED'))
    else:
        print('    SKIPPED — missing columns: [blended_roas]')

    # Recipe E
    print('\nRecipe E: Both Meta and TikTok ROAS dropping  (Meta Ads + TikTok Ads)')
    if 'meta_roas' in existing and 'tiktok_roas' in existing:
        me_r, me_p, me_chg = _chk('meta_roas',   recent, prior)
        tt_r, tt_p, tt_chg = _chk('tiktok_roas', recent, prior)
        _row('meta_roas',   me_r, me_p, me_chg, '<', -5)
        _row('tiktok_roas', tt_r, tt_p, tt_chg, '<', -5)
        triggered = (me_chg is not None and me_chg < -5 and
                     tt_chg is not None and tt_chg < -5)
        print('    => {}'.format('TRIGGERED' if triggered else 'NOT TRIGGERED'))
    else:
        print('    SKIPPED — missing columns: {}'.format(
            [c for c in ['meta_roas', 'tiktok_roas'] if c not in existing]))

    print('\n' + div)


def run_insight(conn):
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Confirm what columns actually exist before building the query
    cur.execute(
        '''SELECT column_name
           FROM information_schema.columns
           WHERE table_schema = 'client_azure_co_marts'
             AND table_name = 'mart_cross_source_daily'
           ORDER BY ordinal_position''',
    )
    existing = {r['column_name'] for r in cur.fetchall()}

    cur.execute(
        '''SELECT *
           FROM client_azure_co_marts.mart_cross_source_daily
           WHERE client_id = %s
             AND date >= CURRENT_DATE - INTERVAL '30 days'
           ORDER BY date DESC''',
        (CLIENT_ID,)
    )
    rows = cur.fetchall()
    cur.close()

    if not rows:
        logger.error(
            'SOURCE: Onboarding Flow | CLIENT: %s | ERROR: No rows in '
            'mart_cross_source_daily for last 30 days',
            CLIENT_ID
        )
        return None, None

    # Split: most recent 15 days vs prior 15 days
    midpoint = len(rows) // 2
    recent = rows[:midpoint] if midpoint else rows
    prior = rows[midpoint:] if midpoint else []

    if not prior:
        return None, None

    _print_recipe_diagnostic(recent, prior, existing)

    candidates = []  # (score, source1, source2, headline, impact, action)

    # Candidate A: Meta ROAS drop + Sentry errors rising → paid landing degraded
    if 'meta_roas' in existing and 'sentry_error_count' in existing:
        roas_chg = _pct_change(_avg(recent, 'meta_roas'), _avg(prior, 'meta_roas'))
        sentry_chg = _pct_change(_avg(recent, 'sentry_error_count'), _avg(prior, 'sentry_error_count'))
        if roas_chg is not None and sentry_chg is not None and roas_chg < -5 and sentry_chg > 10:
            spend = _total(recent, 'meta_spend') if 'meta_spend' in existing else 0
            candidates.append((
                abs(roas_chg) + sentry_chg,
                'Meta Ads', 'Sentry',
                f'Meta ROAS has dropped {abs(roas_chg):.1f}% while Sentry error count has risen '
                f'{sentry_chg:.1f}%, suggesting site errors are degrading paid landing experiences.',
                f'With ${(spend or 0):,.0f} in Meta spend over the period, degraded ROAS is '
                f'directly compressing contribution margin.',
                'Audit Sentry for JS errors on your Meta landing pages and fix the top error '
                'before your next paid campaign.',
            ))

    # Candidate B: Returns rising + Gorgias tickets rising → product/fulfilment issue
    if 'return_count' in existing and 'ticket_count' in existing:
        ret_chg = _pct_change(_avg(recent, 'return_count'), _avg(prior, 'return_count'))
        tick_chg = _pct_change(_avg(recent, 'ticket_count'), _avg(prior, 'ticket_count'))
        if ret_chg is not None and tick_chg is not None and ret_chg > 10 and tick_chg > 10:
            refunds = _total(recent, 'return_refund_total') if 'return_refund_total' in existing else 0
            candidates.append((
                ret_chg + tick_chg,
                'Shopify', 'Gorgias',
                f'Return volume is up {ret_chg:.1f}% and support tickets are up {tick_chg:.1f}% '
                f'over the past 15 days, pointing to a shared root cause.',
                f'Returns have cost ${(refunds or 0):,.0f} in refunds over the last 15 days and '
                f'rising ticket volume signals the issue is not yet resolved.',
                'Pull the top return reason from Gorgias ticket tags this week and '
                'cross-reference with the highest-return SKUs in Shopify.',
            ))

    # Candidate C: Checkout errors rising + CVR falling → live funnel issue
    if 'checkout_error_count' in existing and 'avg_cvr' in existing:
        err_chg = _pct_change(_avg(recent, 'checkout_error_count'), _avg(prior, 'checkout_error_count'))
        cvr_chg = _pct_change(_avg(recent, 'avg_cvr'), _avg(prior, 'avg_cvr'))
        if err_chg is not None and cvr_chg is not None and err_chg > 5 and cvr_chg < -3:
            sessions = _total(recent, 'total_sessions') if 'total_sessions' in existing else 0
            aov = _avg(recent, 'average_order_value') if 'average_order_value' in existing else 0
            lost = (sessions or 0) * abs(cvr_chg / 100) * (aov or 0)
            candidates.append((
                err_chg + abs(cvr_chg),
                'GA4', 'Sentry',
                f'Checkout errors have increased {err_chg:.1f}% while conversion rate has fallen '
                f'{abs(cvr_chg):.1f}%, indicating a live checkout funnel issue.',
                f'A {abs(cvr_chg):.1f}% CVR decline across {int(sessions or 0):,} sessions '
                f'represents approximately ${lost:,.0f} in unrealised revenue.',
                'Reproduce the checkout error in staging today and push a fix — '
                'every hour of delay compounds lost conversions.',
            ))

    # Candidate D: Blended ROAS declining (Meta Ads + Shopify)
    if 'blended_roas' in existing:
        broas_chg = _pct_change(_avg(recent, 'blended_roas'), _avg(prior, 'blended_roas'))
        if broas_chg is not None and broas_chg < -5:
            spend = _total(recent, 'total_ad_spend') if 'total_ad_spend' in existing else 0
            candidates.append((
                abs(broas_chg),
                'Meta Ads', 'Shopify',
                f'Blended ROAS has declined {abs(broas_chg):.1f}% over the past 15 days.',
                f'Across ${(spend or 0):,.0f} in total ad spend, this reduces contribution margin directly.',
                'Review top ad sets and pause creative with frequency > 3 and CTR below 7-day average.',
            ))

    # Candidate E: Both Meta and TikTok ROAS dropping → site-side issue, not creative
    if 'meta_roas' in existing and 'tiktok_roas' in existing:
        me_chg = _pct_change(_avg(recent, 'meta_roas'), _avg(prior, 'meta_roas'))
        tt_chg = _pct_change(_avg(recent, 'tiktok_roas'), _avg(prior, 'tiktok_roas'))
        if me_chg is not None and tt_chg is not None and me_chg < -5 and tt_chg < -5:
            spend = _total(recent, 'total_ad_spend') if 'total_ad_spend' in existing else 0
            candidates.append((
                abs(me_chg) + abs(tt_chg),
                'Meta Ads', 'TikTok Ads',
                f'Both Meta ROAS (down {abs(me_chg):.1f}%) and TikTok ROAS (down {abs(tt_chg):.1f}%) '
                f'have declined in the same period, pointing to a shared landing or product issue.',
                f'Combined ROAS decline across ${(spend or 0):,.0f} of paid spend suggests '
                f'this is not a platform-specific issue but a site or product conversion problem.',
                'Run a landing page A/B test this week — cross-platform ROAS declines '
                'typically resolve to a site-side change, not an ad creative issue.',
            ))

    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        _, s1, s2, headline, impact, action = candidates[0]
        return (s1, s2), {'headline': headline, 'impact': impact, 'action': action}

    # Fallback: largest absolute mover across any two data-bearing sources
    if 'blended_roas' in existing and 'total_ad_spend' in existing:
        broas_r = _avg(recent, 'blended_roas')
        broas_p = _avg(prior, 'blended_roas')
        chg = _pct_change(broas_r, broas_p)
        spend = _total(recent, 'total_ad_spend') or 0
        direction = 'improved' if (chg or 0) > 0 else 'declined'
        return ('Meta Ads', 'Shopify'), {
            'headline': (
                f'Blended ROAS has {direction} {abs(chg or 0):.1f}% over the past 15 days '
                f'versus the prior 15 days.'
            ),
            'impact': (
                f'Across ${spend:,.0f} in total ad spend this period, '
                f'this shift has a direct effect on contribution margin.'
            ),
            'action': (
                'Review your top ad sets and ensure your best-performing creative '
                'is being prioritised for budget allocation.'
            ),
        }

    return None, None


def print_insight(sources, insight):
    s1, s2 = sources
    border = '=' * 40
    print(f'\n{border}')
    print('PROFIT SENTINEL -- FIRST INSIGHT')
    print(f'Sources: {s1} + {s2}')
    print(border)
    print(insight['headline'])
    print(insight['impact'])
    print(f'Action: {insight["action"]}')
    print(border)


# ─────────────────────────────────────────────────────────────────────────────
# Part 4 — onboarding_log.json
# ─────────────────────────────────────────────────────────────────────────────

def write_log(answers, dbt_exit_code, sources):
    log = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'answers': {
            'cogs_source': answers.get('cogs_source'),
            'cogs_confidence_level': answers.get('cogs_confidence_level'),
            'business_model_type': answers.get('_q2_raw'),
            'business_model_type_written_to_db': 'business_model_type' in answers,
            'attribution_philosophy': answers.get('_q3_raw'),
            'meta_attribution_window_written': answers.get('meta_attribution_window'),
            'roas_revenue_definition': answers.get('_q4_raw'),
            'include_shipping_in_revenue': answers.get('include_shipping_in_revenue'),
            'alert_sensitivity': answers.get('alert_sensitivity'),
            'scaled_thresholds': answers.get('_scaled_thresholds', {}),
        },
        'dbt_exit_code': dbt_exit_code,
        'insight_sources': list(sources) if sources else [],
    }
    log_path = os.path.join(os.path.dirname(__file__), 'onboarding_log.json')
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(log, f, indent=2, default=str)
    print(f'\n  Log written to onboarding_log.json')


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    border = '=' * 60
    print(border)
    print('PROFIT SENTINEL -- ONBOARDING FLOW')
    print(f'Client: {CLIENT_ID}')
    print(border)

    conn = get_conn()

    answers = run_questions(conn)           # Part 1
    dbt_exit_code = run_dbt()              # Part 2
    sources, insight = run_insight(conn)   # Part 3

    if sources and insight:
        print_insight(sources, insight)
    else:
        print('\n  No multi-source insight could be derived from the available data.')
        sources = (None, None)

    write_log(answers, dbt_exit_code, sources)  # Part 4

    conn.close()


if __name__ == '__main__':
    main()
