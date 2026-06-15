# Profit Sentinel — CHAT CONTEXT (reasoning log)
## Session: D1 Gap 6 — discount-depth/S19 PARTIAL close
## Date: 2026-06-04

---

## HOW THE SESSION RAN
Opened by confirming file state against the 2026-06-03 sanity handles (all six matched;
both 06-03 saves present; two cosmetic header-staleness flags noted). Decided NOT to
re-litigate the flagged Gap 1 proposal here — it stays open. Worked the discount-depth/S19
component through repeated three-pass critique with hard founder pushback, then captured.

---

## THE DISCOUNTING ARGUMENT (how each call was reached)

- **Why no standalone discount alert / no "too deep":** the founder *sets* the discount,
  so reporting depth back to them fails the founder-utility test. The founder pushed on
  this directly ("he sets the depth, so don't catch 'too deep'") — agreed; it's a feature,
  not a gap. Deleted, not deferred.

- **Why depth is usable without cost (the correction):** the founder caught an
  inconsistency — if "depth went 9%→31%" is a usable number without cost, the discount's
  *contribution to margin direction* is too; only the dollar magnitude is feed-only.
  Earlier framing (contribution needs cost) was withdrawn. Discount is directional/unsized
  for non-feed brands, dollars for feed brands.

- **Why "net out the sale" is honest arithmetic, not a judgment:** we measure the actual
  discount and attribute exactly that slice; we do NOT model an "expected" depth (we
  refused to ask the founder for a plan and refused sale-to-sale comparison). So the
  mechanism flags margin damage the sale does NOT explain; it is *blind to the sale being
  a bad decision* — which is correct, per the point above.

- **Why source decomposition rides the trigger, not a baseline:** the founder asked
  "deeper than what?" There is no honest baseline (founder intent rejected; history
  rejected — slow-creep + which-sale). So no "deeper than X" claim. Instead, when D1 fires
  on its real (brand-relative) Trigger A/B and discounting leads, DECOMPOSE the effective
  discount by source. Shopify exposes each discount's type, so NO founder code-tagging.

- **Why the new-customer confound is deferred, not solved here:** a sale pulls in new
  customers who return more, so suppressing discount while firing on the returns residual
  is naïve. Fix = new-vs-existing split (each customer classed from own history), NOT
  sale-to-sale comparison and NOT a demand-weighted-discount heuristic. The founder
  rejected comparable-sales (manufacturer/pricing/vertical changes) and the heuristic was
  rejected on sample size (4–8 sales/yr), mix-over-depth, and circularity. Founder also
  caught that BAU and sale return rates differ for both customer types — so the split tells
  *who*, not whether abnormal. → genuinely a cross-component (residual-pass) problem.

---

## VERIFICATION DONE (against live sources, 2026-06)
- **Shopify per-item discount EXISTS** (`LineItem.discountAllocations`, with discount type).
  Airbyte already pulls it nested in orders; nothing unpacks it → OUR build. LANDMINE: use
  allocations, never the `total_discount`/`discountedTotalSet` summary fields (empty/zero;
  Shopify recommends allocations).
- **Loop exchange data is rich** (return detail carries the exchange order/replacement
  variant, dispositions, refund objects, label rates, timestamps). So the
  return-to-replacement size link IS buildable — earlier "drop as fuzzy" was a SEED limit.
- **Advanced (different-product) exchanges are a real, marketed Loop feature**, not an edge
  case; the API labels variant vs advanced → two handling paths (variant = size-direction,
  ops-cost-only; advanced = return-plus-purchase, variable margin).
- **Shopify is NOT replacing Loop** (Loop's admin can't be replaced by the Shopify API;
  Loop is the management layer on Shopify's rails). But native returns matured + the new
  Shopify Returns API carries returns/reasons/exchanges natively → build Shopify-primary,
  Loop-enrichment. Loop-vs-native ICP split logged as discovery item.
- **PII:** model already nulls email + customer_id on return rows; customer_id is
  pseudonymous and needed for repeat/new → kept on orders; join returns on order ID, never
  email.

---

## THE PARSER ARGUMENT
- Founder pushed: modern NLP reads sarcasm etc. — why call it slow? Conceded: comprehension
  is off-the-shelf; the slow part is the complaint→return *conversion*, which the founder
  agreed to park. Residual difficulty is small and finite: brand-specific label SCHEMA,
  multi-intent RULE, per-brand accuracy CHECK (gate D1-G12), customer-text-only,
  low-signal reporting.
- Action layer: founder argued (Amazon-review model) for summarise + link, not recommend,
  because the action depends on context we don't hold and can't verify. Agreed — and
  flagged it logically generalises to the evidence-stack 4th layer; founder said decide
  case-by-case, NOT generalise → logged as O-27 (two-part test: groundable + verifiable).
- Live small-sample velocity: history trains the classifier but does NOT enlarge this
  week's window → firing floor + honest silence, not historical depth.

---

## THE FLOOR CATCH
Founder asked how "below the floor" resolves the sale-comparison problem. Answer: D1 does
NOT fire on an absolute floor — Trigger A (drop below the brand's own baseline band scaled
to its own volatility) and Trigger B (downward trend in own weekly CM) are brand-relative.
The `client_config.margin_floor_pct` (default 5%, "calibrate to ~28%" note) is an orphaned
pre-Gap-2 relic, NOT wired into the locked logic → flagged for removal (O-25), routed to
the post-Gap-6 consistency audit (O-26).

---

## THE SAVE-PROTOCOL DECISION
Built `save_protocol.md` (nine checks, two phases) so we don't re-derive the integrity
checks each save. Added five checks beyond the original four (expected-delta, content
anchors, scoped diff, cross-file referential, new-file completeness) — each tied to a real
failure mode the founder named (content-level failure with right count; multi-file mirror
miss; partial-replace corruption). The full project-wide consistency audit + design-
ownership map was LOGGED (O-26), NOT folded into the per-save protocol — different cadence;
it runs after Gap 6 closes and then makes save-protocol check 8 mechanical. Today's
orphaned-floor find is another data point that the latent-inconsistency audit is warranted
(same class as the 06-02 category parallel-copy cascade).

---

## CARRY-FORWARD DISCIPLINE (unchanged)
Three-pass critique before any proposal; founder test on every proposal; pushback not
softened; verify against source before proposing; no hardcoding (brand-relative); no alert
language until all 9 D1 gaps resolved; engineering specifics → Claude Code as spec; all
code batched, no consolidated prompt until after H-series; design vs build chats separate;
end design/critique with a completeness confidence.
