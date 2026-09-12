# Claude Code prompt — finish W-107

Read `work/handoff/HANDOFF-W-107-finish.md` first. Its **Definition of done**,
**Out of scope** and **Non-negotiables** are binding.

You are wiring an already-built, already-green Node read plane into this repo's
own rules: the ADR register, the wheel, `fux setup`, CI, and doc discipline.
**The engine code is written and passing. Do not rewrite it.**

## Read first, before changing anything

- `work/open/W-107-node-read-plane.md` — start at **§Rulings**, then §Hazards
- `docs/adr/0155_node-search.md`, `docs/adr/0156_api.md` — already written
- `docs/adr/README.md` — the register and its ownership table
- `src/fux/store/fuxdir.py` — the declaration tables and `ensure_layout`
- `work/open/W-107-fuxdir-node-vendor.py.txt` — the code you are applying in step 4
- `CLAUDE.md` §Law zero and §The three-file session discipline

⚠ **The working tree already has ~120 uncommitted files from other sessions.**
Run `git --no-optional-locks status` first. **Never** `git checkout`, `git
stash`, `git reset` or `git clean` — keep your changes separable and leave
everything else alone.

## Task — six steps, in this order

**1. Make the suite pass again.** Two things break it today:

- `docs/adr/README.md` has no rows for ADR-NODE-SEARCH (0155) or ADR-API (0156),
  and no ownership entries. Add both. **Match an existing row's format exactly**
  — `scripts/adr-guard.sh` parses that table with `awk`. Ownership:
  `node/` → ADR-NODE-SEARCH, `src/fux/api.py` → ADR-API.
- `src/fux/__init__.py` has no re-export, so `from fux import open` — which
  ADR-API and `.fux/README.md` both document — does not work. Add it. While
  there, its docstring still claims *"rank organizational knowledge"* and
  *"stdlib-only runtime"*; both are false as of today. **Propose the new wording
  and ask before applying.**

Stop here and run `uv run pytest -q`. Do not continue until it is green.

**2. Package `node/` into the wheel with hatchling `force-include`** —
`node/` → `fux/templates/node/` at build time. **Do not copy `node/` into
`src/fux/templates/`**; a second copy in the repo is the drift surface this
codebase exists to avoid. Verify with a real install:

```bash
uv pip install -e . && python -c "
from importlib import resources
print(sorted(p.name for p in (resources.files('fux')/'templates'/'node').iterdir()))"
```

**3. Apply the vendoring block** from `work/open/W-107-fuxdir-node-vendor.py.txt`
into `src/fux/store/fuxdir.py`: `ensure_node_reader`, the `ensure_layout` call,
the `COMMITTED` / `COMMITTED_FILES` entries, and the `fux doctor` row. It is
**overwrite-on-version-difference, not write-if-missing** — read the comment in
that file for why before you change it.

**4. Place the CI workflow.** `node-arm.yml` was delivered as an attachment in
the Cowork chat (remote tools cannot write `.github/workflows/`). Copy it in.

**5. Add the three test files** named in handoff §9 — `tests/test_api.py`,
`tests/test_setup_node.py`, and the `api._PII_RULES` assertion in the existing
`tests/test_cli.py` equality check.

**6. Doc discipline** per handoff §9.5. Everything there except `CLAUDE.md`,
which you **propose and surface, never apply**.

## Required workflow

1. **Explore** before writing. Do not assume the shape of `fuxdir.py` or the
   register table.
2. **Plan** — list the files you will change and pause for my confirmation
   before implementing.
3. **Implement incrementally**, keeping `pytest` green between steps. Step 1 has
   its own gate above.
4. **Update docs to match** as part of the change, per §9.5.
5. **Verify** with the full block in handoff §9. Do not report done until it
   passes.

## Constraints (hard)

- **`node/` gets no `dependencies` and no build step.** A build step is a
  dependency (L1). No bundler, no TypeScript, no `postinstall`.
- **Change no ranking arithmetic** — `bm25f`, `rank`, the sort key, the
  analyzer, `blake2b`, `compat/pyfloat.mjs`. They are pinned and passing.
- **Law zero:** an ADR-owned path changes with its OWNING record in the same
  commit, or the message carries `no ADR affected` on its own line.
- **Do not touch:** `work/golden/**`, `work/regression/**`,
  `work/benchmark/PRE-REGISTRATION-NODE.md` (frozen — superseded, never edited).
- **Do not do** the renderer refactor, publish to npm, add a global npm bin, or
  write any "arm is green" claim into a record. See handoff §3.

## Acceptance criteria (self-check before finishing)

- [ ] `uv run pytest -q` green, incl. the four ADR/registry tests
- [ ] `from fux import open` works, covered by a test
- [ ] `node --test node/test/` → 9/9
- [ ] `uv run python tools/differential/node_arm.py .` → **0 discordant on the
      real 253-shard index** (it has only ever run on 15 shards)
- [ ] `uv run python tools/differential/graph_arm.py .` → N2 IDENTICAL
- [ ] `fux setup` in a scratch repo writes `.fux/node/` + `.fux/fux`, and
      `node .fux/node/fux.mjs find <term>` answers there
- [ ] `fux doctor` reports nothing undeclared
- [ ] Docs updated per §9.5; the CLAUDE.md diff surfaced, not applied

## Report back with numbers, not adjectives

- the `node_arm` comparison count and discordant count **on 253 shards**
- the `graph_arm` digests
- the scan p95 at full corpus, if you measure it — and **if it is anywhere near
  150 ms, stop and tell me the number rather than tuning.** The fence catches an
  algorithmic divergence; a fence that gets moved is not a fence.

## Guardrails

- **Ask before** deleting anything, rewriting `CLAUDE.md`, changing a frozen
  document, or touching a file another session has open.
- If a requirement is ambiguous or conflicts with what you find in the code,
  **STOP and ask** rather than guessing.
- Handoff §10 has three open questions. **O1 (does Node enforce the pii gate)
  changes what a Node-only clone can do — confirm with me before implementing
  it.**
