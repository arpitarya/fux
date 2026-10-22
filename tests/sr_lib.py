"""Shared parsing for the SR register — the single place both the ownership
twin (test_sr_ownership.py) and the freshness gate (test_sr_freshness.py)
read the register from, so they can never disagree about who owns what.
"""

from __future__ import annotations

import ast
import re
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SR_DIR = ROOT / "records"
REGISTER = SR_DIR / "README.md"
OPEN_WORK = ROOT / "work" / "OPEN-WORK.md"
OPEN_DIR = ROOT / "work" / "open"

# A record's directory is its state. `records/` is live; `work/adr/` is
# superseded-pending (still in force, replacement planned); `archive/adr/` is
# superseded and may not back a live claim, so it is not scanned here.
RECORD_DIRS = (SR_DIR, ROOT / "work" / "adr")


def _table_rows(text: str, start: str, end: str) -> list[list[str]]:
    body = text.split(start, 1)[1].split(end, 1)[0]
    rows = []
    for line in body.splitlines():
        line = line.strip()
        if not line.startswith("|") or set(line) <= set("|- :"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells and cells[0].lower() in {"component", "#"}:
            continue
        rows.append(cells)
    return rows


def ownership_table(text: str | None = None) -> dict[str, str]:
    """component -> owner (an `SR-NAME` or a `W-nn` id), from the register.

    `text` is the register's content, defaulting to the working tree's.
    `test_sr_freshness.py` passes an OLD revision of the register so that each
    commit is judged against the table as it stood **at that commit** -- a row
    written today may not convict a commit written before it existed.
    """
    rows = _table_rows(
        REGISTER.read_text(encoding="utf-8") if text is None else text,
        "<!-- OWNERSHIP-TABLE-START -->",
        "<!-- OWNERSHIP-TABLE-END -->",
    )
    table: dict[str, str] = {}
    for cells in rows:
        component = cells[0].strip("`").rstrip("/")
        owner = cells[1].strip().strip("*").strip("`")
        assert component not in table, f"{component} is claimed twice in the ownership table"
        table[component] = owner
    return table


def describes_table(text: str | None = None) -> dict[str, list[str]]:
    """component -> the records that DESCRIBE it but do not own it.

    [SR-WORK-OWNERSHIP](../records/0054_WORK-ownership.md). A second, additive relation:
    ownership stays exactly one record per component, and any number of records
    may describe one. Parsed rather than hard-coded for the same reason the
    ownership table is — a table a test hard-codes is two sources that drift.

    `text` is the register's content, defaulting to the working tree's — see
    `ownership_table` for why an old revision is ever passed. **A register old
    enough to predate SR-WORK-OWNERSHIP has no `DESCRIBES` markers at all**, so this
    returns an empty relation there rather than raising: the relation did not
    exist yet, which is exactly what "empty" means.
    """
    if text is not None and "<!-- DESCRIBES-TABLE-START -->" not in text:
        return {}
    rows = _table_rows(
        REGISTER.read_text(encoding="utf-8") if text is None else text,
        "<!-- DESCRIBES-TABLE-START -->",
        "<!-- DESCRIBES-TABLE-END -->",
    )
    table: dict[str, list[str]] = {}
    for cells in rows:
        component, _ = _split_symbols(cells[0])
        record = cells[1].strip().strip("*").strip("`")
        table.setdefault(component, []).append(record)
    return table


def _split_symbols(cell: str) -> tuple[str, frozenset[str]]:
    """`` `path::a,b` `` -> `("path", {"a", "b"})`; a bare path -> an empty set.

    **The `::` qualifier is the fix for a gate that was demanding records with
    nothing to say** (W-140 row 20, 2026-09-11). The relation is per FILE, and
    `src/fux/query/__init__.py` alone is described by four records — so
    changing one function in it demanded a line in all four, and three of those
    lines could only say *nothing here changed*. Written twice in one session,
    then seven times in one change, which is when it stopped being a nuisance
    and became noise that trains a reader to skip record edits.

    **An empty set means the whole file**, which is every row that predates
    this and the right default: a describer that has not narrowed itself is
    still describing everything.
    """
    text = cell.strip().strip("`").strip()
    if "::" not in text:
        return text.rstrip("/"), frozenset()
    path, _, names = text.partition("::")
    symbols = {n.strip().strip("`") for n in names.split(",") if n.strip()}
    return path.strip().rstrip("/"), frozenset(symbols)


def describes_symbols(text: str | None = None) -> dict[tuple[str, str], frozenset[str]]:
    """`(component, record)` -> the symbols that row narrows itself to.

    Empty set = the whole file. Read by the freshness gate, never by ownership:
    **who owns a component is still decided per file**, and narrowing the
    ownership relation would be a different and much larger change.
    """
    if text is not None and "<!-- DESCRIBES-TABLE-START -->" not in text:
        return {}
    rows = _table_rows(
        REGISTER.read_text(encoding="utf-8") if text is None else text,
        "<!-- DESCRIBES-TABLE-START -->",
        "<!-- DESCRIBES-TABLE-END -->",
    )
    out: dict[tuple[str, str], frozenset[str]] = {}
    for cells in rows:
        component, symbols = _split_symbols(cells[0])
        record = cells[1].strip().strip("*").strip("`")
        out[(component, record)] = symbols
    return out


def describers_of(changed: str, table: dict[str, list[str]] | None = None) -> list[str]:
    """Every record that describes `changed`, by the same prefix rule as `owns`.

    ⚠ **All matches, not the longest one.** Most-specific-wins exists so there
    is exactly ONE owner; describing is a set and every member fires, so
    narrowing it to the most specific row would silently drop describers of a
    parent directory — the precise class of miss this relation exists to end.
    """
    table = describes_table() if table is None else table
    found: list[str] = []
    for component, records in table.items():
        if changed == component or changed.startswith(component + "/"):
            found.extend(records)
    return sorted(set(found))


def owned_paths(table: dict[str, str] | None = None) -> list[str]:
    """Component paths, longest first (most specific wins on a prefix match)."""
    return sorted((table or ownership_table()), key=len, reverse=True)


def owner_of(changed: str, table: dict[str, str] | None = None) -> str | None:
    """The owner (`SR-NAME` or `W-nn`) of `changed`, by longest-prefix match."""
    table = table or ownership_table()
    for p in owned_paths(table):
        if changed == p or changed.startswith(p + "/"):
            return table[p]
    return None


def register_names(text: str | None = None) -> dict[str, Path]:
    """SR-NAME -> the record's file, from the register's record-listing table.

    The link may point into `records/` or `work/adr/`; it is resolved
    relative to the register, so the table stays the single source of both a
    record's name and its current state.
    """
    text = REGISTER.read_text(encoding="utf-8") if text is None else text
    names: dict[str, Path] = {}
    pattern = r"\[(\d{4})\]\(([^)]*\d{4}_[^)]+\.md)\)\s*\|\s*\*\*(SR-[A-Z0-9-]+)\*\*"
    for m in re.finditer(pattern, text):
        names[m.group(3)] = (SR_DIR / m.group(2)).resolve()
    return names


def open_work_ids() -> set[str]:
    return set(re.findall(r"\bW-\d{2}\b", OPEN_WORK.read_text(encoding="utf-8")))


def record_path_for(owner: str, text: str | None = None) -> Path | None:
    """The file that IS `owner`'s record — an SR's own file, or a `W-nn`
    item's detail file under `work/open/`. `None` when it cannot be resolved
    (an unknown owner — test_sr_ownership.py's test_every_owner_resolves is
    what catches that; this function just declines to guess).
    """
    if owner.startswith("SR-"):
        return register_names(text).get(owner)
    if re.fullmatch(r"W-\d{2}", owner):
        matches = sorted(OPEN_DIR.glob(f"{owner}-*.md"))
        return matches[0] if matches else None
    return None


# --- The freshness gate's judge — ONE implementation, two callers ------------
#
# `tests/test_sr_freshness.py` replays every commit since `records/RULE-SINCE`
# in CI; `scripts/sr-guard.sh` runs `python tests/sr_lib.py guard MSGFILE` as
# the `commit-msg` hook on what is staged. Until 2026-10-21 the hook was a
# second implementation in shell that knew no `describes` relation, so the two
# could disagree while both looked correct — the restatement SR-LAW-0 forbids.
# The rule is SR-WORK-OWNERSHIP's; this states none of it.

# Anchored to a whole line, deliberately: the escape hatch is a loud, standalone
# claim ("I checked, nothing applies"), not a substring that can appear inside
# unrelated prose ("note: no SR affected the parser, only the tests" would
# have matched the old unanchored pattern and silently exempted the commit).
_EXEMPT_RE = re.compile(r"(?m)^\s*(no[ -](adr|sr)[ -]affected|\[no-(adr|sr)\])\s*$", re.I)


def _git(*args: str) -> str:
    """Read-only git. `--no-optional-locks` keeps this safe on filesystems that
    forbid unlink (the Cowork device bridge — see work/MACHINE.md)."""
    out = subprocess.run(
        ["git", "--no-optional-locks", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip())
    return out.stdout


# 🔴 **One `git` process per object, not one per question** (W-243 step 3,
# 2026-09-30). This file started ~1 500 `git` processes per run — 54 % of every
# process the unit suite starts — which cost 10 s on Linux and 72 s on Windows,
# where a process start is several times dearer. Blobs now come through ONE
# long-lived `git cat-file --batch`, and each commit's patch is read ONCE and
# split by file. The questions asked of git, and their answers, are unchanged.


class _Blobs:
    """`git cat-file --batch`, started on first use and kept for the session."""

    def __init__(self) -> None:
        self._proc: subprocess.Popen | None = None

    def read(self, spec: str) -> str | None:
        """The text of `<rev>:<path>`, or `None` when git has no such object."""
        if self._proc is None:
            self._proc = subprocess.Popen(
                ["git", "--no-optional-locks", "cat-file", "--batch"],
                cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            )
        assert self._proc.stdin and self._proc.stdout
        self._proc.stdin.write(spec.encode("utf-8") + b"\n")
        self._proc.stdin.flush()
        header = self._proc.stdout.readline().decode("utf-8").split()
        if len(header) != 3:  # `<spec> missing`, `ambiguous`, …
            return None
        body = self._proc.stdout.read(int(header[2]))
        self._proc.stdout.read(1)  # the LF git writes after every object
        if header[1] != "blob":
            return None
        # `text=True`'s universal newlines — what `git show` via `_git` returned.
        return body.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")


_BLOBS = _Blobs()


@lru_cache(maxsize=None)
def _register_at(sha: str) -> str | None:
    """`records/README.md` as it stood at `sha`, or `None` if it was not there."""
    return _BLOBS.read(f"{sha}:records/README.md")


@lru_cache(maxsize=None)
def _patch(sha: str) -> dict[str, str]:
    """`sha`'s zero-context patch, split into one section per file path.

    `--no-renames` because a pathspec'd `git show sha -- path` — what this
    replaced — never detects a rename across the pathspec either: a moved file
    is all-added there, and it must be all-added here. A merge is `--cc`, which
    is `git show`'s own default for one.
    """
    sections: dict[str, list[str]] = {}
    current: list[str] | None = None
    in_header = False
    for line in _git("show", "--no-renames", "--unified=0", "--format=", sha).splitlines():
        if line.startswith(("diff --git ", "diff --cc ", "diff --combined ")):
            current, in_header = [line], True
            if not line.startswith("diff --git "):
                sections[line.split(" ", 2)[2]] = current
            continue
        if current is None:
            continue
        current.append(line)
        if line.startswith("@@"):
            in_header = False
        # `--no-renames` makes `a/X b/X` one path; the `+++`/`---` line names
        # it unambiguously, including a deletion's `+++ /dev/null`. Header
        # lines only: past the first hunk, `--- a/x` is a removed `-- a/x`.
        elif in_header and line.startswith(("+++ b/", "--- a/")) and current[0].startswith("diff --git "):
            sections.setdefault(line[6:], current)
    return {path: "\n".join(lines) for path, lines in sections.items()}


def _git_available() -> bool:
    try:
        _git("rev-parse", "--git-dir")
        return True
    except (RuntimeError, FileNotFoundError):
        return False


def changed_symbols(path: str, *, sha: str | None = None, staged: bool = False) -> set[str] | None:
    """The top-level `def`/`class` names a diff touched in `path`.

    `None` means *could not tell* — a new file, a deleted one, unparseable
    Python, a non-Python file, or a hunk outside every top-level block. **The
    caller must treat `None` as "every symbol"**, because guessing narrow is
    how a gate stops firing.

    `sha` judges that commit against its parent; `staged` judges the index
    against `HEAD` (the `commit-msg` hook); neither judges the working tree
    against `HEAD`.
    """
    if not path.endswith(".py"):
        return None
    try:
        if sha:
            diff = _patch(sha).get(path, "")
        elif staged:
            diff = _git("diff", "--cached", "--unified=0", "HEAD", "--", path)
        else:
            diff = _git("diff", "--unified=0", "HEAD", "--", path)
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
        if sha:
            source = _BLOBS.read(f"{sha}:{path}")
        elif staged:
            source = _BLOBS.read(f":{path}")  # stage 0 — what will be committed
        else:
            source = (ROOT / path).read_text(encoding="utf-8", errors="replace")
    except (RuntimeError, OSError):
        return None
    if source is None:
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
    staged: bool = False,
) -> dict[str, Path | None]:
    """owner name -> that owner's record path, for every owner touched by `files`.

    Deliberately the *owning* record per file, not "any record was touched" —
    a commit that changes `src/fux/query/` and updates `records/0001_LAWS.md`
    (SR-LAWS, which owns none of it) must not pass just because *a* record
    moved. `record_path_for` returns `None` for an owner that does not resolve
    to a file; that is `test_sr_ownership.py`'s `test_every_owner_resolves` to
    catch, not this test's — an unresolved owner is skipped here rather than
    reported as a false freshness violation.

    `register` is `records/README.md` as it stood at the commit being judged,
    or `None` for the working tree's copy.
    """
    owners = {o for o in (owner_of(f, table) for f in files) if o is not None}
    # SR-WORK-OWNERSHIP: the gate demands the owner AND every DESCRIBER.
    #
    # ⚠ **This is the whole widening.** Without it the check is narrower than it
    # reads: `src/fux/query/` is owned by SR-ASK, so rewriting the scorer
    # satisfied it by touching SR-ASK while SR-RANKING — whose entire subject
    # IS that scorer — rotted silently, sixteen records deep, through all of
    # W-76. SR-WORK-OWNERSHIP veto condition 3 is this going away.
    #
    # ⚠ **And the widening is itself retroactive unless it is dated.** The
    # `describes` relation was invented by SR-WORK-OWNERSHIP on 2026-08-27; before
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
        touched = changed_symbols(f, sha=sha, staged=staged)
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




def missing_records(files: list[str], *, register: str | None = None, sha: str | None = None,
                    staged: bool = False) -> list[str]:
    """`OWNER (records/x.md)` for every owner or describer `files` demand and
    do not include. Empty when the change is fresh."""
    table = ownership_table(register)
    owned = {
        owner: path.relative_to(ROOT).as_posix()
        for owner, path in owning_records(files, table, register=register, sha=sha, staged=staged).items()
        if path is not None
    }
    return sorted(f"{owner} ({rel})" for owner, rel in owned.items() if rel not in files)


def guard(msg_file: str) -> int:
    """The `commit-msg` hook: judge the staged change, honour the escape hatch."""
    if not REGISTER.is_file():
        return 0
    msg = Path(msg_file).read_text(encoding="utf-8", errors="replace") if Path(msg_file).is_file() else ""
    if _EXEMPT_RE.search(msg):
        return 0
    staged = _git("diff", "--cached", "--name-only").split()
    if not staged:
        return 0
    missing = missing_records(staged, staged=True)
    if not missing:
        return 0
    print(
        "\n  SR guard: this commit changes an SR-owned component and does not stage\n"
        "  its OWNING record, or a record that DESCRIBES it (SR-WORK-OWNERSHIP):\n\n"
        + "".join(f"    {m}\n" for m in missing)
        + "\n  Update and stage each, or say so in the commit message, on its own line:\n\n"
        "      no SR affected\n\n"
        "  Saying so explicitly is the rule. Skipping silently is not.\n",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "guard":
        raise SystemExit(guard(sys.argv[2]))
    print("usage: python tests/sr_lib.py guard COMMIT_MSG_FILE", file=sys.stderr)
    raise SystemExit(2)
