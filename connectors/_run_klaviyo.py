"""
One-shot orchestration: Steps 1-5 for the 6 Klaviyo tables.

Runs in order:
  1. ADD COLUMN is_synthetic to each table
  2. schema_discovery per table
  3. python_transformer first load per table
  4. python_transformer second run (incremental test) per table
  5. Row count verification (raw vs staging)
"""

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
    level=logging.WARNING,           # suppress INFO noise during the run
    format='%(asctime)s %(levelname)-8s %(message)s',
)

TABLES = [
    'klaviyo_campaigns',
    'klaviyo_events',
    'klaviyo_flows',
    'klaviyo_lists',
    'klaviyo_metrics',
    'klaviyo_profiles',
]

CLIENT_ID   = 'azure_co'
SCHEMA      = 'client_azure_co'
SOURCE_NAME = 'klaviyo'

SEP  = '-' * 66
SEP2 = '=' * 66


def add_is_synthetic(cur, table: str) -> str:
    """Returns 'added', 'already_exists', or error message."""
    try:
        cur.execute(
            f"ALTER TABLE {SCHEMA}.{table} "
            f"ADD COLUMN IF NOT EXISTS is_synthetic boolean default false"
        )
        # Check whether column now exists
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


def get_row_count(cur, qualified_table: str):
    try:
        cur.execute(f'SELECT COUNT(*) FROM {qualified_table}')
        return cur.fetchone()[0]
    except Exception as exc:
        return f'ERROR: {exc}'


def get_registry_count(cur, table: str) -> int:
    cur.execute(
        """
        SELECT COUNT(*) FROM public.source_schema_registry
        WHERE client_id  = %s
          AND table_name = %s
        """,
        (CLIENT_ID, table),
    )
    return cur.fetchone()[0]


def main():
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print('ERROR: DATABASE_URL not in .env')
        sys.exit(1)

    conn = psycopg2.connect(database_url, sslmode='require')

    results = {t: {} for t in TABLES}

    # ------------------------------------------------------------------
    # STEP 1 — add is_synthetic column
    # ------------------------------------------------------------------
    print(SEP2)
    print('STEP 1 — Adding is_synthetic column')
    print(SEP2)
    conn.autocommit = False
    cur = conn.cursor()
    for table in TABLES:
        status = add_is_synthetic(cur, table)
        results[table]['is_synthetic'] = status
        print(f'  {table:<30}  {status}')
    conn.commit()
    print()

    # ------------------------------------------------------------------
    # STEP 2 — schema discovery
    # ------------------------------------------------------------------
    print(SEP2)
    print('STEP 2 — Schema discovery')
    print(SEP2)
    for table in TABLES:
        t0 = time.time()
        summary = discover_and_update_schema(
            client_id=CLIENT_ID,
            table_name=table,
            source_name=SOURCE_NAME,
            conn=conn,
        )
        elapsed = time.time() - t0
        # refresh column count from registry
        cur2 = conn.cursor()
        reg_count = get_registry_count(cur2, table)
        results[table]['discovery'] = summary
        results[table]['reg_cols']  = reg_count
        err_count = len(summary['errors'])
        print(
            f'  {table:<30}  '
            f'found={summary["found"]:>3}  '
            f'new={summary["new"]:>3}  '
            f'changed={summary["changed"]:>2}  '
            f'removed={summary["removed"]:>2}  '
            f'errors={err_count}  '
            f'registered={reg_count}  '
            f'({elapsed:.1f}s)'
        )
    print()

    # Total registry count for Klaviyo
    cur3 = conn.cursor()
    cur3.execute(
        """
        SELECT COUNT(*) FROM public.source_schema_registry
        WHERE client_id   = %s
          AND source_name = %s
        """,
        (CLIENT_ID, SOURCE_NAME),
    )
    total_klaviyo_cols = cur3.fetchone()[0]
    print(f'  Total Klaviyo columns in source_schema_registry: {total_klaviyo_cols}')
    print()

    # ------------------------------------------------------------------
    # STEP 3 — first load (python_transformer)
    # ------------------------------------------------------------------
    print(SEP2)
    print('STEP 3 — First load (transform_table run 1)')
    print(SEP2)
    for table in TABLES:
        # Capture stdout from transform_table by redirecting
        import io, contextlib
        buf = io.StringIO()
        t0 = time.time()
        with contextlib.redirect_stdout(buf):
            success = transform_table(
                client_id=CLIENT_ID,
                table_name=table,
                conn=conn,
            )
        elapsed = time.time() - t0
        output = buf.getvalue()

        # Parse key lines from the report block
        load_mode   = _parse(output, 'Load mode')
        rows_in     = _parse(output, 'Rows inserted')
        fallbacks   = _parse(output, 'Cast-fallback columns')
        wm_col      = _parse(output, 'Watermark column')

        results[table]['run1_mode']      = load_mode
        results[table]['run1_rows']      = rows_in
        results[table]['run1_fallbacks'] = fallbacks
        results[table]['run1_success']   = success

        status = 'OK' if success else 'FAIL'
        print(
            f'  {table:<30}  '
            f'{status}  '
            f'mode={load_mode}  '
            f'rows={rows_in}  '
            f'fallbacks={fallbacks}  '
            f'({elapsed:.1f}s)'
        )
    print()

    # ------------------------------------------------------------------
    # STEP 4 — incremental test (python_transformer run 2)
    # ------------------------------------------------------------------
    print(SEP2)
    print('STEP 4 — Incremental test (transform_table run 2)')
    print(SEP2)
    for table in TABLES:
        import io, contextlib
        buf = io.StringIO()
        t0 = time.time()
        with contextlib.redirect_stdout(buf):
            success = transform_table(
                client_id=CLIENT_ID,
                table_name=table,
                conn=conn,
            )
        elapsed = time.time() - t0
        output = buf.getvalue()

        load_mode  = _parse(output, 'Load mode')
        rows_in    = _parse(output, 'Rows inserted')
        wm_col     = _parse(output, 'Watermark column')
        wm_val     = _parse(output, 'Watermark value')

        results[table]['run2_mode']    = load_mode
        results[table]['run2_rows']    = rows_in
        results[table]['run2_wm_col']  = wm_col
        results[table]['run2_wm_val']  = wm_val
        results[table]['run2_success'] = success

        inc_pass = (
            success
            and load_mode    == 'incremental'
            and rows_in      == '0'
            and wm_col       == '_airbyte_extracted_at'
        )
        status = 'PASS' if inc_pass else 'FAIL'
        print(
            f'  {table:<30}  '
            f'{status}  '
            f'mode={load_mode}  '
            f'rows={rows_in}  '
            f'wm_col={wm_col}  '
            f'({elapsed:.1f}s)'
        )
    print()

    # ------------------------------------------------------------------
    # STEP 5 — row count verification
    # ------------------------------------------------------------------
    print(SEP2)
    print('STEP 5 — Row count verification (raw vs staging)')
    print(SEP2)
    cur4 = conn.cursor()
    for table in TABLES:
        raw     = get_row_count(cur4, f'{SCHEMA}.{table}')
        staging = get_row_count(cur4, f'{SCHEMA}.stg_{table}')
        match   = (raw == staging) and not isinstance(raw, str)
        results[table]['raw_count']     = raw
        results[table]['staging_count'] = staging
        results[table]['count_match']   = match
        status = 'MATCH' if match else 'MISMATCH'
        print(
            f'  {table:<30}  '
            f'raw={raw!s:<6}  staging={staging!s:<6}  {status}'
        )
    print()

    conn.close()

    # ------------------------------------------------------------------
    # STEP 6 — summary table
    # ------------------------------------------------------------------
    print(SEP2)
    print('STEP 6 — Summary')
    print(SEP2)
    print(
        f'  {"Table":<30}  {"Cols":>4}  '
        f'{"Raw":>6}  {"Stg":>6}  '
        f'{"Counts":>7}  {"2-run":>6}  Fallbacks'
    )
    print('  ' + '-' * 62)
    all_pass = True
    for table in TABLES:
        r        = results[table]
        col_ct   = r.get('reg_cols', '?')
        raw      = r.get('raw_count', '?')
        stg      = r.get('staging_count', '?')
        counts   = 'MATCH'  if r.get('count_match')  else 'FAIL'
        inc_pass = (
            r.get('run2_success')
            and r.get('run2_mode')    == 'incremental'
            and r.get('run2_rows')    == '0'
            and r.get('run2_wm_col')  == '_airbyte_extracted_at'
        )
        two_run  = 'PASS' if inc_pass else 'FAIL'
        fallback = r.get('run1_fallbacks', '?')
        if counts == 'FAIL' or two_run == 'FAIL':
            all_pass = False
        print(
            f'  {table:<30}  {col_ct!s:>4}  '
            f'{raw!s:>6}  {stg!s:>6}  '
            f'{counts:>7}  {two_run:>6}  {fallback}'
        )
    print()
    print(f'  Overall: {"ALL PASS" if all_pass else "SEE FAILURES ABOVE"}')
    print(SEP2)

    return results


def _parse(text: str, label: str) -> str:
    """Extract value from transformer print block, e.g. 'Load mode : first_load'"""
    for line in text.splitlines():
        if label in line and ':' in line:
            return line.split(':', 1)[1].strip()
    return '?'


if __name__ == '__main__':
    results = main()
