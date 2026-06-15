# Profit Sentinel — Chat Context
## Date: 2026-05-20 (Session V4)
## Topic: historical_pattern_scan.py — Design, Prompt, Execution, Completion

---

## SESSION PURPOSE

Design and build `historical_pattern_scan.py`. All 6 design questions were
locked in the previous session (state_2026_05_20_v2.md). This session wrote
the Claude Code prompt and executed the script to completion.

---

## CLAUDE CODE PROMPT — KEY DESIGN DECISIONS CARRIED IN

All 6 design questions (Q1–Q6) were locked before this session. The prompt
encoded:

- **Q1 (Pattern detection):** Reconstruct Agent A threshold logic as standalone
  SQL, find trigger events, look forward N days per chain, binary hit definition,
  observable_instance_count as denominator only
- **Q2 (Confidence scoring):** candidate <4 obs OR <70% hit rate; provisional
  4–9 obs AND ≥70%; core ≥10 obs AND ≥80%
- **Q3 (Novel chain discovery):** Separate code path, sparsity filter (≥4
  trigger events), effect size gate (≥50% of col_B SD), calendar dispersion
  check (>60% in fashion windows → calendar_clustered), 500-pair cap
- **Q4 (client_specific promotion):** Track 1 deferred (DEBT-T1), Track 2
  single-client depth only, practitioner_approved required, exact string
  pair matching
- **Q5 (Failure handling):** Per-source DQ pre-checks, scan_skipped_reason
  column, pending_connectors auto-detection in incremental mode
- **Q6 (Output format):** Two onboarding message variants (leakage /
  forward_promise), GMV derived from Shopify, $ threshold ≥1% GMV AND ≥2
  patterns, NLQ reference in both variants

---

## PROMPT ENGINEERING DECISIONS

### Transaction pattern (Risk 1 mitigation)
Constraint 2 was tightened from vague "wrap in transactions" to explicit
per-phase `with conn:` pattern:
```python
try:
    with conn:  # psycopg2 context manager = auto BEGIN/COMMIT/ROLLBACK
        # phase writes here
except Exception as e:
    update_scan_status(conn, client_id, 'failed')
    raise
```
Each phase independently committed — Phase 3 failure does not roll back
Phase 2 writes.

### Novel chain memory bound (Risk 2 mitigation)
500-pair cap stated explicitly in constraints with fallback: evaluate the
500 pairs with highest col_A variance when cap is hit.

### Auto-approval configuration
`settings.local.json` in `.claude` folder — added one line:
`"Bash(python connectors/historical_pattern_scan.py *)"` to the existing
allow array. No `--dangerously-skip-permissions` flag used.

### Token limit
`CLAUDE_CODE_MAX_OUTPUT_TOKENS = 60000` set as permanent Windows system
environment variable. Script generation hit the 32,000 default limit.

---

## EXECUTION RESULTS

**Run mode:** `--mode full`, `--client_id client_azure_co`
**Completed at:** 13:09 UTC, 2026-05-20

| Check | Result |
|-------|--------|
| `historical_scan_status` | `complete` ✓ |
| `causal_pattern_validation` | 22 rows — 1 core, 1 provisional, 20 candidate |
| `candidate_signals` | 440 rows |
| `dq_metric_scores` | 7 rows (all sources) |
| `onboarding_messages` | 1 row — variant: `forward_promise` |

**Phase outcomes:**
- DQ: 7 sources, 2 chains skipped (C1: gorgias_tagging_insufficient,
  Chain5: insufficient_history)
- Known chains: 14 scanned, 8 skipped, tiers: 1 core / 1 provisional / 20 candidate
- Novel discovery: 500-pair cap hit, 440 written, 80 single_client_core
- GMV derived: $6,818,827.73
- Lookback: 718 mart days
- Message: forward_promise variant

**One bug auto-corrected:** `RealDictCursor` passed to `_table_exists` which
used integer indexing — Claude Code self-corrected during execution. No data
impact.

---

## KEY DEVIATIONS TO CARRY FORWARD

| Deviation | Impact | Action |
|-----------|--------|--------|
| 80/440 novel pairs flagged `single_client_core` | Inflated by synthetic data correlations. Will be much lower on real client. | Do not treat as production baseline. Monitor at first real client. |
| `forward_promise` variant fired (not `leakage`) | Leakage threshold not crossed on synthetic data — expected. | Leakage variant will fire on real client with richer history. |
| `dq_metric_scores.score_date` stored as `timestamptz` | `WHERE score_date = CURRENT_DATE` returns 0 rows | Use `date_trunc('day', score_date) = CURRENT_DATE` |
| New table created: `public.onboarding_messages` | Not in original DDL spec | Table is live. Carry forward in all future schema references. |
| D-21 (GMV derivation) now COMPLETE | Was listed as PENDING pre-session | Update pre_agent_build_checklist.md |

---

## PRE-AGENT B BLOCKERS REMAINING

| Item | Status |
|------|--------|
| B-1: causal_pattern_validation seed rows (56 hardcoded chains) | PENDING — highest priority |
| B-2: candidate_signals seed rows | PENDING |
| B-4: G1 ad set → SKU mapping decision | PENDING |
| B-5: Fashion Causal Graph in code | PENDING — high priority, design task |
| B-6: promotion_threshold values | PENDING |
| D-17: Novel chain review infrastructure | PENDING |
| D-20: pending_connectors onboarding question | PENDING |
| S3-P3: stg_klaviyo_profiles column names | PENDING |

D-12 and D-21 are now complete.

---

## SUGGESTED NEXT SESSION FOCUS

B-1 and B-5 are the two most complex remaining blockers and are related:
- B-5 (Fashion Causal Graph in code) defines the full chain library
- B-1 (seed the 56 chains) depends on knowing which chains are already
  written by `historical_pattern_scan.py` to avoid duplicates

Recommend designing B-5 first (or jointly with B-1) in a Claude.ai strategy
session before going to Claude Code. Key questions:
1. Python dict vs JSON file vs database table for the graph representation
2. How does Agent B traverse it — node lookup, not graph traversal?
3. Which of the 56 hardcoded chains overlap with the 22 already in
   `causal_pattern_validation` from the historical scan?

---

## KNOWN SCHEMA DRIFT — FULL LIST

- `alert_log`: `alert_type` (NOT `signal_type`)
- `alert_log`: `evidence_stack_json` (NOT `evidence_stack`)
- `signal_value` + `threshold_value` separate numerics (NOT `signal_values` jsonb)
- `client_id`: `client_azure_co` (NOT `azure_co`)
- `is_synthetic` lives in staging tables for Airbyte sources (Airbyte drops
  unknown columns on sync)
- Meta attribution window hard break: January 12 2026
- `brand_event_calendar`: zero rows in synthetic data
- `stg_klaviyo_profiles`: `profile_id` (not `customer_id`), `vip_status`
  (not `is_vip`)
- `stg_loop_refunds` does not exist — use `stg_loop_returns`
- `stg_meta_ad_performance`: no `attributed_revenue` — proxy: spend × purchase_roas
- `stg_klaviyo_flows`: no date column — use `stg_klaviyo_email_events` for
  time-series
- GA4 tables absent in synthetic data — NULL mart columns expected
- `dq_metric_scores.score_date`: stored as `timestamptz` not `date`
- `public.onboarding_messages`: new table, created by historical_pattern_scan.py
