# Chat Context — 2026-07-02 — Canonical-doc DOC-SYNC closed (5 files + register + corrected charter)

> Narrative companion. AUTHORITATIVE state + SESSION OPEN + owed set:
> state_2026-07-02_docsync-close.md (100 lines). Load that first; this file is the story,
> not the source of truth.

## What this session was
The EDIT-AND-COMMIT phase of a doc-sync: reconciling the 9 canonical spec files against ~6 weeks of
unrecorded decisions from the product's pivot to a returns/profit-leak wedge (C8 the new hero). The
prior COLLECTION phase had built the decision ledger (docsync_findings_running.md); this session edited
each file one at a time — whole-file authored in chat → scoped-diff verified against clean HEAD via
Claude Code → founder committed + pushed — then created the pilot readiness register and resolved the
stale operating charter (DH-1).

## How it went — the read-first discipline earned itself, repeatedly
Every file was read in full BEFORE editing, and that caught a corruption trap in almost every one:
- pilot_scope: the HERO→C8 rename would have hit HERO_DRESS synthetic data — grep-guarded away.
- product_strategy: a "58" on a DATED changelog line was left as history (blindly bumping it would
  falsify the record); and a false-FAIL — the verification flagged the APPROVED TikTok clause as
  out-of-scope — was traced to an under-declared checklist (my error), NOT a bad edit, and fixed by
  sourcing the approved-set from the ledger rather than recall.
- cross_alert: "41-type" appeared 5× but only 3 were the library count — the other 2 were S41/S42 etc.
  SCENARIO IDs (32 refs total). A blind 41→59 would have corrupted the orchestration logic.
- pre_agent_build_checklist: "56/37" are DATED build-log records (validation runs at ffa128f, B-5
  milestones) plus one data value (tiktok_leads 37) — NONE a current count. NO-EDIT was correct; a
  blind swap would have been the worst corruption of the sweep.
- technical_architecture: the HERO→C8 rename was ONE alert line (:1457); the other 5 "hero" hits were
  HERO_DRESS synthetic. And Slack turned out LOAD-BEARING (schema slack_thread_ts/channel NOT NULL,
  Bolt data flow, "founder never leaves Slack") — so "Slack→email" is NOT a find-replace; it became a
  deferred post-pilot decision (OQ-12), and tech-arch stays Slack-native by design.

## Position changes named
- (b) CAO-1 scope: "41-type ×3 = a clean count swap" → 3 count-only edits with 32 S-IDs off-limits (the
  ledger entry was under-tested; the live read corrected it).
- (b) A2 in the blended edit: first EXCLUDED it as "not a blended figure" → RESTORED it — the founder's
  point was sharper (a ROAS-drop root-cause is incomplete if it ignores channels the brand runs;
  multi-channel ≠ blended). A2 became multi-channel + a build task (BT-10).
- (b) the C8 §3D "see lineage note on A2" was a DANGLING ref (no such note existed) → repointed to
  causal_graph.py where the lineage actually lives (Flag-2 fix, caught by Claude Code verification).
- (a) TWO source docs (d1_validation_gates, agent_d_build_spec) had never been checked for the
  rename/blended refs (the earlier sweep was count-only, pre-C8) → read this session, both confirmed
  clean; surfaced BT-12 (C3→S15 wiring, from a dated decision-record in agent_d).
- (a) the CHARTER re-injection source was finally identified: the OLD charter was the Project
  INSTRUCTION (auto-prepended every turn), NOT the uploaded file — which is why the corrected file kept
  "reverting." Replaced the instruction this session → re-injection fixed at source.
- (b) push model: "NO push from Claude Code" → founder authorizes commit AND push via Claude Code
  (recorded in the state METHOD block, per the founder's standing instruction).

## The charter / DH-1 resolution
DH-1 (the stale operating charter) was the highest-value doc-hygiene item — the charter described the
PRE-PIVOT product: old five alerts, Alert 2 = ROAS-drop root cause (Meta+Shopify), 20 beta clients,
Slack, $299, and a seed_design_decisions.md that doesn't exist. Resolved by three moves: (1) a
supersession record citing the committed source for each stale fact; (2) a corrected
operating_charter.md (stance/protocols preserved VERBATIM, only facts fixed); (3) replacing the Project
instruction with the corrected charter. Two founder rulings finalized it this session — 20-beta-clients
KILLED (→ 4–5 design partners), agency partnership decided against — and the Fashion Intelligence Network
was confirmed POST-PILOT against pilot_scope (single-brand pilot, no cross-brand data accumulation). The
Blueprint — the 4th source doc — is the one piece NOT yet reconciled; it's next session's first task, and
the charter's Blueprint-derived lines get re-checked then.

## What's next
Blueprint reconciliation (next session), then the register drives the remaining pilot-readiness build
work (C8/C6/G1/C2 detection wiring, the J-3-style raw-read/var-form audit). Recruitment of 4–5 design
partners is the true launch gate throughout — the doc-sync made the docs tell the truth about the
pivoted product, but none of that has value until a real brand connects.

## Method notes carried
- Mount untrusted (even after the founder refreshed the Project — the cache can lag); reason from HEAD /
  pasted live text. save_protocol live (149).
- I author edits + continuity in chat; Claude Code VERIFIES on disk (handles + scoped diffs), never
  authors continuity, never "updates project memory." Every edit surgical, authored against live text,
  explicit-path staged, paste-before-commit.
- The deeper owed-chain (back to 2026-06-25) is STILL un-reconciled — carried, not closed (this was a
  doc-sync, not the build sweep).
