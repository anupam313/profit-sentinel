# Profit Sentinel — Chat Context
## Date: 2026-05-19 (Session 2)
## Purpose: Captures strategic decisions, architectural reasoning, and
## design choices from this session. Read alongside state_2026_05_19_session2.md.

---

## SESSION FOCUS

Two tracks:
1. Deferred items 2/3/4/6 + Step 10 execution (Claude Code)
2. Fashion Causal Graph design + Historical Pattern Scan architecture (strategy)

---

## FASHION CAUSAL GRAPH — KEY DECISIONS

### Scope: All 56 Alerts, Not Just Five

The five alerts in product_strategy.md Section 3 are Phase 1 day-one alerts
only — the subset that fires with Phase 1 connectors and no historical depth.
Agent A is architected to fire all 56. The others fire as connectors come live
and history accumulates. This is not a product limitation.

Alert count confirmed: 56 total (A1–A6, B1–B5, C1–C7, D1–D6, E1–E4,
F1–F5, G1–G4, H1–H19). H-series are system/DQ alerts, not founder-facing.

When other alerts fire by series:
- A3–A6: after TikTok Shop + Google Ads (Phase 2A)
- B2/B3/B5: after 90 days frequency history per client
- C2–C7: after Loop Returns confirmed >50% of ICP
- D2–D6: after Finaloop connected (Phase 2A)
- E1/E3/E4: after Klaviyo flow history ≥90 days
- F1/F3–F5: after Sentry coverage confirmed >45% of ICP
- G2–G4: after SKU-cost mapping confirmed
- H-series: fires whenever relevant — diagnostic, not founder-facing

### Graph Structure

DAG (directed acyclic graph) — edges flow one direction (cause → effect),
no cycles. Three layers:
- Layer 1: Upstream signals (leading indicators) — Agent A fires on these
- Layer 2: Intermediate mechanisms (cross-source joins)
- Layer 3: Financial outcomes (what founder feels in revenue/margin/ROAS)

Five core causal chains (full graph covers all 56):

Chain 1: Gorgias sizing velocity → Loop return spike (lag 6-13 days)
  → Net revenue per order falls → Post-return ROAS diverges
  → Fires A1 + C1. Verification: A.
  Agent B action: "Audit size chart for [top complaint SKUs]"

Chain 2: Meta CPM 3-day rolling spike → Frequency rising → CTR decay
  → CPC rising → ROAS compression
  → Fires A2 + B4. Verification: A.
  KEY BRANCH: CPM spike WITHOUT frequency rise = market-wide inflation
  (seasonal, not actionable). WITH frequency = creative fatigue (actionable).
  Meta Q4 (Oct-Dec) structural CPM inflation — suppress creative fatigue
  alert unless frequency also spikes.
  Both branches fire with different messages and confidence scores.

Chain 3: TikTok creator attribution spike → Shopify TikTok orders
  → Loop returns from same cohort → Return-adjusted revenue < creator fee
  → Fires A3. Verification: A.
  Return reason codes unreliable — weight Gorgias text over Loop reason
  code when both exist for same order.

Chain 4: Discount rate rising → AOV falling → Contribution margin
  falling below floor → Fires D1. Verification: B (action-confounded).
  Must distinguish from CPM-driven compression — check which moved first.

Chain 5: Sentry checkout error spike → GA4 checkout step drop → CVR
  falling → Revenue gap vs sessions baseline → Fires F2. Verification: A.
  Sentry rate-limits during BFCM (up to 40% underreporting) — apply caveat.

### No-Match Behaviour

When Agent B finds no matching causal chain:
- Fire to Slack as "unexplained signal — monitoring" (Option C)
- Log to candidate_signals simultaneously
- Founders want to know about unusual patterns even without explanation

### Agent B Prompt Scope

Agent B prompt will cover all 56 chains. The five above were teaching
examples for the graph structure design, not the complete spec.

---

## CONFIDENCE TIER FRAMEWORK — NEW ARCHITECTURE

Three tiers for causal_pattern_validation:

| Tier | Instances | Hit Rate | Behaviour |
|------|-----------|----------|-----------|
| candidate | <4 | any | Fires with explicit uncertainty disclosure |
| provisional | 4-5 | ≥70% | Fires with standard Evidence Stack |
| core | ≥10 | ≥80% | Fires without multi-signal confirmation gate |

This replaces the previous binary active/inactive model. Tiers are computed
from both historical scan (onboarding) and live alert outcome tracking.

---

## HISTORICAL PATTERN SCAN — FULL ARCHITECTURE DECISION

### Why This Matters

Previous architecture treated day 1 as a blank slate — waiting months for
live alerts to accumulate confidence. Evidence Stack Layer 3 (historical
precedent) was populated from generic cross-network benchmarks, not brand data.

New approach: scan all available history at onboarding → Layer 3 populated
from real brand data on day one → confidence scores meaningful from first alert.

Brands with 5+ years of Shopify/Klaviyo/Gorgias history produce
significantly higher confidence at launch than brands with 12 months.

### Per-Connector Maximum Lookback

| Connector | Max Lookback | Constraint |
|-----------|-------------|------------|
| Shopify | Account creation | No API limit |
| Klaviyo | Account creation | No API limit |
| Gorgias | Account creation | No API limit |
| Loop Returns | Account creation | No API limit |
| Meta Ads | 13 months | Hard API limit (unique-count fields) |
| GA4 | Post-July 2023 | UA replaced by GA4; pre-2023 inaccessible |
| TikTok | 24 months | Practical limit (API varies) |
| Sentry | 90 days | Plan-dependent (Team/Business = 90 days) |

No fixed 24-month cap. Pull as far back as each connector allows.
Per-connector actual lookback days written to client_config on completion.

### Two Outputs of Historical Scan

**Output 1 — Validate existing 56 chains:**
- Identify occurrences of each known causal chain in historical data
- Count instances, compute hit rate
- Write confidence_tier to causal_pattern_validation with
  historical_scan_seeded = true
- Cross-source chains limited by shallowest connector in the chain
  (e.g., F2 chain limited by Sentry 90-day window)

**Output 2 — Discover novel chains beyond 56:**
- Identify repeating patterns not matching any existing chain
- 4-5 instances at ≥70% hit rate → write to candidate_signals with
  source = 'historical_scan', client_specific = true
- Novel patterns meeting provisional threshold → promoted to
  causal_pattern_validation as new chains before first live alert fires
- Brand may start with more than 56 active alert types on day one
- client_specific = true until cross-network validation (10-15 instances
  across clients of same vertical_tag)

### Category B (Action-Confounded) Handling

Key decision: same approach as future alerts — you cannot know whether
founder acted historically either. The action-confounded problem is
identical for historical and future data.

Solution: compute confidence from hit rate exactly as Category A.
Add explicit Layer 0 disclosure: "Outcome may reflect founder action rather
than natural resolution — this affects confidence calculation."

This was a pushback from this session that was withdrawn after reasoning
confirmed the problem is symmetric across time.

### Onboarding Sequence Position

Runs as Step 6 of onboarding:
1. Connector setup
2. Staging + dbt
3. Three-bucket revenue validation
4. Five confirmation questions
5. Per-connector C1 threshold calibration (CD-10)
6. **Historical pattern scan** ← new mandatory step
7. First live alert fires

---

## NLQ (NATURAL LANGUAGE QUERY) — DESIGN DECISION

Founder types "why did my ROAS drop?" → plain English answer with data proof.

Architecturally feasible: mart layer queryable, Agent D uses LLM for Evidence
Stack formatting. Extension to free-text routing is a fifth agent or Agent D
extension.

NOT in current build sequence. Build after first 3-5 beta clients validate
Evidence Stack trust. Build signal: 3+ clients ask for it unprompted.

Added as Q7 to discovery interview: "Would you ever want to just type a
question and get an answer — rather than wait for an alert to fire?"
Do not prompt or explain NLQ — let answer come naturally.

---

## DTC REVENUE % — ICP QUALIFICATION NOTE

Walmart/Target presence doesn't disqualify a brand from Phase 1.
Disqualifier: DTC revenue <70% of total revenue.

If DTC <70%: return rates, ROAS, margin signals are all distorted because:
- Shopify GMV understates true brand revenue
- Retail returns don't flow through Loop
- Gorgias volume diluted (retail customers contact retail support)
- Meta ROAS inflated (customers may convert in-store)

Probe: added to discovery interview Q3 KEY note as listening instruction —
not a formal question. Surfaces naturally when founder lists channels.

---

## DISCOVERY INTERVIEW — CHANGES MADE

File: discovery_interview_mos_v2.docx (Ministry of Supply interview)

Changes vs original:
- Renumbered Q1–Q9 sequentially (was broken — Q11 appeared after Q3)
- Q6 added: Sidekick/Pulse question + listen-for block
- Q7 added: NLQ probe + listen-for block
- Q8: was "Ranking" label in Section 3
- Q9: was "Q11" in Section 4
- Q3 KEY note: DTC revenue % probe added
- All cross-references updated (Q11 → Q9 in run sheet, instruction bar,
  pivot signals)
- Aman + Rashi names intentional — personalised for Ministry of Supply

---

## STEP 10 SCHEMA DEVIATIONS — CARRY TO ALL FUTURE SESSIONS

These differ from the technical_architecture.md spec. Live schema wins.

| Spec said | Live schema has |
|-----------|----------------|
| evidence_stack (jsonb) | evidence_stack_json (jsonb) |
| signal_values (jsonb) | signal_value (numeric) + threshold_value (numeric) |
| projected_impact column | absent — Block 6 correctly skipped |
| alert_message column | absent — use signal_value/threshold in Block 3 |
| action_taken_at | added this session via ALTER TABLE |
| dismissal_reason | added this session via ALTER TABLE |

---

## DOCUMENTS UPDATED THIS SESSION

Three .md files updated — replace in project knowledge AND local folder:
- technical_architecture.md
- product_strategy.md
- pre_agent_build_checklist.md

New files to add to project knowledge:
- state_2026_05_19_session2.md
- chat_context_2026_05_19_session2.md (this file)
- discovery_interview_mos_v2.docx (updated interview for Ministry of Supply)

---

## NEXT SESSION AGENDA

**historical_pattern_scan.py design session** (Claude.ai, not Claude Code)

Six open design questions:
1. Pattern detection logic — how to identify a causal chain occurrence
   in historical data without a live agent firing it. Likely: query mart
   tables for signal columns meeting threshold criteria across a date range,
   then check if outcome metric moved in predicted direction within lag window.
2. Confidence scoring formula — exact formula for instance_count + hit_rate
   → tier assignment
3. Novel chain discovery algorithm — what constitutes a detectable novel
   pattern. Likely: correlation analysis between leading and lagging mart
   columns above a minimum effect size threshold.
4. client_specific flag — exact conditions for promoting from client_specific
   to global (cross-network threshold already defined: 10-15 instances,
   same vertical_tag)
5. Failure handling — what happens when a connector has insufficient history
   (e.g., brand only has 60 days of Gorgias data)
6. Output format — exactly what gets written to causal_pattern_validation
   and candidate_signals, and what gets reported to the founder at onboarding
   completion ("Your account has 23 validated causal patterns, 4 high
   confidence, 2 novel patterns discovered")
