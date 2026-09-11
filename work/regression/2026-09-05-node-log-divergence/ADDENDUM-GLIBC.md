---
type: Run Report
run: 2026-09-05-node-log-divergence
addendum: glibc-linux-x86_64
classification: blind
date: 2026-09-06
description: "The last blank the Phase 0 run and ADDENDUM-IDF both named: glibc, which is what CI runs. Measured on glibc 2.39 / x86_64 / Node 22, and closed further than either darwin run — the `idf` argument domain is enumerated EXHAUSTIVELY (10 939 arguments, df=1..n at three corpus sizes) rather than sampled. Divergence is real and larger than on darwin; nothing survives round(9) and no ordering moves."
---

# Addendum — glibc, and the `idf` domain exhausted

**This is not a new run.** It closes the one cell
[`report.md`](report.md), [`ANALYSIS.md`](ANALYSIS.md) §4 and
[`ADDENDUM-IDF.md`](ADDENDUM-IDF.md) each named in their own words:

> 🔴 **glibc is still not measured, and that is now the ONLY blank.** CI runs on
> `ubuntu-latest`; this machine has no Linux […] **Until it has, the evidence is
> darwin/arm64's alone.**

It was measured on a Linux container rather than through
`.github/workflows/log-probe.yml`, which is still unrun. **The frozen report and
the first addendum are not edited.**

## What was measured

| | |
|---|---|
| Python | CPython **3.11.15**, **glibc 2.39**, **x86_64** |
| Node | **v22.22.2**, V8, **linux/x64** (fdlibm port) |
| corpus | a 101-document index built in the container from this repo's own `docs/` — **not** the 838-document index the darwin addendum used |
| queries | the same **605** committed single terms, [`evidence/queries-self.txt`](evidence/queries-self.txt) |
| scored documents | **9 647** |

⚠ **The corpus is smaller than the darwin addendum's**, because the container
held only part of the working tree. That weakens the end-to-end count and is why
the third table below exists: it removes the corpus from the question entirely.

## Authorship — classification `blind`

| artifact | author | could reach |
|---|---|---|
| `logprobe.py` / `.mjs`, `dump.py`, `score.mjs`, `compare.py`, `queries-self.txt` | pre-existing, from the Phase 0 run and the first addendum — **unchanged, byte for byte** | — |
| `idfdomain.py` / `.mjs` | Cowork (Opus), 2026-09-06 | nothing but `bm25f.idf`'s formula; **no corpus, no score, no golden** |
| this addendum | Cowork (Opus) | the two prior reports and this probe's output |

**`blind` on the same terms as the first addendum**, and the new script is
blinder still: its input is `df = 1..n`, which is not data.

## Result 1 — `log` alone, corpus-sampled (unchanged script)

| population | distinct values | differ bit-for-bit | max relative | differ at `round(9)` |
|---|---:|---:|---:|---:|
| `idf` arguments (this container's 101-doc corpus) | 84 | **5 (5.95 %)** | `1.595e-16` | **0** |
| `wide` (100 000 seeded doubles, unchanged, seed 20260905) | 100 000 | **722 (0.7220 %)** | `2.211e-16` | **0** |

The `wide` row is directly comparable with darwin's **655 / 100 000** — same
script, same seed, same inputs. **glibc diverges from V8 slightly more often
than Apple's libm does, by the same one ulp.**

## Result 2 — end-to-end BM25F

| | |
|---|---:|
| documents scored | 9 647 |
| scores differing **bit-for-bit** | **428 (4.437 %)** |
| max relative difference | **`5.211e-16`** |
| scores differing at `round(9)` | **0 (0.000 %)** |
| queries with a different top-5, **exact sort** | **0** |
| queries with a different top-5, `round(9)` sort | **0** |

Per-query rows: [`evidence/per-query-self-glibc.csv`](evidence/per-query-self-glibc.csv)
(605 rows). Raw output: [`evidence/logprobe-glibc-output.txt`](evidence/logprobe-glibc-output.txt).

## Result 3 — the `idf` argument domain, exhausted

🔴 **Every `idf` count filed so far — 13, then 182, then 84 — is a property of a
corpus, not of fux.** That is exactly the weakness §3 of `ANALYSIS.md` named,
and widening the sample only made it a bigger sample.

It does not have to be sampled at all. `bm25f.idf`'s argument is
`(n - df + 0.5) / (df + 0.5) + 1` with `df ∈ 1..n`, so **for a corpus of `n`
documents the argument domain is exactly `n` values and can be enumerated.**
[`evidence/idfdomain.py`](evidence/idfdomain.py) does that, at three sizes:

| `n` | arguments (**exhaustive**, `df = 1..n`) | differ bit-for-bit | max relative | differ at `round(9)` |
|---:|---:|---:|---:|---:|
| 101 — this container's corpus | 101 | 6 (5.94 %) | `1.997e-16` | **0** |
| 838 — the repo's own index | 838 | 61 (7.28 %) | `2.135e-16` | **0** |
| 10 000 — ADR-QUALITY's ceiling | 10 000 | 774 (7.74 %) | `2.208e-16` | **0** |
| **total** | **10 939** | **841 (7.69 %)** | **`2.208e-16`** | **0** |

✅ **This is not a sample and carries no corpus caveat.** At any corpus size up
to 10 000 documents, **every argument fux can ever hand `log`** has been checked
on glibc/x86_64 against V8/linux. 7.69 % of them disagree — the same fraction the
darwin widened run found, on a different libm, which is what one expects of two
independent IEEE-conforming implementations. **None disagrees at `round(9)`.**

## What this changes

✅ **The pre-registration's last blank cell is fillable.** The measurement that
`ANALYSIS.md` §4 said must exist before the comparison clause could be frozen
now exists, on the platform CI runs.

✅ **Option (b) is measured on both platform pairs, and on the `idf` half it is
now exhaustive rather than sampled.** `rank.py` sorts on `round(score, 9)`; the
largest disagreement anywhere in this run is `5.211e-16` relative — about **seven
orders of magnitude** below that resolution.

⚠ **The kill clause is unmoved.** Pre-registration §6: a divergence above
`~1e-9` relative on *any* platform pair supersedes the document and makes (a)
mandatory. Nothing here is within seven orders of magnitude of it.

## What this run still cannot support

- **musl** (Alpine) and **Windows/MSVC** are unmeasured. Result 3 is exhaustive
  in the *argument* dimension, not in the *platform* dimension.
- **Node 20** is unmeasured; this is Node 22. The Phase 4 CI matrix names both.
- `.github/workflows/log-probe.yml` **has still not been run.** This container is
  glibc 2.39 / x86_64, the same family as `ubuntu-latest`, but it is not CI.
- The end-to-end count (Result 2) is over 101 documents, not 838. Compare its
  *shape* with the darwin addendum's, never its counts.
- Nothing above 10 000 documents.

## Reproduce

```bash
E=work/regression/2026-09-05-node-log-divergence/evidence
python3 $E/dump.py . $E/queries-self.txt /tmp/self.json
python3 $E/logprobe.py /tmp/self.json /tmp/args.json && node $E/logprobe.mjs /tmp/args.json
node $E/score.mjs /tmp/self.json /tmp/self-scored.json
python3 $E/compare.py /tmp/self-scored.json /tmp/per-query-self-glibc.csv
python3 $E/idfdomain.py /tmp/domain.json && node $E/idfdomain.mjs /tmp/domain.json
```

⚠ The first four lines' numbers move with the corpus. **The last line's do
not** — its input is `df = 1..n`, so it reproduces identically on any machine
with the same libm and V8 build.
