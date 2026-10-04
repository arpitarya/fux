"""W-249: digest both captures and compare them, byte for byte.

usage: compare.py <cap-dir> <evidence-dir> <corpus> ...

Writes `digests-{before,after}-<corpus>.jsonl` — one row per MCP response line
(its JSON-RPC id and the sha256 of the line) and one per serve route (method,
path, status, content type, sha256 of the body) — then prints the count of
identical and different rows per corpus. stderr and the exit code of the MCP
session are compared too.

`/inspect/index` rows also carry `sha256_tie_normalised`: the body with each
`families.misfits[].missing` list sorted. That list's order is a stable sort
whose ties fall back to set iteration order, which `PYTHONHASHSEED` moves
between two processes of the SAME code (`inspect/lenses.py`); residency does
not reach that job, so a difference confined to it is the seed, not the change.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def digests(side: Path, corpus: str) -> list[dict]:
    rows = []
    stdout = (side / f"{corpus}-mcp.stdout").read_bytes()
    for n, line in enumerate(stdout.split(b"\n")):
        if not line:
            continue
        rows.append({"surface": "mcp", "n": n, "id": json.loads(line).get("id"),
                     "sha256": hashlib.sha256(line).hexdigest()})
    for name in ("stderr", "rc"):
        rows.append({"surface": f"mcp-{name}", "sha256": hashlib.sha256((side / f"{corpus}-mcp.{name}").read_bytes()).hexdigest()})
    for line in (side / f"{corpus}-serve.jsonl").read_text().splitlines():
        row = json.loads(line)
        out = {"surface": "serve", **{k: row[k] for k in ("n", "method", "path", "status", "content_type", "sha256")}}
        if row["path"] == "/inspect/index":
            body = json.loads((side / f"{corpus}-serve" / f"{row['n']:03d}.body").read_bytes())
            for misfit in body["report"]["families"]["misfits"]:
                misfit["missing"] = sorted(misfit["missing"])
            out["sha256_tie_normalised"] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
        rows.append(out)
    return rows


def main() -> None:
    cap, evidence, corpora = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3:]
    evidence.mkdir(parents=True, exist_ok=True)
    total_same = total_diff = 0
    for corpus in corpora:
        before, after = digests(cap / "before", corpus), digests(cap / "after", corpus)
        for side, rows in (("before", before), ("after", after)):
            (evidence / f"digests-{side}-{corpus}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
        same = sum(1 for a, b in zip(before, after) if a == b)
        diff = max(len(before), len(after)) - same
        seed_only = sum(1 for a, b in zip(before, after) if a != b and "sha256_tie_normalised" in a
                        and a["sha256_tie_normalised"] == b["sha256_tie_normalised"])
        total_same += same
        total_diff += diff
        mcp = sum(1 for r in before if r["surface"] == "mcp")
        serve = sum(1 for r in before if r["surface"] == "serve")
        print(f"{corpus}: {same} identical, {diff} different, of which {seed_only} only in the "
              f"hash-seed tie order ({mcp} mcp responses, {serve} serve routes, + stderr, rc)")
        for a, b in zip(before, after):
            if a != b:
                print("  DIFF", a, b)
    print(f"total: {total_same} identical, {total_diff} different")


if __name__ == "__main__":
    main()
