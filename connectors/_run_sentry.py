"""
Sentry pipeline — Step 3f.

Discovers all sentry_* tables that Airbyte created in
client_azure_co at runtime (same dynamic pattern as _run_ga4.py),
then runs the full pipeline for each:

  1. Discover sentry_* tables from information_schema
  2. ADD COLUMN is_synthetic boolean default false
  3. Verify is_synthetic present
  4. schema_discovery per table
  5. python_transformer run 1 (first load)
  6. python_transformer run 2 (incremental test)
  7. Row count verification (raw vs staging)
  8. Summary report
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
SOURCE_NAME = 'sentry'
SEP         = '=' * 66


def discover_sentry_tables(cur) -> list[str]:
    cur.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = %s
          AND table_name LIKE 'sentry\\_%%'
        ORDER BY table_name
        """,
        (SCHEMA,),
    )
    return [row[0] for row in cur.fetchall()]


def add_is_synthetic(cur, table: str) -> str:
    try:
        cur.execute(
            f"ALTER TABLE {SCHEMA}.{table} "
            f"ADD COLUMN IF NOT EXISTS is_synthetic boolean default false"
        )
        cur.execute(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = %s
              AND table_name   = %s
              AND column_name  = 'is_synthetic'
            """,
            (SCHEMA, table),
        )
        return 'present' if cur.fetchone() else 'missing_after_alter'
    except Exception as exc:
        return f'ERROR: {exc}'


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
    # STEP 1 — discover Sentry tables
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 1 -- Discovering sentry_* tables in client_azure_co')
    print(SEP)
    tables = discover_sentry_tables(cur)

    if not tables:
        print('  ERROR: No sentry_* tables found in client_azure_co.')
        print('  Confirm Airbyte sync completed before running this script.')
        conn.close()
        sys.exit(1)

    print(f'  Found {len(tables)} table(s):')
    for t in tables:
        print(f'    {t}')
    print()

    results = {t: {} for t in tables}

    # ------------------------------------------------------------------
    # STEP 2 — add is_synthetic column
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 2 -- Adding is_synthetic column')
    print(SEP)
    for table in tables:
        status = add_is_synthetic(cur, table)
        results[table]['is_synthetic'] = status
        print(f'  {table:<45}  is_synthetic: {status}')
    conn.commit()
    print()

    # ------------------------------------------------------------------
    # STEP 3 — schema discovery
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 3 -- Schema discovery')
    print(SEP)
    for table in tables:
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
            f'changed={summary["changed"]:>2}  '
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
    total_sentry_cols = cur2.fetchone()[0]
    print(f'\n  Total Sentry columns in source_schema_registry: {total_sentry_cols}')
    print()

    # ------------------------------------------------------------------
    # STEP 4 — first load (python_transformer run 1)
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 4 -- First load (transform_table run 1)')
    print(SEP)
    for table in tables:
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
    # STEP 5 — incremental test (python_transformer run 2)
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 5 -- Incremental test (transform_table run 2)')
    print(SEP)
    for table in tables:
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
    # STEP 6 — row count verification
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 6 -- Row count verification (raw vs staging)')
    print(SEP)
    cur3 = conn.cursor()
    for table in tables:
        raw     = get_row_count(cur3, f'{SCHEMA}.{table}')
        staging = get_row_count(cur3, f'{SCHEMA}.stg_{table}')
        match   = (raw == staging) and not isinstance(raw, str)
        results[table]['raw_count']     = raw
        results[table]['staging_count'] = staging
        results[table]['count_match']   = match
        status = 'MATCH' if match else 'MISMATCH'
        print(
            f'  {table:<45}  '
            f'raw={raw!s:<6}  staging={staging!s:<6}  {status}'
        )
    print()

    conn.close()

    # ------------------------------------------------------------------
    # STEP 7 — summary
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 7 -- Summary')
    print(SEP)
    print(
        f'  {"Table":<45}  {"Cols":>4}  '
        f'{"Raw":>6}  {"Stg":>6}  '
        f'{"Counts":>7}  {"2-run":>6}  Fallbacks'
    )
    print('  ' + '-' * 78)
    all_pass = True
    for table in tables:
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
            f'{raw!s:>6}  {stg!s:>6}  '
            f'{counts:>7}  {two_run:>6}  {fallback}'
        )
    print()
    print(f'  Total Sentry columns registered: {total_sentry_cols}')
    print(f'  Overall: {"ALL PASS" if all_pass else "SEE FAILURES ABOVE"}')
    print(SEP)
    return results


if __name__ == '__main__':
    main()
