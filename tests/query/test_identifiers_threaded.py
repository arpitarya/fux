"""W-233 — every question matched against the index is analyzed with the families.

**Why a static test.** `query_term_hashes(query)` without `ids` still works:
it analyzes with no families and returns v3's hashes. The index was written
WITH them, so the question silently lacks its canonical term (`rf-118`) and
the document that names the ID loses to one that shares its parts. That is a
defect no ranking test catches on a corpus without families, which is most of
them. So every call site in `src/` and `node/src/` is held to passing `ids`,
and the exceptions are named here with their reason.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

#: Calls that deliberately analyze WITHOUT families, and why (SR-IDENTIFIERS 7).
ALLOWED = {
    # refer's rescore analyzes the question and the passage in one function, on
    # v3's terms both: self-consistent, and it never touches the index's terms.
    ("src/fux/refer/_rescore.py", "query_term_hashes"),
    ("node/src/refer/rescore.mjs", "queryTermHashes"),
}


def _py_calls(name: str):
    for path in sorted((ROOT / "src" / "fux").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                fn = node.func
                called = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", None)
                if called == name:
                    yield path.relative_to(ROOT).as_posix(), node


def test_every_python_index_match_passes_ids():
    bad = []
    for name in ("query_term_hashes",):
        for rel, call in _py_calls(name):
            passed = len(call.args) >= 2 or any(k.arg == "ids" for k in call.keywords)
            if not passed and (rel, name) not in ALLOWED:
                bad.append(f"{rel}:{call.lineno} {name}(...) without ids")
    assert not bad, "a question analyzed without the repo's identifier families:\n  " + "\n  ".join(bad)


def test_the_confidence_and_provenance_pairs_pass_ids():
    """Pairs are aligned to the hashes by hash — analyzed differently, they misalign."""
    bad = []
    for rel in ("src/fux/query/__init__.py", "src/fux/query/provenance.py"):
        for name in ("tokenize_pairs", "analyze_pairs"):
            for r, call in _py_calls(name):
                if r == rel and len(call.args) < 2:
                    bad.append(f"{rel}:{call.lineno} {name}(...) without ids")
    assert not bad, "\n".join(bad)


def test_every_node_index_match_passes_ids():
    bad = []
    for path in sorted((ROOT / "node" / "src").rglob("*.mjs")):
        rel = path.relative_to(ROOT).as_posix()
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for m in re.finditer(r"\bqueryTermHashes\(([^()]*)\)", line):
                if line.lstrip().startswith("export function"):
                    continue
                if "," not in m.group(1) and (rel, "queryTermHashes") not in ALLOWED:
                    bad.append(f"{rel}:{lineno} {m.group(0)}")
    assert not bad, "a Node question analyzed without the repo's identifier families:\n  " + "\n  ".join(bad)


def test_the_allow_list_is_not_stale():
    """Every allowed site still exists and still omits `ids` — or it is deleted."""
    for rel, name in ALLOWED:
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert re.search(rf"\b{name}\(\s*query\s*\)", text), f"{rel}: {name}(query) is gone — drop it from ALLOWED"
