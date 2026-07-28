# DOC-SYNC — RUNNING FINDINGS (durable record)
# SNAPSHOT 1: collection complete, pre-review-list. Saved 2026-07-02.
# SNAPSHOT 2 (APPENDED BELOW): review-list finalized + all founder decisions locked. 2026-07-02.
# Status: REVIEW LIST FINAL. Editing not yet started. Not canonical. Working notes only.
# HEAD context: onboarding_flow.py + seed_meta.py modified in working tree (uncommitted).
#
# NOTE: Original Snapshot-1 content is preserved verbatim below. Where Snapshot 1 and
# Snapshot 2 differ, SNAPSHOT 2 IS CURRENT (later decisions win).

## POINT 1 — CONFIRMATION-FLOW COUNT — RESOLVED
- CODE (onboarding_flow.py) = 5 core question-topics, attribution = ONE (-> meta_attribution_window) [:137-146].
- DOC (product_strategy §5 ":910") = "Six Confirmation Questions", attribution SPLIT model(:947)+window(:965).
- §5 Q3 inline "Pilot status — DEFERRED" (:949): six-question chooser = POST-PILOT; PILOT = one fixed
  attribution basis. Code matches the PILOT design. VERDICT: code does NOT lag.
- RESOLUTION (row 6) = DOC-CLARITY edit (product_strategy §5): label the six-question flow POST-PILOT;
  state the PILOT flow is FIVE (single fixed attribution basis). Conf: HIGH.
- IN-FLOW GAPS -> REGISTER build-items (Point 3 confirmed BOTH = build-lag, code predates doc updates):
  * COGS: doc 4-tier vs code 3-option [product_strategy:913 vs onboarding_flow.py:76-79].
  * ROAS: doc writes roas_net_of_returns; code writes only include_shipping_in_revenue [:977 vs :154].
    (SEE SNAPSHOT 2: superseded by the ROAS display decision — no founder toggle.)
- D-20 pending_connectors: in NEITHER code nor §5; session-notes only; genuinely pending.

## POINT 2 — C8 / RETURN-DRIVER — READ
DECIDED (safe to apply in doc-sync):
- C8 = return-driver's code, Group C; library 58->59 (Option B); A2 retired-from-pilot + lineage "-> C8";
  "HERO" = informal alias for C8; fired pilot set C8/C1/C6/G1/C2. [buildstate_c8:58-73]
NOT DECIDED (do NOT compose into §3D):
- Detection rule PROVISIONAL. OP-1 (06-19) resolved GROUPING grain only, NOT abnormality. Abnormality/
  materiality (AL-19/AL-17/AL-16, C3-foundation 06-10) = provisional + NEVER canonical.
- "2x brand average" headline RETIRED -> "rarity vs product's own history".
- SERIES FIT (Group C) = inference; revisit if attribution-not-returns.
- Confidence floor / verification category = undefined.
BUILD REALITY: reads mart_return_rate_by_sku, CURRENTLY 100% LOOP (native inert until J-1); NO Agent-A
  detection wired; prose (pilot_scope:53-55) still uses retired "2x" -> neutralize.
§3D FORMAT (verbatim captured): block = header · Actionability · Verification · What it detects ·
  Connectors required · Confidence floor; summary row = | Code | Name | Actionability | Verif. | Conf.Floor |;
  insert after C7; Group-C header ":354" = "(C1-C7)" -> "(C1-C8)".
RESOLUTION (row 12) = apply decided parts (rename/count/A2 lineage/header/neutral phrasing) + MINIMAL
  HONEST §3D entry (decided fields filled; detection-rule + conf-floor = "pending detection design"). Do
  NOT fabricate. Detection design + Agent-A wiring + 100%-Loop source -> REGISTER (pilot-critical).
  (SEE SNAPSHOT 2: C8 connectors now include TikTok w/ catalog-ad caveat.)

## POINT 3 — PILOT-READINESS MINI-SCAN — DONE
>>> LIVE CONTRADICTION (RESOLVED): D-F gate cond (2) required R10 sync-guard pre-connect; 25-Jun deferred
    validate_sync to FIRST CONNECT. FOUNDER RULING: build at first connect. D-F(2) reworded when gate
    canonicalized. [prepilot-hardening:172-180 (2) vs durable-rls-bc:40]
>>> PILOT ALERTING INCOMPLETE: Agent A scans A1,A2,B1,B4,C1,D1,E2,F2. Of the 5 fired pilot alerts
    (C8,C1,C6,G1,C2), ONLY C1 detected today. C6/G1/C2/C8 need wiring. [buildstate_c8:23,34-36]

## POINT 3B — MAY-SWEEP + AGENT-A 8-SIGNAL ANALYSIS — DONE
MAY SWEEP: N — NO live, un-mirrored PILOT requirement lost. 3 MAY-ONLY items (each attaches to DEFERRED work):
  * Segment-boundary calibration at onboarding [chat_2026_05_21_b5_design:88-90] — E-series/segments (Phase-2).
  * brand_event_calendar.is_major verify before Agent-B build [chat_2026_05_22_v3:91]. (SEE SNAPSHOT 2: promoted.)
  * Klaviyo open-rate 0.65 default at onboarding [chat_2026_05_20_v3:172-173] — Klaviyo/E-series.
AGENT-A 8-SIGNAL SCOPE (DECISION: keep pilot at 5; do NOT add the 7): A2 IS C8; B1/B4 Meta-only commodity;
  D1/A2/E2 need Agent B/C/D; A1 as-coded is a PROXY; F2 depends on Sentry + name divergence; all synthetic-only.
  Effort -> WIRING C6/G1/C2/C8. NAME DIVERGENCE: F2 "Checkout Error Spike" vs §3D "Payment Gateway Failure"
  [agent_a.py:366 vs ps:520]. (SEE SNAPSHOT 2: resolved -> keep "Checkout Error Spike".)

## POINT 3C — GOOGLE ADS COVERAGE — DONE (DECISION: option 1 — doc reflects decided design)
- MISS confirmed: Google Ads is a DECIDED Phase-1 source [prepilot-hardening:155]; §7 says omitting it makes
  "Alert 1 structurally incomplete" [ps:1118]; only 2 of 13 ad alerts (A3,A4) name Google in §3D. §7 vs §3D
  self-contradiction. seed_google_ads.py EXISTS; NO stg_google_ads; google_spend via B-9 cost_micros/1e6
  [ccd:335-339]; google_roas/attributed_orders NOT built; google_spend used ONLY by G1 gate [ccd:505].
- No "totals-only" decision -> UN-PROPAGATED MISS. Docs reflect all-three design; build tracked in register.

## POINT 3D — BLENDED-MARKETING COMPLETENESS SWEEP — DONE (RULE locked)
RULE: ANY blended/combined marketing figure must cover every channel the brand ACTUALLY RUNS (Meta+Google+
TikTok), must NOT treat unconnected as $0, MUST disclose covered channels.
- DOC: 7 of 9 blended §3D alerts OMIT Google (A1,A2,A5,A6,B2,D1); narrative(§2:65)+§7:1118 say all three;
  pilot_scope:68-69 "total spend" no disclosure; tech-arch:1144 names Google while mart excludes it.
- CODE single root: mart_cross_source_daily total_ad_spend = meta+tiktok [:218]; blended_roas [:224];
  ccd inherits into contribution_margin_pct [:106-109], blended_cac_7d [:270,294], outputs [:606-607];
  google_spend computed [:335-339] feeds only stockout gate [:505]. Fix ONE base + connected-vs-zero + disclosure.
- CONNECTED-VS-ZERO not distinguished: coalesce(...,0) collapses missing->$0; Google dropped entirely.
- Agent-A inheritors: A1, D1, A2 (A5 latent-unwired).
DOC EDIT SITES: ps:259-260(A1),:268(A2),:291-292(A5),:299(A6),:326-327(B2),:418-419(D1),:560-561(G1),
  pilot_scope:68-69, tech-arch:1144, + §2/§7-vs-§3D contradiction.

## FOUNDER DECISIONS — SNAPSHOT 1 (locked)
- Google Ads = MISS -> option 1 (doc reflects all-three design; build in register).
- Blended-marketing rule locked (all-three-the-brand-runs + connected-vs-zero + coverage disclosure).
- validate_sync = FIRST CONNECT (not pre-connect); D-F(2) reworded.
- Agent-A scope = keep pilot at 5; wire C6/G1/C2/C8; do NOT add the 7.
- May sweep = nothing lost; 3 conditional items recorded.

# ============================================================================
# ===== SNAPSHOT 2 — decisions locked AFTER Snapshot 1 (2026-07-02) ==========
# These are CURRENT and override any conflicting Snapshot-1 line above.
# ============================================================================

## POINT 3E — STALE-SWEEP + EVENT-CALENDAR + TIKTOK-API — DONE (all verified)
PART A (final stale count/name sweep):
- Count fix touches 5 FILES, not 3. Beyond ps + pilot_scope: cross_alert_orchestration.md "41-type" x3
  (:11,:38,:650) and pre_agent_build_checklist.md "56 alert codes"/"37 alerts" (:111,:222,:229) are stale.
  "59" appears in NO canonical file yet. agent_d / d1_gates / save_protocol / CLAUDE = clean (no count).
- HERO alert-NAME rename sites = ONLY pilot_scope.md:53 + technical_architecture.md:1457. Every other
  HERO/hero token is SYNTHETIC PRODUCT DATA (HERO_DRESS, AZR-DRESS-HERO, "FW hero" knit) -> MUST NOT rename.
PART B (brand_event_calendar):
- It drives ALL Agent-A suppression (S1-S50) [tech-arch:1491-1495]. Returns pilot alerts (C6,C8,C2) + D6
  ("essential pilot plumbing", pilot_scope:91-92) depend on it -> NOT Agent-B-only.
- LIVE DB: client_azure_co.brand_event_calendar = 116 rows (SEEDED); public = 0. "Zero rows" claims are STALE.
- Auto-derive-from-brand's-own-history (Approach-B) is DESIGN-ONLY (pseudocode tech-arch:2500-2532), NOT built.
  -> FIRST-CONNECT build item for real brands.
- Live stale-comment bug: historical_pattern_scan.py still says "zero rows" + gates launch-chains off it
  (lines 31,621-624,811,1238) -> build-task sub-item.
PART C (TikTok product-level spend — decides PS-4):
- TikTok API DOES document product-level (CATALOG/DSA report catalog_id+product_id; Shop Ads product reporting)
  but USABLE only when brand runs catalog/Shop ads (geo US/UK/SEA); standard video ads = campaign-level only.
- CODE already carries it: tiktok_ad_performance has content_ids (~56% populated) + content_id_confidence
  (a PROXY marker); mart already unions TikTok content_ids [mart:551-557] BUT TikTok branch LACKS the RULE-3
  is_synthetic guard the Meta branch has [mart:552-556] -> provenance-leak to fix.
- pilot_scope:54 names C8 as "Meta+Google only" -> doc-vs-mart divergence regardless of decision.
- VERDICT: (b) possible-but-conditional -> founder decision (see below).

## FOUNDER DECISIONS — SNAPSHOT 2 (locked; CURRENT)
- COUNT FIX = 5 FILES (fix cross_alert_orchestration + pre_agent_build_checklist too; clean everywhere).
- PS-4 TikTok in C8 = INCLUDED, with caveat "product-level where the brand runs catalog/Shop ads;
  confidence-weighted (proxy) signal." Adjust synthetic seed to match real API. + build TikTok catalog report
  + add missing is_synthetic guard on TikTok mart branch.
- ROAS = ALWAYS show BOTH gross ROAS and net-of-returns ROAS; NO founder toggle. Display decision,
  independent of the (parked) onboarding questionnaire. (Supersedes the Snapshot-1 roas_net_of_returns field.)
- CD-2 event calendar = PROMOTED out of "conditional" -> PILOT-CRITICAL FIRST-CONNECT build (FC-6):
  auto-build a real brand's calendar from their own history (engine unbuilt) + fix the stale "zero rows"
  comments in historical_pattern_scan.py.
- BT-5 onboarding questionnaire (COGS 4-tier; D-20; CD-10; [ROAS field dropped]) = PARKED as pre-pilot open
  item (resolve before first real brand onboards, not now).
- OQ-6 category Shopify-vs-LLM cross-check = PROMOTED to PILOT build task (BT-8). Alerts wrong without it
  (C6/C8/C2 group by category; wrong category -> wrong grouping, silent). Disagreement-handling = design item.
- OQ-7 parser labels = SPLIT (BT-9): finalize parser + labelling PROCESS before pilot; VALIDATE labels on
  REAL data DURING pilot. (Links to existing parser-accuracy gate in BT-6.)
- OQ-11 F2 name = RESOLVED: keep "Checkout Error Spike" (the symptom); "Payment Gateway Failure" becomes a
  CAUSE node inside F2's future causal graph. Doc-consistency only; F2 is parked (Phase-2).
- PG-1 D-F gate = (a) stays HARD gate; (b) documented durably in the register; (c) DEEP REVIEW of all 7
  conditions before pilot (tracked pre-pilot action).
- REGISTER = becomes a NEW FILE docs/sessions/pilot_readiness_register.md, created at END of the doc-sync.
- EDIT PROGRESS: pilot_scope.md committed (33d337f, 5 changes). product_strategy.md committed (d695453,
  15 groups + Flag-2 C8-Note correction) — spawned BT-10 (A2 per-channel detection) + BT-11 (C8 code
  lineage note). cross_alert_orchestration.md committed (3 count-only edits 41-type->59-type at :11/:38/:650).
  CAO-1 SCOPE CORRECTED by live read: it is 3 COUNT-ONLY edits, NOT a roster change. The S41-S45 suppression
  -scenario IDs (32 refs) are OFF-LIMITS (a blind 41->59 swap would corrupt them). The :650 illustrative
  A1/A2 list was DELIBERATELY NOT rewritten (it is a partial namespace-collision example ending in "...",
  not a maintained roster — so C8 not added, A2 not updated there).
  FILE 4 pre_agent_build_checklist.md = NO EDIT (RESOLVED by live read; PAC-1 was a FALSE POSITIVE).
  All "56"/"37" occurrences are DATED HISTORICAL build-log records (validation runs at commit ffa128f,
  B-5 design milestones) or a data value (:45 "tiktok_leads 37") — NONE is a current library-count. Per
  the project's own precedent (product_strategy 2026-06-14 changelog kept as history), historical records
  stay as history. A blind 56/37->59 would have falsified dated build records — read-first prevented it.
  FILE 5 technical_architecture.md COMMITTED (5a6bd3d): 2 edits — HERO->C8 return-reason note (:1457) +
  41-type->59-type count (:1390). The 5 HERO_DRESS/AZR synthetic refs and all 26 Slack refs UNTOUCHED.
  DOC-SYNC FILE EDITS STATUS: pilot_scope 33d337f / product_strategy d695453 / cross_alert 09834fd /
  pre_agent_checklist NO-EDIT / technical_architecture 5a6bd3d. 4 committed, 1 no-edit.
  TWO-FILE CHECK RESOLVED (2026-07-02, read twice): d1_validation_gates.md (399L) + agent_d_build_spec.md
  (2722L) = BOTH CLEAN, NO EDIT. Evidence: d1_gates — HERO only synthetic "FW hero knitwear" :53; zero stale
  counts; "blended" hits (:219/:230/:236/:241) all = return-rate brand-average, NOT ad-spend. agent_d — zero
  HERO; zero stale counts; ad-spend "blended" only at :1726 (already names all 3 channel-pairs Meta+TikTok/
  Meta+Google/TikTok+Google, CORRECT) + :1829 (mart column); the "2x" at :2492-2515 is a DATED decision-record
  ("C3 consistency check RESOLVED 2026-06-03") = history, leave. Surfaced BT-12 (C3->S15 wiring).
  DOC-SYNC FILE SCOPE COMPLETE: 7 of 9 canonical files verified (pilot_scope/product_strategy/cross_alert/
  technical_architecture edited-or-committed; pre_agent_checklist no-edit; d1_gates + agent_d clean). Remaining
  2 (save_protocol.md, CLAUDE.md) = clean by nature (protocol/rules files; no alert-names, counts, or blended refs).
- DH-1 ESCALATED: the pasted charter/onboarding-brief lists seed_design_decisions.md (NOT in repo),
  the OLD five alerts (incl. "Alert 2 = ROAS-drop root cause, Meta+Shopify" — contradicted by A2 now
  multi-channel), Slack/$299/20-clients. Live committed files are canonical; charter STANCE in force,
  charter FACTS stale. Founder decision owed at doc-sync end: update the charter or mark superseded.
  It is a TRACKING artifact (like state files), NOT a canonical spec -> no line-count handle, no full
  save-protocol. Rationale: canonical files describe WHAT THE PRODUCT IS; the register tracks WHAT WORK
  REMAINS — different jobs; matches existing docs/sessions/ pattern; keeps canonical files clean.
- DH-1 stale charter/onboarding-brief = recorded in the register as a doc-hygiene item. The pasted IDENTITY
  brief describes the pre-pivot product (old 5 alerts / Slack / $299 / 20 clients / seed_design_decisions.md
  not in repo). DECISION STILL OWED BY FOUNDER: update it to current pilot, or mark superseded.

## EDIT ORDER (whole-file; scoped-diff each; founder commits + pushes; NO push from Claude Code)
1. pilot_scope.md  2. product_strategy.md  3. cross_alert_orchestration.md
4. pre_agent_build_checklist.md  5. technical_architecture.md (largest; last)
Then: write continuity pair; CREATE docs/sessions/pilot_readiness_register.md as a real file.

## ===== FINAL PILOT READINESS REGISTER (candidate; becomes the new file) =====
OPEN-QUESTIONS:
- OQ-1 C8 abnormality rule + series-fit (provisional/non-canonical) [buildstate_c8:103-104; c3-foundation:240-241]
- OQ-2 Blended-marketing coverage-disclosure DESIGN [Point 3D] [NO canonical home]
- OQ-3 Weekly-digest = PILOT (confirmed); cadence-gating design open; canonical-vs-Horizon-2 conflict [prepilot-hardening:167-170]
- OQ-4 E5/E6 canon reconciliation [ps:1365]
- OQ-5 3-namespace alert-numbering collision [ps:1366]. CANONICAL ANALYSIS lives at
  cross_alert_orchestration.md:650 (P2-FINDING 5) — documents the 3 namespaces (§3D alert IDs vs
  gap_abc_decisions seed-design labels vs seed_decisions S1-S50/E-series) + recommends a naming
  convention (ALERT-A6 vs DEC-A6 vs S-rule). Confirmed still OPEN (doc-integrity, not stale) — left
  untouched in the cross_alert doc-sync.
- OQ-8 Small causal-graph completeness — each pilot symptom's root cause present before Agent B? [HIGHEST-RISK; NO file mention]
- OQ-9 You->founder delivery-loop mechanism undesigned [NO canonical home]
- OQ-10 Alert-count reconcile 57(code)/58(canon)/59(C8) as code catches up; delivery surface = EMAIL (decided)
- OQ-12 [NEW] DELIVERY-SURFACE FINAL-PRODUCT DECISION (post-pilot). Pilot uses EMAIL (confirmed, committed
  in pilot_scope). But technical_architecture.md's FULL-PRODUCT architecture is Slack-native: schema columns
  slack_thread_ts/slack_channel (NOT NULL), Slack Bolt data flow (:35), "founder never leaves Slack" surface
  (:48), Agent D posts to Slack (:814), Slack bot build steps. This was LEFT UNTOUCHED in the doc-sync
  (26 Slack refs intact) — it is NOT a find-replace. AFTER the pilot, decide on email's pilot performance
  whether the final product stays email or moves to Slack. If Slack: architecture already built. If email:
  tech-arch delivery layer (schema + Agent D formatting + interaction model) needs redesign — schema-and-
  agent-deep, a real design task, NOT a doc edit. DO NOT resolve until pilot delivers evidence. (Founder
  confirmed 2026-07-02: "trying email in pilot, decide email-vs-Slack for final product based on pilot
  experience.") This is the SAME decision as the DELIVERY half of DH-1.
(RESOLVED & moved out: OQ-6 -> BT-8; OQ-7 -> BT-9; OQ-11 -> "Checkout Error Spike"; delivery surface (PILOT) -> email)
BUILD-TASKS:
- BT-1 Blended-marketing: add google_spend to total_ad_spend + all blended figures; build stg_google_ads,
  google_roas, google_attributed_orders; connected-channel registry + missing-vs-zero + coverage disclosure.
  (Fixes A1/D1/A2/A5 at once.)
- BT-2 C8: add chain to causal_graph.py + wire Agent-A detection (return_rate_pct not scanned today).
- BT-3 causal_graph.py: add missing E5 chain (code 57->58); wire ORPHANED causal_graph into Agent B (GATED on E5).
- BT-4 Wire other pilot alerts into Agent A: C6, G1, C2 (only C1 scanned today). [C8 wiring = BT-2]
- BT-5 [PARKED pre-pilot] Onboarding questionnaire: COGS 3-option->4-tier; D-20 pending_connectors question;
  CD-10 per-client C1 calibration step. [ROAS opt-out field DROPPED per display decision.]
- BT-6 Debt/plumbing: parser per-brand accuracy gate (D-GAP6-21/D1-G12); agent_a hardcoded-55% margin
  (verify locus); GA4 stg_ga4_pages/devices (mart TODOs); Pass-Two SKU-contract validator (in R11).
- BT-7 [NEW] TikTok catalog-report wiring for C8 product-level spend + add is_synthetic guard on TikTok
  mart branch [mart:552-556].
- BT-8 [NEW, PILOT] Category cross-check: Shopify-assigned category vs LLM category; flag disagreements
  (disagreement-handling = design item). Pilot-critical — grouping correctness for C6/C8/C2.
- BT-9 [NEW] Parser + labelling PROCESS finalized before pilot (validation of labels is FC, on real data).
- BT-10 [NEW] A2 per-channel root-cause detection: build the four-cause decomposition (CPM inflation /
  creative fatigue / checkout errors / SKU return outlier) to run PER AD CHANNEL (Meta/Google/TikTok),
  with channel-attribution-confidence handling — name the channel it is confident about, flag ambiguity
  rather than forcing a single-channel verdict. (Origin: A2 made multi-channel in product_strategy §3D
  doc-sync commit; the §3D spec now states multi-channel intent but detection is Meta-only in code.)
- BT-11 [NEW] C8 lineage note in code: add the A2->C8 retirement lineage note to A2's causal_graph.py
  entry (per buildstate_c8 2026-06-18). product_strategy §3D C8 Note now POINTS to causal_graph.py as the
  lineage home, so the code note must actually exist for that pointer to resolve. (Origin: Flag-2 fix in
  product_strategy doc-sync commit.)
- BT-12 [NEW] C3 detection wiring: per the 2026-06-03 resolution (agent_d_build_spec.md:2510), (a) wire C3
  to the SAME per-category baseline D1 uses (S15) so C3 and D1 share one computation — C3's stated method
  does NOT reference S15 today (only D1 is wired to it, per :2500); and (b) decide C3's shared thin-history
  fallback: exposure test (D1's method, can still act) vs 90-day monitor-and-wait (C3's seeded method, waits)
  — a real design fork per :2506. Doc part (a-headline) already done (product_strategy C3 "2x" neutralized);
  the S15 WIRING + fallback decision are the build/design remainder. C-series detection, adjacent to BT-2
  (C8). NOT a duplicate of the line-29 C8-abnormality note (that is C8's rule, this is C3's baseline).
  (Origin: agent_d_build_spec.md read 2026-07-02, C3-consistency-check finding.)
FIRST-CONNECT-ACTIONS:
- FC-1 Build validate_sync.py (R10) — founder-ruled first-connect; reword D-F(2).
- FC-2 Repoint C8/returns to Shopify-native (J-1) + prove native ingestion [tech-arch:1461-1463; D-D].
- FC-3 C1 recalibration (CD-10; manual p90 interim).
- FC-4 Persistent paid Supabase + keep-alive.
- FC-5 Start connector access for ALL platforms, prioritized by lead time:
  * First (long lead, today): Shopify public-app+OAuth+review; Google Ads developer token.
  * Second (pilot-fired, now): Meta API; Gorgias API key; Loop Returns API key.
  * Third (soon after): TikTok API; Klaviyo API key; Sentry (only brands that have it).
  * Plus (long-lead, non-connector): entity registration.
- FC-6 [PROMOTED from CD-2] Build brand's event calendar from their own history (engine design-only, unbuilt);
  fix historical_pattern_scan.py stale "zero rows" comments (lines 31,621-624,811,1238).
- FC-7 Validate parser labels on REAL brand data (pairs with BT-9).
PRE-PILOT-GATE (pointer, do NOT re-type):
- PG-1 D-F 7-condition HARD gate -> state_2026-06-23_prepilot-hardening.md:172-180. NOT yet canonical.
  Status: (1)DONE (2)REWORD-per-ruling (3)DONE (4)PARTIAL (5)OPEN (6)OPEN (7)OPEN.
  Commitments: hard gate; documented in register; DEEP REVIEW of all 7 before pilot.
HOUSEKEEPING:
- HK-1 6 untracked continuity files + slack_bot/ untracked (slack_bot now stale since delivery=email —
  flag-not-delete); seed_meta.py + onboarding_flow.py modified-uncommitted.
- HK-2 OneDrive/.git corruption risk (accepted; repo = source of truth).
- HK-3 [CLOSED — folded into Part 1 count fix via CAO-1 + PAC-1] stale roster counts 41/56/37.
- HK-4 Founder runs all pushes.
DOC-HYGIENE:
- DH-1 Stale charter/onboarding-brief (pre-pivot: old 5 alerts/Slack/$299/20 clients/missing seed file).
  FOUNDER DECISION OWED: update or mark superseded.
CONDITIONAL (re-surface only if deferred work pulled forward):
- CD-1 Segment-boundary calibration (E-series/segments, Phase-2).
- CD-3 Klaviyo 0.65 open-rate default at onboarding (Klaviyo/E-series, Phase-2).
(CD-2 promoted to FC-6.)
NO-CANONICAL-HOME (highest vanish-risk; register is their only home): OQ-2, OQ-8, OQ-9, OQ-1 (abnormality
  method), D-20 (in BT-5), PG-1 (whole D-F gate). Plus DH-1.
