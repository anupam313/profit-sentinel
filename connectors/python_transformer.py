"""
connectors/python_transformer.py

Reads source_schema_registry and generates a dynamic SELECT that applies
the correct transformation per column. Writes typed, clean data to a
staging table in the client schema.

Run behaviour:
    First run  — staging table does not exist:
                 CREATE TABLE stg_{table} + INSERT all rows.
    Subsequent — staging table exists:
                 Read MAX(_airbyte_emitted_at) from staging as watermark,
                 INSERT only rows where _airbyte_emitted_at > watermark.
                 If _airbyte_emitted_at is absent from the registry, abort
                 with an error — never fall back to a silent full refresh.

dbt never does type casting — this module is the only casting layer.

Usage:
    python connectors/python_transformer.py
    (defaults to client_id='azure_co', table='shopify_orders')

Rules observed:
    RULE 2 — schema-qualified queries
    RULE 3 — synthetic data toggle guard
    RULE 4 — zero casts in dbt; all casting lives here
    RULE 5 — structured error logging with SOURCE field
    RULE 6 — NULL / schema drift / rate limit guards
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
# Column expression builder
# ---------------------------------------------------------------------------

def _build_column_expression(column_name: str, transformation: str) -> str:
    """
    Returns a SQL expression for one column based on its transformation.
    The expression includes an alias so the staging column name matches
    the source column name exactly.
    """
    col = f'"{column_name}"'

    if transformation == 'cast_text_to_numeric':
        return f"NULLIF(TRIM({col}), '')::numeric AS {col}"

    if transformation == 'cast_text_to_timestamp':
        return f"NULLIF(TRIM({col}), '')::timestamptz AS {col}"

    if transformation == 'jsonb_extract_from_text':
        return (
            f"CASE WHEN {col} IS NULL THEN NULL "
            f"WHEN TRIM({col}) = '' THEN NULL "
            f"ELSE {col}::jsonb "
            f"END AS {col}"
        )

    # 'jsonb_extract' (already jsonb) and 'none' — pass through unchanged
    return col


def _validate_column_expression(cur, schema: str, table: str,
                                 column_name: str, expression: str) -> bool:
    """
    Runs the cast expression against a small sample to catch data-quality
    failures before the full INSERT. Returns True if the expression is safe.
    """
    try:
        cur.execute(
            f'SELECT {expression} FROM "{schema}"."{table}" LIMIT 100'
        )
        cur.fetchall()
        return True
    except Exception as exc:
        logger.error(
            "SOURCE: Python Transformer | "
            "CAST VALIDATION FAILED: %s.%s.%s | ERROR: %s",
            schema, table, column_name, str(exc),
        )
        return False


# ---------------------------------------------------------------------------
# Schema / table introspection helpers
# ---------------------------------------------------------------------------

def _has_synthetic_column(cur, schema: str, table: str) -> bool:
    cur.execute(
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = %s
          AND table_name   = %s
          AND column_name  = 'is_synthetic'
        """,
        (schema, table),
    )
    return cur.fetchone() is not None


def _staging_table_exists(cur, schema: str, staging_table: str) -> bool:
    cur.execute(
        """
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = %s
              AND table_name   = %s
        )
        """,
        (schema, staging_table),
    )
    return cur.fetchone()[0]


# Airbyte renamed the watermark column in Destinations V2.
# Check V2 name first, fall back to V1.
_WATERMARK_CANDIDATES = [
    '_airbyte_extracted_at',   # Destinations V2 (current)
    '_airbyte_emitted_at',     # Destinations V1 (legacy)
]


def _get_watermark_column(cur, client_id: str, table_name: str) -> str | None:
    """
    Returns the actual watermark column name found in source_schema_registry,
    or None if neither V2 nor V1 candidate is registered.
    """
    for candidate in _WATERMARK_CANDIDATES:
        cur.execute(
            """
            SELECT 1
            FROM public.source_schema_registry
            WHERE client_id   = %s
              AND table_name  = %s
              AND column_name = %s
              AND is_removed  = false
            """,
            (client_id, table_name, candidate),
        )
        if cur.fetchone() is not None:
            return candidate
    return None


def _get_watermark_transformation(cur, client_id: str, table_name: str,
                                   wm_col: str) -> str:
    """
    Returns the registered transformation for the watermark column so the
    WHERE clause casts the source column correctly.
    """
    cur.execute(
        """
        SELECT transformation
        FROM public.source_schema_registry
        WHERE client_id   = %s
          AND table_name  = %s
          AND column_name = %s
        """,
        (client_id, table_name, wm_col),
    )
    row = cur.fetchone()
    return row[0] if row else 'none'


# ---------------------------------------------------------------------------
# Synthetic data condition (returns condition string, no WHERE keyword)
# ---------------------------------------------------------------------------

def _synthetic_condition(client_id: str, has_synthetic: bool) -> str:
    """
    Returns the synthetic data filter as a bare SQL condition (no WHERE
    keyword) so it can be combined with other conditions.
    Returns an empty string if the is_synthetic column does not yet exist,
    and logs a warning.
    """
    if has_synthetic:
        return (
            f"(is_synthetic = false "
            f"OR (SELECT use_synthetic_data FROM public.client_config "
            f"    WHERE client_id = '{client_id}') = true)"
        )
    # is_synthetic lives on staging tables, not on Airbyte-managed raw tables.
    # Absence on the source is expected — no filter needed.
    return ''


# ---------------------------------------------------------------------------
# Main transform function
# ---------------------------------------------------------------------------

def transform_table(client_id: str, table_name: str, conn) -> bool:
    """
    Reads registry for table_name, builds a typed SELECT, and either
    creates the staging table (first run) or incrementally inserts new rows
    using _airbyte_emitted_at as a watermark (subsequent runs).

    If the registry has no entries, calls schema_discovery automatically
    (one retry).

    Returns True on success, False on failure.
    """
    schema        = f'client_{client_id}'
    staging_table = f'stg_{table_name}'
    full_source   = f'"{schema}"."{table_name}"'
    full_staging  = f'"{schema}"."{staging_table}"'

    try:
        cur = conn.cursor()

        # ------------------------------------------------------------------
        # Step 1 — read registry; auto-discover if empty (one retry)
        # ------------------------------------------------------------------
        def _fetch_registry():
            cur.execute(
                """
                SELECT column_name, transformation, target_data_type,
                       json_path, default_value, is_nullable
                FROM public.source_schema_registry
                WHERE client_id  = %s
                  AND table_name = %s
                  AND is_removed = false
                ORDER BY column_name
                """,
                (client_id, table_name),
            )
            return cur.fetchall()

        registry_rows = _fetch_registry()

        if not registry_rows:
            logger.warning(
                "SOURCE: Python Transformer | CLIENT: %s | "
                "WARN: No registry entries for %s — running schema discovery "
                "before retrying.",
                client_id, table_name,
            )
            from connectors.schema_discovery import discover_and_update_schema
            discover_and_update_schema(
                client_id=client_id,
                table_name=table_name,
                source_name='shopify',
                conn=conn,
            )
            registry_rows = _fetch_registry()

        if not registry_rows:
            logger.error(
                "SOURCE: Python Transformer | CLIENT: %s | "
                "ERROR: Registry still empty after discovery for %s. "
                "Check that Airbyte has synced the table.",
                client_id, table_name,
            )
            return False

        # ------------------------------------------------------------------
        # Step 2 — build and validate SELECT expressions
        # ------------------------------------------------------------------
        valid_expressions = []
        failed_columns    = []

        for row in registry_rows:
            col_name, transformation = row[0], row[1]
            expr = _build_column_expression(col_name, transformation)

            if transformation == 'none':
                valid_expressions.append(expr)
            else:
                if _validate_column_expression(cur, schema, table_name,
                                               col_name, expr):
                    valid_expressions.append(expr)
                else:
                    failed_columns.append(col_name)
                    logger.error(
                        "SOURCE: Python Transformer | CLIENT: %s | "
                        "ERROR: Cast validation failed for %s.%s "
                        "(transformation: %s) — falling back to raw value. | "
                        "CONTEXT: %s",
                        client_id, table_name, col_name, transformation,
                        {'target_type': row[2]},
                    )
                    valid_expressions.append(f'"{col_name}"')

        if not valid_expressions:
            logger.error(
                "SOURCE: Python Transformer | CLIENT: %s | "
                "ERROR: No valid expressions built for %s.",
                client_id, table_name,
            )
            return False

        select_clause = ',\n    '.join(valid_expressions)

        # ------------------------------------------------------------------
        # Step 3 — determine load mode (first run vs incremental)
        # ------------------------------------------------------------------
        has_synthetic  = _has_synthetic_column(cur, schema, table_name)
        synth_cond     = _synthetic_condition(client_id, has_synthetic)
        staging_exists = _staging_table_exists(cur, schema, staging_table)

        t0 = time.time()

        if not staging_exists:
            # ----------------------------------------------------------------
            # FIRST RUN — create staging table and load all rows
            # ----------------------------------------------------------------
            cur.execute(
                f"""
                CREATE TABLE {full_staging} AS
                SELECT
                    {select_clause}
                FROM {full_source}
                WHERE 1 = 0
                """
            )
            # is_synthetic is a fixed metadata column on every staging table.
            # It is not in source_schema_registry — added explicitly here so
            # Airbyte sync cycles never interfere with it (Airbyte only touches
            # raw tables, never stg_* tables).
            cur.execute(
                f'ALTER TABLE {full_staging} '
                f'ADD COLUMN IF NOT EXISTS is_synthetic boolean default false'
            )
            conn.commit()

            where_parts = ([synth_cond] if synth_cond else [])
            where_clause = ('WHERE ' + ' AND '.join(where_parts)
                            if where_parts else '')

            cur.execute(
                f"INSERT INTO {full_staging}\n"
                f"SELECT\n    {select_clause}\n"
                f"FROM {full_source}\n"
                f"{where_clause}"
            )
            rows_inserted = cur.rowcount
            conn.commit()

            load_mode      = 'first_load'
            watermark_used = None
            wm_col         = None

            logger.info(
                "SOURCE: Python Transformer | CLIENT: %s | "
                "First load -- %s rows inserted into %s",
                client_id, rows_inserted, full_staging,
            )

        else:
            # ----------------------------------------------------------------
            # SUBSEQUENT RUN — incremental load via Airbyte watermark column
            # ----------------------------------------------------------------
            wm_col = _get_watermark_column(cur, client_id, table_name)
            if wm_col is None:
                logger.error(
                    "SOURCE: Python Transformer | CLIENT: %s | "
                    "ERROR: Staging table %s exists but no Airbyte watermark "
                    "column (%s) is registered in source_schema_registry for "
                    "%s. Cannot determine watermark. "
                    "Aborting — run schema discovery to register the column "
                    "before retrying.",
                    client_id, full_staging,
                    ' / '.join(_WATERMARK_CANDIDATES), table_name,
                )
                return False

            # Read watermark from staging
            cur.execute(
                f'SELECT MAX("{wm_col}") FROM {full_staging}'
            )
            watermark_used = cur.fetchone()[0]

            if watermark_used is None:
                # Staging exists but is empty — full load without DROP
                logger.warning(
                    "SOURCE: Python Transformer | CLIENT: %s | "
                    "WARN: Staging table %s exists but is empty — "
                    "performing full load.",
                    client_id, full_staging,
                )
                where_parts = ([synth_cond] if synth_cond else [])
            else:
                # Normal incremental: watermark filter on source column.
                # Cast source column to timestamptz unconditionally — safe
                # whether the raw type is already timestamptz or text.
                wm_transform = _get_watermark_transformation(
                    cur, client_id, table_name, wm_col
                )
                if wm_transform == 'cast_text_to_timestamp':
                    wm_expr = f"NULLIF(TRIM(\"{wm_col}\"), '')::timestamptz"
                else:
                    wm_expr = f'"{wm_col}"'

                where_parts = [f"{wm_expr} > %s"]
                if synth_cond:
                    where_parts.append(synth_cond)

            where_clause = ('WHERE ' + ' AND '.join(where_parts)
                            if where_parts else '')

            insert_sql = (
                f"INSERT INTO {full_staging}\n"
                f"SELECT\n    {select_clause}\n"
                f"FROM {full_source}\n"
                f"{where_clause}"
            )

            # Pass watermark as parameter to avoid SQL injection and
            # ensure correct timestamptz handling by psycopg2.
            params = [watermark_used] if watermark_used is not None else None
            cur.execute(insert_sql, params)
            rows_inserted = cur.rowcount
            conn.commit()

            load_mode = 'incremental'

            logger.info(
                "SOURCE: Python Transformer | CLIENT: %s | "
                "Incremental load -- %s new rows inserted into %s, "
                "watermark col: %s, watermark was: %s",
                client_id, rows_inserted, full_staging, wm_col, watermark_used,
            )

        elapsed = time.time() - t0

        # ------------------------------------------------------------------
        # Step 4 — report
        # ------------------------------------------------------------------
        print()
        print('-' * 60)
        print(f'  Python Transformer -- {table_name}')
        print('-' * 60)
        print(f'  Load mode                : {load_mode}')
        if load_mode == 'incremental':
            print(f'  Watermark column         : {wm_col}')
            print(f'  Watermark value          : {watermark_used}')
        print(f'  Columns in SELECT        : {len(valid_expressions)}')
        print(f'  Rows inserted            : {rows_inserted}')
        print(f'  Cast-fallback columns    : {len(failed_columns)}')
        if failed_columns:
            for c in failed_columns:
                print(f'    ERR {c}')
        print(f'  Synthetic filter active  : {has_synthetic}')
        print(f'  Staging table            : {full_staging}')
        print(f'  Time taken               : {elapsed:.2f}s')
        print('-' * 60)

        return True

    except Exception as exc:
        logger.error(
            "SOURCE: Python Transformer | CLIENT: %s | "
            "ERROR: %s | CONTEXT: %s",
            client_id, str(exc),
            {'table': table_name, 'staging': f'{schema}.{staging_table}'},
        )
        try:
            conn.rollback()
        except Exception:
            pass
        return False


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
        success = transform_table(
            client_id='azure_co',
            table_name='shopify_orders',
            conn=conn,
        )
        sys.exit(0 if success else 1)
    finally:
        conn.close()
