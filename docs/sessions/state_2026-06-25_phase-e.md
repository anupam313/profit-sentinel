# Profit Sentinel — State — 2026-06-25 — Phase E (suppression_log canonicalization, R13)
## Session: Phase E — make public.suppression_log the single authoritative table
## Status: Phase E CORE COMPLETE + committed (Step 2 `d19ef53`, Step 3 `dcbad92`). Steady state live. No push.

---

## NEXT SESSION — LOAD FIRST

**Load:** docs/save_protocol.md FIRST (authoritative; 149 lines), then CLAUDE.md,
docs/technical_architecture.md, docs/product_strategy.md, and this state file's companion
`chat_context_2026-06-25_phase-e.md`.

**Canonical line-count handles (UNCHANGED this session — Phase E edited NO canonical spec, only
code + this continuity pair. HEAD is source of truth; do NOT false-alarm on mount drift):**
```
product_strategy            1424
technical_architecture      3971
agent_d_build_spec          2722
cross_alert_orchestration    847
d1_validation_gates          399
pre_agent_build_checklist    389
save_protocol                149
pilot_scope                  122
CLAUDE.md                    260
```

**Repo state:** HEAD `dcbad92`, unpushed stack (push as ONE coherent set later — not piecemeal):
```
dcbad92  Phase E Step 3: drop client_azure_co.suppression_log + its DDL — canonicalization complete
d19ef53  Phase E Step 2: repoint suppression_log to public (remove client write, retarget gate); RLS deferred
18d9274  Session 2026-06-24: Phase D — state + context
2863e5c  Phase D (R11): make data-integrity controls real
5724469  Session 2026-06-24: Phase C boundary — state + context
fe8725b  Phase C: is_synthetic real/synthetic boundary for the Shopify spine
8292b02  WIP checkpoint: Session-3/B-9/B-4 mart columns + customer-segments mart (pre-Phase-C)
2c04e76  Session 2026-06-24: R9 double-seed healed + committed
eb21af2  R9: make seed_shopify idempotent; heal double-seed
a307b81  Session 2026-06-22: SKU-namespace contract Pass One state + context
8a707a1  SKU-namespace contract conform: cost seed reads catalog as cost universe
ae8a2d5  Session 2026-06-22: taxonomy-versioning foundation state + context
b8fec19  Taxonomy versioning foundation: pin 2026-05 + resolve/stamp + H21 drift
```
**Stack depth — RECONCILE LIVE:** this lists 13 commits above remote `7d5c2e7` (Phase D left 11;
Phase E added Step 2 + Step 3 = 13). The Phase-D file's 10-vs-11 note resolved to 11 at `18d9274`.
Confirm with `git rev-list --count 7d5c2e7..HEAD` before the coherent push — a quiet off-by-one
matters when the stack is pushed as one set.

**Working tree is NOT clean** (factual note — out of Phase E scope): undisposed Group B remains —
`connectors/seed_meta.py` (M), `onboarding_flow.py` (M), and untracked `connectors/_*.py` probes
(incl. `_dryrun_determinism.py`, whose Phase-E call-removal edit is on disk but UNTRACKED by design —
Option C), `connectors/historical_pattern_scan.py`, `connectors/seed_b4_patch.py`,
`connectors/seed_google_ads.py`, `slack_bot/`, and the pre-existing `docs/sessions/*` files (plus
this new pair until it is committed). Disposition not yet ruled. **Phase E honored Option C:** stage
by explicit path only; never `git add -A`/`.`; no Group B file entered either Phase E commit.

**Live DB steady state:** `public.client_config.use_synthetic_data = TRUE`. `mart_causal_chain_daily`
= 730 rows / sum(order_count) = 84230. No mart reads raw `shopify_*`. **`public.suppression_log` = 29
rows (sole authoritative table); `client_azure_co.suppression_log` DROPPED.**

**TWO DISTINCT identifiers (do not conflate — carried from Phase C):** the dbt var `client_id` =
`'client_azure_co'` (matches the `public.client_config` PK row; used in the RULE-3 staging filter's
scalar subquery, single-row-safe). The seed's Python constant `CLIENT_ID` = `'azure_co'` (used in
`seed_shopify.py` f-string queries). The schema is `client_azure_co` for raw/staging in all cases.
**VERIFY (routed, not asserted): these two values differ across tables** (client_config.client_id =
`client_azure_co` vs seed app-table rows written with `azure_co`). Nothing broken now; a cross-table
join on `client_id` would mismatch. Confirm intentional/safe in a future pass (O-26 / canonical pass).
NOTE: `public.suppression_log` now uses `client_id='azure_co'` (connector-seeded) — its prior
client-schema copy is gone, so the suppression_log half of this split is resolved to public-only.

**Deliberation mode:** tag load-bearing claims [verified—file:line] / [inference] / [guess]; verify
THIS turn in Claude Code, never from memory or the mount; one item at a time with sign-off; design in
chat, build in Claude Code (read-only mount; no repo/DB/git from chat); continuity files are authored
in chat, then Claude Code VERIFIES (does not author) them.

**NEXT ACTION:** decide the **RLS-posture sub-step** on `public.suppression_log` (deferred Option 4 —
RLS still DISABLED, a standing RULE 8 gap; founder picks blanket `USING(true)`-now vs the project's
first `client_id`-isolation policy-later), then **Phase F — R10 build validate_sync.py**. Open in a
NEW chat per the per-session cadence.

---

## WHAT THIS SESSION ACTUALLY DID (in one breath)
Led with a read-only discovery pass on both suppression_log tables, which surfaced that the canonical
`technical_architecture.md` (§3.1/§3.2) explicitly assigns application tables to `public` and the
per-client schema to raw+staging only — so `client_azure_co.suppression_log` was undocumented DRIFT,
NOT the canonical home. That REVERSED the prior plan's "pick the richer client_azure_co" direction
(case b). Canonical = `public.suppression_log` (where Agent A — the production writer — already writes,
where the Supabase API roles + the dedup unique key live). Confirmed the retraction/provisional columns
that made the client table "richer" are Horizon-2 (no fired pilot alert needs them; C2 uses two
alert_log rows), so chose to DROP, not widen. Executed in three gated steps: Step 1 read-only confirm;
Step 2 (`d19ef53`) non-destructive — removed seed_shopify's redundant client write, retargeted the
Phase-D seed gate to public (band centre 29 → `[21,40]`, non-vacuous), updated the test helper, RLS
deferred; Step 3 (`dcbad92`) the gated irreversible DROP of the client table + its DDL. No push.

---

## PHASE 0 — DECISION LEDGER (read from this session)

| # | Decision (plain) | Target | Landed |
|---|---|---|---|
| E1 | Canonical = `public.suppression_log`; `client_azure_co.suppression_log` is undocumented drift → DROP it. CORRECTION (case b) of the prior "pick the richer client_azure_co" plan. Grounded: tech-arch §3.1/§3.2 (app tables in public; per-client schema = raw+staging), Agent A writes public, API roles + dedup key on public. | this state file (corrects prior line 203) + DB | ✅ `dcbad92` |
| E2 | Do NOT widen public with the 6 client-only retraction/provisional cols — Horizon-2. No fired pilot alert needs them; C2 (influencer ROI) uses two `alert_log` rows, not these cols. | this state file + ROUTING | ✅ (no widen) |
| E3 | RLS on `public.suppression_log` DEFERRED (Option 4) — still DISABLED (RULE 8 gap). PLUS: live repo has NO `client_id`-isolation RLS pattern (only alert_log + thread_context carry policies, both `USING(true)`); RULE 8's stated client_id ideal ≠ implementation → a pre-existing gap, NOT resolved here. | OWED items + ROUTING | ✅ deferred + recorded |
| E4 | Group B handled by Option C — stage Phase E by explicit path; `_dryrun_determinism.py` (untracked probe) left UNTRACKED; no catch-all `git add`. | this state file (Group B note) | ✅ both commits |
| E5 | Phase-D seed gate retargeted from `client_azure_co` → `public`: presence-band centre 29 (24 tiktok + 3 sentry + 2 loop) → `_band(29)=[21,40]`, kept CRITICAL + NON-VACUOUS (fails on empty); Check #10 rewritten to `public`, `suppression_stack` predicate DROPPED (client-only col), floor `>=20`. | connectors/seed_shopify.py | ✅ `d19ef53` |
| E6 | Phase E core DONE in 3 gated steps (read-only → non-destructive commit → gated drop). seed_shopify no longer writes suppression; `_create_seed_tables.py` client DDL removed. `public.suppression_log` sole home (29 rows, connector-seeded). | connectors/seed_shopify.py + _create_seed_tables.py + _dryrun_determinism.py + DB | ✅ `d19ef53` + `dcbad92` |

The Phase-A manifest for the CODE work = the 3 touched files across the two commits (seed_shopify.py,
_create_seed_tables.py committed; _dryrun_determinism.py edited-but-untracked per Option C). This
continuity pair is the only artifact of THIS session-close save. No decision left without a target.

### ROUTED / OWED items (recorded here so they do not evaporate)
1. **Cancelled/voided narrowing (OWED — pre-pilot).** Confirm no alert keys off
   `discount_order_rate_90d` / `units_sold` (narrowed by the Phase C mart re-route). UNCHANGED.
2. **Toggle-form divergence (reconciliation phase).** meta/ga4/sentry staging use the dbt-var form;
   Shopify uses the per-client `client_config` form. UNCHANGED.
3. **loop_return_line_items (Loop-connector boundary phase).** No `is_synthetic`;
   `mart_return_rate_by_sku` reads it raw. UNCHANGED.
4. **stg_shopify_inventory_items — RESOLVED in Phase D** (recorded for continuity). UNCHANGED.
5. **Airbyte sync-mode (founder UI action) — INFORMED in Phase D.** Airbyte DORMANT on
   `client_azure_co`; DEBT-006 raw-constraint clobber risk LATENT not active. Founder still to confirm
   per-connection sync mode in Airbyte Cloud before real cutover. UNCHANGED.
6. **Group B working-tree disposition** — full disposition STILL not ruled. Phase E applied Option C
   (stage-by-name; probe left untracked) but did NOT clean Group B. The real per-file decision (delete
   probes / commit real WIP / track docs+slack_bot) is its own near-term housekeeping pass.
7. **klaviyo shape-split (Klaviyo connector boundary, with Loop item 3).** Live klaviyo raw tables are
   Airbyte-native with no stable key; stg models read clean derived sources, so tests are sound.
   UNCHANGED.
8. **Pre-existing hygiene.** (a) seed_shopify.py double-encoded em-dash mojibake (confirmed again in
   Phase E — the file has non-ASCII box/dash bytes; edits were made byte-safe); (b) check #8 reads
   `public.alert_log` without a `client_id` filter (harmless floor check). Fold into hygiene cleanup.
9. **Stack-depth reconcile.** Now 13 above remote `7d5c2e7` — confirm live before the push.
10. **RLS-posture sub-step (NEW — from E3).** `public.suppression_log` RLS disabled; decide
    blanket-`USING(true)`-now vs first `client_id`-isolation-policy-later (net-new design: needs a
    session-context mechanism — JWT claim / GUC — that does not exist yet). Founder decision owed.

---

## WHAT WAS BUILT (Phase E — 2 commits)
**Step 2 `d19ef53`** (connectors/seed_shopify.py +15/−182; _dryrun_determinism.py edited-untracked):
- Removed `seed_suppression_log` (def ~2345, the 173-line banner+function) and its Step-12 call (~2790)
  in seed_shopify.py — its client rows were redundant write-only fixtures with zero readers.
- Retargeted the two Phase-D gate entries to `public`: presence-band row (centre 29, `[21,40]`,
  CRITICAL, non-vacuous); Check #10 rewritten to `SELECT COUNT(*) FROM public.suppression_log WHERE
  client_id='azure_co'` with `>=20` (dropped the client-only `suppression_stack` predicate).
- Updated `_dryrun_determinism.py:44` to drop the removed `s.seed_suppression_log(cur)` call (on disk,
  untracked — Option C).
- GUARD honored: `seed_loop_returns.seed_suppression_log` (the same-named **public** S17 writer) and
  `seed_tiktok.seed_suppression_log_s14` (public S14) left untouched.

**Step 3 `dcbad92`** (connectors/_create_seed_tables.py +4/−34):
- `DROP TABLE client_azure_co.suppression_log` (no CASCADE; fired only after 4 read-only prechecks).
- Removed the orphaned `CREATE TABLE client_azure_co.suppression_log` block + 2 stale docstring mentions
  in `_create_seed_tables.py`.

**Proofs (all green; keeper never disturbed):** Step-2 S2-VERIFY 5/5 (public=29; gate non-vacuous,
`0∉[21,40]` fails empty; client table still 10, safety net intact; loop twin untouched; both compile).
Step-3 S3-PRECHECK 4/4 (HEAD=d19ef53; keeper=29; only ref was the DDL file; client=10) → DROP →
S3-VERIFY 5/5 (`to_regclass` NULL; keeper still 29; re-seed 0-critical and did NOT recreate the table;
retargeted gate non-vacuous; compile clean, zero residual references). Step-1 golden-hash check: NO
tracked baseline hashes the client suppression content.

---

## KEY CORRECTIONS THIS SESSION (stale priors reversed — named, not silently updated)
- **Phase E direction REVERSED (case b — under-tested prior).** The prior state file (line 203) said
  "pick the richer (client_azure_co) schema as canonical; migrate the public connector rows." That
  inverted the architecture: tech-arch §3.1/§3.2 assigns application tables (suppression_log among them)
  to `public`, and the per-client schema to raw+staging only. `client_azure_co.suppression_log` never
  appears in ANY canonical doc — it was drift. Canonical = `public.suppression_log`; client table
  dropped. The "richer" heuristic chose drift over the documented home. [verified—tech-arch §3.1/§3.2]
- **Writer map for suppression_log SUPERSEDED.** Prior (line 189–191): "client_azure_co.suppression_log
  = seed_shopify ONLY; public.suppression_log = connectors-only." Now: the client table is GONE;
  `public.suppression_log` is the sole table, written by 3 connector seeds (tiktok S14=24, sentry
  S24=3, loop S17=2 = 29) **plus Agent A** (the production writer, `agent_a.py:651`, not yet run). The
  prior map's omission of Agent A as a public writer was wrong. [verified—Phase E Step-1 C2]
- **D7/D8/#10 suppression_log specifics SUPERSEDED.** Phase D's #10 + presence-band targeted
  `client_azure_co.suppression_log` (centre 10, `suppression_stack` predicate). E5 retargeted both to
  `public` (centre 29). The Phase-D entries remain historically true for that commit; the LIVE gate is
  the E5 form.

---

## RECON FACTS THAT REMAIN VALID (design inputs for Phase F; verified read-only)
- **G1 seed-isolating predicates** — UNCHANGED from Phase C (products `product_type ∈ {top, dress,
  short, knit, outerwear, denim, formal, mens}`; variants `sku ~ '^AZ-[A-Z]+-[0-9]+'`;
  customers/orders/refunds/fulfillments `id<1e12`; line_items `order_id<1e12`; etc.).
- **G4** — at HEAD `order_line_items.id` IS unique; `klaviyo_email_events` keys on `message_id`.
- **Writer map (UPDATED this session):** alert_log = 8 writers (multi); brand_event_calendar = 4
  (multi); dq_metric_scores = 2 (shopify+gorgias, multi); **`public.suppression_log` = 3 connector
  seeds (tiktok/sentry/loop) + Agent A (production); `client_azure_co.suppression_log` GONE.**
- **public.suppression_log shape:** 20 cols, `id bigint GENERATED ALWAYS AS IDENTITY` PK, dedup key
  `uq_suppression_log_signal (client_id, alert_type, would_have_fired_at)`, RLS DISABLED (owed).

---

## HARDENING PHASES (forward plan — separate gated commits)
- **Phase A — R9 idempotency + heal — DONE, `eb21af2`.**
- **Phase B — Egnition island — DONE: KEPT.**
- **Phase C — is_synthetic boundary (RULE 3) — DONE, `fe8725b`.**
- **Phase D — make controls real (R11) — DONE, `2863e5c`.**
- **Phase E — R13 suppression_log canonicalization — CORE DONE, `d19ef53` + `dcbad92`.** Canonical =
  `public.suppression_log` (CORRECTED from the prior "client_azure_co canonical" plan); client table
  dropped; gate retargeted. OWED tail: the RLS-posture sub-step (deferred Option 4).
- **Phase F — R10 build validate_sync.py** (the absent post-sync variance guard) — NEXT after the RLS
  decision.
- **THEN — canonical state-file corrections pass** (the 9 corrected facts from the R9 session +
  D-A..D-F landings), written once under the save protocol. Source: `state_2026-06-24_r9-heal-committed.md`.

---

## LOCKED DECISIONS (carry forward; do NOT reopen) — from 06-23
- D-A: two-bar connector model.
- D-B: Bar-2 fired sources = Shopify / Gorgias / Meta / Google Ads / TikTok; cost is plumbing.
- D-C: Loop / Klaviyo / GA4 / Sentry opportunistic.
- D-D: Loop fallback until Shopify-native returns proven.
- D-E: weekly founder digest IN pilot via email through the relevance gate (DOC CONFLICT: canonical
  docs vs Horizon-2 — reconcile in the canonical pass).
- D-F: HARD 7-condition pre-pilot gate (incl. a deliberate fault-injection drill).
- D-G: hardening ranks ahead of Pass Two / C8 / taxonomy; Pass Two folded into hardening.

---

## ROUTING (future passes — recorded so they don't evaporate)
- Canonical-doc landings for D-A..D-F (incl. the D-E Horizon-2 conflict) + the 9 R9 corrected facts →
  the later canonical save-protocol pass. STILL OPEN.
- O-26 full design-consistency / doc-vs-DB audit → scheduled, separate cadence. STILL OPEN. (CLAUDE.md's
  "public schema" list names 6 tables; live DB has 14 (Phase-E RLS inspection; prior note said 15) — a doc-drift item for this audit.)
- validate_seed heavy-aggregation timeout → PARTIALLY MITIGATED by Phase D D9; query tuning / faster
  connection STILL OPEN.
- client_id value split (client_config `client_azure_co` vs seed app-table rows `azure_co`) → verify
  intentional/safe (O-26 / canonical pass). suppression_log half is now resolved (public-only, `azure_co`);
  the split remains for other app tables. STILL OPEN.
- Toggle-form divergence (var-form vs client_config-form) → reconciliation phase.
- klaviyo raw shape-split → Klaviyo connector boundary (with Loop boundary).
- Pre-existing hygiene (seed_shopify.py mojibake; #8 alert_log client_id filter) → hygiene cleanup.
- RLS-posture sub-step + the RULE-8-vs-implementation gap (no client_id-isolation policy live) → the
  RLS decision (next), and the broader RULE 8 reconciliation → O-26 / canonical pass.
- Pass Two (SKU-contract assertion) → folded into hardening per D-G; Pass-One contract intact.
- C8 HERO return-driver alert + taxonomy versioning → Horizon items, not this stream.

---

## HORIZON / FLAGS (do not chase next session)
- Unpushed local stack (HEAD `dcbad92`; 13 commits, reconcile live) — one coherent push later. Bulk
  transfer over this machine's link is unreliable; small-commit push is fine; bulk dump/restore needs a
  stable network / cloud shell near AWS us-east-1.
- OneDrive corruption risk on the repo path — ongoing; stop-don't-force on lock errors.
- **Project-mount staleness PERSISTS:** at this session's open the mounted tech-arch was still 3815
  (HEAD 3971); founder uploaded the live tech-arch + product_strategy into chat to design against HEAD.
  STILL OWED: re-upload CLAUDE.md + technical_architecture.md (+ product_strategy.md) to the Project so
  future sessions inherit the live copies.
- The systemic story: the platform had the RIGHT controls designed but historically NONE in the
  enforcement path. Phase C moved RULE 3 in; Phase D moved R11 in. Phase E removed a schema-drift
  ambiguity (one authoritative suppression_log). Phase F (R10 sync guard) still owed.
- Backup `ps_full.dump` exists on disk (D:\ps_backups\, golden) — valid R9 restore point.

---

## FILES TO SAVE / UPLOAD THIS SESSION
- state_2026-06-25_phase-e.md (this file) — ADDED (new dated name).
- chat_context_2026-06-25_phase-e.md (paired narrative) — ADDED.
- No canonical spec edited in Phase E; the code already committed (`d19ef53`, `dcbad92`).
Save → (founder approves text) → Claude Code VERIFIES (does not author) → commit the two continuity
files only (message: "Session 2026-06-25: Phase E — state + context") → re-upload the pair to the
Project. ALSO still owed: re-upload CLAUDE.md + technical_architecture.md + product_strategy.md (mount
stale). NO push.

## SANITY HANDLES (real post-edit counts — Check 9)
- state_2026-06-25_phase-e.md: 273 lines
- chat_context_2026-06-25_phase-e.md: 88 lines
(As-authored counts. Claude Code: re-run `wc -l` on both committed files and confirm they equal these —
if a mounted/committed copy differs, the wrong copy landed → STOP.)
