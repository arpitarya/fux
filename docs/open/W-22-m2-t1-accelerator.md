# W-22 — M2: the T1 accelerator

**Status:** OPEN · **next** — nothing blocks it.
**Blocked by:** — (W-21 DoD met 2026-08-10)
**Spec:** [`PLAN.md` §M2](../PLAN.md) · format of record:
[`compare/index-format.compare.md`](../compare/index-format.compare.md)
**Closes with:** ADR-0005 (reserved) · prediction **R3**
**Model:** **Opus** — the differential law and the `mx` skipping design are
correctness-critical and a plausible-but-wrong implementation passes a naive
test suite.

## Goal

A derived, blocked **term-major** JSONL accelerator under `.fux/runtime/`
(derived plane, `CACHEDIR.TAG`-tagged per [ADR-0011](../adr/0011-fux-dir-layout.md))
that makes warm `ask` fast without changing a single ranked result.

## What lands

- Derived blocked term-major JSONL + an offset table; 128-posting block
  lines with integer `mx` skipping (the measured fix for the common-term
  trap: 397 ms → 44 ms).
- **The differential law** — accelerator results ≡ scan results, asserted
  **byte-for-byte** as a test, not spot-checked. This is the same discipline
  the M4 ARC cache will carry; it is the load-bearing invariant of the whole
  tiering story.
- Int-cached Hamming lane over the existing FuxVec 32 B `code` property.
- RRF fusion (k=60), ported from `archive/v0.26/` **with its tests**.
- `find` / `answer` verbs on the CLI surface.
- Build/refresh path: the accelerator is derived, never committed, and is
  rebuilt from the committed shards alone.

## Definition of done

- [ ] **R3 measured**: warm `ask` ≤ **150 ms** on the RFC corpus
      (8 872 docs, manifest-pinned, in the lab) **including worst-case
      common terms** — not an average over easy queries.
- [ ] Differential suite green: every golden and every bench query returns
      byte-identical results with and without the accelerator.
- [ ] Accelerator rebuild is deterministic from committed bytes only.
- [ ] `find` and `answer` behave per the CLI contract.
- [ ] ADR-0005 written and accepted.
- [ ] `fux doctor` understands the new derived directory.

## Named acceptance targets (from `fux-playground`)

The playground's `known_failure` **class 3 — term presence beating
aboutness** — is the dense lane's target set: `q008`, `q017`, `q030`,
`q031`, `q036`. Each becomes an `XPASS` when it closes. They are targets,
not DoD: closing zero of them with R3 met is still a passing M2, but the
count must be reported.

## Hazards

- **JSONL parse tax on real shapes** may be worse than benched; R3 is the
  tripwire and T2 (M6) is the designed escape. Do not pre-build T2 here.
- **Pruning is forbidden outside W-38** (plan law, [ADR-0003](../adr/0003-pruning-criterion-rerun.md)).
  If the accelerator gets slow, the answer is skipping and blocking, never
  dropping postings.
- Determinism law: no floats and no wall-clock in any committed byte. The
  accelerator is derived, so it may hold ints that vary by build — but the
  **results** may not.

## Lab

Runs go in a **new directory inside** `~/my_programs/fux-lab` — the lab
persists and is never rebuilt. Run the corpus tiers in the cloud, not in the
device VM.
