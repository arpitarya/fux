# 2026-08-22 — graph-acceptance: the three re-scoped phenomena, on a new corpus

**What this is, and what it is not.** W-57's original target was
fux-playground's ~50 hand-written goldens, which were never rebuilt after the
2026-08-20 loss and remain **not rebuilt as of this run** — that decision
stands separately (the playground's own 2026-08-22 planned-redesign note
means it may never be graded again). Rather than wait on that, this run
grades the graph lane against a **new second corpus, built in fux-lab**
(~~satisfying [W-52](../../../archive/open/W-52-df-over-the-union.md)'s "plus a
second corpus" requirement in passing~~ — **struck 2026-08-22, this claim was
wrong**: see the correction below), sized well past playground's 10 documents
so the lane is tested against real background noise, not a hand-tuned toy.

> **Correction, 2026-08-22 — the W-52 claim above is false and is struck rather
> than deleted.** `graph-acceptance` declares **one** source directory (`docs`)
> with **no `archived=true` attribute**, and **0 of its 66 records** carry
> `archived`. W-52 asks whether `df` computed over live-plus-archived distorts
> live scoring; a corpus with no archived half **cannot measure that at all**,
> so this run does nothing for W-52's second-corpus requirement, in passing or
> otherwise. The claim was written from the fact that a second corpus now
> existed, without checking that it had the one property W-52 needs. Checked
> and disproved on contact; W-52's own trigger is unchanged and still unmet.

- **Engine:** `github.com/arpitarya/fux` @ `fa3ba30` (origin/main). The
  working tree on the machine driving this session carries uncommitted
  changes on top of `fa3ba30`, but **none touch `src/fux/graph/`,
  `src/fux/ingest/edges.py`, or ranking** (verified by `git status` diff at
  measurement time) — so measuring the clean `fa3ba30` checkout is equivalent
  for this lane's purposes, and is recorded here rather than assumed.
- **Corpus:** `fux-lab/shared/generate/make_graph_corpus.py`, seed `20260822`
  — 66 documents, deterministic (two independent runs diffed byte-identical).
  Fictional company "Solace" / platform "Ridgeline" — a **different**
  fictional company from fux-playground's Calder Group / Helix, so this is a
  genuinely independent second corpus, not a re-skin.
- **Goldens:** [`evidence/goldens.jsonl`](evidence/goldens.jsonl), 24 entries,
  written from [`evidence/planted.json`](evidence/planted.json) — the
  generator's own record of what it planted, decided **before** any `fux`
  command ran against the phenomena. `fux explain`/`fux path` were run
  afterward only to confirm the corpus's markdown links actually resolved
  into `ref` edges as intended (a corpus-construction sanity check — it
  caught and fixed a real bug, relative links resolving one directory too
  deep) — not to derive what the "correct" answer should be. See
  [`ANALYSIS.md`](ANALYSIS.md) for why that distinction matters here.
- **Reproduce:** `fux-lab/graph-acceptance/setup.sh && python3 check_graph.py`
  (committed to fux-lab in the same change as this report).

---

## 1 · The three phenomena — XPASS count: 0 (of 24 goldens, 0 planted as
`known_failure`; every planted check passed on the first run)

| phenomenon | graph verb(s) checked | goldens | result |
|---|---|---|---|
| supersession | `graph` (node presence), `path` (1-hop `ref`), `explain` (edge set) | 3 pairs × 3 checks = 9 | **9/9 pass** |
| near-duplication | same three | 2 pairs × 3 checks = 6 | **6/6 pass** |
| staleness ≠ wrongness | same three | 2 pairs × 3 checks = 6 | **6/6 pass** |
| general (nopath negatives, one untagged runbook) | `path`, `explain` | 3 | **3/3 pass** |

**The gap `ask` cannot close, closed.** For every supersession pair, `fux ask`
ranks the **superseded** document above the one that replaced it (term
overlap; the new doc necessarily shares vocabulary with the old one it
argues against) — reproduced directly, e.g. `ask "what replaced queue
partitioning by hash"` returns the retired ADR first (score 17.24) and the
replacement second (15.95). `fux graph` on the same query surfaces **both**
nodes, so the superseding document is reachable even though it is not
top-ranked by term statistics. That is exactly ADR-GRAPH's claim, and this is
the first time it has been checked against anything but the tiny
`tests_e2e/eval/relational` fixture (5 documents) or the still-ungraded
playground.

## 2 · Determinism

| check | result |
|---|---|
| Corpus generator, two independent runs | byte-identical (`diff -rq`) |
| Committed index, re-`ingest` | byte-identical (`git status --porcelain .fux/index` empty after) |
| `.fux/runtime/graph.json`, two `fux build` runs, **same machine** | identical sha256 (`3ede5863…`) |
| `.fux/runtime/graph.json`, **second machine** | **not checked — only one machine was available this session** |
| `ask` untouched (`--scan` vs `--fast`, three queries) | byte-identical, as ADR-GRAPH's own consequence claims |

**The two-machine determinism check ADR-GRAPH's veto condition 1 asks for is
still open.** It was open before this run and is open after it — this run
did not have access to a second machine to check it on. Recorded as
outstanding, not silently dropped.

## 3 · What this does and does not settle

- **Settles, for this session:** veto condition 3 — the three phenomena were
  measured and **did** improve. The lane's central claim holds on this
  corpus.
- **Does not settle:** veto condition 1 (two machines) — unresolved, same as
  before.
- **Does not replace:** a graded fux-playground, if that corpus is ever
  regraded. This is a second, independent measurement, not a substitute for
  the original target.

See [`ANALYSIS.md`](ANALYSIS.md) for the methodology caveat on who wrote the
goldens.

---

## Addendum — 2026-08-22, the second machine

**Appended, not merged into §2 above.** §2's determinism table still reads
*"not checked — only one machine was available this session"*, because that is
what was true when the run was filed. A filed run is superseded by a newer
measurement, never rewritten to look better — the same discipline the M2
accelerator report's annotated Reproduce block and R6-MERGE's appended
adjudication follow.

**The check ADR-GRAPH veto condition 1 asks for has now run, on a second
machine, and passed.**

| machine | architecture | `shasum -a 256 .fux/runtime/graph.json` |
|---|---|---|
| cloud sandbox (this run) | x86-64 Linux | `3ede58638eca67857fd9919e21632c8ce0964b3c6ce273de73d11daf1ca30a53` |
| Arpit's own machine | arm64 macOS | `3ede58638eca67857fd9919e21632c8ce0964b3c6ce273de73d11daf1ca30a53` |

Identical across all 64 hex characters, from **independent `setup.sh` runs** —
each generated the 66-document corpus from the seeded generator, ingested, and
built the accelerator from scratch. The second machine also reproduced the
corpus itself (66 documents, 433 terms, 3 696 postings) before hashing.

**This is a stronger result than the condition required.** Veto 1 was written
to catch set-iteration order and unseeded randomness, neither of which two runs
on one machine can see. A match across **two architectures** additionally rules
out float-width and byte-order dependence in the label propagation.

**Repro:** `cd ~/my_programs/fux-lab/graph-acceptance && ./setup.sh && shasum -a 256 .fux/runtime/graph.json`

**A defect was suspected while reading the run's output and then disproved, which
is recorded here because the first version of this addendum asserted it.** The
generator prints `wrote planted-phenomena manifest:
.../graph-acceptance/../shared/generate/planted.json`, which reads as though the
environment's own manifest is never refreshed. It is: `write_corpus()` writes the
canonical copy next to the generator and `__main__` then copies it into the
environment, and both files on disk were rewritten by this run at the same second
and are byte-identical (`diff -q`, checked).

**What is real is only that the print statement names the source path rather than
the destination**, which is cosmetic. **No defect is filed.** The lesson is the
repo's own — a status claim gets checked against the filesystem before it is
written down, not inferred from a log line.
