#!/usr/bin/env python3
"""Score the `families` lens's misfits against work/golden/planted-misfits.tsv.

    python3 check_planted.py <planted-misfits.tsv> <families-<rung>.json> <rung>

A planted misfit is FOUND when its document is listed as a misfit AND the
heading the TSV names is in its `missing` list — case-folded, and with a
leading section number (`5. `, `2.1 `) stripped, because the TSV names the
heading as `Requalification` and the document numbers it `5. Requalification`. A control is
FLAGGED when its document is listed as a misfit at all. Every other misfit is
printed as `unplanted` — the lens's own finding, with no known answer.
Prints one line per planted row and a summary; exit 0 always (a capture, not
a gate).
"""
import csv
import json
import re
import sys

NUM = re.compile(r"^\d+(?:\.\d+)*\.?\s+")


def bare(h: str) -> str:
    return NUM.sub("", h).casefold()


tsv, fam_path, rung = sys.argv[1], sys.argv[2], sys.argv[3]
rows = list(csv.DictReader(open(tsv, encoding="utf-8"), delimiter="\t"))
fam = json.load(open(fam_path, encoding="utf-8"))
misfits = {m["id"].removeprefix("file:"): m for m in fam["misfits"]}
member_of = {}
for f in fam["families"]:
    for m in f["members"]:
        member_of[m.removeprefix("file:")] = (f.get("name") or "", len(f["members"]))

found = missed = flagged = 0
print(f"## {rung}: {fam['family_count']} families, {fam['misfit_count']} misfits, "
      f"misfit_share {fam['misfit_share']:.4f}, flagged {fam['misfit_flagged']}")
for r in rows:
    path = r["file"]
    m = misfits.get(path)
    fam_name, size = member_of.get(path, ("-", 0))
    in_family = f"family of {size}" if size else "NOT IN A FAMILY"
    if r["expected"] == "misfit":
        want = bare(r["missing_heading"])
        hit = m is not None and any(want == bare(h) for h in m["missing"])
        found += hit
        missed += not hit
        got = m["missing"] if m else "-"
        print(f"{'FOUND ' if hit else 'MISSED'}  {path}  want={r['missing_heading']!r}  "
              f"missing={got}  {in_family}")
    else:
        bad = m is not None
        flagged += bad
        print(f"{'FLAGGED' if bad else 'clean  '} {path}  control  {in_family}"
              + (f"  missing={m['missing']}" if bad else ""))
planted = {r["file"] for r in rows}
for path, m in sorted(misfits.items()):
    if path not in planted:
        print(f"unplanted  {path}  missing={m['missing']}")
print(f"summary {rung}: planted found {found}/{found + missed}, controls flagged {flagged}/"
      f"{sum(1 for r in rows if r['expected'] != 'misfit')}, unplanted misfits "
      f"{sum(1 for p in misfits if p not in planted)}")
