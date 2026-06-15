# Profit Sentinel — Session State
## Date: 2026-05-19 (Session 2)
## Session: Deferred Items 2/3/4/6 + Step 10 Slack + Strategic Design

---

## LAST COMMIT

b44ae63 — unchanged from Session 1. No new Claude Code commits this session.
All work this session was: threshold fixes (DB-only), Slack bot build, and
strategy/architecture design (no dbt model changes).

---

## WHAT WAS COMPLETED THIS SESSION

### 1. Deferred Item 6 — blended_gross_margin_pct — COMPLETE

- ALTER TABLE: blended_gross_margin_pct column added to public.client_config
- azure_co (client_azure_co) set to 0.55
- mart_causal_chain_daily.sql: replaced hardcoded 0.55 with subquery reading
  from client_config via var("client_id")
- onboarding_flow.py: Q1b added — prompts for and validates gross margin
  (range 0.20–0.85), writes to client_config
- dbt run: PASS=22 WARN=0 ERROR=0
- contribution_margin_pct range unchanged: 32.85–52.91%

### 2. Deferred Item 2 — D1 Threshold Calibration — COMPLETE

- margin_floor_pct: 5.0 → 28.0
- contribution_margin_drop_threshold: 5.0 → 10.0
- client_id is client_azure_co (NOT azure_co — confirmed this session)
- D1 reads both values from client_config via _cfg() at agent_a.py:336-337
- Synthetic data distribution: min cm_pct = 32.85%, avg = 47.42%
- 0/730 dates below 28% floor → tested at temp floor 35% → D1 fires on
  3 dates: 2025-01-11 (cm=33.63%, chg=-15.63%), 2025-01-12, 2026-01-04
- Production floor reset to 28.0 after test confirmed signal path clean
- KEY TEST DATE FOR D1: 2025-01-11 → fires A1, D1, F2

### 3. Deferred Item 3 — C1 Threshold Calibration — COMPLETE

- gorgias_sentiment_threshold: 15.0 → 43.61 (p90 of signal distribution)
- Distribution: min -64.70%, max 326.97%, avg 6.29%, p75=22.24%, p90=43.61%
- p75 (181 firing dates) was in 150-200 band → used p90 per decision tree
- Firing rate at p90: 72/730 dates (9.9%) — below 15-25% target but
  acceptable; synthetic seed generated purchase_completed and complaint
  series independently, no engineered correlation
- C1 silent on 2025-03-01 (vel=25.80% < 43.61%) ✓
- C1 fires on 2025-10-15 (vel=89.26% >> 43.61%) ✓
- Per-client C1 recalibration required at real client onboarding (CD-10)
- KEY TEST DATE FOR C1: 2025-10-15 → fires A1, C1

### 4. Deferred Item 4 — Recipe C CVR Join Fix — COMPLETE

- Diagnostic confirmed two compounding problems in mart_cross_source_daily:
  Problem A: grain fan-out — ga4_funnel_daily joins at date×device_category
  but ga4_sessions_daily is at date×channel×device×country → overall_cvr
  duplicated per channel/country combination → AVG() was row-count weighted
  Problem B: mismatched populations — checkout_error_count counts
  checkout-step errors; avg_cvr measured entire site funnel
- Fix: replaced AVG(overall_cvr) with
  SUM(purchase_completed)::numeric / NULLIF(SUM(sessions), 0)
- purchase_completed confirmed as column name in stg_ga4_sessions
- avg_cvr range post-fix: 0.338–0.446 (ratio, not percentage) ✓
- avg_cvr mean = 0.42 — above real-world 0.01-0.10 range but this is
  synthetic seed artefact (purchase_completed seeded at ~40% of sessions)
- Direction now logically consistent: errors rising, CVR falling
- 20% co-movement on synthetic dates is seed artefact — recheck on first
  real client; if >10% co-movement persists, tighten err_chg threshold
- dbt run: PASS=22 WARN=0 ERROR=0

### 5. Step 10 — Slack Bolt Bot — COMPLETE

Files created: slack_bot/app.py, alert_formatter.py, action_handlers.py,
test_delivery.py, requirements.txt

SCHEMA DEVIATIONS FROM PROMPT SPEC (carry to all future sessions):
- alert_log column: alert_type (NOT signal_type) — confirmed throughout
- evidence_stack_json (NOT evidence_stack) — actual column name
- signal_value (numeric) + threshold_value (numeric) — NOT signal_values jsonb
- projected_impact absent from live schema → Block 6 correctly skipped
- alert_message absent → signal_value/threshold used in Block 3
- action_taken_at and dismissal_reason added via ALTER TABLE this session

Architecture:
- Socket Mode only (no ngrok, no webhooks)
- 7 blocks per alert (not 8 — projected_impact absent, skip per spec)
- LIMIT 5 in test_delivery.py (not 2 — needed for 3+ distinct alert types)
- All DB connections via DATABASE_URL from .env
- client_id = client_azure_co throughout

Verification results:
- 5 alerts posted to #all-profit-sentinel-dev (A1, C1, A1, F2, D1)
- 4 distinct alert types ✓ (exceeds 3-type requirement)
- Approve → action_taken_at written (id=329, A1) ✓
- Snooze → action_taken_at written, suppressed unchanged (id=328, C1) ✓
- Dismiss → dismissal_reason = capacity_constrained (id=327, A1) ✓
- app.py Socket Mode: "⚡️ Bolt app is running!" ✓
- /sentinel-test: PENDING (CD-12)

DEFERRED from Step 10:
- CD-11: Button UI polish — buttons remain active after click. Founder
  will assume click didn't register. Handler must update original message
  to replace actions block with plain text confirmation post-click.
  Fix before first beta client.
- CD-12: /sentinel-test slash command not yet verified.

CONFIRMED TEST DATES (use for all future Slack/Agent testing):
- 2025-10-15 → fires A1, C1
- 2025-01-11 → fires A1, D1, F2

---

## STRATEGIC DESIGN DECISIONS (see chat_context_2026_05_19_session2.md)

### Fashion Causal Graph — Scope Confirmed

- Full graph covers all 56 alert types (A1–G4 + H1–H19)
- Five alerts in Section 3 of product_strategy.md are day-one Phase 1
  only — not a product limitation. All 56 fire as connectors/history allow.
- Graph structure: DAG (directed acyclic graph), three layers:
  L1 upstream signals → L2 intermediate mechanisms → L3 financial outcomes
- Five core causal chains designed (sizing→returns, CPM→fatigue,
  influencer→ROI reversal, discount→margin, checkout error→CVR)
- Agent B prompt will cover all 56 chains, not just five

### Confidence Tier Framework — NEW

Three tiers added to causal_pattern_validation:
- candidate: <4 instances OR <70% hit rate
- provisional: 4-5 instances AND ≥70% hit rate
- core: ≥10 instances AND ≥80% hit rate (fires without multi-signal gate)

### Historical Pattern Scan — SCOPE REVISED (D-12 pulled forward)

historical_pattern_scan.py is now PRE-FIRST-CLIENT, PRE-AGENT B (not deferred).

Key decisions:
- No fixed 24-month lookback — pull per-connector maximum:
  Shopify/Klaviyo/Gorgias/Loop → account creation (no API limit)
  Meta → 13 months (hard limit)
  GA4 → post-July 2023 (UA replaced by GA4)
  TikTok → 24 months (practical limit)
  Sentry → 90 days (plan-dependent — most brands on Team/Business plan)
- Validates all 56 known chains against historical data → writes
  confidence tiers to causal_pattern_validation
- Discovers novel chains beyond 56 → writes to candidate_signals with
  source='historical_scan', client_specific=true
- Novel chains meeting provisional threshold → promoted to
  causal_pattern_validation as new alert types on day one
- Category B (action-confounded) patterns: same approach as future alerts —
  cannot know if founder acted historically either. Carry Layer 0 disclosure.
- Per-connector lookback days written to client_config on completion
- Runs after five confirmation questions, before first live alert fires

### NLQ (Natural Language Query) — Design Decision

- Architecturally feasible (mart layer queryable, Agent D uses LLM)
- NOT in current build sequence — build after first 3-5 beta clients
  validate Evidence Stack trust
- Build signal: 3+ beta clients ask for it unprompted
- Added as probe to discovery interview (Q7)

### DTC Revenue % — ICP Qualification

- Walmart/Target presence doesn't disqualify — but DTC must be >70% of revenue
- Added as listening probe to discovery interview Q3 KEY note
- Not a new interview question — surfaces naturally when founder lists channels

---

## DOCUMENTS UPDATED THIS SESSION

All three files below have been updated and output to /mnt/user-data/outputs/.
Replace existing versions in project knowledge AND local folder.
No need to keep previous copies — git history is the backup.

| File | Changes |
|------|---------|
| technical_architecture.md | causal_pattern_validation: confidence_tier + historical_scan_seeded added. candidate_signals: source + client_specific added. Promotion rules: confidence tier rules + historical scan spec. client_config: historical scan fields + per-connector lookback days. |
| product_strategy.md | Section 3: scope note added (five = day-one Phase 1 only, not limitation). Section 5: historical pattern scan added as Step 6 of onboarding. |
| pre_agent_build_checklist.md | D-12 scope fully rewritten, priority changed to pre-first-client/pre-Agent B. Header updated. |

Discovery interview also updated (discovery_interview_mos_v2.docx):
- Questions renumbered Q1–Q9 sequentially
- Q6 added: Sidekick/Pulse question
- Q7 added: NLQ probe
- Q8: was "Ranking" (signal priority)
- Q9: was "Q11" (the one question)
- DTC revenue probe added to Q3 KEY note

---

## IMMEDIATE NEXT ACTION

**historical_pattern_scan.py design session** (Claude.ai strategy, not Claude Code)

Six decisions to resolve before writing the Claude Code prompt:
1. Pattern detection logic — how to identify a causal chain occurrence
   in historical data without a live agent firing it
2. Confidence scoring formula — instance count + hit rate → tier
3. Novel chain discovery — what constitutes a detectable novel pattern
4. client_specific flag promotion rules
5. Where scan runs in onboarding sequence (confirmed: after five
   confirmation questions, before first live alert)
6. Whether Category B patterns need different detection approach
   (confirmed this session: no — same approach, different disclosure)

---

## OPEN DEFERRED ITEMS STATUS

### Must-do before first real client

| Item | Status |
|------|--------|
| D-10: business_model_type in client_config | PENDING |
| D-12: historical_pattern_scan.py | PENDING — design session next |
| CD-4: sku_cost_master populated | PENDING |
| CD-5: permanent_dq_limitations rows | PENDING |
| CD-6: suppression_log validated | PENDING |
| CD-7: brand_event_calendar populated | PENDING |
| CD-8: alert_data_lineage confirmed live | PENDING |
| CD-9: dq_metric_scores confirmed live | PENDING |
| CD-10: per-client C1 recalibration at onboarding | PENDING |
| CD-11: Slack button UI polish | PENDING — pre-beta client |
| CD-12: /sentinel-test verification | PENDING |

### Complete this session

| Item | Status |
|------|--------|
| Item 6: blended_gross_margin_pct | COMPLETE ✓ |
| Item 2: margin_floor_pct + drop threshold | COMPLETE ✓ |
| Item 3: gorgias_sentiment_threshold | COMPLETE ✓ |
| Item 4: Recipe C CVR join | COMPLETE ✓ |
| Step 10: Slack Bolt bot | COMPLETE ✓ |

---

## KNOWN SCHEMA DRIFT — CARRY FORWARD

- alert_log column: alert_type (NOT signal_type)
- evidence_stack column: evidence_stack_json (NOT evidence_stack)
- signal_value + threshold_value are separate numerics (NOT signal_values jsonb)
- client_id throughout: client_azure_co (NOT azure_co)
- Airbyte drops columns not in schema on every sync → is_synthetic lives
  in staging tables (stg_*) for Airbyte sources
- Meta attribution window hard break: January 12, 2026
- brand_event_calendar has zero rows in synthetic data

---

## FILES IN PROJECT KNOWLEDGE

| File | Action Required |
|------|----------------|
| Profit_Sentinel_Blueprint_v8.docx | No change |
| technical_architecture.md | REPLACE with updated version |
| product_strategy.md | REPLACE with updated version |
| pre_agent_build_checklist.md | REPLACE with updated version |
| state_2026_05_19_eod.md | Keep — Session 1 record |
| state_2026_05_19_session2.md | ADD — this file |
| chat_context_2026_05_19_session2.md | ADD — strategic decisions |
| gap_abc_decisions.md | Locked — no change |
| seed_decisions_gap_d_e.md | Locked — no change |
| seed_decisions_gap_f_g.md | Locked — no change |
