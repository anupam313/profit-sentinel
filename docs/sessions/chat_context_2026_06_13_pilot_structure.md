# Profit Sentinel — Chat Context: Pilot Structure (OP-PILOT-1)
## Date: 2026-06-13  ·  Session: pilot_structure  ·  Pairs with state_2026_06_13_pilot_structure.md

This file is the WHY behind the state file — the reasoning a future session needs so the
decisions don't read as arbitrary.

---

## THE ARC OF THE SESSION
Started from the pilot pivot (prior session) and resolved OP-PILOT-1: how the pilot is
organized without polluting the full-PS material or confusing pilot vs non-pilot context.

The repeated lesson, learned the hard way across several critique rounds: Claude was proposing
at the design-conversation altitude and only descending into the actual file state when pushed,
so flaws surfaced one critique at a time. Two of three were FILE FACTS (decision-labels
referenced cross-file; the doc pass being COGS-blocked) catchable with greps up front. Fix
adopted as standing rules: verify before propose; label claims by source; front-load
"what would make this wrong." Re-reasoning over unverified assumptions does not catch a missing
fact — only checking the source does.

## KEY REASONING TO CARRY
- **Pilot = product earlier in its life.** The registry is the artifact that makes this literal:
  same registry, different `status` values over time. So it is NOT a pilot-only structure — it
  is the product's permanent alert-lifecycle layer. This is why status names had to be
  lifecycle-neutral (gated-live vs live), not pilot-framed.
- **Why a separate registry, not columns on §3D:** disposition is provisional and fast-changing
  (graduation, 5→6→7); §3D is stable and canonical-locked. Separate the change-rates. The
  registry references §3D by ID and never duplicates its fields → no stale-mirror.
- **Why Agent B now, not deferred:** the causal graph is a hardcoded chain registry; Agent B's
  "traversal" is match-chain → check corroborating signals → score confidence — buildable over a
  small graph. The hard, scale-dependent part (cross-client novel-chain promotion) was already a
  separate deferred track. And the binding constraint is RECRUITMENT, not build — build sits
  behind recruitment on the critical path — so building Agent B properly costs little timeline.
- **Why the §3D hole can't be a two-row patch:** E-codes run to E33+E40, and P2-FINDING 5 says
  E7–E40 / B6–B16 / A8–A18 are a MIX of scenarios, decisions, and possibly-alerts. So
  "complete §3D" = classify each, which IS the namespace task. The two converge; do them as one.
- **Why A2 is park-DISTINCT, not "merged into return-driver":** A2 (Root Cause of ROAS Drop)
  is broader than the return-driver hero — it catches non-returns causes (e.g. bad acquisition
  targeting via the Explorer cohort), not just the returns slice the hero owns. Marking A2
  "merged" in the registry would risk a future session assuming return-driver already does A2's
  whole job and never building the broader capability. So: park-distinct, with a note that
  return-driver covers only its returns portion. (E5 = High-actionability alert; E6 = internal
  plumbing, not a fired alert — see state file for all three calls.)
- **Parser (settled earlier, reaffirmed):** PS validates its own parser against a HUMAN-labelled
  sample of the brand's raw ticket text — never against Gorgias tags (tags are the unreliable
  thing the parser exists to route around). Validating against tags would be circular. The
  per-brand accuracy gate is d1_validation_gates.md GATE D1-G12 — measured against that
  human-labelled sample BEFORE any pilot client sees parser-derived output.
- **Value-vs-moat filter (the promotion criterion):** what's worth building/promoting during the
  pilot is judged on VALUE (is the founder getting this today?) and MOAT (can Shopify or a cheap
  app copy it? — cross-source joins are defensible; single-source + threshold is not), conditional
  on EXECUTION DEPTH. This is what keeps registry growth from drifting toward all 57 (pilot_scope §3).
- **Architecture nuances (from the diagram review, easy to lose):** "suppression and orchestration"
  are TWO distinct engines — suppression = don't fire a known-explained/stale signal; orchestration
  = resolve collisions when two alerts fire on one event. Cross-client novel-chain promotion is
  HUMAN-REVIEWED (a person approves before it's hardcoded), not an automatic flip at 10 clients. And
  the real pipeline isn't a straight line: Agent B reads back into the DQ layer (a low-trust source
  caps the confidence B can assign), and the parser feeds both Agent B's reasoning and Agent C's
  action wording.
- **Where the "three buckets" went:** the pivot session's pilot-only / reused-frozen /
  parked-stays-in-PS buckets are now the registry `status` field (parked → backlog; pilot →
  gated-live; etc.) — superseded by the registry, not dropped.

## THE VERIFICATION MECHANISM (and its honest limits)
Anupam can no longer give a meaningful full sign-off at this complexity. Resolution: the
save_protocol already exists and is comprehensive (3 phases, 11 checks, Phase-0 decision
ledger). So no new mechanism — instead (a) make Checks 1–9 an executable, re-runnable checker
(not Claude self-attesting), and (b) produce a JUDGMENT DIGEST: the 3–5 items per save that no
self-check can verify (the design calls + Phase-0 capture Claude is least sure was exhaustive).
Anupam reviews the digest — the minimal human floor — not the whole file.

The irreducible limits, stated plainly so they are never assumed away:
- The checker only catches what its manifest knows to check; a Phase-0 miss is invisible to it.
- The digest depends on Claude correctly flagging what IS a judgment call — a real choice
  misclassified as "settled" never reaches Anupam's eyes. A mechanism can hide a wrong decision
  by failing to flag it as a decision.
- Self-verification shares Claude's blind spots: a misread of intent corrupts file and check alike.
Conclusion: Claude pushed back on dropping human review to ZERO — the digest stays. A checker
makes the MECHANICAL layer bulletproof; it cannot make the JUDGMENT layer safe.

## A REVERSAL OWNED (for the audit trail)
Claude earlier proposed archiving the state/chat_context files OUT of the searchable Project,
then retracted it. It was wrong: those files are the continuity mechanism and must stay IN the
Project, and the retrieval confusion it was solving for is already handled by the
session-start verification gate + state-file read-back. Reversing a standing, repeatedly-
confirmed decision deserves an explicit "I'm changing earlier advice, here's why" — not a buried
bullet. Logged here so the reversal is visible, not silent.

## POINTERS
- Full decision list + LOCKED/CONFIRMED/PROVISIONAL/OPEN + order of operations:
  state_2026_06_13_pilot_structure.md.
- Save procedure: save_protocol.md (3 phases, 11 checks).
- Namespace + E5/E6 + relationship facts: cross_alert_orchestration.md (P2-FINDING 4 & 5, O-31).
- Pilot alert content: pilot_scope.md §4 (the proto-registry to be formalized).
