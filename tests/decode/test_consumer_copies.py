"""`fux setup` writes every built-in decoder into `.fux/decoders/`, and the copy
is what runs — W-86 P7, ruled by Arpit 2026-08-26.

The consequence that makes these tests worth having: **after setup, the modules
inside the installed package never execute.** A repo's decoders are its own
files. That is the intended behaviour, and it means two things have to hold or
the whole plane is quietly broken:

* every copied file must **load standalone**, with no parent package to resolve
  a relative import against;
* the copy must be **byte-identical** to what fux ships, because a transform at
  copy time would mean the file fux tests and the file the consumer runs are
  different files.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from fux import setup as setup_mod
from fux.decode import BUILTIN_MODULES, decode, registry


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / ".git").mkdir()
    setup_mod.run(tmp_path, agents=False)
    return tmp_path


def test_setup_writes_every_builtin_decoder(repo: Path):
    written = sorted(p.stem for p in (repo / ".fux" / "decoders").glob("*.py"))
    assert written == sorted(BUILTIN_MODULES)


def test_the_copy_is_byte_identical_to_the_shipped_module(repo: Path):
    """No transform at copy time. A rewritten import, a stamped header, anything
    — and the file fux tests stops being the file the consumer runs, which is
    the entire failure mode this plane was created to remove.
    """
    package = Path(setup_mod.__file__).parent / "decode"
    for name in BUILTIN_MODULES:
        shipped = (package / f"{name}.py").read_bytes()
        copied = (repo / ".fux" / "decoders" / f"{name}.py").read_bytes()
        assert copied == shipped, f"{name} was altered on the way out"


def test_every_copied_decoder_loads_standalone(repo: Path):
    """A path-loaded file has no parent package, so a relative import raises
    `attempted relative import with no known parent package`. The modules use
    absolute imports for exactly this reason; without it every copy carrying a
    helper import would be dead on arrival.
    """
    loaded = registry(repo)
    assert loaded, "no decoder loaded from the consumer directory"
    for decoder in set(loaded.values()):
        assert ".fux/decoders/" in decoder.origin.replace("\\", "/")


def test_the_copy_runs_not_the_packaged_module(repo: Path):
    marker = repo / ".fux" / "decoders" / "htmldoc.py"
    source = marker.read_text()
    marker.write_text(
        source.replace(
            'EXTENSIONS = (".html", ".htm", ".xhtml")',
            'EXTENSIONS = (".html", ".htm", ".xhtml")\n_EDITED = True',
        ).replace("    html = raw.decode(_charset(raw), errors=\"replace\")",
                  "    return '# edited by the consumer'\n    html = raw.decode(_charset(raw), errors=\"replace\")")
    )
    assert decode(b"<h1>original</h1>", "a.html", repo) == "# edited by the consumer"


def test_a_deleted_copy_falls_back_to_the_packaged_module(repo: Path):
    """Deleting a decoder must not remove the format — it restores the built-in.

    Without this, `rm .fux/decoders/pdfdoc.py` would silently stop indexing every
    PDF in the corpus, which looks identical to a corpus that has no PDFs.
    """
    (repo / ".fux" / "decoders" / "htmldoc.py").unlink()
    out = decode(b"<h1>Still here</h1>", "a.html", repo)
    assert out is not None and "Still here" in out
    assert registry(repo)[".html"].origin.startswith("built-in:")


def test_setup_never_overwrites_an_edited_decoder(repo: Path):
    edited = repo / ".fux" / "decoders" / "jsondoc.py"
    edited.write_text("EXTENSIONS = ('.json',)\ndef decode(raw, rel_path):\n    return '# mine'\n")
    report = setup_mod.run(repo, agents=False)
    assert edited.read_text().endswith("return '# mine'\n")
    assert ".fux/decoders/jsondoc.py" in report.kept


def test_the_decoders_directory_is_declared(repo: Path):
    """`fux doctor` warns on anything undeclared at the top of `.fux/`. A new
    plane that forgets its declaration ships a warning to every consumer.
    """
    from fux.store import fuxdir

    assert "decoders" in fuxdir.DECLARED
    readme = (repo / ".fux" / "README.md").read_text()
    assert "decoders" in readme


def test_the_decoders_directory_is_not_gitignored(repo: Path):
    """It is consumer source and it is committed. A blanket ignore here would
    drop sixteen files a consumer owns out of git without a word — the defect
    `.fux/.gitignore`'s own comment warns about.
    """
    ignored = (repo / ".fux" / ".gitignore").read_text()
    assert "decoders" not in ignored.replace("`.fux/decoders/`", "")
