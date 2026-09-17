"""W-166 DoD 2 — a changed extraction rule must bump `extract.RULES_VERSION`.

**The `check-version-parity.py` pattern, and `test_sr_freshness`'s shape.** The
constant is what the reuse key compares; a rule change that does not move it
reaches an unchanged document only on `--full`, which is exactly the defect
W-166 closed. A constant nobody is made to bump is a constant that stops being
true, silently — and the failure looks like a working feature: ingest reports
success and serves text the current code would not produce.

⚠ **This checks the WORKING TREE against `HEAD`, so it can only ever be red on
a tree somebody has yet to commit** — which CLAUDE.md names as a hazard, because
CI reads commits. It is paired with `test_the_digest_moves_when_the_constant
_does` below, which needs no git at all and is the half that can never be
invisible.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from fux.ingest import extract as extract_mod
from fux.ingest.run import _extract_config_digest

ROOT = Path(__file__).resolve().parents[2]
MODULE = "src/fux/ingest/extract.py"


class _Limits:
    def __init__(self, phrases: int = 32, rows: int = 50) -> None:
        self.max_phrases = phrases
        self.max_table_rows = rows


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
        env={"GIT_OPTIONAL_LOCKS": "0", "PATH": "/usr/bin:/bin:/usr/local/bin"},
    ).stdout


def test_a_changed_extract_module_bumped_its_rules_version():
    try:
        changed = set(_git("diff", "--name-only", "HEAD").split())
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("not a git checkout — nothing to audit")
    if MODULE not in changed:
        return

    diff = _git("diff", "-U0", "HEAD", "--", MODULE)
    bumped = any(
        line.startswith(("+", "-")) and "RULES_VERSION" in line
        for line in diff.splitlines()
    )
    assert bumped, (
        f"{MODULE} changed and `RULES_VERSION` did not.\n\n"
        "Bump it if the edit can change what this module RETURNS — the next "
        "`fux ingest` then re-extracts the corpus. Leave it alone only for an "
        "edit that provably cannot move a byte of output (a comment, a "
        "docstring, a renamed local), and touch the line in the same change "
        "either way so this check sees a decision rather than an omission."
    )


def test_the_digest_moves_when_the_constant_does(monkeypatch):
    """The half that needs no git: the constant is actually IN the reuse key.

    Without this, `RULES_VERSION` could be bumped forever by a diligent author
    and change nothing, and the test above would pass on every commit while
    guarding a value nothing reads.
    """
    before = _extract_config_digest(_Limits())
    monkeypatch.setattr(extract_mod, "RULES_VERSION", extract_mod.RULES_VERSION + 1)
    assert _extract_config_digest(_Limits()) != before


def test_the_caps_are_still_in_the_digest_too():
    """`rules=` was ADDED to this digest, not substituted for what was there."""
    base = _extract_config_digest(_Limits())
    assert _extract_config_digest(_Limits(phrases=12)) != base
    assert _extract_config_digest(_Limits(rows=5)) != base
