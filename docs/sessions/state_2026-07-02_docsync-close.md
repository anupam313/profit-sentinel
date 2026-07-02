## SESSION OPEN — LOAD FIRST (do this before any work)
- THIS PAIR'S SELF-HANDLES: state_2026-07-02_docsync-close.md = 100 lines;
  chat_context_2026-07-02_docsync-close.md = 74 lines. If either file's real wc -l differs
  from these, a stale/truncated copy is mounted: STOP and ask for the live copy.
- Load docs/save_protocol.md FIRST (governs every save; 149 lines — re-verify at HEAD).
- Load docs/sessions/pilot_readiness_register.md — it is now the LIVE tracker for ALL remaining
  pilot-readiness work (open questions OQ-1..12, build tasks BT-1..12, first-connect FC-1..7, the D-F
  pre-pilot gate PG-1, housekeeping). The "what's left before pilot" list lives THERE, not here.
- Re-verify the 9 canonical handles AGAINST HEAD. TWO changed this session (doc-sync):
    product_strategy 1436 (was 1424; +12: C8 §3D entry + summary row + §5 lead paragraph) ·
    pilot_scope 124 (was 122; +2: C8 fired-bullet + blended-ROAS prose wrapping).
  UNCHANGED (7): technical_architecture 3999 (2 same-line edits, no line delta) ·
    cross_alert_orchestration 847 (3 same-line count edits) · agent_d_build_spec 2722 (no edit) ·
    d1_validation_gates 399 (no edit) · pre_agent_build_checklist 389 (no edit) ·
    save_protocol 149 · CLAUDE.md 271. Flag any drift.
- MOUNT IS UNTRUSTED (Project content-cache bug serves stale copies) — EVEN THOUGH the founder refreshed
  the Project files this session, the cache can still lag. HEAD is the only source of truth; when a
  canonical doc is needed, ASK for the live paste. Canonical files under docs/ (CLAUDE.md at repo root);
  continuity pairs + register + supersession under docs/sessions/; operating_charter.md under docs/.
- Repo state: expect HEAD = THIS continuity pair's commit, on top of the doc-sync trail:
    2954171 (charter v2: Fashion-Intelligence-Network→post-pilot, agency removed, C6 store-average) ·
    7437ca0 (register + charter-supersession + charter v1) · 5a6bd3d (technical_architecture) ·
    09834fd (cross_alert_orchestration) · d695453 (product_strategy) · 33d337f (pilot_scope).
  VERIFY LIVE: `git log --oneline -8` and `git rev-list --count origin/master..HEAD` (expect 0 if the
  continuity commit was pushed). NOTE: docsync_findings_running.md (working ledger) is UNTRACKED unless
  the founder committed it — it holds the full findings history; the register is its durable extract.

## DONE THIS SESSION — the canonical-doc DOC-SYNC, closed
Reconciled the 9 canonical spec files against ~6 weeks of unrecorded decisions (the pivot to a
returns/profit-leak wedge, C8 the new hero). FOUR edited + committed, THREE no-edit, TWO clean by nature:
- pilot_scope.md (33d337f): HERO→C8 rename, 58→59, blended-ROAS all-channel, C8 TikTok caveat.
- product_strategy.md (d695453): 58→59 at 6 CURRENT sites (changelog line left as history), Group-C
  header C1–C8, NEW C8 §3D entry + summary row (detection/floor "pending" — NOT fabricated), 7 blended
  alerts gain Google (A2 also TikTok + made multi-channel), C3 "2×" neutralized, §5 pilot=5/post-pilot=6,
  C8 lineage note repointed to causal_graph.py.
- cross_alert_orchestration.md (09834fd): 41-type→59-type ×3 (COUNT ONLY; the 32 S41–S45 scenario IDs
  and the :650 illustrative namespace list deliberately UNTOUCHED).
- technical_architecture.md (5a6bd3d): HERO→C8 return-reason note (:1457) + 41-type→59-type (:1390) —
  2 edits; the 5 HERO_DRESS synthetic refs and all 26 Slack refs UNTOUCHED (Slack is load-bearing).
- NO-EDIT (read-first, confirmed): pre_agent_build_checklist ("37/56" are DATED build-log history — a
  blind swap would falsify records), d1_validation_gates ("blended" = return-rate average, not ad-spend),
  agent_d_build_spec ("2×" is a dated decision-record; :1726 blended already names all 3 channel-pairs).
  save_protocol + CLAUDE.md clean by nature.
- REGISTER created + committed (7437ca0): docs/sessions/pilot_readiness_register.md — durable
  pilot-readiness tracker (all OQ/BT/FC/PG/HK/CD items lifted from the ledger).
- DH-1 RESOLVED: docs/sessions/charter_facts_superseded_2026-07-02.md marks every stale charter fact
  superseded with committed sources; docs/operating_charter.md is the corrected charter (7437ca0 →
  2954171 with the (b)/(c)/C6 fixes). The Project INSTRUCTION was replaced with the corrected charter
  this session — the pre-pivot re-injection is FIXED at source.

## Key decisions locked (doc-sync)
- Library 58→59; C8 = Return-Driver (the wedge); pilot fired set C8/C1/C6/G1/C2.
- A2 now MULTI-CHANNEL (Meta+Google+TikTok) and RETIRED from the pilot fired set (C8 owns return-driver;
  A2 lineage "→ C8"). A1 post-return ROAS gains Google. All blended figures name every channel the brand
  runs + connected-vs-zero disclosure; an unconnected channel is never treated as zero spend.
- C3 "2× brand average" headline RETIRED → "abnormally high for that product / rarity vs own history."
- Delivery: PILOT = email (committed). FINAL-PRODUCT email-vs-Slack = OQ-12, decide post-pilot on
  evidence (tech-arch stays Slack-native by design meanwhile).
- Charter: Fashion Intelligence Network = POST-PILOT (confirmed vs pilot_scope — pilot is single-brand,
  no cross-brand accumulation); agency partnership = decided against, removed; critical path = 4–5 design
  partners (pilot_scope §8); C6 baseline = brand/store average (a new drop has no product-level history).

## CARRY-FORWARD / OWED (do not lose)
- BLUEPRINT RECONCILIATION = NEXT-SESSION FIRST TASK. Profit_Sentinel_Blueprint_v8.docx is the 4th source
  doc, UNAUDITED — it very likely still carries pre-pivot facts (old five alerts, Slack, $299, client
  targets). It is the ONE unreconciled source. When reconciled, re-check the charter's Blueprint-derived
  references AS A SET: "Blueprint Section 13," the Fashion Intelligence Network definition, the
  moat/Precision-Profit-Calendar framing. (Charter citations to product_strategy §3/§3D/§11/§12 and
  tech-arch §7/§9 were grep-verified ACCURATE this session — those do NOT need re-checking; only the
  Blueprint-derived lines do.)
- THE REGISTER is the home for all remaining build/decision/first-connect work — load it, don't re-list
  here. Includes the FIRED-alert sweep continuation (BT-4 wire C6/G1/C2 into Agent A; BT-2 C8 detection),
  the J-3-style raw-read/var-form audit as a standing sweep item, and BT-10/BT-11/BT-12 (A2 per-channel
  detection; C8 code lineage note; C3→S15 baseline wiring).
- DEEPER OWED-CHAIN (prior sessions) STILL UN-RECONCILED — carried, NOT closed this session (this was a
  doc-sync, not the build sweep): everything in state_2026-06-27_j2-close.md CARRY-FORWARD (J-1
  native-handle slot; regex-band assumption; inner-join undercount; J-3 honest boundary) AND the chain it
  carries back to state_2026-06-27_owed-i-close.md / state_2026-06-25_durable-rls-bc.md (seed_meta
  own-arc; RLS-probe keep/delete; suppression_log REVOKE; full-public-history secret scan; owed D/E/F/G;
  R2 five foundational DDLs; N1–N5; ADD-1/2). Diff the next continuity pair against these before its commit.

## NEXT ACTION
1. Blueprint reconciliation (founder's call) — then re-check the charter's Blueprint-derived lines.
2. Then the register drives pilot-readiness (C8/C6/G1/C2 detection wiring + the J-3-style audit).
Recruitment of 4–5 design partners remains the TRUE launch gate (pilot_scope §8) — all build work has no
value until real brand data connects.

## METHOD / CADENCE (non-negotiable)
- PUSH MODEL (clarified this session — supersedes the old "NO push from Claude Code" line): the founder
  authorizes both COMMIT and PUSH through Claude Code. Claude Code PRESENTS the command and executes ONLY
  on the founder's explicit, single-use in-chat authorization — never autonomously, never batched.
  "Founder runs all pushes" = founder triggers them via Claude Code, not that Claude Code is forbidden.
  [Position change (b): the prior continuity's "NO push from Claude Code" was under-stated.]
- READ-ONLY discovery before every write. Writes gated, fail-closed, reversible, staged by EXPLICIT path
  (never git add -A/.), paste-before-commit.
- Continuity pair authored in chat (downloadable), critiqued ×3, Claude-Code-VERIFIED (handles + scoped
  diffs only — Claude Code NEVER authors continuity files and never "updates project memory").
- save_protocol.md governs every save. MOUNT UNTRUSTED → reason from HEAD / pasted live text (holds even
  after the founder refreshed the Project this session — the cache can still lag).
- Position changes named: (a) new fact / (b) correction of under-tested prior work.
