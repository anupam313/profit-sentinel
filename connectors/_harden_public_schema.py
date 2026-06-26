"""Durable public-schema RLS + grant hardening (owed item H/I — durability home).

This is the AUTHORITATIVE, idempotent home for keeping the public schema fail-closed
against anon / authenticated across rebuilds and new table CREATEs.

Two levers, one transaction (verify-before-commit, fail-closed):

  Lever A  ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
           REVOKE ALL ON TABLES FROM anon, authenticated;
           -- postgres altering its OWN default; legal as postgres. This is what stops
           -- a NEW public CREATE from silently re-granting anon/authenticated.
           -- NOTE: the supabase_admin default-ACL re-grant is a KNOWN residual — postgres
           -- is neither a member of nor superuser over supabase_admin, so we CANNOT and do
           -- NOT touch it here. Dashboard-created tables remain a documented residual.

  Lever B  For each of the 15 known public tables that EXISTS: ENABLE ROW LEVEL SECURITY
           (no FORCE) + REVOKE ALL FROM anon, authenticated. Explicit hardcoded list (NOT a
           dynamic pg_class sweep) so the security surface is auditable. Absent tables are
           skipped + logged (5 of the 15 are doc-only / dashboard-created and may not exist
           on a fresh DB).

suppression_log keeps its own co-located REVOKE in seed_tiktok.create_tables() as belt-and-
suspenders; consolidation into this module is deferred.

RLS posture: enabled, NO policy = deny-all for anon/authenticated. The per-client JWT policy
is a separate post-pilot owed item (D). The privileged write path (postgres / service_role,
which every PS caller uses via DATABASE_URL) is unaffected — RLS is not FORCEd and those roles
retain full table privileges.

Idempotent: every statement is a no-op on already-hardened state, so re-running is safe.
"""
import logging
import os
import sys

import psycopg2
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

logger = logging.getLogger(__name__)

_SOURCE = 'Public Schema Hardener'

# Explicit, auditable list — NOT a dynamic enumeration. (RULE 8: every public table.)
PUBLIC_TABLES = [
    'client_config', 'alert_log', 'thread_context', 'config_change_log',
    'brand_event_calendar', 'founder_preference_profile', 'influencer_profile',
    'network_pattern_benchmarks', 'permanent_dq_limitations', 'candidate_signals',
    'causal_pattern_validation', 'onboarding_messages', 'schema_versions',
    'source_schema_registry', 'suppression_log',
]

_FULL_PRIVS = {'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE', 'REFERENCES', 'TRIGGER'}

# Table used for the rolled-back owner-write probe (write-path-intact check).
# On a fresh DB it may be absent (doc-only) — the probe is then skipped, not failed.
_PROBE_TABLE = 'config_change_log'
_PROBE_SQL = (
    "INSERT INTO public.config_change_log (client_id, field_name, changed_by, reason) "
    "VALUES ('__harden_probe__', '__probe__', '__public_schema_hardener__', 'write-path verify') "
    "RETURNING id;"
)


def _present_tables(cur) -> set:
    cur.execute(
        """
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
          AND table_name = ANY(%s)
        """,
        (PUBLIC_TABLES,),
    )
    return {r[0] for r in cur.fetchall()}


def _rls_map(cur) -> dict:
    cur.execute(
        """
        SELECT c.relname, c.relrowsecurity
        FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public' AND c.relkind = 'r'
        """
    )
    return {r[0]: r[1] for r in cur.fetchall()}


def _grant_map(cur) -> dict:
    cur.execute(
        """
        SELECT table_name, grantee, privilege_type
        FROM information_schema.role_table_grants
        WHERE table_schema = 'public'
          AND grantee IN ('anon', 'authenticated', 'service_role', 'postgres')
        """
    )
    out: dict = {}
    for tbl, grantee, priv in cur.fetchall():
        out.setdefault(tbl, {}).setdefault(grantee, set()).add(priv)
    return out


def _postgres_default_acl_text(cur) -> str:
    """Text of the postgres role's default ACL for TABLES in schema public ('' if none)."""
    cur.execute(
        """
        SELECT COALESCE(defaclacl::text, '')
        FROM pg_default_acl d JOIN pg_namespace n ON n.oid = d.defaclnamespace
        WHERE n.nspname = 'public' AND d.defaclobjtype = 'r'
          AND d.defaclrole = 'postgres'::regrole
        """
    )
    row = cur.fetchone()
    return row[0] if row else ''


def _verify(cur, applied: list) -> tuple:
    """Return (ok, failures, probe_status). In-transaction catalog reflects changes."""
    failures = []

    # (i) postgres default no longer grants anon / authenticated on TABLES
    acl_txt = _postgres_default_acl_text(cur)
    if 'anon=' in acl_txt or 'authenticated=' in acl_txt:
        failures.append(f'(i) postgres default ACL still grants anon/auth: {acl_txt}')

    rls = _rls_map(cur)
    grants = _grant_map(cur)

    for t in applied:
        # (ii) anon / auth zero, RLS on
        a = grants.get(t, {}).get('anon', set())
        au = grants.get(t, {}).get('authenticated', set())
        if a or au:
            failures.append(f'(ii) {t}: anon={sorted(a)} auth={sorted(au)} (expected none)')
        if rls.get(t) is not True:
            failures.append(f'(ii) {t}: RLS not enabled ({rls.get(t)})')
        # (iii) postgres + service_role retain full privs
        for g in ('postgres', 'service_role'):
            have = grants.get(t, {}).get(g, set())
            if have != _FULL_PRIVS:
                failures.append(f'(iii) {t}: {g} privs={sorted(have)} (expected full 7)')

    # (iv) rolled-back owner-write probe (write path intact)
    if _PROBE_TABLE in applied:
        cur.execute('SAVEPOINT harden_probe;')
        try:
            cur.execute(_PROBE_SQL)
            probe_id = cur.fetchone()[0]
            probe_status = 'PASS' if probe_id is not None else 'FAIL'
            if probe_id is None:
                failures.append('(iv) owner-write probe returned no id')
        except Exception as e:  # noqa: BLE001 — surface write-path breakage as a verify failure
            probe_status = 'FAIL'
            failures.append(f'(iv) owner-write probe raised: {e}')
        finally:
            cur.execute('ROLLBACK TO SAVEPOINT harden_probe;')
    else:
        probe_status = f'SKIPPED ({_PROBE_TABLE} absent)'

    return (not failures, failures, probe_status)


def harden_public_schema(conn) -> dict:
    """Idempotently harden the public schema. Single fail-closed transaction on `conn`.

    Commits on full verification pass; rolls back and raises on any failure. Does NOT close
    `conn` — the caller owns its lifecycle. Returns {'applied': [...], 'skipped': [...],
    'probe': str}.

    Fail-closed deviation from RULE 5's "log and return None": a verification failure here
    rolls back and RAISES, because silently returning success on an unhardened schema would be
    a security regression. Same posture as seed_shopify.validate_seed()'s gate.
    """
    cur = conn.cursor()
    applied: list = []
    skipped: list = []
    try:
        # Lever A — stop NEW public CREATEs from re-granting anon/authenticated (postgres default).
        cur.execute(
            'ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public '
            'REVOKE ALL ON TABLES FROM anon, authenticated;'
        )

        # Lever B — re-apply RLS + revoke on each known table that exists.
        present = _present_tables(cur)
        for t in PUBLIC_TABLES:
            if t not in present:
                skipped.append(t)
                logger.warning(
                    'SOURCE: %s | CLIENT: %s | ERROR: %s | CONTEXT: %s',
                    _SOURCE, 'n/a', 'table absent — skipped (expected for doc-only tables)',
                    f'public.{t}',
                )
                continue
            cur.execute(f'ALTER TABLE public.{t} ENABLE ROW LEVEL SECURITY;')
            cur.execute(f'REVOKE ALL ON public.{t} FROM anon, authenticated;')
            applied.append(t)

        ok, failures, probe_status = _verify(cur, applied)
        if not ok:
            conn.rollback()
            logger.error(
                'SOURCE: %s | CLIENT: %s | ERROR: %s | CONTEXT: %s',
                _SOURCE, 'n/a', 'verification failed — rolled back',
                {'failures': failures, 'applied': applied, 'skipped': skipped},
            )
            raise RuntimeError(f'Public schema hardening verification failed: {failures}')

        conn.commit()
        logger.info(
            'SOURCE: %s | hardened %d tables, skipped %d (absent), Lever A applied, probe=%s',
            _SOURCE, len(applied), len(skipped), probe_status,
        )
        return {'applied': applied, 'skipped': skipped, 'probe': probe_status}

    except Exception as e:
        # Defensive: ensure no partial state survives an unexpected error.
        try:
            conn.rollback()
        except Exception:  # noqa: BLE001
            pass
        logger.error(
            'SOURCE: %s | CLIENT: %s | ERROR: %s | CONTEXT: %s',
            _SOURCE, 'n/a', str(e), 'harden_public_schema',
        )
        raise


# ── Standalone run (Part C: run-once + verify) ─────────────────────────────────

def _get_conn():
    url = os.getenv('DATABASE_URL')
    if not url:
        logger.error('SOURCE: %s | ERROR: DATABASE_URL not set', _SOURCE)
        sys.exit(1)
    conn = psycopg2.connect(url, sslmode='require')
    conn.autocommit = False
    return conn


def main() -> None:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s')
    conn = _get_conn()
    try:
        result = harden_public_schema(conn)

        # Post-commit snapshot for the operator paste.
        cur = conn.cursor()
        rls = _rls_map(cur)
        grants = _grant_map(cur)
        print('\n=== POST-HARDEN MATRIX ===')
        print(f'  {"table":<30} {"rls":<5} {"anon":<5} {"auth":<5} {"svc":<5} {"pg":<5}')
        for t in PUBLIC_TABLES:
            if t in result['skipped']:
                print(f'  {t:<30} (absent — skipped)')
                continue
            a = len(grants.get(t, {}).get('anon', set()))
            au = len(grants.get(t, {}).get('authenticated', set()))
            sv = len(grants.get(t, {}).get('service_role', set()))
            pg = len(grants.get(t, {}).get('postgres', set()))
            print(f'  {t:<30} {("on" if rls.get(t) else "off"):<5} {a:<5} {au:<5} {sv:<5} {pg:<5}')

        print('\n=== Lever A — postgres default ACL (TABLES, public) after ===')
        print('  ' + (_postgres_default_acl_text(cur) or '(no postgres default ACL row)'))

        print(f'\napplied={result["applied"]}')
        print(f'skipped={result["skipped"]}')
        print(f'owner-write probe={result["probe"]}')
        print('\n[durable hardening complete — committed]')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
