"""No behaviour change lands without its ADR updated in the same change.

That rule is written in `CLAUDE.md`, and a rule that lives only in prose is a
rule that gets forgotten at 2am. This is the same rule as a check.

**What it does.** For every commit since the rule took effect, if the commit
touched a component that the ownership table in `docs/adr/README.md` assigns to
a record, then the commit must also touch a record — or say, in its own message,
that no record was affected.

**The escape hatch is deliberate and deliberately loud.** Put
`no ADR affected` (or `[no-adr]`) in the commit message. It is not a silent
skip: it is a claim, written into git history under your name, that you checked.
That is exactly what `CLAUDE.md` asks for — say so explicitly rather than
skipping the check quietly.

**Bootstrapping.** The baseline is the commit that added this file, so the rule
applies from the moment the check landed and never retroactively. To move the
baseline forward after a bulk review, write a commit sha into
`docs/adr/RULE-SINCE`.

**Where it runs.** `pytest -q tests` in CI, on every push. For the same check
before you commit, install `scripts/adr-guard.sh` as a pre-commit hook.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "docs" / "adr" / "README.md"
RULE_SINCE_FILE = ROOT / "docs" / "adr" / "RULE-SINCE"

_RECORD_RE = re.compile(r"^(docs|work)/adr/\d{4}_[^/]+\.md$")
_EXEMPT_RE = re.compile(r"no[ -]adr[ -]affected|\[no-adr\]", re.I)


def _git(*args: str) -> str:
    """Read-only git. `--no-optional-locks` keeps this safe on filesystems that
    forbid unlink (the Cowork device bridge — see work/MACHINE.md)."""
    out = subprocess.run(
        ["git", "--no-optional-locks", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip())
    return out.stdout


def _git_available() -> bool:
    try:
        _git("rev-parse", "--git-dir")
        return True
    except (RuntimeError, FileNotFoundError):
        return False


def owned_paths() -> list[str]:
    """Component paths from the ownership table, longest first (most specific wins)."""
    text = REGISTER.read_text(encoding="utf-8")
    body = text.split("<!-- OWNERSHIP-TABLE-START -->", 1)[1]
    body = body.split("<!-- OWNERSHIP-TABLE-END -->", 1)[0]
    paths = []
    for line in body.splitlines():
        line = line.strip()
        if not line.startswith("|") or set(line) <= set("|- :"):
            continue
        cell = [c.strip() for c in line.strip("|").split("|")][0].strip("`")
        if cell.lower() == "component":
            continue
        paths.append(cell.rstrip("/"))
    return sorted(paths, key=len, reverse=True)


def owner_of(changed: str, paths: list[str]) -> str | None:
    for p in paths:
        if changed == p or changed.startswith(p + "/"):
            return p
    return None


def baseline() -> str | None:
    """The commit the rule applies from."""
    if RULE_SINCE_FILE.is_file():
        for line in RULE_SINCE_FILE.read_text(encoding="utf-8").splitlines():
            token = line.split("#", 1)[0].strip()
            if token:
                try:
                    return _git("rev-parse", "--verify", f"{token}^{{commit}}").strip()
                except RuntimeError:
                    pytest.fail(
                        f"docs/adr/RULE-SINCE names {token!r}, which is not a commit in this repo"
                    )
    # self-bootstrapping: the commit that added this very file
    out = _git(
        "log", "--diff-filter=A", "--format=%H", "-1", "--", "tests/test_adr_freshness.py"
    ).strip()
    return out or None


def test_no_behaviour_change_landed_without_its_adr() -> None:
    if not _git_available():
        pytest.skip("not a git checkout (sdist or tarball) — nothing to audit")

    since = baseline()
    if not since:
        pytest.skip(
            "this check is not committed yet, so there is no history to audit. "
            "It starts enforcing from the commit that adds it."
        )

    paths = owned_paths()
    shas = _git("log", "--format=%H", f"{since}..HEAD").split()
    offenders = []

    for sha in shas:
        subject = _git("log", "-1", "--format=%s%n%b", sha)
        if _EXEMPT_RE.search(subject):
            continue
        files = _git("show", "--name-only", "--format=", sha).split()
        touched_record = any(_RECORD_RE.match(f) for f in files)
        if touched_record:
            continue
        hits = sorted({owner_of(f, paths) or "" for f in files} - {""})
        if hits:
            offenders.append(
                f"  {sha[:9]}  {subject.splitlines()[0]}\n"
                f"      changed: {', '.join(hits)}\n"
                f"      but no docs/adr/NNNN_*.md or work/adr/NNNN_*.md was touched"
            )

    assert not offenders, (
        "these commits changed an ADR-owned component without updating any record:\n"
        + "\n".join(offenders)
        + "\n\nEither update the record in the same change, or state it in the commit "
        "message: 'no ADR affected'. Saying so explicitly is the rule; skipping "
        "silently is not."
    )


def test_working_tree_is_not_mid_violation() -> None:
    """The same rule, applied to what you have not committed yet.

    Advisory in spirit but a real failure: if `src/` is edited and no record is,
    the next commit is about to break the rule above. Better to hear it now.
    """
    if not _git_available():
        pytest.skip("not a git checkout — nothing to audit")

    changed = _git("diff", "--name-only", "HEAD").split()
    if not changed:
        return
    if any(_RECORD_RE.match(f) for f in changed):
        return
    paths = owned_paths()
    hits = sorted({owner_of(f, paths) or "" for f in changed} - {""})
    assert not hits, (
        "the working tree changes an ADR-owned component with no record edited:\n  "
        + "\n  ".join(hits)
        + "\n\nUpdate the owning record before committing, or commit with "
        "'no ADR affected' in the message if it genuinely touches no recorded decision."
    )
