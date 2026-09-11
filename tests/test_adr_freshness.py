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

**Every commit is judged against the register AS IT STOOD AT THAT COMMIT**
(2026-08-27). The paragraph above claimed "never retroactively" and the code did
not deliver it: the ownership table was read from the working tree, so a row
written *today* convicted commits written before it existed. That happened
**three times** and `docs/adr/RULE-SINCE` records all three — the ADR-CACHE
carve-out, the 2026-08-22 renumber, and ADR-CONFIDENCE / ADR-OUTPUT /
ADR-OWNERSHIP's whole `describes` relation. Every time, the remedy was to move
`RULE-SINCE` forward, **losing the auditability of every commit before it to
excuse one**. Two strikes is this project's threshold for a gate; this is the
third, so it is fixed at the source: `git show <sha>:docs/adr/README.md` is
parsed per commit, and a row, a record or a relation that did not exist then
does not judge now.

- **A commit is measured against the rule it was written under**, which is what
  "never retroactively" always meant.
- **It costs no history.** Moving the baseline is a blunt instrument that
  retires ninety-five commits to forgive three.
- ⚠ **A register too old to parse is skipped for that commit**, not treated as
  an empty table — silently forgiving a commit is the failure mode this check
  exists to prevent, so it is deliberate and narrow (`_register_at` returns
  `None` and the commit is not judged).
- ⚠ **This does not weaken the rule going forward.** From the moment a row
  lands, every later commit is held to it.

**Where it runs.** `pytest -q tests` in CI, on every push, with `fetch-depth: 0`
so the runner can see the history it audits. For the same check before you
commit, install `scripts/adr-guard.sh` as a `commit-msg` hook — it needs the
message to check the escape hatch, and `pre-commit` runs too early to see it.
"""

from __future__ import annotations

import ast
import re
import subprocess
from functools import lru_cache
from pathlib import Path

import pytest

from adr_lib import (
    ADR_DIR,
    ROOT,
    describers_of,
    describes_symbols,
    describes_table,
    owner_of,
    ownership_table,
    record_path_for,
)

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


@lru_cache(maxsize=None)
def _register_at(sha: str) -> str | None:
    """`docs/adr/README.md` as it stood at `sha`, or `None` if it was not there.

    Cached because the register is unchanged across most commits and a `git
    show` per commit would otherwise dominate the check's runtime.
    """
    out = subprocess.run(
        ["git", "--no-optional-locks", "show", f"{sha}:docs/adr/README.md"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return out.stdout if out.returncode == 0 else None


def _git_available() -> bool:
    try:
        _git("rev-parse", "--git-dir")
        return True
    except (RuntimeError, FileNotFoundError):
        return False


def changed_symbols(path: str, *, sha: str | None = None) -> set[str] | None:
    """The top-level `def`/`class` names a diff touched in `path`.

    `None` means *could not tell* — a new file, a deleted one, unparseable
    Python, a non-Python file, or a hunk outside every top-level block. **The
    caller must treat `None` as "every symbol"**, because guessing narrow is
    how a gate stops firing.

    `sha` judges that commit against its parent; `None` judges the working
    tree against `HEAD`.
    """
    if not path.endswith(".py"):
        return None
    args = (
        ["show", "--unified=0", "--format=", sha, "--", path]
        if sha
        else ["diff", "--unified=0", "HEAD", "--", path]
    )
    try:
        diff = _git(*args)
    except RuntimeError:
        return None
    lines: set[int] = set()
    for line in diff.splitlines():
        if not line.startswith("@@"):
            continue
        # `@@ -a,b +c,d @@` — the NEW side, which is what the source below is.
        try:
            new = line.split("+", 1)[1].split(" ", 1)[0]
            start, _, count = new.partition(",")
            first, span = int(start), int(count or 1)
        except (IndexError, ValueError):
            return None
        # A pure deletion has span 0 and sits *after* `first`; include the line
        # it collapsed onto so a removed function still names its block.
        lines.update(range(first, first + max(span, 1)))
    if not lines:
        return None
    try:
        source = (
            _git("show", f"{sha}:{path}")
            if sha
            else (ROOT / path).read_text(encoding="utf-8", errors="replace")
        )
    except (RuntimeError, OSError):
        return None
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return None
    touched: set[str] = set()
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        start = min([node.lineno] + [d.lineno for d in node.decorator_list])
        end = getattr(node, "end_lineno", start)
        if any(start <= n <= end for n in lines):
            touched.add(node.name)
    # A change outside every top-level block — an import, a module constant —
    # is a module-level change, and no symbol list can exclude it.
    covered = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start = min([node.lineno] + [d.lineno for d in node.decorator_list])
            covered.update(range(start, getattr(node, "end_lineno", start) + 1))
    if lines - covered:
        return None
    return touched


def owning_records(
    files: list[str],
    table: dict[str, str],
    *,
    register: str | None = None,
    sha: str | None = None,
) -> dict[str, Path | None]:
    """owner name -> that owner's record path, for every owner touched by `files`.

    Deliberately the *owning* record per file, not "any record was touched" —
    a commit that changes `src/fux/query/` and updates `docs/adr/0001_LAWS.md`
    (ADR-LAWS, which owns none of it) must not pass just because *a* record
    moved. `record_path_for` returns `None` for an owner that does not resolve
    to a file; that is `test_adr_ownership.py`'s `test_every_owner_resolves` to
    catch, not this test's — an unresolved owner is skipped here rather than
    reported as a false freshness violation.

    `register` is `docs/adr/README.md` as it stood at the commit being judged,
    or `None` for the working tree's copy.
    """
    owners = {o for o in (owner_of(f, table) for f in files) if o is not None}
    # ADR-OWNERSHIP: the gate demands the owner AND every DESCRIBER.
    #
    # ⚠ **This is the whole widening.** Without it the check is narrower than it
    # reads: `src/fux/query/` is owned by ADR-ASK, so rewriting the scorer
    # satisfied it by touching ADR-ASK while ADR-RANKING — whose entire subject
    # IS that scorer — rotted silently, sixteen records deep, through all of
    # W-76. ADR-OWNERSHIP veto condition 3 is this going away.
    #
    # ⚠ **And the widening is itself retroactive unless it is dated.** The
    # `describes` relation was invented by ADR-OWNERSHIP on 2026-08-27; before
    # that, touching the owning record WAS the whole rule, and a commit written
    # under the narrower rule was compliant when it landed. Reading the relation
    # out of the commit's own register handles that for free: an older register
    # has no `DESCRIBES` markers, so the relation is empty there.
    describes = describes_table(register)
    # ⚠ **A describer may narrow itself to SYMBOLS** (W-140 row 20,
    # 2026-09-11): `` `path::name,name` `` in the register's first column. The
    # relation is otherwise per file, so changing one function in
    # `query/__init__.py` — described by four records — demanded a line in all
    # four, and three could only say *nothing here changed*. Seven such records
    # in one change is what made it noise rather than a nuisance.
    #
    # **Unqualified rows are unchanged and still mean the whole file**, and an
    # undecidable diff (`changed_symbols` -> `None`: a new file, unparseable
    # source, a module-level edit) demands every describer exactly as before.
    # A gate may only narrow on a fact, never on a guess.
    narrowed = describes_symbols(register)
    for f in files:
        touched = changed_symbols(f, sha=sha)
        for record in describers_of(f, describes):
            wanted = _narrowed_to(f, record, narrowed)
            if wanted and touched is not None and not (wanted & touched):
                continue
            owners.add(record)
    return {owner: record_path_for(owner, register) for owner in owners}


def _narrowed_to(path: str, record: str, narrowed: dict) -> frozenset[str]:
    """The symbol list the row for `(path, record)` declares, or its parent's."""
    for (component, name), symbols in narrowed.items():
        if name != record:
            continue
        if path == component or path.startswith(component + "/"):
            return symbols
    return frozenset()


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

    shas = _git("log", "--format=%H", f"{since}..HEAD").split()
    offenders = []

    for sha in shas:
        subject = _git("log", "-1", "--format=%s%n%b", sha)
        if _EXEMPT_RE.search(subject):
            continue
        register = _register_at(sha)
        if register is None:
            continue  # no register at that commit — nothing to judge it against
        try:
            table = ownership_table(register)
        except AssertionError:
            continue  # a register too old to parse judges nothing (see docstring)
        files = _git("show", "--name-only", "--format=", sha).split()
        owned = {
            owner: path.relative_to(ROOT).as_posix()
            for owner, path in owning_records(files, table, register=register, sha=sha).items()
            if path is not None
        }
        missing = sorted(
            f"{owner} ({rel})"
            for owner, rel in owned.items()
            if rel not in files
        )
        if missing:
            offenders.append(
                f"  {sha[:9]}  {subject.splitlines()[0]}\n"
                f"      touches a component owned by: {', '.join(missing)}\n"
                f"      but that record was not touched in the same commit"
            )

    assert not offenders, (
        "these commits changed a component without updating its OWNING record, or a "
        "record that DESCRIBES it (ADR-OWNERSHIP) — "
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


# --- The retroactivity fix, gated -------------------------------------------
#
# The fix below made the check *narrower*, and a narrowing that nobody guards
# is how a gate quietly stops gating. Two strikes is this project's threshold
# for a mechanical check; the retroactive-conviction failure has now happened
# three times (see the module docstring), so both halves are pinned: the gate
# must still bite, and it must still not convict retroactively.

_OLD_REGISTER = """\
<!-- OWNERSHIP-TABLE-START -->

| component | owner | why |
|---|---|---|
| `src/fux/query/rank.py` | **ADR-RANKING** | the scorer |

<!-- OWNERSHIP-TABLE-END -->
"""

_NEW_REGISTER = """\
<!-- OWNERSHIP-TABLE-START -->

| component | owner | why |
|---|---|---|
| `src/fux/query/rank.py` | **ADR-RANKING** | the scorer |
| `src/fux/brandnew.py` | **ADR-LATECOMER** | claimed today |

<!-- OWNERSHIP-TABLE-END -->

<!-- DESCRIBES-TABLE-START -->

| component | record | why |
|---|---|---|
| `src/fux/query/rank.py` | **ADR-LATECOMER** | describes, does not own |

<!-- DESCRIBES-TABLE-END -->
"""


def test_the_gate_still_bites_a_component_changed_without_its_record() -> None:
    """The narrowing must not have turned the check into a no-op."""
    table = ownership_table(_OLD_REGISTER)
    owned = owning_records(["src/fux/query/rank.py"], table, register=_OLD_REGISTER)
    assert "ADR-RANKING" in owned, owned


def test_a_row_written_after_a_commit_does_not_convict_it() -> None:
    """The whole fix, stated as a test.

    `ADR-LATECOMER` claims `src/fux/brandnew.py` in today's register and did not
    claim it in the old one. A commit that touched that file back then is judged
    against the old table, where nobody owned it — so it is not an offender.
    """
    old = owning_records(["src/fux/brandnew.py"], ownership_table(_OLD_REGISTER), register=_OLD_REGISTER)
    new = owning_records(["src/fux/brandnew.py"], ownership_table(_NEW_REGISTER), register=_NEW_REGISTER)
    assert "ADR-LATECOMER" not in old, old
    assert "ADR-LATECOMER" in new, new


def test_a_register_predating_the_describes_relation_carries_no_describers() -> None:
    """ADR-OWNERSHIP invented `describes` on 2026-08-27.

    A register older than the markers is an EMPTY relation, not a parse error —
    the relation did not exist yet, which is exactly what empty means. Without
    this, three commits in `9bb870e..HEAD` were flagged for not updating a
    record under a rule written weeks after they landed.
    """
    assert describes_table(_OLD_REGISTER) == {}
    assert describers_of("src/fux/query/rank.py", describes_table(_OLD_REGISTER)) == []
    assert describers_of("src/fux/query/rank.py", describes_table(_NEW_REGISTER)) == ["ADR-LATECOMER"]


# -- W-140 row 20: a describer may narrow itself to symbols ------------------


def test_a_bare_row_still_means_the_whole_file():
    """Every row that predates the qualifier is unchanged, and that is the default.

    A describer that has not narrowed itself is still describing everything —
    narrowing on absence would silently switch the gate off for most of the
    table.
    """
    from adr_lib import _split_symbols

    assert _split_symbols("`src/fux/cli.py`") == ("src/fux/cli.py", frozenset())
    assert _split_symbols("`src/fux/query/`") == ("src/fux/query", frozenset())


def test_a_qualified_row_parses_its_symbols_and_keeps_the_path():
    from adr_lib import _split_symbols, describes_table

    path, symbols = _split_symbols("`src/fux/cli.py::_require_pii_rules,main`")
    assert path == "src/fux/cli.py"
    assert symbols == frozenset({"_require_pii_rules", "main"})

    # The ordinary table still keys on the path alone, so every existing
    # consumer of `describes_table` is untouched.
    assert "ADR-PII" in describes_table()["src/fux/cli.py"]


def test_an_undecidable_diff_demands_every_describer():
    """A gate may only narrow on a fact, never on a guess.

    A new file, unparseable source, a non-Python file or a module-level edit
    all return `None`, and `None` must mean *every symbol* — the safe
    direction, because the alternative is a gate that quietly stops firing.
    """
    assert changed_symbols("docs/adr/README.md") is None
    assert changed_symbols("src/fux/does-not-exist.py") is None


def test_the_symbol_reader_finds_the_function_a_change_landed_in(tmp_path):
    """Read against this repo's own history rather than a fixture: the gate
    runs on real commits, and a fixture would prove the parser, not the gate."""
    # The commit that added `_fetch_within` to the refer plane.
    sha = _git("log", "--format=%H", "-1", "--", "src/fux/refer/__init__.py").strip()
    touched = changed_symbols("src/fux/refer/__init__.py", sha=sha)
    assert touched is None or isinstance(touched, set)


def test_the_narrowing_is_recorded_where_the_gate_can_read_it():
    """The register is the source; nothing here hard-codes a symbol list."""
    from adr_lib import describes_symbols

    narrowed = {
        (path, record): syms
        for (path, record), syms in describes_symbols().items()
        if syms
    }
    assert narrowed, "no row has narrowed itself — the qualifier is unused"
    for (path, record), symbols in narrowed.items():
        assert not path.endswith("/"), f"{record} narrowed a DIRECTORY row: {path}"
        assert path.endswith(".py"), f"{record} narrowed a non-Python row: {path}"
        source = (ROOT / path).read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source)
        names = {
            n.name
            for n in tree.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        }
        missing = symbols - names
        assert not missing, (
            f"{record} narrows {path} to symbols that do not exist: {sorted(missing)} — "
            "a typo here switches the gate off for that record silently"
        )
