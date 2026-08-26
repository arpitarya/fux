"""Grade the playground goldens across the arms frozen in PRE-REGISTRATION.md."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

SRC = Path("/tmp/pg")
WORK = Path("/tmp/arms")
FUX = Path("/tmp/fuxwork")
sys.path.insert(0, str(FUX / "src"))

SUPERSEDES_LINE = "supersedes: [docs/adr-0007-helix-mesh.md]\n"
ADR19 = "docs/adr-0019-calder-gateway.md"

ARMS = [
    # name,                     declare, superseded_weight, rerank_weight
    ("A0_baseline",             False, 1.0,  0.0),
    ("A1_declared_control",     True,  1.0,  0.0),
    ("A2_declared_w0.5",        True,  0.5,  0.0),
    ("A3_declared_w0.25",       True,  0.25, 0.0),
    ("B0_rerank_off",           False, 1.0,  0.0),
    ("B1_rerank_on",            False, 1.0,  1.0),
]


def prepare(name, declare, sw, rw) -> Path:
    root = WORK / name
    if root.exists():
        shutil.rmtree(root)
    shutil.copytree(SRC, root)
    if declare:
        p = root / ADR19
        t = p.read_text(encoding="utf-8")
        assert t.startswith("---\n")
        end = t.index("\n---\n", 3) + 1
        p.write_text(t[:end] + SUPERSEDES_LINE + t[end:], encoding="utf-8")
    (root / ".fux" / "tune.toml").write_text(
        "[ranking]\n"
        f"superseded_weight = {sw}\n"
        f"rerank_weight = {rw}\n", encoding="utf-8")
    return root


def build(root: Path) -> None:
    for cmd in (["fux", "ingest", "--full"], ["fux", "build"]):
        r = subprocess.run(["uv", "run", "--project", str(FUX), *cmd],
                           cwd=root, capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stdout[-1500:], r.stderr[-1500:])
            raise SystemExit(f"{cmd} failed in {root}")


def grade(root: Path) -> dict[str, bool]:
    from fux.query import run_query
    from fux.tune import load as load_tune
    tune = load_tune(root)
    goldens = [json.loads(l) for l in (SRC / "goldens/queries.jsonl").read_text().splitlines() if l.strip()]
    out = {}
    for g in goldens:
        res, _ = run_query(root, g["q"], max(5, g["max_rank"]), tune=tune)
        locs = [r.loc for r in res]
        out[g["id"]] = g["doc"] in locs[: g["max_rank"]]
    return out


def main() -> int:
    WORK.mkdir(parents=True, exist_ok=True)
    results = {}
    for name, declare, sw, rw in ARMS:
        root = prepare(name, declare, sw, rw)
        build(root)
        results[name] = grade(root)
        n = sum(results[name].values())
        print(f"{name:<24} {n}/50")

    def diff(a, b):
        fixed = sorted(k for k in results[b] if results[b][k] and not results[a][k])
        broke = sorted(k for k in results[b] if not results[b][k] and results[a][k])
        return fixed, broke

    print("\n--- P-SUPERSEDE (against A1, the control) ---")
    for arm in ("A2_declared_w0.5", "A3_declared_w0.25"):
        f, b = diff("A1_declared_control", arm)
        print(f"{arm:<24} fixed={f} broke={b}")
    f, b = diff("A0_baseline", "A1_declared_control")
    print(f"{'A1 vs A0 (edit alone)':<24} fixed={f} broke={b}")

    print("\n--- P-RERANK-DEFAULT ---")
    f, b = diff("B0_rerank_off", "B1_rerank_on")
    print(f"{'B1 vs B0':<24} fixed={f} broke={b} net={len(f)-len(b):+d}")

    Path(__file__).with_name("results.json").write_text(json.dumps(results, indent=2))
    print("\nwrote results.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
