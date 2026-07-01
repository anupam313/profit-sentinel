# Profit Sentinel — Pilot Scope
## Date: 2026-06-13  ·  Status: authoritative for the PILOT (content only)

> **Precedence:** where this document conflicts with the canonical specs (product_strategy,
> technical_architecture, agent_d_build_spec, cross_alert_orchestration, d1_validation_gates,
> pre_agent_build_checklist), THIS wins for the pilot. Canonical reconciliation is scheduled
> for next session under the full save protocol.
>
> **OPEN — not settled:** how the pilot docs/files are *organized* is explicitly unresolved
> (OP-PILOT-1) and is the first discussion of the next chat. This file holds CONTENT, not structure.
>
> **PROVISIONAL:** the alert disposition (§4) and "returns intelligence as identity" (§5) are
> actively being shaped — do not treat as locked.

---

## 1. What the pilot is (CONFIRMED)
The full product, automated end-to-end: same connectors, detection, system-generated reasoning,
checks/gates, Evidence Stack, and alert language; delivered through the real surface (Shopify app +
NLQ + email). Two — and only two — differences from full-scale PS:
1. **Limited alert set** (the dense cross-source core), not the full 58-alert library / deep causal graph.
2. **One human relevance-gate.** The system fires an alert TO Anupam automatically; he checks whether the
   system's reasoning fits that specific brand; then releases it to the founder. He computes and
   orchestrates nothing by hand — he is a relevance/release check on automated output.

Timeline: **6 weeks to LAUNCH the beta**; the free pilot then runs **3–4+ months** on real brand data.
The 6 weeks is the whole product (connectors, surface, alerts, gate flow), not just the causal graph.

## 2. The human gate = a correctness LOG (CONFIRMED)
- Every alert that reaches the gate is logged with TWO columns: **(a) my-verdict vs system** (did the
  system's reasoning hold for this brand) and **(b) founder-outcome vs system** (did the founder act, was
  the system right). Column (b) is what later licenses removing the gate per alert (graduation — threshold OPEN).
- Three exits: **send / reject-as-wrong / suppress-as-stale.** A stale alert (problem already resolved) is
  suppressed and logged, never sent late.
- Max **1-day** latency to clear the gate; **intraday FAST-LANE** for time-sensitive alerts (G1). State the
  latency promise to founders per alert class, not as a flat number.
- NLQ is **answer-or-abstain** (never guesses); it is a pilot-launch surface (the founder's day-one visibility).

## 3. The value-vs-moat filter (CONFIRMED — how alerts are judged)
- **Value** = is the founder getting this today? Proactive alerting (dashboards display, they don't alert),
  inference the founder skips (e.g., overstock from inventory + sell-through), and cross-source causal DEPTH
  (is-it-abnormal / precedent / which-cohort / why) all add value — even on single-source metrics.
- **Moat** = can Shopify or a cheap app copy it? Cross-source joins the founder can't do are defensible;
  single-source + threshold is not. The deep "why" that makes a single-source metric defensible is itself
  usually cross-source.
- **Differentiation is conditional on EXECUTION DEPTH.** A shallow threshold ping is commodity; the product is
  the cross-source causal answer (explanation, not detection). Build to that bar or the alert is replaceable.

## 4. Alert disposition (PROVISIONAL)

### PILOT — build now, in the 6-week beta (the defensible core)
**Fired (pushed through the relevance gate):**
- **Return-driver (HERO)** — "Campaign/collection X funds product P, which returns at 2× your average; 70%
  'too small' — fix the size guide or rein in spend." Shopify return rate + reason × product-level spend
  (Meta product_id / Google shopping_performance_view). No revenue attribution; routes around lossy data. [J-2 plumbing status, bd46884: reason is derived native-PRIMARY / Loop-supplement; the Shopify-native leg is scaffolded but INERT until first live connect (J-1) — pre-pilot the mart resolves 100% to Loop, so HERO demos on Loop-carrying brands today and gains the native reason at connect. Consistent with §6's locked "Shopify native Returns API is primary" note.]
- **C1 — sizing-complaint velocity** — leading indicator (Gorgias × Shopify/Loop); validated retrospectively
  from a brand's HISTORICAL Gorgias data (did past complaint spikes precede return spikes?). Fires if history
  supports it; else stays quiet for that brand. The only "warns before it happens" alert.
- **C6 — high-return new collection** — return rate on a new drop exceeds the brand's own average early
  (within ~14 days). Fashion-specific; vs store average, no full clustering needed.
- **G1 — stockout during active spend** — Shopify inventory × active ad spend. Scoped to single-product-
  destination ads (catalog ads self-suppress OOS; static single-product is the real value). Time-sensitive →
  fast-lane. Needs the Day-N spend / Day-N+1 inventory timing-tolerance fix.
- **C2 — influencer ROI after returns** — opportunistic (fires only if the brand runs influencer); near-free
  on the returns spine.

**In-app metrics / lists (pulled via app + NLQ, NOT fired):**
- **Blended post-return ROAS** (total revenue − returns ÷ total spend) — the headline "returns reality on your
  own numbers" hook. Label ad-spend blended, not MER.
- **Serial-offenders list** — quantified repeat-returner cost (a standing state, not an event).
- **Return-rate + reason table** — the returns ground-truth view.

### PHASE 2 — build DURING the pilot on real data, then promote
A1/A6 (return-adjusted ROAS/revenue by cohort; measure per-brand attribution loss), C4 (return-initiation spike,
matures with real returns), C7 (repeat-customer return rate, needs real cohorts + cross-source why), D1 (margin —
COGS-gated; learn which brands give trustworthy cost; ship Tier-0 component version, full when COGS clears),
E2/E3 (repeat-purchase decline / high-LTV quiet — only the DEEP cross-source version), F1/F5 (conversion — if a
brand has clean GA4), G4 (back-in-stock window — when waitlist data flows). *Why Phase 2:* each needs real data
to build the abnormality baselines and cross-source causal depth (synthetic can't), or to learn a dependency.
Building them here also resolves parked questions (e.g., OP-1 grouping on real returns).

### PARK — roadmap, not pilot/early (low-moat breadth or dependency-gated)
B1–B5 (creative/campaign — all Meta-dashboard commodity), D2 (discount creep), D5 (Klaviyo flow revenue),
E1/E4 (Klaviyo-visible), A2 (collapses into return-driver), A3 (lossy channel reversal), A5 (CAC>LTV — Phase-2
only if return-adjusted), A7 (one-time onboarding DQ check, not recurring), D3/D4 (COGS/fulfilment-feed gated),
G3 (COGS-gated), F2/F4 (conditional on the brand having any error-monitoring source), G2 (overstock — useful but
all-Shopify/low-moat; the cheapest single non-returns add if ever wanted). *Why park:* valuable to some founders
but replicable, or gated on a dependency most of the ICP lacks. Never let them dilute the returns-moat message.

### INTERNAL — plumbing, never founder-facing alerts (some pilot-essential)
A4/C5/F3 (diagnostics — surface inside the Evidence Stack, not standalone). **D6 (seasonal baseline) — essential
pilot plumbing**, stops returns alerts false-firing on seasonality; keep. H-series (data quality / system health):
keep the pilot subset **H1, H3, H11, H12, H15, H16, H19**; the rest accrue later. These keep the product honest;
they are not "product alerts."

## 5. Identity question (OPEN — posed, not confirmed)
Is PS, durably, a **returns/profit-leak intelligence product** (a focused, defensible moat with helpful breadth
around it), rather than the broad 58-signal platform the library implies? The filter says the moat concentrates
in cross-source returns; margin/conversion/retention are genuine-but-later expansion gated on COGS/Sentry/depth.
Anupam to decide deliberately — this shapes the whole product journey.

## 6. Data access reality (LOCKED — from Points 1 & 2)
- **Shopify:** full history via read_all_orders + PCD (developer-side, one-time); custom distribution app;
  CSV fallback only. PII/PCD on the critical path. Start approvals now.
- **Meta/TikTok:** Airbyte Cloud OAuth (no own Meta/TikTok app at pilot scale); Meta lost 7d/28d-view on Jan 12 2026;
  product_id via Airbyte Custom Insight (config); v5.2.7+; build on current Advantage+ structures.
- **Google Ads:** developer token = the real long pole (own credentials; entity helps) — start now;
  product-level via shopping_performance_view.
- **Klaviyo:** self-serve key, daily sync, every brand.
- **Loop Returns:** plan-gated → opportunistic; Shopify native Returns API is primary (carries reasons).
- **Gorgias:** the brand's own data; connect day one (needed for C1; fetch HISTORICAL data for retrospective validation).
- **Sentry:** opportunistic only; developer-skewed, not ubiquitous at this tier; never force-install (PII).
- **Validation:** no paid test — mechanism doc-confirmed; measure per-brand coverage by read-only inspection of a
  connected account.

## 7. Company status (LOCKED)
No entity required for the Shopify pilot (individual path). Register a simple Indian entity in PARALLEL for the
Google Ads token, DPA credibility with VC-backed brands, and liability shielding. Run both tracks; don't sequence.

## 8. The binding constraint (not a decision — the top risk)
No committed design partners yet; Aman is cold. Recruiting 4–5 brands willing to connect live data for months is
slower than any build step and gates the timeline. Solve recruitment before/alongside the build.
