# ONE-OFF HISTORICAL FIXUP - committed as a record, NOT a rebuild step.
# Deletes five specific alert_log ids left by a broken seed run in 2026.
# Has no effect on a fresh database. Do not include in any rebuild path.
"""Delete 5 stale B1 alert_log rows from a previous broken seed run."""
import os, sys
import psycopg2
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

STALE_IDS = (153, 174, 175, 176, 177)

def main():
    url = os.getenv('DATABASE_URL')
    if not url:
        print('ERROR: DATABASE_URL not set'); sys.exit(1)
    conn = psycopg2.connect(url, sslmode='require')
    cur  = conn.cursor()

    # Confirm before deleting
    cur.execute('SELECT id, alert_type, fired_at FROM public.alert_log WHERE id = ANY(%s)',
                (list(STALE_IDS),))
    rows = cur.fetchall()
    print(f'Rows to delete ({len(rows)}):')
    for r in rows:
        print(f'  id={r[0]}  type={r[1]}  fired={r[2]}')

    cur.execute('DELETE FROM public.alert_log WHERE id = ANY(%s)', (list(STALE_IDS),))
    deleted = cur.rowcount
    conn.commit()
    print(f'Deleted {deleted} rows.')

    cur.execute("SELECT COUNT(*) FROM public.alert_log WHERE alert_type = 'B1'")
    remaining = cur.fetchone()[0]
    print(f'Remaining B1 rows: {remaining}  (expected 0 before seed runs)')

    cur.close()
    conn.close()

if __name__ == '__main__':
    main()
