"""
Profit Sentinel — SKU Cost Master Seed Script
Brand: Azure & Co (client_azure_co)
Archetype: Premium Contemporary Womenswear, $150 AOV, $2M–$10M GMV

SOLE WRITER of client_azure_co.sku_cost_master — both record_types (sku_cogs and
influencer_gifting_package). seed_shopify.py no longer writes this table.

Cost universe is READ from the catalog, never re-authored: load_canonical_skus()
pulls the 125 AZ- style SKUs from shopify_product_variants, so cost cannot drift
from the catalog SKU contract.

sku_cogs rows:
  One row PER STYLE = 125 rows (per-style grain, not per-size; no hero/STD tier).
  Cost is price-derived from each style's catalog price:
    supplier_cost = price / 1.28 / uniform(2.2, 3.0)
    landed_cost   = supplier_cost * 1.28
  landed_cost_source = 'derived'; effective_to = NULL (single active row per style).

influencer_gifting_package rows:
  8 rows — synthetic influencer gifting packages across the seed window.

Category columns are NOT written here — category_inference.py is the sole writer
(OP-1, post-seed).

validate() asserts: 125 sku_cogs / 125 active / 0 orphans / 0 uncovered.
"""

import logging
import os
from datetime import date, timedelta

import numpy as np
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s')
logger = logging.getLogger(__name__)

CLIENT_ID = 'client_azure_co'
SCHEMA    = 'client_azure_co'

SEED_END         = date.today()
SEED_START       = date(SEED_END.year - 2, SEED_END.month, SEED_END.day)
STEP_CHANGE_FROM = date(2025, 9, 1)
STEP_CHANGE_TO   = date(2025, 8, 31)   # effective_to for the old row

RNG = np.random.default_rng(42)

SIZES_5 = ['XS', 'S', 'M', 'L', 'XL']
SIZES_4 = ['XS', 'S', 'M', 'L']


# ─── SKU universe ─────────────────────────────────────────────────────────────

def load_canonical_skus(cur):
    """Single source of truth for the cost universe: the synthetic catalog itself.
    Cost cannot drift from catalog because it READS catalog, never re-authors it.
    Per-style grain (price uniform across sizes — verified). Fails loud if the
    catalog is absent, since no orchestrator guarantees seed_shopify ran first."""
    cur.execute('''
        SELECT sku, MIN(id) AS representative_variant_id, MIN(price) AS price
        FROM client_azure_co.shopify_product_variants
        WHERE sku ~ '^AZ-[A-Z]+-[0-9]{3}$'
        GROUP BY sku ORDER BY sku
    ''')
    rows = cur.fetchall()
    if not rows:
        raise RuntimeError(
            "Cost seed found 0 catalog styles in shopify_product_variants. "
            "Run seed_shopify.py FIRST (catalog-before-cost; no orchestrator enforces this).")
    return [(r[0], r[1], float(r[2])) for r in rows]


def _supplier_cost(category: str, is_hero: bool) -> float:
    """Pre-step-change supplier cost."""
    if category == 'DRESS':
        lo, hi = (32.0, 42.0) if is_hero else (22.0, 30.0)
    elif category == 'TOP':
        lo, hi = 12.0, 28.0
    elif category == 'KNIT':
        lo, hi = 28.0, 55.0
    else:                                    # PANT
        lo, hi = 18.0, 38.0
    return round(float(RNG.uniform(lo, hi)), 2)


# ─── Row generators ───────────────────────────────────────────────────────────

def generate_sku_cogs(catalog):
    """One sku_cogs row per catalog style. Cost derived from the style's own price
    (ported from seed_shopify) so per-SKU margin stays realistic; computed ONCE per
    style (fixes old per-size jitter that made distinct-on(sku) nondeterministic)."""
    rows = []
    for sku, representative_variant_id, price in catalog:
        supplier_cost = price / 1.28 / RNG.uniform(2.2, 3.0)
        landed_cost   = supplier_cost * 1.28
        rows.append({
            'client_id':          CLIENT_ID,
            'shopify_variant_id':  str(representative_variant_id),  # real catalog id; NOT NULL; not a join key
            'sku':                 sku,                              # catalog style SKU = join key
            'record_type':        'sku_cogs',
            'supplier_cost':       round(supplier_cost, 2),
            'landed_cost':         round(landed_cost, 2),
            'landed_cost_source': 'derived',                        # all derived (drop 75/25 provenance split)
            'effective_from':      SEED_START,
            'effective_to':        None,                            # single active row per style
            'is_synthetic':        True,
            # Package/influencer columns are NULL for sku_cogs (only gifting rows use them) —
            #   present here because INSERT_SQL binds them by name (execute_batch needs every key).
            'influencer_id':           None,
            'package_landed_cost':     None,
            'packaging_cost':          None,
            'shipping_cost':           None,
            'total_package_cost':      None,
            'featured_item_sku':       None,
            'non_featured_item_skus':  None,
            # category_* columns NOT set here — category_inference.py is the SOLE writer (OP-1, post-seed).
        })
    return rows


def generate_gifting_packages(skus: list, current_landed: dict) -> list[dict]:
    """8 influencer gifting packages distributed across the seed window."""
    dress_top = [s for s, cat, _ in skus if cat in ('DRESS', 'TOP')]
    all_skus  = [s for s, _, _ in skus]

    campaign_starts = [
        date(2024, 6, 15), date(2024, 8, 20), date(2024, 10, 10),
        date(2025, 1, 15), date(2025, 3, 20), date(2025, 6, 10),
        date(2025, 9, 15), date(2025, 11, 20),
    ]

    rows: list[dict] = []
    for i, start in enumerate(campaign_starts):
        inf_id   = f'INF_{i + 1:03d}'
        duration = int(RNG.integers(14, 22))
        end_date = start + timedelta(days=duration)

        featured = dress_top[int(RNG.integers(0, len(dress_top)))]

        non_feat: list[str] = []
        n_extra = int(RNG.integers(2, 4))
        attempts = 0
        while len(non_feat) < n_extra and attempts < 200:
            candidate = all_skus[int(RNG.integers(0, len(all_skus)))]
            if candidate != featured and candidate not in non_feat:
                non_feat.append(candidate)
            attempts += 1

        packaging = round(float(RNG.uniform(8.0, 12.0)), 2)
        shipping  = round(float(RNG.uniform(18.0, 25.0)), 2)
        pkg_landed = round(
            sum(current_landed.get(s, 25.0) for s in [featured] + non_feat), 2
        )
        total_pkg  = round(pkg_landed + packaging + shipping, 2)

        rows.append(dict(
            client_id=CLIENT_ID,
            shopify_variant_id=f'900000000{i + 1}',
            sku=f'PKG-{inf_id}-GIFT',
            record_type='influencer_gifting_package',
            supplier_cost=pkg_landed,
            landed_cost=pkg_landed,
            landed_cost_source='derived',
            influencer_id=inf_id,
            package_landed_cost=pkg_landed,
            packaging_cost=packaging,
            shipping_cost=shipping,
            total_package_cost=total_pkg,
            featured_item_sku=featured,
            non_featured_item_skus=non_feat,
            effective_from=start,
            effective_to=end_date,
            is_synthetic=True,
        ))

    return rows


# ─── DB helpers ───────────────────────────────────────────────────────────────

def get_conn():
    return psycopg2.connect(os.getenv('DATABASE_URL'), sslmode='require')


INSERT_SQL = f"""
INSERT INTO {SCHEMA}.sku_cost_master
    (client_id, shopify_variant_id, sku, record_type,
     supplier_cost, landed_cost, landed_cost_source,
     influencer_id, package_landed_cost, packaging_cost, shipping_cost,
     total_package_cost, featured_item_sku, non_featured_item_skus,
     effective_from, effective_to, is_synthetic)
VALUES
    (%(client_id)s, %(shopify_variant_id)s, %(sku)s, %(record_type)s,
     %(supplier_cost)s, %(landed_cost)s, %(landed_cost_source)s,
     %(influencer_id)s, %(package_landed_cost)s, %(packaging_cost)s, %(shipping_cost)s,
     %(total_package_cost)s, %(featured_item_sku)s, %(non_featured_item_skus)s,
     %(effective_from)s, %(effective_to)s, %(is_synthetic)s)
"""


def seed(conn):
    with conn:
        cur = conn.cursor()
        # Load the canonical SKU set from the catalog ONCE; pass it to both generators.
        catalog = load_canonical_skus(cur)
        cogs_rows = generate_sku_cogs(catalog)
        # gifting's body is unchanged: it expects (sku, category, is_hero) tuples + a
        # current_landed map. Reshape the catalog to that contract (category parsed from the
        # AZ-{cat}-{NNN} sku; is_hero retired) and derive current_landed from the cogs rows.
        current_landed = {r['sku']: r['landed_cost'] for r in cogs_rows}
        gift_skus = [(sku, sku.split('-')[1], False) for sku, _vid, _price in catalog]
        gift_rows = generate_gifting_packages(gift_skus, current_landed)
        all_rows = cogs_rows + gift_rows

        cur.execute(f"DELETE FROM {SCHEMA}.sku_cost_master WHERE is_synthetic = true")
        logger.info("Cleared existing synthetic rows.")
        psycopg2.extras.execute_batch(cur, INSERT_SQL, all_rows, page_size=500)
        logger.info("Inserted %d rows (%d sku_cogs + %d gifting).",
                    len(all_rows), len(cogs_rows), len(gift_rows))


# ─── Verification ─────────────────────────────────────────────────────────────

def validate(cur):
    failures = []
    cur.execute("SELECT count(*) FROM client_azure_co.sku_cost_master WHERE record_type='sku_cogs'")
    sku_cogs = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM client_azure_co.sku_cost_master WHERE record_type='sku_cogs' AND effective_to IS NULL")
    active = cur.fetchone()[0]
    cur.execute('''
        SELECT
          (SELECT count(*) FROM client_azure_co.sku_cost_master c
             WHERE c.record_type='sku_cogs'
               AND NOT EXISTS (SELECT 1 FROM client_azure_co.shopify_product_variants v WHERE v.sku=c.sku)),
          (SELECT count(DISTINCT v.sku) FROM client_azure_co.shopify_product_variants v
             WHERE v.sku ~ '^AZ-[A-Z]+-[0-9]{3}$'
               AND NOT EXISTS (SELECT 1 FROM client_azure_co.sku_cost_master c WHERE c.sku=v.sku AND c.record_type='sku_cogs'))
    ''')
    cost_orphans, catalog_uncovered = cur.fetchone()
    if sku_cogs != 125:    failures.append(f"sku_cogs={sku_cogs}, expected 125")
    if active   != 125:    failures.append(f"active sku_cogs={active}, expected 125")
    if cost_orphans:       failures.append(f"{cost_orphans} sku_cogs rows not in catalog")
    if catalog_uncovered:  failures.append(f"{catalog_uncovered} catalog styles have no cost row")
    print("PASS" if not failures else "FAIL — " + "; ".join(failures))
    return not failures


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    conn = get_conn()
    try:
        seed(conn)
        print("\n=== VALIDATION ===")
        validate(conn.cursor())
        print("\n=== B-8 COMPLETE ===")
    except Exception:
        logger.exception("Seed failed")
        raise
    finally:
        conn.close()
