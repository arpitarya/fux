---
type: Proposal
title: The ingest engine in Rust — Python's ingest replaced, not accelerated
description: "Arpit's direction (2026-10-26): the core engine is designed to be built on Rust, and the whole ingest path — slow today — runs only in Rust; Python's ingest is replaced, not kept beside it. Reverses W-268's accepted F1 = S1 (incremental Python first) and F3 = P1 (Python engine as fallback). Maps what today's Python ingest is made of, proposes the shape (a PyO3 native module, one Rust pipeline, incremental from day one, Python decoders called back), names the eight forks only Arpit can close, and stages the build behind measured bars."
status: graduated
timestamp: 2026-10-26T11:30:00+05:30
---

# The ingest engine in Rust — Python's ingest replaced

**Arpit, 2026-10-26 (Cowork):** *"Okay, the core engine. Let's design for it
to be built on Rust. And Python will be replaced by Rust. The whole ingest
part, which is slow today, would be only in Rust. Research, propose, create a
work item. Ask me if there are any blockers."*

> **Verdict — RULED by Arpit, 2026-10-26 (Cowork), the same session:**
> **R1 = a** straight to Rust, incremental built in · **R2/R3 = b** the Python
> ingest is **kept** as the fallback for a machine with no wheel and as the
> reference Rust is diffed against (W-268's P1 stands) · **R4 = a** text formats
> + JSON native, other decoders called back · **R5 = both, held equal** — the
> Rust analyzer where a wheel exists, Python's kept for the fallback, a
> differential test between them (re-recommended after R2 = b) · **R6 = a**
> `fancy-regex` where needed · **R7 = a** runtime build in Rust, Node's and
> Python's builders kept and held equal · **R8 = a** a new `fux-native`
> distribution. ⚠ **So "Python replaced" means Rust is the ingest engine
> wherever a wheel exists; Python's ingest is no longer developed for speed but
> is not deleted.** Where the text below says *deleted at cutover* or *one
> analyzer*, the verdict overrides it. Decision record:
> [`rust-ingest-core.compare.md`](../compare/rust-ingest-core.compare.md).

**Status: graduated 2026-10-26** into the compare doc above. Nothing built. Work item: [W-305](../open/W-305-rust-ingest-core.md).
It builds on [`ingest-under-one-second.md`](ingest-under-one-second.md) (the
per-phase timings, the language survey, the prototype) and does not repeat it.

## Recommendation, first

- **Shape:** one Rust crate, `fux-native`, shipped as a PyO3 extension module in
  pre-built wheels. `fux ingest` stays the same command; its whole pipeline —
  walk, stat cache, decode of the built-in text formats, redaction, analysis,
  edges, git priors, records, shards, register, runtime build — runs in Rust.
  Python keeps argument parsing and the call into the module.
- **Incremental from day one, in Rust.** No Python shape A first: it would be
  written once and deleted. The Rust pipeline skips unchanged files by a
  git-style stat cache (the old proposal §2).
- **Python ingest is deleted at cutover.** Its last output on every rung is
  frozen first as a committed byte oracle, so "Rust ≡ the engine it replaced"
  stays testable after the Python code is gone.
- **Python decoders stay Python, except JSON.** `.fux/decoders/*.py` and the
  decoder packages (pdf, sheet, office, html…) are called back from Rust through
  PyO3. JSON is ported, because it is ~39 % of fux's own corpus (§3 hazard 7).
  Porting any other package is a later, per-package choice.
- **One analyzer for Python.** The query side calls the same Rust analyzer, so
  ingest and query cannot drift; Node keeps its own twin, held by the parity
  test it already has.

**What this reverses:** W-268's accepted **F1 = S1** and **F3 = P1**
([compare doc](../compare/ingest-under-one-second.compare.md), ruled
2026-10-25). F2 (Rust + PyO3, no consumer installs Rust) stands.

## 1 · What "the ingest part" is today

The `fux ingest` command touches far more than `src/fux/ingest/`. Python lines
on the path, counted 2026-10-26 (a count of what exists, **not** a port
estimate):

| area | lines | layer | on the hot path because |
|---|---:|---|---|
| `src/fux/ingest/` | 4 350 | writer | the run, extract, edges, priors, register, queue |
| `src/fux/text/` | 1 842 | core | analyzer, stemmer, tokenizer, identifiers, chunker — **shared with query** |
| `src/fux/acquire/` (walk, pii, gitdir, sources, fuxignore, types, yaml subset) | ~4 900 | core | what is a document, redaction, git commit times |
| `src/fux/decode/` (registry + markdown ext) | ~1 300 | core | built-in decoding, the plugin gate |
| `src/fux/store/` (format, canonical, writer, pack, reader) | ~900 | core | term hash, content sha, canonical JSON, shards |
| `src/fux/derive/` | 1 825 | reader | the `.fux/runtime/` build — rebuilt in full after every ingest |
| **total** | **~15 000** | | |

**URL ingest is out of this scope:** fetching (`acquire/urlsrc.py`, the http and
cdp fetcher packages) is network-bound, stays Python, and hands its bytes to
the Rust pipeline through the acquired plane.

## 2 · The shape

```
fux ingest (Python: parse args, load nothing else)
   │
   ▼
fux_native.ingest(root)                         ← Rust, GIL released
   ├─ config: fux.toml + .fux/config/*.toml + constants.toml (L12: no defaults in code)
   ├─ walk + stat cache ── unchanged file? → carry its record, never read it
   ├─ decode ── built-in text formats in Rust
   │            └─ any other suffix → Python callback (plugin package or .fux/decoders/)
   ├─ redact (pii.toml) ─ analyze ─ edges ─ priors (git, incremental)
   ├─ records → 256 shards, built in parallel, emitted in shard order (L4)
   ├─ REGISTER, .fuxignore blocks, enrich queue
   └─ .fux/runtime/ build
```

- **Distribution:** a new PyPI name `fux-native`, platform wheels, depended on by
  `fux-core`. `fux-core`, `fux-reader`, `fux-writer` and `fux-engine` stay
  pure-Python wheels; only `fux-native` carries per-platform binaries.
- **Determinism (L4):** documents sorted by id before anything is assigned;
  work partitioned by shard; nothing ordered by which thread finished first;
  `BTreeMap`/sorted vectors, never iteration over a hash map. Byte-identical
  across thread counts and platforms, tested on every rung.
- **Laws:** L2 — a record names the crate set, every crate OSI-licensed
  (`regex`, `fancy-regex`, `rayon`, `blake2`, `toml`, `pyo3` are MIT/Apache);
  L4 — the parallel design and its test; L7 — `abi3-py312` covers 3.12+;
  L10 — a compiled module is build output, it fits; L12 — Rust reads the same
  TOML keys. **None broken; L2 and L4 each need a record decision.**

## 3 · Hazards found while mapping

1. 🔴 **The PII rules are written in Python's regex dialect, and Rust's
   `regex` crate cannot compile them.** fux's own shipped `pii.toml` template
   uses look-behind, look-ahead and back-references (`(?<![0-9][\s-])`,
   `(?!000|666|9[0-9]{2})`, `\1`). `regex` supports none of those, by design.
   `fancy-regex` does, delegating the easy parts to `regex` — but gives **no
   worst-case time guarantee** for the hard parts
   ([fancy-regex](https://docs.rs/crate/fancy-regex/0.19.0)), the ReDoS class
   W-255 bounded. Consumer `identifiers.toml` and `refusals.toml` regexes have
   the same question. → **fork R6**.
2. **Two regex engines do not agree at the edges.** `\b`, `\s`, `\w` and
   case-folding differ between Python `re` and any Rust engine. The analyzer
   must be specified by explicit character classes and checked against the
   oracle on the whole ladder, not assumed equal.
3. **Unicode version stops depending on Python.** Today `str.lower()` and
   `str.isalnum()` follow whatever Unicode the interpreter ships, so an index can
   differ between Python 3.12 and 3.14. A Rust core pins its Unicode tables per
   release — **a determinism gain**, but the first Rust build may differ from
   the oracle on rare code points; those diffs must be listed, not hidden.
4. **Canonical JSON must match Python's float repr.** Node already carries
   `compat/pyfloat.mjs` for exactly this. Rust's shortest-round-trip formatting
   prints exponents differently (`1e-05` vs `1e-5`); a formatter written to
   Python's rules is needed.
5. **The stemmer is fux's own** (`text/stem.py`, 210 lines), not a library one;
   it is ported, not swapped for `rust-stemmers`.
6. **Free-threaded CPython cannot load abi3 wheels** until `abi3t` (3.15,
   [PyO3](https://docs.rs/crate/pyo3/0.29.2/source/guide/src/building-and-distribution.md));
   3.13t/3.14t need their own version-specific wheels.
7. **A Python callback re-takes the GIL.** Callback decoders run one at a time;
   a corpus of mostly PDFs gets little from Rust until that decoder is ported.
   **fux's own corpus is the case:** of ~2 600 files of indexable types under its
   source paths (counted 2026-10-26), Markdown and text are ~56 % and **JSON /
   JSON Lines ~39 %** — and JSON is a decoder *package*. So the json decoder is
   ported in step 4, not left as a callback.
8. **macOS per-file open cost** stays the open risk from the old proposal §5:
   ~140 µs/file would be the whole budget. Parallel reads plus the stat cache
   are the answer; step 0 measures it.

## 4 · The forks — Arpit's to close

| # | question | options | recommended |
|---|---|---|---|
| R1 | Build incremental in Python first (S1, ruled 2026-10-25)? | (a) **no — straight to Rust, incremental built into the Rust pipeline** · (b) keep S1 | (a) — A in Python would be deleted at cutover |
| R2 | What happens to the Python ingest? | (a) **deleted at cutover; its output frozen first as a committed byte oracle** · (b) kept as a shipped fallback (P1) · (c) deleted, no oracle | (a) |
| R3 | A machine with no wheel? | (a) **wheels for macOS x64/arm64, Linux glibc+musl x64/arm64, Windows x64/arm64, plus free-threaded builds; anything else fails at install, loudly** · (b) keep a Python fallback | (a) — needs one L2 sentence: an unsupported *platform* is refused at install, which is loud, not machine-chosen behaviour |
| R4 | Decoders | (a) **built-in text formats and the json package native; other packages and `.fux/decoders/` called back into Python** · (b) port every first-party decoder package to Rust now · (c) drop the Python decoder seam | (a); (b) later, one package at a time, each measured |
| R5 | Analyzer | (a) **Rust is Python's only analyzer — query calls it too** (every Python install then carries `fux-native`) · (b) Rust in the writer only; Python query keeps its own, held equal by a test | (a) — one analyzer cannot drift from itself |
| R6 | Consumer regexes (pii, identifiers, refusals) | (a) **`fancy-regex` for rules that need it, `regex` for the rest; `fux doctor` refuses a rule neither compiles; equality test vs the oracle** · (b) a new linear-time-only dialect — templates rewritten, a breaking change for consumers · (c) redaction stays a Python callback (~1 s — misses the goal) | (a) |
| R7 | `.fux/runtime/` build (~2.5 s of today's command) | (a) **in Rust, Node's JS builder kept and held equal** · (b) left in Python | (a) |
| R8 | Packaging | (a) **new `fux-native` distribution, platform wheels; the other four stay pure Python** · (b) `fux-core` itself becomes platform-specific | (a) — needs **your** PyPI trusted publisher for the new name |

## 5 · The staged plan

| step | what | bar, named before it runs | model |
|---|---|---|---|
| 0 | Measure on the Mac: start-up + import, runtime build, 10k-file read serial vs parallel (W-268 step 4) | sets the budget; reopen if reads ≥ 1 s even in parallel | Sonnet |
| 1 | The differential harness: run Python and Rust ingest on every rung and on scripted edit sequences, compare every committed and derived byte (R2 = b keeps Python as the live reference) | the harness passes Python against itself, and fails on a planted one-byte change | Sonnet |
| 2 | Rust spike: tokenizer + analyzer + stemmer + term hash + canonical JSON over rung-10000 | tokens and term hashes byte-equal to the oracle; projected G3 < 1 s from measured stages, or stop | Opus |
| 3 | Crate, workspace, wheel matrix on CI, the crate-set record (L2) | wheels install and import on every listed platform | Opus |
| 4 | The full pipeline in Rust, incremental, with Python decoder callbacks | every committed and derived byte equal to the oracle on every rung; G1, G2 < 1 s | Opus |
| 5 | Runtime build in Rust; the query analyzer switched to Rust | `ask`/`answer` results unchanged on the ladder | Opus |
| 6 | Cutover: Rust becomes the default ingest engine wherever `fux-native` imports; Python stays as fallback; `fux doctor` names the engine; records updated | G3 < 1 s on the Mac at rung-10000; both suites green on both engines | Opus |

**The clock is W-268's:** wall clock of the `fux ingest` command, start-up and
runtime build included, rung-10000, Arpit's Mac, warm cache — **G1** nothing
changed · **G2** one file changed · **G3** full ingest from no index.

**Records it will touch:** SR-INGEST, SR-DECODE, SR-PLUGINS (the callback seam),
SR-PII (the regex dialect), SR-RANKING (`src/fux/text/`), SR-T1-ACCELERATOR,
SR-LAW-2 (crate set), SR-LAW-4 (parallel determinism), SR-WORK-RELEASE (the
wheel matrix), and the layer map in `records/README.md`.

## References

- [`ingest-under-one-second.md`](ingest-under-one-second.md) — timings, language survey, prototype, sources.
- [W-268's compare doc](../compare/ingest-under-one-second.compare.md) — the F1/F3 rulings this reverses.
- [fancy-regex 0.19](https://docs.rs/crate/fancy-regex/0.19.0) — look-around and back-references; no worst-case guarantee for them.
- [PyO3 building and distribution](https://docs.rs/crate/pyo3/0.29.2/source/guide/src/building-and-distribution.md) — abi3, abi3t, free-threaded builds.
- [Windows on Arm runners for public repositories](https://blogs.windows.com/windowsdeveloper/2025/04/14/github-actions-now-supports-windows-on-arm-runners-for-all-public-repos/) — the Windows arm64 wheel can be built on free CI.
