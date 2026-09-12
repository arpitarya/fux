---
type: ADR
name: ADR-NODE-SEARCH
title: "ADR-NODE-SEARCH (0155) — the Node read plane: one index, two readers, three arms"
description: "Why a Node reader exists, what it may and may not do, and the decisions that keep it from becoming a second product: the _format version policy, the never-fetch rule, the url: verdict asymmetry, the shared tool-description file, and the three places where Node is deliberately a SUBSET of Python rather than a copy — the derived graph plane, the accelerator label, and the decoder boundary."
status: accepted
date: 2026-09-12
feature: "`node/` — the zero-dependency Node.js read plane, published as `fux-engine`, vendored into `.fux/node/` by `fux setup`, and held byte-equal to Python by the third arm of the differential law"
owns: [node]
laws: [L1, L3, L4, L6]
ratifies: "Arpit, 2026-09-12 — R1-R6 in W-107, which closed the same day (archive/open/W-107-node-read-plane.md)"
timestamp: 2026-09-12T00:00:00Z
---

# ADR-NODE-SEARCH — the Node read plane

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
[PRE-REGISTRATION-NODE](../../work/benchmark/PRE-REGISTRATION-NODE.md) says
otherwise.**

## §2 — For agents

### Context

W-107 carried the plan; **it closed on 2026-09-12** and this record carries the
decisions that outlive it. What grounds them is
[`2026-09-12-node-tune-and-surfaces`](../../work/regression/2026-09-12-node-tune-and-surfaces/report.md)
and [`2026-09-12-node-arm-rungs`](../../work/regression/2026-09-12-node-arm-rungs/report.md),
never the retired item — its file is named in
[`archive/README.md`](../../archive/README.md) and may not back a live claim.
What it could **not** close is
[W-148](../../work/open/W-148-what-the-two-readers-still-owe.md).

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
A link to [ADR-RANKING decision 8a](0111_ranking.md), never a second statement
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
[ADR-URL-FRESHNESS](0149_url-freshness.md) exists to prevent.

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
([`2026-09-12-node-tune-and-surfaces`](../../work/regression/2026-09-12-node-tune-and-surfaces/report.md)):

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
be.** [ADR-TUNE](0135_tuning.md) decision 11 calls it the *"is it me or the
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
is arbitrary Python in `.fux/decoders/` ([ADR-DECODE](0139_decode.md)'s whole
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
is never repeated in `include` ([ADR-TYPES](0128_types-list.md) decision 12), so
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
`next` — so the one key [ADR-CONFIDENCE](0142_confidence.md) exists for was
absent from the surface it exists to serve.

Nothing could have caught this except comparing the two servers: each was
internally consistent, and the shared descriptions file held only the
descriptions, not the handlers. `node_arm.py::compare_mcp` now drives both over
one stdio session per run.

### Consequences

- **`fux` names two binaries when both are installed globally.** `--version`
  reports the runtime (`fux 2.0.0-alpha.7 (node 22.9.0)`), an unsupported verb
  signposts the other, and `fux doctor` reports a node `fux` earlier on PATH.
  ⚠ **Amended 2026-09-12 (Arpit): the global bin SHIPS.** This clause read
  *"No global bin ships in the first npm release"* and `fux-engine`
  **2.0.0-alpha.7 was published to npm on 2026-09-12 carrying
  `bin: {"fux": "./fux.mjs"}`** — so the rule was already false when it was
  read. Arpit ruled the bin stays rather than burning a version to remove it.
  ✅ **All three mitigations now ship.** The clause was holding up the
  `fux doctor` PATH row, deferred *because* nothing was going to shadow
  Python's `fux`; that premise died with the clause and the row **landed the
  same day** — `doctor._fux_on_path`, a `warn` that names the resolved path and
  points at `fux --version`. It **reads the shim's shebang and never executes
  it**: doctor does not run a binary the environment chose for it. Registered
  in [ADR-DOCTOR](0154_doctor.md) §2.
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
- **The arm covers five surfaces since 2026-09-12, and it covered one before.**
  `find` and `ask` · `explain`/`graph`/`path` as whole parsed payloads ·
  the MCP server over a real stdio session · `fux.api` against
  `node/src/index.mjs`. Every one of the three defects in decisions 9-12 lived
  on a surface the arm did not reach, and each was found on the first run after
  it did. ⚠ **`verify`, `--why`, `--receipt` and `--journal` are still
  uncovered**, because they have no Node twin at all (W-107 R6) — that is a
  stated absence, not a gap the arm should pretend to close.
- ⚠ **The arm cannot be called green yet.** PRE-REGISTRATION-NODE §4 names
  `fux-playground`, which [L9](0011_LAW-9-environments.md) voided as an
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

- [`2026-09-12-node-tune-and-surfaces`](../../work/regression/2026-09-12-node-tune-and-surfaces/report.md)
  — decisions 8-12, measured · [`2026-09-12-node-arm-rungs`](../../work/regression/2026-09-12-node-arm-rungs/report.md)
  — the ladder run that found decision 8
- [PRE-REGISTRATION-NODE-2](../../work/benchmark/PRE-REGISTRATION-NODE-2.md) (frozen,
  sha `2ea40303…`) · [PRE-REGISTRATION-NODE](../../work/benchmark/PRE-REGISTRATION-NODE.md)
  (frozen, superseded)
- [W-148](../../work/open/W-148-what-the-two-readers-still-owe.md) — what W-107
  could not close. ⚠ **W-107 itself is retired and is NAMED, never cited**
  (`CLAUDE.md` §"Archive is not evidence")
- [ADR-RANKING](0111_ranking.md) decision 8a · [ADR-DOTFUX](0102_fux-directory.md) · [ADR-MCP](0136_mcp.md) · [ADR-URL-FRESHNESS](0149_url-freshness.md)
- RFC 7693 (BLAKE2) <https://www.rfc-editor.org/rfc/rfc7693>
- UAX #29, text segmentation <http://www.unicode.org/reports/tr29/>
- Cormack, Clarke & Buettcher, *Reciprocal rank fusion*, SIGIR 2009
