"""
One-time setup: creates source_schema_registry and schema_versions
in the public schema with RLS enabled.
"""
import os
import sys

import psycopg2
from dotenv import load_dotenv

_ROOT = os.path.join(os.path.dirname(__file__), '..')
load_dotenv(os.path.join(_ROOT, '.env'))


DDL_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS public.source_schema_registry (
        id                  bigint generated always as identity primary key,
        client_id           text not null,
        source_name         text not null,
        table_name          text not null,
        column_name         text not null,
        raw_data_type       text not null,
        target_data_type    text not null,
        transformation      text not null,
        json_path           text,
        default_value       text,
        is_nullable         boolean default true,
        is_removed          boolean default false,
        last_validated      timestamptz default now(),
        unique(client_id, table_name, column_name)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS public.schema_versions (
        id              bigint generated always as identity primary key,
        client_id       text not null,
        table_name      text not null,
        column_name     text not null,
        old_type        text,
        new_type        text,
        change_type     text not null,
        detected_at     timestamptz default now(),
        is_resolved     boolean default false,
        resolved_at     timestamptz
    )
    """,
    "ALTER TABLE public.source_schema_registry ENABLE ROW LEVEL SECURITY",
    "ALTER TABLE public.schema_versions ENABLE ROW LEVEL SECURITY",
]

VERIFY_SQL = """
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
      AND table_name IN ('source_schema_registry', 'schema_versions')
    ORDER BY table_name
"""


def main():
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print('ERROR: DATABASE_URL not found in .env')
        sys.exit(1)

    conn = psycopg2.connect(database_url, sslmode='require')
    conn.autocommit = True
    cur = conn.cursor()

    for stmt in DDL_STATEMENTS:
        label = stmt.strip()[:60].replace('\n', ' ')
        try:
            cur.execute(stmt)
            print(f'  OK  {label}')
        except psycopg2.errors.DuplicateTable:
            print(f'  --  already exists, skipping: {label}')
        except Exception as exc:
            print(f'  ERR {label}\n      {exc}')

    cur.execute(VERIFY_SQL)
    found = [r[0] for r in cur.fetchall()]
    print(f'\nTables confirmed in public schema: {found}')

    conn.close()


if __name__ == '__main__':
    main()
