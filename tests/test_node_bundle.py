"""The Node reader's bundle — one artefact, and it must ANSWER like its sources.

`fux.store.nodebundle` is what makes [L10](../records/0011_LAW-10-bundled-output.md)
possible: a consumer gets one generated `.mjs`, never `node/src/**`. Two things
have to hold, and they are different claims:

1. **Deterministic** — same sources, byte-identical output. Asserted directly.
2. **Equivalent** — the bundle returns what the module tree returns. A
   concatenation that parses and runs is not evidence of this; the bundler
   rewrites imports and wraps every module in a scope, and a mistake there
   produces a reader that answers *something*.

⚠ **This is the test the differential arm's sixth surface exists beside, not
instead of.** `tools/differential/node_arm.py --bundle-cap` compares the two on
a real corpus; this file makes the same comparison a unit gate so a broken
bundler fails before anyone runs a harness.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from fux.errors import FuxError
from fux.store import nodebundle

ROOT = Path(__file__).resolve().parent.parent
NODE = ROOT / "node"


def _needs_node():
    if shutil.which("node") is None:
        pytest.skip("no node on PATH")


@pytest.fixture(scope="module")
def built(tmp_path_factory) -> Path:
    """The published payload, built once for the module."""
    out = tmp_path_factory.mktemp("bundle")
    nodebundle.write(NODE, out)
    return out


# --------------------------------------------------------------------------
# 1 · determinism and shape


def test_the_bundle_is_byte_identical_across_builds():
    """L3's promise, adopted voluntarily for a build artefact (decision 14)."""
    assert nodebundle.bundle(NODE) == nodebundle.bundle(NODE)


def test_the_payload_is_the_bundle_and_its_sidecars_only():
    names = [rel for rel, _ in nodebundle.bundle_files(NODE)]
    assert names == sorted(["fux.mjs", "package.json", "mcp-tools.json", "README.md"])


def test_no_module_path_survives_in_the_bundle(built: Path):
    """The point of the exercise: nothing imports a relative file any more."""
    text = (built / "fux.mjs").read_text(encoding="utf-8")
    assert re.search(r'^import .*from "\./', text, re.M) is None
    assert re.search(r'^import .*from "\.\./', text, re.M) is None
    # Every surviving import is a Node builtin, and they are all at the top.
    imports = [m.start() for m in re.finditer(r'^import ', text, re.M)]
    specs = re.findall(r'^import .*from "([^"]+)";$', text, re.M)
    assert specs and all(s.startswith("node:") for s in specs)
    assert max(imports) < text.index("// ──")


def test_the_shebang_is_line_one_and_appears_once(built: Path):
    """`bin` points at this file, so a `#!` anywhere else is a syntax error."""
    text = (built / "fux.mjs").read_text(encoding="utf-8")
    assert text.startswith("#!/usr/bin/env node\n")
    assert text.count("#!/usr/bin/env node") == 1


def test_every_module_of_the_reader_is_in_the_bundle(built: Path):
    """A bundle missing a module still compiles — it fails at a call site.

    Counted from the tree rather than from a list: a new module must appear in
    the bundle without anybody remembering to add it here.
    """
    text = (built / "fux.mjs").read_text(encoding="utf-8")
    reachable = {rel for rel in _reachable()}
    for rel in reachable:
        assert f"// ── {rel} " in text, f"{rel} is missing from the bundle"


def _reachable() -> set[str]:
    """Module paths reachable from the entry, resolved the bundler's way.

    Re-derived here rather than asked of the bundler: a test that reused the
    bundler's own walk would be comparing it with itself.
    """
    import posixpath

    seen: set[str] = set()
    pending = [nodebundle.ENTRY]
    while pending:
        rel = pending.pop()
        if rel in seen or not (NODE / rel).is_file():
            continue
        seen.add(rel)
        text = (NODE / rel).read_text(encoding="utf-8")
        for spec in re.findall(r'^import .*from "(\.[^"]+)";$', text, re.M):
            pending.append(posixpath.normpath(posixpath.join(posixpath.dirname(rel), spec)))
    return seen


def test_the_library_surface_is_exported(built: Path):
    text = (built / "fux.mjs").read_text(encoding="utf-8")
    assert re.search(r"^export \{ open, Index \};$", text, re.M)


def test_the_bundles_version_is_derived_not_written():
    """It is not a fifth version site — `check-version-parity.py` §the bundle."""
    assert nodebundle.version(NODE) == json.loads(
        (NODE / "package.json").read_text(encoding="utf-8")
    )["version"]


# --------------------------------------------------------------------------
# 2 · the bundler REFUSES rather than skipping


def _tree(tmp_path: Path, entry: str, **extra: str) -> Path:
    node = tmp_path / "node"
    (node / "src").mkdir(parents=True)
    (node / "package.json").write_text('{"version": "9.9.9"}', encoding="utf-8")
    (node / "mcp-tools.json").write_text('{"tools": []}', encoding="utf-8")
    (node / "README.md").write_text("# x\n", encoding="utf-8")
    (node / "fux.mjs").write_text(entry, encoding="utf-8")
    for name, text in extra.items():
        (node / "src" / f"{name}.mjs").write_text(text, encoding="utf-8")
    return node


@pytest.mark.parametrize(
    "entry, expect",
    [
        ('export default 1;\n', "export default"),
        ('import x from "./src/a.mjs";\n', "does not understand this import"),
        ('import { a } from "left-pad";\n', "bare package import"),
        ('export { a } from "./src/a.mjs";\n', "does not understand this export"),
    ],
)
def test_an_unsupported_form_raises_rather_than_being_dropped(tmp_path, entry, expect):
    """🔴 A silently skipped statement is a reader that answers differently.

    Every form the tree does not use is a refusal with the offending line in
    it, so teaching the bundler is the cheap path and shipping a hole is not a
    path at all.
    """
    node = _tree(tmp_path, entry, a="export const a = 1;\n")
    with pytest.raises(FuxError) as exc:
        nodebundle.bundle(node)
    assert expect in str(exc.value)


def test_an_import_cycle_raises(tmp_path):
    """The IIFE shape cannot express one, and ESM's hoisting hides it."""
    node = _tree(
        tmp_path,
        'import { a } from "./src/a.mjs";\nconsole.log(a);\n',
        a='import { b } from "./b.mjs";\nexport const a = b;\n',
        b='import { a } from "./a.mjs";\nexport const b = a;\n',
    )
    with pytest.raises(FuxError) as exc:
        nodebundle.bundle(node)
    assert "import cycle" in str(exc.value)


def test_a_missing_module_raises(tmp_path):
    node = _tree(tmp_path, 'import { a } from "./src/gone.mjs";\n')
    with pytest.raises(FuxError) as exc:
        nodebundle.bundle(node)
    assert "imported but absent" in str(exc.value)


def test_a_builtin_name_bound_two_ways_raises(tmp_path):
    """Module bodies close over the hoisted builtins, so a collision would
    make one of them silently wrong. It raises instead."""
    node = _tree(
        tmp_path,
        'import { a } from "./src/a.mjs";\nimport { join } from "node:path";\nconsole.log(a, join);\n',
        a='import { readFileSync as join } from "node:fs";\nexport const a = join;\n',
    )
    with pytest.raises(FuxError) as exc:
        nodebundle.bundle(node)
    assert "bind `join` differently" in str(exc.value)


# --------------------------------------------------------------------------
# 3 · equivalence — the claim that matters


def _repo_with_an_index(tmp_path: Path) -> Path:
    """A minimal repo both readers can read: an index and the PII gate."""
    from fux.store import TF_FIELDS, term_hash, write_index

    (tmp_path / ".git").mkdir(exist_ok=True)
    (tmp_path / ".fux").mkdir(exist_ok=True)
    (tmp_path / ".fux" / "pii.toml").write_text("", encoding="utf-8")
    docs = tmp_path / "docs"
    docs.mkdir(exist_ok=True)
    records = []
    for i, (name, title, term, body) in enumerate(
        [
            ("retry.md", "Retry policy", "rollback", "# Retry policy\n\nRoll back with care.\n"),
            ("rank.md", "Ranking", "ranking", "# Ranking\n\nBM25F weights then saturates.\n"),
            ("index.md", "Index format", "rollback", "# Index format\n\nRollback and shards.\n"),
        ]
    ):
        (docs / name).write_text(body, encoding="utf-8")
        tf = [0] * len(TF_FIELDS)
        tf[TF_FIELDS.index("body")] = 5 - i
        flen = [0] * len(TF_FIELDS)
        flen[TF_FIELDS.index("body")] = 40 + i
        records.append({
            "id": f"file:docs/{name}", "src": "git", "loc": f"docs/{name}",
            "mode": "extracted", "title": title, "phrases": [],
            "terms": {term_hash(term): tf}, "flen": flen, "sha": "a" * 40, "edges": [],
        })
    write_index(tmp_path, records)
    return tmp_path


def _run(entry: Path, root: Path, argv: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        ["node", str(entry), *argv], capture_output=True, text=True, encoding="utf-8", cwd=root
    )
    return proc.returncode, proc.stdout


@pytest.mark.parametrize(
    "argv",
    [
        ["find", "rollback", "--json"],
        ["ask", "rollback", "--json", "--band"],
        ["ask", "ranking", "--json", "--band", "--top", "3"],
        ["answer", "rollback", "--json"],
        ["find", "zzzznomatch", "--json"],
        ["--version"],
    ],
)
def test_the_bundle_answers_exactly_what_the_module_tree_answers(tmp_path, built, argv):
    """🔴 **The definition-of-done clause: equal ANSWERS, not equal bytes.**

    W-149 §6.3. Identical output would also be produced by two readers that
    were both broken the same way, which is why the arm's sixth surface runs
    this on a real corpus too — but a unit gate is what fails first.
    """
    _needs_node()
    root = _repo_with_an_index(tmp_path)
    tree_code, tree_out = _run(NODE / "fux.mjs", root, argv)
    bundle_code, bundle_out = _run(built / "fux.mjs", root, argv)
    assert (tree_code, tree_out) == (bundle_code, bundle_out)


def test_importing_the_bundle_does_not_run_the_cli(tmp_path, built):
    """The main guard. `exports` names this file, so an import that parsed the
    caller's `process.argv` and set their exit code would be a shipped bug."""
    _needs_node()
    root = _repo_with_an_index(tmp_path)
    script = (
        # A file URL, not a path: `import("C:\\...")` is
        # ERR_UNSUPPORTED_ESM_URL_SCHEME on Windows.
        f"const m = await import({json.dumps((built / 'fux.mjs').as_uri())});\n"
        "if (process.exitCode !== undefined) { console.log('RAN'); }\n"
        f"const ix = await m.open({json.dumps(str(root))});\n"
        "const r = await ix.find('rollback', { top: 2 });\n"
        "process.stdout.write(JSON.stringify(r.map((x) => x.loc)));\n"
    )
    proc = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        capture_output=True, text=True, encoding="utf-8", cwd=root,
    )
    assert proc.returncode == 0, proc.stderr
    assert "RAN" not in proc.stdout
    assert json.loads(proc.stdout) == ["docs/retry.md", "docs/index.md"]


def test_the_bundle_finds_its_own_tool_descriptions(tmp_path, built):
    """`mcp-tools.json` sits BESIDE the bundle and two directories up from the
    module — one source file, so the path is resolved rather than constant.
    Wrong here, `fux mcp` throws ENOENT on a consumer's machine only."""
    _needs_node()
    root = _repo_with_an_index(tmp_path)
    calls = (
        json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        + "\n"
        + json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        + "\n"
    )
    proc = subprocess.run(
        ["node", str(built / "fux.mjs"), "mcp"],
        input=calls, capture_output=True, text=True, encoding="utf-8", cwd=root,
    )
    assert proc.returncode == 0, proc.stderr
    listed = json.loads(proc.stdout.splitlines()[1])
    assert [t["name"] for t in listed["result"]["tools"]] == [
        "fux_search", "fux_passage", "fux_related"
    ]


def test_the_bundle_and_the_tree_agree_on_the_mcp_surface(tmp_path, built):
    _needs_node()
    root = _repo_with_an_index(tmp_path)
    calls = "\n".join(
        json.dumps(c) for c in [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
             "params": {"name": "fux_search", "arguments": {"query": "rollback", "k": 3}}},
        ]
    ) + "\n"
    out = []
    for entry in (NODE / "fux.mjs", built / "fux.mjs"):
        proc = subprocess.run(
            ["node", str(entry), "mcp"], input=calls,
            capture_output=True, text=True, encoding="utf-8", cwd=root,
        )
        assert proc.returncode == 0, proc.stderr
        out.append(proc.stdout)
    assert out[0] == out[1]


def test_the_bundle_compiles(built: Path):
    """Cheap, and it fails first when the bundler emits something malformed."""
    _needs_node()
    proc = subprocess.run(
        ["node", "--check", str(built / "fux.mjs")], capture_output=True, text=True, encoding="utf-8"
    )
    assert proc.returncode == 0, proc.stderr
