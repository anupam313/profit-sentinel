# Profit Sentinel — Chat Context — 2026-06-22 — SKU-Namespace Contract (Pass One)
Companion narrative to state_2026-06-22_sku-contract-pass1.md. The "why / how it went."

---

## Arc of the session
Goal: fix the SKU-namespace mismatch where the cost table (AZR-/PKG-) was a universe disjoint
from the catalog (AZ-/AD-), so 0/428 cost rows reached a category and everything floored. Scoped
as a CONTRACT decision, not a prefix patch.

Discovery (Claude Code, read-only) drove every decision, and overturned several first instincts
— each caught BEFORE a line was written:
1. Catalog AZ- is authoritative (137k order lines + 625 variants + products all AZ-; cost the
   lone outlier). Join key is sku string, not shopify_variant_id — the broken placeholder
   variant_id was a red herring.
2. The real root cause was a DUAL WRITER: seed_shopify.py AND the WIP cost seed both wrote
   sku_cost_master (both record_types). Single-owner became load-bearing, not optional.
3. The contract is "cost READS the catalog from the DB," not a new shared module — the variant
   construction was too entangled in seed_shopify to extract cleanly, and reading the DB is
   drift-proof by construction.
4. Per-style grain (not per-size), the catalog's 8 categories (not the WIP's invented PANT), no
   hero tier (catalog marks no hero; "HERO" is a C8 nickname, not a product designation —
   minting a cost-side hero set would re-create the drift one layer up).
5. Cost is price-derived (the convention already in seed_shopify), not a flat per-category band
   (which I'd proposed; it decouples cost from price -> implausible margins).

The build: cost seed rewritten to read the catalog, generate 125 per-style price-derived rows,
gifting fed from the new set; seed_shopify's two cost writers removed. validate() PASS.
Re-seeded: 54 resolve, 71 floor (LLM-not-run, by design). Committed 8a707a1, not pushed.
Docstring caught stale (described the retired AZR-/428/hero design) and fixed before commit.

## CORRECTIONS OWNED THIS SESSION (audit trail — this is the important part)
A repeating error CLASS dominated: asserting what live code/schema/data DOES from a NON-
authoritative source (a doc, docstring, prompt, or my own prior turn), stated as verified.
1. unit_cost — invented; the live column is landed_cost/supplier_cost. Root cause: trusted the
   tech-arch doc schema over the live table (doc-vs-live drift).
2. "B-4 reads shopify_variant_id" + "B-4 filters effective_to" — both FALSE; from B-4's
   docstring/prompt, not its code. B-4 uses the labels as opaque tokens; reads nothing here.
3. Flat cost-band — proposed before checking that a price-derived convention already existed.
4. "Third namespace blocks the rebind / C2 / C6" — tagged [inference], NOT built on, routed to
   discovery -> overturned (label<->label, off critical path). The verify-loop working.
5. "Raise synthetic Step-0 coverage" — offered as a floor option, then RETRACTED after reading
   that 54/71 is the deliberate production-mirror.
6. "Committing at 57%-floor locks an uncleared gate" — OVERSTATED; the floor is a separate axis
   from the conform, and a code commit doesn't freeze the DB floor state.
The fix held for the rest of the session: no component-dependency or schema claim is load-
bearing unless carried by a live citation read THIS session; docstrings/prompts/docs/mount/
prior-turns are NOT authoritative for runtime facts. (Founder declined adding this as a prompt
block — instructions already long; the value is applying the existing tag rule, not more text.)

## KEY JUDGMENTS (in prose)
- Pass One's job (the SKU contract) is DONE and committable independently of the floor. The
  conform fixes PRODUCTION logic (the same join runs on real brands), so the time was not
  synthetic polish — it was production correctness surfacing in the seed.
- The floor is a SEPARATE axis. The genuinely pilot-gating item is that the LLM snap — the
  production workhorse — has NEVER run. Proving it end-to-end on synthetic data is de-risking an
  unproven production-critical path, not seed tuning. After that, stop seed work; the binding
  constraint becomes pilot-brand recruitment.
- Where over-investment risk is real: chasing the synthetic floor NUMBER once the engine is
  proven. Real brands have different catalogs; the synthetic split tells us little past "the
  engine works."

## SEQUENCING (founder-approved)
Checkpoint now (this handoff) -> Pass Two (assertion) in a fresh chat -> LLM/fan-out pass (opens
by reading category_inference.py's LLM code) -> marts/D1 rebind -> C8.

## Resume prompt (for a clean new chat)
> Resuming Profit Sentinel. Load save_protocol.md and state_2026-06-22_sku-contract-pass1.md
> (+ this chat_context). Re-verify line-count handles AGAINST REPO HEAD (8a707a1) before any
> edit — mount has been stale. Next item: PASS TWO — the assertion. Design here, build in
> Claude Code.
