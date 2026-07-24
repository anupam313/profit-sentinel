# Pilot Readiness Register

**Purpose:** The single durable tracker of everything that must happen before the DTC Prism pilot goes live — the work that is *not* a documentation fix. Documentation reconciliation (the doc-sync) is complete; this file carries the remaining build, decision, and first-connect work.

**Status:** Created 2026-07-02 at the close of the canonical-doc reconciliation (doc-sync). Five canonical files edited/committed (`pilot_scope` 33d337f, `product_strategy` d695453, `cross_alert_orchestration` 09834fd, `technical_architecture` 5a6bd3d); four verified no-edit/clean (`pre_agent_build_checklist`, `d1_validation_gates`, `agent_d_build_spec`, plus `save_protocol` + `CLAUDE.md` clean by nature).

**This is a tracking artifact, not a canonical spec.** It records *what work remains*, not *what the product is*. No line-count handle, no full save-protocol — it is maintained like the state files in `docs/sessions/`.

**Line-citation caveat:** file:line pointers below were captured during the doc-sync's collection phase. `product_strategy.md` citations predate the doc-sync edits and are shifted by roughly **+12 lines** in the current committed file (the C8 §3D block, the C8 summary row, and the §5 lead paragraph all added lines above ~:1365). `cross_alert_orchestration.md:650` is accurate (that file had count-only edits, no line shift). Verify against the current committed file before relying on any `ps:` line number.

**Freshness tags:** items whose status depends on another file's content carry an inline *(checked-against: <file> · <date>)* tag. Today's sessions found two register notes stale against the files they summarised; a date marker would have caught both.

---

## THE BINDING CONSTRAINT (read first)

Recruiting **4–5 design partners** is the true launch gate (pilot_scope.md §8). All architectural and build work below has no value until real brand data connects. Design-partner recruitment runs as an independent parallel track from day one. Everything in this register serves getting a real brand connected and the pilot alerts firing correctly on their data.

---

## OPEN QUESTIONS (undecided — do not close without evidence)

- **OQ-1 — C8 abnormality rule + series-fit.** C8's detection rule (what counts as "return rate abnormally high for that product") is PROVISIONAL and explicitly non-canonical. OP-1 (2026-06-19) resolved the grouping grain only, not the abnormality threshold. Series-fit (C8 in Group C) is an inference — revisit if C8 turns out to be attribution-driven rather than returns-driven. *(Refs: buildstate_c8:103-104; c3-foundation:240-241.)* **No canonical home — this register is its only home.** The C8 abnormality rule is the SHARED detection rule for C3 — one method serves both (see BT-12 and pilot_scope §4 C3).
- **OQ-2 — Blended-marketing coverage-disclosure design.** The rule is locked (every channel the brand runs is named; unconnected ≠ zero; coverage disclosed). The *design* of how disclosure is surfaced to the founder is open. *(Point 3D.)* **No canonical home.**
- **OQ-3 — Weekly-digest cadence.** Weekly digest confirmed as pilot scope. The cadence-gating design (when/how it fires) is open, and there's a canonical-vs-Horizon-2 framing to resolve. *(prepilot-hardening:167-170.)*
- **OQ-4 — E5/E6 canon reconciliation.** E5/E6 exist in seed files but §3D lists only E1–E4; reconcile which is canonical. *(ps:~1377 post-edit.)*
- **OQ-5 — 3-namespace alert-numbering collision.** Three unrelated things share "A1/A2/…" labels: §3D alert IDs, `gap_abc_decisions.md` seed-design labels, and `seed_decisions` S1–S50/E-series. A future "check A6" is ambiguous across all three. **Canonical analysis lives at `cross_alert_orchestration.md:650` (P2-FINDING 5)**, which documents all three namespaces and recommends a naming convention (ALERT-A6 vs DEC-A6 vs S-rule). Confirmed still open (doc-integrity, not stale) — deliberately left untouched in the doc-sync. *(checked-against: cross_alert_orchestration.md · 2026-07-24)*
- **OQ-8 — Small causal-graph completeness.** Is each pilot symptom's root cause present in the causal graph before Agent B runs? **HIGHEST-RISK open item; no file mention anywhere — this register is its only home.**
- **OQ-9 — Delivery-loop mechanism.** The mechanism that gets an alert from the system to the founder is undesigned. **No canonical home.**
- **OQ-10 — Alert-count reconciliation.** Documents reconciled at 59 (2026-07-02 doc-sync, all current sites; the "58" in the product_strategy changelog is preserved history). Only the CODE (57) needs to catch up. (Delivery surface for pilot = email, decided.) *(checked-against: product_strategy.md · 2026-07-24)*
- **OQ-12 — Delivery-surface FINAL-PRODUCT decision (post-pilot).** Pilot uses EMAIL (confirmed, committed in pilot_scope). But `technical_architecture.md`'s full-product architecture is Slack-native: schema columns `slack_thread_ts`/`slack_channel` (NOT NULL), Slack Bolt data flow (:35), "founder never leaves Slack" surface (:48), Agent D posts to Slack (:814), Slack bot build steps. This was left untouched in the doc-sync (26 Slack refs intact) — it is NOT a find-replace. **After the pilot, decide on email's performance whether the final product stays email or moves to Slack.** If Slack: architecture already built. If email: the tech-arch delivery layer (schema + Agent D formatting + interaction model) needs a real redesign — schema-and-agent-deep, not a doc edit. Do not resolve until the pilot delivers evidence. *(Founder confirmed 2026-07-02: "trying email in pilot, decide email-vs-Slack for final product based on pilot experience.")* This is the delivery half of the former DH-1.
- **OQ-13 — Graduation rule (when an alert stops needing the human gate).** OPEN. The per-alert threshold that licenses removing the relevance gate (pilot_scope §2, column (b)) is undecided. The reviewer verdict MUST be LOGGED FROM THE FIRST ALERT even though the threshold is undecided — it cannot be reconstructed later. **No canonical home — this register is its only home.**
- **OQ-14 — Weekly-digest CONTENT (which numbers belong on the one page).** OPEN. OQ-3 covers digest CADENCE (when/how it fires); nothing covers CONTENT. The three items named in pilot_scope §4 (blended post-return ROAS, serial-offenders list, return-rate + reason table) are INDICATIVE, not final — the onboarding copy deliberately says "things like" for this reason. Settle before pilot launch. **No canonical home — this register is its only home.**

*Resolved & moved out: OQ-6 → BT-8; OQ-7 → BT-9; OQ-11 → "Checkout Error Spike" (Payment Gateway Failure = a cause node inside F2); delivery surface (pilot) → email.*

---

## BUILD TASKS (before a real brand connects, unless noted)

- **BT-1 — Blended-marketing math.** Add `google_spend` to `total_ad_spend` and all blended figures; build `stg_google_ads`, `google_roas`, `google_attributed_orders`; add the connected-channel registry + missing-vs-zero logic + coverage disclosure. Fixes A1/D1/A2/A5 at once.
- **BT-2 — C8 detection.** Add the C8 chain to `causal_graph.py` + wire Agent-A detection (`return_rate_pct` is not scanned today).
- **BT-3 — E5 chain + Agent B wiring.** Add the missing E5 chain to `causal_graph.py` (code 57→58); wire the orphaned causal_graph into Agent B (gated on E5).
- **BT-4 — Wire remaining pilot alerts into Agent A:** C6, G1, C2 (only C1 is scanned today; C8 wiring = BT-2).
- **BT-5 — [PARKED pre-pilot] Onboarding questionnaire.** COGS 3-option → 4-tier questionnaire remains parked. (ROAS opt-out field DROPPED per the display decision: ROAS always shown gross and net-of-returns, no founder toggle.) Pulled OUT of this parked item 2026-07-24: CD-10 per-client C1 calibration is a connect-day action (tracked at FC-3, not restated here); D-20 pending-connectors is PROMOTED to BT-14 below (vanish-risk — must not stay parked).
- **BT-6 — Debt / plumbing.** Parser per-brand accuracy gate (D-GAP6-21 / D1-G12); the `agent_a` hardcoded-55% margin (verify locus); GA4 `stg_ga4_pages`/`devices` (mart TODOs); Pass-Two SKU-contract validator (in R11).
- **BT-7 — TikTok catalog-report wiring** for C8 product-level spend + add an `is_synthetic` guard on the TikTok mart branch. *(mart:552-556.)*
- **BT-8 — [PILOT] Category cross-check.** Shopify-assigned category vs LLM category; flag disagreements (disagreement-handling is itself a design item). Pilot-critical — grouping correctness underpins C6/C8/C2.
- **BT-9 — Parser + labelling PROCESS finalized before pilot** (validation of the labels on real data is a first-connect action, FC-7).
- **BT-10 — A2 per-channel root-cause detection.** Build the four-cause decomposition (CPM inflation / creative fatigue / checkout errors / SKU return outlier) to run PER AD CHANNEL (Meta/Google/TikTok), with channel-attribution-confidence handling — name the channel it is confident about, flag ambiguity rather than forcing a single-channel verdict. *(Origin: A2 made multi-channel in the product_strategy §3D doc-sync commit; the §3D spec states multi-channel intent but detection is Meta-only in code.)*
- **BT-11 — C8 lineage note in code.** Add the A2→C8 retirement lineage note to A2's `causal_graph.py` entry (per buildstate_c8 2026-06-18). The product_strategy §3D C8 Note now points to `causal_graph.py` as the lineage home, so the code note must actually exist for that pointer to resolve. *(Origin: Flag-2 fix in the product_strategy doc-sync commit.)*
- **BT-12 — C3 detection wiring.** Per the 2026-06-03 resolution (`agent_d_build_spec.md:2510`): (a) wire C3 to the SAME per-category baseline D1 uses (S15) so C3 and D1 share one computation — C3's stated method does not reference S15 today (only D1 is wired to it, per :2500); and (b) decide C3's shared thin-history fallback: exposure test (D1's method, can still act) vs 90-day monitor-and-wait (C3's seeded method, waits) — a real design fork per :2506. The doc part (headline) is already done (product_strategy C3 "2×" neutralized); the S15 wiring + fallback decision are the build/design remainder. C-series detection, adjacent to BT-2 (C8). [DECIDED 2026-07-24: the thin-history fork resolves to ACT on the weaker signal with an explicit seasonality caveat, NOT 90-day monitor-and-wait — matches the documented narrate-don't-suppress posture. The shared-baseline (S15) wiring remains open.] *(checked-against: agent_d_build_spec.md · 2026-07-24)*
- **BT-13 — Human relevance gate + email delivery loop (ONE merged build: compose → hold → verdict → send).** Holding state (alert composed, not yet released); reviewer verdict field; three exits (send / reject-as-wrong / suppress-as-stale); one-day turnaround tracking; intraday FAST LANE for G1; a review-queue surface for Anupam; the founder action endpoint for Agree/Snooze/Disagree from email. CONSTRAINTS: (i) alert_log ALREADY carries the founder-outcome half (action_taken, action_taken_at, dismissal_reason, outcome_value_7d/14d) — build only the missing REVIEWER half; (ii) do NOT reuse the name "practitioner_approved" — that belongs to causal-chain promotion, a different mechanism. DESIGN NOTE: email security scanners and inbox prefetchers auto-click links, so the action link must land on a confirmation page with a button (two-step) and never write to the DB on the raw click. (Builds the delivery mechanism OQ-9 flags as undesigned.) DIGESTS: the gate and delivery loop also cover weekly digests — a digest is composed, held, reviewed and released through the SAME compose → hold → verdict → send path. Not identical to alerts: a digest has no Agree/Snooze/Disagree founder response and no intraday fast lane.
- **BT-14 — [PROMOTED from BT-5, 2026-07-24] D-20 pending-connectors onboarding question.** "Are you planning to connect any additional sources in the next 90 days?" — writes client_config.pending_connectors (text[]) + pending_connectors_noted_at; the monthly incremental scan re-runs scan_skipped_reason chains when a pending connector activates. On the HIGHEST VANISH-RISK list; full spec at pre_agent_build_checklist D-20 (pending connectors, ~line 189). Must not be lost.

---

## FIRST-CONNECT ACTIONS (the day the first brand connects)

- **FC-1 — Build `validate_sync.py`** (R10) — founder-ruled first-connect; reword D-F(2).
- **FC-2 — Repoint C8/returns to Shopify-native** (J-1) + prove native ingestion. *(tech-arch:1461-1463; D-D.)*
- **FC-3 — C1 recalibration** (CD-10; manual p90 interim).
- **FC-4 — Persistent paid Supabase + keep-alive.**
- **FC-5 — Start connector access for ALL platforms, prioritized by lead time:**
  - First (long lead, start today): Shopify CUSTOM DISTRIBUTION + OAuth (read_all_orders approval is the long-lead item; protected-data review NOT required — aligns with pilot_scope §6, which has pilot precedence); Google Ads developer token. *(checked-against: pilot_scope.md · 2026-07-24)*
  - Second (pilot-fired, now): Meta API; Gorgias API key; Loop Returns API key.
  - Third (soon after): TikTok API; Klaviyo API key; Sentry (only brands that have it).
  - Plus (long-lead, non-connector): entity registration.
- **FC-6 — [promoted from CD-2] Build the brand's event calendar from their own history** (engine is design-only, unbuilt); fix `historical_pattern_scan.py` stale "zero rows" comments (lines 31, 621-624, 811, 1238).
- **FC-7 — Validate parser labels on REAL brand data** (pairs with BT-9).

---

## PRE-PILOT GATE

- **PG-1 — D-F 7-condition HARD gate** → `state_2026-06-23_prepilot-hardening.md:172-180`. Not yet canonical.
  - Status: (1) DONE · (2) REWORD-per-ruling · (3) DONE · (4) PARTIAL · (5) OPEN · (6) OPEN · (7) OPEN.
  - Commitments: stays a hard gate; documented here; DEEP REVIEW of all 7 conditions before pilot.

---

## HOUSEKEEPING

- **HK-1 — Untracked/uncommitted working tree.** 6 untracked continuity files + `slack_bot/` untracked (now stale since delivery = email — flag, don't delete); `seed_meta.py` + `onboarding_flow.py` modified-uncommitted.
- **HK-2 — OneDrive/.git corruption risk** (accepted; the repo is the source of truth).
- **HK-3 — [CLOSED]** stale roster counts 41/56/37 — folded into the doc-sync count fix (CAO-1 + PAC-1 resolved).
- **HK-4 — Founder runs all commits and pushes** (through Claude Code; explicit-path staging only).
- **HK-5 — [watch during pilot] Cold-start visibility gap.** Removing the query feature from the pilot (now post-pilot, product_strategy §3C) means the product may be invisible to the founder between connect and first alert. The connect-day email is the chosen mitigation. An observation to MONITOR during the pilot — not an open question. Source: rationale preserved in product_strategy §3C.

---

## DOC-HYGIENE

- **DH-1 — [RESOLVED 2026-07-02] Stale charter / onboarding-brief.** The pasted IDENTITY brief described the pre-pivot product (old five alerts / Slack / $299 / 20 clients / a non-existent `seed_design_decisions.md`). **Resolution:** its stale FACTS are now explicitly marked superseded, item-by-item with committed sources, in `charter_facts_superseded_2026-07-02.md`. The charter's STANCE and PROTOCOLS remain fully in force. Two embedded scope questions were flagged for founder ruling (see that record: the "20 beta clients" milestone, and adopting a corrected charter to stop re-injection). **Follow-on [CLOSED 2026-07-24]:** the Blueprint staleness check is done — `Profit_Sentinel_Blueprint_v9.docx` exists and is reconciled (July 2026) with an explicit pilot-vs-post-pilot scope box, the five-alert pilot set named, and pricing marked indicative. Closure recorded in charter_facts_superseded_2026-07-02.md. *(checked-against: charter_facts_superseded_2026-07-02.md · 2026-07-24)*

---

## CONDITIONAL (re-surface only if deferred work is pulled forward)

- **CD-1 — Segment-boundary calibration** (E-series/segments, Phase-2).
- **CD-3 — Klaviyo 0.65 open-rate default at onboarding** (Klaviyo/E-series, Phase-2).
- *(CD-2 promoted to FC-6.)*
- **CD-4 — [PARKED until code pass] Confirm Agent D output can be cleanly intercepted before sending.** The compose → hold → verdict → send loop (BT-13) assumes Agent D's output can be held before delivery; verify in the codebase. Park until the code pass.

---

## HIGHEST VANISH-RISK (this register is their only home)

These have **no canonical home** anywhere else — if they leave this register, they are lost: **OQ-2, OQ-8, OQ-9, OQ-1** (abnormality method), **OQ-13** (graduation rule), **OQ-14** (digest content), **D-20** (now BT-14), **PG-1** (the whole D-F gate). DH-1 was in this set; it is now resolved.
