# Profit Sentinel — Chat Context
## Date: 2026-05-20 (Session 2)
## Topic: historical_pattern_scan.py Design — Q4, Q5, Q6

---

## Q4 — `client_specific` Flag Promotion Rules

### Key reasoning

**Scope clarification:** Q4 applies to novel chains only. The 56 hardcoded chains in `causal_pattern_validation` are never subject to promotion logic — this was an implicit assumption made explicit during discussion.

**Track 1 deferral:** The 3-client cross-client convergence threshold is arbitrary at this stage. Agreed to defer Track 1 global promotion to post-10-client milestone. Logged as DEBT-T1 / D-19. Between now and 10 clients, novel chains can only reach core behaviour via Track 2 (single-client depth, `practitioner_approved`). No novel chain fires globally before 10 clients — this is the right call.

**`client_specific` flip timing:** Agreed that `client_specific = false` is set only after re-scan confirms the chain across all 3+ client histories — not at practitioner approval. Practitioner approval authorises the re-scan. Re-scan writes the final result. This prevents a practitioner approval from silently activating a chain that re-scan then fails to confirm.

**Monthly auto-check:** After each monthly incremental scan, a post-sweep check runs across all `candidate_signals` where `promotion_status = 'candidate'` and `client_specific = true`. Any pair where `cross_client_instance_count ≥ 3` AND `calendar_clustered = false` → `promotion_status = 'validated'` → practitioner review queue. Review volume to be monitored as client count grows — threshold re-evaluated at 10+ clients.

**Pair matching:** Exact string match on `leading_signal_column` + `outcome_column`. No alias resolution. Mart column names must be standardised before writing to `candidate_signals`. Simpler and audit-clean.

**Vertical scope:** Novel chains are vertical-specific in both Track 1 and Track 2. A chain validated for contemporary_womenswear does not apply to swimwear. Each vertical builds its own confidence trajectory independently.

**Multi-vertical clients:** Clients operating across multiple verticals (e.g. brand that sells womenswear and swimwear) get separate `causal_pattern_validation` rows per `vertical_tag`. Historical scan runs per vertical. Correct SKU-to-vertical mapping in `sku_cost_master` is a hard dependency (CD-4).

---

## Q5 — Failure Handling: Insufficient History

### 5A — Novel vs hardcoded code paths

Founder asked for explicit confirmation: novel chain discovery and hardcoded chain validation are completely separate code paths with no merging at any stage. Novel sweep writes only to `candidate_signals`. Hardcoded validation writes only to `causal_pattern_validation`. After Track 1 promotion, a novel chain gets hardcoded into the chain list and a new row written to `causal_pattern_validation` — at that point it is indistinguishable from the original 56 in operation. Separation is only during discovery and validation phase.

### 5B — Gorgias tagging quality

**Founder's hypothesis confirmed by research:** Gorgias tagging is structurally unreliable at the $2M–$10M fashion brand tier. Root cause is not AI quality — it is the flat data model. Gorgias only supports a single tag dimension per ticket out-of-the-box. A "return" ticket cannot simultaneously carry a sizing reason without compound tags like `return-sizing`. Most brands at this GMV tier have 1–3 support agents with no formal tagging governance.

**Key finding from research:** The AI auto-tagging is keyword/rule-based, not semantic. Accuracy is only as good as the precision of defined keywords and intents. Returns tagged as "complaint" and sizing issues tagged as "general" is the norm, not the exception for brands without a dedicated CX team.

**Scope expanded:** Founder correctly pushed back on Gorgias-only framing. All sources receive DQ pre-checks at onboarding scan. Gorgias is the most complex. Per-source checks:

| Source | Key DQ check | Skip threshold |
|--------|-------------|---------------|
| Gorgias | Tag coverage rate, vocabulary size, compound tag presence, return/sizing tag rate vs Loop return rate, agent tagging variance | Tag coverage <50% → skip C1 chains |
| Meta | % spend unmatched to Shopify order | >30% → low DQ, scan proceeds with caveat |
| TikTok | Creator-to-SKU mapping coverage | <70% → low DQ |
| Loop Returns | Reason code coverage | >40% null or "Other" → low DQ |
| Klaviyo | Active post-purchase flow | None → D5/E4 chains skipped |
| GA4 | Checkout funnel step completeness | Missing steps → F1/F5 skipped |
| Sentry | Coverage window days | <30 days → insufficient_history |

**NLP classifier decision:** Founder asked whether an NLP classifier on Gorgias ticket bodies would solve the tagging problem. Pushback accepted: this is not a lightweight addition. Fashion-specific vocabulary ("runs small", "boxy fit", "fabric too sheer"), multi-issue tickets, multilingual text, short ambiguous messages, and sarcasm all make it a full NLP pipeline with ongoing maintenance. Estimate: 2–3 weeks build, not a side addition.

**Decision: discovery-gated.** Build only after customer discovery confirms (a) founders trust that sizing complaints predict return spikes AND (b) Gorgias tagging is unreliable across 3+ beta clients. If built: covers all return reasons (sizing/fit, quality/defect, wrong item, changed mind, price, damaged in transit, description mismatch) — not sizing only. Logged as D-22.

### 5C — Missing connector handling

`scan_skipped_reason` gets a dedicated `text` column on `causal_pattern_validation` — not stored in `threshold_at_scan_time` jsonb. Reason: operational queries ("show me all clients missing TikTok") are painful against jsonb. One column, worth the schema addition.

**Late connector addition (e.g. Gorgias added 4 months post-onboarding):** Monthly incremental scan auto-detects when a previously-missing connector is now present and re-runs skipped chains. Internal notification only — not founder-facing.

**Pending connectors collected at onboarding:** New question added at end of existing 5-question confirmation flow: "Are you planning to add any sources in the next 90 days?" — yes/no with free-text for which sources. Writes to `client_config.pending_connectors` (text[]). Non-intrusive, single question, zero operational overhead at scale. Logged as D-20.

---

## Q6 — Output Format

### Onboarding completion message design

**Founding principle established:** The founder does not care about chains, tiers, or signals. He cares about three things at onboarding end: (1) what we already know about his business from history, (2) what we're watching for now, (3) what he should look at today if anything is already active.

**$ leakage as anchor vs forward promise as anchor:** Discussion established that $ leakage should be a bonus, not the anchor. The anchor is the forward promise. If $ is strong, lead with it. If weak, omit it and go straight to forward promise — no apology, no mention of what wasn't found.

**$ display threshold:** ≥1% of derived annual GMV AND ≥2 distinct patterns. Below threshold: suppress entirely. Why 1% GMV: meaningful enough to create urgency, realistic enough to find in almost every brand's 12-month history. Below 1%, the number feels small relative to the business and may undermine rather than build confidence.

**GMV derivation:** From Shopify total order revenue in scan window — not founder-stated. More accurate and one less question. Written to `client_config.gmv_derived_annual`. Logged as D-21.

**Headline lookback rule:** Founder challenged the "shallowest source" rule — correctly. A brand with 5 years of Shopify but only 1 year of Gorgias (recently switched from another tool) should not see "1 month" as the headline. Resolution: use deepest single-source (Shopify/Klaviyo anchor). Per-source limitations handled silently in the scan. Short-history connectors produce lower instance counts, not a shorter headline.

**NLQ in onboarding message:** Initially pushed back on including NLQ reference — said it wasn't built yet. Founder corrected: NLQ is a pilot launch requirement per product_strategy.md Section 3B, not post-beta. Confirmed: Agent D handles formatting, NLQ reuses same layer, built as parallel workstream to Agent D (Step 13). "Why did my ROAS drop?" example is accurate at pilot — Agent B handles causal reasoning.

**Causal questions without a chain:** For causal questions where Agent B has no matching chain, response is: "I can see X happened but I don't yet have enough data to identify the cause — I'm tracking it." This is not a failure state — it's honest and still more useful than any dashboard. Set this expectation in onboarding message.

**Agree/Snooze/Disagree framing:** Founder insisted on including the tap rationale in the onboarding message — framed as personalisation mechanism, not just feedback. The more the founder responds, the sharper and more personalised the alerts become. This is the right framing — it sets the expectation that the system learns from founder behaviour, which is the Moat 3 (Founder Decision DNA) mechanism.

**"N signals" removed:** Founder correctly pushed back on mentioning signal count in the message — business user doesn't care. Language rewritten in business terms: "profit guard", "one objective: protect and grow your margin", "only reach out when something genuinely threatens your profitability".

**Final two message variants documented in product_strategy.md Section 5.** Key difference: leakage section present/absent. Everything from the forward promise onward is identical in both variants.

---

## Broader decisions made during Q6 discussion

**Gorgias is used for Alert 5 only (C1 — sizing complaint velocity).** All other Gorgias usage is DQ pre-checks and tagging quality monitoring. This was confirmed, not expanded.

**NLQ cannot answer causal questions for chains not in the 56 at beta.** Gaps identified: Klaviyo deliverability (spam folder placement), GA4 mobile conversion issues (device data absent in synthetic), TikTok creative fatigue at ad-creative level (current chains at ad set level), AOV drop from product mix shift (not discount-driven), new customer acquisition slowing from organic decay. For all of these at beta: Agent B finds no matching chain → "unexplained signal — monitoring" → `candidate_signals`. Set founder expectation in onboarding message.

**ICP self-selects for signal density.** Founder pushed back on adding "active Meta ads for 12+ months" as a hard ICP gate — doesn't want to reduce pilot market. Agreed: a $5M–$10M brand without Meta ads and 12+ months of history is an outlier, not a segment. No hard gate needed. The ICP self-selects. Current ICP definition in product_strategy.md stands.

---

## Files updated this session

| File | Location |
|------|----------|
| `technical_architecture.md` | Replace in project knowledge |
| `product_strategy.md` | Replace in project knowledge |
| `pre_agent_build_checklist.md` | Replace in project knowledge |
| `state_2026_05_20_v2.md` | Add to project knowledge |
| `chat_context_2026_05_20_v2.md` | Add to project knowledge (this file) |
