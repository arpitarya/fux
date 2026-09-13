---
type: Report
description: "The first benchmark run that files all seven captures SR-WORK-BENCHMARK requires — built to prove the harness, on one corpus tier, with a planted key derived from the generator's own construction rules."
run: 2026-09-13-benchmark-captures
item: W-150
classification: informed
engine: fux-engine 2.0.0-alpha.7 (arm B) against 1.0.0 (arm A)
filed: 2026-09-13
---

# Benchmark captures — the harness run that proves the harness

**This run exists to make [SR-WORK-BENCHMARK](../../../records/0053_WORK-benchmark.md)
runnable.** On 2026-09-13 the record was accepted and the harness produced **two
of its seven captures**; CAP-3 and CAP-4 were not merely missing but
*impossible*, because the benchmark corpora carried no key.

**All seven are filed here.** `tests/test_benchmark_capture.py` passes against
this directory.

---

## 1. Scope — one tier, and that is deliberate

🔴 **`docs-00100` only.** This is a **harness-validation run**, not a version
comparison, and stretching it across all seven tiers would have produced six
more tiers of numbers nobody had asked a question about. The harness is the
deliverable; the numbers below are a by-product and are reported because a run
that files evidence it will not discuss is worse than one that discusses it.

**Both arms, as [SR-WORK-ENVIRONMENTS](../../../records/0052_WORK-environments.md)
requires:** `fux-engine 1.0.0` (arm A, the newest previous major) against
`2.0.0-alpha.7` (arm B, the current build, editable install).

⚠ **Arm B is an EDITABLE install of a dirty working tree.** It carries this
session's W-151/W-152/W-153 changes, which are not committed. A rerun after
those land will not reproduce these bytes exactly.

## 2. Authorship and classification — `informed`, and the reason is structural

**`informed`** ([SR-RS](../../../records/0133_predictions.md) decisions 11-15).
The judged questions and their relevance key were authored **in this session**,
by the same author who then read the results.

| artifact | author | could reach the queries? | could reach the key? |
|---|---|---|---|
| the corpus (`_pool`, unchanged) | an earlier session, 2026-09-12 | no | it predates the key |
| the query set `queries.jsonl` | an earlier session | — | there was no key |
| **`judged.jsonl` + `key.jsonl`** | **Claude, this session** | wrote them | wrote them |
| the harness verbs | Claude, this session | yes | yes |
| this report | Claude, this session | yes | yes |

🔴 **So no delta here may be compared with a blind run, and none is claimed.**
It is not an upper bound either — that would assert a bounded magnitude a leak
does not have. **Not a generalisation estimate.**

⚠ **What weakens the `informed` label, and it is worth stating:** the key is not
a judgement anybody made. It is **read off the generator's construction rules**
(`bin/judged.py`) — document `i` has domain `DOMAINS[i % 10]`, subject
`SUBJECTS[(i // 10) % 20]`, and a unique reference token — and the author chose
*which* structural facts to ask about, not *which document is the answer*. That
is a smaller exposure than writing an answer key, and it is still an exposure.

## 3. The planted key — how it is planted, and what it does not touch

**Nothing from `work/golden/` enters this environment**
([`work/golden/README.md`](../../golden/README.md)), and no document was read to
build the key.

- **`judged.jsonl` + `key.jsonl` sit beside `queries.jsonl`** in each corpus
  tier. 52 questions: **42 judged** in five classes and **10 planted
  unanswerable**.
- 🔴 **`corpus_sha256` did not move.** `gen_corpus.py --keys` writes the two
  files into the tiers that already exist and re-checks the corpus hash
  afterwards rather than asserting it. **Every timing filed against these
  corpora before today is still comparable**, and no corpus was regenerated —
  which is the standing rule for this environment.
- **The timing set is untouched.** `queries.py` draws its words from vocabulary
  the generator scatters *randomly inside* each document, so no key can be
  planted for it without re-reading the corpus. It stays a timing set; the
  judged set is its own file and says so.
- **The unanswerables are absent by construction, not by inspection:** a
  reference token beyond the pool's last document, a volume number beyond it,
  and a `<domain> <word> handbook` whose word is **not in the generator's source
  file at all**. The generator can only write words it contains literally, so a
  word missing from `gen_corpus.py` is missing from every document it will ever
  produce.

## 4. What the captures say

**CAP-3 — `hit@k`, 42 judged questions, scan path.**

| arm | version | hit@1 | hit@5 | hit@10 | hit@20 | hit@50 |
|---|---|---:|---:|---:|---:|---:|
| A | 1.0.0 | 0.833 | 0.952 | 1.000 | 1.000 | 1.000 |
| B | 2.0.0-alpha.7 | 0.833 | **0.976** | 1.000 | 1.000 | 1.000 |

- **The whole difference is one query, in the `title` class** (0.75 → 0.88 at
  hit@5). **A net of 1 against [SR-RS](../../../records/0133_predictions.md)
  decision 19's floor of 6.** That is **no detected change**, and a benchmark
  rules nothing in any case (SR-WORK-BENCHMARK decision 6).
- 🔴 **Headroom, stated in BOTH directions** (SR-RS decision 22b), because one
  number answers neither question. **Improvement headroom** is the questions
  wrong in *both* arms — the most that could have been fixed. **Regression
  headroom** is the questions right in both — the most that could have broken.

  | k | n | improvement headroom | regression headroom | `b` (A wrong → B right) | `c` (A right → B wrong) |
  |---:|---:|---:|---:|---:|---:|
  | 1 | 42 | 7 | 35 | 0 | 0 |
  | 5 | 42 | **1** | 40 | **1** | 0 |
  | 10 | 42 | **0** | 42 | 0 | 0 |

  **The `+1` at `hit@5` consumed the entire improvement headroom**, and at
  `hit@10` there is none at all — no delta is representable in that direction,
  so a run reporting `hit@10 1.000 vs 1.000` as agreement would be reporting a
  ceiling. ⚠ **Only `hit@1` has real headroom in both directions**, and there
  the two arms are identical.
- **`needle`, `volume`, `rare+domain` and `domain` are 1.000 at every k on both
  arms.** Those four classes discriminate nothing here and are kept because a
  ceiling that stops being a ceiling is the signal worth having.
- ⚠ **`title` at hit@1 is 0.12 on both arms**, and it is the one class with
  headroom. The query is a document's own title (`freight manifest handbook`)
  and neither version puts that document first. **That is a finding about the
  corpus as much as about the ranking** — 100 documents share ten domains, so
  `freight` alone selects ten of them — and this run does not adjudicate it.

**CAP-4 — the answer layer. 🔴 The result worth carrying out of this run.**

| arm | answered | declined | fabricated |
|---|---:|---:|---:|
| A 1.0.0 | 42 | 0 | **10** |
| B 2.0.0-alpha.7 | 42 | 0 | **10** |

**Every planted unanswerable was answered, by both versions, with a citation.**
And arm B **named the missing term while doing it**:

| question | band | `answerable` | coverage | `missing` |
|---|---|---|---:|---|
| `freight thermocline handbook` | `partial` | **`true`** | 0.2994 | `["thermocline"]` |
| `volume 10014` | `partial` | **`true`** | **0.0009** | `["10014"]` |

- 🔴 **The engine knew and said so, and still said `answerable: true`.** At
  `coverage: 0.0009` essentially nothing matched. This is the **fourth** recorded
  occurrence of the abstention shape (20/20 twice, 0/124 on five golden rungs,
  now 10/10 here) and the **first with an instrument that names the absent
  term**, which is what makes it actionable rather than another tally.
- ⚠ **It is not adjudicated here.** *Does `weak` imply `answerable: false`?* is
  an open question in [`work/BLOCKED.json`](../../BLOCKED.json) and is Arpit's.
  A benchmark reports; a person judges.
- ⚠ **Arm A has no `--band` flag**, so its rows carry no `confidence`. Its ten
  fabrications are read off `answer` being non-null alone. Stated, not smoothed.

**CAP-2 — what moved.** 29 of 60 timing queries have a different top-10 between
the two versions; 7 documents entered B's top-10 and 7 left. Per-document rows
with the rank delta are in `evidence/rankdiff.jsonl`.

**CAP-5 — committed index size.** A 1.41 MB against B 1.34 MB on 100 documents
(14 076 vs 13 360 bytes/document, 84 shards each) — **B's index is 5.1 %
smaller** for the same corpus.

**CAP-6 — speed.** A 51.3 ms median-of-medians against B 72.6 ms (p95 52.3 vs
74.3); ingest 3.9 s vs 1.8 s, build 0.14 s vs 0.19 s.

🔴 **The latency numbers are the least trustworthy thing in this run and must
not be quoted.** Another session was working on this machine throughout, which is
the failure mode [SETUP-BENCHMARK](../../setup/fux-benchmark.md) standing rule 0a
records: **a loaded machine does not produce noise, it produces a clean,
localised anomaly that reads like a finding.** Interleaving A B A B protects the
*difference* and never the absolute number. **The ranked lists, `hit@k` and the
answer verdicts are deterministic and are unaffected.**

## 5. The null control

`nullcontrol` ran first, as it always does: arm A twice on `docs-00100` returned
**identical ranked lists on every query**. A difference there voids every number
in a session.

## 6. What this run does NOT do

- **It rules no threshold.** SR-WORK-BENCHMARK decision 6, and there is no
  pass/fail anywhere in the harness or in `benchmark.html`.
- **It does not compare quality across versions in any load-bearing way.** One
  tier, one machine, an `informed` key, and a net of 1.
- **It does not cover the other six tiers.** A full sweep is a separate run with
  its own id, and it should be taken on a quiet machine.
