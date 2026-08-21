"""R4 — cold and warm latency for the refer plane, against a mock server.

**The threshold, the arms and the verdict rule live in
[`PRE-REGISTRATION.md`](PRE-REGISTRATION.md), not here.** This file is the
instrument; that file is the contract, and it was committed first. The
constants below are copied from it and are not to be edited to make a run pass.

## What is actually exercised

Everything except a real corporate network. A `http.server` on `127.0.0.1`
serves ten documents; the engine reaches them through **the consumer fetcher
`fux setup` generates** (`.fux/fetchers/http.py`), so the measured path is the
shipped one: socket, HTTP, the consumer's file, `urlsrc.sanitize`, the sha
comparison, chunking, re-scoring and assembly.

Nothing is injected past the fetcher. A bench that handed `refer()` a lambda
returning bytes would be measuring the parts of the plane that were never in
doubt.

## Cold and warm

The plane has two caches and they are not the same thing:

| | ARC | the TTL fetch cache |
|---|---|---|
| keyed by | `(loc, sha)` — content address | `loc` alone |
| served | only when the sha is already known correct | before the sha is confirmed |

**Cold** is a fresh `ARC` and an empty `.fux/runtime/fetch-cache/`, in a
process that has already imported the engine — interpreter start-up is
excluded, because the prediction is about a query on a running agent's path.
**Warm** is the immediately following identical call. Cold first, in the same
process, so warm is genuinely the second call.

## The arms

The server sleeps a fixed interval before responding, and that interval is the
arm: `local` 0 ms (the engine's own floor), **`internal` 100 ms — the judged
arm**, `slow` 500 ms (a rate-limited or distant source).

**The plane fetches serially.** `refer()` loops over candidates and there is no
concurrency in `src/fux/refer/`; paper §8's P4 says "(k=10, parallel)" and that
parallelism is not built. The pre-registration says so in advance, so a cold
number linear in `k x delay` is a known property rather than a surprise.

Usage:
    python tools/refer-bench/run.py --out work/regression/<date>-<run>
"""

from __future__ import annotations

import argparse
import http.server
import json
import os
import shutil
import socketserver
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from fux.ingest import urlsrc  # noqa: E402
from fux.refer import Policy, refer  # noqa: E402
from fux.refer.arc import ARC  # noqa: E402
from fux.refer.freshness import ALWAYS  # noqa: E402
from fux.store import read_index  # noqa: E402

#: The pre-registered bars. Do not edit these to make a run pass.
R4_COLD_BUDGET_S = 3.0
R4_WARM_BUDGET_S = 0.300

#: Pre-registration §4 and §6.
K = 10
PAIRS = 20
JUDGED_ARM = "internal"
ARMS = {"local": 0.0, "internal": 0.100, "slow": 0.500}

#: The cache must be big enough to hold all ten documents, or "warm" would be
#: measuring eviction rather than a warm path.
ARC_BYTES = 8 * 1024 * 1024

_LOCAL_FUX = ROOT / ".venv" / "bin" / "fux"
FUX = str(_LOCAL_FUX) if _LOCAL_FUX.exists() else (shutil.which("fux") or str(_LOCAL_FUX))

QUERY = "rollout policy for the storage compaction service during a region failover"


# ---------------------------------------------------------------- the corpus


def _document(i: int) -> str:
    """One wiki page, **as HTML**, roughly 5 KB with eight `<h2>` sections.

    HTML and not markdown, because the shipped fetcher is an *HTML-to-markdown*
    fetcher: `html_to_markdown` runs on whatever comes back. Serving markdown
    as `text/plain` puts it through the inline-text path, which collapses all
    whitespace — the document arrives as one 9 KB line, `chunk()` finds no
    heading boundaries, the single passage exceeds the byte budget, and the
    bench reports **zero citations in 1.9 ms**. That happened, which is why
    `citations_on_last_cold_call` is in the report: a latency bench with
    nothing to show for the latency is the easiest wrong number to file.

    Size matters too. Eight sections give `chunk()` real boundaries and
    `rescore()` more than one candidate passage to choose between; a 200-byte
    fixture would make the warm path look free for the wrong reason.
    """
    topics = ["rollout", "compaction", "failover", "quota", "replica", "token", "ingress", "ledger"]
    sections = []
    for n, topic in enumerate(topics):
        body = " ".join(
            f"{topic}-{i}-{n}-{w} service region cluster policy threshold latency"
            for w in range(18)
        )
        sections.append(f"<h2>{topic.title()} {n}</h2>\n<p>{body}</p>")
    intro = (
        f"The rollout policy for the storage compaction service during a region "
        f"failover, revision {i}."
    )
    return (
        f"<!doctype html><html><head><title>Runbook {i}</title></head><body>\n"
        f"<h1>Runbook {i}</h1>\n<p>{intro}</p>\n" + "\n".join(sections) + "\n</body></html>\n"
    )


class _Handler(http.server.BaseHTTPRequestHandler):
    delay = 0.0
    docs: dict[str, bytes] = {}

    def do_GET(self):  # noqa: N802 - stdlib naming
        body = self.docs.get(self.path)
        if body is None:
            self.send_error(404)
            return
        # The stand-in for a corporate service: SSO, proxy, and the source's own
        # work all collapse into one fixed interval, which the report names.
        if self.delay:
            time.sleep(self.delay)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):  # silence: the bench prints its own numbers
        return


class _Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def start_server(docs: dict[str, bytes]) -> tuple[_Server, int]:
    _Handler.docs = docs
    server = _Server(("127.0.0.1", 0), _Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, server.server_address[1]


# ---------------------------------------------------------------- the repo


def _run(cmd: list[str], cwd: Path) -> None:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(f"{' '.join(cmd)} failed:\n{result.stdout}\n{result.stderr}")


def build_repo(directory: Path, port: int) -> Path:
    """A repo whose corpus is ten URL documents on the mock server."""
    directory.mkdir(parents=True, exist_ok=True)
    _run(["git", "init", "-q"], directory)
    _run([FUX, "setup"], directory)

    urls = "\n".join(f"http://127.0.0.1:{port}/doc-{i}" for i in range(K))
    (directory / ".fux" / "sources" / "urls").write_text(
        "# R4 bench corpus — the mock server\n" + urls + "\n", encoding="utf-8"
    )
    # `meta = "plain"`: the bench needs to read what it cited, and these are
    # localhost fixtures with no ACL to mismatch. L5's default is untouched.
    (directory / "fux.toml").write_text(
        '[sources]\n\n[sources.url]\nmeta = "plain"\n', encoding="utf-8"
    )
    _run([FUX, "update"], directory)  # W-63: `--refresh-urls` retired into this
    return directory


def candidates_from(root: Path) -> list[tuple[str, str, str]]:
    index = read_index(root)
    rows = [
        (doc_id, record["loc"], record["sha"])
        for doc_id, record in sorted(index.items())
        if doc_id.startswith("url:")
    ]
    if len(rows) != K:
        raise SystemExit(f"expected {K} url documents in the index, found {len(rows)}")
    return rows


# ---------------------------------------------------------------- the measurement


def _p95(samples: list[float]) -> float:
    """The 95th percentile, nearest-rank. Stdlib only, and no interpolation.

    `statistics.quantiles` interpolates, which invents a value between two
    measurements. A latency budget is judged against something that was
    actually observed.
    """
    ordered = sorted(samples)
    index = max(0, min(len(ordered) - 1, int(round(0.95 * len(ordered) + 0.5)) - 1))
    return ordered[index]


def measure_arm(root: Path, candidates, fetcher, arm: str, delay: float, pairs: int) -> dict:
    _Handler.delay = delay
    policy = Policy(mode=ALWAYS, cache_ttl_seconds=300)
    cache_dir = root / ".fux" / "runtime" / "fetch-cache"

    cold, warm = [], []
    for _ in range(pairs):
        # Cold: both caches empty. A fresh ARC per pair, and the TTL directory
        # removed rather than expired — an expired entry is still a file read.
        shutil.rmtree(cache_dir, ignore_errors=True)
        arc = ARC(ARC_BYTES)

        start = time.perf_counter()
        bundle = refer(root, QUERY, candidates, policy=policy, cache=arc, fetcher=fetcher)
        cold.append(time.perf_counter() - start)

        start = time.perf_counter()
        refer(root, QUERY, candidates, policy=policy, cache=arc, fetcher=fetcher)
        warm.append(time.perf_counter() - start)

    labels = sorted({d.verdict.label for d in bundle.documents})
    return {
        "arm": arm,
        "delay_ms": round(delay * 1000),
        "judged": arm == JUDGED_ARM,
        "pairs": pairs,
        "k": K,
        "cold_median_s": round(statistics.median(cold), 4),
        "cold_p95_s": round(_p95(cold), 4),
        "warm_median_s": round(statistics.median(warm), 4),
        "warm_p95_s": round(_p95(warm), 4),
        "cold_passes": _p95(cold) <= R4_COLD_BUDGET_S,
        "warm_passes": _p95(warm) <= R4_WARM_BUDGET_S,
        # Recorded so a fast number cannot come from citations that silently
        # failed to fetch: `unverified` everywhere would be a broken bench.
        "verdict_labels_on_last_cold_call": labels,
        "citations_on_last_cold_call": len(bundle.assembled.citations),
    }


def _engine_sha() -> str:
    sha = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True
    ).stdout.strip()
    dirty = subprocess.run(
        ["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True
    ).stdout.strip()
    return sha + ("+dirty" if dirty else "")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="directory to write report.json into")
    parser.add_argument("--pairs", type=int, default=PAIRS)
    parser.add_argument("--arms", nargs="+", default=list(ARMS), choices=list(ARMS))
    args = parser.parse_args(argv)

    docs = {f"/doc-{i}": _document(i).encode("utf-8") for i in range(K)}
    server, port = start_server(docs)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            root = build_repo(Path(tmp) / "repo", port)
            candidates = candidates_from(root)
            # `load_fetcher` returns the imported *module*; the refer plane
            # takes the callable. Passing the module makes every fetch raise a
            # TypeError that the plane correctly degrades to `unverified` — a
            # broken bench that runs in 1.3 ms and reports a comfortable pass.
            # The `verdict_labels_on_last_cold_call` field exists because that
            # is exactly what happened the first time this was run.
            fetcher = urlsrc.load_fetcher(root, ".fux/fetchers/http.py").fetch

            rows = []
            for arm in args.arms:
                row = measure_arm(root, candidates, fetcher, arm, ARMS[arm], args.pairs)
                rows.append(row)
                print(
                    f"  R4 {arm:<8} ({row['delay_ms']:>3} ms): "
                    f"cold p95 {row['cold_p95_s']:.3f}s  warm p95 {row['warm_p95_s']:.4f}s"
                    f"{'   <- judged' if row['judged'] else ''}"
                )
    finally:
        server.shutdown()

    judged = next((r for r in rows if r["judged"]), None)
    report = {
        "engine_sha": _engine_sha(),
        "fux": FUX,
        "python": sys.version.split()[0],
        "platform": f"{os.uname().sysname} {os.uname().release} {os.uname().machine}",
        "pre_registration": "tools/refer-bench/PRE-REGISTRATION.md",
        "cold_budget_s": R4_COLD_BUDGET_S,
        "warm_budget_s": R4_WARM_BUDGET_S,
        "judged_arm": JUDGED_ARM,
        "arms": rows,
    }
    if judged is None:
        # The judged arm is pre-registered; ruling off another one would be the
        # threshold moving under a different name.
        report["r4_verdict"] = "NOT RULED — the judged arm was not run"
    else:
        report["r4_verdict"] = "PASS" if (judged["cold_passes"] and judged["warm_passes"]) else "FAIL"
    print(f"  R4 verdict: {report['r4_verdict']}")

    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {args.out / 'report.json'}")
    else:
        print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
