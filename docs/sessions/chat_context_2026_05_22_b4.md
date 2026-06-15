# Profit Sentinel — Chat Context
## Date: 2026-05-22
## Session: B-4 Design + Architecture Decisions
## Type: Design session — Claude Code prompt ready, not yet executed

---

## KEY ARCHITECTURAL DECISIONS MADE THIS SESSION

### Decision 1 — SKU-to-Ad Mapping: content_ids (LOCKED)

Ad set naming convention inference: REJECTED.
- Ad set names are maintained by low-paid marketing coordinators
- Naming discipline degrades within weeks in real accounts
- Agency-managed accounts use agency naming conventions, not brand conventions
- Any solution requiring naming discipline will fail on majority of real clients

phash image matching: REJECTED for general use.
- Fails on lifestyle/editorial creatives (agency standard)
- 60–70% match rate on product-forward only; 30–40% on lifestyle
- Agencies specifically produce lifestyle — unreliable for agency accounts
- Works only for Shopping (trivially — product feed is the direct source)

**Chosen approach: content_ids from Meta/TikTok Purchase events**
- Meta Pixel `Purchase` event fires content_ids array = Shopify product IDs
- TikTok `CompletePayment` event carries content_id — same pattern
- Both readable via respective Reporting APIs at campaign level
- Zero founder input required. Zero naming dependency.
- Updates automatically as campaigns change.

Google: product_id from Shopping feed for Shopping/PMax eligible SKUs.
All other Google campaign types: no product signal available by design.

---

### Decision 2 — campaign_objective is load-bearing (LOCKED)

Campaign objective must be read from API for all three platforms before
any ROAS calculation is meaningful. Without objective context, ROAS numbers
are uninterpretable.

Meta API field: `objective`
Values: OUTCOME_SALES / OUTCOME_TRAFFIC / OUTCOME_AWARENESS / OUTCOME_ENGAGEMENT

TikTok API field: `objective_type`
Values: PRODUCT_SALES / TRAFFIC / REACH / VIDEO_VIEWS / LEAD_GENERATION

Google Ads: derived from campaign_type
SEARCH/SHOPPING/PMAX → SALES
VIDEO/DEMAND_GEN → AWARENESS_AND_CONSIDERATION

ROAS gating rule (applies to all three platforms):
- AWARENESS campaigns: ROAS = NULL (wrong metric for objective)
- All other objectives: ROAS calculable

---

### Decision 3 — View-through ROAS disclosure (LOCKED)

click_only_purchase_value seeded in Meta (structural field).
Shows view-through gap factually. No recommendation attached.
Shown to founder as data disclosure only:
"Meta-reported ROAS includes view-through attribution.
Click-only ROAS strips this. Both are shown for transparency."

Pause recommendation (if ever built) requires ALL THREE:
1. Pattern duration ≥ 11/14 days (not a single day event)
2. Layer 3: founder's own historical precedent (prior pause outcome from their data)
3. Financial stake quantified in £/$ terms

Never fire a pause recommendation on ROAS < 1.0 alone.
ROAS < 1.0 on a single day has too many confounders: inventory, seasonality,
competition, creative fatigue, day-of-week variance.

---

### Decision 4 — Dropped signals (LOCKED — do not reopen)

**ROAS < 1.0 pause recommendation: DROPPED**
Reason: Insufficient without inventory context, seasonality context,
competitive landscape, and historical baseline. Would damage founder trust.
If this signal is ever rebuilt, it requires multi-signal confirmation
(ROAS + spend trajectory + conversion rate + competitor signal) before firing.

**Upper-funnel CPM → organic lift: DROPPED**
Reason: Pre/post measurement without AB control is directional noise.
Seasonality, PR coverage, competitor stockouts, algorithm changes all confound it.
PS does not comment on awareness campaign lift via organic correlation.
If this is ever rebuilt, it requires: matched market design, holdout control,
minimum 4-week test window, and explicit statistical disclosure.

---

### Decision 5 — Correlation-not-causation qualifier (PENDING application)

Agreed as a principle: Agent D must never say "caused by" when the mechanism
is observational/correlational. Always "correlated with."

Current application: NONE — the two signals it was attached to were dropped.
Re-apply to any future cross-source correlation alert that lacks a
confirmed causal mechanism (i.e. the pathway from A to B is not mechanistic).

---

### Decision 6 — PS white space vs Triple Whale / Northbeam (LOCKED)

Triple Whale and Northbeam both do:
- Cross-channel ROAS aggregation
- Post-purchase attribution modelling

Neither does:
- Post-return ROAS (they pull Shopify revenue at order creation, returns never feed back)
- SKU-level return rate by campaign (no Loop Returns integration at SKU grain)
- Gorgias sizing complaint → return spike prediction
- Segment-level (Explorer/Loyalist) post-return ROAS by campaign

PS differentiators for A1 and B-series:
1. Return-adjusted ROAS at campaign level using Loop Returns
2. Which campaign's content_ids have the highest return rate this week vs last
3. "Campaign X is driving purchases of HERO DRESS XS which has a 34% return rate —
   vs 12% brand average. Pause or redirect creative." — not available anywhere else.

---

### Decision 7 — F2 Payment Gateway Alert scope (LOCKED)

PS value proposition for F2: NOT error detection (Sentry already does that,
developer gets PagerDuty). PS value = founder-facing revenue quantification.

Frame: "Payment gateway failures elevated for 3.2 hours this morning —
estimated 34 lost checkouts, £4,800 revenue impact. Resolved."

Segmentation to build:
- By gateway (Stripe vs Shop Pay vs PayPal) — different fix actions
- By device (mobile vs desktop) — mobile-only = Shop Pay Express issue
- By time of day — correlates with traffic source (TikTok peaks 7–10pm)
- Revenue impact quantified — not just error count

Sentry seed already has payment_gateway_timeout events. No new seeding needed for F2.

---

### Decision 8 — PMax SKU alert (LOCKED)

PMax withholds asset-level and ad group data by design.
PS can still identify eligible SKUs from Merchant Center feed.
Alert scope: if eligible SKUs in PMax feed have high return rate
→ alert founder to exclude from PMax feed.

Example: "PMax campaign includes HERO DRESS XS, HERO DRESS S in its product feed.
These SKUs have a 31% return rate this month vs 12% brand average.
Consider excluding them from the PMax feed until sizing issue is resolved."
Action: exclude from PMax feed in Google Merchant Center — 2-minute action.
Confidence cap: 0.65 (max_confidence_cap already seeded for PMax rows).

---

### Decision 9 — YouTube video completion as candidate signal (LOCKED)

Not a core alert at launch. Candidate signal in causal_pattern_validation.
Fields to seed in Google Ads VIDEO rows:
video_quartile_p25/p50/p75/p100_rate + video_view_rate + average_cpv

Poor-performing creative window: Month 8–9, p100_rate < 0.09
High-performing window: Month 3–4, p100_rate 0.16–0.18

Candidate signal framing:
"FW25 hero video completion rate below 25% on cold audiences —
creative is not holding attention past the first 5 seconds.
Consider testing a product-forward opening frame."

---

## B-4 CLAUDE CODE PROMPT — READY TO EXECUTE

### TASK: B-4 — SKU-to-Ad Attribution via content_ids + Cross-Source Chain Hardening

### CONTEXT
B-10 is complete. B-4 is now the highest priority.

The architectural decision for SKU-to-ad mapping is LOCKED:
- Primary method: content_ids from Meta and TikTok Purchase/CompletePayment events
- Google Shopping/PMax: product_id from Shopping feed (NULL for other campaign types)
- No ad set naming convention inference
- No phash image matching
- campaign_objective is the foundation — all ROAS calculations are objective-dependent
- ROAS < 1.0 pause recommendation: NOT implemented (dropped — see Decision 4)
- Upper-funnel organic lift correlation: NOT implemented (dropped — see Decision 4)

This session makes changes to FIVE seed scripts and ONE mart model.
Read every file before touching it.

---

### PRELIMINARY CHECKS — RUN BEFORE ANY CHANGES

Check 1: Read current Meta seed schema
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'client_azure_co'
  AND table_name = 'meta_ad_performance'
ORDER BY ordinal_position;

Check 2: Read current TikTok seed schema
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'client_azure_co'
  AND table_name = 'tiktok_ad_performance'
ORDER BY ordinal_position;

Check 3: Read current Google Ads seed schema
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'client_azure_co'
  AND table_name = 'google_ads_performance'
ORDER BY ordinal_position;

Check 4: Read current Gorgias seed schema
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'client_azure_co'
  AND table_name = 'gorgias_tickets'
ORDER BY ordinal_position;

Check 5: Confirm SKUs available for content_ids seeding
SELECT sku, shopify_variant_id
FROM client_azure_co.sku_cost_master
WHERE record_type = 'sku_cogs' AND effective_to IS NULL
ORDER BY landed_cost DESC
LIMIT 10;
→ Use top 5 by landed_cost as the HIGH-RETURN SKUs in the causal chain test

Check 6: Read current Loop Returns schema to confirm product_id field
SELECT column_name FROM information_schema.columns
WHERE table_schema = 'client_azure_co_staging'
  AND table_name = 'stg_loop_returns';

Report all check results before proceeding.

---

### FIX 1 — Meta Ads Seed: content_ids + campaign_objective + click_only_purchase_value

File: connectors/seed_meta_ads.py

New columns to add:

campaign_objective: VARCHAR
- Reflects Meta API `objective` field
- Values: OUTCOME_SALES / OUTCOME_TRAFFIC / OUTCOME_AWARENESS / OUTCOME_ENGAGEMENT
- Assignment by campaign type:
  Retargeting campaigns → OUTCOME_SALES
  Prospecting/lookalike campaigns → OUTCOME_SALES
  Brand/awareness campaigns → OUTCOME_AWARENESS
  Traffic campaigns → OUTCOME_TRAFFIC
- ROAS gating: OUTCOME_AWARENESS campaigns → ROAS = NULL (wrong metric)
- Seed must have at least 1 OUTCOME_AWARENESS campaign across the date range

attribution_type: VARCHAR
- Values: 'click_7d' / 'click_1d' / 'view_1d' / 'blended_7d_click_1d_view'
- Default for most rows: 'blended_7d_click_1d_view' (Meta default window)
- For retargeting campaigns: seed both 'click_7d' AND 'blended_7d_click_1d_view'
  rows on SAME date to demonstrate the gap

click_only_purchase_value: NUMERIC
- Revenue attributable to 7d_click only (strips view-through)
- For retargeting: 75–85% of total conversion_value (small gap — warm audience)
- For prospecting: 30–45% of total conversion_value (large gap — cold audience)
- For awareness: NULL (no conversion objective)
- Structural field only — no recommendation logic attached to this column
- Used by mart to show view-through gap factually as a data disclosure

content_ids: TEXT[] (PostgreSQL array)
- Array of Shopify product IDs purchased in conversions attributed to this campaign
- Population rules:
  OUTCOME_SALES campaigns with conversions: 1–4 product IDs per row
  Use top 5 SKUs by landed_cost from sku_cost_master as the pool
  Assign specific SKUs to specific campaigns consistently:
    Retargeting campaign 1: [HERO_DRESS_PRODUCT_ID, TROUSER_PRODUCT_ID]
    Prospecting campaign 1: [HERO_DRESS_PRODUCT_ID, JACKET_PRODUCT_ID]
  OUTCOME_AWARENESS campaigns: empty array []
  Rows with 0 conversions: empty array []
  Carousel/catalogue campaigns: 3–4 product IDs
  Single product campaigns: 1 product ID

CRITICAL REALISM REQUIREMENT:
Top 2 SKUs in prospecting campaign content_ids during BFCM window
(November 2024, Month 6) must match SKUs with elevated return rates
in stg_loop_returns for the same period.
Specifically: HERO_DRESS top variants must appear in:
1. Meta prospecting content_ids (Nov 2024)
2. Loop Returns with 34–38% return rate (Nov 2024)
3. Gorgias sizing_issue tickets (Oct 28 – Nov 14 2024, T-7 before return spike)
This creates the testable A1 causal chain.

---

### FIX 2 — TikTok Ads Seed: content_ids + campaign_objective

File: connectors/seed_tiktok.py

Read the full file first. Add these columns if not present:

campaign_objective: VARCHAR
- TikTok API field: `objective_type`
- Values: PRODUCT_SALES / TRAFFIC / REACH / VIDEO_VIEWS / LEAD_GENERATION
- Spark Ads (influencer): PRODUCT_SALES or VIDEO_VIEWS
- Paid media campaigns: PRODUCT_SALES
- ROAS gating: REACH / VIDEO_VIEWS → ROAS = NULL

content_ids: TEXT[]
- TikTok CompletePayment event aggregated to array at campaign level
- REALISM: 40% of TikTok rows have empty array []
  (UGC/organic Spark Ads where creator didn't tag product in TikTok Shop)
- For rows with content_ids: use same SKU pool as Meta
  (overlap intentional — same products promoted on both platforms)

attribution_window: VARCHAR
- Check if already exists. If not: add '1d_view_7d_click' for all TikTok rows

content_id_confidence: VARCHAR
- Values: 'high' / 'low' / 'none'
- high: TikTok Shop product tagged by creator — direct match
- low: inferred from campaign name or product catalogue — less reliable
- none: no content_id available (awareness/UGC campaigns)
- Distribution: high 35% / low 25% / none 40%

---

### FIX 3 — Google Ads Seed: product_id + campaign_objective + video metrics

File: connectors/seed_google_ads.py

READ THE FULL CURRENT FILE FIRST — heavily modified in previous session.
Do not overwrite any of the 9 columns added in the B-9 hardening session.

Add these columns:

campaign_objective: VARCHAR
- Map from campaign_type:
  SEARCH → 'SALES'
  SHOPPING → 'SALES'
  PERFORMANCE_MAX → 'SALES'
  VIDEO → 'AWARENESS_AND_CONSIDERATION'
  DEMAND_GEN → 'AWARENESS_AND_CONSIDERATION'

product_id: TEXT
- SHOPPING rows only: Shopify product_id matching sku_cost_master shopify_variant_id
  Use top 5 SKUs from sku_cost_master pool. One product_id per Shopping row.
- PERFORMANCE_MAX rows: NULL
  Append to existing diagnostic_block_reason:
  ' | PRODUCT_CONVERSION_ATTRIBUTION_WITHHELD: Google does not provide
  product-level conversion breakdown for PMax. Eligible SKUs from feed known —
  converted SKUs unknown by design.'
- SEARCH/VIDEO/DEMAND_GEN: NULL

reason_product_id_null: VARCHAR
- NULL for Shopping rows (product_id populated)
- PERFORMANCE_MAX: 'PMAX_PRODUCT_CONVERSION_WITHHELD: see diagnostic_block_reason'
- SEARCH/VIDEO/DEMAND_GEN: 'CAMPAIGN_TYPE_NO_PRODUCT_SIGNAL: Search/Video/DemandGen
  campaigns do not carry product-level attribution in Google Ads API.'

video_view_rate: NUMERIC (VIDEO rows only, NULL for all others)
- Range: 0.15–0.45

video_quartile_p25_rate: NUMERIC (VIDEO rows only)
video_quartile_p50_rate: NUMERIC (VIDEO rows only)
video_quartile_p75_rate: NUMERIC (VIDEO rows only)
video_quartile_p100_rate: NUMERIC (VIDEO rows only)
- Realistic fashion completion curve:
  p25: 0.45–0.65, p50: 0.28–0.42, p75: 0.18–0.28, p100: 0.10–0.18
- TWO scenarios:
  High-performing (Month 3–4): p100 = 0.16–0.18
  Poor-performing (Month 8–9): p100 = 0.06–0.08, p25 = 0.31
  (Poor-performing window triggers YouTube video completion candidate signal)

average_cpv: NUMERIC (VIDEO rows only, NULL for all others)
- Range: $0.02–$0.06

---

### FIX 4 — Gorgias Seed: product_id + order_id on complaint tickets

File: connectors/seed_gorgias.py

Read the full file first.

Add column: product_id TEXT
- sizing_issue tickets: 85% populated
- product_quality tickets: 70% populated
- return_intent tickets: 60% populated
- wismo / general enquiry: 5% populated
- All others: NULL
- Use HERO_DRESS product_id from sku_cost_master pool (same SKUs as content_ids)

Add column: order_id TEXT
- For tickets where product_id is populated: 70% also have order_id
  matching a real order_id from stg_shopify_orders for that customer
- Closes Gorgias → Shopify → Loop three-source chain

CRITICAL REALISM REQUIREMENT — CROSS-SOURCE CHAIN:
BFCM window (Oct 28 – Nov 14 2024, T-7 before Loop return spike):
- Seed Gorgias sizing_issue tickets for HERO_DRESS product_id
- Volume: 3× baseline (35–42% of tickets vs 14–18% baseline)
- customer_email on these tickets MUST match customer emails in Shopify
  orders for HERO_DRESS purchases in that period (84% match rate per XD1)

---

### FIX 5 — Loop Returns Seed: Confirm product_id + HERO_DRESS return spike

File: Read first to find correct filename and location.

Targeted change only — do NOT change overall return rate distribution.

In BFCM window (Nov 1–30 2024):
- Elevate HERO_DRESS SKU return rate to 34–38%
  (vs 18–22% brand average — clearly anomalous)
- return_reason: 'sizing' (keep existing dominant reason)
- customer_email values must match Gorgias sizing_issue ticket emails from Fix 4
  (closes three-source chain: Gorgias → Loop → same customer)

If product_id not currently on loop_returns rows: add it.
Same SKU pool — HERO_DRESS product_id for elevated return rows.

---

### FIX 6 — mart_causal_chain_daily: New column campaign_sku_return_rate_7d

File: warehouse/models/marts/mart_causal_chain_daily.sql

Add ONE new column:

campaign_sku_return_rate_7d: NUMERIC
Definition: weighted average return rate (trailing 7 days) of SKUs appearing
in content_ids across all active Meta + TikTok campaigns.

Logic:
1. Unnest content_ids arrays from meta_ad_performance and tiktok_ad_performance
   for the trailing 7 days
2. Join unnested product_ids to stg_loop_returns on product_id + return_date
   in trailing 7 days
3. Return rate = returns for these SKUs / orders for these SKUs in same window
4. Weight by campaign spend (higher spend → SKUs weighted more)
5. NULL if no content_ids available

SQL comment: 'SKU-weighted return rate for actively promoted products.
Elevated = high-return SKUs being actively spent against.
Primary signal for A1 (post-return ROAS) and B-series (ROAS drop root cause).
Requires content_ids populated in meta_ad_performance and tiktok_ad_performance.'

Add to schema.yml with NULL-allowed (no not_null test) and description of NULL condition.

---

### EXECUTION SEQUENCE

1. Run all 6 preliminary checks — report results
2. Execute Fix 1 (Meta seed) — drop/recreate table
3. Execute Fix 2 (TikTok seed) — drop/recreate table
4. Execute Fix 3 (Google Ads seed) — drop/recreate table
5. Execute Fix 4 (Gorgias seed) — drop/recreate table
6. Execute Fix 5 (Loop Returns seed) — targeted update only
7. Execute Fix 6 (dbt mart column)
8. dbt run --select mart_causal_chain_daily
9. dbt run && dbt test (full regression — all 65 tests must pass)
10. Run all 8 cross-source chain verification queries

---

### CROSS-SOURCE CHAIN VERIFICATION — MANDATORY

CHECK 1 — Three-source causal chain closes:
SELECT
  g.ticket_date, g.product_id as gorgias_product_id,
  g.customer_email, o.order_id,
  l.return_reason, l.return_date
FROM client_azure_co.gorgias_tickets g
JOIN client_azure_co_staging.stg_shopify_orders o
  ON g.customer_email = o.email
JOIN client_azure_co_staging.stg_loop_returns l
  ON o.order_id = l.order_id
WHERE g.ticket_category = 'sizing_issue'
  AND g.ticket_date BETWEEN '2024-11-01' AND '2024-11-30'
  AND g.product_id LIKE '%HERO%'
ORDER BY g.ticket_date LIMIT 10;
→ Must return rows

CHECK 2 — Meta content_ids + view-through gap visible:
SELECT m.date_day, m.campaign_name, m.campaign_objective,
  m.content_ids, m.conversion_value, m.click_only_purchase_value,
  ROUND(1 - (m.click_only_purchase_value / NULLIF(m.conversion_value,0)), 2)
    as view_through_pct
FROM client_azure_co.meta_ad_performance m
WHERE m.date_day BETWEEN '2024-11-01' AND '2024-11-30'
  AND m.campaign_objective = 'OUTCOME_SALES'
  AND array_length(m.content_ids, 1) > 0
ORDER BY m.date_day LIMIT 10;
→ Must return rows with content_ids and view_through_pct visible

CHECK 3 — HERO_DRESS return spike in BFCM:
SELECT DATE_TRUNC('week', l.return_date) as week,
  l.product_id, COUNT(*) as returns
FROM client_azure_co_staging.stg_loop_returns l
WHERE l.return_date BETWEEN '2024-10-01' AND '2024-12-31'
  AND l.product_id LIKE '%HERO%'
GROUP BY DATE_TRUNC('week', l.return_date), l.product_id
ORDER BY week;
→ BFCM weeks must show elevated returns vs pre/post BFCM

CHECK 4 — campaign_sku_return_rate_7d populated:
SELECT date, campaign_sku_return_rate_7d
FROM client_azure_co_marts.mart_causal_chain_daily
WHERE date BETWEEN '2024-11-01' AND '2024-11-30'
  AND campaign_sku_return_rate_7d IS NOT NULL
ORDER BY campaign_sku_return_rate_7d DESC LIMIT 5;
→ Must return rows with elevated rates in BFCM window

CHECK 5 — Google product_id coverage:
SELECT campaign_type, COUNT(*) as rows,
  COUNT(product_id) as has_product_id,
  COUNT(reason_product_id_null) as has_reason
FROM client_azure_co.google_ads_performance
GROUP BY campaign_type;
→ SHOPPING: has_product_id = total rows
→ All others: has_product_id = 0, has_reason = total rows

CHECK 6 — TikTok content_id_confidence distribution:
SELECT content_id_confidence,
  COUNT(*), ROUND(COUNT(*)*100.0/SUM(COUNT(*)) OVER(), 1) as pct
FROM client_azure_co.tiktok_ad_performance
GROUP BY content_id_confidence;
→ high ~35%, low ~25%, none ~40% (±5% tolerance)

CHECK 7 — YouTube poor creative window present:
SELECT date_day, video_quartile_p100_rate
FROM client_azure_co.google_ads_performance
WHERE campaign_type = 'VIDEO'
  AND video_quartile_p100_rate < 0.09
ORDER BY date_day LIMIT 5;
→ Must return rows (Month 8–9 poor-performing window)

CHECK 8 — Gorgias product_id coverage:
SELECT ticket_category, COUNT(*) as total,
  COUNT(product_id) as has_product_id,
  ROUND(COUNT(product_id)*100.0/COUNT(*), 1) as coverage_pct
FROM client_azure_co.gorgias_tickets
GROUP BY ticket_category;
→ sizing_issue ~85%, product_quality ~70%, wismo ~5%

---

### WHAT NOT TO CHANGE

- Do not implement ROAS < 1.0 pause recommendation logic anywhere
- Do not implement upper-funnel organic lift correlation logic anywhere
- Do not change overall Loop Returns return rate distribution
  (HERO_DRESS BFCM elevation is a targeted change only)
- Do not change Google Ads campaign_type values or campaign_id structure
- Do not change the 14-day zero-spend window (G_SHOP_001 Jul 15–28 2025)
- Do not change the 9 columns added in the B-9 Google Ads hardening session
- Do not add ROAS calculations for OUTCOME_AWARENESS or REACH/VIDEO_VIEWS campaigns
  (NULL is correct — wrong metric for objective)

---

### REPORT FORMAT

"B-4 complete. SKU-to-ad attribution via content_ids implemented.

Seed changes:
- Meta: [X] rows updated, content_ids on [X] rows,
  objectives: OUTCOME_SALES [X]% / OUTCOME_AWARENESS [X]%
- TikTok: content_ids on [X]% rows, content_id_confidence none [X]%
- Google Ads: product_id on [X] Shopping rows, reason codes on [X] other rows,
  video metrics on [X] VIDEO rows
- Gorgias: product_id on [X] tickets, order_id on [X] tickets
- Loop Returns: HERO_DRESS BFCM return rate: [X]% vs brand avg [X]%

Cross-source chain checks:
- CHECK 1 (3-source chain): [rows returned]
- CHECK 2 (Meta content_ids): [rows returned]
- CHECK 3 (HERO_DRESS return spike): [confirmed/not confirmed]
- CHECK 4 (mart campaign_sku_return_rate_7d): [max value BFCM]
- CHECK 5 (Google product_id): [PASS/FAIL]
- CHECK 6 (TikTok confidence): [actual %s]
- CHECK 7 (YouTube poor creative): [rows present]
- CHECK 8 (Gorgias coverage): [sizing_issue %]

dbt: PASS=[X] WARN=[X] ERROR=0
Ready for B-5."

---

## WHAT IS NOT IN SCOPE FOR B-4

The following were discussed and explicitly dropped:
1. ROAS < 1.0 pause recommendation
2. Upper-funnel CPM → organic lift correlation
3. Merchant Center API integration (Phase 1.5 — not blocking)
4. Attribution window mismatch alert (B-12 — not blocking Agent B)

These are closed decisions. Do not reopen without new evidence.
