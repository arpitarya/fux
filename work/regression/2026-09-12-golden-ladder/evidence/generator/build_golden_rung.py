#!/usr/bin/env python3
"""Build one rung of the sealed golden ladder — W-136 phase 2.

A rung is a **self-contained git repository** holding the twenty seed documents
plus the first `count - 20` documents of the ext stream, with its own committed
`.fux/` index. Phase 4 then only has to ask.

    python3 build_golden_rung.py --rung rung-00100 --count 100

What it does, in order:

1. Copy `work/golden/seed/` into `<rung>/seed/` — paths byte-identical to the
   names the answer key uses, so a prediction needs no translation.
2. Generate `<rung>/ext/` with `make_golden_ext.py`, which refuses to write if
   a generated document mentions a seed entity.
3. `fux setup`, then **declare**: `seed`, `seed/archive archived=true`, `ext`,
   `ext/archive archived=true`. Archived-ness is declared here, never derived
   from a path, which is what makes `archived_weight` measurable at all.
4. Commit every document at **its own date** — seed documents from
   `seed-dates.tsv`, ext documents from the generator's stream — because fux
   derives `mtime` from git commit time and the recency prior is a no-op
   without it. Commits are grouped by date and ordered, so the history is
   chronological and reproducible.
5. `fux ingest --full`, then check that the skip list names no `seed/` file.
6. Write the three ladder records into the fux repo:
   `rung-NNNNN.sha256` (documents, category, origin), `rung-NNNNN.index`
   (engine version + index root hash) and `rung-NNNNN.coverage` (counts of
   superseded / archived / mtime-carrying records, checked against the
   declarations — the rung is not frozen if they disagree).

**This script never reads `work/golden/questions/` or the answer key.**
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
FUX_REPO = Path("/Users/arpitarya/my_programs/fux")
LAB = Path("/Users/arpitarya/my_programs/fux-lab")
GOLDEN = FUX_REPO / "work" / "golden"
LADDER = GOLDEN / "ladder"
FUX = FUX_REPO / ".venv" / "bin" / "fux"

SOURCES = """# The golden ladder's corpus. Declared, never derived (ADR-DIR-LIST).
#
# `archived=true` is what makes `archived_weight` measurable: a rung that only
# *puts* files in an archive directory without declaring it measures nothing.
seed
seed/archive        archived=true
"""

EXT_SOURCES = """ext
ext/archive         archived=true
"""


def run(cmd, cwd, env=None, check=True, capture=True):
    e = dict(os.environ)
    if env:
        e.update(env)
    p = subprocess.run(cmd, cwd=str(cwd), env=e, check=False,
                       text=True, capture_output=capture)
    if check and p.returncode != 0:
        sys.stderr.write(f"$ {' '.join(cmd)}\n{p.stdout}\n{p.stderr}\n")
        raise SystemExit(f"command failed in {cwd}: {' '.join(cmd)}")
    return p


def seed_dates() -> dict[str, str]:
    out = {}
    for line in (GOLDEN / "seed-dates.tsv").read_text().splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        path, date = line.split("\t")
        out[path.strip()] = date.strip()
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rung", required=True)
    ap.add_argument("--count", type=int, required=True,
                    help="total documents in the rung, seeds included")
    a = ap.parse_args()

    rung = LAB / "corpora" / "golden" / a.rung
    if rung.exists():
        shutil.rmtree(rung)
    rung.mkdir(parents=True)

    # 1. seeds ------------------------------------------------------------
    shutil.copytree(GOLDEN / "seed", rung / "seed")
    dates = seed_dates()
    seed_docs = sorted(
        str(p.relative_to(rung)) for p in (rung / "seed").rglob("*") if p.is_file())
    missing = [d for d in seed_docs if d not in dates]
    if missing:
        raise SystemExit(f"seed-dates.tsv does not cover: {missing}")

    # 2. ext --------------------------------------------------------------
    ext_n = a.count - len(seed_docs)
    ext_meta: dict[str, tuple[str, str, str]] = {}
    if ext_n > 0:
        run([sys.executable, str(HERE / "make_golden_ext.py"),
             "--out", str(rung), "--count", str(ext_n)], cwd=HERE)
        meta = rung / ".ext-manifest.tsv"
        for line in meta.read_text().splitlines():
            path, cat, origin, date, _sha = line.split("\t")
            ext_meta[path] = (cat, origin, date)
        meta.unlink()  # not a document

    all_docs = {d: ("seed", "authored", dates[d]) for d in seed_docs}
    all_docs.update(ext_meta)
    if len(all_docs) != a.count:
        raise SystemExit(f"expected {a.count} documents, have {len(all_docs)}")

    # 3. git + .fux -------------------------------------------------------
    run(["git", "init", "-q", "-b", "main"], cwd=rung)
    run(["git", "config", "user.name", "fux-lab"], cwd=rung)
    run(["git", "config", "user.email", "lab@fux.example"], cwd=rung)

    # 4. commit every document at its own date ----------------------------
    by_date: dict[str, list[str]] = defaultdict(list)
    for path, (_c, _o, date) in all_docs.items():
        by_date[date].append(path)
    for date in sorted(by_date):
        paths = sorted(by_date[date])
        stamp = f"{date}T12:00:00+00:00"
        run(["git", "add", "--"] + paths, cwd=rung)
        run(["git", "commit", "-q", "-m", f"corpus: {date} ({len(paths)} documents)"],
            cwd=rung, env={"GIT_AUTHOR_DATE": stamp, "GIT_COMMITTER_DATE": stamp})

    # 5. fux config, committed after the documents so it carries no date --
    run([str(FUX), "setup", "--no-agents"], cwd=rung)
    # rung-seed has no ext/ at all, and a source line pointing at a directory
    # that does not exist is a hard ingest error — so the ext lines are written
    # only when there is an ext to declare.
    (rung / ".fux" / "sources" / "dirs").write_text(
        SOURCES + (EXT_SOURCES if ext_n > 0 else ""), encoding="utf-8")
    (rung / ".fux" / "pii.toml").touch()
    fmts = (rung / ".fux" / "formats.toml").read_text()
    for ext in (".md", ".txt"):
        assert f'"*{ext}"' in fmts, f"formats.toml does not include {ext}"
    for ext in ("html", "eml", "yaml"):
        assert f"{ext} =" in fmts, f"formats.toml does not bind .{ext}"
    run(["git", "add", "-A", "--", ".fux"], cwd=rung)
    run(["git", "commit", "-q", "-m", "fux: index configuration"], cwd=rung,
        env={"GIT_AUTHOR_DATE": "2026-09-12T12:00:00+00:00",
             "GIT_COMMITTER_DATE": "2026-09-12T12:00:00+00:00"})

    # 6. ingest -----------------------------------------------------------
    skipped = run([str(FUX), "ingest", "--list-skipped"], cwd=rung, check=False)
    bad = [ln for ln in skipped.stdout.splitlines() if "seed/" in ln]
    if bad:
        raise SystemExit("a seed document is on the skip list:\n" + "\n".join(bad))
    run([str(FUX), "ingest", "--full", "--no-progress"], cwd=rung)
    run(["git", "add", "-A", "--", ".fux"], cwd=rung)
    run(["git", "commit", "-q", "-m", f"fux: index {a.rung}"], cwd=rung,
        env={"GIT_AUTHOR_DATE": "2026-09-12T12:05:00+00:00",
             "GIT_COMMITTER_DATE": "2026-09-12T12:05:00+00:00"})

    # 7. the three ladder records ----------------------------------------
    LADDER.mkdir(parents=True, exist_ok=True)
    lines = []
    for path in sorted(all_docs):
        cat, origin, _d = all_docs[path]
        sha = hashlib.sha256((rung / path).read_bytes()).hexdigest()
        lines.append(f"{sha}  {path}  {cat}  {origin}")
    (LADDER / f"{a.rung}.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")

    ver = run([str(FUX), "--version"], cwd=rung).stdout.strip()
    root = run(["git", "rev-parse", "HEAD"], cwd=rung).stdout.strip()
    idx_files = sorted((rung / ".fux" / "index").rglob("*"))
    idx_sha = hashlib.sha256()
    for f in idx_files:
        if f.is_file():
            idx_sha.update(str(f.relative_to(rung)).encode())
            idx_sha.update(f.read_bytes())
    (LADDER / f"{a.rung}.index").write_text(
        f"engine: {ver}\n"
        f"rung: {a.rung}\n"
        f"documents: {a.count}\n"
        f"index_root_sha256: {idx_sha.hexdigest()}\n"
        f"rung_head_commit: {root}\n", encoding="utf-8")

    # coverage — read the records the index actually holds
    cov = coverage(rung)
    declared_archived = sum(
        1 for p in all_docs if p.startswith(("seed/archive/", "ext/archive/")))
    # `superseded` is a flag on the RETIRED document (ingest/priors.py), so the
    # declaration is the set of `supersedes:` TARGETS, not the documents that
    # carry the key. Counting the carriers is the easy way to write a coverage
    # file that agrees with nothing.
    targets: set[str] = set()
    for p in all_docs:
        text = (rung / p).read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"^supersedes:\s*(\S+)\s*$", text, re.M):
            targets.add(m.group(1))
    unknown = sorted(t for t in targets if t not in all_docs)
    if unknown:
        raise SystemExit(f"supersedes: targets not in the rung: {unknown}")
    declared_superseded = len(targets)
    (LADDER / f"{a.rung}.coverage").write_text(
        f"rung: {a.rung}\n"
        f"documents_indexed: {cov['total']}\n"
        f"archived_declared: {declared_archived}\n"
        f"archived_in_index: {cov['archived']}\n"
        f"superseded_declared: {declared_superseded}\n"
        f"superseded_in_index: {cov['superseded']}\n"
        f"carrying_mtime: {cov['mtime']}\n"
        f"categories: {json.dumps(dict(Counter(c for c, _, _ in all_docs.values())), sort_keys=True)}\n",
        encoding="utf-8")

    problems = []
    if cov["total"] != a.count:
        problems.append(f"index holds {cov['total']} documents, rung declares {a.count}")
    if cov["archived"] != declared_archived:
        problems.append(f"archived: {cov['archived']} indexed vs {declared_archived} declared")
    if cov["superseded"] != declared_superseded:
        problems.append(f"superseded: {cov['superseded']} indexed vs {declared_superseded} declared")
    if cov["mtime"] != cov["total"]:
        problems.append(f"mtime: {cov['mtime']} of {cov['total']} — recency prior is partly dead")
    if problems:
        print(f"NOT FROZEN — {a.rung}:", file=sys.stderr)
        for p in problems:
            print("  " + p, file=sys.stderr)
        return 1

    print(f"{a.rung}: {a.count} documents · archived {declared_archived} · "
          f"superseded {declared_superseded} · mtime {cov['mtime']}/{cov['total']} · frozen")
    return 0


def coverage(rung: Path) -> dict:
    """Counts straight out of the committed index's doc-meta plane."""
    sys.path.insert(0, str(FUX_REPO / "src"))
    from fux.store import reader  # noqa: E402

    records = reader.read_index(rung)
    total = len(records)
    archived = sum(1 for r in records.values() if r.get("archived"))
    superseded = sum(1 for r in records.values() if r.get("superseded"))
    mtime = sum(1 for r in records.values() if r.get("mtime"))
    return {"total": total, "archived": archived,
            "superseded": superseded, "mtime": mtime}


if __name__ == "__main__":
    raise SystemExit(main())
