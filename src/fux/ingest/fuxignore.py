"""`.fux/.fuxignore` — the one file that says what fux does not index.

**Why it exists.** Before this, the answer to *"why is my file not in the
index?"* lived in four places: a `!` line in `.fux/sources/dirs`, a `!` line in
`.fux/sources/types`, the type allowlist in that same file, and two hardcoded
rules in the walker. Four places is three too many, and the symptom was always
the same — a document silently absent, and no single file to read to find out
why.

**So exclusion moves here, and this file outranks the rest.** One file, the
shape every developer already knows, editable by hand, and it is consulted
*first*.

## The grammar is `.gitignore`'s, and the divergences are stated

Everything a `.gitignore` reader expects holds:

| written | means |
|---|---|
| `build` | any file or directory named `build`, at any depth |
| `/build` | `build` at the **repo root** only — a leading `/` anchors |
| `docs/build` | anchored too: **any `/` in the pattern anchors it** |
| `build/` | a **directory** named `build`; a *file* of that name is untouched |
| `*.log` | `*` matches within one path segment and never crosses a `/` |
| `work/**/evidence` | `**` is the explicit any-depth form |
| `!keep.log` | **re-includes** — the gitignore meaning of `!` |
| `[0-9]*.md` | character classes work, `[!0-9]` negates one |

**Last match wins**, exactly as git resolves it, and **a file under an ignored
directory cannot be re-included** — also git's rule, and the reason
`.fux/**` followed by `!.fux/decoders/*.py` does not do what it looks like.

⚠ **Two deliberate divergences from git, and both are here rather than
buried:**

1. **A `#` after whitespace begins a comment**, so `*.log   # noisy` is a
   pattern plus a note. Git treats that whole line as a literal pattern that
   matches nothing — a footgun the rest of fux's source lists already fixed
   ([`sourcelist.strip_comment`](sourcelist.py)), and one grammar in one tool
   beats bug-compatibility with another.
2. **There is exactly one `.fuxignore`, at `.fux/.fuxignore`**, and it is never
   nested. A per-directory file would make the skip reason depend on which of
   several files matched, and would need a defined merge order to keep L3.

## `fux ingest` WRITES into this file, and that is W-93's ruling

Two delimited blocks, rewritten by every ingest, holding **every path the run
did not index and why**:

```
# >>> fux: not indexed >>>
archive/v0.1/fux/cli.py   # not an indexed file type
# <<< fux: not indexed <<<

# >>> fux: skipped >>>
archive/v0.26/tests_e2e/corpus/docs/binary.md   # binary
# <<< fux: skipped <<<
```

The list used to live in `.fux/runtime/skipped` — derived, gitignored, and
invisible to review. **Arpit ruled on 2026-08-27 that it belongs here**, and
five properties make that survivable:

| property | why it is load-bearing |
|---|---|
| **the blocks are written FIRST** | last match wins, so anything you write below beats them — including the `!` that pulls a file back out. A block written last would silently beat a human line, which is the one real hazard of letting a machine edit a `.gitignore`-shaped file |
| **a line is a literal path, never a glob** | fux only writes exact paths; translating them would invent a meaning nothing put there. `*` in a filename is a character |
| **which block a line is in IS its class** | structural, so the `not indexed` / `skipped` split is never parsed back out of the note text — ADR-INGEST decision 15's property |
| **the note is the reason that put it there** | a generated verdict reports *that*, not *"ignored by .fuxignore:12"*, so the second run's answer is not *"because the first run said so"* |
| **a path a hand-written pattern covers gets no line** | write `*.py[cod]` yourself and 257 generated lines collapse to zero. One line beats many |

⚠ **The cost, stated because it was accepted rather than avoided: a generated
line DECIDES.** It freezes the verdict that produced it — widen
`.fux/sources/types` and the listed `.py` files stay out; write content into a
file listed as `empty` and it stays out, still labelled `empty`. The freeze is
not undone; `skipnotice.stale_warnings` makes it **loud** on stderr, and the
fix is deleting the line or writing a `!` for it.

## `!` means the opposite here of what it means next door, on purpose

In `.fux/sources/dirs` and `.fux/sources/types`, `!` **subtracts**
([ADR-DIR-LIST](../../../docs/adr/0022_dir-list.md) decision 2b). Here it
**re-includes**. Same character, opposite direction, two files.

**That collision is accepted rather than avoided**, because the alternative is
a `.fuxignore` that is not a `.fuxignore` — a reader who has to learn a new
negation rule for the file named after the one they already know is worse off
than one who reads this paragraph. `fux ingest` warns when the same pattern
appears in both places (`duplicate_warnings`), which is where the confusion
would actually surface.

## It outranks the type allowlist, in both directions

The three walk conditions used to be a **conjunction with no precedence**
(ADR-TYPES decision 7). They are now a conjunction with **one** thing above
them, and this is it:

- a path this file **ignores** is skipped, whatever `types` says;
- a path this file **explicitly re-includes** with `!` is indexed, whatever
  `types` says.

⚠ **The second half is the sharp edge and it is not softened.** `!*.py` indexes
Python files as **raw bytes**, because no decoder claims `.py` — which is
exactly the shape [ADR-TYPES](../../../docs/adr/0031_types-list.md) was opened
about. It takes an explicit `!` line a human wrote to get there, it is visible
in one committed file, and it is the price of the file meaning what its name
says.

**What it does not override:** a file has to be under an included
`.fux/sources/dirs` entry to be seen at all, and `empty` / `binary` /
`non-utf8` still skip a re-included file, because there is nothing to index
either way.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from ..errors import FuxError
from .sourcelist import strip_comment

#: The one path. Not configurable, and not nested — see the module docstring.
IGNORE_FILE = ".fux/.fuxignore"

#: The two fux-written blocks. **Which block a line sits in IS its class** —
#: structural, never parsed out of the reason text, which is the property
#: ADR-INGEST decision 15 rests on.
BLOCK_NOT_INDEXED = "not indexed"
BLOCK_SKIPPED = "skipped"
BLOCKS = (BLOCK_NOT_INDEXED, BLOCK_SKIPPED)

_OPEN = "# >>> fux: {name} >>>"
_CLOSE = "# <<< fux: {name} <<<"

#: Header prose for each block. It has to earn its place in a committed file a
#: person opens, so it says what the block is, that fux rewrites it, and how to
#: get a file back.
_BLURB = {
    BLOCK_NOT_INDEXED: (
        "# a committed list said not to index these. Rewritten by every `fux ingest`.",
        "# Delete a line and it comes back next run unless the list that rejected it changed.",
    ),
    BLOCK_SKIPPED: (
        "# fux opened these and could not read them. Rewritten by every `fux ingest`.",
        "# These are the ones worth a look. Fix the file and delete its line.",
    ),
}


@dataclass(frozen=True)
class Generated:
    """One line fux wrote into a block. Always an exact, literal path.

    Kept out of `Ignores.rules` entirely rather than parsed into a `Rule`, for
    two reasons that are both load-bearing:

    1. **Ordering.** Hand-written lines live below the blocks, and last match
       wins, so **anything you write beats anything fux generated** — including
       a `!` re-include. Holding the two in separate structures makes that
       precedence a property of the lookup rather than of line numbers nobody
       controls.
    2. **Cost.** A block is hundreds of lines on a real corpus, and the
       last-match scan is linear. An exact path needs a dict, not a regex
       sweep — otherwise a 600-line block turns the walk into millions of
       pattern matches.
    """

    path: str
    #: The reason that put it here, carried forward verbatim so it survives
    #: the run that reads it back. Rendered as a trailing `#` comment.
    note: str
    #: `BLOCK_NOT_INDEXED` or `BLOCK_SKIPPED` — the class, stated by position.
    block: str
    lineno: int


@dataclass(frozen=True)
class Rule:
    """One line. `body` is the glob with the `!`, anchor and trailing `/` removed."""

    body: str
    negate: bool
    dir_only: bool
    anchored: bool
    lineno: int
    #: The line as written, `!` and all — what a warning or a skip reason shows.
    raw: str

    def matches(self, path: str, *, is_dir: bool) -> bool:
        if self.dir_only and not is_dir:
            return False
        return _compiled(self.body, self.anchored).match(path) is not None


@dataclass(frozen=True)
class Verdict:
    """What `.fuxignore` says about one path, and which line said it.

    `rule is None` means **the file has no opinion** — the walk falls through
    to the exclusions and the type allowlist, which is the case for every path
    in a repo with no `.fuxignore` at all.
    """

    rule: Rule | None = None
    #: Set instead of `rule` when a fux-written block line decided it.
    generated: Generated | None = None
    #: The path the rule actually matched: the file, or the ancestor directory
    #: that carried it. A skip reason naming `work/` when the file is
    #: `work/a/b.md` is the difference between a usable message and a puzzle.
    matched: str = ""

    @property
    def ignored(self) -> bool:
        if self.generated is not None:
            return True
        return self.rule is not None and not self.rule.negate

    @property
    def reincluded(self) -> bool:
        """True only for an **explicit** `!` match — the allowlist override.

        A path the file simply never mentions is not "re-included"; it has no
        verdict, and `rule is None` says so. Conflating the two would make an
        empty `.fuxignore` index the whole disk.
        """
        return self.rule is not None and self.rule.negate

    def reason(self) -> str:
        """The skip line. Names the file, the line number and the pattern, so
        `fux ingest --list-skipped` answers *why* without a second command.

        **ASCII only** - it is printed, and printed text reaches a Windows
        console (`_report_takeover`'s rule, pinned by
        `tests/test_windows_console_safe.py`).
        """
        assert self.ignored, "reason() describes a skip; a re-include is not one"
        if self.generated is not None:
            # **The reason that put the line there, not "ignored by the line".**
            # A block line is fux's own record of a verdict it already reached;
            # reporting the line as the reason would make the second run's
            # answer *"because the first run said so"*, and the real reason
            # would be lost after one ingest.
            return self.generated.note
        where = f" ({self.matched})" if self.matched else ""
        return f"ignored by {IGNORE_FILE}:{self.rule.lineno} `{self.rule.raw}`{where}"


@dataclass(frozen=True)
class Ignores:
    """A parsed `.fuxignore`. Empty and absent are the same thing to every caller."""

    rules: tuple[Rule, ...] = ()
    #: `{path: Generated}` for the fux-written blocks. Separate from `rules` —
    #: see `Generated` for why.
    generated: dict[str, Generated] = field(default_factory=dict)

    def __bool__(self) -> bool:
        return bool(self.rules) or bool(self.generated)

    def decide(self, rel_path: str, *, is_dir: bool = False, hand_only: bool = False) -> Verdict:
        """The verdict for one repo-relative path.

        **Ancestors first, shallowest to deepest.** Git's rule is that a file
        under an excluded directory cannot be re-included, and the only honest
        way to implement it is to stop descending the moment a directory's own
        last-match-wins verdict is *ignore*. Checking the file alone would make
        `build/` plus `!build/keep.md` resurrect a file git would not.

        **Hand-written lines are consulted first and win outright.** They sit
        below the fux blocks in the file and last match wins, so this ordering
        *is* the file's own semantics — including a `!` line, which is the one
        thing that can pull a path back out of a generated block.

        `hand_only=True` asks what the file would say with the blocks deleted.
        That is how the writer decides a path is already covered by a pattern
        you wrote, and so does not need a line of its own.
        """
        parts = rel_path.split("/")
        for depth in range(len(parts) - 1):
            ancestor = "/".join(parts[: depth + 1])
            rule = self._last_match(ancestor, is_dir=True)
            if rule is not None and not rule.negate:
                return Verdict(rule=rule, matched=ancestor)
        rule = self._last_match(rel_path, is_dir=is_dir)
        if rule is not None:
            return Verdict(rule=rule, matched=rel_path)
        if hand_only:
            return Verdict()
        found = self.generated.get(rel_path)
        return Verdict(generated=found, matched=rel_path if found is not None else "")

    def _last_match(self, path: str, *, is_dir: bool) -> Rule | None:
        """The **last** rule that matches, which is git's resolution order.

        Iterating in reverse and returning the first hit is the same answer for
        a fraction of the work, and the same answer is the point: file order is
        semantic here, unlike every other list fux reads.
        """
        for rule in reversed(self.rules):
            if rule.matches(path, is_dir=is_dir):
                return rule
        return None

    def patterns(self) -> dict[str, Rule]:
        """`{pattern-as-written: rule}` for every **ignoring** line.

        Negations are left out: `!*.min.md` here and `!*.min.md` in
        `sources/types` are opposite statements that happen to share a spelling,
        and warning that they duplicate each other would be wrong.
        """
        # Generated lines are exact paths, never patterns anybody would also
        # write into `sources/`, and there can be hundreds of them. Including
        # them here would turn an advisory into a scan of the whole block.
        return {rule.raw: rule for rule in self.rules if not rule.negate}


def parse(text: str, *, origin: str = IGNORE_FILE) -> Ignores:
    """Parse a whole `.fuxignore`. `origin` is what an error message names.

    **Two grammars in one file, told apart by position.** Between a
    `# >>> fux: <block> >>>` marker and its close, every line is a literal path
    fux wrote and its class is the block's; everywhere else is the `.gitignore`
    grammar a person writes. An unclosed block reads to end-of-file, which is
    the safe direction: the alternative is silently reinterpreting fux's own
    paths as patterns.
    """
    rules: list[Rule] = []
    generated: dict[str, Generated] = {}
    block: str | None = None
    for lineno, raw_line in enumerate(text.split("\n"), start=1):
        marker = raw_line.strip()
        if block is None:
            opened = next((b for b in BLOCKS if marker == _OPEN.format(name=b)), None)
            if opened is not None:
                block = opened
                continue
        else:
            if marker == _CLOSE.format(name=block):
                block = None
                continue
            path, note = _split_note(raw_line)
            if path:
                generated[path] = Generated(path=path, note=note, block=block, lineno=lineno)
            continue

        line = strip_comment(raw_line).strip()
        if not line:
            continue
        written = line
        negate = line.startswith("!")
        if negate:
            line = line[1:].strip()
            if not line:
                raise FuxError(
                    f"{origin}:{lineno}: `!` with no pattern after it. Here `!` re-includes "
                    f"(the .gitignore meaning), so there is nothing for it to act on"
                )
        dir_only = line.endswith("/")
        body = line.rstrip("/") if dir_only else line
        if not body:
            raise FuxError(f"{origin}:{lineno}: `/` is not a pattern")
        # Git's anchoring rule, both halves: a leading `/` anchors, and so does
        # ANY other `/` in the pattern. `docs/build` is repo-root-relative;
        # `build` is a name matched at every depth.
        anchored = body.startswith("/") or "/" in body.strip("/")
        rules.append(
            Rule(
                body=body.lstrip("/"),
                negate=negate,
                dir_only=dir_only,
                anchored=anchored,
                lineno=lineno,
                raw=written,
            )
        )
    return Ignores(rules=tuple(rules), generated=generated)


def _split_note(raw: str) -> tuple[str, str]:
    """A generated line: `<path>` or `<path>   # <reason>`.

    The path is taken literally — no glob translation, no anchoring — because
    fux only ever writes exact repo-relative paths here. `strip_comment`'s
    rule applies (a `#` counts after whitespace), which is why `_writable`
    refuses to materialise a path that contains one.
    """
    body = strip_comment(raw)
    note = raw[len(body) :].lstrip().lstrip("#").strip() if len(body) < len(raw) else ""
    return body.strip(), note


def read(root: Path) -> Ignores:
    """Read `.fux/.fuxignore`, or return an empty one.

    **Absent means "nothing is ignored", and that is safe here** in a way it is
    not for `sources/types`. This file only ever subtracts by default; a missing
    one therefore cannot empty an index, which is why it has no built-in default
    and no error for being empty.
    """
    path = root / IGNORE_FILE
    if not path.is_file():
        return Ignores()
    return parse(path.read_text(encoding="utf-8"), origin=IGNORE_FILE)


def writable(rel_path: str) -> bool:
    """Can this path survive a round trip through a `.fuxignore` line?

    Three shapes cannot, and every one of them is refused rather than mangled:
    a path with a `#` after whitespace (`strip_comment` would eat the rest), a
    path with leading or trailing whitespace (the parser strips it), and a path
    with a newline (there is no such thing as half a line).

    **A refused path is not lost — it keeps being reported every run**, which
    is the loud direction. Silently writing a line that parses back as a
    different path would ignore the wrong file.
    """
    if not rel_path or rel_path != rel_path.strip() or "\n" in rel_path:
        return False
    return strip_comment(rel_path) == rel_path


def write_blocks(root: Path, *, not_indexed, skipped) -> None:
    """Rewrite the fux-written blocks. Everything outside them is untouched.

    `not_indexed` and `skipped` are `(path, note)` pairs. Three properties, and
    each is the answer to a way this could go wrong:

    - **The blocks go FIRST, above every hand-written line.** Last match wins
      in this file, so a block written last would silently beat a `!` you wrote
      — the one hazard of letting a machine edit a `.gitignore`-shaped file.
      First means you always win.
    - **Sorted, and no wall clock.** Same corpus, same bytes (L3). The file is
      committed, so a timestamp here would break the byte-identical guarantee
      on the second machine.
    - **Rewritten whole, never appended to.** A path that stops being skipped
      leaves the file on the next run, so the block cannot accumulate lines for
      documents that no longer exist.

    Writes nothing and creates no file when there is nothing to record and no
    file already exists.
    """
    path = root / IGNORE_FILE
    existing = path.read_text(encoding="utf-8") if path.is_file() else None
    remainder = _without_blocks(existing or "")

    body = "".join(
        _render_block(name, pairs)
        for name, pairs in ((BLOCK_NOT_INDEXED, not_indexed), (BLOCK_SKIPPED, skipped))
        if pairs
    )
    if not body and existing is None:
        return
    text = body + remainder
    if text == existing:
        return  # do not touch mtime for a no-op; `git status` stays quiet
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _render_block(name: str, pairs) -> str:
    lines = [_OPEN.format(name=name), *_BLURB[name]]
    width = max((len(p) for p, _ in pairs), default=0)
    for rel, note in sorted(pairs):
        lines.append(f"{rel.ljust(width)}   # {note}" if note else rel)
    lines.append(_CLOSE.format(name=name))
    return "\n".join(lines) + "\n\n"


def _without_blocks(text: str) -> str:
    """`text` with every fux block removed, and nothing else changed.

    An **unclosed** block swallows the rest of the file, matching `parse`. The
    two readings must agree or a hand-written line could be parsed as a rule
    and then deleted as block content.
    """
    out: list[str] = []
    block: str | None = None
    for raw in text.split("\n"):
        marker = raw.strip()
        if block is None:
            opened = next((b for b in BLOCKS if marker == _OPEN.format(name=b)), None)
            if opened is not None:
                block = opened
                continue
            out.append(raw)
        elif marker == _CLOSE.format(name=block):
            block = None
    while out and not out[0].strip():
        out.pop(0)
    return "\n".join(out)


def duplicate_warnings(root: Path, *, dirs_file: str, types_file: str) -> list[str]:
    """Lines warning that a pattern is stated in two files at once.

    **The duplicate is not an error and is not resolved silently.** Both copies
    do the same thing, so nothing is broken today — but the two files disagree
    about `!`, so the day someone edits one of them the two lines stop meaning
    the same thing, and *that* is the failure this warning is early for.

    **`.fuxignore` is the home; the other line is the one to delete.** The
    message says which, rather than reporting a conflict and leaving the reader
    to guess which way it resolves.

    **ASCII only**, for the same reason `reason()` is.
    """
    ignores = read(root)
    if not ignores:
        return []
    mine = ignores.patterns()
    warnings: list[str] = []
    for rel, kind in ((types_file, "types"), (dirs_file, "dirs")):
        for pattern, lineno in _exclusions(root, rel).items():
            rule = mine.get(pattern) or mine.get(f"{pattern}/")
            if rule is None:
                continue
            warnings.append(
                f"warning: `{pattern}` is excluded in both {rel}:{lineno} and "
                f"{IGNORE_FILE}:{rule.lineno}.\n"
                f"  {IGNORE_FILE} is where exclusions live and it is consulted first, so the "
                f"{kind} line changes nothing today.\n"
                f"  Delete `!{pattern}` from {rel} - `!` subtracts there and RE-INCLUDES in "
                f"{IGNORE_FILE}, so leaving both is one edit away from meaning two things."
            )
    return sorted(warnings)


def _exclusions(root: Path, rel_path: str) -> dict[str, int]:
    """`{pattern: lineno}` for the `!` lines of a `dirs`/`types` file.

    Parsed with the **shared** grammar rather than re-read here: two readers for
    one file is how the warning and the walk end up disagreeing about which
    lines exist, and this module exists to remove that class of bug, not add one.
    """
    from . import sourcelist

    path = root / rel_path
    if not path.is_file():
        return {}
    spec = sourcelist.TYPES if rel_path.endswith("types") else sourcelist.DIRS
    try:
        entries = sourcelist.parse(path.read_text(encoding="utf-8"), spec, origin=str(path))
    except FuxError:
        return {}  # a broken list is the walk's error to raise, not this advisory's
    return {entry.value: entry.lineno for entry in entries if entry.exclude}


@lru_cache(maxsize=1024)
def _compiled(body: str, anchored: bool) -> re.Pattern[str]:
    """Compile one glob against a whole repo-relative path.

    Hand-rolled like every other codec here (L1), and **not** `fnmatch`: its
    `*` crosses a `/`, which is the same reason `sourcelist.glob_match` is
    hand-rolled. The prefix is what implements git's *"a pattern with no slash
    matches a basename at any depth"*.
    """
    prefix = "" if anchored else r"(?:.*/)?"
    return re.compile(prefix + _translate(body) + r"\Z")


def _translate(glob: str) -> str:
    out: list[str] = []
    i, n = 0, len(glob)
    while i < n:
        ch = glob[i]
        if ch == "\\" and i + 1 < n:
            out.append(re.escape(glob[i + 1]))
            i += 2
        elif ch == "*":
            if glob[i : i + 3] == "**/":
                out.append(r"(?:.*/)?")  # zero or more directories, git's reading
                i += 3
            elif glob[i : i + 2] == "**":
                out.append(r".*")
                i += 2
            else:
                out.append(r"[^/]*")
                i += 1
        elif ch == "?":
            out.append(r"[^/]")
            i += 1
        elif ch == "[":
            close = _class_end(glob, i)
            if close is None:
                out.append(re.escape("["))  # unterminated: a literal bracket
                i += 1
            else:
                inner = glob[i + 1 : close]
                out.append("[" + ("^" + inner[1:] if inner.startswith("!") else inner) + "]")
                i = close + 1
        else:
            out.append(re.escape(ch))
            i += 1
    return "".join(out)


def _class_end(glob: str, start: int) -> int | None:
    """Index of the `]` closing the class opened at `start`, or `None`.

    `[!]a]` and `[]a]` are classes whose first member is `]` — the one place a
    naive `glob.index("]")` gets it wrong, and the reason this is a function.
    """
    i = start + 1
    if i < len(glob) and glob[i] in "!^":
        i += 1
    if i < len(glob) and glob[i] == "]":
        i += 1
    while i < len(glob):
        if glob[i] == "]":
            return i
        i += 1
    return None
