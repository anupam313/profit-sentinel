# STATE — Agent Verification (snapshot)
**As of:** 2026-07-28 (session 2) · **Repo HEAD at session start:** `8aac9cb` (origin/master, in sync)
**Companion:** none yet — this file is the Phase-0 decision ledger, written BEFORE the work it
authorises, per `save_protocol.md` Phase 0 ("build the bridge before the manifest").
**Supersedes on ONE point only:** `state_2026-07-28_f3-interview-git-closure.md` remains current
for everything else. The point it is wrong on is inherited from
`state_2026-07-27_pilot_readiness.md:22` and is corrected in D-1 below.

**WHY THIS FILE EXISTS.** A long chat session verified build state directly against the
filesystem and git for the first time. The findings contradict a committed state file. This
file exists so they cannot be lost to chat length or rediscovered later. It is a TRACKING
artifact, not a canonical spec — same class as the other `docs/sessions/` state files.

**IT IS NOT A NEW TRACKER.** `pilot_readiness_register.md` remains the single durable home for
remaining work. Every item below carries its register destination. Fold them in at the next
register flush, then this file is history.

---

## EVIDENCE GRADES USED BELOW

- **VERIFIED-FS** — filesystem or git command output, this session.
- **VERIFIED-DB** — live database query, 2026-07-27 pass.
- **DOC** — a committed document asserts it; the artifact was not checked.
- **UNVERIFIED** — no evidence either way. Not guessed.

The distinction is load-bearing. D-1 exists precisely because a DOC-grade claim was carried
as fact for a month.

---

## D-1 — AGENTS B, C AND D WERE NEVER WRITTEN. **VERIFIED-FS.**

**The claim this retires**, verbatim from `state_2026-07-27_pilot_readiness.md:22`:
"Agents A-D EXIST (data flow ends at "Agents Query Marts"). Marts, seed scripts, RLS, synthetic
data all built. Register tasks are WIRING, not build-from-scratch."

That is false. Its basis was the title of `technical_architecture.md` Section 4 Step 6 — a
specification of intended data flow, not an observation of the repository.

**Evidence, four independent checks:**
1. `find . -path ./.git -prune -o -name "agent*.py" -print` returns exactly one path:
   `./agents/agent_a.py`.
2. `ls -la agents/` contains only `agent_a.py` (40088 bytes, 932 lines, mtime 19 May),
   `causal_graph.py` (41336 bytes, mtime 22 May) and `__pycache__/`.
3. `grep -rn "causal_graph" --include=*.py .` excluding the file itself returns NO MATCHES.
   Nothing in the codebase imports, reads or references the causal graph. This is behavioural,
   so a differently-named Agent B cannot hide from it.
4. `git log --all --diff-filter=D --name-only --oneline | grep -i agent` returns only
   `docs/sessions/pre_agent_build_checklist.md` — a documentation path. NO agent `.py` was ever
   deleted. This is never-written, not lost.

**Corroborating, from the repo's own history:** `git log --all --oneline -- agents/` returns two
commits, one of which states the position outright —
`d52ffde Add agents/causal_graph.py (authored, unwired) - pilot build-state baseline`.
The other is `692f52a Add agents/agent_a.py + Python/build .gitignore rules - pilot build-state baseline`.

**Corroborating, from Agent A's own docstring** (`agents/agent_a.py`, lines 1-5):
"Agent A - Signal Scanner / Reads mart_causal_chain_daily, runs pure-Python threshold checks,
writes confirmed signals to public.alert_log for Agent B. / No LLM calls anywhere in this file."
Agent A was built to hand off to a component that was never written.

**`__pycache__` contains only `causal_graph.cpython-311.pyc`** (11419 bytes, 22 May) — no
`agent_a` bytecode. Recorded, not interpreted.

**REGISTER DESTINATION:** a correction note wherever the WIRING framing is repeated, plus the
re-scoping in D-2, D-3 and D-4.

---

## D-2 — BT-3 AND BT-15 ARE AGENT BUILDS, NOT WIRING. **VERIFIED-FS.**

- **BT-3** (spreadsheet A10) currently reads "wire the orphaned causal_graph into Agent B",
  estimated 1-2 days. There is no Agent B to wire it to. This is an Agent B build.
- **BT-15** (spreadsheet A14) currently reads "Evidence Stack assembly", estimated 3-5 days.
  Confirmed from-scratch by `slack_bot/alert_formatter.py:145`, which reads:
  "Priority 1: evidence_stack_json (populated by Agent D in Step 13)".
  The formatter RENDERS an Evidence Stack that nothing assembles. Agent D's actual job is
  untouched.

**REGISTER DESTINATION:** BT-3 and BT-15, re-scoped in place.

---

## D-3 — BT-13 IS A PARTIAL PORT, NOT FROM-SCRATCH. **VERIFIED-FS, with a stated limit.**

`slack_bot/` holds 572 lines of delivery-loop code — the ONLY delivery code in the repository.
It was previously run: `pre_agent_build_checklist.md` records CD-1, CD-2 and CD-3 as
"COMPLETE" with "Step 10 done 2026-05-19", and `slack_bot/__pycache__` is dated 19 May.

| File | Lines | What it is |
|---|---|---|
| `action_handlers.py` | 228 | Approve / Snooze / Dismiss, writing to `alert_log` via psycopg2 |
| `alert_formatter.py` | 172 | Slack Block Kit builder, no LLM calls |
| `app.py` | 57 | Socket Mode entry point |
| `test_delivery.py` | 111 | Standalone alert-delivery script |
| `requirements.txt` | 4 | |

**What ports to email:** the `alert_log` write layer in `action_handlers.py`, and the live-schema
deviations already documented in `alert_formatter.py` lines 5-9 (`evidence_stack` ->
`evidence_stack_json`; `signal_values` jsonb -> `signal_value` + `threshold_value` numeric;
`projected_impact` absent so Block 6 always skipped; `alert_message` absent).
**What does NOT port:** Block Kit rendering, Socket Mode transport.

**LIMIT, stated honestly:** four docstrings and roughly 80 of the 572 lines were read. If
`action_handlers.py`'s write logic is entangled with Block Kit payload parsing, the reusable
core shrinks. Read it before committing to an A15 estimate. **UNVERIFIED.**

**Unexplained and recorded, not interpreted:** all five `slack_bot/` files carry mtime 22 June,
nine days AFTER the email pivot (2026-06-13), while `__pycache__` is 19 May. Could be
post-pivot edits or a OneDrive sync touching mtimes. `git log` cannot answer it — the directory
was untracked until this session. `md5sum slack_bot/*.py` would pin it.

**ACTION TAKEN THIS SESSION:** `slack_bot/` committed as a preservation baseline (five files by
explicit path; no `.pyc`, no `__pycache__`). Preservation only — it stays PARKED. Rationale:
it was untracked on the OneDrive path with the known corruption risk (HK-2), and it is the only
delivery code that exists. Mirrors `d52ffde`.

**REGISTER DESTINATION:** BT-13, and HK-1 (which lists `slack_bot/` as untracked — now false).

---

## D-4 — CD-4 IS MOOT AS WRITTEN. **VERIFIED-FS.**

CD-4 reads: "Confirm Agent D output can be cleanly intercepted before sending." There is no
Agent D and therefore no output to intercept. The underlying concern survives and should be
rewritten as a design constraint ON the Agent D build, not a verification of it.

**REGISTER DESTINATION:** CD-4, rewritten in place.

---

## D-5 — OQ-17 (NEW) — AGENT C DISPOSITION. **VERIFIED-FS. DECISION OWED.**

Agent C is UNWRITTEN, not merely untracked — which is a stronger statement than the previous
session reached.

`grep -rn "founder_preference_profile" --include=*.py .` returns hits in four files, none an
agent: `connectors/patch_script.py` (creates the table and seeds 43 alert types),
`connectors/_harden_public_schema.py:48`, `connectors/_harden_precondition_probe.py:18`,
`connectors/_rls_grant_harden_live.py:24` — the last three only list the table name in an RLS
sweep. So: table created, RLS enabled on it 2026-06-26, and the reader was never written.

**What Agent C is, with dates:**
- 2026-05-17, `chat_context_2026_05_17_session2.md` Decision 6: `capital_constraint_active`
  re-ranks Agent C suggestions only; spend-increase actions demoted, not removed; alert always
  fires. Marked "Closed - do not reopen."
- 2026-05-17, same file: "Dismissal reason threshold (churn signal definition)" recorded as
  blocking Agent C design. Carried into no current file.
- 2026-05-19 to 2026-05-23, six state files: build sequence Step 12/13, "Agent C (Recommendation
  engine)", Pending. `state_2026_05_23_alert_review_fg.md` is the LAST file containing that
  build-sequence table.
- 2026-06-13, `chat_context_2026_06_13_pilot_structure.md`, in a bullet headed "Architecture
  nuances (from the diagram review, easy to lose)": "the parser feeds both Agent B's reasoning
  and Agent C's action wording." **Agent C was named as live in the pipeline on the day the
  pilot was scoped, in a bullet flagged as easy to lose. It was then lost.**
- `technical_architecture.md:625` and `:644`: Agent C reads `founder_preference_profile`; at
  `dismissed_correct_count >= 3` raises the confidence threshold before recommending snooze; at
  `dismissed_incorrect_count >= 3` reduces urgency framing. Feeds Moat 3 from Month 6.

**Register searches, all returning 0:** "Agent C", "agent_c", "Recommendation engine",
"founder_preference_profile". For comparison: "Agent A" 2, "Agent B" 5, "Agent D" 6.

**Its function IS tracked, unnamed:** BT-15 specifies Evidence Stack layer 4 as "ranked
CORRECTIVE ACTIONS with projected impact and a confidence score" — that is Agent C's output,
inside Agent D's build item, with Agent C's name nowhere in it.

**RECOMMENDATION, not a decision:** for the pilot, fold layer 4 into the Agent D build, and
move the `founder_preference_profile` personalisation and the `capital_constraint_active`
re-ranking to a NAMED post-pilot item — so the May-2026 "do not reopen" decision stops pointing
at a component nothing covers. Founder to rule.

**REGISTER DESTINATION:** new OQ-17. Add to the HIGHEST VANISH-RISK list — no canonical home.

---

## D-6 — SYNTHETIC-DATA VAR-FORM DIVERGENCE IS LIVE. **VERIFIED-FS. Register mentions: 0.**

`CLAUDE.md` RULE 3 states the connector-staging form "keys off the dbt var, not the client, and
can expose real data on a wrong toggle", and marks the divergence "PENDING reconciliation".

`grep -rn "use_synthetic_data" warehouse/models/` shows **5 occurrences of the unsafe form
across 4 files**:
- `stg_meta_ad_performance.sql:6` <- **PILOT PATH. Meta feeds C8 and G1.**
- `stg_ga4_sessions.sql:3` and `:7`
- `stg_ga4_checkout_errors.sql:3`
- `stg_sentry_errors.sql:3`

The correct per-client form is already in use in at least eight places, and
`stg_shopify_orders.sql:49` carries the pattern as an in-code comment warning against the
var-form. The pattern is documented; four files never got it.

Register searches, all 0: "var-form", "use_synthetic_data", "DEBT-006".

**REGISTER DESTINATION:** new BT item, scoped so that `stg_meta_ad_performance.sql` is the
pilot-blocking half and the GA4/Sentry three are not.

---

## D-7 — STAGE 1 (INGEST) HAS CODE AND GIT TRACKING BUT NO REGISTER ITEM. **VERIFIED-FS.**

`connectors/schema_discovery.py` (453 lines) and `connectors/python_transformer.py` (500 lines)
both EXIST and both appear in `git ls-files`. My earlier characterisation of them as
"orphaned / untracked" conflated git state with register state and was wrong on the git half.

What is true: register mentions of each are **0**, and the spreadsheet's "Pipeline stage" column
contains 0. Onboarding, 2. Connect, 3. Transformation, 4. Detection, 5. Causal explanation,
6. Delivery, 7. Pre-pilot QA — **there is no stage 1 in the entire workbook**, because no
register item belongs to it.

Whether either script has ever run against a live source is **UNVERIFIED**. The seed path writes
synthetic rows directly into the client schema and bypasses both. First real connect is the
first time this code matters.

**REGISTER DESTINATION:** new item under first-connect actions, adjacent to FC-1.

---

## D-8 — CD-8 FRAMING IS MISLEADING. **VERIFIED-FS.**

CD-8 currently reads: "alert_log holds 177 rows and alert_data_lineage holds 0, so 177 alerts
were produced and none wrote lineage." That implies an agent produced them and failed to write
lineage.

Seed scripts INSERT `evidence_stack_json` directly: `connectors/seed_sentry.py:434` and `:461`,
and `connectors/category_inference.py:259`. So at least some of the 177 rows are seeded.

**The producer of the 177 rows is UNVERIFIED.** The dependency BT-15 has on a populated
`alert_data_lineage` is real either way and does not change.

**REGISTER DESTINATION:** CD-8, reworded to state the producer is unverified.

---

## D-9 — RULE 8 DIVERGENCE IS IN THE RULE TEXT, NOT THE DATABASE. **VERIFIED-DB (2026-07-27).**

`state_2026-07-27_dbverify-reproducibility.md` records: "NEVER A GAP: RLS policies - live state
(RLS on, zero policies, deny-all) IS reproducible from the tracked `_harden_public_schema.py`."

So the deny-all posture is deliberate and reproducible, not drift. `CLAUDE.md` RULE 8 demands
"Row-Level Security enabled and a policy applied. No exceptions", which the canonical hardening
script does not do. Closing this means editing RULE 8 to describe deny-all plus
application-layer isolation, and deciding separately what changes at client two — which
`state_2026-07-28_f3-interview-git-closure.md` correctly flags as a pilot-timeframe event.

`connectors/_harden_public_schema.py` is 276 lines and IS tracked (`git ls-files`). The
2026-07-28 state file's phrase "nine read-only `connectors/_*.py` probe scripts (untracked,
throwaway diagnostics)" is accurate — `git status --short` shows exactly nine untracked `_*.py`
files and the hardening script is not among them. A concern raised in chat that it might be
swept up was **unfounded** and is recorded here so it is not raised a third time.

**REGISTER DESTINATION:** RULE 8 text change belongs in `CLAUDE.md`; the client-two decision
stays where it already is.

---

## D-10 — HELD-2 POINTS AT A SOURCE THAT CANNOT ANSWER IT. **VERIFIED-FS.**

HELD-2 states the Step 0 / Step 0b verification SQL path "must come from CLAUDE.md's FILE
LOCATIONS section, not a guess." That section, in the authoritative 280-line `CLAUDE.md`,
contains exactly ONE entry: `sql/schema.sql`, described as a point-in-time DDL snapshot. It is
not a path convention and cannot answer HELD-2.

**REGISTER DESTINATION:** HELD-2, amended.

---

## D-11 — A FOURTH NAMESPACE COLLISION, INSIDE THE REGISTER. **VERIFIED-FS.**

OQ-5 documents three colliding "A1/A2" namespaces and points at
`cross_alert_orchestration.md:650` (P2-FINDING 5). Both were read; neither mentions CD-.

`pre_agent_build_checklist.md` has its own CD-1 to CD-16 under "PRE-AGENT C/D GAPS". The
register uses CD-1, CD-2, CD-3 and CD-4 for entirely different things coined in the 2026-07-02
doc-sync, while simultaneously carrying CD-5, CD-8 and CD-14 promoted from the checklist with
their ORIGINAL codes. Same prefix, two meanings, one file:

| Code | Checklist meaning | Register meaning |
|---|---|---|
| CD-1 | Slack workspace created - COMPLETE | Segment-boundary calibration, Phase 2 |
| CD-2 | Evidence Stack message format - COMPLETE | promoted to FC-6 (event calendar) |
| CD-3 | Approve/Snooze/Dismiss wiring - COMPLETE | Klaviyo 0.65 open-rate default |
| CD-4 | `sku_cost_master` populated | Agent D interception check |

**Consequence in the working spreadsheet:** the Legend sheet defines "CD-n | Conditional | Only
matters if some deferred, post-pilot work gets pulled forward", while the same workbook marks
A30 (CD-5) and A31 (CD-8) as blocking with "YES - A14 depends". A reader following the Legend
would deprioritise two items the sheet itself calls blocking.

**Also:** the spreadsheet's `A1`-`A37` is a FIFTH thing labelled "A1", created 2026-07-27, three
days after OQ-5 was last checked (2026-07-24).

**REGISTER DESTINATION:** OQ-5, widened.

---

## D-12 — WORKING SPREADSHEET DEFECTS. **VERIFIED-FS. Spreadsheet only, not the register.**

`pilot_readiness_27072026.xlsx`, sheet "1. Build Sequence", read with openpyxl:
- Block A banner says "23 items". Actual rows A1-A37 = **37**.
- Block C banner says "3 items". Actual rows C1-C5 = **5**.
- Block B says 6, actual 6. Block D / HELD says 3, actual 3.

Cause identified: `state_2026-07-27_pilot_readiness.md:24` says "23 of 32 items need no design
partner (Block A). 6 need first connect. 3 are during/after pilot" — true against the
**116-line** register. The workbook was regenerated from the **151-line** register (Legend
sheet: commit `70fd48f`), rows updated, banner text not.

---

## OPEN ITEMS CARRIED IN, NOT RESOLVED THIS SESSION

- The three F3 interview findings still need register items (returns-versus-CAC challenge to the
  C8 premise; grouping by fit x sleeve; the manual-calling validation). Written up in
  `chat_context_2026-07-28_f3-interview-git-closure.md`.
- HK-2 needs rewriting.
- `technical_architecture.md` documents ~40 `client_config` columns against a live 159.
- The two `client_config` triggers appear in no repo file; behaviour unknown.
- Nothing creates the `client_config` ROW except a fallback in `onboarding_flow.py` (which is
  modified-uncommitted and parked).
- A34 / A35 doc corrections.
- HELD-3 unchanged: free tier now, upgrade before FIRST REAL BRAND CONNECTS for the
  encrypted-backups requirement in `pilot_scope.md` section 6.
- **OQ-1 confirmation pass is still OWED on the committed record.** Searching every file for
  "confirmation pass" returns hits only in the register and the two 2026-07-27 pilot-readiness
  files — nothing in either 2026-07-28 pair. A1 is therefore TWO pieces of work, not one.

## APPROVALS — ALREADY DOCUMENTED, DO NOT DUPLICATE

The approvals sequence is recorded at register **FC-5** (Shopify custom distribution +
`read_all_orders` and the Google Ads developer token first; Meta / Gorgias / Loop second;
TikTok / Klaviyo / Sentry third; entity registration in parallel) and at `pilot_scope.md`
section 6 (per-source access reality, LOCKED 2026-06-13). Writing a second home for it would
create exactly the divergence D-11 describes.

**One thing is genuinely open and belongs in the register:** `pilot_scope.md` section 6 asserts
Meta and TikTok need no own app at pilot scale because Airbyte Cloud offers managed OAuth. That
premise has NOT been confirmed since it was written. **UNVERIFIED.** If it no longer holds, two
further developer-token applications land on the critical path. Confirm before relying on it.

---

## TIME TO PILOT-READY — REVISED

Effort totals computed from the spreadsheet's own "Effort (est.)" column (ranges parsed
directly; "hours" read as 0.25-0.5 day; approximate by construction):
- **Block A: 48.8 - 85.6 working days.** Block B: 4.5 - 8.0. Block C: 4.6 - 8.1.

Those were written on the premise D-1 disproves. Adjusting:

| Change | Delta |
|---|---|
| BT-3: wire the graph -> write Agent B | +8 to +15 d |
| BT-15: assemble Evidence Stack -> write Agent D | +7 to +13 d |
| BT-13: from-scratch -> partial port | -1 to -2 d |
| Agent C folded into D (if OQ-17 resolves that way) | 0 |
| **Revised Block A** | **~63 to 112 working days** |

At a solo cadence of 3-4 build days a week alongside outreach and admin: **roughly 4.5 to 8
months** to the point where one alert can reach a founder by email. Full-time on build only:
~3 to 4 months. **Treat the lower bound as a floor, not a likely case** — the agent-build deltas
are judgement, not derived from any document, and `agent_a.py` at 932 lines is the SIMPLEST of
the four by design (RULE 7: no LLM calls).

**The 6-week beta window in `pilot_scope.md` (dated 2026-06-13) expired on 25 July.** It needs
re-baselining in the same commit that fixes D-1.

**Recruitment has no rate, so it has no number.** 46 cold emails, 0 replies; one warm
introduction produced one interview, against the repo's own bar of 10. Design partners are a
further conversion beyond interviews. Pilot-ready is max(build, recruitment), not the sum —
and recruitment is the side without an estimate. **The binding constraint has not moved.**

---

## SANITY HANDLES

`pilot_readiness_register.md` = **151** · `pilot_scope.md` = 137 · `operating_charter.md` = 308 ·
`pre_agent_build_checklist.md` = 389 · `technical_architecture.md` = 3999 ·
`CLAUDE.md` = **280** · `save_protocol.md` = 149

`agents/agent_a.py` = 932 · `connectors/schema_discovery.py` = 453 ·
`connectors/python_transformer.py` = 500 · `connectors/_harden_public_schema.py` = 276 ·
`slack_bot/` = 572 lines across 5 files

**UNRESOLVED HANDLE — DO NOT TRUST EITHER NUMBER YET.** `product_strategy.md` reads **1439** on
the `/mnt/project/` mount but is recorded as **1440** in both `state_2026-07-27_pilot_readiness.md`
and `state_2026-07-28_f3-interview-git-closure.md`. `CLAUDE.md` showed the same symptom this
session (mount 260, authoritative 280) and the mount was the stale copy, so this is probably the
same — but it was NOT confirmed. Verify against HEAD before using this handle as a tripwire.

`technical_architecture.md` was confirmed IDENTICAL between the mount and the authoritative
uploaded copy (`diff` returns zero lines). The mount is trustworthy for that one file.

---

## NEXT SESSION — LOAD AND SEQUENCE

Load: `save_protocol.md` · `operating_charter.md` · `pilot_readiness_register.md` (151) ·
`pilot_scope.md` · `state_2026-07-28_f3-interview-git-closure.md` · THIS FILE.
Working view of Block A: `pilot_readiness_27072026.xlsx` (37 Block-A rows, banner wrongly says 23).

1. **A1** — OQ-1. Two pieces: the confirmation pass (owed, hours, chat) and the four dials.
2. **A2** — OQ-8, causal-graph completeness. Viable now: `causal_graph.py` exists and is
   auditable, and auditing it should precede writing the agent that traverses it.
3. **Register flush** at session end — D-1 through D-12 above, plus the carried-in items.
4. Approvals: file FC-5's first tier, and confirm the Airbyte OAuth premise.

## STANDING DISCIPLINE

Two-agent split (Claude authors and reviews in chat; Claude Code edits, commits and pushes;
founder authorises every commit). Explicit-path staging only. Never bundle a verification step
with a write step. Locate by quoted text. HK-6 straight ASCII quotes. Mount UNTRUSTED — verify
against HEAD or pasted text. For DATABASE state query the database; for FILE state open the
file; **for CODE state list the directory** — added this session, and it is the whole reason
this file exists.
