"""The committed FACTS that ranking reads about a document: its `mtime`, and
whether something supersedes it.

🔴 **This module used to own two ranking priors and now owns neither.**
`recency_multiplier` lived here until 2026-09-13 and was deleted with
`recency_half_life_days` (W-152); `superseded_weight` went the same day (W-151).
Both were **multipliers**, expressed through `query/rank.py::Weighting` rather
than applied anywhere else, under
[SR-T1-ACCELERATOR](../../records/0110_accelerator.md) veto 5 — W-73's lesson
about a multiplier that reaches the scorer without reaching the pruning bound.
**That veto still binds any multiplier that arrives next.**

What is left here is the *derivation of the facts at ingest*: `git_commit_times`
writes `mtime`, `superseded_ids` reads the declared `supersedes:` edges. Both
facts still reach ranking — as `query/rank.py`'s declared tie-break, which
cannot move a document past one that outscores it.

## Why these are facts in the record, not derivations at query time

`mtime` and `superseded` are committed. Two reasons:

1. **The scan cannot shell out.** Deriving a git timestamp per document at
   query time means one subprocess per candidate; the whole design is that a
   query touches the index and nothing else.
2. **They must be identical on every clone.** A derivation from local
   filesystem mtimes would differ per machine and break L3. A git commit
   timestamp is a property of the history every clone shares.

The *weights* applied to them were tunable (`tune.toml`); the facts never were.
That was the SR-TUNE decision 1 split, on the right side of the line — and since
2026-09-13 there are no weights left on this side of it at all.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def git_commit_times(root: Path, rel_paths: list[str]) -> dict[str, int]:
    """`{rel_path: unix seconds of its last commit}` in ONE git invocation.

    **One call, not one per document.** `git log -1 -- <path>` per document is
    the obvious implementation and it is a subprocess per document: at the
    10 000-document design point that is 10 000 process spawns, which dwarfs
    the entire rest of an ingest (measured at 9.5 s for 10 000 documents once
    the embedding came out). This walks the history once instead.

    Returns `{}` on any git failure — not a raise. A corpus outside a git
    checkout, a shallow clone, a repo with no commits: all legitimate, and
    none of them is a reason to refuse to index. A document with no timestamp
    simply gets no recency prior, which is the same as the shipped default.
    """
    wanted = set(rel_paths)
    if not wanted:
        return {}
    try:
        proc = subprocess.run(
            ["git", "--no-optional-locks", "log", "--format=%ct", "--name-only", "--no-renames"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (OSError, subprocess.SubprocessError):
        return {}
    if proc.returncode != 0:
        return {}

    out: dict[str, int] = {}
    current = 0
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.isdigit():
            current = int(line)
            continue
        # History is newest-first, so the FIRST time a path appears is its
        # most recent commit. `setdefault` is the whole algorithm.
        if line in wanted:
            out.setdefault(line, current)
    return out


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

