"""W-247 byte-equality capture: ask / lexical / find / answer in every output mode.

Runs a fixed invocation list through `python -m fux` inside a ROOT directory and
records stdout, stderr and the exit code per invocation, byte for byte. Run it
before the renderer split and after, on the same snapshot ROOT, then `--diff`.

    capture.py run  --set repo|lab --root DIR --out DIR
    capture.py diff BEFORE_DIR AFTER_DIR

ROOT is a COPY (see the run's README): `fux answer` writes
`.fux/runtime/last-cited.json`, which changes the NEXT stderr (`nothing has
changed since you last asked this`), so each invocation starts with that file
absent -- except one whose argv begins with `!keep`, which inherits the state
the previous invocation left, so the "changed / unchanged since last asked"
report is exercised too. Nothing outside ROOT and OUT is written.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

#: Query sets. `repo` is this repository's own index, `lab` a fux-lab rung.
QUERIES = {
    "repo": {
        "single": [
            "how does the refer plane verify freshness",
            "SR-API frozen library surface",
            "what is the confidence band",
            "PII redaction rules false positive",
            "v0.26 archived substrate engine sqlite",
            "zzqxv flurble nonexistent gibberish",
        ],
        "fused": [("how do we release to PyPI", ["publishing to npm", "release process"])],
        "expand": [("rank documents", "bm25 postings impact")],
        "find_flags": [
            ["--under", "records"],
            ["--under", "docs/paper"],
            ["--phrase", "refer plane"],
            ["--all"],
        ],
        "find_query": "freshness verdict",
    },
    "lab": {
        "single": [
            "temperature excursion procedure",
            "sensor thresholds",
            "telematics vendor decision",
            "night shift handover",
            "zzqxv flurble nonexistent gibberish",
        ],
        "fused": [("vaccine temperature excursion", ["cold chain breach", "postmortem nagpur"])],
        "expand": [("sensor alarm", "threshold celsius")],
        "find_flags": [["--under", "seed"], ["--phrase", "temperature"], ["--all"]],
        "find_query": "temperature excursion",
    },
}


def invocations(name: str) -> list[list[str]]:
    q = QUERIES[name]
    out: list[list[str]] = []
    for text in q["single"]:
        for verb in ("ask", "lexical"):
            out += [
                [verb, text],
                [verb, text, "--json"],
                [verb, text, "--band"],
                [verb, text, "--band", "--json"],
                [verb, text, "--why"],
                [verb, text, "--why", "--json"],
                [verb, text, "--explain", "--top", "3"],
                [verb, text, "--no-sections"],
                [verb, text, "--no-sections", "--json"],
            ]
        out += [
            ["ask", text, "--no-related"],
            ["ask", text, "--no-related", "--json"],
            ["ask", text, "--no-tune", "--json", "--band"],
            ["ask", text, "--fast", "--json"],
            ["find", text],
            ["find", text, "--json"],
            ["find", text, "--band"],
            ["find", text, "--band", "--json"],
            ["find", text, "--no-tune"],
            ["answer", text],
            ["answer", text, "--json"],
            ["answer", text, "--band"],
            ["answer", text, "--band", "--json"],
            ["answer", text, "--no-refer"],
            ["answer", text, "--no-refer", "--json"],
            ["answer", text, "--no-refer", "--band", "--json"],
            ["answer", text, "--audit"],
            ["answer", text, "--audit", "--json"],
            ["answer", text, "--receipt"],
            ["answer", text, "--receipt", "--json"],
            ["answer", text, "--audit", "--receipt", "--band", "--json"],
            ["answer", text, "--no-refer", "--receipt", "--json"],
            ["answer", text, "--no-refer", "--receipt"],
            ["answer", text, "--cache-ttl", "15m", "--json"],
        ]
    for text, more in q["fused"]:
        qs = [a for m in more for a in ("-q", m)]
        for verb in ("ask", "lexical"):
            out += [[verb, text, *qs], [verb, text, *qs, "--json"],
                    [verb, text, *qs, "--band", "--json"], [verb, text, *qs, "--why"]]
        out += [["find", text, *qs], ["find", text, *qs, "--json"],
                ["find", text, *qs, "--band", "--json"]]
    for text, expansion in q["expand"]:
        out += [["ask", text, "--expand", expansion], ["ask", text, "--expand", expansion, "--json", "--band"],
                ["find", text, "--expand", expansion, "--json"],
                ["answer", text, "--expand", expansion, "--json", "--band"],
                ["answer", text, "--expand", expansion, "--no-refer", "--receipt", "--json"]]
    ftext = q["find_query"]
    for flags in q["find_flags"]:
        out += [["find", ftext, *flags], ["find", ftext, *flags, "--json"],
                ["find", ftext, *flags, "--band"]]
    # the "since you last asked" report needs the previous invocation's state
    for text in q["single"][:2]:
        out += [["answer", text, "--json"], ["!keep", "answer", text, "--json"],
                ["!keep", "answer", text, "--no-refer"], ["!keep", "answer", text]]
    # usage errors and a missing-root style refusal are part of the surface too
    out += [["ask"], ["find", "x", "--top", "notanumber"], ["answer", "x", "--cache-ttl", "1x"]]
    return out


def run(args) -> int:
    root, out = Path(args.root), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    remembered = root / ".fux" / "runtime" / "last-cited.json"
    rows = []
    for i, argv in enumerate(invocations(args.set)):
        if argv[0] == "!keep":
            argv = argv[1:]
        else:
            remembered.unlink(missing_ok=True)
        proc = subprocess.run(
            [args.python, "-m", "fux", *argv], cwd=root, capture_output=True, timeout=300,
        )
        stem = f"{i:04d}"
        (out / f"{stem}.out").write_bytes(proc.stdout)
        (out / f"{stem}.err").write_bytes(proc.stderr)
        rows.append({
            "n": i, "argv": argv, "rc": proc.returncode,
            "out_sha256": hashlib.sha256(proc.stdout).hexdigest(), "out_bytes": len(proc.stdout),
            "err_sha256": hashlib.sha256(proc.stderr).hexdigest(), "err_bytes": len(proc.stderr),
        })
    (out / "index.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    print(f"{len(rows)} invocations -> {out}")
    return 0


def diff(args) -> int:
    def load(p):
        return [json.loads(l) for l in (Path(p) / "index.jsonl").read_text().splitlines()]

    before, after = load(args.before), load(args.after)
    same = differ = 0
    for b, a in zip(before, after):
        if b["argv"] != a["argv"]:
            print("ARGV MISMATCH", b["n"]); differ += 1; continue
        ok = (b["rc"], b["out_sha256"], b["err_sha256"]) == (a["rc"], a["out_sha256"], a["err_sha256"])
        if ok:
            same += 1
        else:
            differ += 1
            print("DIFFERS", b["n"], " ".join(b["argv"]),
                  f"rc {b['rc']}->{a['rc']} out {b['out_bytes']}->{a['out_bytes']} err {b['err_bytes']}->{a['err_bytes']}")
    if len(before) != len(after):
        print("LENGTH MISMATCH", len(before), len(after)); differ += abs(len(before) - len(after))
    nonempty = sum(1 for b in before if b["out_bytes"])
    print(f"identical {same}  different {differ}  (of {len(before)}; {nonempty} with non-empty stdout)")
    return 1 if differ else 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--set", choices=sorted(QUERIES), required=True)
    r.add_argument("--root", required=True)
    r.add_argument("--out", required=True)
    r.add_argument("--python", default=sys.executable)
    r.set_defaults(fn=run)
    d = sub.add_parser("diff")
    d.add_argument("before")
    d.add_argument("after")
    d.set_defaults(fn=diff)
    a = p.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
