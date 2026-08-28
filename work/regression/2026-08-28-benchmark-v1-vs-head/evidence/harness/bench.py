#!/usr/bin/env python3
"""The two-engine benchmark harness. Stdlib only, drives the shipped CLI.

**It never picks a threshold.** Every bar lives in the frozen pre-registration
(`fux/work/benchmark/PRE-REGISTRATION-V1-VS-HEAD.md`); this file produces rows
and, in `mcnemar`, a p-value. It does not know what "pass" means.

**Per-query rows are the product.** One row per query per arm, written as the
run goes, under `runs/<run>/rows/`. Every aggregate anybody computes later —
the discordant count, `b`, `c`, the exact test — is derivable from these rows
and from nothing else, which is the obligation four filed runs could not meet.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import statistics
import subprocess
import sys
import time
from math import comb
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


# --------------------------------------------------------------------------
# arms
# --------------------------------------------------------------------------

def fux_bin(arm: str) -> Path:
    return ROOT / "arms" / arm / "venv" / "bin" / "fux"


def arm_version(arm: str) -> str:
    return subprocess.run(
        [str(fux_bin(arm)), "--version"], capture_output=True, text=True, check=True
    ).stdout.strip()


def workdir(run: str, arm: str, tier: str) -> Path:
    return ROOT / "runs" / run / "work" / f"{arm}-{tier}"


def prepare(run: str, arm: str, tier: str, corpus: str | None = None) -> dict:
    """Copy the corpus bytes, then `fux setup` + `fux ingest` into a fresh `.fux/`.

    Each arm gets its **own copy** of the same bytes: the committed record shape
    differs between `fux.index.v1` and `v2`, so there is no shared index and
    there cannot be one. The copy is what makes "identical corpus bytes" a
    checkable claim rather than an assumption — the sha is recorded here.
    """
    src = ROOT / "corpora" / (corpus or tier) / "repo"
    dst = workdir(run, arm, tier)
    if dst.exists():
        shutil.rmtree(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst)
    # `fux setup` anchors on the nearest git root, not on `cwd` — a corpus
    # nested inside another repository gets its `.fux/` written at that
    # repository's root instead. Both arms do it, so it is not a version
    # difference; it IS a harness bug if the work directory is not its own
    # repo. Found by running it: the first attempt wrote `.fux/` into
    # `fux-benchmark/` itself.
    subprocess.run(["git", "init", "-q"], cwd=dst, check=True)
    binp = str(fux_bin(arm))
    subprocess.run([binp, "setup"], cwd=dst, capture_output=True, text=True, check=True)
    (dst / ".fux" / "sources" / "dirs").write_text("docs\n", encoding="utf-8")
    t0 = time.perf_counter()
    proc = subprocess.run([binp, "ingest"], cwd=dst, capture_output=True, text=True, check=True)
    ingest_ms = (time.perf_counter() - t0) * 1000
    return {
        "arm": arm,
        "tier": tier,
        "corpus": corpus or tier,
        "version": arm_version(arm),
        "ingest_ms": round(ingest_ms, 1),
        "ingest_stdout": proc.stdout.strip().splitlines(),
        "index_bytes": dir_bytes(dst / ".fux" / "index"),
        "shards": len(list((dst / ".fux" / "index").glob("*.jsonl"))),
    }


def dir_bytes(p: Path) -> int:
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())


# --------------------------------------------------------------------------
# the CLI, driven
# --------------------------------------------------------------------------

def _json_stdout(argv: list[str], cwd: Path) -> tuple[dict, float]:
    """Parse stdout ONLY.

    `fux answer` writes a repeat-query `note:` to **stderr**; a harness that
    merged the streams would fail to parse it intermittently, which is the
    worst kind of harness bug because it looks like a flaky engine.
    """
    t0 = time.perf_counter()
    proc = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, check=True)
    ms = (time.perf_counter() - t0) * 1000
    return json.loads(proc.stdout), ms


def ask(arm: str, cwd: Path, q: str, top: int, extra: list[str] | None = None):
    argv = [str(fux_bin(arm)), "ask", q, "--json", "--top", str(top), *(extra or [])]
    payload, ms = _json_stdout(argv, cwd)
    return [r["loc"] for r in payload["results"]], ms


def answer(arm: str, cwd: Path, q: str, band: bool):
    argv = [str(fux_bin(arm)), "answer", q, "--json"]
    if band:
        argv.append("--band")
    payload, ms = _json_stdout(argv, cwd)
    return payload, ms


def load(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


# --------------------------------------------------------------------------
# quality — the row emitters
# --------------------------------------------------------------------------

TOP = 10


def quality(run: str, arm: str, tier: str, corpus: str | None, label: str | None,
            work: str | None = None) -> Path:
    evald = ROOT / "corpora" / (corpus or tier) / "eval"
    cwd = workdir(run, arm, work or tier)
    name = label or arm
    outdir = ROOT / "runs" / run / "rows"
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / f"{name}-{tier}.jsonl"
    band = name.startswith("B")

    # Warm-up, discarded. 20 queries the row file never sees.
    for row in load(evald / "pairs.jsonl")[:20]:
        ask(arm, cwd, row["q"], TOP)

    rows: list[dict] = []

    for i, row in enumerate(load(evald / "pairs.jsonl")):
        locs, ms = ask(arm, cwd, row["q"], TOP)
        rank = locs.index(row["doc"]) + 1 if row["doc"] in locs else 0
        rows.append({
            "suite": "pairs", "qid": f"pairs-{i:04d}", "q": row["q"], "expect": row["doc"],
            "rank": rank, "hit@5": int(0 < rank <= 5), "hit@10": int(rank > 0),
            "rr": round(1.0 / rank, 6) if rank else 0.0, "top": locs[:5], "ms": round(ms, 2),
        })

    for i, row in enumerate(load(evald / "chains.jsonl")):
        locs, ms = ask(arm, cwd, row["q"], TOP)
        r_cur = locs.index(row["current"]) + 1 if row["current"] in locs else 0
        r_sup = locs.index(row["superseded"]) + 1 if row["superseded"] in locs else 0
        both = bool(r_cur and r_sup)
        # An inversion needs both halves visible. With only one in the top-k
        # there is no ordering to invert, and scoring it either way would be
        # inventing a comparison the run did not make.
        inversion = int(both and r_sup < r_cur)
        rows.append({
            "suite": "chains", "qid": f"chain-{i:04d}", "q": row["q"],
            "current": row["current"], "superseded": row["superseded"],
            "rank_current": r_cur, "rank_superseded": r_sup, "both_visible": int(both),
            "inversion": inversion, "current_first": int(both and r_cur < r_sup),
            "ms": round(ms, 2),
        })

    for i, row in enumerate(load(evald / "unanswerable.jsonl")):
        payload, ms = answer(arm, cwd, row["q"], band)
        passages = (payload.get("answer") or {}).get("passages") or []
        conf = payload.get("confidence") or {}
        rows.append({
            "suite": "unanswerable", "qid": f"unans-{i:04d}", "q": row["q"], "kind": row["kind"],
            "passages": len(passages),
            # The only observable BOTH arms have. Arm A emits no band at all,
            # so a band-based definition of "decline" could not be paired.
            "declined": int(not passages),
            "band": conf.get("band"), "answerable": conf.get("answerable"),
            "coverage": conf.get("coverage"), "doc_coverage": conf.get("doc_coverage"),
            "missing": conf.get("missing"), "ms": round(ms, 2),
        })

    stamp = {"run": run, "arm": name, "engine": arm, "tier": tier, "corpus": corpus or tier,
             "version": arm_version(arm)}
    out.write_text(
        "".join(json.dumps({**stamp, **r}, sort_keys=True) + "\n" for r in rows), encoding="utf-8"
    )
    return out


# --------------------------------------------------------------------------
# the exact test — reads rows, prints a p-value, rules on nothing
# --------------------------------------------------------------------------

def mcnemar_exact(b: int, c: int) -> float:
    """Exact two-sided binomial on the discordant pairs. `b+c == 0` -> `p = 1.0`."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(comb(n, i) for i in range(0, k + 1))
    return min(1.0, 2.0 * tail / (2 ** n))


def paired(rows_a: list[dict], rows_b: list[dict], key: str) -> dict:
    a = {r["qid"]: r for r in rows_a}
    bb = {r["qid"]: r for r in rows_b}
    shared = sorted(set(a) & set(bb))
    b = c = both = neither = 0
    flips: list[dict] = []
    for qid in shared:
        va, vb = a[qid].get(key), bb[qid].get(key)
        if va is None or vb is None:
            continue
        if vb and not va:
            b += 1
            flips.append({"qid": qid, "q": a[qid]["q"], "direction": "fixed-by-B"})
        elif va and not vb:
            c += 1
            flips.append({"qid": qid, "q": a[qid]["q"], "direction": "broken-by-B"})
        elif va and vb:
            both += 1
        else:
            neither += 1
    return {"metric": key, "n": len(shared), "b_fixed_by_B": b, "c_broken_by_B": c,
            "discordant": b + c, "net": b - c, "both": both, "neither": neither,
            "p_exact_two_sided": round(mcnemar_exact(b, c), 6), "flips": flips}


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("prepare")
    p.add_argument("--run", required=True)
    p.add_argument("--arm", required=True)
    p.add_argument("--tier", required=True)
    p.add_argument("--corpus")

    q = sub.add_parser("quality")
    q.add_argument("--run", required=True)
    q.add_argument("--arm", required=True)
    q.add_argument("--tier", required=True)
    q.add_argument("--corpus")
    q.add_argument("--label")
    q.add_argument("--work", help="work-directory suffix, when it differs from --tier")

    m = sub.add_parser("mcnemar")
    m.add_argument("--a", required=True, type=Path)
    m.add_argument("--b", required=True, type=Path)
    m.add_argument("--suite", required=True)
    m.add_argument("--key", required=True)

    args = ap.parse_args()

    if args.cmd == "prepare":
        print(json.dumps(prepare(args.run, args.arm, args.tier, args.corpus), sort_keys=True))
        return 0
    if args.cmd == "quality":
        out = quality(args.run, args.arm, args.tier, args.corpus, args.label, args.work)
        print(f"rows -> {out.relative_to(ROOT)} ({len(load(out))} rows)")
        return 0
    if args.cmd == "mcnemar":
        ra = [r for r in load(args.a) if r["suite"] == args.suite]
        rb = [r for r in load(args.b) if r["suite"] == args.suite]
        print(json.dumps(paired(ra, rb, args.key), indent=1, sort_keys=True))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
