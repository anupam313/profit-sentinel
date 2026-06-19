"""Backfill synthetic Standard Taxonomy categories onto existing shopify_products rows.

The seed insert uses ON CONFLICT DO NOTHING, so re-seeding will not update rows
that already exist. This applies assign_synthetic_category() (the SAME function
the seed uses, imported — single source of truth) to the synthetic block only.

Idempotent: values are a deterministic function of product_id, and NULLs are
written explicitly, so re-running produces an identical result and never
double-applies. The real (non-synthetic) Airbyte rows are never touched.
"""
import os
import sys

import psycopg2
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from seed_shopify import assign_synthetic_category  # noqa: E402  (same logic as the seed)

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

SCHEMA = 'client_azure_co'
# Synthetic ids start at 500_000_001; real Airbyte ids are ~7.6e12. Anything
# below this bound is synthetic seed data. Verified this session.
SYNTHETIC_ID_BOUND = 600_000_000


def get_conn():
    url = os.getenv('DATABASE_URL')
    if not url:
        print('ERROR: DATABASE_URL not set')
        sys.exit(1)
    return psycopg2.connect(url, sslmode='require')


def real_row_fingerprint(cur):
    """Snapshot real rows' category state so we can prove they were not touched."""
    cur.execute(f"""
        SELECT COUNT(*),
               COUNT(category_id),
               md5(COALESCE(string_agg(
                   id || ':' || COALESCE(category_id, '') || ':' || COALESCE(category_full_name, ''),
                   '|' ORDER BY id), ''))
        FROM {SCHEMA}.shopify_products
        WHERE id >= %s
    """, (SYNTHETIC_ID_BOUND,))
    return cur.fetchone()


def main():
    conn = get_conn()
    cur = conn.cursor()
    try:
        before_real = real_row_fingerprint(cur)
        print(f'real rows BEFORE: count={before_real[0]} non_null_cat={before_real[1]} '
              f'fingerprint={before_real[2][:12]}')

        cur.execute(f"""
            SELECT id, product_type FROM {SCHEMA}.shopify_products
            WHERE id < %s ORDER BY id
        """, (SYNTHETIC_ID_BOUND,))
        synthetic = cur.fetchall()

        categorized = nulled = 0
        for pid, ptype in synthetic:
            cid, cfull = assign_synthetic_category(pid, ptype)
            cur.execute(f"""
                UPDATE {SCHEMA}.shopify_products
                   SET category_id = %s, category_full_name = %s
                 WHERE id = %s
            """, (cid, cfull, pid))
            if cid is None:
                nulled += 1
            else:
                categorized += 1

        conn.commit()

        after_real = real_row_fingerprint(cur)
        total = len(synthetic)
        print(f'\nsynthetic rows updated: {total}')
        print(f'  categorized: {categorized} ({categorized / total:.0%})')
        print(f'  NULL:        {nulled} ({nulled / total:.0%})')
        print(f'\nreal rows AFTER:  count={after_real[0]} non_null_cat={after_real[1]} '
              f'fingerprint={after_real[2][:12]}')
        untouched = (before_real == after_real)
        print(f'real rows UNTOUCHED: {untouched}')
        if not untouched:
            print('  !! WARNING: real-row fingerprint changed — investigate before trusting this run')
    except Exception as e:
        conn.rollback()
        print(f'ERROR: {e}')
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == '__main__':
    main()
