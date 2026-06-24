# Profit Sentinel — State — 2026-06-24 — Phase C boundary
## Session: Phase C — is_synthetic real/synthetic boundary for the Shopify spine
## Status: Phase C COMPLETE + committed (fe8725b). Steady state live. No push (8-deep stack).

---

## NEXT SESSION — LOAD FIRST

**Load:** docs/save_protocol.md FIRST (authoritative; 149 lines), then CLAUDE.md,
docs/technical_architecture.md, docs/product_strategy.md, and this state file's companion
`chat_context_2026-06-24_phase-c-boundary.md`.

**Canonical line-count handles (verified this session — do NOT false-alarm on drift; mount
has been stale before, HEAD is source of truth):**
```
product_strategy            1424
technical_architecture      3947   <- changed this session (was 3929)
agent_d_build_spec          2722
cross_alert_orchestration    847
d1_validation_gates          399
pre_agent_build_checklist    389
save_protocol                149
pilot_scope                  122
CLAUDE.md                    214   <- changed this session (was 187)
```

**Repo state:** HEAD `fe8725b`, 8-deep unpushed stack (NOT pushed; push as ONE coherent set
later, after hardening lands — not piecemeal):
```
fe8725b  Phase C: is_synthetic real/synthetic boundary for the Shopify spine
8292b02  WIP checkpoint: Session-3/B-9/B-4 mart columns + customer-segments mart (pre-Phase-C)
2c04e76  Session 2026-06-24: R9 double-seed healed + committed
eb21af2  R9: make seed_shopify idempotent; heal double-seed
a307b81  Session 2026-06-22: SKU-namespace contract Pass One state + context
8a707a1  SKU-namespace contract conform: cost seed reads catalog as cost universe
ae8a2d5  Session 2026-06-22: taxonomy-versioning foundation state + context
b8fec19  Taxonomy versioning foundation: pin 2026-05 + resolve/stamp + H21 drift
```
**Working tree is NOT clean** (factual note — out of Phase C scope per the 0b WIP ruling,
which committed Group A only): undisposed Group B remains — `connectors/seed_meta.py` (M),
`onboarding_flow.py` (M), and untracked `connectors/_*.py` probes,
`connectors/historical_pattern_scan.py`, `connectors/seed_b4_patch.py`,
`connectors/seed_google_ads.py`, `slack_bot/`, and the six pre-existing `docs/sessions/*`
files. Disposition not yet ruled.

**Live DB steady state:** `public.client_config.use_synthetic_data = TRUE` for
`client_azure_co`. All staging views + mart tables rebuilt at TRUE.
`mart_causal_chain_daily` = 730 rows / sum(order_count) = 84230. No mart reads raw
`shopify_*`.

**Deliberation mode:** tag load-bearing claims [verified—file:line] / [inference] / [guess];
verify THIS turn in Claude Code, never from memory or the mount; one item at a time with
sign-off; design in chat, build in Claude Code (read-only mount; no repo/DB/git from chat);
continuity files are authored in chat, then Claude Code VERIFIES (does not author) them.

**NEXT ACTION:** pre-pilot hardening **Phase D** — constraints + dbt tests in the run path
(see HARDENING PHASES). Do NOT start until directed.

---

## WHAT THIS SESSION ACTUALLY DID (in one breath)
Ran C-0 discovery (read-only ground truth), then built Phase C: derived `is_synthetic` in the
5 raw-reading Shopify staging models from the seed isolation predicates, filtered at the
staging boundary with the per-client RULE 3 form, and re-routed `mart_causal_chain_daily`'s
raw Shopify reads through filtered staging so no mart exposes synthetic rows to a client.
Committed Group A WIP separately first (`8292b02`) to keep the Phase C diff isolated; set
`client_config.use_synthetic_data = TRUE` as steady state (founder-ruled); proved the boundary
with the Egnition island as a fail-closed gate. Phase C committed at `fe8725b` (9 files).
CLAUDE.md RULE 3 + tech-arch §3.3/§7 were corrected in the same commit (RULE 9 doc-sync).

---

## PHASE 0 — DECISION LEDGER (read from this session)

| # | Decision (plain) | Target | Landed |
|---|---|---|---|
| L1 | WIP Group A (Session-3/B-9/B-4 mart columns + customer-segments mart) committed separately FIRST, so the Phase C diff stays isolated and reviewable | git checkpoint | ✅ `8292b02` |
| L2 | `use_synthetic_data` steady-state = **TRUE** for client_azure_co (founder-ruled); authorized to set the flag (was FALSE — stale; seed never set it) | `public.client_config` (live data) | ✅ set TRUE (gate toggled false→true, landed TRUE) |
| L3 | Derive `is_synthetic` from the seed isolation predicates in the 5 raw-reading Shopify stg models, then RULE-3 filter at the staging boundary | stg_shopify_orders, _order_line_items, _refunds, _order_source_attribution, _inventory_levels | ✅ `fe8725b` |
| L4 | `stg_shopify_net_sales_validation` passes `is_synthetic` THROUGH from upstream (`bool_and`, date-grain aggregate) — no re-derive, no re-filter | stg_shopify_net_sales_validation | ✅ `fe8725b` |
| L5 | Re-route `mart_causal_chain_daily` off raw shopify (discount_daily, inventory_snapshot_base, units_sold_daily → stg refs) + `discount_codes` pass-through on stg_shopify_orders + join recast `o.order_id::text = li.order_id` | mart_causal_chain_daily + stg_shopify_orders | ✅ `fe8725b` |
| L6 | RULE 3 amended: false universal claim ("every source table has is_synthetic") → two-source provenance (derive-in-staging for shopify; stored for some) + per-client filter form; never the connector-staging var-form | CLAUDE.md | ✅ `fe8725b` |
| L7 | tech-arch §3.3 + §7 updated for DEBT-006 + derive-in-staging + per-client toggle | technical_architecture.md | ✅ `fe8725b` |
| L8 | **Phase B Egnition island = KEEP through Phase C** (closes the prior file's "purge vs keep — pending"); re-designated as the boundary's real-row test fixture; purge NOT executed. Re-open purge only after the boundary is proven (now proven by the gate). | this state file (resolves prior Phase B) | ✅ kept; gate proves it |

### ROUTED / OWED items (recorded here so they do not evaporate)

1. **Cancelled/voided narrowing (OWED — pre-pilot).** Routing `mart_causal_chain_daily`
   through `stg_shopify_orders` now EXCLUDES cancelled/voided orders
   (`cancelled_at is null and financial_status != 'voided'`) from `discount_order_rate_90d`
   and `units_sold`; the prior raw reads included them. Deliberate metric-definition
   narrowing. **OWED: alert-threshold calibration check — confirm whether any alert keys off
   these two columns before pilot.**
2. **Toggle-form divergence (pending reconciliation phase).** New Shopify staging uses the
   per-client `client_config` table form; connector staging (meta/ga4/sentry) still uses the
   dbt-var form `is_synthetic = {{ var('use_synthetic_data', true) }}`. At toggle-OFF the
   var-form sources still emit synthetic rows (why `mart_causal` keeps 706 ga4-driven date
   rows at OFF while Shopify contribution = island only). Reconcile in a later phase. Noted in
   CLAUDE.md RULE 3 and tech-arch §3.3/§7.
3. **loop_return_line_items (later Loop-connector boundary phase).** No `is_synthetic` column;
   `mart_return_rate_by_sku` reads it raw via `source(...)`. Non-Shopify → out of Phase C
   scope; address at the Loop connector boundary.
4. **stg_shopify_inventory_items (no action; reported).** Island-only (1 real, non-AZ row),
   `seed_shopify.py` does not write it, no mart consumes its stg. NOT edited; no predicate
   guessed.
5. **Airbyte sync-mode (founder UI action).** Not verifiable from this environment (no
   `AIRBYTE_*` creds). Founder to confirm per-Shopify-connection sync mode in Airbyte Cloud
   UI. Boundary is predicate-based → sync-mode-agnostic, BUT real-data correctness assumes
   real ids stay ≥ 1e12 and real SKUs stay non-`AZ-`. If real Shopify ids/SKUs ever fall in
   synthetic ranges, the predicates mislabel — revisit before real cutover.
6. **Group B working-tree disposition** — not yet ruled (see repo-state note above).

---

## WHAT WAS BUILT (Phase C, commit fe8725b — 9 files; code +152/−36, docs +81/−18)

**Derivation predicates (predicate match = synthetic; identical to seed_shopify.py):**
- orders / refunds / order_source_attribution: `id < 1000000000000`
- order_line_items: `order_id < 1000000000000`
- inventory_levels: `not (inventory_item_id::text ~ '^[0-9]{13,}$')`

**Filter (per-client RULE 3 form), applied at the staging boundary:**
```sql
where (
  is_synthetic = false
  or (select use_synthetic_data from public.client_config
      where client_id = '{{ var("client_id") }}') = true
)
```
`client_id` dbt var = `'client_azure_co'` (NOT `'azure_co'`) — matches the single
`client_config` PK row, so the scalar subquery is single-row-safe.

**mart_causal_chain_daily:** `discount_daily`, `inventory_snapshot_base`, `units_sold_daily`
now read `{{ ref('stg_shopify_*') }}`. `discount_codes` exposed as a pass-through on
`stg_shopify_orders`. Only remaining raw `{{ var('client_schema') }}.` reads are
google_ads / meta / tiktok (out of Phase C scope). Verified in compiled SQL.

**Note on the diffstat:** "9 files" = the Phase C commit set; the code/doc split above is from
the save package and was reported inconsistently in-session — confirm with
`git show --stat fe8725b` next session if an exact number is needed (low priority).

---

## ISLAND ACCEPTANCE GATE — PASS (fail-closed)

Island = order `6438993559648`, customer `8824697159776`, 43 real products, 1 real variant,
1 real discount, 1 real inventory row → all resolve `is_synthetic = FALSE`.

| Toggle | Staging synthetic survivors | Island | mart Shopify contribution |
|---|---|---|---|
| OFF (false) | **0** across all 5 stg views | intact (orders=1, inv=1, attr=1) | mart_net_revenue 1 row/order_count **1** ($40); mart_causal order_count **1** |
| ON (true) | 84,229 + island | intact | order_count **84,230** |

dbt build green at steady-state TRUE (PASS across affected staging + marts + tests; only
failures were transient Supabase pooler timeouts, all cleared on retry). At toggle-OFF
`mart_causal` still shows 706 rows — that is the ga4-driven date spine (ga4 still synthetic
via the var-form divergence, item 2), NOT a Shopify leak: Shopify contribution = island only.

---

## RECON FACTS THAT REMAIN VALID (design inputs for Phases D–F; verified read-only)
- **G1 seed-isolating predicates** (implemented in committed seed): products `product_type ∈
  {top,dress,short,knit,outerwear,denim,formal,mens}`; variants `sku ~ '^AZ-[A-Z]+-[0-9]+'`;
  customers/orders/refunds/fulfillments `id < 1e12`; line_items `order_id < 1e12`;
  inventory_levels `NOT (inventory_item_id::text ~ '^[0-9]{13,}$')`; touchpoint non-13-digit
  order_id; pii_lookup `synthetic_customer_id < 1e12` (text-safe); discount `code ∈
  12-seed-list`; discount id deterministic `920_000_000 + seq`.
- **G4 constraint-key validity** (Phase D): `order_line_items.id` is NOT unique even
  single-copy (colliding seed id space; natkey has legit collisions) → needs a surrogate/fix
  before a unique constraint; `klaviyo_email_events` must key on `message_id` (natkey has 374
  legit collisions); all others id==natkey OK.
- **R11 untested staging** (Phase D): 5 untested stg models (stg_klaviyo_flows,
  stg_klaviyo_profiles, stg_shopify_inventory_items, stg_shopify_inventory_levels,
  stg_synthetic_touchpoint_journey); add schema.yml test entries + wire `dbt test` into the run path.

---

## HARDENING PHASES (forward plan — separate gated commits)
- **Phase A — R9 idempotency + heal — DONE, committed eb21af2.**
- **Phase B — Egnition island purge vs keep — DONE: KEPT** (founder-ruled keep-through-Phase-C;
  re-designated as the boundary test fixture; no purge). Reference-safe either way (G2).
- **Phase C — is_synthetic boundary (R6 / RULE 3) — DONE, committed fe8725b.** Derived in the
  shopify staging spine + per-client RULE-3 filter + re-routed the bypassing mart
  (mart_causal_chain_daily) through filtered staging. Island gate PASS.
- **Phase D — make controls real (R11) — NEXT.** Add unique constraints on G4-validated keys
  (fix order_line_items key; klaviyo message_id); add schema.yml test entries for the 5
  untested stg models; wire `dbt test` into the run path. **CRITICAL: relocate the durable
  presence/uniqueness validation into `validate_seed`** — the temporary heal gate that provided
  this was removed for the permanent commit, so the production seed's bare `conn.commit()`
  currently has NO such guard. This is where that protection permanently lives.
- **Phase E — R13 suppression_log canonicalization.** Pick the richer (client) schema as
  canonical; migrate the public connector rows; repoint all writers; one home.
- **Phase F — R10 build validate_sync.py** (the absent post-sync variance guard).
- **THEN — canonical state-file corrections pass** (the 9 corrected facts from the R9 session +
  D-A..D-F landings), written once under the save protocol (Checks 4/7/8/10/11). NOTE: the 9
  corrected facts live in `state_2026-06-24_r9-heal-committed.md` (CORRECTED FACTS section) —
  that file is the source for this pass; this Phase C did NOT re-list them.

---

## LOCKED DECISIONS (carry forward; do NOT reopen) — from 06-23
- D-A: two-bar connector model.
- D-B: Bar-2 fired sources = Shopify / Gorgias / Meta / Google Ads / TikTok; cost is plumbing.
- D-C: Loop / Klaviyo / GA4 / Sentry opportunistic.
- D-D: Loop fallback until Shopify-native returns proven.
- D-E: weekly founder digest IN pilot via email through the relevance gate (DOC CONFLICT:
  canonical docs vs Horizon-2 — reconcile in the canonical pass).
- D-F: HARD 7-condition pre-pilot gate (incl. a deliberate fault-injection drill — the R9
  session was an UNINTENTIONAL real-world instance of exactly that failure mode; gate's value proven).
- D-G: hardening ranks ahead of Pass Two / C8 / taxonomy; Pass Two folded into hardening.

---

## ROUTING (future passes — recorded so they don't evaporate)
- Canonical-doc landings for D-A..D-F (incl. the D-E Horizon-2 conflict) → the later canonical
  save-protocol pass (the scheduled pilot_scope reconciliation). STILL OPEN. ALSO carries the 9
  corrected facts from the R9 session. NOTE: Phase C already landed the RULE 3 + tech-arch
  §3.3/§7 corrections early (RULE 9 doc-sync), so those two are DONE ahead of this pass.
- O-26 full design-consistency / doc-vs-DB audit → scheduled, separate cadence (unchanged). STILL OPEN.
- validate_seed heavy-aggregation timeout over this network → query tuning / faster connection. OPEN.
- Pass Two (SKU-contract assertion) → folded into hardening per D-G; the Pass-One set-membership
  contract remains intact.
- C8 HERO return-driver alert + taxonomy versioning → unchanged Horizon items, not this stream.
- Toggle-form divergence (var-form vs client_config-form) → new this session; reconciliation
  phase (see ROUTED/OWED item 2).

---

## HORIZON / FLAGS (do not chase next session)
- Local-only commit stack (now 8-deep, fe8725b at top) not pushed — one coherent push later.
  **NOTE: bulk transfer over this machine's link is unreliable** (transaction + session poolers
  both drop large COPYs; local NAT/idle/TLS-inspection suspected). A push of small commits is
  fine; any future bulk dump/restore needs a stable network or a cloud shell near AWS us-east-1.
  (Also seen this session as transient pooler timeouts during dbt builds — retry, not a fault.)
- OneDrive corruption risk on the repo path — ongoing; stop-don't-force on lock errors.
- The whole platform has the RIGHT controls designed (R10 sync guard, R11 dbt tests, RULE 3
  is_synthetic boundary) but historically NONE were in the enforcement path — the systemic story.
  Phase C moved the is_synthetic boundary IN; Phases D/F move the rest in.
- Backup `ps_full.dump` exists on disk (D:\ps_backups\, verified golden content) — a valid
  restore point from the R9 session.

---

## FILES TO SAVE / UPLOAD THIS SESSION
- state_2026-06-24_phase-c-boundary.md (this file) — ADDED (new dated name).
- chat_context_2026-06-24_phase-c-boundary.md (paired narrative) — ADDED.
- No canonical spec edited during the session-close save (CLAUDE.md / tech-arch were already
  committed in fe8725b).
Save → (founder approves text) → Claude Code VERIFIES (does not author) → commit the two
continuity files only (message: "Session 2026-06-24: Phase C boundary — state + context") →
re-upload the pair to the Project (one-way sync). NO push.

## SANITY HANDLES (real post-edit counts — Check 9)
- state_2026-06-24_phase-c-boundary.md: 258 lines
- chat_context_2026-06-24_phase-c-boundary.md: 105 lines
(These are the as-authored counts. Claude Code: re-run `wc -l` on both committed files and
confirm they equal 258 / 105 — if they differ, the wrong copy is mounted → STOP. Claude Code's
own pre-merge drafts were 140 / 93; the merge re-added the dropped standing sections, hence longer.)
