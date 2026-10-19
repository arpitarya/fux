"""W-287 — the Python and Node refer planes agree about a table, byte for byte.

`text/chunk.py` and `node/src/refer/chunk.mjs` both turn a Markdown table into
row passages carrying `TableRow` metadata (B1), and `refer/_rescore.py` and
`node/src/refer/rescore.mjs` both score those rows on three fields with a column
selector (B2–B5). A disagreement between them ships as a `--fast`/scan answer
that cites a different row, so this runs both on the same inputs and compares
everything a citation is built from: each passage's lines, text and row, and
each scored passage's locator, score and `columns_matched` — with the mechanism
off and on.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from l12_fixtures import chunk_bounds, scoring, template_tune

from fux.refer._rescore import rescore
from fux.text.chunk import chunk

ROOT = Path(__file__).resolve().parents[2]
NODE_SRC = ROOT / "node" / "src"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")

DOCS = {
    "tickets.md": (
        "# Tickets\n\nOpen work, by owner.\n\n"
        "| Ticket | Owner | Status | Notes |\n|---|---|---|---|\n"
        "| INC1 | Alice | closed | reopened once, still open questions |\n"
        "| INC2 | Bob \\| B | open | none |\n"
        "| INC3 | Carol | closed | see INC2 |\n"
        "| inc4 | Dan |  | open source dependency |\n\n"
        "## Props\n\nSome prose about the service owner.\n\n"
        "| Field | Value |\n|---|---|\n| Owner | Erin |\n| Status | open |\n| Pager | sre-oncall |\n"
    ),
    "pipeless.md": "# Hosts\n\nhost | owner | region\n--- | --- | ---\nweb-1 | Alice | eu\nweb-2 | Bob | us\ndb-1 | Alice | eu\n",
    "prose.md": "# Notes\n\nThe owner of INC2 is Bob, and its status is open.\n",
    "Owners.xlsx": "## Owners\n\n| Ticket | Owner |\n|---|---|\n| INC7 | Gail |\n| INC8 | Hana |\n",
}
QUERIES = ["status open", "owner of INC2", "INC2", "pager", "alice eu", "who owns web-2"]


def _python(column_weight: float) -> dict:
    candidates = []
    passages = {}
    for loc, text in DOCS.items():
        generated = loc.endswith(".xlsx")
        ps = chunk(text, **chunk_bounds(), line_numbers=not generated, frontmatter=False)
        passages[loc] = [
            {
                "heading": p.heading,
                "text": p.text,
                "line_start": p.line_start,
                "line_end": p.line_end,
                "row": None
                if p.row is None
                else {
                    "label": p.row.label,
                    "ordinal": p.row.ordinal,
                    "columns": list(p.row.columns),
                    "values": list(p.row.values),
                    "key": p.row.key,
                    "record": p.row.record,
                },
                "cells": None if p.cells is None else [list(c) for c in p.cells],
            }
            for p in ps
        ]
        candidates.append((f"file:{loc}", loc, "sha", ps))
    scored = {
        q: [
            [s.locator, s.score, list(s.columns_matched)]
            for s in rescore(
                q,
                candidates,
                scoring=scoring(),
                weight=0.0,
                proximity=template_tune().proximity,
                column_weight=column_weight,
            )
        ]
        for q in QUERIES
    }
    return {"passages": passages, "scored": scored}


_NODE = """
const chunkMod = await import(%(chunk)s);
const rescoreMod = await import(%(rescore)s);
const bm = await import(%(bm25f)s);
const input = %(input)s;
const scoring = new bm.Scoring(input.k1, input.b, input.weights, input.anchor, input.section);
const candidates = [];
const passages = {};
for (const [loc, text] of Object.entries(input.docs)) {
  const generated = loc.endsWith(".xlsx");
  const ps = chunkMod.chunk(text, { ...input.bounds, lineNumbers: !generated, frontmatter: false });
  passages[loc] = ps.map((p) => ({
    heading: p.heading, text: p.text, line_start: p.line_start, line_end: p.line_end,
    row: p.row, cells: chunkMod.cellsOf(p.row),
  }));
  candidates.push(["file:" + loc, loc, "sha", ps]);
}
const scored = {};
for (const q of input.queries) {
  scored[q] = rescoreMod.rescore(q, candidates, { scoring, weight: 0.0, proximity: null, columnWeight: input.columnWeight })
    .map((s) => [s.locator, s.score, s.columns_matched]);
}
process.stdout.write(JSON.stringify({ passages, scored }));
"""


def _node(column_weight: float) -> dict:
    s = scoring()
    bounds = chunk_bounds()
    payload = {
        "docs": DOCS,
        "queries": QUERIES,
        "columnWeight": column_weight,
        "k1": s.k1,
        "b": s.b,
        "weights": list(s.weights),
        "anchor": s.anchor,
        "section": s.section,
        "bounds": {
            "minPassageBytes": bounds["min_passage_bytes"],
            "maxPassageBytes": bounds["max_passage_bytes"],
            "tableRowsPerPassage": bounds["table_rows_per_passage"],
        },
    }
    script = _NODE % {
        "chunk": json.dumps((NODE_SRC / "refer" / "chunk.mjs").as_uri()),
        "rescore": json.dumps((NODE_SRC / "refer" / "rescore.mjs").as_uri()),
        "bm25f": json.dumps((NODE_SRC / "query" / "bm25f.mjs").as_uri()),
        "input": json.dumps(payload),
    }
    out = subprocess.run(
        ["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=True
    )
    return json.loads(out.stdout)


@pytest.mark.parametrize("column_weight", [0.0, 1.0])
def test_python_and_node_chunk_and_score_a_table_identically(column_weight):
    py, js = _python(column_weight), _node(column_weight)
    assert py["passages"] == js["passages"]
    for q in QUERIES:
        assert py["scored"][q] == js["scored"][q], q


def test_the_inputs_reach_every_mechanism():
    """A parity test over inputs that never select a column proves nothing about
    the selector — so this asserts the inputs exercise B3, B4, B5 and C3."""
    py = _python(1.0)
    rows = [p["row"] for ps in py["passages"].values() for p in ps if p["row"]]
    assert any(r["record"] for r in rows), "no record table (B5)"
    assert any(r["key"] >= 0 for r in rows), "no key column (B4)"
    assert any(m for q in QUERIES for _l, _s, m in py["scored"][q]), "no column selected (B3)"
    assert any("#Owners!R" in loc for q in QUERIES for loc, _s, _m in py["scored"][q]), "no sheet locator (C3)"
