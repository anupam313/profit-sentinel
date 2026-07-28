# STATE — F3 Interview & Git Closure (snapshot)
**As of:** 2026-07-28 · **Repo HEAD:** `27a3a30` (origin/master, in sync)
**Companion:** `chat_context_2026-07-28_f3-interview-git-closure.md` (the narrative).
**Supersedes:** `state_2026-07-27_dbverify-reproducibility.md`, which is now stale on four points
(HEAD hash, the three founder actions it lists as open, the untracked `docs/sessions/*` line,
and it predates the F3 interview entirely). Keep it for history; read THIS one for current state.

---

## REPO STATUS
- Branch `master` == `origin/master` == `27a3a30`. Clean, in sync, all pushed.
- Two commits this session:
  - `120dcd0` — docs: add DB-verification / reproducibility session continuity pair
  - `27a3a30` — docs: commit backlog of untracked session continuity files (11 files, +1390)
- **`docs/sessions/` is now FULLY committed.** No untracked session files remain.
- Working tree, all DELIBERATE and parked by founder decision:
  - `connectors/seed_meta.py` (M), `onboarding_flow.py` (M) — see POSTPONED below
  - nine read-only `connectors/_*.py` probe scripts (untracked, throwaway diagnostics)
  - `slack_bot/` (untracked, stale since the email pivot — PARKED, flag do not delete)

## SANITY HANDLES
- `pilot_readiness_register.md` = **151 lines** (unchanged this session)
- `CLAUDE.md` = 280 · `sql/schema.sql` = 1489 · `connectors/seed_client_config_calibration.py` = 128
- `pilot_scope.md` (137) · `product_strategy.md` (1440) · `operating_charter.md` (308) ·
  `pre_agent_build_checklist.md` (389) · `technical_architecture.md` (3999)

## KEEP-ALIVE — FULLY CLOSED AND PROVEN
All three founder actions from the previous state file are DONE:
1. `SUPABASE_DATABASE_URL` repository secret added (session pooler + `?sslmode=require`).
2. Manual run #1: **SUCCESS**, 20s total / 12s job, on `master`.
3. GitHub failure notification confirmed on (default, email).
**Proof from the run log** — the query actually reached Supabase, not just a green job:
`ping = keepalive | client_rows = 1 | now = 2026-07-28 07:49:30.098338+00`
Next automatic run: Friday 06:14 UTC. Schedule is Tue/Fri.

## POSTPONED BY FOUNDER DECISION (not open work)
- **`seed_meta.py` and `onboarding_flow.py` diagnosis.** ~800 unexplained deletions were never read.
  Rationale accepted: git protects the committed versions at `origin/master`, so nothing is at risk;
  `git checkout -- <file>` restores either. The only consequence is that running the seed scripts or
  `dbt build` from the working tree would use the modified copies. Synthetic data only.
  **BUT `onboarding_flow.py` IS on the first-connect path** — spreadsheet row A33 / checklist D-10
  requires a `business_model_type` column plus an onboarding script update before a real brand onboards.
  Covered in the spreadsheet at A33 and Parallel Track #5 (HK-1). Verified, not assumed.
- **`slack_bot/`** — parked. OQ-12 may revive it post-pilot.
- **The nine `_*.py` probes** — throwaway, leave untracked.

## PROJECT-KNOWLEDGE HYGIENE — WAS BROKEN, NOW FIXED
Audited this session and found:
- `pilot_readiness_register.md` in project knowledge was the **STALE 116-line version** — zero of the
  twelve new items present. A future session would have rediscovered completed work.
- The `_dbverify-reproducibility` pair was **MISSING** entirely.
Founder has since replaced the register with the 151-line version and added both files.
**STANDING RULE (new): after any register commit, replace the project-knowledge copy in the same sitting.**

## F3 LIFESTYLE / SLAY.FASHION — INTERVIEW 1 (India column)
Brand: SLAY.FASHION, entity F3.LIFESTYLE. Shopify. Men's shirts only, six sizes, Rs 699-1199.
HSR Layout Bengaluru. ~5,000 customers, 50+ designs, ~6 months trading. 60-minute delivery of its OWN
stock (Slikk / Blip / Zilo / Myntra M-Now are quick-commerce MARKETPLACES; he is not).
Stack: WhatsApp (support AND email marketing) · Unicommerce (WMS) · GoKwik (gateway, high-return-customer linking).
100% paid-driven — "organic is non-existent". Marketing team separate from the founder.

**Scenario test: TYPE A** — "terminate the campaign immediately". First recorded data point on the
core hypothesis (will a founder act on a warning they did not ask for).

**THREE HIGH FINDINGS — these need register items and currently exist ONLY in a spreadsheet outside git:**
1. **F3-01 — the returns-versus-CAC trade. A direct challenge to the C8 premise.** His words: return
   goes 10% to 20%, the extra cost is only on that 10%, supply chain cost is Rs 150, "so don't worry
   too much about it if CAC is reducing from Rs 400 to Rs 200". On HIS numbers he is arithmetically
   right: +10pp x Rs 150 = Rs 15/order against a Rs 200 CAC saving. Two things weaken it and both are
   testable: Rs 150 assumes the shirt is fully resellable, and at US AOV ($80-150) with US reverse
   logistics ($25-40) the trade flips. **Needs a register OPEN QUESTION. Do not dismiss, do not panic —
   one Indian founder at Rs 900 AOV is a warning, not a verdict.**
2. **F3-03 — grouping. He does NOT think in SKUs.** "Always by the shirt type — regular, tight, half
   sleeve, full sleeve... the combination of regular x half sleeve. Then the feedback goes to design and
   manufacturer." He ACTS on fit x sleeve attribute combinations. PS groups by Shopify Standard Taxonomy
   (locked 2026-06-19). **One data point — do NOT reopen the lock.** Add to the US script: "when returns
   spike, what do you group by to decide what to fix?"
3. **F3-02 — the validation, and the outreach hook.** "They call each and every customer why the person
   has returned. Currently manual completely." He is doing by telephone what C8 and C1 automate, and
   knows it does not scale. Better outreach line than anything currently in the email.

**Two MEDIUM findings worth carrying:** he already HAS a stockout alert ("if the size is OOS it comes
as an alert to founders and marketing") — unknown whether it joins to live ad spend, which is the actual
differentiator; and he PREVENTS the G1 condition rather than detecting it ("we do not run a campaign on
less than 150 units"), so G1's value may be inversely proportional to operational discipline.

**Not captured:** THE ONE QUESTION (never asked — still open). US referral WAS asked: "will try, low
chances" — logged. Signals 2-5 not asked, so no signal-gap score.

## WORKING ARTIFACTS (NOT in repo — personal, not backed up)
- **`India_Discovery_Interviews_Master.xlsx`** — NEW. Six sheets: interview log · findings (13 F3 rows,
  extensible) · signal visibility with live tallies · Section 11 rubric · follow-ups · how-to-use.
  F3 is interview 1. **This is where all India interviews go from now on.**
- `pilot_readiness_27072026.xlsx` — 60 Build Sequence rows, 9 Parallel Track, 24 Legend.
- `F3_SLAY_Meeting_Simple.docx` — the completed interview with notes.
- `DTC_Prism_Founder_Discovery_Call_India.docx` — the generic 5-page India questionnaire.
- SUPERSEDED, delete: `F3_SLAY_Interview_Findings.xlsx` (folded into the master workbook).

## NEXT SESSION — THE AGENDA THE FOUNDER SET
1. **Pilot readiness spreadsheet, Block A IN SEQUENCE** — not cherry-picked. A1 onward.
2. **ARCHITECTURE STATUS MAP — an explicit founder request.** He wants to see, in detail, what is
   actually plugged in versus pending, so open items are visualisable. Which connectors are wired,
   which agents are built, which alerts are scanned, what is synthetic versus real, what the data flow
   looks like end to end today. This does not exist as an artifact yet.
3. **Approvals — start them, they are pure waiting time.** Shopify Partner account + custom-distribution
   app + `read_all_orders` request (needed for 12 months of history; `read_orders` alone reaches 60 days).
   Google Ads developer token (the long pole; Basic Access review ~5 business days, faster with brand
   verification). Meta and TikTok need no application at pilot scale — Airbyte Cloud managed OAuth,
   but CONFIRM that is still offered. Klaviyo is a self-serve key.
4. The three F3 HIGH findings become register items.

## STILL OPEN — CARRIED FORWARD, NOT RESOLVED
- **HK-2 needs REWRITING.** Its premise "the repo is the source of truth" was false; it is closer to
  true now but the item as written reassures about a risk it no longer fully covers.
- **RULE 8 divergence.** `CLAUDE.md` requires RLS enabled AND a policy on every public table. Live:
  RLS on, ZERO policies. Tenant isolation lives in the APPLICATION layer. No exposure at one client;
  load-bearing at client two, which is a pilot-timeframe event.
- **`technical_architecture.md`** documents ~40 `client_config` columns against a live 159.
- The two `client_config` triggers (`client_config_change_log`, `tier_limits_trigger`) — in no repo file,
  and we still do not know what they do. The no-op UPDATE test proved only that they do not error.
- Nothing creates the `client_config` ROW except a fallback path inside `onboarding_flow.py`.
- The F3 one question, unasked.
- HELD-3 unchanged: stay on free tier, upgrade before FIRST REAL BRAND CONNECTS for the encrypted-backups
  requirement in `pilot_scope.md` §6. The keep-alive covers the interval.

## STANDING DISCIPLINE
Two-agent split (Claude authors + reviews in chat; Claude Code edits/commits/pushes; founder authorises).
Locate by quoted text. HK-6 straight quotes. Mount UNTRUSTED. Continuity files authored in chat.
For DATABASE state query the database; for FILE state open the file.
**Added this session:** when building an instrument that already exists in the repo (an interview script,
a rubric, a checklist), USE THE COMMITTED ONE. Do not build bespoke — §11 already had a v3 questionnaire
with an 8-signal rubric and it was ignored.
