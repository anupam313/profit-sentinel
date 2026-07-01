# Chat Context — 2026-06-27 — J-2 (HERO native-ready reason + J-3 leak fix) shipped & doc-synced

> Narrative companion. AUTHORITATIVE state + SESSION OPEN + owed set: state_2026-06-27_j2-close.md
> (87 lines). Load that first; this file is the story,
> not the source of truth.

## What this session was
Owed-J from the FIRED-alert plug-and-play sweep: HERO's return-reason source. The read-only discovery
found HERO was 100% Loop-based (mart_return_rate_by_sku read loop_return_line_items.return_reason_primary
directly) — the REVERSE of pilot_scope §6's locked "Shopify-native Returns API is primary, Loop
opportunistic." So owed-J was not a small parser tweak; it was a realignment. It got reframed from
"rewire the parser to the returnReasonDefinition.handle field" to "BUILD HERO's native reason path,"
because the native handle existed nowhere — not in seed, staging, mart, or the Airbyte sync. The
founder chose a small, guarded J-2 now: make HERO native-READY (the plumbing) WITHOUT seeding a guessed
handle, and fix the J-3 RULE-3 leak while already inside the mart. Then Track A: doc-sync it.

## How it went (the surprises the discovery caught)
- CARRIER REVERSAL (b): the native carrier is NOT a new return-line-items table — Airbyte syncs no such
  table here. It is the existing shopify_order_refunds.return jsonb, live-confirmed PRESENT but 100%
  NULL. Minting a new table would have rebuilt the C1 invented-field trap one layer up (a synthetic-only
  object Airbyte would never fill in production).
- ::bigint → REGEX (b): the discovery's proposed order_id::bigint provenance cast would CRASH the entire
  staging model on a real Shopify GID (e.g. 'gid://shopify/Order/…') at first connect. Switched to a
  text-safe regex band — genuinely fail-closed (a real id tests FALSE, never throws) and RULE-4-clean
  (no raw cast). The project's own precedent (inventory_item_id regex, not a cast) argued for this.
- ORPHAN PATH (added, not in the discovery): transitive provenance via the parent header meant an orphan
  line item (return_id with no header) got NULL provenance and would DROP under the RULE-3 filter when
  the toggle is off — a silent real-data loss. Fixed fail-closed (COALESCE(...,false) => treat orphan as
  real) with a not_null test on return_id as the loud tripwire.
- TWO COMMIT GATES: GATE 1 proved sku_cost_master has 0 real rows, so the costs var-form→per-client swap
  is output-identical — closing the ONE column (estimated_return_cost) the 5-column equality proof left
  open. GATE 2 secret-scanned the diff (public repo). Commit bd46884, behavior-identical on synthetic
  (125 rows, sha256 0316b4f7…).
- TRACK A doc-sync: 3 surgical canonical edits + this pair. The PREMISE pass KILLED one planned edit —
  "reconcile the Loop-reason contamination note" — because that note describes AGENT B's
  Gorgias-over-Loop weighting, which J-2 did not touch; editing it would have introduced an error into a
  true statement about a different component. The tech-arch edit is an ADDITION (no existing "mart reads
  Loop/raw" sentence to strike) plus retiring the stale "(to be created)" mart stub.

## Position changes named
- (b) carrier: new return-line-items table → existing shopify_order_refunds.return jsonb.
- (b) provenance: order_id::bigint cast → text-safe regex band.
- (b) "the 8-column re-hash is cheap" → a targeted GATE-1 query (the re-hash was NOT cheap — the BEFORE
  snapshot was gone once dbt rebuilt the mart; a query settled the one open column directly).
- (b) "tech-arch is the only canonical doc" → pilot_scope §4 (Check-8 mirror) and checklist D-GAP6-11
  are also owed.
- (b) "reconcile the contamination note" → LEAVE it untouched (separate component; editing it would be
  wrong).

## What's next
The FIRED-alert sweep continues — C6, G1, C2 — same treatment, with the J-3-style raw-read / var-form
audit folded into each (the var-form leak is a documented PATTERN, not a HERO one-off). Recruitment
remains the true launch gate.

## Method notes carried
- Mount untrusted; reason from HEAD / pasted live text. save_protocol live (149).
- I author edits + continuity in chat; Claude Code VERIFIES on disk (handles + scoped diffs), never
  authors continuity and never "updates project memory." Every canonical edit is surgical, authored
  against live text, explicit-path staged, paste-before-commit, no push from Claude Code.
- The deeper owed-chain (back to 2026-06-25) is still UN-reconciled — carried, not closed.
