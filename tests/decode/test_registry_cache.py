"""W-239 — `registry()` and `meta_bindings()` are cached per process.

`registry()` runs two or three times per ingested document, and until
2026-09-29 each call re-executed every `.fux/decoders/*.py`: 58 000 imports on
a 1 000-document corpus. `meta_bindings()` re-parsed `.fux/formats.toml` per
document. Both are pure functions of committed files, so they are now cached on
those files' stat — and the cache must never serve an edit stale.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from fux import decode
from fux.errors import FuxError
from fux.ingest import typesfile


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / ".git").mkdir()
    (tmp_path / ".fux" / "decoders").mkdir(parents=True)
    return tmp_path


def _decoder(root: Path, name: str, marker: str) -> Path:
    """A consumer decoder that records each time its module body runs."""
    log = root / f"{name}.imports"
    path = root / ".fux" / "decoders" / f"{name}.py"
    path.write_text(
        f"open({str(log)!r}, 'a').write('x')\n"
        f"EXTENSIONS = ('.foo',)\n"
        f"def decode(raw, rel_path):\n"
        f"    return '# {marker}'\n",
        encoding="utf-8",
    )
    return path


def _imports(root: Path, name: str) -> int:
    log = root / f"{name}.imports"
    return len(log.read_text()) if log.exists() else 0


def _bump(path: Path) -> None:
    """Move mtime forward by a whole second, so a coarse-mtime filesystem sees it."""
    st = path.stat()
    os.utime(path, ns=(st.st_atime_ns, st.st_mtime_ns + 1_000_000_000))


def test_a_consumer_decoder_is_imported_once_across_calls(repo: Path):
    _decoder(repo, "foo", "one")
    for _ in range(5):
        assert decode.registry(repo)[".foo"].name == "foo"
    assert _imports(repo, "foo") == 1


def test_an_edited_decoder_is_picked_up_in_the_same_process(repo: Path):
    path = _decoder(repo, "foo", "one")
    assert decode.registry(repo)[".foo"](b"", "a.foo") == "# one"
    _decoder(repo, "foo", "two")
    _bump(path)
    assert decode.registry(repo)[".foo"](b"", "a.foo") == "# two"
    assert _imports(repo, "foo") == 2


def test_an_added_or_removed_decoder_is_seen(repo: Path):
    assert ".foo" not in decode.registry(repo)
    path = _decoder(repo, "foo", "one")
    assert ".foo" in decode.registry(repo)
    path.unlink()
    assert ".foo" not in decode.registry(repo)


def test_a_helper_edit_invalidates_too(repo: Path):
    """A `_helper.py` is not a decoder, but a decoder may import it."""
    _decoder(repo, "foo", "one")
    decode.registry(repo)
    helper = repo / ".fux" / "decoders" / "_shared.py"
    helper.write_text("X = 1\n", encoding="utf-8")
    decode.registry(repo)
    assert _imports(repo, "foo") == 2


def test_a_broken_decoder_raises_on_every_call(repo: Path):
    (repo / ".fux" / "decoders" / "bad.py").write_text("raise RuntimeError('no')\n", encoding="utf-8")
    for _ in range(2):
        with pytest.raises(FuxError, match="failed to import"):
            decode.registry(repo)


def test_a_caller_cannot_poison_the_cache(repo: Path):
    _decoder(repo, "foo", "one")
    decode.registry(repo).clear()
    assert ".foo" in decode.registry(repo)


def _formats(root: Path, meta: dict[str, str]) -> Path:
    path = root / ".fux" / "formats.toml"
    text = typesfile.render([], {}, grouped=True)
    text += "\n[meta]\n" + "".join(f'{k} = "{v}"\n' for k, v in meta.items())
    path.write_text(text, encoding="utf-8")
    return path


def test_meta_bindings_parse_the_file_once_and_see_an_edit(repo: Path, monkeypatch):
    path = _formats(repo, {"owner": "ctx"})
    real = typesfile.read
    calls = []
    monkeypatch.setattr(typesfile, "read", lambda *a, **k: calls.append(1) or real(*a, **k))
    for _ in range(4):
        assert decode.meta_bindings(repo) == {"owner": "ctx"}
    assert len(calls) == 1
    _formats(repo, {"owner": "none"})
    _bump(path)
    assert decode.meta_bindings(repo) == {"owner": "none"}
    decode.meta_bindings(repo)["owner"] = "title"  # a caller's copy, not the cache
    assert decode.meta_bindings(repo) == {"owner": "none"}
