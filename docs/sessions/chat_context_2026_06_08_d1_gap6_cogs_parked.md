# Profit Sentinel — CHAT CONTEXT
## Session: 2026-06-08 (Gap 6 closeout → COGS PARKED)
## Pairs with: state_2026_06_08_d1_gap6_cogs_parked.md

---

## PURPOSE OF THIS FILE
Carries the PERSISTED PHASE-0 DECISION LEDGER (with verbatim source quotes from the conversation)
plus the reasoning arc, so the next session can audit this save as an independent second reader.
This matters because the save was self-verified without founder content review: the only real
guard against a misread/dropped decision is a fresh read checking this ledger against the files.

---

## PHASE-0 DECISION LEDGER (read from the conversation, each item anchored to its source)

| # | Decision | Status | Target file(s) | Source anchor (verbatim) |
|---|----------|--------|----------------|--------------------------|
| D-1 | O-24a new-vs-returning return split RETIRED — Stage 2 owns return-rate suppression; no actionable lever; prior-sale comparator too context-sensitive; composition → Horizon-2 digest | LOCKED (retired) | cross_alert O-24 + session log; agent_d Gap 6 row; state | Founder: "Yes i agree" (to the proposal to retire O-24a) |
| D-2 | "Recently-connected = thin history" reasoning RETIRED — full Shopify history on connection | LOCKED (retired) | state; context | Founder: "we are extracting historical data so it doesnt matter if the brand is 6 weeks old in our system or not we will have entire history of the brand" |
| D-3 | O-24b REFRAMED (day-count → cost-regime/versioned-COGS) + BLOCKED on COGS foundation | PARKED-OPEN (blocked) | cross_alert O-24; agent_d Gap 6 row; state | "O-24b cannot close until O-28 is worked" — founder agreed to park COGS first |
| D-4 | All-explained actionability gate + residual-band-cutoff brand-relativity BLOCKED on COGS | PARKED-OPEN (blocked) | cross_alert O-24; agent_d Gap 6 row; state | Founder: "Mark the all-explained gate and residual cutoffs explicitly as 'blocked on COGS foundation,' alongside O-24b. - Agreed" |
| D-5 | Test-data-constant verification CLOSED — verified clean (grep/view evidence) | LOCKED (closed) | cross_alert O-24 + session log; agent_d Gap 6 row; state | Founder: "Go for it"; evidence: grep hits = retired-S20 description + O-26 log only |
| D-6 | COGS elevated to OWN foundational section (O-28), PARKED, discovery-blocked; not authored into tech-arch | PARKED-OPEN (routed) | cross_alert O-28 (new); state; context | Founder: "I agree to the section"; "should we part it first and move to other gaps as COGS is a bigger part and definitely need some discovery discussions" |
| D-7 | Build sequence: D-series PARKED → C-series NEXT | LOCKED (routing) | cross_alert session log; state | Founder: "Does that mean we will move to C series and park D series?" → confirmed "Roughly yes" |
| D-8 | Gap 6 stays FORMALLY OPEN (1 closed-clean, 3 blocked); does not lock | LOCKED (status) | agent_d Gap 6 row; cross_alert; state | "Gap 6 as a whole does not lock until COGS resolves. No false 'Gap 6 done.'" — founder proceeded on this basis |
| D-9 | COGS open-spec captures provisional direction + the discovery unknown as OPEN QUESTIONS (not spec) | PARKED-OPEN (open Q) | cross_alert O-28; state; context | Founder: "should we plan to accommodate ... multiple files for different seasons and categories"; "this is my biggest concern, I am not able to connect to any of fashion founders" |
| D-10 | Verified Shopify facts recorded as FINDINGS | LOCKED (finding) | state; context | Search docs this session: line items freeze SKU/title/price/qty + survive deletion; cost field current-only / not in Order API; deleted-variant cost unrecoverable |

### Derived lists (per save_protocol Phase 0)
- **Check-4 retired-wording scan list** (from (iv) entries): "new-vs-existing return split ... DEFERRED to residual pass" (old Gap 6 row / old O-24 — must now read as RETIRED, not deferred); "residual pass IN PROGRESS" (must now read closed-this-pass where applicable); "Gap 6 remains WIP ... Closes when Gap 6 closes" (old O-14 tail — still acceptable as WIP but superseded by the parked framing; left intact in O-14 since that row is not in this session's edit scope — FLAGGED for O-26).
- **Check-8 mirror list** (from (iii) entries): Gap 6 status appears in BOTH agent_d (Gap 6 row) AND cross_alert (O-24 + session log) — both updated. O-28 lives canonically in cross_alert; referenced (not duplicated) in state. D→C sequence in cross_alert session log + state next-session block.

---

## REASONING ARC (why each decision landed where it did)

**O-24a retirement.** The split tells you *who* returns, not *whether* the level is abnormal —
Stage 2 already decides suppression/narration of the return-rate component. The split can neither
override a Stage 2 fire nor trigger a suppression Stage 2 didn't apply, so it only adds narration
with no lever. The prior-sale comparator fails because each sale differs (pricing depth, quality,
delivery, competition, design novelty). Founder's instinct ("weekly blurb not an alert") was right;
formalised as Horizon-2 digest.

**The COGS escalation.** Started as a thin-baseline confidence sub-item. Unfolded across the
session into a foundational finding: a profit product must compute historical profit, but Shopify
does not expose historical/at-sale cost, and deleted-variant cost is unrecoverable. Crucially,
SKU string + price survive on the frozen order line, so revenue-side baselines (marketing, returns,
Klaviyo) are intact — the damage is confined to per-SKU margin. So the product CAN compute
historical profit for the costable share of revenue, via a SKU-string-joined versioned/season-regime
founder cost record, with mandatory coverage disclosure and component-only fallback. The single
unresolved variable — what fraction of founders can supply usable versioned cost — is irreducibly
discovery-dependent, which is why O-28 is parked, not designed.

**Why park rather than push.** Designing the COGS schema now means committing to a guessed
reconstruction rate; designing it after even a few founder conversations means committing to
evidence. The cost of waiting is low (revenue-side C-series work fills the gap and is higher in
Blueprint priority); the cost of guessing wrong is schema rework post-build. That asymmetry says
park COGS specifically and keep the COGS-independent work moving regardless of whether discovery
materialises.

**Why C-series, not "tidy D1 first."** Two of the three remaining Gap 6 items (all-explained gate,
residual cutoffs) operate on the margin residual and are themselves COGS-dependent — they cannot be
"tidied" closed without the input being deferred. Forcing them now bakes an assumption into a closed
item (invisible later) instead of leaving a visible blocked flag. So jump to C; leave D1 parked at an
honest, flagged boundary.

---

## METHOD NOTE (how this save was verified)
- Phase-0 ledger built by reading the conversation with source quotes (verification against source,
  not recall), then a second file-by-file derivation pass ("what in this session changes THIS file?").
  Repetition of the same read was explicitly rejected as non-independent; source-quoting + the
  persisted ledger for the next session are the real guards.
- Mechanical checks (counts, presence, scoped diff, anchors) run with raw tooling — see state file
  sanity handles and the save report in-chat.
- **Self-verified without founder content review** — next session is the independent second reader;
  re-check this ledger against the four touched files.

## FILES TOUCHED THIS SESSION
- UPDATED (full-file, in-place edits): agent_d_build_spec.md (Gap 6 row), cross_alert_orchestration.md
  (O-24 rewrite, O-28 added, session-log entry, header changelog).
- ADDED: state_2026_06_08_d1_gap6_cogs_parked.md, chat_context_2026_06_08_d1_gap6_cogs_parked.md.
- DELIBERATELY UNTOUCHED: technical_architecture.md, product_strategy.md, pre_agent_build_checklist.md,
  d1_validation_gates.md (COGS parked-open, not designed), and all locked seed/gap files.
