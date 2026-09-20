---
type: Standing Record
kind: component
name: SR-NODE-SEARCH
title: "SR-NODE-SEARCH (0153) — the Node read plane: one index, two readers, three arms"
description: "Why a Node reader exists, what it may and may not do, and the decisions that keep it from becoming a second product: the _format version policy, the never-fetch rule, the url: verdict asymmetry, the shared tool-description file, and the three places where Node is deliberately a SUBSET of Python rather than a copy — the derived graph plane, the accelerator label, and the decoder boundary. Decisions 13-16 carry the SHIPPING shape, ruled AND BUILT on 2026-09-12: the consumer gets a published artefact rather than source, the bundle is built at publish time into both registries, a monorepo is auto-detected and wired up, and the .fux/fux shim resolves the binary across five package managers."
status: accepted
date: 2026-09-12
feature: "`node/` — the zero-dependency Node.js read plane, published as `fux-engine`, vendored into `.fux/node/` by `fux setup`, and held byte-equal to Python by the third arm of the differential law"
owns: [node@54b87937e653, src/fux/store/nodebundle.py@071a24a596dd]
laws: [L1, L3, L4, L6]
ratifies: "Arpit, 2026-09-12 — R1-R6 in W-107, which closed the same day (archive/open/W-107-node-read-plane.md); and decisions 13-16, ruled the same day in the exchange recorded in work/open/W-149-the-consumer-gets-no-source.md §1"
timestamp: 2026-09-12T00:00:00Z
content_sha: 33b45ab84d50ed66245904291b6d4d8b448c39d6fe73c5105077e29ebbf28ea2
---

# SR-NODE-SEARCH — the Node read plane

## §1 — For humans

**A fux index is a small, plain-text index committed to git.** Python writes
it. Until now Python was also the only thing that could read it, which made
"clone and ask" a promise fux could only keep for people who had Python.

`node/` is a second reader. It is published to npm as **`fux-engine`**,
invoked as **`fux`**, and vendored by `fux setup` into **`.fux/node/`** so a
clone with nothing installed still answers.

**It is not a port in the usual sense.** A port is allowed to be different in
ways nobody minds; this one is held byte-equal to Python by a third arm of the
differential law, and **every difference is a defect until
[PRE-REGISTRATION-NODE](../work/benchmark/PRE-REGISTRATION-NODE.md) says
otherwise.**

## §2 — For agents

⚠ **2026-09-15 — `store/fuxdir.py` and `doctor.py` changed under this record and
NOTHING this record decides moved.** W-185 added `index/*.jsonl.tmp` to
`_GITIGNORE` and an `index temp files ignored` row to `doctor`. This record
describes `ensure_node_reader` and friends in the first file and `_node_reader`
/ `_installed_reader` in the second; **none of them is touched**, and
`node/node_modules/` is listed exactly as W-149 left it.

⚠ **Said out loud rather than left to the freshness gate**, which proves a
record was *touched* and never that it was read: the changed symbol is a module
CONSTANT, and the gate resolves top-level `def`/`class` names only, so a
constant edit deliberately reads as *every symbol* and demands every describer.


### Context

W-107 carried the plan; **it closed on 2026-09-12** and this record carries the
decisions that outlive it. What grounds them is
[`2026-09-12-node-tune-and-surfaces`](../work/regression/2026-09-12-node-tune-and-surfaces/report.md)
and [`2026-09-12-node-arm-rungs`](../work/regression/2026-09-12-node-arm-rungs/report.md),
never the retired item — its file is named in
[`archive/README.md`](../archive/README.md) and may not back a live claim.
What it could **not** close is
W-148 (closed 2026-09-15).

⚠ **Decisions 9-11 were all found on one day, 2026-09-12, by pointing the
differential arm at surfaces it had never covered** — the graph verbs, the MCP
server and the library export. Each was a place where Node answered *something*
where Python answers something else or refuses, and none of them could have
been caught by the arm as it stood, because the arm compared `find` and `ask`
and nothing else. That is the pattern, and it is worth more than the three
findings: **a transcription is only as true as the surface the instrument is
aimed at.**

### Decision

**1. Scores are equal after `round(9)`; ordering is byte-equal.**
A link to [SR-RANKING decision 8a](0111_ranking.md), never a second statement
of the rule (L0). `Math.log` and `math.log` genuinely differ — 655/100 000 on
darwin, 722/100 000 on glibc — but every difference is one ulp and **none
survives `round(9)`**, which is the sort key's own resolution.

⚠ **Ordering is not subject to that tolerance.** A discordant top-5 fails the
arm. The tolerance is on the printed score field and nothing else.

**2. The `_format` version policy: refuse, naming both versions.**
A reader that guesses at an unknown `_format` corrupts every `df` silently, and
the corruption is undetectable at query time. `store/reader.mjs` refuses, and
the message says which version the index is and which the reader speaks —
because the fix ("upgrade the reader" versus "re-ingest") depends on which way
round they are.

**The vendored copy makes this unreachable in practice**, which is the real
guard: `.fux/node/` is rewritten by `fux setup` whenever the engine version
differs, so the reader in a repo is always the one that wrote the index. The
npm copy is where the policy binds, because there a consumer picks versions.

**3. Node NEVER fetches.** Not "does not by default" — there is no transport in
`node/`, no fetcher seam, and nothing to inject one through.

- `file:` reads the working tree. **Reading your own checkout is not a fetch.**
- `url:` reads `.fux/acquired/` if the blob was retained, else the answer falls
  back to `source: "index"`.

**4. …so the `url:` verdict set is ASYMMETRIC with Python's, deliberately.**

| verdict | Python | Node | why |
|---|---|---|---|
| `current` / `stale` | `file:` and `url:` | **`file:` only** | Node cannot look at a URL |
| `as-ingested` | yes | yes | the acquired blob is local |
| `unverified` | yes | yes | *we did not look* |
| `cached` | yes | **never** | a TTL fetch cache requires fetching |

🔴 **This is a decision and not a gap.** The alternative — Node reporting
`current` for a URL it never checked — would make the claim-strength vocabulary
mean different things in two runtimes, which is the one thing
[SR-URL-FRESHNESS](0147_url-freshness.md) exists to prevent.

**5. The MCP tool DESCRIPTIONS live in one file both runtimes read.**
`node/mcp-tools.json`, read by `src/fux/mcp.py` and `node/src/verbs/mcp.mjs`.

A description is what an agent reads to decide whether to call a tool. Two
hand-maintained copies would drift into **two different products wearing one
name**, and the drift would be invisible: both would work, and they would
advise differently. `{{TOP}}` is the only substitution, filled with the
connection's resolved `[mcp] top`.

**6. `node/` is many files, one per Python module, at the same relative path.**
Superseding `search-v3.md` §6.4's *one ESM file*. Phase 4's freshness test maps
each Python module to its Node twin, which needs more than one file, and a
6 000-line `.mjs` is unreviewable.

⚠ **This decision governs what is AUTHORED, and since 2026-09-12 that is no
longer the same thing as what SHIPS** — see decision 13. `node/` stays many
files and `tests/test_node_twins.py` is unchanged; the consumer receives one
bundled artefact. The rule stands; its reach narrowed.

✅ **That test landed 2026-09-12: `tests/test_node_twins.py`.** The map is
derived three ways in order — the path rule (`x/y.mjs` → `src/fux/x/y.py`, or
`_y.py` for a private module), else a `src/fux/….py` path the module names in
its own header, else the two-entry exemption set. **It also fails when a Python
twin changes in the working tree and its `.mjs` does not** — which the
differential arm structurally cannot catch, because a Node module nobody
updated still agrees with itself and only disagrees with Python on a corpus
that exercises the changed branch.

**The exemption list is short and visible, and that is the point** — it is
exactly where the divergence risk concentrates:

| Node file | why it has no twin |
|---|---|
| `src/hash/blake2b.mjs` | Python uses `hashlib`; `node:crypto` cannot do arbitrary digest sizes |
| `src/compat/pyfloat.mjs` | Python float semantics JS does not share — see decision 7 |
| `src/config/toml.mjs` | Python has `tomllib`; Node has no TOML |
| `src/verbs/*.mjs` | one-to-many against `query/__init__.py`, recorded here |

**7. Three Python semantics are reimplemented, and each is a correctness fix.**

- **`round(x, 9)` is half-EVEN on the exact binary value.**
  `Number(x.toFixed(9))` is half-UP and fails exactly on ties — and a tie
  resolved the other way is a different ORDER.
- **`repr(float)` switches to an exponent at `e < -4 or e >= 16`;** JS at
  `-6 / 21`. Both are shortest-round-trip, so only the layout differs.
- 🔴 **Python compares strings by CODE POINT; JS `<` compares by UTF-16 code
  UNIT.** A surrogate pair sorts BELOW U+E000–U+FFFF in JS and ABOVE it in
  Python. The sort key ends in `id`, so **one document id containing an emoji
  or a rare CJK extension character orders differently in the two runtimes** —
  measured 2026-09-12: **30 of 324 ordered pairs disagree.** Every comparison
  on a doc id goes through `cmpCodePoints`.

**8. ✅ Node reads `.fux/tune.toml` and `.fux/output.toml`. CLOSED 2026-09-12.**

This decision was filed as a **gap, not a decision**: Node read neither file,
so a consumer who ran `fux tune` got **a different ranked list from the same
index at the same engine version**, with nothing saying so. `fux-engine` is on
npm and `fux setup` vendors the reader into every consumer's `.fux/`, so the
blast radius was every repository that had ever been tuned. Decision 2's
`_format` refusal did not reach it: the versions agreed and the answer still
differed.

**Measured before and after**, on fux's own repo, whose tune sets
`rerank_weight = 0.3`
([`2026-09-12-node-tune-and-surfaces`](../work/regression/2026-09-12-node-tune-and-surfaces/report.md)):

| | before | after |
|---|---|---|
| contract arm (tune applied) | **90 of 174 discordant** | **0 of 199** |
| transcription arm (`--no-tune` both sides) | 0 of 174 | **0 of 199** |

**What closed it, and where each piece went:**

| file | what it is |
|---|---|
| `node/src/config/toml.mjs` | the TOML subset. **No Python twin — CPython's `tomllib` is the twin**, and it is stdlib, which is why this exists at all |
| `node/src/config/tune.mjs` | the reader half of `tune.py`: the defaults, the closed key set, the validators and the error COLLECTION. Not the writer half — Node never writes this file |
| `node/src/config/output.mjs` | `output_config.py`'s precedence chain and both closed key sets |
| `node/src/query/rerank.mjs` | the proximity reranker, which reads document content and so lands with the refer plane |
| `node/src/ingest/{sourcelist,gitdir}.mjs` | the `archived=true` declaration, read live from `.fux/sources/dirs` rather than trusted to the record's stamped property |
| `node/src/query/run.mjs` | where they all enter — `find`, `ask`, `answer`, `graph` and the library export are projections of it |

🔴 **The integer/float distinction is carried, and it is not pedantry.**
`tune.py::_at_least` refuses `[graph] iterations = 3.0` and accepts `3`; JS has
one number type. `config/toml.mjs` records, per table, which keys were written
as TOML **floats**. Without it Node would silently load a file Python refuses —
a divergence in which repositories *work*, which is worse than a divergence in
what they mean and far harder to notice.

⚠ **What the differential arm could never have caught here**, and why the
closing change ships equality tests instead
(`tests/test_node_config_parity.py`): a drifted key set only shows on a corpus
whose tune actually sets the drifted key, and **every golden rung's tune is
all-defaults**. A drifted *refusal* never shows at all — a repository one
reader refuses and the other accepts produces an error on one side and an
answer on the other, which the harness reports as a crash rather than a finding.

⚠ **`--no-tune` is a two-runtime flag now, or it is not the switch it claims to
be.** [SR-TUNE](0135_tuning.md) decision 11 calls it the *"is it me or the
config?"* switch; a flag that exists in one reader can only ask the question of
that reader. `node/fux.mjs` parses it and `tools/differential/node_arm.py`
passes it **to both sides or to neither** — flipping only Python's would compare
a tuned reader against an untuned one and file `.fux/tune.toml` as a
transcription defect.

**9. The graph lane is ASYMMETRIC: Python requires `fux build`, Node does not.**
Found 2026-09-12.

`graph/plane.py::load` reads the derived `.fux/runtime/graph.json` and
**refuses** when it is absent or stale. Node rebuilds the same plane in memory
from the committed records and answers either way.

**Node's behaviour is the right one for its audience and is kept.** The reader
exists for a clone with no Python; `.fux/runtime/` is gitignored and is written
by `fux build`, which is Python — so requiring it would make the Node reader
refuse precisely where it is the only reader present.

⚠ **It follows that `explain`, `graph` and `path` cannot be compared on a
corpus with no fresh build**, and the harness says so out loud rather than
skipping quietly (`node_arm.py::graph_lane_ready`). A lane that silently does
not run is how `find` went a month without its tune file.

**10. `ranked_by` names the candidate path, and the two runtimes differ there —
which is honest, not a defect.**

`mcp.py::_search` passes `force_scan=False` and reports `"accelerator"` when a
fresh build exists. Node has no accelerator and reports `"scan"`. The
differential law asserts the two paths return **the same documents in the same
order**, so the label is the only difference, and each side's label is true of
itself. The differential arm excludes this key **by name** — never by a
loosened comparison.

**11. 🔴 Node does not refer a document it cannot DECODE. It declines.**
Found 2026-09-12.

Python's refer plane runs a cited document's bytes back through the decoder
plane before chunking, so a `.csv` is re-scored as the Markdown table ingest
indexed. Node has no decoders and was chunking the **raw bytes** — producing
`path:L20-L28` locators that point at real lines of a file whose text the index
never contained. Caught by comparing the two library surfaces on this repo:
`answer("rollback")` returned a different document, a different passage and a
different locator in each runtime.

**Porting the decoders is not the fix and never will be.** A consumer decoder
is arbitrary Python in `.fux/decoders/` ([SR-DECODE](0139_decode.md)'s whole
boundary) and there is no Node twin of a file the consumer wrote in another
language; nor can `xlsx`, `pdf` or `docx` be transcribed safely, because a
near-miss there produces *plausible* text.

**So Node declines, in the shape decision 3 already uses for the network.** A
document whose type goes through a decoder is skipped by `answer`, exactly as
an unreachable `url:` is, and the verb falls back rather than citing something
it cannot reproduce.

⚠ **The question is asked the right way round.** Not *"does a decoder claim
this extension?"* — which would need the built-in registry, every
`.fux/decoders/*.py` and their precedence, all mirrored in JS and all able to
drift — but *"is this document ALREADY TEXT?"*, which `.fux/formats.toml`'s
`include` list answers in committed bytes both runtimes read. A bound extension
is never repeated in `include` ([SR-TYPES](0128_types-list.md) decision 12), so
the two sets do not overlap and the complement is exact. **Under-claiming is the
only safe direction**: a document wrongly treated as plain text is a wrong
citation, one wrongly skipped is an answer from the next candidate.

**The arm asserts the invariant, not equality.** Once Python refers a decoded
document Node skipped, the two rescore over different passage populations —
`df` is computed across the candidate set — so every score downstream
legitimately differs, and comparing there would be meaningless rather than
merely weak. What is checked on **every** answer is that nothing Node cites is
a decoded document.

**12. The MCP handlers read the argument names the SCHEMA advertises.**
Found 2026-09-12, in a package already on npm.

`node/mcp-tools.json` declares `path` for `fux_passage` and `fux_related`;
Node's handlers read `args.id`. Every conformant client therefore got an empty
answer **from a server reporting success**. `fux_search` additionally returned
five of the nine keys Python returns, and none of `ranked_by`, `confidence` or
`next` — so the one key [SR-CONFIDENCE](0141_confidence.md) exists for was
absent from the surface it exists to serve.

Nothing could have caught this except comparing the two servers: each was
internally consistent, and the shared descriptions file held only the
descriptions, not the handlers. `node_arm.py::compare_mcp` now drives both over
one stdio session per run.

**13. 🔴 The consumer gets NO SOURCE. `.fux/node/` carries a published
artefact, never a copy of `node/`.** RULED by Arpit 2026-09-12 and **BUILT the
same day** (W-149, closed).

> *"`src` is not needed for the consumer. It should just be the bundled code
> which needs to be executed on the system."*

Two shapes, both shipping, consuming the same published artefact:

| | `.fux/node/` holds | offline | how it runs |
|---|---|---|---|
| **A**, the default | `package.json` · the bundled `fux.mjs` · `mcp-tools.json` · `README.md` | **yes** | the `.fux/fux` shim — decision 16 |
| **C**, a monorepo | `package.json` only, declaring `fux-engine@<version>` | after install | the shim, which resolves the installed bin |

**What shipped.** `fuxdir._packaged_node_files` returns the four-file payload;
`ensure_node_reader(root, shape=...)` writes the declared shape and
`_prune_node_reader` deletes everything else under `.fux/node/`, **`node_modules/`
excepted** — that directory holds shape C's installed reader, and deleting it
would leave a manifest pointing at nothing. **The shape is read back OFF the
directory** (`node_shape`: shape C's manifest declares a `fux-engine`
dependency and shape A's never does), so there is no fifth config file and a
consumer who switches by hand gets the shape they actually created.

**What it replaces:** `_packaged_node_files` walked the whole packaged tree, so
`fux setup` wrote **47 files, 223 KB, 5 484 lines** into a consumer's git, and
`ensure_node_reader` **pruned nothing** — every version bump re-diffed all of
them. The consequence block below recorded the growth and asked no question of
it; this is the answer.

⚠ **The prune is part of the decision, not a follow-up.** Without it, every
repository that ever ran `fux setup` keeps its 37-47 stale files for good.

🔴 **And the VERSION is not a sufficient trigger for it — found by running the
migration on fux's own repository, not by reading the code.**
`ensure_node_reader` rewrote on a version difference, so a `.fux/node/` written
by *this* version before the payload changed shape kept its 44 modules: the
version matched, nothing was rewritten, and the prune never ran. A consumer
upgrading across a release is covered; **anyone tracking one alpha from git is
not, and fux itself was not.** So the trigger is version **or shape or LAYOUT** —
`_layout_is_stale` compares the file-name set against the shape's declared one,
which is cheap enough for the head of every ingest because it builds nothing.
✅
It ships with the rest, and `tests/test_setup_node.py` asserts both halves — the
tree goes and `node_modules/` stays. **The test that used to assert the opposite**
(*"writes the whole tree, not just the entry point"*, naming
`src/query/bm25f.mjs` by hand) **is the same file, rewritten**, which is the only
honest way to record that a decision reversed.

**14. 🔴 The bundle is built when fux PUBLISHES, and ships inside BOTH
distributions.** RULED by Arpit 2026-09-12 and **BUILT the same day**.

> *"It should be bundled and then published in Python as well as in the npm
> package."* — *"It shouldn't be bundled at the consumer end."*

- **One build, two registries.** The bundle exists before either job in
  [`publish.yml`](../.github/workflows/publish.yml) runs, off the single
  `release: published` trigger, so a bundle built per-job cannot ship two
  registries disagreeing.
  ⚠ **The halves were NOT symmetric until 2026-09-14** — PyPI automatic via
  OIDC, npm **staged and waiting for a human**. **Arpit ruled them symmetric on
  2026-09-14** and `publish.yml` now runs `npm publish`: both registries go out
  off the one trigger, with no human in either path.
  🔴 **What the asymmetry actually cost is why it went.** `2.0.0` staged on
  2026-09-13 and `2.0.1` on 2026-09-14 and **neither was ever approved**, so
  npm's `latest` went on pointing at `2.0.0-alpha.7` — published 2026-09-02 —
  while PyPI moved twice. Two releases were live on one registry and absent
  from the other, and nothing failed, warned or blocked: the release workflow
  was green each time, because staging IS its success. **A gate nobody walks
  through does not hold the line, it just hides which side of it you are on.**
  ⚠ **One thing moved out of this repository and cannot be asserted from it.**
  The direct publish works only while `Allow npm publish` is ticked on the
  `fux-engine` trusted publisher at npmjs.com. Untick it and the npm job fails
  with a registry refusal that no diff in this tree explains. It is named here
  because it is now a precondition of a release succeeding, and the only
  written trace of it is this paragraph and the comment beside the step.
- ✅ **This is why *"no build step — a build step is a dependency"* survives.**
  The line narrows to **the consumer's end**, which is the end it was ever
  about. Fux's release has a bundler; nobody running `fux setup` does.
- **The bundler is fux's own, zero-dependency, and deterministic** — same
  sources, byte-identical bundle. [L1](0003_LAW-1-zero-cost.md) would permit a
  third-party one; nothing needs it. ⚠ **Determinism here is a promise adopted
  voluntarily, not [L3](0005_LAW-3-deterministic.md) reaching a build
  artefact** — L3 binds the index. Stated so nobody later cites the wrong
  authority for it.
  ✅ **What it is:** [`src/fux/store/nodebundle.py`](../src/fux/store/nodebundle.py),
  ~300 lines of stdlib. Each source module becomes an **IIFE returning its
  exports**, emitted in topological order with a path tie-break; `node:` imports
  are hoisted and deduplicated; the entry's shebang moves to line 1.
  🔴 **It is not a parser, and it REFUSES rather than skipping.** A flat
  concatenation would have to rename — `signals`, `isArchivedLoc`, `STOPWORDS`,
  `DEPTH` and `K` are each exported by two different modules — and a renaming
  bundler without a real JS parser is a silent-wrong-answer machine. So every
  form the tree does not use (`export default`, `export … from`, a bare package
  import, a cycle, a builtin name bound two ways) raises `FuxError` **with the
  offending line in it**. A dropped statement compiles and answers differently,
  which is the one failure mode a build step may never have.
  ✅ **And the test is on ANSWERS, not bytes** (`tests/test_node_bundle.py`):
  the bundle and the module tree are run through `find`, `ask`, `answer`,
  `--version` and a real MCP session and must agree exactly. Byte-identity
  across builds is asserted too, but it is the weaker claim.
- 🔴 **A checkout has no bundle, and must not quietly fall back to the module
  tree.** `_node_source()` resolves `node/` beside `src/` when the wheel's
  template is absent; there, `fux setup` **builds the bundle or refuses with a
  message saying so.** Silently vendoring `node/src/**` in development and the
  bundle in release is two products wearing one version.
  ✅ **Built both ways round.** In a checkout `_packaged_node_files` calls the
  bundler; in a release install it copies the payload — and if that payload ever
  contains a `src/` file it **refuses**, naming L10, rather than writing fux's
  source into a repository.
  ✅ **The wheel gets it from a hatchling build HOOK**
  ([`hatch_build.py`](../hatch_build.py)), not a static `force-include`: a
  generated file cannot be named in an include list without somebody having
  remembered to generate it first. `pyproject.toml` no longer mentions
  `node/src` at all, which is this record's own veto check.
- **The npm package's own shape changes with it** — `exports` leaves
  `./src/index.mjs`, `files` drops `"src"`. A published-surface change, so it
  lands in the next alpha rather than being back-fitted to `2.0.0-alpha.7`.
  ✅ **Both now name `fux.mjs`, and one file therefore carries two surfaces.**
  `node/fux.mjs` re-exports `open` and `Index` from `src/index.mjs` and runs
  `main()` **only when it is the program** — the standard ESM entry check,
  through `realpath` so a package manager's `.bin` symlink resolves to the same
  file. 🔴 **Unconditional invocation was safe while the library lived in a
  separate file and became a bug the moment one bundle served both**: `import
  "fux-engine"` would have parsed the caller's `process.argv` and set their exit
  code. Asserted directly, because nothing else would notice.
  ✅ **`mcp-tools.json` is now RESOLVED rather than addressed.** It sits two
  directories above `src/verbs/mcp.mjs` in this repo and beside the bundle in a
  consumer's, so a constant path works in one shape and throws `ENOENT` in the
  other — and the other is the one people run.
  ✅ **`publish.yml` builds it ONCE**, in the `build` job before either
  registry job exists, uploads it as an artifact, and stages npm from
  `node/dist` rather than from `node/`. `scripts/check-version-parity.py
  --with-bundle` asserts the built bundle's header and `VERSION` against
  `src/fux/__init__.py` — the bundle is a **derivation**, so what is checked is
  the derivation and not a fifth hand-written site.

**15. 🔴 A monorepo is AUTO-DETECTED and wired up — and the dot path is
MEASURED to work.** RULED by Arpit 2026-09-12 (*"Auto detect. Auto detect and
set it up as well."*) and **BUILT the same day**. Grounded in
[`2026-09-12-workspace-dotpath-probe`](../work/regression/2026-09-12-workspace-dotpath-probe/report.md)
and [`2026-09-12-yarn-berry-probe`](../work/regression/2026-09-12-yarn-berry-probe/report.md).

Detected in this order, first hit wins — `setup.py::detect_workspace`:

| signal | shape |
|---|---|
| Yarn Berry (`.yarnrc.yml`, or `packageManager: yarn@≥2`) with `nodeLinker` **unset or `pnp`** | **A** — no `node_modules` exists to resolve from |
| Yarn Berry with `nodeLinker: node-modules` | **C**, yarn — the bin hoists to the root, MEASURED |
| `workspaces` declared as an **object** (`{packages: […]}`) | **A** — an array splicer cannot extend an object |
| `pnpm-workspace.yaml` with `packages:` | **C**, pnpm |
| root `package.json` `workspaces` array | **C**, npm / yarn 1 / bun |
| none of the above | **A** |

Then `.fux/node` is added to that manifest's workspace list and
`.fux/node/package.json` declares `fux-engine@<version>`.

🔴 **THE ORDER ABOVE IS NOT THE ORDER THIS DECISION FIRST CARRIED, AND THE
FIRST ONE WAS WRONG.** It read *"`workspaces` array → C"* **above** *"Berry →
A"*, and a Berry repository declares `workspaces` in `package.json` exactly as
npm does — so a literal first-hit reading gave every Berry repo shape C,
including the PnP ones this decision's own warning said must not have it. **The
record contradicted itself inside one file, which is the W-83 class of failure
and no mechanical check here can see it** (`CLAUDE.md` §Law zero). Corrected in
the change that built it: the Berry test runs **first**, and
`tests/test_setup_workspace.py` pins the order.

✅ **The probe settles the question this was gated on, and refutes the hazard as
it was written.** *"Several package managers' glob handling skips
dot-directories"* was **wrong**: npm, pnpm, yarn 1 and bun all accept
`.fux/node` as a workspace project when it is declared — pnpm says so itself
(`Scope: all 3 workspace projects` against `all 2` on the control).

🔴 **And the control is what makes the wiring load-bearing:** a root manifest
declaring only `packages/*` picks `.fux/node` up in **none** of the four. An
existing monorepo does not acquire the reader by having workspaces. *"Set it up
as well"* is the decision, not a courtesy.

⚠ **Why detection does not conflict with *declared, never detected*.**
[SR-FETCHER](0117_fetcher.md) decision 5, and W-86 fork E's refusal of decoder
auto-detection, both govern **ingest** — where detection would make **the
index** a function of the environment, which is what
[L3](0005_LAW-3-deterministic.md) forbids. **`fux setup`'s scaffolding is not
the index.** Neither precedent reaches it and no law does; W-149 proposed
*declared* on that mistaken reading and records the correction.

Four constraints the decision carries:

1. ⚠ **The manifest edit belongs to `setup` ALONE.** `ensure_node_reader` runs
   at the head of **every ingest** via `ensure_layout`
   ([SR-DOTFUX](0102_fux-directory.md)), whose own rule is that a no-op ingest
   produces a no-op diff. An ingest that rewrites the consumer's
   `package.json` breaks it.
   ✅ **Enforced by STRUCTURE, not by a comment asking nobody to call it**:
   `detect_workspace` and `wire_workspace` live in `setup.py`, and
   `ensure_layout` takes the answer as a keyword (`node_shape=`) it never
   computes. `test_an_ingest_never_edits_the_consumers_manifest` asserts it
   where it could actually be violated.
2. **The edit is format-preserving** — existing indent, key order and trailing
   newline kept. This is fux's **first write to a file it does not own and a
   team reviews**; `fux hooks` writes `.git/`, which is machinery. A one-line
   addition arriving as a whole-file reformat is a bad diff in someone's PR.
   ✅ **A splice, never a re-serialize.** One array editor handles the JSON
   key (`"workspaces":`) and pnpm's bare one (`packages:`), plus the YAML block
   sequence, copying the last element's own indentation and quoting style.
   Asserted on 2-space, 4-space, tab, single-line and empty arrays.
3. **Idempotent, and it says what it touched.** Re-running `setup` never adds
   the entry twice, and the run names the manifest it edited.
   ✅ `fux setup` prints `monorepo detected: declared .fux/node in <manifest>`
   and the install command for the manager whose lockfile is actually present.
4. **Half-configured is not a state.** A monorepo detected but not safely
   editable — comments in the JSON, an unknown shape, a read-only file — gets
   **shape A**, and `fux doctor` says why. A workspace stub with nothing
   resolving it is worse than no workspace.
   ✅ Every refusal path carries its reason to the consumer's terminal, and
   ⚠ **a manifest fux cannot PARSE but which names `workspaces` still counts as
   a monorepo** — returning "no monorepo" there would write shape A with nothing
   said about it. `doctor`'s `node reader` row additionally fails when a shape-C
   manifest is declared and no `node_modules/.bin/fux` resolves anywhere the
   shim would look, which is the half-configured state observed rather than
   assumed away.

✅ **Yarn Berry is MEASURED now, and the second probe this decision owed is
filed** ([`2026-09-12-yarn-berry-probe`](../work/regression/2026-09-12-yarn-berry-probe/report.md),
Yarn 4.1.0). Two findings:

- **`.fux/node` links in Berry too**, in both linkers — `yarn workspaces list`
  names it. The dot path is now fine in **five of five** managers, and W-149's
  hazard 3 is wrong in every one of them.
- 🔴 **The boundary is the LINKER, not the manager.** `nodeLinker:
  node-modules` hoists `fux` to the workspace **root** — rung 3, exactly where
  npm and yarn 1 put it — so shape C works unmodified. **PnP has no
  `node_modules` anywhere**, by design, so neither install rung resolves and
  shape A is required. ⚠ **Berry's default IS PnP**, so an unset key is read as
  PnP: guessing the other way would wire a workspace whose reader nothing can
  resolve, which is constraint 4's state in a new costume. `corepack yarn fux`
  is not a fallback either — under PnP a binary is reached through Yarn's own
  resolver, which a three-line `/bin/sh` shim cannot consult.

**16. 🔴 `.fux/fux` RESOLVES the binary in three rungs; it no longer assumes a
path.** RULED 2026-09-12 and **BUILT the same day**. Measured, same probe.

| manager | root `node_modules/.bin/fux` | `.fux/node/node_modules/.bin/fux` |
|---|---|---|
| npm | present | absent |
| yarn 1 | present | present |
| pnpm | **absent** | present |
| bun | **absent** | present |

npm and yarn hoist the bin to the workspace root; **pnpm and bun do not.** So
the shim tries, in order:

1. `node .fux/node/fux.mjs` — shape A's vendored bundle
2. `.fux/node/node_modules/.bin/fux` — pnpm, bun, yarn
3. `node_modules/.bin/fux`, walking up to the workspace root — npm, yarn

**The shim is therefore the one entry point correct in every shape, and the one
a README may name.** Documenting `node_modules/.bin/fux` would be right for half
the ecosystem and silently wrong for the other half. ✅ SR-DOTFUX's `fux` row
is amended with it, and both READMEs name the shim and nothing else.

✅ **Yarn Berry adds a row and changes no rung** — `node-modules` resolves at
rung 3, PnP at none, which is why PnP takes shape A and rung 1. The shim's
failure message says so, and names the one-line `.yarnrc.yml` change that would
make shape C available.


**2026-09-14 — `src/fux/setup.py` changed under this record and NOTHING this record
decides moved.** The scaffolded `fux.toml` moved into `templates/fux.toml.txt` and grew
derived per-fetcher config tables ([SR-DOTFUX](0102_fux-directory.md)).
`detect_workspace`, `wire_workspace` and `_yarn_berry_linker` — the monorepo
half of decision 15, which is what this record owns in that file — are
untouched, and no byte of `node/` changed.

⚠ **Said out loud rather than left to the freshness gate.** That check proves an
owning record was *touched*, never that it was read (CLAUDE.md §Law zero), so a
co-owner's file changing under this one is exactly the case where a reader needs
to be told *"not yours"* in writing.
**17. THE GRAPH TIER IS ON BOTH READERS, and the asymmetry it inherits is
decision 9's, not a new one** (W-161).

Node composes W-161's two tiers. It does **not** read Python's derived
`.fux/runtime/graph.json` — it rebuilds the plane in memory from the committed
records, exactly as `verbs/graph.mjs` already does, because decision 9 ruled
that behaviour *"the right one for its audience"*: this reader exists for a
clone with no Python, and `.fux/runtime/` is written by `fux build`, which is
Python.

**So the two readers are byte-equal wherever Python has a fresh plane**, **and
diverge on a corpus with no fresh build**, where Python has no tier and Node has
one. That is decision 9's existing asymmetry showing through a new surface.

**17b. 🔴 The generalisation this decision made about CI was WRONG, and the
harness discovered it exactly as the sentence above promised it would not**
(2026-09-16, cutting `3.0.0-alpha.0`).

⚠ **What decision 17 said until now:** that the readers are byte-equal *"wherever
Python has a fresh plane — which is every corpus the differential arm runs on,
because the golden ladder's rungs are built"*, and that the asymmetry *"is stated
here rather than left for the harness to discover"*. The first clause was the
defect and the second is what it cost.

🔴 **`node-arm.yml` runs the arm over THIS repo from a bare checkout**, not over
a ladder rung. Nothing in that workflow ever built anything, so `.fux/runtime/`
did not exist, Python had no tier, Node had one, and **all six matrix jobs went
red at 44 of 202 discordant** — with the step's own comment attributing it to *"a
Node transcription defect and nothing else"*. **Both readers were correct.** The
ladder's rungs are built; this repo was not, and the decision generalised from
the corpus that happened to be fine to the one that gates a merge.

✅ **The gate, not a note:** `node-arm.yml` runs `fux build` before the arm, and
again after `adversarial_corpus.py` rewrites the index — **a STALE plane is the
same as an absent one to `compose.py`**, so the rebuild has to follow every write
to `.fux/index/`, not merely the checkout. Measured both ways at the fix: 44 of
202 without it, **0 of 225 with it**.

⚠ **The general lesson is the one worth keeping.** A stated asymmetry does not
stop a harness from misattributing it — it only makes the misattribution
diagnosable after the fact. What stops it is removing the divergence from the
arm's environment, which is what a build step does and what a paragraph cannot.

**17c. 🔴 Building the plane switched the GRAPH LANE on in CI for the first
time, and it was comparing by the wrong rule** (2026-09-16, same session).

The lane skips without a fresh derived plane, so **it had never run in CI at
all** — `node-arm.yml` built nothing, and the comparison count gives the tell:
**202 without the lane, 225 with it.** Its first run went red at **1 of 225**.

**Nothing was wrong with either reader.** `Arm.compare_verb` — a symbol this
record claims by name — compared graph payloads to the score's last bit, which
is stricter than the cross-runtime contract [SR-RANKING](0111_ranking.md)
decision 8a rules and than the ranking lane beside it already applied. The
premise, and what it cost, are [SR-ACCELERATOR](0110_accelerator.md) decision
14's; this decision states none of it and records only the consequence **for
this reader**: Node's graph verbs were never in breach, and no number measured
against them before 2026-09-16 was measuring what it claimed to.

⚠ **Two defects, and each one hid the other.** A skipping lane cannot fail, so
its comparison was never exercised; a comparison that was never exercised gave
nobody a reason to ask why the lane was quiet. **That is the same shape as 17b
one level down** — a paragraph asserting a property, and nothing checking it —
which is why the close is [`tests/test_differential_arm.py`](../tests/test_differential_arm.py)
rather than a third paragraph.

**17a. 🔴 And it is not free on this reader.** Rebuilding the plane parses
**every** committed record — the work the B2 prefilter exists to avoid — so a
Node `ask` with the tier on pays a full parse that its lexical answer does not.
Python reads one JSON file. **Node's query latency is unmeasured**
(W-148 (closed 2026-09-15) row 2 — the
instrument does not exist), and this is now one more reason it should not stay
that way. `[graph] ask_boost = false` and `ask_related = false` turn it off.

**17b. `fux lexical` and `fux ask` are no longer the same call.** They were one
function on this reader and equal by construction; `fux.mjs` now dispatches
`ask` with `compose: true` and `lexical` with `compose: false`, and `runQuery`
forces both tier booleans off on that argument rather than trusting the caller.
**A repository whose `tune.toml` turns the tier on must not be able to make the
frozen baseline verb stop being a baseline** — every ranking verdict in this
repo cites `lexical` as its control.

**17c. ⚠ `Object.create` + `Object.assign`, never a `{...spread}`, to override
a `Tune`.** `Tune.scoring` is a **prototype getter**; spreading an instance into
an object literal keeps the own properties and silently drops it, so
`resolved.scoring` would be `undefined` and every score would be computed at
default weights — on the frozen baseline verb, with nothing failing. Caught
while writing 17b, not by a test.

**17d. The six `[graph] ask_*` keys are PARSED AND CARRIED by this reader's
tune loader**, and validated identically (`boolean` and `edgeKinds` are twins of
Python's `_boolean` and `_edge_kinds`). A key one reader refused and the other
accepted would make one committed `tune.toml` valid in one runtime and an error
in the other, which is the one asymmetry the config parity test exists to
forbid.


**18. 🔴 THE OBSERVER HOOK IS OUT OF SCOPE ON THIS READER, declared rather
than missing** (W-170).

[SR-OBSERVE](0157_observe.md) decision 1 requires Node's half to ship with the
Python half **or** to be declared out of scope here, in the same change —
*never silently missing*. This is that declaration.

**The reason is not effort.** Python has one post-render dispatch point for
every verb, `cli.main`, and the hook's whole guarantee comes from sitting
there: after the exit code is fixed, after stdout is flushed, after every write
the verb makes. **This reader has no equivalent** — `fux.mjs` dispatches per
verb and each verb writes and returns on its own path — so hosting the hook
would mean either inventing that seam or placing the call in five places, where
*after everything* becomes five things to keep true instead of one.

**Building it twice before the first subscriber exists on either reader is the
trade this refuses.** `.fux/observers/*.mjs` stays reserved and unread; a
subscriber that needs it on this reader is what makes the seam worth inventing,
and this decision is what that change amends.

⚠ **So a repository with observers installed produces records for its Python
runs and none for its Node runs**, and a consumer joining the two will see a
gap that is this decision rather than a bug. That is the cost, and it is stated
so nobody diagnoses it twice.



**19. The Node reader folds anchors identically, and it brought its own
corpus** (W-168 step 1, 2026-09-15).

`scan.mjs`, `bm25f.mjs`, `rank.mjs`, `expand.mjs` and `config/tune.mjs` carry
the same anchor path their Python twins do: the byte regex over every line, the
`at` fold on parsed lines, the second targeted pass through `recordFor`, `atf`
and `alen` on every candidate, and `[bm25f] anchor` read out of
`.fux/tune.toml`.

🔴 **The differential arm could not have caught a forgotten transcription
here.** It answers *do the two readers disagree on this corpus?* — and a corpus
with no document reachable only through a linker's wording exercises no anchor
branch, so a Node half that was never written would agree with itself. So the
feature ships its own fixture: `tests/query/test_anchor_node_twin.py` builds a
corpus that contains the input, switches the key on **in the file a consumer
would edit**, and compares both readers. With the key on the target ranks #1 in
both; with it off, it is unreachable in both.

⚠ **Compared on parsed values, never stdout bytes** — hazard H2: Python prints
`--json` with `ensure_ascii=True` and `JSON.stringify` does not. `score` after
`round(9)`, decision 8a's tolerance.

**19a. `SCHEMA_ID` moved to `fux.index.v3` on the Node side in the same
change**, and **the vendored bundle had to be rebuilt or it would have refused
this repository's index outright.** `.fux/node/fux.mjs` pins the schema string
it was bundled with, so a re-ingested corpus and a stale bundle are a hard
refusal rather than a degradation — which is the right failure, and is the
reason the bundle is regenerated in the same commit as the bump.

⚠ **That rebuild also carried W-161's `related` payload and W-176's `weak`
steering into `.fux/node/`**, which had not been regenerated since. Stated here
because a commit that says *anchor text* and moves 60 KB of bundle owes the
reader the reason.

⚠ **`node/src/ingest/sourcelist.mjs` is narrowed for freshness, and the gap is
covered by parity instead** (2026-09-15, W-178). That module is the **`dirs`
half** of `src/fux/ingest/sourcelist.py` — Node never fetches (decision 3), so
`fetch`, `keep`, `ttl` and `update` decide nothing there. A change
entirely inside the `URLS` spec therefore reported the twin as behind, and
porting it would have meant teaching this reader a grammar for a list it does
not read.

🔴 **The narrowing leaves one thing uncovered and it is named rather than
accepted.** `test_node_twins` narrows by git's hunk-context header, which names
an enclosing `def`; the `dirs` **attribute tuple** is a module-level constant
and has none. So that half is held by
`test_node_config_parity.py::test_the_dirs_attribute_set_is_the_python_one`,
which compares the two tuples by value — the stronger check, because it asserts
the fact rather than asserting that somebody edited a file. It matters here
specifically: `query/__init__.py` catches a refusal from this parser and
degrades to *no archived directories*, so two readers with different attribute
sets return **different archived sets from the same committed file**.

⚠ **`B` moved `0.75 → 0.15` in BOTH readers on 2026-09-16**
([SR-RANKING](0111_ranking.md) decision 3, W-144). `node/src/query/bm25f.mjs`
carries the constant and `tests/test_node_config_parity.py` holds the two equal,
so the change is one line on each side and a parity test that fails if only one
moves.

🔴 **This is the case the two-reader discipline exists for.** A ranking default
that moved in Python and not in Node would produce **two readers of one index
returning different orders** — the defect the parity pair in
[SR-WORK-BENCHMARK](0053_WORK-benchmark.md) decision 16 reports as a bug rather
than a finding, and the one a differential arm on an unchanged corpus could not
catch, because both readers would still agree with themselves.

### Consequences

- ⚠ **W-200 (2026-09-20) added the ingest provenance ledger**,
  `.fux/runtime/ingest-log.jsonl` — one runtime line per consumed document
  naming its decoder and, for a URL, its fetcher
  ([SR-INGEST](0106_ingest.md) decision 19). Nothing in `node/` reads or writes it — the Node plane reads an index and never builds one, so there is no twin to port and none is owed. **This record's decisions
  are unaffected**, and the line is here because the freshness gate asks a
  describer to say so rather than to be silent.

- **`routes()` returns `(routes, truncated)` on both readers, and the budget is
  the same number on both** (W-140 row 12, 2026-09-15). `EXPANSION_BUDGET` is a
  constant in each and must stay equal: the truncation point is a function of
  the index — `out_edges` is sorted on both sides — so two readers on one index
  cut at the same place, and a different budget would make them disagree about
  whether a search finished.
  ⚠ **Verified byte-equal on the `path --json` payload.** The one difference
  found is `"reliability": 1.0` against `1`, which is `json.dumps` against
  `JSON.stringify` and is this record's own known divergence, present in the
  confidence block too and **not W-140's**.

- **`fux lexical` is ONE FUNCTION on this reader, and that is stronger than the
  test that holds the Python pair equal** (2026-09-14, W-160). `fux.mjs`
  dispatches `ask` and `lexical` to the same `runAsk`, so the freeze holds by
  construction here — decision 10's agreement-by-construction device applied to
  a verb rather than to bytes. Python has two entry points over one body, held
  equal by `tests_e2e/test_relational.py::test_lexical_is_byte_identical_to_ask`.

  ⚠ **When [W-161 → W-204](../work/open/W-204-golden-outputs-scoring-and-version-benchmark.md) gives Python's
  `ask` a graph tier, this is the case that splits**, and the differential law
  will then compare a Python `ask` that has one against a Node `ask` that does
  not. **That divergence is W-161's to declare**, in this record, before it
  lands — not something for the harness to discover.

- **`graph --seed` and the three walk parameters are on both readers** (W-160),
  with `--seed` reporting `score: null` and `rank` in both. That last choice was
  forced by a divergence rather than chosen for taste: the first cut reported
  the walk's `1/(i+1)` mass, and seed 0's mass is exactly `1.0` — which
  `json.dumps` writes `1.0` and `JSON.stringify` writes `1`. **`pyRepr` exists
  in `compat/pyfloat.mjs` for precisely this and had no caller**, because a
  BM25F score is never an exact integer; the new output was the first value that
  could be one. `null` is `null` in both, and the number that was diverging was
  one no reader should have been comparing anyway.

- ⚠ **`link_idf` is the first `log1p` on the query path, and the two readers
  agree to `round(9)` rather than bit-for-bit.** Measured on this repository
  with `--link-idf` on: identical node ordering, four scores differing in the
  last digit or two. **That is decision 1's contract**, and BM25F's own `idf`
  has always depended on libm `log` in the same way — it simply happened to
  agree exactly on the corpora anyone compared. Recorded so that when W-161
  turns the parameter on, a last-digit difference is read as the contract
  working rather than as a port defect.

- **`fetch_at_answer = false` COLLAPSES decision 4's asymmetry, from Python's
  side** (2026-09-14, W-174). `[sources.url] fetch_at_answer = false` tells
  `fux answer` never to open a socket for `url:` documents; Python then does
  exactly what decision 3 says Node always does — read `.fux/acquired/` if the
  blob was retained, fall back to the index if not — so for such a repo the
  table's two divergent rows go away: no `current`/`stale` on a URL from either
  reader, and no `cached` from either.

  ⚠ **Node needs no change for this, and that is the point.** There is no
  transport in `node/` to switch off, so the flag is inert there and the two
  readers agree by construction. **The asymmetry is NOT retired** — it is the
  default behaviour with the flag on, which is what ships — and Node still
  cannot *offer* the verdicts Python offers by default. What is recorded here is
  that a consumer can now choose the symmetric half, and that choosing it costs
  them the strongest verdicts rather than buying them anything Node lacked.

- **W-163's eight `fux doctor` rows changed `doctor.py` and changed NOTHING this
  record describes** (2026-09-14). Stated here because the freshness gate was
  right to ask and the answer is worth writing down rather than waving through.

  `records/README.md` gives this record `src/fux/doctor.py::_node_reader,_installed_reader`
  — the `node reader` row and the PATH row's helper — and neither moved. What the
  gate saw is that the change **inserted 494 lines in one hunk**, which made
  `changed_symbols` return *"could not tell"*: a hunk that starts between two
  top-level blocks maps to no enclosing symbol. **The narrowing then correctly
  refuses to narrow** — *"a gate may only narrow on a fact, never on a guess"* —
  and demands every describer.

  ⚠ **That is the check working, not a false positive**, and the remedy is this
  paragraph rather than a looser rule: the alternative is a narrowing that
  guesses, and a gate that guesses narrow is a gate that stops firing.

- **The no-match sentence moved to stderr in BOTH readers, in one change**
  (2026-09-14, W-165 fix 2). `decline()` in `node/src/verbs/find.mjs` is the twin
  of `_decline()` in `src/fux/query/__init__.py`; `ask` and `answer` import it
  rather than each holding the literal, on both sides. Exit codes, wording and
  `--json` are unchanged. **`fux graph` still writes it to stdout in both** —
  named so the asymmetry is recorded rather than found.

  ⚠ **`tests/test_node_twins.py` did not catch a thing here, and the fix was to
  narrow it.** `node/src/query/run.mjs` declares `src/fux/query/__init__.py` as
  its twin, and so do the three verb modules — a one-to-many mapping the record
  already had. A change to what a verb *prints* moves the Python module without
  touching anything `runQuery` mirrors, so the check reported `run.mjs` as behind
  while the three files carrying the change sat updated beside it. `run.mjs` is
  now in `NARROWED` against `run_query`, which is what its own header has always
  said it mirrors: *"twin of the PURE half"*. **The three verb modules stay
  unnarrowed** — narrowing those too would leave the printing half unguarded,
  which is the failure this row exists to describe.
- **`fux` names two binaries when both are installed globally.** `--version`
  reports the runtime (`fux 2.0.0-alpha.7 (node 22.9.0)`), an unsupported verb
  signposts the other, and `fux doctor` reports a node `fux` earlier on PATH.
  ⚠ **Amended 2026-09-12 (Arpit): the global bin SHIPS.** This clause read
  *"No global bin ships in the first npm release"* and `fux-engine`
  **2.0.0-alpha.7 was published to npm on 2026-09-12 carrying
  `bin: {"fux": "./fux.mjs"}`** — so the rule was already false when it was
  read. Arpit ruled the bin stays rather than burning a version to remove it.
  ⚠ **`2.0.0` (2026-09-13) carries the same bin**, unchanged — the alpha line
  promoted, not re-decided.
  ✅ **All three mitigations now ship.** The clause was holding up the
  `fux doctor` PATH row, deferred *because* nothing was going to shadow
  Python's `fux`; that premise died with the clause and the row **landed the
  same day** — `doctor._fux_on_path`, a `warn` that names the resolved path and
  points at `fux --version`. It **reads the launcher and never executes it**:
  doctor does not run a binary the environment chose for it. Registered in
  [SR-DOCTOR](0152_doctor.md) §2.

  ⚠ **Amended 2026-09-14 (W-159): "reads the shim's SHEBANG" was the Unix
  half of the rule, stated as the whole of it.** npm writes no shebang on
  Windows — it writes a `fux.cmd` whose body names `node` — so the sentence
  described a mechanism that is absent on the platform where two globally
  installed `fux` binaries are most likely. `_is_node_shim` reads both shapes.

  **The row covers Windows, macOS and Linux.** W-159 was filed believing it
  could not fire on Windows, on the evidence of a test skipped there. **That
  reading was wrong, and the correction is the finding**: `shutil.which` honours
  PATHEXT, which is exactly how it resolves the `fux.cmd` npm installs. What
  could not be built on Windows was the *test's* extensionless shim — a fixture
  defect read back as a claim about the code it could not reach. The fixture is
  platform-shaped now and the skip is gone.

  🔴 **And the platform sweep found a real false positive.** The classifier
  read whatever `which` returned as text with `errors="replace"` and asked
  whether `node` appeared in the first 512 bytes. **A Windows console script is
  a `.exe`** — a small binary launcher — and three letters occurring by chance in
  its bytes would have told someone their working Python `fux` was the Node
  reader and only reads. A compiled binary is not a shim and is no longer read;
  `tests/test_doctor.py::test_a_compiled_launcher_is_never_read_as_text` pins it.

  ⚠ **`_is_node_shim` is split out so it can be tested on EVERY platform.**
  Neither end-to-end shape is reachable on both — `which('fux')` finds
  `fux.cmd` only on Windows and an extensionless `fux` only on Unix — so the
  row's own test exercises one shape per platform forever, and the half that was
  actually wrong would have stayed half-covered.
- ✅ **The 47-file vendored tree is GONE as of 2026-09-12 — decisions 13-16
  replaced it and W-149 built them.** The paragraph below is kept as the
  measurement that produced the ruling rather than rewritten; **it describes
  what shipped until that day and is not a description of the current state.**
  What a consumer's tree holds now is **four files, 244 KB** in shape A
  (`fux.mjs` · `package.json` · `mcp-tools.json` · `README.md`) or **one** in
  shape C, and `fux setup` **prunes** whatever an older engine left behind.
- - **The vendored reader is 47 files / 336 KB** as of 2026-09-12, against the
  37 files / 196 KB W-107 measured before the config readers and the graph
  walk landed. ⚠ **Still ~3 % of this repo's 9.6 MB index and still smaller
  than `.fux/decoders/`**, so R2's argument survives its own numbers — but a
  consumer's `git status` now shows 47 new files after `fux setup`, and every
  version bump re-diffs them. `_packaged_node_files` walks the directory, so
  nothing had to be updated for the new modules to ship; **that is also why
  nobody would have noticed the growth.**
- **A second implementation is a second thing to keep true.** The arm runs on
  every push, across three OSes and two Node versions, because the whole reason
  this record exists is that two libms disagree.
- ✅ **The sixth surface is BUILT: the BUNDLE.** `node_arm.py --bundle-cap`
  builds the published artefact and compares it against the module tree it came
  from — `find`, `ask`, `answer`, the MCP server over a real stdio session, and
  the library export, on whole parsed payloads. **0 discordant on this repo's
  own index.** It closes decisions 9-12's own lesson applied to itself: *a
  transcription is only as true as the surface the instrument is aimed at*, and
  shipping one artefact while measuring another was that failure in a new
  costume. ⚠ **Determinism is the weaker claim and is not the one that matters
  here**: a bundler can emit bytes that are reproducible, compile, run, and
  answer differently. The arm and `tests/test_node_bundle.py` both compare
  ANSWERS.
- **The arm covers six surfaces since 2026-09-12, and it covered one before.**
  `find` and `ask` · `explain`/`graph`/`path` as whole parsed payloads ·
  the MCP server over a real stdio session · `fux.api` against
  `node/src/index.mjs` · **the published bundle against the module tree**.
  Every one of the three defects in decisions 9-12 lived
  on a surface the arm did not reach, and each was found on the first run after
  it did. ⚠ **`verify`, `--why`, `--receipt` and `--journal` are still
  uncovered**, because they have no Node twin at all (W-107 R6) — that is a
  stated absence, not a gap the arm should pretend to close.
- ⚠ **The arm cannot be called green yet.** PRE-REGISTRATION-NODE §4 names
  `fux-playground`, which [SR-WORK-ENVIRONMENTS](0052_WORK-environments.md) voided as an
  instrument. A frozen pre-registration is superseded, never edited; the build
  is unaffected and no measured arm may be reported until the superseding
  document exists on lab golden data.

### Alternatives

- **One portable `log` in both runtimes** (byte-identity, one Python change) —
  declined by Arpit 2026-09-06. It bought bit-identity at the price of a
  corpus-wide ranking change, to fix a difference seven orders of magnitude
  below the sort key.
- **Truncating `blake2b512`** — wrong, not merely slower: the parameter block
  folds the digest length into `h[0]`, so `blake2b(x, 8)` and
  `blake2b(x, 64)[:8]` disagree on every input.
- **A WASM build of the Python scorer** — one implementation and no
  transcription, at the price of a build step, a toolchain and a binary in the
  repo. A build step is a dependency (L1), and the differential law is what
  makes two implementations safe.

## References

- [`2026-09-12-node-tune-and-surfaces`](../work/regression/2026-09-12-node-tune-and-surfaces/report.md)
  — decisions 8-12, measured · [`2026-09-12-node-arm-rungs`](../work/regression/2026-09-12-node-arm-rungs/report.md)
  — the ladder run that found decision 8
- [PRE-REGISTRATION-NODE-2](../work/benchmark/PRE-REGISTRATION-NODE-2.md) (frozen,
  sha `2ea40303…`) · [PRE-REGISTRATION-NODE](../work/benchmark/PRE-REGISTRATION-NODE.md)
  (frozen, superseded)
- [`2026-09-12-workspace-dotpath-probe`](../work/regression/2026-09-12-workspace-dotpath-probe/report.md)
  — decisions 15 and 16, measured across npm / pnpm / yarn 1 / bun. **A surface
  capture**, so no classification and no per-query rows; Yarn Berry is named as
  unmeasured in its §4
- [`src/fux/store/nodebundle.py`](../src/fux/store/nodebundle.py) — the
  bundler · [`hatch_build.py`](../hatch_build.py) — the wheel's build hook ·
  [`tests/test_node_bundle.py`](../tests/test_node_bundle.py) — equal
  ANSWERS, not equal bytes · [`tests/test_setup_workspace.py`](../tests/test_setup_workspace.py)
  — the detection table and the manifest diff
- [`2026-09-12-yarn-berry-probe`](../work/regression/2026-09-12-yarn-berry-probe/report.md)
  — decision 15's second probe: Berry links `.fux/node`, and `nodeLinker`
  decides the shape. **A surface capture**, so no classification and no
  per-query rows
- **W-149 is CLOSED** (2026-09-12) — decisions 13-16's build item. Its outcome
  is in [`work/IMPLEMENTATION.md`](../work/IMPLEMENTATION.md); the item file
  is deleted, per OPEN-WORK rule 2, and is **named, never cited** ·
  W-148 (closed 2026-09-15) — what W-107
  could not close. ⚠ **W-107 itself is retired and is NAMED, never cited**
  (`CLAUDE.md` §"Archive is not evidence")
- npm workspaces <https://docs.npmjs.com/cli/using-npm/workspaces> · pnpm
  workspaces <https://pnpm.io/workspaces> · Yarn workspaces
  <https://yarnpkg.com/features/workspaces> · Bun workspaces
  <https://bun.com/docs/install/workspaces>
- [SR-RANKING](0111_ranking.md) decision 8a · [SR-DOTFUX](0102_fux-directory.md) · [SR-MCP](0136_mcp.md) · [SR-URL-FRESHNESS](0147_url-freshness.md)
- RFC 7693 (BLAKE2) <https://www.rfc-editor.org/rfc/rfc7693>
- UAX #29, text segmentation <http://www.unicode.org/reports/tr29/>
- Cormack, Clarke & Buettcher, *Reciprocal rank fusion*, SIGIR 2009
