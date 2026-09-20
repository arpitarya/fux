"""The OKF bundle's one required field, checked against the tree rather than claimed in prose.

Fux follows Google's **Open Knowledge Format** (OKF v0.1), whose conformance bar
is a parseable frontmatter block with a **non-empty `type`** on every knowledge
document. The bundle is `docs/` + `records/` + `work/`, rooted at `docs/index.md`.
(`records/` moved out of `docs/` to the repo root on 2026-09-13 with the SR
rename; it stays in the bundle, because what a root is called never decided
whether its documents conform.)

**Why this file exists.** Until 2026-09-12 the bar was stated in `CLAUDE.md`,
restated in `docs/index.md`, and checked nowhere. A scan run for
`work/proposals/positioning-documents-not-code.md` §6 found **94 of 314 files**
failing it, including an ALL-CAPS exemption the repo had invented and the spec
does not have. A conformance claim nothing verifies is the class of defect this
repo calls *a record that reads as authority*.

**Three exclusions, and each is a boundary rather than a waiver.**

- `work/regression/*/evidence/**` — raw run material: model output, generated
  corpora, captured stdout. Evidence is cited *by* a document; it is not one.
- `work/golden/seed/**`, `work/golden/golden-answers/**` and the older singular
  spelling — the sealed benchmark's test data, authored outside this lane.
  Editing it to satisfy a docs rule would corrupt the instrument it is, and
  since L11 decision 3 the answers directory may actually hold a key, which no
  agent opens for any reason including this one.
- Filed regression runs before `FROZEN_SINCE` — `report.md` and `ANALYSIS.md`
  in those directories are frozen. `tests/test_regression_runs.py` baselines its
  own classification rule on the same date for the same stated reason: *turning
  a rule on by editing the evidence it governs is the failure the rule is
  about.* Runs filed on or after that date conform.

Repo-root `CLAUDE.md` and `README.md` are tool entry points outside the bundle roots, so they are outside the bundle by construction, not by exclusion.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fux import frontmatter as fm  # noqa: E402

BUNDLE_ROOTS = ("docs", "records", "work")
#: The bundle root declares `okf_version` and nothing else; it is the one
#: reserved filename in the spec and carries no `type`.
BUNDLE_INDEX = Path("docs/index.md")

#: Regression runs filed before this date are frozen. Same baseline, same
#: reason, as CLASSIFY_SINCE in tests/test_regression_runs.py.
FROZEN_SINCE = "2026-08-25"
_RUN_DATE = re.compile(r"^work/regression/(\d{4}-\d{2}-\d{2})-")

#: Not knowledge documents. See the module docstring for why each is a boundary.
EXCLUDED_PREFIXES = (
    "work/golden/seed/",
    # Both spellings. `golden-answers/` is canonical since L11 decision 3
    # (Arpit, 2026-09-18); the singular stays because a boundary that covers
    # only the live name is a boundary that reads green while the other is open.
    "work/golden/golden-answers/",
    "work/golden/golden-answer/",
)


def _in_evidence(rel: str) -> bool:
    return rel.startswith("work/regression/") and "/evidence/" in rel


def _frozen_run_artifact(rel: str) -> bool:
    """A filed run's own report or analysis, from before the freeze baseline."""
    m = _RUN_DATE.match(rel)
    if not m or m.group(1) >= FROZEN_SINCE:
        return False
    return Path(rel).name in {"report.md", "ANALYSIS.md"}


def bundle_docs() -> list[Path]:
    out: list[Path] = []
    for root in BUNDLE_ROOTS:
        for path in sorted((ROOT / root).rglob("*.md")):
            rel = path.relative_to(ROOT).as_posix()
            if rel == BUNDLE_INDEX.as_posix():
                continue
            if rel.startswith(EXCLUDED_PREFIXES) or _in_evidence(rel) or _frozen_run_artifact(rel):
                continue
            out.append(path)
    return out


def test_the_bundle_has_a_root_that_declares_its_version() -> None:
    meta = fm.parse((ROOT / BUNDLE_INDEX).read_text(encoding="utf-8")).meta
    assert str(meta.get("okf_version", "")).strip(), (
        f"{BUNDLE_INDEX}: the bundle root declares `okf_version`. Without it nothing "
        "identifies this tree as an OKF bundle, and the bar below is unmoored."
    )


def test_the_bundle_is_not_empty() -> None:
    found = len(bundle_docs())
    assert found > 200, (
        f"only {found} documents matched under {BUNDLE_ROOTS}. Either the tree moved or an "
        "exclusion above is swallowing the bundle -- a check that inspects nothing passes "
        "for the wrong reason."
    )


@pytest.mark.parametrize("path", bundle_docs(), ids=lambda p: p.relative_to(ROOT).as_posix())
def test_bundle_doc_declares_a_type(path: Path) -> None:
    rel = path.relative_to(ROOT).as_posix()
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---"), (
        f"{rel}: no frontmatter block. OKF v0.1's only required field is `type`, and a "
        "document without frontmatter cannot carry one.\n\n"
        "If this file is not a knowledge document, it does not belong in the bundle -- "
        "say so in docs/index.md and add it to EXCLUDED_PREFIXES here, in the same change."
    )
    meta = fm.parse(text).meta
    assert str(meta.get("type", "")).strip(), (
        f"{rel}: frontmatter carries no non-empty `type`. That is the OKF conformance bar, "
        "and it applies to trackers and directory indexes too -- the ALL-CAPS exemption was "
        "retired 2026-09-12 because the spec has no such rule."
    )
