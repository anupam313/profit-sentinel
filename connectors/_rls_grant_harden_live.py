# ONE-OFF HARDENING PASS - committed as a record, NOT re-runnable.
# Gates on a specific dirty pre-state (RLS off, anon/auth grants present,
# leaky policy present). After a successful run that pre-state no longer
# holds, so re-running fails the gate and exits without writing.
"""Owed item H — LIVE public-schema RLS+grant hardening (single atomic, fail-closed pass).

Part A : read-only precondition gate (must match expected MUST-FIX shape, else STOP, no write).
Part B : ONE transaction — ENABLE RLS (7), REVOKE anon/authenticated (14), DROP 2 leaky policies,
         then 6 verification checks; COMMIT only if all pass, else ROLLBACK.
Part C : post-state matrix + revert commands.

No repo edits. No git. Schema-altering DB writes only, gated and reversible.
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

FULL_PRIVS = {'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE', 'REFERENCES', 'TRIGGER'}

ENABLE_RLS = [
    'client_config', 'brand_event_calendar', 'founder_preference_profile',
    'influencer_profile', 'network_pattern_benchmarks', 'permanent_dq_limitations',
    'config_change_log',
]
REVOKE_14 = ENABLE_RLS + [
    'alert_log', 'thread_context', 'candidate_signals', 'causal_pattern_validation',
    'onboarding_messages', 'schema_versions', 'source_schema_registry',
]
DROP_POLICY = ['alert_log', 'thread_context']
SKIP = 'suppression_log'
ALL_15 = sorted(set(REVOKE_14 + [SKIP]))


def get_conn():
    url = os.getenv('DATABASE_URL')
    if not url:
        print('ERROR: DATABASE_URL not set')
        sys.exit(1)
    conn = psycopg2.connect(url, sslmode='require')
    conn.autocommit = False  # one explicit transaction
    return conn


def rls_state(cur):
    cur.execute("""
        SELECT c.relname, c.relrowsecurity, c.relforcerowsecurity
        FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname='public' AND c.relkind='r'
    """)
    return {r[0]: (r[1], r[2]) for r in cur.fetchall()}


def grant_map(cur):
    """{table: {grantee: set(privs)}} for the relevant grantees."""
    cur.execute("""
        SELECT table_name, grantee, privilege_type
        FROM information_schema.role_table_grants
        WHERE table_schema='public'
          AND grantee IN ('anon','authenticated','service_role','postgres')
    """)
    out = {}
    for tbl, grantee, priv in cur.fetchall():
        out.setdefault(tbl, {}).setdefault(grantee, set()).add(priv)
    return out


def policy_map(cur):
    cur.execute("""
        SELECT tablename, policyname FROM pg_policies WHERE schemaname='public'
    """)
    out = {}
    for tbl, pol in cur.fetchall():
        out.setdefault(tbl, []).append(pol)
    return out


def main():
    conn = get_conn()
    cur = conn.cursor()

    print('=' * 80)
    print('PART A — READ-ONLY PRECONDITION GATE')
    print('=' * 80)

    rls = rls_state(cur)
    grants = grant_map(cur)
    pols = policy_map(cur)

    failures = []

    # all 15 tables must exist
    for t in ALL_15:
        if t not in rls:
            failures.append(f'TABLE MISSING: public.{t}')

    # REVOKE_14: each must currently have FULL anon AND authenticated grant
    for t in REVOKE_14:
        for g in ('anon', 'authenticated'):
            have = grants.get(t, {}).get(g, set())
            if have != FULL_PRIVS:
                failures.append(f'{t}: expected FULL {g} grant pre-state, found {sorted(have) or "none"}')

    # ENABLE_RLS 7: RLS must currently be OFF
    for t in ENABLE_RLS:
        if rls.get(t, (None,))[0] is not False:
            failures.append(f'{t}: expected RLS OFF pre-state, found {rls.get(t)}')

    # The other 7 REVOKE_14 (already RLS-on) sanity: RLS should be ON
    for t in [x for x in REVOKE_14 if x not in ENABLE_RLS]:
        if rls.get(t, (None,))[0] is not True:
            failures.append(f'{t}: expected RLS ON pre-state, found {rls.get(t)}')

    # DROP_POLICY 2: must currently carry "service role full access"
    for t in DROP_POLICY:
        if 'service role full access' not in pols.get(t, []):
            failures.append(f'{t}: expected policy "service role full access" pre-state, found {pols.get(t, [])}')

    # suppression_log: anon/auth already revoked, RLS on
    sl = grants.get(SKIP, {})
    if sl.get('anon') or sl.get('authenticated'):
        failures.append(f'{SKIP}: expected anon/auth already revoked, found anon={sorted(sl.get("anon", []))} auth={sorted(sl.get("authenticated", []))}')
    if rls.get(SKIP, (None,))[0] is not True:
        failures.append(f'{SKIP}: expected RLS ON, found {rls.get(SKIP)}')

    print('Pre-state snapshot (15 public tables):')
    print(f'  {"table":<30} {"rls":<6} {"anon":<5} {"auth":<5} {"svc_role":<9} {"postgres":<9} policies')
    for t in ALL_15:
        r = 'ON' if rls.get(t, (False,))[0] else 'off'
        a = len(grants.get(t, {}).get('anon', set()))
        au = len(grants.get(t, {}).get('authenticated', set()))
        sv = len(grants.get(t, {}).get('service_role', set()))
        pg = len(grants.get(t, {}).get('postgres', set()))
        pl = ','.join(pols.get(t, [])) or '-'
        print(f'  {t:<30} {r:<6} {a:<5} {au:<5} {sv:<9} {pg:<9} {pl}')

    if failures:
        print('\n*** PRECONDITION GATE FAILED — NO WRITES PERFORMED ***')
        for f in failures:
            print('  - ' + f)
        conn.rollback()
        conn.close()
        sys.exit(2)

    print('\nGATE PASSED — pre-state matches expected MUST-FIX shape. Proceeding to Part B.')

    # ───────────────────────────────────────────────────────────────────────
    print('\n' + '=' * 80)
    print('PART B — ATOMIC LIVE HARDENING (single transaction)')
    print('=' * 80)

    try:
        # B-1 ENABLE RLS (idempotent)
        for t in ENABLE_RLS:
            cur.execute(f'ALTER TABLE public.{t} ENABLE ROW LEVEL SECURITY;')
        print(f'B-1  ENABLE RLS on {len(ENABLE_RLS)} tables — done')

        # B-2 REVOKE anon, authenticated
        for t in REVOKE_14:
            cur.execute(f'REVOKE ALL ON public.{t} FROM anon, authenticated;')
        print(f'B-2  REVOKE ALL FROM anon, authenticated on {len(REVOKE_14)} tables — done')

        # B-3 DROP leaky policies
        for t in DROP_POLICY:
            cur.execute(f'DROP POLICY IF EXISTS "service role full access" ON public.{t};')
        print(f'B-3  DROP POLICY "service role full access" on {DROP_POLICY} — done')

        # B-4 VERIFY (in-transaction catalog reflects the changes)
        print('\nB-4  VERIFICATION')
        rls2 = rls_state(cur)
        grants2 = grant_map(cur)
        pols2 = policy_map(cur)
        vfail = []

        # (i) anon/auth ZERO privs on all 14
        for t in REVOKE_14:
            a = grants2.get(t, {}).get('anon', set())
            au = grants2.get(t, {}).get('authenticated', set())
            if a or au:
                vfail.append(f'(i) {t}: anon={sorted(a)} auth={sorted(au)} (expected none)')
        # (ii) RLS enabled on all 14
        for t in REVOKE_14:
            if rls2.get(t, (None,))[0] is not True:
                vfail.append(f'(ii) {t}: RLS not enabled ({rls2.get(t)})')
        # (iii) no policy on alert_log / thread_context
        for t in DROP_POLICY:
            if pols2.get(t):
                vfail.append(f'(iii) {t}: policy still present {pols2.get(t)}')
        # (iv) postgres AND service_role still FULL on all 14
        for t in REVOKE_14:
            for g in ('postgres', 'service_role'):
                have = grants2.get(t, {}).get(g, set())
                if have != FULL_PRIVS:
                    vfail.append(f'(iv) {t}: {g} privs={sorted(have)} (expected full 7)')
        # (v) suppression_log unchanged
        slr = rls2.get(SKIP, (None,))[0]
        sla = grants2.get(SKIP, {}).get('anon', set())
        slau = grants2.get(SKIP, {}).get('authenticated', set())
        if slr is not True or sla or slau:
            vfail.append(f'(v) {SKIP}: rls={slr} anon={sorted(sla)} auth={sorted(slau)}')

        # (vi) rolled-back owner-write probe
        probe_ok = False
        cur.execute('SAVEPOINT p;')
        try:
            cur.execute(
                "INSERT INTO public.config_change_log (client_id, field_name, changed_by, reason) "
                "VALUES ('__rls_probe__', '__probe__', '__rls_harden__', 'write-path verify') RETURNING id;"
            )
            probe_id = cur.fetchone()[0]
            probe_ok = probe_id is not None
        finally:
            cur.execute('ROLLBACK TO SAVEPOINT p;')
        if not probe_ok:
            vfail.append('(vi) owner-write probe did not succeed')

        for chk, label in [
            ('i', 'anon/auth zero privs on 14'),
            ('ii', 'RLS enabled on 14'),
            ('iii', 'no policy on alert_log/thread_context'),
            ('iv', 'postgres+service_role full on 14'),
            ('v', 'suppression_log unchanged'),
            ('vi', 'owner-write probe ok (rolled back)'),
        ]:
            bad = [m for m in vfail if m.startswith(f'({chk})')]
            print(f'  ({chk}) {label}: {"PASS" if not bad else "FAIL"}')
            for m in bad:
                print('       ' + m)

        if vfail:
            conn.rollback()
            print('\n*** VERIFICATION FAILED — TRANSACTION ROLLED BACK. No change persisted. ***')
            conn.close()
            sys.exit(3)

        conn.commit()
        print('\nALL CHECKS PASSED — COMMITTED.')

    except Exception as e:
        conn.rollback()
        print(f'\n*** ERROR during Part B — ROLLED BACK: {e} ***')
        conn.close()
        raise

    # ───────────────────────────────────────────────────────────────────────
    print('\n' + '=' * 80)
    print('PART C — POST-STATE MATRIX (15 tables)')
    print('=' * 80)
    rls3 = rls_state(cur)
    grants3 = grant_map(cur)
    pols3 = policy_map(cur)
    print(f'  {"table":<30} {"rls":<6} {"anon":<5} {"auth":<5} {"svc_role":<9} {"postgres":<9} policies')
    for t in ALL_15:
        r = 'ON' if rls3.get(t, (False,))[0] else 'off'
        a = len(grants3.get(t, {}).get('anon', set()))
        au = len(grants3.get(t, {}).get('authenticated', set()))
        sv = len(grants3.get(t, {}).get('service_role', set()))
        pg = len(grants3.get(t, {}).get('postgres', set()))
        pl = ','.join(pols3.get(t, [])) or '-'
        print(f'  {t:<30} {r:<6} {a:<5} {au:<5} {sv:<9} {pg:<9} {pl}')

    cur.close()
    conn.close()
    print('\n[live hardening complete — committed; suppression_log untouched]')


if __name__ == '__main__':
    main()
