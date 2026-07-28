# Profit Sentinel — Chat Context — 2026-06-23 — Pre-Pilot Hardening
Companion narrative to state_2026-06-23_prepilot-hardening.md. The "why / how it went."

---

## Arc of the session
Opened to run Pass Two — the SKU-contract + uniqueness assertion (old R1) on top of last
session's committed conform (8a707a1). The very first recon query (do all order-line SKUs
resolve to the catalog?) came back clean — 0 orphans, Pass One intact — but a follow-up "is
the order-line table sane?" check found total rows ≈ 2x distinct line-item ids. Pulling that
thread turned the whole session into a live-data integrity investigation. Pass Two never ran;
instead we mapped the real state of the data and the controls meant to protect it. (The Pass
Two guard DESIGN was reached earlier in the session and is preserved in the state file under
"PASS TWO GUARD DESIGN" so it is not re-derived.)

The investigation, step by step (each step read-only, schema-qualified):
1. order_line_items: 274029 rows / 137023 distinct ids. The two rows sharing an id held
   DIFFERENT business content (different order, sku, price) — so not literal duplicates.
2. Per-table id scan: EVERY core Shopify table ~2x distinct ids, all under a single Airbyte
   generation_id -> a double seed-RUN, not an Airbyte re-sync.
3. Root cause: seed_shopify.py has no clear-before-insert; its ON CONFLICT DO NOTHING is
   untargeted, so it's inert on the constraint-less raw tables -> a second run appends a full
   second universe. discount_codes (which HAS a unique constraint) stayed clean — the control
   case that proves the mechanism.
4. Blast radius is non-uniform: clean 2x on the raw tables; products 1.744x (partial — only the
   125 catalog styles doubled); touchpoint_journey 1.204x (fractional, RNG-divergent). The
   fractional/partial cases CANNOT be reconstructed by deletion -> full clean re-seed is the
   only reliable fix.
5. Downstream: marts SUM over doubled rows (2x), and mart_causal_chain_daily inner-joins
   doubled lines x doubled orders -> ~4x. Ratio/DISTINCT measures survive; absolute units/
   revenue do not.
6. Why nothing caught it: the dbt unique tests EXIST on exactly the violated keys but are inert
   (not gated, staging unmaterialized -> vacuous pass, marts bypass staging, schema.yml name-
   drift). The production sync-variance guard that would catch the prod analog is UNBUILT.
7. Widening out: only seed_shopify + seed_sku_cost_master have actually run; 8 source connectors
   are built but at 0 rows. The DB is Shopify + cost only. suppression_log is even split across
   two schemas by different connectors.

## CORRECTIONS OWNED THIS SESSION (audit trail — the important part)
The same error class as prior sessions recurred and was caught by the verify-loop each time:
asserting a whole-table / whole-system conclusion from a partial sample or a non-authoritative
source, then revising when the authoritative scan landed.
1. "Double-load" (turn 1) -> RETRACTED to "single coherent dataset" (turn 2, from ONE sampled
   id pair) -> RE-CONFIRMED as a double seed-RUN (turn 3, from the all-tables 2x scan). Two
   flips before the per-table evidence settled it. Lesson re-learned: don't generalize from one
   row; the per-table scan is the authoritative artifact.
2. "Revenue is fine / genuine distinct lines" (turn 2) -> WRONG; the all-tables doubling means
   absolute revenue IS ~2x inflated. Over-corrected, then fixed.
3. "customers 19017 is odd -> not doubled / single-loaded" -> WRONG; 9509x2=19018≈19017, it IS
   doubled. Mis-read parity; corrected by the distinct-id scan.
4. "suppression_log is in public with a unique constraint, so it deduped" -> conflated TWO
   tables; the populated 10-row one is client_azure_co.suppression_log (seed_shopify's),
   constraints unverified. Correction recorded in R13.
5. (Process) Recommendation churn: recommended the surgical-dedup path, then reversed to full
   re-seed when the touchpoint fractional-doubling proved dedup non-viable; and repeatedly put
   an A-vs-B technical choice to the founder that was the architect's to own. Fix going forward:
   while diagnosis is incomplete, recommend the next DIAGNOSTIC, not the remediation; own the
   technical call; bring the founder only scope/priority/risk.
Throughout, [inference]-tagged claims (e.g. "products partial-constraint", "tests never gated")
were routed to a confirming query/read rather than banked — that discipline is what kept the
final R9–R13 set evidence-backed.

## KEY JUDGMENTS (in prose)
- The systemic story is bigger than any single bug: the platform has the RIGHT controls
  DESIGNED (sync-variance guard, dbt unique tests) but NONE are in the enforcement path. R9 is
  the symptom; R10 + R11 are why it went unseen; all three would independently have caught it.
- Pass Two was not a detour abandoned — it was REFRAMED. The uniqueness assertion the founder
  wanted IS the missing warehouse-layer guard (R11). Its full design (home / 4 asserts /
  fail-hard-on-3 / coverage-reported-not-enforced / exclusions-by-kind / build-only / new
  uniqueness assertion) is preserved in the state file so it isn't re-derived.
- The double-seed fixes PRODUCTION logic, not just synthetic polish: the same append-only +
  inert-ON-CONFLICT pattern is exactly what a production Airbyte double-sync would hit, and
  there is no guard to stop agents firing on the inflated data. That is the pilot risk.
- Pilot-readiness reframed (founder): the pilot is the FULL product end-to-end (same connectors
  + checks), where causal sophistication deepens on REAL data — NOT a place to stress-test
  integration. So plumbing + checks must be proven BEFORE a brand connects.
- Scope discipline held: nothing was fixed or re-seeded this session. The cost of a wrong
  truncate on a OneDrive-synced repo, mid-session, is high; capture first, execute next session
  with the run-order mapped.

## DECISIONS (the founder's calls, in brief)
Two-bar connector model (D-A): Bar 1 integrity for everything connectable; Bar 2 rich-synthetic
+ proven-end-to-end for the fired-alert five — Shopify, Gorgias, Meta, Google Ads, TikTok
(TikTok confirmed IN). Loop/Klaviyo/GA4/Sentry are opportunistic (D-C). Loop stays fallback
until Shopify-native returns is proven (D-D). Weekly founder digest is IN the pilot via email,
through the relevance gate, carrying the full-product digest INTENT scoped to the pilot-monitored
signals (fired alerts + in-app metrics + suppressed-leaks) — with a doc-conflict to reconcile
later (D-E, currently Horizon-2 in canon). A HARD pre-pilot hardening gate of 7 conditions (D-F)
including a deliberate fault-injection drill. And the priority call (D-G): hardening + connector
completion ranks ahead of Pass Two / C8 / taxonomy-versioning, with Pass Two folded INTO the
hardening.

## SEQUENCING (founder-approved)
Capture now (this handoff) -> next session: pre-pilot hardening, opening with the connector
run-order map so the R9 clean re-seed is actionable -> then build the enforced guards (R10/R11)
-> prove the 5 Bar-2 sources end-to-end -> fault-injection drill -> pilot readiness.

## Resume prompt (for a clean new chat)
> Resuming Profit Sentinel. Load save_protocol.md and state_2026-06-23_prepilot-hardening.md
> (+ this chat_context). Re-verify line-count handles AGAINST REPO HEAD (a307b81) before any
> edit — mount has been stale. Next item: PRE-PILOT HARDENING (R9–R13 / D-F gate), NOT Pass Two
> in isolation. Open by MAPPING THE CONNECTOR RUN-ORDER for the R9 clean re-seed. Design here,
> build in Claude Code.
