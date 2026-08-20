# W-56 — `fux-lab` needs rebuilding

**Status:** OPEN (Lane A) — **DECIDED 2026-08-20, Arpit: build both if they do
not exist.** No longer human-only: `~/my_programs` is reachable, so an agent can
stand them up from the setup docs. · **Filed:** 2026-08-20
**Blocked by:** — · **blocks** W-57, W-59, and R4 · R5 · R6 · R7
**Model:** **Opus** — the scaffolding is mechanical; **the playground's goldens
are not**, and knowing the difference is the whole risk.
**Spec:** [SETUP-LAB](../setup/fux-lab.md) · [SETUP-PLAYGROUND](../setup/fux-playground.md)

> **Verified 2026-08-20: neither exists.** `~/my_programs` holds anton · bach ·
> barrel-loader · cage · dante · elgar · fux · graphify · milo · sentenel ·
> stock-prediction-patterns · wagner. **`fux-playground` is not there** — it was
> reported recreated, and it is not on disk under that name.
>
> **Build both, and do not conflate the two halves.** The lab is scaffolding:
> directory layout, `shared/new-env.sh`, `TEST-PLAN.md` with standing rule §0b,
> one environment per corpus. The playground is **authorship** — it had no
> remote, so its **50 ranked goldens (41 pass · 9 named `xfail`) cannot be
> restored, only re-graded by hand**. A generated golden is not a golden, and a
> playground whose goldens were invented by the engine under test is worse than
> no playground. **Rebuild the corpus and the harness; stop at the goldens and
> say so.**

## The finding

Neither sibling environment exists:

```bash
$ ls -d ~/my_programs/fux-playground ~/my_programs/fux-lab
ls: /Users/arpitarya/my_programs/fux-playground: No such file or directory
ls: /Users/arpitarya/my_programs/fux-lab: No such file or directory

$ find ~ -maxdepth 4 -name 'fux-playground*' -not -path '*/Library/*'
$ find ~/my_programs -maxdepth 3 -iname '*playground*'
   # both empty
```

`~/my_programs` holds: anton · bach · barrel-loader · cage · dante · elgar ·
fux · graphify · milo · sentenel · stock-prediction-patterns · wagner. No
`fux-lab`, no `fux-playground`.

## Why each one matters, and how bad it is

### `fux-playground` — **recreated 2026-08-20.** Kept below for the record of what it is *for*, since that is what a rebuild has to satisfy.

[SETUP-PLAYGROUND](../setup/fux-playground.md) describes it as a **sibling git
repository with one local commit and no remote**, holding **50 ranked goldens**
(41 pass · 9 named `xfail` at creation). It had **no remote**, so a rebuild is authorship, not a clone: the goldens have
to be re-graded by hand against the fixture corpus, and a golden nobody graded
is not a golden.

It is the instrument for:

- the graph lane's named acceptance targets `q005`/`q009`/`q011`/`q015`
  ([W-57](W-57-graph-lane-acceptance.md), [ADR-GRAPH](../../docs/adr/0030_graph-lane.md));
- the dense lane's named target set `q008`/`q017`/`q030`/`q031`/`q036`, which
  is the evidence that would let `--hybrid` flip on
  ([`query/hybrid.py`](../../src/fux/query/hybrid.py) says so in its docstring);
- any future claim that a ranking change helped.

### `fux-lab` — **still missing. This is the item.**

The standing obligation in [`OPEN-WORK.md`](../OPEN-WORK.md) reads: *"**The lab
persists.** `~/my_programs/fux-lab` is never deleted or rebuilt — new runs are
new environments inside it ([SETUP-LAB](../setup/fux-lab.md))."*

Rebuild it from [SETUP-LAB](../setup/fux-lab.md). **The standing obligation now
needs amending in the same change**: "never deleted or rebuilt" was written to
stop an agent clearing it, and it now reads as a rule the repo itself has
broken. It should say what it means — *an agent never deletes or rebuilds it;
Arpit may.*

The M2 run's own reproduce commands point into it and no longer run:

```bash
# work/regression/2026-08-12-m2-accelerator/report.md:148
python tools/differential/bench_r3.py --root ~/my_programs/fux-lab/2026-08-12-m2-r3
```

**This is the "the reproduce command must actually reproduce" law failing**,
and it fails silently — the report still reads as if it were reproducible.

## What it blocks

| item | needs | status |
|---|---|---|
| [W-57](W-57-graph-lane-acceptance.md) | playground | **unblocked if the goldens survived** — verify first |
| flipping `--hybrid` on | playground | same: needs the named target set, not just the corpus |
| **R4** (refer plane, W-24) | lab | will block |
| **R5 / R6** (maintenance, W-25) | lab | will block |
| **R7** (100k density, W-26) | lab | will block |

**Every unmeasured prediction left in the plan runs in the lab.** So this is
not a graph-lane problem that happens to be inconvenient; it is the next four
milestones' instrument.

## Definition of done

- [ ] **Arpit says which is true**: (a) the directories moved, (b) they were
      deleted and a backup exists, or (c) they are gone.
- [ ] If gone: decide whether the playground is **rebuilt** (50 goldens is real
      human work) or **retired**, and say so in
      [SETUP-PLAYGROUND](../setup/fux-playground.md) — a setup doc describing a
      repo that does not exist is worse than no doc.
- [ ] The lab is restored or re-created per [SETUP-LAB](../setup/fux-lab.md),
      **or** the "the lab persists" obligation is struck from `CLAUDE.md`,
      because a standing rule nobody can follow is a rule that teaches rules
      are optional.
- [ ] `work/regression/2026-08-12-m2-accelerator/report.md`'s reproduce
      commands are either made runnable again or annotated with what they
      needed — under the conformance law, a reproduce command that cannot
      reproduce is a defect in the filing, not a fact about the past.

## Hazard

**Do not "fix" this by regenerating a playground and calling the goldens
restored.** The 50 goldens are *graded* — a human decided what the right answer
was. A regenerated corpus graded by the engine under test measures nothing, and
would silently convert every future eval into a tautology. If the gradings are
gone, the honest move is to say the instrument is gone and re-grade
deliberately.

## Evidence

Measured in this file, 2026-08-20, by the two commands above. Found while
attempting [W-23](../../archive/open/W-23-m3-graph-lane.md)'s named acceptance
measurement, which could not run.
