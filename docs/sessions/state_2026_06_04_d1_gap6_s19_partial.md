# Profit Sentinel — STATE
## Session: D1 Gap 6 — discount-depth/S19 component PARTIAL CLOSE
## Date: 2026-06-04

---

## WHAT CLOSED THIS SESSION (discount-depth/S19 — PARTIAL)

S19 eases the margin alert during a markdown (sale) window. Core tension confirmed:
discounting is the one margin driver the founder *sets themselves*, so an alert that says
"your discounting got deeper" reports a deliberate decision back to them.

**SETTLED (self-contained calls):**
1. **No standalone "discount is deep" alert.** Discount is a margin CONTRIBUTOR only. The
   "is the sale too deep" question is a NON-ITEM (deleted, not deferred) — flagging a
   deliberate founder decision gives the founder nothing.
2. **Dollar figure feed-only; depth-terms for everyone else.** The dollar margin impact of
   discounting needs trustworthy cost (same as the COGS driver). Discount *depth* is
   computed from order data and needs no cost, so non-feed brands get a DIRECTIONAL,
   UNSIZED contribution ("discounting deepened by N points → margin down"). *(Corrects an
   earlier over-claim that the contribution needed cost — only the dollar magnitude does.)*
3. **Source decomposition rides a REAL trigger.** When D1 fires (Trigger A/B) and
   discounting leads, decompose the effective discount by source (code/automatic/shipping,
   all data-derived; Shopify exposes each discount's type). No founder code-tagging; no
   "deeper than intended/history" judgment (no defensible baseline). The decomposition is
   the value; it rides the margin trigger, never a discount threshold.
4. **Planned sales suppressed via the shared known-events suppression**, not a
   discount-specific window (retires week-1-2/weeks-3-4/>5pp/0.20-default — all hardcoded).
   Unconfirmed/panic markdowns NARRATED-with-context, never silently suppressed.

**DEFERRED to the final cross-component residual pass (O-24):**
- New-vs-existing customer split for a suppressed sale's downstream returns (the
  new-customer return confound). NOT a sale-to-sale comparison (rejected) and NOT a
  demand-weighted-discount heuristic (rejected at this tier: 4–8 sales/yr too few; mix
  drives returns more than depth; circular for slow-creep). Caveat: both customer types'
  return rates rise during a sale, so the split tells you *who*, not whether abnormal.
- Thin-baseline confidence handling (few clean non-sale days → fire with limited-history
  caveat at lower confidence, not silent / not full confidence).

**Return-lag reality:** sale-window returns are a TRAILING read → not in the acute alert.

---

## CORRECTIONS LOGGED (own them, carry forward)
- Discount contribution does NOT need cost — only the dollar magnitude does (depth is
  costless and usable directionally). Earlier framing was inconsistent with the COGS
  no-verdict posture; corrected.
- Return-to-replacement size link is BUILDABLE via the live Loop API (returns carry the
  exchange order / replacement variant) — earlier "drop it as fuzzy" was a SEED limitation
  mistaken for a data limitation; reinstated.
- Gorgias parser difficulty was OVERSTATED by smuggling in the complaint→return conversion
  timeline; comprehension is off-the-shelf, taxonomy fit is a small deliberate build.
- "the floor" was used loosely — D1 fires on relative Trigger A/B, not an absolute floor;
  `margin_floor_pct` is an orphaned pre-Gap-2 relic (now flagged O-25).

---

## PARALLEL ITEMS SPECCED (NOT Gap 6)
- **Gorgias NLP parser — NEAR-TERM CORE INFRA** (feeds sizing velocity, return-reason,
  retrospective review, sale channel). Tags unreliable at this tier and worst in sales →
  parse customer text, not tags. Brand-specific label schema + multi-intent rule +
  customer-text-only + low-signal reporting. Train taxonomy on ≥1yr (recent-weighted);
  live small-sample velocity handled by a firing floor + honest silence, not history.
  OUTPUT = faithful summary + link, NO recommended action. Per-brand accuracy GATE before
  pilot (D1-G12). Complaint→return conversion = slow/data-earned, parked.
- **Sale-period informational channel + delivery-label ingestion — Horizon-2 / probationary.**
  Delivered-cohort complaint pulse (+ in-transit share), NOT a return-rate readout. Hard
  rule: never show a number the founder's dashboards already show. Representativeness gate
  (delivered cohort must look like the whole sale, not its fast front edge). Mix-risk:
  history-assisted for established product, live-only for new collections.
- **Returns ingestion architecture:** new Shopify Returns API PRIMARY (works with/without
  Loop, post-~Apr-2026 migration), Loop API as ENRICHMENT. Returns-object (RMA) ≠
  refunds-object (money). Join on order ID + Shopify numeric customer ID (pseudonymous,
  not PII); NEVER email. Shopify is NOT replacing Loop (Loop is the management layer on
  Shopify's rails) but native returns are maturing — Loop-vs-native ICP split is a
  discovery item.

---

## FILES UPDATED THIS SESSION (applied; replace in project)
- **agent_d_build_spec.md** — discount-depth/S19 PARTIAL subsection; Gap 6 header + status
  paragraph; NINE GAPS Gap 6 row; header stamp.
- **cross_alert_orchestration.md** — O-14 Gap-6 half (S19 PARTIAL); O-24 extended (two
  deferred S19 items); O-25 (margin_floor_pct), O-26 (full audit + ownership map,
  logged-not-folded, post-Gap-6), O-27 (action-layer posture) added; changelog.
- **technical_architecture.md** — header stamp; margin_floor_pct flagged orphaned;
  2026-06-04 appendix (per-item discount staging; returns ingestion; Loop returns/exchange
  staging + return-to-replacement link + two exchange paths; Gorgias NLP parser; sale
  channel + delivery-label ingestion).
- **pre_agent_build_checklist.md** — rows D-GAP6-16…D-GAP6-23; header stamp.
- **product_strategy.md** — Section 12 closed-position note (parser core infra + action
  posture); Loop-vs-native discovery item; Section 12 + header stamps.
- **d1_validation_gates.md** — GATE D1-G12 (parser per-brand accuracy); discount-component
  gates deferred note; header stamp.

## FILES ADDED THIS SESSION
- **save_protocol.md** — the nine-check, two-phase save procedure (invariant).
- **state_2026_06_04_d1_gap6_s19_partial.md** — this file.
- **chat_context_2026_06_04_d1_gap6_s19_partial.md** — reasoning log.

**NOT edited (intentional):** seed_decisions_gap_f_g.md (S-rule defs — parked for the
orchestration pass); causal_graph.py (code batched post-H).

---

## SANITY HANDLES (post-edit line counts — next session's tripwire)
- agent_d_build_spec.md = **2635** (was 2547)
- technical_architecture.md = **3790** (was 3677)
- cross_alert_orchestration.md = **723** (was 705)
- d1_validation_gates.md = **350** (was 318)
- pre_agent_build_checklist.md = **385** (was 377)
- product_strategy.md = **1415** (was 1411)
- save_protocol.md = **84** (new)
If any updated file shows its OLD count, the wrong/older copy is mounted → STOP.

---

## D1 GAP STATUS
| Gap | Status |
|-----|--------|
| Gap 1 — COGS tier disclosure | LOCKED ✓ (component-only tightening FLAGGED, not confirmed) |
| Gap 2 — Threshold (Trigger A + B) | LOCKED ✓ |
| Gap 3 — Causal decomposition | LOCKED ✓ |
| Gap 4 — CPM → margin intermediate steps | DESIGN-COMPLETE ✓ (blocked on schema gate) |
| Gap 5 — AOV decline retired as a driver | LOCKED ✓ |
| Gap 6 — Seasonality suppression | **WIP** — dependencies + return-rate (Seam 2 + C3) + COGS/S21 CLOSED; **discount-depth/S19 PARTIAL 2026-06-04**; operational-cost/S20 untouched; final residual pass owed |
| Gap 7 — "Entirely explained" framing retired | PENDING |
| Gap 8 — No action named per driver | PENDING |
| Gap 9 — No $ revenue impact (display) | PENDING |

---

## STILL OPEN IN GAP 6 (before Gap 6 closes)
1. **operational-cost / S20** component — UNTOUCHED. Do NOT assume clean. NEXT.
2. **Final cross-component residual-disclosure pass** — confirm all five suppressed
   components feed `total_measured_impact` / the residual gate identically; absorbs the two
   deferred S19 items (O-24).

---

## NEXT SESSION STARTING POINT
New chat. Load: this file · save_protocol.md · agent_d_build_spec.md ·
cross_alert_orchestration.md · product_strategy.md · technical_architecture.md ·
d1_validation_gates.md · pre_agent_build_checklist.md · plus
chat_context_2026_06_04_d1_gap6_s19_partial.md.

**FIRST:** run save_protocol Phase B sanity handles on load (counts above).
**THEN:** the still-FLAGGED Gap 1 proposal (component-only vs driver-only) remains
undecided — gate D1-G9 depends on it.
**THEN:** resume Gap 6 at **operational-cost/S20** (verify against source; do NOT assume
clean), then the final cross-component residual pass.

After Gap 6: 7 → 8 → 9 → D1 alert language → D2 → D3 → D5 → D6 → C → B → A →
orchestration resolution pass → H → consolidated Claude Code prompt.

**Post-Gap-6 (logged, do not pull forward):** O-26 full design-consistency audit +
design-ownership map (feeds save-protocol check 8). Plus the parked C-series items and
clustering-coherence validation factors.
