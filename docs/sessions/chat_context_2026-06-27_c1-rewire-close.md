# Chat Context — 2026-06-27 — C1 signal rewire (Units A + B); threshold -> CD-10 routed; arc closed

## What this session was
Make pilot alert C1 (sizing-complaint velocity) fire correctly at a real client connect. C1 was
silently broken in two coupled ways: it read an INVENTED synthetic scalar
(gorgias_tickets.last_ticket_reason='sizing_issue') that the live Gorgias API has no equivalent for,
and its DQ tag-coverage gate read a STALE EMPTY base-schema table while dbt materialised the live view
to a _staging schema. The session ran the project discipline throughout: read-only discovery before
every write, three critique passes with a premise attack each turn, one item at a time with founder
sign-off. Each discovery surfaced a real blocker rather than dripping them across turns.

## How it went, pass by pass
1. C1 TRACING (read-only). Confirmed the mart reads the invented scalar; the real sizing data lives in
   gorgias_ticket_tags (35 tag values, 100% coverage, 1.27 tags/ticket). The DQ gate was DESIGNED
   tag-correct but its staging input column didn't exist.
2. SCHEMA RESOLUTION (read-only). The premise "only the mart drifted" was REFUTED: two
   stg_gorgias_tickets objects exist — a stale 0-row base TABLE (client_azure_co) and the live
   10,296-row VIEW (client_azure_co_staging). The Python gate read the empty base; dbt-ref'd marts read
   the live view. Verdict C (BOTH): wrong schema AND the model omits a tags column.
3. SYSTEMIC SCOPE (read-only). The gate's suffix-less client_schema bug is SYSTEMIC — 4 stg_ pre-checks
   (Gorgias/Meta/TikTok/Klaviyo) read stale base tables. At a real connect the gate SILENTLY no-ops
   (TABLE_ABSENT, no skip_map set) -> C1 would fire UNGUARDED. That inverted the risk: not "C1 stays
   quiet" but "C1 fires with no reliability gate" — the worse failure for a trust-first pilot.
4. client_id CONVENTION (read-only). Confirmed the canonical triple (client_id = client_schema =
   'client_azure_co'; staging_schema = 'client_azure_co_staging') so the staging fix can't
   double-suffix. Found a real namespace split (306 seeded app rows on 'azure_co') — routed; doesn't
   block C1.
5. UNIT A — signal rewire — BUILT + COMMITTED (7293420). The 2-file plan hit a wall — gorgias_ticket_tags
   wasn't a declared dbt source; corrected to a 3-file build (declare the source — my own
   under-specification, named (b)). Added a 1:ticket tags jsonb column, repointed the mart's sizing
   numerator to a boolean-per-ticket EXISTS over the 12-value sizing-only set. The verify gate tripped on
   a number (3,368 not the expected ~3,940) — but that expectation was MY occurrence-sum mis-estimate;
   the one-per-ticket count is correctly 3,368, a strict superset of the old 3,343 (+25, 0 old-only).
   KEPT, committed. Lesson: semantic gates assert structural invariants, not magic numbers.
6. UNIT B — gate fix — BUILT ON-DISK, NOT COMMITTED. Re-grep found the surface was BIGGER than the prior
   "4" (Meta reads TWO tables; a 5th dynamic stg_{connector} site) — 5 sites / 6 refs. Repointed all to
   staging_schema; added fail-closed (skip_map["C1"]) to the absent/error branches — but ONLY for
   Gorgias/C1, the sole alert gate (Meta/TikTok/Klaviyo set no skip_map, so fail-closed there would be an
   invented mapping). Verified read-only (tag_rate 1.000 staging / 0.000 base; py_compile). The file is
   untracked -> commit routed to owed-I; the on-disk fix is live for the pilot run.
7. UNIT C — threshold — turned out NOT to be a build. The discovery proved there's no recalibrator, the
   rewire caused no regression (new p90 43.08 ~= old 43.61), and 43.61 doesn't leak to real clients (they
   get the 15.0 default, which over-fires). The real item is CD-10 (per-client calibration at onboarding,
   already PENDING) — routed to the onboarding stream, with a manual p90 interim mandated for the first
   pilot client. The C1-signal arc CLOSED at A+B.

## Decisions (founder)
- Bucketing: C1 = sizing-only, quality excluded (no cross-alert impact — nothing else reads Gorgias tags).
- 1(a) fail-closed: suppress C1 if its DQ gate can't run, rather than fire unguarded (trust-first).
- 2(a): Unit B's untracked-file commit routed to owed-I (on-disk fix lands now).
- A: CD-10 routed to the onboarding stream; manual p90 interim for the first pilot client. Arc closed at A+B.

## The fragile thing (recorded so it doesn't evaporate)
Unit B's fix lives ONLY on-disk in the UNTRACKED historical_pattern_scan.py — not committed. A tree
reset loses it while Unit A (committed) survives. The state file's SESSION OPEN carries the survival
grep-check (the unique tokens `staging_schema` / `stg_staging_absent` / `dq_check_failed`, spacing-
independent). Locking it down (owed I) is the #1 next action.

## What's next
owed-I first (protect the work: reconcile the ~20-commit stack + bring the untracked gate file into git,
then the one coherent push), then the remaining FIRED pilot alerts get the same plug-and-play sweep
(HERO = owed J, C6, G1, C2-unbuilt) — that's where the next real surprises hide. Then lower-stakes
cleanup (namespace split, doc-sync, orphan schemas). Recruitment is still the true launch gate.

## Method notes carried
- Mount untrusted; reason only from HEAD / pasted live files. save_protocol live this session (149).
- Read-only discovery led every phase; every write fail-closed, reversible, explicit-path,
  paste-before-commit, no push from Claude Code. CC verifies continuity files, never authors them.
- Honest verification boundary: A+B verified at UNIT level read-only; the end-to-end fire/suppress
  integration + the fail-closed branches were NOT runtime-tested (the scan writes app tables). First
  controlled scan run on azure synthetic is the integration check.
- Position changes named (a) new fact / (b) under-tested prior — both reversals this session were (b).
