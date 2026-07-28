# Profit Sentinel — Chat Context — 2026-06-19 — OP-1 Close

Companion narrative to `state_2026-06-19_op1-close.md`. The state file is the machine-readable capture; this is the "why / how we got here" for a clean resume.

---

## Arc of the session

**1. Shopify access path (post-Jan-2026 deprecation).** The old "Develop apps → create custom app" route is deprecated — admin can no longer create new legacy custom apps; Shopify pushes everything to the Dev Dashboard (Client ID/Secret + client-credentials grant, ~24h token). But the founder's screen still showed the legacy button with a partner-pre-transfer carve-out, and on this partner-owned, untransferred dev store **Path A (the legacy button) still worked** — yielding a permanent `read_products` token. We noted the pilot implication: real-brand onboarding can no longer use the merchant-hands-you-a-token shortcut; it needs a public app + OAuth + review, which has lead time. Start that track now.

**2. The category probe.** With the token, Claude Code ran a GraphQL probe and confirmed `Product.category` resolves on **API 2026-04**, returning the full Standard Taxonomy breadcrumb (`fullName`) plus `id`/`level`/`isLeaf`. Coverage on the test store: only **5 of 43** real rows carried a genuine path; **26 were the `Uncategorized` sentinel** (`gid://shopify/TaxonomyCategory/na`), the rest NULL. The key reframe: **Step 0 (reading Shopify's assignment) is the cheap win for the minority; the LLM-classify-and-snap fallback is the workhorse (~88% here)** — though this is a generic test store, so 12% is directional, not a real-fashion-brand fill rate.

**3. The founder's two good challenges.**
- *"Can we use Shopify's UI category suggestion?"* — sound instinct, but we verified it is **UI-only**: introspection showed `Product` exposes exactly one taxonomy field (`category`), which returns `na` until the merchant accepts. The suggestion is never persisted to the API. Reframe: our LLM fallback **is** our own version of that suggestion — we generate it rather than read Shopify's. Rejected and recorded so it isn't re-litigated. (Also surfaced the robust rule: filter on the **na-gid**, not the localizable "Uncategorized" string.)
- *"Won't snapping to Shopify's taxonomy dissolve the Phase-2 sub-category deferral?"* — this one **changed a decision.** It came in two steps:
  - First correction: more clients do NOT fix thin per-brand volume (Problem A) — that's AL-19 + roll-up, within-brand, same in any phase. Clients help the *classification* layer (Problem B): recognizing/validating fine sub-types from product-text variety + recurrence. The volume rationale I'd led with was a red herring.
  - Second correction (the decisive one): since we snap to **Shopify's published, cross-merchant-validated** taxonomy, we are **not naming or validating a taxonomy from one brand** — Shopify already did. The 2026-06-02 deferral's rationale ("single-brand data cannot validate a fine sub-category taxonomy") was written for the **retired self-clustering** approach and is dissolved. Net: **sub-category depth is dynamic, not Phase-2-deferred** (revised #18). Honesty caveat retained: this unblocks deep *tagging*, not deep *alerting* — per-brand volume still caps firing depth via AL-19.

**4. The seed.** Claude Code updated the synthetic seed to mirror the confirmed production shape: ~40/60 split landed at **54 categorized / 71 NULL**, type→node map baked from the taxonomy file, independent `Random(product_id)` so the global `PY_RNG(42)` stream is untouched, real rows provably unchanged, no `na` sentinel written into synthetic rows. Scope-clean: did not touch dbt staging, the schema registry, or technical_architecture.md — those are formalized through this OP-1 close.

**5. OP-1 finalized.** The full decision set (state file) was confirmed, including revised #18. The founder asked for the file/checks plan before execution; it was given and approved. This session produced the Phase-0 ledger + these two continuity files. The Claude Code change-specs + save-protocol prompt are the next artifact.

---

## Working-discipline notes (carry forward)

- The taxonomy file (`data/shopify_taxonomy/categories.json`, ~80MB) is **gitignored**; gids were baked into the seed. For runtime the LLM-snap fallback needs a node list — decide trimmed-subset-committed vs load-from-source when formalizing. Not a durable dependency yet.
- This OP-1 close **revises** existing closed content (the 2026-06-02 spec, D1-G3, agent_d category spec) — not just appends. The highest-risk save-protocol checks are therefore **Check 7** (scoped diff — no collateral deletion), **Check 4** (0.70 / AL-25 / return-rate-coherence / old deferral fully retired with notes), and **Check 10** (the rewrite says the new thing, not its opposite).
- Editing tech-arch and cross_alert for OP-1 is **not** license to fix the deferred roster counts living in the same files; the scoped diff must show only the OP-1 regions.
- C8 stays a **separate** pass after OP-1. Do not merge.

---

## Resume prompt (for a clean new chat)

> Resuming Profit Sentinel. Load `save_protocol.md` and `state_2026-06-19_op1-close.md`. OP-1 design is LOCKED (see the decision set). We are at: build the Claude Code save-protocol prompt + exact change-specs from the real file content (confirm ranges + retired-wording strings against the live files — mount may be stale), then Claude Code applies the 5 repo edits and runs Phase B mechanical checks, then I edit product_strategy.md manually for semantic read-back, then C8 as its own pass. Re-verify all line-count handles first.
