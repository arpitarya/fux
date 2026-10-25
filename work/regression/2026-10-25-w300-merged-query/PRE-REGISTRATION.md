---
type: Pre-registration
name: W-300-MERGED-QUERY
item: W-300
filed: 2026-10-25
filed_by: "Claude Code (Opus 5.5), the session building W-300"
law: L13, defaults
classification: informed
---

# PRE-REGISTRATION — W-300: one query over the repository and every pinned package

**Frozen before any number exists**, in the commit that adds only this file, the
question set and the consumer corpus. The question set and corpus hashes are
below; nothing here is edited after the first measurement
([SR-RS](../../../records/0133_predictions.md) decision 10b).

**The bar is [L13](../../../records/0015_LAW-13-the-standing-bar.md)'s, with its
defaults** (decisions 2–4). This file fills in parameters only; it restates
nothing and loosens nothing.

## The change

W-300 makes `fux ask` and `fux_search` rank the repository **and** every pinned
index package under ONE `rank()` call, `df` / `n` / `total_flen` summed,
`scope` = `repo` · `packages` · `all` (default `all`). With no pin, or at
`scope = repo`, the engine is meant to be unchanged byte for byte.

## Data

- **Package**: `tests/fixtures/pkg-index/docs/` (3 documents — `configuration.md`,
  `glossary.md`, `rollback.md`), ingested, packed as a segment and pinned as
  `acme-docs-index` exactly as `tests/test_pkg_merged_query.py` does.
- **Consumer repository**: `evidence/corpus/docs/` (6 documents written for this
  run, sharing the package's vocabulary — *widget*, *broker*, *customer*,
  *retried* — so that merged statistics and package hits can displace a
  repository answer).
- **Questions**: `evidence/questions.tsv` — 30 questions, each with one expected
  document. **16 slice** (`slice = package`: the answer is a package document),
  **14 outside the slice** (`slice = repo`: the answer is a consumer document).
  A fresh set: no mechanism has been decided on it (L13 decision 5).

| file | sha256 |
|---|---|
| `evidence/questions.tsv` | `79ff1066be656ae9f45e058c4b3fa6bce96e1aebee96c36570af2d3f0a7ca401` |
| `evidence/corpus/docs/billing.md` | `0d712b409f811bf8a4aceccaf45bb7c76e0e844dc08180d6ea2864d0429e2c23` |
| `evidence/corpus/docs/broker.md` | `af235ad1b29002bc831e893c4476a785f76bd965a0ba8a8c11b404836e92e7e1` |
| `evidence/corpus/docs/deploy.md` | `b2709da433f8532e3849e9fbc2c7081576873075137d56978e28f053e628b681` |
| `evidence/corpus/docs/incidents.md` | `db07e750534e51ad17d9728fa2f1856d3fda4dee5efcccf46f53e5a90de0c980` |
| `evidence/corpus/docs/oncall.md` | `1a2fa3491522b22c13f8c0c2a32b8f6513dd4262554bbd4803e2d053e3aeb7e1` |
| `evidence/corpus/docs/secrets.md` | `2567e6c894529e3a00897d3f3a32acf1d49d876cdd82965fccb0379e7d01dc02` |

Hashed 2026-10-25 16:26:48 UTC.

## Arms

- **Baseline**: `scope = repo` — the repository alone, which is what every
  consumer got before W-300.
- **Decided arm (named now, before any number)**: `scope = all`, the shipped
  default.
- **Reported only**: `scope = packages`; the Node reader at `scope = all`.

All arms: `run_query(..., force_scan=True, use_tune=True)` at `top = 10`, the
shipped `tune.toml`, `identifiers.toml` and `output.toml`.

## Parameters (L13 decision 2's right-hand column)

| row | this run |
|---|---|
| **G** | **G0a** — a consumer with NO pin: `ask --json` (`build_ask(...).payload()`) and `fux_search` (`mcp._search`) byte-identical between this engine and the pre-W-300 engine (`main` @ `9688d479`), all 30 questions. **G0b** — the pinned consumer at `scope = repo` byte-identical to G0a's pre-W-300 output. **G0c** — this repository's own committed index (no pin): `ask --json` byte-identical between the two engines, all 30 questions. **G-Node** — the decided arm in Node equals Python: ids, `package` and order exactly, scores at `round(9)` (SR-NODE-SEARCH d1). Size bar: n/a — the change adds no committed byte |
| **C1 · helps** | slice = `slice = package` (16); endpoint **`hit@1`** — the expected document (id **and** package) ranked first, because a package answer that arrives below a repository document is still the reader's second read; paired against baseline by `tools/quality-controls/verdict.py::rule(b = wins, c = losses)`; holds when `outcome == "b"` |
| **C2** | outside the slice (14 questions): `losses − wins ≤ max(2, floor(0.03 × 14)) = 2` |
| **C3** | whole-set paired net on `hit@1` > 0 |
| **GR** | `hit@5` (whole set) falls by at most 1; the count of `grounded` bands falls by at most 2. ⚠ **Not measurable here, stated now:** `section@1` (no scorer runs; no answer key exists for this set) and `ask` latency on `rung-10000` (no package-bearing ladder rung exists) |
| **slice floor** | the baseline's count of slice questions the change can win: every slice question the baseline misses at `hit@1`. Must be **≥ 15** or the run STOPS before an arm is read |

## How the outcome is filed — decided now

1. A failed gate or a slice below 15 → **STOP**, filed `VOID` (a build or data
   defect, never a verdict).
2. Otherwise L13 decision 4's table is read on the numbers.
3. 🔴 **A table reading of PASS is filed `INCONCLUSIVE` → Arpit**, because this
   run cannot meet three things the bar assumes, all known before measuring:
   - [SR-RS](../../../records/0133_predictions.md) decision 6 — the session that
     built W-300 wrote the questions, captured the arms and computed the
     reading; it may not adjudicate its own measurement;
   - G over **golden** rows (L13 decision 2) — this session has no golden corpus
     and may not run the scorer (L11); G0a–c stand in for it;
   - the latency guardrail and `section@1`, above.
   A table reading of FAIL is filed `FAIL`; an INCONCLUSIVE reading is filed
   `INCONCLUSIVE`.
4. `classification: informed` — the builder authored the questions, the
   expected documents and the consumer corpus with the code in hand.

**No threshold above moves after the first number.** If a number lands between
rows of the table, it goes to Arpit as INCONCLUSIVE ([SR-RS](../../../records/0133_predictions.md)
decision 6).
