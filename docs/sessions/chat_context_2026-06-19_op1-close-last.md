# Profit Sentinel — Chat Context — 2026-06-19 — OP-1 Close

Companion narrative to `state_2026-06-19_op1-close.md` (the machine-readable handoff). This is the "why / how it went" for a clean resume.

---

## Arc of the session

**1. Shopify access (post-Jan-2026 deprecation).** Legacy admin custom-app creation is gone; Dev Dashboard (Client ID/Secret + client-credentials grant, ~24h token) is the new path. But the partner-pre-transfer legacy button still worked on this dev store → permanent read_products token. Pilot implication flagged: real-brand onboarding now needs a public app + OAuth + review (lead time) — start that track now.

**2. Category probe.** Confirmed `Product.category` resolves on API 2026-04 (full breadcrumb). Coverage on the generic test store: 5/43 genuine paths, 26 the `na` "Uncategorized" sentinel, rest NULL — directional only. Reframe: Step 0 (read Shopify's assignment) is the cheap win for the minority; the LLM-classify-and-snap fallback is the workhorse.

**3. Two founder challenges that changed decisions.**
- *Shopify UI suggestion?* — verified UI-only (introspection: Product exposes only `category`, returns `na` until accepted). Our LLM fallback IS our own version of that suggestion. Rejected & recorded. Also surfaced the robust na-gid filter rule (not the localizable string).
- *Doesn't snapping to Shopify's taxonomy dissolve the Phase-2 sub-category deferral?* — yes. Two-step correction: (i) more clients don't fix thin per-brand volume (that's AL-19 + roll-up); (ii) snapping to Shopify's cross-merchant-validated taxonomy means we don't name/validate a taxonomy from one brand — Shopify already did. Net: revised #18 — sub-category depth is dynamic, not deferred. Honesty caveat kept: unblocks deep TAGGING, not deep ALERTING.

**4. Seed.** Synthetic seed updated to the confirmed shape: 54 categorized / 71 NULL, real rows untouched, gids baked, independent RNG (global PY_RNG untouched), no na sentinel in synthetic rows.

**5. The canonical propagation — one file at a time, byte-exact.** d1_validation_gates → agent_d_build_spec → technical_architecture → cross_alert_orchestration → pre_agent_build_checklist → product_strategy. Each: Step-0 byte-match (halt on mismatch), scoped diff, retired-wording scan, anchors-once, semantic read-back. Two corrections worth remembering:
- My line-delta hand-counts were unreliable (overcounted agent_d by 10) → switched to "report actual + diffstat, don't trust my estimate."
- I MISSED the D-28 schema mirror in the checklist (keyed the grep on clustering vocabulary, not schema vocabulary). Claude Code caught it as an out-of-scope adjacency. Fixed it, then ran a repo-wide safety grep that confirmed no other live stale mirror survives. Lesson: edit-site greps must cover BOTH the mechanic words and the schema words.

**6. source_schema_registry — read-first prevented a wrong edit.** It's a runtime auto-populated cast-manifest table (not a design file), scoped to Airbyte SOURCE columns. My ledger had mis-routed #4/#5/#16 to it; re-classified — no registry edit. Raw columns auto-register via schema_discovery at build time.

**7. Worktree scare → benign.** A `.claude/worktrees/...` copy held pre-OP-1 docs; checked it: clean, 29 behind master, strict ancestor, never edited → cannot revert OP-1. Ignored.

---

## Discipline notes (carry forward)
- Repo ≠ Claude Project knowledge. The project mount goes stale (it was 3815 vs 3818 authoritative). Re-upload edited files to the project for the next session's mount; commit to the repo separately.
- Verification that actually protected us: str_replace byte-match halts on mismatch (can't corrupt from a stale line number); LF-normalized sha256 to confirm repo==upload; scoped diff as the "nothing collateral" guard.
- The two authoritative category-schema homes (tech-arch ALTERED TABLE block + checklist D-28) now agree. Grouping/firing-depth authority = D1-G3 + the renamed "CATEGORY GROUPING + FIRING-DEPTH GATE" section.

---

## Resume prompt (new chat — TAXONOMY work)

> Resuming Profit Sentinel. OP-1 is closed (canonical edits landed + signed off; see state_2026-06-19_op1-close.md; commit pending/done). Load save_protocol.md and that state file; re-verify the line-count handles first. **Today's topic: TAXONOMY REFRESH + VERSIONING** (the flagged open item). START by verifying Shopify's Standard Product Taxonomy gid/node-stability + re-id policy from their release notes/changelog — that's the pre-req fact, currently only inferred. Then choose a refresh mechanism (pull-on-build vs pinned-version-committed + migration) and decide whether to store a taxonomy_version stamp alongside category_id. Separately, C8 (HERO return-driver) remains its own save-protocol pass.
