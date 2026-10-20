"""The decoder registry is gated on `.fux/plugins.toml` — SR-PLUGINS, W-289 phase 2.

Each test names the decision it holds:

- **P3** a decoder runs only when its package is declared; an installed package
  nobody declared is never imported, and its format is never read as prose;
- **P8** `.fux/decoders/<module>.py` beats the declared package, which beats
  nothing;
- **P5** `fux ingest` counts, per suffix and on stderr, the source files no
  declared package reads — and says *prose only* when there is no declaration;
- **P4** a declared package that is missing or drifted stops every verb that
  reads the index or ingests, before anything is written; `fux doctor` and
  `fux setup` still run.

The real-venv half of P13 — two environments, one with an extra undeclared
package installed, byte-identical indexes — is `tests_e2e/test_plugin_l4_gate.py`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from fux import decode, plugins
from fux import setup as setup_mod
from fux.cli import main
from l12_fixtures import write_plugins

PDF = b"%PDF-1.4\n1 0 obj\n<< >>\nendobj\ntrailer\n<< >>\n%%EOF\n"


@pytest.fixture(autouse=True)
def _fresh_cache():
    plugins.reset()
    yield
    plugins.reset()


@pytest.fixture
def repo(tmp_path: Path, monkeypatch) -> Path:
    """Markdown, two PDFs and a JSON file; `fux setup` run; JSON declared alone."""
    (tmp_path / ".git").mkdir()
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "a.md").write_text("# Alpha\n\nrollback the broker\n", encoding="utf-8")
    (docs / "b.json").write_text('{"service": "ledger"}\n', encoding="utf-8")
    (docs / "c.pdf").write_bytes(PDF)
    (docs / "d.pdf").write_bytes(PDF)
    setup_mod.run(tmp_path, agents=False)
    write_plugins(tmp_path, ["fux-decoder-json"], force=True)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _loads(monkeypatch) -> list[tuple[str, str]]:
    calls: list[tuple[str, str]] = []
    real = plugins.load_decoder

    def spy(decl, module):
        calls.append((decl.name, module))
        return real(decl, module)

    monkeypatch.setattr(plugins, "load_decoder", spy)
    return calls


# -- P3 -----------------------------------------------------------------------


def test_only_a_declared_package_is_imported(repo, monkeypatch):
    calls = _loads(monkeypatch)
    loaded = decode.registry(repo)
    assert {name for name, _ in calls} == {"fux-decoder-json"}
    assert ".json" in loaded and ".jsonl" in loaded
    assert ".pdf" not in loaded, "fux-decoder-pdf is installed here and was NOT declared"


def test_no_declaration_means_prose_only(tmp_path, monkeypatch):
    (tmp_path / ".git").mkdir()
    calls = _loads(monkeypatch)
    assert decode.registry(tmp_path) == {}
    assert calls == []
    assert decode.decode(b'{"a": 1}', "x.json", tmp_path) is None


def test_an_undeclared_format_leaves_the_allowlist(repo):
    """SR-TYPES decision 1: prose plus every suffix a DECLARED package claims."""
    from fux.acquire.gitdir import read_types

    types = read_types(repo)
    assert types.accepts("docs/b.json") and types.accepts("docs/a.md")
    assert not types.accepts("docs/c.pdf")
    write_plugins(repo, ["fux-decoder-json", "fux-decoder-pdf"], force=True)
    assert read_types(repo).accepts("docs/c.pdf"), "declaring the package is the whole change"


# -- P8 -----------------------------------------------------------------------


def test_a_consumer_file_beats_the_declared_package(repo, monkeypatch):
    folder = repo / ".fux" / "decoders"
    folder.mkdir(parents=True)
    (folder / "json.py").write_text(
        "EXTENSIONS = ('.json',)\ndef decode(raw, rel_path):\n    return '# mine'\n",
        encoding="utf-8",
    )
    calls = _loads(monkeypatch)
    loaded = decode.registry(repo)
    assert loaded[".json"].origin.endswith("json.py") and ".fux" in loaded[".json"].origin
    assert ("fux-decoder-json", "json") not in calls, "the overridden module was imported"
    assert loaded[".jsonl"].origin.startswith("pkg:fux-decoder-json@")


def test_a_consumer_file_reads_its_format_with_no_package_declared(repo):
    write_plugins(repo, [], force=True)
    folder = repo / ".fux" / "decoders"
    folder.mkdir(parents=True)
    (folder / "pdf.py").write_text(
        "EXTENSIONS = ('.pdf',)\ndef decode(raw, rel_path):\n    return '# consumer pdf'\n",
        encoding="utf-8",
    )
    assert decode.decode(PDF, "docs/c.pdf", repo) == "# consumer pdf"
    assert ".pdf" not in plugins.unread(repo), "an override reads the format; P5 has nothing to say"


# -- P5 -----------------------------------------------------------------------


def test_ingest_counts_undeclared_formats_on_stderr(repo, capsys):
    assert main(["ingest", "--no-fetch"]) == 0
    captured = capsys.readouterr()
    assert "2 .pdf file(s) not read" in captured.err
    assert "fux-decoder-pdf" in captured.err
    assert ".pdf" not in captured.out, "the count is stderr's, so a piped ingest is unchanged"
    register = (repo / ".fux" / "index" / "REGISTER").read_text(encoding="utf-8")
    assert "docs/b.json" in register and "docs/c.pdf" not in register


def test_ingest_without_a_declaration_says_prose_only(repo, capsys):
    plugins.path(repo).unlink()
    assert main(["ingest", "--no-fetch"]) == 0
    err = capsys.readouterr().err
    assert "no .fux/plugins.toml - only Markdown and plain text are read" in err
    assert "fux setup" in err
    assert "1 .json file(s) not read" in err and "2 .pdf file(s) not read" in err


# -- P4 -----------------------------------------------------------------------


def _drift(root: Path) -> None:
    path = plugins.path(root)
    text = path.read_text(encoding="utf-8")
    start = text.index('digest = "sha256:') + len('digest = "sha256:')
    path.write_text(text[:start] + "0" * 64 + text[start + 64:], encoding="utf-8")
    plugins.reset()


@pytest.mark.parametrize("argv", [["ingest", "--no-fetch"], ["ask", "broker"], ["find", "broker"]])
def test_a_drifted_package_stops_every_verb_that_reads_or_ingests(repo, capsys, argv):
    _drift(repo)
    assert main(argv) != 0
    err = capsys.readouterr().err
    assert "fux-decoder-json" in err and "drifted" in err and "SR-PLUGINS P4" in err
    assert not (repo / ".fux" / "index").exists(), "an index was written past P4"


def test_doctor_and_setup_still_run_with_a_drifted_package(repo, capsys):
    _drift(repo)
    main(["doctor"])
    out = capsys.readouterr()
    assert "plugins installed" in out.out, "doctor ran its rows"
    assert not out.err.startswith("error: .fux/plugins.toml")
    assert main(["setup", "--pin", "--no-agents"]) == 0
    plugins.reset()
    assert plugins.problems(repo) == [], "setup --pin re-pinned the drifted row"
