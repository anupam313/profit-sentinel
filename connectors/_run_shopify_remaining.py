"""
DEBT-005 — Register all remaining Shopify source tables in
source_schema_registry and create their staging tables.

Steps:
  1. Find all shopify_* tables in client_azure_co
  2. Find which are already registered (skip those)
  3. schema_discovery for each unregistered table
  4. python_transformer run 1 (first load)
  5. python_transformer run 2 (incremental test)
  6. Row count verification (raw vs staging)
  7. Summary report with updated registry totals
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

from connectors.schema_discovery import discover_and_update_schema
from connectors.python_transformer import transform_table

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s %(levelname)-8s %(message)s',
)

CLIENT_ID   = 'azure_co'
SCHEMA      = 'client_azure_co'
SOURCE_NAME = 'shopify'
SEP         = '=' * 66


def get_row_count(cur, qualified: str):
    try:
        cur.execute(f'SELECT COUNT(*) FROM {qualified}')
        return cur.fetchone()[0]
    except Exception as exc:
        return f'ERROR: {exc}'


def get_registry_count(cur, table: str) -> int:
    cur.execute(
        """
        SELECT COUNT(*) FROM public.source_schema_registry
        WHERE client_id  = %s AND table_name = %s
        """,
        (CLIENT_ID, table),
    )
    return cur.fetchone()[0]


def _parse(text: str, label: str) -> str:
    for line in text.splitlines():
        if label in line and ':' in line:
            return line.split(':', 1)[1].strip()
    return '?'


def main():
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print('ERROR: DATABASE_URL not in .env')
        sys.exit(1)

    conn = psycopg2.connect(database_url, sslmode='require')
    conn.autocommit = False
    cur = conn.cursor()

    # ------------------------------------------------------------------
    # STEP 1 — already registered Shopify tables
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 1 -- Shopify tables already in source_schema_registry')
    print(SEP)
    cur.execute(
        """
        SELECT DISTINCT table_name
        FROM public.source_schema_registry
        WHERE client_id   = %s
          AND table_name LIKE 'shopify\\_%%'
        ORDER BY table_name
        """,
        (CLIENT_ID,),
    )
    already_registered = {row[0] for row in cur.fetchall()}
    print(f'  Already registered: {len(already_registered)} table(s)')
    for t in sorted(already_registered):
        print(f'    {t}')
    print()

    # ------------------------------------------------------------------
    # STEP 2 — all Shopify tables in client_azure_co
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 2 -- All shopify_* tables in client_azure_co')
    print(SEP)
    cur.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = %s
          AND table_name LIKE 'shopify\\_%%'
        ORDER BY table_name
        """,
        (SCHEMA,),
    )
    all_shopify = [row[0] for row in cur.fetchall()]
    print(f'  Found: {len(all_shopify)} table(s)')
    print()

    # ------------------------------------------------------------------
    # STEP 3 — tables to process (in schema but not registered)
    # ------------------------------------------------------------------
    to_process = [t for t in all_shopify if t not in already_registered]
    print(SEP)
    print(f'STEP 3 -- Tables to register: {len(to_process)}')
    print(SEP)
    for t in to_process:
        print(f'  {t}')
    print()

    if not to_process:
        print('  Nothing to do — all Shopify tables already registered.')
        conn.close()
        return {}

    results = {t: {} for t in to_process}

    # ------------------------------------------------------------------
    # STEP 4 — schema discovery for unregistered tables
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 4 -- Schema discovery')
    print(SEP)
    for table in to_process:
        t0 = time.time()
        summary = discover_and_update_schema(
            client_id=CLIENT_ID,
            table_name=table,
            source_name=SOURCE_NAME,
            conn=conn,
        )
        elapsed = time.time() - t0
        reg = get_registry_count(conn.cursor(), table)
        results[table]['reg_cols']  = reg
        results[table]['discovery'] = summary
        err_count = len(summary['errors'])
        print(
            f'  {table:<45}  '
            f'found={summary["found"]:>3}  '
            f'new={summary["new"]:>3}  '
            f'errors={err_count}  '
            f'registered={reg}  '
            f'({elapsed:.1f}s)'
        )

    cur2 = conn.cursor()
    cur2.execute(
        """
        SELECT COUNT(*) FROM public.source_schema_registry
        WHERE client_id = %s AND source_name = %s
        """,
        (CLIENT_ID, SOURCE_NAME),
    )
    total_shopify = cur2.fetchone()[0]
    print(f'\n  Total Shopify columns now in registry: {total_shopify}')
    print()

    # ------------------------------------------------------------------
    # STEP 5 — first load
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 5 -- First load (transform_table run 1)')
    print(SEP)
    for table in to_process:
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
        results[table].update({
            'run1_mode': mode, 'run1_rows': rows,
            'run1_fallbacks': fallback, 'run1_ok': success,
        })
        status = 'OK' if success else 'FAIL'
        print(
            f'  {table:<45}  {status}  '
            f'mode={mode}  rows={rows}  fallbacks={fallback}  ({elapsed:.1f}s)'
        )
    print()

    # ------------------------------------------------------------------
    # STEP 6 — incremental test (run 2)
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 6 -- Incremental test (transform_table run 2)')
    print(SEP)
    for table in to_process:
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
        wm_val = _parse(out, 'Watermark value')
        inc_pass = (
            success
            and mode   == 'incremental'
            and rows   == '0'
            and wm_col == '_airbyte_extracted_at'
        )
        results[table].update({
            'run2_mode': mode, 'run2_rows': rows,
            'run2_wm_col': wm_col, 'run2_wm_val': wm_val,
            'run2_ok': success, 'inc_pass': inc_pass,
        })
        status = 'PASS' if inc_pass else 'FAIL'
        print(
            f'  {table:<45}  {status}  '
            f'mode={mode}  rows={rows}  wm_col={wm_col}  ({elapsed:.1f}s)'
        )
        if not inc_pass:
            print(f'    >> success={success}  wm_val={wm_val}')
    print()

    # ------------------------------------------------------------------
    # STEP 7 — row count verification
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 7 -- Row count verification (raw vs staging)')
    print(SEP)
    cur3 = conn.cursor()
    for table in to_process:
        raw     = get_row_count(cur3, f'{SCHEMA}.{table}')
        staging = get_row_count(cur3, f'{SCHEMA}.stg_{table}')
        match   = (raw == staging) and not isinstance(raw, str)
        results[table]['raw_count']     = raw
        results[table]['staging_count'] = staging
        results[table]['count_match']   = match
        status = 'MATCH' if match else 'MISMATCH'
        print(
            f'  {table:<45}  '
            f'raw={raw!s:<8}  staging={staging!s:<8}  {status}'
        )
    print()

    conn.close()

    # ------------------------------------------------------------------
    # STEP 8 — summary
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 8 -- Summary')
    print(SEP)
    print(
        f'  {"Table":<45}  {"Cols":>4}  '
        f'{"Raw":>8}  {"Stg":>8}  '
        f'{"Counts":>7}  {"2-run":>6}  Fallbacks'
    )
    print('  ' + '-' * 86)
    all_pass = True
    for table in to_process:
        r        = results[table]
        cols     = r.get('reg_cols', '?')
        raw      = r.get('raw_count', '?')
        stg      = r.get('staging_count', '?')
        counts   = 'MATCH' if r.get('count_match') else 'FAIL'
        two_run  = 'PASS'  if r.get('inc_pass')    else 'FAIL'
        fallback = r.get('run1_fallbacks', '?')
        if counts == 'FAIL' or two_run == 'FAIL':
            all_pass = False
        print(
            f'  {table:<45}  {cols!s:>4}  '
            f'{raw!s:>8}  {stg!s:>8}  '
            f'{counts:>7}  {two_run:>6}  {fallback}'
        )
    print()
    print(f'  Total Shopify columns now in registry: {total_shopify}')
    print(f'  Overall: {"ALL PASS" if all_pass else "SEE FAILURES ABOVE"}')
    print(SEP)

    return results, total_shopify


if __name__ == '__main__':
    main()
