#!/usr/bin/env python3
"""W-108 — `fux answer` over the 43 `relevance: complete` playground goldens.

Four arms, so the top-3 change and the proximity multiplier are never read off
one number:

| arm | engine | `[ranking] rerank_weight` |
|---|---|---|
| `A0` | `main` (before W-108) | `0.0` — the shipped default |
| `B0` | W-108 | `0.0` — the shipped default |
| `A1` | `main` | `1.0` — the reranker switched on |
| `B1` | W-108 | `1.0` |

`A0 -> B0` is the clean top-3 delta. `A1 -> B1` is the same change with the
document reranker on, which is **the only configuration where W-108's passage
multiplier fires at all** — and it is conflated with the reranker's own effect
on which documents are candidates, so it is reported as post-hoc.

Emits one row per query per arm. Nothing here reads a score.
"""
from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from pathlib import Path

GOLDENS = Path.home() / "my_programs/fux-playground/goldens/queries.jsonl"


def load_goldens():
    rows = []
    for line in GOLDENS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        g = json.loads(line)
        if g.get("relevance") == "complete":
            rows.append(g)
    return rows


def run(src: Path, cwd: Path, query: str) -> dict:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(src)
    env.pop("VIRTUAL_ENV", None)
    proc = subprocess.run(
        [sys.executable, "-m", "fux.cli", "answer", query, "--json", "--band", "--audit"],
        cwd=cwd, capture_output=True, text=True, env=env,
    )
    if proc.returncode != 0:
        raise SystemExit(f"answer failed ({proc.returncode}) on {query!r}:\n{proc.stderr}")
    return json.loads(proc.stdout)


def cited_docs(payload: dict) -> list[str]:
    """Every document the answer cites, `file:` prefix stripped.

    Arm A has no per-passage `id` (that key is W-108's), so its cited set is
    the one document `citation` names — which is exactly the shape being
    measured, not a limitation of the harness.
    """
    answer = payload.get("answer") or {}
    passages = answer.get("passages") or []
    ids = [p["id"] for p in passages if "id" in p]
    if not ids:
        citation = payload.get("citation") or {}
        ids = [citation["id"]] if citation.get("id") else []
    seen, out = set(), []
    for i in ids:
        d = i[5:] if i.startswith("file:") else i
        if d not in seen:
            seen.add(d)
            out.append(d)
    return out


def main() -> int:
    scratch = Path(sys.argv[1])
    arms = {
        "A0": (scratch / "arm-main/src", scratch / "pg-rw0"),
        "B0": (Path.cwd() / "src", scratch / "pg-rw0"),
        "A1": (scratch / "arm-main/src", scratch / "pg-rw1"),
        "B1": (Path.cwd() / "src", scratch / "pg-rw1"),
    }
    goldens = load_goldens()
    out = []
    for g in goldens:
        relevant = set(g["relevant"])
        for arm, (src, cwd) in arms.items():
            payload = run(src, cwd, g["q"])
            docs = cited_docs(payload)
            budget = (payload.get("audit") or {}).get("budget") or {}
            block = payload.get("confidence") or {}
            out.append({
                "id": g["id"],
                "q": g["q"],
                "arm": arm,
                "n_relevant": len(relevant),
                "source": payload.get("source", ""),
                "n_docs_cited": len(docs),
                "cited": "|".join(docs),
                "hit": int(bool(relevant & set(docs))),
                "recall": round(len(relevant & set(docs)) / len(relevant), 4) if relevant else 0.0,
                "band": block.get("band", ""),
                "separation": block.get("separation", ""),
                "support": block.get("support", ""),
                "budget_used": budget.get("used", ""),
                "budget_bytes": budget.get("bytes", ""),
                "dropped": budget.get("dropped", ""),
            })
        print(f"  {g['id']} done", file=sys.stderr)

    dest = Path(sys.argv[2])
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    print(f"{len(out)} rows -> {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
