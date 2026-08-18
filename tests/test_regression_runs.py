"""Every filed run keeps the contract its README states.

`work/regression/` is what other documents cite when they need grounding, so a
run directory that is missing its evidence, or a verdict that does not say what
it ruled against, quietly turns a citation into an assertion.

The **verdict** rules are the newer half. A run that adjudicates a
pre-registered prediction carries a `VERDICT.md`: `type: Verdict`, the
prediction id, the frozen pre-registration it was ruled against, and the ruling
itself. Verdicts are deliberately not ADRs — an ADR records a decision someone
can supersede, and nothing supersedes a measurement except a better one.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fux import frontmatter as fm  # noqa: E402

REGRESSION = ROOT / "work" / "regression"
INDEX = REGRESSION / "README.md"
VERDICTS = {"PASS", "FAIL", "INCONCLUSIVE"}


def runs() -> list[Path]:
    return sorted(p for p in REGRESSION.iterdir() if p.is_dir() and re.match(r"\d{4}-\d{2}-\d{2}-", p.name))


def verdicts() -> list[Path]:
    return sorted(p / "VERDICT.md" for p in runs() if (p / "VERDICT.md").is_file())


@pytest.mark.parametrize("run", runs(), ids=lambda p: p.name)
def test_run_carries_its_evidence(run: Path) -> None:
    """A run whose numbers cannot be traced is an anecdote."""
    has_report = (run / "report.md").is_file() or (run / "evidence" / "report.md").is_file()
    has_analysis = (run / "ANALYSIS.md").is_file()
    has_evidence = (run / "evidence").is_dir() or (run / ".evidence").is_dir()

    # A *surface capture* is allowed to have no `evidence/`: its primary data is
    # the verbatim transcript in the report itself. The README says a run must
    # declare which it is, so this reads that declaration rather than guessing.
    report = next(
        (f for f in (run / "report.md", run / "evidence" / "report.md") if f.is_file()),
        None,
    )
    declares_capture = bool(report) and "surface capture" in report.read_text(encoding="utf-8").lower()

    missing = [
        name
        for name, ok in (
            ("a report", has_report),
            ("ANALYSIS.md", has_analysis),
            ("evidence/", has_evidence or declares_capture),
        )
        if not ok
    ]
    assert not missing, (
        f"{run.name}: missing {missing} — see work/regression/README.md §Per-run contract. "
        "A measurement needs its primary data; a surface capture must say so in its report."
    )


@pytest.mark.parametrize("run", runs(), ids=lambda p: p.name)
def test_run_is_listed_in_the_index(run: Path) -> None:
    assert run.name in INDEX.read_text(encoding="utf-8"), (
        f"{run.name} is filed but not listed in work/regression/README.md — "
        "a run nobody can find is a run nobody cites"
    )


@pytest.mark.parametrize("path", verdicts(), ids=lambda p: p.parent.name)
def test_verdict_says_what_it_ruled_and_against_what(path: Path) -> None:
    meta = fm.parse(path.read_text(encoding="utf-8")).meta
    assert meta.get("type") == "Verdict", (
        f"{path.parent.name}/VERDICT.md: type must be Verdict, got {meta.get('type')!r}. "
        "A verdict is not an ADR — nothing supersedes a measurement except a better one."
    )
    for key in ("name", "verdict", "prediction", "pre_registration"):
        assert str(meta.get(key, "")).strip(), f"{path.parent.name}/VERDICT.md: missing {key!r}"
    assert meta["verdict"] in VERDICTS, (
        f"{path.parent.name}/VERDICT.md: verdict must be one of {sorted(VERDICTS)}, got {meta['verdict']!r}"
    )


@pytest.mark.parametrize("path", verdicts(), ids=lambda p: p.parent.name)
def test_verdict_points_at_a_frozen_pre_registration(path: Path) -> None:
    """The threshold has to have been written down *before* the number existed."""
    meta = fm.parse(path.read_text(encoding="utf-8")).meta
    target = ROOT / str(meta["pre_registration"])
    assert target.is_file(), (
        f"{path.parent.name}/VERDICT.md: pre_registration points at {meta['pre_registration']!r}, "
        "which does not exist. A verdict without its frozen threshold is an opinion."
    )
