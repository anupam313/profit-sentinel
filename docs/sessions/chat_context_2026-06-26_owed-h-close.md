# Chat Context — 2026-06-26 — owed item H close (public-schema RLS + grant hardening)

## What this session was
Close owed item H: the systemic public-schema RLS + grant sweep flagged last session (§C11). The
same default-ACL leak that exposed suppression_log had left the whole public schema open —
anon/authenticated holding full DML on every public table, with RLS missing on the sensitive ones.
The session ran the C/D/E lesson throughout: read-only discovery first, then gated reversible
writes, then de-wire/doc, then commit. It took five Claude Code passes; each one surfaced and fixed
exactly one thing rather than dripping issues across turns.

## How it went, pass by pass
1. READ-ONLY DISCOVERY. Trusted no doc for the table list (CLAUDE.md said 6, the state file 15,
   tech_arch ~20 with a self-contradiction on sku_cost_master). Live catalog = 15 base tables, 0
   views. Per-table: RLS state, grants by role, readers/writers + their connection role, blast
   radius. Load-bearing find: EVERY in-repo caller connects as postgres (owner, bypasses its own
   RLS) or service_role (BYPASSRLS) via DATABASE_URL; frontend/ and slack-bot/ are empty; the anon
   key is never instantiated into a client. So a blind anon/auth revoke breaks no code path.
   Adversarial correction baked in: "open grant + no RLS" is only a LIVE breach if PostgREST exposes
   public — else it's LATENT. That distinction became a standing founder check (the Data API toggle).
2. LIVE WRITE. One atomic, fail-closed transaction: enabled RLS on the 7 off tables, revoked
   anon/auth on all 14, dropped the two leaky "service role full access" (PUBLIC/qual=true) policies
   on alert_log + thread_context. 6 verify checks, committed. suppression_log untouched.
3. DURABILITY. The §C9 finding drove it: pg_default_acl re-grants anon/auth on every public CREATE
   from BOTH postgres AND supabase_admin defaults, so a one-time revoke dies on the next CREATE.
   I corrected my OWN earlier "never ALTER DEFAULT, co-located only" stance — that was right for a
   single table, wrong for a schema-wide pass. Decided design: _harden_public_schema.py with
   Lever A (ALTER DEFAULT for ROLE postgres — its own default, legal) + Lever B (explicit 15-table
   ENABLE RLS + REVOKE, existence-guarded, no FORCE). Flagged honestly: we CANNOT alter the
   supabase_admin default (postgres isn't a member/superuser) — a named residual, not a silent gap.
4. DE-WIRE. Claude Code wired the call into seed_tiktok::main() as "the terminal seed." REJECTED
   against CLAUDE.md's own "seed order is NOT fixed" — an order-dependent whole-schema sweep can't
   ride an order-unfixed seed. Moved it to an explicit standalone RUN PATH step 1b. The
   suppression_log REVOKE stays in seed_tiktok because it's order-INDEPENDENT (co-located with its
   own CREATE) — different kind of thing.
5. DOC ACCURACY + COMMIT. Caught that the new RLS note still claimed the hardener runs "from
   seed_tiktok::main()" — a contradiction WE created this session — and fixed it to match RUN PATH
   1b before committing, rather than shipping it and cleaning up in owed E. Committed a46f541
   (3 files, 303 insertions), no push.

## The two residuals (recorded so they don't evaporate)
- supabase_admin default ACL: untouchable as postgres; dashboard-created tables still re-grant.
  Defense = periodic hardener re-run. Known platform constraint.
- Reproducibility gap: 5 foundational tables (client_config, alert_log, thread_context,
  config_change_log, brand_event_calendar) have no repo CREATE site — durable only live, not on
  rebuild, until their real DDLs are captured. Its own pass; needs true DDLs, not the stale doc.

## Why recruitment is next, not the next code item
H had to exist before real brand data lands — it's not synthetic-seed polish, it's a live
cross-tenant exposure on the application schema. But it's now closed at a clean line, and the
launch critical path is unchanged: zero committed design partners, Aman cold (pilot_scope §8).
Every build item left (E, R2, G) is off the critical path. The next session should open on
recruitment.

## Method notes carried
- Mount untrusted; reason only from HEAD / pasted live files. save_protocol live this session (149).
- Read-only discovery led every phase; every write fail-closed, reversible, explicit-path,
  paste-before-commit, no push from Claude Code.
- Claude Code reached for "update project memory" several times — disregarded each time; the
  continuity artifact is authored in chat, then CC-verified. CC does not author continuity files.
- Open verify for next session: re-check all 9 handles vs HEAD; confirm rev-list count (expect 18,
  the number most likely to drift); record the PostgREST toggle answer.

## Post-close addendum (2026-06-26, later same day)
After the H-close commit, two read-only audits + one decision (full detail in the state file's POST-CLOSE
ADDENDUM):
- Seeding completeness audit -> PARTIAL: data effectively complete (10 connectors, provenance isolatable,
  marts full-grain, 51/51 dbt tests); gaps are GA4 secondary tables (S3-P1/P2) + uncommitted Group B.
- Fidelity audit (prompted by the founder's point that synthetic seeds must match CURRENT API contracts or
  first client connect holds surprises): Google Ads + Meta faithful on join-critical shape. The real find —
  the HERO return-reason join is wired Loop-only while pilot_scope §4/§6 say Shopify-native is primary
  (internal spec-vs-wiring contradiction). Decided: wire to native. Live Shopify docs then showed the native
  returnReason enum is deprecated (2026-01) for returnReasonDefinition.handle, so the parser must target the
  handle. Read-only discovery prompt ready; build is pilot-critical (HERO fired) but not on the recruitment
  path — only bites for a non-Loop brand. New owed item J in the state file.
