#!/usr/bin/env python3
"""W-242 Tier 1's arm — decision 3 of PRE-REGISTRATION.md, on three corpora.

For every query, three generators must agree:

- **candidates** — Node scan, Node plane and Python plane, at `skipping=False`
  so the plane's set is the whole set: the same document ids, the same `n`, the
  same `total_wlen` (exact), the same `df`;
- **ranking** — Node plane at `skipping=True` against Node scan: the same ids,
  in the same order, at the same `round(9)` score, at tops 1, 5 and 20;
- **stdout** — `node fux.mjs <verb> Q --json --fast` against the same without
  `--fast`, byte for byte, for `find`, `ask` and `answer`.

Usage: `t1_arm.py <label> <corpus-root> <queries: records|vocab|file:PATH>`.
`records` reads `records/*.md` titles (this repo: no source walk, W-244);
`vocab` uses `queryset.generate` on a corpus outside this repo. One JSON line
per corpus goes to stdout; a discordance prints the first ten and exits 1.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ENGINE / "src"))
sys.path.insert(0, str(ENGINE / "tools" / "differential"))

from fux import tune as tune_mod  # noqa: E402
from fux.derive import accel  # noqa: E402
from fux.query import identifiers as ids_mod  # noqa: E402
from fux.query.scan import query_term_hashes, scan_candidates  # noqa: E402

TOPS = (1, 5, 20)
NODE_ENTRY = ENGINE / "node" / "fux.mjs"


def record_titles() -> list[str]:
    out = []
    for path in sorted((ENGINE / "records").glob("[0-9][0-9][0-9][0-9]_*.md")):
        m = re.search(r'^title: "?(.*?)"?$', path.read_text(encoding="utf-8"), re.M)
        if m:
            out.append(re.sub(r"^SR-[A-Z0-9-]+ \(\d+\) — ", "", m.group(1)).replace("`", ""))
    return out + ["rollback", "incident", "zzqq", "graph tier boosted", "anchor text field"]


def queries_for(spec: str, root: Path) -> list[str]:
    if spec == "records":
        return record_titles()
    if spec == "vocab":
        import queryset

        return queryset.generate(root, common=25, median=25, rare=25, pairs=25, triples=10)
    return Path(spec.removeprefix("file:")).read_text(encoding="utf-8").splitlines()


def python_candidates(root: Path, queries: list[str]) -> list[dict]:
    scoring = tune_mod.load(root, enabled=True).scoring
    ids = ids_mod.for_root(root)
    out = []
    for q in queries:
        hashes = query_term_hashes(q, ids)
        if not hashes:
            out.append(None)
            continue
        cands, df, corpus = accel.accel_candidates(accel.Runtime(root), hashes, 20, skipping=False, scoring=scoring)
        out.append({"ids": sorted(c["id"] for c in cands), "df": df, "n": corpus.n, "total_wlen": corpus.total_wlen})
    return out


NODE_SCRIPT = r"""
import { readFileSync } from "node:fs";
import { Runtime, accelCandidates, ask as accelAsk } from "%(accel)s";
import { scanCandidates, ask as scanAsk, queryTermHashes } from "%(scan)s";
import { loadTune } from "%(tune)s";
import { identifiersFor } from "%(ids)s";
const root = process.argv[1];
const queries = JSON.parse(readFileSync(0, "utf8"));
const scoring = loadTune(root, { enabled: true }).scoring;
const ids = identifiersFor(root);
const rows = [];
for (const q of queries) {
  const hashes = queryTermHashes(q, ids);
  if (!hashes.length) { rows.push(null); continue; }
  const [sc, sdf, scorpus] = scanCandidates(root, hashes, { scoring });
  const [ac, adf, acorpus] = accelCandidates(new Runtime(root), hashes, 20, { skipping: false, scoring });
  const ranked = {};
  for (const top of %(tops)s) {
    const s = scanAsk(root, q, top, { scoring }).map((r) => [r.id, r.score]);
    const a = accelAsk(root, q, top, { skipping: true, scoring }).map((r) => [r.id, r.score]);
    ranked[top] = { scan: s, accel: a };
  }
  rows.push({
    scan: { ids: sc.map((c) => c.id).sort(), df: sdf, n: scorpus.n, total_wlen: scorpus.totalWlen },
    accel: { ids: ac.map((c) => c.id).sort(), df: adf, n: acorpus.n, total_wlen: acorpus.totalWlen },
    ranked,
  });
}
process.stdout.write(JSON.stringify(rows));
"""


def node_rows(root: Path, queries: list[str]) -> list:
    script = NODE_SCRIPT % {
        "accel": (ENGINE / "node/src/derive/accel.mjs").as_uri(),
        "scan": (ENGINE / "node/src/query/scan.mjs").as_uri(),
        "tune": (ENGINE / "node/src/config/tune.mjs").as_uri(),
        "ids": (ENGINE / "node/src/query/identifiers.mjs").as_uri(),
        "tops": json.dumps(list(TOPS)),
    }
    proc = subprocess.run(
        ["node", "--input-type=module", "-e", script, str(root)],
        input=json.dumps(queries), capture_output=True, text=True, encoding="utf-8",
    )
    if proc.returncode != 0:
        raise SystemExit(proc.stderr)
    return json.loads(proc.stdout)


def cli_pairs(root: Path, queries: list[str], cap: int) -> list[str]:
    bad = []
    for q in queries[:cap]:
        for argv in (["find", q, "--json", "--top", "5"], ["ask", q, "--json", "--top", "20", "--band"], ["answer", q, "--json"]):
            outs = [
                subprocess.run(["node", str(NODE_ENTRY), *argv, *extra], cwd=root, capture_output=True)
                for extra in ([], ["--fast"])
            ]
            if outs[0].returncode != outs[1].returncode or outs[0].stdout != outs[1].stdout:
                bad.append(f"stdout {argv[0]} {q!r}")
    return bad


def main() -> int:
    label, root_arg, spec = sys.argv[1:4]
    cli_cap = int(sys.argv[4]) if len(sys.argv) > 4 else 40
    root = Path(root_arg).resolve()
    queries = queries_for(spec, root)
    py = python_candidates(root, queries)
    nd = node_rows(root, queries)
    bad: list[str] = []
    for q, p, n in zip(queries, py, nd, strict=True):
        if p is None or n is None:
            if not (p is None and n is None):
                bad.append(f"empty-query mismatch {q!r}")
            continue
        for side in ("scan", "accel"):
            # JS sorts by UTF-16 unit, Python by code point: re-sort here.
            if {**n[side], "ids": sorted(n[side]["ids"])} != p:
                bad.append(f"candidates node-{side} != python-accel {q!r}")
        for top, pair in n["ranked"].items():
            s = [(i, round(x, 9)) for i, x in pair["scan"]]
            a = [(i, round(x, 9)) for i, x in pair["accel"]]
            if s != a:
                bad.append(f"ranked top={top} {q!r}")
    bad += cli_pairs(root, queries, cli_cap)
    row = {
        "label": label, "corpus": str(root), "queries": len(queries),
        "candidate_checks": sum(1 for p in py if p is not None) * 2,
        "ranked_checks": sum(1 for p in py if p is not None) * len(TOPS),
        "stdout_checks": min(cli_cap, len(queries)) * 3,
        "discordant": len(bad),
    }
    print(json.dumps(row))
    for line in bad[:10]:
        print("  " + line, file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
