"""Every filed run keeps the contract its README states.

`work/regression/` is what other documents cite when they need grounding, so a
run directory that is missing its evidence, or a verdict that does not say what
it ruled against, quietly turns a citation into an assertion.

The **verdict** rules are the newer half. A run that adjudicates a
pre-registered prediction carries a `VERDICT.md`: `type: Verdict`, the
prediction id, the frozen pre-registration it was ruled against, and the ruling
itself. Verdicts are deliberately not ADRs — an ADR records a decision someone
can supersede, and nothing supersedes a measurement except a better one.

The **classification** rules are newer still (2026-08-25, W-78 ruling 2). Every
*measured* run declares itself `blind` or `informed` and names who authored each
artifact and what evaluation material they could reach, so that a number
produced against the answers cannot be mistaken for one produced without them.
The rule is baselined on the run directory's own date because filed reports are
frozen and are never edited to satisfy a rule written after them.
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

# ADR-RS decision 11, ruled by Arpit 2026-08-25. Runs filed before this date are
# exempt by BASELINE, not by exception: their reports are frozen, and turning a
# rule on by editing the evidence it governs is the failure the rule is about.
CLASSIFY_SINCE = "2026-08-25"
CLASSIFICATIONS = {"blind", "informed"}
AUTHORSHIP_HEADING = re.compile(r"^#{2,4}\s+.*authorship", re.MULTILINE | re.IGNORECASE)


def report_of(run: Path) -> Path | None:
    """A run's report, wherever the two allowed layouts put it."""
    return next((f for f in (run / "report.md", run / "evidence" / "report.md") if f.is_file()), None)


def is_surface_capture(report: Path | None) -> bool:
    """A capture states no delta, so a blind/informed label would label nothing.

    Read from the run's own declaration -- the same one the evidence rule reads
    -- so the two exemptions cannot drift apart.
    """
    return bool(report) and "surface capture" in report.read_text(encoding="utf-8").lower()


def needs_classification(run: Path) -> bool:
    """A MEASURED run, filed on or after the rule's baseline date."""
    if run.name[:10] < CLASSIFY_SINCE:
        return False
    return not is_surface_capture(report_of(run))


def classified_runs() -> list[Path]:
    return [r for r in runs() if needs_classification(r)]


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
    declares_capture = is_surface_capture(report_of(run))

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


# --------------------------------------------------------------------------
# The run-classification rule -- ADR-RS decisions 11-13, ruled 2026-08-25.
#
# Two layers on purpose. The parametrised checks below guard the runs actually
# filed; the fixture checks after them guard THE RULE, so that a refactor which
# quietly makes `classified_runs()` return nothing cannot turn this gate off
# without a test going red. An empty parametrisation is silent; a fixture is not.
# --------------------------------------------------------------------------


@pytest.mark.parametrize("run", classified_runs(), ids=lambda p: p.name)
def test_measured_run_declares_blind_or_informed(run: Path) -> None:
    report = report_of(run)
    assert report is not None  # the evidence test owns this failure
    meta = fm.parse(report.read_text(encoding="utf-8")).meta
    got = str(meta.get("classification", "")).strip().lower()
    assert got in CLASSIFICATIONS, (
        f"{run.name}: report needs `classification: blind` or `classification: informed` "
        f"in its frontmatter, got {got or 'nothing'!r}. See CLAUDE.md "
        "(§Conformance runs) and ADR-RS decision 11. A run whose artifacts were "
        "authored with the evaluation queries in hand produces a number that looks "
        "exactly like a clean one -- the label is the only thing that separates them. "
        "If this is a surface capture, say so in the report and the rule does not apply."
    )


@pytest.mark.parametrize("run", classified_runs(), ids=lambda p: p.name)
def test_measured_run_names_who_authored_what(run: Path) -> None:
    report = report_of(run)
    assert report is not None
    text = report.read_text(encoding="utf-8")
    assert AUTHORSHIP_HEADING.search(text), (
        f"{run.name}: report has no `## Authorship` section. ADR-RS decision 13 -- "
        "name each artifact's author and which of queries / judgments / prior scores / "
        "none they could reach at the time. The burden is on the author to argue "
        "exposure was absent, not on a reader to prove it was present."
    )


def _write_run(root: Path, name: str, body: str) -> Path:
    run = root / name
    run.mkdir(parents=True)
    (run / "report.md").write_text(body, encoding="utf-8")
    return run


BLIND_REPORT = """---
type: Report
name: fixture
classification: blind
---

## Authorship

Enrichment, prompt, chunking, tuning, analysis: agent B, access `none`.
"""


def test_the_rule_exempts_runs_filed_before_its_baseline(tmp_path: Path) -> None:
    """Frozen evidence is never edited to satisfy a rule written after it."""
    before = _write_run(tmp_path, "2026-08-24-something", "---\ntype: Report\n---\n\nbody\n")
    assert not needs_classification(before)


def test_the_rule_applies_from_its_baseline_date(tmp_path: Path) -> None:
    on_the_day = _write_run(tmp_path, "2026-08-25-something", "---\ntype: Report\n---\n\nbody\n")
    assert needs_classification(on_the_day)


def test_a_surface_capture_is_out_of_scope(tmp_path: Path) -> None:
    """It states no delta, so a blind/informed label would label nothing."""
    capture = _write_run(
        tmp_path,
        "2026-09-01-verbs",
        "---\ntype: Report\n---\n\nThis is a surface capture, not a measurement.\n",
    )
    assert not needs_classification(capture)


@pytest.mark.parametrize(
    "value",
    ["", "yes", "partial", "semi-blind", "double-blind", "unknown"],
    ids=lambda v: v or "missing",
)
def test_only_blind_and_informed_are_admissible(value: str) -> None:
    """The taxonomy is closed. `partial` is how a binary becomes a shrug."""
    assert value.strip().lower() not in CLASSIFICATIONS


def test_a_conforming_report_satisfies_both_checks(tmp_path: Path) -> None:
    """The gate has to be passable, or it is a wall."""
    run = _write_run(tmp_path, "2026-09-01-measured", BLIND_REPORT)
    meta = fm.parse((run / "report.md").read_text(encoding="utf-8")).meta
    assert needs_classification(run)
    assert str(meta.get("classification")).strip().lower() in CLASSIFICATIONS
    assert AUTHORSHIP_HEADING.search((run / "report.md").read_text(encoding="utf-8"))
