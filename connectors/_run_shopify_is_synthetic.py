"""
Step 4 — DEBT-002: Add is_synthetic to all Shopify source tables.

Discovers all shopify_* tables in client_azure_co at runtime,
runs ADD COLUMN IF NOT EXISTS is_synthetic boolean default false
on each, then verifies the column is present.
"""

import logging
import os
import sys

import psycopg2
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s %(levelname)-8s %(message)s',
)

SCHEMA = 'client_azure_co'
SEP    = '=' * 66


def main():
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print('ERROR: DATABASE_URL not in .env')
        sys.exit(1)

    conn = psycopg2.connect(database_url, sslmode='require')
    conn.autocommit = False
    cur = conn.cursor()

    # ------------------------------------------------------------------
    # STEP 1 — discover shopify_* tables
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 1 -- Discovering shopify_* tables in client_azure_co')
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
    tables = [row[0] for row in cur.fetchall()]

    if not tables:
        print('  ERROR: No shopify_* tables found.')
        conn.close()
        sys.exit(1)

    print(f'  Found {len(tables)} Shopify table(s):')
    for t in tables:
        print(f'    {t}')
    print()

    # ------------------------------------------------------------------
    # STEP 2 — ALTER TABLE: add is_synthetic to every table
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 2 -- ALTER TABLE: ADD COLUMN is_synthetic')
    print(SEP)
    alter_errors = []
    for table in tables:
        try:
            cur.execute(
                f"ALTER TABLE {SCHEMA}.{table} "
                f"ADD COLUMN IF NOT EXISTS is_synthetic boolean default false"
            )
            print(f'  OK   {table}')
        except Exception as exc:
            alter_errors.append((table, str(exc)))
            print(f'  ERR  {table}  — {exc}')
    conn.commit()
    print()

    # ------------------------------------------------------------------
    # STEP 3 — verify is_synthetic present on every table
    # ------------------------------------------------------------------
    print(SEP)
    print('STEP 3 -- Verification: is_synthetic present on every table')
    print(SEP)
    cur.execute(
        """
        SELECT table_name
        FROM information_schema.columns
        WHERE table_schema = %s
          AND table_name   LIKE 'shopify\\_%%'
          AND column_name  = 'is_synthetic'
        ORDER BY table_name
        """,
        (SCHEMA,),
    )
    confirmed = {row[0] for row in cur.fetchall()}

    results = {}
    all_yes = True
    for table in tables:
        present = table in confirmed
        results[table] = present
        if not present:
            all_yes = False

    # Print full report
    print(f'  {"Table":<55}  is_synthetic')
    print('  ' + '-' * 68)
    for table in tables:
        flag = 'yes' if results[table] else 'NO — MISSING'
        print(f'  {table:<55}  {flag}')

    print()
    print(f'  Tables checked : {len(tables)}')
    print(f'  Confirmed yes  : {sum(results.values())}')
    missing = [t for t, v in results.items() if not v]
    if missing:
        print(f'  MISSING        : {missing}')
    print()

    conn.close()

    # ------------------------------------------------------------------
    # STEP 4 — outcome
    # ------------------------------------------------------------------
    print(SEP)
    if all_yes and not alter_errors:
        print('DEBT-002: CLOSED — is_synthetic present on all Shopify tables')
    else:
        print('DEBT-002: OPEN — see failures above')
    print(SEP)

    return results


if __name__ == '__main__':
    main()
