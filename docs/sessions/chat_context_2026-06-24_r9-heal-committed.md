# Profit Sentinel — Chat Context — 2026-06-24 — R9 Heal + Recovery (narrative / decision trail)
## Pairs with: state_2026-06-24_r9-heal-committed.md
## Continues: the 2026-06-23 pre-pilot-hardening session.

> Resuming Profit Sentinel. Load save_protocol.md and state_2026-06-24_r9-heal-committed.md
> first. Re-verify the 8 canonical line-count handles against repo HEAD before any work. HEAD
> is eb21af2. Next action: hardening Phase B (Egnition island purge/keep).

---

## WHAT THIS FILE IS
The decision trail for how the R9 double-seed was healed — including a real data-loss incident
and its full recovery — so the *reasoning* survives, not just the end state. The state file holds
the verified facts and forward plan; this holds the story and the judgment calls.

---

## THE ARC

**1. Going in.** The R9 fix (idempotent seed) was authored and verified in prior turns; the seed
edits were correct and the determinism golden matched. The task this session was to RUN the heal
against the live doubled DB and land single-copy.

**2. The incident.** A throwaway harness (`_heal_run.py`) was written to do a "dry pre-check then
live run" in one process. It monkeypatched `execute_values` to a no-op for the dry pass; the reload
between passes restored the seed's `batch_insert` but not the global `execute_values`. So the live
pass DELETED everything and silently INSERTED nothing, then committed. The gate's assertions passed
**vacuously** — empty tables satisfy uniqueness, island-present, and connector-preserved checks. The
loss committed looking green. Claude Code reported it immediately and without minimizing; the seed
edits were never the problem — the test harness was.

**3. The key realization that de-risked everything.** The lost data was the *synthetic seed universe*
— which is **regenerable** from the deterministic golden. The only **irreplaceable** data was the
Egnition dev-store island (43 products + 1 order + 1 customer), and the damage scope confirmed it was
**intact**, as were all connector tables. So this was never a true disaster — it was "regenerate the
regenerable," with a verified backup (`ps_full.dump`) underneath as a second safety net.

**4. The recovery ordeal — and why it took so long.** The plan was restore-from-backup first, then
re-heal. But the restore could not be carried over this machine's link: large COPYs dropped SSL on
the largest connector table (~67k rows / ~8MB) on BOTH the transaction pooler (6543) and the session
pooler (5432). The pooler-mode switch (the documented fix for bulk transfer) was correct in principle
but didn't help — the real wall was **local link instability** (NAT/idle timeout, possibly TLS
inspection), not the pooler mode. Worse, every failed transfer left a **zombie backend** "idle in
transaction" holding locks; they piled up (8 of them, plus a blocked DROP) until ordinary reads timed
out. We cleared them with `pg_terminate_backend` once we diagnosed the lock chain via pg_stat_activity.

**5. The decision: Option 3 (regenerate, don't restore).** Because the seed is deterministically
regenerable and the island was safe, we chose to re-run the **production** `seed_shopify.py main()`
directly into the seed-empty state — which lands the intended healed single-copy without fighting the
network to push 274k+126k rows back up. The restore-then-heal path and the regenerate path converge on
the same end state; regenerate sidesteps the broken link entirely. (`ps_full.dump` stays on disk as a
valid restore point regardless.)

**6. The two non-negotiable fixes baked into the retry.** (a) **No harness, ever** — run through the
seed's own `main()` with real `execute_values`; the monkeypatch is what caused the loss. (b)
**Presence-band assertions** — every seed table must land in its expected POPULATED band, so an empty
table FAILS loudly. This closes the vacuous-pass hole that let the loss commit silently. Plus dry
determinism re-confirm (separate process) and island/connector preservation checks.

**7. The BEC false-fail (and why loosening it was correct, not a shortcut).** The first gated run
rolled back on one assertion: `brand_event_calendar` 116 rows vs 114 distinct `(client_id,event_name)`.
Investigation (read-only) showed this was a **mis-keyed assertion, not bad data**: the seed emits 100
BEC rows with 100 distinct names (zero seed dup), BEC `id` is an IDENTITY column (so useless for
doubling detection), and the *connector* data has 2 native duplicate-name rows. So `(client_id,
event_name)` was never a valid unique key. We replaced it with a **dup-excess invariant** (heal adds
no NEW duplicate keys beyond the connector's pre-existing 2) — guarded for doubling by the presence
band (a doubled BEC ≈ 216 blows the band) + connector-key-preservation. Replacing a *false* assertion
with a *true* one isn't weakening the gate; keeping a false key would just force endless false-fails.
The gate working (rollback, no commit) is the opposite of the vacuous pass that caused the incident.

**8. The re-run committed.** 32/32 assertions passed; the transaction committed the healed single-copy
universe. Post-commit `validate_seed` timed out on its heavy aggregation queries (the same network
ceiling) — but that's post-commit and informational; integrity was proven by the 32 pre-commit
assertions. No stuck backend was left.

**9. The commit (Phase A).** We separated the **permanent** R9 fix (the 16 idempotency edits in the
seed functions) from the **temporary** heal-assertion gate that had been wired into `main()` for the
one-time run — the gate must NOT ship in the production seed. Removed the gate (93-line functions block
+ the before-capture + restored the original bare `conn.commit()`), confirmed zero heal-scaffold
references remained and the 16 permanent edits were intact, and deleted `_heal_run.py`. The diff vs
HEAD was exactly the permanent fix. The re-baselined manifest's line-ending was verified: `core.autocrlf
=true` stores LF, so the staged blob hashes to the golden `55aba735…` (the on-disk `2f27ff24…` is just
the CRLF serialization of the same content). Committed as **eb21af2**, two files only, on a307b81,
stack now 5-deep, NOT pushed. Stash WIP untouched.

---

## JUDGMENT CALLS WORTH REMEMBERING
- **Restore-first was the right instinct, but the network made regenerate the right action.** When the
  link can't carry the bytes and the data is regenerable, regenerate beats fighting the transfer.
- **The insurance-dump requirement was dropped mid-recovery — deliberately.** `--single-transaction`
  restore rolls back to current state on failure (the exact thing insurance protected against), and the
  damaged state was itself reconstructable, so insisting on an insurance dump we *couldn't produce over
  this network* would have blocked recovery for no real gain.
- **Terminating zombie backends was a write/admin action, gated and confirmed safe** — they were
  idle-in-transaction with nothing committing, so termination released locks without data loss.
- **The incident is, in effect, the fault-injection drill from D-F** — an unintentional one. It proved
  both the failure mode (silent INSERT-skip + vacuous assertions) and the value of the hard gate. The
  durable fix (presence/uniqueness validation in `validate_seed` + dbt tests + constraints) is Phase D.

---

## NETWORK / ENVIRONMENT NOTES (for the next bulk operation)
- This machine's link cannot sustain a single large COPY (~8MB / ~67k rows) to Supabase on EITHER
  pooler port. Suspected: NAT/idle timeout, TLS inspection, or link quality.
- Workarounds that did NOT fix it: switching 6543→5432; libpq keepalives (helped marginally, not
  enough). Workarounds that WOULD: a stable wired link with AV TLS-inspection paused; or a cloud shell /
  VM near AWS us-east-1 doing the transfer; or per-table (smallest-first) restore to keep each COPY small.
- Every failed transfer orphaned a backend → always check pg_stat_activity for idle-in-transaction
  zombies after a dropped bulk op, and clear them before retrying.

---

## SEQUENCING (founder-approved)
One item at a time with sign-off. Design here, build in Claude Code (read-only mount; no repo/DB/git
from chat). Paste-before-commit. No pushes from Claude Code. Next: Phase B (island purge/keep — founder
decision), then C → D → E → F, then the canonical-corrections pass.
