# Profit Sentinel — State
## Date: 2026-06-09 (C-series review — O-6 / O-30 / O-31 resolved; category-and-returns-baseline FOUNDATION opened)
## Supersedes: state_2026_06_08_d1_gap6_cogs_parked.md
## Status: C-series review IN PROGRESS — paused at a newly-named foundation stream. Point 1 (sales-period comparability) is the next thing to work.

---

## WHERE WE ARE (one-paragraph orientation)

The C-series review (returns-side alerts) is underway. Three items were resolved this session and are saved in the orchestration ledger (`cross_alert_orchestration.md`, now 840 lines). On opening the next item (C3 — the shared "what counts as an abnormal return" yardstick), the discussion surfaced that C3 is not a single sub-item but the visible edge of a larger **category-and-returns-baseline foundation** that several alerts stand on. We have NOT resolved that foundation. We named it, listed its open questions (below, as QUESTIONS — no answers yet), and decided to work the highest-anxiety one first. The rest of the C-chain is parked behind this foundation.

---

## LOCKED THIS SESSION (all in cross_alert_orchestration.md, 840-line version)

Plain-language summaries; the ledger has the full text.

- **O-6 — returns router (RESOLVED).** When returns move, the returns alerts own the story and always fire on their own; the margin alert references them and never raises its own returns alarm. Both must use the SAME definition of "abnormal returns." The margin alert's reference reads as a sequel weeks later ("the return spike flagged earlier has now cost real profit"), not a same-week duplicate. If returns rise for a reason the returns alerts don't track, the margin alert may carry the cost but not diagnose the reason. The dollar figure stays parked behind the cost (COGS) work. Formal wiring into the causal graph + tightening the margin-alert spec's coarse "still open" note both ride the later orchestration pass.

- **O-30 — returns prevented-outcome (RESOLVED).** The returns warning is a prediction; if the founder acts, the predicted spike may never appear, so a successful warning and a false one look identical. Handled by judging COHORTS, not "did the founder act": the in-flight cohort (orders already shipped when the warning fired) tests whether the warning was real; the next cohort (orders after) tests whether a fix worked. Judge only once cohorts are readable. Leans on cohort OUTCOME, not on detecting the action. Directional, never naked-directional, never formal stat-sig at this brand size (confidence = cross-source agreement + a fair comparison). Honesty stays "appears to have," never "your action saved $X." Dollar parked behind cost work.

- **O-31 — dial calibration & system-freeze (ADDED, GENERAL to all alerts).** The live system stays deterministic and frozen during beta — chains, alert logic, comparison rules do NOT self-tune in production (that would break the trust moat and is undebuggable on live data). Only the DIALS are calibrated, by a deliberate evidence step: instrument first (log each fired alert, its cohort sizes, whether the founder acted, the actual outcome), then set dials from logged evidence against pre-agreed criteria — never in ad-hoc chat, never continuously. The Evidence Stack's verifiable-numbers and own-history layers CONSUME these dials and can't vouch for them until they're calibrated-and-frozen. Self-proposing dials with one-click approval are legitimate but post-beta only. Permanent home: the principles doc — to be authored at the pre-beta instrumentation stage; the ledger is its interim home.

---

## THE FOUNDATION STREAM — category-and-returns-baseline (OPEN — questions only, NO answers yet)

This is the bedrock under the confirmed-return-spike alert (C3), the margin alert's return driver (D1), the returns chain, and the O-30 prevented-outcome check. It is logged as OPEN QUESTIONS on purpose — none is resolved, and nothing downstream should treat any line below as a decision.

1. **Period-aware "normal" returns — OPEN.** One return band per category is wrong, because returns are not flat across the calendar (post-sale and post-holiday cohorts return far more, with a lag). Open question: how does "normal" account for BAU vs pre-sale vs sale vs post-sale? Real worry raised this session: at this brand size, idiosyncratic per-brand sales (a payday sale, a one-off summer sale) may have NO comparable prior event to form a "sale normal" from — common events (BFCM, season launches, Halloween) are comparable, but small bespoke sales are not. A live possibility is that the honest answer is "during idiosyncratic sales, suppress / narrate rather than try to build a comparable band." NOT decided. **This is the first item to work next session — it is the load-bearing wall, and its answer may simplify questions 2–4.**

2. **Cluster granularity tuning — OPEN.** Target: "the coarsest grouping that is still behaviourally coherent AND leaves each category with enough returns to read." Today's design DETECTS bad granularity (too many tiny categories = too thin; too few giant ones = incoherent) and retreats to brand-level-with-disclosure — but it does NOT tune toward the sweet spot. How to actively find that grouping is open. Ties to the roll-up grain question.

3. **Making "abnormal" and "thin" concrete at beta — OPEN.** "Dialled in from data later" does not mean "starts empty." The LEVEL (each category's normal return rate) is computed at onboarding from the brand's OWN history. The SENSITIVITY (how far outside the spread = abnormal; how few points = thin) needs a starting value. Distinction to hold: a guessed brand-specific return LEVEL is a forbidden seed; a conservative system-wide SENSITIVITY default is allowed (same class as the provisional 0.70 / 0.30 thresholds already in the design marked "to be calibrated"). At 5 beta brands there is not enough data to calibrate statistically, so beta runs on deliberately CONSERVATIVE settings (err toward narrate-don't-fire) while LOGGING what would have fired at other settings; real calibration comes later. Open: the exact conservative defaults + the instrumentation spec. (An illustrative example is owed — see chat_context.)

4. **New category / new product grouping — OPEN.** Two different cases. A semantically new product TYPE (a dresses brand launches outerwear) the classifier can recognise day one — it should get its OWN provisional group, watch-only, with NO band until it accumulates its own history (not force-fit into an existing category, not dumped to brand-level). A behavioural SPLIT (discovering "dresses" is really two return populations) cannot be done on one brand's data — deferred to the multi-client / network phase. Open: the "new semantic type → own provisional watch-only group" path is not explicitly specified, and it is tangled with stability (item 5) because the current design does not auto-group new products after onboarding (they wait for a manual re-run).

5. **Cluster stability — OPEN.** The current design has the grouping mechanism and a return-coherence quality gate, but NO mechanism guaranteeing an existing product keeps its category when the grouping is re-run. Re-running could re-draw clusters and silently reassign existing products, moving their bands underneath them — poison for a determinism-based trust model. Direction (same shape as O-31's freeze rule): cluster assignments are STICKY; new products are SLOTTED into existing categories (not reshuffled); re-drawing the whole structure is a DELIBERATE, logged recalibration, never an automatic side-effect, flagged because bands may shift. NOT yet specified or locked.

**Possible sixth gap (flagged, not confirmed):** how the return LAG interacts with period-keying (a sale-driven return lands weeks after the sale). May be part of item 1 or its own item — to be found by working item 1.

---

## WHAT IS PARKED BEHIND THIS FOUNDATION

The rest of the C-chain does NOT move until this foundation is worked:
- the remaining C3 sub-items (fair "apple-to-apple" comparison controls; brand-relative materiality band; roll-up grain SKU→style→category; readable-cohort minimum; the shared thin-history fallback — margin alert's exposure test vs C3's 90-day wait, must converge; the instrumentation spec);
- O-7 (returns chain ↔ influencer-ROI shared cohorts);
- C10 (Alert-3 destination-fulfilment-cost seam).

Note for when C3 finally resolves: C3 lives in TWO files — the open item in `cross_alert_orchestration.md` AND a "provisional lock" finding in `agent_d_build_spec.md` (around line 2480). Resolving C3 is a two-file save.

---

## HARD BOUNDARIES STILL IN FORCE (do not cross without explicit instruction)

- **Cost (COGS) work is PARKED** (discovery-blocked, ledger item O-28). The margin alert (D-series) and any margin/profit VERDICT are parked behind it. The foundation stream above is all catalogue-and-returns data and is COGS-INDEPENDENT — it can be worked now. If foundation work starts to need a margin/profit number, STOP and flag, do not reopen cost work.
- **No alert language** until all design gaps close (a standing rule). The foundation is design, not wording.
- **O-14 stale tail** still carried for the later one-time consistency audit (ledger O-26) — do not patch ad hoc.
- **O-31's permanent home** is the principles doc, authored at the pre-beta instrumentation stage — not now.

---

## NEXT SESSION — START HERE

1. Verification gate FIRST: read the load list below, then report each canonical file's line count vs the handles in this file. Uniform +1 = trailing-newline convention, proceed. Any non-uniform delta or a file at an OLD count = STOP and re-read fresh.
2. Then work **foundation question 1 (sales-period comparability)** — alone, one item, three passes, plain language, explicit sign-off before moving on. Its answer likely reshapes questions 2–4.
3. Logging discipline for the foundation: log QUESTIONS and RESOLUTIONS only when signed off — never provisional answers (the questions above are deliberately answer-free).

---

## SANITY HANDLES (line counts as of this save — next-session tripwire)

- agent_d_build_spec.md — 2710
- technical_architecture.md — 3815
- cross_alert_orchestration.md — 840  ← UPDATED this session (O-6/O-30/O-31); upload the 840-line version, it supersedes all earlier copies
- product_strategy.md — 1416
- d1_validation_gates.md — 386
- pre_agent_build_checklist.md — 389
- save_protocol.md — 149

---

## LOAD LIST (next session — load in the project)

- state_2026_06_09_cseries_o6_o30_o31_foundation.md  ← read FIRST (this file)
- chat_context_2026_06_09_cseries_o6_o30_o31_foundation.md  ← the reasoning trail + the four questions + the comparability worry + the owed example
- save_protocol.md (the 11 checks)
- cross_alert_orchestration.md (840), agent_d_build_spec.md, technical_architecture.md, product_strategy.md, d1_validation_gates.md, pre_agent_build_checklist.md
- locked, do not reopen: seed_decisions_gap_d_e.md, seed_decisions_gap_f_g.md, gap_abc_decisions.md
