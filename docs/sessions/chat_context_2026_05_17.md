# Profit Sentinel — Chat Context
## Date: 2026-05-17
## Purpose: Captures decisions, reasoning, and nuances from
## the May 17 2026 session. Read alongside state_2026_05_17.md.

---

## SESSION FOCUS

Execution of Step 5 — Shopify synthetic seed script.
This was an infrastructure-heavy session. Most decisions were
reactive fixes to schema mismatches between the seed script
(written against design decisions) and the actual database state.

---

## KEY DECISIONS AND REASONING

### Decision 1 — Separate prompts per source (not one monolithic prompt)

Rationale confirmed:
- Context window exhaustion risk with all 8 sources in one prompt
- Verification impossible at scale — each source must be checked
  before downstream sources reference its IDs
- Dependency order: Shopify → Meta/TikTok → Klaviyo →
  Loop Returns → Gorgias → GA4 → Sentry
- TikTok ban (Gap D) and suppression scenarios (Gap F) complex
  enough to fill a prompt alone

### Decision 2 — Default Sonnet 4.6 over Adaptive mode

Adaptive (extended thinking) not useful for seed execution prompts.
Decisions are already locked in reference files — no ambiguous
reasoning required. Adaptive consumes tokens faster with no benefit.
Reserve Adaptive for genuinely hard architectural tradeoffs.

### Decision 3 — Tables must be created by seed script

Azure & Co is a synthetic brand — no real Airbyte sync has run.
Airbyte-managed raw tables only exist post-sync. Seed scripts must
CREATE TABLE IF NOT EXISTS before inserting. This is permanent
for all remaining seed scripts (Meta through Sentry).

### Decision 4 — is_synthetic removed from raw inserts (Fix 1)

DEBT-006 was correctly resolved: is_synthetic lives in staging
tables only. Raw table inserts must not include this column.
Synthetic data identified via client_config.use_synthetic_data = true.
Do not reopen this decision.

### Decision 5 — Airbyte metadata columns are mandatory (Fix 2)

All Airbyte-managed raw tables have four NOT NULL metadata columns:
_airbyte_raw_id (uuid4), _airbyte_extracted_at (timestamptz),
_airbyte_meta (jsonb {}), _airbyte_generation_id (bigint 0).
Helper function airbyte_meta_cols() must be used in every
subsequent seed script for all Airbyte-managed table inserts.

### Decision 6 — Nearest PD projection over manual correlation fix (Fix 4)

Three options were presented when Cholesky failed:
1. Nearest PD projection (Higham's / eigenvalue clipping)
2. Manual correlation reduction
3. Replace with independent random walks

Fix 1 chosen. Reasoning: correlation values were analytically derived
not validated by real client data — minor adjustments acceptable.
Fix 3 rejected explicitly — losing correlated structure defeats the
purpose of the seed data. The cross-signal realism is the entire
point of System 2.

### Decision 7 — Bare ON CONFLICT DO NOTHING (Fix 3)

ON CONFLICT (_airbyte_raw_id) DO NOTHING requires a UNIQUE
constraint. Airbyte-managed tables have no UNIQUE constraint on
_airbyte_raw_id (varchar NOT NULL only).
Do not add UNIQUE constraints to Airbyte-managed tables —
Airbyte controls that schema and conflicts may arise in production.
Single transaction boundary makes deduplication unnecessary.

### Decision 8 — Fix 2 on GENERATED ALWAYS identity columns

public.alert_log.id is GENERATED ALWAYS AS IDENTITY.
Never insert explicit id values into such columns.
Drop id from cols list. Postgres auto-generates.
Check all subsequent seed scripts for tables with identity columns.

### Decision 9 — Validation threshold was wrong, not the data

84,229 orders across 104 weeks (802/week avg) is correct.
Original threshold 18K–28K was written for a single season.
Corrected to 75K–95K (802/week × 104 weeks ±15%).
Lesson: validation thresholds must be calculated against the
full seed period, not a partial window.

### Decision 10 — Schema is source of truth over seed script

When column name mismatch occurred (confidence vs confidence_score),
the table schema was not renamed to match the seed. The seed was
fixed to match the schema. Seed scripts are disposable; schema is not.

---

## FAILURE SEQUENCE — WHAT BROKE AND WHY

This is logged for pattern recognition in subsequent seed scripts.

| Failure | Root Cause | Fix Applied |
|---------|-----------|-------------|
| is_synthetic column missing | DEBT-006 removed it from raw tables | Strip from all raw inserts |
| _airbyte_raw_id NOT NULL | Seed only provided _airbyte_extracted_at | Add all 4 Airbyte metadata cols |
| Tables don't exist | No real Airbyte sync ever ran | CREATE TABLE IF NOT EXISTS in seed |
| Cholesky decomposition fails | CORR_MATRIX not positive definite | Nearest PD projection |
| 505,375 orders (6× expected) | No single transaction boundary — prior crashed runs partially committed | Wrap all 14 functions in one transaction |
| ON CONFLICT (_airbyte_raw_id) fails | No UNIQUE constraint on that column | Revert to bare ON CONFLICT DO NOTHING |
| confidence column missing | Seed used 'confidence', table has 'confidence_score' | Fix seed to match schema |
| id NOT NULL violation | id is GENERATED ALWAYS AS IDENTITY | Drop id from insert cols |
| Order count check fails | Threshold written for single season not 24 months | Update threshold to 75K–95K |

---

## PATTERN FOR SUBSEQUENT SEED SCRIPTS

Every seed script from seed_meta.py onward must:

1. Read seed_manifest_shopify.json first for cross-source alignment
2. Call airbyte_meta_cols() for all Airbyte-managed table inserts
3. CREATE TABLE IF NOT EXISTS before any insert
4. Apply nearest PD projection to any correlation matrix
5. Wrap all functions in single transaction boundary
6. Use bare ON CONFLICT DO NOTHING (not column-specific)
7. Never insert explicit values into GENERATED ALWAYS identity cols
8. Calculate validation thresholds against full seed period
9. Fix seed to match schema — never rename schema to match seed

---

## TOOLING DECISIONS

### --dangerously-skip-permissions flag
Use at Claude Code session start for local dev environment.
Eliminates repeated "allow once / allow always / don't allow"
permission prompts. Flag must be set at session start —
cannot be applied mid-session.

### Model choice
Default Sonnet 4.6 for all seed execution prompts.
Adaptive mode not justified — decisions are pre-locked.

---

## WHAT THIS SESSION DID NOT COVER

- product_strategy.md Section 3A (Alert Library) — still pending
- technical_architecture.md DDL update — still pending
- Meta seed script — next session
- Customer discovery interviews — still zero completed

---

## CONTEXT FOR NEXT SESSION PROMPT

The system prompt (Lead Product Architect persona) is unchanged.
Four source documents remain the same.
Add this to the next session's context:

"Shopify seed is complete. 11/11 validation checks passed.
84,229 orders seeded across June 2024 – May 2026.
seed_manifest_shopify.json written and ready for Meta consumption.

Six architectural fixes were applied to seed_shopify.py.
All subsequent seed scripts must inherit these fixes —
see chat_context_2026_05_17.md for the complete list.

Next action: seed_meta.py consuming seed_manifest_shopify.json."
