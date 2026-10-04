#!/usr/bin/env python3
"""The loopback halves of the network measurements. W-256 section 4.

Pre-registered in `work/regression/2026-10-04-loopback-network/PRE-REGISTRATION.md`
BEFORE this script produced a number. Measurement tooling (L12 exempt: lives
under `tools/`). **Everything happens on 127.0.0.1 in a temporary repository** -
no real host is contacted, the lab and the playground are not touched.

    loopback_network.py ratelimit  --out <evidence dir>     # B-102, loopback half
    loopback_network.py asingested --out <evidence dir>     # B-124, loopback half

Each scenario writes `observations.jsonl` (one row per pre-registered
observation: `id`, `arm`, `expected`, `observed`, `ok`) and `raw.json` (the
server's request log, the engine's outputs, the state files). It prints the
table and exits 0 only if every observation holds.

The engine is driven as a user would drive it: `fux setup`, `fux add --no-fetch`,
`fux ingest`, `fux answer --journal`, `fux doctor --json` - subprocesses of
this repository's own tree, so the fetcher is the shipped `http.py`.
"""

from __future__ import annotations

import argparse
import http.server
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from fux.constants import fixed  # noqa: E402

#: The engine's own values, READ - never restated here (L12, SR-RS 10b: the
#: pre-registration names these keys, not numbers a runner could adjust).
RETRIES = fixed("fetch", "rate_limit_retries")
BACKOFF = fixed("fetch", "rate_limit_backoff_s")
VETO_SHARE = fixed("doctor", "as_ingested_veto_share")

#: The scenario's own shape, FIXED by the pre-registration.
FLAKY_REFUSALS = 2          # < RETRIES: refused twice, the third request succeeds
FLAKY_PATHS = ("flaky-1", "flaky-2")
ALWAYS_PATH = "always"
OK_PATH = "ok"
#: the timing window for one backoff gap: [base * 2**i, base * 2**i + SLACK_S]
SLACK_S = 1.5

DOCS = 8                    # as-ingested scenario corpus
ANSWERS_UP = 16             # answers with the server up
ANSWERS_DOWN_1 = 4          # then down: 4 / 20 = 20 percent, under the quarter
ANSWERS_DOWN_2 = 4          # then 4 more: 8 / 24 = 33 percent, over it


# --- the server ---------------------------------------------------------------

class Server:
    """A loopback HTTP server with a request log and per-path behaviour."""

    def __init__(self, behaviour):
        self.log: list[dict] = []
        self.count: dict[str, int] = {}
        outer = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):  # noqa: N802
                path = self.path.lstrip("/")
                outer.count[path] = outer.count.get(path, 0) + 1
                status, body = behaviour(path, outer.count[path])
                outer.log.append({"t": time.monotonic(), "path": path,
                                  "n": outer.count[path], "status": status})
                self.send_response(status)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)

    def start(self):
        self.thread.start()
        return self

    def stop(self):
        self.httpd.shutdown()
        self.httpd.server_close()


def document(name: str) -> bytes:
    """Deterministic, distinct, above the thin-page word floor."""
    words = " ".join(f"{name}-term{i}" for i in range(200))
    return f"# Loopback {name}\n\nThe {name} runbook. {words}\n".encode()


# --- driving the engine ---------------------------------------------------------

ENV = {**os.environ, "PYTHONPATH": str(ROOT / "src")}


def fux(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    done = subprocess.run([sys.executable, "-m", "fux", *args], cwd=repo, env=ENV,
                          capture_output=True, text=True)
    if check and done.returncode != 0:
        sys.exit(f"fux {' '.join(args)} failed ({done.returncode}):\n{done.stdout}\n{done.stderr}")
    return done


def new_repo(tmp: Path) -> Path:
    repo = tmp / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    fux(repo, "setup")
    return repo


def add_url(repo: Path, url: str) -> None:
    fux(repo, "add", url, "--http", "--decoder", "prose", "--keep", "--ttl", "0", "--no-fetch")


def obs(rows: list[dict], oid: str, arm: str, expected, observed, ok: bool) -> None:
    rows.append({"id": oid, "arm": arm, "expected": expected, "observed": observed, "ok": bool(ok)})


def finish(out: Path, rows: list[dict], raw: dict) -> int:
    out.mkdir(parents=True, exist_ok=True)
    with (out / "observations.jsonl").open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True, default=str) + "\n")
    (out / "raw.json").write_text(json.dumps(raw, indent=1, sort_keys=True, default=str) + "\n",
                                  encoding="utf-8")
    for r in rows:
        print(f"{'OK ' if r['ok'] else 'NO '} {r['id']:6} expected {r['expected']!s:40} observed {r['observed']!s}")
    bad = [r["id"] for r in rows if not r["ok"]]
    print(f"\n{len(rows) - len(bad)} of {len(rows)} observations hold" + (f"; FAILED: {bad}" if bad else ""))
    return 1 if bad else 0


# --- B-102: a 429 on loopback ------------------------------------------------------

def ratelimit(out: Path) -> int:
    def behaviour(path: str, n: int):
        if path in FLAKY_PATHS:
            return (429, b"slow down") if n <= FLAKY_REFUSALS else (200, document(path))
        if path == ALWAYS_PATH:
            return 429, b"slow down"
        return 200, document(path)

    server = Server(behaviour).start()
    rows: list[dict] = []
    raw: dict = {"retries": RETRIES, "backoff_s": BACKOFF}
    try:
        with tempfile.TemporaryDirectory(prefix="fux-loopback-429-") as t:
            repo = new_repo(Path(t))
            for p in (*FLAKY_PATHS, ALWAYS_PATH, OK_PATH):
                add_url(repo, f"http://127.0.0.1:{server.port}/{p}")
            server.log.clear(); server.count.clear()  # the adds did not fetch; belt and braces
            ingest = fux(repo, "ingest")
            raw["ingest"] = {"returncode": ingest.returncode, "stdout": ingest.stdout,
                             "stderr": ingest.stderr}
            raw["requests"] = server.log
            host = f"127.0.0.1:{server.port}"
            state_path = repo / ".fux" / "runtime" / fixed("maintain", "url_state")
            state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.is_file() else {}
            raw["url_state"] = state
            doctor = json.loads(fux(repo, "doctor", "--json", check=False).stdout or "{}")
            raw["doctor_url_row"] = [c for c in doctor.get("checks", []) if c.get("name") == "url sources"]
            ids = []
            for shard in (repo / ".fux" / "index").glob("*.jsonl"):
                for line in shard.read_text(errors="ignore").splitlines():
                    try:
                        ids.append(json.loads(line).get("id") or "")
                    except ValueError:
                        pass
            raw["indexed_ids"] = sorted(i for i in ids if i)
    finally:
        server.stop()

    n = server.count
    # R1 - attempts per path
    for p in FLAKY_PATHS:
        obs(rows, f"R1-{p}", "retry", FLAKY_REFUSALS + 1, n.get(p, 0), n.get(p, 0) == FLAKY_REFUSALS + 1)
    obs(rows, "R1-always", "retry", RETRIES + 1, n.get(ALWAYS_PATH, 0), n.get(ALWAYS_PATH, 0) == RETRIES + 1)
    obs(rows, "R1-ok", "control", 1, n.get(OK_PATH, 0), n.get(OK_PATH, 0) == 1)
    # R2 - the run survives the refused URL, indexes the recovered ones
    obs(rows, "R2-exit", "isolation", 0, raw["ingest"]["returncode"], raw["ingest"]["returncode"] == 0)
    for p in (*FLAKY_PATHS, OK_PATH):
        obs(rows, f"R2-{p}", "indexed", True, f"/{p} in index", any(i.endswith(f"/{p}") for i in raw["indexed_ids"]))
    obs(rows, "R2-always", "not indexed", False, f"/{ALWAYS_PATH} in index", not any(i.endswith(f"/{ALWAYS_PATH}") for i in raw["indexed_ids"]))
    # R3 - the doubling backoff, from the server's own timestamps
    for p in (*FLAKY_PATHS, ALWAYS_PATH):
        ts = [r["t"] for r in server.log if r["path"] == p]
        gaps = [b - a for a, b in zip(ts, ts[1:])]
        want = [BACKOFF * (1 << i) for i in range(len(gaps))]
        ok = len(gaps) == (RETRIES if p == ALWAYS_PATH else FLAKY_REFUSALS) and all(
            w <= g <= w + SLACK_S for g, w in zip(gaps, want))
        obs(rows, f"R3-{p}", "backoff", f"gap_i in [{BACKOFF}*2^i, +{SLACK_S}]", [round(g, 2) for g in gaps], ok)
    # R4 - refusals counted by host, persisted
    total = FLAKY_REFUSALS * len(FLAKY_PATHS) + RETRIES + 1
    counted = (state.get("rate_limited") or {}).get(host)
    obs(rows, "R4-count", "url-state.json", {host: total}, state.get("rate_limited"), counted == total)
    # R5 - doctor names the host and the count
    detail = " ".join(str(c.get("detail", "")) for c in raw["doctor_url_row"])
    want = f"rate-limited by {host} x{total}"
    obs(rows, "R5-doctor", "fux doctor", want, detail[:200], want in detail)
    return finish(out, rows, raw)


# --- B-124: as-ingested on loopback -------------------------------------------------

def as_ingested(out: Path) -> int:
    def behaviour(path: str, n: int):
        return 200, document(path)

    names = [f"doc{i}" for i in range(DOCS)]
    server = Server(behaviour).start()
    rows: list[dict] = []
    raw: dict = {"veto_share": VETO_SHARE, "stages": []}
    up = True

    def journal_labels(repo: Path) -> list[dict]:
        path = repo / ".fux" / "runtime" / "provenance.jsonl"
        verdicts: list[dict] = []
        if path.is_file():
            for line in path.read_text(encoding="utf-8").splitlines():
                pred = (json.loads(line).get("predicate") or {})
                verdicts.extend(v for v in pred.get("verdicts") or [] if isinstance(v, dict))
        return verdicts

    try:
        with tempfile.TemporaryDirectory(prefix="fux-loopback-asingested-") as t:
            repo = new_repo(Path(t))
            for name in names:
                add_url(repo, f"http://127.0.0.1:{server.port}/{name}")
            fux(repo, "ingest")
            raw["acquired"] = sorted(p.name for p in (repo / ".fux" / "acquired").rglob("*") if p.is_file())

            def answer(i: int) -> dict:
                name = names[i % DOCS]
                done = fux(repo, "answer", "--journal", "--json", f"{name}-term7 runbook", check=False)
                try:
                    return json.loads(done.stdout)
                except json.JSONDecodeError:
                    return {"_raw": done.stdout, "_err": done.stderr}

            def stage(label: str, count: int, start: int) -> None:
                before = len(journal_labels(repo))
                results = [answer(start + i) for i in range(count)]
                verdicts = journal_labels(repo)
                new = verdicts[before:]
                counts: dict[str, int] = {}
                for v in verdicts:
                    counts[v.get("freshness")] = counts.get(v.get("freshness"), 0) + 1
                doctor = json.loads(fux(repo, "doctor", "--json", check=False).stdout or "{}")
                row = [c for c in doctor.get("checks", []) if c.get("name") == "freshness verdicts"]
                raw["stages"].append({"label": label, "answers": count, "new_verdicts": new,
                                      "cumulative": counts, "doctor_freshness": doctor.get("freshness"),
                                      "doctor_row": row, "results": results})

            stage("up", ANSWERS_UP, 0)
            server.stop(); up = False
            time.sleep(0.2)
            stage("down-1", ANSWERS_DOWN_1, ANSWERS_UP)
            stage("down-2", ANSWERS_DOWN_2, ANSWERS_UP + ANSWERS_DOWN_1)
    finally:
        if up:
            server.stop()

    s_up, s_d1, s_d2 = raw["stages"]
    # A1 - retention: every document's bytes are held after the one networked ingest
    obs(rows, "A1-kept", "keep=true", f">= {DOCS} retained files", len(raw["acquired"]), len(raw["acquired"]) >= DOCS)
    # A2 - server up: every citation is a live comparison, none as-ingested
    up_labels = {v.get("freshness") for v in s_up["new_verdicts"]}
    obs(rows, "A2-up", "no as-ingested while reachable", "{current} only", sorted(map(str, up_labels)),
        bool(up_labels) and up_labels == {"current"})
    # A3 - server down: every new citation is as-ingested, and the retained bytes MATCH the index
    for s in (s_d1, s_d2):
        new = s["new_verdicts"]
        labels = {v.get("freshness") for v in new}
        obs(rows, f"A3-{s['label']}-label", "as-ingested", {"as-ingested"}, sorted(map(str, labels)),
            bool(new) and labels == {"as-ingested"})
        match = all(v.get("fetched_sha") and v.get("fetched_sha") == v.get("indexed_sha") for v in new)
        obs(rows, f"A3-{s['label']}-match", "fetched_sha == indexed_sha (match=True)", True, match, bool(new) and match)
    # A4 - doctor's counts equal an independent count of the journal, to the verdict
    for s in (s_up, s_d1, s_d2):
        obs(rows, f"A4-{s['label']}-counts", "doctor == journal", s["cumulative"], s["doctor_freshness"],
            s["doctor_freshness"] == s["cumulative"])
    # A5 - the quarter veto fires exactly where the share crosses it, and not before
    for s in (s_up, s_d1, s_d2):
        total = sum(s["cumulative"].values())
        share = s["cumulative"].get("as-ingested", 0) / total if total else 0.0
        should_warn = share > VETO_SHARE
        detail = " ".join(str(c.get("detail", "")) for c in s["doctor_row"])
        warned = "reopen condition" in detail
        obs(rows, f"A5-{s['label']}-veto", f"warn iff share {share:.3f} > {VETO_SHARE}", should_warn, warned,
            warned == should_warn)
    fired = [s["label"] for s in (s_up, s_d1, s_d2)
             if any("reopen condition" in str(c.get("detail", "")) for c in s["doctor_row"])]
    obs(rows, "A5-fires", "the veto fires at least once, in a down stage", "subset of down-1/down-2, non-empty",
        fired, bool(fired) and "up" not in fired)
    return finish(out, rows, raw)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("scenario", choices=("ratelimit", "asingested"))
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    return ratelimit(args.out) if args.scenario == "ratelimit" else as_ingested(args.out)


if __name__ == "__main__":
    raise SystemExit(main())
