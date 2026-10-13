"""W-274 — section records are opt-in: `fux.toml [index] section_records`.

SR-SECTIONS decision 11. Pinned here:

1. **Off is an index built without section code**, byte for byte.
2. **On writes the plane**, as W-236 and W-273 built it.
3. **A flip refuses a delta ingest** in both directions and names `--full`;
   `--full` then builds the other mode cleanly.
4. **`section_weight > 0` with the key off is a hard error naming both keys**,
   in Python and in Node — never a silent zero.
5. **A missing key is a hard error naming it** (L12).
6. **`fux doctor`** reports the mode and flags the disagreements.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest
from l12_fixtures import write_config

from fux import config as config_mod
from fux import doctor, store, tune
from fux.errors import FuxError
from fux.ingest.run import run

NODE = shutil.which("node")
FUX_MJS = Path(__file__).resolve().parents[2] / "node" / "src" / "config" / "tune.mjs"

DOCS = {
    "docs/runbook.md": "# Runbook\n\n## Deploy\n\nship the canary\n\n## Rollback\n\nrun the rollback script\n",
    "docs/guide.md": "# Guide\n\n## One\n\nalpha beta\n\n## Two\n\ngamma delta\n",
    "docs/short.md": "# Short\n\none section only\n",
}


def _repo(root: Path, *, on: bool) -> Path:
    (root / ".fux" / "sources").mkdir(parents=True, exist_ok=True)
    (root / ".fux" / "sources" / "dirs").write_text("docs\n", encoding="utf-8")
    (root / ".fux" / "pii.toml").write_text("", encoding="utf-8")
    (root / "fux.toml").write_text(
        f"[sources]\n\n[index]\nsection_records = {str(on).lower()}\n", encoding="utf-8"
    )
    write_config(root)
    for rel, text in DOCS.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return root


def _flip(root: Path, on: bool) -> None:
    path = root / "fux.toml"
    text = path.read_text(encoding="utf-8")
    path.write_text(
        re.sub(r"section_records = (true|false)", f"section_records = {str(on).lower()}", text),
        encoding="utf-8",
    )


def _set_weight(root: Path, weight: float) -> None:
    path = root / ".fux" / "tune.toml"
    text = path.read_text(encoding="utf-8")
    path.write_text(
        re.sub(r"(?m)^section_weight\s*=.*$", f"section_weight = {weight}", text), encoding="utf-8"
    )


def _index_bytes(root: Path) -> dict[str, bytes]:
    base = root / ".fux" / "index"
    return {p.relative_to(base).as_posix(): p.read_bytes() for p in sorted(base.rglob("*")) if p.is_file()}


# -- 1, 2. the two modes ------------------------------------------------------


def test_off_is_byte_identical_to_an_index_written_without_section_records(tmp_path):
    off = _repo(tmp_path / "off", on=False)
    run(off, refresh_urls=False, full=False)
    assert not store.iter_section_paths(off)

    # The reference: the same corpus with the plane on, then rewritten with no
    # `sections` key on any record — which is what an engine without section
    # code writes (W-273's base index; SR-SECTIONS decision 7).
    ref = _repo(tmp_path / "ref", on=True)
    run(ref, refresh_urls=False, full=False)
    assert store.iter_section_paths(ref), "the fixture must have something to section"
    store.write_index(ref, list(store.read_index(ref).values()))

    assert _index_bytes(off) == _index_bytes(ref)
    assert all("nsec" not in r for r in store.read_index(off).values())


def test_on_writes_the_plane_and_stamps_nsec(tmp_path):
    on = _repo(tmp_path, on=True)
    run(on, refresh_urls=False, full=False)
    records = store.read_index(on)
    assert records["file:docs/runbook.md"]["nsec"] == 2      # the bodiless title folds forward
    assert "nsec" not in records["file:docs/short.md"]
    assert store.iter_section_paths(on)


# -- 3. the flip ----------------------------------------------------------------


def test_switching_off_refuses_a_delta_and_full_removes_the_plane(tmp_path):
    root = _repo(tmp_path, on=True)
    run(root, refresh_urls=False, full=False)
    _flip(root, on=False)
    with pytest.raises(FuxError, match=r"section_records = false.*fux ingest --full"):
        run(root, refresh_urls=False, full=False)
    run(root, refresh_urls=False, full=True)
    assert not store.iter_section_paths(root)
    run(root, refresh_urls=False, full=False)              # and settles: no refusal now


def test_switching_on_refuses_a_delta_and_full_builds_the_plane(tmp_path):
    root = _repo(tmp_path, on=False)
    run(root, refresh_urls=False, full=False)
    _flip(root, on=True)
    with pytest.raises(FuxError, match=r"section_records = true.*fux ingest --full"):
        run(root, refresh_urls=False, full=False)
    run(root, refresh_urls=False, full=True)
    assert store.iter_section_paths(root)
    run(root, refresh_urls=False, full=False)


def test_on_with_nothing_to_section_does_not_refuse_forever(tmp_path):
    """The one case the plane cannot tell from off: the recorded mode settles it."""
    root = _repo(tmp_path, on=True)
    for rel in ("docs/runbook.md", "docs/guide.md"):
        (root / rel).unlink()
    run(root, refresh_urls=False, full=False)
    assert not store.iter_section_paths(root)
    (root / "docs" / "more.md").write_text("# More\n\nstill one section\n", encoding="utf-8")
    run(root, refresh_urls=False, full=False)


# -- 4. the mismatch --------------------------------------------------------------


def test_a_section_weight_with_the_plane_off_is_a_hard_error_naming_both_keys(tmp_path):
    root = _repo(tmp_path, on=False)
    _set_weight(root, 1.0)
    with pytest.raises(FuxError, match=r"section_weight > 0.*section_records = false"):
        tune.load(root, enabled=True)
    _set_weight(root, 0.0)
    tune.load(root, enabled=True)                           # off at 0.0 is the default, fine
    _flip(root, on=True)
    _set_weight(root, 1.0)
    tune.load(root, enabled=True)


@pytest.mark.skipif(NODE is None, reason="node is not installed")
def test_node_refuses_the_same_mismatch(tmp_path):
    root = _repo(tmp_path, on=False)
    _set_weight(root, 1.0)
    script = (
        f"import({FUX_MJS.as_uri()!r}).then(m => {{ try {{ m.loadTune({str(root)!r}, {{enabled: true}}); "
        "console.log('LOADED'); } catch (e) { console.log(e.message); } })"
    )
    out = subprocess.run([NODE, "-e", script], capture_output=True, text=True, encoding="utf-8").stdout
    assert "section_weight > 0" in out and "section_records = false" in out, out

    _flip(root, on=True)
    out = subprocess.run([NODE, "-e", script], capture_output=True, text=True, encoding="utf-8").stdout
    assert out.strip() == "LOADED", out


def test_a_section_weight_above_one_is_refused(tmp_path):
    """W-278, SR-TUNE: `λ > 1` extrapolates past the section's own score."""
    root = _repo(tmp_path, on=True)
    _set_weight(root, 1.5)
    with pytest.raises(FuxError, match=r"section_weight must be between 0 and 1"):
        tune.load(root, enabled=True)
    _set_weight(root, 1.0)
    tune.load(root, enabled=True)


@pytest.mark.skipif(NODE is None, reason="node is not installed")
def test_node_refuses_a_section_weight_above_one(tmp_path):
    root = _repo(tmp_path, on=True)
    _set_weight(root, 1.5)
    script = (
        f"import({FUX_MJS.as_uri()!r}).then(m => {{ try {{ m.loadTune({str(root)!r}, {{enabled: true}}); "
        "console.log('LOADED'); } catch (e) { console.log(e.message); } })"
    )
    out = subprocess.run([NODE, "-e", script], capture_output=True, text=True, encoding="utf-8").stdout
    assert "section_weight must be between 0 and 1" in out, out


# -- 5. the key is required ---------------------------------------------------------


def test_a_missing_key_is_a_hard_error_naming_it(tmp_path):
    root = _repo(tmp_path, on=False)
    path = root / "fux.toml"
    path.write_text(re.sub(r"section_records = false\n", "", path.read_text(encoding="utf-8")), encoding="utf-8")
    with pytest.raises(FuxError, match=r"section_records"):
        config_mod.load(root)
    with pytest.raises(FuxError, match=r"\[index\] section_records is missing"):
        config_mod.section_records(root)


def test_the_template_ships_it_off():
    from fux.setup import template_config

    assert template_config()["index"]["section_records"] is False


# -- 6. doctor ------------------------------------------------------------------------


def test_doctor_reports_the_mode_and_flags_both_disagreements(tmp_path):
    root = _repo(tmp_path, on=False)
    run(root, refresh_urls=False, full=False)
    check = doctor._section_mode(root)
    assert check.ok and check.detail.startswith("off")

    _set_weight(root, 1.0)
    check = doctor._section_mode(root)
    assert not check.ok and check.level == "error"

    _set_weight(root, 0.0)
    _flip(root, on=True)
    run(root, refresh_urls=False, full=True)
    _flip(root, on=False)
    check = doctor._section_mode(root)
    assert not check.ok and check.level == "warn" and "fux ingest --full" in check.detail
