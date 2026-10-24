"""SR-PLUGINS P13 — the L4 gate, in two REAL virtual environments (W-289 phase 2).

Two machines on one repository must never build different indexes because of
what each happened to have installed. Asserted the way a consumer meets it:
wheels built from this tree, installed with no network into fresh venvs.

- **env A** has `fux-engine` and the one package the repository declares
  (`fux-decoder-json`);
- **env B** has the same, plus `fux-decoder-pdf` — installed, NOT declared.

The repository holds Markdown, JSON and a PDF. Both environments must write a
**byte-identical** `.fux/index/`, and neither may read the PDF (P3) — while
both say so on stderr, naming the package (P5).

Then the drift half: a declared package whose installed bytes differ from the
pin (env B's `fux_decoder_json` edited in place), and one pinned at a version
that is not fux's, are each a **hard error with no index written** (P4).

Built offline with `python -m hatchling build` and installed with
`pip --no-index`, as `test_role_packages.py` does, so no network is needed (L5).
"""

from __future__ import annotations

from l12_fixtures import config_file
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from l12_fixtures import write_config, write_plugins

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = (
    ROOT / "packages" / "fux-core",
    ROOT / "packages" / "fux-reader",
    ROOT / "packages" / "fux-writer",
    ROOT,
    ROOT / "packages" / "fux-decoder-json",
    ROOT / "packages" / "fux-decoder-pdf",
)
#: A one-page PDF whose content stream shows one line of text.
PDF = (
    b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    b"3 0 obj\n<< /Type /Page /Parent 2 0 R /Contents 4 0 R >>\nendobj\n"
    b"4 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf (quarterly zebra budget) Tj ET\n"
    b"endstream\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF\n"
)


def _bin(env: Path, name: str) -> Path:
    scripts = env / ("Scripts" if sys.platform == "win32" else "bin")
    return scripts / (f"{name}.exe" if sys.platform == "win32" else name)


def _clean_env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items()
            if k not in ("PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV", "__PYVENV_LAUNCHER__")}


@pytest.fixture(scope="module")
def wheels(tmp_path_factory) -> Path:
    pytest.importorskip("hatchling")
    out = tmp_path_factory.mktemp("plugin-wheels")
    for project in PROJECTS:
        subprocess.run(
            [sys.executable, "-m", "hatchling", "build", "-t", "wheel", "-d", str(out)],
            cwd=project, check=True, capture_output=True, text=True,
        )
    assert len(list(out.glob("*.whl"))) == len(PROJECTS)
    return out


def _env(wheels: Path, where: Path, *dists: str) -> Path:
    subprocess.run([sys.executable, "-m", "venv", "--clear", str(where)],
                   check=True, capture_output=True, env=_clean_env())
    subprocess.run(
        [str(_bin(where, "python")), "-m", "pip", "install", "-q", "--no-index",
         "--find-links", str(wheels), *dists],
        check=True, capture_output=True, text=True, env=_clean_env(),
    )
    return where


@pytest.fixture(scope="module")
def envs(wheels, tmp_path_factory) -> dict[str, Path]:
    return {
        "A": _env(wheels, tmp_path_factory.mktemp("env-a"), "fux-engine", "fux-decoder-json"),
        "B": _env(wheels, tmp_path_factory.mktemp("env-b"),
                  "fux-engine", "fux-decoder-json", "fux-decoder-pdf"),
    }


@pytest.fixture(scope="module")
def corpus(tmp_path_factory) -> Path:
    """Markdown, JSON and a PDF; `.fux/config/plugins.toml` declares JSON alone."""
    root = tmp_path_factory.mktemp("plugin-corpus")
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    (root / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    dirs = root / ".fux" / "sources" / "dirs"
    dirs.parent.mkdir(parents=True, exist_ok=True)
    dirs.write_text("docs\n", encoding="utf-8")
    (config_file(root, "pii")).write_text("", encoding="utf-8")
    write_config(root)
    # The pin is the dev tree's digest, which is the wheel's: the same files.
    write_plugins(root, ["fux-decoder-json"], force=True)
    docs = root / "docs"
    docs.mkdir()
    (docs / "a.md").write_text("# Alpha\n\nrollback the broker\n", encoding="utf-8")
    (docs / "b.json").write_text('{"service": "ledger", "owner": "payments"}\n', encoding="utf-8")
    (docs / "c.pdf").write_bytes(PDF)
    return root


def _copy(corpus: Path, where: Path) -> Path:
    shutil.copytree(corpus, where)
    return where


def _ingest(env: Path, root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(_bin(env, "fux")), "ingest", "--no-fetch"], cwd=root, capture_output=True,
        text=True, encoding="utf-8", env=_clean_env(),
    )


def _index_bytes(root: Path) -> dict[str, bytes]:
    index = root / ".fux" / "index"
    return {
        p.relative_to(index).as_posix(): p.read_bytes()
        for p in sorted(index.rglob("*"))
        if p.is_file()
    }


def test_an_extra_undeclared_package_changes_no_index_byte(envs, corpus, tmp_path):
    a, b = _copy(corpus, tmp_path / "a"), _copy(corpus, tmp_path / "b")
    ran_a, ran_b = _ingest(envs["A"], a), _ingest(envs["B"], b)
    assert ran_a.returncode == 0, ran_a.stderr
    assert ran_b.returncode == 0, ran_b.stderr
    index_a, index_b = _index_bytes(a), _index_bytes(b)
    assert index_a, "env A wrote no index"
    assert index_a == index_b, sorted(k for k in index_a.keys() | index_b.keys()
                                      if index_a.get(k) != index_b.get(k))
    register = index_a["REGISTER"].decode("utf-8")
    assert "docs/b.json" in register and "pkg:fux-decoder-json@" in register
    assert "docs/c.pdf" not in register, "an undeclared package read the PDF"
    # P5: never silent, on both machines.
    for ran in (ran_a, ran_b):
        assert "1 .pdf file(s) not read" in ran.stderr and "fux-decoder-pdf" in ran.stderr


def test_a_drifted_declared_package_is_a_hard_error_and_writes_no_index(envs, corpus, tmp_path):
    """Env B's installed `fux_decoder_json` edited in place: the digest differs."""
    probe = subprocess.run(
        [str(_bin(envs["B"], "python")), "-c",
         "import importlib.util as u; print(list(u.find_spec('fux_decoder_json').submodule_search_locations)[0])"],
        check=True, capture_output=True, text=True, env=_clean_env(),
    )
    target = Path(probe.stdout.strip()) / "json.py"
    original = target.read_bytes()
    try:
        target.write_bytes(original + b"\n# drifted on this machine\n")
        root = _copy(corpus, tmp_path / "drift")
        ran = _ingest(envs["B"], root)
        assert ran.returncode != 0
        assert "fux-decoder-json" in ran.stderr and "drifted" in ran.stderr
        assert not (root / ".fux" / "index").exists(), "an index was written past P4"
    finally:
        target.write_bytes(original)


def test_a_declared_package_at_another_version_is_a_hard_error(envs, corpus, tmp_path):
    root = _copy(corpus, tmp_path / "version")
    declared = config_file(root, "plugins")
    text = declared.read_text(encoding="utf-8")
    import re

    declared.write_text(re.sub(r'version = "[^"]+"', 'version = "0.0.1"', text), encoding="utf-8")
    ran = _ingest(envs["A"], root)
    assert ran.returncode != 0
    assert "fux-decoder-json" in ran.stderr and "0.0.1" in ran.stderr
    assert not (root / ".fux" / "index").exists(), "an index was written past P4"
