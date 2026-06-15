# Profit Sentinel — Chat Context
## Date: 2026-05-17 (End of Day)
## Session: Seed Scripts Meta → Gorgias

---

## SESSION NARRATIVE

This session completed seed scripts for five sources (Meta, TikTok,
Klaviyo, Loop Returns, Gorgias) following the Shopify seed completed
in the prior session. All six scripts are now locked.

---

## KEY DECISIONS MADE THIS SESSION

### 1. --dangerously-skip-permissions approved
Running `claude --dangerously-skip-permissions` in Claude Code is safe
at this stage. Dev database with synthetic data only. No production
systems at risk. Avoids manual permission clicks during long seed runs.

### 2. Alert3 final count is 57 (not 60)
Spec overstated at 30 activations. Manifest has 29.
INF-2026-MAY-01 stage2 fires Day 21 = June 2 2026, which is outside
seed window (ends May 31). Correctly excluded by boundary check.
57 is the correct and final count. Closed.

### 3. fatigue_period_active semantics locked
True = founder has NOT yet systematised creative rotation
  (each fatigue event is a surprise, problem is ongoing)
False = founder HAS implemented rotation fix
  (Y2 events are residual, problem mostly solved)
Y1 rows: True. Y2 rows: False.
Patched in seed_meta.py and seed_tiktok.py. Locked.

### 4. Meta ROAS drop Check 5: 30.92% is correct
Spec said 18–22% for attribution window effect alone.
Actual is compound: attribution window (×0.80) AND audience
saturation (×0.83) both active post-Jan 12 2026.
Expected range updated to 25–35%. No data change needed.

### 5. Patch script required before Step 6
Six backfill items identified from architecture doc review:
  - return_lag_segment on loop_returns
  - verification_category on alert_log
  - vertical_tag on network_pattern_benchmarks
  - Meta synthetic data gaps (stored_before_retention_limit,
    Advantage+ campaign labels, deprecated fields)
  - influencer_profile table population (29 activations)
  - founder_preference_profile skeleton rows
Do as one patch script after seed_sentry.py, before dbt rebuild.

---

## BUILD STANDARDS ESTABLISHED THIS SESSION

All eight fixes below must appear in seed_ga4.py and seed_sentry.py:

Fix 1: No is_synthetic on raw table inserts
Fix 2: airbyte_meta_cols() on every Airbyte-managed row
Fix 3: Single transaction, ON CONFLICT DO NOTHING (bare form)
Fix 4: _nearest_pd_corr() before Cholesky
Fix 5: No explicit id on GENERATED ALWAYS columns
Fix 6: CREATE TABLE IF NOT EXISTS before all inserts
Fix 7: UNIQUE constraint on natural key before insert (from TikTok)
Fix 8: Cast numpy scalars via float()/int() before psycopg2 (from Klaviyo)

---

## PER-SCRIPT DECISIONS AND FIXES

### seed_meta.py
- Schema mismatch on actual Airbyte table: date_start (not date),
  adset_id (not ad_set_id), attribution_setting (not attribution_window),
  purchase_roas JSONB (not roas numeric), spend/cpm/ctr stored as text
- Script patched to match actual schema before running
- 5 stale B1 rows (ids 153,174,175,176,177) deleted before run
- fatigue_period_active corrected post-validation (was inverted)
- billing_statement uses dynamic column detection — confirmed 24 rows
  with $0.00 delta across all months

### seed_tiktok.py
- Failed on suppression_log step mid-run (prior tables committed)
- Re-run safe due to ON CONFLICT DO NOTHING
- Root cause: no UNIQUE constraints on tiktok_ad_performance or
  tiktok_organic_performance → duplicate inserts on re-run
- Fix: UNIQUE(campaign_id, date), UNIQUE(week_start),
  UNIQUE(client_id, alert_type, would_have_fired_at)
- Now fully idempotent

### seed_klaviyo.py
- Two apostrophe syntax errors in campaign subject lines
- numpy float64 leaking into psycopg2 → fixed via .tolist()
- iOS MPP model corrected: per-row 65% probability, not two-tier scheme
- Alert3 check: 57 rows (not 60) — root cause investigated and confirmed valid

### seed_loop_returns.py
- Pre-existing Airbyte loop tables had different schema — dropped and recreated
- suppression_log column names fixed (no suppressed_by_event_name in real schema)
- Defective unit received_date fixed: always initiated_date + 6-8 days
- CHECK 1 range widened to 2,300 (arc 2,116 + defective batch 110)
- Windows console encoding fixed: sys.stdout.reconfigure(encoding='utf-8')

### seed_gorgias.py
- Pre-existing Airbyte gorgias tables had JSONB schema — dropped and recreated
- Defective unit check failed: BFCM distribution consumed product_quality slot
  Fix: separate seed_defective_tickets() step added on top of BFCM arc
  Result: 50 explicit defective tickets + existing quality tickets = 105 total ✓
- Final: 10,296 tickets, 50 tag normalisation entries, 4 Alert5 chains aligned

---

## ARCHITECTURE REVIEW — CHANGES NOTED

From review of updated technical_architecture.md and product_strategy.md:

### Already handled in this session:
- fatigue_period_active semantics
- UNIQUE constraints on all seed tables
- numpy casting standard

### Needs patch script (after seed_sentry.py):
- return_lag_segment (Section 14 — return timing segmentation)
- verification_category A/B/C on alert_log (Section 14)
- vertical_tag on benchmarks (Section 14 — self-extending graph)
- Meta API breaking changes: Advantage+ labels, retention limit flag,
  deprecated field removal (Section 8)
- influencer_profile population (Section 3.2)
- founder_preference_profile skeleton (Section 3.2)

### Needs attention at dbt rebuild (Step 6):
- dbt models must use seasonally-adjusted D5 benchmarks
  (same-week-prior-year from Month 13, not flat baseline)
- Loop staging tables must segment by return_lag_segment
- Agent B must weight Gorgias complaint text over Loop reason code
  for sizing/fit causal chains (reason codes unreliable)

### New architectural additions (Sections 14):
- Self-extending Fashion Causal Graph: candidate_signals →
  causal_pattern_validation promotion pipeline
  Per-client: 3–5 validated instances → active for that client
  Cross-network: 10–15 instances across same vertical → global
  Cross-vertical promotion prohibited
- Dismissed alert outcome follow-up (Agent D behaviour):
  followup_queued flips true when dismissal was wrong
  Agent D queues thread message with outcome + impact
- Pre-fire uncertainty communication mandatory for all alerts:
  "I'm X% confident. What I'm less certain about: [specific element]"

---

## NEXT SESSION — IMMEDIATE ACTIONS

### Action 1 — Generate seed_ga4.py prompt (ready in this chat)
GA4 complexity: session stitching, bot filtering, enhanced ecommerce
gaps (Months 1–8), cross-device attribution loss, cross-source
alignment with all 6 prior scripts.

Key GA4 decisions to carry in:
  - GD7: 18% cross-device session stitching failure
  - GD8: bot traffic 5–12%, spikes during viral moments
    Seed as flagged rows, NOT filtered — Agent B needs to see contamination
  - GD9: add_to_cart double-firing (Month 1–3), Shop Pay missing (Month 1–8)
    H12 fires until Month 8
  - GD10: data <7 days: dq_score 81. Data >7 days: dq_score 96
  - GA4 purchase count vs Shopify: must show 20% gap (ad blocker loss)
  - 72-hour processing delay: last 3 days always provisional

### Action 2 — seed_sentry.py after GA4

### Action 3 — patch_script.py after Sentry (6 items above)

### Action 4 — Step 6 dbt rebuild

---

## OPEN QUESTIONS (not yet resolved)

### From product_strategy.md Section 12 (formally open):
- Whether Slack is definitively the right delivery channel
  (not yet validated by customer discovery)
- Whether $299/month is the correct Growth tier price
- Whether Gorgias tagging is consistent enough for Alert 5
- Whether founders will act on proactive alerts before seeing
  the problem themselves (the core hypothesis)

### Risk 1 — Customer Discovery (HIGHEST RISK)
No interviews completed. Compounds every week delayed.

---

## IMPORTANT CONTEXT FOR NEXT CHAT

1. The identity prompt (Lead Product Architect) must be pasted at the
   start of the next chat for consistent behaviour.

2. seed_ga4.py prompt is ready to generate — no additional decisions
   needed before writing it.

3. All 8 build standards (Fixes 1–8) are locked. Do not relitigate.

4. The patch script is a separate step after seed_sentry.py — do not
   attempt to bake patch items into seed_ga4.py or seed_sentry.py.

5. Shopify manifest (seed_manifest_shopify.json) remains the
   cross-source alignment anchor for GA4 and Sentry.
