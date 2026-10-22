"""`scripts/law-gate.py` — SR-WORK-RELEASE decision 18.

The gate reads artefacts, so these build tiny synthetic ones: a well-formed
release passes, and each law the gate claims to hold is broken once and must be
refused. Stdlib only — no wheel is really built here; ci.yml runs the gate on
real ones.
"""

from __future__ import annotations

import importlib.util
import io
import json
import tarfile
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("law_gate", ROOT / "scripts" / "law-gate.py")
gate = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(gate)

V = gate.pep440(gate.version())
NODE_PJ = {"name": "fux-engine", "version": gate.version(), "license": "MIT",
           "engines": {"node": ">=22"}, "files": ["fux.mjs", "mcp-tools.json", "README.md"]}


def _wheel(dist: Path, name: str, *, requires_python=">=3.12", lic="MIT", deps=(), extra_files=None):
    mod = name.replace("-", "_")
    meta = [f"Metadata-Version: 2.4", f"Name: {name}", f"Version: {V}",
            f"License-Expression: {lic}", f"Requires-Python: {requires_python}"]
    meta += [f"Requires-Dist: {d}" for d in deps]
    path = dist / f"{mod}-{V}-py3-none-any.whl"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(f"{mod}-{V}.dist-info/METADATA", "\n".join(meta) + "\n")
        for arc, data in (extra_files or {}).items():
            z.writestr(arc, data)
    return path


def _release(dist: Path, **override) -> None:
    dist.mkdir()
    for name in gate.expected_dists():
        kw = {}
        if name == "fux-engine":
            kw["deps"] = [f"fux-core=={V}", f"fux-reader=={V}", f"fux-writer=={V}", "pytest>=8; extra == 'dev'"]
        elif name != "fux-core":
            kw["deps"] = [f"fux-core=={V}"]
        if name == "fux-writer":
            kw["extra_files"] = {"fux/templates/node/fux.mjs": "export {}\n",
                                 "fux/templates/node/package.json": json.dumps(NODE_PJ)}
        kw.update(override.get(name, {}))
        if kw.pop("skip", False):
            continue
        _wheel(dist, name, **kw)
    with tarfile.open(dist / f"fux_engine-{V}.tar.gz", "w:gz") as t:
        data = b"x"
        info = tarfile.TarInfo(f"fux_engine-{V}/PKG-INFO")
        info.size = len(data)
        t.addfile(info, io.BytesIO(data))


def _npm(d: Path, pj=None, extra=()) -> Path:
    d.mkdir()
    (d / "package.json").write_text(json.dumps(pj or NODE_PJ))
    for f in ("fux.mjs", "mcp-tools.json", "README.md", *extra):
        (d / f).parent.mkdir(parents=True, exist_ok=True)
        (d / f).write_text("x")
    return d


def _errs(tmp_path, npm=None, **override) -> list[str]:
    _release(tmp_path / "dist", **override)
    errs = gate.check_dist(tmp_path / "dist", V)
    if npm is not None:
        errs += gate.check_npm(npm, gate.version())
    return errs


def test_a_well_formed_release_passes(tmp_path):
    assert _errs(tmp_path, npm=_npm(tmp_path / "npm")) == []


def test_a_missing_distribution_is_refused(tmp_path):
    errs = _errs(tmp_path, **{"fux-decoder-pdf": {"skip": True}})
    assert any("no wheel for fux-decoder-pdf" in e for e in errs)


def test_a_loose_fux_pin_is_refused(tmp_path):
    errs = _errs(tmp_path, **{"fux-reader": {"deps": ["fux-core>=1"]}})
    assert any(e.startswith("L2:") and "fux-core>=1" in e for e in errs)


def test_an_unnamed_third_party_dependency_is_refused(tmp_path):
    errs = _errs(tmp_path, **{"fux-decoder-pdf": {"deps": [f"fux-core=={V}", "pypdf>=4"]}})
    assert any(e.startswith("L2:") and "pypdf" in e for e in errs)


def test_a_non_osi_licence_is_refused(tmp_path):
    errs = _errs(tmp_path, **{"fux-core": {"lic": "BUSL-1.1"}})
    assert any(e.startswith("L2:") and "BUSL-1.1" in e for e in errs)


@pytest.mark.parametrize("floor", [">=3.11", ">=3.8", ""])
def test_a_python_floor_below_312_is_refused(tmp_path, floor):
    errs = _errs(tmp_path, **{"fux-core": {"requires_python": floor}})
    assert any(e.startswith("L7:") for e in errs)


def test_a_node_engine_below_22_is_refused(tmp_path):
    errs = _errs(tmp_path, npm=_npm(tmp_path / "npm", pj={**NODE_PJ, "engines": {"node": ">=20"}}))
    assert any(e.startswith("L8:") for e in errs)


def test_source_in_the_npm_package_is_refused(tmp_path):
    errs = _errs(tmp_path, npm=_npm(tmp_path / "npm", extra=("src/index.mjs",)))
    assert any(e.startswith("L10:") for e in errs)


def test_a_second_mjs_in_fux_writer_is_refused(tmp_path):
    files = {"fux/templates/node/fux.mjs": "", "fux/templates/node/extra.mjs": "",
             "fux/templates/node/package.json": json.dumps(NODE_PJ)}
    errs = _errs(tmp_path, **{"fux-writer": {"extra_files": files, "deps": [f"fux-core=={V}"]}})
    assert any(e.startswith("L10:") and "fux_writer" in e for e in errs)


def test_a_writer_without_the_bundle_passes(tmp_path):
    """W-292 takes the bundle out of fux-writer; the gate must not block it."""
    assert _errs(tmp_path, **{"fux-writer": {"extra_files": {}, "deps": [f"fux-core=={V}"]}}) == []


def test_an_mjs_in_any_other_wheel_is_refused(tmp_path):
    errs = _errs(tmp_path, **{"fux-core": {"extra_files": {"fux/x.mjs": ""}}})
    assert any(e.startswith("L10:") and "fux_core" in e for e in errs)


def test_the_gate_runs_in_both_workflows():
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    publish = (ROOT / ".github" / "workflows" / "publish.yml").read_text(encoding="utf-8")
    assert "scripts/law-gate.py dist --npm node/dist node/dist-scoped" in ci
    assert "scripts/law-gate.py dist --npm node/dist node/dist-scoped" in publish
    assert "scripts/smoke.py dist node/dist" in ci
