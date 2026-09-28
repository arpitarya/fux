#!/usr/bin/env python3
"""G1 — every frozen query, analyzed by BOTH readers under the after arm's rules.

The rules are the `.fux/identifiers.toml` each after-arm copy was given by
`fux identifiers --write` (filed as `identifiers-<rung>.toml`). One divergence
stops the run (PRE-REGISTRATION §4).
"""
import json
import subprocess
import sys
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "src"))
from fux.query.analyzer import analyze  # noqa: E402
from fux.query.identifiers import parse  # noqa: E402

EV = Path(__file__).resolve().parent
NODE = (
    'import {parse} from "./node/src/query/identifiers.mjs";'
    'import {analyze} from "./node/src/query/analyzer.mjs";'
    'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{const {data,texts}=JSON.parse(s);'
    'const r=parse(data,"g1");process.stdout.write(JSON.stringify(texts.map(t=>analyze(t,r))));});'
)
bad = 0
for rung in ("rung-00100", "rung-01000", "rung-10000"):
    data = tomllib.loads((EV / f"identifiers-{rung}.toml").read_text(encoding="utf-8"))
    rules = parse(data, origin=rung)
    texts = [json.loads(l)["query"] for l in (EV / f"variants-{rung}.jsonl").read_text("utf-8").splitlines()]
    out = subprocess.run(["node", "--input-type=module", "-e", NODE], cwd=REPO, check=True,
                         input=json.dumps({"data": data, "texts": texts}), capture_output=True, text=True)
    js = json.loads(out.stdout)
    diffs = [(t, analyze(t, rules), j) for t, j in zip(texts, js) if analyze(t, rules) != j]
    bad += len(diffs)
    print(f"{rung}: {len(rules.rules)} families, {len(texts)} queries, {len(diffs)} divergent")
    for d in diffs[:5]:
        print("  ", d)
print("G1 PASS" if bad == 0 else f"G1 FAIL: {bad} divergent")
sys.exit(1 if bad else 0)
