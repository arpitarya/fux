"""A benchmark run captures all seven things, or it is not a benchmark run.

[SR-WORK-BENCHMARK](../records/0053_WORK-benchmark.md) is the home of the
capture set (Arpit, 2026-09-13): the ranked lists, what moved between the two
arms, `hit@k` at 1/5/10/20/50, the answer layer with its planted unanswerables,
the committed index size, the speed, and an HTML report. This module is that
record's enforcement -- a `kind: process` record owns its enforcing test.

**Why a file-existence check and not a content one.** The captures are produced
by a harness that lives outside this repo (`fux-benchmark`, per
SR-WORK-ENVIRONMENTS), so what this repo can assert is what was *filed*: that
every capture arrived, at the path the record names. Whether a row is *correct*
is the reader's judgement, exactly as SR-LAW-0 leaves coherence.

**The baseline is not an exemption.** Runs filed before `CAPTURE_SINCE` were
written under plans that chose their own metrics, and their reports are frozen.
Turning a rule on by editing the evidence it governs is the failure the rule is
about -- the same discipline `CLASSIFY_SINCE` uses in
`tests/test_regression_runs.py`.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REGRESSION = ROOT / "work" / "regression"
RECORD = ROOT / "records" / "0053_WORK-benchmark.md"

# SR-WORK-BENCHMARK, ruled by Arpit 2026-09-13. A run directory is dated by its
# own name, which is what makes the baseline checkable without reading a report.
CAPTURE_SINCE = "2026-09-13"

# The six evidence captures, CAP-1 .. CAP-6, at the paths decision 7 names.
REQUIRED_EVIDENCE = {
    "ranked-lists.jsonl": "CAP-1 the ranked list each arm returned, per query",
    "rankdiff.jsonl": "CAP-2 what entered, what left, and the per-document rank delta",
    "hits.jsonl": "CAP-3 hit@1,5,10,20,50 per query per arm",
    "answers.jsonl": "CAP-4 answered|declined, and fabricated on the planted unanswerables",
    "index-size.csv": "CAP-5 committed bytes, bytes/doc, shard count",
    "latency.csv": "CAP-6 query p50/p95 interleaved, ingest and build wall-clock",
}

CAP_IDS = [f"CAP-{n}" for n in range(1, 8)]


def is_benchmark_run(run: Path) -> bool:
    """A filed benchmark run: a dated directory whose name says `benchmark`.

    Naming is the only signal available before the evidence is read, and it is
    the signal every filed run has used so far (`2026-09-12-benchmark-l9`).
    """
    return "bench" in run.name.lower()


def runs() -> list[Path]:
    if not REGRESSION.is_dir():
        return []
    return sorted(
        p for p in REGRESSION.iterdir() if p.is_dir() and is_benchmark_run(p) and p.name[:10] >= CAPTURE_SINCE
    )


def _missing(run: Path) -> list[str]:
    evidence = run / "evidence"
    missing = [f"{name} -- {why}" for name, why in REQUIRED_EVIDENCE.items() if not (evidence / name).is_file()]
    if not list(run.glob("*.html")):
        missing.append("*.html -- CAP-7 the HTML report, generated every run")
    return missing


@pytest.mark.parametrize("run", runs(), ids=lambda p: p.name)
def test_benchmark_run_files_every_capture(run: Path) -> None:
    missing = _missing(run)
    assert not missing, (
        f"{run.name} is filed as a benchmark and is missing:\n  " + "\n  ".join(missing) + "\n"
        "SR-WORK-BENCHMARK: all seven captures, or it is not filed as a benchmark run."
    )


def test_the_record_still_names_the_seven_captures() -> None:
    """The test and the record drift apart silently; this is what notices."""
    text = RECORD.read_text(encoding="utf-8")
    absent = [cap for cap in CAP_IDS if cap not in text]
    assert not absent, f"SR-WORK-BENCHMARK no longer names {absent} -- amend the record and this module together"
    for name in REQUIRED_EVIDENCE:
        assert name in text, f"SR-WORK-BENCHMARK decision 7 no longer names `{name}`"


def test_the_baseline_is_the_one_the_record_states() -> None:
    text = RECORD.read_text(encoding="utf-8")
    assert CAPTURE_SINCE in text, "the record must state the baseline this module enforces"


def _make_run(root: Path, name: str, *, complete: bool, html: bool = True) -> Path:
    run = root / name
    (run / "evidence").mkdir(parents=True)
    names = list(REQUIRED_EVIDENCE) if complete else list(REQUIRED_EVIDENCE)[:-1]
    for f in names:
        (run / "evidence" / f).write_text("", encoding="utf-8")
    if html:
        (run / "benchmark.html").write_text("<!doctype html>", encoding="utf-8")
    return run


def test_a_complete_run_passes(tmp_path: Path) -> None:
    assert _missing(_make_run(tmp_path, "2026-09-20-benchmark-x", complete=True)) == []


def test_a_run_missing_one_capture_fails(tmp_path: Path) -> None:
    missing = _missing(_make_run(tmp_path, "2026-09-20-benchmark-x", complete=False))
    assert len(missing) == 1 and missing[0].startswith("latency.csv")


def test_a_run_with_no_html_report_fails(tmp_path: Path) -> None:
    missing = _missing(_make_run(tmp_path, "2026-09-20-benchmark-x", complete=True, html=False))
    assert missing == ["*.html -- CAP-7 the HTML report, generated every run"]


@pytest.mark.parametrize(
    ("name", "in_scope"),
    [
        ("2026-09-12-benchmark-l9", False),
        ("2026-08-28-benchmark-v1-vs-head", False),
        ("2026-09-13-benchmark-quiet", True),
        ("2027-01-01-benchmark-anything", True),
        ("2026-09-20-golden-ladder", False),
    ],
)
def test_scope_is_dated_benchmark_runs_only(name: str, in_scope: bool) -> None:
    dated = re.match(r"^\d{4}-\d{2}-\d{2}-", name) is not None
    assert dated
    assert (is_benchmark_run(Path(name)) and name[:10] >= CAPTURE_SINCE) is in_scope
