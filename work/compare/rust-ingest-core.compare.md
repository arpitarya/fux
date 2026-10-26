---
type: Compare
description: "W-305 — the ingest engine in Rust. Eight forks: R1 the order, R2/R3 what happens to the Python ingest and to a machine with no wheel, R4 which decoders go native, R5 the analyzer, R6 the consumer regex dialect, R7 the runtime build, R8 where the binaries ship. All ruled by Arpit 2026-10-26. Graduates the proposal rust-ingest-core.md; supersedes F1 of ingest-under-one-second.compare.md and confirms its F3."
---

# The ingest engine in Rust — the eight forks

> **Verdict:** **ACCEPTED — Arpit, 2026-10-26 (Cowork):** R1 = a · R2/R3 = b ·
> R4 = a · R5 = both, held equal · R6 = a · R7 = a · R8 = a. Six of eight as
> recommended; **R2/R3 against the recommendation** (Python ingest kept as the
> fallback), and R5 re-recommended in the same session because of it.

| | |
|---|---|
| **status** | **accepted 2026-10-26**; nothing built — research the same day ([proposal](../proposals/rust-ingest-core.md)) |
| **the call** | Rust is the ingest engine wherever a `fux-native` wheel imports — the whole pipeline, incremental, the runtime build included; Python's ingest stays as the fallback and the live reference, byte-identical and slower |
| **confidence** | **high** that the pipeline can be ported byte-equal on Markdown, text and JSON (deterministic inputs, a live reference to diff against); **medium** on G3 < 1 s (projected, not measured on fux); **medium** on regex equality — two engines disagree at `\b`/`\s`/`\w` edges until the ladder proves otherwise |
| **reopen-trigger** | (1) step 0 measures 10 000-file reads on the Mac at ≥ 1 s even in parallel; **or** (2) the Rust spike projects G3 ≥ 1 s from measured stages; **or** (3) a rule in fux's shipped `pii.toml`, `identifiers.toml` or `refusals.toml` that `fancy-regex` cannot match exactly as Python `re` does on the ladder; **or** (4) keeping the Python engine byte-equal costs a release, or forces a Rust change that makes Rust slower; **or** (5) a decoder package other than JSON grows past a third of a real consumer's corpus |

## The rulings

| # | question | ruled | what it means |
|---|---|---|---|
| R1 | Incremental in Python first? | **a — straight to Rust** | the stat cache and carry-forward are built into the Rust pipeline; W-268's F1 = S1 is superseded |
| R2/R3 | The Python ingest; a machine with no wheel | **b — kept as fallback** | P1 stands: no wheel → today's Python engine, byte-identical, slower; `fux doctor` names the engine; two engines held equal by a differential test for as long as both exist |
| R4 | Native decoders | **a — text formats + JSON** | pdf, sheet, office, html, svg, image, mail, config and `.fux/decoders/*.py` are called back into Python |
| R5 | Analyzer | **both, held equal** | Rust's where a wheel exists (ingest and query), Python's kept for the fallback, a differential test between them; Node keeps its twin and parity test |
| R6 | Consumer regexes | **a — `fancy-regex` where needed** | `regex` for linear-time rules, `fancy-regex` for look-around and back-references; `fux doctor` refuses a rule neither compiles; no consumer file changes |
| R7 | `.fux/runtime/` build | **a — in Rust** | Node's builder and Python's are kept and held equal |
| R8 | Packaging | **a — new `fux-native`** | the only platform-wheel distribution; `fux-core`, `fux-reader`, `fux-writer`, `fux-engine` stay pure Python. Needs Arpit's PyPI trusted publisher for the new name before its first publish |

## Consequences

- **Three ingest-side copies of the analyzer** (Rust, Python, Node) and two
  ingest engines — the cost of R2 = b, named at the ruling. The differential
  harness (step 1) is permanent, not a migration aid.
- **Records** (through the build items): SR-INGEST, SR-DECODE, SR-PLUGINS,
  SR-PII (decision on the dialect), SR-RANKING, SR-T1-ACCELERATOR, SR-LAW-2 (the
  crate set), SR-LAW-4 (shard-partitioned determinism), SR-WORK-RELEASE (the
  wheel matrix), the layer map.
- **Steps:** 0 measure (Sonnet) → 1 differential harness (Sonnet) → 2 Rust
  spike (Opus) → 3 crate + wheels (Opus) → 4 full pipeline (Opus) → 5 runtime +
  query analyzer (Opus) → 6 Rust becomes the default (Opus); each a W-item with
  its bar named before it runs.

## References

- [the proposal](../proposals/rust-ingest-core.md) — the map, the hazards, the sources.
- [ingest-under-one-second](ingest-under-one-second.compare.md) — the clock (G1–G3) and the F2 ruling this keeps.

## Reopen-trigger

In the verdict table above.
