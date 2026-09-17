"""W-166 DoD 1 — every built-in decoder carries a `VERSION`, and it is the key.

**Why a constant and not a file sha.** `binding_digests` explains the split: fux
owns this tree and can require a hand bump, and a constant does not move on a
comment. The price is that a constant nobody is made to bump stops being true —
so the discipline is a test, not a note.

⚠ **The freshness half checks the WORKING TREE against `HEAD`**, which CLAUDE.md
names as a hazard: CI reads commits, so a red here is invisible until somebody
commits. Every other test in this file needs no git and cannot go unseen.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from fux import decode
from fux.ingest import decoderdigest

ROOT = Path(__file__).resolve().parents[2]
DECODE_DIR = "src/fux/decode"


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
        env={"GIT_OPTIONAL_LOCKS": "0", "PATH": "/usr/bin:/bin:/usr/local/bin"},
    ).stdout


def test_every_builtin_module_declares_a_version():
    missing = []
    for name in decode.BUILTIN_MODULES:
        module = __import__(f"fux.decode.{name}", fromlist=["VERSION"])
        version = getattr(module, "VERSION", None)
        if not isinstance(version, int) or version < 1:
            missing.append(name)
    assert not missing, (
        "these built-in decoders declare no integer `VERSION >= 1`:\n  "
        + "\n  ".join(missing)
        + "\n\nIt is what the reuse key compares; without it the decoder's "
        "digest is `<name>@0` and every version of that decoder looks alike."
    )


def test_every_binding_has_a_digest_naming_its_decoder():
    for ext, digest in decoderdigest.binding_digests().items():
        assert "@" in digest, ext
        name, _, version = digest.partition("@")
        assert name and version, ext
        assert decode.registry()[ext].name == name, ext


def test_a_version_bump_changes_only_its_own_bindings(monkeypatch):
    """The design claim, asserted rather than described.

    A corpus-wide digest would re-extract the markdown corpus for a `.pptx` fix.
    Keyed by extension, the blast radius is the extensions that decoder claims —
    **all of them**, which is why this checks a multi-extension decoder.
    """
    import fux.decode.csv as csv_mod

    before = decoderdigest.binding_digests()
    monkeypatch.setattr(csv_mod, "VERSION", csv_mod.VERSION + 1)
    decode.registry.cache_clear() if hasattr(decode.registry, "cache_clear") else None
    after = decoderdigest.binding_digests()

    moved = {ext for ext in set(before) | set(after) if before.get(ext) != after.get(ext)}
    assert moved == {".csv", ".tsv"}, moved


def test_a_changed_builtin_decoder_bumped_its_version():
    """The freshness half — the same shape `test_sr_freshness` uses for records."""
    try:
        changed = set(_git("diff", "--name-only", "HEAD").split())
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("not a git checkout — nothing to audit")

    behind = []
    for name in decode.BUILTIN_MODULES:
        rel = f"{DECODE_DIR}/{name}.py"
        if rel not in changed:
            continue
        diff = _git("diff", "-U0", "HEAD", "--", rel)
        if not any(
            line.startswith(("+", "-")) and "VERSION" in line for line in diff.splitlines()
        ):
            behind.append(rel)

    assert not behind, (
        "these decoders changed and their `VERSION` did not:\n  "
        + "\n  ".join(behind)
        + "\n\nBump it if the edit can change what `decode()` RETURNS — the next "
        "`fux ingest` then re-extracts the documents bound to this decoder and no "
        "others. Leave it alone only for an edit that provably cannot move a byte "
        "of output, and touch the line in the same change either way so this check "
        "sees a decision rather than an omission."
    )
