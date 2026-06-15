# Profit Sentinel — Chat Context
## Date: 2026-05-20 (v1)
## Session: historical_pattern_scan.py Design — Q2 and Q3

---

## Q2 — CONFIDENCE SCORING FORMULA (LOCKED)

### What is an instance?
An instance is one historical occurrence where a leading signal crossed its threshold. Example using Chain 1 (CPM spike → ROAS drop, lag = 3 days):

The scan finds every date where CPM rose ≥20% over a 3-day rolling baseline. Each such date = one instance. For each instance, the scan checks whether ROAS dropped ≥15% within the lag window (3 days ± 2). Hit = 1 if yes, 0 if no.

Observable instance = one where the outcome window has fully closed (trigger_date ≤ scan_date − (lag_days + 2)). Recent instances within the unclosed window are counted in `instance_count` but excluded from `hit_rate` denominator.

### Hit definition
Both the leading signal AND the outcome metric must cross their respective live-agent thresholds within the lag window (lag_days ± 2 days). Binary — 1 or 0. No magnitude weighting. Uses the same thresholds as the live agent. Threshold values at scan time recorded in `threshold_at_scan_time` (jsonb) for auditability.

### Tier boundaries (dead zone 6–9 closed — Option A accepted)
- `candidate`: <4 observable instances OR <70% hit rate — uncertainty disclosure, multi-signal gate active, confidence score 0–40
- `provisional`: 4–9 observable instances AND ≥70% hit rate — standard Evidence Stack, gate active, confidence score 41–70
- `core`: ≥10 observable instances AND ≥80% hit rate — gate removed, fires on leading signal alone, confidence score 71–100

### Multi-signal confirmation gate
- `candidate` / `provisional`: Agent B requires at least one corroborating mart column in the same causal chain trending in the predicted direction before firing
- `core`: gate removed — alert fires immediately on leading signal alone, same day threshold crossed
- Novel client-specific chains at `core` tier: gate retained until `practitioner_approved = true` manually set

### Alert tone by tier (same alert, three versions)
- `candidate`: hedged — "limited confidence", "we're watching for a second confirming signal"
- `provisional`: standard Evidence Stack, specific recommendation, corroborating signal confirmed before firing (possible 1–2 day delay)
- `core`: assertive — "act now", instance count explicit as evidence, fastest (fires day threshold crossed)

### Why core threshold stays at 10
Core removes the multi-signal gate — that is a meaningful product decision. 10 instances is the right bar for removing it. Most chains reach provisional from historical data; core is earned via live outcome accumulation. Lowering to 7–8 was considered but rejected.

### Fields written to causal_pattern_validation
- `instance_count` — all instances found including recent unobservable
- `observable_instance_count` — denominator for hit_rate
- `confirmed_count` — hits
- `hit_rate` — confirmed_count / observable_instance_count
- `threshold_at_scan_time` — jsonb of thresholds active at scan time
- `confidence_tier` — candidate / provisional / core
- `historical_scan_seeded = true`

---

## Q3 — NOVEL CHAIN DISCOVERY (LOCKED)

### Mechanism: unconstrained bivariate sweep
Scan all mart column pairs. No predefined whitelist of additional pairs — real data surfaces what is worth hardcoding. Additional 24 hardcoded pairs were considered and rejected.

### Sparsity filter
Leading signal must have crossed its threshold ≥4 times in full history before the pair is stored. Pairs below this are silently dropped — too sparse to be meaningful.

### Storage: nothing auto-promotes
All novel candidates written to `candidate_signals` with `source = 'historical_scan'` and `client_specific = true`. Nothing auto-promotes to `causal_pattern_validation`. Promotion requires practitioner review.

### Pre-filters before practitioner review

**Calendar dispersion check:**
- Extract all trigger dates for the novel pair across all instances
- If >60% fall within known fashion calendar windows (BFCM Nov 15–Dec 5, SS drop Feb–Mar, FW drop Aug–Sep, January returns Jan 5–25) → `calendar_clustered = true`
- Cross-client convergence on `calendar_clustered = true` pair: increases confound suspicion, not signal confidence. This is the key insight — cross-client convergence in the same vertical at the same calendar period is observationally identical whether the cause is genuine or seasonal confounding. Calendar dispersion is the distinguishing test.
- `calendar_clustered = true` but causally plausible → `confound_unresolved = true` — explicit practitioner question: "Is the calendar causing both signals, or just the context in which the mechanism activates?" Example: swimwear February CPM spike → genuine (auction competition). BFCM Gorgias volume → return rate: confound.

**Effect size minimum:**
- Outcome metric must move by ≥50% of its live-agent threshold to count as a hit
- Eliminates weak-effect true correlations that are technically real but not actionable

### Two promotion tracks

**Track 1 — Cross-client convergence:**
Novel pair appears in 3+ clients of same `vertical_tag` with `calendar_clustered = false` → fast-tracked to practitioner review as likely genuine → validated → hardcoded into chain list → re-scan confirms instances → promoted to `causal_pattern_validation`. Applies globally to that vertical. `client_specific` becomes false.

**Track 2 — Single-client depth:**
Novel pair reaches ≥10 observable instances at ≥80% hit rate within one client → `single_client_core = true` → Track 2 practitioner review queue → `practitioner_approved = true` manually set → core behaviour activates for that client only. Remains `client_specific = true` permanently — never promoted to global list without Track 1 validation.

Track 2 is a disproportionate moat: brand-specific causal intelligence that deepens over time. Competitor cannot replicate — they don't have the cross-source data to detect it. Switching cost grows as Track 2 depth accumulates.

### Promotion path (both tracks)
Practitioner review → validated → hardcoded → re-scan confirms (against existing mart data, no re-pull needed) → `causal_pattern_validation`. Re-scan is fast — mart already built.

### Practitioner review at scale
Manual review breaks at 200 clients. Solution: machine pre-filtering reduces volume, practitioner applies domain judgment to shortlist only.

**Monthly practitioner digest (internal Slack, not founder-facing):**
- Triggered after monthly incremental sweep completes
- Target: <10 items/month regardless of client count
- Each card: leading signal (plain English), outcome (plain English), instances, hit rate, calendar_clustered status, effect size, clients showing this, 3-button response (✅ Validate / ❌ Reject / ⏳ Watch)
- Deferred until 5+ beta clients — manual DB review acceptable until then
- Requires Agent D secondary output mode (internal digest distinct from founder-facing Evidence Stack) — add to Agent D spec

### Seasonal confound risk
`seasonal_confound_risk = true` when both signals show correlated seasonality with the same calendar anchor. Strongest pre-filter — eliminates ~40–60% of spurious candidates in fashion data.

### Execution: two run modes
- **Full sweep (onboarding):** Async, Step 6, silent completion, no founder-facing message. `historical_scan_status` updated. `last_historical_scan_at` written.
- **Monthly incremental:** Scheduled 1st of month. Incremental window since `last_historical_scan_at`. New novel pairs validated against full history before writing to `candidate_signals` (not re-pulled — uses existing mart).

### New fields in candidate_signals
`leading_signal_column`, `outcome_column`, `observable_instance_count`, `hit_rate`, `calendar_clustered`, `confound_unresolved`, `seasonal_confound_risk`, `single_client_core`, `practitioner_approved`

### New fields in client_config
`last_historical_scan_at` (timestamptz), `historical_scan_status` (text: pending/running/complete/failed)

---

## OPEN DECISIONS NEXT SESSION — Q4, Q5, Q6

Q4: `client_specific` promotion rules — exact conditions beyond 3-client threshold (vertical_tag match, network-level hit rate, practitioner sign-off automatic or manual?)

Q5: Failure handling — (a) sparsity filter <4 crossings, (b) brand <90 days on a connector, (c) cross-source chain limited by shallowest connector

Q6: Exact output format written to `causal_pattern_validation` and `candidate_signals` at scan completion, and what gets written to onboarding completion log (internal, not founder-facing)
