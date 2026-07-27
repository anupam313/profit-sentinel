"""
Seed the hand-calibrated client_config threshold + segment-boundary values
for client_azure_co.

WHY THIS EXISTS (reproducibility gap, found 2026-07-27):
  onboarding_flow.py READS these values from client_config and scales them by
  the chosen alert sensitivity, then writes them back. Nothing SETS the base
  values -- they were entered by hand and lived only inside Supabase. If the
  database were rebuilt from the repo alone, these calibrations would be lost.
  This script restores exactly the values that were live on 2026-07-27.

  Contains NO Slack token, workspace id, or channel id -- only calibration
  numbers. Idempotent: a plain UPDATE of fixed literals, so re-running sets
  the same values. Run AFTER the client_config row exists.

REBUILD ORDER: schema DDL (sql/schema.sql) -> the client_config row
  (created by onboarding, or restored from the schema + a row insert) -> this
  script. This script only UPDATEs an existing row; it does not create one.

RUN: python connectors/seed_client_config_calibration.py
"""
import logging
import os
import sys

import psycopg2
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s')
logger = logging.getLogger(__name__)

# client_config.client_id is 'client_azure_co' -- the CANONICAL value
# (dbt var client_id = client_schema = 'client_azure_co', corrected
# 2026-05-18 during the dbt rebuild). The seed scripts' Python
# CLIENT_ID constant is still 'azure_co'; ~306 seeded app rows carry
# it. Known, routed as a seed-normalisation fix, synthetic-only, not
# urgent. This script targets the canonical value.
CLIENT_ID = 'client_azure_co'

# column -> value.  Provenance in comments; sources are the
# pre_agent_build_checklist.md calibration log.  Values read back live 2026-07-27.
CALIBRATION = {
    # C1 sizing-complaint trigger. p90 of sizing_complaint_velocity_pct on the
    # synthetic mart -- fires on 9.9% of synthetic dates. Per-client
    # recalibration is owed at real onboarding (checklist T-1 / CD-10).
    'gorgias_sentiment_threshold':          43.61,

    # D1 contribution-margin floor. Raised from the 5% default (far too low for
    # womenswear); D1 then fires on 3/730 synthetic dates (checklist T-2,
    # 2026-05-19).
    'margin_floor_pct':                     28.0,

    # D1 margin-drop trigger, paired with margin_floor_pct above
    # (checklist T-2, 2026-05-19).
    'contribution_margin_drop_threshold':   10.0,

    # Blended gross margin for the D1 mart. Onboarding-entered value (Q1b,
    # validated 0.20-0.85); azure_co answered 0.55 (checklist D-11, 2026-05-19).
    'blended_gross_margin_pct':             0.55,

    # Customer-segment boundaries -- the ALTER TABLE column DEFAULTs from B-11
    # (2026-05-21); the live values match those defaults exactly.
    'repeat_customer_order_minimum':        2,    # B-11 default
    'explorer_max_orders':                  1,    # B-11 default
    'regular_max_orders':                   3,    # B-11 default
    'loyalist_max_orders':                  6,    # B-11 default
    'advocate_min_orders':                  7,    # B-11 default
    'segment_significance_min_revenue_pct': 2.0,  # B-11 default (numeric)
}


def get_conn():
    url = os.getenv('DATABASE_URL')
    if not url:
        logger.error('SOURCE: client_config calibration | CLIENT: %s | '
                     'ERROR: DATABASE_URL not set | CONTEXT: %s',
                     CLIENT_ID, 'cannot connect')
        sys.exit(1)
    return psycopg2.connect(url, sslmode='require')


def main():
    cols = list(CALIBRATION.keys())
    set_clause = ', '.join(f'{c} = %s' for c in cols)
    params = [CALIBRATION[c] for c in cols] + [CLIENT_ID]

    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            f'UPDATE public.client_config SET {set_clause} WHERE client_id = %s',
            params,
        )
        affected = cur.rowcount
        if affected == 0:
            conn.rollback()
            logger.error('SOURCE: client_config calibration | CLIENT: %s | '
                         'ERROR: no client_config row updated | CONTEXT: %s',
                         CLIENT_ID, 'row must exist before calibration is set')
            return
        conn.commit()
        logger.info('Set %d calibration values on client_config (%d row).',
                    len(cols), affected)

        # read-back verification (named columns only -- never SELECT *)
        cur.execute(
            f'SELECT {", ".join(cols)} FROM public.client_config '
            f'WHERE client_id = %s', (CLIENT_ID,))
        for c, v in zip(cols, cur.fetchone()):
            logger.info('  %-38s = %s', c, v)
        cur.close()
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        logger.error('SOURCE: client_config calibration | CLIENT: %s | '
                     'ERROR: %s | CONTEXT: %s',
                     CLIENT_ID, str(e), {'columns': cols})
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    main()
