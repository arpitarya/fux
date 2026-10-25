"""W-300's L13 run: the merged query (`scope = all`) against the repository alone.

    PYTHONPATH=src .venv/bin/python work/regression/2026-10-25-w300-merged-query/evidence/run.py \
        <pre-W-300 src dir> <out dir>

The pre-W-300 engine is `git archive 9688d479 src | tar -x -C <dir>`. Everything
is built in a temporary directory: the fixture package is ingested, packed and
pinned exactly as `tests/test_pkg_merged_query.py` does it; the consumer is
`evidence/corpus/docs/`. Writes `rows.jsonl` (one row per question per arm),
`gates.json` and `summary.json` into <out dir>.
"""

from __future__ import annotations

import csv
import importlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parents[3]
sys.path.insert(0, str(ENGINE / "tests"))
sys.path.insert(0, str(ENGINE / "tools" / "quality-controls"))

from fux import plugins  # noqa: E402
from fux.constants import fixed  # noqa: E402
from fux.ingest.run import run as ingest  # noqa: E402
from fux.query import run_query  # noqa: E402
from test_pkg_merged_query import IMPORT, NAME, VERSION, _fixture_files, _pack, _repo  # noqa: E402
from verdict import line, rule  # noqa: E402

QUESTIONS = HERE / "questions.tsv"
CORPUS = HERE / "corpus" / "docs"
RUN_MJS = ENGINE / "node" / "src" / "query" / "run.mjs"
TOP = 10


def _consumer(base: Path, segment: Path | None) -> Path:
    files = {p.name: p.read_text(encoding="utf-8") for p in sorted(CORPUS.iterdir())}
    root = _repo(base / "consumer", files)
    if segment is not None:
        site = base / "site"
        shutil.copytree(segment, site / IMPORT)
        info = site / f"{IMPORT}-{VERSION}.dist-info"
        info.mkdir(parents=True)
        (info / "METADATA").write_text(f"Metadata-Version: 2.1\nName: {NAME}\nVersion: {VERSION}\n", encoding="utf-8")
        npm = root / "node_modules" / NAME
        shutil.copytree(segment, npm)
        (npm / "package.json").write_text(json.dumps({"name": NAME, "version": VERSION}), encoding="utf-8")
        sys.path.insert(0, str(site))
        importlib.invalidate_caches()
    plugins.reset()
    ingest(root, refresh_urls=False, full=False)
    if segment is not None:
        target = plugins.path(root)
        target.write_text(
            target.read_text(encoding="utf-8") + "\n[[package]]\n"
            + f'name = "{NAME}"\nkind = "index"\nversion = "{VERSION}"\n'
            + f'digest = "{plugins.segment_digest(segment)}"\nnpm = "{NAME}"\npypi = "{NAME}"\n',
            encoding="utf-8",
        )
        plugins.reset()
    return root


def _key(hit) -> str:
    return f"{hit.package or 'repo'}:{hit.id}"


def _arm(root: Path, question: str, scope: str) -> dict:
    confidence: dict = {}
    results, path = run_query(
        root, question, TOP, force_scan=True, use_tune=True, scope=scope, confidence_out=confidence,
    )
    block = confidence.get("confidence")
    return {
        "ranked": [[_key(r), round(r.score, fixed("ranking", "score_digits"))] for r in results],
        "band": block.band if block is not None else None,
        "path": path,
    }


def _node(root: Path, question: str, scope: str) -> list:
    script = (
        f"import {{ runQuery }} from {json.dumps(RUN_MJS.as_uri())};"
        f"const r = runQuery(process.cwd(), {json.dumps(question)}, {TOP}, "
        f"{{ useTune: true, wantConfidence: false, compose: true, scope: {json.dumps(scope)} }});"
        "console.log(JSON.stringify(r.results.map((h) => [`${h.package ?? 'repo'}:${h.id}`, h.score])));"
    )
    out = subprocess.run(["node", "--input-type=module", "-e", script], cwd=root, capture_output=True, text=True, check=True)
    digits = fixed("ranking", "score_digits")
    return [[k, round(s, digits)] for k, s in json.loads(out.stdout)]


def _payloads(src: Path, root: Path, scope: str | None) -> list[str]:
    cmd = [sys.executable, str(HERE / "payloads.py"), str(root), str(QUESTIONS)] + ([scope] if scope else [])
    out = subprocess.run(cmd, capture_output=True, text=True, check=True, env={"PYTHONPATH": str(src), "PATH": "/usr/bin:/bin"})
    return out.stdout.splitlines()


def main() -> int:
    old_src, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    new_src = ENGINE / "src"
    with QUESTIONS.open(encoding="utf-8") as f:
        questions = list(csv.DictReader(f, delimiter="\t"))
    repo, everything, packages = fixed("scope", "repo"), fixed("scope", "all"), fixed("scope", "packages")

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        author = _repo(tmp / "author" / "repo", _fixture_files())
        segment = _pack(author, tmp / "segment" / "seg")
        pinned = _consumer(tmp / "a", segment)
        plain = _consumer(tmp / "b", None)

        # -- G: the gates ---------------------------------------------------------
        gates = {}
        old_plain, new_plain = _payloads(old_src, plain, None), _payloads(new_src, plain, None)
        gates["G0a_no_pin_byte_identical"] = {"questions": len(old_plain), "differ": sum(a != b for a, b in zip(old_plain, new_plain, strict=True))}
        old_pinned, new_repo = _payloads(old_src, pinned, None), _payloads(new_src, pinned, repo)
        gates["G0b_scope_repo_byte_identical"] = {"questions": len(old_pinned), "differ": sum(a != b for a, b in zip(old_pinned, new_repo, strict=True))}
        old_self, new_self = _payloads(old_src, ENGINE, None), _payloads(new_src, ENGINE, None)
        gates["G0c_this_repository_byte_identical"] = {"questions": len(old_self), "differ": sum(a != b for a, b in zip(old_self, new_self, strict=True))}

        # -- the arms, one row per question per arm ---------------------------------
        rows = []
        node_differs = 0
        for q in questions:
            arms = {
                "baseline_repo": _arm(pinned, q["question"], repo),
                "decided_all": _arm(pinned, q["question"], everything),
                "reported_packages": _arm(pinned, q["question"], packages),
            }
            node = _node(pinned, q["question"], everything)
            node_differs += node != arms["decided_all"]["ranked"]
            for arm, got in arms.items():
                ranked = [k for k, _ in got["ranked"]]
                rows.append({
                    "id": q["id"], "slice": q["slice"], "expected": q["expected"], "arm": arm,
                    "rank": ranked.index(q["expected"]) + 1 if q["expected"] in ranked else None,
                    "hit@1": ranked[:1] == [q["expected"]], "hit@5": q["expected"] in ranked[:5],
                    "band": got["band"], "path": got["path"], "top5": got["ranked"][:5],
                })
            rows.append({"id": q["id"], "slice": q["slice"], "expected": q["expected"], "arm": "reported_node_all",
                         "equals_python_decided": node == arms["decided_all"]["ranked"], "top5": node[:5]})
        gates["G_node_equals_python"] = {"questions": len(questions), "differ": node_differs}

    with (out / "rows.jsonl").open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    (out / "gates.json").write_text(json.dumps(gates, indent=2) + "\n", encoding="utf-8")

    # -- the reading, by the table frozen in PRE-REGISTRATION.md -------------------------
    by = {(r["id"], r["arm"]): r for r in rows}
    ids = [q["id"] for q in questions]
    slice_ids = [q["id"] for q in questions if q["slice"] == "package"]
    other_ids = [q["id"] for q in questions if q["slice"] != "package"]

    def flips(subset, metric="hit@1"):
        wins = sum(1 for i in subset if by[(i, "decided_all")][metric] and not by[(i, "baseline_repo")][metric])
        losses = sum(1 for i in subset if by[(i, "baseline_repo")][metric] and not by[(i, "decided_all")][metric])
        return wins, losses

    winnable = sum(1 for i in slice_ids if not by[(i, "baseline_repo")]["hit@1"])
    c1_w, c1_l = flips(slice_ids)
    c1 = rule(c1_w, c1_l)
    c2_w, c2_l = flips(other_ids)
    margin = max(2, (3 * len(other_ids)) // 100)
    all_w, all_l = flips(ids)
    hit5 = {arm: sum(by[(i, arm)]["hit@5"] for i in ids) for arm in ("baseline_repo", "decided_all")}
    grounded = {arm: sum(by[(i, arm)]["band"] == "grounded" for i in ids) for arm in ("baseline_repo", "decided_all")}
    hit1 = {arm: sum(by[(i, arm)]["hit@1"] for i in ids) for arm in ("baseline_repo", "decided_all", "reported_packages")}
    gates_ok = all(g["differ"] == 0 for g in gates.values())
    summary = {
        "gates_ok": gates_ok,
        "slice_winnable": winnable,
        "slice_floor_ok": winnable >= 15,
        "C1": {"wins": c1_w, "losses": c1_l, "verdict_line": line(c1), "holds": c1["outcome"] == "b"},
        "C2": {"wins": c2_w, "losses": c2_l, "margin": margin, "holds": c2_l - c2_w <= margin},
        "C3": {"wins": all_w, "losses": all_l, "holds": all_w - all_l > 0},
        "GR_hit5": {**hit5, "holds": hit5["baseline_repo"] - hit5["decided_all"] <= 1},
        "GR_grounded": {**grounded, "holds": grounded["baseline_repo"] - grounded["decided_all"] <= 2},
        "hit@1": hit1,
    }
    if not gates_ok or not summary["slice_floor_ok"]:
        reading = "STOP"
    elif all(summary[k]["holds"] for k in ("C1", "C2", "C3", "GR_hit5", "GR_grounded")):
        reading = "PASS"
    elif summary["C3"]["holds"] is False or (c2_l - c2_w) > margin + 2:
        reading = "FAIL: drift"
    elif c1_w - c1_l <= 0:
        reading = "FAIL: no gain"
    else:
        reading = "INCONCLUSIVE"
    summary["table_reading"] = reading
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
