"""Confirm Shopify Standard Taxonomy `category` is fetchable via Admin GraphQL
and land it on client_azure_co.shopify_products.

Reads creds from env ONLY (never hardcode/commit):
    SHOPIFY_ADMIN_TOKEN   Admin API access token from the custom app
    SHOPIFY_STORE         e.g. profit-sentinel-test.myshopify.com

What it does:
  1. Negotiates an API version (prefers 2026-04, falls back to 2024-04).
  2. Paginates products via Admin GraphQL, backing off on THROTTLED.
  3. Prints id / title / productType / category.fullName per product + a
     non-null category summary.
  4. Adds category_id, category_full_name to shopify_products and upserts the
     real (non-synthetic) records, matched on the numeric Shopify product id.

Read-only against Shopify (read_products); only writes the two derived
columns to our own table.
"""
import os
import re
import sys
import json
import time
import logging

import requests
import psycopg2
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Prefer the requested 2026-04; step down to a known-good version if the store
# is pinned older. Anything >= 2024-04 exposes Product.category.
API_VERSIONS = ['2026-04', '2025-04', '2024-04']

SYN_LO, SYN_HI = 500000000, 500999999  # synthetic seed id block (excluded from upsert)

QUERY = """
query($cursor: String) {
  products(first: 100, after: $cursor) {
    edges {
      node {
        id
        title
        productType
        category { id fullName name level isLeaf }
      }
    }
    pageInfo { hasNextPage endCursor }
  }
}
"""


def get_db_conn():
    url = os.getenv('DATABASE_URL')
    if not url:
        logger.error('SOURCE: Category GraphQL Probe | ERROR: DATABASE_URL not set')
        sys.exit(1)
    return psycopg2.connect(url, sslmode='require')


def gid_to_int(gid: str):
    """gid://shopify/Product/7698712985696 -> 7698712985696"""
    m = re.search(r'/(\d+)$', gid or '')
    return int(m.group(1)) if m else None


def endpoint(store: str, version: str) -> str:
    return f'https://{store}/admin/api/{version}/graphql.json'


def post_graphql(store, token, version, variables, max_retries=6):
    """POST one GraphQL call. Retries on THROTTLED (cost throttling) and 5xx.

    Returns (data_dict, errors_list). Raises on hard auth/version failure.
    """
    url = endpoint(store, version)
    headers = {'X-Shopify-Access-Token': token, 'Content-Type': 'application/json'}
    payload = {'query': QUERY, 'variables': variables}

    backoff = 2.0
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
        except requests.RequestException as e:
            logger.error('SOURCE: Category GraphQL Probe | ERROR: request failed (%s) | attempt %d',
                         e, attempt)
            time.sleep(backoff)
            backoff = min(backoff * 2, 30)
            continue

        # Hard failures worth surfacing immediately.
        if resp.status_code == 401:
            raise RuntimeError('401 Unauthorized — token invalid or app not installed.')
        if resp.status_code == 404:
            raise RuntimeError(f'404 — API version {version} not served by this store.')
        if resp.status_code == 429:
            wait = float(resp.headers.get('Retry-After', backoff))
            logger.info('  HTTP 429, sleeping %.1fs', wait)
            time.sleep(wait)
            backoff = min(backoff * 2, 30)
            continue
        if resp.status_code >= 500:
            logger.info('  HTTP %d, retrying in %.1fs', resp.status_code, backoff)
            time.sleep(backoff)
            backoff = min(backoff * 2, 30)
            continue
        if resp.status_code != 200:
            raise RuntimeError(f'HTTP {resp.status_code}: {resp.text[:300]}')

        body = resp.json()
        errors = body.get('errors') or []
        throttled = any((e.get('extensions') or {}).get('code') == 'THROTTLED' for e in errors)
        if throttled:
            cost = (body.get('extensions') or {}).get('cost') or {}
            ts = cost.get('throttleStatus') or {}
            avail = ts.get('currentlyAvailable', 0)
            restore = ts.get('restoreRate', 100) or 100
            requested = (cost.get('requestedQueryCost') or 100)
            wait = max((requested - avail) / restore, backoff)
            logger.info('  THROTTLED (avail=%s restore=%s/s), sleeping %.1fs',
                        avail, restore, wait)
            time.sleep(wait)
            backoff = min(backoff * 2, 30)
            continue

        return body.get('data'), errors

    raise RuntimeError('Exhausted retries (persistent throttling or network failure).')


def negotiate_version(store, token):
    """Find the first API_VERSIONS entry that serves Product.category for this store."""
    for v in API_VERSIONS:
        try:
            data, errors = post_graphql(store, token, v, {'cursor': None})
        except RuntimeError as e:
            logger.info('  version %s rejected: %s', v, e)
            continue
        # A schema that lacks `category` returns a GraphQL field error.
        field_err = any('category' in (e.get('message') or '').lower()
                        and 'doesn' in (e.get('message') or '').lower()
                        for e in errors)
        if field_err:
            logger.info('  version %s does not expose Product.category', v)
            continue
        if data is not None:
            logger.info('  using API version %s', v)
            return v, data
    raise RuntimeError('No configured API version exposes Product.category for this store.')


def fetch_all(store, token, version, first_page):
    """Paginate from the already-fetched first page."""
    products = []
    data = first_page
    while True:
        conn_block = data['products']
        for edge in conn_block['edges']:
            products.append(edge['node'])
        page = conn_block['pageInfo']
        if not page['hasNextPage']:
            break
        data, errors = post_graphql(store, token, version, {'cursor': page['endCursor']})
        if errors:
            logger.info('  non-fatal errors on page: %s', json.dumps(errors)[:300])
        if data is None:
            break
    return products


def upsert_categories(products):
    """Add columns if missing and write category_id/full_name for real records."""
    conn = get_db_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            ALTER TABLE client_azure_co.shopify_products
                ADD COLUMN IF NOT EXISTS category_id text,
                ADD COLUMN IF NOT EXISTS category_full_name text
        """)
        conn.commit()

        written = 0
        for p in products:
            pid = gid_to_int(p['id'])
            if pid is None or SYN_LO <= pid <= SYN_HI:
                continue  # skip unparmsable + synthetic seed block
            cat = p.get('category') or {}
            cur.execute("""
                UPDATE client_azure_co.shopify_products
                   SET category_id = %s, category_full_name = %s
                 WHERE id = %s
            """, (cat.get('id'), cat.get('fullName'), pid))
            written += cur.rowcount
        conn.commit()
        logger.info('  upserted category columns onto %d existing rows', written)
    except Exception as e:
        conn.rollback()
        logger.error('SOURCE: Category GraphQL Probe | ERROR: upsert failed | %s', e)
    finally:
        cur.close()
        conn.close()


def main():
    store = os.getenv('SHOPIFY_STORE')
    token = os.getenv('SHOPIFY_ADMIN_TOKEN')
    if not store or not token:
        logger.error(
            'Missing creds. Set SHOPIFY_STORE and SHOPIFY_ADMIN_TOKEN in .env '
            '(gitignored) and re-run. Prereq: create a custom app on the store '
            'with read_products scope, install it, copy the Admin API token.')
        sys.exit(2)

    logger.info('Store: %s', store)
    logger.info('Negotiating API version...')
    version, first_page = negotiate_version(store, token)

    logger.info('Paginating products...')
    products = fetch_all(store, token, version, first_page)

    logger.info('\n%-16s %-40s %-16s %s', 'id', 'title', 'productType', 'category.fullName')
    logger.info('-' * 100)
    with_cat = 0
    sample_node = None
    for p in products:
        pid = gid_to_int(p['id'])
        cat = p.get('category')
        full = cat.get('fullName') if cat else None
        if cat:
            with_cat += 1
            if sample_node is None:
                sample_node = cat
        logger.info('%-16s %-40.40s %-16.16s %s',
                    pid, p.get('title') or '', p.get('productType') or '', full or 'NULL')

    logger.info('\nSUMMARY: %d / %d products have a non-null category', with_cat, len(products))
    if sample_node is not None:
        logger.info('\nExact JSON shape of one category node:\n%s',
                    json.dumps(sample_node, indent=2))
    else:
        logger.info('\nNo product returned a non-null category. NULL != broken — it means '
                    'no category is assigned in the admin. Assign one to >=2 products and re-run.')

    logger.info('\nWriting category columns to client_azure_co.shopify_products...')
    upsert_categories(products)
    logger.info('Done.')


if __name__ == '__main__':
    main()
