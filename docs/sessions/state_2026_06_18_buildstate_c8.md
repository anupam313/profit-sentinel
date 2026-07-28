# Profit Sentinel — State: 2026-06-18 (build-state verification closed · HERO=C8 code locked · next = OP-1)
## Date: 2026-06-18 · Session: buildstate_c8 · Status: NO file edits made this session to the canonical/pilot
##   spec files. All repo changes this session were CODE + CLAUDE.md and are ALREADY COMMITTED (hashes below).
##   The C8 alert edit is DESIGNED-IN-PART and SCAFFOLDED but NOT executed — it runs as ONE pass AFTER OP-1.

> NEXT SESSION — LOAD FIRST: the 7 canonical files + save_protocol.md + pilot_scope.md + this file + its
> chat_context (chat_context_2026_06_18_buildstate_c8.md). Run the VERIFICATION GATE (line counts at the
> bottom) BEFORE any edit. THEN open OP-1 (the returns-baseline grouping/abnormality method). Do NOT edit
> any spec file before OP-1 is resolved — the C8 entry's detection fields are GATED on OP-1 (see below).

---

## WHAT THIS SESSION DID (no spec-file edits; build-state verification + one code decision)
1. **Closed Step 1 — verified the REAL build state from the repo** (the resume's #1 task). Findings, all
   verified via Claude Code greps + my reads of the uploaded files:
   - **causal_graph.py** — 962-line hardcoded structured-dict registry (NOT a DAG/traversal engine, by
     design). **57 distinct chains** (A1–A7, B1–B5, C1–C7, D1–D6, **E1–E4**, F1–F5, G1–G4, H1–H19 =
     38 business + 19 system). **Missing E5** (one behind the library's 58). **ORPHANED** — nothing imports
     it; three trivial getter funcs only. 16 of 57 chains run on `active_proxy`/`mart_column_missing`
     (google_roas/google_attributed_orders absent from mart; google_spend in CTE only). COMMITTED `d52ffde`.
   - **agent_a.py** — 932-line LangGraph 5-node pipeline (load_context → run_threshold_checks →
     apply_suppression → write_alerts → build_summary), deterministic, zero LLM calls. Scans **8 signals:
     A1, A2, B1, B4, C1, D1, E2, F2.** Does NOT import causal_graph. **ORPHANED** (only a path-STRING ref in
     slack_bot/test_delivery.py; nothing imports it as a module). Carries a hardcoded 55% gross-margin in D1
     (No-Seed debt, TODO in code). COMMITTED `692f52a` (+ .gitignore rules for __pycache__/target/logs/.claude).
   - **dbt marts** — 5 exist (mart_causal_chain_daily, mart_cross_source_daily, mart_customer_segments_daily,
     mart_net_revenue_daily, mart_return_rate_by_sku). `dbt parse` PASSES (1.11.9). All fired-set columns
     physically present in mart_causal_chain_daily.sql. Schema = **client_azure_co_marts** (canonical;
     consistent across dbt macro, agent_a.py, historical_pattern_scan.py — verified, NO discrepancy).
   - **Reuse finding** — `connectors/historical_pattern_scan.py` (Onboarding Step 11, a ONE-SHOT validation
     scan that writes to causal_pattern_validation/candidate_signals/client_config — NOT a continuous alert
     emitter) already contains reusable rolling-window detection MATH for return_rate / net_revenue /
     avg_days_to_refund; stockout partial. **Only agent_a.py emits to alert_log.**
   - **THE GAP (the substantive build question):** of the 5 fired alerts, Agent A covers **only C1**.
     C8(HERO), C6, C2, G1 key on columns Agent A never reads (return_rate_pct not scanned at all; net_revenue;
     stockout_with_active_spend_count; tiktok_roas only as an A1 corroborator). So 4 alerts need detection
     WIRING into Agent A's threshold→suppression→alert_log path — but the MATH is largely reusable from
     historical_pattern_scan.py, so it's net-new WIRING, not net-new logic.
   - **"Never fired" correction (settled):** the 4 uncovered alerts were never emitted — they are the pilot
     PLAN, not a firing history. Test logs only ever showed A1/C1/E2. No regression, no mystery component.
2. **Doc-hygiene fixes (all committed, all out of the way):**
   - CLAUDE.md schema description corrected to 3 schemas (client_azure_co / _staging / _marts) + names the
     generate_schema_name macro; Rule 1 discovery-query example genericized (was hardcoded to client_azure_co,
     silently missed marts/staging — a real false-"column missing" trap). COMMITTED `177bb4d`.
   - Phantom `docs/blueprint.md` reference removed from CLAUDE.md read-list (file never existed in any format;
     its remit lives in product_strategy.md §7). "three files" → "two files". COMMITTED `fd545db`.
   - Memory (`schema_drift_rules.md`) — added a TRIMMED finding ("schema question resolved 2026-06-18, both
     runtime components verified on client_azure_co_marts; convention's home is the macro — don't
     re-investigate"). The per-schema convention bullets were REMOVED (they'd be a stale 3rd copy). MEMORY.md
     index reverted to original. Memory POINTS to the home, does not COPY it.
3. **OneDrive scare — repo intact, fix DEFERRED.** A OneDrive "delete 370 items" dialog fired; the items were
   git internals (hash-named objects, packs/refs), not docs. `git fsck` clean, all tracked files present,
   commit chain whole. Founder clicked "Keep". **The repo lives INSIDE OneDrive — a live corruption risk
   (sync layer touching .git). Founder chose to DEFER the .git-exclusion fix.** Carry as a LIVE risk: the
   next chat's C8 edit + commits increase .git churn.

## LOCKED (decided this session — hard to reopen)
1. **HERO alert code = `C8`** (Group C — "Returns and Product Quality"; the return-driver is a returns alert
   linking source→product-level returns). Clean **+1: library count 58 → 59** (40 business + 19 system).
   Chosen via OPTION B (fresh code + retired-A2 pointer), NOT reuse-A2 (Option A) and NOT plain-fresh (C).
2. **A2 = retired-from-PILOT, NOT deleted from the library.** A2 stays a defined, counted library chain
   (its Meta-CPM→ROAS detection logic is real, lives in Agent A's 8 signals). It is simply not in the pilot
   fired set. A one-line lineage note goes on A2's causal_graph entry: "return-driver concern now owned by C8".
   (A2 net-zero-cancels-C8 was REJECTED: only deleting A2 from the library would cancel the +1, and that
   would orphan working Meta-CPM detection code — not worth a cosmetic count save. So it is a clean +1 → 59.)
3. **E5 = HELD (NOT added to the pilot).** Founder first said "add E5", I pushed back (off-thesis Klaviyo
   deliverability; carries the O-26 hardcoded-75%-floor debt; E1/D5 suppression dependents not in pilot;
   parked E5/E6 reconciliation), founder agreed to HOLD. The fired set is unchanged. Do NOT re-add E5.
   NOTE: E5 already EXISTS in the product_strategy §3D library (count 58 includes E5) — the HOLD is about the
   PILOT fired set, not the library. causal_graph.py is separately missing E5 (57); do NOT fix that while
   adding C8 — the C8 pass adds ONLY C8.
4. **Fired pilot set (naming updated): C8 (return-driver) · C1 · C6 · G1 · C2.** ("HERO" is now an informal
   alias for C8 only.) In-app metrics + plumbing unchanged.
5. **The C8 edit runs as ONE pass AFTER OP-1.** No spec-file edits before OP-1. Reason: a causal_graph entry's
   fields ARE the detection spec, and C8's core field (abnormally-elevated return rate by product, "returns
   at 2× your average") is exactly what OP-1 defines. Writing it pre-OP-1 = provisional-as-locked.

## THE PENDING C8 EDIT — SCAFFOLD (Phase-0 ledger; execute AFTER OP-1, as ONE save-protocol pass)
Targets and decisions (so the next chat does NOT re-derive this):
- **causal_graph.py** (Claude Code): add C8 entry (~13–14 lines; a standard C-entry is 11 fields, cf. C6 at
  lines 328–338) + the A2 retirement-lineage note (~2 lines). Expected delta ≈ 962 + ~16 ≈ ~978.
  **C8's detection FIELDS are GATED on OP-1 — design them after OP-1, then write.** Anchor: `"causal_chain_id": "C8"`.
- **pilot_scope.md** (Claude Code): "Return-driver (HERO)" → "C8 (return-driver)" in the fired set, AND fix
  its OWN two "58" mentions (lines 21, 98) → "59" (we're in the file anyway; don't leave it self-inconsistent).
- **product_strategy.md** (FOUNDER does this MANUALLY, uploads for validation): the count reconciliation —
  6 in-place swaps + 1 new table row. The 7 homes (verified this session): :58 ("contains 58 alert types"),
  :232 ("Full 58-Type Specification"), :236 ("58 alert types"), :354 ("(C1–C7)" → "(C1–C8)"),
  :1093 ("not yet in the 58"), :1420 ("The 58 validated alert types"), + a NEW C8 row in the §3D summary
  table. ROUTED (not edited this session). Expected delta = 1422 + 1 (the new table row; the 6 swaps are
  net-zero). **§3D TABLE STRUCTURE IS STILL UNREAD — read the table before giving the founder the exact C8
  row format; do NOT guess it.**
- **Save protocol applies** (product_strategy + pilot_scope are/near canonical): run Phase 0 ledger → Phase A
  declarations → edit → Phase B (Check-1 line handles, Check-7 scoped diff = the "nothing deleted" guard,
  Check-6 anchors-once) → Check-10 semantic read-back (me) → founder ACCEPT. Mechanical checks run in Claude
  Code (I have no repo access); ledger + read-back are done in chat.

## OPEN (carries what closes it)
- **OP-1 — THE IMMEDIATE NEXT ITEM.** The returns-baseline grouping/abnormality method = C3's yardstick,
  reused by C3 / C6 / C2 and now **C8**. It defines what an "abnormal" return rate IS (by product/cohort),
  which is C8's leading signal. STATUS: open. The C3-foundation work that surrounds it was AGREED-IN-CHAT but
  NEVER written to canonical (lives in state_2026_06_10_c3_foundation_abnormal_bigenough_new.md + its
  chat_context). Treat those AL-items as provisional, not locked. Resolve OP-1 first; it unblocks C8's fields.
- **Series-fit caveat on C8:** judged a Group-C returns alert. If, in design, it proves to be more a
  channel/collection-ATTRIBUTION alert than a returns alert, revisit the letter BEFORE anything is written.
- **§3D summary-table structure** unread — read before composing the C8 row.
- **causal_graph.py missing E5** (57 not 58) — a known graph-vs-library gap, SEPARATE from C8. Do not fix in
  the C8 pass. Also a GUARD: do NOT wire causal_graph into Agent B until E5 + its E1/D5 suppression edges land
  and E5/E6 doc reconciliation is done (recorded in d52ffde's commit message).
- **OneDrive .git-exclusion** DEFERRED by founder (live corruption risk; more churn coming with C8 commits).
- **Working-tree untracked files** (slack_bot/ = RETIRED, connector seeds, mart_customer_segments_daily.sql,
  _-prefixed scratch) — a broader baseline pass, deferred; do NOT baseline slack_bot.
- **Pre-existing OPEN (carried from 2026-06-14, none blocks the pilot build):** cross-file stale roster
  counts (tech-arch:1348 "41-type"; cross_alert:11/38/643 "41-type"; checklist:111/229 "56", :21 "37") — fix
  ALL together in the consolidated/registry pass, not piecemeal; 1368/O-15 E5/E6 reconciliation flip (parked);
  O-26 hardcoded-floor revisit (E5 75% floor) after Gap 6; D6 single-seasonal-authority question; the
  DEFERRED registry build (post-pilot SCALE infra — full design carried in the 2026-06-14 state file, do not
  pull forward).

## COMMITS THIS SESSION (audit trail)
`d52ffde` causal_graph.py (authored, unwired) baseline · `692f52a` agent_a.py + .gitignore rules ·
`177bb4d` CLAUDE.md schema fix + Rule-1 query genericized · `fd545db` removed phantom blueprint.md reference.
(All on master; on top of prior `4ce8d42`/`ead47a2`.)

## WORKING RULES (standing — carry forward unchanged)
- Three genuine deep passes before any recommendation; founder flags if skipped.
- Genuine pushback when disagreement exists; hold correct positions, revise only on a valid challenge.
- One open item at a time with explicit sign-off before moving on.
- CHECK-BEFORE-ANSWER: verify every number/line/file claim with a tool THIS turn (stale-by-turn); tag
  verified / inference / unchecked; list what an edit forces before editing; end each substantive answer with
  what was checked + the one thing most likely still wrong.
- Verify before propose (show the greps/actual lines first). Complete files, never patches. Design in chat;
  batch engineering code to a Claude Code build prompt. Plain language; gloss any code inline.
- I have NO repo or local-disk access — only the read-only project mount + founder uploads. All repo
  reads/edits run in Claude Code; mechanical save-protocol checks run there too.

## HONEST FLOOR (what the checks/this handoff cannot guarantee)
- Build-state findings rest on Claude Code's greps (which I cannot independently run) + my reads of the
  UPLOADED causal_graph.py. If the repo's agent_a.py differs from what was reported, the "8 signals / orphaned"
  picture shifts.
- C8's series fit (Group C) and its assumed leading signal (return-rate-by-product) are INFERENCE pending the
  OP-1-gated detection design — not locked.
- Phase 0 of any later save rests on reading the whole conversation — the irreducible human floor.

---

## NEXT SESSION — VERIFICATION GATE (canonical line counts; STOP if any differs)
NO spec file was edited this session, so all canonical counts are UNCHANGED from the 2026-06-14 close:
agent_d_build_spec=2710 · technical_architecture=3818 · cross_alert_orchestration=840 ·
product_strategy=1422 · d1_validation_gates=386 · pre_agent_build_checklist=389 · save_protocol=149.
pilot_scope=122 (non-canonical count-home).
NOTE: CLAUDE.md changed this session (commits 177bb4d, fd545db) but is OUTSIDE this gate. causal_graph.py is
now committed at 962 lines, agent_a.py at 932 (code files, not in the doc gate — listed for build reference).
(This pair's own line counts are handed over in the session report / digest.)
