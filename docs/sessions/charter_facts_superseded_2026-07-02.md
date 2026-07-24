# Charter — Facts Superseded (2026-07-02)

**What this is:** the resolution of DH-1. The operating charter (the pasted "IDENTITY / DECISION FILTER / DEPTH PROTOCOL / …" brief) describes the **pre-pivot** product. This record marks each stale FACT superseded, citing the committed file that supersedes it, so the charter's facts stop silently contradicting the shipped product.

**What is NOT changed:** the charter's **stance and protocols** — Lead Product Architect identity, the Decision Filter *structure*, the Depth Protocol (three passes), the Evidence Stack, the Pushback Protocol, the Response Format, position-change naming, and own-the-architecture — remain **fully in force, unchanged.** Only the specific factual claims below are superseded.

**Canonical authority:** the live committed files in the repo (`pilot_scope.md`, `product_strategy.md`, `technical_architecture.md`, `cross_alert_orchestration.md`, and the other synced canonical docs) are canonical. Where a genuine product-scope question remains, it is flagged for founder ruling, not decided here.

---

## Superseded facts

**1. Source document `seed_design_decisions.md` — SUPERSEDED (does not exist).**
The charter's "Four Source Documents" names `seed_design_decisions.md`. That file is not in the repo. The real seed-design decisions live in three files: `seed_decisions_gap_a_b_c.md`, `seed_decisions_gap_d_e.md`, `seed_decisions_gap_f_g.md`. *(Confirmed: `agent_d_build_spec.md:2497` cites `gap_abc_decisions.md`; `cross_alert_orchestration.md:650` cites the `seed_decisions` family.)*
→ The charter's source-doc list should name these three, not the single non-existent file.
[Corrected 2026-07-24: the first file is gap_abc_decisions.md; seed_decisions_gap_a_b_c.md does not exist in the repo.]

**2. "The Five Alerts — Build Priority Order" — SUPERSEDED as the pilot set.**
The charter lists the old five: (1) True post-return ROAS, (2) Root cause of ROAS drop, (3) Influencer ROI after returns, (4) Contribution margin compression, (5) Sizing complaint velocity. The committed **pilot fired set is C8, C1, C6, G1, C2** (product_strategy.md §3D + pilot_scope.md). The "Five Proactive Alerts" framing was explicitly RETIRED (product_strategy 2026-06-14 changelog).
Mapping old → pilot: old #3 Influencer ROI → **C2** (in pilot); old #5 Sizing velocity → **C1** (in pilot); old #1/#2/#4 (True post-return ROAS / ROAS-drop root cause / margin = A1/A2/D1) are **NOT** in the pilot fired set. New to the pilot: **C8** (Return-Driver — the wedge), **C6** (High Return Rate New Collection), **G1** (Stockout During Active Spend).
→ The full-product vision is the 59-alert library; the pilot is C8/C1/C6/G1/C2. The old five are a retired framing, not a current roadmap.

**3. "Alert 2 = Root cause of ROAS drop (Meta + Shopify)" — SUPERSEDED.**
A2 is now **multi-channel (Meta + Google + TikTok)**, per committed product_strategy §3D (commit `d695453`). A2 is also **retired from the pilot fired set** — C8 owns the return-driver concern; A2's lineage points "→ C8". A2's actual per-channel detection is a pending build task (BT-10 in the register).

**4. Alert priority list "1. True post-return ROAS by channel (Shopify + Meta + TikTok)" — channel list SUPERSEDED.**
Post-return ROAS (A1) now includes **Google**: Shopify + Meta + **Google** + TikTok, per committed product_strategy §3D. All blended-marketing figures now name every channel the brand runs (Meta/Google/TikTok) with connected-vs-zero disclosure.

**5. Critical Path = "20 beta clients with 70%+ alert action rate" — SUPERSEDED as the immediate gate.**
The committed binding launch gate is **4–5 design partners** (pilot_scope.md §8).
→ **SCOPE QUESTION FOR FOUNDER:** is "20 beta clients" a *killed* target, or a *later* milestone after the 4–5 design-partner pilot? The doc-sync settles the immediate gate (4–5 design partners); whether 20 beta remains a labeled later milestone is your call. Until you rule, the critical path is 4–5 design partners.
**Closed 2026-07-24 (founder ruling):** "20 beta clients" is NOT a hard target anywhere — neither a killed metric to track nor a labeled later milestone. The binding launch gate remains 4–5 design partners (pilot_scope.md §8).

**6. Open Decision "whether Slack is definitively the right delivery channel" — PARTIALLY SUPERSEDED.**
Delivery surface for the **pilot** is decided: **EMAIL** (committed in pilot_scope). The **final-product** Slack-vs-email decision remains genuinely open, to be decided post-pilot on email's performance (OQ-12 in the register).
→ Re-scope this open decision to: pilot = email (closed); final-product surface (open, post-pilot). Note: `technical_architecture.md` is still Slack-native by design (schema, agents, build steps) — deliberately, pending that post-pilot call.

---

## NOT superseded — remain genuinely open (keep in the charter)

- **$299/month Growth-tier price** — no decision made; pricing isn't in the synced files. Still open.
- **Gorgias tagging consistency** — the sizing alert is now **C1** in the pilot; this validation question still applies (re-label to C1). Still open.
- **Whether founders act on proactive alerts before seeing the problem** — the core hypothesis. Still open.

---

## Stance — explicitly preserved

Unchanged and in force: **Identity** (Lead Product Architect), **Decision Filter** *structure* (assumption / critical-path / specificity checks — with the critical-path *fact* corrected per #5), **Depth Protocol** (three passes), **Domain Flags**, **Evidence Stack**, **Fashion Profitability Leakage** context, **Pushback Protocol**, **Response Format**, **position-change naming**, **own-the-architecture**.

---

## Follow-on (recommended, your call)

Marking these facts superseded closes DH-1 as a tracked item — but the charter is pasted verbatim each session, so the stale facts keep being re-injected until the charter text itself is corrected. **Recommendation:** adopt a corrected charter going forward (paste the corrected version instead of the current one). This record is the exact change-set. I can produce the full corrected charter text on your go — it needs your ruling on **#5 (the 20-beta-clients milestone)** to be complete, and I'd fold in the corrected source-doc names, the C8/C1/C6/G1/C2 pilot set, the multi-channel A2, the Google-inclusive ROAS, and the email/pilot + Slack/final-product delivery split.

**Also flagged:** `Profit_Sentinel_Blueprint_v8.docx` is a real source doc that likely carries the same pre-pivot facts (old five alerts, Slack, pricing, client targets). It was **not** checked this session. Recommend a separate staleness review before it's relied on.

**Closed 2026-07-24:** this follow-on is CLOSED — Blueprint v9 exists (Profit_Sentinel_Blueprint_v9.docx) and was reconciled July 2026 to the committed pilot specs, with pilot-vs-post-pilot scope marked explicitly. The v8 staleness review is no longer outstanding.
