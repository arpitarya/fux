"""W-295 -- the eight policy TOMLs live in `.fux/config/`.

`fux setup` MOVES a file from the pre-move address (byte for byte, mode kept),
refuses when a stem is at both, and every other verb stops loudly -- naming the
new address -- when one is still at the old address. There is no fallback
reader. [SR-DOTFUX](../records/0102_fux-directory.md) states the layout; this
file holds the behaviour.
"""

from __future__ import annotations

import os
import stat

import pytest

from fux import configfiles
from fux.cli import main
from fux.constants import fixed
from fux.errors import FuxError
from l12_fixtures import config_file

NAMES = ("formats", "identifiers", "inspect", "output", "pii", "plugins", "refusals", "tune")


def _old(root, name):
    return root / ".fux" / f"{name}.toml"


def _repo(tmp_path, *, names=NAMES):
    """A repo as an older `fux setup` left it: every named file at `.fux/<name>.toml`."""
    (tmp_path / ".fux").mkdir()
    (tmp_path / "fux.toml").write_text("", encoding="utf-8")
    for name in names:
        _old(tmp_path, name).write_text(f"# {name} -- mine\n", encoding="utf-8")
    return tmp_path


def test_the_set_is_the_eight_and_every_address_is_under_config_dir():
    assert configfiles.names() == NAMES
    for name in NAMES:
        assert fixed("files", name) == f"{fixed('files', 'config_dir')}/{name}.toml"
    # the [plugins] block spells the same address (SR-PLUGINS)
    assert fixed("plugins", "file") == fixed("files", "plugins")


def test_setup_moves_all_eight_byte_for_byte_and_keeps_the_mode(tmp_path, monkeypatch):
    _repo(tmp_path)
    secret = _old(tmp_path, "pii")
    secret.write_bytes(b"# pii \xe2\x80\x94 CRLF kept\r\n[[rule]]\r\n")
    secret.chmod(0o600)
    before = {n: _old(tmp_path, n).read_bytes() for n in NAMES}
    monkeypatch.chdir(tmp_path)

    assert main(["setup", "--no-agents"]) == 0

    for name in NAMES:
        assert not _old(tmp_path, name).exists(), name
        moved = config_file(tmp_path, name)
        assert moved.is_file(), name
    # the moved files are the SAME bytes, not a re-seeded or re-filled copy
    # (`fill_missing` may ADD keys to tune/output/inspect; pii and refusals are verbatim).
    assert config_file(tmp_path, "pii").read_bytes() == before["pii"]
    assert config_file(tmp_path, "refusals").read_bytes().startswith(before["refusals"])
    # Windows has no POSIX mode bits to keep: chmod sets only read-only there.
    if os.name != "nt":
        assert stat.S_IMODE(os.stat(config_file(tmp_path, "pii")).st_mode) == 0o600


def test_migrate_alone_is_a_pure_rename(tmp_path):
    _repo(tmp_path)
    before = {n: _old(tmp_path, n).read_bytes() for n in NAMES}
    moved = configfiles.migrate(tmp_path)
    assert moved == [f".fux/config/{n}.toml" for n in NAMES]
    for name in NAMES:
        assert config_file(tmp_path, name).read_bytes() == before[name]
        assert not _old(tmp_path, name).exists()
    assert configfiles.migrate(tmp_path) == []  # once


def test_a_stem_at_both_addresses_refuses_naming_both_and_touches_neither(tmp_path):
    _repo(tmp_path, names=("pii", "tune"))
    config_file(tmp_path, "tune").write_text("# the new one\n", encoding="utf-8")
    with pytest.raises(FuxError) as exc:
        configfiles.migrate(tmp_path)
    text = str(exc.value)
    assert ".fux/tune.toml" in text and ".fux/config/tune.toml" in text
    # all-or-nothing: `pii` (which had no clash) was NOT moved either
    assert _old(tmp_path, "pii").is_file()
    assert not config_file(tmp_path, "pii").exists()
    assert _old(tmp_path, "tune").read_text(encoding="utf-8") == "# tune -- mine\n"
    assert config_file(tmp_path, "tune").read_text(encoding="utf-8") == "# the new one\n"


def test_setup_on_a_clash_exits_nonzero_with_both_named(tmp_path, monkeypatch, capsys):
    _repo(tmp_path, names=("tune",))
    config_file(tmp_path, "tune").write_text("# new\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert main(["setup", "--no-agents"]) == 1
    err = capsys.readouterr().err
    assert ".fux/tune.toml" in err and ".fux/config/tune.toml" in err


def test_the_pii_hard_stop_says_it_moved_not_that_it_is_missing(tmp_path, monkeypatch, capsys):
    """An un-migrated repo must not read as a repo with no PII policy."""
    _repo(tmp_path, names=("pii",))
    monkeypatch.chdir(tmp_path)
    assert main(["find", "anything"]) == 1
    err = capsys.readouterr().err
    assert "`.fux/pii.toml` moved to `.fux/config/pii.toml`" in err
    assert "run `fux setup`" in err
    assert "missing" not in err


@pytest.mark.parametrize("name", NAMES)
def test_every_verb_but_setup_refuses_a_file_at_the_old_address(tmp_path, monkeypatch, capsys, name):
    _repo(tmp_path, names=(name,))
    config_file(tmp_path, "pii").write_text("", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    for verb in (["find", "x"], ["ingest"], ["ask", "x"]):
        assert main(verb) == 1
        err = capsys.readouterr().err
        assert f"`.fux/{name}.toml` moved to `.fux/config/{name}.toml`" in err
        assert "run `fux setup`" in err


def test_the_library_gate_says_the_same_sentence(tmp_path):
    import fux

    _repo(tmp_path, names=("pii", "tune"))
    with pytest.raises(FuxError, match=r"`\.fux/pii\.toml` moved to `\.fux/config/pii\.toml`"):
        fux.open(tmp_path)


def test_doctor_runs_and_fails_the_new_row(tmp_path, monkeypatch):
    from fux import doctor

    _repo(tmp_path, names=("pii", "output"))
    monkeypatch.chdir(tmp_path)
    rows = {c.name: c for c in doctor.run(tmp_path)}
    row = rows["config files at the pre-W-295 address"]
    assert row.ok is False
    assert "`.fux/pii.toml` moved to `.fux/config/pii.toml`" in row.detail
    assert "`.fux/output.toml` moved to `.fux/config/output.toml`" in row.detail
    assert "run `fux setup`" in row.detail


def test_doctor_row_passes_once_migrated(tmp_path, monkeypatch):
    from fux import doctor

    _repo(tmp_path, names=("pii", "output"))
    configfiles.migrate(tmp_path)
    monkeypatch.chdir(tmp_path)
    rows = {c.name: c for c in doctor.run(tmp_path)}
    assert rows["config files at the pre-W-295 address"].ok is True


def test_doctor_fix_will_not_seed_a_second_copy_beside_an_unmoved_file(tmp_path):
    from fux import setup

    _repo(tmp_path, names=("tune",))
    with pytest.raises(FuxError, match="moved to"):
        setup.fill_missing(tmp_path)
    assert not config_file(tmp_path, "tune").exists()


def test_no_source_joins_a_policy_file_onto_dot_fux_itself():
    """L12: after W-295 no module spells `.fux/<name>.toml` or joins a bare name."""
    import re
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    names = "|".join(NAMES)
    spelled = re.compile(rf"\.fux/({names})\.toml|\"\.fux\", *\"({names})\.toml\"")
    offenders = []
    for base in ("src", "node/src", "node/fux.mjs"):
        target = root / base
        files = [target] if target.is_file() else [
            p for p in target.rglob("*") if p.suffix in {".py", ".mjs"} and "__pycache__" not in p.parts
        ]
        for path in files:
            for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if spelled.search(line):
                    offenders.append(f"{path.relative_to(root)}:{lineno}")
    assert not offenders, offenders
