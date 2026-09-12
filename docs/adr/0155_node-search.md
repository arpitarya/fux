---
type: ADR
name: ADR-NODE-SEARCH
title: "ADR-NODE-SEARCH (0155) — the Node read plane: one index, two readers, three arms"
description: "Why a Node reader exists, what it may and may not do, and the four decisions that keep it from becoming a second product: the _format version policy, the never-fetch rule, the url: verdict asymmetry, and the shared tool-description file."
status: accepted
date: 2026-09-12
feature: "`node/` — the zero-dependency Node.js read plane, published as `fux-engine`, vendored into `.fux/node/` by `fux setup`, and held byte-equal to Python by the third arm of the differential law"
owns: [node]
laws: [L1, L3, L4, L6]
ratifies: "Arpit, 2026-09-12 — R1-R6 in work/open/W-107-node-read-plane.md"
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

[W-107](../../work/open/W-107-node-read-plane.md) carries the plan and the
measurements; this record carries the four decisions that outlive it.

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
- **A second implementation is a second thing to keep true.** The arm runs on
  every push, across three OSes and two Node versions, because the whole reason
  this record exists is that two libms disagree.
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

- [W-107](../../work/open/W-107-node-read-plane.md) · [PRE-REGISTRATION-NODE](../../work/benchmark/PRE-REGISTRATION-NODE.md)
- [ADR-RANKING](0111_ranking.md) decision 8a · [ADR-DOTFUX](0102_fux-directory.md) · [ADR-MCP](0136_mcp.md) · [ADR-URL-FRESHNESS](0149_url-freshness.md)
- RFC 7693 (BLAKE2) <https://www.rfc-editor.org/rfc/rfc7693>
- UAX #29, text segmentation <http://www.unicode.org/reports/tr29/>
- Cormack, Clarke & Buettcher, *Reciprocal rank fusion*, SIGIR 2009
