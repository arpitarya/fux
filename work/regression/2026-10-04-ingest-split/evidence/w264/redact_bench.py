"""W-264 DoD 1: isolate the body-redact cost on a rung copy (walk, parse, then redact)."""
import json
import sys
import time
from pathlib import Path

from fux.config import load as load_config
from fux.ingest import fuxignore, pii as pii_mod
from fux.ingest.gitdir import read_types, source_dirs, source_excludes, walk_sources
from fux.ingest.parse import parse_document

root = Path(sys.argv[1]).resolve()
config = load_config(root)
t = time.perf_counter()
files, _ = walk_sources(root, source_dirs(root, config.dirs_file),
                        excludes=source_excludes(root, config.dirs_file),
                        types=read_types(root), ignores=fuxignore.read(root))
t1 = time.perf_counter()
parsed = {}
for wf in files:
    d = parse_document(wf.content, wf.rel_path, root)
    if d is not None:
        parsed[wf.rel_path] = d
t2 = time.perf_counter()
rules = pii_mod.load(root)
chars = sum(len(d.body) for d in parsed.values())
per = {}
if "--per-rule" in sys.argv:
    for r in rules:
        s = time.perf_counter()
        for d in parsed.values():
            r.apply(d.body)
        per[r.name] = round(time.perf_counter() - s, 3)
s = time.perf_counter()
nonzero = 0
for d in parsed.values():
    _, h = pii_mod.redact(rules, d.body)
    nonzero += bool(h)
whole = time.perf_counter() - s
print(json.dumps({"root": str(root), "docs": len(parsed), "body_chars": chars,
                  "walk": round(t1 - t, 2), "parse": round(t2 - t1, 2),
                  "redact_body": round(whole, 3), "docs_with_hits": nonzero,
                  "rules": len(rules), "per_rule": per}))
