# Profit Sentinel — Chat Context (Category-Consistency Fix Pass)
## Date: 2026-06-02
## Session type: Targeted documentation-consistency fix (NOT design)
## Pairs with: state_2026_06_02_d1_gap6_wip.md (design state — UNCHANGED by this session)
## Corrects: chat_context_2026_06_02_spec_update_pass.md (its "caught three contradictions"
##           claim was incomplete — two more copies survived; see below)

Purpose: record that the Gap-6 category-resolution decision had stale copies the earlier
spec-update pass missed, what was fixed, and the verified-clean end state — so the next chat
does not re-open the category question and resumes directly at return-rate Seam 2. No new
design was done; every change here is propagation of the already-closed Gap-6 category design
(source of truth: pre_agent_build_checklist.md D-28/D-29 + technical_architecture.md GAP 6).

---

## WHAT THIS SESSION FOUND AND FIXED

The 2026-06-02 spec-update pass claimed a full-file retired-phrase sweep and reported catching
three contradictions across three files. The opening verification gate this session caught a
**fourth** stale copy, and the fix work then surfaced a **fifth** residual:

1. **agent_d_build_spec.md, lines 1919–1962 (4th copy).** The entire pre-Gap-6 category design
   was live in the Gap-3 schema section: DDL comment "Mandatory founder rename before any alert
   uses this label"; category_inference.py logic with collection-FIRST / "Skip AI inference"
   when coverage ≥70%; mandatory founder rename step; "founder declines rename → category-level
   D1 output suppressed"; "<0.70 → fall back to product_type." This file calls itself the
   authoritative Agent D build spec, so a builder would have shipped the wrong logic. FIXED to
   match D-29 verbatim on load-bearing parts.

2. **technical_architecture.md, ai_inferred_category DDL comment (5th residual).** Line ~3371
   still read "used when Shopify collections < 70% populated" — coverage-gated framing that
   contradicted the same comment's own line ~3375 ("internal grouping uses this AI clustering
   directly") and D-29. The category_inference.py script body (step 2/3) ALSO still had
   "collection ≥70% → skip AI inference entirely." Both FIXED: AI clustering is the internal
   grouping basis for EVERY brand; collection coverage governs the DISPLAY-label choice ONLY,
   never whether AI clustering runs.

Root cause of the disagreement: the spec-update pass scoped the category/rename fix to
technical_architecture.md only and did not realize agent_d carried a parallel copy; and within
tech-arch it fixed the rename gate + skip→suppress + 0.70 redefinition but left the
collection-coverage-gates-AI control flow intact. The closed decision overrode collection-first
for a SEMANTIC reason (promotional collections — "Bestsellers", "Sale", "New Arrivals" — are
unsafe grouping keys regardless of coverage), so a coverage gate measures the wrong thing.

LESSON (carry forward): when a decision is written in more than one file, the retired-phrase
sweep must be run on EVERY file that could carry a copy — including build specs that duplicate
schema/DDL. Two files agreeing is not proof; here the two designated source-of-truth files
(D-29 and tech-arch) themselves disagreed until this pass.

---

## THE SIX LOAD-BEARING POINTS (now consistent across agent_d / technical_architecture / D-29)

1. AI clustering is the INTERNAL grouping basis for every brand, regardless of collection coverage.
2. Collection feeds the DISPLAY label only.
3. Founder rename is a non-blocking DISPLAY gate; it never blocks internal grouping or alerts.
4. Founder skips/declines rename → keep AI labels for display, category_source stays 'ai_inferred',
   category-level D1 PROCEEDS (the "skip → suppressed" behaviour is retired).
5. category_inference_confidence = a cross-signal AGREEMENT score (title/tags/product_type/
   vendor/collection concurring), NOT a model self-report; 0.70 provisional placeholder.
6. product_type is the least-trusted signal — used for INTERNAL grouping of a low-agreement SKU
   only, NEVER as a founder-facing display label.

Per-brand output granularity is set by the CLUSTERING-QUALITY GATE (go-live gate D1-G3):
category-granular D1, or brand-level-with-disclosure (explicit low-quality path, never a silent
coarse fallback).

---

## VERIFICATION RUN (final six-file gate — PASSED)

Swept all six canonical files for: rename / skip AI inference / collection coverage / ±1 SD /
≥12 months / spend optional / collection_launch_suppression_active. Every hit triaged as one of:
new correct category wording, an intentional "(Retires…)" note, a changelog header, the O-11
open-item description (which quotes "spend optional" as the contradiction it exists to fix), or
unrelated legitimate content (Airbyte _airbyte_emitted_at→_extracted_at rename; ad-account
campaign rename). "skip AI inference" = 0 live occurrences in either corrected file. Three-way
category consistency confirmed.

Diff scope confirmed: agent_d changed only within 1919–1962; tech-arch changed only at the
ai_inferred_category DDL comment and the category_inference.py step 2/3 block. Everything else
byte-identical (pre-conditions 6/7, GAP 6 dependency blocks, NINE GAPS table, clustering-quality
gate, Approach-B detector code).

---

## FILE LINE COUNTS (sanity handle for the next load)

Corrected agent_d_build_spec.md: 2359 raw newlines → 2360 in the UI (trailing newline).
Corrected technical_architecture.md: 3613 raw newlines → 3614 in the UI (trailing newline).
(Stale pre-fix versions were ~2328 / ~3605 in the UI — if the next load shows those, the wrong
copy is in the project.)

---

## RESUME POINT (unchanged from the WIP handoff, now genuinely unblocked)

Gap 6: two named dependencies CLOSED (mix-shift seasonal grading; organic-viral). Category
resolution CLOSED + now consistent across files. Return-rate component PARTIAL. Resume one-by-one:
1. Return-rate Seam 2 — S17/S18 (size-guide / photography) vs C3 cross-alert gap (O-14
   contradiction). Does a size-guide/photography return spike that suppresses for C3 but is
   unseen by D1's S44 return bucket create a real D1/C3 disagreement, or is it absorbed by the
   two-stage baseline (S15) / residual (S3,S16) model?
2. C3 consistency check — does C3 also apply S15 as its return baseline; if so the two-stage
   model must be consistent across D1 and C3.
3. Then COGS/S21 → discount-depth/S19 → operational-cost/S20, each its own seam check (do NOT
   assert clean).
4. Final cross-component residual-disclosure consistency pass — all five suppressed components
   feed total_measured_impact / the residual gate identically.

Do not revive the three retracted positions (virality-is-accretive; three-state seed lifecycle;
modeled viral echo-window). After Gap 6: 7 → 8 → 9 → D1 alert language → D2 → D3 → D5 → D6 → C
→ B → A → orchestration resolution pass → H → consolidated Claude Code prompt. No alert language
until all 9 D1 gaps resolved. Parked post-H: clustering-coherence validation needs factors beyond
return-rate (price-band, margin-rate, discount-behaviour, size/fit-complaint, AOV).
