"""Phase 2's two ranking priors: recency, and supersession.

Both are **multipliers**, and both are expressed through
`query/rank.py::Weighting` rather than applied anywhere else. That is not a
style preference — it is [ADR-T1-ACCELERATOR](../../docs/adr/0011_accelerator.md)
veto 5, added when W-73 showed what happens to the accelerator's pruning bound
when a multiplier reaches the scorer without reaching the bound: at any
non-default weight the two paths silently return different documents.

## Why these are facts in the record, not derivations at query time

`mtime` and `superseded` are committed. Two reasons:

1. **The scan cannot shell out.** Deriving a git timestamp per document at
   query time means one subprocess per candidate; the whole design is that a
   query touches the index and nothing else.
2. **They must be identical on every clone.** A derivation from local
   filesystem mtimes would differ per machine and break L3. A git commit
   timestamp is a property of the history every clone shares.

The *weights* applied to them are tunable (`tune.toml`); the facts are not.
That is the ADR-TUNE decision 1 split, on the right side of the line.
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
    the same rule ADR-DIR-LIST decision 10 applies to `archived` — a path
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


def recency_multiplier(mtime: int | None, newest: int, half_life_days: float) -> float:
    """A gentle exponential decay, normalised so the newest document is `1.0`.

    `half_life_days <= 0` disables it and returns `1.0` — the shipped default,
    so no corpus changes ranking until someone asks for it.

    **Bounded below by design.** The multiplier is in `(0, 1]`, so recency can
    demote an old document but can never promote a new one past a genuinely
    better match by an unbounded factor. An unbounded prior on a fact nobody
    calibrated is how a ranking becomes a date sort.
    """
    if half_life_days <= 0 or mtime is None or newest <= 0:
        return 1.0
    age_days = max(0.0, (newest - mtime) / 86400.0)
    return 0.5 ** (age_days / half_life_days)
