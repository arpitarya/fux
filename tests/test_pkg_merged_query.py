"""SR-PKG-INDEX decision 10 (W-300) — one query over the repository and every pin.

The package is `tests/fixtures/pkg-index/docs/`, packed and installed exactly as
`tests/test_pkg_index.py` does it; the consumer here has documents of its own
that share the package's vocabulary (`widget`, `rollback`), so one ranking has
something to merge. Each test names the clause of decision 10 it holds.
"""

from __future__ import annotations

import importlib
import json
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from fux import plugins, store as store_mod
from fux.constants import fixed
from fux.errors import FuxError
from fux.ingest.run import run as ingest
from fux.query import build_ask, run_query
from fux.query import scan as scan_mod
from fux.query.bm25f import derive_wlen
from fux.schema import load as load_schema
from l12_fixtures import config_file, template_tune, write_config, write_dirs

ENGINE = Path(__file__).resolve().parents[1]
FIXTURE = ENGINE / "tests" / "fixtures" / "pkg-index" / "docs"
RUN_MJS = ENGINE / "node" / "src" / "query" / "run.mjs"
NAME = "acme-docs-index"
IMPORT = "acme_docs_index"
VERSION = "1.0.0"
HAS_NODE = shutil.which("node") is not None
REPO, PACKAGES, ALL = (fixed("scope", k) for k in ("repo", "packages", "all"))

#: The consumer's own pages — the package's words, so `df` has two sources.
CONSUMER_DOCS = {
    "deploy.md": "# Deploying our widget\n\nWe roll back a widget release by hand, never with zarquon.\n",
    "own.md": "# Own page\n\nthe consumer's own words about the widget\n",
}

#: A family only the PACKAGE declares (W-300 step 1).
FAMILY = "ZQ-{n}"


@pytest.fixture(autouse=True)
def _fresh_cache():
    plugins.reset()
    yield
    plugins.reset()


def _repo(root: Path, files: dict[str, str], *, keep: list[str] | None = None) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    config_file(root, "pii").write_text("", encoding="utf-8")
    write_dirs(root, "docs\n")
    write_config(root)
    if keep:
        ids = config_file(root, "identifiers")
        ids.write_text(
            ids.read_text(encoding="utf-8").replace("keep = []", f"keep = {json.dumps(keep)}", 1),
            encoding="utf-8",
        )
    (root / "docs").mkdir(exist_ok=True)
    for name, text in files.items():
        # LF on every platform: the installed docs are the LF fixture's bytes
        (root / "docs" / name).write_text(text, encoding="utf-8", newline="\n")
    return root


def _pack(author: Path, out: Path) -> Path:
    """The segment `fux pack` would write (W-302), laid out by hand."""
    plugins.reset()
    ingest(author, refresh_urls=False, full=False)
    (out / "index").mkdir(parents=True)
    for shard in sorted((author / fixed("index", "dir")).glob("*" + fixed("index", "shard_suffix"))):
        shutil.copyfile(shard, out / "index" / shard.name)
    shutil.copyfile(author / fixed("files", "identifiers"), out / "identifiers.toml")
    header = json.loads(sorted((out / "index").iterdir())[0].read_bytes().split(b"\n", 1)[0])
    manifest = {
        "fux_version": "5.0.0",
        "index_header": header,
        "content": {"npm": "acme-docs", "pypi": "acme-docs", "version": VERSION},
        "docs": plugins.segment_docs(out),
        "digest": plugins.segment_digest(out),
    }
    load_schema(fixed("schema_files", "fux_index")).validate(manifest)
    (out / fixed("plugins.index", "manifest")).write_text(json.dumps(manifest), encoding="utf-8")
    return out


def _fixture_files() -> dict[str, str]:
    return {p.name: p.read_text(encoding="utf-8") for p in sorted(FIXTURE.iterdir())}


@pytest.fixture(scope="module")
def segment(tmp_path_factory) -> Path:
    author = _repo(tmp_path_factory.mktemp("author") / "repo", _fixture_files())
    return _pack(author, tmp_path_factory.mktemp("segment") / "seg")


@pytest.fixture(scope="module")
def family_segment(tmp_path_factory) -> Path:
    """A package built under an identifier family the consumer does not declare."""
    files = _fixture_files() | {"incident.md": "# Incident ZQ-118\n\nThe zarquon broker dropped every widget.\n"}
    author = _repo(tmp_path_factory.mktemp("fauthor") / "repo", files, keep=[FAMILY])
    return _pack(author, tmp_path_factory.mktemp("fsegment") / "seg")


def _consume(tmp_path: Path, segment: Path, monkeypatch) -> Path:
    """A consumer with `segment` installed (PyPI and npm) and pinned."""
    root = _repo(tmp_path / "consumer", CONSUMER_DOCS)
    site = tmp_path / "site"
    shutil.copytree(segment, site / IMPORT)
    info = site / f"{IMPORT}-{VERSION}.dist-info"
    info.mkdir(parents=True)
    (info / "METADATA").write_text(f"Metadata-Version: 2.1\nName: {NAME}\nVersion: {VERSION}\n", encoding="utf-8")
    npm = root / "node_modules" / NAME
    shutil.copytree(segment, npm)
    (npm / "package.json").write_text(json.dumps({"name": NAME, "version": VERSION}), encoding="utf-8")
    # The DOCS package the manifest's `content` names (W-301), so a package
    # winner can be read in place.
    docs_py = site / "acme_docs"
    shutil.copytree(FIXTURE, docs_py / "docs")
    docs_info = site / f"acme_docs-{VERSION}.dist-info"
    docs_info.mkdir(parents=True)
    (docs_info / "METADATA").write_text(f"Metadata-Version: 2.1\nName: acme-docs\nVersion: {VERSION}\n", encoding="utf-8")
    docs_npm = root / "node_modules" / "acme-docs"
    shutil.copytree(FIXTURE, docs_npm / "docs")
    (docs_npm / "package.json").write_text(json.dumps({"name": "acme-docs", "version": VERSION}), encoding="utf-8")
    monkeypatch.syspath_prepend(str(site))
    importlib.invalidate_caches()
    plugins.reset()
    ingest(root, refresh_urls=False, full=False)
    target = plugins.path(root)
    target.write_text(
        target.read_text(encoding="utf-8")
        + "\n[[package]]\n"
        + f'name = "{NAME}"\nkind = "index"\nversion = "{VERSION}"\n'
        + f'digest = "{plugins.segment_digest(segment)}"\nnpm = "{NAME}"\npypi = "{NAME}"\n',
        encoding="utf-8",
    )
    plugins.reset()
    return root


@pytest.fixture
def consumer(tmp_path, segment, monkeypatch) -> Path:
    return _consume(tmp_path, segment, monkeypatch)


def _query(root: Path, text: str, scope, top: int = 10):
    results, path = run_query(root, text, top, force_scan=True, use_tune=True, scope=scope)
    return results, path


def _rows(results) -> list[tuple]:
    return [(r.id, r.package, r.score) for r in results]


# -- d10: one ranking, statistics summed ------------------------------------------


def test_one_search_ranks_the_repository_and_the_package_together(consumer):
    results, path = _query(consumer, "widget rollback", ALL)
    packages = {r.package for r in results}
    assert packages == {None, NAME}, _rows(results)
    assert path == "scan"
    lexical = [r for r in results if not r.boosted]
    scores = [round(r.score, fixed("ranking", "score_digits")) for r in lexical]
    assert scores == sorted(scores, reverse=True)


def test_the_merged_statistics_are_the_sums_and_avg_wlen_is_derived_once(consumer):
    scoring = template_tune().scoring
    segs = scan_mod.segments_for(consumer, ALL)
    assert [s.package for s in segs] == [None, NAME]
    hashes = scan_mod.merged_hashes("widget rollback zarquon", segs)
    candidates, df, corpus = scan_mod.merged_candidates(segs, hashes, scoring=scoring)
    parts = [scan_mod._scan_segment(s.root, hashes, scoring=scoring) for s in segs]
    assert df == {h: sum(p[1][h] for p in parts) for h in hashes}
    assert corpus.n == sum(p[2] for p in parts) == 2 + 3
    flen = [sum(p[3][i] for p in parts) for i in range(len(parts[0][3]))]
    assert corpus.total_wlen == derive_wlen(flen, scoring, sum(p[4] for p in parts))
    assert len(candidates) == sum(len(p[0]) for p in parts)
    assert {c.get("package") for c in candidates} == {None, NAME}


def test_scope_repo_is_byte_equal_to_the_engine_before_w300(consumer):
    before = _rows(_query(consumer, "widget rollback", None)[0])
    assert _rows(_query(consumer, "widget rollback", REPO)[0]) == before
    assert all(package is None for _, package, _ in before)
    args = SimpleNamespace(
        query="widget rollback", top=10, also=None, expand=None, fast=None, scan=True, why=False,
        related=None, sections=True, band=True, max_headings=3, explain=None, no_tune=False, scope=REPO,
    )
    repo_payload = build_ask(consumer, args, compose=True, with_related=True).payload()
    assert all("package" not in hit for hit in repo_payload["results"])
    # `lexical` is the frozen baseline: the repository alone, whatever --scope says.
    lexical = [
        build_ask(consumer, SimpleNamespace(**{**vars(args), "scope": scope}), compose=False, with_related=True)
        .payload()
        for scope in (ALL, REPO)
    ]
    assert lexical[0] == lexical[1]
    assert all("package" not in hit for hit in lexical[0]["results"])


def test_scope_packages_returns_only_package_hits(consumer):
    results, _ = _query(consumer, "widget rollback", PACKAGES)
    assert results and all(r.package == NAME for r in results)


def test_all_without_a_pin_is_the_repository_alone(tmp_path):
    root = _repo(tmp_path / "plain", CONSUMER_DOCS)
    ingest(root, refresh_urls=False, full=False)
    assert _rows(_query(root, "widget rollback", ALL)[0]) == _rows(_query(root, "widget rollback", None)[0])
    assert _query(root, "widget rollback", PACKAGES)[0] == []


def test_a_package_hit_names_its_own_title_and_record(consumer):
    results, _ = _query(consumer, "zarquon migration", PACKAGES)
    top = results[0]
    assert top.package == NAME and top.title == "Rolling back a widget release"
    args = SimpleNamespace(
        query="zarquon migration", top=10, also=None, expand=None, fast=None, scan=True, why=False,
        related=None, sections=True, band=False, max_headings=3, explain=None, no_tune=False, scope=PACKAGES,
    )
    payload = build_ask(consumer, args, compose=True, with_related=True).payload()
    assert payload["results"][0]["package"] == NAME
    assert payload["results"][0]["title"] == "Rolling back a widget release"
    assert isinstance(payload["results"][0]["headings"], list)


def test_an_unknown_scope_is_refused():
    with pytest.raises(FuxError, match="scope must be one of"):
        scan_mod.segments_for(Path("."), "everything")


# -- d6, d10: lockstep — a foreign segment is refused by name, nothing scored -------


def test_a_foreign_analyzer_stops_the_query_naming_the_package(tmp_path, segment, monkeypatch):
    foreign = tmp_path / "foreign"
    shutil.copytree(segment, foreign)
    for shard in sorted((foreign / "index").iterdir()):
        head, rest = shard.read_bytes().split(b"\n", 1)
        header = json.loads(head) | {"analyzer": "v2"}
        shard.write_bytes(json.dumps(header, separators=(",", ":"), sort_keys=True).encode() + b"\n" + rest)
    manifest = foreign / fixed("plugins.index", "manifest")
    manifest.write_text(
        json.dumps(json.loads(manifest.read_text(encoding="utf-8")) | {"digest": plugins.segment_digest(foreign)}),
        encoding="utf-8",
    )
    root = _consume(tmp_path, foreign, monkeypatch)
    with pytest.raises(FuxError) as caught:
        _query(root, "widget rollback", ALL)
    assert NAME in str(caught.value) and "foreign segment" in str(caught.value)
    from fux.derive import segments

    assert not segments.packages_dir(root).exists() or not any(segments.packages_dir(root).iterdir())


# -- step 1: the query hashed once per distinct identifiers digest -------------------


def test_a_family_identifier_matches_only_when_hashed_under_the_packages_rules(tmp_path, family_segment, monkeypatch):
    root = _consume(tmp_path, family_segment, monkeypatch)
    segs = scan_mod.segments_for(root, ALL)
    assert segs[0].ids.digest != segs[1].ids.digest
    union = scan_mod.merged_hashes("zq118", segs)
    canonical = store_mod.term_hash("zq-118")
    assert canonical not in scan_mod.query_term_hashes("zq118", segs[0].ids)
    assert canonical in union
    scoring = template_tune().scoring
    repo_only = scan_mod.merged_ask(
        segs, scan_mod.query_term_hashes("zq118", segs[0].ids), 10, scoring=scoring,
    )
    assert repo_only == []
    results, _ = _query(root, "zq118", ALL)
    assert [(r.id, r.package) for r in results] == [("file:docs/incident.md", NAME)]


# -- d10 on the agent surface: `scope` on fux_search -----------------------------------


def test_fux_search_takes_scope_and_names_the_package(consumer):
    from fux import mcp

    tool = next(t for t in mcp.TOOLS if t["name"] == "fux_search")
    scope = tool["inputSchema"]["properties"]["scope"]
    assert scope["enum"] == [REPO, PACKAGES, ALL] and scope["default"] == fixed("scope", "default")
    assert len(mcp.TOOLS) == 3
    both = mcp._search(consumer, {"query": "widget rollback", "k": 10}, top=5, max_headings=3)
    assert {hit.get("package") for hit in both["results"]} == {None, NAME}
    package_hit = next(hit for hit in both["results"] if hit.get("package"))
    assert package_hit["sha"]  # read from the package's own record
    # W-301: a merged hit's location is the docs package's `pkg:` address.
    assert package_hit["location"] == f"pkg:acme-docs@{VERSION}#{package_hit['path']}"
    repo = mcp._search(consumer, {"query": "widget rollback", "k": 10, "scope": REPO}, top=5, max_headings=3)
    assert all(hit["package"] is None and hit["location"].startswith("file:") for hit in repo["results"])


# -- step 5: Python ≡ Node over the repository plus the fixture segment ---------------


def _at_round9(rows) -> list:
    """SR-NODE-SEARCH d1 (SR-RANKING d8a): ids, packages and ORDER byte-equal,
    scores equal at the sort key's resolution — `Math.log` and `math.log`
    differ by one ulp on some inputs, and this fixture's `n = 3` hits one."""
    digits = fixed("ranking", "score_digits")
    return [[i, p, round(s, digits)] for i, p, s in rows]


def _node_rows(root: Path, query: str, scope: str | None) -> list:
    script = (
        f"import {{ runQuery }} from {json.dumps(RUN_MJS.as_uri())};"
        f"const r = runQuery(process.cwd(), {json.dumps(query)}, 10, "
        f"{{ useTune: true, wantConfidence: true, compose: true, scope: {json.dumps(scope)} }});"
        "console.log(JSON.stringify({rows: r.results.map((h) => [h.id, h.package ?? null, h.score]),"
        " n: r.stats.n, df: r.stats.df}));"
    )
    out = subprocess.run(
        ["node", "--input-type=module", "-e", script], cwd=root, capture_output=True, text=True, encoding="utf-8",
    )
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)


@pytest.mark.skipif(not HAS_NODE, reason="node is not on PATH")
@pytest.mark.parametrize("scope", [ALL, PACKAGES, REPO])
@pytest.mark.parametrize("query", ["widget rollback", "zarquon migration broker", "retries"])
def test_python_and_node_rank_the_merged_corpus_identically(consumer, scope, query):
    confidence: dict = {}
    results, _ = run_query(
        consumer, query, 10, force_scan=True, use_tune=True, scope=scope, confidence_out=confidence,
    )
    node = _node_rows(consumer, query, scope)
    assert _at_round9(_rows(results)) == _at_round9(node["rows"])  # same hits, same order
    assert confidence["stats"]["n"] == node["n"]
    assert confidence["stats"]["df"] == node["df"]


@pytest.mark.skipif(not HAS_NODE, reason="node is not on PATH")
def test_python_and_node_hash_a_package_family_identically(tmp_path, family_segment, monkeypatch):
    root = _consume(tmp_path, family_segment, monkeypatch)
    results, _ = _query(root, "zq118 widget", ALL)
    assert _at_round9(_rows(results)) == _at_round9(_node_rows(root, "zq118 widget", ALL)["rows"])


def _shape(hits: list[dict]) -> list:
    """A hit as the differential law compares it: every key, the score at the
    sort key's resolution (SR-NODE-SEARCH d1)."""
    digits = fixed("ranking", "score_digits")
    return [{k: (round(v, digits) if k == "score" else v) for k, v in hit.items()} for hit in hits]


@pytest.mark.skipif(not HAS_NODE, reason="node is not on PATH")
@pytest.mark.parametrize("scope", [None, REPO, PACKAGES])
def test_fux_search_answers_identically_on_both_readers(consumer, scope):
    """`fux_search(scope)`: same hits, same keys — `package` only on a package
    hit — and the same order, in Python and in Node."""
    from fux import mcp

    call = {"query": "widget rollback", "k": 10, **({"scope": scope} if scope else {})}
    py = mcp._search(consumer, call, top=5, max_headings=3)
    message = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "fux_search", "arguments": call}}
    script = (
        "import { handle } from " + json.dumps((ENGINE / "node" / "src" / "verbs" / "mcp.mjs").as_uri()) + ";"
        f"console.log(JSON.stringify(handle(process.cwd(), {json.dumps(message)}, 5, 3).result.structuredContent));"
    )
    out = subprocess.run(
        ["node", "--input-type=module", "-e", script], cwd=consumer, capture_output=True, text=True, encoding="utf-8",
    )
    assert out.returncode == 0, out.stderr
    node = json.loads(out.stdout)
    assert _shape(py["results"]) == _shape(node["results"])
    packages = {hit.get("package") for hit in py["results"]}
    assert packages == ({NAME} if scope == PACKAGES else {None} if scope == REPO else {None, NAME})


@pytest.mark.skipif(not HAS_NODE, reason="node is not on PATH")
@pytest.mark.parametrize("scope", [None, REPO, PACKAGES])
def test_ask_json_answers_identically_on_both_readers(consumer, scope):
    """`fux ask --json [--scope]` on the Node CLI against `build_ask` in Python."""
    flag = [] if scope is None else ["--scope", scope]
    out = subprocess.run(
        ["node", str(ENGINE / "node" / "fux.mjs"), "ask", "widget", "rollback", "--json", "--top", "10", *flag],
        cwd=consumer, capture_output=True, text=True, encoding="utf-8",
    )
    assert out.returncode == 0, out.stderr
    args = SimpleNamespace(
        query="widget rollback", top=10, also=None, expand=None, fast=None, scan=True, why=False,
        related=None, sections=True, band=False, max_headings=3, explain=None, no_tune=False, scope=scope,
    )
    py = build_ask(consumer, args, compose=True, with_related=True).payload()["results"]
    assert _shape(py) == _shape(json.loads(out.stdout)["results"])


# -- W-300 + W-301: `answer` refers a package winner at its `pkg:` location ----------


def _py_answer(root: Path, query: str) -> dict:
    from fux.api import _Args
    from fux.query import build_answer

    args = _Args(query=query, json=True, band=False, no_refer=False, audit=False, receipt=False, top=None)
    return build_answer(root, args).payload


def test_answer_reads_a_package_winner_inside_the_installed_docs_package(consumer):
    payload = _py_answer(consumer, "run the zarquon migration in reverse")
    assert payload["source"] == "refer", payload
    assert payload["citation"]["id"] == f"pkg:acme-docs@{VERSION}#docs/rollback.md"
    assert payload["citation"]["freshness"] == "current"


@pytest.mark.skipif(not HAS_NODE, reason="node is not on PATH")
def test_answer_cites_the_same_package_location_on_both_readers(consumer):
    query = "run the zarquon migration in reverse"
    out = subprocess.run(
        ["node", str(ENGINE / "node" / "fux.mjs"), "answer", *query.split(), "--json"],
        cwd=consumer, capture_output=True, text=True, encoding="utf-8",
    )
    assert out.returncode == 0, out.stderr
    node = json.loads(out.stdout)
    py = _py_answer(consumer, query)
    assert node["citation"]["id"] == py["citation"]["id"] == f"pkg:acme-docs@{VERSION}#docs/rollback.md"
    assert node["citation"]["sha"] == py["citation"]["sha"]
