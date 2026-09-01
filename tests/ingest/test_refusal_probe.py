"""The shipped starter rules, against real captured responses.

`tests/ingest/test_refusals.py` tests the MATCHER. This tests the RULES — the
six entries in `templates/refusals.toml.txt` — against responses that were
actually captured, which is the only way to catch a rule that is well-formed
and wrong about the world.

⚠ **The `accepted` cases are the load-bearing ones.** A rule that refuses too
much removes documents from a corpus silently; nothing else in the suite would
notice.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

from fux.ingest import refusals

PROBE = Path(__file__).resolve().parents[2] / "tools" / "refusal-probe"
CASES = tomllib.loads((PROBE / "cases.toml").read_text(encoding="utf-8"))["case"]


@pytest.fixture(scope="module")
def rules(tmp_path_factory):
    """The SHIPPED starter, loaded exactly as a consumer's repo would load it."""
    root = tmp_path_factory.mktemp("repo")
    (root / ".fux").mkdir()
    template = (
        Path(__file__).resolve().parents[2]
        / "src" / "fux" / "templates" / "refusals.toml.txt"
    )
    (root / ".fux" / "refusals.toml").write_text(
        template.read_text(encoding="utf-8"), encoding="utf-8"
    )
    return refusals.load(root)


def test_the_starter_has_a_case_file_that_is_not_empty():
    assert CASES, "tools/refusal-probe/cases.toml has no [[case]] entries"


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["label"][:48])
def test_each_captured_response_gets_the_expected_verdict(case, rules):
    raw = (PROBE / case["body"]).read_bytes()
    why = refusals.refused(rules, case["url"], case["content_type"], raw)
    outcome = "refused" if why else "accepted"
    assert outcome == case["expect"], (
        f"{case['label']}: expected {case['expect']}, got {outcome}"
        + (f" — {why}" if why else "")
    )


def test_at_least_one_case_must_NOT_be_refused():
    """Without one, a rule that refuses everything passes this whole file."""
    assert any(c["expect"] == "accepted" for c in CASES)
