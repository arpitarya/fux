# Handoff: finish W-107 — wire the Node read plane into the repo's own rules

**One-liner:** The Node reader, the Python API and the two ADRs are written and
green in isolation; this wires them into the register, the wheel, `fux setup`
and CI, then verifies on the real 253-shard index.

**Owner / executor:** Claude Code, on `arpits-macbook` (the Cowork shell is wedged)
**Status:** Ready to build
**Stress-tested:** Debated 2026-09-12 against the plan as committed. **Three
findings, two of which changed the plan:**

1. 🔴 **`api.py` re-introduced the ~70 ms decoder import** that `cli.py`
   explicitly avoids — its gate did `from .ingest import pii`, and `cli.py`
   spells the path inline with a comment saying why. **Fixed before packaging**
   (stat first, import only on the cold path where it is about to raise).
   Already committed.
2. 🟠 **W-107 R2's size argument was framed for ONE file** (*"~200 KB"*). The
   reader is **37 files, 196 KB**. The conclusion survives — 196 KB against a
   9.6 MB index is still 2 %, and still less than `.fux/decoders/` — but a
   consumer's `git status` now shows **37 new files** after `fux setup`, not
   one, and every version bump re-diffs them. R2's wording needs correcting
   rather than its ruling.
3. 🟠 **Copying `node/` into `src/fux/templates/node/` would put a second copy
   in the repo** — the drift surface this codebase exists to avoid. Hatchling's
   `force-include` maps `node/` into the wheel at build time with no second
   copy. **Plan changed to use it.**

**Residual risk:** the arms have only ever run on 15 shards / 48 documents. The
253-shard run is the first real one, and it is where an N4 latency problem
would first appear.

## 1. Context & background

[W-107](../work/open/W-107-node-read-plane.md) is the Node read plane: a second
reader for an index Python writes, held byte-equal by a third arm of the
differential law. Phases 1–3 are implemented and every gate that can run without
the repo's own test suite is green (174 comparisons on `find`+`ask`, N2 digest
identical, chunker 50/50, refer plane 170 passage-sets, 9 Node pins).

**What is NOT done is the part that needs the repo's own rules applied**: the
ADR register, the wheel, `fux setup`, CI, and the doc discipline `CLAUDE.md`
requires. Two of those make the suite fail today.

## 2. Definition of done

- [ ] `uv run pytest -q` is green — **including** `test_adr_ownership.py`,
      `test_adr_owns_consistency.py`, `test_adr_register_status.py`,
      `test_doc_registry.py`, which fail right now
- [ ] `from fux import open` works and is covered by a test
- [ ] `node --test node/test/` — 9/9
- [ ] `uv run python tools/differential/node_arm.py .` — **0 discordant on the
      real 253-shard index**
- [ ] `uv run python tools/differential/graph_arm.py .` — N2 IDENTICAL
- [ ] `fux setup` in a scratch repo writes `.fux/node/` + `.fux/fux`, and
      `node .fux/node/fux.mjs find <term>` answers there
- [ ] `fux doctor` does not report `.fux/node/` or `.fux/fux` as undeclared
- [ ] Documentation updated to match (§9.5)

## 3. Scope

**In scope:** the register rows, the `__init__` re-export, the wheel packaging,
the `fuxdir` vendoring, the CI workflow, the doc discipline, and the verification.

**Out of scope (explicit) — do not "helpfully" add these:**

- 🔴 **The renderer refactor.** `cmd_ask -> print(render(api.ask(...)))` is the
  finished shape and **ADR-API records it as deliberately staged**. It touches a
  1 481-line hot file. Not in this change.
- 🔴 **Publishing to npm.** `fux-engine` is not to be published here, and **no
  global bin ships in the first release** (W-107 R1a).
- 🔴 **Reporting any differential arm as "green" in a record.** PRE-REG-NODE §4
  names `fux-playground`, which L9 voided as an instrument. A frozen
  pre-registration is superseded, never edited. Run the arms, report the
  numbers in the WORKLOG — do not write "N0 passes" into an ADR.
- Touching `PRE-REGISTRATION-NODE.md` at all. It is frozen.
- `--expand`, `--why`, `--receipt`, `--journal`, `verify` in Node.
- Moving `Tune.rerank_weight` off `0.0`.

## 4. Current state

- Repo: `~/my_programs/fux`, branch as-is. ⚠ **The tree already has ~120
  uncommitted files from other sessions.** Do not `git checkout`, `git stash`
  or `git reset` — read `git status` first and keep your changes separable.
- Written and committed already (do not rewrite):
  - `node/` — 37 files: `fux.mjs`, `mcp-tools.json`, `package.json`,
    `README.md`, `src/**`, `test/pins.test.mjs`
  - `src/fux/api.py`
  - `docs/adr/0155_node-search.md`, `docs/adr/0156_api.md`
  - `tools/differential/{node_arm,graph_arm,adversarial_corpus}.py`
  - `work/open/W-107-node-read-plane.md` (the rulings; read §Rulings first)
  - `work/open/W-107-fuxdir-node-vendor.py.txt` — **the code for step 4, to apply**
- Patterns to follow: `.fux/decoders/` and `.fux/fetchers/` for how `fux setup`
  lays down consumer-visible files; `store/fuxdir.py` for the declaration table.

## 5. Technical approach (decided)

- **`.fux/node/` is committed, engine-owned and OVERWRITTEN** on a version
  difference — the fourth shape in ADR-DOTFUX. **Not write-if-missing**: nobody
  edits a vendored reader, and a stale one against a bumped `_format` is a
  wrong answer rather than an old preference. (The evidence is this repo's own
  `.fux/decoders/` `doc`-suffix rename, which shipped with no migration.)
- **The wheel carries `node/` via hatchling `force-include`, not a second copy
  in the repo.** Changed during the debate — see Stress-tested (3).
- **The PII gate is a stat, never an import of `fux.ingest`** — see
  Stress-tested (1), already applied to `api.py`.

## 6. Non-negotiables / constraints

- **`node/` has NO `dependencies` key and no build step.** A build step is a
  dependency (L1). Do not add a bundler, a TypeScript pass, or a `postinstall`.
- **Do not change any ranking arithmetic** — `bm25f`, `rank`, the sort key, the
  analyzer, `blake2b`. They are pinned against Python and the pins pass.
- **Do not silently rewrite `CLAUDE.md`.** Propose the edit and surface it.
- **Law zero:** any change under an ADR-owned path touches that path's OWNING
  record in the same commit, or the commit message carries `no ADR affected` on
  its own line. `scripts/adr-guard.sh` enforces it as a `commit-msg` hook.
- **Use `git --no-optional-locks`** for read-only git on any bridge surface
  (`work/MACHINE.md`).
- ASCII-only in anything `fuxdir.py` writes — `ensure_layout` encodes to ASCII
  and one em-dash fails the write on a Windows console.
- **Do not touch:** `work/golden/` (sealed), `work/regression/**` (frozen
  evidence), `PRE-REGISTRATION-NODE.md` (frozen).

## 7. Dependencies & prerequisites

- Node ≥ 20 on PATH (`node --version`); Python ≥ 3.11 via `uv`.
- No network, no credentials, no env vars. Everything is local.
- `.github/workflows/node-arm.yml` must be placed **by hand** — remote tools
  are blocked from writing that path, which is why it arrived as an attachment.

## 8. Edge cases & risks

- **The register tests are strict about format.** Read an existing row in
  `docs/adr/README.md` and match it exactly — the ownership table is parsed by
  `awk` in `scripts/adr-guard.sh`, so a stray backtick or a trailing `/`
  changes what it matches.
- **`_packaged_node_files()` raises if the wheel lacks the data.** Verify with
  an actual install (`uv pip install -e .` then `fux setup` in `/tmp`), not by
  reading the config.
- **`fux doctor`'s undeclared-entry check will fire** on `.fux/node/` and
  `.fux/fux` until `COMMITTED`/`COMMITTED_FILES` are updated. That is the
  check working; update the tables.
- **`.fux/README.md` is generated and write-if-missing** — its declaration
  table comes from those same dicts, so a repo that already has the file keeps
  the old table. Expected; note it, don't force-rewrite.
- **N4:** if the 253-shard scan p95 is anywhere near 150 ms, stop and report the
  number rather than tuning. The fence catches an algorithmic divergence, and a
  fence that gets moved is not a fence.

## 9. Testing & validation

```bash
uv run pytest -q
node --test node/test/
uv run python tools/differential/node_arm.py .
uv run python tools/differential/graph_arm.py .

# the adversarial corpus, in a COPY — never the real index
cp -R . /tmp/fux-adv && cd /tmp/fux-adv
uv run python tools/differential/adversarial_corpus.py .
uv run python tools/differential/node_arm.py .
```

New tests to add:

- `tests/test_api.py` — `from fux import open` works; `open()` outside a root
  raises `FuxError`; `open()` without `.fux/pii.toml` raises; `find`/`ask`
  return the documented shapes and `as_dict()` validates against
  `query/output.schema.json`.
- `tests/test_setup_node.py` — `fux setup` writes `.fux/node/package.json` at
  the engine version and an executable `.fux/fux`; a second `setup` is a no-op;
  a version mismatch rewrites.
- Extend `tests/test_cli.py`'s existing "the two are held equal" check to cover
  `api._PII_RULES` alongside the CLI's copy.

## 9.5 Documentation impact

- [x] **ADR / decision record** — `0155_node-search.md` and `0156_api.md` exist;
      **the register (`docs/adr/README.md`) must gain rows and ownership
      entries.** ADR-DOTFUX gains the fourth-shape amendment; ADR-MCP gains the
      shared-tool-description-file decision.
- [x] **README** — the front door should say a Node reader exists. One line
      under *Install*: `npx fux-engine find <query>` / `node .fux/node/fux.mjs`.
- [x] **CHANGELOG** — user-facing: a second reader, and an importable Python API.
- [x] **`.fux/README.md`** — the generated declaration table gains `node/` and
      `fux` automatically once the dicts are updated; its *Calling fux from a
      script* section should gain the **in-process** Python form beside the
      subprocess one, and drop *"the CLI is the contract; the modules are not"*.
- [x] **`work/DOC-REGISTRY.md`** — rows for `node/`, `src/fux/api.py`, the two
      ADRs, `tools/differential/`.
- [x] **`work/WORKLOG.md`** (one entry), **`work/IMPLEMENTATION.md`** (one row),
      **`work/open/W-107-node-read-plane.md`** (tick Phases 1b–4; leave 1a's
      renderer half open), **`work/OPEN-WORK.md`**.
- [ ] **CLAUDE.md** — ⚠ **propose, do not apply.** Its §Follow the OKF pattern
      and §Where the state of play lives may want a line about `node/`. Surface
      the diff for Arpit.

## 10. Open questions

- **OPEN QUESTION (O1, W-107):** the Node reader does **not** enforce the
  `.fux/pii.toml` gate today; `api.py` does. Recommend making Node match, which
  means `fux.mjs` stats the file before dispatching any verb. **Confirm before
  implementing** — it changes what a Node-only clone can do.
- **OPEN QUESTION (O2):** is `fux.api` public at 1.0, or marked provisional
  through alpha? ADR-API currently says public and frozen.
- **OPEN QUESTION:** `src/fux/__init__.py`'s docstring still says *"rank
  organizational knowledge"* and *"stdlib-only runtime"*. Both are now false
  (today's positioning ruling; L1's 2026-09-06 amendment). Fix on contact —
  confirm the replacement wording.
