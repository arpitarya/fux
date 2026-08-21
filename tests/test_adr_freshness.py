"""No behaviour change lands without its ADR updated in the same change.

That rule is written in `CLAUDE.md`, and a rule that lives only in prose is a
rule that gets forgotten at 2am. This is the same rule as a check.

**What it does.** For every commit since the rule took effect, if the commit
touched a component that the ownership table in `docs/adr/README.md` assigns to
a record, then that commit must also touch **that record specifically** —
touching some other, unrelated record does not satisfy it — or say, in its own
message, that no record was affected.

**The escape hatch is deliberate and deliberately loud.** Put a line reading
exactly `no ADR affected` (or `[no-adr]`) in the commit message — its own line,
nothing else on it. It is not a silent skip: it is a claim, written into git
history under your name, that you checked. That is exactly what `CLAUDE.md`
asks for — say so explicitly rather than skipping the check quietly.

**Bootstrapping.** The baseline is the commit that added this file, so the rule
applies from the moment the check landed and never retroactively. To move the
baseline forward after a bulk review, write a commit sha into
`docs/adr/RULE-SINCE`.

**Where it runs.** `pytest -q tests` in CI, on every push, with `fetch-depth: 0`
so the runner can see the history it audits. For the same check before you
commit, install `scripts/adr-guard.sh` as a `commit-msg` hook — it needs the
message to check the escape hatch, and `pre-commit` runs too early to see it.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from adr_lib import ADR_DIR, ROOT, owner_of, ownership_table, record_path_for

RULE_SINCE_FILE = ADR_DIR / "RULE-SINCE"

# Anchored to a whole line, deliberately: the escape hatch is a loud, standalone
# claim ("I checked, nothing applies"), not a substring that can appear inside
# unrelated prose ("note: no ADR affected the parser, only the tests" would
# have matched the old unanchored pattern and silently exempted the commit).
_EXEMPT_RE = re.compile(r"(?m)^\s*(no[ -]adr[ -]affected|\[no-adr\])\s*$", re.I)


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


def owning_records(files: list[str], table: dict[str, str]) -> dict[str, Path | None]:
    """owner name -> that owner's record path, for every owner touched by `files`.

    Deliberately the *owning* record per file, not "any record was touched" —
    a commit that changes `src/fux/query/` and updates `docs/adr/0001_laws.md`
    (ADR-LAWS, which owns none of it) must not pass just because *a* record
    moved. `record_path_for` returns `None` for an owner that does not resolve
    to a file; that is `test_adr_ownership.py`'s `test_every_owner_resolves` to
    catch, not this test's — an unresolved owner is skipped here rather than
    reported as a false freshness violation.
    """
    owners = {o for o in (owner_of(f, table) for f in files) if o is not None}
    return {owner: record_path_for(owner) for owner in owners}


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

    table = ownership_table()
    shas = _git("log", "--format=%H", f"{since}..HEAD").split()
    offenders = []

    for sha in shas:
        subject = _git("log", "-1", "--format=%s%n%b", sha)
        if _EXEMPT_RE.search(subject):
            continue
        files = _git("show", "--name-only", "--format=", sha).split()
        owned = {
            owner: path.relative_to(ROOT).as_posix()
            for owner, path in owning_records(files, table).items()
            if path is not None
        }
        missing = sorted(
            f"{owner} ({rel})" for owner, rel in owned.items() if rel not in files
        )
        if missing:
            offenders.append(
                f"  {sha[:9]}  {subject.splitlines()[0]}\n"
                f"      touches a component owned by: {', '.join(missing)}\n"
                f"      but that record was not touched in the same commit"
            )

    assert not offenders, (
        "these commits changed an ADR-owned component without updating its OWNING "
        "record (touching some other record does not count):\n"
        + "\n".join(offenders)
        + "\n\nEither update the owning record in the same change, or state it in "
        "the commit message on its own line: 'no ADR affected'. Saying so "
        "explicitly is the rule; skipping silently is not."
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
    table = ownership_table()
    owned = {
        owner: path.relative_to(ROOT).as_posix()
        for owner, path in owning_records(changed, table).items()
        if path is not None
    }
    missing = sorted(f"{owner} ({rel})" for owner, rel in owned.items() if rel not in changed)
    assert not missing, (
        "the working tree changes an ADR-owned component without its OWNING record:\n  "
        + "\n  ".join(missing)
        + "\n\nUpdate the owning record before committing, or commit with "
        "'no ADR affected' on its own line if it genuinely touches no recorded decision."
    )
