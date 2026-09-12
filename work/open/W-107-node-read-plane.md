---
type: OpenItem
id: W-107
title: "W-107 — the Node read plane: ask / find / answer / explain / graph / path / mcp from Node.js, zero dependencies, byte-equal to Python"
description: "A read-only port of the seven query verbs to Node so a host with no Python reads an index Python wrote. Published to npm as fux-engine, invoked as `fux`, and vendored into .fux/fux.mjs by `fux setup` so a fresh clone needs nothing installed. Behind it, one shared API surface — `fux.api` in Python, the same methods in Node — so both readers and the CLI call one implementation. Four phases behind a pre-registered third arm of the differential law. Phase 0 CLOSED 2026-09-06; naming, placement and the API seam RULED 2026-09-12."
status: open
lane: agent
timestamp: 2026-09-04T00:00:00Z
---

# W-107 — the Node read plane

**Model: Opus.** Phase 0 is a determinism decision and touches ranking
arithmetic; Phases 1–3 are transcription where a wrong last bit is invisible
until the differential arm fires. Sonnet may run the mechanical suites once
the pre-registration exists; Opus owns every gate.

## The spec this implements

[`../proposals/search-v3.md`](../proposals/search-v3.md) §6 (design), §8
(plan), §9.6 (mechanics). Nothing below restates a bar.

⚠ **search-v3 §6.4 says `fux-search` and one ESM file. Both are superseded by
§Rulings below** — the proposal is `graduated` and is not rewritten; this file
is the live spec where they disagree.

## Goal

`fux ask|find|answer|explain|graph|path|mcp` on a repo whose index Python
committed, with **no Python on the host**, producing what Python produces: same
ids, order, locs, headings, band; scores equal after `round(9)`; `graph.json`
digest equal.

---

## Rulings — 2026-09-12 (Arpit)

### R1 · Names

| thing | name | why not the alternative |
|---|---|---|
| npm package | **`fux-engine`** | `fux` is taken on npm (a 2016 UI library — search-v3 §6.4 found this), so `npx fux` fetches someone else's package. `fux-engine` is free **and is already the PyPI name**, so the product has one name in both registries instead of two. |
| the command | **`fux`** | `bin: { "fux": "./fux.mjs" }`. The package name and the command name are different things; the command is what a person types. |
| the vendored file | **`.fux/fux.mjs`** | written by `fux setup`, see R2 |
| the source tree | **`node/`** | in this repo, so the goldens, the harness and CI see it |

**Invocations, all four supported:**

```console
$ node .fux/fux.mjs find rollback     # a fresh clone, nothing installed
$ .fux/fux find rollback              # the shim setup writes beside it
$ npx fux-engine find rollback        # one bin, so npx resolves it
$ fux find rollback                   # after `npm i -g fux-engine`
```

`npx -p fux-engine fux find …` is the explicit form for a script that wants no
ambiguity.

### R1a · The PATH collision, and the three things that make it safe

`npm i -g fux-engine` puts a `fux` on PATH **beside Python's `fux`, with a
different verb set.** Whichever resolves first wins, so `fux ingest` can answer
*"this only reads"* on a machine where Python fux is installed and would have
worked. Not hypothetical; it is what two binaries of the same name means.

1. **`--version` names the runtime.** `fux 2.0.0-alpha.7 (node 22.9.0)` versus
   `fux 2.0.0-alpha.7 (python 3.13.1)`. One word, and no bug report is ever
   ambiguous again. **This is the highest-value line in the whole item.**
2. **An unsupported verb signposts rather than erroring.**
   `error: `ingest` writes the index — this is fux-engine (node), which only
   reads. Install Python fux and run `fux ingest`, or see .fux/README.md.`
   A person typing that has a specific wrong model and deserves the specific
   correction, not `unknown command`.
3. **`fux doctor` (Python) gains a row** when a node `fux` resolves first on
   PATH — reported by the half that can report it.

⚠ **Inside a repo there is no collision at all**, because the call is
`node .fux/fux.mjs`. The shadowing exists only for the opt-in global install.

🔴 **AMENDED 2026-09-12 (Arpit) — the bin ships.** This paragraph read *"No
global bin ships in the first npm release; the library export and the vendored
copy cover both real use cases, and the bin is added once someone asks for
it."* **`fux-engine` 2.0.0-alpha.7 went to npm on 2026-09-12 carrying
`bin: {"fux": "./fux.mjs"}`** — published at Arpit's direction to hold the name,
with the bin unnoticed until after the fact. Offered unpublish (inside the 72h
window), a bin-less alpha.8, or keeping it: **he ruled keep it.**

✅ **Item 3 landed the same day.** It had only ever been deferred because of
the sentence that just went away. `doctor._fux_on_path` is a `warn` row that
names the resolved path and points at `fux --version`; it **reads the shim's
shebang and never executes it** — doctor does not run a binary the environment
chose for it. Registered in [ADR-DOCTOR](../../docs/adr/0154_doctor.md) §2,
five tests in `tests/test_doctor.py` including a fake npm shim ahead of Python
on PATH. **All three R1a mitigations now ship.**

### R2 · `.fux/fux.mjs` — committed, engine-owned, OVERWRITTEN

`fux setup` writes the reader into the consumer's `.fux/`, and **`ensure_layout`
rewrites it whenever the engine version differs.** It is **not**
write-if-missing.

**Why committed and not gitignored.** The audience is a host with no Python. A
gitignored copy can only be regenerated by the Python that is, by construction,
not there — so gitignoring it withholds the file from exactly the person it is
for. Committing extends the README's existing *clone and ask* promise from the
index to the reader.

**The size objection does not survive measurement** (this repo, 2026-09-12):

| | |
|---|---|
| `.fux/index/` | **9.6 MB**, 253 shards |
| `.fux/decoders/` — already committed, already vendored engine code | **280 KB** |
| `.fux/fux.mjs` — projected | **~200 KB** |

**2 % of the index, and smaller than the vendored Python already sitting beside
it.**

🔴 **Why NOT write-if-missing, in one piece of evidence from this tree.**
`.fux/decoders/` is write-if-missing, and the `doc`-suffix rename
(`csvdoc` → `csv`, 2026-09-06) shipped **with no migration**: a repo set up
before it still holds stale `<name>doc.py` files that claim the same extensions
and **win**. `tests/test_orphaned_modules.py` catches the shipped half and
nothing reaches a consumer's directory. Same mechanism here, worse outcome — a
stale `fux.mjs` against a bumped `_format` is a **wrong answer**, not an old
preference, and nobody edits a vendored reader, so there is no consumer edit to
protect.

**The payoff is structural:** the copy in `.fux/` is always written by the
Python that wrote the index, so **a `_format` mismatch cannot happen.** That is
stronger than npm, where the consumer picks versions independently.

**This is a fourth shape under [ADR-DOTFUX](../../docs/adr/0102_fux-directory.md),
and that record is amended in the same change:**

| shape | examples | rule |
|---|---|---|
| committed, **consumer-owned** | `fetchers/` `decoders/` `*.toml` | write-if-missing — a consumer's edit survives |
| committed, **engine-owned, annotatable** | `README.md` `.gitignore` | write-if-missing — a consumer annotates them |
| committed, **engine-owned, vendored** | **`fux.mjs`**, **`fux`** | **overwritten on a version difference** ← new |
| derived / acquired | `runtime/` `acquired/` | gitignored |

`fux doctor` reports the drift it can still see:
*`.fux/fux.mjs` is 2.0.0-alpha.4; the engine is alpha.7 — run `fux setup`.*

### R3 · One API, three surfaces — and it ships FIRST

**Arpit, 2026-09-12: Python must be able to import these functions too, the
same way the npm package can.**

Today `cmd_ask(args)` takes an argparse `Namespace`, prints to stdout and
returns an exit code. It cannot be called from Python without faking a
Namespace and capturing stdout — which is why
[`.fux/README.md`](../../.fux/README.md) has to say *"the CLI is the contract;
the modules are not."*

```python
from fux import open as fux_open

ix = fux_open(".")                        # find_root, gate, tune, output — once
ix.find("rollback", top=5)                # -> list[Result]
ix.ask("how do we roll back a release")   # -> AskResult(results, confidence)
ix.answer("what is the RTO")              # -> Answer(passages, citation, freshness)
ix.explain("file:docs/x.md"); ix.graph(q); ix.path(a, b)
```

```js
import { open } from 'fux-engine'
const ix = await open('.')
await ix.find('rollback', { top: 5 })
```

**Same method names, same argument names, same return shape as the `--json`
payload.** Three consequences, and the third is why this goes first:

1. **[`output.schema.json`](../../src/fux/query/output.schema.json) becomes the
   contract for three surfaces** — CLI JSON, Python objects, Node objects — not
   one. One schema file, already written, already validated at the boundary.
2. **The differential arm can compare library calls, not subprocess stdout.**
   That removes the `ensure_ascii` and float-repr noise in H2 from the arm
   entirely: those are *printing* defects, and the arm stops testing printing.
3. 🔴 **It makes the port transcribable.** Right now
   [`query/__init__.py`](../../src/fux/query/__init__.py) is **1 481 lines**
   with computing and printing interleaved. After the seam, `cmd_ask` is
   `print(render(api.ask(...)))` and the Node target is the pure half.
   **Porting the current shape means refactoring twice.**

⚠ **The cost, stated: a public Python API is a new frozen surface.** Once
`from fux import open` is documented it cannot churn — it needs its own record
(**ADR-API**, new) and it joins what L0 keeps true. This is a commitment, not a
free win.

**Sequencing:** the seam lands as **Phase 1a, before any `node/` file is
written.**

### R4 · `node/` is many files, not one

search-v3 §6.4 says *one ESM file*. **Superseded**, because Phase 4 requires a
freshness test mapping *each Python module to its Node twin* — which needs more
than one file — and because a 6 000-line `.mjs` is unreviewable.

**The rule that makes Phase 4 cheap: same relative path, same stem, one Node
file per Python module.** Then the twin map is derived, not hand-maintained.

```
node/
  package.json              no `dependencies` key at all — absent, not empty
  README.md
  fux.mjs                   #!/usr/bin/env node — argv + dispatch, nothing else
  src/
    index.mjs               the library export: `open()`
    api.mjs                 ← src/fux/api.py            (R3's twin)
    config/root.mjs         ← src/fux/config.py         (find_root only)
    config/toml.mjs         ← (no twin) the TOML subset
    hash/blake2b.mjs        ← (no twin) RFC 7693, 32-bit halves
    store/format.mjs        ← src/fux/store/format.py
    store/reader.mjs        ← src/fux/store/reader.py
    query/tokenize.mjs      ← src/fux/query/tokenize.py
    query/stem.mjs          ← src/fux/query/stem.py
    query/analyzer.mjs      ← src/fux/query/analyzer.py
    query/bm25f.mjs         ← src/fux/query/bm25f.py
    query/rank.mjs          ← src/fux/query/rank.py
    query/scan.mjs          ← src/fux/query/scan.py
    query/confidence.mjs    ← src/fux/query/confidence.py
    query/{headings,expand,fuse,rerank,provenance}.mjs
    refer/{chunk,rescore,assemble}.mjs   ← src/fux/refer/_*.py
    graph/{community,model,plane,walk}.mjs
    ingest/priors.mjs       ← src/fux/ingest/priors.py  (recency + priority only)
    compat/pyfloat.mjs      ← (no twin) repr layout + round-half-even
    compat/pyjson.mjs       ← (no twin) ensure_ascii dumps, for the receipt digest
    verbs/{find,ask,answer,explain,graph,path,mcp}.mjs
  test/vectors/             RFC 7693 App. A · Porter voc.txt / output.txt
```

**`compat/` and `hash/` have no Python twin and are declared exempt in the
ownership table.** That list is short, visible, and is exactly where the
divergence risk concentrates — which is the point of naming it rather than
letting it be an unexplained gap.

**One deliberate deviation:** `query/__init__.py` splits into `verbs/*.mjs`,
because it is seven verbs plus plumbing and the twin map records that
one-to-many edge explicitly.

**`package.json`:**

```json
{
  "name": "fux-engine",
  "type": "module",
  "engines": { "node": ">=20" },
  "bin": { "fux": "./fux.mjs" },
  "exports": { ".": "./src/index.mjs" },
  "files": ["fux.mjs", "src", "README.md"]
}
```

No `dependencies` key **at all** — absent rather than `{}`, so it cannot grow
one by accident. No `scripts.build`: a build step is a dependency.

### R5 · The read path, fixed

```
findRoot(cwd)                   walk up for fux.toml or .git       ← same as Python
.fux/pii.toml                   stat only — the gate, see O1
.fux/output.toml                folded into args once, same precedence
.fux/tune.toml                  absent = defaults; malformed = hard error
.fux/sources/dirs               the archived set
.fux/index/{00..ff}.jsonl       line 0 = header → REFUSE unless
                                  _format "fux.index.v2" and analyzer "v2"
                                lines 1..n = Buffer.indexOf('"<16hex>"'),
                                  JSON.parse ONLY on a hit
rank() → emit
```

Three things in there are load-bearing:

- 🔴 **Read each shard as a `Buffer`, never as a string.** Python's scan
  regex-matches `flen`/`mtime` and substring-matches the term hash against
  **raw bytes**, parsing a line only on a hit.
  `readFileSync().toString().split("\n")` allocates ~10 MB of UTF-16 per query
  at 10 000 documents and is how **N4's 150 ms fence gets blown by a
  transcription that is otherwise correct.**
- **The header is a refusal, not a hint.** A v1 shard silently mixed into a v2
  read corrupts every `df` and is undetectable at query time. Refuse, naming
  both versions.
- **Nothing under `.fux/runtime/` is read.** The graph plane is rebuilt in
  memory and must hash to Python's `graph.json`; the accelerator is out of
  scope entirely.

### R6 · The command surface, and what is absent

```
fux find   <query>  [--json] [--top N] [--under DIR] [--phrase P] [--all]
fux ask    <query>  [--json] [--top N] [--band] [--explain] [--expand TERMS] [-q Q]...
fux answer <query>  [--json] [--band] [--no-refer] [--audit] [--receipt]
fux explain <doc-id>
fux graph  <query>  [--hops N]
fux path   <a> <b>  [--hops N]
fux mcp
fux --version
```

| absent | why |
|---|---|
| `ingest` `build` `add` `remove` `update` `enrich` `setup` | they write, or need a decoder, or need a fetcher |
| `doctor` | it reports on a tree Node cannot fully see |
| `--fast` / `--scan` | no Node accelerator; the scan is the only path, so a flag selecting it is a lie |
| `--journal` | it writes |
| `--cache-ttl` | Node never fetches, so there is nothing to cache |
| `verify` | reproducing a receipt needs the digest path — Phase 2 earns it |

**`answer` on a `url:` document** reads `.fux/acquired/` if the blob is there
(→ `as-ingested`), else falls back to `source: "index"`. It never emits
`current` or `stale`, because it never looked. **That asymmetry with Python is
a decision in ADR-NODE-SEARCH, not a footnote.**

---

## Hazards found 2026-09-12 — each unmeasured before this reading

### H1 🔴 The `id` tie-break is a string comparison, and the two runtimes disagree

The sort key ends in `id`. **Python compares strings by Unicode code point; JS
`<` compares by UTF-16 code unit.** These differ above U+FFFF — a surrogate
pair sorts *below* U+E000–U+FFFF in JS and *above* in Python. One document id
carrying an emoji or a rare CJK extension character and **the ordering
assertion — the one [PRE-REG-NODE](../benchmark/PRE-REGISTRATION-NODE.md) §2
calls non-negotiable — silently fails.**

**Phase 0 measured `log`. Nobody measured the tie-break.**

- **Fix:** a code-point comparator in Node (iterate code points, not units).
- **Pin:** the differential corpus gains a document whose id contains a
  character above U+FFFF, deliberately, so the arm would catch a regression.

### H2 🟠 `--json` is emitted with `ensure_ascii=True`

[`query/__init__.py`](../../src/fux/query/__init__.py) prints
`json.dumps(payload, indent=2)` — Python's default escapes every non-ASCII
character as `\uXXXX`; `JSON.stringify` emits it raw.

**So "byte-equal" in PRE-REG-NODE §2 is only meaningful on *parsed field
values*, never on raw stdout** — and this repo's own corpus is full of
em-dashes, so a byte diff fails on query one. **The frozen pre-registration is
ambiguous on this point and cannot be edited**; the superseding one (O3) states
it, and the harness compares parsed values.

⚠ **One place it is genuinely byte-level and does not go away:**
`provenance.py:534` computes the **receipt digest** over
`json.dumps(payload, sort_keys=True, separators=(",", ":"))` — also
`ensure_ascii=True`. Node must reproduce Python's escaping exactly or every
receipt sha diverges. Hence `compat/pyjson.mjs`.

**Not a hazard, checked:** the committed index is written with
`ensure_ascii=False` ([`store/canonical.py`](../../src/fux/store/canonical.py)),
so the shards are raw UTF-8 and read identically in both runtimes.

### H3 🔴 The frozen pre-registration is voided in part by L9

[PRE-REG-NODE](../benchmark/PRE-REGISTRATION-NODE.md) §4 names
`fux-playground` as a corpus and **N3** says *"every distinct term of the
playground index"*. [L9](../../docs/adr/0011_LAW-9-environments.md) makes the
playground **Arpit's hands only — no agent, no test, no number.**

**A frozen pre-registration is never edited.** It is superseded (O3). The
**build** (Phases 1a–4) is unaffected and starts now; **no arm may be called
green** until the superseding document exists on lab golden data, which waits
on W-136 phase 2. Tracked in [W-138](../../archive/open/W-138-reconcile-with-l9.md).

### H4 — carried from the original filing

- 🔴 **A port that "improves" anything has diverged.** Every difference is a
  defect until the pre-registration says otherwise.
- `math.log`: settled by Phase 0 — 655/100 000 on darwin, 722/100 000 on
  glibc, every one a single ulp, **none surviving `round(9)`**.
- Truncated `blake2b512` is **not** BLAKE2b-8 — the parameter block puts the
  digest length in the IV. Hand-roll RFC 7693 and test it.
- `Number(x.toFixed(9))` is half-up on exact binary ties; Python is half-even.
  Detect ties via `toFixed(20)`.
- A `_format` bump in Python without a Node release breaks every Node clone —
  **R2's overwrite-on-version-difference is the guard**, and the npm copy still
  needs the version policy.
- `node/` must have **no** `package.json` dependencies; a build step is a
  dependency.

---

## Build order

**Harness before code.** This is a ~5 000-line transcription where a wrong last
bit is invisible until something fires, so the first commit is the thing that
catches lies, and it passes trivially (Python vs Python) before any `node/`
file exists.

## Phase 0 — the `log()` decision (Arpit)

- [x] **DONE 2026-09-05.** Measure Python-vs-Node BM25F score divergence *as
      is* on the playground and the 10 000-document corpus; file the discordant
      top-5 count. →
      [`2026-09-05-node-log-divergence`](../regression/2026-09-05-node-log-divergence/report.md),
      `blind`, per-query rows for all 290 queries.
      **`Math.log` and `math.log` DO differ** — 655 / 100 000 wide doubles on
      darwin/arm64, the same order as the glibc figure in Hazards below — but
      **every difference is one ulp** (max rel `2.211e-16`) and **not one
      survives `round(9)`**, which is `rank.py`'s own sort-key resolution.
      Over the corpora: **0 discordant scores and 0 discordant top-5 on
      197 233 scored documents**, checked on both the real sort key and an
      exact one. Python's scan **p95 = 50.2 ms at 10 000 documents**.
      ⚠ **Two limits bound every sentence of that**: the `idf` argument
      population in those corpora is **13 distinct values** (a property of a
      10-document corpus and a synthetic 10 000-document one, not of fux), and
      **glibc — what CI runs — was not measured**, because this machine has no
      Linux.
- [x] ✅ **BOTH LIMITS CLOSED 2026-09-06.**
      [`ADDENDUM-IDF`](../regression/2026-09-05-node-log-divergence/ADDENDUM-IDF.md)
      widened the `idf` population on this repo's own 838-document index
      (13 → 182 distinct, **7.69 % diverge**, 8.98 % of real BM25F scores
      differ bit-for-bit, **0 at `round(9)`**), and
      [`ADDENDUM-GLIBC`](../regression/2026-09-05-node-log-divergence/ADDENDUM-GLIBC.md)
      measured **glibc 2.39 / x86-64 / Node 22** — 722/100 000 wide,
      4.44 % of scores bit-different, **0 at `round(9)`, 0 top-5 moves** — and
      went further than the clause asked: the `idf` argument domain is
      **enumerated, not sampled**. `idf`'s argument is
      `(n - df + 0.5)/(df + 0.5) + 1` with `df ∈ 1..n`, so at a given corpus
      size it is finite; **all 10 939 arguments at `n ∈ {101, 838, 10 000}`**
      were checked, **841 (7.69 %) differ, 0 differ at `round(9)`**.
      ⚠ **Still unmeasured: musl, Windows, Node 20**, and
      [`log-probe.yml`](../../.github/workflows/log-probe.yml) **has still not
      been run** — the glibc figure came from a Linux container, not from CI.
- [x] **WRITTEN 2026-09-05, deliberately NOT FROZEN, and FROZEN IN FULL
      2026-09-06** (sha `0e3b4c80bf9e6a3ad122cb4e0db4f81adf04693fd47047fa24dd9edc7cb037a7`).
      [`../benchmark/PRE-REGISTRATION-NODE.md`](../benchmark/PRE-REGISTRATION-NODE.md)
      — ids `N0`–`N4`, the byte-equal field table, both corpora, all three
      OS/libm pairs, and `N4`'s **p95 ≤ 150 ms** (3× the measured Python
      figure: a fence against an *algorithmic* divergence, not against a
      constant factor). 🔴 **§2's score-comparison cell is blank** and is the
      bullet below. **The document was not frozen and Phase 1 did not start
      until Arpit filled it in.**
- [x] ✅ **ARPIT RULED 2026-09-06 — option (b), tolerance at `round(9)`.**
      No Python change, no golden re-derivation, no hand-rolled transcendental:
      the arm compares the score *field* at `round(9)`, which is the resolution
      `rank.py`'s sort key already uses. **(a)** — `src/fux/query/portable_math.py`
      mirrored bit-for-bit in JS — was declined; it bought bit-identity at the
      price of a corpus-wide ranking change to fix a difference seven orders of
      magnitude below the sort key.
      🔴 **This file previously described (b) as accepting "ordering flips it
      can explain". That was wrong and is corrected here**: under
      [PRE-REG-NODE §2](../benchmark/PRE-REGISTRATION-NODE.md) the ordering
      assertion is **byte-equal under either option**, and a discordant top-5
      fails the arm. (b) tolerates a difference in the printed score, never a
      different ranking.
- [x] Decision recorded in
      **[ADR-RANKING decision 8a](../../docs/adr/0111_ranking.md)** — the sort
      key's resolution is the cross-runtime contract for the score, the order
      is byte-equal, and a divergence above `~1e-9` relative on any platform
      pair voids it.
- [x] **DONE** — [ADR-NODE-SEARCH](../../docs/adr/0155_node-search.md)
      decision 1 says it, as a link to ADR-RANKING 8a and not a second
      statement of the rule (L0). *(This box was still unticked on 2026-09-12;
      re-derived from the record, per OPEN-WORK rule 3.)*

## Phase 1a — the API seam (Python), BEFORE any `node/` file

- [ ] `src/fux/api.py` — `open(root=".") -> Index`; `Index.find/ask/answer/
      explain/graph/path`, each returning a dataclass whose `as_dict()` is the
      `--json` payload and validates against `output.schema.json`.
- [ ] `src/fux/query/__init__.py`'s `cmd_*` become **renderers**:
      `print(render(api.ask(...)))`. No behaviour change — the differential
      harness's Python-vs-Python arm proves it.
- [ ] `src/fux/__init__.py` re-exports `open`. `ADR-API` (new) freezes the
      surface and states what is NOT in it (anything that writes).
- [ ] `.fux/README.md`'s *"the CLI is the contract; the modules are not"*
      becomes *"the CLI and `fux.api` are the contract"* — and the Python
      example in *Calling fux from a script* gains the in-process form beside
      the subprocess one.

## Phase 1b — the harness

- [ ] `tools/differential/node_arm.py` — run both readers over one corpus,
      compare **per PRE-REG-NODE §2's field table on PARSED values** (H2),
      print the first discordant row with both sides. Green Python-vs-Python
      before `node/` exists.
- [ ] The corpus gains a document whose id contains a character above U+FFFF
      (H1) and one whose heading contains non-ASCII (H2).

## Phase 1c — `find`, as a thin vertical slice first

**One query, one document, end to end before any breadth**: hash → analyze →
read one shard → score → emit. That flushes out H1, H2 and the `round(9)` shim
while there are 200 lines to debug rather than 2 000.

- [ ] `hash/blake2b.mjs` (RFC 7693, 32-bit halves, digest sizes 1/8/20; pinned
      against Python `hashlib` **and** RFC Appendix A).
- [ ] `query/{tokenize,stem,analyzer}.mjs` — identifier split before
      lowercasing, the boundary regex, stopwords, Porter with `should_stem`.
- [ ] `store/{format,reader}.mjs`, `query/{scan,bm25f,rank}.mjs`,
      `ingest/priors.mjs`, `config/{root,toml}.mjs`,
      `compat/pyfloat.mjs` (`round(9)` half-even + Python `repr` layout).
- [ ] **The comparator uses code points, not `<`** (H1).
- [ ] `verbs/find.mjs`, `fux.mjs`, `src/index.mjs`, `package.json`.
- [ ] **N4's shape measured on this slice at 10 000 documents** — not its bar,
      its shape. A p95 discovered at Phase 3 is a rewrite; discovered here it
      is a morning.

**Phase 1 gate: N0 + N3.**

## Phase 2 — `ask` + `answer`

- [ ] `query/{confidence,headings,expand,fuse,rerank,provenance}.mjs`;
      `refer/{chunk,rescore,assemble}.mjs`; `compat/pyjson.mjs` for the receipt
      digest (H2).
- [ ] Display title (no cache ⇒ Python's no-cache fallback), W-84 headings,
      the confidence block, `--why`; the rescore **with** W-108's proximity
      multiplier and per-passage locators. **Never fetches** — `answer` on a
      `url:` document reads `.fux/acquired/` or returns `source: index`, so the
      URL-keyed fetcher dispatch has **no Node twin** (R6).
- [ ] `output.schema.json` validated in Node too — the same file, not a copy.

**Phase 2 gate: N1.**

## Phase 3 — graph + `mcp`

- [ ] `edges_from_records` → label propagation (determinized) → PPR-lite /
      routes; the in-memory plane digest equals Python's `graph.json` on both
      corpora.
- [ ] MCP: newline-delimited JSON-RPC on stdio, `initialize` →
      `notifications/initialized`, `tools/list`, `tools/call`, `ping`; tool
      descriptions from **one shared JSON that `src/fux/mcp.py` also reads** (a
      new file; ADR-MCP amended).

**Phase 3 gate: N2.**

## Phase 4 — ship

**Folded in 2026-09-12 from the W-107 finish handoff**, which was
written into a directory retired on 2026-08-18 (`tests/test_archive_law.py`
caught it, for the second time — [W-98's pair](../../archive/README.md) was the
first). The pair is in [`archive/handoff/`](../../archive/handoff/); what was
still live is here, because an archived doc may not back a live claim.

### Out of scope — do not "helpfully" add these

- 🔴 **The renderer refactor.** `cmd_ask -> print(render(api.ask(...)))` is the
  finished shape and [ADR-API](../../docs/adr/0156_api.md) records it as
  deliberately staged. It touches a 1 481-line hot file.
- 🔴 **Publishing to npm**, and **no global bin in the first release** (R1a).
- 🔴 **Reporting any differential arm as "green" in a record.** PRE-REG-NODE §4
  names `fux-playground`, which L9 voided as an instrument (H3). Run the arms,
  report the numbers in the WORKLOG; do not write *"N0 passes"* into an ADR.
- Touching [`PRE-REGISTRATION-NODE.md`](../benchmark/PRE-REGISTRATION-NODE.md)
  at all. It is frozen.
- `--expand`, `--why`, `--receipt`, `--journal`, `verify` in Node.
- Moving `Tune.rerank_weight` off `0.0`.

### Three findings from the 2026-09-12 stress test, two of which changed the plan

1. 🔴 **`api.py` re-introduced the decoder import** `cli.py` explicitly avoids.
   **It was NOT fixed when the handoff said it was** — re-measured 2026-09-12,
   `fux.open(".")` cost **50.2 ms**, against 2.6 ms once the gate became a stat
   with the import only on the cold path. `tests/test_api.py` asserts on
   `sys.modules` rather than on a clock.
2. 🟠 **R2's size argument was framed for ONE file** (*"~200 KB"*). The reader
   is **37 files, 196 KB**. The conclusion survives — 2 % of a 9.5 MB index,
   still smaller than `.fux/decoders/` — but a consumer's `git status` shows
   **37 new files** after `fux setup`, and every version bump re-diffs them.
3. 🟠 **Copying `node/` into `src/fux/templates/` would put a second copy in
   the repo.** Hatchling `force-include` maps it into the wheel at build time
   instead. ⚠ **It does not surface in an EDITABLE install** (measured: 37
   files in the built wheel, 0 under `uv pip install -e .`), so
   `fuxdir._node_source()` falls back to the checkout's own `node/` — the
   directory the wheel is built from, one source read two ways.

### What landed

- [x] **`fux setup` writes `.fux/node/` + `.fux/fux`** per R2 —
      **overwritten on a version difference, not write-if-missing** — and
      `fux doctor` gains the drift row. **ADR-DOTFUX amended** with the fourth
      shape.
- [x] **`ADR-NODE-SEARCH`** (0155, accepted) and **`ADR-API`** (0156, accepted) — both in the register with ownership rows. Decisions on the `_format` version policy, the never-fetch rule, the `url:`-verdict asymmetry, the shared tool-description file (ADR-MCP decision 11) and the `compat/`+`hash/` twin exemption.
      ⚠ **Superseded line, kept for the diff:** owns `node/`; decisions on the `_format`
      version policy, the never-fetch rule, the `url:`-verdict asymmetry, the
      shared tool-description file, and the `compat/`+`hash/` twin exemption.
- [x] **Ownership table + `tests/test_adr_ownership.py`** — `node/` -> ADR-NODE-SEARCH (the only owned component outside `src/` and `tools/`), `src/fux/api.py` -> ADR-API, and a `describes` row narrowing `store/fuxdir.py` to the four vendoring functions.
      ⚠ **`src/fux/__init__.py` has NO describes row**: the qualifier narrows to top-level `def`s and `class`es, `open` there is an imported NAME, and an un-narrowed row would demand ADR-API on every version bump. The gate reaches ADR-API through `api.py` instead; editing the re-export alone does not open it.
      ✅ **LANDED 2026-09-12: `tests/test_node_twins.py`** — the map is derived
      from the path rule, then from a `src/fux/….py` path the module names in
      its own header, then a **two-entry** exemption set (`compat/pyfloat.mjs`,
      `hash/blake2b.mjs`), which is the only hand-maintained part. Five
      modules — `index.mjs` and the four `verbs/*.mjs` — had no machine-readable
      twin declaration and gained one. It also fails when a Python twin moves
      in the working tree and its `.mjs` does not, **which the differential arm
      structurally cannot catch**: an un-updated Node module still agrees with
      itself, and only disagrees on a corpus that exercises the changed branch.
- [x] **`--version` names the runtime** (`fux 2.0.0-alpha.7 (node 24.13.0)`) and unsupported verbs signpost. ⏳ The Python `doctor` PATH row (R1a item 3) is **not built** and is not owed yet: no global bin ships in the first release, so there is nothing to shadow.
      ⏳ superseded line: unsupported verbs signpost; the Python
      `doctor` PATH row (R1a).
- [x] **CI matrix Node 20/22 × ubuntu/macos(arm64)/windows** —
      [`node-arm.yml`](../../.github/workflows/node-arm.yml), the arm on every
      push. ⚠ **`node --test node/test/` — a bare directory argument — dies
      `MODULE_NOT_FOUND` on Node 24**, so the step runs `node --test` with
      `working-directory: node` instead: stable on 20/22/24 and needing no
      shell glob, which `pwsh` would not have expanded on the windows leg.
      ⚠ `log-probe.yml` is still **unrun**. ⚠ `log-probe.yml` is still **unrun** — musl, Windows and
      Node 20 are unmeasured.
- [x] **npm `fux-engine` PUBLISHED 2026-09-12** — `2.0.0-alpha.7`, tags
      `alpha` and `latest`. ⚠ **`latest` was not intended and could not be
      prevented:** npm always creates `latest` on a package's FIRST publish and
      ignores `--tag`, so `npm i fux-engine` resolves to an alpha until a
      stable release moves it. `npm dist-tag rm fux-engine latest` is the undo
      if that is wrong. **Shipped WITH the global bin against R1a** — see the
      amendment in R1a above. **npm trusted publishing (OIDC) is configured**:
      `arpitarya/fux` · `publish.yml` · no environment · `Allow npm publish`
      **unchecked**, so CI stages and a human confirms each publish on
      npmjs.com. Original line: **npm `fux-engine` NOT published (out of scope,
      R1a)**. ⚠ **Two publication defects were fixed on contact**: `mcp-tools.json` was absent from `package.json`'s `files`, so `fux mcp` would have broken in the published package; and `{{TOP}}` substituted into serialized JSON produced `"default": "5"` — a string — on a property declared `"type": "integer"`. Original line: **no global bin in the first release**
      (R1a); README front door; CHANGELOG.
- [x] `IMPLEMENTATION.md` row. ⏳ **This file stays in `open/`**: npm publication and the renderer split are still open, so the item is not closed.

## Blockers

- ~~`arpit`: ratification~~ — **ratified 2026-09-05.**
- ~~🔴 `arpit`: the Phase 0 `log()` pick~~ — **ruled 2026-09-06: (b),
  tolerance at `round(9)`.**
- ~~W-108 should land first~~ — **landed 2026-09-05.**
- ~~🔴 `arpit`: naming, placement, and whether Python gets an importable
  surface~~ — **ruled 2026-09-12, R1–R6 above.**
- 🟡 **H3 — no arm is green until the superseding pre-registration exists**,
  which waits on W-136 phase 2 for lab golden data. **The build is not
  blocked.**

▶ **Nothing blocks Phase 1a. It starts.**

## Open questions for Arpit — re-derived 2026-09-12; TWO OF THREE ARE SETTLED

⚠ **This section was stale.** O1 and O2 were answered in the code and in a
record respectively, and the section still presented them as open — the exact
defect OPEN-WORK rule 3 warns about, in a detail file rather than the queue.

- ✅ **O1 · Does Node enforce the `.fux/pii.toml` gate?** **Yes, identically —
  ruled by Arpit 2026-09-12 and built.** `node/fux.mjs`'s `requirePiiRules`
  refuses every verb and exits 1 without the file; the literal is held equal to
  the two Python copies by
  `tests/test_cli.py::test_the_node_reader_gates_on_the_same_file`. Verified by
  behaviour 2026-09-12, not by reading the box.
- ✅ **O2 · Is `fux.api` public at 1.0, or provisional?** **Public and frozen** —
  [ADR-API](../../docs/adr/0156_api.md) decision 1: *"`fux.api` is a supported
  surface, frozen like any other."* Provisional was not taken.
- 🟡 **O3 · `PRE-REGISTRATION-NODE-2` — DRAFTED 2026-09-12, NOT FROZEN.**
  [`../benchmark/PRE-REGISTRATION-NODE-2.md`](../benchmark/PRE-REGISTRATION-NODE-2.md).
  Supersedes rather than edits (H3), moves the corpora to the committed golden
  ladder, states H2's parsed-not-bytes comparison, and carries **Arpit's ruling
  of 2026-09-12**: the arm is **standing, not a gate** — every change to either
  reader, in fux-lab, and both must give the same results. Ids **N5–N9**;
  N0–N4 retired with the document that froze them and never reused.
  🔴 **Two cells are his and the document does not freeze until they are
  filled** — §7: (1) does the latency fence `N9` belong in an equivalence
  document or in `fux-benchmark` under L9, and (2) all eight rungs on every
  push, or the two ends on every push and all eight nightly? **No number may
  be measured against it until then**, and no arm may be reported.

## Out of scope

`ingest`, `build`, `add/remove/update`, `enrich`, `embed`, `doctor`, `setup`,
the accelerator, any fetcher. A Node-side cache (`--fast`) until the scan p95
is measured at 10 000 documents.

## From OPEN-WORK (moved 2026-09-11)

*Moved here verbatim when OPEN-WORK became one-to-two-line rows (Arpit, 2026-09-11). Links are rewritten for this directory.*

*This is what the queue said at the move. Re-derive it before believing it (OPEN-WORK rule 4).*

- 🟠 **Search v3 — what is left of it: W-107 Phases 1–4, then W-112.** ·
  *(spec: [`proposals/search-v3.md`](../proposals/search-v3.md) §8 · one detail
  file each under [`open/`](README.md))* · **Opus** executes, in Arpit's
  ratified order: **W-107 Phases 1–4** → **W-112**. `ratified: 2026-09-05`
  - **[W-107](W-107-node-read-plane.md)** · `agent` · *(**ADR-NODE-SEARCH** new · ADR-RANKING · ADR-MCP)* · the Node read plane — `npx fux-search ask|find|answer|explain|graph|path|mcp`, zero deps, one contract, a third arm of the differential law. ▶ **Phase 1 starts; nothing blocks it.** Phase 0's `log()` question is settled and the rule lives in [ADR-RANKING decision 8a](../../docs/adr/0111_ranking.md) — scores equal after `round(9)`, ordering byte-equal; [`PRE-REGISTRATION-NODE.md`](../benchmark/PRE-REGISTRATION-NODE.md) is frozen in full, sha `0e3b4c80bf9e6a3ad122cb4e0db4f81adf04693fd47047fa24dd9edc7cb037a7`, and Phases 1–4 build against it. ⚠ **§4 still requires all three OSes before an arm is called green**, and only glibc/arm64 has been touched — [`log-probe.yml`](../../.github/workflows/log-probe.yml) is **unrun**, so musl, Windows and Node 20 are unmeasured. ⚠ **[L9](../../docs/adr/0011_LAW-9-environments.md): its frozen pre-registration names the playground** — the build (Phases 1–4) is unaffected, but any measured arm runs on fux-lab golden data under a superseding pre-registration ([W-138](../../archive/open/W-138-reconcile-with-l9.md)). `filed: 2026-09-04`
