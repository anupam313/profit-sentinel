# Profit Sentinel — State: Pilot Structure (OP-PILOT-1 CLOSED)
## Date: 2026-06-13  ·  Session: pilot_structure  ·  Status: closeable package, edit session not yet run
## Supersedes nothing — sits after state_2026_06_13_pilot_pivot.md (kept as audit trail).

> NEXT SESSION — LOAD FIRST: the 7 canonical files + save_protocol.md + this file + its
> chat_context. Run the verification gate (line counts below) BEFORE any edit. Then run the
> edit session in the order at the bottom. Nothing is written to a canonical file until the
> executable checker passes AND the judgment digest is reviewed (the minimal human floor).

---

## WHAT THIS SESSION DID
Closed OP-PILOT-1 (how the pilot is structured across docs, code, and repo). No canonical
file was edited this session — only this state file and its chat_context were created. The
edit session that applies the decisions below is the NEXT thing to run.

---

## LOCKED (hard to reopen)
1. **One product, no fork.** The pilot IS the full product earlier in its life — same engine
   (Agent A/B/C/D, DQ layer, suppression and orchestration [TWO distinct engines: suppression =
   don't fire a known-explained/stale signal; orchestration = resolve collisions when two alerts
   fire on one event], parser, Evidence Stack, NLQ, app + email). Differences are only: (a) a
   smaller causal graph (5–10 chains, grows on real data), (b) a human relevance-gate before
   delivery, (c) SCALE (few brands vs many — which is why cross-client learning stays off, per #2).
   NOTE: per-brand eligibility is UNIVERSAL (applies to pilot and full alike), NOT a difference —
   it is the runtime model described in CONFIRMED.
2. **Agent B is NOT deferred.** Build the traversal + corroboration + confidence engine now,
   over the small graph. Only the self-extending / novel-chain cross-client promotion is later
   (already a separate track — post-10-client, DEBT-T1), and that promotion is HUMAN-REVIEWED
   (a person approves a novel pattern before it is hardcoded), NOT an automatic flip at scale.
   Building Agent B now removes the throwaway-detection rework and gives the core hypothesis a fair test.
3. **Three layers, one truth each.** Specs (the laptop/OneDrive folder is the truth); code
   (git); config (the registry). Sync direction is one-way: edit local → push git → re-upload
   to the Claude Project. The line-count verification gate is the drift detector. CAVEAT:
   OneDrive can spawn conflict copies (`...-DESKTOP-xyz.md`) that silently break the line-count
   gate — treat any such filename as a fire, and lean on git (not OneDrive) as the authoritative
   history/backup.
4. **KEEP state + chat_context files in the Project.** (Claude's earlier "archive them out"
   suggestion was RETRACTED — it contradicted a standing, repeatedly-confirmed decision and
   relied on a confusion the verification-gate workflow already prevents.)
5. **Git docs/ is stale — verified this session.** docs/product_strategy.md = 449 lines (live
   1416); docs/technical_architecture.md = 925 (live 3815); the other 5 specs are absent.
   Push current copies of all 7 specs to docs/ BEFORE editing; TAG pre-pilot-baseline only
   AFTER the stale fixes, so the tag captures a corrected baseline, not the errors.
6. **Namespace convention ADOPTED:** ALERT- (canonical alerts) / DEC- (seed-script decisions)
   / S- (suppression rules) / SCEN- (scenarios). Operative home = the registry header;
   product_strategy §12 note flips from "adopt at doc pass" to "adopted." All new alert refs
   (and pilot alerts in conversation) use the ALERT- form.

## CONFIRMED (stable, build on it)
- **Registry = a separate machine-readable file (YAML), keyed to §3D by alert ID.** It OWNS
  only: `id` (ALERT-<§3D code>, or METRIC-<n> for in-app metrics not in §3D), `type`
  (fired-alert / in-app-metric / internal-plumbing), `status` (lifecycle), `routing pointer`
  (merged_into / feeds — nullable, minimal). It does NOT restate §3D's name, connectors,
  actionability, verification category, confidence floor — one fact, one home. Content =
  formalize pilot_scope §4.
- **Status values are lifecycle-NEUTRAL** (survive the pilot→full transition): backlog /
  in-development / shadow / gated-live / live / retired. `backlog` = parked/roadmap, valid-future
  but not being built now (pilot_scope §4 PARK); `in-development` = actively building; `shadow` =
  running but not founder-facing (collecting validation); `gated-live` = pilot mode (human gate on);
  `live` = graduated / autonomous; `retired` = killed. Growth 5→6→7 and pilot→full are status
  flips, not schema changes.
- **Per-brand eligibility is computed at RUNTIME** (a brand's connected sources vs §3D's
  required connectors), never stored as per-brand rows. Universal logic + per-brand connection
  state. Graceful degradation reads required-connectors from §3D (already there) — registry
  does not duplicate it.
- **Value-vs-moat filter (the promotion criterion — pilot_scope §3).** Which alerts are worth
  building/promoting during the pilot is judged on VALUE (is the founder getting this today? —
  proactive alerting, skipped inference, and cross-source causal depth all add value, even on
  single-source metrics) and MOAT (can Shopify or a cheap app copy it? — cross-source joins are
  defensible; single-source + threshold is not), conditional on EXECUTION DEPTH (a shallow ping
  is commodity). This filter governs §3D-completeness and registry growth so growth does NOT
  drift toward all 57.
- **The human gate = a correctness LOG** (two columns: my-verdict-vs-system; founder-outcome-
  vs-system). Three exits: send / reject / suppress. Max 1-day latency; intraday fast-lane for
  G1. NLQ answer-or-abstain is a launch surface.
- **Failure-mode resolutions:** (1) calcification → `status` is governed by the O-31 discipline
  (changes only by a deliberate logged evidence step, never ad-hoc) — an EXTENSION of O-31,
  which was written about dials. (2) relationship duplication → cross_alert keeps relationship
  ownership; registry holds the routing-minimal pointer only. (3) format → one YAML source of
  truth; any rendered view is generated, never hand-maintained (field-names confirmed at build).
- **Verification mechanism (replaces full human sign-off, which Anupam can't give at this
  complexity):** run the existing save_protocol; make Checks 1–9 an EXECUTABLE checker script
  (re-runnable, not self-attested); produce a JUDGMENT DIGEST (3–5 lines per save) of only the
  items no self-check can verify. Anupam reviews the digest — the minimal human floor — not the
  whole file.

## PROVISIONAL (must NOT calcify)
- The alert disposition (pilot_scope §4) and "returns intelligence as PS's durable identity"
  remain shaped, not locked. The registry STRUCTURE is fixed; `status` VALUES are mutable.

## THE THREE CALLS SIGNED OFF THIS SESSION (were judgment, now decided)
- **E5 (Deliverability Risk) = High-actionability alert** (Klaviyo; Verification B; ~65% floor).
  Root cause behind E1; suppresses E1.
- **E6 (Klaviyo Revenue Seasonality) = internal plumbing**, NOT a fired alert (a baseline/
  context signal, like D6).
- **A2 (Root Cause of ROAS Drop) = park-DISTINCT, NOT merged into return-driver.** A2 is broader
  (non-returns causes too); return-driver covers only its returns slice. Marking it "merged"
  would risk silently dropping the broader capability later.

## OPEN (carries what closes it)
- **Registry POPULATION** — per-alert, with a judgment digest each; next active item.
- **§3D completeness** — the hole is wider than E5/E6 (E7–E40, B6–B16, A8–A18 unclassified);
  closed by the CLASSIFICATION TASK (alert / decision / scenario), with E5/E6 as its first two
  entries — but E5 and E6 are NOT symmetric: E5 gets a §3D alert row, E6 is recorded as plumbing
  (type=internal-plumbing; the way H-series plumbing already sits in §3D), NOT a fired-alert entry.
  Decoupled from the COGS-blocked O-26 doc pass — runs near-term on its own.
- **Graduation threshold** (N correct outcomes across M brands → gate off per alert) — parked,
  revisit at first pilot client. At-scale gap flagged: global graduate-flag ignores per-brand
  reliability variance — may need per-brand/segment later.
- **Identity question** — returns-intelligence as the durable product identity — Anupam to decide.

## EDIT-SESSION ORDER OF OPERATIONS (next session, each step: draft → checker → digest → apply → push → re-upload)
1. Push current 7 specs into git docs/ (default branch is `master`, not `main`), commit. (Preserve; do NOT tag yet.)
2. Classification task: classify E7–E40 / B6–B16 / A8–A18 into ALERT-/DEC-/SCEN-; add E5 to §3D
   as an alert row, and E6 as a plumbing entry (NOT symmetric — E6 is internal plumbing). Output:
   hole-free §3D + disambiguated namespaces.
3. Fix stale specs (save protocol): product_strategy (kill old five-alerts + six-model
   attribution); technical_architecture §11 (mention docs/).
4. Tag pre-pilot-baseline (now clean + complete).
5. Create the registry (YAML, agreed schema); flip §12 convention note to "adopted"; convention
   text in registry header.
6. Code: registry-driven routing + graceful degradation, batched into the consolidated Claude
   Code prompt (not run incrementally during design).

## WORKING RULES (adopted this session, standing)
- Verify before propose (show the file reconnaissance first).
- Label every load-bearing claim: verified-from-file / inference / unchecked-assumption; treat
  unchecked as a TODO to check before relying on it.
- State what would make it wrong, in the first answer (front-load the failure-mode hunt).
- One file/item at a time; complete files, never patches; design here, build in Claude Code.

## CARRY-FORWARD — DO NOT LOSE
- B-9 Google Ads `cost_micros ÷ 1,000,000` when reading into the mart column (confirm direction).
- E5/E6 reconciliation now folded into the classification task (Open, above).
- PARALLEL TRACKS (non-gated; do NOT deprioritize — homes in pilot_scope §6/§7): (1) recruitment
  is the BINDING CONSTRAINT (no committed design partners; Aman cold) — slower than any build step;
  (2) Shopify approvals — PCD + read_all_orders, custom distribution app, start now; (3) Google Ads
  developer token — the real long pole, start now; (4) Indian entity registration — for the Google
  token, DPA credibility with VC-backed brands, and liability shielding. The doc/code work must not
  crowd these out.
- At-scale gaps flagged for later: global-vs-per-brand graduation; metric-definitions split-home.

## NEXT SESSION — VERIFICATION GATE (canonical line counts; STOP if any differs)
agent_d_build_spec=2710 · technical_architecture=3815 · cross_alert_orchestration=840 ·
product_strategy=1416 · d1_validation_gates=386 · pre_agent_build_checklist=389 ·
save_protocol=149. (These continuity files' own counts are handed over in the session report.)
