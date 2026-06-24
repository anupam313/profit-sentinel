# Profit Sentinel — State — 2026-06-24 — Phase D (make controls real, R11)
## Session: Phase D — controls into the enforcement path (dbt staging tests + pre-commit seed gate)
## Status: Phase D COMPLETE + committed (2863e5c). Steady state live. No push.

---

## NEXT SESSION — LOAD FIRST

**Load:** docs/save_protocol.md FIRST (authoritative; 149 lines), then CLAUDE.md,
docs/technical_architecture.md, docs/product_strategy.md, and this state file's companion
`chat_context_2026-06-24_phase-d.md`.

**Canonical line-count handles (verified this session against the committed files — do NOT
false-alarm on mount drift; HEAD is source of truth):**
```
product_strategy            1424
technical_architecture      3971   <- changed this session (was 3947) — §10 Phase D block + date stamp
agent_d_build_spec          2722
cross_alert_orchestration    847
d1_validation_gates          399
pre_agent_build_checklist    389
save_protocol                149
pilot_scope                  122
CLAUDE.md                    260   <- changed this session (was 214) — RUN PATH section
```

**Repo state:** HEAD `2863e5c`, unpushed stack (push as ONE coherent set later, after hardening
lands — not piecemeal):
```
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
**Stack depth — RECONCILE:** this lists 10 commits above remote `7d5c2e7`; Claude Code reported
"11-deep" after the Phase D commit. Confirm the true count next session with
`git rev-list --count 7d5c2e7..HEAD` before the coherent push — a quiet off-by-one here matters
when the stack is pushed as one set.

**Working tree is NOT clean** (factual note — out of Phase D scope): undisposed Group B remains —
`connectors/seed_meta.py` (M), `onboarding_flow.py` (M), and untracked `connectors/_*.py` probes,
`connectors/historical_pattern_scan.py`, `connectors/seed_b4_patch.py`,
`connectors/seed_google_ads.py`, `slack_bot/`, and the pre-existing `docs/sessions/*` files (plus
this new pair until it is committed). Disposition not yet ruled.

**Live DB steady state:** `public.client_config.use_synthetic_data = TRUE`. `mart_causal_chain_daily`
= 730 rows / sum(order_count) = 84230. No mart reads raw `shopify_*`.

**TWO DISTINCT identifiers (do not conflate — carried from Phase C):** the dbt var `client_id` =
`'client_azure_co'` (matches the `public.client_config` PK row; used in the RULE-3 staging filter's
scalar subquery, single-row-safe). The seed's Python constant `CLIENT_ID` = `'azure_co'` (used in
`seed_shopify.py` f-string queries — e.g. checks #9/#10 `WHERE client_id = '{CLIENT_ID}'` on
dq_metric_scores / suppression_log). The schema is `client_azure_co` in all cases. **VERIFY (routed,
not asserted): these two values differ across tables** (client_config.client_id = `client_azure_co`
vs seed app-table rows written with client_id = `azure_co`). Each query matches its own table today,
so nothing is broken now — but any cross-table join on `client_id` would mismatch. Confirm the split
is intentional/safe in a future pass (O-26 audit or the canonical pass); do NOT chase here.

**Deliberation mode:** tag load-bearing claims [verified—file:line] / [inference] / [guess]; verify
THIS turn in Claude Code, never from memory or the mount; one item at a time with sign-off; design in
chat, build in Claude Code (read-only mount; no repo/DB/git from chat); continuity files are authored
in chat, then Claude Code VERIFIES (does not author) them.

**NEXT ACTION:** pre-pilot hardening **Phase E — R13 suppression_log canonicalization** (see HARDENING
PHASES). Do NOT start until directed. Open Phase E in a NEW chat per the per-session cadence.

---

## WHAT THIS SESSION ACTUALLY DID (in one breath)
Led with a read-only Phase D discovery pass, then made the data-integrity controls real and put them in
the enforcement path: added dbt staging uniqueness/not_null tests for the 5 previously-untested stg
models (composite keys tested via NATIVE singular tests — no surrogate column, no cast, per RULE 4);
made `dbt build` (run + test) the canonical post-seed dbt command and recorded it in CLAUDE.md;
relocated `validate_seed()` to run PRE-commit with a conditional commit (critical failure → rollback +
exit), split its checks by OWNERSHIP (gate only on integrity seed_shopify owns), and made the critical
checks blip-resilient (statement_timeout + per-check SAVEPOINT + retry-once on timeout); declined unique
constraints on the Airbyte-managed raw Shopify tables (DEBT-006 — durable uniqueness lives in staging
tests + the seed gate). Committed at `2863e5c` (6 files, +278/−30). RULE 9 doc-sync landed in the same
commit (tech-arch §10 + CLAUDE.md RUN PATH). No push.

---

## PHASE 0 — DECISION LEDGER (read from this session)

| # | Decision (plain) | Target | Landed |
|---|---|---|---|
| D1 | Add dbt staging tests for the 5 untested stg models: single-key models (stg_klaviyo_flows.flow_id, stg_klaviyo_profiles.profile_id, stg_shopify_inventory_items.inventory_item_id) get `unique+not_null`; composite models get `not_null` on each key col | warehouse/models/staging/schema.yml | ✅ `2863e5c` |
| D2 | Composite uniqueness via NATIVE singular tests (dbt_utils ABSENT; no surrogate column, no `::text` cast — RULE 4) | warehouse/tests/assert_unique_stg_shopify_inventory_levels.sql + assert_unique_stg_synthetic_touchpoint_journey.sql (new) | ✅ `2863e5c` |
| D3 | `dbt build` (run+test) is the canonical post-seed dbt command; gate is order-independent (no orchestrator built — scope-creep pre-pilot); run-path documented | CLAUDE.md (RUN PATH section) | ✅ `2863e5c` |
| D4 | Relocate `validate_seed()` PRE-commit; commit conditional on no critical failure (else rollback + sys.exit(1)); keep the existing 11 checks; rollback logs in the RULE 5 format (gate is NOT itself RULE 5) | connectors/seed_shopify.py (validate_seed + main) | ✅ `2863e5c` |
| D5 | Add per-key uniqueness (COUNT==DISTINCT) + presence-band (centers = R9 healed counts; integer `_band`: lower `max(1,⌈0.7c⌉)`, upper `⌊1.4c⌋`) for seed-owned tables; BEC dup-excess ≤ 2 | connectors/seed_shopify.py | ✅ `2863e5c` |
| D6 | OWNERSHIP split (gate only on what seed_shopify owns): CRITICAL = spine band+uniqueness, content #1/#2/#3/#5/#7/#11; ADVISORY = #4 (pre-existing tautology, unchanged) + genuinely cross-source #6 (sku_cost) + #9 (dq 7-sources) + multi-writer presence>0 | connectors/seed_shopify.py | ✅ `2863e5c` |
| D7 | Promote #8 (alert_log Alert3) + #10 (client suppression_log) to CRITICAL — verified seed-owned/connector-independent (seed writes Alert3 at 2148/2172; client_azure_co.suppression_log single-writer). Live data: #8=57≥40, #10=4≥3 (CLIENT_ID='azure_co'). | connectors/seed_shopify.py | ✅ `2863e5c` |
| D8 | Multi-writer shared tables (alert_log, brand_event_calendar, dq_metric_scores) keep CRITICAL uniqueness/dup-excess but band is advisory (order-independent); single-writer client_azure_co.suppression_log keeps tight band | connectors/seed_shopify.py | ✅ `2863e5c` |
| D9 | RESILIENCE: `SET LOCAL statement_timeout ~120s` for validation; per-check SAVEPOINT; data-assertion false → FAIL → full rollback; exception/timeout → ROLLBACK TO SAVEPOINT + retry once; persistent ERROR on a critical check → full rollback (RULE 6 timeout guard) | connectors/seed_shopify.py | ✅ `2863e5c` |
| D10 | Add NO unique constraints to Airbyte-managed raw Shopify tables (DEBT-006 / tech-arch 705/726/1175); no genuine public.* gap. Durable uniqueness = staging tests (D1/D2) + seed gate (D4–D9). | CLAUDE.md RUN PATH ("NOT raw constraints") + this state file | ✅ none added |
| D11 | RULE 9 doc-sync: tech-arch §10 Build Sequence marks R11/Phase D controls in-path; tech-arch "Last updated" stamped 2026-06-24 | technical_architecture.md §10 + header | ✅ `2863e5c` |

The Phase-A manifest = exactly the 6 committed files; every decision above lands in one of them. No
decision left without a target.

### ROUTED / OWED items (recorded here so they do not evaporate)
1. **Cancelled/voided narrowing (OWED — pre-pilot).** Confirm no alert keys off
   `discount_order_rate_90d` / `units_sold` (narrowed by the Phase C mart re-route). UNCHANGED from Phase C.
2. **Toggle-form divergence (reconciliation phase).** meta/ga4/sentry staging still use the dbt-var
   form; Shopify uses the per-client `client_config` form. UNCHANGED from Phase C.
3. **loop_return_line_items (Loop-connector boundary phase).** No `is_synthetic`; `mart_return_rate_by_sku`
   reads it raw. UNCHANGED from Phase C.
4. **stg_shopify_inventory_items — RESOLVED this session (recorded for continuity).** Was Phase C
   "no action; reported" (island-only, 1 real non-AZ row, seed does not write it). Phase D added its
   `inventory_item_id unique+not_null` test (D1) — tests pass on the 1-row island, no synthetic
   assumption. Numbering preserved from Phase C so cross-references stay valid.
5. **Airbyte sync-mode (founder UI action) — now INFORMED.** Phase D Step 4 found Airbyte DORMANT on
   `client_azure_co`: no `airbyte*` schemas/state tables; `_airbyte_generation_id=0` for every row
   (seed constant); `_airbyte_extracted_at` static/stale (synthetic max 2026-05-31; island 2026-06-08).
   So the DEBT-006 raw-constraint clobber risk is LATENT, not active. Founder still to confirm
   per-connection sync mode in Airbyte Cloud before real cutover; predicates assume real ids ≥ 1e12 and
   real SKUs stay non-`AZ-`. (This is the canonical "routed-item-5" referenced in the charter.)
6. **Group B working-tree disposition** — not yet ruled. UNCHANGED from Phase C.
7. **klaviyo shape-split (NEW this session — route).** Live `klaviyo_profiles` / `klaviyo_flows` /
   `klaviyo_campaigns` are Airbyte-native (`id, type, links, attributes`), `id` ~all NULL, only
   non-deterministic `_airbyte_raw_id` is unique → no stable key; they do NOT match seed_klaviyo.py's
   flat DDL/INSERT. Cannot take a meaningful constraint as-is. NOTE: the stg models
   (stg_klaviyo_flows/profiles) are built from clean derived sources (email_events / shopify_customers),
   NOT these broken raw tables — so D1's tests are sound. Address the raw shape-split at the Klaviyo
   connector boundary (with Loop, item 3).
8. **Pre-existing hygiene (NEW — route, do not chase).** (a) `connectors/seed_shopify.py` has mixed
   double-encoded em-dash mojibake (`â€"`) in some pre-existing lines; (b) check #8 reads `public.alert_log`
   without a `client_id` filter (mild RULE 2 untidiness; harmless as a floor check — cross-client rows can
   only over-satisfy ≥40, never false-fail). Fold into a future hygiene cleanup.
9. **Stack-depth reconcile (NEW).** See NEXT SESSION repo-state note — confirm 10 vs 11 before the push.

---

## WHAT WAS BUILT (Phase D, commit 2863e5c — 6 files, +278/−30)
- `warehouse/models/staging/schema.yml` — +5 model entries (3 single-key `unique+not_null`; 2 composite
  models `not_null` on each key col; uniqueness via singular tests).
- `warehouse/tests/assert_unique_stg_shopify_inventory_levels.sql` (new) — `group by inventory_item_id,
  location_id having count(*)>1`.
- `warehouse/tests/assert_unique_stg_synthetic_touchpoint_journey.sql` (new) — `group by order_id,
  touchpoint_sequence having count(*)>1`.
- `CLAUDE.md` — RUN PATH section: seeds (manual, each idempotent), then `dbt build` from warehouse/ as
  canonical (NEVER ship on `dbt run` alone — skips tests); gate is order-independent; uniqueness enforced
  at staging tests + seed gate, NOT raw constraints.
- `docs/technical_architecture.md` §10 — Phase D (R11) controls IN-PATH block; header "Last updated"
  stamped 2026-06-24.
- `connectors/seed_shopify.py` — `_band` + `SEED_TABLE_SPECS`; `validate_seed()` pre-commit relocate +
  ownership/criticality split + per-key uniqueness + presence-band + BEC dup-excess + savepoint/timeout
  resilience; `main()` conditional commit (rollback + exit on critical failure). `ast.parse` clean.

**Proofs (all green, nothing persisted):** `dbt build` 5 models + 2 singular tests PASS; full staging
suite 51 tests PASS / 0 ERROR (prior `stg_shopify_net_sales_validation` ERROR resolved by
build-before-test); fault-injection (a) current data → COMMIT, (b) doubled discount_codes (13→26) →
critical band+uniqueness fail → ROLLBACK + exit, restored to 13. Save-protocol Check 10 (semantic
read-back) + Check 4 (no live "RULE 5" gate label) + Check 2 (tech-arch date stamp) passed pre-commit.

---

## KEY CORRECTIONS THIS SESSION (stale priors reversed — named, not silently updated)
- **G4 was STALE (supersedes the Phase C RECON G4 fact).** Phase C recorded `order_line_items.id` NOT
  unique + `klaviyo_email_events.message_id` 374 collisions. Live at HEAD both are FULLY UNIQUE
  (line_items.id 137006/137006; message_id 67840/67840; email_events has no `id` column). Phase D
  therefore only ADDS tests on already-clean keys; no surrogate invention needed. [verified—Phase D discovery]
- **Constraint surface reframed (case (a) — new fact: tech-arch 705/726/1175 + CLAUDE.md RULE 3/DEBT-006).**
  Raw Shopify tables are Airbyte-managed → raw-table constraints are not a durable control. Durable
  uniqueness moved to staging tests + the seed gate.
- **Composite-test method reversed (case (a) — RULE 4).** Surrogate-column approach needs `::text` casts →
  violates RULE 4; replaced with native singular tests (no model edit, no cast).
- **#8/#10 ownership corrected (case (b) — under-tested prior).** Initially listed advisory from the RULE 3
  label; verified writer map shows both seed-owned → promoted to CRITICAL.

---

## RECON FACTS THAT REMAIN VALID (design inputs for Phases E–F; verified read-only)
- **G1 seed-isolating predicates** — UNCHANGED from Phase C (products `product_type ∈ {top, dress,
  short, knit, outerwear, denim, formal, mens}`; variants `sku ~ '^AZ-[A-Z]+-[0-9]+'`;
  customers/orders/refunds/fulfillments `id<1e12`; line_items `order_id<1e12`; inventory_levels NOT 13+
  digit; touchpoint non-13-digit order_id; pii `synthetic_customer_id<1e12`; discount 12-seed-list;
  discount id deterministic `920_000_000+seq`).
- **G4 (CORRECTED — see KEY CORRECTIONS):** at HEAD, `order_line_items.id` IS unique; `klaviyo_email_events`
  keys on `message_id` (unique; no id column). The old "not unique / 374 collisions" reading is retired.
- **R11 untested staging — DONE this session** (the 5 stg models now carry tests; `dbt build` wires them in).
- **Writer map (verified live):** alert_log = 8 writers (multi); brand_event_calendar = 4 writers (multi);
  dq_metric_scores = 2 writers shopify+gorgias (multi); client_azure_co.suppression_log = seed_shopify ONLY
  (single); public.suppression_log = connectors-only. #8/#10 target seed-owned rows.

---

## HARDENING PHASES (forward plan — separate gated commits)
- **Phase A — R9 idempotency + heal — DONE, committed eb21af2.**
- **Phase B — Egnition island purge vs keep — DONE: KEPT** (boundary test fixture).
- **Phase C — is_synthetic boundary (R6 / RULE 3) — DONE, committed fe8725b.** Island gate PASS
  (toggle OFF → 0 synthetic survivors across the 5 stg views, island intact; full PASS table preserved
  in `state_2026-06-24_phase-c-boundary.md`).
- **Phase D — make controls real (R11) — DONE, committed 2863e5c.** dbt staging tests + pre-commit seed
  gate in the enforcement path; raw-constraint path declined (DEBT-006).
- **Phase E — R13 suppression_log canonicalization — NEXT.** Pick the richer (client_azure_co) schema as
  canonical; migrate the public connector rows; repoint all writers; one home. (Writer map above is a
  design input: client schema = seed-only, public = connectors-only.) Do NOT start until directed.
- **Phase F — R10 build validate_sync.py** (the absent post-sync variance guard).
- **THEN — canonical state-file corrections pass** (the 9 corrected facts from the R9 session +
  D-A..D-F landings), written once under the save protocol (Checks 4/7/8/10/11). The 9 corrected facts
  live in `state_2026-06-24_r9-heal-committed.md` (CORRECTED FACTS section) — that file is the source.
  Phase C landed RULE 3 + tech-arch §3.3/§7 early; Phase D landed §10 + CLAUDE.md RUN PATH early.

---

## LOCKED DECISIONS (carry forward; do NOT reopen) — from 06-23
- D-A: two-bar connector model.
- D-B: Bar-2 fired sources = Shopify / Gorgias / Meta / Google Ads / TikTok; cost is plumbing.
- D-C: Loop / Klaviyo / GA4 / Sentry opportunistic.
- D-D: Loop fallback until Shopify-native returns proven.
- D-E: weekly founder digest IN pilot via email through the relevance gate (DOC CONFLICT: canonical docs
  vs Horizon-2 — reconcile in the canonical pass).
- D-F: HARD 7-condition pre-pilot gate (incl. a deliberate fault-injection drill — the R9 session was
  an UNINTENTIONAL real-world instance of exactly that failure mode; gate's value proven. Phase D's
  fault-injection proof is a clean intentional instance of the same drill).
- D-G: hardening ranks ahead of Pass Two / C8 / taxonomy; Pass Two folded into hardening.

---

## ROUTING (future passes — recorded so they don't evaporate)
- Canonical-doc landings for D-A..D-F (incl. the D-E Horizon-2 conflict) + the 9 R9 corrected facts →
  the later canonical save-protocol pass. STILL OPEN (RULE 3 + tech-arch §3.3/§7/§10 + CLAUDE.md already
  landed early).
- O-26 full design-consistency / doc-vs-DB audit → scheduled, separate cadence. STILL OPEN. (CLAUDE.md's
  "public schema" list names 6 tables; live DB has 15 — a doc-drift item for this audit.)
- validate_seed heavy-aggregation timeout over this network → PARTIALLY MITIGATED by Phase D D9
  (statement_timeout + per-check SAVEPOINT + retry-once means a blip no longer false-rolls-back a good
  seed). Root cause (slow link / heavy join+aggregate checks #3/#7) NOT fixed — query tuning / faster
  connection STILL OPEN.
- client_id value split (client_config.client_id = `client_azure_co` vs seed app-table rows written
  with client_id = `azure_co`) → verify intentional/safe (O-26 / canonical pass); see the Live-DB
  block. Nothing broken today; a cross-table join on client_id would mismatch. STILL OPEN.
- Toggle-form divergence (var-form vs client_config-form) → reconciliation phase.
- klaviyo raw shape-split → Klaviyo connector boundary (with Loop boundary).
- Pre-existing hygiene (seed_shopify.py mojibake; #8 alert_log client_id filter) → hygiene cleanup.
- Pass Two (SKU-contract assertion) → folded into hardening per D-G; Pass-One contract intact.
- C8 HERO return-driver alert + taxonomy versioning → Horizon items, not this stream.

---

## HORIZON / FLAGS (do not chase next session)
- Unpushed local stack (HEAD 2863e5c; ~10 commits, reconcile vs CC's "11") — one coherent push later.
  Bulk transfer over this machine's link is unreliable (poolers drop large COPYs); small-commit push is
  fine; bulk dump/restore needs a stable network / cloud shell near AWS us-east-1.
- OneDrive corruption risk on the repo path — ongoing; stop-don't-force on lock errors.
- Project-mount staleness: tech-arch + CLAUDE.md were stale in the mount this session; founder uploaded
  the live copies into chat. RE-UPLOAD CLAUDE.md + technical_architecture.md to the Project so future
  sessions inherit them.
- The systemic story: the platform had the RIGHT controls designed (R10 sync guard, R11 dbt tests,
  RULE 3 boundary) but historically NONE in the enforcement path. Phase C moved RULE 3 in; Phase D moved
  R11 in (dbt tests + seed gate). Phase F (R10) still owed.
- Backup `ps_full.dump` exists on disk (D:\ps_backups\, golden) — valid R9 restore point.

---

## FILES TO SAVE / UPLOAD THIS SESSION
- state_2026-06-24_phase-d.md (this file) — ADDED (new dated name).
- chat_context_2026-06-24_phase-d.md (paired narrative) — ADDED.
- No canonical spec edited during the session-close save (CLAUDE.md / tech-arch already committed in 2863e5c).
Save → (founder approves text) → Claude Code VERIFIES (does not author) → commit the two continuity files
only (message: "Session 2026-06-24: Phase D — state + context") → re-upload the pair to the Project
(one-way sync). ALSO re-upload CLAUDE.md + technical_architecture.md (changed in 2863e5c). NO push.

## SANITY HANDLES (real post-edit counts — Check 9)
- state_2026-06-24_phase-d.md: 276 lines
- chat_context_2026-06-24_phase-d.md: 85 lines
(As-authored counts. Claude Code: re-run `wc -l` on both committed files and confirm they equal
276 / 85 — if a mounted/committed copy differs, the wrong copy landed → STOP.)
