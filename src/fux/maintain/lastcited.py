"""What the last answer to this question cited — W-82 §3.4.

Arpit's sentence was *"if nothing has changed, then give the same old answer."*
The comparison it wants — **did the cited bytes move?** — is already performed on
every `fux answer`: the refer plane fetches each cited source and compares
`fetched_sha` against `indexed_sha`. What was missing is only the **memory of
what was said last time**.

## This is a report, not a memo — and the distinction is the whole design

**No answer is stored and nothing is ever replayed.** Every answer is recomputed
on freshly fetched bytes, per the 2026-08-26 ruling that a URL's actual document
is fetched before any final answer.

The memo that was *not* built is recorded in W-82 §6.0 with its reasoning. In
short: `fux answer` is model-free and deterministic, and ARC is keyed
`(loc, sha)`, so identical bytes give an identical answer **by construction**.
Caching the output of a pure function whose inputs were just downloaded buys
rescore+assemble — stdlib CPU on bytes already in hand — and costs three real
hazards, of which the sharpest is that a memo validated by a TTL hit would
replay an answer on bytes nobody confirmed while reporting `current`.

**Storing only `(loc, sha)` cannot have that failure**, because there is no
stored answer to serve. The worst this can do is say *"unchanged"* about a
question whose answer it does not hold.

## Why it needs no fifth verdict label

[ADR-REFER](../../../docs/adr/0030_refer-plane.md) decision 6's labels —
`current` / `stale` / `unverified` / `cached` — are **per-citation** facts about
one fetch. This is a **per-answer** statement about the relationship between two
runs. Different object, different place, so nothing here folds *"we did not
look"* into *"we looked and it was fine"*.

## Advisory, gitignored, and off the byte-identical path

Lives in `.fux/runtime/` beside the other derived planes. Every failure — absent,
corrupt, unwritable — degrades to *"no previous answer"*. **The report is written
to stderr, never stdout**, so `fux answer`'s stdout stays byte-identical with
this feature on or off, exactly as W-64 required of the progress plane.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from ..store import fuxdir

LOG_NAME = "last-cited.json"

#: Bound on remembered questions. A local diagnostic must not grow without
#: limit; the oldest entries are dropped by insertion order, which is enough
#: for a feature whose value is entirely in the *most recent* repeat.
MAX_QUESTIONS = 256


def key_for(query: str) -> str:
    """A stable id for *the same question asked again*.

    Whitespace-normalised and lowercased, then hashed: a repeat with different
    spacing is the same question, and hashing keeps the user's query text out of
    a file that lands in a shared checkout's working tree. The store is
    gitignored, but keeping plaintext questions out of it costs one line.
    """
    normal = " ".join(query.split()).lower()
    return hashlib.sha256(normal.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class Change:
    """The verdict on one repeat of a question."""

    #: `True` the first time a question is asked — nothing to compare against.
    first_time: bool
    #: Locators whose sha differs from the previous answer's.
    changed: tuple[str, ...]
    #: Locators cited now that were not cited before (and vice versa).
    added: tuple[str, ...]
    removed: tuple[str, ...]

    @property
    def anything_changed(self) -> bool:
        return bool(self.changed or self.added or self.removed)

    def line(self) -> str:
        """One ASCII line for stderr, or `""` when there is nothing to say.

        ASCII only: these bytes reach a Windows console, whose default codepage
        cannot encode arrows or dashes and **crashes `print()` rather than
        degrading** (ADR-CLI veto 7, and a shipped defect twice).
        """
        if self.first_time:
            return ""
        if not self.anything_changed:
            return "note: nothing has changed since you last asked this."
        parts = []
        if self.changed:
            parts.append(f"{len(self.changed)} source(s) changed: {', '.join(self.changed[:3])}")
        if self.added:
            parts.append(f"{len(self.added)} newly cited")
        if self.removed:
            parts.append(f"{len(self.removed)} no longer cited")
        return "note: " + "; ".join(parts) + "."


def _path(root: Path) -> Path:
    return fuxdir.fux_dir(root) / "runtime" / LOG_NAME


def _read(root: Path) -> dict:
    try:
        raw = json.loads(_path(root).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return raw if isinstance(raw, dict) else {}


def compare(root: Path, query: str, cited: dict[str, str]) -> Change:
    """What changed since this question was last asked. **Reads only.**

    `cited` maps locator -> the sha actually cited this time. Separating this
    from `remember` is deliberate: a caller can report without recording (a
    dry run, a test), and the recording step cannot accidentally become the
    thing that decides the verdict.
    """
    previous = _read(root).get(key_for(query))
    if not isinstance(previous, dict):
        return Change(first_time=True, changed=(), added=(), removed=())
    prior = {k: v for k, v in previous.items() if isinstance(k, str) and isinstance(v, str)}
    changed = tuple(sorted(loc for loc, sha in cited.items() if loc in prior and prior[loc] != sha))
    added = tuple(sorted(set(cited) - set(prior)))
    removed = tuple(sorted(set(prior) - set(cited)))
    return Change(first_time=False, changed=changed, added=added, removed=removed)


def remember(root: Path, query: str, cited: dict[str, str]) -> None:
    """Record what this answer cited. **Best-effort; never raises.**

    A diagnostic that can fail an answer is worse than no diagnostic — the same
    rule the detector and the URL health counter follow.
    """
    try:
        store = _read(root)
        store[key_for(query)] = dict(cited)
        while len(store) > MAX_QUESTIONS:
            store.pop(next(iter(store)))
        directory = fuxdir.derived_dir(root, "runtime")
        text = json.dumps(store, indent=2, sort_keys=True) + "\n"
        (directory / LOG_NAME).write_text(text, encoding="utf-8")
    except Exception:  # pragma: no cover - a report must not break an answer
        pass
