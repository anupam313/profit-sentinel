"""
Loop Returns — corrected pipeline (2026-05-15).

Drops the 2026-05-14 placeholder tables and rebuilds from
the API-verified schema in docs/manual_schemas/loop_returns_schema.sql.

What changed vs the previous version and why:
  loop_returns
    id          text (was bigint — Loop IDs are strings)
    state       replaces status (actual API field name)
    type        replaces return_type (actual API field)
    customer    text replaces customer_id bigint
    processed_at REMOVED — not in API
    destination_id replaces destination
    total_refund_amount REMOVED — replaced by 11 financial fields
    30 new fields from API (carrier, tracking, exchanges, etc.)

  loop_return_line_items
    line_item_id text replaces id bigint
    return_id text added as FK
    provider_line_item_id replaces order_line_item_id
    quantity REMOVED — not in API
    price/discount/tax now text (API returns strings)
    return_reason_detail REMOVED — API uses return_comment
    12 new fields (refund*, condition, disposition, etc.)

  loop_refunds DROPPED — no API endpoint. Refund data is
    embedded in loop_returns.refund and per-line fields.

Steps run:
  1. Drop staging and source tables + clear registry
  2. Create corrected loop_returns and loop_return_line_items
  3. Verify tables exist
  4. schema_discovery per table
  5. python_transformer first load per table
  6. python_transformer second run (incremental test)
  7. Row count verification + summary report
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

# loop_refunds intentionally excluded — no API endpoint
TABLES      = ['loop_returns', 'loop_return_line_items']
CLIENT_ID   = 'azure_co'
SCHEMA      = 'client_azure_co'
SOURCE_NAME = 'loop_returns'
SEP         = '=' * 66

DDL = [
    """
    CREATE TABLE IF NOT EXISTS client_azure_co.loop_returns (
        id                          text primary key,
        state                       text,
        type                        text,
        outcome                     text,
        created_at                  text,
        updated_at                  text,
        edited_at                   text,
        label_updated_at            text,
        order_id                    text,
        order_name                  text,
        order_number                text,
        provider_order_id           text,
        provider_order_number       text,
        customer                    text,
        origin_country              text,
        origin_country_code         text,
        currency                    text,
        multi_currency              boolean,
        return_product_total        text,
        return_discount_total       text,
        return_tax_total            text,
        return_total                text,
        return_credit_total         text,
        exchange_product_total      text,
        exchange_discount_total     text,
        exchange_tax_total          text,
        exchange_total              text,
        exchange_credit_total       text,
        gift_card                   text,
        gift_card_order_name        text,
        gift_card_order_id          text,
        handling_fee                text,
        refund                      text,
        upsell                      text,
        carrier                     text,
        tracking_number             text,
        label_status                text,
        label_url                   text,
        label_rate                  text,
        status_page_url             text,
        destination_id              text,
        package_reference           text,
        return_method               jsonb,
        exchanges                   jsonb,
        labels                      jsonb,
        _airbyte_extracted_at       timestamptz,
        is_synthetic                boolean default false
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS client_azure_co.loop_return_line_items (
        line_item_id                text,
        return_id                   text not null,
        provider_line_item_id       text,
        product_id                  text,
        variant_id                  text,
        sku                         text,
        barcode                     text,
        title                       text,
        price                       text,
        discount                    text,
        tax                         text,
        refund                      text,
        refund_item                 text,
        refund_tax                  text,
        return_reason               text,
        parent_return_reason        text,
        return_comment              text,
        outcome                     text,
        returned_at                 text,
        exchange_variant            text,
        provider_restock_location_id    text,
        consolidation_tracking          text,
        consolidation_destination_id    text,
        condition                   jsonb,
        disposition                 jsonb,
        _airbyte_extracted_at       timestamptz,
        is_synthetic                boolean default false,
        UNIQUE (return_id, line_item_id)
    )
    """,
]

# Tables to drop (source + staging + the removed loop_refunds)
TABLES_TO_DROP = [
    f'{SCHEMA}.stg_loop_refunds',
    f'{SCHEMA}.stg_loop_return_line_items',
    f'{SCHEMA}.stg_loop_returns',
    f'{SCHEMA}.loop_refunds',
    f'{SCHEMA}.loop_return_line_items',
    f'{SCHEMA}.loop_returns',
]

# Registry table_names to clear (includes the removed table)
REGISTRY_TABLES_TO_CLEAR = [
    'loop_returns',
    'loop_return_line_items',
    'loop_refunds',
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
    # STEP 1a — drop staging and source tables
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 1a -- Dropping existing tables (placeholder schema)')
    print(SEP)
    for qualified in TABLES_TO_DROP:
        try:
            cur.execute(f'DROP TABLE IF EXISTS {qualified} CASCADE')
            print(f'  DROPPED  {qualified}')
        except Exception as exc:
            print(f'  ERR      {qualified}  {exc}')
    conn.commit()
    print()

    # ------------------------------------------------------------------
    # STEP 1b — clear source_schema_registry and schema_versions
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 1b -- Clearing registry for loop_returns tables')
    print(SEP)
    for tbl in REGISTRY_TABLES_TO_CLEAR:
        cur.execute(
            """
            DELETE FROM public.source_schema_registry
            WHERE client_id = %s AND table_name = %s
            """,
            (CLIENT_ID, tbl),
        )
        deleted = cur.rowcount
        print(f'  registry  {tbl:<30}  {deleted} rows deleted')

        cur.execute(
            """
            DELETE FROM public.schema_versions
            WHERE client_id = %s AND table_name = %s
            """,
            (CLIENT_ID, tbl),
        )
        deleted_sv = cur.rowcount
        print(f'  versions  {tbl:<30}  {deleted_sv} rows deleted')
    conn.commit()
    print()

    # ------------------------------------------------------------------
    # STEP 2 — create corrected tables
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 2 -- Creating corrected Loop Returns tables')
    print(SEP)
    for stmt in DDL:
        label = stmt.strip().splitlines()[0].strip()[:60]
        try:
            cur.execute(stmt)
            print(f'  OK   {label}')
        except Exception as exc:
            print(f'  ERR  {label}')
            print(f'       {exc}')
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
    print(f'\n  Total loop_returns columns in registry: {total}')
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

    # ------------------------------------------------------------------
    # STEP 7 — row count verification
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 7 -- Row count verification (raw vs staging)')
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
            f'  {table:<30}  '
            f'raw={raw!s:<6}  staging={staging!s:<6}  {status}'
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
        f'  {"Table":<30}  {"Cols":>4}  '
        f'{"Raw":>6}  {"Stg":>6}  '
        f'{"Counts":>7}  {"2-run":>6}  Fallbacks'
    )
    print('  ' + '-' * 66)
    all_pass = True
    for table in TABLES:
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
            f'  {table:<30}  {cols!s:>4}  '
            f'{raw!s:>6}  {stg!s:>6}  '
            f'{counts:>7}  {two_run:>6}  {fallback}'
        )
    print()
    print(f'  Overall: {"ALL PASS" if all_pass else "SEE FAILURES ABOVE"}')
    print()
    print('  Removed from client_azure_co:')
    print('    loop_refunds        — no API endpoint in Loop Returns')
    print('    stg_loop_refunds    — staging for removed table')
    print('  Registry cleared for: loop_returns, loop_return_line_items,')
    print('                        loop_refunds')
    print(SEP)
    return results


if __name__ == '__main__':
    main()
