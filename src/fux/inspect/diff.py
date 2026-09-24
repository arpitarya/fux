"""`fux inspect --diff A B` — what moved between two reports, per document.

**W-220's fourth rung** ([SR-INSPECT](../../../records/0156_inspect.md) decision
21). The review artifact for any change that re-reads a corpus — a decoder
`VERSION`, `extract.RULES_VERSION`, an analyzer bump. Two `report.json` files in,
one descriptive diff out: distinct terms, edges, field token counts, passages,
title identity and probe ranks, per document.

🔴 **An edge that disappears is ALWAYS an alert**, whatever else moved. The
lesson is W-220 finding 5's: a decoder that stripped link targets looked like a
tidy-up and deleted every `ref` edge in the sample — the graph lost its input and
nothing about the ranking said so.

It reads two files and writes nothing. It needs no index — the reports are the
input — and it applies no lever.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..errors import FuxError

__all__ = ["compare", "load_report", "render_markdown"]

#: Per-document fields compared, and what each is called in the output.
_FIELDS = (
    ("nterms", "distinct terms"),
    ("flen", "field tokens"),
    ("passages", "passages"),
    ("word_cuts", "word-cut passages"),
    ("title", "title"),
    ("title_shared_with", "title shared with"),
    ("decoder", "decoder"),
)


def load_report(path: Path) -> dict:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise FuxError(f"cannot read an inspect report at {path}: {exc}") from exc
    if "documents" not in payload:
        raise FuxError(
            f"{path} has no per-document rows — it was written before `fux inspect` "
            "carried them (W-220). Re-run `fux inspect --json` on that index first."
        )
    return payload


def _probe_rank(row: dict):
    probe = row.get("probe")
    return None if probe is None else probe.get("title")


def compare(a: dict, b: dict) -> dict:
    """The diff as data. Deterministic: every list sorted by id."""
    rows_a = {r["id"]: r for r in a.get("documents", [])}
    rows_b = {r["id"]: r for r in b.get("documents", [])}
    added = sorted(set(rows_b) - set(rows_a))
    removed = sorted(set(rows_a) - set(rows_b))
    changed = []
    alerts = []
    for doc_id in sorted(set(rows_a) & set(rows_b)):
        ra, rb = rows_a[doc_id], rows_b[doc_id]
        moves = {}
        for key, label in _FIELDS:
            if ra.get(key) != rb.get(key):
                moves[label] = [ra.get(key), rb.get(key)]
        ea = {tuple(e) for e in ra.get("edges", [])}
        eb = {tuple(e) for e in rb.get("edges", [])}
        lost, gained = sorted(ea - eb), sorted(eb - ea)
        if lost or gained:
            moves["edges"] = {"lost": [list(e) for e in lost], "gained": [list(e) for e in gained]}
        pa, pb = _probe_rank(ra), _probe_rank(rb)
        if ra.get("probe") is not None and rb.get("probe") is not None and pa != pb:
            moves["title probe rank"] = [pa, pb]
        if lost:
            alerts.append({"id": doc_id, "lost_edges": [list(e) for e in lost]})
        if moves:
            changed.append({"id": doc_id, "moves": moves})
    for doc_id in removed:
        if rows_a[doc_id].get("edges"):
            alerts.append({"id": doc_id, "lost_edges": rows_a[doc_id]["edges"]})
    corpus = {}
    for key in ("documents", "terms", "postings", "edges"):
        va, vb = (a.get("corpus") or {}).get(key), (b.get("corpus") or {}).get(key)
        corpus[key] = [va, vb]
    return {
        "corpus": corpus,
        "added": added,
        "removed": removed,
        "changed": changed,
        "changed_count": len(changed),
        "alerts": alerts,
        "edge_loss": sum(len(x["lost_edges"]) for x in alerts),
    }


def _fmt(value) -> str:
    if isinstance(value, list):
        return "[" + ", ".join(str(v) for v in value) + "]"
    return "—" if value is None else str(value)


def render_markdown(diff: dict, *, a: str, b: str, top: int = 50) -> str:
    out: list[str] = []
    add = out.append
    add("# `fux inspect --diff` — what moved between two reports\n")
    add(f"`{a}` → `{b}`. **Descriptive.** It applies no lever and writes nothing.\n")
    if diff["alerts"]:
        add(
            f"## 🔴 Edge loss — {diff['edge_loss']} edge(s) on {len(diff['alerts'])} document(s)\n\n"
            "An edge that disappears is always an alert: the graph loses its input and no "
            "ranking number says so.\n"
        )
        for alert in diff["alerts"][:top]:
            lost = ", ".join(f"{k} → `{d}`" for k, d in alert["lost_edges"][:5])
            more = len(alert["lost_edges"]) - 5
            add(f"- `{alert['id']}` — {lost}" + (f" … {more} more" if more > 0 else ""))
        if len(diff["alerts"]) > top:
            add(f"- … {len(diff['alerts']) - top} more document(s)")
        add("")
    else:
        add("## Edge loss — none\n")
    add("## Corpus\n")
    add("| | before | after |")
    add("|---|---|---|")
    for key, (va, vb) in diff["corpus"].items():
        add(f"| {key} | {_fmt(va)} | {_fmt(vb)} |")
    add(
        f"\n{len(diff['added'])} document(s) added · {len(diff['removed'])} removed · "
        f"**{diff['changed_count']} changed**.\n"
    )
    if diff["changed"]:
        add("## Changed documents\n")
        add("| document | what moved |")
        add("|---|---|")
        for row in diff["changed"][:top]:
            parts = []
            for label, move in row["moves"].items():
                if label == "edges":
                    parts.append(f"edges −{len(move['lost'])} +{len(move['gained'])}")
                else:
                    parts.append(f"{label} {_fmt(move[0])} → {_fmt(move[1])}")
            add(f"| `{row['id']}` | {' · '.join(parts)} |")
        if diff["changed_count"] > top:
            add(f"\n… {diff['changed_count'] - top} more")
    for label, ids in (("Added", diff["added"]), ("Removed", diff["removed"])):
        if ids:
            add(f"\n## {label}\n")
            for doc_id in ids[:top]:
                add(f"- `{doc_id}`")
            if len(ids) > top:
                add(f"- … {len(ids) - top} more")
    return "\n".join(out) + "\n"
