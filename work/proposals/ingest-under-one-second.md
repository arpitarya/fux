---
type: Proposal
title: Ingest under one second — 10 000 documents, any language
description: "Arpit's ask (2026-10-10): `fux ingest` of 10 000 documents in under one second, with no language off the table. Finds where today's 4.9 s (no change) and ~12 s (full, end to end) go, and that pure Python can reach the no-change and small-change cases but not a full ingest. Proposes two shapes in order: A — an incremental ingest in today's Python (skip unchanged files by a git-style stat cache; carry per-document statistics, never text), then B — a Rust core behind PyO3 for the full ingest, parallel by shard and deterministic. Step 0 measures three unknowns on the Mac first."
status: graduated
timestamp: 2026-10-10T00:45:00+05:30
---

# Ingest under one second — 10 000 documents, any language

**Arpit, 2026-10-10 (Cowork), after W-267:** *"I was talking about if ingest
can happen within one second, even more better. No boundaries, no limitations.
If programming language is a boundary, find another programming language in
which it can be done in a faster way. But do some research. I would love to
bring it under one second. For the time being, close this work item and let's
do some research and put a proposal."*

**Status: graduated 2026-10-10 into the compare doc [`ingest-under-one-second.compare.md`](../compare/ingest-under-one-second.compare.md)** — the forks and their verdicts live there now; this file keeps the research. Not ruled, not built.

**Was: proposed, not ruled, not built.** Research and a recommendation only
— no code, no record change. Work item: [W-268](../open/W-268-ingest-under-one-second.md).

## Recommendation, first

1. **Define the clock before anything else.** Three numbers, all wall clock of
   the `fux ingest` **command** (interpreter start to exit, accelerator build
   included), rung-10000, Arpit's Mac, warm page cache:
   **G1** nothing changed · **G2** one file changed · **G3** full ingest from
   no index. Today the timed `ingest.run` alone is **4.90 s** (G1) and
   **9.44 s** (G3); the G3 command took **11.995 s**.
2. **Step 0 — measure three unknowns on the Mac** (a spike, no product code):
   Python start + `import fux` time; the accelerator build's time; the cost of
   opening and reading 10 000 small files, serial and parallel.
3. **Shape A — incremental ingest, in today's Python.** Reaches **G1 and G2**
   without a new dependency. Probably G1 ≈ 0.1–0.3 s, G2 < 1 s *[inference]*.
4. **Shape B — a Rust core behind PyO3, for G3.** Pure Python cannot reach a
   one-second full ingest (§3); native code with deterministic parallelism can
   *[inference from §5's prototype]*. It costs a platform-wheel matrix and a
   second implementation of the analyzer, so it goes **after** A, behind its
   own measured spike.

**What Arpit picks:** (a) A then B, staged, each behind a pre-registered bar
(recommended) · (b) B directly — rewrite ingest in Rust now · (c) A only, and
accept a multi-second full ingest.

## 1 · Where the time goes today

Medians of three, `ingest.run` only, fresh process each, 10-core Mac, Python
3.14, gen-4 rung-10000 ([run](../regression/2026-10-09-ingest-split-remeasure/report.md)):

| phase | no change | full | what it does for an **unchanged** document |
|---|---:|---:|---|
| walk | 0.84 | 0.83 | reads **every file's bytes** and hashes them |
| parse gap | 1.42 | 1.38 | JSON-parses all 256 committed shards; decodes and parses **every** file |
| redact | 0.96 | 0.97 | redacts **every** file (edges and the PII census need redacted text) |
| extract | 0.00 | 3.81 | tokenise + analyse 5 fields; skipped when reused |
| before:write | 0.86 | 1.49 | edge resolution for every doc; term hashing; **one `git log --name-only` over the whole history** |
| write | 0.69 | 0.76 | canonical JSON of **every** record; byte-compares all 256 shards |
| tail | 0.11 | 0.17 | digests, counts, ledger |
| **total** | **4.90** | **9.44** | |

**Not in those numbers:** interpreter start-up and the accelerator build
(`derive/_build.py`, called from `ingest/__init__.py` after `run()`), which
**rebuilds `.fux/runtime/` in full every time**. The full command was 11.995 s,
so about 2.5 s sits outside the timed run *[inference: subtraction, not a
measured split]*.

**The finding that shapes everything:** at no change, **every second of the
4.90 s is spent re-doing work for documents that did not change**. The
committed records already hold per-field term counts and lengths, and scoring
(BM25F) happens at query time from `stats.json` — **committed records do not
depend on corpus-wide df or avgdl**, so changing one document does not ripple
into other documents' records, except through links that start or stop
resolving.

## 2 · Shape A — incremental ingest, in Python (G1, G2)

Skip unchanged documents entirely, instead of making their work faster:

1. **A stat cache, the way git's own index works.** Keep path, size, mtime,
   ctime, inode per file in `.fux/runtime/`; a file whose stat matches is
   unchanged and **is not read**. Git's *racily clean* rule applies verbatim: a
   file whose mtime is not older than the cache is re-hashed
   ([racy-git](https://git-scm.com/docs/racy-git)). Statting 10 000 files took
   29–40 ms in §5's prototype.
2. **Carry per-document derived facts, never text.** What edges, anchors, the
   PII census and priors need from an unchanged document — link targets,
   anchor-term hashes, frontmatter `superseded`/tags, PII hit counts — is
   cached per content sha. These are statistics of the kind the index already
   commits, so **L3 is not engaged** (unlike a parse cache, which would hold
   parsed text).
3. **Priors from history incrementally:** remember the last commit
   `git_commit_times` processed and read only the commits since.
4. **Write only what changed:** re-serialise only changed records and the
   shards they live in; do not JSON-parse all 256 shards to find that out.
5. **Accelerator updated, not rebuilt:** today `docidx` is a position in the
   id-sorted list, so one insert shifts every later id. Either give documents
   stable ids in the runtime plane, or rebuild lazily on first query.

**A hazard already named:** [SR-INGEST](../../records/0106_ingest.md) decision 17
records that anchor text must be resolved *source-locally*, and that an
incremental ingest would have inherited the drift had it been built first;
`tests/ingest/test_anchor_is_source_local.py` guards the property. Shape A
keeps that test green.

**Proof obligation (L4):** an incremental ingest must be **byte-identical** to a
full ingest of the same tree, on every committed and derived byte — a
randomised edit-sequence test, the way `fux-merge-index` is tested.

**Cost:** no dependency, no packaging change, Python only. **Does not move
G3.**

## 3 · Why Python alone cannot reach G3

- **Compilers for Python top out near 5×.** mypyc: 1.5–5× typical, 5–10× when
  tuned ([mypyc](https://mypyc.readthedocs.io/en/latest/introduction.html)).
  9.44 s ÷ 5 ≈ 1.9 s, before start-up and the accelerator *[inference]*.
- **Processes:** macOS and Windows start workers by *spawn*, which the docs call
  "rather slow" ([multiprocessing](https://docs.python.org/3/library/multiprocessing.html)).
- **Free-threaded CPython** costs 1–8 % single-thread
  ([howto](https://docs.python.org/3/howto/free-threading-python.html)) and
  would parallelise the pure-Python stages — realistically 2–3 s on 10 cores
  *[inference]*.
- **The regex gap alone:** rebar's geometric-mean search-time ranking puts
  `python/re` at 42.1 against `rust/regex` 3.08 ([rebar](https://github.com/BurntSushi/rebar))
  — redaction and tokenising are regex-bound here.

## 4 · Shape B — a Rust core behind PyO3 (G3)

**Why Rust over the alternatives:**

| language / route | verdict | why |
|---|---|---|
| **Rust + PyO3/maturin** | **recommended** | abi3 wheels for macOS, Linux (glibc+musl), Windows, x64+arm64 ([maturin](https://www.maturin.rs/platform_support)); GIL released + rayon (PyO3's own example: 29.0 ms Python → 8.0 ms Rust → 2.0 ms Rust+rayon, [pyo3](https://pyo3.rs/main/parallelism.html)); precedents: pydantic-core, orjson, ruff, HF tokenizers; the `regex` crate is linear-time (no ReDoS — the class W-255 tripped on); the same crate can serve Node via napi-rs |
| C++ (nanobind) | viable, second | stable ABI from 3.12, BSD-3 ([nanobind](https://github.com/wjakob/nanobind)); no memory safety; fewer Python precedents |
| mypyc / Cython | short of goal | ≤ 5× (§3); per-version wheels; free-threading experimental |
| Go (gopy) | rejected | no wheel story ([gopy](https://github.com/go-python/gopy)) |
| Zig (ziggy-pydust) | rejected | "early stages", no releases ([pydust](https://github.com/spiraldb/ziggy-pydust)) |
| Mojo | rejected for now | open-sourced 2026-08-18; no Windows or Python-extension packaging story found |
| Vectorscan (regex) | rejected | Windows unsupported — breaks L2's "works the same on every machine" |

**The design:**

- **Rust owns the hot path:** walk + stat cache, hashing, built-in decoders for
  prose/yaml/eml, redaction (`RegexSet` + the Luhn/Verhoeff validators), the
  analyzer, term hashing, edges, record building and canonical JSON.
- **Python keeps the CLI, config loading and the consumer extension points.**
  `.fux/decoders/` stays readable Python (L10's contract): the Rust core calls
  back for those files only; those calls run one at a time under the GIL.
- **Deterministic parallelism (L4):** sort documents by id before assigning
  anything; partition work by **shard** (256 is already the natural unit);
  build each shard independently; emit in fixed order. Nothing is ordered by
  which thread finished first. Lucene shows the failure this avoids: its
  multi-threaded indexing assigns doc ids "in a non-deterministic order"
  ([arXiv 1807.05798](https://ar5iv.labs.arxiv.org/html/1807.05798)).

**What it costs — named, not hidden:**

1. **Distribution.** Today one pure-Python wheel; after, ~8 abi3 platform
   wheels (+ free-threaded ones: abi3 wheels do not load on free-threaded
   CPython until `abi3t`, 3.15 — [pyo3](https://pyo3.rs/main/building-and-distribution.html)).
   pydantic-core wheels are ~2 MB, rpds-py 0.2–0.6 MB. **L2's "dependencies
   ship packaged … no capability that works on one machine and not another"**
   means every supported platform gets a wheel, or there is a pure-Python
   fallback — a fork for Arpit.
2. **A third analyzer.** Python (ingest + query) and Node (query) already
   carry the analyzer; Rust would be a third copy, held equal by a differential
   test. Or Rust becomes **the** analyzer for all three (PyO3 + napi-rs) — a
   larger, later decision.
3. **Laws touched:** L2 (an SR names the crate set; all MIT/Apache), L4 (the
   parallel design above + a byte-equality test against the Python engine on
   every rung), L10 (a compiled extension is build output — fits), L12 (Rust
   reads the same TOML keys; no defaults in code). **None is broken; L2 and L4
   each need an SR decision.**
4. **YAML in Rust is a weak spot:** `serde_yaml` is deprecated and `serde_yml`
   is flagged unsound (RUSTSEC-2025-0068); the maintained forks need vetting.

## 5 · Evidence that G3 is reachable natively

- **Engines:** Tantivy indexed English Wikipedia — 5 M documents, 8 GB — in
  94 s on 4 threads, about 53 000 docs/s ([fulmicoton](https://fulmicoton.com/posts/behold-tantivy-part2/)).
  At that rate 10 000 documents is ~0.2 s *[inference: arithmetic, on very
  different documents]*.
- **A throwaway prototype (this research, not fux code):** Rust, standard
  library only, a slow 2-vCPU Linux VM, a **synthetic** 10 000-file corpus of
  133.6 MB — walk + stat 29–40 ms, read 117–148 ms, tokenise 0.82–0.92 s,
  invert + quantise 0.89–1.10 s: **≈ 2.0 s on 1 thread, ≈ 1.5 s on 2**, output
  hash identical at both thread counts.
- **fux's corpus is ~15× smaller:** about 8.9 M characters of body text and
  905 044 postings at rung-10000, against the prototype's 133.6 MB and 8.88 M
  postings. Scaled, tokenise + invert is ~0.2–0.4 s on **one** slow core
  *[inference]* — before using the Mac's 10.

**The one real risk:** macOS per-file open/read cost. One write-up measured
~140 µs per file on macOS ([modulovalue](https://modulovalue.com/blog/syscall-overhead-tar-gz-io-performance/),
single-threaded, cache state not stated) — **1.4 s for 10 000 files**, the
whole budget. G1/G2 avoid it by not reading unchanged files; G3 needs parallel
reads, and Step 0 measures it.

## 6 · The staged plan

| step | what | bar (pre-registered before it runs) | model |
|---|---|---|---|
| 0 | **Spike on the Mac:** start-up + import, accelerator build, 10k-file read serial vs parallel | — (it sets the budget) | Sonnet |
| 1 | **Shape A** | G1 < 1 s and G2 < 1 s at rung-10000; incremental ≡ full, byte for byte | Opus |
| 2 | **Rust spike:** the analyzer + tokenise over rung-10000, tokens byte-equal to Python's | projected G3 < 1 s from measured stages, or stop | Opus |
| 3 | **Shape B** | G3 < 1 s; Rust ≡ Python output on every rung; wheels on every platform | Opus |

Each step is its own W-item and stops on its own bar; a step that misses goes
back to Arpit, not around him (SR-RS decision 10b).

**Graduation trigger:** Arpit picks (a), (b) or (c) on W-268 → step 0 and the
chosen steps are filed as W-items, and this file becomes `graduated`.

## References

- [W-267's run](../regression/2026-10-09-ingest-split-remeasure/report.md) — the per-phase split above.
- [racy-git](https://git-scm.com/docs/racy-git) — git's stat cache and the racily-clean rule.
- [PyO3 parallelism](https://pyo3.rs/main/parallelism.html) · [PyO3 distribution](https://pyo3.rs/main/building-and-distribution.html) · [maturin platforms](https://www.maturin.rs/platform_support).
- [rebar](https://github.com/BurntSushi/rebar) — regex engine benchmarks.
- [Tantivy part 2](https://fulmicoton.com/posts/behold-tantivy-part2/) — indexing Wikipedia.
- [Deterministic doc ids in Lucene](https://ar5iv.labs.arxiv.org/html/1807.05798).
- [mypyc](https://mypyc.readthedocs.io/en/latest/introduction.html) · [free-threading](https://docs.python.org/3/howto/free-threading-python.html) · [multiprocessing](https://docs.python.org/3/library/multiprocessing.html).
- [nanobind](https://github.com/wjakob/nanobind) · [gopy](https://github.com/go-python/gopy) · [ziggy-pydust](https://github.com/spiraldb/ziggy-pydust).
- [RUSTSEC-2025-0068](https://api.osv.dev/v1/vulns/RUSTSEC-2025-0068) — `serde_yml`.
- [macOS per-file I/O](https://modulovalue.com/blog/syscall-overhead-tar-gz-io-performance/).
