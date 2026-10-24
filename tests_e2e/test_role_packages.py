"""Each of the four wheels, installed ALONE in a clean venv, does its own job (W-282).

The unit gate (`tests/test_package_layers.py`) proves no import crosses the
layer map. This proves the thing a consumer meets: the wheels built from this
tree, installed with no network into fresh virtual environments.

- **writer alone** ingests a fixture repository, and has no `fux.query`;
- **reader alone** ranks and answers from that index, has no `fux.ingest`, and
  its `ask` / `find` / `answer --json` are byte-identical to `fux-engine`'s on
  the same repository (ruling F2: the reader's `answer` is today's, refer
  included);
- **each refuses the other's verbs by name**, and `--help` lists only its own;
- **fux-engine** is every verb, and its `--help` is the development tree's.

Wheels are built offline with `python -m hatchling build` (hatchling is a dev
dependency) and installed with `pip --no-index` from a local directory, so the
test needs no network (L5).
"""

from __future__ import annotations

from l12_fixtures import config_file, write_dirs
import json
import subprocess
import sys
import os
from pathlib import Path

import pytest

from l12_fixtures import write_config

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = {
    "fux-core": ROOT / "packages" / "fux-core",
    "fux-reader": ROOT / "packages" / "fux-reader",
    "fux-writer": ROOT / "packages" / "fux-writer",
    "fux-engine": ROOT,
}
QUERIES = ("pruning gates", "café body text", "what does B say")


def _bin(env: Path, name: str) -> Path:
    scripts = env / ("Scripts" if sys.platform == "win32" else "bin")
    return scripts / (f"{name}.exe" if sys.platform == "win32" else name)


@pytest.fixture(scope="module")
def wheels(tmp_path_factory) -> Path:
    pytest.importorskip("hatchling")
    out = tmp_path_factory.mktemp("wheels")
    for project in PROJECTS.values():
        subprocess.run(
            [sys.executable, "-m", "hatchling", "build", "-t", "wheel", "-d", str(out)],
            cwd=project, check=True, capture_output=True, text=True,
        )
    assert len(list(out.glob("*.whl"))) == 4
    return out


@pytest.fixture(scope="module")
def envs(wheels, tmp_path_factory) -> dict[str, Path]:
    made = {}
    for dist in ("fux-core", "fux-reader", "fux-writer", "fux-engine"):
        env = tmp_path_factory.mktemp(dist)
        # A subprocess, not `venv.EnvBuilder` in-process: inside pytest the
        # in-process ensurepip aborted on macOS, and a user makes one this way.
        subprocess.run([sys.executable, "-m", "venv", "--clear", str(env)],
                       check=True, capture_output=True, env=_clean_env())
        python = _bin(env, "python")
        subprocess.run(
            [str(python), "-m", "pip", "install", "-q", "--no-index", "--find-links", str(wheels), dist],
            check=True, capture_output=True, text=True, env=_clean_env(),
        )
        made[dist] = env
    return made


def _clean_env() -> dict[str, str]:
    """The caller's environment without the variables that point Python at
    THIS tree — a clean venv must see only what was installed into it."""
    return {k: v for k, v in os.environ.items()
            if k not in ("PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV", "__PYVENV_LAUNCHER__")}


def _fux(env: Path, cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(_bin(env, "fux")), *args], cwd=cwd, capture_output=True, text=True,
        encoding="utf-8", check=check, env=_clean_env(),
    )


def _imports(env: Path, module: str) -> bool:
    probe = subprocess.run([str(_bin(env, "python")), "-c", f"import {module}"],
                           capture_output=True, env=_clean_env())
    return probe.returncode == 0


@pytest.fixture(scope="module")
def corpus(tmp_path_factory) -> Path:
    root = tmp_path_factory.mktemp("corpus")
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    (root / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    dirs = root / ".fux" / "sources" / "dirs"
    dirs.parent.mkdir(parents=True, exist_ok=True)
    write_dirs(root, "docs\n")
    (config_file(root, "pii")).write_text("", encoding="utf-8")
    write_config(root)
    # Markdown only, so no plugin package is needed — and none is installed in
    # these venvs. No declaration means prose only (SR-PLUGINS, W-289 phase 2).
    (config_file(root, "plugins")).unlink()
    docs = root / "docs"
    (docs / "sub").mkdir(parents=True)
    (docs / "a.md").write_text("---\ntitle: A\ntags: [x, y]\n---\n# A\n\nsee [b](b.md) and `docs/a.md`\n",
                               encoding="utf-8")
    (docs / "b.md").write_text("# B\n\nsome body text about pruning and gates\n", encoding="utf-8")
    (docs / "sub" / "c.md").write_text("# C\n\nmore body text, café naïve\n", encoding="utf-8")
    return root


@pytest.fixture(scope="module")
def ingested(envs, corpus) -> Path:
    """The fixture repository, ingested by the WRITER ALONE."""
    _fux(envs["fux-writer"], corpus, "ingest")
    assert list((corpus / ".fux" / "index").glob("*.jsonl")), "the writer wrote no shards"
    return corpus


def test_the_writer_alone_ingests_and_has_no_ranker(envs, ingested):
    writer = envs["fux-writer"]
    assert not _imports(writer, "fux.query")
    assert _imports(writer, "fux.ingest")
    assert _bin(writer, "fux-merge-index").exists()
    refused = _fux(writer, ingested, "ask", "pruning", check=False)
    assert refused.returncode == 1 and "fux-reader" in refused.stderr


def test_the_reader_alone_answers_and_has_no_ingest(envs, ingested):
    reader = envs["fux-reader"]
    assert not _imports(reader, "fux.ingest")
    assert not _bin(reader, "fux-merge-index").exists()
    refused = _fux(reader, ingested, "ingest", check=False)
    assert refused.returncode == 1 and "fux-writer" in refused.stderr
    assert json.loads(_fux(reader, ingested, "ask", "--json", "pruning gates").stdout)


def test_the_readers_output_is_the_engines(envs, ingested):
    """Ruling F2: one meaning of `answer` on every install, refer included."""
    for query in QUERIES:
        for verb in ("ask", "find", "answer"):
            mine = _fux(envs["fux-reader"], ingested, verb, "--json", query).stdout
            engine = _fux(envs["fux-engine"], ingested, verb, "--json", query).stdout
            assert mine == engine, f"{verb} {query!r}: the reader and the engine disagree"


def test_each_install_lists_only_its_own_verbs(envs, corpus):
    def verbs(dist):
        usage = _fux(envs[dist], corpus, "--help").stdout
        return set(usage[usage.index("{") + 1: usage.index("}")].split(","))

    core, reader, writer, engine = (verbs(d) for d in ("fux-core", "fux-reader", "fux-writer", "fux-engine"))
    assert core == {"tune", "output"}
    assert {"ask", "answer", "find", "build", "doctor"} <= reader and "ingest" not in reader
    assert {"ingest", "setup", "hooks", "doctor"} <= writer and "ask" not in writer
    assert reader | writer < engine and {"inspect", "serve", "identifiers"} <= engine


def test_the_engines_help_is_the_development_trees(envs, corpus):
    installed = _fux(envs["fux-engine"], corpus, "--help").stdout
    here = subprocess.run([sys.executable, "-m", "fux.cli", "--help"], cwd=corpus,
                          capture_output=True, text=True, encoding="utf-8", check=True).stdout
    assert installed == here


def test_each_role_doctor_runs_its_own_rows(envs, ingested):
    reader = json.loads(_fux(envs["fux-reader"], ingested, "doctor", "--json", check=False).stdout)
    writer = json.loads(_fux(envs["fux-writer"], ingested, "doctor", "--json", check=False).stdout)
    engine = json.loads(_fux(envs["fux-engine"], ingested, "doctor", "--json", check=False).stdout)
    names = {k: {c["name"] for c in v["checks"]} for k, v in
             (("reader", reader), ("writer", writer), ("engine", engine))}
    assert names["reader"] < names["engine"] and names["writer"] < names["engine"]
    assert "runner" in writer and "runner" not in reader
    assert "freshness" in reader and "freshness" not in writer
    fixed = _fux(envs["fux-reader"], ingested, "doctor", "--fix", check=False)
    assert fixed.returncode == 1 and "fux-writer" in fixed.stderr


def test_a_wheel_carries_no_file_another_carries(wheels):
    import zipfile

    owners: dict[str, str] = {}
    clashes = []
    for wheel in sorted(wheels.glob("*.whl")):
        for name in zipfile.ZipFile(wheel).namelist():
            if name.startswith("fux/"):
                if name in owners:
                    clashes.append(f"{name}: {owners[name]} and {wheel.name}")
                owners[name] = wheel.name
    assert not clashes, "\n".join(clashes)


def test_no_wheel_carries_the_node_reader(wheels):
    """W-292 (Arpit, 2026-10-21): the bundle ships on npm alone. Until then
    fux-writer's wheel carried it at `fux/templates/node/`."""
    import zipfile

    found = [f"{w.name}: {n}" for w in sorted(wheels.glob("*.whl"))
             for n in zipfile.ZipFile(w).namelist() if n.endswith(".mjs") or "/templates/node/" in n]
    assert not found, "\n".join(found)


def test_the_installed_setup_writes_no_node_reader(envs, tmp_path):
    """`pip install` -> `fux setup`: no `.fux/node/`, no `.fux/fux` (W-292)."""
    for dist in ("fux-writer", "fux-engine"):
        repo = tmp_path / dist
        repo.mkdir()
        (repo / ".git").mkdir()
        done = _fux(envs[dist], repo, "setup", "--no-agents", check=False)
        assert done.returncode == 0, done.stderr
        assert (repo / "fux.toml").is_file()
        assert not (repo / ".fux" / "node").exists(), dist
        assert not (repo / ".fux" / "fux").exists(), dist
