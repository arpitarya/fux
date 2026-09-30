"""W-239 — the gated family scan returns exactly what the combined scan did.

`IdentifierRules.matches()` stopped running one 103-way alternation at every
character and now finds candidate starts with a cheap gate, then tries only the
families that share the candidate's first letter. **That is a speed change and
nothing else**: the index must be byte-identical before and after. These tests
hold the two scans equal on every text this repo can reach cheaply — the shared
fixture, the repo's own families over its own Markdown, and the edge cases the
boundaries exist for.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from fux.query import identifiers as ids_mod
from fux.query.identifiers import build

REPO = Path(__file__).resolve().parents[2]
FIXTURE = json.loads((Path(__file__).parent / "identifiers-fixture.json").read_text("utf-8"))


def _ungated(rules, text: str) -> list[tuple[int, int, str]]:
    """The pre-W-239 scan: one combined pattern, `finditer`."""
    rx, groups, _gated = ids_mod._compiled(rules)
    return [ids_mod._found(m, groups) for m in rx.finditer(text)]


def _gated_is_used(rules) -> bool:
    return ids_mod._compiled(rules)[2] is not None


TEMPLATES = build(FIXTURE["families"]["templates"], [], [], [])

EDGES = [
    "",
    "RF-118",
    "rf118 RF 118 RF–118 RF—118 RF_118 RF-0118",
    "xRF-118 RF-118x 1RF-118 RF-118-2",
    "v2.RF-118 a.RF-118 .RF-118 RF-118.x RF-118. (RF-118)",
    "…/wiki/RF-118?rev=2#RF-119",
    "ADR-4 against ADR-0004, and adr4; ADR-",
    "RFRF-118 R RF- RF-- 118",
    "\nRF-118\nRF-119\n",
    "ÄRF-118 éRF-118 日本RF-118",
]


@pytest.mark.parametrize("text", EDGES + [c["text"] for c in FIXTURE["analysis"]])
def test_gated_equals_combined_on_the_fixture_families(text):
    assert _gated_is_used(TEMPLATES)
    assert TEMPLATES.matches(text) == _ungated(TEMPLATES, text)


def test_a_regex_rule_keeps_the_combined_scan():
    """A [user] regex may start with anything, so there is no letter to gate on."""
    rules = build(FIXTURE["families"]["templates"], [], [], FIXTURE["families"]["regex"])
    assert rules.rules and any(r.kind == "regex" for r in rules.rules)
    assert not _gated_is_used(rules)
    for c in FIXTURE["analysis"]:
        assert rules.matches(c["text"]) == _ungated(rules, c["text"])


def _tracked_markdown() -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "--", "tests/*.md", "records/00*.md"],
        cwd=REPO, capture_output=True, text=True, check=True,
    ).stdout.split("\n")
    return [REPO / f for f in out if f and (REPO / f).is_file()]


def test_gated_equals_combined_over_this_repos_markdown_with_its_own_families():
    """The property the DoD names, on real prose: the repo's committed families
    over its tracked test fixtures and the Law records — `records/0001_LAWS.md`
    is where a prototype gate holding a literal `-` first diverged. Any
    divergence is a changed index, which is exactly what W-239 may not do. (The
    full 1 213-file sweep was run once, 0 mismatches; it takes 90 s.)"""
    rules = ids_mod.for_root(REPO)
    if rules.empty:
        pytest.skip("this checkout declares no identifier families")
    assert _gated_is_used(rules)
    files = _tracked_markdown()
    assert files
    for p in files:
        text = p.read_text(encoding="utf-8", errors="replace")
        assert rules.matches(text) == _ungated(rules, text), p.relative_to(REPO)
