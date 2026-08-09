#!/usr/bin/env python3
"""Acquire the RFC corpus into the lab — once, politely, pinned by manifest.

    archive/v0.26/.venv/bin/python tools/pruning-eval/fetch_rfc.py \
        --out ~/my_programs/fux-lab/rfc

**This is a lab activity, not an engine activity.** Fux's offline law constrains
the engine; the eval harness may reach the network exactly here, to acquire a
corpus once. Nothing in this file becomes engine code, and no later run touches
the network: every run reads the local copy, verified against
`manifest.json` (`{id: sha256}`), which is what makes the experiment
re-obtainable rather than merely repeatable.

Politeness is deliberate — `rfc-editor.org` is a public, volunteer-run archive:
one connection, a delay between requests, honest User-Agent, resumable so a
retry does not re-fetch what is already on disk.

Determinism: RFC numbers are processed in sorted order; the manifest is written
with sorted keys; nothing depends on wall-clock or on filesystem iteration
order.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

INDEX_URL = "https://www.rfc-editor.org/rfc-index.txt"
RFC_URL = "https://www.rfc-editor.org/rfc/rfc{n}.txt"
UA = "fux-pruning-eval/0.30 (research corpus acquisition; contact: arpitarya.me@gmail.com)"

# "1129 Internet Time Synchronization: ..." — an entry starts with the number.
_ENTRY = re.compile(r"^(\d{4})\s+(.+)$")


def _get(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 — lab-only
        return resp.read()


def issued_rfcs(index_text: str) -> list[int]:
    """RFC numbers that were actually issued and are available as plain text.

    Entries are multi-line; an entry begins with a 4-digit number at column 0.
    "Not Issued" placeholders and entries without a TXT format are skipped —
    the latter because the corpus must be plain prose, not PDF-only scans.
    """
    out: list[int] = []
    current: int | None = None
    body: list[str] = []

    def flush() -> None:
        if current is None:
            return
        text = " ".join(body)
        if "Not Issued" in text:
            return
        fmt = re.search(r"\(Format:\s*([^)]*)\)", text)
        if fmt and "TXT" not in fmt.group(1).upper() and "ASCII" not in fmt.group(1).upper():
            return
        out.append(current)

    for line in index_text.splitlines():
        m = _ENTRY.match(line)
        if m:
            flush()
            current, body = int(m.group(1)), [m.group(2)]
        elif current is not None and line.strip():
            body.append(line.strip())
        elif current is not None:
            flush()
            current, body = None, []
    flush()
    return sorted(set(out))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, required=True, help="lab corpus directory")
    ap.add_argument("--limit", type=int, default=0, help="0 = every issued RFC")
    ap.add_argument("--delay", type=float, default=0.12, help="seconds between requests")
    ap.add_argument("--retries", type=int, default=3)
    ap.add_argument("--workers", type=int, default=5,
                    help="bounded concurrency — keep this small; it is a public archive")
    args = ap.parse_args()

    out = args.out.expanduser()
    docs = out / "corpus" / "docs"
    docs.mkdir(parents=True, exist_ok=True)

    index_path = out / "rfc-index.txt"
    if not index_path.is_file():
        print("fetching rfc-index.txt …", flush=True)
        index_path.write_bytes(_get(INDEX_URL, timeout=60))
    numbers = issued_rfcs(index_path.read_text(encoding="utf-8", errors="replace"))
    if args.limit:
        numbers = numbers[: args.limit]
    print(f"{len(numbers)} issued text RFCs to acquire", flush=True)

    manifest_path = out / "manifest.json"
    manifest: dict[str, str] = {}
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text())

    todo = [n for n in numbers
            if not ((docs / f"rfc{n}.txt").is_file() and f"rfc{n}" in manifest)]
    skipped = len(numbers) - len(todo)
    print(f"{skipped} already on disk · {len(todo)} to fetch "
          f"· {args.workers} workers", flush=True)

    def fetch_one(n: int) -> tuple[int, bytes | None]:
        for attempt in range(args.retries):
            try:
                return n, _get(RFC_URL.format(n=n))
            except urllib.error.HTTPError as exc:
                if exc.code == 404:  # withdrawn / never published as text
                    return n, None
                time.sleep(1.0 + attempt * 2)
            except Exception:  # noqa: BLE001 — transient network, retry
                time.sleep(1.0 + attempt * 2)
            time.sleep(args.delay)
        return n, None

    fetched = failed = 0
    missing: list[int] = []
    # Bounded concurrency: a public, volunteer-run archive gets a handful of
    # connections, not a swarm. Results are collected as they land but the
    # manifest is written sorted, so output stays deterministic.
    with cf.ThreadPoolExecutor(max_workers=args.workers) as pool:
        for n, data in pool.map(fetch_one, todo):
            if data is None:
                failed += 1
                missing.append(n)
                continue
            (docs / f"rfc{n}.txt").write_bytes(data)
            manifest[f"rfc{n}"] = hashlib.sha256(data).hexdigest()
            fetched += 1
            if fetched % 500 == 0:
                manifest_path.write_text(
                    json.dumps(manifest, indent=1, sort_keys=True) + "\n")
                print(f"  fetched {fetched}/{len(todo)} · unavailable {failed}",
                      flush=True)

    manifest_path.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    (out / "missing.json").write_text(json.dumps(sorted(missing), indent=1) + "\n")
    print(f"done — {len(manifest)} documents pinned in {manifest_path}")
    print(f"fetched {fetched} · already present {skipped} · unavailable {failed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
