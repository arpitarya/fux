---
type: Compare
description: "W-268 — ingest of 10 000 documents in under one second. Three forks: F1 the order (incremental Python first then a Rust core · Rust now · incremental only), F2 the native language (Rust + PyO3 · C++ · mypyc/Cython · Go · Zig · Mojo), F3 what a machine with no pre-built wheel gets (the Python engine as fallback · wheels only · source build). Arpit's direction 2026-10-10: Rust, and no consumer ever installs Rust. Graduates the proposal ingest-under-one-second.md."
---

# Ingest under one second — the order, the language, the fallback

> **Verdict:** **proposed — Arpit picks F1 and F3.** F2 carries his direction
> (2026-10-10): *"We can build it in Rust. The only catch here is I don't want
> consumer to install Rust."* Recommended: **F1 = S1** (incremental Python
> first, then a Rust core behind its own spike) · **F2 = Rust + PyO3/maturin,
> abi3 wheels** · **F3 = P1** (the Python engine stays as fallback and as the
> reference the Rust output is checked against).

| | |
|---|---|
| **status** | proposed — research done 2026-10-10 in Cowork ([proposal](../proposals/ingest-under-one-second.md)); nothing built |
| **the call** | skip unchanged documents in Python (G1/G2), then move the hot path of a full ingest into a Rust core shipped as pre-compiled wheels (G3); a machine with no wheel runs today's Python engine, byte-identical and slower |
| **confidence** | **high** that G1/G2 are reachable in Python (the 4.90 s is all unchanged-document work); **medium** on G3 < 1 s natively — projected from a prototype and engine numbers, not measured on fux; **low** on macOS per-file read cost until step 0 measures it |
| **reopen-trigger** | (1) step 0 measures opening + reading 10 000 files on the Mac at ≥ 1 s **even in parallel**, or Python start-up + import alone at ≥ 1 s; **or** (2) the Rust spike projects G3 ≥ 1 s from measured stages; **or** (3) a platform fux supports cannot be given a wheel; **or** (4) a filed run shows pure Python reaching G3 < 1 s (free-threading, a JIT) |

**The clock (same for every option):** wall clock of the `fux ingest`
**command**, start-up and accelerator build included, gen-4 rung-10000,
Arpit's Mac, warm cache. **G1** nothing changed · **G2** one file changed ·
**G3** full ingest from no index. Today: timed run 4.90 s (G1), 9.44 s (G3);
the G3 command 11.995 s ([run](../regression/2026-10-09-ingest-split-remeasure/report.md)).

## Context

- **At no change, every second is unchanged-document work.** Walk reads every
  file (0.84 s); every file is decoded and parsed (1.42 s) and redacted
  (0.96 s); every record is re-serialised and every shard compared (0.69 s);
  edges are resolved for every document and `git log` reads the whole history
  (0.86 s). The accelerator is rebuilt in full afterwards, outside the timed run.
- **Committed records do not depend on corpus-wide df or avgdl** — they hold
  per-field term counts; BM25F is computed at query time. One changed document
  touches its own record and those whose links start or stop resolving.
- **Pure Python tops out short of G3:** mypyc 1.5–5× (≈ 1.9 s best case);
  `spawn`-based processes on macOS/Windows; free-threading ≈ 2–3 s on 10 cores
  *[inference]*. Detail and sources: the proposal §3.

## F1 — the order

| option | G1 / G2 | G3 | new dependency | risk |
|---|---|---|---|---|
| **S1 — A then B** *(recommended)* | ✅ first, in Python | ✅ after a spike | none for A; a Rust core for B | lowest: each step stops on its own bar |
| S2 — B directly (rewrite ingest in Rust) | ✅ | ✅ | the Rust core at once | highest: incremental logic and the port land together; nothing measured first |
| S3 — A only | ✅ | ❌ stays ~9–12 s | none | a full ingest (first setup, upgrades) stays slow |

**Why S1:** A is needed in either world — even a native full ingest should not
re-read 10 000 unchanged files on every commit — and it is pure Python. B then
starts from a measured budget (step 0) and a spike, not a projection.

## F2 — the native language

| option | consumer installs a toolchain? | wheels on every platform | evidence | verdict |
|---|---|---|---|---|
| **Rust + PyO3/maturin, abi3** | **no** — pre-compiled wheels | macOS x64/arm64, Linux glibc+musl x64/arm64, Windows x64/arm64 ([maturin](https://www.maturin.rs/platform_support)) | pydantic-core, orjson, ruff, HF tokenizers; PyO3's own example 29.0 → 8.0 → 2.0 ms ([pyo3](https://pyo3.rs/main/parallelism.html)); `regex` crate linear-time | **Arpit's direction; recommended** |
| C++ + nanobind | no | yes, stable ABI from 3.12 ([nanobind](https://github.com/wjakob/nanobind)) | fewer Python precedents; no memory safety | viable second |
| mypyc / Cython | no | per Python version | ≤ 5× → ~1.9 s | short of G3 |
| Go (gopy) | — | no wheel story ([gopy](https://github.com/go-python/gopy)) | — | rejected |
| Zig (ziggy-pydust) | — | no releases ([pydust](https://github.com/spiraldb/ziggy-pydust)) | — | rejected |
| Mojo | — | no Windows / extension packaging story found | — | rejected for now |

**How the Rust core executes on a user's machine** (Arpit asked, 2026-10-10):
the core is compiled **on CI**, once per platform, into a native library inside
the wheel — `fux/_native.abi3.so` on macOS/Linux, `fux\_native.pyd` (a DLL) on
Windows. `pip`/`uv` picks the wheel for the machine; `import fux._native` loads
the library into the same Python process; Python calls it like a function.
**No Rust, compiler or runtime on the user's machine**, and no new `.exe` — the
`fux.exe` launcher pip creates today is unchanged. One abi3 wheel per platform
covers Python 3.12, 3.13, 3.14 and later (L7); free-threaded CPython cannot load
abi3 wheels until `abi3t` in 3.15 ([pyo3](https://pyo3.rs/main/building-and-distribution.html)).

## F3 — a machine with no pre-built wheel

| option | what that machine gets | engines maintained | L2 ("works the same on every machine") | consumer installs Rust? |
|---|---|---|---|---|
| **P1 — Python engine as fallback** *(recommended)* | today's Python ingest: **byte-identical**, slower; `fux doctor` names the engine | two — but the Python one is needed anyway as the reference every Rust result is diffed against | ✅ same capability, same bytes | never |
| P2 — wheels only, no sdist | install fails with "unsupported platform" | one | ⚠ a capability that works on one machine and not another | never |
| P3 — publish an sdist | pip builds from source | one | ✅ | ❌ **yes** — breaks Arpit's condition |

**Why P1:** the differential test (Rust ≡ Python on every rung, L4) needs the
Python engine to exist; keeping it importable costs nothing extra, and it also
covers free-threaded CPython until 3.15.

## Consequences (if S1 · Rust · P1)

- **Records:** SR-INGEST (incremental path, then the native core), SR-LAW-2
  (an SR names the crate set — all MIT/Apache), SR-LAW-4 (the shard-partitioned
  parallel design and the Rust ≡ Python test), SR-WORK-RELEASE (the wheel
  matrix on PyPI; npm unchanged — Node never ingests).
- **Kept as is:** `.fux/decoders/` stays readable Python (L10) — the core calls
  back for those files only; Python keeps the CLI and config loading; Rust reads
  the same TOML keys (L12).
- **Hazard already named:** SR-INGEST decision 17 — anchors must resolve
  source-locally; `tests/ingest/test_anchor_is_source_local.py` guards it.
- **Steps:** 0 measure (Sonnet) → 1 shape A (Opus) → 2 Rust spike (Opus) →
  3 Rust core (Opus), each a W-item with a bar named before it runs.

## References

- [the proposal](../proposals/ingest-under-one-second.md) — the per-phase table, the prototype, every source.
- [W-267's run](../regression/2026-10-09-ingest-split-remeasure/report.md).
- [maturin platforms](https://www.maturin.rs/platform_support) · [PyO3 parallelism](https://pyo3.rs/main/parallelism.html) · [PyO3 distribution](https://pyo3.rs/main/building-and-distribution.html).
- [nanobind](https://github.com/wjakob/nanobind) · [gopy](https://github.com/go-python/gopy) · [ziggy-pydust](https://github.com/spiraldb/ziggy-pydust) · [mypyc](https://mypyc.readthedocs.io/en/latest/introduction.html).

## Reopen-trigger

In the verdict table above: a measured Mac read or start-up floor at ≥ 1 s; a
Rust spike projecting G3 ≥ 1 s; a supported platform with no wheel; or pure
Python measured under 1 s for G3.
