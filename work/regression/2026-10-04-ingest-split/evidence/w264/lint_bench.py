"""W-264 DoD 1: is the 6 s the per-call `_lint` (W-255) re-parsing every pattern on every apply?

Times the run.py redact loop shape (body + title + loc per document) twice in one
process on the same parsed documents: as shipped, and with `Rule.compiled`
memoised per rule (re.compile alone, as before W-255, after one lint at load).
"""
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
files, _ = walk_sources(root, source_dirs(root, config.dirs_file),
                        excludes=source_excludes(root, config.dirs_file),
                        types=read_types(root), ignores=fuxignore.read(root))
parsed = {}
for wf in files:
    d = parse_document(wf.content, wf.rel_path, root)
    if d is not None:
        parsed[f"file:{wf.rel_path}"] = d
rules = pii_mod.load(root)


def loop():
    s = time.perf_counter()
    for doc_id, doc in parsed.items():
        pii_mod.redact(rules, doc.body)
        front = doc.meta.get("title")
        if isinstance(front, str) and front:
            pii_mod.redact(rules, front)
        pii_mod.redact(rules, doc_id.split(":", 1)[1])
    return time.perf_counter() - s


calls = {"n": 0}
orig = pii_mod._compile


def counting(rule):
    calls["n"] += 1
    return orig(rule)


pii_mod._compile = counting
shipped = loop()
n_calls = calls["n"]
pii_mod._compile = orig

import re

memo = {r: re.compile(r.pattern, sum(pii_mod._FLAGS[f] for f in r.flags)) for r in rules}
pii_mod.Rule.compiled = lambda self: memo[self]
memoised = loop()
lint_one = time.perf_counter()
for _ in range(1000):
    pii_mod._lint(rules[6].pattern, 0)
lint_one = (time.perf_counter() - lint_one) / 1000
print(json.dumps({"root": str(root), "docs": len(parsed), "compile_calls": n_calls,
                  "redact_loop_shipped_s": round(shipped, 3),
                  "redact_loop_memoised_s": round(memoised, 3),
                  "lint_one_call_us": round(lint_one * 1e6, 1)}))
