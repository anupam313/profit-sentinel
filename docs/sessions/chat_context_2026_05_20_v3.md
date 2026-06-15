# Profit Sentinel — Chat Context
## Date: 2026-05-20 (Session V3)
## Topic: historical_pattern_scan.py Design — Q1 + Mart Audit + Mart Patch

---

## SESSION PURPOSE

Design session for `historical_pattern_scan.py` before writing the Claude Code
prompt. Six design questions to resolve. This session covered Q1 in full and
completed a mart audit + patch as a prerequisite. Q2–Q6 carry to next session.

---

## Q1 — PATTERN DETECTION LOGIC (RESOLVED AND LOCKED)

### Core approach
For each causal chain, the scan:
1. Reconstructs Agent A's threshold logic as a standalone query across all
   historical mart rows — finds every date where threshold conditions were met
   ("trigger event")
2. Looks forward N days (chain-specific lag window) from each trigger event
   and checks whether the predicted outcome metric moved in the predicted direction
3. Records each trigger event as one instance. Outcome confirmed =
   confirmed_count increment. Outcome not confirmed = false_positive_count.
   Outcome window fell outside available history = excluded from denominator.

### Two outputs per scan
Output 1: Validate all known causal chains (56 + expanded list) against
historical data. Write confidence_tier to causal_pattern_validation.

Output 2: Discover novel patterns not in the known chain library. Write to
candidate_signals with source='historical_scan', client_specific=true.
This is the self-extending graph mechanism — not optional.

### Lag windows — locked
Fixed default lag windows with ±2 day tolerance band. Do NOT fit lag
distributions from historical data — circular dependency problem (fitting
a lag window requires the lag window as a parameter). Adjust a prior via
`effective_lag_days` written per client as live outcome data accumulates.

Practitioner rationale: the 8–12 day Gorgias→Loop return window is structural
(return shipping transit + customer initiation time) — doesn't vary within
contemporary womenswear vertical. What varies is rate level, not lag.
Meta CPM→ROAS lag varies by budget level but calibration belongs in CD-10
onboarding threshold session, not the historical scan.

### Confirmed lag windows

| Chain | Description | Lag |
|-------|-------------|-----|
| A1 | Channel ROAS gap | 7d |
| A2 | ROAS drop root cause — CPM | 7d |
| A3 | Channel ROAS ranking reversal | 7d |
| B1 | Creative fatigue | 3d (revised from 5d — fashion creative fatigues faster) |
| B4 | CPM spike / audience saturation | 7d |
| C1 | Sizing complaint velocity | 10d |
| C3 | SKU return rate outlier | 10d |
| C5 | Refund timing acceleration | 7d |
| D1 | Contribution margin compression | 7d |
| D2 | Discount dependency creep | 14d |
| D4 | AOV compression with margin impact | 14d |
| E1 | Email list health decay | 14d |
| E2 | Repeat purchase rate drop | 14d |
| E3 | High-LTV customers going quiet | 21d |
| F2 | Payment gateway failure | 5d |
| F4/F5 | PDP bounce → conversion drop | 5d |
| G1 | Stockout during active spend | 1d |
| G4 | Back-in-stock revenue window | 2d |
| Chain 1 | Post-launch CAC creep (new) | 14d |
| Chain 2 | Mobile vs desktop checkout gap (new) | 5d |
| Chain 3 | Post-purchase flow revenue isolation (new) | 14d |
| Chain 5 | Attribution double-counting expansion (new) | 14d |

Chains 4 (new collection return rate vs brand average) and 6 (SKU sell-through
velocity during active spend) deferred to Agent B design — B-4 (SKU-level
mart infrastructure) dependency.

### Threshold approach — locked
Use practitioner-informed default thresholds at onboarding. Historical scan
uses defaults to find instances and compute hit rates. `effective_threshold`
written per client from live outcome tracking post-onboarding (same CD-10
mechanism). NOT fitted from historical data — avoids circular dependency
(fitting threshold to the data you're scanning inflates hit rates).

---

## MART AUDIT — COMPLETED

Full audit of mart column availability for historical scan chains.

### Results summary
- 7 chains ready to scan immediately (A1, A2, A3, B1, B4, C1, E2, F2)
- 4 partial (column exists, weak signal on synthetic data)
- 6 columns missing — needed new mart CTEs
- 1 chain blocked (influencer cohort — UTM attribution join not built)

### Missing columns identified (pre-patch)
| Column | Source | Gap type |
|--------|--------|----------|
| avg_days_to_refund | stg_loop_returns | Missing CTE |
| aov_7d (rolling) | stg_shopify_orders | Missing CTE |
| effective_open_rate_7d | stg_klaviyo_email_events | Missing CTE + iOS adjustment |
| vip_purchase_gap_days | stg_klaviyo_profiles × shopify_orders | Missing CTE + formula |
| ga4_pdp_bounce_rate | ga4_pages | Missing source table |
| send_frequency_7d | stg_klaviyo_email_events | Missing CTE |

### Six new chains added (from deep fashion-expert analysis)
These were discovered during mart audit pass — not in original 56 chains:

**Chain 1 — Post-launch CAC creep**
Collection launch exhausts easy-to-convert existing audience → post-launch CAC
rises and doesn't recover to pre-launch level within 14 days → structural CAC
inflation misread as seasonal. Founders celebrate launch revenue and miss this.
New columns: `new_customer_rate_7d`, `blended_cac_7d`

**Chain 2 — Mobile vs desktop checkout gap**
Mobile checkout completion rate falls while desktop holds → blended CVR looks
"slightly soft" while $15K–$40K/week leaks undetected. Founders look at blended
CVR only — device split at checkout step level is invisible to them.
New columns: `mobile_checkout_completion_rate_7d`, `desktop_checkout_completion_rate_7d`
Note: NULL on synthetic data (GA4 absent) — will populate on real client.

**Chain 3 — Post-purchase flow revenue isolation**
Post-purchase flow revenue falls >20% over 28 days while list growth, open rate,
and campaign revenue hold → isolated flow degradation invisible in total Klaviyo
revenue. Post-purchase sequence is highest-margin Klaviyo revenue and degrades
silently.
New column: `post_purchase_flow_revenue_7d`

**Chain 4 — New collection return rate vs brand average** (DEFERRED — SKU-level)
New collection SKUs return at >8pp above brand average within 21 days of launch →
signals size chart inaccuracy, photography mismatch, or quality issue specific to
new supplier. Founders see aggregate return rate only.
Deferred: requires SKU-level mart infrastructure (B-4 dependency)

**Chain 5 — Attribution double-counting expansion**
Sum of channel-attributed revenues as % of Shopify total rises above 100% and
expands over 28 days → attribution overlap is growing, not shrinking → real
blended efficiency is worse than any single channel reports.
New columns: `meta/tiktok/klaviyo_attributed_pct_of_shopify_revenue`

**Chain 6 — SKU sell-through velocity during active spend** (DEFERRED — SKU-level)
Daily units sold on hero SKU declining week-over-week while spend holds → audience
saturation on that specific product before ROAS drops. Founders pause campaigns on
ROAS not sell-through velocity — action is late.
Deferred: requires SKU-level mart infrastructure (B-4 dependency)

---

## KEY DECISIONS MADE THIS SESSION

### Threshold validation approach
Discovery interviews cannot validate quantitative thresholds — founders can't give
calibrated lag numbers, only gestalt impressions. Thresholds are set from
practitioner-informed defaults, calibrated via live outcome tracking per client.
Same mechanism as every other threshold in the system (CD-10).

### SKU-level mart work deferred
Chains 4 and 6 require SKU-level mart CTEs. B-4 (ad set → SKU mapping) is the
foundational decision — building SKU-level columns now creates rework when B-4
resolves. Deferred to Agent B design session.

### Chain 3 (post-purchase flow) built now
Not a SKU-level dependency — flow-type filtering on stg_klaviyo_flows which already
exists. Built in mart patch.

### ios_mpp_multiplier added to client_config
Column: `ios_mpp_multiplier numeric default 0.65`
Rationale: 0.65 is the single most consequential assumption in every E-series alert.
If hardcoded and wrong for a specific client (Android-heavy audience → multiplier
closer to 0.85), every open rate alert misfires systematically.
Default 0.65 if not answered at onboarding. Never hardcode in mart SQL.

### blended_cac_7d — date-level join accepted
No order-level attribution at this stage. Date-level join: spend on day N /
new customers on day N. Noise cancels over 7-day rolling window. Column must
only be read as rolling average — single-day values meaningless. SQL comment
added to mart.

### D-16 logged — network-adjusted lag windows
Before network reaches 10 clients: add `median_lag_days` + `lag_sample_size`
to `network_pattern_benchmarks`. Background aggregation query runs after each
new client onboards, reads `effective_lag_days` grouped by `causal_chain_id`
+ `vertical_tag`. Network median replaces practitioner prior once ≥5 clients
same `vertical_tag`.
Dependency: `vertical_tag` accurate on all clients (mandatory — no cross-vertical
pooling). Confirmed in `pre_agent_build_checklist.md` as D-16.

### Product learning mechanism confirmed
System learns per-client lag and threshold via `effective_lag_days` and
`effective_threshold` written to `causal_pattern_validation` by outcome tracking.
Cross-network learning via D-16 (network_pattern_benchmarks). Both mechanisms
confirmed in architecture — no gap.

### Novel chain discovery is non-optional
Self-extending graph is the core moat claim. A scan that only validates 56 known
chains is architecturally incomplete. Both outputs (validate known + discover novel)
run in a single pass.

---

## MART PATCH COMPLETED — SESSION 3/4

13 new columns added across two mart models. Full validation results in
`state_2026_05_19_session3.md` and `state_2026_05_19_session4.md`.

### Key deviations to carry forward
- `aov_7d` at $265 vs $142–158 spec: seed includes tax+shipping. Correct on real client.
- `new_customer_rate_7d` at 0.133: seed mature repeat-purchase pattern. Metric correct.
- `blended_cac_7d` at $371: sparse denominator on synthetic data. Correct on real client.
- Klaviyo columns at 32/730 rows: batch dispatch dates only in seed. Dense on real client.
- GA4 columns NULL: no GA4 source tables in synthetic data. Expected.
- `vip_purchase_gap_days` formula bug fixed: was `now() - created_at` (age from today),
  fixed to LAG() inter-purchase gap. avg 42.1d (spec 30–90d ✓).
- `stg_klaviyo_profiles` actual column names: `profile_id` (not `customer_id`),
  `vip_status` (not `is_vip`).

---

## FILE NAMING NOTE

- `state_2026_05_19_session3.md` — Claude Code's file. More implementation detail
  (exact CTE names, source tables, post_purchase_flow_revenue = $11,978 / 6.3%).
- `state_2026_05_19_session4.md` — My EOD file. Better structured deviations and
  carry-forward. Both kept in project knowledge — complementary.

---

## WHAT IS NOT RESOLVED — CARRY TO NEXT SESSION

Q2 — Confidence scoring formula (exact formula: instance_count + hit_rate → tier)
Q3 — Novel chain discovery algorithm (leading indicator whitelist, effect size gate)
Q4 — client_specific flag promotion conditions (exact mechanics)
Q5 — Failure handling for insufficient connector history
Q6 — Output format at onboarding completion (database writes + founder Slack message)

No Claude Code prompt until all six questions are resolved and locked.
