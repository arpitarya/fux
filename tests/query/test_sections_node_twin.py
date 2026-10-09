"""W-236 — the Node reader adds the best-section term identically (SR-SECTIONS d7).

The differential law's Node arm for section records. The corpus is the one
`test_sections.py` pins — a long runbook whose answer is one short heading
section, beside short sectionless documents and two-section fillers — so both
branches of `_best_section` (a sectioned document, and a sectionless one scored
as its own single section) are reached, and `[ranking] section_weight` is set
in `.fux/tune.toml`, the file a consumer edits, so both readers resolve it.

Held here:

- **Node `ask --json` equals Python's, scan and `--fast`**: every key, in the
  same order, with `score` compared after `round(9)` (SR-RANKING decision 8a —
  `Math.log` and `math.log` differ in the last ulp, which is the only thing a
  byte comparison would add) and `section` compared exactly.
- **Node `--fast` prints exactly what Node's scan prints**, byte for byte.
- **At 0.0 the key does not exist** on either reader, and `fux lexical` and
  `find` never carry it.
- **`node fux.mjs build` writes Python's section plane byte for byte**:
  `sections.json`, `sections/<prefix>.json`, `stats.json`, `docs.jsonl` and the
  manifest, whose shard names carry `sections/`.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from fux.derive import build
from fux.derive import format as fmt
from fux.ingest.run import run
from l12_fixtures import write_config

ENGINE = Path(__file__).resolve().parents[2]
NODE_ENTRY = ENGINE / "node" / "fux.mjs"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node is not on PATH")

WEIGHTS = (0.0, 0.25, 1.0)
QUERIES = ("rollback canary deploy", "rollback", "filler queues", "canary", "nothing xyzzy")


def _long_doc() -> str:
    parts = ["# Operations runbook\n", "## Overview\n"]
    parts += [f"general operational prose line {i} about servers and queues\n" for i in range(60)]
    parts += ["## Rollback procedure\n", "to rollback the canary deploy run the rollback script\n"]
    parts += ["## Appendix\n"] + [f"appendix filler line {i} on unrelated tooling\n" for i in range(60)]
    return "".join(parts)


@pytest.fixture(scope="module")
def corpus(tmp_path_factory) -> Path:
    root = tmp_path_factory.mktemp("sections-node")
    listing = root / ".fux" / "sources" / "dirs"
    listing.parent.mkdir(parents=True, exist_ok=True)
    listing.write_text("docs\n", encoding="utf-8")
    (root / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    (root / ".fux" / "pii.toml").write_text("", encoding="utf-8")
    write_config(root)
    files = {
        "docs/runbook.md": _long_doc(),
        "docs/short.md": "# Canary\n\nthe canary deploy is a staged rollout\n",
        "docs/rollback-note.md": "# Rollback\n\nrollback means returning to the previous release\n",
        "docs/one-section.md": "# Lonely\n\nonly one section, rollback mentioned once\n",
    }
    for i in range(25):
        files[f"docs/filler-{i:02d}.md"] = (
            f"# Filler {i}\n\n## Part a\n\nfiller text {i} about queues\n\n## Part b\n\nmore filler {i}\n"
        )
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    run(root, refresh_urls=False, full=False)
    build(root)
    return root


def _set_weight(root: Path, weight: float) -> None:
    tune = root / ".fux" / "tune.toml"
    lines = tune.read_text(encoding="utf-8").splitlines(keepends=True)
    hits = [i for i, line in enumerate(lines) if line.split("=")[0].strip() == "section_weight"]
    assert len(hits) == 1, "the template must carry exactly one section_weight line"
    lines[hits[0]] = f"section_weight = {weight}\n"
    tune.write_text("".join(lines), encoding="utf-8")


def _node(root: Path, *argv: str) -> str:
    proc = subprocess.run(
        ["node", str(NODE_ENTRY), *argv], capture_output=True, text=True, encoding="utf-8", cwd=root,
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


def _python(root: Path, *argv: str) -> str:
    env = dict(os.environ, PYTHONPATH=str(ENGINE / "src"))
    proc = subprocess.run(
        [sys.executable, "-m", "fux", *argv], capture_output=True, text=True, encoding="utf-8",
        cwd=root, env=env,
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


def _rows(stdout: str) -> list[dict]:
    rows = json.loads(stdout)["results"]
    for row in rows:
        row["score"] = round(row["score"], 9)
    return rows


def _keys(rows: list[dict]) -> list[list[str]]:
    return [list(row) for row in rows]


@pytest.mark.parametrize("weight", WEIGHTS)
def test_node_ask_equals_python_ask_on_both_paths(corpus, weight):
    _set_weight(corpus, weight)
    for query in QUERIES:
        for extra in ((), ("--fast",)):
            argv = ("ask", query, "--json", "--top", "10", *extra)
            py, nd = _rows(_python(corpus, *argv)), _rows(_node(corpus, *argv))
            assert nd == py, f"{argv} at section_weight={weight}"
            assert _keys(nd) == _keys(py), f"{argv}: key order differs"
            for row in nd:
                assert ("section" in row) == (weight > 0), f"{argv}: section key at {weight}"


@pytest.mark.parametrize("weight", WEIGHTS[1:])
def test_node_fast_prints_exactly_what_node_scan_prints(corpus, weight):
    _set_weight(corpus, weight)
    for query in QUERIES:
        for top in ("1", "3", "10"):
            scan = _node(corpus, "ask", query, "--json", "--top", top)
            fast = _node(corpus, "ask", query, "--json", "--top", top, "--fast")
            assert fast == scan, f"{query!r} --top {top} at {weight}"


def test_the_fixture_reaches_a_named_section(corpus):
    """Both readers agreeing about nothing would pass the tests above (SR-RS d23)."""
    _set_weight(corpus, 1.0)
    rows = _rows(_node(corpus, "ask", "rollback canary deploy", "--json", "--top", "10"))
    by_id = {row["id"]: row["section"] for row in rows}
    assert by_id["file:docs/runbook.md"] == "file:docs/runbook.md#s2"
    assert by_id["file:docs/short.md"] is None


def test_lexical_and_find_never_carry_the_key(corpus):
    _set_weight(corpus, 1.0)
    for argv in (("lexical", "rollback", "--json"), ("find", "rollback", "--json")):
        nd = _rows(_node(corpus, *argv))
        assert nd == _rows(_python(corpus, *argv)), argv
        assert all("section" not in row for row in nd), argv


def test_node_build_writes_pythons_section_plane(corpus, tmp_path):
    clone = tmp_path / "clone"
    clone.mkdir()
    shutil.copy2(corpus / "fux.toml", clone / "fux.toml")
    shutil.copytree(
        corpus / ".fux", clone / ".fux",
        ignore=lambda d, n: ["runtime"] if Path(d) == corpus / ".fux" else [],
    )
    proc = subprocess.run(
        ["node", str(NODE_ENTRY), "build"], capture_output=True, text=True, encoding="utf-8", cwd=clone,
    )
    assert proc.returncode == 0, proc.stderr
    py_rt, nd_rt = fmt.runtime_dir(corpus), fmt.runtime_dir(clone)
    names = [fmt.SECTION_TABLE_NAME, fmt.STATS_NAME, fmt.DOCS_NAME, fmt.MANIFEST_NAME]
    for name in names:
        assert (nd_rt / name).read_bytes() == (py_rt / name).read_bytes(), name
    py_sec = sorted(p.name for p in (py_rt / fmt.SECTIONS_RT_DIR).iterdir())
    assert py_sec, "the fixture has section postings"
    assert sorted(p.name for p in (nd_rt / fmt.SECTIONS_RT_DIR).iterdir()) == py_sec
    for name in py_sec:
        assert (nd_rt / fmt.SECTIONS_RT_DIR / name).read_bytes() == (
            py_rt / fmt.SECTIONS_RT_DIR / name
        ).read_bytes(), name
    manifest = json.loads((nd_rt / fmt.MANIFEST_NAME).read_text(encoding="utf-8"))
    assert any(name.startswith("sections/") for name in manifest["shards"])
