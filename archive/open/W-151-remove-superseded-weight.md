---
type: OpenItem
id: W-151
title: "W-151 — remove superseded_weight: supersession is a fact, not a weight"
description: "Arpit ruled 2026-09-13 that superseded_weight goes. The knob multiplies a flag nobody declares, and the only values that order a corpus sensibly are set by unrelated documents. The FACT stays — the index property, the graph edges and fux explain are untouched. Ratified here, not built."
status: open
lane: agent
timestamp: 2026-09-13T00:00:00Z
filed: 2026-09-13
---

# W-151 — remove `superseded_weight`

**Model: Sonnet.** The decision is made and the definition of done below is
explicit, which is itself the signal the design phase is over. ⚠ **Escalate to
Opus if any of the four records needs more than the key removed** — a record
that has to be *re-argued* rather than edited is a judgement call, and
SR-TUNE's closed-key-set prose is the likely one.

## The ruling

**Arpit, 2026-09-13:** *"I believe we don't need superseded weight at all
because there is no weight that determines which document supersedes another in
the real world. So let's remove it."*

This is option (c) — *close the knob* — from
[W-143](../../archive/open/W-143-four-no-op-priors.md), taken for the first of
the four priors. The other three were ruled the same day:
[W-152](W-152-close-archived-and-recency.md) and
[W-154](W-154-rerank-weight-cost.md).

## Why, with the evidence

**1. The only values that work are set by documents that have nothing to do
with supersession.** A three-document corpus — a 2023 vendor decision, a 2026
one declaring `supersedes:`, and an unrelated fleet handbook — asked *"telematics
vendor for cold-chain vehicles"*:

| `superseded_weight` | 1st | 2nd | 3rd |
|---|---|---|---|
| **1.0** (shipped) | **vendor-2023** `0.8692` | vendor-2026 `0.8684` | handbook `0.7875` |
| 0.99 | vendor-2026 | vendor-2023 `0.8605` | handbook |
| 0.95 | vendor-2026 | vendor-2023 `0.8257` | handbook |
| 0.90 | vendor-2026 | **handbook** `0.7875` | vendor-2023 `0.7823` |
| 0.50 | vendor-2026 | handbook | vendor-2023 `0.4346` |

The band that produces the sensible order is roughly **0.906 – 0.999**, and its
lower edge is the handbook's score. **Add a document and the correct value
moves.** Above the band the knob does nothing; below it the retired decision
sinks beneath documents that do not answer the question at all.

⚠ **THIS IS AN ILLUSTRATION, NOT A MEASUREMENT.** It was run in a scratch
directory outside the lab to show a mechanism, it is not filed under
[`regression/`](../regression/README.md), and **no session may cite it as
measured evidence.** The measured finding is
[VERDICT-W143](../regression/2026-09-12-priors-and-tables/VERDICT-W143.md),
which answers the pre-registered question with **NO** on 26 intent-split probes.

**2. The flag it multiplies is, in practice, never set.** Supersession is
**declared, never inferred** (`src/fux/ingest/edges.py`): the newer document
carries `supersedes: <repo-root path>` in its frontmatter and the flag lands on
the target. Nothing reads dates, titles or numbering. And in the real corpus
nobody ever wrote it — `adr-0019` says *"Supersedes ADR-0007"* in **prose** with
no key, and `git log -S "supersedes:"` is **empty across the playground's whole
history**. That is why the 2026-09-11 precondition check found **zero headroom**.

**3. Removing it changes no ranking today.** It ships at `1.0`, so `Weighting.of`
already returns the same float. ⚠ **This is a cleanup, not a fix**: after it
lands, *"which vendor do we use"* still answers **2023** on the corpus above.
The behaviour fix is a different item and is not authorised here.

## Definition of done

1. **`superseded_weight` is gone from the closed key set** in `src/fux/tune.py`,
   from `Weighting` and `Weighting.of()` and the `maximum` bound in
   `src/fux/query/rank.py`, from `src/fux/query/__init__.py` and
   `src/fux/doctor.py`.
2. **The Node twin moves in the same change** — `node/src/config/tune.mjs` and
   `node/test/config.test.mjs`. `tests/test_node_twins.py` will demand it.
3. **A committed `superseded_weight` is REFUSED BY NAME, not as an unknown key.**
   The error says it was removed on 2026-09-13 and that supersession is a fact,
   not a weight. A silent *"unknown key"* on a key fux itself shipped costs
   somebody an afternoon. This is the one piece of NEW behaviour in the item.
4. **`.fux/tune.toml` in this repo drops the key.**
5. **Four records are amended in the same change** (Law zero):
   [SR-TUNE](../../records/0135_tuning.md) — the key set and decision 13;
   [SR-RANKING](../../records/0111_ranking.md) — the multiplier list;
   [SR-DOTFUX](../../records/0102_fux-directory.md) and
   [SR-DOCTOR](../../records/0153_doctor.md) — wherever they name the key.
   Then `scripts/sr-owns.py --write && scripts/sr-hash.py --write`.
6. **The agent skill and its three vendored copies** —
   `src/fux/templates/agents/CONFIG-SKILL.md` is the template; `.agents/`,
   `.claude/` and `.kiro/` are renderings. **Edit the template, copy across**;
   `tests/test_setup_agents.py` will demand it.
7. **`CHANGELOG.md`** gains the removal under the current version.
8. **Both suites whole**, plus `node --test node/test/*.test.mjs`.

## In scope / out of scope

- **IN:** the knob, its key, its plumbing, its documentation, its refusal.
- **OUT — do not touch:** the `superseded` record property, the `supersedes:`
  frontmatter declaration, the edge in `src/fux/ingest/edges.py`, the graph
  plane and `fux explain`. **The fact is not the weight**, and the fact is what
  the ruling leaves standing.
- **OUT:** `archived_weight`, `recency_half_life_days` —
  [W-152](W-152-close-archived-and-recency.md); `rerank_weight` —
  [W-154](W-154-rerank-weight-cost.md).
- **OUT:** adding `superseded` / `superseded_by` to the `ask` hit. It is the
  better idea and it is **not authorised** — `query/output.schema.json` is the
  only public shape fux has, frozen by [SR-API](../../records/0155_api.md), and
  three readers must agree on it. It needs its own item.

## Key files

`src/fux/tune.py` · `src/fux/query/rank.py` · `src/fux/query/__init__.py` ·
`src/fux/doctor.py` · `node/src/config/tune.mjs` · `.fux/tune.toml` ·
`src/fux/templates/agents/CONFIG-SKILL.md` · `tools/quality-controls/priors_sweep.py`

## Tests to update

`tests/test_config.py` · `tests/test_tune_boundary.py` · `tests/query/test_priors.py` ·
`tests/test_doctor.py` · `tests/test_node_config_parity.py` — plus a **new** test
that the named refusal fires on a committed `superseded_weight`.

## Open question, NOT blocking this item

🔴 **Will anyone ever write `supersedes:`?** It has never appeared in a real
corpus. If the answer is no, the `superseded` property is `False` on every
record everywhere and the whole concept — not just the knob — is worth
re-examining, along with whether a `fux link --supersedes` verb would make the
declaration cheap enough to adopt. **Arpit's call, and a separate item.**
