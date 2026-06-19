"""Confirm a 'Uncategorized' product's category via API, then introspect the
Product type for any field that could carry a category *suggestion*.

Reads creds from env only (SHOPIFY_ADMIN_TOKEN, SHOPIFY_STORE).
"""
import os
import re
import sys
import json

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

VERSION = '2026-04'
PRODUCT_GID = 'gid://shopify/Product/7698712789088'  # CONVERSE | CHUCK TAYLOR ALL STAR LO
PATTERN = re.compile(r'suggest|recommend|categor|taxonom', re.I)

PRODUCT_QUERY = """
query($id: ID!) {
  product(id: $id) {
    id
    title
    productType
    category { id fullName name level isLeaf }
  }
}
"""

# Introspect Product fields, including nested object field names one level deep,
# so a suggestion living on a sub-object (e.g. productCategory { ... }) is caught.
INTROSPECT = """
query {
  __type(name: "Product") {
    fields {
      name
      description
      type { name kind ofType { name kind ofType { name kind } } }
    }
  }
}
"""


def post(store, token, query, variables=None):
    url = f'https://{store}/admin/api/{VERSION}/graphql.json'
    headers = {'X-Shopify-Access-Token': token, 'Content-Type': 'application/json'}
    resp = requests.post(url, headers=headers,
                         json={'query': query, 'variables': variables or {}}, timeout=30)
    resp.raise_for_status()
    body = resp.json()
    if body.get('errors'):
        print('GraphQL errors:', json.dumps(body['errors'], indent=2))
    return body.get('data')


def unwrap(t):
    """Flatten a possibly-wrapped type ref to its underlying name."""
    while t and t.get('name') is None and t.get('ofType'):
        t = t['ofType']
    return (t or {}).get('name')


def main():
    store, token = os.getenv('SHOPIFY_STORE'), os.getenv('SHOPIFY_ADMIN_TOKEN')
    if not store or not token:
        print('Missing SHOPIFY_STORE / SHOPIFY_ADMIN_TOKEN in .env')
        sys.exit(2)

    print('=' * 70)
    print('1. Direct category query for', PRODUCT_GID)
    print('=' * 70)
    data = post(store, token, PRODUCT_QUERY, {'id': PRODUCT_GID})
    prod = (data or {}).get('product')
    print(json.dumps(prod, indent=2))
    cat = (prod or {}).get('category') or {}
    print(f"\n  -> category.fullName = {cat.get('fullName')!r}")

    print('\n' + '=' * 70)
    print('2. Product type introspection — fields matching '
          'suggest|recommend|categor|taxonom')
    print('=' * 70)
    data = post(store, token, INTROSPECT)
    fields = ((data or {}).get('__type') or {}).get('fields') or []
    print(f'  (Product exposes {len(fields)} fields total)')
    hits = [f for f in fields if PATTERN.search(f['name'])]
    if not hits:
        print('  NO fields match the pattern.')
    for f in hits:
        tn = unwrap(f['type'])
        desc = (f.get('description') or '').replace('\n', ' ')[:90]
        print(f"  - {f['name']:<24} : {tn:<22} {desc}")


if __name__ == '__main__':
    main()
