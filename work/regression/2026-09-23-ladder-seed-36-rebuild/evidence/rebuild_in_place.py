#!/usr/bin/env python3
"""Rebuild every golden rung IN PLACE on the 2026-09-23 seed — prompt 4, W-215.

**Why this exists.** Prompt 10 committed fourteen seed documents on 2026-09-23
(`23-…` through `36-…`), and `rungs.seed_drift()` reported all eight rungs
STALE: *"14 seed document(s) absent from the manifest"*. That is the one
condition `work/golden/prompts/4-claude-corpus.md` authorises a rebuild on.

**Why not `build_golden_rung.py` directly.** The 2026-09-12 builder begins with
`shutil.rmtree(rung)`, and the corpora are KEPT (Arpit, 2026-09-12: never wipe
a rung). So this driver reaches the builder's end state by EDITING the existing
rung repository, and proves it reached the same state by building a reference
copy in a scratch directory with the unmodified builder and comparing
`index_root_sha256` — see `--reference`.

The builder and generator are NOT edited: they are the reproducibility claim
for `ext/`.

What an in-place rebuild does, per rung:

1. Refuse unless the rung matches its committed manifest (`rungs.verify`).
2. Copy every file of `work/golden/seed/` into `seed/`; the ones already there
   must come out byte-identical (they are the same seed).
3. The rung keeps its headline size, as on 2026-09-21: `ext_n = count - seeds`,
   so the ext stream is 14 documents shorter. The dropped documents are the
   stream's TAIL (the stream is prefix-stable) and are `git rm`'d; every kept
   ext file is checked byte-for-byte against the generator's text.
4. Commit the new seed documents grouped by their `seed-dates.tsv` date, at
   that date (`GIT_AUTHOR_DATE`/`GIT_COMMITTER_DATE`), then the removal. fux
   reads `mtime` as the committer time of the newest commit touching a path,
   and history here is linear, so every file ends with the date the builder
   would give it.
5. Re-run `fux setup --no-agents` so the rung's `.fux/` config is the current
   engine's, re-assert the declared sources and `pii.toml`, check the skip
   list, `fux ingest --full`, commit `.fux/`.
6. Write the three ladder records exactly as the builder does, plus
   `engine_commit:` (W-186).

🔴 **Reads `work/golden/seed/` and `seed-dates.tsv` and nothing else under
`work/golden/`**, and writes only `work/golden/ladder/`.

    python rebuild_in_place.py                     # all eight, in place
    python rebuild_in_place.py rung-seed           # one
    python rebuild_in_place.py --reference DIR rung-seed   # scratch build, unmodified builder
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path("/Users/arpitarya/my_programs/fux")
GEN_DIR = REPO / "work" / "regression" / "2026-09-12-golden-ladder" / "evidence" / "generator"
SEED = REPO / "work" / "golden" / "seed"
LADDER = REPO / "work" / "golden" / "ladder"
CORPORA = Path("/Users/arpitarya/my_programs/fux-lab/corpora/golden")
FUX = REPO / ".venv" / "bin" / "fux"

#: (rung, total documents incl. every seed document); None => the seed corpus.
RUNGS = [
    ("rung-seed", None),
    ("rung-00100", 100),
    ("rung-00200", 200),
    ("rung-00500", 500),
    ("rung-01000", 1000),
    ("rung-02000", 2000),
    ("rung-05000", 5000),
    ("rung-10000", 10000),
]

#: Fixed stamps for the two commits that carry no document date, so the rung
#: repository is reproducible from this file.
REMOVAL_STAMP = "2026-09-23T12:00:00+00:00"
CONFIG_STAMP = "2026-09-23T12:02:00+00:00"
INDEX_STAMP = "2026-09-23T12:05:00+00:00"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


builder = _load("build_golden_rung", GEN_DIR / "build_golden_rung.py")
gen = _load("make_golden_ext", GEN_DIR / "make_golden_ext.py")
sys.path.insert(0, str(REPO / "tools" / "differential"))
import rungs  # noqa: E402

run = builder.run


def engine_commit() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                          text=True, capture_output=True).stdout.strip()


def seed_files() -> list[str]:
    return sorted("seed/" + p.relative_to(SEED).as_posix()
                  for p in SEED.rglob("*") if p.is_file())


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def stamp(date: str) -> dict:
    return {"GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date}


def in_place(name: str, count: int | None, commit: str) -> int:
    rung = CORPORA / name
    if not (rung / ".git").is_dir():
        raise SystemExit(f"{name}: no rung repository at {rung} — refusing to create one")
    problems = rungs.verify(name, rung)
    if problems:
        raise SystemExit(f"{name}: does not match its manifest, refusing:\n  " + "\n  ".join(problems))

    seeds = seed_files()
    dates = builder.seed_dates()
    missing = [s for s in seeds if s not in dates]
    if missing:
        raise SystemExit(f"seed-dates.tsv does not cover: {missing}")
    n = len(seeds) if count is None else count
    ext_n = n - len(seeds)

    old_paths = {rel for _sha, rel in rungs.documents(name)}
    old_ext = sorted(p for p in old_paths if p.startswith("ext/"))

    # 2. seeds -----------------------------------------------------------
    new_seeds = []
    for rel in seeds:
        src = (SEED / rel[len("seed/"):]).read_bytes()
        dst = rung / rel
        if dst.exists():
            if dst.read_bytes() != src:
                raise SystemExit(f"{name}: {rel} differs from work/golden/seed/ — not a pure addition")
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src)
        new_seeds.append(rel)

    # 3. ext: keep the stream's prefix, drop its tail ---------------------
    stream = gen.stream(ext_n) if ext_n > 0 else []
    bad = gen.check_corpus(stream)
    if bad:
        raise SystemExit(f"{name}: generator reports seed-entity leaks: {bad[:5]}")
    keep = {d["path"]: d for d in stream}
    if not set(keep) <= set(old_ext):
        raise SystemExit(f"{name}: the shorter stream names files the rung never had: "
                         f"{sorted(set(keep) - set(old_ext))[:5]}")
    for path, d in keep.items():
        if (rung / path).read_bytes() != d["text"].encode("utf-8"):
            raise SystemExit(f"{name}: {path} is not the generator's bytes")
    drop = sorted(set(old_ext) - set(keep))

    # 4. commits ---------------------------------------------------------
    by_date: dict[str, list[str]] = defaultdict(list)
    for rel in new_seeds:
        by_date[dates[rel]].append(rel)
    for date in sorted(by_date):
        paths = sorted(by_date[date])
        run(["git", "add", "--"] + paths, cwd=rung)
        run(["git", "commit", "-q", "-m", f"corpus: {date} ({len(paths)} documents)"],
            cwd=rung, env=stamp(f"{date}T12:00:00+00:00"))
    if drop:
        run(["git", "rm", "-q", "--"] + drop, cwd=rung)
        run(["git", "commit", "-q", "-m",
             f"corpus: drop the ext tail ({len(drop)} documents) — seed grew to {len(seeds)}, "
             f"rung keeps {n}"], cwd=rung, env=stamp(REMOVAL_STAMP))

    all_docs = {d: ("seed", "authored", dates[d]) for d in seeds}
    all_docs.update({d["path"]: (d["category"], d["origin"], d["date"]) for d in stream})
    on_disk = {p.relative_to(rung).as_posix() for sub in ("seed", "ext")
               if (rung / sub).exists() for p in (rung / sub).rglob("*") if p.is_file()}
    if on_disk != set(all_docs) or len(all_docs) != n:
        raise SystemExit(f"{name}: tree holds {len(on_disk)} documents, expected {n}; "
                         f"extra {sorted(on_disk - set(all_docs))[:5]} "
                         f"missing {sorted(set(all_docs) - on_disk)[:5]}")

    # 5. config, ingest --------------------------------------------------
    run([str(FUX), "setup", "--no-agents"], cwd=rung)
    (rung / ".fux" / "sources" / "dirs").write_text(
        builder.SOURCES + (builder.EXT_SOURCES if ext_n > 0 else ""), encoding="utf-8")
    (rung / ".fux" / "pii.toml").touch()
    fmts = (rung / ".fux" / "formats.toml").read_text()
    for e in (".md", ".txt"):
        assert f'"*{e}"' in fmts, f"formats.toml does not include {e}"
    for e in ("html", "eml", "yaml"):
        assert f"{e} =" in fmts, f"formats.toml does not bind .{e}"
    run(["git", "add", "-A", "--", ".fux"], cwd=rung)
    if run(["git", "diff", "--cached", "--quiet"], cwd=rung, check=False).returncode:
        run(["git", "commit", "-q", "-m", "fux: index configuration (fux setup, current engine)"],
            cwd=rung, env=stamp(CONFIG_STAMP))

    skipped = run([str(FUX), "ingest", "--list-skipped"], cwd=rung, check=False)
    bad = [ln for ln in skipped.stdout.splitlines() if "seed/" in ln]
    if bad:
        raise SystemExit(f"{name}: a seed document is on the skip list:\n" + "\n".join(bad))
    run([str(FUX), "ingest", "--full", "--no-progress"], cwd=rung)
    run(["git", "add", "-A", "--", ".fux"], cwd=rung)
    run(["git", "commit", "-q", "-m", f"fux: index {name} ({len(seeds)} seed documents)"],
        cwd=rung, env=stamp(INDEX_STAMP))

    # 6. ladder records ---------------------------------------------------
    return write_records(name, rung, all_docs, n, commit)


def write_records(name: str, rung: Path, all_docs: dict, n: int, commit: str) -> int:
    lines = []
    for path in sorted(all_docs):
        cat, origin, _d = all_docs[path]
        lines.append(f"{sha((rung / path).read_bytes())}  {path}  {cat}  {origin}")
    (LADDER / f"{name}.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")

    ver = run([str(FUX), "--version"], cwd=rung).stdout.strip()
    head = run(["git", "rev-parse", "HEAD"], cwd=rung).stdout.strip()
    (LADDER / f"{name}.index").write_text(
        f"engine: {ver}\n"
        f"engine_commit: {commit}\n"
        f"rung: {name}\n"
        f"documents: {n}\n"
        f"index_root_sha256: {rungs.index_root_sha256(rung)}\n"
        f"rung_head_commit: {head}\n", encoding="utf-8")

    cov = builder.coverage(rung)
    declared_archived = sum(1 for p in all_docs if p.startswith(("seed/archive/", "ext/archive/")))
    targets: set[str] = set()
    for p in all_docs:
        text = (rung / p).read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"^supersedes:\s*(\S+)\s*$", text, re.M):
            targets.add(m.group(1))
    unknown = sorted(t for t in targets if t not in all_docs)
    if unknown:
        raise SystemExit(f"{name}: supersedes: targets not in the rung: {unknown}")
    (LADDER / f"{name}.coverage").write_text(
        f"rung: {name}\n"
        f"documents_indexed: {cov['total']}\n"
        f"archived_declared: {declared_archived}\n"
        f"archived_in_index: {cov['archived']}\n"
        f"superseded_declared: {len(targets)}\n"
        f"superseded_in_index: {cov['superseded']}\n"
        f"carrying_mtime: {cov['mtime']}\n"
        f"categories: {json.dumps(dict(Counter(c for c, _, _ in all_docs.values())), sort_keys=True)}\n",
        encoding="utf-8")

    problems = []
    if cov["total"] != n:
        problems.append(f"index holds {cov['total']} documents, rung declares {n}")
    if cov["archived"] != declared_archived:
        problems.append(f"archived: {cov['archived']} indexed vs {declared_archived} declared")
    if cov["superseded"] != len(targets):
        problems.append(f"superseded: {cov['superseded']} indexed vs {len(targets)} declared")
    if cov["mtime"] != cov["total"]:
        problems.append(f"mtime: {cov['mtime']} of {cov['total']}")
    if problems:
        print(f"NOT FROZEN — {name}:", file=sys.stderr)
        for p in problems:
            print("  " + p, file=sys.stderr)
        return 1
    print(f"{name}: {n} documents · archived {declared_archived} · superseded {len(targets)} · "
          f"mtime {cov['mtime']}/{cov['total']} · root {rungs.index_root_sha256(rung)[:12]} · frozen",
          flush=True)
    return 0


def reference(scratch: Path, name: str, count: int | None) -> int:
    """Build `name` from nothing with the UNMODIFIED builder, under `scratch`.

    The builder's two module globals are pointed away from the lab and the
    ladder, so its `rmtree` can only ever reach a scratch directory.
    """
    scratch = scratch.resolve()
    assert CORPORA not in scratch.parents and scratch != CORPORA
    builder.LAB = scratch / "lab"
    builder.LADDER = scratch / "ladder"
    n = len(seed_files()) if count is None else count
    sys.argv = ["build_golden_rung.py", "--rung", name, "--count", str(n)]
    return builder.main()


def main() -> int:
    args = sys.argv[1:]
    scratch = None
    if args[:1] == ["--reference"]:
        scratch, args = Path(args[1]), args[2:]
    only = args or [nm for nm, _ in RUNGS]
    commit = engine_commit()
    print(f"seed documents: {len(seed_files())}   engine_commit: {commit}", flush=True)
    for name, count in RUNGS:
        if name not in only:
            continue
        rc = reference(scratch, name, count) if scratch else in_place(name, count, commit)
        if rc:
            return rc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
