# ONE-OFF HISTORICAL FIXUP - committed as a record, NOT a rebuild step.
# WARNING: DESTRUCTIVE. Unconditionally DELETEs every alert_log row with
# alert_type='B1' before re-inserting 8 canonical rows. Row ids are
# serial and CHANGE on every run. Do not run without reading it first.
"""
Delete all B1 rows from alert_log and reinsert with corrected fatigue_period_active.

Fix: fatigue_period_active = True for Y1 events (founder has NOT fixed rotation),
                           = False for Y2 events (founder HAS fixed rotation).
Old logic: fd in CREATIVE_FATIGUE_DATES[-2:]  -> True only for Y2 (WRONG)
New logic: year_label == 'Y1'                 -> True for Y1 (CORRECT)
"""
import os, sys, random
import psycopg2
import psycopg2.extras
from datetime import date, datetime, timezone
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

CLIENT_ID = 'azure_co'

CREATIVE_FATIGUE_DATES = [
    date(2024,  8, 15),
    date(2024, 10,  1),
    date(2024, 12, 10),
    date(2025,  1, 22),
    date(2025,  3,  8),
    date(2025,  5, 15),
    date(2025,  8, 10),
    date(2025, 10, 20),
]

# Reproduce same RNG state as the seed script (seed 99, B1 is the first consumer)
PY_RNG = random.Random(99)

ALERT_COLS = [
    'client_id', 'alert_type', 'fired_at',
    'should_fire', 'confidence_score',
    'signal_value', 'threshold_value', 'threshold_direction',
    'layer1_headline', 'layer2_context', 'layer3_precedent',
    'alert_instance_number', 'escalation_level',
    'suppressed', 'suppression_category',
    'fatigue_period_active', 'fatigue_reason',
    'outcome_confirmed', 'dismissal_correct',
    'is_synthetic',
]

def utc_dt(d: date, hour: int = 9) -> datetime:
    return datetime(d.year, d.month, d.day, hour, 0, 0, tzinfo=timezone.utc)

def build_b1_rows() -> list[tuple]:
    rows = []
    for idx, fd in enumerate(CREATIVE_FATIGUE_DATES, start=1):
        year_label = 'Y1' if fd < date(2025, 6, 1) else 'Y2'
        conf    = round(PY_RNG.uniform(0.72, 0.88), 2)
        freq_v  = round(PY_RNG.uniform(2.82, 3.15), 2)
        ctr_dec = round(PY_RNG.uniform(0.15, 0.24), 2)

        # CORRECTED: True for Y1 (fatigue era active, no fix yet),
        #            False for Y2 (founder fixed rotation, events are residual)
        fatigue_period_active = (year_label == 'Y1')

        rows.append((
            CLIENT_ID,
            'B1',
            utc_dt(fd),
            True,                   # should_fire
            conf,                   # confidence_score
            freq_v,                 # signal_value
            2.8,                    # threshold_value
            'above',                # threshold_direction
            (f'Creative fatigue -- prospecting frequency {freq_v:.2f} (threshold 2.8) '
             f'and CTR declined {ctr_dec*100:.0f}% over 7 days.'),
            (f'Fatigue event {idx} ({year_label}). Rotate prospecting creative to reset '
             f'frequency. Retargeting ad sets on separate audience pool -- not affected.'),
            ('No prior Y1 baseline.' if idx == 1
             else 'Prior fatigue events resolved within 5-7 days of creative rotation.'),
            1,                      # alert_instance_number
            0,                      # escalation_level
            False,                  # suppressed
            None,                   # suppression_category
            fatigue_period_active,  # fatigue_period_active (CORRECTED)
            None,                   # fatigue_reason
            None,                   # outcome_confirmed
            None,                   # dismissal_correct
            True,                   # is_synthetic
        ))
    return rows

def main():
    url = os.getenv('DATABASE_URL')
    if not url:
        print('ERROR: DATABASE_URL not set'); sys.exit(1)
    conn = psycopg2.connect(url, sslmode='require')
    cur  = conn.cursor()

    # Step 1: delete all existing B1 rows
    cur.execute("SELECT COUNT(*) FROM public.alert_log WHERE alert_type = 'B1'")
    before = cur.fetchone()[0]
    cur.execute("DELETE FROM public.alert_log WHERE alert_type = 'B1'")
    deleted = cur.rowcount
    print(f'Deleted {deleted} B1 rows (was {before}).')

    # Step 2: build corrected rows
    rows = build_b1_rows()
    print(f'Inserting {len(rows)} corrected B1 rows...')

    sql = (f'INSERT INTO public.alert_log ({", ".join(ALERT_COLS)}) VALUES %s')
    psycopg2.extras.execute_values(cur, sql, rows)
    conn.commit()
    print('Committed.')

    # Step 3: print final state
    cur.execute("""
        SELECT id, alert_type, fired_at::date,
               confidence_score, signal_value,
               fatigue_period_active,
               layer2_context
        FROM public.alert_log
        WHERE alert_type = 'B1'
        ORDER BY fired_at
    """)
    result = cur.fetchall()
    print(f'\nFinal B1 rows ({len(result)} total):')
    print(f'  {"id":<6} {"alert":<6} {"fired_at":<12} {"conf":<6} {"freq":<6} '
          f'{"fatigue_period_active":<22} year')
    for r in result:
        rid, atype, fired, conf, freq, fatigue, ctx = r
        year = 'Y1' if fired < date(2025, 6, 1) else 'Y2'
        print(f'  {rid:<6} {atype:<6} {str(fired):<12} {float(conf):<6.2f} '
              f'{float(freq):<6.2f} {str(fatigue):<22} {year}')

    cur.close()
    conn.close()

if __name__ == '__main__':
    main()
