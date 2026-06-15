# Profit Sentinel — Chat Context
## Date: 2026-05-26
## Version: v2
## Session: Alert Review — D1 Gap 2 Complete

---

## SESSION PURPOSE

Continue D1 gap review from state_2026_05_26_d1_gap1.md.
Gap 1 (COGS architecture) was locked in the prior session.
This session: full deliberation of Gap 2 (threshold definition),
covering Trigger A (step change) and Trigger B (slow bleed).
Both triggers fully locked. Next session starts at Gap 3.

---

## GOVERNING PRINCIPLES REINFORCED THIS SESSION

### No Hardcoding Principle (New — Gap 2)
Every threshold and window must be derived from the brand's own data.
Fixed pp values and fixed calendar windows are architectural debt.
All parameters configurable and outcome-tracked from onboarding.

### Historical Data Used From Day 1 (Reinforced)
We have historical data at onboarding. No 6–8 week wait.
Calibration runs retrospectively at onboarding using full history.

### Permanently Promotional Brand = Different Alert (New — Gap 2)
A brand with no meaningful BAU is not served by a CM baseline alert.
D1 Trigger A and B disabled for sparse_bau_profile brands.
D2 (Discount Dependency Creep) elevated as primary margin signal for this archetype.

---

## TRIGGER A DELIBERATION PATH

### Opening challenge: fixed comparison windows
Original proposal: "same 7 days, 4 weeks ago." Challenged immediately.
4-weeks-ago comparison fails in all these cases:
- 4 weeks ago was a sale event → comparing to depressed baseline
- 4 weeks ago was an echo period → also depressed, not comparable
- Current week is an echo period → expected compression, not an alert
- Current week had an influencer campaign whose returns haven't cleared

### Resolution: abandon fixed comparison windows entirely
Build a brand-specific structural CM baseline from verified BAU days only.
IQR band (p25–p75) replaces point estimate — acknowledges that the brand
legitimately operates across a range.

### Echo period — must be modelled
Echo period is the period after a sale event when returns are clearing.
Two distinct conditions from active event and from BAU:
- Active event: sale/campaign running. D1 suppressed.
- Echo period: event ended, return volume still elevated. D1 suppressed.
- BAU: no event, no echo, returns within normal range. D1 can fire.

Key design decision: echo closes when rolling 7-day return average
drops below 1.3× BAU for 7 consecutive days (hysteresis pattern).
Opening threshold (1.5×) is higher than closing threshold (1.3×) —
prevents oscillation from secondary return waves.

### 7 clean days required (not 5 or 6)
Challenged: weekday/weekend order mix creates directional bias in CM.
Weekends drive 35–45% of weekly orders and skew toward full-price,
higher-margin purchases. A CM read missing a Saturday is biased upward.
A CM read missing a Saturday and Sunday is materially different from
one that includes both.
Resolution: 7 clean days required, including ≥1 Saturday + ≥1 Sunday.

### Seasonality — cannot use 180-day window
180-day window spans seasons. A brand selling summer wear has structurally
different CM in June vs October. Pooling produces a baseline that is wrong
for both periods.
Resolution: 90-day rolling BAU window. Seasonal contamination acknowledged
but addressed by requiring same-season comparison in Trigger B.

### Self-calibrating 3-pass bootstrap
Exclusion filters and BAU day identification are interdependent.
Bootstrap approach: 3 passes converging on a stable BAU day set.
Pass 1: hard event flags only. Pass 2: echo period filter applied.
Pass 3: refinement and season profile computation.
Eliminates circular dependency without requiring manual resolution.

### Permanently promotional brand
If bau_coverage_rate < 15% after bootstrap: sparse_bau_profile = true.
Trigger A disabled. Not an alert problem — an archetype problem.
A brand in permanent promotion has no meaningful BAU to compare against.
D2 is the correct signal for this archetype.

### Threshold: adaptive, not fixed
MIN(MAX(SD × 2.0, 3pp floor), 8pp ceiling).
SD = standard deviation of daily CM across BAU days.
A stable brand (SD = 1pp) alerts at 2pp drop — 2σ event for them.
A volatile brand (SD = 6pp) alerts at 8pp (ceiling) — prevents waiting
for a catastrophic drop while still being meaningful.

### Structural break detection: continuous, not one-time
Onboarding question was proposed and challenged. A founder who pivots
6 months after onboarding cannot be handled by a one-time question.
Resolution: 30-day rolling self-detection. If recent p50 has shifted
>5pp from prior 60-day BAU p50, and shift persisted ≥21 BAU days →
structural_break_detected = true → baseline resets → founder asked
retrospectively to confirm what changed.

---

## TRIGGER B DELIBERATION PATH

### What a slow bleed actually looks like
Not a smooth downward line. Episodic — events, echoes, BAU, breaks.
A founder running their business sees each BAU week in isolation and
thinks "a bit soft." They never see the trajectory because they compare
this week to last week, which was an echo period.
Slow bleed is only visible when comparing BAU to BAU across time.

### Original proposal: linear regression on 28 days
Challenged: fashion CM is non-linear. A linear regression across 28 days
that includes two echo periods will produce a negative slope explained
entirely by those events. Regression cannot distinguish bleed from events.
Additionally, regression on 8–20 observations is unreliable regardless
of threshold chosen. Abandoned.

### Cluster-based approach: also abandoned
Proposed clusters of BAU days compared p25 to p25. Challenged:
- Clusters have different lengths and different weekday/weekend composition
- P25 comparison between an 8-weekday cluster and a 5-weekday cluster
  is biased by day-type mix, not genuine margin deterioration
- Z-score normalisation proposed to fix this — challenged: z-scores on
  3–8 observations per day type are statistically unreliable

### Resolution: complete BAU weeks as unit of analysis
A complete BAU week: all 7 Mon–Sun days are clean (no event, echo,
public holiday on any day). This eliminates day-mix contamination
entirely — every qualifying week has the same composition.
No normalisation needed. No z-scores. No day-type medians.

Minimum: 8 complete same-season BAU weeks.

### Mann-Kendall trend test
Non-parametric. No linearity assumption. Works reliably at N=8–20.
Detects monotonic decline in any shape. Robust to outlier weeks.
Firing condition: significant downward trend at p < 0.10.

### Theil-Sen slope
Natural companion to Mann-Kendall. Median of all pairwise slopes.
Robust to outliers. Expressed in pp/week — interpretable units.
Used as magnitude gate: confirms trend is large enough to matter.

### Magnitude threshold: brand-adaptive
bau_weekly_cm_sd × 0.20 with floor 0.2pp/week, ceiling 0.5pp/week.
A brand losing 20% of one SD of their natural CM volatility per week,
consistently across all BAU week pairs, is experiencing a genuine
structural bleed. Below this — within noise. Above ceiling — already
serious enough that Trigger A may have fired.

### Historical calibration at onboarding
Same pattern as Trigger A. Run Theil-Sen retrospectively across all
available complete BAU weeks at onboarding. Find the slope that
preceded known business responses. Store as trigger_b_theil_sen_multiplier.
Default 0.20 applies only when history is insufficient.

### Seasonality for Trigger B
All 8+ qualifying weeks must be from same season window (same
brand_season_profile window type). Season derived from brand's own
BAU order volume rolling median, not hardcoded calendar.
Flat profile (peak/trough gap < 2× BAU order SD): all weeks comparable.
Cross-season year-on-year comparison: enabled when no structural break
between periods, ≥13 months history.

### Public holidays
Any week containing a public holiday is not a complete BAU week and
does not qualify. Single rule. No positional mapping. No mid-week
exclusion logic. Cleaner and more robust than day-type normalisation.

### Activation lag
8 complete BAU weeks may take 3–6 months for event-heavy brands.
Accepted. Trigger A handles point-in-time detection in the interim.
Activation lag surfaced as insight in Profit Audit, not as a limitation.

---

## KEY DECISIONS CHALLENGED AND REVERSED THIS SESSION

| Proposal | Challenge | Resolution |
|----------|-----------|------------|
| 6–8 week wait for baseline | Historical data available at onboarding | Reversed — calibrate from historical data immediately |
| Stage 1 (180-day) / Stage 2 (90-day) two-stage baseline | Seasonal contamination + pivot frequency | Reversed — single 90-day rolling BAU window |
| 180-day window | Spans seasons for busy brands | Reversed — 90 days |
| Onboarding question for structural breaks | Doesn't handle future pivots | Reversed — continuous 30-day rolling detection |
| 5-day cluster minimum for Trigger B | Weekday/weekend bias in p25 | Reversed — 7-day complete BAU week |
| Z-score normalisation for day-type | Small N, unreliable statistics | Reversed — complete BAU week eliminates need |
| Linear regression for slow bleed | Non-linear data, unreliable at small N | Reversed — Mann-Kendall + Theil-Sen |
| Cluster-based p25 comparison | Day-mix contamination across unequal clusters | Reversed — complete BAU weeks as unit |
| Fixed 2pp threshold | Too large to catch slow bleed early | Reversed — adaptive Theil-Sen slope |
| Public holiday positional mapping | Overly complex, thin data per position | Reversed — any public holiday week excluded |
| Hardcoded 1.3 ratio for flat profile | No empirical basis | Reversed — signal-to-noise ratio vs own SD |

---

## WHAT IS NOW LOCKED — COMPLETE SUMMARY

**Trigger A:**
- 90-day rolling BAU baseline using IQR band (p25–p75)
- D1 fires below p25 minus adaptive threshold: MIN(MAX(2×SD, 3pp), 8pp)
- Continuous structural break detection (30-day rolling)
- Retrospective founder confirmation of break
- Historical data used from day 1 — no wait
- Self-calibrating 3-pass bootstrap for BAU identification
- Sparse_bau_profile → Trigger A disabled, D2 elevated
- Echo period: opens at 1.5× BAU return rate
- Echo period: closes at rolling 7-day avg < 1.3× BAU for 7 consecutive days
- Event-type caps as maximum only: 21 days standard, 45 days peak
- Hysteresis prevents oscillation
- 7 clean days required including ≥1 Saturday + ≥1 Sunday

**Trigger B:**
- Unit of analysis: complete BAU week (all 7 days clean, no public holidays)
- Minimum 8 complete same-season BAU weeks
- Season detection: brand-derived from BAU order volume rolling median
- Flat profile: peak/trough gap < 2× BAU order SD → all weeks comparable
- Cross-season year-on-year: enabled when no structural break, ≥13 months history
- Trigger B disabled for sparse_bau_profile brands
- Trigger B disabled when < 12 months history (seasonal_profile = 'undetected')
- Mann-Kendall trend test: significant downward trend, p < 0.10
- Theil-Sen slope: < −(bau_weekly_cm_sd × 0.20), floor 0.2pp/week, ceiling 0.5pp/week
- Threshold calibrated from historical data at onboarding, outcome-tracked continuously
- Trigger B suppressed when Trigger A firing same week
- Activation lag surfaced in profit audit

---

## NEXT SESSION STARTING POINT

1. Load: state_2026_05_26_d1_gap2.md, this file,
         agent_d_build_spec.md, technical_architecture.md,
         product_strategy.md
2. Start: D1 Gap 3 — Causal decomposition
   Question: When D1 fires, how does Profit Sentinel decompose the margin
   compression across all drivers with appropriate confidence per driver?
3. Work through Gaps 4–9 in order
4. Write D1 alert language after all 9 gaps resolved
5. Then D2 → D3 → D4 → D5 → D6 → C → B → A → H
6. Consolidated Claude Code prompt after H-series only
