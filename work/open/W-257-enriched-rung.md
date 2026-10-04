---
type: Handoff
name: W-257
description: "An enriched rung-01000 — model-generated questions over the rung with enrich=true declared — the one deliverable B-108, B-109, B-110 and B-245's second condition all wait on (measurement plan §7; W-251 §3 #23). The protocol the plan missed: a BLIND author, or the three rows get no delta. The launch is Arpit's tokens; everything before and after it is agent work. Filed 2026-10-04."
item: W-257
filed: 2026-10-04
ball: arpit
---

# W-257 — an enriched rung, authored blind

**Model: Opus** for the pre-registration and the three runs; **the authoring
session is a fresh agent of any strong model that has read nothing listed
below.** 🔴 **The launch is Arpit's** — the authoring is tokens, and they are
his (W-251 §3 #23). Filed 2026-10-04 by delegation
([W-251](W-251-backlog-audit-rulings.md) §3 #23); nothing here is built or run.

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
