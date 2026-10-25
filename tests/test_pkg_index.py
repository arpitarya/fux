"""SR-PKG-INDEX (W-299) — a pinned index package: parsed, verified, refused, inflated.

The fixture is `tests/fixtures/pkg-index/docs/`, ingested here in a temporary
directory (never at this repo's root, W-244), laid out as a segment and
installed twice — as the PyPI import package `acme_docs_index/` on `sys.path`
with a `.dist-info`, and as `node_modules/acme-docs-index/` under the consumer —
so Python and Node see identical segment bytes. Each test names the decision it
holds.
"""

from __future__ import annotations

import importlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from fux import plugins
from fux.constants import fixed
from fux.derive import segments
from fux.errors import FuxError
from fux.ingest.run import run as ingest
from fux.schema import load as load_schema
from l12_fixtures import config_file, write_config, write_dirs

ENGINE = Path(__file__).resolve().parents[1]
FIXTURE = ENGINE / "tests" / "fixtures" / "pkg-index"
PLUGINS_MJS = ENGINE / "node" / "src" / "config" / "plugins.mjs"
SEGMENTS_MJS = ENGINE / "node" / "src" / "derive" / "segments.mjs"
NAME = "acme-docs-index"
IMPORT = "acme_docs_index"
VERSION = "1.0.0"
HAS_NODE = shutil.which("node") is not None


@pytest.fixture(autouse=True)
def _fresh_cache():
    plugins.reset()
    yield
    plugins.reset()


def _repo(root: Path, docs: Path | None = None) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    config_file(root, "pii").parent.mkdir(parents=True, exist_ok=True)
    config_file(root, "pii").write_text("", encoding="utf-8")
    write_dirs(root, "docs\n")
    write_config(root)
    if docs is not None:
        shutil.copytree(docs, root / "docs")
    else:
        (root / "docs").mkdir(exist_ok=True)
        (root / "docs" / "own.md").write_text("# Own page\n\nthe consumer's own words\n", encoding="utf-8")
    return root


@pytest.fixture(scope="module")
def segment(tmp_path_factory) -> Path:
    """The packed segment: ingested from the fixture docs, laid out by hand
    (`fux pack` is W-302's), its manifest validated against the schema."""
    author = _repo(tmp_path_factory.mktemp("author") / "repo", FIXTURE / "docs")
    plugins.reset()
    ingest(author, refresh_urls=False, full=False)
    out = tmp_path_factory.mktemp("segment")
    (out / "index").mkdir()
    for shard in sorted((author / fixed("index", "dir")).glob("*" + fixed("index", "shard_suffix"))):
        shutil.copyfile(shard, out / "index" / shard.name)
    shutil.copyfile(author / fixed("files", "identifiers"), out / "identifiers.toml")
    header = json.loads((sorted((out / "index").iterdir())[0]).read_bytes().split(b"\n", 1)[0])
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


def _install(base: Path, segment: Path, consumer: Path, version: str = VERSION) -> Path:
    """Install `segment` as the PyPI and the npm package; return the site dir."""
    site = base / "site"
    shutil.copytree(segment, site / IMPORT)
    info = site / f"{IMPORT}-{version}.dist-info"
    info.mkdir(parents=True)
    (info / "METADATA").write_text(f"Metadata-Version: 2.1\nName: {NAME}\nVersion: {version}\n", encoding="utf-8")
    npm = consumer / "node_modules" / NAME
    shutil.copytree(segment, npm)
    (npm / "package.json").write_text(json.dumps({"name": NAME, "version": version}), encoding="utf-8")
    return site


@pytest.fixture
def consumer(tmp_path, segment, monkeypatch):
    root = _repo(tmp_path / "consumer")
    site = _install(tmp_path, segment, root)
    monkeypatch.syspath_prepend(str(site))
    importlib.invalidate_caches()
    plugins.reset()
    ingest(root, refresh_urls=False, full=False)
    return root


def _pin_row(digest: str, *, npm: str | None = NAME, pypi: str | None = NAME, extra: str = "") -> str:
    lines = ["", "[[package]]", f'name = "{NAME}"', 'kind = "index"', f'version = "{VERSION}"', f'digest = "{digest}"']
    if npm:
        lines.append(f'npm = "{npm}"')
    if pypi:
        lines.append(f'pypi = "{pypi}"')
    return "\n".join(lines) + "\n" + extra


def _declare(root: Path, row: str) -> None:
    target = plugins.path(root)
    target.write_text(target.read_text(encoding="utf-8") + row, encoding="utf-8")
    plugins.reset()


def _node(script: str, root: Path) -> dict:
    out = subprocess.run(
        ["node", "--input-type=module", "-e", script], cwd=root, capture_output=True, text=True, encoding="utf-8",
    )
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)


def _node_check(root: Path) -> list:
    return _node(
        f"import {{ indexes, checkIndex }} from {json.dumps(PLUGINS_MJS.as_uri())};"
        f"const pins=[...indexes(process.cwd()).values()];"
        f"console.log(JSON.stringify(pins.map(p=>checkIndex(process.cwd(),p))));",
        root,
    )


def _py_check(root: Path) -> list:
    return [list(plugins._check_index(pin)) for pin in plugins.indexes(root).values()]


def _as_node(message: str | None, version: str = VERSION) -> str | None:
    """Python's refusal in Node's words: only the install line differs."""
    if message is None:
        return None
    return message.replace(f"pip install {NAME}=={version}", f"npm install {NAME}@{version}")


# -- d2: the row ---------------------------------------------------------------


def test_an_index_row_is_parsed_beside_package_rows():
    text = '[[package]]\nname = "fux-decoder-json"\nversion = "1"\n' + _pin_row("sha256:ab")
    assert set(plugins.parse(text, "f")) == {"fux-decoder-json"}
    pin = plugins.parse_indexes(text, "f")[NAME]
    assert (pin.version, pin.digest, pin.npm, pin.pypi, pin.import_name) == (VERSION, "sha256:ab", NAME, NAME, IMPORT)


@pytest.mark.parametrize(
    "row, words",
    [
        (_pin_row("", extra='suffixes = [".md"]\n'), "delete its `suffixes` key"),
        (_pin_row("", extra='colour = "red"\n'), "unknown key(s) colour"),
        (_pin_row("") + _pin_row(""), "is declared twice"),
        (_pin_row("", npm=None, pypi=None), "names neither an `npm` nor a `pypi`"),
        ('[[package]]\nname = "Bad/Name"\nkind = "index"\nversion = "1"\npypi = "x"\n', "must match"),
        ('[[package]]\nname = "fux-decoder-json"\nkind = "decoder"\nversion = "1"\n', "may only be 'index'"),
    ],
)
def test_a_malformed_index_row_is_refused_by_name(row, words):
    with pytest.raises(FuxError, match=None) as caught:
        plugins.parse_indexes(row, "f")
    assert words in str(caught.value)


def test_an_index_name_and_a_package_name_cannot_collide():
    text = '[[package]]\nname = "fux-decoder-json"\nversion = "1"\n' + _pin_row("").replace(NAME, "fux-decoder-json", 1)
    with pytest.raises(FuxError, match="declared twice"):
        plugins.parse(text, "f")


def test_render_keeps_index_rows():
    pin = plugins.IndexPin(name=NAME, version=VERSION, digest="sha256:ab", npm=NAME, pypi=NAME)
    text = plugins.render([], [pin])
    assert plugins.parse_indexes(text, "f") == {NAME: pin}


# -- d4: the digest ----------------------------------------------------------------


def test_the_digest_covers_the_segment_files_only(tmp_path, segment):
    wheel, tarball = tmp_path / "wheel" / IMPORT, tmp_path / "npm" / NAME
    shutil.copytree(segment, wheel)
    shutil.copytree(segment, tarball)
    (tarball / "package.json").write_text("{}", encoding="utf-8")
    (wheel / "py.typed").write_text("", encoding="utf-8")
    (tarball / fixed("plugins.index", "manifest")).write_text("{}", encoding="utf-8")
    assert plugins.segment_digest(wheel) == plugins.segment_digest(tarball) == plugins.segment_digest(segment)
    shard = sorted((tarball / "index").iterdir())[0]
    shard.write_bytes(shard.read_bytes() + b" ")
    assert plugins.segment_digest(tarball) != plugins.segment_digest(segment)


# -- d5, d7: located, verified, refused in order ------------------------------------


def test_a_good_pin_verifies_and_locates(consumer, segment):
    _declare(consumer, _pin_row(plugins.segment_digest(segment)))
    pin = plugins.indexes(consumer)[NAME]
    assert plugins.check_index(pin) is None
    assert plugins.locate_index(pin).name == IMPORT
    assert plugins.problems(consumer) == []


def test_pin_index_reads_what_is_installed(consumer, segment):
    pin = plugins.pin_index(NAME, npm=NAME)
    assert (pin.version, pin.digest) == (VERSION, plugins.segment_digest(segment))


def test_missing_and_other_version_name_the_package_and_the_install_line(consumer, segment):
    _declare(consumer, _pin_row(plugins.segment_digest(segment)).replace(f'pypi = "{NAME}"', 'pypi = "acme-absent"'))
    problem = plugins.check_index(plugins.indexes(consumer)[NAME])
    assert "not installed" in problem and "pip install acme-absent==1.0.0" in problem
    plugins.path(consumer).write_text(
        plugins.path(consumer).read_text(encoding="utf-8").replace('pypi = "acme-absent"', f'pypi = "{NAME}"')
        .replace(f'version = "{VERSION}"\ndigest', 'version = "2.0.0"\ndigest'), encoding="utf-8",
    )
    plugins.reset()
    problem = plugins.check_index(plugins.indexes(consumer)[NAME])
    assert f"{NAME} {VERSION} is installed" in problem and f"pip install {NAME}==2.0.0" in problem


def test_drift_stops_every_verb(consumer, segment, monkeypatch):
    _declare(consumer, _pin_row(plugins.segment_digest(segment)))
    shard = sorted((Path(sys.path[0]) / IMPORT / "index").iterdir())[0]
    shard.write_bytes(shard.read_bytes() + b"\n")
    with pytest.raises(FuxError, match="has drifted") as caught:
        plugins.require(consumer)
    assert f"pip install {NAME}=={VERSION}" in str(caught.value)
    with pytest.raises(FuxError, match="has drifted"):
        segments.inflate_all(consumer)
    assert not segments.packages_dir(consumer).exists() or not any(segments.packages_dir(consumer).iterdir())


def test_no_digest_and_no_registry_key_are_refused(consumer):
    _declare(consumer, _pin_row(""))
    assert "pinned without a digest" in plugins.check_index(plugins.indexes(consumer)[NAME])
    plugins.path(consumer).write_text(
        plugins.path(consumer).read_text(encoding="utf-8").replace(f'pypi = "{NAME}"\n', ""), encoding="utf-8"
    )
    plugins.reset()
    assert "no `pypi` name" in plugins.check_index(plugins.indexes(consumer)[NAME])


# -- d6: lockstep ---------------------------------------------------------------------


def _rewrite_headers(directory: Path, change: dict) -> None:
    for shard in sorted((directory / "index").iterdir()):
        head, rest = shard.read_bytes().split(b"\n", 1)
        header = json.loads(head) | change
        shard.write_bytes(json.dumps(header, separators=(",", ":"), sort_keys=True).encode() + b"\n" + rest)


def _repack(directory: Path) -> str:
    digest = plugins.segment_digest(directory)
    manifest = directory / fixed("plugins.index", "manifest")
    data = json.loads(manifest.read_text(encoding="utf-8")) | {"digest": digest}
    manifest.write_text(json.dumps(data), encoding="utf-8")
    return digest


def test_a_foreign_analyzer_is_refused_by_name(consumer):
    installed = Path(sys.path[0]) / IMPORT
    _rewrite_headers(installed, {"analyzer": "v0"})
    _declare(consumer, _pin_row(_repack(installed)))
    problem = plugins.check_index(plugins.indexes(consumer)[NAME])
    assert "foreign segment" in problem and 'analyzer "v0"' in problem


def test_another_identifiers_digest_is_not_refused(consumer):
    installed = Path(sys.path[0]) / IMPORT
    _rewrite_headers(installed, {"identifiers": "0" * 32})
    _declare(consumer, _pin_row(_repack(installed)))
    assert plugins.check_index(plugins.indexes(consumer)[NAME]) is None


def test_a_manifest_that_disagrees_with_its_shards_is_refused(consumer, segment):
    installed = Path(sys.path[0]) / IMPORT
    (installed / fixed("plugins.index", "manifest")).write_text('{"digest": "sha256:00"}', encoding="utf-8")
    _declare(consumer, _pin_row(plugins.segment_digest(segment)))
    assert "is malformed" in plugins.check_index(plugins.indexes(consumer)[NAME])


# -- d8: the runtime --------------------------------------------------------------------


def _tree(directory: Path) -> dict[str, bytes]:
    return {
        p.relative_to(directory).as_posix(): p.read_bytes()
        for p in sorted(directory.rglob("*"))
        if p.is_file() and p.name != fixed("runtime", "stamp")
    }


def test_the_runtime_is_rebuilt_only_when_the_pin_digest_changes(consumer, segment):
    digest = plugins.segment_digest(segment)
    _declare(consumer, _pin_row(digest))
    assert segments.inflate_all(consumer) == [f"{NAME}@{VERSION}"]
    target = segments.segment_dir(consumer, plugins.indexes(consumer)[NAME])
    assert (target / fixed("plugins.index", "pin_stamp")).read_text(encoding="utf-8") == digest + "\n"
    assert (target / ".fux" / "runtime" / fixed("runtime", "manifest")).is_file()
    before = {p: p.stat().st_mtime_ns for p in target.rglob("*") if p.is_file()}
    assert segments.inflate_all(consumer) == []
    assert {p: p.stat().st_mtime_ns for p in target.rglob("*") if p.is_file()} == before
    (target / fixed("plugins.index", "pin_stamp")).write_text("sha256:old\n", encoding="utf-8")
    assert segments.inflate_all(consumer) == [f"{NAME}@{VERSION}"]
    stale = segments.packages_dir(consumer) / "gone@0.1.0"
    stale.mkdir()
    segments.inflate_all(consumer)
    assert not stale.exists()


def test_fux_build_inflates_the_pinned_packages(consumer, segment):
    from fux.derive import build

    _declare(consumer, _pin_row(plugins.segment_digest(segment)))
    build(consumer)
    assert segments.is_current(consumer, plugins.indexes(consumer)[NAME])


# -- d7, d8: the Node twin, held equal -----------------------------------------------------


@pytest.mark.skipif(not HAS_NODE, reason="node is not on PATH")
@pytest.mark.parametrize("case", ["good", "drifted", "other_version", "no_digest", "foreign", "manifest", "missing"])
def test_python_and_node_verify_and_refuse_identically(consumer, segment, case):
    digest = plugins.segment_digest(segment)
    py_seg, node_seg = Path(sys.path[0]) / IMPORT, consumer / "node_modules" / NAME
    version = VERSION
    if case == "drifted":
        for seg in (py_seg, node_seg):
            shard = sorted((seg / "index").iterdir())[0]
            shard.write_bytes(shard.read_bytes() + b"\n")
    elif case == "other_version":
        version = "9.9.9"
    elif case == "no_digest":
        digest = ""
    elif case == "foreign":
        for seg in (py_seg, node_seg):
            _rewrite_headers(seg, {"tf_fields": ["body"]})
            digest = _repack(seg)
    elif case == "manifest":
        for seg in (py_seg, node_seg):
            (seg / fixed("plugins.index", "manifest")).write_text("{}", encoding="utf-8")
    elif case == "missing":
        shutil.rmtree(node_seg)
        shutil.rmtree(py_seg)
        shutil.rmtree(Path(sys.path[0]) / f"{IMPORT}-{VERSION}.dist-info")
        importlib.invalidate_caches()
    _declare(consumer, _pin_row(digest).replace(f'version = "{VERSION}"', f'version = "{version}"'))
    py = _py_check(consumer)
    node = _node_check(consumer)
    expected_code = None if case == "good" else case
    assert [row[0] for row in py] == [row[0] for row in node] == [expected_code]
    assert [_as_node(row[1], version) for row in py] == [
        row[1] for row in node
    ]


@pytest.mark.skipif(not HAS_NODE, reason="node is not on PATH")
def test_node_gate_refuses_every_verb_before_reading(consumer, segment):
    _declare(consumer, _pin_row("sha256:" + "0" * 64))
    out = subprocess.run(
        ["node", str(ENGINE / "node" / "fux.mjs"), "find", "widget"],
        cwd=consumer, capture_output=True, text=True, encoding="utf-8",
    )
    assert out.returncode == 1
    assert "has drifted" in out.stderr and f"npm install {NAME}@{VERSION}" in out.stderr


@pytest.mark.skipif(not HAS_NODE, reason="node is not on PATH")
def test_python_and_node_inflate_byte_identical_runtimes(tmp_path, consumer, segment):
    _declare(consumer, _pin_row(plugins.segment_digest(segment)))
    segments.inflate_all(consumer)
    twin = tmp_path / "twin"
    shutil.copytree(consumer, twin, ignore=shutil.ignore_patterns("runtime"))
    built = _node(
        f"import {{ inflateAll }} from {json.dumps(SEGMENTS_MJS.as_uri())};"
        f"import {{ buildOwn }} from {json.dumps(SEGMENTS_MJS.with_name('build.mjs').as_uri())};"
        f"console.log(JSON.stringify(inflateAll(process.cwd(), buildOwn)));",
        twin,
    )
    assert built == [f"{NAME}@{VERSION}"]
    pin = plugins.indexes(consumer)[NAME]
    python_tree = _tree(segments.segment_dir(consumer, pin))
    node_tree = _tree(segments.segment_dir(twin, pin))
    assert python_tree.keys() == node_tree.keys()
    assert [k for k in python_tree if python_tree[k] != node_tree[k]] == []


# -- d2, d9: setup and doctor --------------------------------------------------------------


def test_setup_writes_an_index_row_only_when_told_and_pin_repins_it(consumer, segment):
    from fux import setup as setup_mod

    setup_mod.run(consumer, agents=False)
    plugins.reset()
    assert plugins.indexes(consumer) == {}  # never proposed by the scan
    setup_mod.run(consumer, agents=False, index=NAME, index_npm=NAME)
    plugins.reset()
    pin = plugins.indexes(consumer)[NAME]
    assert (pin.version, pin.digest, pin.npm, pin.pypi) == (VERSION, plugins.segment_digest(segment), NAME, NAME)
    assert plugins.declared(consumer)  # the decoder rows survived the rewrite
    plugins.path(consumer).write_text(
        plugins.path(consumer).read_text(encoding="utf-8").replace(pin.digest, "sha256:stale"), encoding="utf-8"
    )
    plugins.reset()
    setup_mod.run(consumer, agents=False)
    plugins.reset()
    assert plugins.indexes(consumer)[NAME].digest == "sha256:stale"  # kept without --pin
    setup_mod.run(consumer, agents=False, pin=True)
    plugins.reset()
    assert plugins.indexes(consumer)[NAME].digest == pin.digest


def test_doctor_prints_the_package_rows_and_the_merged_count(consumer, segment, monkeypatch):
    from fux import health

    _declare(consumer, _pin_row(plugins.segment_digest(segment)))
    rows = health._index_packages(consumer)
    assert [r.ok for r in rows] == [True] and f"{NAME} {VERSION}: verified, 3 document(s)" in rows[0].detail
    merged = health._merged_corpus(consumer)
    assert merged.ok and merged.detail.startswith("4 document(s) merged (repo 1, acme-docs-index 3)")
    monkeypatch.setattr(health, "fixed", lambda t, k: 3 if (t, k) == ("scale", "ceiling") else fixed(t, k))
    above = health._merged_corpus(consumer)
    assert not above.ok and above.level == "warn" and "SR-WORK-SCALE" in above.detail


# -- d11 (W-301): `pkg:` locations, read inside the installed docs package ---------------

DOCS = "acme-docs"
DOCS_IMPORT = "acme_docs"
MCP_MJS = ENGINE / "node" / "src" / "verbs" / "mcp.mjs"


def _install_docs(site: Path, consumer: Path, version: str = VERSION) -> Path:
    """The DOCS package the segment indexes (manifest `content`), installed on
    both registries: `acme_docs/docs/*.md` beside a `.dist-info`, and
    `node_modules/acme-docs/docs/*.md` beside a `package.json`. Returns the
    Python package root."""
    py = site / DOCS_IMPORT
    shutil.copytree(FIXTURE / "docs", py / "docs")
    info = site / f"{DOCS_IMPORT}-{version}.dist-info"
    info.mkdir(parents=True)
    (info / "METADATA").write_text(f"Metadata-Version: 2.1\nName: {DOCS}\nVersion: {version}\n", encoding="utf-8")
    npm = consumer / "node_modules" / DOCS
    shutil.copytree(FIXTURE / "docs", npm / "docs")
    (npm / "package.json").write_text(json.dumps({"name": DOCS, "version": version}), encoding="utf-8")
    importlib.invalidate_caches()
    return py


@pytest.fixture
def pinned(consumer, segment):
    """The consumer with the index pinned and inflated, and the docs installed."""
    _declare(consumer, _pin_row(plugins.segment_digest(segment)))
    segments.inflate_all(consumer)
    docs = _install_docs(Path(sys.path[0]), consumer)
    return consumer, docs


def _segment_records(root: Path) -> dict:
    """A segment's records, read directly from its inflated repository layout —
    the way every root-keyed reader opens a pinned package."""
    from fux.store import read_index

    return read_index(segments.segment_dir(root, plugins.indexes(root)[NAME]))


def _location(loc: str) -> str:
    return f"pkg:{DOCS}@{VERSION}#{loc}"


def test_a_segment_hit_names_the_docs_package_and_the_index_package(pinned):
    from fux.acquire import pkgsrc

    root, _ = pinned
    seg = pkgsrc.segment(plugins.indexes(root)[NAME])
    assert seg.content == pkgsrc.Content(version=VERSION, npm=DOCS, pypi=DOCS)
    records = _segment_records(root)
    assert records
    for doc_id, record in records.items():
        assert doc_id.startswith("file:")  # the record id is unchanged
        assert pkgsrc.hit_fields(doc_id, record["loc"], seg) == {"location": _location(record["loc"]), "package": NAME}
    assert pkgsrc.hit_fields("file:docs/own.md", "docs/own.md") == {"location": "file:docs/own.md", "package": None}


def test_fux_passage_reads_a_package_file_in_place_with_its_fresh_sha(pinned):
    from fux import mcp
    from fux.acquire import pkgsrc
    from fux.store import content_sha

    root, docs = pinned
    for record in _segment_records(root).values():
        location = _location(record["loc"])
        installed = docs / record["loc"]
        got = mcp._passage(root, {"path": location})
        assert got["text"] == "\n".join(installed.read_text(encoding="utf-8").splitlines())
        # the fresh sha is the ledger hash of the INSTALLED bytes -- and so equals
        # the sha the segment's record was indexed at
        assert got["sha"] == content_sha(installed.read_bytes()) == record["sha"]
        assert pkgsrc.read(root, location).path == installed.resolve()  # read in place, never a copy
    one = mcp._passage(root, {"path": _location("docs/glossary.md"), "line_start": 1, "line_end": 1})
    assert one["text"] == (docs / "docs" / "glossary.md").read_text(encoding="utf-8").splitlines()[0]


@pytest.mark.parametrize("fragment", ["../../etc/passwd", "docs/../../x", f"../{IMPORT}/fux-index.json", "/etc/passwd"])
def test_a_traversal_out_of_the_docs_package_is_refused_after_collapse(pinned, fragment):
    from fux import mcp

    root, _ = pinned
    with pytest.raises(FuxError) as caught:
        mcp._passage(root, {"path": _location(fragment)})
    assert str(caught.value) == f"'{_location(fragment)}' resolves outside {DOCS}@{VERSION}"


def test_another_installed_docs_version_is_refused_naming_both_and_the_install_line(consumer, segment):
    from fux import mcp

    _declare(consumer, _pin_row(plugins.segment_digest(segment)))
    _install_docs(Path(sys.path[0]), consumer, version="1.0.1")
    with pytest.raises(FuxError) as caught:
        mcp._passage(consumer, {"path": _location("docs/glossary.md")})
    text = str(caught.value)
    assert f"{DOCS} 1.0.1 is installed" in text and f"indexes {DOCS} {VERSION}" in text
    assert f"pip install {DOCS}=={VERSION}" in text


def test_a_missing_docs_package_an_unpinned_one_and_a_malformed_location_are_refused(consumer, segment):
    from fux.acquire import pkgsrc

    _declare(consumer, _pin_row(plugins.segment_digest(segment)))
    with pytest.raises(FuxError, match=f"{DOCS} is not installed.*pip install {DOCS}=={VERSION}"):
        pkgsrc.read(consumer, _location("docs/glossary.md"))
    with pytest.raises(FuxError, match="which no pinned index package describes"):
        pkgsrc.read(consumer, f"pkg:{DOCS}@9.9.9#docs/glossary.md")
    for bad in (f"pkg:{DOCS}#docs/glossary.md", f"pkg:{DOCS}@{VERSION}", f"pkg:@{VERSION}#x"):
        with pytest.raises(FuxError, match="is not a pkg: location"):
            pkgsrc.read(consumer, bad)


def test_the_refer_plane_reads_a_pkg_location_locally(pinned):
    from fux.acquire import source

    root, docs = pinned
    location = _location("docs/rollback.md")
    got = source.fetch_document(root, location, "docs/rollback.md")
    want = (source.PKG, "docs/rollback.md", (docs / "docs" / "rollback.md").read_bytes())
    assert (got.strategy, got.loc, got.content) == want
    assert source.PKG in source.LOCAL and source.from_acquired(root, location, "docs/rollback.md") is None


def test_verbs_that_read_only_the_repository_refuse_a_pkg_location_by_name(pinned):
    from fux import correct, mcp
    from fux import graph as graph_mod
    from fux.inspect import xray

    root, _ = pinned
    location = _location("docs/glossary.md")
    for call, verb in (
        (lambda: correct._resolve(root, location), "fux correct"),
        (lambda: graph_mod._resolve_doc(root, location), "the graph"),
        (lambda: mcp._related(root, {"path": location}), "fux_related"),
        (lambda: xray.document(root, None, location), "fux inspect"),
    ):
        with pytest.raises(FuxError) as caught:
            call()
        assert str(caught.value) == (
            f"'{location}' is a pkg: location, and {verb} reads only this repository's own documents"
            " - a pinned package's file is read with fux_passage"
        )


def _passage_both(root: Path, path: str) -> tuple[dict, dict]:
    from fux import mcp

    message = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
               "params": {"name": "fux_passage", "arguments": {"path": path}}}
    py = mcp._handle(root, message, top=5, max_headings=3)["result"]
    node = _node(
        f"import {{ handle }} from {json.dumps(MCP_MJS.as_uri())};"
        f"console.log(JSON.stringify(handle(process.cwd(), {json.dumps(message)}, 5, 3).result));",
        root,
    )
    return py, node


@pytest.mark.skipif(not HAS_NODE, reason="node is not on PATH")
def test_python_and_node_read_the_same_package_passage_and_refuse_alike(pinned):
    root, _ = pinned
    for record in _segment_records(root).values():
        py, node = _passage_both(root, _location(record["loc"]))
        assert py["structuredContent"] == node["structuredContent"]
        assert py["structuredContent"]["sha"] == record["sha"]
    for bad in (_location("docs/../../x"), _location("docs/absent.md"), f"pkg:{DOCS}@9.9.9#x", "pkg:nothing"):
        py, node = _passage_both(root, bad)
        assert py["isError"] and node["isError"]
        assert py["content"][0]["text"] == node["content"][0]["text"]


@pytest.mark.skipif(not HAS_NODE, reason="node is not on PATH")
def test_python_and_node_refuse_a_drifted_docs_package_alike(consumer, segment):
    _declare(consumer, _pin_row(plugins.segment_digest(segment)))
    _install_docs(Path(sys.path[0]), consumer, version="1.0.1")
    py, node = _passage_both(consumer, _location("docs/glossary.md"))
    want = py["content"][0]["text"].replace(f"pip install {DOCS}=={VERSION}", f"npm install {DOCS}@{VERSION}")
    assert node["content"][0]["text"] == want
