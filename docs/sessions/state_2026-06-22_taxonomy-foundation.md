# STATE — 2026-06-22 — Taxonomy-Versioning Foundation (committed)

## NEXT CHAT STARTS HERE
**Topic: SKU-namespace realignment — establish the authoritative SKU contract across the synthetic seeds.**
Scope it as a *contract* decision, NOT a prefix-patch:
- Decide which namespace is authoritative (`AZ-…`/`AD-…` catalog vs `AZR-…`/`PKG-…` cost seed) and conform the other to it. Do NOT invent a third.
- Root cause is independent seed authoring with no shared SKU contract — fix the contract so future seeds can't drift, not just the strings.
- This is the binding constraint: it blocks the marts/D1 rebind, which blocks every category-grouped alert (returns-by-category, CM/D3). One item at a time.
- The broader "do other OP-1 'done' doc claims match live DB?" reconciliation stays a HORIZON item (logged below) — do NOT fold it into the SKU session.

## SESSION-START GATE (run before any design work)
- Load `save_protocol.md` (authoritative over any summary) and this state file + its paired `chat_context_2026-06-22_taxonomy-foundation.md`.
- Re-verify canonical line-count handles **against repo HEAD** (mount/uploads proven stale this session — do not trust them). Expected post-`b8fec19`:
  - product_strategy.md = **1424**
  - technical_architecture.md = **3929**  *(was 3827 pre-edit; +102 in b8fec19; mount still shows 3827/stale)*
  - agent_d_build_spec.md = **2722**
  - cross_alert_orchestration.md = **847**
  - d1_validation_gates.md = **399**
  - pre_agent_build_checklist.md = **389**
  - save_protocol.md = **149**  *(build report once showed 149/150 — confirm exact at HEAD)*
  - pilot_scope.md = **122**
- Deliberation mode: tag load-bearing claims [verified—file:line] / [inference] / [guess]; verify this turn (not from memory); give the self-counter; end with what-I-checked + most-likely-wrong + completeness confidence. One item at a time with sign-off. Design in chat; build in Claude Code (read-only mount; no repo/DB/git from chat).

## REPO / PROCESS STATE
- **Commit `b8fec19`** — "Taxonomy versioning foundation: pin 2026-05 + resolve/stamp + H21 drift". **LOCAL ONLY** — `master...origin/master [ahead 1]`, NOT pushed.
- HEAD = `b8fec19`. Prior: `7d5c2e7` (OP-1 close), `ef1f1c8` (seed/probe).
- Pre-existing WIP restored from stash (clean `git stash pop`, no conflicts, stash auto-dropped): 7 modified tracked + 16 untracked (incl. `seed_sku_cost_master.py` 376 lines, `slack_bot/`). Working tree is intentionally dirty with this WIP on top of `b8fec19`.
- OneDrive-synced path — known corruption risk; bit us this session (half-failed `stash push`, reconciled). Treat git operations cautiously; stop-don't-force on lock errors.
- **TODO (you, outside Claude Code):** re-upload the 3929-line `technical_architecture.md` (the live repo file, not a backup copy) to the Claude Project so next session's mount matches git.

## WHAT LANDED TODAY (in b8fec19)
- `connectors/taxonomy_config.py` — NEW. `PINNED_TAXONOMY_VERSION = "2026-05"` (single authoritative home) + pinned-list loader + `resolves()`.
- `connectors/category_inference.py` — NEW. 4-step resolution + provenance stamp + `ensure_schema()` (additive ALTER) + H21 drift emit.
- `connectors/data/taxonomy/2026-05/categories.json` — NEW. Slim all-vertical pinned list: 14,606 nodes, ~3.4 MB (id/full_name/parent_id/level only). 80 MB raw stays gitignored. Reproducible via generator. NOT the deferred apparel projection (all verticals, fewer fields/node).
- `connectors/seed_shopify.py` — M. Reads the version constant (no duplicated literal); records it in MANIFEST.
- `docs/technical_architecture.md` — M. 3827→3929. OP-1 ALTER corrected (`public.`→`client_azure_co.`; "done"→never-applied); 6 columns documented; taxonomy-versioning subsection; H21 row.

### Live (synthetic) DB changes — part of build, not git
- Additive ALTER applied to `client_azure_co.sku_cost_master`: 6 columns added — `category_id`, `category_full_name`, `category_inference_confidence`, `category_source` (the OP-1 set, **never previously applied**) + `taxonomy_version`, `category_grouping_key` (net-new).
- All 428 rows stamped: `taxonomy_version='2026-05'`, `category_grouping_key` set. All currently `brand_level_floor` (see SKU-mismatch finding). No H21 fired. Invariant `category_grouping_key == category_id` proven on catalog products via real resolution code.

## LOCKED DECISIONS (do not reopen without new evidence)
- **(c) version stamp MANDATORY + (b) pinned-version migration model; (a) auto-pull REJECTED.** Pin = **2026-05**.
- **Keep uncategorizable SKUs at brand level WITH disclosure — NEVER silently drop.** Rationale: reconciliation with founder's own Shopify totals + unbiased baselines (NOT signal). Separate data-quality exclusion gate (also disclosed) for SKUs untrustworthy even at brand level.
- **Foundation = version stamp + grouping-key indirection** (aggregations bind to `category_grouping_key`, never raw `category_id`). Day-one grouping_key = resolved node at AL-19 firing depth = category_id.
- Slim all-vertical pinned artifact + committed generator (reproducible, hash-verifiable; not a hand copy).
- Drift = **H21 — Taxonomy Version Drift** (`data_integrity`). A stored/Shopify-assigned code not resolving in the pinned list raises H21 naming exact SKUs. A–H codes locked; next-available read from live roster (H20 = New SKU COGS Gap).

## VERIFIED FACTS (repo-checked this session — don't re-litigate)
- **Category ids are STABLE-ASSIGNED.** 465/465 apparel (`aa`) nodes kept byte-identical ids 2026-02→2026-05 despite +198 new apparel sub-nodes. New children take next-available numbers; existing nodes never renumbered. Drift only on deliberate re-parent/merge/split.
- **Deliberate apparel structural change ≈ 0 per release.** Across 2025-09→12, 2025-12→2026-02, 2026-02→2026-05: two pairs had ZERO; one had a single bounded "Baby & Toddler → Baby & Children's" rename/reparent (101 ids, one initiative, fully crosswalked). **Zero merge/split/retire in all three.**
- **Shopify ships version-to-version crosswalks** (`dist/en/integrations/shopify/<src>_to_<tgt>.json`), e.g. `shopify_2025-12_to_shopify_2026-02`. BUT no direct `2026-02→2026-05` map (nearest source 2025-12) — remap must handle the no-crosswalk case.
- No `archived` flag in dist files (retirement = code absent from new pinned list). 2026-05 is current published release (apparel-heavy; CHANGELOG.md lagged at 2026-02, Releases page is authoritative).

## DEFERRED (with reasons — written into technical_architecture.md)
- **Remap algorithm.** Justified by detect-and-bounded-cost (H21), NOT change frequency. On migration: re-resolve all SKUs (active + inactive) to grouping_key; most codes still resolve unchanged (stable ids), only the vanished residual needs the crosswalk. MUST check whether a shopify→shopify crosswalk shipped for the specific pin-jump; if none, fall back to id/breadcrumb diff of the two pinned categories.json. Non-destructive (never overwrite the as-assigned code + version).
- **PS-owned surrogate-key dimension table** (rides with remap; aggregations already bind to grouping_key so no query rewrite later).
- **Apparel projection** (derived from pinned full file, never hand-trimmed).

## NEXT ITEMS (ordered)
1. **SKU-namespace realignment** (see NEXT CHAT — the binding constraint).
2. **Marts/D1 rebind** `category_id` → `category_grouping_key`. GATED on #1 (can't verify grouping_key == real category until cost rows reach a category).
3. **C8 (HERO return-driver) edit** — separate save-protocol pass (causal_graph.py +C8; pilot_scope 58→59; product_strategy count reconciliation). Still pending.

## HORIZON / FLAGS (do not chase in the SKU session)
- **Doc-vs-DB drift reconciliation.** Three gaps surfaced today: OP-1 columns never applied to live DB; doc said `public.` (table is `client_azure_co`); doc claimed "done" for unbuilt work. OPEN QUESTION: do *other* OP-1 "done" claims match live state? Needs a deliberate doc-vs-live-schema sweep (relate to O-26 design-consistency audit). Separate cadence — log, don't fold in.
- OneDrive corruption risk on the repo path — ongoing.

## FILES TO SAVE THIS SESSION
- `state_2026-06-22_taxonomy-foundation.md` (this file)
- `chat_context_2026-06-22_taxonomy-foundation.md` (paired narrative)
Save → commit → re-upload both to the Project (one-way sync; mount treated as stale vs repo).
