"""
Fix misclassified column types in source_schema_registry for 3 Shopify tables,
then re-run transform_table for each to create their staging tables.

Root cause: schema_discovery pattern-matched on column names and assigned wrong
transformation types. These columns contain text/jsonb but were typed as numeric
or timestamp.

Tables affected:
  shopify_customers    — tax_exemptions typed as cast_text_to_numeric (actually jsonb)
  shopify_discount_codes — discount_type typed as cast_text_to_numeric (actually text)
  shopify_shop         — money_with_currency_format, money_with_currency_in_emails_format
                         typed as jsonb_extract_from_text (actually plain text);
                         timezone typed as cast_text_to_timestamp (actually text)
"""

import contextlib
import io
import logging
import os
import sys
import time

import psycopg2
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from connectors.python_transformer import transform_table

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s %(levelname)-8s %(message)s',
)

CLIENT_ID = 'azure_co'
SCHEMA    = 'client_azure_co'
SEP       = '=' * 66

# (table_name, column_name, correct_raw_type, correct_target_type, correct_transformation)
FIXES = [
    (
        'shopify_customers', 'tax_exemptions',
        'text', 'jsonb', 'jsonb_extract',
    ),
    (
        'shopify_discount_codes', 'discount_type',
        'text', 'text', 'passthrough',
    ),
    (
        'shopify_shop', 'money_with_currency_format',
        'text', 'text', 'passthrough',
    ),
    (
        'shopify_shop', 'money_with_currency_in_emails_format',
        'text', 'text', 'passthrough',
    ),
    (
        'shopify_shop', 'timezone',
        'text', 'text', 'passthrough',
    ),
]

TABLES_TO_RERUN = ['shopify_customers', 'shopify_discount_codes', 'shopify_shop']


def _parse(text: str, label: str) -> str:
    for line in text.splitlines():
        if label in line and ':' in line:
            return line.split(':', 1)[1].strip()
    return '?'


def get_row_count(cur, qualified: str):
    try:
        cur.execute(f'SELECT COUNT(*) FROM {qualified}')
        return cur.fetchone()[0]
    except Exception as exc:
        return f'ERROR: {exc}'


def main():
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print('ERROR: DATABASE_URL not in .env')
        sys.exit(1)

    conn = psycopg2.connect(database_url, sslmode='require')
    conn.autocommit = False
    cur = conn.cursor()

    # ------------------------------------------------------------------
    # STEP 1 — show current (wrong) registry entries
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 1 -- Current registry entries for affected columns')
    print(SEP)
    for table, column, *_ in FIXES:
        cur.execute(
            """
            SELECT raw_data_type, target_data_type, transformation
            FROM public.source_schema_registry
            WHERE client_id = %s AND table_name = %s AND column_name = %s
            """,
            (CLIENT_ID, table, column),
        )
        row = cur.fetchone()
        if row:
            print(f'  {table}.{column}')
            print(f'    raw={row[0]}  target={row[1]}  transformation={row[2]}')
        else:
            print(f'  {table}.{column}  — NOT FOUND in registry')
    print()

    # ------------------------------------------------------------------
    # STEP 2 — apply fixes
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 2 -- Updating registry to correct types')
    print(SEP)
    fix_errors = []
    for table, column, raw_type, target_type, transformation in FIXES:
        try:
            cur.execute(
                """
                UPDATE public.source_schema_registry
                SET raw_data_type    = %s,
                    target_data_type = %s,
                    transformation   = %s
                WHERE client_id  = %s
                  AND table_name = %s
                  AND column_name = %s
                """,
                (raw_type, target_type, transformation, CLIENT_ID, table, column),
            )
            affected = cur.rowcount
            print(f'  OK   {table}.{column}  ->  {transformation}  (rows updated: {affected})')
        except Exception as exc:
            fix_errors.append((table, column, str(exc)))
            print(f'  ERR  {table}.{column}  -- {exc}')
    conn.commit()
    print()

    if fix_errors:
        print('  Registry update errors — aborting before transformer runs.')
        conn.close()
        sys.exit(1)

    # ------------------------------------------------------------------
    # STEP 3 — drop stale staging tables for the 3 failing tables
    #          (transformer's CREATE TABLE IF NOT EXISTS won't re-create
    #           columns if the table already exists from a prior partial run)
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 3 -- Drop stale staging tables')
    print(SEP)
    for table in TABLES_TO_RERUN:
        stg = f'{SCHEMA}.stg_{table}'
        try:
            cur.execute(f'DROP TABLE IF EXISTS {stg}')
            print(f'  dropped (if existed): {stg}')
        except Exception as exc:
            print(f'  ERR dropping {stg}: {exc}')
    conn.commit()
    print()

    # ------------------------------------------------------------------
    # STEP 4 — re-run transform_table (first load)
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 4 -- Re-run transform_table (first load)')
    print(SEP)
    run1_results = {}
    for table in TABLES_TO_RERUN:
        buf = io.StringIO()
        t0 = time.time()
        with contextlib.redirect_stdout(buf):
            success = transform_table(
                client_id=CLIENT_ID,
                table_name=table,
                conn=conn,
            )
        elapsed = time.time() - t0
        out      = buf.getvalue()
        mode     = _parse(out, 'Load mode')
        rows     = _parse(out, 'Rows inserted')
        fallback = _parse(out, 'Cast-fallback columns')
        run1_results[table] = {
            'ok': success, 'mode': mode, 'rows': rows, 'fallbacks': fallback,
        }
        status = 'OK' if success else 'FAIL'
        print(
            f'  {table:<45}  {status}  '
            f'mode={mode}  rows={rows}  fallbacks={fallback}  ({elapsed:.1f}s)'
        )
        if not success:
            print(f'    >> {out.strip()[-300:]}')
    print()

    # ------------------------------------------------------------------
    # STEP 5 — incremental test (run 2)
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 5 -- Incremental test (transform_table run 2)')
    print(SEP)
    run2_results = {}
    for table in TABLES_TO_RERUN:
        buf = io.StringIO()
        t0 = time.time()
        with contextlib.redirect_stdout(buf):
            success = transform_table(
                client_id=CLIENT_ID,
                table_name=table,
                conn=conn,
            )
        elapsed = time.time() - t0
        out    = buf.getvalue()
        mode   = _parse(out, 'Load mode')
        rows   = _parse(out, 'Rows inserted')
        wm_col = _parse(out, 'Watermark column')
        inc_pass = (
            success
            and mode   == 'incremental'
            and rows   == '0'
            and wm_col == '_airbyte_extracted_at'
        )
        run2_results[table] = {'ok': success, 'inc_pass': inc_pass, 'mode': mode, 'rows': rows}
        status = 'PASS' if inc_pass else 'FAIL'
        print(
            f'  {table:<45}  {status}  '
            f'mode={mode}  rows={rows}  wm_col={wm_col}  ({elapsed:.1f}s)'
        )
        if not inc_pass:
            print(f'    >> success={success}')
    print()

    # ------------------------------------------------------------------
    # STEP 6 — row count verification (fresh connection to avoid tx state)
    # ------------------------------------------------------------------
    conn.close()
    conn2 = psycopg2.connect(database_url, sslmode='require')
    cur2  = conn2.cursor()

    print(SEP)
    print('STEP 6 -- Row count verification')
    print(SEP)
    count_results = {}
    for table in TABLES_TO_RERUN:
        raw     = get_row_count(cur2, f'{SCHEMA}.{table}')
        staging = get_row_count(cur2, f'{SCHEMA}.stg_{table}')
        match   = (raw == staging) and not isinstance(raw, str)
        count_results[table] = {'raw': raw, 'staging': staging, 'match': match}
        status = 'MATCH' if match else 'MISMATCH'
        print(
            f'  {table:<45}  raw={raw!s:<8}  staging={staging!s:<8}  {status}'
        )
    conn2.close()
    print()

    # ------------------------------------------------------------------
    # STEP 7 — summary
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 7 -- Summary')
    print(SEP)
    all_pass = True
    for table in TABLES_TO_RERUN:
        r1    = run1_results.get(table, {})
        r2    = run2_results.get(table, {})
        cr    = count_results.get(table, {})
        ok    = r1.get('ok') and r2.get('inc_pass') and cr.get('match')
        if not ok:
            all_pass = False
        status = 'ALL PASS' if ok else 'FAIL'
        print(
            f'  {table:<45}  {status}  '
            f'raw={cr.get("raw", "?")}  stg={cr.get("staging", "?")}  '
            f'fallbacks={r1.get("fallbacks", "?")}'
        )
    print()
    print(f'  Overall: {"ALL PASS" if all_pass else "SEE FAILURES ABOVE"}')
    print(SEP)


if __name__ == '__main__':
    main()
