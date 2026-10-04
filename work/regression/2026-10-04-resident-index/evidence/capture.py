"""W-249 surface capture: every MCP tool and every serve route, before and after.

usage: capture.py <src-dir-for-PYTHONPATH> <corpus-name> <root> <out-dir>

One `fux mcp` stdio session (a real subprocess) and one `fux serve` process
per corpus. Writes `<out>/<corpus>-mcp.stdout`, `<out>/<corpus>-serve.jsonl`
(one row per route: method, path, status, content-type, sha256 of the body)
and the raw bodies under `<out>/<corpus>-serve/`.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

PY = sys.executable

QUERIES = {
    "repo": ["how does the accelerator detect staleness", "mcp tool descriptions", "retry payments",
             "golden answer key lock", "zzqx flurbnog", "serve page computes nothing", "decoder for pdf"],
    "repo-norun": ["how does the accelerator detect staleness", "mcp tool descriptions", "zzqx flurbnog",
                   "serve page computes nothing"],
    "lab": ["ammonia leak response", "seal control decision", "payroll run", "finance close checklist",
            "TMS-44 mapping study", "zzqx flurbnog"],
}
SEEDS = {
    "repo": ["records/0136_mcp.md", "records/0158_serve.md", "src/fux/mcp.py"],
    "repo-norun": ["records/0136_mcp.md", "src/fux/mcp.py"],
    "lab": ["seed/44-decision-ammonia-leak-response.md", "ext/adjacent/00001-finance-close.md"],
}
WORDS = {"repo": ["stamp", "accelerator"], "repo-norun": ["stamp"], "lab": ["ammonia", "payroll"]}


def clean(root: Path, name: str) -> None:
    runtime = root / ".fux" / "runtime"
    if name.endswith("norun"):
        shutil.rmtree(runtime, ignore_errors=True)
        return
    (runtime / "last-cited.json").unlink(missing_ok=True)
    shutil.rmtree(runtime / "inspect", ignore_errors=True)


def mcp_session(name: str) -> list[dict]:
    msgs: list = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
    ]
    i = 3
    for _round in range(2):  # every call twice: the second is the one residency serves
        for q in QUERIES[name]:
            msgs.append({"jsonrpc": "2.0", "id": i, "method": "tools/call",
                         "params": {"name": "fux_search", "arguments": {"query": q}}}); i += 1
        msgs.append({"jsonrpc": "2.0", "id": i, "method": "tools/call",
                     "params": {"name": "fux_search", "arguments": {"query": QUERIES[name][0], "k": 2}}}); i += 1
        msgs.append({"jsonrpc": "2.0", "id": i, "method": "tools/call",
                     "params": {"name": "fux_search", "arguments": {"query": QUERIES[name][1], "expand": "server protocol"}}}); i += 1
        for seed in SEEDS[name] + ["no/such/doc.md"]:
            msgs.append({"jsonrpc": "2.0", "id": i, "method": "tools/call",
                         "params": {"name": "fux_related", "arguments": {"path": seed}}}); i += 1
            msgs.append({"jsonrpc": "2.0", "id": i, "method": "tools/call",
                         "params": {"name": "fux_passage", "arguments": {"path": seed, "line_start": 2, "line_end": 6}}}); i += 1
        msgs.append({"jsonrpc": "2.0", "id": i, "method": "tools/call",
                     "params": {"name": "fux_passage", "arguments": {"path": "../../etc/passwd"}}}); i += 1
    msgs.append({"jsonrpc": "2.0", "id": i, "method": "tools/call", "params": {"name": "fux_answer", "arguments": {}}}); i += 1
    msgs.append({"jsonrpc": "2.0", "id": i, "method": "resources/list"}); i += 1
    return msgs


def run_mcp(src: str, name: str, root: Path, out: Path) -> None:
    lines = "\n".join(json.dumps(m) for m in mcp_session(name)) + "\nthis is not json\n"
    env = dict(os.environ, PYTHONPATH=src)
    proc = subprocess.run([PY, "-m", "fux", "mcp"], cwd=root, input=lines, capture_output=True,
                          text=True, env=env, timeout=1800)
    (out / f"{name}-mcp.stdout").write_text(proc.stdout)
    (out / f"{name}-mcp.stderr").write_text(proc.stderr)
    (out / f"{name}-mcp.rc").write_text(str(proc.returncode))


def routes(name: str) -> list[tuple[str, str]]:
    from urllib.parse import quote

    out = [("GET", "/"), ("GET", "/health")]
    for q in QUERIES[name]:
        out.append(("GET", f"/ask?q={quote(q)}"))
    out.append(("GET", f"/ask?q={quote(QUERIES[name][0])}&top=3"))
    out.append(("GET", "/ask?q="))
    out.append(("GET", "/ask?q=x&top=zero"))
    for q in QUERIES[name][:3]:
        out.append(("GET", f"/answer?q={quote(q)}&no_refer=1"))
    out.append(("GET", f"/answer?q={quote(QUERIES[name][0])}"))
    for seed in SEEDS[name]:
        out.append(("GET", f"/graph?seed={quote(seed)}"))
    out.append(("GET", "/graph?seed=no/such/doc.md"))
    out.append(("GET", "/inspect/documents"))
    out.append(("GET", f"/inspect/document?loc={quote(SEEDS[name][0])}"))
    out.append(("GET", f"/inspect/document/probes?loc={quote(SEEDS[name][0])}"))
    out.append(("GET", "/inspect/words?limit=50"))
    out.append(("GET", "/inspect/words?sort=idf&order=asc&limit=20&offset=5"))
    out.append(("GET", f"/inspect/analyze?q={quote(QUERIES[name][0])}"))
    for w in WORDS[name]:
        out.append(("GET", f"/inspect/word?term={quote(w)}"))
    out.append(("GET", "/inspect/identifiers?p=TMS-%7Bn%7D"))
    out.append(("JOB", "/inspect/index"))
    out.append(("GET", "/inspect/diff"))
    out.append(("POST", "/ask?q=x"))
    out.append(("GET", "/nope"))
    # the same /ask and /graph again: what residency serves from memory
    for q in QUERIES[name]:
        out.append(("GET", f"/ask?q={quote(q)}"))
    for seed in SEEDS[name]:
        out.append(("GET", f"/graph?seed={quote(seed)}"))
    return out


def fetch(base: str, method: str, path: str) -> tuple[int, str, bytes]:
    req = urllib.request.Request(base + path, method=method, data=b"" if method == "POST" else None)
    try:
        with urllib.request.urlopen(req, timeout=1800) as resp:
            return resp.status, resp.headers.get("Content-Type", ""), resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers.get("Content-Type", ""), exc.read()


def run_serve(src: str, name: str, root: Path, out: Path) -> None:
    env = dict(os.environ, PYTHONPATH=src)
    proc = subprocess.Popen([PY, "-m", "fux", "serve", "--port", "0"], cwd=root, env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    try:
        first = proc.stdout.readline()
        port = re.search(r":(\d+)/", first).group(1)
        base = f"http://127.0.0.1:{port}"
        bodies = out / f"{name}-serve"
        bodies.mkdir(exist_ok=True)
        rows = []
        for n, (method, path) in enumerate(routes(name)):
            if method == "JOB":
                while True:
                    status, ctype, body = fetch(base, "GET", path)
                    if json.loads(body).get("state") != "running":
                        break
                    time.sleep(0.2)
                method = "GET"
            else:
                status, ctype, body = fetch(base, method, path)
            (bodies / f"{n:03d}.body").write_bytes(body)
            rows.append({"n": n, "method": method, "path": path, "status": status, "content_type": ctype,
                         "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body)})
        (out / f"{name}-serve.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    finally:
        proc.terminate()
        proc.wait(timeout=30)


def main() -> None:
    src, name, root, out = sys.argv[1], sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4])
    out.mkdir(parents=True, exist_ok=True)
    clean(root, name)
    run_mcp(src, name, root, out)
    clean(root, name)
    run_serve(src, name, root, out)
    clean(root, name)


if __name__ == "__main__":
    main()
