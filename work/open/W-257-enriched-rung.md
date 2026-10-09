---
type: Handoff
name: W-257
description: "An enriched rung-01000 — model-generated questions over the rung with enrich=true declared — the one deliverable B-108, B-109, B-110 and B-245's second condition all wait on (measurement plan §7; W-251 §3 #23). The protocol the plan missed: a BLIND author, or the three rows get no delta. The launch is Arpit's tokens; everything before and after it is agent work. Filed 2026-10-04."
item: W-257
filed: 2026-10-04
ball: arpit
---

# W-257 — an enriched rung, authored blind

✅ **RULED 2026-10-10 (Arpit) — run the FULL enriched rung, instructions
unchanged** (the recommendation). **DoD 2 is done:** [the pre-registration](../regression/2026-10-10-enriched-rung/PRE-REGISTRATION.md),
frozen and committed alone. It covers B-108 (`unfiltered` vs `none`, placebo
control), B-109 (`filtered` vs `unfiltered`) and B-110 (`cov-25`/`cov-50` vs
`cov-100` on the questions the un-enriched part answered). All three are judged
at `hit@1` on set-5-claude per SR-RS d19, scope all four `dirs` lines.
⚠ **The run is `informed` regardless of the blind author**, because set-5-claude
is Claude-authored (L11 d7). The pre-registration says so; the blind author
still keeps the enrichment unfitted to the set. **Next:** the full-rung author
prompt (the pilot's, scope widened to all four lines, nothing else changed) →
**Arpit launches it**. No session that has read the pre-registration gives the
author any content.

**Status 2026-10-10: PILOT RUN (2026-10-09, launched by Arpit) and read by a
non-author session.** [The capture](../regression/2026-10-09-enrich-pilot-gen4/report.md):
scope `seed` (94 docs; no 40–60 folder exists on this rung). **745 questions;
`--check` refused 237 (31.8 %)** on the first pass, all *"does not retrieve its
document"*, and 17/94 documents came through clean. The refused lines are reader
paraphrases (*"8 degrees … breach"* against the document's *"+8.0 C …
excursion"*), which is the vocabulary gap doc2query exists to bridge
([ANALYSIS](../regression/2026-10-09-enrich-pilot-gen4/ANALYSIS.md)). **🔴 Arpit:
(1) the author's wall clock and token cost** (they are in its report, not on
disk); **(2) rule the full rung.** Recommended: **go, with the instructions
unchanged.** Pre-register filtered (508) against unfiltered (745) as B-109's arm;
rewriting the refused lines into the documents' words would delete that arm.

✅ **RULED 2026-10-09 (Arpit, Cowork) — *"go with the recommendation"*: the
PILOT only, now.** The gen-4 rebuild it waited on is done (W-240, 2026-10-05),
so only his hand remains. **Arpit** opens **one fresh Claude Code session in
`~/my_programs/fux-lab`** — not in the fux repo and not in a Cowork project,
both of which carry failure notes — pastes the prompt below, closes that
session after its report, and brings the report to any session that is not the
author. That session reads the first-pass `--check` refusal rate; Arpit reads
the token cost and rules the full rung. **The pre-registration (DoD 2) is owed
before the full rung, not before the pilot** — the pilot measures cost and
refusal, not doc2query.

```text
You are a BLIND enrichment author for a fux measurement. Do exactly one job, report, and stop.

NEVER open, list, grep, search or read:
- anything under ~/my_programs/fux/ (the fux repo)
- any work/golden/questions/, work/golden/golden-answers/ or work/regression/ path
- any evidence/ folder, query log, result file or failure list
If any such content reaches you, stop and say so.

1. In ~/my_programs/fux-lab, create a new environment with shared/new-env.sh
   (read its usage first) named enrich-pilot-gen4. Copy corpora/golden/rung-01000
   into it. Never modify corpora/golden/ itself.
2. In the copy, pick ONE source folder that holds roughly 40-60 documents.
   Add enrich=true to that folder's line in .fux/sources/dirs, and to that line only.
   Run `fux ingest`.
3. Run `fux enrich --plan` and take its worklist.
4. Follow the fux-enrich skill (.claude/skills/fux-enrich; if absent, `fux enrich --help`)
   and write the questions for every planned document. Use only each document's own text.
5. Run `fux enrich --check`. Do NOT rewrite refused questions: the first-pass refusal
   rate is the measurement.
6. Report, then stop:
   - the folder chosen
   - documents planned
   - questions written
   - questions refused, with the reasons --check gave
   - wall-clock time
   Do not run ask, find, answer or any benchmark afterwards.
```

**✅ RULED 2026-10-04 (Arpit, Cowork) — *"Go with the recommendation. But keep it
blocked until I say that we need to run this."*** So:

1. **On hold.** Nothing here starts — not the pilot, not the pre-registration —
   until Arpit says *run it*. The row stays 🔴 in the inbox for that word.
2. **After the generation-4 ladder rebuild** (waits on W-240). Enriching
   today's gen-3 rung-01000 would label a rung that is about to be replaced.
3. **Pilot first:** one `--plan` scope of about 50 documents; read `--check`'s
   refusal rate and fix the instructions before the full rung.
4. Then the full rung and the three pre-registered runs, as below.

**Model: Opus** for the pre-registration and the three runs; **the authoring
session is a fresh agent of any strong model that has read nothing listed
below.** 🔴 **The launch is Arpit's** — the authoring is tokens, and they are
his (W-251 §3 #23). Filed 2026-10-04 by delegation
([W-251](../../archive/open/W-251-backlog-audit-rulings.md) §3 #23); nothing here is built or run.

## What it is

SR-ENRICH d15: doc2query questions are *"BUILT AND UNPROVEN"* — the four-arm
run was voided because its bar never named `k`. d16: the `--check` filter
*"refused 2 of 98 … too small to see"*. Main d6: the enrichment tilt *"is a
measurement, not an opinion."* B-245 (the vector plane) reopens only when
doc2query's ceiling is measured **and** a rank-contract corpus exists. All four
wait on one artefact: **rung-01000 with `enrich=true` on its `dirs` line and a
pinned `.fux/enrich/` written by an agent** — `fux enrich --plan` names the
scope, the agent writes the questions, `fux enrich --check` validates them with
fux's own index (`title` and `ctx` zeroed, d16). fux calls no model; L2, L4 and
L5 are untouched (SR-ENRICH d1; ENRICH-SKILL: *"You are the model."*).

## The protocol the plan missed — authorship

SR-RS d11: a run is `blind` only if *"corpus enrichment, the enrichment prompt
…"* were authored *"without access to the evaluation queries … or any derived
report of them"*; d12: an `informed` run *"never supplies a delta."* The
question sets are released text (the key is separate and sealed, L11) — so an
authoring session that has read **any** `questions/set-N.jsonl`, W-168's
failure lists, or a per-query capture yields an **informed** rung, and
B-108/B-109/B-110 get no delta from it.

So: **one fresh session**, instructed in its first line never to open
`work/golden/questions/`, `work/golden/golden-answers/` (closed anyway, L11),
any `work/regression/*/evidence/`, or any failure list; it reads
`work/golden/seed/` for rung-01000 only, runs `fux enrich --plan`, writes the
questions, runs `--check`, and stops. The run then declares `blind` with that
session named; placebo and decoy controls (SR-RS d15, built) run beside it.
**Pilot first:** one `--plan` scope (d13's TARGET), check the refusal rate, then
the rung — a blind author who has never seen the corpus's question style can
fail `--check` wholesale and burn the spend.

## Definition of done

1. 🔴 **Arpit launches the authoring session** (the token cost — ~1 000
   documents × 5–10 questions) after reading the protocol above; or says *no*.
2. PRE-REGISTRATION, frozen and committed alone before any run: doc2query's bar
   **naming `k`** (`hit@1` per W-168's endpoints, net ≥ 6 at the observed
   discordant count — SR-RS d19); the `--check` filter's visibility bar
   (B-109); the tilt at 25 / 50 / 100 % coverage (B-110).
3. Three runs filed under `work/regression/`, `blind` or — if the protocol
   failed — `informed` and said so; SR-ENRICH d15, d16 and main d6 rewritten to
   what was measured, `sr-hash.py --write`.
4. `BACKLOG.md`: B-108, B-109, B-110 leave on the numbers; B-245's second
   condition is marked met or not.
5. SR-WORK-TESTDATA: the rung's enrichment is golden test data and is authored
   against the checklist; a row if one is missing.

## Out of scope

- Building the vector plane (B-245 needs the rank-contract corpus too).
- Any change to `fux enrich`.

## Hazards

- ⚠ The spend is real and a wholesale `--check` refusal wastes it — hence the
  pilot.
- ⚠ A session that *also* runs a rung or returns to the benchmark after
  authoring has crossed d11; the authoring session does one thing and ends.
- ⚠ Run in `fux-lab` (L9); never `fux-playground`.
