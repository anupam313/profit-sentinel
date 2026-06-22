"""connectors/category_inference.py — Agent D category resolution + provenance stamp + taxonomy drift.

Resolves every SKU in client_azure_co.sku_cost_master to a node of the Shopify Standard
Product Taxonomy PINNED to PINNED_TAXONOMY_VERSION (read from taxonomy_config — the single
home for the version literal), then stamps the resolved node and its provenance.

Resolution order, per SKU (Step 0 = the Shopify-assigned category enrichment that
_category_graphql_probe.py lands on client_azure_co.shopify_products):
  1. Step 0 present AND resolves in the pinned list  → use it; category_source='shopify_assigned'.
  2. Step 0 present but does NOT resolve in pinned list → raise the H21 taxonomy-drift signal
     (D), then LLM-snap to a pinned node; category_source='ai_inferred'.
  3. No Step 0 but product text available → LLM-snap to a pinned node; category_source='ai_inferred'.
  4. No Step 0 AND thin/absent product text → cannot place: hold at the AL-19 brand-level-with-
     disclosure floor (LOCKED DECISION: keep such SKUs at brand level WITH disclosure, never
     silently drop — rationale: reconciliation with the founder's own Shopify totals + unbiased
     baselines). category_source='brand_level_floor'.

Every SKU is stamped with taxonomy_version = PINNED_TAXONOMY_VERSION and
category_grouping_key = the resolved node id at the AL-19 firing depth. Day-one the AL-19
firing depth IS the resolved node, so category_grouping_key == category_id for every placed
SKU (and == BRAND_LEVEL_FLOORING_KEY for case 4). category_grouping_key is the field
category-level aggregations will bind to; rebinding marts/D1 from category_id to
category_grouping_key is the NEXT build item and is explicitly OUT OF SCOPE here.

Schema (Step B): ensure_schema() applies the additive ALTER (ADD COLUMN IF NOT EXISTS) to
client_azure_co.sku_cost_master — the columns are net-new (verified absent live). DDL is
applied via this connector's own pattern, mirroring _category_graphql_probe.py; there is no
migrations runner and none is introduced.

Trigger model (unchanged): onboarding backfill over ACTIVE and INACTIVE SKUs, and ongoing on
new/changed SKUs.

Agent boundary: this is Agent D work, so the LLM snap (Agents B/C/D) is permitted. Agent A
(threshold scanning) never calls the Claude API — this module is not Agent A.
"""

import json
import logging
import os
import sys

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from taxonomy_config import (  # noqa: E402  (single home for the version pin + pinned list)
    PINNED_TAXONOMY_VERSION,
    full_name_for,
    load_pinned_taxonomy,
    resolves,
)

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s')
logger = logging.getLogger(__name__)

SCHEMA = 'client_azure_co'

# Upstream "unassigned" sentinel on shopify_products.category_id — NOT drift, just "no Step 0".
UNASSIGNED_SENTINEL = 'gid://shopify/TaxonomyCategory/na'

# category_grouping_key value for case 4 (cannot place): hold at brand level WITH disclosure,
# never NULL — a NULL key would let a SKU fall out of category-level aggregation entirely,
# which the LOCKED decision forbids. A constant key keeps these SKUs grouped at brand level.
BRAND_LEVEL_FLOORING_KEY = 'brand-level'

# H-series data-integrity code for taxonomy drift — assigned as the NEXT AVAILABLE H-code by
# reading the live alert roster (H1..H20 in use; H20 = New SKU COGS Gap in technical_architecture.md).
# Do NOT renumber; do NOT reuse a locked A–H code.
DRIFT_ALERT_CODE = 'H21'

# Default model for the category snap (constrained classification). Per the Claude API
# reference the default is Opus 4.8; override via env without code change.
CATEGORY_SNAP_MODEL = os.getenv('CATEGORY_SNAP_MODEL', 'claude-opus-4-8')

# Minimum meaningful product-text length before we will attempt an LLM snap (case 3 vs case 4).
_MIN_TEXT_CHARS = 3


def get_connection():
    """Open a psycopg2 connection using the connectors' standard env var. Caller closes."""
    return psycopg2.connect(os.getenv('DATABASE_URL'), sslmode='require')


# ── Step B — additive schema (ADD COLUMN IF NOT EXISTS) ───────────────────────
def ensure_schema(conn) -> None:
    """Apply the additive category columns to client_azure_co.sku_cost_master.

    All six are net-new (verified absent live). Idempotent via ADD COLUMN IF NOT EXISTS, so
    repeat runs and re-onboards never double-apply. Semantics mirror technical_architecture.md's
    OP-1 ALTER block (correct in intent; this build is what actually creates the columns, and it
    targets client_azure_co — there is no public.sku_cost_master).
    """
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    ALTER TABLE {SCHEMA}.sku_cost_master
                        ADD COLUMN IF NOT EXISTS category_id                   text,
                        ADD COLUMN IF NOT EXISTS category_full_name            text,
                        ADD COLUMN IF NOT EXISTS category_inference_confidence numeric,
                        ADD COLUMN IF NOT EXISTS category_source               text,
                        ADD COLUMN IF NOT EXISTS taxonomy_version              text,
                        ADD COLUMN IF NOT EXISTS category_grouping_key         text;
                    """
                )
        logger.info(
            "SOURCE: Category Inference | INFO: ensured 6 additive columns on %s.sku_cost_master",
            SCHEMA,
        )
    except psycopg2.Error as e:
        logger.error(
            "SOURCE: Category Inference | CLIENT: %s | ERROR: %s | "
            "CONTEXT: ensure_schema ALTER on %s.sku_cost_master",
            'client_azure_co', str(e), SCHEMA,
        )
        raise


def grouping_key_for(category_id: str | None) -> str:
    """The category_grouping_key for a resolved node id.

    Day-one the AL-19 firing depth equals the resolved node, so the grouping key IS the
    resolved category_id. When firing depth later diverges from grouping depth, this is the
    one place that changes — callers never recompute the key inline.
    """
    return category_id if category_id else BRAND_LEVEL_FLOORING_KEY


# ── Step C — LLM snap (cases 2 and 3) ─────────────────────────────────────────
_SNAP_SCHEMA = {
    "type": "object",
    "properties": {
        "node_full_name": {
            "type": "string",
            "description": "The single best-matching Shopify Standard Product Taxonomy node, "
                           "given EXACTLY as its full breadcrumb path (e.g. "
                           "'Apparel & Accessories > Clothing > Dresses'). Must be a real node "
                           "in the supplied pinned taxonomy version.",
        },
        "confidence": {
            "type": "number",
            "description": "Cross-signal agreement 0.0–1.0 that this node is correct.",
        },
    },
    "required": ["node_full_name", "confidence"],
    "additionalProperties": False,
}


def _llm_snap(product_text: str, name_index: dict[str, str]) -> tuple[str | None, float | None, str | None]:
    """Snap free product text to a pinned-taxonomy node via the Claude API.

    Returns (category_id, confidence, full_name), or (None, None, None) if the SDK is
    unavailable, the API errors/rate-limits, or the model's node does not resolve in the pinned
    list. `name_index` maps full_name -> id for the pinned version (the validation surface — the
    model's answer is accepted ONLY if it names a real pinned node, never free text).

    NOTE: this is the single-pass snap. The deepest-agreement, signal-weighted node mapping
    (description STRONG > tags > title/product_type weak; tag at the deepest concurring level)
    is the documented-unbuilt algorithm and plugs in here; this build does not invent it.
    """
    try:
        import anthropic  # lazy: non-LLM paths (shopify_assigned, floor) must work without the SDK
    except ImportError:
        logger.error(
            "SOURCE: Category Inference | ERROR: anthropic SDK not installed | "
            "CONTEXT: cannot LLM-snap; install `anthropic` to enable cases 2/3"
        )
        return (None, None, None)

    try:
        client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
        response = client.messages.create(
            model=CATEGORY_SNAP_MODEL,
            max_tokens=512,
            system=(
                "You classify e-commerce products into the Shopify Standard Product Taxonomy, "
                f"version {PINNED_TAXONOMY_VERSION}. Choose the single most specific node that "
                "the product text confidently supports. Return the node as its exact full "
                "breadcrumb path. Never invent a node or category name."
            ),
            output_config={"format": {"type": "json_schema", "schema": _SNAP_SCHEMA}},
            messages=[{"role": "user", "content": f"Product:\n{product_text}"}],
        )
        if response.stop_reason == "refusal":
            logger.error(
                "SOURCE: Category Inference | ERROR: snap refused | CONTEXT: stop_reason=refusal"
            )
            return (None, None, None)
        text = next((b.text for b in response.content if b.type == "text"), "")
        parsed = json.loads(text)
        full_name = parsed.get("node_full_name", "")
        confidence = parsed.get("confidence")
        node_id = name_index.get(full_name)
        if node_id is None:
            logger.error(
                "SOURCE: Category Inference | ERROR: snapped node not in pinned list | "
                "CONTEXT: node='%s' version=%s", full_name, PINNED_TAXONOMY_VERSION,
            )
            return (None, None, None)
        return (node_id, confidence, full_name)
    except (anthropic.APIError, ValueError, KeyError) as e:
        # Rate limits / timeouts / 5xx are auto-retried by the SDK; a final failure or a bad
        # payload degrades to "no snap" so the backfill keeps going rather than crashing.
        logger.error(
            "SOURCE: Category Inference | ERROR: %s | CONTEXT: LLM snap failed; returning no-snap",
            str(e),
        )
        return (None, None, None)


# ── Step D — taxonomy-drift system signal (H21) ───────────────────────────────
def raise_drift_signal(conn, client_id: str, unresolved: list[dict], signal_date) -> None:
    """Write one H21 data-integrity alert naming the exact drifted SKUs.

    `unresolved` is a list of {sku, category_id} whose stored/Shopify-assigned code did NOT
    resolve in the pinned list. Deduped on (client_id, alert_type, signal_date) like Agent A so
    a re-run of the same backfill does not double-fire. Confidence is near-certain (H-series are
    not threshold-based). The exact SKUs live in evidence_stack_json (Layer-0 evidence).
    """
    if not unresolved:
        return
    skus = [u['sku'] for u in unresolved]
    headline = (
        f"{len(unresolved)} SKU(s) carry a Shopify-assigned category code that does not resolve "
        f"in the pinned taxonomy {PINNED_TAXONOMY_VERSION}: {', '.join(skus[:10])}"
        + ("…" if len(skus) > 10 else "")
    )
    evidence = {
        "pinned_taxonomy_version": PINNED_TAXONOMY_VERSION,
        "unresolved": unresolved,
        "remediation": "version->version remap (deferred) or re-pin; see technical_architecture.md",
    }
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id FROM public.alert_log
                    WHERE client_id = %s AND alert_type = %s AND signal_date = %s
                    LIMIT 1
                    """,
                    (client_id, DRIFT_ALERT_CODE, signal_date),
                )
                if cur.fetchone():
                    logger.info(
                        "SOURCE: Category Inference | CLIENT: %s | INFO: %s duplicate skipped on %s",
                        client_id, DRIFT_ALERT_CODE, signal_date,
                    )
                    return
                cur.execute(
                    """
                    INSERT INTO public.alert_log (
                        client_id, alert_type, signal_source, confidence_score,
                        evidence_stack_json, layer1_headline, layer2_context,
                        severity, signal_date, should_fire, is_synthetic, fired_at
                    ) VALUES (
                        %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s, true, false, now()
                    )
                    """,
                    (
                        client_id,
                        DRIFT_ALERT_CODE,
                        'Category Inference Taxonomy Drift',
                        1.0,
                        json.dumps(evidence),
                        headline,
                        "A pinned-list resolution miss means a release re-id/merge/split/retire, "
                        "or a stale baked code. These SKUs are LLM-re-snapped to a pinned node so "
                        "grouping proceeds; the drift is surfaced for deliberate remap.",
                        'data_integrity',
                        signal_date,
                    ),
                )
        logger.info(
            "SOURCE: Category Inference | CLIENT: %s | INFO: raised %s for %d SKU(s)",
            client_id, DRIFT_ALERT_CODE, len(unresolved),
        )
    except psycopg2.Error as e:
        logger.error(
            "SOURCE: Category Inference | CLIENT: %s | ERROR: %s | CONTEXT: raise_drift_signal %s",
            client_id, str(e), DRIFT_ALERT_CODE,
        )


# ── Resolution per SKU ────────────────────────────────────────────────────────
def _product_text(row: dict) -> str:
    """Concatenate the available product-text signals for an LLM snap."""
    parts = [row.get('title'), row.get('product_type'), row.get('description')]
    return ' | '.join(p.strip() for p in parts if p and p.strip())


def resolve_one(row: dict, name_index: dict[str, str], *, allow_llm: bool = True) -> dict:
    """Resolve a single joined SKU row to the stamp dict, plus a drift flag.

    Returns a dict with the six column values and a private `_drift` entry ({sku, category_id})
    when Step 0 was present-but-unresolved (so the caller can batch the H21 signal). `allow_llm`
    can be turned off for deterministic (no-API) backfills — cases 2/3 then fall through to the
    brand-level floor rather than snapping, and the drift is still recorded for case 2.
    """
    step0 = row.get('step0_category_id')
    has_step0 = bool(step0) and step0 != UNASSIGNED_SENTINEL
    text = _product_text(row)

    stamp = {
        'category_id': None,
        'category_full_name': None,
        'category_inference_confidence': None,
        'category_source': None,
        'taxonomy_version': PINNED_TAXONOMY_VERSION,
        'category_grouping_key': None,
        '_drift': None,
    }

    # Case 1 — Shopify-assigned and resolves in the pinned list.
    if has_step0 and resolves(step0):
        stamp['category_id'] = step0
        stamp['category_full_name'] = full_name_for(step0)  # authoritative pinned breadcrumb
        stamp['category_source'] = 'shopify_assigned'
        # category_inference_confidence stays NULL for shopify_assigned (OP-1 semantics).
        stamp['category_grouping_key'] = grouping_key_for(step0)
        return stamp

    # Case 2 — Shopify-assigned but does NOT resolve → drift, then re-snap.
    if has_step0 and not resolves(step0):
        stamp['_drift'] = {'sku': row.get('sku'), 'category_id': step0}
        if allow_llm and len(text) >= _MIN_TEXT_CHARS:
            node_id, conf, fname = _llm_snap(text, name_index)
            if node_id:
                stamp.update(
                    category_id=node_id, category_full_name=fname,
                    category_inference_confidence=conf, category_source='ai_inferred',
                    category_grouping_key=grouping_key_for(node_id),
                )
                return stamp
        # No usable snap → hold at the brand-level floor (never silently drop).
        stamp['category_source'] = 'brand_level_floor'
        stamp['category_grouping_key'] = BRAND_LEVEL_FLOORING_KEY
        return stamp

    # Case 3 — no Step 0 but product text available → LLM snap.
    if allow_llm and len(text) >= _MIN_TEXT_CHARS:
        node_id, conf, fname = _llm_snap(text, name_index)
        if node_id:
            stamp.update(
                category_id=node_id, category_full_name=fname,
                category_inference_confidence=conf, category_source='ai_inferred',
                category_grouping_key=grouping_key_for(node_id),
            )
            return stamp

    # Case 4 — no Step 0 AND thin/absent text (or snap unavailable) → brand-level floor.
    stamp['category_source'] = 'brand_level_floor'
    stamp['category_grouping_key'] = BRAND_LEVEL_FLOORING_KEY
    return stamp


# ── Backfill / ongoing entry point ────────────────────────────────────────────
_READ_SQL = f"""
    SELECT scm.id                 AS scm_id,
           scm.client_id          AS client_id,
           scm.sku                AS sku,
           sp.category_id         AS step0_category_id,
           sp.category_full_name  AS step0_full_name,
           sp.title               AS title,
           sp.product_type        AS product_type,
           sp.description         AS description
    FROM {SCHEMA}.sku_cost_master scm
    -- Step-0 category reaches a cost SKU via the catalog: sku_cost_master.sku is the variant
    -- SKU (the same key mart_return_rate_by_sku joins on), variant -> product -> category.
    LEFT JOIN {SCHEMA}.shopify_product_variants v ON v.sku = scm.sku
    LEFT JOIN {SCHEMA}.shopify_products sp        ON sp.id = v.product_id
    {{where}}
    ORDER BY scm.id
"""

_UPDATE_SQL = f"""
    UPDATE {SCHEMA}.sku_cost_master
       SET category_id                   = %(category_id)s,
           category_full_name            = %(category_full_name)s,
           category_inference_confidence = %(category_inference_confidence)s,
           category_source               = %(category_source)s,
           taxonomy_version              = %(taxonomy_version)s,
           category_grouping_key         = %(category_grouping_key)s,
           updated_at                    = now()
     WHERE id = %(scm_id)s
"""


def run(*, allow_llm: bool = True, only_scm_ids: list[int] | None = None) -> dict:
    """Resolve + stamp every SKU (backfill) or a subset (ongoing).

    `allow_llm=False` runs the deterministic paths only (shopify_assigned + brand-level floor),
    which needs no Claude API — used for the no-LLM backfill of Step-0 SKUs and for verification.
    `only_scm_ids` scopes to specific sku_cost_master rows (ongoing on new/changed SKUs).
    Returns a counts summary. NULL/zero-row safe; per-row failures are logged and skipped.
    """
    counts = {'rows': 0, 'shopify_assigned': 0, 'ai_inferred': 0, 'brand_level_floor': 0,
              'drift': 0, 'errors': 0}
    name_index = {meta['full_name']: nid for nid, meta in load_pinned_taxonomy().items()}

    try:
        conn = get_connection()
    except psycopg2.Error as e:
        logger.error(
            "SOURCE: Category Inference | ERROR: %s | CONTEXT: cannot open db connection", str(e)
        )
        return counts

    try:
        ensure_schema(conn)

        where = ""
        params: tuple = ()
        if only_scm_ids:
            where = "WHERE scm.id = ANY(%s)"
            params = (only_scm_ids,)

        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(_READ_SQL.format(where=where), params)
            rows = cur.fetchall()

        if not rows:
            logger.info("SOURCE: Category Inference | INFO: zero SKUs to resolve")
            return counts

        drift_by_client: dict[str, list[dict]] = {}
        signal_date = None
        with conn.cursor() as cur:
            cur.execute("SELECT current_date")
            signal_date = cur.fetchone()[0]

        for row in rows:
            try:
                stamp = resolve_one(dict(row), name_index, allow_llm=allow_llm)
                drift = stamp.pop('_drift', None)
                if drift:
                    drift_by_client.setdefault(row['client_id'], []).append(drift)
                    counts['drift'] += 1
                stamp['scm_id'] = row['scm_id']
                with conn:
                    with conn.cursor() as ucur:
                        ucur.execute(_UPDATE_SQL, stamp)
                counts['rows'] += 1
                counts[stamp['category_source']] = counts.get(stamp['category_source'], 0) + 1
            except psycopg2.Error as e:
                counts['errors'] += 1
                logger.error(
                    "SOURCE: Category Inference | CLIENT: %s | ERROR: %s | CONTEXT: stamp sku=%s",
                    row.get('client_id'), str(e), row.get('sku'),
                )

        for client_id, unresolved in drift_by_client.items():
            raise_drift_signal(conn, client_id, unresolved, signal_date)

        logger.info("SOURCE: Category Inference | INFO: backfill complete | %s", counts)
        return counts
    finally:
        conn.close()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="Resolve + stamp SKU taxonomy categories.")
    parser.add_argument('--no-llm', action='store_true',
                        help="deterministic paths only (shopify_assigned + brand-level floor)")
    parser.add_argument('--scm-id', type=int, action='append',
                        help="restrict to specific sku_cost_master id(s); repeatable")
    args = parser.parse_args()
    run(allow_llm=not args.no_llm, only_scm_ids=args.scm_id)
