# Chat Context — D1 Gap 4 Close
## Date: 2026-05-31
## Pairs with: state_2026_05_31_d1_gap4_closed.md

This file records the *reasoning* behind the Gap 4 close — the judgments most
likely to be re-litigated later if only the decisions (not the why) survive.

---

## 1. The O-14 reconciliation — what actually changed

We discovered last session that the build already contains a 50-rule suppression
system (S1–S50). Earlier in Gap 4 we had started writing D1's *own* "is this just
seasonal?" gate, not realising rule S44 already mandates exactly this — and
mandates it *per component*. O-14 was catching that overlap.

The fix: D1 stops computing seasonality and instead **reads the verdict the
S-series already produces**, component by component. Concretely the seasonal
step now consumes S44 (decompose D1 into CPM/return/COGS/discount/operational
before suppressing) → S38 (how much is "explained away" sets State 3/2/1) → S41
(that explanation decays over the event window).

**Why it matters beyond tidiness:** if D1 ran its own seasonal gate, it could
disagree with the rest of the system — D1 says "seasonal, ignore" while the
B-series fires "creative fatigue" on the same week. One shared, consumed
suppression state makes that contradiction structurally impossible. That is the
whole point of Sub-Decision 1.

Of the four named chain steps, only the seasonal step was a re-derivation. Step 4
(handoff) was already heading into S35 via O-13. Steps 1 (funnel split) and 3
(cross-channel) are genuinely D1-internal and stayed.

---

## 2. The S38 confusion the founder surfaced — and the real flaw under it

Founder question: "Over 85% explained → go silent. If more is explained, why go
*silent*?"

The trap is the word **explained**. It does NOT mean "we understand the problem."
It means **"explained away"** — accounted for by a known, boring, can't-do-
anything reason like Black Friday. So: mostly explained-away → quiet (harmless
known cause); mostly unexplained → loud (something real).

But the founder's instinct caught a genuine design flaw: **"explained" and
"harmless" are not the same thing.**
- A margin drop can be 90% explained AND a disaster (90% from returns on a
  defective batch — fully explained, must fire). This is exactly why per-component
  suppression (S44) exists: a harmless explanation for the CPM piece must not
  silence a real problem in the returns piece.
- A spike can be fully explained by Black Friday AND still actionable ("yes it's
  seasonal, but you're overspending into inflated ad prices — pull back"). The
  current model has no way to say "seasonal *and* do something."

We logged this second case ("explained ≠ can't act") as an open decision in
product_strategy.md Section 12, inherited by Gap 8. In D1 we kept a concrete
anchor: a State-3 seasonal CPM does NOT suppress the SKU-level spend-misallocation
finding. Full resolution waits for Gap 8 — we did not over-resolve it in Gap 4.

---

## 3. The schema gap — why it's a gate, not a queue item, and why we did NOT build it early

`suppression_log` records suppression by `alert_type` only. It has no column for
*which component*. So S44's "suppress per component" cannot actually be recorded
today — the decision is locked but the table to support it isn't built. The
ledger's "EXISTING-LOCKED" label conflated the decision with the schema.

Failure mode if ignored: during BFCM (highest-suppression week), D1 finds no
per-component slot, writes one whole-alert suppression, sees the CPM looks
seasonal, and **goes fully silent** — missing a defective-batch returns problem
underneath, during the exact week the product most needs to prove itself.

We considered building the column early. Rejected it, from two seats:
- **Architect:** nothing runs today that the column would help (we're in design
  review; no live D1). `suppression_log` is a *shared* table touched by all
  S-rules and every alert series; B/A/orchestration/H reviews could still change
  what it needs. Migrating now risks an amend/redo mid-review and doc drift — the
  exact "documentation compounds" failure mode already logged.
- **Founder:** the real need isn't seeing it built early, it's a *guarantee it
  can't be forgotten*. A test that fails the day someone validates D1 without the
  column is a harder guarantee than an early build against a design still in flux.

So: schema change stays BATCHED (post-H), but is promoted to a **go-live gate**
(d1_validation_gates.md, D1-G1) tied to the BFCM + AZ-KNIT-031 seed scenario. A
red test, not a sticky note. The latest responsible build moment (the
consolidated prompt) already sits before any validation run, so the discipline
doesn't endanger it.

---

## 4. Two conflicts we surfaced rather than papered over

- **F2 vs S44 precedence:** S35 says F2 (payment failure) suppresses *all* of D1.
  S44 says judge D1 per component — which implies F2 should suppress only the
  conversion component, leaving CPM and return-rate free. The F2 case is never
  worked in the S44 example. Unresolved → routed to O-5 (orchestration pass).
  Gap 4 closes WITH this documented; Step 0's F2 branch is not finalised.
- **Escalation vs stacking (O-18):** proposed resolution — a D1 escalation is
  subordinate to any S42 suppression stack and fires only once the stacked state
  decays (S41) to ≤ State 2. Consistent with S42; ratify the general question at
  the pass.

---

## 5. Plain-language glossary (so we don't re-derive it)

- **D1** — the "your margin shrank, here's why" alert (the one with 9 gaps).
- **CPM** — cost of ads (per 1,000 impressions). "CPM component" = the ad-cost
  slice of a margin problem.
- **B1 / B4** — "ads going stale" / "audience used up"; both also raise ad cost,
  so D1 must coordinate, not re-diagnose.
- **F2** — "checkout payments failing" (a root cause others sit downstream of).
- **States** — 1 = fire loud · 2 = fire with context + what's unexplained ·
  3 = stay quiet but log the innocent reason · 4 = quiet because data unreliable.
- **S-rules** — the 50-rule "when to stay quiet" book. S1 sale period, S2
  collection launch, S5 election, S10 back-to-school = the four seasonal CPM
  reasons. S35 = map of which alert is downstream of which. S38 = how-quiet rule
  (by % explained-away). S41 = explanations fade over time. S42 = what to do when
  several suppressions stack. S44 = break D1 into pieces and judge each piece
  separately.
- **A4** — reference table of how signals historically move together.
- **O-items** — numbered open questions in the orchestration to-do list (O-5,
  O-13, O-14, O-17, O-18 used this session).
- **Cluster N / Gap N** — organising headings, no deeper meaning.

---

## 6. File-hygiene decisions (and a correction to remember)

- New gate file is separate from the spec (cross-alert artifact; must be findable
  at ship time, not buried at line 2,000).
- Chat-context files are session logs and are NOT superseded; only **state** files
  get a "SUPERSEDED BY" pointer (one current state at a time).
- **Correction from the founder:** this project does NOT overwrite same-named
  uploads — a same-name file is added as a *separate* copy. So the superseded
  state file was **renamed** to `..._orchestration_SUPERSEDED.md`, and the
  original `..._orchestration.md` must be **manually deleted** from the project
  after upload. Going forward, never rely on same-name overwrite; rename or
  delete explicitly.
- Provenance note: a copy of the orchestration state file was found pre-staged in
  the working directory carrying a header not written this session. Unknown
  provenance, no instructions in it — not used as a source. The superseded file
  was rebuilt from the verified project content instead.

---

## 7. Where we are

Gap 4 closed (design-complete, blocked on gate D1-G1). Nothing here blocks Gap 5
(AOV decline driver), which is the next item.
