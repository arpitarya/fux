"""`seeded copies removable` — W-289 (SR-PLUGINS P9), on W-262's stamp.

A pre-W-289 `fux setup` seeded every decoder and fetcher into `.fux/` with a
first-line stamp naming the sha256 of the template it came from. Setup seeds
nothing now: the declared package runs, and a same-named file in `.fux/`
OVERRIDES it (P8). So an **unedited** copy — its body still hashes to its stamp
— is fux's code pinned in place, and `fux doctor` names it as removable.
**fux never deletes it** (SR-DOTFUX decision 6): the last tests here are the
ones that matter most.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from fux import doctor, plugins
from fux import setup as setup_mod

ROW = "seeded copies removable"


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / ".git").mkdir()
    setup_mod.run(tmp_path, agents=False)
    plugins.reset()
    yield tmp_path
    plugins.reset()


def _seed(root: Path, rel: str, body: bytes) -> Path:
    """What a pre-W-289 setup wrote: the stamp, then the template's bytes."""
    path = root / ".fux" / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(setup_mod.stamped(body))
    return path


def _row(root: Path) -> doctor.Check:
    return doctor._seeded_copies_removable(root)


def test_setup_seeds_nothing(repo: Path):
    assert not (repo / ".fux" / "decoders").exists()
    assert not (repo / ".fux" / "fetchers").exists()
    check = _row(repo)
    assert check.ok and check.level == "warn"
    assert "no unedited seeded copy" in check.detail


def test_the_seeded_set_is_both_fetchers_and_every_built_in_decoder():
    from fux.decode import BUILTIN_MODULES

    paths = [rel for _, _, rel in setup_mod.seeded_paths()]
    assert paths[:2] == ["fetchers/cdp.py", "fetchers/http.py"]
    assert sorted(paths[2:]) == sorted(f"decoders/{m}.py" for m in BUILTIN_MODULES)


def test_an_unedited_decoder_copy_is_named_as_removable(repo: Path):
    _seed(repo, "decoders/pdf.py", b"# the template as an older fux shipped it\n")
    check = _row(repo)
    assert not check.ok and check.level == "warn"
    assert ".fux/decoders/pdf.py" in check.detail
    assert "delete them yourself" in check.detail


def test_an_unedited_fetcher_copy_waits_for_its_package_to_be_declared(repo: Path):
    _seed(repo, "fetchers/http.py", b"def fetch(url):\n    return b'', 'text/html'\n")
    check = _row(repo)
    assert "declare fux-fetcher-http first" in check.detail
    plugins.path(repo).write_text(plugins.render([plugins.pin("fux-fetcher-http")]), encoding="utf-8")
    plugins.reset()
    check = _row(repo)
    assert ".fux/fetchers/http.py" in check.detail
    assert "declare fux-fetcher-http first" not in check.detail


def test_an_edited_copy_is_the_consumers_and_is_not_named(repo: Path):
    edited = _seed(repo, "fetchers/http.py", b"def fetch(url):\n    pass\n")
    edited.write_bytes(edited.read_bytes() + b"\n# my own change\n")
    check = _row(repo)
    assert check.ok
    assert "http.py" not in check.detail
    assert "1 edited" in check.detail


def test_an_unstamped_copy_is_counted_never_judged(repo: Path):
    """A repo seeded before W-262 has no stamp; whether it was edited is
    unanswerable, so the row counts it and draws no conclusion."""
    path = repo / ".fux" / "decoders" / "json.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"EXTENSIONS = ('.json',)\n")
    check = _row(repo)
    assert check.ok
    assert "1 unstamped" in check.detail


def test_crlf_checkout_of_an_unedited_copy_is_still_unedited(repo: Path):
    """`core.autocrlf` must not turn every unedited copy into an edited one."""
    path = _seed(repo, "decoders/toml.py", b"a\nb\n")
    path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
    check = _row(repo)
    assert "edited (yours" not in check.detail
    assert ".fux/decoders/toml.py" in check.detail


def test_neither_doctor_nor_setup_ever_deletes_or_rewrites_a_copy(repo: Path):
    """🔴 Never a rewrite and never a deletion (SR-DOTFUX decision 6). The
    copy's bytes survive a full `doctor` run, `doctor --fix`'s writer, and
    `fux setup`."""
    path = _seed(repo, "decoders/yaml.py", b"# older template\n")
    before = path.read_bytes()
    doctor.run(repo)
    setup_mod.fill_missing(repo)
    setup_mod.run(repo, agents=False)
    assert path.read_bytes() == before


def test_the_row_is_in_the_full_doctor_run(repo: Path):
    assert ROW in {c.name for c in doctor.run(repo)}
