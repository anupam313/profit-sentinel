# Profit Sentinel — Chat Context v5
*Date: May 21 2026 | Session type: Customer discovery debrief + product decisions*
*Preceding context files: v1–v4 (same date)*

---

## Session Summary

This session covered the first founder discovery interview (Ministry of Supply, founder: Aman) and a series of product decisions triggered by what was learned. Two parallel outputs: discovery interview debrief documents and updates to product_strategy.md.

---

## Discovery Interview — Ministry of Supply

### Interview Facts
- Brand: Ministry of Supply (MOS) — 100% DTC, Shopify-native, US fashion brand
- Founder: Aman (connected via Rashi)
- Duration: ~35 min (incomplete — cut short at Section 3, Signal 1 due to all-hands)
- Interview score: 21/24 — Priority Beta Candidate
- Pending: Q8, Q9, Signals 2–5 (follow-up email sent)

### Key Validated Findings
- **24-hour detection lag** on a site-down revenue event — confirmed, not assumed
- **"Scattershot" diagnosis** — his own word, unprompted. Opens multiple tools manually.
- **Sidekick verdict:** "Only as smart as my next question" — ad hoc, doesn't solve any one thing
- **Signal 1 confirmed blind spot:** Post-return ROAS by channel — "can't see today" at described granularity
- **Returns pain:** Deep and unprompted. $43K serial offender, Klaviyo/ReturnGo disconnect, size bracketing, 3-tier policy (returnable/exchange-only/final sale)
- **Delivery surface:** Shopify app store unambiguously. Not Slack ("too crowded"). Checks 3–4 Shopify apps daily.
- **Attribution skepticism:** Won't trust ROAS without understanding methodology. Wants multi-touch as baseline. 15-day first-impression-to-purchase window stated.
- **Traffic quality scoring gap:** Independently articulated — no tool scores upper-funnel traffic for propensity to buy. Not in PS scope but noted.

### Stack Confirmed
Shopify, Triple Whale, Meta, Google Ads, GA4, ReturnGo (previously Loop Returns), Klaviyo, Helpdesk

### What Works Against PS (MOS Lens)
| Issue | Status |
|---|---|
| Attribution skepticism — trust bar is high | Addressed: attribution model + methodology shown at onboarding |
| Signals 2–5 unvalidated | Open: email follow-up |
| Q8 (build priority) and Q9 (one question) unanswered | Open: email follow-up — load-bearing |
| Shopify-native delivery preference | Strategic decision pending — monitor across interviews |
| One interview, possibly an outlier | Mitigated by further interviews |

### Documents Created This Session
1. `interview_01_ministry_of_supply.docx` — Filled debrief with scoring, section findings, signal validation table
2. `profit_sentinel_discovery_synthesis.docx` — Living cross-interview tracker (10 interviews, pre-structured)
3. `discovery_interview_questionnaire_v3.docx` — Updated questionnaire with all agreed changes

---

## Product Decisions Made This Session

### 1. Returns Intelligence — Expanded to Phase 1 Scope
Returns confirmed as a disproportionate profit lever in fashion. Beyond Alert 5 (sizing complaint velocity), the following are now in scope for Phase 1 build — all derivable from existing connectors (ReturnGo/Loop Returns + Shopify + Gorgias):

- Serial repeat offender detection (configurable threshold)
- Return rate by SKU
- Return rate by acquisition channel
- Return rate by influencer cohort
- Refund vs exchange rate
- Return lag by SKU (short lag = expectation mismatch; long lag = sizing issue)

Build priority within Phase 1 sequence: return rate by channel and SKU first (directly feed existing ROAS and margin alerts). Add to technical_architecture.md build sequence.

### 2. Attribution Model Flexibility — Onboarding Question Added
Full attribution model choice offered at onboarding. Six models plus custom weights:
- Last touch
- First touch
- Linear
- Time decay *(default — recommended for fashion)*
- Position-based (40/40/20)
- Linear clicks + deterministic views

Default if no selection: **time decay**.

Attribution window also configured at onboarding:
Options: 1 / 7 / 14 / 21 / 28 / custom days
Default: **14 days** *(working assumption — validate across remaining interviews)*

All ROAS alerts display the configured model label. Non-default choices labelled prominently in every alert header.

Rationale: Founders who don't trust the attribution methodology won't trust any alert built on top of it. Validated by MOS interview directly.

### 3. Google Ads — First-Class Phase 1 Connector
Added to Phase 1 connector list alongside Meta and TikTok. Rationale:
- Intent-driven channel (different customer profile from social)
- Already in MOS stack, used daily
- Channel ROAS comparison in Alert 1 is structurally incomplete without it
- Mature API, lowest incremental build cost
- Requires own synthetic seed data for testing — does not affect existing seeds

### 4. Shopify Notification Layer — Deferred to Post-Pilot
Agree/disagree/snooze feedback loop on alerts is a core intelligence mechanism. Deferred because Shopify's native notification API has limited interactivity. Needs proper design before build. Email alerts remain primary delivery in Phase 1.

Design requirement when built: agree/disagree/snooze must feed back into per-account alert threshold calibration. Disagreement signals identify noise; agreement + outcome data closes the feedback loop on recommendation accuracy.

### 5. Delivery Surface Decision — Open, Monitor
MOS: Shopify app store preferred, Slack explicitly rejected. One data point. Decision threshold: if 6+ of 10 interviews confirm same, Shopify-native delivery becomes a build requirement. Monitor in every subsequent interview.

### 6. Pre-Interview Screener — Removed
Adds friction before relationship established. Context questions (team size, agency dependency, analytics spend, DTC %) folded into warm-up conversation. Takes 2 minutes verbally, feels like rapport-building.

---

## Discovery Interview Questionnaire — v3 Changes

Changes from original questionnaire:
- Target duration: 45 min (was 30 min)
- Warm-up expanded: team size, agency dependency, analytics spend, DTC % surfaced conversationally
- Q3 reframed: "decision that cost you money or margin" (was open-ended)
- Scenario test: spoken setup + chat paste protocol (no longer read aloud in full)
- Section 3 signals: compressed to one sentence each
- Section 4 (new): Tool stack checklist — 9 categories, top 3–4 tools each, "none/manual" option
- Scoring: Slack-first signal replaced with delivery surface fit
- Referral close: warm and direct — explicitly asks for warm intro, no cold-name escape hatch
- GMV question: removed (available via public signals)

---

## Follow-Up Email Status
Draft sent to Aman. Covers:
- Signal validation (reordered: sizing → influencer ROI → margin → campaign ROAS → post-return ROAS by channel)
- Q8: priority signal ranking
- Q9: one piece of information
- Warm referral ask for 2 warm intros to other Shopify fashion founders

Key design decisions in email:
- ROAS signals placed last (not first) — Aman won't trust ROAS without attribution methodology context; building evidence before asking him to evaluate ROAS numbers
- No mention of free trial — too early; would shift him from advisor to potential customer mode
- No attribution methodology question — already known from interview; belongs in product build, not further discovery

---

## Files to Update
- `product_strategy.md` — Updated this session (v5). Replace in projects and local.
- `discovery_interview_questionnaire_v3.docx` — New file. Add to projects.
- `interview_01_ministry_of_supply.docx` — New file. Add to projects or keep local.
- `profit_sentinel_discovery_synthesis.docx` — New file. Add to projects.
- `technical_architecture.md` — Returns intelligence build priority and Google Ads seeding to be added in next technical session.

---

## Open Items Entering Next Session

| Item | Priority | Owner |
|---|---|---|
| Email reply from Aman (Q8, Q9, signals 2–5) | High | Wait |
| Google Ads synthetic seed data | High | Claude Code |
| Returns intelligence build sequence | High | Next technical session |
| Attribution window default validation | Medium | Subsequent interviews |
| Shopify delivery surface pattern | Medium | Subsequent interviews |
| technical_architecture.md update (Google Ads + returns) | Medium | Next technical session |
| Interviews 2–10 | High | Ongoing |
