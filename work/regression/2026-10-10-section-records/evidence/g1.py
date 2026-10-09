#!/usr/bin/env python3
"""G1 — the W-251 #9 size bar on a --full re-ingested copy of rung-10000. Read-only.

    python3 g1.py <rung-copy> > g1.json

Bars (PRE-REGISTRATION §G1): section plane / doc plane <= 2.0; total committed
.fux/index/ <= 55 000 000 B; largest file under .fux/index/ <= 1 048 576 B;
totality misses and nsec disagreements = 0.
"""
import json, sys
from pathlib import Path

root = Path(sys.argv[1]) / ".fux" / "index"
doc_paths = sorted(root.glob("??.jsonl"))
sec_paths = sorted((root / "sections").glob("??.jsonl"))
every = [p for p in root.rglob("*") if p.is_file()]
doc_bytes = sum(p.stat().st_size for p in doc_paths)
sec_bytes = sum(p.stat().st_size for p in sec_paths)
total = sum(p.stat().st_size for p in every)
largest = max(every, key=lambda p: p.stat().st_size)

def records(paths):
    for p in paths:
        for line in p.read_bytes().split(b"\n")[1:]:
            if line:
                yield json.loads(line)

docs = {r["id"]: r for r in records(doc_paths)}
secs = {}
for r in records(sec_paths):
    secs.setdefault(r["id"].rsplit("#s", 1)[0], []).append(r)
pad = lambda xs: (list(xs) + [0, 0])[:2]
nsec_bad = [d for d, r in docs.items() if r.get("nsec", 0) != len(secs.get(d, []))]
orphans = [p for p in secs if p not in docs]
totality = []
for parent, group in secs.items():
    doc = docs.get(parent)
    if doc is None:
        continue
    flen = [sum(pad(s["flen"])[i] for s in group) for i in range(2)]
    ok = flen == pad(doc["flen"])
    for term, tf in doc["terms"].items():
        got = [sum(pad(s["terms"].get(term, []))[i] for s in group) for i in range(2)]
        ok = ok and got == pad(tf)
    if not ok:
        totality.append(parent)
ratio = sec_bytes / doc_bytes
out = {
    "documents": len(docs),
    "multi_section_documents": len(secs),
    "section_records": sum(len(g) for g in secs.values()),
    "doc_plane_bytes": doc_bytes,
    "section_plane_bytes": sec_bytes,
    "ratio": round(ratio, 4),
    "total_index_bytes": total,
    "largest_file": str(largest.relative_to(root)),
    "largest_file_bytes": largest.stat().st_size,
    "totality_misses": len(totality),
    "nsec_disagreements": len(nsec_bad) + len(orphans),
    "bars": {
        "ratio_le_2.0": ratio <= 2.0,
        "total_le_55000000": total <= 55_000_000,
        "largest_le_1048576": largest.stat().st_size <= 1_048_576,
        "integrity_zero": not totality and not nsec_bad and not orphans,
    },
}
out["verdict"] = "PASS" if all(out["bars"].values()) else "FAIL"
print(json.dumps(out, indent=1))
