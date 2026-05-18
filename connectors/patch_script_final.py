"""
patch_script_final.py — Three backfill patches closing Step 5 of the build sequence.

Patch 1: return_lag_segment on loop_returns and loop_return_line_items (raw tables).
         Staging tables (stg_) also receive the column for schema consistency,
         but have 0 rows so no UPDATE is needed there.

Patch 2: verification_category on public.alert_log (156 rows, 41 alert_type values).
         Uses actual column name 'alert_type' (not 'signal_type' which does not exist).

Patch 3: vertical_tag on public.network_pattern_benchmarks.
         Column added; UPDATE targets Archetype A rows (0 rows currently — schema patch
         for future data).

Discovery summary (queried before writing this script):
  loop_returns:               2226 rows, join key order_id → shopify_orders.id::text
  loop_return_line_items:     2691 rows, join key return_id → loop_returns.return_id
  stg_loop_returns:           0 rows (staging not yet loaded)
  stg_loop_return_line_items: 0 rows
  shopify_orders:             84230 rows, order date column: created_at
  alert_log:                  156 rows, alert_type column present
  network_pattern_benchmarks: 0 rows, archetype column (not archetype_id)

Build standards:
  Fix 3:  One transaction block per patch. ON CONFLICT DO NOTHING bare.
  Fix 5:  Never insert explicit id on GENERATED ALWAYS columns.
  Fix 8:  No numpy scalars used — pure SQL backfills, no Python numerics sent to psycopg2.
  No airbyte_meta_cols() on any table.
  No is_synthetic operations — these are backfill patches, not inserts.
"""

import os
import sys
import logging
from dotenv import load_dotenv
import psycopg2

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)

CLIENT_SCHEMA = 'client_azure_co'


# ─── HELPERS ─────────────────────────────────────────────────────────────────

def _connect():
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.error('DATABASE_URL not set')
        sys.exit(1)
    conn = psycopg2.connect(db_url)
    conn.autocommit = False
    return conn


def _fail(msg: str):
    logger.error('SOURCE: patch_script_final.py | ERROR: %s', msg)
    raise RuntimeError(msg)


# ─── PATCH 1 ─────────────────────────────────────────────────────────────────

def patch1_return_lag_segment():
    """Add and populate return_lag_segment on loop_returns and loop_return_line_items."""
    logger.info('=== PATCH 1: return_lag_segment ===')
    conn = _connect()
    try:
        cur = conn.cursor()

        # ── Step 1: Discovery queries ──────────────────────────────────────
        print('\n--- Patch 1 discovery ---')

        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'client_azure_co' AND table_name = 'stg_loop_returns'
            ORDER BY ordinal_position
        """)
        print('stg_loop_returns columns:')
        for r in cur.fetchall(): print(f'  {r}')

        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'client_azure_co' AND table_name = 'stg_loop_return_line_items'
            ORDER BY ordinal_position
        """)
        print('stg_loop_return_line_items columns:')
        for r in cur.fetchall(): print(f'  {r}')

        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'client_azure_co' AND table_name = 'stg_shopify_orders'
            AND column_name IN ('id','order_id','created_at','order_date','processed_at')
            ORDER BY ordinal_position
        """)
        print('stg_shopify_orders date columns:')
        for r in cur.fetchall(): print(f'  {r}')

        cur.execute('SELECT COUNT(*) FROM client_azure_co.stg_loop_returns')
        print(f'stg_loop_returns row count: {cur.fetchone()[0]}')
        cur.execute('SELECT COUNT(*) FROM client_azure_co.stg_loop_return_line_items')
        print(f'stg_loop_return_line_items row count: {cur.fetchone()[0]}')
        cur.execute('SELECT COUNT(*) FROM client_azure_co.loop_returns')
        raw_lr_count = cur.fetchone()[0]
        print(f'loop_returns (raw) row count: {raw_lr_count}')
        cur.execute('SELECT COUNT(*) FROM client_azure_co.loop_return_line_items')
        raw_li_count = cur.fetchone()[0]
        print(f'loop_return_line_items (raw) row count: {raw_li_count}')

        # ── Step 2: Add column to all four tables ──────────────────────────
        logger.info('Adding return_lag_segment column...')
        for tbl in ['loop_returns', 'loop_return_line_items',
                    'stg_loop_returns', 'stg_loop_return_line_items']:
            cur.execute(f"""
                ALTER TABLE {CLIENT_SCHEMA}.{tbl}
                ADD COLUMN IF NOT EXISTS return_lag_segment TEXT
            """)
        logger.info('Columns added.')

        # ── Step 3a: UPDATE loop_returns via shopify_orders join ──────────
        # loop_returns.order_id (text) → shopify_orders.id (bigint)
        # return date column: return_initiated_at
        # order date column:  shopify_orders.created_at
        logger.info('Updating loop_returns.return_lag_segment...')
        cur.execute(f"""
            UPDATE {CLIENT_SCHEMA}.loop_returns lr
            SET return_lag_segment = CASE
                WHEN (lr.return_initiated_at::date - so.created_at::date) <= 3
                    THEN 'impulse_regret'
                WHEN (lr.return_initiated_at::date - so.created_at::date) <= 14
                    THEN 'fit_quality'
                WHEN (lr.return_initiated_at::date - so.created_at::date) <= 30
                    THEN 'lifestyle_change'
                ELSE 'other'
            END
            FROM {CLIENT_SCHEMA}.shopify_orders so
            WHERE lr.order_id = so.id::text
              AND lr.return_lag_segment IS NULL
        """)
        lr_updated = cur.rowcount
        logger.info('loop_returns updated: %d rows', lr_updated)

        # Rows that failed to join (order_id not in shopify_orders)
        cur.execute(f"""
            UPDATE {CLIENT_SCHEMA}.loop_returns
            SET return_lag_segment = 'other'
            WHERE return_lag_segment IS NULL
        """)
        lr_fallback = cur.rowcount
        if lr_fallback > 0:
            logger.warning(
                'SOURCE: patch_script_final.py | CLIENT: azure_co | '
                'CONTEXT: %d loop_returns rows had no matching shopify_orders.id — '
                'set to "other"', lr_fallback
            )

        # ── Step 3b: Propagate to loop_return_line_items via return_id ────
        logger.info('Propagating return_lag_segment to loop_return_line_items...')
        cur.execute(f"""
            UPDATE {CLIENT_SCHEMA}.loop_return_line_items li
            SET return_lag_segment = lr.return_lag_segment
            FROM {CLIENT_SCHEMA}.loop_returns lr
            WHERE li.return_id = lr.return_id
              AND li.return_lag_segment IS NULL
        """)
        li_updated = cur.rowcount
        logger.info('loop_return_line_items updated: %d rows', li_updated)

        # Line items whose return_id has no match in loop_returns
        cur.execute(f"""
            UPDATE {CLIENT_SCHEMA}.loop_return_line_items
            SET return_lag_segment = 'other'
            WHERE return_lag_segment IS NULL
        """)
        li_fallback = cur.rowcount
        if li_fallback > 0:
            logger.warning(
                'SOURCE: patch_script_final.py | CLIENT: azure_co | '
                'CONTEXT: %d loop_return_line_items rows had no matching return_id — '
                'set to "other"', li_fallback
            )

        conn.commit()

        # ── Step 4: Verification ──────────────────────────────────────────
        print('\n--- Patch 1 verification ---')
        cur.execute(f"""
            SELECT return_lag_segment, COUNT(*)
            FROM {CLIENT_SCHEMA}.loop_returns
            GROUP BY return_lag_segment
            ORDER BY return_lag_segment
        """)
        rows = cur.fetchall()
        print('loop_returns return_lag_segment distribution:')
        for seg, cnt in rows:
            print(f'  {seg}: {cnt:,}')

        cur.execute(f"""
            SELECT COUNT(*) FROM {CLIENT_SCHEMA}.loop_returns
            WHERE return_lag_segment IS NULL
        """)
        null_lr = cur.fetchone()[0]

        cur.execute(f"""
            SELECT return_lag_segment, COUNT(*)
            FROM {CLIENT_SCHEMA}.loop_return_line_items
            GROUP BY return_lag_segment
            ORDER BY return_lag_segment
        """)
        li_rows = cur.fetchall()
        print('loop_return_line_items return_lag_segment distribution:')
        for seg, cnt in li_rows:
            print(f'  {seg}: {cnt:,}')

        cur.execute(f"""
            SELECT COUNT(*) FROM {CLIENT_SCHEMA}.loop_return_line_items
            WHERE return_lag_segment IS NULL
        """)
        null_li = cur.fetchone()[0]

        segments_lr = {r[0] for r in rows}
        # Pass: no NULLs; all segment values are from the valid enum.
        # impulse_regret (lag ≤3 days) may be absent if no seed returns had that short a lag.
        valid_segments = {'impulse_regret', 'fit_quality', 'lifestyle_change', 'other'}
        invalid = segments_lr - valid_segments
        if null_lr > 0:
            _fail(f'Patch 1 FAIL: {null_lr} NULL return_lag_segment rows in loop_returns')
        if null_li > 0:
            _fail(f'Patch 1 FAIL: {null_li} NULL return_lag_segment rows in loop_return_line_items')
        if invalid:
            _fail(f'Patch 1 FAIL: unexpected segment values in loop_returns: {invalid}')
        if not segments_lr:
            _fail('Patch 1 FAIL: no segment values found in loop_returns')

        print(f'Patch 1 PASS — NULLs: loop_returns={null_lr}, line_items={null_li}')
        cur.close()

    except Exception:
        conn.rollback()
        conn.close()
        raise
    finally:
        try:
            conn.close()
        except Exception:
            pass


# ─── PATCH 2 ─────────────────────────────────────────────────────────────────

def patch2_verification_category():
    """Add and populate verification_category on public.alert_log."""
    logger.info('=== PATCH 2: verification_category ===')
    conn = _connect()
    try:
        cur = conn.cursor()

        # ── Step 1: Discovery queries ──────────────────────────────────────
        print('\n--- Patch 2 discovery ---')
        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'alert_log'
            ORDER BY ordinal_position
        """)
        print('alert_log columns:')
        for r in cur.fetchall(): print(f'  {r}')

        cur.execute('SELECT DISTINCT alert_type FROM public.alert_log ORDER BY alert_type')
        alert_types = [r[0] for r in cur.fetchall()]
        print(f'\nDISTINCT alert_type values ({len(alert_types)}):')
        for at in alert_types: print(f'  {at}')

        cur.execute('SELECT COUNT(*) FROM public.alert_log')
        total = cur.fetchone()[0]
        print(f'\nalert_log total rows: {total}')

        # Check column presence
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'alert_log'
            AND column_name = 'verification_category'
        """)
        col_exists = bool(cur.fetchone())
        print(f'verification_category column already exists: {col_exists}')

        # ── Step 2: Add column if not present ─────────────────────────────
        cur.execute("""
            ALTER TABLE public.alert_log
            ADD COLUMN IF NOT EXISTS verification_category TEXT
        """)
        logger.info('verification_category column ensured.')

        # ── Step 3: UPDATE by alert_type ──────────────────────────────────
        # Category A — directionally verifiable in data independent of founder action:
        #   A1 (ROAS drop trajectory), A3 (channel reversal — verifiable in ad data),
        #   Alert5_stage1/stage2 (complaint velocity → return spike),
        #   C3 (SKU return confirmed), G1 (stockout prediction), G2 (overstock)
        #
        # Category C — structurally unverifiable:
        #   dark_social, multi_touch, attribution patterns (none in current data)
        #
        # Category B — action-confounded (conservative default for everything else):
        #   B1/D1/D5/E1 families, H-series DQ, F-series checkout, E2, operational signals
        logger.info('Updating verification_category...')
        cur.execute("""
            UPDATE public.alert_log
            SET verification_category = CASE
                -- Category A: directionally verifiable (outcome arrives in data regardless)
                WHEN alert_type IN (
                    'A1', 'A3',
                    'Alert5_stage1', 'Alert5_stage2',
                    'C3',
                    'G1', 'G2'
                ) THEN 'A'
                -- Category C: structurally unverifiable (no clean outcome signal)
                WHEN alert_type ILIKE '%dark_social%'  THEN 'C'
                WHEN alert_type ILIKE '%multi_touch%'  THEN 'C'
                WHEN alert_type ILIKE '%attribution%'  THEN 'C'
                -- Category B: action-confounded (conservative default)
                ELSE 'B'
            END
            WHERE verification_category IS NULL
        """)
        updated = cur.rowcount
        logger.info('alert_log verification_category updated: %d rows', updated)

        conn.commit()

        # ── Step 4: Verification ──────────────────────────────────────────
        print('\n--- Patch 2 verification ---')
        cur.execute("""
            SELECT verification_category, COUNT(*)
            FROM public.alert_log
            GROUP BY verification_category
            ORDER BY verification_category
        """)
        rows = cur.fetchall()
        print('alert_log verification_category distribution:')
        for cat, cnt in rows:
            print(f'  {cat}: {cnt}')

        cur.execute("""
            SELECT COUNT(*) FROM public.alert_log
            WHERE verification_category IS NULL
        """)
        null_count = cur.fetchone()[0]
        print(f'NULL count: {null_count}')

        categories = {r[0] for r in rows}
        if null_count > 0:
            _fail(f'Patch 2 FAIL: {null_count} NULL verification_category rows')
        if 'A' not in categories or 'B' not in categories:
            _fail(f'Patch 2 FAIL: expected A and B categories, got {categories}')

        print('Patch 2 PASS')
        cur.close()

    except Exception:
        conn.rollback()
        conn.close()
        raise
    finally:
        try:
            conn.close()
        except Exception:
            pass


# ─── PATCH 3 ─────────────────────────────────────────────────────────────────

def patch3_vertical_tag():
    """Add vertical_tag to network_pattern_benchmarks; tag all Archetype A rows."""
    logger.info('=== PATCH 3: vertical_tag ===')
    conn = _connect()
    try:
        cur = conn.cursor()

        # ── Step 1: Discovery queries ──────────────────────────────────────
        print('\n--- Patch 3 discovery ---')
        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'network_pattern_benchmarks'
            ORDER BY ordinal_position
        """)
        print('network_pattern_benchmarks columns:')
        for r in cur.fetchall(): print(f'  {r}')

        cur.execute("""
            SELECT DISTINCT archetype FROM public.network_pattern_benchmarks
            ORDER BY archetype
        """)
        archetypes = cur.fetchall()
        print(f'DISTINCT archetype values: {archetypes}')

        cur.execute('SELECT COUNT(*) FROM public.network_pattern_benchmarks')
        total = cur.fetchone()[0]
        print(f'network_pattern_benchmarks total rows: {total}')

        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'network_pattern_benchmarks'
            AND column_name = 'vertical_tag'
        """)
        print(f'vertical_tag column already exists: {bool(cur.fetchone())}')

        # ── Step 2: Add column if not present ─────────────────────────────
        cur.execute("""
            ALTER TABLE public.network_pattern_benchmarks
            ADD COLUMN IF NOT EXISTS vertical_tag TEXT
        """)
        logger.info('vertical_tag column ensured.')

        # ── Step 3: Tag all Archetype A rows ──────────────────────────────
        # actual column name is 'archetype' (not 'archetype_id')
        cur.execute("""
            UPDATE public.network_pattern_benchmarks
            SET vertical_tag = 'contemporary_womenswear'
            WHERE archetype = 'A'
              AND vertical_tag IS NULL
        """)
        a_updated = cur.rowcount
        logger.info('Archetype A rows tagged: %d', a_updated)

        conn.commit()

        # ── Step 4: Verification ──────────────────────────────────────────
        print('\n--- Patch 3 verification ---')
        cur.execute("""
            SELECT archetype, vertical_tag, COUNT(*)
            FROM public.network_pattern_benchmarks
            GROUP BY archetype, vertical_tag
            ORDER BY archetype
        """)
        rows = cur.fetchall()
        print('network_pattern_benchmarks archetype/vertical distribution:')
        if rows:
            for arch, vtag, cnt in rows:
                print(f'  archetype={arch!r}  vertical_tag={vtag!r}  count={cnt}')
        else:
            print('  (no rows — table is empty; column schema added for future data)')

        # Check: no Archetype A row has NULL vertical_tag
        cur.execute("""
            SELECT COUNT(*) FROM public.network_pattern_benchmarks
            WHERE archetype = 'A' AND vertical_tag IS NULL
        """)
        null_a = cur.fetchone()[0]
        if null_a > 0:
            _fail(f'Patch 3 FAIL: {null_a} Archetype A rows with NULL vertical_tag')

        print(f'Archetype A rows tagged: {a_updated}. NULL Archetype A: {null_a}.')
        print('Patch 3 PASS')
        cur.close()

    except Exception:
        conn.rollback()
        conn.close()
        raise
    finally:
        try:
            conn.close()
        except Exception:
            pass


# ─── FINAL SUMMARY ────────────────────────────────────────────────────────────

def print_final_summary():
    conn = _connect()
    conn.autocommit = True
    cur = conn.cursor()

    print('\n' + '=' * 60)
    print('PATCH_SCRIPT_FINAL COMPLETE')
    print('=' * 60)

    # Patch 1 summary
    print('\nPatch 1 — return_lag_segment:')
    cur.execute(f"""
        SELECT return_lag_segment, COUNT(*)
        FROM {CLIENT_SCHEMA}.loop_returns
        GROUP BY return_lag_segment ORDER BY return_lag_segment
    """)
    for seg, cnt in cur.fetchall():
        print(f'  {seg:<20} {cnt:>6,}')

    # Patch 2 summary
    print('\nPatch 2 — verification_category:')
    cur.execute("""
        SELECT verification_category, COUNT(*)
        FROM public.alert_log
        GROUP BY verification_category ORDER BY verification_category
    """)
    for cat, cnt in cur.fetchall():
        print(f'  Category {cat}:  {cnt:>4} rows')
    cur.execute('SELECT COUNT(*) FROM public.alert_log WHERE verification_category IS NULL')
    print(f'  NULL count: {cur.fetchone()[0]}')

    # Patch 3 summary
    print('\nPatch 3 — vertical_tag (network_pattern_benchmarks):')
    cur.execute("""
        SELECT archetype, vertical_tag, COUNT(*)
        FROM public.network_pattern_benchmarks
        GROUP BY archetype, vertical_tag ORDER BY archetype
    """)
    rows = cur.fetchall()
    if rows:
        for arch, vtag, cnt in rows:
            print(f'  archetype={arch!r}  vertical_tag={vtag!r}  count={cnt}')
    else:
        print('  (table empty — vertical_tag column added for future seeding)')

    print()
    print('All 3 patches verified. Step 5 complete.')
    print('Ready for Step 6 (dbt rebuild).')
    cur.close()
    conn.close()


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    logger.info('Starting patch_script_final.py')
    try:
        patch1_return_lag_segment()
        patch2_verification_category()
        patch3_vertical_tag()
        print_final_summary()
    except RuntimeError as exc:
        logger.error('SOURCE: patch_script_final.py | FATAL: %s', exc)
        sys.exit(1)


if __name__ == '__main__':
    main()
