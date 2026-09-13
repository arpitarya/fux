"""Every Standing Record carries a current `content_sha`.

**Arpit, 2026-09-13:** *"maintain a hash value of every SR in the frontmatter
itself so that we can tell when something got changed in the SR document."*

A record is **amended in place** — that is Law zero, and it is what makes an SR
an SR rather than a decision-log entry. The cost is that "which version of SR-X
was this written against?" has no answer from the file alone. `content_sha` is
that answer: quote it beside a citation, and a later reader can tell whether the
record has moved.

## What the hash covers

The whole file — frontmatter **and** body — with its own `content_sha:` line
removed, LF endings, UTF-8, SHA-256, full hex.

- **A hash cannot cover itself**, so that one line is excised before hashing.
  Recomputation is therefore stable: stamping a record twice is a no-op.
- **Hashing only the body was rejected.** `owns`, `status`, `laws` and `amended`
  could then change without moving the hash, and those are precisely the changes
  a reader pinning a version cares about.
- **Deterministic, as L3 requires:** same bytes in, same digest out. No clock,
  no path, no ordering dependence.

## What it does NOT do

⚠ **It tells you THAT a record moved, never what moved** — `git diff` does that,
and this test is not a substitute for reading the record. The value is outside
git: a vendored copy, an agent policy file, or a document that pins the version
of the rule it was written against.

⚠ **It is not a signature.** It proves nothing about who changed the record or
whether the change was ruled; it is a drift detector, not an authority.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "sr-hash.py"


def _hasher():
    """`scripts/sr-hash.py` as a module — imported by path, because `scripts/` is
    not a package and must not become one for one test."""
    spec = importlib.util.spec_from_file_location("fux_sr_hash", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def sr_hash():
    return _hasher()


def test_the_stamper_exists(sr_hash) -> None:
    assert SCRIPT.is_file(), "scripts/sr-hash.py is missing — nothing can stamp a record."
    assert sr_hash.records(), "no records found to hash"


def test_every_record_carries_a_current_content_sha(sr_hash) -> None:
    stale, missing = [], []
    for path in sr_hash.records():
        text = path.read_text(encoding="utf-8")
        have = sr_hash.current(text)
        if have is None:
            missing.append(path.name)
        elif have != sr_hash.digest(text):
            stale.append(path.name)
    assert not missing, (
        "these records carry no `content_sha`: " + ", ".join(missing) + "\n\n"
        "Run `python scripts/sr-hash.py --write`."
    )
    assert not stale, (
        "these records changed and their `content_sha` did not: " + ", ".join(stale) + "\n\n"
        "Run `python scripts/sr-hash.py --write` in the SAME change that amends the record — "
        "a hash stamped later describes a version nobody read."
    )


def test_stamping_is_idempotent(sr_hash) -> None:
    """Stamping twice must be a no-op, or the hash chases itself forever."""
    for path in sr_hash.records():
        once = sr_hash.stamped(path.read_text(encoding="utf-8"))
        assert sr_hash.stamped(once) == once, (
            f"{path.name}: stamping is not idempotent — the excision of the "
            "`content_sha:` line is not exact, so every run would produce a new digest."
        )


def test_the_digest_ignores_only_its_own_line(sr_hash) -> None:
    """The property the whole scheme rests on, checked rather than asserted."""
    sample = sr_hash.records()[0].read_text(encoding="utf-8")
    base = sr_hash.digest(sample)
    assert sr_hash.digest(sample.replace("\r\n", "\n")) == base, "line endings must not matter"
    moved = sample.replace("status: accepted", "status: proposed", 1)
    assert sr_hash.digest(moved) != base, (
        "a frontmatter change did not move the digest — the hash is covering the body only, "
        "which is the shape this test's docstring rejects."
    )
