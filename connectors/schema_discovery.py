"""
connectors/schema_discovery.py

Runs after every Airbyte sync. Reads actual column types from
information_schema, diffs against source_schema_registry, and writes
new / changed / removed columns. Logs all schema drift to schema_versions
so Agent A can suppress false alerts during transitions.

Usage:
    python connectors/schema_discovery.py
    (defaults to client_id='azure_co', table='shopify_orders')

Rules observed:
    RULE 1  — discovery before transformation
    RULE 2  — schema-qualified queries (client_{client_id})
    RULE 5  — structured error logging with SOURCE field
    RULE 9  — caller must update technical_architecture.md after Step 2
"""

import logging
import os
import sys
import time

import psycopg2
from dotenv import load_dotenv

_ROOT = os.path.join(os.path.dirname(__file__), '..')
load_dotenv(os.path.join(_ROOT, '.env'))

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Inference helpers
# ---------------------------------------------------------------------------

# Ordered pattern lists — first match wins within each rule tier.
_JSONB_TEXT_PATTERNS = [
    'price_set', 'money', 'client_details',
    'billing_address', 'shipping_address',
    'payment_gateway_names', 'line_items',
    'tax_lines', 'discount_codes', 'fulfillments',
    'note_attributes', 'refund_line_items',
]
_NUMERIC_PATTERNS = [
    'price', 'amount', 'total', 'discount',
    'tax', 'shipping', 'subtotal', 'cost',
    'revenue', 'refund', 'fee',
]
_TIMESTAMP_PATTERNS = [
    '_at', '_date', 'date', 'time',
    'processed', 'created', 'updated',
    'cancelled', 'closed',
]

_TYPE_MAP = {
    'text': 'text',
    'bigint': 'bigint',
    'integer': 'bigint',
    'numeric': 'numeric',
    'boolean': 'boolean',
    'jsonb': 'jsonb',
    'json': 'jsonb',
    'timestamp with time zone': 'timestamptz',
    'timestamp without time zone': 'timestamptz',
    'date': 'date',
    'character varying': 'text',
}


def infer_transformation(column_name: str, data_type: str) -> str:
    """
    Returns the transformation string for a column.
    Rules applied in priority order — first match wins.

    Returns one of:
        'none' | 'cast_text_to_numeric' | 'cast_text_to_timestamp' |
        'jsonb_extract' | 'jsonb_extract_from_text'
    """
    # Rule a — native jsonb / json: pass through unchanged
    if data_type in ('jsonb', 'json'):
        return 'jsonb_extract'

    # Airbyte sometimes uses 'character varying' where we'd expect 'text'.
    # Normalise so pattern rules b–d apply uniformly to both string types.
    effective_type = 'text' if data_type in ('text', 'character varying') else data_type

    # Rule b — known JSONB-stored-as-text columns
    if effective_type == 'text' and any(p in column_name for p in _JSONB_TEXT_PATTERNS):
        return 'jsonb_extract_from_text'

    # Rule c — numeric values stored as text
    if effective_type == 'text' and any(p in column_name for p in _NUMERIC_PATTERNS):
        return 'cast_text_to_numeric'

    # Rule d — timestamps stored as text
    if effective_type == 'text' and any(p in column_name for p in _TIMESTAMP_PATTERNS):
        return 'cast_text_to_timestamp'

    return 'none'


def infer_target_type(data_type: str, transformation: str) -> str:
    """Maps raw postgres type + transformation to the desired target type."""
    if transformation == 'cast_text_to_numeric':
        return 'numeric'
    if transformation == 'cast_text_to_timestamp':
        return 'timestamptz'
    if transformation in ('jsonb_extract', 'jsonb_extract_from_text'):
        return 'jsonb'
    return _TYPE_MAP.get(data_type, 'text')


# ---------------------------------------------------------------------------
# Main discovery function
# ---------------------------------------------------------------------------

def discover_and_update_schema(
    client_id: str,
    table_name: str,
    source_name: str,
    conn,
) -> dict:
    """
    Compares information_schema against source_schema_registry.
    Inserts new columns, records type changes, marks removed columns.
    All schema drift is written to schema_versions.

    Args:
        client_id   : e.g. 'azure_co'  (schema = client_{client_id})
        table_name  : e.g. 'shopify_orders'
        source_name : e.g. 'shopify'
        conn        : open psycopg2 connection

    Returns:
        dict with keys: found, new, changed, removed, errors
    """
    schema_name = f'client_{client_id}'
    summary = {
        'found': 0,
        'new': 0,
        'changed': 0,
        'removed': 0,
        'errors': [],
    }

    try:
        cur = conn.cursor()

        # ------------------------------------------------------------------
        # Step 1 — read actual schema from information_schema
        # ------------------------------------------------------------------
        cur.execute(
            """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = %s
              AND table_name   = %s
            ORDER BY ordinal_position
            """,
            (schema_name, table_name),
        )
        rows = cur.fetchall()
        current_schema = {
            row[0]: {
                'data_type':   row[1],
                'is_nullable': (row[2] == 'YES'),
            }
            for row in rows
        }
        summary['found'] = len(current_schema)

        if not current_schema:
            logger.error(
                "SOURCE: Airbyte Schema Discovery | CLIENT: %s | "
                "ERROR: No columns found in information_schema | "
                "CONTEXT: %s",
                client_id,
                {'schema': schema_name, 'table': table_name},
            )
            return summary

        # ------------------------------------------------------------------
        # Step 2 — read registered schema (type + current transformation)
        # ------------------------------------------------------------------
        cur.execute(
            """
            SELECT column_name, raw_data_type, transformation
            FROM public.source_schema_registry
            WHERE client_id  = %s
              AND table_name = %s
            """,
            (client_id, table_name),
        )
        raw = cur.fetchall()
        registered_schema       = {row[0]: row[1] for row in raw}
        registered_transform    = {row[0]: row[2] for row in raw}

        # ------------------------------------------------------------------
        # Step 3 — process columns present in information_schema
        # ------------------------------------------------------------------
        batch_count = 0

        for col_name, col_info in current_schema.items():
            data_type   = col_info['data_type']
            is_nullable = col_info['is_nullable']

            try:
                transformation = infer_transformation(col_name, data_type)
                target_type    = infer_target_type(data_type, transformation)

                if col_name not in registered_schema:
                    # New column ——————————————————————————————————————————
                    cur.execute(
                        """
                        INSERT INTO public.source_schema_registry
                            (client_id, source_name, table_name, column_name,
                             raw_data_type, target_data_type, transformation,
                             is_nullable, last_validated)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, now())
                        ON CONFLICT (client_id, table_name, column_name)
                        DO UPDATE SET
                            raw_data_type    = EXCLUDED.raw_data_type,
                            target_data_type = EXCLUDED.target_data_type,
                            transformation   = EXCLUDED.transformation,
                            is_nullable      = EXCLUDED.is_nullable,
                            is_removed       = false,
                            last_validated   = now()
                        """,
                        (client_id, source_name, table_name, col_name,
                         data_type, target_type, transformation, is_nullable),
                    )
                    cur.execute(
                        """
                        INSERT INTO public.schema_versions
                            (client_id, table_name, column_name,
                             old_type, new_type, change_type, detected_at)
                        VALUES (%s, %s, %s, NULL, %s, 'new_column', now())
                        """,
                        (client_id, table_name, col_name, data_type),
                    )
                    summary['new'] += 1

                elif registered_schema[col_name] != data_type:
                    # Type changed ————————————————————————————————————————
                    old_type = registered_schema[col_name]
                    cur.execute(
                        """
                        UPDATE public.source_schema_registry
                        SET raw_data_type    = %s,
                            target_data_type = %s,
                            transformation   = %s,
                            last_validated   = now()
                        WHERE client_id  = %s
                          AND table_name = %s
                          AND column_name = %s
                        """,
                        (data_type, target_type, transformation,
                         client_id, table_name, col_name),
                    )
                    cur.execute(
                        """
                        INSERT INTO public.schema_versions
                            (client_id, table_name, column_name,
                             old_type, new_type, change_type, detected_at)
                        VALUES (%s, %s, %s, %s, %s, 'type_changed', now())
                        """,
                        (client_id, table_name, col_name, old_type, data_type),
                    )
                    summary['changed'] += 1
                    logger.warning(
                        "SOURCE: Airbyte Schema Discovery | CLIENT: %s | "
                        "SCHEMA DRIFT: %s.%s changed %s → %s | "
                        "CONTEXT: %s",
                        client_id, table_name, col_name, old_type, data_type,
                        {'transformation': transformation},
                    )

                else:
                    # Raw type unchanged — but re-apply inference in case
                    # infer_transformation rules changed (e.g. adding
                    # 'character varying' normalisation).
                    prev_transform = registered_transform.get(col_name, '')
                    if prev_transform != transformation:
                        # Transformation logic updated — write new values
                        cur.execute(
                            """
                            UPDATE public.source_schema_registry
                            SET target_data_type = %s,
                                transformation   = %s,
                                last_validated   = now()
                            WHERE client_id   = %s
                              AND table_name  = %s
                              AND column_name = %s
                            """,
                            (target_type, transformation,
                             client_id, table_name, col_name),
                        )
                        summary['changed'] += 1
                        logger.info(
                            "SOURCE: Airbyte Schema Discovery | CLIENT: %s | "
                            "TRANSFORM UPDATE: %s.%s: '%s' -> '%s'",
                            client_id, table_name, col_name,
                            prev_transform, transformation,
                        )
                    else:
                        # Truly no change — refresh last_validated only
                        cur.execute(
                            """
                            UPDATE public.source_schema_registry
                            SET last_validated = now(),
                                is_removed     = false
                            WHERE client_id   = %s
                              AND table_name  = %s
                              AND column_name = %s
                            """,
                            (client_id, table_name, col_name),
                        )

            except Exception as exc:
                summary['errors'].append(
                    {'column': col_name, 'error': str(exc)}
                )
                logger.error(
                    "SOURCE: Airbyte Schema Discovery | CLIENT: %s | "
                    "ERROR: %s | CONTEXT: %s",
                    client_id, str(exc),
                    {'table': table_name, 'column': col_name,
                     'data_type': data_type},
                )
                # Rollback the failed statement so the batch stays consistent,
                # then continue with the next column.
                conn.rollback()
                batch_count = 0  # reset batch counter after rollback
                continue

            batch_count += 1
            if batch_count % 50 == 0:
                conn.commit()
                logger.info(
                    "SOURCE: Airbyte Schema Discovery | CLIENT: %s | "
                    "INFO: Committed batch of 50 columns (table: %s)",
                    client_id, table_name,
                )

        # ------------------------------------------------------------------
        # Step 4 — mark columns removed from source
        # ------------------------------------------------------------------
        for col_name in registered_schema:
            if col_name not in current_schema:
                try:
                    cur.execute(
                        """
                        UPDATE public.source_schema_registry
                        SET is_removed     = true,
                            last_validated = now()
                        WHERE client_id   = %s
                          AND table_name  = %s
                          AND column_name = %s
                        """,
                        (client_id, table_name, col_name),
                    )
                    cur.execute(
                        """
                        INSERT INTO public.schema_versions
                            (client_id, table_name, column_name,
                             old_type, new_type, change_type, detected_at)
                        VALUES (%s, %s, %s, %s, NULL, 'column_removed', now())
                        """,
                        (client_id, table_name, col_name,
                         registered_schema[col_name]),
                    )
                    summary['removed'] += 1
                    logger.warning(
                        "SOURCE: Airbyte Schema Discovery | CLIENT: %s | "
                        "COLUMN REMOVED: %s.%s | CONTEXT: %s",
                        client_id, table_name, col_name,
                        {'old_type': registered_schema[col_name]},
                    )
                except Exception as exc:
                    summary['errors'].append(
                        {'column': col_name, 'error': str(exc)}
                    )
                    logger.error(
                        "SOURCE: Airbyte Schema Discovery | CLIENT: %s | "
                        "ERROR: %s | CONTEXT: %s",
                        client_id, str(exc),
                        {'table': table_name, 'column': col_name,
                         'action': 'mark_removed'},
                    )
                    conn.rollback()

        conn.commit()

    except Exception as exc:
        logger.error(
            "SOURCE: Airbyte Schema Discovery | CLIENT: %s | "
            "ERROR: %s | CONTEXT: %s",
            client_id, str(exc),
            {'table': table_name, 'source_name': source_name},
        )
        try:
            conn.rollback()
        except Exception:
            pass
        summary['errors'].append({'column': 'N/A', 'error': str(exc)})

    return summary


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s  %(levelname)-8s  %(message)s',
    )

    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print('ERROR: DATABASE_URL not found in .env')
        sys.exit(1)

    conn = psycopg2.connect(database_url, sslmode='require')

    try:
        t0 = time.time()
        result = discover_and_update_schema(
            client_id='azure_co',
            table_name='shopify_orders',
            source_name='shopify',
            conn=conn,
        )
        elapsed = time.time() - t0

        print()
        print('-' * 52)
        print('  Schema Discovery -- shopify_orders')
        print('-' * 52)
        print(f'  Columns found in information_schema : {result["found"]}')
        print(f'  New columns registered              : {result["new"]}')
        print(f'  Type changes detected               : {result["changed"]}')
        print(f'  Columns marked removed              : {result["removed"]}')
        print(f'  Errors                              : {len(result["errors"])}')
        if result['errors']:
            for err in result['errors']:
                print(f'    ERR {err["column"]}: {err["error"]}')
        print(f'  Time taken                          : {elapsed:.2f}s')
        print('-' * 52)
    finally:
        conn.close()
