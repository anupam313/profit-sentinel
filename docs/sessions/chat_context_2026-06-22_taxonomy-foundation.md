# CHAT CONTEXT — 2026-06-22 — Taxonomy-Versioning Foundation

Paired with `state_2026-06-22_taxonomy-foundation.md`. This is the narrative/reasoning trail; the state file is the machine-readable resume handle.

## What this session was
Designed and shipped the **taxonomy-versioning foundation** — the data-model layer that lets Profit Sentinel store Shopify product categories without silently breaking when Shopify revises its taxonomy. Ended with everything committed (`b8fec19`, local-only), the prior WIP restored, and the canonical doc independently diff-verified.

## The problem, in plain terms
PS sorts every SKU into a Shopify Standard Product Taxonomy category and stores that category's id (e.g. `aa-1-13-8`). The id encodes the node's position in the tree, so when Shopify moves/merges/retires a node the id changes — a stored id can quietly go stale. Worse, the schema stored the id but **no record of which taxonomy version it came from**, so after an upstream change there was no way to tell if a stored id was current, drifted, or retired. Two surfaces: the pinned node list (LLM-snap fallback + baked gids in seed_shopify.py) and the per-SKU stamp (category_inference.py writing category_id onto sku_cost_master).

## How the design was reached (the reasoning, so it isn't re-derived)
- Verified upstream that the taxonomy is versioned (~quarterly, date-named), mutates existing nodes (rename/relocate/consolidate), and that a wholesale re-id already happened at 2024-07. Killed candidate (a) auto-pull.
- Landed on **(c) store a `taxonomy_version` stamp (mandatory) + (b) pin a tested version, migrate deliberately**. (c) is a prerequisite for (b), not an alternative.
- Founder's Q2 ("how do inactive/deleted SKUs get a category even with a frozen taxonomy?") reframed the problem: it exposed a **coverage** problem (deleted SKUs with thin text) distinct from the **versioning** problem. They meet in the same column. Resolution: categorize all SKUs fresh against the pinned version at onboarding (Step 0 if still in Shopify, LLM-snap if gone); uncategorizable ones go to the brand-level floor with disclosure.
- The grouping-key indirection was moved from "deferred (part of remap)" into the **now-foundation**, because inactive SKUs need a grouping home day-one and retrofitting the indirection later would force rewriting every category-grouped query. (Flagged at the time as a correction of an earlier over-compression, not a fresh idea.)

## Key repo-checks that de-risked the decision (Claude Code, read-only)
- **Ids are stable-assigned** (465/465 apparel nodes unchanged 2026-02→2026-05 despite +198 additions). So routine releases don't churn stored codes; only deliberate re-parents do. This *vindicated the founder's original "categories won't change that often" instinct* — an earlier hedge of mine (that 2026-05 being apparel-heavy "dented" stability) was overturned by the data: additions don't renumber.
- **Deliberate changes ≈ 0/release** (one bounded rename across three pairs; zero merge/split/retire). So the remap is rare AND cheap.
- **Shopify ships version-to-version crosswalks** — overturned my earlier (web-search-based) claim that the remap would be an expensive derive-from-diff. Caveat: no direct 2026-02→2026-05 map exists, so the remap must handle the no-crosswalk case.
- Conclusion: defer the remap algorithm confidently — justified by **detect (H21) + bounded cost**, not by a frequency estimate.

## The drop-vs-keep pushback (resolved)
Founder argued uncategorizable discontinued SKUs add no signal at brand level, so why keep them. Held the **keep** position — conceded the signal point, but the value is (1) reconciliation with the founder's own Shopify totals (PS's moat is verifiable explanation; dropping orders breaks the tie-out) and (2) unbiased baselines (discontinued SKUs are often killed *because* they returned badly; dropping a non-random subset flatters the baseline). LOCKED: keep at brand level with disclosure, never silent.

## Process discipline that mattered this session
- A persona addition was made mid-session (the **Deliberation Integrity Protocol** rules): when a position changes, state (a) new fact vs (b) correction of under-tested work; and **architecture is owned, not put to the founder for validation** — ask only for product scope/priority/risk. These were prompted by a flip-flop (I recommended a trimmed subset, then reversed it on the founder's own "no stale mirror" principle without new evidence).
- Repeated catches by the build agent that the design depended on but I'd asserted from docs: schema is `client_azure_co` not `public`; the OP-1 category columns were **never applied** to the live DB; the 80 MB categories.json is deliberately gitignored. Each was a doc-vs-reality gap. The pattern (canonical docs drifting from live state) is logged as a horizon reconciliation item.
- The founder demanded an **independent integrity check** of the edited technical_architecture.md rather than trusting the agent's self-attested 18/18. Done via real `git diff HEAD` read against the verified 3827-line original: 110 added / 8 deleted, all 8 deletions intended (schema correction + one deliberate DB-default drop + comment re-alignment + relocated fence), zero silent removals, all changes confined to the three authorized regions. This is the right bar for canonical-doc edits going forward.

## The finding that becomes next session
The live synthetic `sku_cost_master` (from the stashed WIP seed) uses SKUs `AZR-…`/`PKG-…` **disjoint** from the catalog's `AZ-…`/`AD-…` — zero overlap. So no cost row reaches a Step-0 category; every row floors. The categorization *code* is proven correct (run on catalog products); the *data* is two disconnected universes. This sits under every margin/CM alert (costs can't join to categories to returns). Diagnosed as independent seed authoring with no shared SKU contract — hence next session is scoped as establishing the **authoritative SKU contract**, not patching prefixes. It gates the marts-rebind.

## Resume pointers
- Load save_protocol.md + the state file; verify handles against **repo HEAD** (mount is stale — showed 1422/3827 when truth is 1424/3929).
- `b8fec19` is local-only; not pushed.
- Re-upload the 3929-line technical_architecture.md to the Project.
- Next: SKU-namespace realignment (contract, not prefix) → then marts/D1 rebind → C8 edit still pending.
