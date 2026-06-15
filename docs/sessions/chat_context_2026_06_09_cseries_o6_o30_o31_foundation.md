# Profit Sentinel — Chat Context
## Date: 2026-06-09 (C-series review — O-6 / O-30 / O-31; category-and-returns-baseline foundation opened)
## Pairs with: state_2026_06_09_cseries_o6_o30_o31_foundation.md
## Purpose: the WHY and HOW behind this session — the reasoning the ledger doesn't carry, the open questions, and the live worry that sets next session's order.

---

## HOW THE SESSION WENT (reasoning trail)

The session opened with a documentation-integrity pass (independent second-read of the previous self-verified save), which found that the previous session's mirror list had MISSED two files that carried a stale Gap-6 status — pre_agent_build_checklist and d1_validation_gates. Both were corrected by a "mirror-sync" save, and the cause (a hand-built mirror list misses status mirrors) was logged to the consistency-audit item (O-26). Lesson that recurred all session: a product-wide rule or status must live in ONE authoritative home; copies elsewhere go stale. This lesson drove several later calls.

Then the C-series review proper:

- **O-6 (returns router).** Settled who owns the return story when both the returns alerts and the margin alert can see the same returns. Decided: returns alerts own and always fire; margin alert references, never re-alerts. Key fashion-specific nuance that the advertising-cost version did not need: returns are SLOW — the returns alerts fire early, the margin hit lands weeks later — so the margin alert's reference is a SEQUEL, not a same-week duplicate. Deliberately scoped to the ownership RULE only; the dollar magnitude needs cost data and stays parked.

- **O-30 (prevented-outcome).** Raised by the founder: the returns chain runs Gorgias (early complaint signal) → founder may act → Loop (actual returns). If the founder acts, the predicted spike may never land, and a SUCCESSFUL warning looks identical to a FALSE one. Resolved by judging COHORTS, not "did they act": in-flight cohort (already shipped, a fix can't rescue them) tests if the warning was real; next cohort tests if the fix worked. Leans on cohort OUTCOME because we CAN'T reliably see the action anyway (no clean product-state/price history; Loop reason codes unreliable). This forced the stat-sig question (below).

- **Stat-sig vs directional (settled inside O-30).** At $2–10M, a per-SKU BAU week might be 15–40 orders; a "spike" is 4 returns becoming 8 — real to a founder, never significant on a formal test. So: DIRECTIONAL, never naked-directional, never gate on formal significance. Confidence comes from cross-source agreement + a fair (apple-to-apple) comparison, not a p-value. Pushback made to the founder's framing: apple-to-apple is not a later refinement that directional waits for — it is the PRECONDITION that makes directional honest. "Apple-to-apple" = same return-window maturity + same product mix + same acquisition mix + same seasonal point.

- **O-31 (freeze + calibrate, general).** Founder asked whether, in beta, the system develops dials on the fly or we fix things in conversation. Answer: NEITHER. The live system stays deterministic and frozen; only dials are calibrated, by instrument-then-set-from-logged-evidence, deliberately, not continuously, not in chat. The founder twice pushed (rightly) that this is product-wide, not returns-specific — so O-31 was written GENERAL, and the planned per-returns cross-reference was DROPPED so O-31 isn't mirrored into one alert (consistency with the session's recurring lesson). The Evidence Stack does NOT cover this: it audits the per-alert OUTPUT, while O-31 governs the system that PRODUCES outputs — the Stack consumes dials but can't vouch for their calibration.

Then C3 (the shared yardstick) was opened, sub-item (a) — retire the blended-average / fixed-2× / fixed-7-day rule and use the category's-own-range method — was agreed in principle. But the founder's follow-up questions about HOW category is defined and HOW "abnormal/thin" become concrete exposed that C3 is the edge of a larger foundation. That is where we paused.

---

## THE FOUR QUESTIONS THE FOUNDER RAISED (these define the foundation; all OPEN)

1. **Periods.** How do we define "normal" returns separately across BAU, pre-sale, sale, post-sale — when exact sale dates are fuzzy and a founder may not even agree on them?
2. **Algorithm + granularity.** Which algorithm defines categories (segmentation mislabels without labels)? What happens with too many tiny clusters vs too few large ones?
3. **Concrete at beta.** "Dialled in from data later" — what must we actually FEED the system so these vague terms are concrete when beta runs? (An EXAMPLE is owed — see below.)
4. **New category.** When a genuinely new category appears, how does it get its own group instead of being dumped to brand-level?

State file holds the current best understanding of each as OPEN questions. Note the partial answers reached in discussion (NOT yet locked, for context only): the algorithm is LLM CLASSIFICATION (not unsupervised clustering) from title/tags/type/vendor/collections — sidesteps the no-labels problem; confidence is a cross-signal AGREEMENT score, not the model's self-opinion; a return-rate COHERENCE gate decides if category-level analysis is trustworthy or the brand drops to brand-level-with-disclosure; collections feed DISPLAY labels only (they're promotional buckets, unsafe as grouping keys); internal grouping uses the AI clusters directly, founder rename is display-only. These are the EXISTING design (in technical_architecture.md ~lines 3470–3597); the GAPS are granularity-tuning, stability, period-aware bands, and the new-type provisional-group path.

---

## THE LIVE WORRY THAT SETS NEXT SESSION'S ORDER

The founder is genuinely anxious — and it is a legitimate worry, not to be smoothed over — that per-brand sales comparability may be near-impossible. Common events (BFCM, season launches, Halloween) are comparable across time; but bespoke per-brand sales (a payday sale at month start, a once-a-year summer sale) have no prior comparable to build a "sale normal" from. This anxiety is WHY foundation question 1 is worked FIRST: it is the load-bearing wall. A live possibility (NOT decided) is that the honest answer is "during idiosyncratic sales, suppress / narrate rather than force a comparable" — and if so, questions 2–4 get simpler. Do not resolve question 1 toward a clever comparable just to avoid the uncomfortable answer; pressure-test the suppress-don't-compare option honestly.

---

## THE OWED EXAMPLE (foundation question 3 — to be worked next session, illustrative only)

The founder asked for a concrete example of "abnormal/thin dialled in from data." The shape of the answer (to be developed, NOT locked): at onboarding, read the brand's own history → "your dresses returned at 28–34% across the last year (their own range)." That LEVEL is the brand's own data, not seeded. Then a conservative system-wide SENSITIVITY default — e.g. "abnormal = clearly outside the category's own range; thin = a category with too few returns in the window to draw a stable range" — with the exact width/threshold flagged "calibrate from logged data," exactly like the 0.70 agreement threshold and 0.30 coherence floor already in the design. Beta does NOT learn the right numbers at 5 brands; it runs conservative (narrate-don't-fire) and LOGS what would have fired at other settings, for later calibration. The forbidden thing is guessing a brand's return LEVEL; the allowed thing is a conservative system-wide sensitivity DIAL.

---

## PRINCIPLES / DECISIONS REAFFIRMED THIS SESSION

- **No-Seed:** brand-own levels are required; a guessed brand-specific return level is forbidden; a conservative system-wide sensitivity default is allowed (it's a dial, not a seed).
- **Freeze-skeleton, calibrate-dials (O-31):** applies to alerts AND to the category structure (sticky clusters, slot-in new products, deliberate recalibration).
- **Directional over stat-sig** at this GMV tier; fair (apple-to-apple) comparison is the precondition, not a later refinement.
- **Wrong alert is worse than a missed one** → conservative defaults at beta, narrate-don't-fire when unsure.
- **One authoritative home** for any product-wide rule/status; copies elsewhere are stale-mirror risks (the session's recurring lesson, now embodied in how O-31 was written and why the consistency audit O-26 exists).
- **Honesty boundary (correlation-not-causation):** "appears to have / coincided with," never "your action saved $X."

---

## WORKING DISCIPLINE (carry forward)

Three passes before any proposal; ONE open item at a time with explicit sign-off; no hardcoding (brand-relative or narrate); gloss coded refs in plain language; deliver COMPLETE files via the save protocol's 11 checks (no manual editing by the founder); verify against source files before any claim; genuine pushback held when correct; flagged items go to the named ledger, not patched ad hoc. RESPONSE STYLE: simple plain language, no code unless asked; when starting a series, first say in plain words what it's for.

Founder note: low confidence in signing off the foundation's FRAMING is expected and correct at this stage — which is why the foundation is logged as QUESTIONS, not answers. Logging a question commits to nothing and is reversible; logging a provisional answer is the thing that bites. Resolutions land only on explicit sign-off, one at a time.
