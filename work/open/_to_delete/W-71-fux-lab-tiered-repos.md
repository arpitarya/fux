# W-71 — fux-lab: five tiers, each its own independent git repo

**Status:** OPEN — **planning only** · **Filed:** 2026-08-22.

**Spec:** this file.
**Closes with:** `~/my_programs/fux-lab` holds five sibling directories — `10/`,
`100/`, `1000/`, `5000/`, `10000/` — **each an independent git repository with
its own independent fux setup** (own venv, own corpus, own `.fux/`, own pinned
engine version), scaffolded by an agent for testing/benchmarking. `SETUP-LAB`
rewritten to describe the new layout.
**Blocked by:** nothing structurally, but see Open questions — two of them
(repo naming, `shared/` vendoring) are Arpit's calls and should be settled
before an agent starts, not discovered mid-scaffold.
**Model:** **Sonnet** for scaffolding each of the five repos once the two open
questions below are answered — mechanical, repeated five times. **Opus** is
not needed for the scaffolding itself, but the two open questions (shared
tooling strategy, and whether the outer directory needs its own protection
against the 2026-08-20 loss) are judgment calls, not mechanical ones — flag
them rather than picking silently.

## Why this exists

Arpit, 2026-08-22, direct: *"Fux setup is also going to be a sibling repo. It
will have multiple folders in it... All these directories are going to be
individual git repos which will have independent fux setup in them and should
be used for testing or for benchmarking by the agent."* Tier list confirmed in
this session's AskUserQuestion exchange: **10, 100, 1000, 5000, 10000**
documents.

This is the same *purpose* `fux-lab` already serves (per
[`SETUP-LAB`](../setup/fux-lab.md): "the lab is where numbers come from... one
directory per environment") but a different *shape*. Today, `fux-lab` is
**one** git repository containing environment subdirectories (`1k/`, `5k/`,
`10k/`, `acme/`, `orbit/`, `rfc/`, `smoke/`). What Arpit described is each tier
as its **own** repository — five independent repos, not five subdirectories of
one.

## What changes

| | today (`SETUP-LAB`) | after this item |
|---|---|---|
| **outer structure** | `fux-lab` is one git repo; environments are subdirectories inside it | `fux-lab` is a plain directory; each tier is its own git repo inside it |
| **tiers** | `1k`, `5k`, `10k` (plus `acme`, `orbit`, `rfc`, `smoke` — realistic/special corpora) | `10`, `100`, `1000`, `5000`, `10000` — the five numeric tiers Arpit named |
| **isolation** | already isolated (own venv/corpus/results/version pin) but sharing one `.git` | fully isolated, including version control |
| **`shared/` tooling** | one copy, common to every tier by construction | needs a strategy — see Open questions; no longer "common by construction" once tiers are separate repos |

**What this item does not decide by itself:** whether `acme`, `orbit`, `rfc`
and `smoke` — the non-numeric, special-purpose corpora already documented in
`SETUP-LAB` — move into this structure, stay as they are, or are dropped. Arpit
named five numeric tiers; he did not say what happens to the others. Treat
them as untouched unless a future item says otherwise.

## Definition of done

- [ ] Five independent git repositories exist, one per tier, each bootable
      per `SETUP-LAB`'s existing `./setup.sh` → `./run.sh --accept-baseline`
      flow (bootstrap → generate → `fux setup` → ingest → verify).
- [ ] Each tier's `VERSION` file pins the same `fux-engine` version, so the
      five are comparable to each other (per `SETUP-LAB`'s existing rule that
      new-env pins must match whatever tiers a run is compared against).
- [ ] The two Open questions below are answered **before** scaffolding starts,
      not discovered mid-way through five repeated setups.
- [ ] [`SETUP-LAB`](../setup/fux-lab.md) rewritten to describe the new
      layout — the "one directory per environment" framing, the `new-env.sh`
      section, and the "environments that existed before 2026-08-20" table all
      need to say what is and isn't still literally true.
- [ ] The **CLAUDE.md 10 000-document ceiling is respected as written**: this
      item's largest tier is 10 000, at the ceiling, not above it — no sixth
      tier at 50k/100k gets added under cover of this item (CLAUDE.md
      §Litmus, 2026-08-22: *"no testing should go beyond ten thousand
      documents"*).
- [ ] A `work/WORKLOG.md` entry, and `work/setup/fux-lab.md`'s DOC-REGISTRY
      row bumped in the same change that executes this.

## What is reused

Everything in `shared/` that does not assume a single enclosing repo:

- `shared/new-env.sh` — scaffolds the full flow (bootstrap, generate,
  `fux setup`, ingest, `--check`, a present/MISSING verification block,
  `run.sh`, a `fux` shim, and a README answering "where is `.fux/`?"). This is
  the tool that stands up **each** of the five repos; it does not need to
  change, only to be invoked five times, once per tier root.
- `shared/generate/make_corpus.py` — seeded, byte-identical for a given seed,
  so a tier's corpus is reproducible.
- `shared/regress/run.py` — the accumulated, hand-corrected measurement
  harness (per [[fux-lab-persists]]: "corrected against four runs of real
  observed CLI output... worth more than it looks").
- The **standing rule that fux-lab is never deleted or rebuilt** ([[fux-lab-persists]],
  `TEST-PLAN.md` §0b) — new work is a new environment, not a fresh harness.
  That rule was written for the single-repo shape; it still applies in spirit
  (don't delete a tier repo and regenerate its baseline for no reason), even
  though the mechanism (`new-env.sh` inside one `.git`) changes.
- The environment/tooling notes in `MACHINE.md`: **this cannot run on the
  Cowork device VM** (no network, Python 3.10 < the required 3.11) — it has
  to run in the cloud sandbox, with results and baselines committed back.

## Hazards

- **The single-repo shape was chosen, in part, because it survived a data
  loss the multi-repo shape would not have.** `SETUP-LAB`'s own history: *"the
  whole directory was missing on 2026-08-20... it is now a git repository,
  which it was not before — that is exactly why it was lost."* Splitting into
  five independent repos with no enclosing repo removes whatever protection
  the outer `.git` was providing. **This item should not silently drop that
  protection** — see Open question 2.
- **`shared/`'s failure mode changes shape, not disappears.** Today, "a bug in
  `shared/` corrupts every tier identically," which is a hazard but at least a
  legible one — one fix, five tiers recover together. If `shared/` is copied
  into each of the five repos independently, the five copies can drift, and a
  fix applied to one does not propagate to the others without someone
  remembering to do it five times. Vendoring strategy is Open question 1, not
  a detail to improvise per-repo.
- **Comparability.** `SETUP-LAB` already establishes that byte budgets and
  quality metrics are deterministic (comparable across machines) but
  wall-clock is not. That rule does not change with this restructuring, but
  it is worth re-stating in the rewritten doc so a reader of five independent
  repos doesn't assume otherwise.

## Open questions

1. **How does `shared/` get into five independent repos?** Candidates, none
   chosen here: (a) vendor a full copy into each tier repo at scaffold time —
   simple, but the five copies can drift; (b) keep one canonical `shared/`
   outside all five (e.g. a sixth, tooling-only repo or a plain
   un-versioned directory) and have each tier's `new-env.sh` invocation pull
   from it — preserves "one fix, five tiers recover," at the cost of a
   dependency between repos that are supposed to be independent; (c) a git
   submodule per tier pointing at a `shared/` repo — gets versioning right but
   adds submodule-management overhead for something whose whole point was
   supposed to be independence. **Needs Arpit's call before scaffolding
   starts**, since it changes what "independent" means.
2. **Does the outer `fux-lab` directory need its own safety net**, given the
   single-repo shape existed partly to survive exactly the 2026-08-20 loss?
   Options: a lightweight manifest file (not itself a git repo) listing the
   five tier repos and their remotes/commits, so the set can be reconstructed
   even if one goes missing; or accept the reduced protection as the cost of
   Arpit's explicit ask for independence. Not decided here.
3. **Naming.** Arpit called this "Fux setup" in conversation, not "fux-lab."
   This item assumes the existing name and location (`~/my_programs/fux-lab`)
   carry forward, since the *purpose* (agent-driven testing/benchmarking) is
   unchanged from what `SETUP-LAB` already documents — only the internal shape
   changes. If Arpit meant a new, differently-named sibling repo instead of a
   restructuring of the existing one, that changes this item's location line
   and should be confirmed before executing.
4. **`acme`, `orbit`, `rfc`, `smoke`.** Left alone per "what this item does not
   decide" above — but an executor should ask Arpit rather than guess if their
   fate seems to matter once the five numeric tiers exist.

## Reference

- [`SETUP-LAB`](../setup/fux-lab.md) — the contract this item rewrites, and
  the source of every "what is reused" claim above.
- [[fux-lab-persists]] — the standing "never delete, new work is a new
  environment" rule this item's spirit preserves even as its mechanism
  changes.
- [[fux-lab-runs]] — how to actually run the suite (cloud sandbox only, no
  network/Python-3.10 on the device VM), unchanged by this item.
- `MACHINE.md` — the environment notes this item's execution must follow.
- Arpit, 2026-08-22 (this session) — the direction this item implements, and
  the AskUserQuestion exchange in this session confirming the tier list
  (10, 100, 1000, 5000, 10000).
