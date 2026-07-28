# STATE — Pilot Readiness (snapshot)
**As of:** 2026-07-27 · **Repo HEAD:** `0a4031c` (origin/master, in sync)
**Companion:** `chat_context_2026-07-27_pilot_readiness_docsync.md` (the narrative).
State = where things stand. Context = how we got here.

---

## REPO STATUS
- Branch `master` == `origin/master` == `0a4031c`. Clean, in sync.
- Ten commits this session: `a22ac8d` · `6472dd1` · `b9f0879` · `d1d84a1` · `b59c7b7` · `63a03f1` · `7179eb3` · `f8d451f` · `0a4031c` (+ precondition). All pushed.
- Uncommitted working-tree changes exist and are KNOWN (HK-1): `seed_meta.py`, `onboarding_flow.py`, connector probe scripts, `slack_bot/`, session files. Not touched by any batch. Inventory them (read-only) before next code work; flag `slack_bot/` (stale, email pivot) — do not delete.

## CANONICAL FILES (committed, current)
- `pilot_scope.md` (137 lines) · `product_strategy.md` (1440) · `pilot_readiness_register.md` (116) · `operating_charter.md` (308) · `pre_agent_build_checklist.md` (389) · `charter_facts_superseded_2026-07-02.md` (60) · `technical_architecture.md` (3999) · `Profit_Sentinel_Blueprint_v9.docx` (plain text w/ .docx ext — reconciled July 2026, NOT stale).
- Project mount `/mnt/project/` is UNTRUSTED (proved stale this session). HEAD / uploaded live text is authoritative.

## WORKING ARTIFACTS (NOT in repo — personal)
- `pilot_readiness_24072026.xlsx` — 3 sheets, regenerate from the register when it changes.
- `DTC_Prism_Outreach_Tracker.xlsx` — see the outreach state file.

## BUILD STATE — WHERE IT ACTUALLY STANDS
- Agents A–D EXIST (data flow ends at "Agents Query Marts"). Marts, seed scripts, RLS, synthetic data all built. Register tasks are WIRING, not build-from-scratch.
- **Only C1 is scanned today.** Return rate is not scanned at all. C8/C6/G1/C2 not wired into Agent A. The causal graph is written but NOT connected to Agent B (orphaned).
- **23 of 32 items need no design partner / no real data (Block A).** 6 need first connect (Block B). 3 are during/after pilot (Block C). The A/B/C split is committed fact (register section headings).

## THE FIVE PILOT ALERTS
C8 Return-Driver (WEDGE) · C1 Sizing-Complaint Velocity · C6 High-Return New Collection · G1 Stockout During Active Spend · C2 Influencer ROI After Returns. (Full defs in the context file §8.)

## C8 ABNORMALITY RULE (OQ-1) — the most-blocking item
- **METHOD DECIDED** (2026-06-10; grouping gate closed 2026-06-19). Seven mechanisms: ABNORMAL (own-band percentiles), TRUST GATE (pessimistic-end fires; sales value never waives), MATERIALITY (behind trust gate), SIZE on sales value not cost, TRAJECTORY (rate curve not count), NEW PRODUCTS (silent watch), CONCENTRATION.
- **OPEN = 4 dials only** (calibration): percentiles, confidence width, absolute floor, materiality bar. Propose now on test data, confirm at connect.
- **CONFIRMATION PASS OWED** — un-provisionalise the ~12 grouping-dependent 2026-06-10 decisions against the locked grouping set. RECOMMENDED NEXT. Thinking task, in chat, hours.
- Shared rule with C3.

## KEY LOCKED FACTS (this session)
- Pilot surface = EMAIL ONLY. Shopify app = data connection only. NLQ = post-pilot.
- **Everything generated passes the human gate; nothing auto-sends.** Covers alerts, digests, onboarding completion message, data-quality notification.
- Shopify: CUSTOM DISTRIBUTION (no PCD review, no App Store review); `read_all_orders` is the critical-path approval; PCD *requirements* still apply. Meta/Google/TikTok via Airbyte Cloud managed OAuth (no own app at pilot scale).
- C3 = Phase 2, shares C8 rule, thin-history = fire-with-caveat.
- BT-5 questionnaire PARKED; FC-3 (C1 calibration) + BT-14 (pending-connectors Q) pulled out.
- Gorgias: parse ticket TEXT not tags (parser PENDING; tag-coverage gate needs rethink when parser lands).
- Blueprint v9 reconciled, NOT stale. Alert count: docs 59, code 57 (code to catch up). "20 beta clients" NOT a hard target.
- Seasonal mechanism = seasonal baseline (D6) + brand event calendar (FC-6); no 12-month elapsed-time dependency anywhere.

## OPEN QUESTIONS STILL LIVE
OQ-1 (4 dials + confirmation pass) · OQ-2 (coverage-disclosure design) · OQ-3 (digest cadence) · OQ-8 (causal-graph completeness — HIGHEST RISK) · OQ-10 (code alert count) · OQ-12 (final surface email vs Slack) · OQ-13 (graduation rule) · OQ-14 (digest content) · product identity (returns-focused vs 59-signal platform).
HIGHEST VANISH-RISK list (register only home): OQ-1, OQ-2, OQ-8, OQ-9, OQ-13, OQ-14, D-20(→BT-14), PG-1.

## NEXT ACTIONS (priority order)
1. **C8 confirmation pass** — next session, fresh head, in chat. (Setup prompt offered.)
2. Any Block A item (e.g. BT-8 category cross-check, BT-1 blended-marketing).
3. Recruitment — the binding gate (outreach state file).
4. Standing: refresh the live Project instruction from committed `operating_charter.md` whenever the charter changes.

## STANDING DISCIPLINE
Two-agent split (Claude authors + reviews; Claude Code edits/commits/pushes; founder authorises each). Locate by quoted text. HK-6 straight quotes. Mount untrusted → verify against file not summary. Continuity files authored in chat, Claude Code verifies only.
