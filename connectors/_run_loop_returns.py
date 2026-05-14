"""
Steps 2-6 for the 3 manually-designed Loop Returns tables.

  Step 2  — CREATE tables in Supabase (from manual schema design)
  Step 3  — Verify tables exist
  Step 4  — schema_discovery per table
  Step 5  — python_transformer first load per table
  Step 6  — python_transformer second run (incremental test)
  Step 7  — Summary report
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

TABLES      = ['loop_returns', 'loop_return_line_items', 'loop_refunds']
CLIENT_ID   = 'azure_co'
SCHEMA      = 'client_azure_co'
SOURCE_NAME = 'loop_returns'
SEP         = '=' * 66

DDL = [
    """
    CREATE TABLE IF NOT EXISTS client_azure_co.loop_returns (
        id                      bigint          primary key,
        order_id                bigint,
        customer_id             bigint,
        status                  text,
        return_type             text,
        created_at              timestamptz,
        updated_at              timestamptz,
        processed_at            timestamptz,
        total_refund_amount     numeric,
        currency                text,
        destination             text,
        _airbyte_extracted_at   timestamptz,
        is_synthetic            boolean default false
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS client_azure_co.loop_return_line_items (
        id                      bigint          primary key,
        return_id               bigint,
        order_line_item_id      bigint,
        variant_id              bigint,
        product_id              bigint,
        sku                     text,
        quantity                integer,
        return_reason           text,
        return_reason_detail    text,
        condition               text,
        price                   numeric,
        _airbyte_extracted_at   timestamptz,
        is_synthetic            boolean default false
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS client_azure_co.loop_refunds (
        id                      bigint          primary key,
        return_id               bigint,
        amount                  numeric,
        currency                text,
        status                  text,
        refund_method           text,
        created_at              timestamptz,
        _airbyte_extracted_at   timestamptz,
        is_synthetic            boolean default false
    )
    """,
]


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
        WHERE client_id  = %s AND table_name = %s
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
    results = {t: {} for t in TABLES}

    # ------------------------------------------------------------------
    # STEP 2 — create tables
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 2 -- Creating Loop Returns tables in Supabase')
    print(SEP)
    for stmt in DDL:
        label = stmt.strip().splitlines()[0].strip()[:60]
        try:
            cur.execute(stmt)
            print(f'  OK   {label}')
        except Exception as exc:
            print(f'  ERR  {label}\n       {exc}')
    conn.commit()
    print()

    # ------------------------------------------------------------------
    # STEP 3 — verify tables exist
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 3 -- Verifying tables exist')
    print(SEP)
    cur.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = %s
          AND table_name = ANY(%s)
        ORDER BY table_name
        """,
        (SCHEMA, TABLES),
    )
    found = [r[0] for r in cur.fetchall()]
    missing = [t for t in TABLES if t not in found]
    for t in found:
        print(f'  EXISTS  {t}')
    if missing:
        print(f'\n  MISSING: {missing}')
        print('  Aborting — fix table creation before continuing.')
        conn.close()
        sys.exit(1)
    print()

    # ------------------------------------------------------------------
    # STEP 4 — schema discovery
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 4 -- Schema discovery')
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
            f'  {table:<30}  '
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
    total = cur2.fetchone()[0]
    print(f'\n  Total loop_returns columns registered: {total}')
    print()

    # ------------------------------------------------------------------
    # STEP 5 — first load
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 5 -- First load (transform_table run 1)')
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
        out = buf.getvalue()
        mode     = _parse(out, 'Load mode')
        rows     = _parse(out, 'Rows inserted')
        fallback = _parse(out, 'Cast-fallback columns')
        results[table].update({
            'run1_mode': mode, 'run1_rows': rows,
            'run1_fallbacks': fallback, 'run1_ok': success,
        })
        status = 'OK' if success else 'FAIL'
        print(
            f'  {table:<30}  {status}  '
            f'mode={mode}  rows={rows}  fallbacks={fallback}  ({elapsed:.1f}s)'
        )
    print()

    # ------------------------------------------------------------------
    # STEP 6 — incremental test (run 2)
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 6 -- Incremental test (transform_table run 2)')
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
        out = buf.getvalue()
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
            f'  {table:<30}  {status}  '
            f'mode={mode}  rows={rows}  wm_col={wm_col}  ({elapsed:.1f}s)'
        )

        if not inc_pass:
            print(f'    >> success={success}  wm_val={wm_val}')
    print()

    conn.close()

    # ------------------------------------------------------------------
    # STEP 7 — summary
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 7 -- Summary')
    print(SEP)
    print(
        f'  {"Table":<30}  {"Cols":>4}  '
        f'{"Stg?":>5}  {"2-run":>6}  Fallbacks'
    )
    print('  ' + '-' * 58)
    all_pass = True
    for table in TABLES:
        r        = results[table]
        cols     = r.get('reg_cols', '?')
        stg      = 'yes' if r.get('run1_ok') else 'no'
        two_run  = 'PASS' if r.get('inc_pass') else 'FAIL'
        fallback = r.get('run1_fallbacks', '?')
        if two_run == 'FAIL' or stg == 'no':
            all_pass = False
        print(
            f'  {table:<30}  {cols!s:>4}  '
            f'{stg:>5}  {two_run:>6}  {fallback}'
        )
    print()
    print(f'  Overall: {"ALL PASS" if all_pass else "SEE FAILURES ABOVE"}')
    print(SEP)
    return results


if __name__ == '__main__':
    main()
