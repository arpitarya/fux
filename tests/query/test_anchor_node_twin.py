"""W-168 step 1 obligation 7 — the Node reader folds anchors identically.

**The differential law's third arm** (W-107): `node/` is a transcription of
`src/fux/`, and the arm in `tools/differential/node_arm.py` answers *"do the
two readers disagree on this corpus?"* over a real repo. It cannot answer
*"does this corpus even contain the shape the new feature acts on?"* — and a
corpus that never exercises a branch makes a forgotten transcription silent.

So the feature brings its own corpus: a document reachable **only** through a
linker's wording, with `[bm25f] anchor` switched on in `.fux/tune.toml` so
both readers pick the weight up from the file a consumer would edit.

Compared on **parsed values, never stdout bytes** — W-107 hazard H2: Python
prints `--json` with `ensure_ascii=True` and `JSON.stringify` does not, so a
byte comparison fails on the first em-dash and measures nothing about the
engine. `score` is compared after `round(9)`, which is the sort key's own
resolution (SR-RANKING decision 8a, Arpit's option (b)).
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
from fux.ingest.run import run

ENGINE = Path(__file__).resolve().parents[2]
NODE_ENTRY = ENGINE / "node" / "fux.mjs"

pytestmark = pytest.mark.skipif(
    shutil.which("node") is None, reason="node is not on PATH on this machine"
)

#: Written to the file rather than passed in: the point of this test is that
#: BOTH readers resolve the key out of `.fux/tune.toml`. `None` writes no file,
#: which is the default (`ANCHOR`, on since 2026-09-24) — the case every fresh
#: clone is in; `0.0` is what every repo that ran `fux setup` before then pins.
TUNES = {
    "default": None,
    "off": "[bm25f]\nanchor = 0.0\n",
    "two": "[bm25f]\nanchor = 2.0\n",
}


def _corpus(tmp_path: Path, tune: str | None = TUNES["two"]) -> Path:
    listing = tmp_path / ".fux" / "sources" / "dirs"
    listing.parent.mkdir(parents=True, exist_ok=True)
    listing.write_text("docs\n", encoding="utf-8")
    (tmp_path / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    (tmp_path / ".fux" / "pii.toml").write_text("", encoding="utf-8")
    files = {
        "docs/target.md": "# Widget\n\nthis page explains the widget machinery in detail\n",
        "docs/linker-one.md": "# One\n\nSee [the zarquon protocol](target.md) for details.\n",
        "docs/linker-two.md": "# Two\n\nThe [zarquon](target.md) is documented elsewhere.\n",
        "docs/decoy.md": "# Decoy\n\nan unrelated page about machinery and details\n",
    }
    for i in range(12):
        files[f"docs/filler-{i:02d}.md"] = f"# Filler {i}\n\nfiller body text number {i}\n"
    for rel, text in files.items():
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    run(tmp_path)
    build(tmp_path)
    if tune is not None:
        (tmp_path / ".fux" / "tune.toml").write_text(tune, encoding="utf-8")
    return tmp_path


def _node(root: Path, query: str, top: int) -> list[dict]:
    proc = subprocess.run(
        ["node", str(NODE_ENTRY), "ask", query, "--json", "--top", str(top)],
        capture_output=True, text=True, encoding="utf-8", cwd=root,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)["results"]


def _python(root: Path, query: str, top: int) -> list[dict]:
    env = dict(os.environ, PYTHONPATH=str(ENGINE / "src"))
    proc = subprocess.run(
        [sys.executable, "-m", "fux", "ask", query, "--json", "--top", str(top)],
        capture_output=True, text=True, encoding="utf-8", cwd=root, env=env,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)["results"]


@pytest.mark.parametrize("tune", sorted(TUNES))
@pytest.mark.parametrize("query", ["zarquon", "zarquon protocol", "widget machinery"])
def test_the_node_reader_folds_anchors_identically(tmp_path, query, tune):
    root = _corpus(tmp_path, TUNES[tune])
    py = _python(root, query, 10)
    nd = _node(root, query, 10)
    assert [r["id"] for r in nd] == [r["id"] for r in py], f"order differs on {query!r}"
    for a, b in zip(py, nd, strict=True):
        assert a["loc"] == b["loc"]
        assert a["archived"] == b["archived"]
        assert round(a["score"], 9) == round(b["score"], 9), f"{a['id']}: score differs"


@pytest.mark.parametrize("tune", ["default", "two"])
def test_both_readers_reach_the_target_through_its_linkers_words(tmp_path, tune):
    """The fixture has to contain the input the feature acts on, or the
    comparison above is two readers agreeing about nothing (SR-RS d23). With
    no `tune.toml` at all, that is W-168 step 1's shipped default."""
    root = _corpus(tmp_path, TUNES[tune])
    assert [r["id"] for r in _python(root, "zarquon", 5)][0] == "file:docs/target.md"
    assert [r["id"] for r in _node(root, "zarquon", 5)][0] == "file:docs/target.md"
