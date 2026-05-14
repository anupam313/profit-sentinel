"""Verification queries for Step 2 completion check."""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
conn = psycopg2.connect(os.getenv('DATABASE_URL'), sslmode='require')
cur = conn.cursor()

SEP = '-' * 62

# ── 4a: Registry count matches shopify_orders column count ─────────────────
cur.execute("""
    SELECT COUNT(*), source_name
    FROM public.source_schema_registry
    WHERE client_id = 'azure_co'
    GROUP BY source_name
""")
print(SEP)
print('VERIFY 1 — source_schema_registry row count')
print(SEP)
for row in cur.fetchall():
    print(f'  count={row[0]}  source={row[1]}')

# ── 4b: Staging table exists ────────────────────────────────────────────────
cur.execute("""
    SELECT COUNT(*)
    FROM information_schema.tables
    WHERE table_schema = 'client_azure_co'
      AND table_name   = 'stg_shopify_orders'
""")
print(SEP)
print('VERIFY 2 -- stg_shopify_orders exists')
print(SEP)
print(f'  table exists: {cur.fetchone()[0] == 1}')

# ── 4b: Row counts match ────────────────────────────────────────────────────
cur.execute("""
    SELECT
        (SELECT COUNT(*) FROM client_azure_co.shopify_orders)     AS raw_count,
        (SELECT COUNT(*) FROM client_azure_co.stg_shopify_orders) AS staging_count
""")
row = cur.fetchone()
print(SEP)
print('VERIFY 3 -- row counts match')
print(SEP)
print(f'  raw shopify_orders    : {row[0]}')
print(f'  stg_shopify_orders    : {row[1]}')
print(f'  counts match          : {row[0] == row[1]}')

# ── 4c: Spot check transformations ─────────────────────────────────────────
cur.execute("""
    SELECT column_name, transformation, raw_data_type, target_data_type
    FROM public.source_schema_registry
    WHERE table_name      = 'shopify_orders'
      AND transformation != 'none'
    ORDER BY transformation, column_name
    LIMIT 20
""")
rows = cur.fetchall()
print(SEP)
print('VERIFY 4 -- spot check transformations (non-none, up to 20)')
print(SEP)
print(f'  {"column_name":<40}  {"transformation":<28}  {"raw_type":<12}  target_type')
for r in rows:
    print(f'  {r[0]:<40}  {r[1]:<28}  {r[2]:<12}  {r[3]}')

# ── 4d: Type verification on staging ───────────────────────────────────────
key_cols = [
    'total_price', 'subtotal_price',
    'created_at', 'processed_at',
    'total_shipping_price_set', 'customer',
]
cur.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_schema = 'client_azure_co'
      AND table_name   = 'stg_shopify_orders'
      AND column_name  = ANY(%s)
    ORDER BY column_name
""", (key_cols,))
rows = cur.fetchall()
print(SEP)
print('VERIFY 5 -- key column types in stg_shopify_orders')
print(SEP)
expected = {
    'total_price':             'numeric',
    'subtotal_price':          'numeric',
    'created_at':              'timestamp with time zone',
    'processed_at':            'timestamp with time zone',
    'total_shipping_price_set':'jsonb',
    'customer':                'jsonb',
}
for r in rows:
    col, dtype = r[0], r[1]
    exp = expected.get(col, '?')
    ok  = 'PASS' if dtype == exp else f'FAIL (expected {exp})'
    print(f'  {col:<30}  {dtype:<35}  {ok}')

# ── schema_versions: new_column entries ────────────────────────────────────
cur.execute("""
    SELECT change_type, COUNT(*)
    FROM public.schema_versions
    WHERE client_id = 'azure_co'
    GROUP BY change_type
""")
rows = cur.fetchall()
print(SEP)
print('VERIFY 6 -- schema_versions entries')
print(SEP)
for r in rows:
    print(f'  {r[0]:<20}  {r[1]} rows')

conn.close()
print(SEP)
