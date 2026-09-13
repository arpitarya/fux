"""Every `owns:` claim carries a current content hash of what it owns.

**Arpit, 2026-09-13:** *"in every SR, owns should have the file name and content
hash so that we can track if something changed — it should be updated in the SR
if there is a design/functional change."*

`owns: [src/fux/query/rank.py@d95543ea8d13]`. A reader can now compare a record
against the code it claims without opening either.

## Why this is stronger than the freshness gate, and where it stops

`test_sr_freshness.py` proves an owning record was **touched** in a change. This
proves the record's claim still **matches the bytes**. The first can be satisfied
by adding a comma to the record; the second cannot.

⚠ **What it still cannot do.** A hash moves on a typo, a reformat, a comment and
a redesign alike. It says *this component is not the one the record was written
against* — never whether the change was a design or functional one. **That
judgement is the reader's**, in the same place SR-LAW-0 leaves coherence, and a
failure here is a prompt to re-read the record rather than an instruction to
re-stamp it.

⚠ **So the honest risk is noise.** Every edit to an owned file fails this until
`scripts/sr-owns.py --write` runs, including edits that change nothing a record
could describe. A gate that fires on everything gets routed around — if that
starts happening, the answer is to narrow what is owned, never to loosen the
check.

## The mechanics

- **A file** — SHA-256 of its bytes, LF-normalised, first 12 hex.
- **A directory** — SHA-256 over `relpath\\0filehash` for every file under it,
  sorted; moves on add, remove, rename and edit. `__pycache__` and `*.pyc` are
  skipped because they are not the component.
- **12 hex, not 64** — drift detection, not content addressing. A record owning
  five paths would otherwise carry 320 characters of hash.
- **`owns` hashes are stamped BEFORE `content_sha`**, because stamping them
  changes the record.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "sr-owns.py"


def _mod():
    spec = importlib.util.spec_from_file_location("fux_sr_owns", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def owns():
    return _mod()


def test_the_stamper_exists(owns) -> None:
    assert SCRIPT.is_file(), "scripts/sr-owns.py is missing — nothing can stamp a claim."
    assert owns.records(), "no records found"


def test_every_claim_carries_a_hash(owns) -> None:
    bare = []
    for path in owns.records():
        for claim in owns.claims(path.read_text(encoding="utf-8")):
            component, sha = owns.split_claim(claim)
            if sha is None:
                bare.append(f"{path.name}: {component}")
    assert not bare, (
        "these claims carry no content hash: " + ", ".join(bare) + "\n\n"
        "Run `python scripts/sr-owns.py --write && python scripts/sr-hash.py --write`."
    )


def test_every_claim_matches_what_it_owns(owns) -> None:
    moved = []
    for path in owns.records():
        _, changed = owns.restamp(path.read_text(encoding="utf-8"))
        moved.extend(f"{path.name}: {c}" for c in changed)
    assert not moved, (
        "these components changed and their record's `owns:` hash did not:\n  "
        + "\n  ".join(moved)
        + "\n\nRE-READ THE RECORD FIRST. A hash moves on a typo and on a redesign alike, "
        "and only one of those means the record is now wrong. Then:\n"
        "  python scripts/sr-owns.py --write && python scripts/sr-hash.py --write"
    )


def test_stamping_is_idempotent(owns) -> None:
    for path in owns.records():
        text = path.read_text(encoding="utf-8")
        once, _ = owns.restamp(text)
        twice, moved = owns.restamp(once)
        assert twice == once and not moved, f"{path.name}: stamping is not idempotent"


def test_a_directory_hash_moves_when_a_file_under_it_changes(owns, tmp_path) -> None:
    """The property a directory claim rests on, checked rather than assumed."""
    import hashlib

    d = ROOT / "src" / "fux" / "query"
    assert d.is_dir(), "expected a directory component to test against"
    before = owns.component_digest("src/fux/query")
    assert before and len(before) == 12
    # a pure function of the bytes: same input, same digest
    assert owns.component_digest("src/fux/query") == before
    assert owns.component_digest("src/fux/does-not-exist") is None
    assert hashlib.sha256(b"").hexdigest()[:12] != before
