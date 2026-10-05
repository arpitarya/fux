"""`seeded copies current` — W-262, Arpit 2026-10-04, W-251 #2 (option B).

`fux setup` stamps every decoder and fetcher copy with the sha256 of the
template it came from. `fux doctor` names an **unedited** copy whose template
has since changed, with the lever *re-seed it yourself* — and **fux never
writes the file**. Option A (refresh unedited copies on upgrade) was refused in
the same ruling, so the last test here is the one that matters most.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from fux import doctor
from fux import setup as setup_mod

ROW = "seeded copies current"


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / ".git").mkdir()
    setup_mod.run(tmp_path, agents=False)
    return tmp_path


def _row(root: Path) -> doctor.Check:
    return doctor._seeded_copies_current(root)


def test_setup_stamps_every_fetcher_and_decoder(repo: Path):
    for rel, template in setup_mod.seeded_copies():
        raw = (repo / ".fux" / rel).read_bytes()
        stamp, body = setup_mod.read_stamp(raw)
        assert body == template, rel
        assert stamp == setup_mod.template_digest(template), rel


def test_a_fresh_setup_is_current(repo: Path):
    check = _row(repo)
    assert check.ok
    assert check.level == "warn"
    assert f"{len(setup_mod.seeded_copies())} unedited" in check.detail


def test_an_unedited_copy_of_an_older_template_is_named_with_the_lever(repo: Path):
    stale = repo / ".fux" / "decoders" / "pdf.py"
    stale.write_bytes(setup_mod.stamped(b"# the template as an older fux shipped it\n"))
    check = _row(repo)
    assert not check.ok
    assert check.level == "warn"
    assert ".fux/decoders/pdf.py" in check.detail
    assert "re-seed it yourself" in check.detail
    assert "fux setup" in check.detail


def test_an_edited_copy_is_the_consumers_and_is_not_named(repo: Path):
    edited = repo / ".fux" / "fetchers" / "http.py"
    edited.write_bytes(edited.read_bytes() + b"\n# my own change\n")
    check = _row(repo)
    assert check.ok
    assert "http.py" not in check.detail
    assert "1 edited" in check.detail


def test_an_edited_copy_of_an_older_template_is_still_not_named(repo: Path):
    """Edited wins over stale: a consumer who changed the file owns it, whatever
    the template has done since. Only an unedited copy is a fux finding."""
    path = repo / ".fux" / "decoders" / "csv.py"
    path.write_bytes(setup_mod.stamped(b"old\n") + b"# edited\n")
    check = _row(repo)
    assert check.ok
    assert "csv.py" not in check.detail


def test_an_unstamped_copy_is_counted_never_judged(repo: Path):
    """A repo seeded before W-262 has no stamp; whether it was edited is
    unanswerable, so the row counts it and draws no conclusion."""
    path = repo / ".fux" / "decoders" / "json.py"
    path.write_bytes(setup_mod.decoder_source("json"))
    check = _row(repo)
    assert check.ok
    assert "1 unstamped" in check.detail


def test_crlf_checkout_of_an_unedited_copy_is_still_unedited(repo: Path):
    """`core.autocrlf` must not turn every unedited copy into an edited one."""
    path = repo / ".fux" / "decoders" / "toml.py"
    path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
    check = _row(repo)
    assert check.ok
    assert "edited (yours" not in check.detail


def test_neither_doctor_nor_setup_ever_rewrites_a_stale_copy(repo: Path):
    """🔴 Option B: never a rewrite (SR-DOTFUX decision 6). The stale copy's
    bytes survive a full `doctor` run, `doctor --fix`'s writer, and `fux setup`."""
    stale = repo / ".fux" / "decoders" / "yaml.py"
    before = setup_mod.stamped(b"# older template\n")
    stale.write_bytes(before)
    doctor.run(repo)
    setup_mod.fill_missing(repo)
    report = setup_mod.run(repo, agents=False)
    assert stale.read_bytes() == before
    assert ".fux/decoders/yaml.py" in report.kept


def test_the_row_is_in_the_full_doctor_run(repo: Path):
    assert ROW in {c.name for c in doctor.run(repo)}
