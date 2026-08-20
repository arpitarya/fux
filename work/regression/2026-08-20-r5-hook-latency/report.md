# 2026-08-20 — R5: what a hook-driven commit costs

**A measurement against a pre-registered threshold.** The threshold, the judged
corpus size, the arms and the statistic were frozen in
[`tools/maintenance-bench/PRE-REGISTRATION.md`](../../../tools/maintenance-bench/PRE-REGISTRATION.md)
§2 and committed **before** this harness produced a number (`d98874d`). The
ruling is [`VERDICT.md`](VERDICT.md).

This run also measured **R6**, whose ruling is filed separately at
[`../2026-08-20-r6-merge-driver/`](../2026-08-20-r6-merge-driver/report.md) —
one verdict per prediction, sharing one harness and one raw report.

- **Engine:** the working tree at `d98874d` (dirty — the harness was
  uncommitted while it ran). `src/` last changed in `3a9aabc`, before this run
  and before R4's, so all three measurements describe the same engine.
- **Surface:** Darwin 25.3.0 arm64, Python 3.14.2. Latency is **not comparable
  across machines** (fux-lab TEST-PLAN §2).
- **Reproduce:** [`evidence/reproduce.sh`](evidence/reproduce.sh) — offline,
  ~30 min; the 100 000-document corpus is the long pole.
- **Raw:** [`evidence/report.json`](evidence/report.json) ·
  [`evidence/attribution.json`](evidence/attribution.json) ·
  [`evidence/run.log`](evidence/run.log)

---

## 1 · The numbers

What is timed is **`git commit` itself**, on a repository whose `post-commit`
hook was installed by `fux hooks --install` — so git's own work, the hook's
process spawn, the interpreter start, the ingest and the derived build are all
inside it. Five commits per row after a discarded warm-up; judged on the
maximum, median beside it.

| corpus | arm | median | **max** | vs the 1 s bound |
|---|---|---|---|---|
| 1 000 | `edit` | 0.647 s | **0.651 s** | **passes** |
| 10 000 | `edit` | 3.298 s | **3.523 s** | 3.5× over |
| **100 000** | **`edit`** | **43.167 s** | **44.380 s** | **44× over — judged** |
| 1 000 | `add` | 0.686 s | 0.700 s | *(unjudged)* |
| 10 000 | `add` | 3.444 s | 3.477 s | *(unjudged)* |
| 100 000 | `add` | 44.339 s | 46.490 s | *(unjudged)* |

**Verdict: FAIL at the judged size.** See [`VERDICT.md`](VERDICT.md).

Spread is tight — the five samples at 100 000 span 41.9 s to 44.4 s — so this
is not a noisy result sitting near a boundary. It is 44× over.

## 2 · The shape: cost tracks the corpus, not the commit

| corpus | ×10 growth | measured growth |
|---|---|---|
| 1 000 → 10 000 | 10× | **5.4×** |
| 10 000 → 100 000 | 10× | **12.6×** |

Roughly linear in corpus size, with the second decade slightly superlinear.
The commit is twenty documents in every row.

**So the finding, stated plainly: a 20-document commit costs whatever touching
the whole corpus costs.** Delta ingest ([ADR-INGEST](../../../docs/adr/0007_ingest.md)
decision 1b) already removed the expensive per-document work — extraction is
carried forward for an unchanged `sha` — and what remains is a set of passes
that must each visit everything.

The `add` arm confirms it from the other side. Adding twenty documents changes
the corpus id set, which is the more expensive case, and it costs **within 5 %
of editing twenty** at every size. If per-document work dominated, that gap
would be large.

## 3 · Where the 44 seconds go

A separate run ([`attribute.py`](../../../tools/maintenance-bench/attribute.py))
splits the same commit into its parts, with no hook installed so nothing is
double-counted. Medians of three:

| corpus | `git` (no hook) | `ingest` (delta) | `derive` (T1 + graph) | `spawn` | sum |
|---|---|---|---|---|---|
| 1 000 | 0.183 s | 0.231 s | 0.270 s | 0.027 s | 0.711 s |
| 10 000 | 0.190 s | 1.318 s | 1.785 s | 0.026 s | 3.319 s |
| **100 000** | **0.340 s** | **21.325 s** | **19.726 s** | **0.038 s** | **41.429 s** |

Shares at the judged size: **ingest 51.5 %, derive 47.6 %, git 0.8 %, spawn
0.1 %.** The sum tracks the hook-driven commit it decomposes (41.4 s against a
43.2 s median), so nothing material is missing from the split.

**Two O(corpus) passes are the whole cost, and git is not one of them.**
Staging and committing twenty changed files out of 100 000 is essentially
constant — 0.183 s at 1 000 documents and 0.340 s at 100 000, a 1.9× rise across a 100× corpus — because git works from the index, not the tree. The
process spawn is **38 ms** and irrelevant at every size.

**The consequence matters more than the split.** The two passes are **almost exactly half each**, so there is no single hot spot
to attack, and — more decisively — **no plausible speedup on them reaches the
bound at this size.** Removing 90 % of both still leaves ~4.1 s against a 1 s
budget; the bound is only reachable if the work leaves the commit path
altogether. That is an architectural choice, not an optimisation, and it is
what [`hook-at-scale.compare.md`](../../compare/hook-at-scale.compare.md) puts
in front of Arpit.

Note also what the split says about the work already done. **Delta ingest cut
the per-document cost and this is what was left**: at 100 000 documents
`ingest` is 21.3 s *without re-extracting a single unchanged document*. The
residue is parsing every file, resolving every edge, and writing every shard —
the passes ADR-INGEST decision 1 keeps corpus-wide on purpose, because an edge
can be resolved by a document that changed elsewhere.

## 4 · What this run does not measure

- **Not a real repository.** Synthetic documents, uniform in a way real
  documentation is not. The *shape* — cost tracking the corpus — is the robust
  finding; the absolute seconds belong to this surface.
- **Not the merge driver.** That is R6, filed separately.
- **Not `--no-accelerator`.** The hook builds the derived plane because `ask`
  should never pay for a build; whether that belongs on the commit path is
  precisely the decision this run hands over.
- **Not concurrent commits, rebases, or `git commit --amend`.**
