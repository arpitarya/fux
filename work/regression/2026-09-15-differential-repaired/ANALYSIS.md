---
type: Analysis
run: 2026-09-15-differential-repaired
description: "One assumption, three failures, and the gate that now holds it — plus the part that is still a person's job."
filed: 2026-09-15
---

# ANALYSIS — one assumption, three failures

## 1 · The diagnosis

**Every file under a source directory is text.** That is the assumption, and it
was written twice: once as `.decode("utf-8")` and once as
`.decode("utf-8", errors="replace")`. `walk_sources` yields **every** file under
a configured directory — the ones no decoder claims and ingest skips included —
so the assumption was false the day a PNG landed in `docs/`.

**Why nothing noticed.** `tools/differential/` had no importer. The register's
own ownership row said so — *"⚠ No test imports it, so it can break silently —
and has"* — and the sentence was written before this, about a different break.
The unit-suite arm exercises `compare()` over synthetic corpora it builds
itself, which is a real test of the differential law and no test at all of the
harness that runs it over a repository.

**And the third defect is a different class.** `archived_weight` was removed from
the engine on 2026-09-13 by W-152. The harness kept passing it. Nothing in the
repository connects a removed parameter to the tools that used it, and the
harness's own dead state is what hid the consequence.

## 2 · The changes, each with a repro

| # | change | repro |
|---|---|---|
| 1 | `vocabulary` skips a file it cannot decode and **counts and names** what it skipped; `run.py` prints it | `python tools/differential/run.py --root . --tops 5 --skipping off` |
| 2 | `bench_r3.source_vocabulary` routes through the same helper — one decision about what text is | `pytest tests/derive/test_differential_harness.py::test_the_bench_arm_walks_sources_the_same_way` |
| 3 | the weight sweep rides `[priority]`, with `--priority-prefix` | `python tools/differential/run.py --root . --tops 1` |
| 4 | **the gate** — the decode assumption and the shape of the weight sweep, held by a test that imports the harness | `pytest tests/derive/test_differential_harness.py` |

**Gate 4 is [SR-WORK-SESSION](../../../records/0060_WORK-session.md) decision
13's two-strike rule discharged**: the same assumption failed twice, so it
becomes a mechanical check in the change that records the second occurrence.

## 3 · Decided, and stated in the docstring: this walks SOURCES, not INGEST

W-184's definition of done asked whether the query set should be generated from
what ingest keeps rather than from what the directory holds. **It keeps walking
the sources**, and the reason is the harness's own subject: the two sides have
to agree on a **miss** exactly as they agree on a hit, and a term that names no
indexed document is one of the cheapest ways to make them disagree. The
docstring says so, because the two sets are genuinely different and the
difference is the point.

## 4 · Unresolved

🔴 **The real-corpus arm is still something a person has to run.** The new test
holds the assumptions; it does not run 22 144 comparisons, because that is a
fourteen-minute job and the unit suite is not where it belongs. **The two days
this harness spent dead are what that costs**, and nothing in this change
reduces it.

⚠ **No CI arm is proposed here.** That is a scheduling decision with a cost, and
it belongs to whoever owns the CI budget rather than to the session that found
the bug.
