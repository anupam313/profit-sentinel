# Chat Context — Pilot Readiness & Canonical-Doc Updates
**Date of session:** 2026-07-27 (work/commit dates referenced within are 2026-07-24)
**Topic 2 of 2** from a long combined session. The other file covers outreach.
**Authoring rule:** written in the chat interface from a full read of the conversation. Claude Code never authors continuity files — verification only.

---

## 1. WHAT THIS SESSION DID

Reconciled the pilot-readiness plan against the committed repo, then made a disciplined multi-batch set of edits to the canonical docs through Claude Code, and rebuilt the readiness spreadsheet. **Ten commits, all pushed to origin/master, all in sync. Final HEAD: `0a4031c`.**

**The load-bearing finding:** the founder believed he was blocked ("without data I can't build the causal graph, the product is stuck"). The committed register contradicts this — **23 of 32 work items need no design partner and no real brand data.** Four of five pilot alerts have no detection wired; the causal graph isn't connected to the explanation agent; the highest-risk open item is a graph-completeness question synthetic data can answer. The outreach-or-build dilemma was false.

---

## 2. THE WORKING METHOD (proven this session — keep using it)

**Two-agent split, never both authoring:**
- **Claude (chat)** authors change-lists + prompts, and REVIEWS Claude Code's output against pre-edit baselines uploaded to chat. Authors continuity files.
- **Claude Code** edits, runs mechanical checks, commits, pushes — under hard-stop gates. Never authors continuity files (verification only).
- **Founder** authorises every commit AND every push (single-use, explicit; never autonomous). Pushes go through Claude Code (June "no push" note is superseded).

**Per-batch discipline:** Step 0 handles (line count + sha256 at HEAD and working tree, flag dirty — Claude Code CANNOT see `/mnt/project/`, so it reports handles and the comparison is external) → ledger + manifest → **HARD STOP #1** for external review → edit one file at a time with scoped diff, declared line delta (±3 tripwire), anchor counts, retired-wording scan, semantic read-back → cross-file check → landing reconciliation → **HARD STOP #2** before any stage/commit → founder authorises commit → then push.

**Locate edits by QUOTED TEXT, never line number** (the mount can be stale). If an anchor is missing or non-unique, STOP.

**HK-6 straight-quote guard:** this file family uses STRAIGHT quotes only. Editors auto-format straight→curly and regenerated copies drift curly→straight; both happened this session. Silent quote drift breaks exact-text matching → false "not found". Guard runs on staged content every batch.

**MOUNT IS UNTRUSTED.** `/mnt/project/` proved stale this session (charter was 20 lines behind HEAD). Reason from HEAD / uploaded live text. When a register NOTE and an actual FILE disagree, the FILE wins — two stale register notes caused the first-half errors today. **Verify against the file, never a summary.**

---

## 3. THE TEN COMMITS (all on origin/master, in sync)

- `a22ac8d` — precondition: uncommitted 3-July charter work (Blueprint v8→v9 pointer + reconciliation note).
- `6472dd1` — **Batch 1:** seed-decisions filename pointer fix (`seed_decisions_gap_a_b_c.md` → `gap_abc_decisions.md`, the real on-disk name) + dated corrections.
- `b9f0879` — **Batch 1b:** closed scope-question #5 — "20 beta clients" is NOT a hard target anywhere; binding gate = 4–5 design partners.
- `d1d84a1` — **Batch 2:** NLQ (natural-language query) moved post-pilot; pilot surface = EMAIL ONLY (Shopify app kept as data connection only); Shopify approval path corrected (see §4); C3 added as Phase 2; §3C re-scoped post-pilot (preserved in full incl. cold-start rationale); onboarding copy rewritten; register gained BT-13 (merged gate+email loop), BT-14 (D-20 promoted out of parked BT-5), HK-5 (cold-start watch), freshness-tag convention; charter Gorgias→parse-text pointer + seasonality→pilot-mechanism.
- `b59c7b7` — **Batch 2b:** onboarding completion copy finalised (plain language, no timing promise, no internal names).
- `63a03f1` — **Batch 2c:** gate covers weekly digests too; OQ-13 (graduation rule) + OQ-14 (digest content) added, both on the vanish-risk list.
- `7179eb3` — **Batch 2d:** gate rule restated as **EVERYTHING GENERATED** passes the human gate (nothing auto-sends); caught two uncovered outputs — the onboarding completion message (was "Delivered in Slack", auto-sent on script completion) and the below-60%-confidence data-quality notification; §13 Slack principle annotated not rewritten; HK-6 straight-quote guard added.
- `f8d451f` — **Batch 2e:** added the gate rule to `operating_charter.md` (new paragraph in the PILOT ALERTS section, citing pilot_scope §1–2).
- `0a4031c` — **Batch 4:** rewrote OQ-1 to separate DECIDED from OPEN (see §6); added BT-15 (Evidence Stack assembly) + PG-2 (legal counsel pass).

(There is no "Batch 3" commit — Batch 3 = retire the map + rebuild the spreadsheet, which touched no repo file. See §7.)

---

## 4. THE SHOPIFY APPROVAL CORRECTION (verified against Shopify's own docs)

**Earlier belief (WRONG):** protected-customer-data (PCD) review is on the critical path.
**Verified truth:** Shopify's own documentation shows **custom apps get PCD Level 1 & 2 access automatically; only PUBLIC apps require PCD review.**
- Use **custom distribution** for the pilot (private install link to 4–5 known stores; no App Store review; no PCD review; no Shopify-billing requirement). Build the public app later only if going to market on the App Store.
- The **real critical-path approval is `read_all_orders`** (permission to read orders older than 60 days) — requested in the Partner Dashboard, Shopify-approved. Needed because the seasonal baseline + parser want 12+ months of history; 60 days is nowhere near.
- **PCD *requirements* still apply regardless** (encryption in transit/at rest, encrypted backups, test/prod separation, retention limits, staff access limits, access logging, incident-response policy, **merchant data agreement**).
- Meta/Google/TikTok at pilot scale: route through **Airbyte Cloud managed OAuth — no own Meta app needed** (avoids Meta app review + business verification's chicken-and-egg). This is the committed architecture (`pilot_scope §6`).
- One 2-week-old developer report: custom-distribution apps in the new Dev Dashboard can still hit an "Order object not approved" error with read_orders declared — expect some Partner-Dashboard fiddling. Worth a 10-min test on a dev store before relying on the timeline.

---

## 5. KEY DECISIONS MADE THIS SESSION (founder rulings)

- **Delivery = EMAIL ONLY** for the pilot. Shopify app kept purely as the **data connection** (OAuth/sync), not a founder-facing screen. NLQ (query feature) → post-pilot. (Final-product surface email-vs-Slack stays open = OQ-12; `technical_architecture.md` stays Slack-native by design pending that call.)
- **Everything generated passes the human relevance gate during the pilot** — alerts, weekly digests, onboarding completion message, data-quality notification, and anything added later. **Nothing auto-sends.** The gate is a relevance/release check on automated output, NOT manual analysis (the founder computes nothing by hand). Stated in pilot_scope §1–2, register BT-13, and charter.
- **Onboarding completion message** is generated (per-brand dollar figures) → **must pass the gate**; delivered by email, not Slack; is NOT a static message for gate purposes. It fires once per brand and is the first thing a design partner reads.
- **Weekly digest:** no connect-day send (would pressure same-day review + can't guarantee it through the gate). Just "weekly." Content is INDICATIVE ("things like…") pending OQ-14. First-digest-at-connect wording (added in d1d84a1) was deliberately removed in 2c — the cold-start gap it addressed is already covered by the completion message.
- **C3** → Phase 2 (was undispositioned). It shares the C8 abnormality rule (decide once, apply to both). Thin-history behaviour DECIDED: fire with an explicit seasonality caveat, not 90-day monitor-and-wait (matches narrate-don't-suppress).
- **Onboarding questionnaire (BT-5)** stays PARKED — but the per-brand C1 threshold calibration (now FC-3) and the pending-connectors question (now BT-14) were pulled OUT so they aren't parked with it.
- **"20 beta clients"** is NOT a hard target anywhere. Gate = 4–5 design partners.
- **Blueprint v9** is reconciled (July 2026) — pilot-vs-vision marked explicitly; NOT stale. **This reversed an earlier wrong flag** (the register's "not checked" note referred to v8 and predated v9). Lesson: summaries go stale faster than the files they summarise — open the file.
- **Precision Profit Calendar / seasonality:** the four algorithms (launch, sale-period, return-window, creative-fatigue detection) **run on existing data** — "6–12 months" is a data-availability + switching-cost point, NOT a waiting period or a month-6 gate. Three of four are day-one computable from history. The pilot mechanism is the **seasonal baseline (D6) + brand event calendar (FC-6)**. No 12-month elapsed-time dependency exists anywhere in the pilot. (The one real constraint: comparing this July to last July needs 12 months of the brand's OWN history — a fact about the brand, not a wait. Founder chose NOT to make this a recruitment screen.)
- **Gorgias/C1:** committed direction is **parse ticket TEXT, not trust tags** (tags unreliable at this brand size, worst during sales). Parser is PENDING BUILD. WATCH: the current data-quality gate keys on tag coverage (<50% skips) — once the parser reads text, that gate would silently skip exactly the brands the parser exists to rescue. Needs rethinking when the parser lands.
- **Label collision** (A1/A2/A6 mean different things in the alert library vs seed-decision files vs numbered rules) — left PARKED deliberately, out of the readiness map. Low severity; disambiguate by naming the file when it comes up.
- **Alert count:** documents reconciled to **59**; only the CODE (57) needs to catch up (small task). The "58" in the product_strategy changelog is preserved history, not a live contradiction.

---

## 6. THE C8 ABNORMALITY RULE — STATUS (register OQ-1, rewritten in Batch 4)

The single most-blocking item. **The METHOD is fully specified; only the NUMBERS are open — a four-dial calibration job, not an unstarted design problem.**

**DECIDED** (agreed 2026-06-10 in `state_2026_06_10_c3_foundation_abnormal_bigenough_new.md`, tagged provisional-pending-grouping; the grouping question that gated them CLOSED 2026-06-19 in `state_2026-06-19_op1-close-last.md`) — seven interlocking mechanisms:
1. **ABNORMAL** = rate clearly above the group's OWN robust band, built from mid-range percentiles, NOT mean/SD.
2. **TRUST GATE** = confidence band around observed rate; fires only if the pessimistic end still sits above normal (does abnormality + data-sufficiency + maturity at once; thin data fails on its own); an absolute floor beneath it; **sales value never waives it.**
3. **MATERIALITY** = return volume OR returned-order sales value crosses a brand-relative bar; sits BEHIND the trust gate; size alone never fires.
4. **SIZE on sales value, not cost** — no cost dependency ever for this alert.
5. **TRAJECTORY** = a cohort return-RATE curve (never a raw count — counts are polluted by promo timing); behind the size gate.
6. **NEW PRODUCTS** = silent watch, no alert, until a history-free signal crosses the size bar, then an honestly-worded "new, no normal yet" alert.
7. **CONCENTRATION** inside the group is load-bearing — a group average can look fine while one or two products drive everything.

**RETIRED — do not resurrect:** separate period bands for sale/non-sale; comparing a sale to prior comparable sales; cross-sectional/leave-one-out comparison against other categories.

**STILL OPEN — four dials (calibration, not design; propose now on test data, confirm at connect):** (1) which percentiles define the band; (2) confidence-band width; (3) the absolute floor; (4) where the materiality bar sits.

**CONFIRMATION PASS OWED:** the 2026-06-10 decisions were tagged provisional pending grouping; grouping closed 2026-06-19 but nothing went back to un-provisionalise them. **This is the recommended NEXT action** — a thinking task (done in chat, not Claude Code), hours not days. The 2026-06-10 file already sorts its decisions into grouping-independent vs the ~12 grouping-dependent, so only that subset needs re-checking. Unblocks C8 wiring (the wedge). A prompt to pull the ~12 items + the locked grouping set into one place was offered — founder wants it done next session on a fresh head.

---

## 7. THE READINESS SPREADSHEET + RETIRING THE MAP (Batch 3)

**`pilot_readiness_map.md` — RETIRED.** Claude Code confirmed it was **never in git**, never committed, not in the working tree, no committed doc references it — it lived only on `D:\Anupam\Profit Sentinel\Pilot Docs - Timeline and Effort\` (a different drive from the repo at `C:\…\profit-sentinel\docs\`). **No git action.** Founder deleted the local copy and removed it from the Project files. Retired to stop three-artifact drift (it caused the stale PCD claim and the wrongly-unparked questionnaire). Its unique content was harvested first (legend, two long poles, pipeline stages, effort estimates).

**`/mnt/user-data/outputs/pilot_readiness_24072026.xlsx`** — regenerated from the committed register. **Personal/working file — NOT committed to the repo** (avoids two-artifact drift; regenerate from the register when the register changes). 3 sheets, 0 errors:
- **Sheet 1 "Build Sequence"** — all 32 items in three blocks: **BLOCK A (23 items) buildable NOW, no design partner / no real data; BLOCK B (6) only at first connect; BLOCK C (3) during/after pilot.** The A/B/C split is COMMITTED FACT (the register's own section headings: "BUILD TASKS (before a real brand connects)" vs "FIRST-CONNECT ACTIONS"). Within-block ordering is DERIVED (marked so in-file). Columns: #, pipeline stage, item plain name, register item, plain meaning, sub-steps, effort (inherited from old map, unvalidated), **Cowork can help? (kept — founder's choice)**, blocks-pilot. Row A1 (the C8 dials) updated post-Batch-4 to reflect method-decided / four-numbers-open.
- **Sheet 2 "Parallel Track"** — recruitment (the gate), connector approvals, entity registration, legal counsel pass, housekeeping.
- **Sheet 3 "Legend"** — the code glossary (BT/FC/OQ/PG/CD/HK/DH/D/H in plain language) + the five pilot alerts in plain language.

**Two items flagged RED — real work with no tracked register home → fixed in Batch 4:** Evidence Stack assembly (→ BT-15) and legal counsel pass (→ PG-2).

---

## 8. THE PILOT (committed reference — for a fresh session)

**Pilot = the full automated product in ~6 weeks, with exactly a few deliberate differences from full PS:** limited alert set, one human relevance gate, reduced surface (email only, no in-app screen, no NLQ).

**Pilot fired set (5 alerts):**
- **C8 Return-Driver** — THE WEDGE. Ad spend pushes a product that then returns abnormally often for that product. Connectors: Shopify returns + Meta + Google + TikTok (confidence-weighted) + Loop. Detection rule per §6 above.
- **C1 Sizing-Complaint Velocity** — support fit-complaints rising predict a return wave; validated retrospectively per brand against historical Gorgias; parse text not tags (pending build). The only alert that warns BEFORE.
- **C6 High-Return New Collection** — a new drop exceeds the store average early (~14 days; baseline = store average since no product history).
- **G1 Stockout During Active Spend** — SKU out of stock while an ad channel spends on it. Time-sensitive → fast-lane. Needs the +/-1-day timing fix (spend arrives next day, inventory snapshotted at midnight).
- **C2 Influencer ROI After Returns** — return-adjusted ROI by creator; fires only if the brand runs influencer.

**Not in the fired set (Horizon 2 for the pilot):** A1 true post-return ROAS by channel; A2 root cause of a noticed ROAS drop (retired from fired set — C8 owns return-driver); D1 margin compression. All blended-marketing figures name every channel the brand runs, with connected-vs-zero disclosure (unconnected ≠ zero spend).

**Three in-app/digest items** (not fired alerts) now delivered in the WEEKLY DIGEST EMAIL, all gated: blended post-return ROAS (the headline hook), the serial-offenders/repeat-returner cost (a standing total, not weekly news), the return-rate-and-reason table.

---

## 9. WHAT'S NEXT (as left at session end)

1. **Recommended:** the **C8 confirmation pass** — re-check the ~12 grouping-dependent 2026-06-10 decisions against the locked 2026-06-19 grouping set; confirm/flag each; commit. Thinking task in chat. Next session, fresh head. A setup prompt was offered.
2. Any other Block A item (23 need no design partner) — e.g. category cross-check (BT-8), blended-marketing fix (BT-1).
3. Recruitment — the binding gate (see the outreach context file).
4. **Standing reminder:** whenever `operating_charter.md` changes, refresh the live **Project instruction** from the committed file (repo first, then paste). The stale instruction re-injecting pre-pivot framing was a recurring cause of errors this session. Founder confirmed refreshed after the charter commits.

**Status:** documentation work is finished — specs internally consistent, every claim traceable, register carries nothing untracked found. What remains is doing the build, not describing it.
