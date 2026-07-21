"""Explanation assembly — the agent-facing *why* behind every ranking."""

from __future__ import annotations

from ..index.bm25f import ScoredChunk
from .answer import Sentence


def chunk_explain_json(sc: ScoredChunk) -> list[dict]:
    return [
        {"term": term, **info}
        for term, info in sorted(
            sc.terms.items(), key=lambda kv: (-kv[1]["contribution"], kv[0])
        )
    ]


def chunk_explain_lines(sc: ScoredChunk) -> list[str]:
    lines = []
    for entry in chunk_explain_json(sc):
        tf = entry["tf"]
        lines.append(
            f"'{entry['term']}': idf {entry['idf']} · "
            f"tf h{tf['heading']}/p{tf['path']}/b{tf['body']} → {entry['contribution']}"
        )
    return lines


def sentence_explain_line(s: Sentence) -> str:
    f = s.factors
    return (
        f"passage {f.get('passage', 0)} × (overlap {f.get('overlap', 0)} + 0.05) "
        f"× (0.5 + 0.5·centrality {f.get('centrality', 0)}) = {round(s.score, 4)}"
    )
