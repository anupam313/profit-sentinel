"""
GA4 pipeline orchestration — Steps 1-7.
Discovers actual GA4 tables, then runs the full pipeline.
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
SOURCE_NAME = 'ga4'
SEP         = '=' * 66


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


def get_registry_count(cur, table: str) -> int:
    cur.execute(
        """
        SELECT COUNT(*) FROM public.source_schema_registry
        WHERE client_id = %s AND table_name = %s
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
    conn.autocommit = False
    cur = conn.cursor()

    # ------------------------------------------------------------------
    # STEP 1 — discover GA4 tables
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 1 -- Discovering GA4 tables in client_azure_co')
    print(SEP)
    cur.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = %s
          AND table_name LIKE %s
        ORDER BY table_name
        """,
        (SCHEMA, 'ga4\\_%%'),   # escape _ wildcard; %% = literal %
    )
    TABLES = [r[0] for r in cur.fetchall()]
    if not TABLES:
        print('  No GA4 tables found. Check Airbyte sync completed.')
        conn.close()
        sys.exit(1)
    for t in TABLES:
        print(f'  {t}')
    print(f'\n  Total: {len(TABLES)} tables found')
    print()

    results = {t: {} for t in TABLES}

    # ------------------------------------------------------------------
    # STEP 2 — add is_synthetic column
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 2 -- Adding is_synthetic column')
    print(SEP)
    for table in TABLES:
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
            status = 'present' if cur.fetchone() else 'missing_after_alter'
        except Exception as exc:
            status = f'ERROR: {exc}'
        results[table]['is_synthetic'] = status
        print(f'  {table:<45}  {status}')
    conn.commit()
    print()

    # ------------------------------------------------------------------
    # STEP 3 — schema discovery
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 3 -- Schema discovery')
    print(SEP)
    for table in TABLES:
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
        print(
            f'  {table:<45}  '
            f'found={summary["found"]:>3}  '
            f'new={summary["new"]:>3}  '
            f'errors={len(summary["errors"])}  '
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
    total_ga4 = cur2.fetchone()[0]
    print(f'\n  Total GA4 columns in source_schema_registry: {total_ga4}')
    print()

    # ------------------------------------------------------------------
    # STEP 4 — first load
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 4 -- First load (transform_table run 1)')
    print(SEP)
    for table in TABLES:
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
    # STEP 5 — incremental test (run 2)
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 5 -- Incremental test (transform_table run 2)')
    print(SEP)
    for table in TABLES:
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
    for table in TABLES:
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
        f'{"Raw":>5}  {"Stg":>5}  {"Counts":>7}  {"2-run":>6}  Fallbacks'
    )
    print('  ' + '-' * 74)
    all_pass = True
    for table in TABLES:
        r       = results[table]
        cols    = r.get('reg_cols', '?')
        raw     = r.get('raw_count', '?')
        stg     = r.get('staging_count', '?')
        counts  = 'MATCH'  if r.get('count_match')  else 'FAIL'
        two_run = 'PASS'   if r.get('inc_pass')      else 'FAIL'
        fb      = r.get('run1_fallbacks', '?')
        if counts == 'FAIL' or two_run == 'FAIL':
            all_pass = False
        print(
            f'  {table:<45}  {cols!s:>4}  '
            f'{raw!s:>5}  {stg!s:>5}  {counts:>7}  {two_run:>6}  {fb}'
        )
    print()
    print(f'  Total GA4 columns registered: {total_ga4}')
    print(f'  Overall: {"ALL PASS" if all_pass else "SEE FAILURES ABOVE"}')
    print(SEP)

    return results, TABLES, total_ga4


if __name__ == '__main__':
    main()
