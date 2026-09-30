"""The committed FACTS that ranking reads about a document: its `mtime`, how
many people and commits maintained it, and whether something supersedes it.

🔴 **This module used to own two ranking priors and now owns neither.**
`recency_multiplier` lived here until 2026-09-13 and was deleted with
`recency_half_life_days` (W-152); `superseded_weight` went the same day (W-151).
Both were **multipliers**, expressed through `query/rank.py::Weighting` rather
than applied anywhere else, under
[SR-T1-ACCELERATOR](../../records/0110_accelerator.md) veto 5 — W-73's lesson
about a multiplier that reaches the scorer without reaching the pruning bound.
**That veto still binds any multiplier that arrives next** — and W-168 step 8's
authority prior is one: it is applied in `Weighting`, never here.

What is left here is the *derivation of the facts at ingest*: `git_history`
writes `mtime`, `authors` and `commits` from ONE walk, and `superseded_ids`
reads the declared `supersedes:` edges.

## Why these are facts in the record, not derivations at query time

`mtime`, `authors`, `commits` and `superseded` are committed. Two reasons:

1. **The scan cannot shell out.** Deriving a git timestamp per document at
   query time means one subprocess per candidate; the whole design is that a
   query touches the index and nothing else.
2. **They must be identical on every clone.** A derivation from local
   filesystem mtimes would differ per machine and break L4. A git commit
   timestamp, and a count of commits and authors, is a property of the history
   every full clone shares.

The *weights* applied to them are tunable (`tune.toml`); the facts never are.
That is the SR-TUNE decision 1 split.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

#: The one byte a path cannot contain, so a commit header line can never be
#: mistaken for a path (the old `%ct`-only format read an all-digit root file
#: name as a timestamp).
_MARK = "\x00"


@dataclass(frozen=True)
class GitHistory:
    """What the one walk found, per path relative to the repository.

    `mtime` — unix seconds of the path's most recent commit.
    `counts` — `(authors, commits)`: how many commits list the path, and how
    many distinct case-folded author emails those commits carry. 🔴 **Counts
    only.** The emails exist in this process's memory for the length of the
    walk and are never returned, written or logged (the W-168 step 8 bar,
    §What this run may NOT do, item 6).
    """

    mtime: dict[str, int] = field(default_factory=dict)
    counts: dict[str, tuple[int, int]] = field(default_factory=dict)


def _run_git(root: Path, argv: list[str], timeout_s: float) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "--no-optional-locks", *argv],
            cwd=root,
            capture_output=True,
            text=True,
            # 🔴 UTF-8 named, never the platform's. `text=True` alone decodes
            # with the ANSI code page on Windows, and these lines are PATHS: a
            # non-ASCII filename would raise UnicodeDecodeError inside ingest,
            # or come back mangled and silently lose that file's facts.
            encoding="utf-8",
            errors="replace",
            timeout=timeout_s,  # `fux.toml [index] git_timeout_s`
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout


def git_history(root: Path, rel_paths: list[str], *, timeout_s: float) -> GitHistory:
    """Every path's `mtime`, and its `(authors, commits)`, in ONE `git log`.

    **One walk, not one per document.** `git log -1 -- <path>` per document is
    the obvious implementation and it is a subprocess per document: at the
    10 000-document design point that is 10 000 process spawns, which dwarfs
    the entire rest of an ingest (measured at 9.5 s for 10 000 documents once
    the embedding came out). This walks the history once instead.

    **`commits`** is the number of commits in the walk that list the path.
    `--name-only` without `-m` lists no path for a merge commit, so a merge
    counts 0 — the same semantics `mtime` has always had. **`authors`** is the
    number of distinct `%aE` values among them: the mailmap-aware author email,
    case-folded (A3 of `work/compare/authority-prior.compare.md`).

    Returns an empty history on any git failure — not a raise. A corpus outside
    a git checkout, a repo with no commits: all legitimate, and none of them is
    a reason to refuse to index. **A shallow clone keeps its `mtime`** (the
    newest commit is present) **but gets no counts**: its history is truncated,
    so a count would be a number that differs between two clones of one
    repository. A document with no counts reads as `f = 0`, which is the prior
    switched off.
    """
    wanted = set(rel_paths)
    if not wanted:
        return GitHistory()
    out = _run_git(
        root,
        # `%x00` is the format's own spelling of `_MARK`: an argv cannot carry a
        # NUL byte, so git writes it rather than being handed it.
        ["log", "--format=%x00%ct%x00%aE", "--name-only", "--no-renames"],
        timeout_s,
    )
    if out is None:
        return GitHistory()

    mtime: dict[str, int] = {}
    commits: dict[str, int] = {}
    authors: dict[str, set[str]] = {}
    current_time = 0
    current_author = ""
    for line in out.splitlines():
        if line.startswith(_MARK):
            _, stamp, email = line.split(_MARK)
            current_time = int(stamp)
            current_author = email.strip().casefold()
            continue
        line = line.strip()
        if not line or line not in wanted:
            continue
        # History is newest-first, so the FIRST time a path appears is its
        # most recent commit. `setdefault` is the whole algorithm.
        mtime.setdefault(line, current_time)
        commits[line] = commits.get(line, 0) + 1
        authors.setdefault(line, set()).add(current_author)

    shallow = _run_git(root, ["rev-parse", "--is-shallow-repository"], timeout_s)
    if shallow is None or shallow.strip() != "false":
        return GitHistory(mtime=mtime)
    return GitHistory(
        mtime=mtime,
        counts={path: (len(authors[path]), n) for path, n in commits.items()},
    )


def superseded_ids(records: list[dict]) -> set[str]:
    """Doc ids that some other document declares it supersedes.

    **Declared, never inferred.** A document says `supersedes: [...]` in its
    own frontmatter; nothing guesses from titles, numbering or dates. This is
    the same rule SR-DIR-LIST decision 10 applies to `archived` — a path
    heuristic is exact for the repo that invented it and a silent convention
    for everybody else.

    The relation is recorded on the *superseding* document because that is
    where a human writes it, and resolved to a flag on the *superseded* one
    because that is where the ranking needs it.
    """
    out: set[str] = set()
    known = {r["id"] for r in records}
    for record in records:
        for edge in record.get("edges", ()):
            if edge.get("kind") == "supersedes":
                dst = edge.get("dst")
                if dst in known and dst != record["id"]:
                    out.add(dst)
    return out

