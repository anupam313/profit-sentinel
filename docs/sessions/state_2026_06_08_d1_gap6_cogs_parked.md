# Profit Sentinel — STATE
## Session: 2026-06-08 (Gap 6 closeout → COGS PARKED, build pivots to C-series)
## Supersedes: state_2026_06_08_d1_gap6_residual_presale.md
## Status: Gap 6 PARKED behind COGS foundation (O-28). Build moves to C-series.

---

## ONE-LINE SUMMARY
Gap 6 did not lock. Of its remaining items: O-24a (new-vs-returning return split) RETIRED;
test-data-constant verification CLOSED-clean; O-24b + the all-explained actionability gate +
residual-band-cutoff brand-relativity all BLOCKED on a newly-elevated COGS foundation (O-28),
which is PARKED and discovery-blocked. Build pivots D-series → C-series.

---

## WHAT CLOSED / CHANGED THIS SESSION

1. **O-24a new-vs-returning return split — RETIRED.** Stage 2 (S17/S18 vs C3) already owns
   suppression/narration of the return-rate component after a known sale. The split produces no
   actionable lever (a founder cannot un-return items) and the prior-sale comparator is too
   context-sensitive at this tier (each sale differs on pricing depth, quality cohort, delivery
   delay, competitive context, design novelty). New-vs-returning composition, if ever surfaced,
   is a periodic-digest item → Horizon-2. NOT a suppression gate, NOT an alert.

2. **"Recently-connected brand = thin history" — RETIRED as reasoning.** Full Shopify order
   history is available on connection. Thin history is only a genuinely young-brand case, never a
   recently-connected case.

3. **Test-data-constant verification — CLOSED, verified clean.** grep + view across agent_d,
   technical_architecture, cross_alert, d1_validation_gates found no live test constants wired
   into suppression paths. The only matches were (a) the retired-S20 mechanic *description*
   (Month-15 / $3,950 / full-suppression — documented as removed) and (b) the O-26 audit log
   entry. Both are notes about removed/auditable items, not live paths.

4. **O-24b thin-baseline confidence — REFRAMED + BLOCKED.** It is not a clean-day-count problem;
   it is a cost-regime / versioned-COGS problem. Its honest resolution ("component-only mode until
   the cost-regime-consistent window supports a margin verdict") is *defined by* the COGS
   foundation. So O-24b cannot close until O-28 is worked.

5. **All-explained edge-case actionability gate + residual-band-cutoff brand-relativity —
   BLOCKED on O-28.** Both operate on the margin residual; neither can settle without the COGS
   decision.

6. **COGS elevated to its own foundational section = O-28, PARKED + DISCOVERY-BLOCKED.** It feeds
   every margin-bearing alert (D1/D2/D3…), not just D1, so it is not a Gap 6 child. See O-28 in
   cross_alert_orchestration.md for the full entry. NOT authored into technical_architecture.md —
   parked-open, not designed.

7. **Build sequence pivots: D-series PARKED → C-series NEXT.** Revenue-side alerts (post-return
   ROAS, ROAS-drop root cause, influencer ROI, sizing velocity) are COGS-independent and higher in
   Blueprint priority. They advance the critical path while O-28 awaits discovery.

---

## VERIFIED SHOPIFY DATA-LAYER FACTS (evidence-backed this session)
- Historical order **line items** freeze SKU string + title + price + quantity at sale time and
  **survive product/variant deletion**.
- The **link** to the live product/variant object — and the **cost field** behind it — is LOST on
  deletion. `cost per item` is current-only and not in the Order API; deleted-variant cost is
  unrecoverable.
- Therefore cross-source baselines (marketing/ROAS, returns, Klaviyo) join on
  **order/customer/date/channel** — all frozen — and **do NOT fall flat on deleted SKUs**. Only
  **per-SKU cost/margin** degrades, and Shopify cost was never our intended source.
- Net: the historical-margin gap is governed by the **founder's CSV completeness** (does their
  sheet still carry the SKU string), not by Shopify deletion — the SKU-string join survives
  deletion.

---

## O-28 COGS FOUNDATION — PROVISIONAL DIRECTION (NOT LOCKED)
Do NOT write any of this into technical_architecture.md until the dedicated COGS session.
- Versioned / season-regime cost model: `sku_cost_version` (sku_string, cost, regime_label,
  regime_start, regime_end, source_tier).
- Join on **SKU string**, not variant ID (survives deletion).
- Season/regime granularity accepted — founders think Spring/Fall, not exact dates; coarser than
  the underlying cost reality already, so honest.
- **Coverage disclosure mandatory** — % of historical revenue that is cost-covered.
- Uncostable orders run **component-only**, never imputed.
- **Multiple-file ingestion** (per season / per category) + a normalisation step for heterogeneous
  founder formats.
- **Prompt-the-founder fallback** for high-revenue unmatched SKUs (industry-standard, cf. BeProfit);
  low-revenue long tail left component-only, not chased.
- Detailed messy-ingestion-tolerance spec = its own dedicated session.

## THE HARD UNKNOWN (discovery-gated, the real blocker)
What fraction of ICP founders can actually supply usable historical versioned cost? NOT answerable
by analysis or search — needs founder conversations (Aman + next discovery interviews). De-risk
idea if discovery stays blocked: instrument onboarding to MEASURE the reconstruction rate on the
first real brands, so the product itself becomes the discovery instrument for this one variable.
Do NOT freeze the COGS schema on a guessed rate.

---

## GAP 6 STATUS (does NOT lock)
- CLOSED: Seam 2 (S17/S18 vs C3), C3 consistency, COGS/S21 component, operational-cost/S20,
  residual-pass Tier-1 locks (measured-not-explained, two-door fire, go-quiet ceiling, fulfilment
  retired, structural-break magnitude brand-relative, BAU pre-sale-ramp exclusion + backfill),
  O-24a (retired), test-data-constant check (clean).
- BLOCKED on O-28: O-24b thin-baseline confidence; all-explained actionability gate; residual-band
  cutoff brand-relativity.
- Tier-2 designs still HELD (in state_2026_06_08_d1_gap6_residual_presale.md): pre-sale-ramp
  detector; new-product cost-collection; materiality math. Fold in only when Gap 6 closes.
- Gap 6 reopens after O-28 (COGS foundation) is worked.

---

## NEXT SESSION STARTING POINT
New chat. Load: this file · save_protocol.md (11 checks) · agent_d_build_spec.md ·
technical_architecture.md · cross_alert_orchestration.md · product_strategy.md ·
d1_validation_gates.md · pre_agent_build_checklist.md · plus
chat_context_2026_06_08_d1_gap6_cogs_parked.md.

**FIRST:** run save_protocol Phase B sanity handles on load. Expected counts (wc -l basis):
agent_d=2710 · technical_architecture=3815 · cross_alert=774 · pre_agent=389 ·
product_strategy=1416 · d1_validation_gates=383 · save_protocol=149. (A uniform +1 = trailing
-newline convention, harmless. Non-uniform or any OLD count = real problem; re-read fresh, do not
edit, flag if it persists.)

**THEN:** begin **C-series** review (revenue-side, COGS-independent). Internal C-series structure
already designed (see cross_alert_orchestration.md ~line 204). Carry the logged C-series items:
C10/Alert-3 destination-fulfilment-cost reconciliation; O-6 D1 return-driver ↔ C-chain router
pattern; O-7 C-chain ↔ A1/A6 shared Loop cohorts.

**COGS (O-28):** reopen only when (a) some founder discovery has happened, or (b) revenue-side
work is exhausted and you choose to proceed on a stated assumption with eyes open. Detailed
messy-ingestion-tolerance spec is its own session.

**After C-series:** B → A → orchestration resolution pass → H → consolidated Claude Code prompt.
D-series (incl. D1 alert language) resumes only after O-28 unblocks the margin verdict.

**Post-Gap-6 (logged, do not pull forward):** O-26 full design-consistency audit + design-ownership
map (incl. O-25 orphaned `margin_floor_pct` removal + the three 2026-06-08 audit items: launch
-detector 5/7 count, structural-break 21-day duration, S38 85%/60% placeholders).

---

## SANITY HANDLES (this save — real post-edit counts)
- agent_d_build_spec.md = 2710 (Gap 6 row rewritten in place; net 0-line delta — single-row replace)
- cross_alert_orchestration.md = 774 (O-24 rewritten in place; O-28 row added; session-log entry
  +24; header changelog rewritten in place; +25 net from pre-edit 749)
- state_2026_06_08_d1_gap6_cogs_parked.md = THIS FILE (new)
- chat_context_2026_06_08_d1_gap6_cogs_parked.md = new
- Untouched: technical_architecture=3815 · product_strategy=1416 · pre_agent=389 ·
  d1_validation_gates=383 · save_protocol=149 · all locked seed/gap files.

## SAVE INTEGRITY FLAG
This save was **self-verified without founder content review** (founder cannot verify content). The
Phase-0 decision ledger with verbatim source quotes is persisted in the context file as the audit
trail. Next session should re-read that ledger against these files as the independent second reader.
