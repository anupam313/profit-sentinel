# Chat Context — DB Verification, Register Update & the Reproducibility Discovery
**Date:** 2026-07-27 · **Companion:** `state_2026-07-27_dbverify-reproducibility.md`
**Started at HEAD `0a4031c`, ended at `f191fa7`.** Four commits, all pushed.
Third session pair of 2026-07-27, following `_outreach` and `_pilot_readiness`.

---

## 1. WHAT THIS SESSION DID

It began as India outreach strategy and a register update, and turned into something else halfway
through. The register update went ahead — twelve new items, verified against the live database before
being written. But verifying them surfaced that **the repo could not rebuild the database**, which
made HK-2's premise ("the repo is the source of truth") false. Most of the second half was closing that.

Nothing this session moved the binding constraint. Design partners are still the gate. This was
insurance against a failure mode found by accident.

## 2. THE WORKING METHOD (proven again — keep using it)

- **Verify before writing.** Eight database-state claims were checked against the live DB before entering
  the register. Three closed outright, one was dropped, three stood. Roughly a third of what would have
  been written was wrong or unnecessary.
- **Scripts validated before running.** Both verification SQL scripts were run against a real PostgreSQL
  16.14 with a mock schema mirroring the expected findings, exercising every branch — including the
  missing-table and missing-column paths — before they ever touched Supabase.
- **The save protocol earned its place.** Check 6 (anchors present exactly once) caught two bad anchor
  DECLARATIONS. In both cases the file was correct and the declaration was wrong. That is the check
  doing precisely what it exists for.
- **Claude Code stopped rather than guessed, repeatedly.** It flagged a self-contradictory instruction
  (the final line was supposed to be "intact" while an edit deliberately changed it), a conflicting pair
  of instructions on the Co-Authored-By trailer, and a case-sensitivity mismatch on an anchor. All three
  were errors in the prompt, not in the work.

## 3. THE FOUR COMMITS

- **`70fd48f`** — register: 116 → 151 lines, +35 declared and reconciled exactly. Twelve edits across
  eight regions, all sixteen anchors unique, scoped diff clean, hash-verified before commit.
- **`1c1130f`** — four previously-untracked connector scripts. `seed_b4_patch.py` was the ONLY copy of
  the B-4 alias map in existence; the other three are historical one-offs, each given a warning header.
- **`894f9e1`** — `sql/schema.sql` (catalog-generated DDL, 45 tables, 159-column `client_config`),
  the calibration script, and the `sql/` entry added to CLAUDE.md's previously-EMPTY FILE LOCATIONS section.
- **`f191fa7`** — the Supabase keep-alive workflow.

## 4. THE REPRODUCIBILITY DISCOVERY — THE REAL FINDING

Asked plainly: *if Supabase were deleted tomorrow, what could not be rebuilt from the repo?* Answer at
the time: the core-table DDL, the RLS story, the calibrated config values, the entire B-4 attribution
layer, and several one-off DB mutations. `CLAUDE.md`'s run path covers seeds and dbt — everything
downstream of a schema and config the repo did not hold.

The sharpest single fact: **`seed_b4_patch.py` was untracked, and it was the only file anywhere
containing the HERO_DRESS alias map and the Gorgias → Shopify → Loop chain that C8 demonstrates on.**
The wedge alert's demonstrable data layer existed in one OneDrive-synced folder.

Four of the five gaps are now closed. The RLS one was never a gap — live state is RLS on with zero
policies, which is exactly what the tracked `_harden_public_schema.py` applies. Two smaller ones opened:
the two `client_config` triggers, and the fact that nothing creates the `client_config` row.

## 5. CORRECTIONS I MADE THIS SESSION — AND THE PATTERN

Seven, and they share one shape. Recording them because the pattern is the useful part.

1. Flagged the G1 size-level question as unresolved — it was decided 2026-05-23, in full.
2. Said `top_sku_inventory_pct` was empty; then "corrected" myself on the strength of
   `tech_arch:1160`; the database says 0 of 730. **The original claim was right.**
3. Said the missed-revenue dependency was untracked — it is tracked twice, in the checklist at D-6 and
   in `technical_architecture.md` as a decided permanent limitation.
4. Said the SKU-format mismatch was unresolved — B-4 resolved it on 2026-05-22.
5. Said "every RLS policy lives only in Supabase" — overstated; the deny-all posture is reproducible.
6. Said a path "must come from CLAUDE.md's FILE LOCATIONS section" three times. **That section was empty.**
7. Pushed to upgrade Supabase immediately while simultaneously recommending the work that removed the
   justification for upgrading. The founder caught this one.

**The pattern:** every error came from trusting a document or a session file instead of checking the
thing itself. **Rule for next time: for database state, query the database. For file state, open the file.
A spec describes intent; only the artifact carries fact.**

## 6. DECISIONS MADE (founder rulings)

- **India as PIPELINE TEST BED, not design partners.** Connectors, data-quality checks, seasonality and
  category grouping can be rehearsed on an Indian brand's data. Thresholds and the parser cannot.
  Indian brands do NOT count toward the 4–5 design-partner gate; their feature requests go in a separate
  file and enter the product plan only with US corroboration. Reasoning: catalogue-ads and returns
  mechanics differ (RTO vs post-delivery returns), and roadmap drift is the real risk, not bad data.
- **G1 splits into G1a/G1b** rather than scoping catalogue ads out. Meta's own documentation states only
  one variant per item displays in ads and that it substitutes an available variant — so catalogue ads
  suppress the sold-out ITEM but keep advertising the PRODUCT.
- **Slack paused**, revisited after real design partners. Only G1 (a pilot alert) renders to email now.
- **G3 parked** — not a pilot alert under either definition; low stakes.
- **HELD-3 reverts** to its original trigger: upgrade before first connect, for backups.
- **Ten checklist items keep their ORIGINAL codes** when promoted, preserving the searchable thread back.
- **Original codes over renumbering; verification over assumption**, throughout.

## 7. THE INFLUENCER FINDING (register OQ-16, DH-2)

The Blueprint claims return-adjusted influencer ROI by creator is built by nobody. **Too strong.**
Triple Whale's Affluencer Hub ships creator-level revenue, creator-level cost including gifting, and
per-creator ROAS. GRIN, Aspire, Upfluence and CreatorIQ all carry per-creator sales attribution.

What is NOT built anywhere found: **netting returns at creator level from the brand's own refund data** —
and Triple Whale documents that it does not read third-party returns apps at all. So the gap is real but
NARROWER, and it is specifically the returns leg. **Reclassify from moat to wedge:** the incumbent already
holds the creator infrastructure, so adding "minus refunds" is a small step for them.

Corroboration worth keeping: CreatorIQ's own positioning admits it can report that a creator drove 847
clicks converting at 4.2% but cannot weight that against a retargeted paid ad seen three days later.
That is the double-count problem, unsolved, in a market leader's own words.

## 8. THE INDIA DISCOVERY QUESTIONNAIRE

Built this session: `DTC_Prism_Founder_Discovery_Call_India.docx`, 5 pages, ~30 minutes. Screening
questions first (own-site share, prepaid split, platform, ad channels), the scenario test scored A/B/C/D,
six signals scored see-it / effort / cannot-see, two India-specific questions (refused delivery vs real
return; where sizing complaints land), three creator questions, the one question, the data ask, and a
four-part close — other founders, Shopify agency people, investors with US exposure, direct US contacts.
**Log India interviews in a SEPARATE column.** The §11 pivot rule runs on US interviews only.

## 9. WHAT'S NEXT (as left at session end)

1. **Recruitment.** The gate. Untouched today.
2. **A24 / BT-16** — the G1a/G1b split. Buildable on synthetic data now; the join is proven at
   137,006 of 137,006. Do the A34 doc edits in the same session.
3. **A36 / BT-19** — the checklist sweep. Treat the register as probably-incomplete until it runs.
4. Founder-only actions: the `SUPABASE_DATABASE_URL` secret, one manual keep-alive run, and confirming
   GitHub emails on workflow failure.

## 10. FOR A FRESH SESSION — WHAT TO LOAD
`save_protocol.md` · `operating_charter.md` · `pilot_readiness_register.md` (151 lines) ·
`pilot_scope.md` · the state file above. The mount is stale; verify against HEAD or pasted live text.
The spreadsheet `pilot_readiness_27072026.xlsx` is the working view and regenerates from the register.
