# Profit Sentinel — State: Pilot-Pivot Documentation Edit Plan
## Date: 2026-06-14 · Session: edit_plan · Status: PLANNING COMPLETE — no canonical file edited yet
## Replaces the EDIT-SESSION ORDER OF OPERATIONS in state_2026_06_13_pilot_structure.md
##   (the old 6-step plan → the 2-session plan below). The prior file is kept as audit trail.

> NEXT SESSION — LOAD FIRST: the 7 canonical files + save_protocol.md + this file + its
> chat_context. Run the VERIFICATION GATE (line counts at the bottom) BEFORE any edit.
> The next session is SESSION 1 of the 2-session plan below: sort the codes + fix the count.
> Nothing is written to a canonical file until the executable checker passes AND the
> judgment digest is reviewed (the minimal human floor).

---

## WHAT THIS SESSION DID
Planned HOW to document the pilot pivot. NO canonical file was edited — only this state file
and its chat_context were created. Decided a 2-session edit plan (replacing the prior 6-step
order-of-operations), corrected several earlier mistakes (logged below), and produced this
pair as the continuity mechanism. The edit work itself is the NEXT thing to run.

---

## THE 2-SESSION PLAN (this replaces the 6-step order-of-operations in the prior state file)

### SESSION 1 — Sort the codes + fix the count
1. Go through the ~50 extra code-names (A8–A18, B6–B16, E7–E40) in the three
   "Seed Script Design Decisions" files (gap_abc_decisions.md, seed_decisions_gap_d_e.md,
   seed_decisions_gap_f_g.md). Confirm they are seed DESIGN DECISIONS / SCENARIOS, NOT alerts.
   They need NO relabelling and NO central lookup table — those files already self-identify
   as decision files on the cover ("Profit Sentinel — Seed Script Design Decisions").
2. Pull the genuine NEW ALERTS hiding among them into the alert library (§3D of
   product_strategy). Confirmed one: "Deliverability Risk" (E5). The scan must adjudicate any
   others the seed files flag as "New Alert" (candidates seen: H6/H7 mentions — may collide
   with existing §3D H-codes rather than being new; "new alert variant" mentions are variants
   of existing alerts, not new codes).
3. Record "Klaviyo Revenue Seasonality" (E6) as a BACKGROUND SIGNAL (internal plumbing), NOT a
   fired alert — represented the way the system-health (H-series) plumbing already sits in §3D.
4. SETTLE THE FINAL ALERT COUNT (output ONE number). Verified true total TODAY = 57
   (38 business A1–G4 + 19 system H1–H19). Adding "Deliverability Risk" = 58. THEN decide
   whether the "Klaviyo Revenue Seasonality" background signal counts toward the total —
   system-health plumbing IS counted today, so consistency may push to 59. This is a rule to
   DECIDE in Session 1, not assume.
5. FIX the count everywhere it is stated wrong (currently a mix of 41 / 56 / 57) in
   product_strategy: lines 58, 232, 236, 250, 1087, 1357, 1414. ADD the missing summary-table
   row: "A7 — Wholesale Order Contamination Warning" (defined at line 302 but ABSENT from the
   summary table — that omission is the source of the wrong "56"). FIX the broken explanation
   at line 250 ("the original 41 types counted A–G groups only" — wrong; A–G business = 38,
   not 41).

### SESSION 2 — Remove outdated wording → snapshot label → build the status file
1. Remove the outdated "FIVE PROACTIVE ALERTS" framing across its stale homes in
   product_strategy: lines 54, 58, 124, 1099, 1324, 1328. LEAVE lines 1260 and 1295 ALONE —
   those two are interview-scoring lines in the Customer Discovery Framework (§11), a
   deliberate yardstick, not stale product copy. Annotate (do not blindly overwrite) the two
   that sit INSIDE logged closed decisions (1324, 1328).
2. Remove the outdated "SIX ATTRIBUTION MODELS" promise. In the onboarding questions (§5, the
   chooser at ~line 943) state the single pilot default: CLICK-BASED, TIME-DECAY, 14-DAY;
   chooser DEFERRED to post-pilot; KEEP the six-model design as the future full-product target
   (do NOT delete it). Fix the two leftover copies of the chooser idea: line 67 (the
   attribution note under the first alert) and line 1332 (the closed-decision in §12).
3. technical_architecture §11 — add a mention of the docs/ folder.
4. Clean the stale patch cruft at product_strategy lines 736–738 (leftover "insert §3C here"
   instructions; §3C itself is correctly in place at line 148 — only the 3-line header is junk).
5. Apply the git snapshot label "pre-pilot-baseline" (now clean + complete).
6. Create the small status-tracking file (the registry, a separate machine-readable YAML keyed
   to §3D by alert ID; owns only id / type / status / routing-pointer; does NOT restate §3D
   facts). Flip the §12 naming-convention note from "adopt later" to "ADOPTED", add the missing
   "SCEN-" to its example, and put the convention text in the status-file header.

### AFTER the two sessions (separate tracks, do NOT crowd out)
- The registry-driven routing + graceful-degradation CODE is batched into the consolidated
  Claude Code prompt — build, never run incrementally in a design session.
- The broader cleanup of the OTHER FIVE documents (pilot-flow edits to technical_architecture
  beyond §11, cross_alert, agent_d, d1_gates, pre_agent_build_checklist, save_protocol) is a
  LATER pass — already written down in state_2026_06_13_pilot_pivot.md lines 168–183, so not lost.

---

## LOCKED (decided this session, hard to reopen)
1. **Two sessions, not one.** The ~50-code sort and the heavy wording edits do not share one
   chat (reliability degrades as a chat grows long); the snapshot label is a natural break.
2. **Classification stays MINIMAL.** No central lookup table; no edit to cross_alert for this.
   The ~50 decision codes need no relabelling (their files self-identify); only the genuine
   alerts move into the library; the naming rule lives in the status-file header.
3. **Continuity = a state + chat_context PAIR** (not a short paragraph — scope outgrew that).
4. **Settle ONE alert count in Session 1** rather than carrying 57/58/59 forward.

## CONFIRMED (stable mechanism, build on it)
- **Save mechanism (unchanged from prior session):** run save_protocol.md; make the mechanical
  checks (1–9) an EXECUTABLE, re-runnable script (not self-attested); hand a 3–5 line JUDGMENT
  DIGEST of only what no check can verify. Human review of list + digest stays — not zero.
- **Verified true alert count = 57** today (38 business + 19 system), by direct enumeration.

## OPEN (carries what closes it)
- **Does "Klaviyo Revenue Seasonality" count toward the alert total?** — settle in Session 1.
- **Returns-identity question** (is returns-intelligence the product's durable identity?) —
  Anupam decided NO this session; it stays OPEN; §12 only points to it, does not close it.
- **At-a-glance index of alert-vs-decision codes** — recommended AGAINST (a second copy that
  goes stale); if ever wanted, it must be GENERATED from source, never hand-kept.

## SETTLED — no action (recorded so they are not re-opened)
- Natural-language-query feature is already marked a pilot-launch feature (§3C header) — no edit.
- "Status lives in §3D" is superseded — status lives in the status file, not the alert library.
- Git docs/ backup is DONE (commit 7402434) — no push to do; only the snapshot label remains.

---

## CORRECTIONS OWNED THIS SESSION (audit trail — where Claude was wrong, and the fix)
1. The "six models" change targets the ONBOARDING CHOOSER (§5), NOT the test-data table; and
   removing it does NOT break the attribution-inconsistency alert (A4 is cross-PLATFORM
   inconsistency, independent of the chooser). [Claude had it backwards.]
2. "Klaviyo Revenue Seasonality" (E6) DOES have a §3D home — the system-health plumbing pattern.
   [Claude had claimed it had none.]
3. "These items are a deliberate session-1 subset, rest for later" was Claude's INFERENCE, not
   in the files; the files assumed ONE session — which is why two sessions was a deliberate choice.
4. The ~50 extra code-names are seed DESIGN DECISIONS, not 50 alerts to judge. [Oversized earlier.]
5. The git backup is already DONE — Claude contradicted its own opening read-back by later
   calling it stale.
6. Claude briefly dropped the executable checker + judgment digest from the save mechanism;
   both were already agreed and are restored.

## OPTIONS CONSIDERED AND REJECTED (kept for the audit trail)
- "Fast bar" (call pivot documented after only the wording fix) → rejected: do it properly.
- Central lookup table for the codes → rejected: second copy, goes stale.
- Putting the code-sort in cross_alert → rejected: wrong home, same stale-copy risk.
- Relabelling all ~50 seed codes in their files → rejected: churns dated audit records, unneeded.
- One single edit session for everything → rejected: reliability degrades over a long chat.
- A short continuity paragraph instead of files → rejected: scope grew (Claude reversed itself).
- Reconciling all seven documents' pending edits now → rejected: already in the pivot file;
  only product_strategy matters for these two sessions.

---

## WORKING RULES (standing)
- Verify before propose (show the file reconnaissance first).
- Label every load-bearing claim: verified-from-file / inference / unchecked-assumption.
- State what would make it wrong, in the first answer.
- One item at a time; complete files, never patches; design here, build in Claude Code.
- No jargon/code without a plain-language gloss inline.

## CARRY-FORWARD — DO NOT LOSE
- B-9 Google Ads `cost_micros ÷ 1,000,000` when reading into the mart column (confirm direction).
- PARALLEL TRACKS (non-gated, do NOT deprioritize — recruitment is the binding constraint;
  Shopify PCD + read_all_orders approval; Google Ads developer token (the long pole); Indian
  entity registration). Doc/code work must not crowd these out.

---

## NEXT SESSION — VERIFICATION GATE (canonical line counts; STOP if any differs)
NO canonical file was edited this session, so the counts are UNCHANGED from the prior gate:
agent_d_build_spec=2710 · technical_architecture=3815 · cross_alert_orchestration=840 ·
product_strategy=1416 · d1_validation_gates=386 · pre_agent_build_checklist=389 ·
save_protocol=149.

WARNING — LINE NUMBERS WILL SHIFT IN SESSION 1: Session 1 edits product_strategy (adds the
"Deliverability Risk" alert, adds the missing A7 summary-table row, fixes counts), so its
count WILL change from 1416. Session 2 must therefore (a) re-take product_strategy's gate
number from the Session-1 output, and (b) locate every Session-2 edit by CONTENT anchor, not
by the line numbers recorded above — those line numbers are accurate as of 2026-06-14 only.

(These two continuity files' own line counts are handed over in the session report / digest.)
