"""W-242 Tier 1 — the Node reader answers from `.fux/runtime/`, and it changes nothing.

A plane Python built is read by `node/src/derive/accel.mjs` under `--fast`.
Three things must hold, and each is asserted against a corpus built to reach
the branches that break a candidate generator:

- **Node `--fast` prints exactly what Node's scan prints**, byte for byte, at
  several `top` values (a bound is only load-bearing at larger `top`; see
  `test_differential.py`'s header), with skipping on, and through the whole
  `ask` spine: tune, priority, anchors, the mined table, rerank and graph tier.
- **Node `--fast` agrees with Python `--fast`** on ids, order and `round(9)`
  scores — parsed values, never stdout bytes (W-107 hazard H2).
- **Anything not fresh is the scan, never an error**: a touched shard, an
  unknown schema, and a stamp a few nanoseconds off — the case a `Number`
  cannot see, because `mtime_ns` is past 2^53 (W-242 step 6).

The corpus is ingested in a temp directory, never at this repo's root (W-244).
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
ACCEL = (ENGINE / "node" / "src" / "derive" / "accel.mjs").as_uri()
RUN = (ENGINE / "node" / "src" / "query" / "run.mjs").as_uri()

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node is not on PATH")

TOPS = (1, 5, 20, 50)
QUERIES = (
    "common words everywhere",
    "zarquon protocol",
    "mean kinetic temperature",
    "MKT excursion",
    "widget machinery details",
    "rare term seventeen",
    "filler body text number",
    "nothing matches xyzzy",
)


@pytest.fixture(scope="module")
def corpus(tmp_path_factory) -> Path:
    root = tmp_path_factory.mktemp("node-accel")
    listing = root / ".fux" / "sources" / "dirs"
    listing.parent.mkdir(parents=True, exist_ok=True)
    listing.write_text("docs\n", encoding="utf-8")
    (root / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    (root / ".fux" / "pii.toml").write_text("", encoding="utf-8")
    write_config(root)
    files = {
        "docs/target.md": "# Widget\n\nthis page explains the widget machinery in detail\n",
        "docs/linker-one.md": "# One\n\nSee [the zarquon protocol](target.md) for details.\n",
        "docs/linker-two.md": "# Two\n\nThe [zarquon](target.md) is documented elsewhere.\n",
        "docs/glossary.md": "# Glossary\n\nMean Kinetic Temperature (MKT) is the averaged storage temperature.\n",
        "docs/team/runbook.md": "# Runbook\n\nan excursion in mean kinetic temperature is logged here\n",
    }
    for i in range(320):
        # A term in every document spans three 128-posting blocks, so the block
        # bound and `_fill_deferred` are exercised, not bypassed.
        extra = " rare term seventeen" if i % 17 == 0 else ""
        files[f"docs/filler-{i:03d}.md"] = (
            f"# Filler {i}\n\ncommon words everywhere filler body text number {i}"
            + " words" * (i % 9) + extra + "\n"
        )
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    run(root, refresh_urls=False, full=False)
    # A per-source weight, so `Weighting.maximum` is not 1.0 on this corpus.
    tune = root / ".fux" / "tune.toml"
    text = tune.read_text(encoding="utf-8")
    assert text.count("\n[priority]\n") == 1
    tune.write_text(text.replace("\n[priority]\n", '\n[priority]\n"docs" = 1.5\n'), encoding="utf-8")
    build(root)
    return root


def _node_cli(root: Path, *argv: str) -> str:
    proc = subprocess.run(
        ["node", str(NODE_ENTRY), *argv], capture_output=True, text=True, encoding="utf-8", cwd=root
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


def _python_cli(root: Path, *argv: str) -> str:
    env = dict(os.environ, PYTHONPATH=str(ENGINE / "src"))
    proc = subprocess.run(
        [sys.executable, "-m", "fux", *argv], capture_output=True, text=True, encoding="utf-8",
        cwd=root, env=env,
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


def _node_path(root: Path, query: str, fast: bool) -> str:
    """Which generator `runQuery` used — the plane or the scan."""
    script = (
        f"import {{ runQuery }} from {json.dumps(RUN)};"
        f"const r = runQuery({json.dumps(str(root))}, {json.dumps(query)}, 5,"
        f" {{ useTune: true, wantConfidence: false, compose: true, fast: {json.dumps(fast)} }});"
        "console.log(r.path);"
    )
    proc = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.strip()


def test_the_plane_is_what_answers_under_fast(corpus):
    assert _node_path(corpus, "zarquon protocol", fast=True) == "accelerator"
    assert _node_path(corpus, "zarquon protocol", fast=False) == "scan"


@pytest.mark.parametrize("top", TOPS)
def test_node_fast_prints_exactly_what_node_scan_prints(corpus, top):
    for verb in ("ask", "find"):
        for query in QUERIES:
            scan = _node_cli(corpus, verb, query, "--json", "--top", str(top))
            fast = _node_cli(corpus, verb, query, "--json", "--top", str(top), "--fast")
            assert fast == scan, f"{verb} {query!r} --top {top}"


@pytest.mark.parametrize("top", (5, 50))
def test_node_fast_agrees_with_python_fast(corpus, top):
    for query in QUERIES:
        node = json.loads(_node_cli(corpus, "ask", query, "--json", "--top", str(top), "--fast"))["results"]
        python = json.loads(_python_cli(corpus, "ask", query, "--json", "--top", str(top), "--fast"))["results"]
        assert [r["id"] for r in node] == [r["id"] for r in python], query
        assert [round(r["score"], 9) for r in node] == [round(r["score"], 9) for r in python], query


def test_skipping_and_expansion_agree_with_the_scan_below_the_cli(corpus):
    """`accel.ask` against `scan.ask` directly, skipping on and off, with an
    expansion at weights either side of 1 — the `_kth_score` guard's case."""
    script = f"""
import {{ ask as accelAsk }} from {json.dumps(ACCEL)};
import {{ ask as scanAsk, queryTermHashes }} from {json.dumps((ENGINE / 'node/src/query/scan.mjs').as_uri())};
import {{ build }} from {json.dumps((ENGINE / 'node/src/query/expand.mjs').as_uri())};
import {{ loadTune }} from {json.dumps((ENGINE / 'node/src/config/tune.mjs').as_uri())};
import {{ identifiersFor }} from {json.dumps((ENGINE / 'node/src/query/identifiers.mjs').as_uri())};
const root = {json.dumps(str(corpus))};
const scoring = loadTune(root, {{ enabled: true }}).scoring;
const ids = identifiersFor(root);
let bad = [];
let checked = 0;
for (const [q, extra] of [["filler body", "words everywhere"], ["zarquon", "widget"], ["common", "rare seventeen"]]) {{
  for (const weight of [0, 0.3, 1.0, 2.5]) {{
    const expansion = build(queryTermHashes(q, ids), queryTermHashes(extra, ids), weight);
    for (const top of {list(TOPS)}) {{
      const want = JSON.stringify(scanAsk(root, q, top, {{ scoring, expansion }}));
      for (const skipping of [false, true]) {{
        const got = JSON.stringify(accelAsk(root, q, top, {{ skipping, scoring, expansion }}));
        checked++;
        if (got !== want) bad.push([q, weight, top, skipping]);
      }}
    }}
  }}
}}
console.log(JSON.stringify({{ checked, bad }}));
"""
    proc = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout)
    assert out["checked"] == 3 * 4 * len(TOPS) * 2
    assert out["bad"] == []


def _usable(root: Path) -> bool:
    script = f"import {{ usable }} from {json.dumps(ACCEL)}; console.log(usable({json.dumps(str(root))}));"
    proc = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.strip() == "true"


def _copy(corpus: Path, tmp_path: Path) -> Path:
    dst = tmp_path / "copy"
    shutil.copytree(corpus, dst)
    # copytree keeps mtimes only to the second on some filesystems; restamp by
    # rebuilding, so the copy starts fresh and each test breaks one thing.
    build(dst)
    return dst


def test_a_fresh_python_plane_is_usable_by_node(corpus):
    assert _usable(corpus)


def test_a_stamp_a_few_nanoseconds_off_is_stale(corpus, tmp_path):
    """The case a `Number` cannot see: 2^53 < mtime_ns, so +1 rounds away."""
    root = _copy(corpus, tmp_path)
    stamp_path = fmt.runtime_dir(root) / fmt.STAMP_NAME
    stamp = json.loads(stamp_path.read_bytes())
    name = sorted(stamp["shards"])[0]
    size, mtime = stamp["shards"][name]
    assert mtime > 2**53, "the fixture no longer exercises the precision hazard"
    # The smallest shift a double cannot see (doubles are 256 ns apart here).
    delta = next(d for d in (k * sign for k in range(1, 128) for sign in (1, -1)) if float(mtime + d) == float(mtime))
    stamp["shards"][name] = [size, mtime + delta]
    stamp_path.write_text(json.dumps(stamp), encoding="utf-8")
    assert not _usable(root)
    assert _node_path(root, "zarquon protocol", fast=True) == "scan"


def test_a_touched_shard_falls_back_to_the_scan(corpus, tmp_path):
    root = _copy(corpus, tmp_path)
    shard = sorted((root / ".fux" / "index").glob("*.jsonl"))[0]
    os.utime(shard, ns=(shard.stat().st_atime_ns, shard.stat().st_mtime_ns + 1_000))
    assert not _usable(root)
    assert _node_path(root, "zarquon protocol", fast=True) == "scan"


def test_an_unknown_schema_falls_back_to_the_scan(corpus, tmp_path):
    root = _copy(corpus, tmp_path)
    manifest_path = fmt.runtime_dir(root) / fmt.MANIFEST_NAME
    manifest = json.loads(manifest_path.read_bytes())
    manifest["schema"] = "fux.runtime.v0"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    assert not _usable(root)
    out = _node_cli(root, "ask", "zarquon protocol", "--json", "--fast")
    assert out == _node_cli(root, "ask", "zarquon protocol", "--json")


def test_fast_and_scan_together_are_refused_as_python_refuses_them(corpus):
    proc = subprocess.run(
        ["node", str(NODE_ENTRY), "ask", "x", "--fast", "--scan"], capture_output=True, text=True, cwd=corpus
    )
    assert proc.returncode == 2
    assert "not allowed with" in proc.stderr
